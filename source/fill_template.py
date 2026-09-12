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
import re
from pathlib import Path

from text_manager import get_tables
from tables import parse_table, parse_legends_from_text, apply_legend, clean_text
from column_relevance import make_llm, invoke_sized

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "template_descriptions"
_EMPTY_LIKE = {None, "", "null", "none", "unknown"}


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
            msgs = tag_finder_msg_builder_multi(target, tags, chunk["content"])
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
        present = [m[tag] for m in cols if not _is_empty_like(m.get(tag))]
        missing = [m for m in cols if _is_empty_like(m.get(tag))]
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
    text = "\n\n".join(c["content"] for c in chunks) if chunks else ""
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
    text = "\n\n".join(c["content"] for c in chunks) if chunks else ""
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
        content = llm.invoke(msgs).content if llm else invoke_sized(msgs)
        parsed = json.loads(content)
    except (json.JSONDecodeError, AttributeError):
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


def decode_grouped_values(grouped_path, tables, paper_text, chunks, mappings, llm=None):
    """Decode table codes to canonical labels and rewrite grouped in place.

    Strategy: recover the footnote legend deterministically as *grounding*, then
    let the LLM produce the canonical label for every code (it reads the
    annotation and normalises). Resolution order per code:
        LLM canonical label  ->  deterministic footnote term  ->  raw code.
    """
    from table_to_data import table_id  # local import avoids a cycle at module load

    grouped = json.loads(Path(grouped_path).read_text(encoding="utf-8"))

    for table in tables:
        mapping = mappings.get(table_id(table))
        if not mapping:
            continue

        # deterministic footnote legend = grounding hints for the LLM
        hints = parse_legends_from_text(paper_text, table)
        hints = {clean_text(k): v for k, v in hints.items()}

        # LLM normalises every code (grounded on the hints)
        col_codes = collect_categorical_codes(table, mapping)
        llm_legends = agent_normalize_legends(col_codes, hints, chunks, llm=llm)

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
            for meas in species_data.get("measurements", []):
                leg = legend_by_col.get(clean_text(meas.get("measurementType", "")))
                if leg and isinstance(meas.get("measurementValue"), str):
                    meas["measurementValue"] = apply_legend(meas["measurementValue"], leg)

    Path(grouped_path).write_text(json.dumps(grouped, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  decoded values in {grouped_path}")
    return grouped