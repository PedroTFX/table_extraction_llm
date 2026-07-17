"""
table_to_data.py — map tables to the template and group measurements by species.

Refactor notes
--------------
* All table access goes through ``tables.Table`` (aligned records). The old
  ``headers.index(header)`` join is gone, so blank/merged header cells and
  footnote/nbsp drift between the LLM mapping keys and the physical headers can
  no longer desync columns — that was the "only some lines have a value" bug.
* The LLM agents are now *pure*: they take inputs and return data. File IO and
  orchestration live in the pipeline, which makes them testable and lets the
  same mapper run over a paper's complementary files.
* ``build_grouped`` merges measurements from *all* tables (main + complementary)
  into one species-keyed dict, so a species split across files is unified.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Iterable, Optional

from tables import Table, parse_table, clean_text, find_abbreviation_definitions
from text_manager import get_tables, xlsx_to_table, csv_to_table
from column_relevance import agent_define_columns_relevance, make_llm, invoke_sized

MODEL = "gemma4:e4b-it-qat"

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "template_descriptions"
MAP_FIELDS = ["verbatimIdentification", "measurementType",
              "measurementMethod", "measurementStatistic"]


def get_tag_explanation(tag: str) -> str:
    return (TEMPLATE_DIR / f"{tag}.md").read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Table collection across the whole document set (paper + complementary files)
# ---------------------------------------------------------------------------

def tables_from_text(text: str, source: str) -> list[Table]:
    return [parse_table(t["content"], source=source, table_index=i)
            for i, t in enumerate(get_tables(text))]


def collect_tables(sources: Iterable) -> list[Table]:
    """Gather tables from a list of files, tagged with provenance.

    Supported: .md/.html/.htm/.txt (MinerU output, may hold several tables),
    .xlsx/.xls (one sheet -> one table), .csv/.tsv. Complementary files are
    just more entries in ``sources``.
    """
    out: list[Table] = []
    for src in sources:
        p = Path(src)
        ext = p.suffix.lower()
        if ext in {".md", ".html", ".htm", ".txt"}:
            text = p.read_text(encoding="utf-8", errors="replace")
            out.extend(tables_from_text(text, source=p.name))
        elif ext in {".xlsx", ".xls"}:
            out.append(parse_table(xlsx_to_table(str(p)), source=p.name, table_index=0))
        elif ext in {".csv", ".tsv"}:
            text = p.read_text(encoding="utf-8", errors="replace")
            out.append(parse_table(csv_to_table(text), source=p.name, table_index=0))
        else:
            print(f"  (skipping unsupported file type: {p.name})")
    return out


def table_id(table: Table) -> str:
    stem = Path(table.source).stem if table.source else "table"
    return f"{stem}__table_{table.table_index}"


# ---------------------------------------------------------------------------
# Structural decomposition (LLM) — runs BEFORE mapping
# ---------------------------------------------------------------------------
#
# Some tables are "banded": a flat grid that actually stacks several logical
# sub-tables, e.g. trait names sitting in a header band with the specimen/family
# rows beneath, or a blank-header row-label column carrying the identifier. The
# per-column mapper cannot fix this — by the time we look at one column the
# structure is already baked in. So a structure-only agent looks at each raw
# table and, IF it is banded, rewrites it into one or more clean
# `identifier x trait` pipe-grids. Clean tables pass through unchanged.
#
# This agent judges STRUCTURE ONLY. Whether a (clean) table is trait data vs
# statistics is still decided downstream by the per-column relevance agent, so
# we never duplicate that judgment here.
#
# A deterministic data-preservation guard protects already-good tables: if the
# decomposition drops or alters any non-empty data cell, we discard the agent
# output and keep the original table.

def _table_to_grid(table: Table) -> str:
    """Render a parsed Table back to a simple pipe-grid string (header + rows)."""
    header = "| " + " | ".join(c.raw for c in table.columns) + " |"
    lines = [header]
    for rec in table.records:
        cells = [rec.get(c.name, "") for c in table.columns]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _data_cell_multiset(table: Table) -> "Counter":
    """Multiset of non-empty data-cell values (order-independent), for the guard."""
    from collections import Counter
    bag: Counter = Counter()
    for rec in table.data_records():
        for c in table.columns:
            v = (rec.get(c.name) or "").strip()
            if v:
                bag[v] += 1
    return bag


def agent_decompose_table(table: Table, paper_text: str, llm=None) -> list[Table]:
    """Return a list of clean sub-tables for `table`. If the table is already
    clean (a simple identifier x trait grid) the agent returns it unchanged and
    we yield the original. If banded, the agent rewrites it into one or more
    clean pipe-grids, which we re-parse. A data-preservation guard discards any
    rewrite that loses or mutates data cells.
    """
    grid = _table_to_grid(table)
    # cheap skip: tiny tables can't be banded meaningfully
    if len(table.records) < 2 or len(table.columns) < 2:
        return [table]

    # Option 3 — salvage mode only: if the table ALREADY has a column that looks
    # like a usable identifier (mostly non-numeric organism-name-ish text, with a
    # non-blank header), it is a clean identifier x trait grid and must NOT be
    # decomposed. Decomposition exists to rescue banded tables whose identifier is
    # missing/blank-headered; running it on clean tables only risks corruption.
    for col in table.columns:
        if getattr(col, "synthetic", False):
            continue
        if not (col.name or "").strip():
            continue  # blank header -> not a clean identifier, allow decomposition
        if _looks_like_identifier_column(table, col.name):
            return [table]

    system = (
        "You normalize the STRUCTURE of a data table. You are given one raw "
        "table (pipe-delimited) from a scientific paper. Some tables are "
        "'banded': a flat grid that actually stacks several logical sub-tables — "
        "for example trait names sitting in a header band with the "
        "specimen/taxon rows beneath them, or a row-label (identifier) column "
        "whose header cell is blank, or repeated section-header rows.\n\n"
        "Your ONLY job is STRUCTURE. Decide:\n"
        "- If the table is already a clean grid (one identifier column + trait "
        "columns), return it UNCHANGED.\n"
        "- If it is banded/multi-section, rewrite it into one or more CLEAN "
        "pipe-grids, each with a proper header row where the first column is the "
        "identifier (taxon/specimen/family) and the remaining columns are the "
        "measurements. Give the identifier column a real header name if it was "
        "blank (e.g. 'Taxon'). Preserve EVERY data value exactly as written — do "
        "not invent, drop, reformat, split, or merge any value.\n"
        "- Do NOT judge whether the data is statistical or biological; that is "
        "decided elsewhere. Only fix structure.\n\n"
        "Return ONLY JSON: {\"tables\": [\"<pipe-grid-1>\", \"<pipe-grid-2>\", "
        "...]}. Each string is a full table with a header line and data lines, "
        "rows separated by \\n, cells by ' | '. If unchanged, return the single "
        "original grid."
    )
    user = ("Raw table:\n" + grid +
            "\n\n(Context from the paper, for understanding the table only:)\n"
            + paper_text[:4000])

    try:
        content = (llm.invoke([{"role": "system", "content": system},
                               {"role": "user", "content": user}]).content
                   if llm else
                   invoke_sized([{"role": "system", "content": system},
                                 {"role": "user", "content": user}]))
        data = json.loads(content)
        grids = data.get("tables") if isinstance(data, dict) else None
    except (json.JSONDecodeError, AttributeError, TypeError):
        grids = None

    if not grids or not isinstance(grids, list):
        return [table]

    # re-parse each returned grid
    subs: list[Table] = []
    for i, g in enumerate(grids):
        if not isinstance(g, str) or "|" not in g:
            continue
        try:
            t = parse_table(g, source=table.source,
                            table_index=table.table_index * 100 + i)
            if t.header_names and t.data_records():
                subs.append(t)
        except Exception:
            continue
    if not subs:
        return [table]

    # Option 1 — only accept a genuine SPLIT. If the agent returned a single
    # sub-table, it did not actually decompose anything (it just rewrote the
    # table, which risks corrupting headers, e.g. appending ' ---' junk or
    # renaming columns). In that case keep the ORIGINAL table untouched.
    if len(subs) < 2:
        return [table]

    # DATA-PRESERVATION GUARD: the union of sub-table data cells must contain
    # every data cell of the original (no loss, no mutation). Decomposition may
    # legitimately DUPLICATE an identifier across sub-tables, so we require
    # superset-or-equal on the original's multiset, not exact equality.
    from collections import Counter
    orig = _data_cell_multiset(table)
    out_bag: Counter = Counter()
    for t in subs:
        out_bag += _data_cell_multiset(t)
    missing = orig - out_bag   # values present in orig but not covered by output
    if missing:
        print(f"    decompose: discarded (would lose {sum(missing.values())} "
              f"cell(s)); keeping original {table_id(table)}")
        return [table]

    if len(subs) == 1 and _data_cell_multiset(subs[0]) == orig and \
            len(subs[0].columns) == len(table.columns):
        # effectively unchanged
        return [table]

    print(f"    decompose: {table_id(table)} -> {len(subs)} clean sub-table(s)")
    return subs


# ---------------------------------------------------------------------------
# Column mapping (LLM) — pure functions, return dicts
# ---------------------------------------------------------------------------

def classify_value_types(table: Table, mapping: dict) -> dict:
    for header, m in mapping.items():
        if m.get("field") == "verbatimIdentification" or m.get("category") is None:
            continue
        values = [v for v in table.column_values(header) if v != ""]
        if not values:
            m["value_type"] = "categorical"
            continue
        numeric = 0
        for v in values:
            try:
                float(v)
                numeric += 1
            except ValueError:
                pass
        m["value_type"] = "numeric" if numeric >= len(values) * 0.7 else "categorical"
    return mapping


def agent_table_mapper(table: Table, paper_text: str, llm=None) -> dict:
    """Map a table's headers to template fields and merge in column relevance.
    Returns the mapping dict (no file IO). Context is sized to the prompt."""
    headers = table.header_names

    descs = {t: get_tag_explanation(t) for t in
             ["verbatimIdentification", "measurementType", "measurementValue",
              "measurementMethod", "measurementStatistic"]}
    sample = [{h: r[h] for h in headers} for r in table.data_records()[:6]]

    prompt = f"""You're mapping a scientific table to a fixed template.

Template fields:
- verbatimIdentification: {descs['verbatimIdentification']}
- measurementType: {descs['measurementType']}
- measurementValue: {descs['measurementValue']}
- measurementMethod: {descs['measurementMethod']}
- measurementStatistic: {descs['measurementStatistic']}

Table headers: {headers}
Sample rows: {sample}

For each header, return an object with:
- field: one of {MAP_FIELDS}
- value_column: true if this column holds measurement values (numeric or
  categorical). Taxonomic identities are NOT values, so verbatimIdentification
  always has value_column=false.
- reasoning: brief justification grounded in the header and its values.
Return ONLY a JSON object keyed by header name."""

    print(f"  Mapping table {table.source}#{table.table_index} ({len(headers)} cols)")
    content = llm.invoke(prompt).content if llm else invoke_sized(prompt)
    mapping = json.loads(content)

    start = time.perf_counter()
    relevance = agent_define_columns_relevance(headers, paper_text)
    print(f"  relevance check: {time.perf_counter() - start:.1f}s")
    for header, rel in relevance.items():
        if header in mapping and isinstance(mapping[header], dict):
            rel = rel if isinstance(rel, dict) else {}
            mapping[header]["category"] = rel.get("category")
            mapping[header]["reasoning_relevance"] = rel.get("reasoning", "not found in text")

    return classify_value_types(table, mapping)


# ---------------------------------------------------------------------------
# Grouping — row-major over aligned records, no index math
# ---------------------------------------------------------------------------

_GROUP_LABEL_RE = re.compile(r"^\s*group\b", re.IGNORECASE)   # 'Group 2', 'Group 3a'


def _looks_like_identifier_column(table: Table, col_name: str) -> bool:
    """A genuine identifier column (species/specimen) is mostly non-numeric text
    that names organisms. Guards against numeric columns and against analysis
    'Group N' label columns being mistaken for specimen identities. The primary
    organism-vs-place/group judgement lives in the verbatimIdentification
    template description; this is a light structural backstop."""
    vals = [v.strip() for v in table.column_values(col_name) if v and v.strip()]
    if not vals:
        return False
    nonnumeric = 0
    group_labels = 0
    for v in vals:
        if _GROUP_LABEL_RE.match(v):
            group_labels += 1
        try:
            float(v.replace("±", " ").split()[0]) if v else None
            # parsed as number -> looks numeric, don't count
        except (ValueError, IndexError):
            nonnumeric += 1
    # if most populated cells are 'Group N' labels, this isn't an organism column
    if group_labels >= max(1, len(vals) // 2 + 1):
        return False
    # majority of populated cells should be non-numeric text to be an identifier
    return nonnumeric >= max(1, len(vals) // 2 + 1)


def _identifier_column(table: Table, mapping: dict) -> Optional[str]:
    """Return the column confidently mapped to verbatimIdentification, or None.

    No first-column fallback: a table without a real identifier column produces
    NO specimen rows. This is general and fails safe — it drops stats/summary
    tables (GLMM coefficients, etc.) that have no taxon column, while keeping any
    trait table that does, regardless of the table's specific layout."""
    for header, m in mapping.items():
        if m.get("field") == "verbatimIdentification":
            col = table.resolve(header)
            if col is not None and _looks_like_identifier_column(table, col.name):
                return col.name
    return None


def add_table_to_grouped(table: Table, mapping: dict, grouped: dict) -> dict:
    id_col = _identifier_column(table, mapping)
    if id_col is None:
        print(f"    skip table {table.source}#{table.table_index} — "
              f"no identifier (verbatimIdentification) column; not specimen data")
        return grouped

    kept = []
    for header, m in mapping.items():
        if m.get("field") == "verbatimIdentification":
            continue
        if m.get("category") is None:
            print(f"    skip '{header}' — {m.get('reasoning_relevance', 'not relevant')}")
            continue
        col = table.resolve(header)
        if col is None:
            print(f"    skip '{header}' — not found in this table")
            continue
        kept.append((col.name, m))

    # Require at least one surviving trait column. A table that has an identifier
    # column but ZERO relevant trait columns is not specimen data — it is a
    # metadata/admin/statistics table whose "identifier" is really a study code,
    # author citation, or reference (e.g. Boetzl's 'Reference' and 'Study ID'
    # columns get mis-mapped to verbatimIdentification and otherwise emit garbage
    # rows). Dropping it here fails safe: a real trait table always has >=1 column
    # the relevance check accepted (a non-null category).
    if not kept:
        print(f"    skip table {table.source}#{table.table_index} — "
              f"identifier present but no relevant trait columns; not specimen data")
        return grouped

    for rec in table.data_records():
        species = rec.get(id_col, "").strip()
        if not species:
            continue
        entry = grouped.setdefault(species, {
            "verbatimIdentification": species,
            "measurements": [],
        })
        for col_name, m in kept:
            value = rec.get(col_name, "")
            meas = {
                "measurementType": m.get("canonicalType", col_name),
                "measurementValue": value if value != "" else None,
            }
            # statistic + sample size are set by the canonicalize step on the
            # column mapping; the statistic is column-constant, the sample size
            # is read per row from the linked count column in this table.
            stat = m.get("measurementStatistic")
            if stat:
                meas["measurementStatistic"] = stat
            size_col = m.get("sampleSizeColumn")
            if size_col:
                sv = (rec.get(size_col, "") or "").strip()
                if sv:
                    meas["sampleSizeValue"] = sv
            entry["measurements"].append(meas)
    return grouped


def _apply_glossary(header: str, glossary: dict) -> str:
    """Deterministically expand abbreviations in `header` using `glossary`
    (abbrev -> full term), matching ONLY whole tokens (word boundaries), then
    drop a single trailing unit parenthetical. The model never rewrites the
    header itself — code controls exactly what changes, so a header with no
    known abbreviation is returned byte-for-byte (minus a trailing unit)."""
    name = header
    for abbr, full in glossary.items():
        if not abbr or not isinstance(full, str) or not full.strip():
            continue
        # whole-token, case-sensitive match (acronyms like CTM/MAT/ITS are caps)
        pattern = r"(?<![\w])" + re.escape(abbr) + r"(?![\w])"
        name = re.sub(pattern, full.strip(), name)
    # drop a single trailing unit parenthetical: '... (ºC)' / '... (mm)'
    name = re.sub(r"\s*\([^()]*\)\s*$", "", name).strip()
    return name or header


# Canonical statistic vocabulary. IMPORTANT: this only NORMALISES a label the
# model already chose in context (so 'avg' and 'average' both surface as 'mean'
# in the CSV). It does NOT decide whether a header carries a statistic — that
# judgement is the LLM's, with the paper in view. There is deliberately no
# header-matching statistic dictionary anywhere; that approach mis-split real
# trait names like 'Range size'.
_STATISTIC_VOCAB = {
    "mean": "mean", "average": "mean", "avg": "mean", "x̄": "mean",
    "median": "median",
    "mode": "mode",
    "sd": "standard deviation", "std": "standard deviation",
    "stdev": "standard deviation", "standard deviation": "standard deviation",
    "se": "standard error", "sem": "standard error",
    "standard error": "standard error",
    "min": "minimum", "minimum": "minimum",
    "max": "maximum", "maximum": "maximum",
    "range": "range",
    "sum": "sum", "total": "sum",
    "count": "count",
}


def _normalize_statistic(label) -> Optional[str]:
    """Map the model's free-form statistic label onto a canonical output term,
    or None if it is not a statistic we record."""
    if not isinstance(label, str):
        return None
    key = label.strip().lower().rstrip(".")
    return _STATISTIC_VOCAB.get(key) or _STATISTIC_VOCAB.get(key.replace(".", ""))


def _strip_leading_token(text: str, token: str) -> Optional[str]:
    """If `text` begins with `token` as a whole token (case-insensitive), return
    `text` with that leading token — and any immediately following 'of'/separator
    — removed; else None. Leading-only and whole-token, so a trait whose name
    merely CONTAINS the word (e.g. 'range size') is never altered here; the
    caller only reaches this when the LLM has flagged a genuine leading prefix."""
    token = (token or "").strip()
    if not token:
        return None
    m = re.match(r"\s*" + re.escape(token) + r"(?![\w])\s*", text, flags=re.IGNORECASE)
    if not m:
        return None
    rest = text[m.end():]
    rest = re.sub(r"^(of\b\s*|[-\u2013\u2014:,]\s*)", "", rest, flags=re.IGNORECASE).strip()
    return rest or None


_SAMPLE_SIZE_RE = re.compile(
    r"^(n|nº|no\.?)$|sample\s*size|number\s+of\b|no\.?\s+of\b|\bcount\b|\bn\s*=",
    re.IGNORECASE,
)


def _find_sample_size_column(mapping: dict) -> Optional[str]:
    """Conservatively locate a sample-size column in ONE table's mapping, to link
    as the sampleSize source for aggregate (mean/median/...) columns in that same
    table. Header-keyword based and low-collision: bare 'n'/'N', 'sample size',
    'number of <x>'. Returns the raw header or None; when in doubt, None (and the
    aggregate simply carries no sampleSizeValue)."""
    for header in mapping:
        if _SAMPLE_SIZE_RE.search(clean_text(header)):
            return header
    return None


def _is_acronym(k: str) -> bool:
    """True for short ACRONYM-like tokens (ITD, CTM, MAT): 2-6 chars, >=2
    uppercase, no spaces, at least as many uppercase as lowercase. Keeps ordinary
    words ('N', 'Daily', 'Month') out of the glossary and out of token scanning."""
    if not isinstance(k, str) or not (1 < len(k) <= 6) or " " in k:
        return False
    uppers = sum(c.isupper() for c in k)
    lowers = sum(c.islower() for c in k)
    return uppers >= 2 and uppers >= lowers


def agent_canonicalize_measurement_types(mappings: dict, paper_text: str, llm=None) -> dict:
    """One whole-paper LLM call that does the measurementType name-cleanup AND
    the statistic detection in a single place (no separate regex pass).

    The model returns two things:
      * glossary {ABBREV -> full term} — applied deterministically, exactly as
        before (the model never emits the final type string, so a weak local
        model still cannot reword 'Daily rhythm' into 'Daily activity rhythm');
      * per column, whether the header carries a leading summary-statistic word
        ('mean ITD', 'Median body length', 'SD of mass') and the EXACT leading
        token, decided WITH the paper in context so a trait whose name contains
        a statistic-ish word ('Range size') is not mis-split.

    Code then expands abbreviations and, only when the model flagged a real
    leading token, removes that token to get the base canonicalType and records
    measurementStatistic (+ a sample-size source column, if the table has one).
    Writes 'canonicalType' (always) and 'measurementStatistic'/'sampleSizeColumn'
    (when an aggregate) into each measurementType mapping entry in place.
    """
    headers = []
    for mapping in mappings.values():
        for header, m in mapping.items():
            if m.get("field") == "measurementType" and m.get("category") is not None:
                if header not in headers:
                    headers.append(header)
    if not headers:
        return mappings

    # --- deterministic, paper-grounded abbreviation resolution (runs FIRST) ----
    # Pull acronym-looking tokens out of the measurementType headers, then resolve
    # each from the paper text deterministically (two shapes today: 'full term
    # (ABBR)' and 'ABBR =/:/, term'). These hits are verbatim from the paper, so
    # they are trusted; the LLM is only asked about whatever is left over.
    header_tokens = []
    for h in headers:
        for tok in re.findall(r"[A-Za-z][A-Za-z./]*", h):
            t = tok.strip("./")
            if _is_acronym(t) and t not in header_tokens:
                header_tokens.append(t)

    found = find_abbreviation_definitions(paper_text, header_tokens)
    seed_glossary = {tok: info["term"] for tok, info in found.items()}
    leftovers = [t for t in header_tokens if t not in seed_glossary]

    if header_tokens:
        if found:
            print("  abbreviations resolved from text (deterministic):")
            for tok, info in found.items():
                print(f"    {tok} -> {info['term']}  [{info['shape']}]")
        else:
            print("  abbreviations resolved from text (deterministic): none")
        print(f"  abbreviations handed to the LLM: {leftovers or 'none'}")

    system = (
        "You analyse the measurement-type column names of ONE scientific paper "
        "and return JSON with two parts.\n\n"
        "(1) glossary: genuine abbreviations/acronyms that appear AS A TOKEN in "
        "the column names AND are explicitly defined in the paper text, mapped to "
        "the paper's own full term. Examples: column 'CTM (ºC)' with paper text "
        "'Critical thermal maximum (CTM)' -> {\"CTM\": \"Critical thermal "
        "maximum\"}. Keys must be acronym tokens that literally appear (CTM, MAT, "
        "ITS, ITD, TL). Values are the paper's own full term, nothing invented. "
        "Do NOT include ordinary words ('N', 'Daily', 'Month', 'Defense'). If "
        "there are no abbreviations, use {}.\n\n"
        "(2) columns: for EACH column name, decide whether the name begins with a "
        "summary-STATISTIC word describing how the values were aggregated across "
        "specimens — mean/average, median, mode, SD/standard deviation, "
        "SE/standard error, min/minimum, max/maximum, range, sum, count. Use the "
        "paper for context. Flag it ONLY when the word is genuinely a statistic "
        "applied to a trait (e.g. 'mean ITD', 'Median body length', 'SD of "
        "mass'), NOT when the word is part of the trait's OWN name (e.g. 'Range "
        "size' is a trait, not a 'range' statistic; a column called just "
        "'Maximum temperature' may be the trait itself). When a statistic IS "
        "present, return its canonical name and the EXACT leading substring "
        "(token) as written in the column name, so it can be removed. Otherwise "
        "return null for both.\n\n"
        "Return ONLY JSON in this exact shape:\n"
        "{\n"
        '  \"glossary\": {\"<ABBREV>\": \"<full term>\", ...},\n'
        '  \"columns\": {\n'
        '    \"<exact column name>\": {\"statistic\": \"<canonical name or '
        'null>\", \"token\": \"<exact leading substring or null>\"},\n'
        "    ...\n"
        "  }\n"
        "}"
    )
    if seed_glossary:
        system += ("\n\nThese abbreviations are ALREADY resolved from the paper "
                   "text and are GROUND TRUTH \u2014 reuse them as-is, do not "
                   "redefine or alter them:\n"
                   + json.dumps(seed_glossary, ensure_ascii=False, indent=2))
        if leftovers:
            system += ("\n\nFor the glossary, only try to define these still-"
                       "unresolved acronym tokens, and only if the text defines "
                       "them: " + json.dumps(leftovers, ensure_ascii=False))
        else:
            system += ("\n\nNo other abbreviations need defining; return "
                       '\"glossary\" as {}. Still complete the per-column '
                       "statistic analysis below.")
    user = ("Column names:\n" + json.dumps(headers, ensure_ascii=False, indent=2)
            + "\n\nPaper text:\n" + paper_text)

    try:
        content = (llm.invoke([{"role": "system", "content": system},
                               {"role": "user", "content": user}]).content
                   if llm else
                   invoke_sized([{"role": "system", "content": system},
                                 {"role": "user", "content": user}]))
        parsed = json.loads(content)
    except (json.JSONDecodeError, AttributeError):
        print("  canonicalize: malformed response; keeping raw names")
        parsed = {}
    if not isinstance(parsed, dict):
        parsed = {}

    # Tolerate the older/looser shape (a bare {ABBREV: full} glossary with no
    # 'glossary'/'columns' wrapper) so the step degrades gracefully.
    if "glossary" in parsed or "columns" in parsed:
        glossary = parsed.get("glossary") or {}
        columns = parsed.get("columns") or {}
    else:
        glossary, columns = parsed, {}
    if not isinstance(glossary, dict):
        glossary = {}
    if not isinstance(columns, dict):
        columns = {}

    # Safety filter: keep only true ACRONYM-like keys so an over-eager model can't
    # smuggle ordinary words ('N', 'Daily', 'Month') into the glossary.
    glossary = {k: v for k, v in glossary.items() if _is_acronym(k)}
    # Deterministic, paper-verbatim seeds win over anything the LLM proposed.
    glossary.update(seed_glossary)

    n = 0
    n_stat = 0
    for mapping in mappings.values():
        # one sample-size column per table, linked to that table's aggregates
        size_col = _find_sample_size_column(mapping)
        for header, m in mapping.items():
            if not (m.get("field") == "measurementType" and m.get("category") is not None):
                continue
            expanded = _apply_glossary(header, glossary)
            info = columns.get(header) if isinstance(columns.get(header), dict) else {}
            stat = _normalize_statistic(info.get("statistic"))
            token = info.get("token")
            canonical = expanded
            if stat and token:
                stripped = _strip_leading_token(expanded, token)
                # accept the split only if the token truly LEADS the raw header
                # (the model can't invent a prefix that isn't there) and removing
                # it leaves a non-empty trait name.
                if stripped and _strip_leading_token(header, token) is not None:
                    canonical = stripped
                    m["measurementStatistic"] = stat
                    if size_col:
                        m["sampleSizeColumn"] = size_col
                    n_stat += 1
            m["canonicalType"] = canonical
            if canonical != header:
                n += 1
    llm_keys = [k for k in glossary if k not in seed_glossary]
    print(f"  canonicalized {n} measurementType name(s); detected statistic on "
          f"{n_stat} column(s); glossary "
          f"[from text: {list(seed_glossary) or 'none'}; "
          f"from LLM: {llm_keys or 'none'}]")
    return mappings

def build_grouped(tables: list, mappings: dict) -> dict:
    grouped: dict = {}
    for table in tables:
        mapping = mappings.get(table_id(table))
        if mapping:
            add_table_to_grouped(table, mapping, grouped)
    return grouped


# ---------------------------------------------------------------------------
# Convenience orchestration
# ---------------------------------------------------------------------------

def map_and_group(sources, paper_text, out_dir=".", llm=None):
    out_dir = Path(out_dir)
    sources = list(sources)
    tables = collect_tables(sources)
    print(f"Collected {len(tables)} table(s) from {len(sources)} file(s)")

    # Structural decomposition pass: rewrite banded/multi-section tables into
    # clean identifier x trait sub-tables BEFORE mapping. Clean tables pass
    # through unchanged (guarded against data loss).
    print("  Checking table structure (decomposition)...")
    decomposed: list[Table] = []
    for table in tables:
        decomposed.extend(agent_decompose_table(table, paper_text, llm=llm))
    tables = decomposed
    print(f"  {len(tables)} table(s) after decomposition")

    mappings: dict = {}
    for table in tables:
        if not table.header_names:
            continue
        mapping = agent_table_mapper(table, paper_text, llm=llm)
        tid = table_id(table)
        mappings[tid] = mapping
        (out_dir / f"{tid}_mapping.json").write_text(
            json.dumps(mapping, indent=2, ensure_ascii=False), encoding="utf-8")

    # canonicalize measurementType names across the whole paper (one call):
    # expand abbreviations from the paper, drop unit suffixes
    print("  Canonicalizing measurementType names...")
    agent_canonicalize_measurement_types(mappings, paper_text, llm=llm)
    # re-persist mappings now that canonicalType is set
    for tid, mapping in mappings.items():
        (out_dir / f"{tid}_mapping.json").write_text(
            json.dumps(mapping, indent=2, ensure_ascii=False), encoding="utf-8")

    grouped = build_grouped(tables, mappings)
    return grouped, tables, mappings


if __name__ == "__main__":
    main = "Abensperg-Traun M. (1991).md"
    paper_text = Path(main).read_text(encoding="utf-8")
    sources = [main]  # add complementary files here, e.g. "..._S1.xlsx"
    grouped, tables, mappings = map_and_group(sources, paper_text)
    json.dump(grouped, open("grouped_by_species.json", "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print(f"Grouped {len(grouped)} species")