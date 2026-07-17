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

def get_measurement_level_tags(table_mapping, paper_chunks, llm=None):
    for header, mapping in table_mapping.items():
        if mapping.get("field") == "verbatimIdentification" or mapping.get("category") is None:
            continue
        is_categorical = mapping.get("value_type") == "categorical"
        # basisOfRecord is measurement-dependent (morphology -> PreservedSpecimen,
        # behaviour/ecology -> HumanObservation), so it is decided per column here
        # rather than once for the whole paper.
        tags = ["basisOfRecord", "measurementMethod"] if is_categorical else \
               ["basisOfRecord", "measurementMethod", "measurementUnit", "measurementStatistic"]
        tags = [t for t in tags if not mapping.get(t)]
        if not tags:
            continue
        print(f"  column '{header}' ({'cat' if is_categorical else 'num'}) -> {tags}")
        results = agent_define_multi_tags(f"the column '{header}'", tags, paper_chunks, llm=llm)
        for tag, result in results.items():
            value = result.get("value")
            if not _is_empty_like(value):
                mapping[tag] = value
                mapping[f"{tag}_reasoning"] = result.get("reasoning")
    return table_mapping


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
    """{clean_header: sorted distinct codes} for relevant categorical columns."""
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
    """LLM decoder for value codes — but only for codes the deterministic footnote
    parse did NOT already resolve, and stopping as soon as every code is filled.

    Previously this looped over every text chunk and called the LLM once per
    chunk for ALL codes, even codes the footnotes had already defined — so a
    paper with clean footnote legends still paid N big-context LLM calls per
    table. Now: (1) seed results from `hints` (deterministic, free); (2) compute
    the leftover undefined codes; (3) if none remain, return with ZERO LLM calls;
    (4) otherwise ask the LLM only about leftovers, and break the chunk loop the
    moment all leftovers are resolved.
    """
    if not col_codes:
        return {}

    # (1) seed from deterministic footnote hints — these are free and trusted.
    merged = {c: {} for c in col_codes}
    hints = hints or {}
    for c, codes in col_codes.items():
        hint_map = hints.get(c, {}) or {}
        for code in codes:
            v = hint_map.get(code, hint_map.get(code.lower()))
            if not _is_empty_like(v):
                merged[c][code] = v

    # (2) leftovers = codes still undefined after hints
    def leftovers():
        return {c: [code for code in codes if _is_empty_like(merged[c].get(code))]
                for c, codes in col_codes.items()}
    left = {c: codes for c, codes in leftovers().items() if codes}

    # (3) nothing left for the LLM — return immediately, no calls.
    if not left:
        return {c: {k: v for k, v in m.items() if not _is_empty_like(v)}
                for c, m in merged.items()}

    # (4) ask the LLM only about leftover codes; stop once they're all resolved.
    cols_desc = "\n".join(f'- "{c}": codes {codes}' for c, codes in left.items())
    hints_desc = json.dumps(hints, ensure_ascii=False, indent=2) if hints else "{}"
    system = f"""A scientific table uses short codes in several columns. The codes are
defined in the table's footnotes/legend/surrounding text. The SAME letter can
mean different things in different columns, so resolve each column independently.
For each code, return a CLEAN CANONICAL label for what it stands for:
- a short noun phrase in sentence case (e.g. "Wood", "Standing dead wood",
  "Found in mounds of other termites");
- use the paper's own term when it is already a clean label; otherwise lightly
  normalise it (fix casing, expand obvious abbreviations);
- do NOT append words derived from the column name ("feeders", "nesting"),
  do NOT pluralise, and do NOT write a full sentence;
- if you truly cannot determine the meaning from the text, return null.
Columns and the exact codes appearing in each:
{cols_desc}
Legend pairs already recovered from the footnotes (treat as ground truth to
clean up, not to override with guesses):
{hints_desc}
Return ONLY a JSON object: {{"<column>": {{"<code>": "<canonical label or null>"}}}}"""

    for chunk in chunks:
        try:
            msgs = [{"role": "system", "content": system},
                    {"role": "user", "content": f"Here is the text:\n{chunk['content']}"}]
            content = llm.invoke(msgs).content if llm else invoke_sized(msgs)
            parsed = json.loads(content)
        except (json.JSONDecodeError, AttributeError):
            continue
        if not isinstance(parsed, dict):
            continue
        for c, codes in left.items():
            got = parsed.get(c) if isinstance(parsed.get(c), dict) else {}
            for code in codes:
                if _is_empty_like(merged[c].get(code)) and not _is_empty_like(got.get(code)):
                    merged[c][code] = got[code]
        # stop as soon as no leftovers remain
        if not any(codes for codes in
                   ({c: [k for k in cs if _is_empty_like(merged[c].get(k))]
                     for c, cs in left.items()}).values()):
            break

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

        # merge: LLM wins, fall back to deterministic footnote term
        legend_by_col = {}
        for c, codes in col_codes.items():
            merged = dict(hints.get(c, {}))
            merged.update(llm_legends.get(c, {}))   # LLM overrides footnote casing/wording
            if merged:
                legend_by_col[c] = merged

        # persist resolved legends into the mapping for traceability
        for header, m in mapping.items():
            leg = legend_by_col.get(clean_text(header))
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