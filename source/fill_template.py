"""
fill_template.py — fill template tags the table doesn't carry directly.

Three jobs:
  1. measurement-level tags (measurementMethod / Unit / Statistic) per column;
  2. paper-level tags (basisOfRecord / sex / lifeStage) for every species;
  3. value-legend decoding: turn table codes (W, M(O), LDW) into the verbatim
     terms the paper defines (Wood, Found in mounds of other termites, ...).

For (3) we try a deterministic footnote parse first (tables.parse_legends_from_text,
which copies the term *verbatim* and so matches the volunteers' wording) and only
ask the LLM for codes the footnote parse couldn't resolve. The old version asked
the LLM for everything and got paraphrases like "wood feeders", which is what
tanked the match against ground truth.
"""

from __future__ import annotations

import json
import time
import re
from pathlib import Path

from text_manager import get_tables
from tables import (parse_table, parse_legends_from_text, legend_from_code_definitions,
                    legend_for_named_column,
                    apply_legend, clean_text)
from column_relevance import make_llm, invoke_sized, loads_salvaging

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "template_descriptions"
_EMPTY_LIKE = {None, "", "null", "none", "unknown"}

# Value-legend decoding decides, per code, whether an explicit definition exists
# in the paper and copies its wording. On the small e2b model this call is the
# least stable (it non-deterministically returns null for a code it CAN resolve),
# so run it on the larger e4b: bigger logit margins flip far less under the GPU's
# float non-determinism, and it is one low-volume call per table.
DECODE_MODEL = "gemma4:e4b-it-qat"

# Max characters of paper prose fed to a tag agent. The measurement-level tag
# step runs one call PER COLUMN, and the paper-/cross-level tag calls run per
# tag; feeding the whole paper (e.g. Fondjo2024 ~128k chars) each time balloons
# num_ctx to 49k+ and makes every call crawl — even on the GPU — so a 25-column
# table takes many minutes. The tag signal (measurement method/unit/statistic,
# sex/lifeStage/caste) lives in the abstract + methods, which sit at the head of
# the paper, so bound the context to keep each call in a small, fast window.
TAG_CONTEXT_CHARS = 16000
_HEAD_CHARS = 3000          # title + abstract always kept

# Paragraphs that carry tag evidence: who/what was measured (sex, stage, caste,
# n), how (instrument, units, statistic) and where values came from.
_TAG_EVIDENCE_RE = re.compile(
    r"\b(males?|females?|workers?|queens?|gynes?|drones?|soldiers?|larva[el]?|nymphs?|"
    r"pupa[el]?|instars?|adults?|juveniles?|specimens?|individuals?|measured|"
    r"measurements?|preserved|pinned|ethanol|museum|reared|laboratory|caliper|"
    r"microscope|weighed|literature|database|obtained|mean|means|s\.?e\.?|s\.?d\.?|"
    r"standard (?:error|deviation)|n\s*=|sampled|collected|traps?)\b", re.I)
_METHODS_HEAD_RE = re.compile(r"^#*\s*\d*\.?\s*(materials?\s+and\s+methods|methods|methodology|"
                              r"study (?:area|site|design)|sampling|data collection)\b", re.I | re.M)
def _spaced(word):          # 'R E F E R E N C E S' (letter-spaced headings, Gibb2005)
    return r"\s?".join(word)


_REFS_HEAD_RE = re.compile(
    rf"^#*\s*(?:{_spaced('references')}|literature\s+cited|{_spaced('bibliography')})\s*:?\s*$",
    re.I | re.M)
# one bibliography entry: 'Surname, A. B. (2010) ...' / '- Surname A (2010) ...' /
# numbered '12. Surname ...' — i.e. an author-like start and a year
_REF_ENTRY_RE = re.compile(
    r"^\s*(?:[-*•]\s*|\[?\d{1,3}[.)\]]\s*)?[A-ZÀ-Ý][\w'’\-]+,?\s+(?:[A-ZÀ-Ý][.\w]*|van|de|von|da)"
    r".{0,400}?\b(1[89]\d{2}|20\d{2})[a-z]?\b", re.S)


# publisher running headers/footers that interrupt a reference list mid-page
_PAGE_NOISE_RE = re.compile(r"downloaded from https?://|terms and conditions|"
                            r"creative commons|onlinelibrary\.wiley\.com", re.I)


def _drop_reference_lists(text: str) -> str:
    """Remove each bibliography, and ONLY the bibliography.

    A paper's _full.md is the main PDF with every supplement appended after it
    (mineru_extract), so the first 'References' heading is usually the end of the
    main paper, not of the file — cutting 'everything after it' would throw the
    supplements away. Instead drop the heading plus the paragraphs that follow it
    while they look like reference entries, and resume at the first paragraph
    that does not (the next section, appendix or appended document)."""
    out, pos = [], 0
    for m in _REFS_HEAD_RE.finditer(text):
        if m.start() < pos:
            continue
        out.append(text[pos:m.start()])
        rest = text[m.end():]
        cut = 0
        for p in re.finditer(r"(?s)(.*?)(?:\n\s*\n|\Z)", rest):
            para = p.group(1)
            if not para.strip():
                if p.end() >= len(rest):
                    break
                cut = p.end()
                continue
            s = para.strip()
            is_noise = (len(s) <= 120 and not s.startswith("#")) or _PAGE_NOISE_RE.search(s)
            # a '- ...' list item with a year is an entry, even one continued
            # lowercase after a page break ('- in amounts ... 157, 101–118.')
            is_item = s.startswith(("- ", "* ", "• ")) and re.search(r"\b(1[89]\d{2}|20\d{2})\b", s)
            if not (_REF_ENTRY_RE.match(para) or is_item or is_noise):
                break               # page numbers / running headers don't end the list
            cut = p.end()
        pos = m.end() + cut
    out.append(text[pos:])
    return "".join(out)


def _cap_context(text: str) -> str:
    """Bound the prose fed to a tag agent to TAG_CONTEXT_CHARS (see above).

    The first TAG_CONTEXT_CHARS characters used to be taken verbatim, which cut
    the methods off in long papers (Gibb2005's '20 males of each species' sits at
    ~17k chars, so the router answered 'no sex information'). Now: keep the head
    (title/abstract), drop the reference list, then add the paragraphs with the
    most tag evidence — Methods paragraphs first — until the budget is used, in
    document order."""
    if not text or len(text) <= TAG_CONTEXT_CHARS:
        return text
    text = _drop_reference_lists(text)
    if len(text) <= TAG_CONTEXT_CHARS:
        return text
    head, rest = text[:_HEAD_CHARS], text[_HEAD_CHARS:]
    paras = [p for p in re.split(r"\n\s*\n", rest) if p.strip()]
    m = _METHODS_HEAD_RE.search(rest)
    methods_at = m.start() if m else None
    scored, pos = [], 0
    for i, p in enumerate(paras):
        start = rest.find(p, pos)
        pos = start + len(p)
        hits = len(_TAG_EVIDENCE_RE.findall(p))
        in_methods = methods_at is not None and methods_at <= start < methods_at + 25000
        scored.append((hits * (3 if in_methods else 1), i))
    budget = TAG_CONTEXT_CHARS - len(head)
    keep = set()
    for score, i in sorted(scored, key=lambda x: (-x[0], x[1])):
        if score == 0 or len(paras[i]) > budget:
            continue
        keep.add(i)
        budget -= len(paras[i]) + 2
    return head + "\n\n" + "\n\n".join(paras[i] for i in sorted(keep))


def get_tag_explanation(tag: str) -> str:
    return (TEMPLATE_DIR / f"{tag}.md").read_text(encoding="utf-8")


def _is_empty_like(v):
    return (v if v is None else str(v).strip().lower()) in _EMPTY_LIKE


# ---------------------------------------------------------------------------
# Generic multi-tag extractor (one LLM pass per chunk, then judge if >1 chunk)
# ---------------------------------------------------------------------------

def tag_finder_msg_builder_multi(target, tags, text):
    tag_explanations = "\n\n".join(f"### {tag}\n{get_tag_explanation(tag)}" for tag in tags)
    if target == "ALL_SPECIES_IN_THIS_PAPER":
        target_phrase = "all species studied in this paper"
    elif target.startswith("the column"):
        target_phrase = target
    else:
        target_phrase = f"the species {target}"

    system = f"""Your task is to extract from the text the following tags for {target_phrase}:
{', '.join(tags)}

Each tag is defined as:

{tag_explanations}

Pay special attention to generic methodology statements (e.g. 'specimens were
preserved in ethanol'); they override absence of evidence. Citations to other
studies should be ignored — they describe other papers' methods.

Return a JSON object keyed by tag name:
{{
    "{tags[0]}": {{"value": "<value or null>", "reasoning": "<explanation>"}},
    ...
}}"""
    return [{"role": "system", "content": system},
            {"role": "user", "content": f"Here is the text:\n{text}"}]


def agent_define_multi_tags(target, tags, chunks, llm=None):
    per_tag = {t: [] for t in tags}
    for chunk in chunks:
        try:
            msgs = tag_finder_msg_builder_multi(target, tags, _cap_context(chunk["content"]))
            content = llm.invoke(msgs).content if llm else invoke_sized(msgs)
            parsed = json.loads(content)
        except json.JSONDecodeError:
            print("Skipping malformed chunk response")
            continue
        for t in tags:
            if t in parsed:
                per_tag[t].append(parsed[t])

    if len(chunks) == 1:
        return {t: (per_tag[t][0] if per_tag[t] else {"value": None, "reasoning": "not found in text"})
                for t in tags}

    final = {}
    for t in tags:
        judge_prompt = f"""Per-chunk evaluations of tag "{t}" for {target}.

{get_tag_explanation(t)}

Combine all chunks; strongest positive evidence wins. Generic methodology
statements override absence; ignore citations to other studies.

Return: {{"tag": "{t}", "value": "<value or null>", "reasoning": "<consolidated>"}}

Per-chunk results:
{json.dumps(per_tag[t], indent=2)}"""
        final[t] = json.loads(invoke_sized([{"role": "system", "content": judge_prompt}]))
    return final


# ---------------------------------------------------------------------------
# (1) measurement-level tags
# ---------------------------------------------------------------------------

NUMERIC_ONLY_TAGS = {"measurementUnit", "measurementStatistic"}


def _fill_column_tags_from_siblings(table_mapping, tags):
    """Fill a measurementType column's MISSING column-level tag from the unanimous
    value of its sibling measurementType columns in the same table.

    Some tags — notably basisOfRecord — are effectively constant across a paper
    (every trait column in Beyer is 'HumanObservation'). The per-column LLM pass
    occasionally returns null for a column with no column-specific evidence (e.g.
    'density'), leaving an inconsistent blank that then drops the column from the
    output lookup entirely. When every OTHER measurement column agrees on a value,
    propagate it. When they disagree (e.g. Barber: morphology -> PreservedSpecimen
    but behaviour -> HumanObservation), leave the blank untouched rather than guess.
    Invents nothing: it only copies a value the model already assigned unanimously.
    """
    cols = [m for m in table_mapping.values()
            if m.get("field") == "measurementType" and m.get("category")]
    for tag in tags:
        # A unit/statistic only describes a numeric measurement: never hand a
        # numeric column's 'mm'/'mean' to a categorical sibling (Barber2017's
        # 'Mean bodylength (mm)' was the only column with a unit, so it counted
        # as "unanimous" and stamped mm/mean on wing morphology, diet, ...).
        pool = cols if tag not in NUMERIC_ONLY_TAGS else \
            [m for m in cols if m.get("value_type") != "categorical"]
        present = [m[tag] for m in pool if not _is_empty_like(m.get(tag))]
        missing = [m for m in pool if _is_empty_like(m.get(tag))]
        if not present or not missing:
            continue                      # nothing to copy, or nothing to fill
        if len({str(v) for v in present}) != 1:
            continue                      # siblings disagree -> don't guess
        consensus = present[0]
        for m in missing:
            m[tag] = consensus
            m[f"{tag}_reasoning"] = ("inherited from unanimous sibling "
                                     "measurement columns in the same table")
    return table_mapping


_HEADER_UNIT_RE = re.compile(
    r"\(\s*((?:[µμu]m|mm|cm|dm|m|km|nm|mg|µg|μg|g|kg|ml|mL|µl|l|L|s|min|h|hrs?|days?|d|"
    r"weeks?|months?|years?|yrs?|°C|ºC|℃|%|ha|m2|m²|mm2|mm²|cm2|cm²|mm3|mm³|kJ|J|W|Hz|"
    r"ppm|ind\.?|individuals|°)"
    r"(?:\s*[/·*]\s*[\w°µμ²³.-]+)*)\s*\)\s*$")


def _unit_from_header(header):
    """The unit in a trailing header parenthetical — 'Mean bodylength (mm)' ->
    'mm', 'CTmax (°C)' -> '°C', 'Mass (mg/ind)' -> 'mg/ind'. Only a recognised
    unit counts, so '(reference)' or '(Lycosidae)' is ignored. The tag LLM often
    returns no unit even when the header states it, which blanked the unit."""
    m = _HEADER_UNIT_RE.search(header or "")
    return m.group(1).strip() if m else None


def get_measurement_level_tags(table_mapping, paper_chunks, llm=None, allowed_tags=None):
    """Assign column-level tags per relevant column. ``allowed_tags`` (from the tag
    router) restricts which tags this stage handles; None means all column tags.

    Only columns the mapper routed to measurementType are tagged. These tags
    (basisOfRecord/measurementMethod/measurementUnit/measurementStatistic)
    describe a measurement, and only measurementType columns become measurement
    rows at grouping — so tagging anything else buys nothing and costs a
    whole-paper LLM call per tag per column (e.g. Fiedler's biogeographic-realm
    columns, which grouping then discards). Gating on category alone is not
    enough: the relevance pass can hand a category to a column the mapper mapped
    to no field at all (field=null), which is exactly those realm columns.
    """
    for header, mapping in table_mapping.items():
        if mapping.get("field") != "measurementType" or mapping.get("category") is None:
            continue
        is_categorical = mapping.get("value_type") == "categorical"
        # basisOfRecord is measurement-dependent (morphology -> PreservedSpecimen,
        # behaviour/ecology -> HumanObservation), so it is decided per column here
        # rather than once for the whole paper.
        tags = ["basisOfRecord", "measurementMethod"] if is_categorical else \
               ["basisOfRecord", "measurementMethod", "measurementUnit", "measurementStatistic"]
        header_unit = _unit_from_header(header)
        if header_unit and not mapping.get("measurementUnit") and \
                (allowed_tags is None or "measurementUnit" in allowed_tags):
            mapping["measurementUnit"] = header_unit
            mapping["measurementUnit_reasoning"] = "stated in the column header"
        tags = [t for t in tags if not mapping.get(t)]
        if allowed_tags is not None:
            tags = [t for t in tags if t in allowed_tags]
        if not tags:
            continue
        print(f"  column '{header}' ({'cat' if is_categorical else 'num'}) -> {tags}")
        results = agent_define_multi_tags(f"the column '{header}'", tags, paper_chunks, llm=llm)
        for tag, result in results.items():
            # A smaller local model sometimes returns null (or a bare string) for
            # a tag instead of the {value, reasoning} object; skip those rather
            # than crashing on result.get().
            if not isinstance(result, dict):
                continue
            value = result.get("value")
            if not _is_empty_like(value):
                mapping[tag] = value
                mapping[f"{tag}_reasoning"] = result.get("reasoning")

    # Reconcile blanks the per-column LLM left behind (e.g. 'density'): inherit a
    # column-level tag only when every sibling measurement column agrees on it.
    fill_tags = list(allowed_tags) if allowed_tags is not None else \
        ["basisOfRecord", "measurementMethod", "measurementUnit", "measurementStatistic"]
    _fill_column_tags_from_siblings(table_mapping, fill_tags)
    return table_mapping


# ---------------------------------------------------------------------------
# Tag routing: decide each tag's LEVEL once (paper / species / derived / varies),
# instead of hardcoding which tags are measurement-level vs paper-level.
# ---------------------------------------------------------------------------

# Curated, inspectable derivation rules. The model may route a tag to "derived"
# and is told which field it derives FROM, but the value mapping lives HERE and is
# never invented per paper. Matched case-insensitively against the driver value.
DERIVATION_RULES = {
    "sex": {
        "from": "caste",
        "map": {
            "worker": "female", "workers": "female", "minor": "female",
            "major": "female", "soldier": "female", "soldiers": "female",
            "queen": "female", "queens": "female", "gyne": "female", "gynes": "female",
            "male": "male", "males": "male", "drone": "male", "drones": "male",
        },
    },
}


def route_msg_builder(tags, species, text):
    tag_explanations = "\n\n".join(f"### {t}\n{get_tag_explanation(t)}" for t in tags)
    derivable = {t: DERIVATION_RULES[t]["from"] for t in tags if t in DERIVATION_RULES}
    deriv_note = ("\n".join(f'  - "{t}" may be derived from the field "{f}"'
                            for t, f in derivable.items()) or "  - (none)")
    system = f"""You plan, per tag, the LEVEL at which its value is decided in THIS paper.

Tags and their definitions:
{tag_explanations}

Levels (choose exactly one per tag):
- "paper": one value holds for EVERY species in the paper. Give "value".
- "species": constant within a species but differing between species. Give
  "by_species": a map from species name to that species' value.
- "derived": the value follows another recorded field (e.g. sex follows caste).
  Give "from": the field's name. ONLY these derivations are supported:
{deriv_note}
- "varies": none of the above, or no textual evidence. Give nothing.

Rules:
- Choose the level the TEXT supports; prefer the narrowest. No evidence -> "varies".
- Generic methodology statements count ("all specimens were adult females");
  citations to other studies do not.
- Use "derived" only for the derivations explicitly listed above.

Species in this paper:
{json.dumps(species, ensure_ascii=False)}

Return ONLY JSON keyed by tag:
{{
  "<tag>": {{"level": "paper|species|derived|varies",
             "value": "<only if paper>",
             "by_species": {{"<species>": "<value>"}},
             "from": "<only if derived>",
             "reasoning": "<brief>"}}
}}"""
    return [{"role": "system", "content": system},
            {"role": "user", "content": f"Here is the text:\n{text}"}]


def route_tags(tags, species, chunks, llm=None):
    """One LLM call classifying each cross-record tag into a level. Derived is only
    honoured when a curated rule exists for that tag; anything malformed, empty, or
    unsupported degrades to 'varies'. Returns {tag: {level, ...}}."""
    text = _cap_context("\n\n".join(c["content"] for c in chunks)) if chunks else ""
    msgs = route_msg_builder(tags, species, text)
    try:
        content = llm.invoke(msgs).content if llm else invoke_sized(msgs)
        parsed = json.loads(content)
    except (json.JSONDecodeError, AttributeError):
        print("  tag router: malformed response; routing all to 'varies'")
        parsed = {}
    if not isinstance(parsed, dict):
        parsed = {}

    plan = {}
    for t in tags:
        r = parsed.get(t) if isinstance(parsed.get(t), dict) else {}
        level = r.get("level")
        if level not in ("paper", "species", "derived", "varies"):
            # the small model sometimes drops "level" but still answers
            if isinstance(r.get("by_species"), dict) and r["by_species"]:
                level = "species"
            elif not _is_empty_like(r.get("value")):
                level = "paper"
        if level == "derived" and t in DERIVATION_RULES:
            rule = DERIVATION_RULES[t]
            plan[t] = {"level": "derived", "from": rule["from"], "map": rule["map"]}
        elif level == "paper" and not _is_empty_like(r.get("value")):
            plan[t] = {"level": "paper", "value": r["value"]}
        elif level == "species" and isinstance(r.get("by_species"), dict) and r["by_species"]:
            plan[t] = {"level": "species", "by_species": r["by_species"]}
        else:
            plan[t] = {"level": "varies"}
    return plan


def apply_plan(plan, grouped_path):
    """Execute a routing plan against grouped_by_species.json. paper/species tags
    are stamped onto species nodes; derived tags map a driver field (e.g. caste)
    to a value per measurement (falling back to species-level driver). setdefault
    throughout, so anything more specific already present is never overwritten.
    'column' and 'varies' do nothing here (column -> stage 3; varies -> default)."""
    data = json.loads(Path(grouped_path).read_text(encoding="utf-8"))
    log = []

    # pass 1: paper + species (so drivers like caste exist before deriving).
    for tag, spec in plan.items():
        lvl = spec["level"]
        if lvl == "paper":
            v = spec["value"]
            for sd in data.values():
                sd.setdefault(tag, v)
            log.append(f"    {tag}: paper -> all {len(data)} species ({v!r})")
        elif lvl == "species":
            by = spec["by_species"]
            n = 0
            for sp, sd in data.items():
                v = by.get(sp)
                if not _is_empty_like(v):
                    sd.setdefault(tag, v)
                    n += 1
            log.append(f"    {tag}: species -> stamped {n}/{len(data)} species")

    # pass 2: derived (driver now resolved at species level if it was set above).
    for tag, spec in plan.items():
        if spec["level"] != "derived":
            continue
        frm, mp = spec["from"], spec["map"]
        n = 0
        for sd in data.values():
            drv_sp = sd.get(frm)
            for meas in sd.get("measurements", []):
                drv = meas.get(frm, drv_sp)
                if _is_empty_like(drv):
                    continue
                val = mp.get(str(drv).strip().lower())
                if val and _is_empty_like(meas.get(tag)):
                    meas[tag] = val
                    n += 1
            if not _is_empty_like(drv_sp):
                val = mp.get(str(drv_sp).strip().lower())
                if val:
                    sd.setdefault(tag, val)
        src = f"'{frm}'" if n else f"'{frm}' (driver not present in rows)"
        log.append(f"    {tag}: derived from {src} -> set on {n} measurement(s)")

    for tag, spec in plan.items():
        if spec["level"] == "varies":
            log.append(f"    {tag}: varies -> left for default")

    Path(grouped_path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    for line in log:
        print(line)
    return data


# ---------------------------------------------------------------------------
# (2) paper-level tags
# ---------------------------------------------------------------------------

def scope_tag_msg_builder(tags, species, text):
    """Ask, per tag, at what SCOPE a single value holds (whole paper / per species
    / varies below species), and the value(s) for that scope."""
    tag_explanations = "\n\n".join(f"### {tag}\n{get_tag_explanation(tag)}" for tag in tags)
    species_list = json.dumps(species, ensure_ascii=False)
    system = f"""For each tag below, decide the SCOPE at which one value is valid, then give the value(s).

Tags and their definitions:
{tag_explanations}

Scope options (choose exactly one per tag):
- "paper": a single value is correct for EVERY species in the paper. Provide "value".
- "species": the value is constant within each species but differs between species.
  Provide "by_species": a map from species name to that species' value.
- "varies": the value changes BELOW the species level (e.g. it depends on caste,
  sex, or lifeStage within a species), or the text gives no basis for one value.
  Provide neither value nor by_species; it will be resolved elsewhere.

Rules:
- Choose "paper" or "species" ONLY with real textual evidence; otherwise "varies".
- Prefer the NARROWEST scope the evidence supports; do not generalise a single
  mention to the whole paper.
- Generic methodology statements count (e.g. "all specimens were adult females");
  citations to other studies do not.

Species in this paper:
{species_list}

Return ONLY JSON keyed by tag:
{{
  "<tag>": {{
    "scope": "paper|species|varies",
    "value": "<value — only when scope is paper>",
    "by_species": {{"<species>": "<value>"}},
    "reasoning": "<brief>"
  }}
}}"""
    return [{"role": "system", "content": system},
            {"role": "user", "content": f"Here is the text:\n{text}"}]


def agent_define_scoped_tags(tags, species, chunks, llm=None):
    """One LLM call returning a per-tag scope verdict. Scope reasoning needs the
    whole paper, so chunks are merged into a single view. Always returns every
    tag; anything missing/malformed degrades to scope='varies' (stamp nothing)."""
    text = _cap_context("\n\n".join(c["content"] for c in chunks)) if chunks else ""
    msgs = scope_tag_msg_builder(tags, species, text)
    try:
        content = llm.invoke(msgs).content if llm else invoke_sized(msgs)
        parsed = json.loads(content)
    except (json.JSONDecodeError, AttributeError):
        print("  scoped tags: malformed response; treating all as 'varies'")
        parsed = {}
    if not isinstance(parsed, dict):
        parsed = {}
    out = {}
    for t in tags:
        r = parsed.get(t)
        r = r if isinstance(r, dict) else {"scope": "varies"}
        if r.get("scope") not in ("paper", "species", "varies"):
            r["scope"] = "varies"
        out[t] = r
    return out


def get_paper_level_templates(chunks, filepath="grouped_by_species.json", llm=None):
    """Resolve cross-species tags at the RIGHT scope instead of stamping one value
    on everything. The model says, per tag, whether a value is paper-constant,
    species-constant, or varies below species; code applies each accordingly.
    setdefault throughout, so a value already established (e.g. from the table or
    a measurement) is never overwritten — most-specific wins."""
    PAPER_LEVEL_TAGS = ["sex", "lifeStage"]
    data = json.loads(Path(filepath).read_text(encoding="utf-8"))
    species = list(data.keys())
    print(f"  scope check for {PAPER_LEVEL_TAGS} across {len(species)} species")

    results = agent_define_scoped_tags(PAPER_LEVEL_TAGS, species, chunks, llm=llm)

    log = []
    for tag, r in results.items():
        scope = r.get("scope")
        if scope == "paper":
            val = r.get("value")
            if _is_empty_like(val):
                log.append(f"    {tag}: paper scope claimed but no value -> left unstamped")
                continue
            for sd in data.values():
                sd.setdefault(tag, val)
            log.append(f"    {tag}: paper-level = {val!r} -> all {len(data)} species")
        elif scope == "species":
            by = r.get("by_species") or {}
            n = 0
            for sp, sd in data.items():
                v = by.get(sp)
                if not _is_empty_like(v):
                    sd.setdefault(tag, v)
                    n += 1
            log.append(f"    {tag}: species-level -> stamped {n}/{len(data)} species")
        else:
            log.append(f"    {tag}: varies / no evidence -> left for measurement-level or default")

    Path(filepath).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    for line in log:
        print(line)
    return results


# ---------------------------------------------------------------------------
# (3) value legends: deterministic first, LLM only for the leftovers
# ---------------------------------------------------------------------------

def collect_categorical_codes(table, table_mapping):
    """{clean_header: sorted distinct values} for relevant categorical columns.

    Every distinct value is collected. Whether a value actually needs decoding
    (an opaque code) or should be kept verbatim (an already-complete term) is
    decided per value by the LLM in agent_normalize_legends — nothing is
    pre-filtered here by string shape."""
    out = {}
    for header, mapping in table_mapping.items():
        if mapping.get("field") == "verbatimIdentification" or mapping.get("category") is None:
            continue
        if mapping.get("value_type") != "categorical":
            continue
        codes = set()
        for cell in table.column_values(header):
            for part in str(cell).split(","):
                p = part.strip()
                if p:
                    codes.add(p)
        if codes:
            out[clean_text(header)] = sorted(codes)
    return out

def agent_normalize_legends(col_codes, hints, chunks, llm=None):
    """Decode table codes to canonical labels — but let the LLM first DECIDE, per
    value, whether the value even needs decoding.

    A value is rewritten only when the LLM judges it to be a short code/abbreviation
    whose expansion is EXPLICITLY DEFINED in the paper text, and it returns the
    paper's own wording. Values that are already complete terms (spring, predator,
    macropterous) come back as null and are left verbatim, so faithful data is
    never paraphrased into a synonym or prose expansion.

    Deterministic footnote pairs in `hints` are trusted and seeded first; the LLM
    is asked only about the leftover values, and over the WHOLE text at once —
    legends are global, so one grounded decision beats per-chunk passes where a
    stray methods sentence could "expand" an already-complete word.
    """
    if not col_codes:
        return {}

    # (1) seed from deterministic footnote hints — free and trusted.
    merged = {c: {} for c in col_codes}
    hints = hints or {}
    for c, codes in col_codes.items():
        hint_map = hints.get(c, {}) or {}
        for code in codes:
            v = hint_map.get(code, hint_map.get(code.lower()))
            if not _is_empty_like(v):
                merged[c][code] = v

    # (2) leftovers = values still undefined after hints
    left = {c: [code for code in codes if _is_empty_like(merged[c].get(code))]
            for c, codes in col_codes.items()}
    left = {c: codes for c, codes in left.items() if codes}
    if not left:
        return {c: {k: v for k, v in m.items() if not _is_empty_like(v)}
                for c, m in merged.items()}

    # (3) LLM decides decode-or-keep for each leftover, grounded in the full text.
    #     A null answer means "already a complete term — leave verbatim".
    cols_desc = "\n".join(f'- "{c}": values {codes}' for c, codes in left.items())
    hints_desc = json.dumps(hints, ensure_ascii=False, indent=2) if hints else "{}"
    system = f"""A scientific table has several categorical columns. SOME values are short
CODES or ABBREVIATIONS (e.g. "W", "LDW", "M(O)", "W/S") whose meaning is defined
in the table's footnotes, legend, or surrounding text. OTHER values are ALREADY
COMPLETE TERMS (e.g. "spring", "predator", "macropterous", "nocturnal") that need
no decoding at all.

For EACH value listed below, FIRST decide whether it needs decoding, then answer:
- If it is a short code/abbreviation AND the text EXPLICITLY defines what it
  stands for: return the paper's OWN definition as a clean canonical label
  (copy the wording used in the text; only fix casing).
- Otherwise return null. "Otherwise" covers (a) the value is already an ordinary
  complete word, or (b) the text gives no explicit "code = meaning" definition.
  null means "leave the value exactly as written".

STRICT RULES:
- NEVER replace a value with a synonym or paraphrase from general knowledge.
  Expand a code ONLY from an explicit "code = meaning" definition in the text.
- A value that is already an ordinary word is ALWAYS null — even if the text
  mentions related phrases. Do NOT turn "spring" into "spring–early summer", and
  do NOT turn "predator" into "carnivorous".
- Resolve each column independently; the same letter may mean different things.

EXAMPLES:
- column "Feeding group", value "W", text says "W = wood"        -> "Wood"
- column "Feeding group", value "LDW", text: "LDW lying dead wood" -> "Lying dead wood"
- column "Diet", value "predator"                                -> null
- column "Breeding season", value "spring"                       -> null

Columns and the exact values appearing in each:
{cols_desc}

Legend pairs already recovered from footnotes (trusted; clean casing only, never
override these with guesses):
{hints_desc}

Return ONLY a JSON object: {{"<column>": {{"<value>": "<canonical label or null>"}}}}"""

    context = "\n\n".join(ch["content"] for ch in chunks) if chunks else ""
    try:
        msgs = [{"role": "system", "content": system},
                {"role": "user", "content": f"Here is the text:\n{context}"}]
        content = llm.invoke(msgs).content if llm else invoke_sized(msgs, model=DECODE_MODEL)
        parsed = loads_salvaging(content)
    except (json.JSONDecodeError, AttributeError) as e:
        # used to be silent: Beyer2021's 0/1 legend decoded fine in isolation
        # but came back undecoded from the run with no trace of why
        print(f"  legend LLM reply unusable ({type(e).__name__}); codes left as written")
        parsed = {}
    except (TimeoutError, OSError) as e:
        # a slow/busy local model must not fail the whole paper: keep the
        # deterministic legends already in `merged`, leave the rest verbatim
        print(f"  legend LLM unavailable ({type(e).__name__}); using the "
              f"deterministic legends only")
        parsed = {}

    if isinstance(parsed, dict):
        for c, codes in left.items():
            got = parsed.get(c) if isinstance(parsed.get(c), dict) else {}
            for code in codes:
                # null / missing => keep verbatim (stays out of the legend map)
                if _is_empty_like(merged[c].get(code)) and not _is_empty_like(got.get(code)):
                    merged[c][code] = got[code]

    return {c: {k: v for k, v in m.items() if not _is_empty_like(v)}
            for c, m in merged.items()}


VALUE_EXTRA_FIELDS = ["measurementUnit", "measurementRemarks", "sampleSizeValue",
                      "sampleSizeUnit", "verbatimLocality", "keep"]


def route_value_extras(grouped_path, llm=None):
    """Move detail that rides along in a value into its own field.

    The SPLIT is deterministic (to_output.split_value_parts: a trailing unit,
    '(n = 4)', a taxonomic authority and/or family after a name). WHERE each
    fragment goes is decided by the LLM, once per paper over the distinct
    (trait, fragment) pairs — 'Agelenidae' is a family, '(Emerton, 1890a)' an
    authority, 'mm' a unit — with 'keep' for a split that was wrong. If the model
    is unavailable, each fragment's deterministic guess is used.

    Only EMPTY fields are filled (remarks are appended), and a value is left
    whole if any of its fragments is judged 'keep'. Rewrites grouped in place."""
    from to_output import split_value_parts   # local import avoids a cycle
    grouped = json.loads(Path(grouped_path).read_text(encoding="utf-8"))
    splits, pairs = [], {}
    for sp in grouped.values():
        for meas in sp.get("measurements", []):
            core, parts = split_value_parts(meas.get("measurementValue", ""))
            if parts:
                splits.append((meas, core, parts))
                for p in parts:
                    key = (meas.get("measurementType", ""), p["text"], p["kind"])
                    pairs.setdefault(key, {"guess": p["guess"],
                                           "example": meas.get("measurementValue", "")})
    if not splits:
        return 0
    keys = list(pairs)[:80]
    listing = "\n".join(f'{i}. trait "{t}": fragment "{f}" (looks like: {k}; '
                        f'from value "{pairs[(t, f, k)]["example"]}")'
                        for i, (t, f, k) in enumerate(keys, 1))
    system = f"""Values in a species-trait table sometimes carry extra detail that
belongs in another Darwin Core field. Each numbered fragment below was split off
a value. For each, choose where it belongs:
- "measurementUnit": the unit of the value (mm, mg, °C, days, %)
- "measurementRemarks": a note about the value — a taxonomic authority, a
  family name, a qualifier
- "sampleSizeValue": the number of individuals/samples behind the value
- "sampleSizeUnit": the unit of that sample size (individuals, colonies)
- "verbatimLocality": a place
- "keep": it is part of the value itself and must stay there

Return ONLY JSON: {{"1": "<field>", "2": "<field>", ...}}

Fragments:
{listing}"""
    routed = {}
    try:
        content = llm.invoke([{"role": "system", "content": system}]).content if llm \
            else invoke_sized([{"role": "system", "content": system}])
        answer = json.loads(content)
        for i, key in enumerate(keys, 1):
            field = answer.get(str(i)) if isinstance(answer, dict) else None
            if field in VALUE_EXTRA_FIELDS:
                routed[key] = field
    except (json.JSONDecodeError, AttributeError, TimeoutError, OSError) as e:
        print(f"  value-extra routing LLM unavailable ({type(e).__name__}); using defaults")
    n = 0
    for meas, core, parts in splits:
        fields = [routed.get((meas.get("measurementType", ""), p["text"], p["kind"]), p["guess"])
                  for p in parts]
        if "keep" in fields:
            continue
        meas["measurementValue"] = core
        for p, field in zip(parts, fields):
            if field == "measurementRemarks":
                note = f"{p['kind'].replace('_', ' ')}: {p['text']}"
                meas[field] = "; ".join(x for x in (str(meas.get(field) or "").strip(), note) if x)
            elif not str(meas.get(field) or "").strip():
                meas[field] = p["text"]
        n += 1
    Path(grouped_path).write_text(json.dumps(grouped, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  moved extra detail out of {n} value(s) "
          f"({len(routed)}/{len(keys)} fragment(s) routed by the LLM)")
    return n


def _looks_like_code(v: str) -> bool:
    """A value that may need expanding: short ('W', 'nc', 'Pred'), or an
    abbreviation-shaped token ('LDW', 'GenForager', 'W/S', 'M(O)', 'para.sma').
    Ordinary words and phrases ('spring', 'preferring moist places') are not."""
    s = str(v).strip()
    if not s or len(s) > 24:
        return False
    if len(s) <= 4:
        return True
    return bool(re.search(r"[A-Z].*[A-Z]|[a-z][A-Z]|\d|[/.()_]", s))


def _legend_code_list(value: str, legend: dict):
    """['Sub', 'Lit'] when a cell joins >= 2 codes that are EACH defined in the
    column's legend ('Sub/Lit', 'W, S', 'A+B'); else None. The legend is the
    evidence that the pieces are separate states — a slash inside an ordinary
    value ('3/4', 'and/or') has pieces the legend never defines, so it stays."""
    parts = [p.strip() for p in re.split(r"\s*[/,;+]\s*", value.strip())]
    if len(parts) < 2 or not all(parts):
        return None
    keys = {str(k).strip().lower() for k in legend}
    if not all(p.lower() in keys for p in parts):
        return None
    return list(dict.fromkeys(parts))


def _code_context(text: str, codes, limit: int = 6000, headers=()) -> str:
    """The paragraphs that mention any of these codes as a whole token, most
    codes first, capped at `limit` chars — what a legend decode actually needs,
    instead of 16k chars of general prose.

    A paragraph that also names a column counts double per name: digit codes
    ('0'/'1') occur in nearly every paragraph, so without the names the legend
    ('Sociality: Social species (1) or solitary species (0)', Beyer2021) lost
    to number-heavy results paragraphs and never reached the model."""
    paras = [p for p in re.split(r"\n\s*\n", text or "") if p.strip()]
    pats = [re.compile(rf"(?<![\w]){re.escape(c)}(?![\w])") for c in set(codes) if c]
    names = [re.compile(rf"\b{re.escape(h.strip())}\b", re.I) for h in set(headers) if h and h.strip()]

    def score(p):
        hits = sum(bool(p_.search(p)) for p_ in pats)
        return hits + 2 * sum(bool(n.search(p)) for n in names) if hits else 0
    scored = sorted(((score(p), i) for i, p in enumerate(paras)),
                    key=lambda x: (-x[0], x[1]))
    keep, used = [], 0
    for score, i in scored:
        if score == 0 or used + len(paras[i]) > limit:
            continue
        keep.append(i)
        used += len(paras[i])
    return "\n\n".join(paras[i] for i in sorted(keep)) or _cap_context(text)[:limit]


def decode_grouped_values(grouped_path, tables, paper_text, chunks, mappings, llm=None):
    """Decode table codes to canonical labels and rewrite grouped in place.

    Strategy: recover the footnote legend deterministically as *grounding*, then
    let the LLM produce the canonical label for every code (it reads the
    annotation and normalises). Resolution order per code:
        LLM canonical label  ->  deterministic footnote term  ->  raw code.
    """
    from table_to_data import table_id  # local import avoids a cycle at module load

    grouped = json.loads(Path(grouped_path).read_text(encoding="utf-8"))

    # A code's meaning often lives in a DATA-DICTIONARY table (a term/code column
    # paired with a definition column), which the prose chunks strip out — so the
    # resolver never sees it. The mapper already flags those tables
    # (field=definitionTerm/definitionText); render just those as compact
    # "term = definition" lines and give them to the resolver as extra context.
    # Only dictionary tables are added (they are inherently small), never the big
    # data tables, so context stays bounded on huge papers.
    legend_lines = []
    for table in tables:
        m = mappings.get(table_id(table))
        if not m:
            continue
        term_cols = [h for h, mm in m.items()
                     if isinstance(mm, dict) and mm.get("field") == "definitionTerm"]
        text_cols = [h for h, mm in m.items()
                     if isinstance(mm, dict) and mm.get("field") == "definitionText"]
        if not (term_cols and text_cols):
            continue
        for rec in table.data_records():
            term = " ".join(str(rec.get(c, "")).strip() for c in term_cols if rec.get(c))
            text = " ".join(str(rec.get(c, "")).strip() for c in text_cols if rec.get(c))
            if term and text:
                legend_lines.append(f"{term} = {text}")
    dict_chunks = ([{"content": "Data-dictionary definitions:\n" + "\n".join(legend_lines)}]
                   if legend_lines else [])

    grouped_types = {clean_text(m.get("measurementType", ""))
                     for sp in grouped.values() for m in sp.get("measurements", [])}
    prose_text = "\n\n".join(c["content"] for c in chunks) if chunks else ""
    decode_cache: dict = {}
    for table in tables:
        mapping = mappings.get(table_id(table))
        if not mapping:
            continue

        # deterministic footnote legend = grounding hints for the LLM
        hints = parse_legends_from_text(paper_text, table)
        hints = {clean_text(k): v for k, v in hints.items()}

        # LLM normalises every code (grounded on the hints + any dictionary tables).
        # Cap the PROSE context (bounds num_ctx so a large paper can't balloon the
        # decode call — see TAG_CONTEXT_CHARS) but keep the dictionary-table chunks
        # in full, since those carry the exact "code = meaning" definitions decode
        # exists to read.
        col_codes = collect_categorical_codes(table, mapping)
        # Numeric-looking CODE columns ('Colony population' = 1/2/3, Arnan2012)
        # are typed numeric, so they never reach decoding. Decode one only when
        # a legend introduced by its OWN name defines its values — and pass only
        # those codes on, so the LLM is never asked to "decode" a real number.
        for header, mm in mapping.items():
            if mm.get("field") != "measurementType" or mm.get("category") is None \
                    or mm.get("value_type") == "categorical":
                continue
            vals = sorted({str(v).strip() for v in table.column_values(header) if str(v).strip()})
            named = legend_for_named_column(paper_text, header, vals) if len(vals) <= 12 else {}
            if named and set(vals) <= set(named):
                col = clean_text(header)
                col_codes[col] = sorted(named)
                hints.setdefault(col, {}).update({k: v for k, v in named.items()
                                                  if k not in hints.get(col, {})})
        # codes defined in a caption/sentence with no footnote marker
        # ('M: monophagous, NO: narrowly oligophagous, ...') — also trusted
        for col, codes in col_codes.items():
            # a legend introduced by this column's own name wins ('Colony
            # population: 1, hundreds; 2, thousands'); else a caption that
            # defines several of its codes
            found = legend_for_named_column(paper_text, col, codes) or \
                legend_from_code_definitions(paper_text, codes)
            if found:
                hints.setdefault(col, {})
                for code, term in found.items():
                    hints[col].setdefault(code, term)
        # Only columns that feed a measurement in grouped are worth decoding:
        # stats tables and skipped tables produced nothing (Barber2017's GLMM
        # tables used to cost a full decode call each).
        canon = {clean_text(h): clean_text(m.get("canonicalType") or h) for h, m in mapping.items()}
        col_codes = {c: v for c, v in col_codes.items() if canon.get(c, c) in grouped_types}
        if not col_codes:
            continue
        # The LLM is asked only about values that LOOK like codes; a column of
        # plain words ('spring', 'predator') needs no call at all. The
        # deterministic legend readers above still ran on every value.
        ask = {c: [v for v in codes if _looks_like_code(v)
                   and _is_empty_like((hints.get(c) or {}).get(v))]
               for c, codes in col_codes.items()}
        ask = {c: v for c, v in ask.items() if v}
        sig = json.dumps([sorted(col_codes.items()), sorted((k, sorted(v.items()))
                          for k, v in hints.items())], ensure_ascii=False)
        t0 = time.time()
        if sig in decode_cache:
            llm_legends = decode_cache[sig]
            how = "reused (same columns/codes as an earlier fragment)"
        elif ask:
            ctx = _code_context(prose_text, [v for vs in ask.values() for v in vs],
                                headers=list(ask))
            llm_legends = agent_normalize_legends(
                {c: col_codes[c] for c in ask}, hints,
                [{"content": ctx}] + dict_chunks, llm=llm)
            for c, codes in col_codes.items():      # hint-only columns
                if c not in llm_legends and hints.get(c):
                    llm_legends[c] = {k: v for k, v in hints[c].items() if k in codes}
            how = f"LLM on {sum(map(len, ask.values()))} code(s), {len(ctx)} chars context"
        else:
            llm_legends = {c: {k: v for k, v in (hints.get(c) or {}).items() if k in codes}
                           for c, codes in col_codes.items()}
            how = "deterministic only (no code-like values left)"
        decode_cache[sig] = llm_legends
        n_det = sum(len(v) for v in hints.values())
        print(f"    {table_id(table)}: {len(col_codes)} column(s), {n_det} code(s) from "
              f"legends in the text; {how} ({time.time() - t0:.1f}s)")

        # The grouped measurements carry the CANONICAL type name (canonicalize
        # renames e.g. 'FG' -> 'functional groups'), but col_codes/hints are keyed
        # by the raw header. Key the legend by the canonicalType so it matches the
        # measurementType looked up at rewrite time below; otherwise a decoded
        # legend is silently never applied whenever the type was renamed.
        canon_of = {clean_text(h): clean_text(m.get("canonicalType") or h)
                    for h, m in mapping.items()}

        # merge: LLM wins, fall back to deterministic footnote term
        legend_by_col = {}
        for c, codes in col_codes.items():
            merged = dict(hints.get(c, {}))
            merged.update(llm_legends.get(c, {}))   # LLM overrides footnote casing/wording
            if merged:
                legend_by_col[canon_of.get(c, c)] = merged

        # persist resolved legends into the mapping for traceability
        for header, m in mapping.items():
            leg = legend_by_col.get(clean_text(m.get("canonicalType") or header))
            if leg:
                m["valueDecode"] = leg

        # rewrite the codes in grouped (match on cleaned measurementType)
        for species_data in grouped.values():
            expanded = []
            for meas in species_data.get("measurements", []):
                leg = legend_by_col.get(clean_text(meas.get("measurementType", "")))
                if leg and isinstance(meas.get("measurementValue"), str):
                    parts = _legend_code_list(meas["measurementValue"], leg)
                    if parts:
                        # 'Sub/Lit' = two states (Pereira2016): one measurement each
                        for p in parts:
                            expanded.append({**meas, "measurementValue": apply_legend(p, leg)})
                        continue
                    meas["measurementValue"] = apply_legend(meas["measurementValue"], leg)
                expanded.append(meas)
            if "measurements" in species_data:
                species_data["measurements"] = expanded

    Path(grouped_path).write_text(json.dumps(grouped, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  decoded values in {grouped_path}")
    return grouped