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

import copy
import json
import re
import time
from pathlib import Path
from typing import Iterable, Optional

from tables import (Table, parse_table, clean_text, find_abbreviation_definitions,
                    find_binomial_candidates,
                    is_headerless_continuation)
from text_manager import get_tables, xlsx_to_table, csv_to_table
from column_relevance import (agent_define_columns_relevance, make_llm,
                              invoke_sized, loads_salvaging)

MODEL = "gemma4:e4b-it-qat"

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "template_descriptions"
# The ONE place to add/remove a mappable tag. Each name needs a matching
# <name>.md in template_descriptions/. The mapper prompt (field list + per-tag
# descriptions) is generated from this list, so adding a tag = add it here (and
# drop in its .md); removing one = delete the line. Nothing else to touch.
MAP_FIELDS = [
    "verbatimIdentification",
    "verbatimLocality",
    "measurementType",
    "measurementValue",
    "measurementMethod",
    "measurementStatistic",
]

# Fields that flag a DATA DICTIONARY / KEY table — one that DEFINES variables
# instead of recording specimens (a "KEY to variables" / glossary / metadata
# sheet). They are NOT template output fields (no <field>.md description) and are
# never written to the CSV; the mapper may return them so a later step can build
# a code -> full-name/unit glossary from the term/text pair and use it to
# canonicalize measurementType names and pick the identifier column.
DICT_FIELDS = ["definitionTerm", "definitionText"]

# Reserved mapping key for a species that belongs to the PAPER, not to a column.
# A single-species paper never puts its organism in a table column, so nothing in
# `mapping` records where those rows' verbatimIdentification came from. This key
# holds that decision (the name, who made it, and why) alongside the column
# entries, so the mapping JSON is a complete account of the table.
#
# It is deliberately inert to every consumer: it carries category=None and
# field="verbatimIdentification", and no Table.resolve() lookup can match it — so
# the relevance pass, the tag passes, the canonicaliser, grouping, and
# to_output.build_column_lookup all skip it exactly as they already skip
# identifier columns and uncategorised columns.
PAPER_SPECIES_KEY = "__paperSpecies__"

# Of the mappable fields, these describe the OBSERVATION rather than name a
# trait: where the specimen was found, how it was measured, what statistic the
# number is. A column mapped to one of them is not a measurementType and must
# not become one — but it is not junk either, so its value is attached to every
# measurement taken from the same row instead of being dropped. Without this,
# grouping consumed only verbatimIdentification and measurementType, and a
# column the mapper correctly routed to verbatimLocality (e.g. 'Microhabitat
# found') silently vanished: no trait row, and the verbatimLocality output
# column stayed empty for every record.
ROW_FIELDS = [f for f in MAP_FIELDS
              if f not in ("verbatimIdentification", "measurementType",
                           "measurementValue")]


def get_tag_explanation(tag: str) -> str:
    path = TEMPLATE_DIR / f"{tag}.md"
    if not path.exists():
        return f"(no description file {tag}.md found)"
    return path.read_text(encoding="utf-8")


def _field_descriptions_block(fields=MAP_FIELDS) -> str:
    """Bulleted 'field: description' block built from MAP_FIELDS, so the prompt
    always matches the mappable-field list exactly (no hand-kept second copy)."""
    return "\n".join(f"- {f}: {get_tag_explanation(f)}" for f in fields)


# ---------------------------------------------------------------------------
# Table collection across the whole document set (paper + complementary files)
# ---------------------------------------------------------------------------

def tables_from_text(text: str, source: str) -> list[Table]:
    """Parse every <table> in a document, joining page-continuation fragments.

    A long table split across pages arrives as several <table> blocks and the
    later ones usually DON'T repeat the header. Parsed alone, such a fragment
    eats its first species as a header and gets a schema that never matches its
    parent — every row in it is lost. So parse sequentially and, when a fragment
    is a header-less continuation of the previous table, re-parse it with that
    table's header (see tables.is_headerless_continuation).

    `parent` stays pointing at the last table that had a header of its OWN, so a
    table split over three or more pages has every fragment inherit the same
    header rather than chaining off an inherited one.
    """
    out: list[Table] = []
    parent: Table | None = None
    for i, t in enumerate(get_tables(text)):
        raw = t["content"]
        if parent is not None and is_headerless_continuation(parent, raw):
            header = [("" if c.synthetic else c.name) for c in parent.columns]
            tbl = parse_table(raw, source=source, table_index=i,
                              header_override=header)
            print(f"    [continuation] table #{i} has no header — inherited from "
                  f"#{parent.table_index}, {len(tbl.data_records())} row(s) recovered")
        else:
            tbl = parse_table(raw, source=source, table_index=i)
            parent = tbl                     # this one owns its header
        out.append(tbl)
    return out


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

def _cell_is_numeric(v) -> bool:
    """A cell counts as numeric even when it carries a spread or range around the
    number — the shapes stat tables use for a measurement:

        '385.2 (252.51)'   mean (SD)      -> numeric
        '12.4 ± 6.0'        mean ± SD      -> numeric
        '85.2 - 1459.3'     min - max      -> numeric
        '1.25', '0', '18'   plain          -> numeric
        'Arboreal omnivore', 'W', '-'      -> NOT numeric

    Strip a trailing parenthetical, then accept a plain number, an 'x ± y', or a
    numeric range. Without this, a morphology column of 'mean (SD)' cells fails
    float() on every value, is typed 'categorical', and then never gets a
    measurementUnit/measurementStatistic (those are requested for numeric columns
    only)."""
    s = str(v).strip()
    if not s:
        return False
    core = re.sub(r"\s*\([^)]*\)\s*$", "", s).strip().replace(",", "")  # drop "(sd)"
    try:
        float(core)
        return True
    except ValueError:
        pass
    num = r"[-+]?\d*\.?\d+"
    return bool(re.fullmatch(rf"{num}\s*(?:±|\+/-|[-–—])\s*{num}", core))


def classify_value_types(table: Table, mapping: dict) -> dict:
    for header, m in mapping.items():
        if m.get("field") == "verbatimIdentification" or m.get("category") is None:
            continue
        # If the relevance agent judged this a categorical trait, digits in the
        # cells are just the author's shorthand CODES (0/1 for absent/present,
        # sociality, etc.), not measurements. Type it categorical so the legend
        # decoder is allowed to expand those codes; 'numeric' would gate it out.
        if m.get("category") == "Categorical biological trait":
            m["value_type"] = "categorical"
            continue
        values = [v for v in table.column_values(header) if v != ""]
        if not values:
            m["value_type"] = "categorical"
            continue
        numeric = sum(1 for v in values if _cell_is_numeric(v))
        m["value_type"] = "numeric" if numeric >= len(values) * 0.7 else "categorical"
    return mapping


def agent_table_mapper(table: Table, paper_text: str, llm=None) -> dict:
    """Map a table's headers to template fields and merge in column relevance.
    Returns the mapping dict (no file IO). Context is sized to the prompt."""
    headers = table.header_names

    sample = [{h: r[h] for h in headers} for r in table.data_records()[:6]]

    prompt = f"""You're mapping a scientific table to a fixed template.

Template fields:
{_field_descriptions_block()}

A few tables are DATA DICTIONARIES (a "key", "glossary", "variables", or
"metadata" sheet) that DEFINE other columns instead of recording specimens. For
those tables ONLY, two extra fields are available:
- definitionTerm: cells are the variable names or codes being defined
  (e.g. "HL", "EL", "Biomass", "Species")
- definitionText: cells are the human-readable definition of that term
  (e.g. "Head length (mm)", "Latin name of the species")
Use these ONLY when the table is clearly a glossary — one column of short
terms/codes paired with one column of longer descriptions. NEVER use them on a
normal specimen or trait table.

Table headers: {headers}
Sample rows: {sample}

For each header, return an object with:
- field: one of {MAP_FIELDS + DICT_FIELDS}, or null if the column fits none of them
- value_column: true if this column holds measurement values (numeric or
  categorical). Taxonomic identities are NOT values, so verbatimIdentification
  always has value_column=false.
- reasoning: justification grounded in the header and its values, at most 15 words.

Map a column to the field that best fits its VALUES. A place (country, region,
site, habitat/vegetation type) is a verbatimLocality, not a verbatimIdentification
— only organism names belong in verbatimIdentification. Do not force a non-taxon
column into verbatimIdentification just because its values are text and unique.
Return ONLY a JSON object keyed by header name."""

    print(f"  Mapping table {table.source}#{table.table_index} ({len(headers)} cols)")
    # The reply is one object per header, but its size cannot be predicted from
    # the width alone (the same 3-column prompt has answered in 165 tokens and
    # run away past 1500). invoke_sized grows num_ctx and retries when a reply is
    # cut off, so there is no budget to estimate here.
    content = (llm.invoke(prompt).content if llm else invoke_sized(prompt))
    mapping = loads_salvaging(content)
    missing = [h for h in headers if h not in mapping]
    if missing:
        # A salvaged (truncated) reply loses its trailing columns. Fill them as
        # unmapped rather than KeyError-ing downstream: an unmapped column is
        # dropped by build_column_lookup, which is the same outcome as a column
        # the model declined to map.
        print(f"  ! {len(missing)} column(s) unmapped (truncated reply): {missing}")
        for h in missing:
            mapping[h] = {"field": None, "value_column": False,
                          "reasoning": "no mapping returned (response truncated)"}
    # value_type classification is deferred to enrich_with_relevance, which runs
    # AFTER category is set. classify_value_types skips category-less columns, so
    # running it here would leave value_type unset and break legend decoding
    # (collect_categorical_codes requires value_type == "categorical").
    return mapping


def enrich_with_relevance(table: Table, mapping: dict, paper_text: str) -> dict:
    """Add per-column relevance (category + reasoning) to an already-mapped table.

    Split out from the mapper because it is the expensive call (a whole-paper LLM
    pass, ~1-2 min). We only run it on tables that survive the identifier check,
    so stats/summary tables with no taxon column never pay for it. Mutates and
    returns `mapping`."""
    headers = table.header_names
    start = time.perf_counter()
    relevance = agent_define_columns_relevance(headers, paper_text)
    print(f"  relevance check: {time.perf_counter() - start:.1f}s")
    for header, rel in relevance.items():
        if header in mapping and isinstance(mapping[header], dict):
            rel = rel if isinstance(rel, dict) else {}
            mapping[header]["category"] = rel.get("category")
            mapping[header]["reasoning_relevance"] = rel.get("reasoning", "not found in text")
    # category is now populated -> classify value types (categorical vs numeric),
    # which legend decoding downstream relies on.
    classify_value_types(table, mapping)
    return mapping


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


def _identifier_columns(table: Table, mapping: dict) -> list:
    """Every column mapped to verbatimIdentification that looks like an
    identifier, in TABLE COLUMN ORDER.

    A taxon name is often split across columns — Fiedler's 'Butterfly_Genus' +
    'Butterfly_Species'. The mapper correctly marks BOTH as
    verbatimIdentification; taking only the first keys every row on the genus, so
    all species of a genus collapse into one entry and their measurements pile up
    on it (523 species -> 137 genera, with duplicated rows). Joining the parts in
    column order rebuilds the full name ('Acrodipsas' + 'aurata').

    Table order (not mapping/dict order) decides the join order, so the genus
    precedes the species exactly as the table presents them.
    """
    names = []
    for header, m in mapping.items():
        if m.get("field") != "verbatimIdentification":
            continue
        col = table.resolve(header)
        if col is not None and _looks_like_identifier_column(table, col.name):
            if col.name not in names:
                names.append(col.name)
    order = {h: i for i, h in enumerate(table.header_names)}
    names.sort(key=lambda n: order.get(n, len(order)))
    return names


def _identifier_column(table: Table, mapping: dict) -> Optional[str]:
    """First identifier column, or None. Kept for callers that only need to know
    WHETHER the table has an identifier (e.g. run_pipeline's tagging guard).

    No first-column fallback: a table without a real identifier column produces
    NO specimen rows. This is general and fails safe — it drops stats/summary
    tables (GLMM coefficients, etc.) that have no taxon column, while keeping any
    trait table that does, regardless of the table's specific layout."""
    cols = _identifier_columns(table, mapping)
    return cols[0] if cols else None


def _join_identifier(parts) -> str:
    """Join the identifier columns of one row into a single taxon name WITHOUT
    repeating the genus (or subgenus).

    A binomial is often split across columns and the parts overlap, which the
    naive space-join turns into a duplicated genus — and that duplicated genus is
    exactly what stops the name matching the ground-truth binomial:

        'Agapostemon' + 'Agapostemon femoratus'  -> 'Agapostemon Agapostemon femoratus'
        'Calopteryx.aequabilis' + 'Calopteryx aequabilis' (dotted twin)

    Two conservative passes, in table order:
      1. collapse parts that are the SAME name re-spelled (an exact duplicate
         column, or a dot-separated code column duplicating the spelled name);
         one is kept, preferring the spelled form over the dotted code.
      2. drop any token that exactly repeats an earlier token (case-insensitive).

    Distinct tokens are untouched (Fiedler's 'Acrodipsas' + 'aurata', a real
    subgenus, 'sp.'), so split binomials still rebuild correctly.
    """
    parts = [p.strip() for p in parts if p and p.strip()]
    if len(parts) <= 1:
        return parts[0] if parts else ""

    def norm(s):
        return re.sub(r"\s+", " ", s.replace(".", " ")).strip().lower()

    by_norm, order = {}, []
    for p in parts:
        k = norm(p)
        if k not in by_norm:
            by_norm[k] = p
            order.append(k)
        elif "." in by_norm[k] and "." not in p:
            by_norm[k] = p
    kept = [by_norm[k] for k in order]

    seen, out = set(), []
    for tok in " ".join(kept).split():
        key = tok.lower()
        if key not in seen:
            seen.add(key)
            out.append(tok)
    return " ".join(out)


def agent_table_species(table: Table, candidates: list, paper_text: str,
                        llm=None) -> Optional[str]:
    """Decide which species a table's rows describe when the table has NO species
    column, e.g. a single-species paper whose organism is only named in the prose.

    `candidates` come from the deterministic scan (tables.find_binomial_candidates);
    the model only CHOOSES among them or declines — it is never asked to recall a
    species, so it cannot invent one. Returns the chosen name, or None when the
    table is not per-specimen data of a single species (a stats/site/model table).
    """
    if not candidates:
        return None
    headers = table.header_names
    sample = [{h: r[h] for h in headers} for r in table.data_records()[:4]]
    names = [c["name"] for c in candidates]
    prompt = f"""A table from a scientific paper has NO species column. Decide which
species — if any — its rows describe.

Species named in this paper (most-mentioned first): {names}

Table headers: {headers}
Sample rows: {sample}

Paper text (excerpt):
{paper_text[:6000]}

Answer with JSON only:
{{"species": "<one name from the list, or null>",
  "reasoning": "<at most 15 words>"}}

Choose a species ONLY if these rows are measurements/observations of individual
organisms of that one species. Return null if the table is about study sites,
model outputs, statistics, or covers several species. Never invent a name that is
not in the list."""
    try:
        content = (llm.invoke(prompt).content if llm else invoke_sized(prompt))
        out = loads_salvaging(content)
    except Exception:
        return None
    chosen = out.get("species")
    if not chosen or str(chosen).strip().lower() in {"null", "none", ""}:
        return None
    chosen = str(chosen).strip()
    # only accept a name the deterministic scan actually found in the paper
    for n in names:
        if clean_text(n).lower() == clean_text(chosen).lower():
            print(f"    paper-level species for {table.source}#{table.table_index}: "
                  f"{n!r} ({out.get('reasoning','')})")
            return n
    print(f"    (rejected off-list species {chosen!r} — not found in the paper)")
    return None


def add_table_to_grouped(table: Table, mapping: dict, grouped: dict,
                         fallback_species: Optional[str] = None) -> dict:
    id_cols = _identifier_columns(table, mapping)
    if not id_cols:
        if not fallback_species:
            print(f"    skip table {table.source}#{table.table_index} — "
                  f"no identifier (verbatimIdentification) column; not specimen data")
            return grouped
        # Single-species paper: the organism is named in the prose, never in a
        # column, so every row of this table belongs to that one species.
        print(f"    {table.source}#{table.table_index} has no species column — "
              f"attributing all rows to {fallback_species!r} (paper-level)")
    if len(id_cols) > 1:
        print(f"    identifier built from {len(id_cols)} columns: {id_cols}")

    kept = []
    row_cols = []          # (col_name, field) — qualifies the row, not a trait
    for header, m in mapping.items():
        field = m.get("field")
        if field == "verbatimIdentification":
            continue
        # A column mapped to a row field (verbatimLocality / measurementMethod /
        # measurementStatistic) describes the observation, not a trait. Carry it
        # onto this row's measurements rather than dropping it or turning it into
        # a bogus measurementType named after the column.
        if field in ROW_FIELDS:
            col = table.resolve(header)
            if col is not None:
                row_cols.append((col.name, field))
                print(f"    '{header}' -> {field} (qualifies the row, not a trait)")
            continue
        # Everything else is emitted below as its OWN measurementType (the
        # header/canonicalType names the trait, the cell is its value), so it is
        # kept only if the mapper mapped it to measurementType AND the relevance
        # pass gave it a biological category. That stops columns mapped to
        # nothing (an abundance/count/citation/section-label) from leaking in as
        # spurious per-column measurementTypes (e.g. Fiedler's biogeographic
        # realms and 'sources'; Beyer's 'number of bumblebees'/'TL category').
        if field != "measurementType" or m.get("category") is None:
            print(f"    skip '{header}' — field={field!r}, "
                  f"category={m.get('category')!r} (not a measurementType column)")
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
        # join the identifier parts for THIS row (genus + species -> binomial),
        # dropping duplicated genus/subgenus and dotted-code twins (see
        # _join_identifier) so the name matches the plain binomial. With no
        # identifier column at all, the paper-level species applies to every row.
        species = (_join_identifier(rec.get(c, "") for c in id_cols) if id_cols
                   else fallback_species)
        if not species:
            continue
        entry = grouped.setdefault(species, {
            "verbatimIdentification": species,
            "measurements": [],
        })
        # Values that qualify THIS row (locality/method/statistic). They apply to
        # every measurement taken from the row, so they are read once per record.
        row_attrs = {}
        for col_name, field in row_cols:
            v = (rec.get(col_name, "") or "").strip()
            if v:
                row_attrs[field] = v

        for col_name, m in kept:
            value = rec.get(col_name, "")
            meas = {
                "measurementType": m.get("canonicalType", col_name),
                "measurementValue": value if value != "" else None,
            }
            # row-level qualifiers first; a column-specific tag below overrides
            # them, being the more precise statement about that measurement.
            meas.update(row_attrs)
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
        parsed = loads_salvaging(content)
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

def build_grouped(tables: list, mappings: dict, fallback_species: dict = None) -> dict:
    """Merge every mapped table into one species-keyed structure.

    ``fallback_species`` maps table_id -> species name, for tables that have no
    species column because the paper studies a single species (see
    resolve_table_species). Tables absent from it behave exactly as before.
    """
    fallback_species = fallback_species or {}
    grouped: dict = {}
    for table in tables:
        tid = table_id(table)
        mapping = mappings.get(tid)
        if mapping:
            add_table_to_grouped(table, mapping, grouped,
                                 fallback_species=fallback_species.get(tid))
    return grouped


def resolve_paper_species(tables: list, mappings: dict, paper_text: str,
                          llm=None) -> dict:
    """Attribute a SINGLE-SPECIES paper's tables to the species named in its prose.

    Two stages, in order:

      1. STRUCTURAL VETO (deterministic, non-negotiable). NO table in the paper
         may have an identifier column. If even one table names species, this is
         not a single-species paper and we must not guess: the other tables'
         missing identifier is a different problem (a stats table, or identifier
         detection failing) and inventing a species there would manufacture wrong
         rows instead of dropping them.
      2. THE DECISION ITSELF, made by the LLM, always. The deterministic scan
         supplies the candidate binomials with their evidence (how often each is
         written in full, how often abbreviated 'H. ligatus'-style, whether it
         appears in the title/abstract); the model reads the prose and says
         whether the paper studies ONE of them, and which.

         The old code gated the LLM behind a score-ratio test
         (``top >= 3 * runner_up``) and only called it to confirm. That test
         compares TOTALS, and a total is dominated by raw frequency — so any
         repeatedly-named non-study taxon (a cited species, a host plant, or a
         capitalised prose pair the binomial regex happens to match) vetoed the
         attribution no matter how strong the evidence for the real organism.
         Brant2021 died there: 'Halictus ligatus' abbreviated 26x, score 146,
         beaten by a runner-up scoring 134 that needed only to reach 49 to block
         it. Reading the prose is exactly the judgement an LLM makes better than
         a ratio, so it now makes it.

    The deterministic dominance test is not gone — it survives as the FALLBACK
    for when the LLM is unreachable or returns something unparseable, so a
    machine with no Ollama degrades to the previous behaviour instead of
    attributing blind. It is also tightened to compare abbreviation counts rather
    than totals, since abbreviation support is what distinguishes a study
    organism from a mentioned one.

    The species is applied to every table that has at least one measurementType
    column (a model/site table has no trait to attribute).

    Returns (species_by_table_id, verdict) where verdict is the decision record
    ({single_species, species, reasoning, decided_by, candidates}) or None when no
    decision was reached; map_and_group writes it into the table mappings.
    """
    mapped = [(t, mappings.get(table_id(t))) for t in tables]
    mapped = [(t, m) for t, m in mapped if m]
    if not mapped:
        return {}, None

    # (1) any table with a species column => not a single-species paper
    named = [t for t, m in mapped if _identifier_column(t, m) is not None]
    if named:
        return {}, None

    # (2) candidate binomials + their evidence, for the model to judge
    cands = find_binomial_candidates(paper_text)
    if not cands:
        print("  No table names a species, and no binomial found in the prose; "
              "leaving tables unattributed")
        return {}, None

    print("  No table names a species. Binomial candidates from the prose:")
    for c in cands[:4]:
        print(f"    {c['name']!r:<34} full={c['mentions']:<4} "
              f"abbreviated={c['abbrev_mentions']:<4} score={c['score']}")

    verdict = agent_resolve_paper_species(cands, paper_text, llm=llm)

    if verdict is None:
        # No usable LLM verdict -> deterministic fallback, on ABBREVIATION
        # support: a rival with many raw mentions but no 'G. species' form is a
        # cited taxon or prose noise, not a second study organism.
        top = cands[0]
        ru = cands[1] if len(cands) > 1 else {"score": 0, "abbrev_mentions": 0}
        dominant = (top["abbrev_mentions"] >= 3
                    and top["abbrev_mentions"] >= 3 * ru["abbrev_mentions"]
                    and top["score"] > ru["score"])
        verdict = {
            "single_species": dominant,
            "species": top["name"] if dominant else None,
            "reasoning": (
                f"no LLM verdict available; deterministic fallback: "
                f"{top['name']!r} abbreviated {top['abbrev_mentions']}x vs "
                f"{ru['abbrev_mentions']}x for the runner-up"),
            "decided_by": "deterministic-fallback",
        }
        print(f"    [species] fallback verdict: single_species="
              f"{verdict['single_species']} ({verdict['reasoning']})")

    verdict["candidates"] = [{k: c[k] for k in
                              ("name", "mentions", "abbrev_mentions", "score")}
                             for c in cands[:4]]

    if not (verdict["single_species"] and verdict["species"]):
        print("    -> not a single-species paper; leaving tables unattributed")
        return {}, verdict

    species = verdict["species"]
    out = {}
    for t, m in mapped:
        if any(v.get("field") == "measurementType" for v in m.values()):
            out[table_id(t)] = species
    if out:
        print(f"    -> single-species paper: attributing {len(out)} table(s) "
              f"to {species!r}")
    else:
        print(f"    -> {species!r} accepted, but no table has a measurementType "
              f"column to attribute")
    return out, verdict


def _paper_species_entry(species: str, verdict: Optional[dict]) -> dict:
    """The mapping entry recorded under PAPER_SPECIES_KEY.

    Shaped like a column entry so anything walking the mapping treats it
    uniformly, but with category=None and no resolvable column, which is what
    makes every existing consumer skip it (see PAPER_SPECIES_KEY)."""
    v = verdict or {}
    return {
        "field": "verbatimIdentification",
        "category": None,
        "scope": "paper",
        "column": None,
        "value": species,
        "reasoning": v.get("reasoning") or "(no reasoning recorded)",
        "decided_by": v.get("decided_by", "unknown"),
        "candidates": v.get("candidates", []),
    }


def agent_resolve_paper_species(candidates: list, paper_text: str,
                                llm=None) -> Optional[dict]:
    """One call per paper: is this a single-species study, and of WHICH species?

    The model both decides and picks, but only from `candidates` — the binomials
    the deterministic scan actually found in the text. A name outside that list is
    rejected, so the model cannot invent an organism the paper never names; it is
    choosing among evidence, not generating.

    It is given the evidence behind each candidate (full mentions, abbreviated
    mentions, score) because that is the signal a bare excerpt hides: the study
    organism is the one written out once and abbreviated thereafter, while a
    frequently-cited comparison taxon is not.

    Returns {single_species, species, reasoning, decided_by} — or None if the call
    failed or the reply was unusable, which tells the caller to fall back to the
    deterministic test rather than guess.
    """
    names = [c["name"] for c in candidates[:5]]
    evidence = "\n".join(
        f'- "{c["name"]}": written in full {c["mentions"]}x, '
        f'abbreviated ("{c["name"][0]}. {c["name"].split()[-1]}") '
        f'{c["abbrev_mentions"]}x'
        for c in candidates[:5])

    prompt = f"""You are deciding whether a biological paper reports measurements
for a SINGLE study species, and if so which one.

None of the paper's tables has a species column, which happens for two very
different reasons:
  (a) the paper studies ONE species, named in the title/abstract and referred to
      throughout, so no table needs to repeat it;
  (b) the paper studies MANY species and the species column simply failed to be
      detected.
Telling (a) from (b) is the whole task. If the text compares species, lists
several study organisms, or reports per-species results, answer false.

Candidate names found in the text, with how they are used:
{evidence}

A name that is written out once and then abbreviated many times is being used as
THE study organism. A name mentioned often but never abbreviated is usually a
cited or compared taxon, not the subject.

Paper text (excerpt):
{paper_text[:8000]}

Answer JSON only, choosing "species" from this list exactly as written {names},
or null if the paper is not a single-species study:
{{"single_species": true|false, "species": "<name or null>",
  "reasoning": "<at most 25 words, citing what in the text decided it>"}}"""

    try:
        content = (llm.invoke(prompt).content if llm else invoke_sized(prompt))
        out = loads_salvaging(content)
    except Exception as e:
        print(f"    [species] LLM call failed ({type(e).__name__}: {e}); "
              f"falling back to the deterministic test")
        return None
    if not isinstance(out, dict) or "single_species" not in out:
        print(f"    [species] unusable reply {str(out)[:120]!r}; "
              f"falling back to the deterministic test")
        return None

    single = bool(out.get("single_species"))
    species = str(out.get("species") or "").strip()
    reasoning = str(out.get("reasoning") or "").strip()

    if single and species not in names:
        # Refuse a name the text scan never found: that is generation, not choice.
        print(f"    [species] rejected {species!r} — not among the candidates "
              f"{names}; leaving unattributed")
        return {"single_species": False, "species": None,
                "reasoning": f"model proposed {species!r}, which is not a "
                             f"binomial found in the paper text",
                "decided_by": "llm-rejected"}

    print(f"    [species] single_species={single} species={species or None!r} "
          f"({reasoning})")
    return {"single_species": single, "species": species or None,
            "reasoning": reasoning or "(model gave no reasoning)",
            "decided_by": "llm"}


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

    # Tables are often ONE logical table split across pages: identical headers
    # and identical column semantics, only different rows. The per-column LLM
    # work (header->field mapping, relevance, canonicalize) depends only on the
    # headers + column value TYPES + paper text — all the same across fragments —
    # so run it ONCE per distinct schema and share the finished mapping. Every
    # fragment's ROWS are still collected by build_grouped, so nothing is dropped.
    groups: dict = {}                       # signature -> [tables] in doc order
    order: list = []
    for table in tables:
        if not table.header_names:
            continue
        sig = tuple(table.header_names)
        if sig not in groups:
            groups[sig] = []
            order.append(sig)
        groups[sig].append(table)

    # phase 1 (map) on ONE representative per schema
    rep_mapping: dict = {}                   # signature -> finished mapping
    for sig in order:
        rep = groups[sig][0]
        rep_mapping[sig] = agent_table_mapper(rep, paper_text, llm=llm)
        extra = len(groups[sig]) - 1
        if extra:
            print(f"    schema shared: reusing this mapping for {extra} more "
                  f"fragment(s) (same headers) — no repeat LLM calls")

    # A single-species paper never puts its organism in a column, so those tables
    # have no identifier and would be dropped. Resolve a paper-level species for
    # them FIRST, so they still qualify for the relevance pass below.
    reps = [groups[sig][0] for sig in order]
    rep_by_tid = {table_id(groups[sig][0]): rep_mapping[sig] for sig in order}
    species_by_tid, species_verdict = resolve_paper_species(
        reps, rep_by_tid, paper_text, llm=llm)

    # phase 2 (relevance) — for tables with an identifier OR a paper-level species
    for sig in order:
        rep = groups[sig][0]
        mapping = rep_mapping[sig]
        if (_identifier_column(rep, mapping) is None
                and table_id(rep) not in species_by_tid):
            print(f"    skip relevance for {rep.source}#{rep.table_index} — "
                  f"no identifier column (not specimen data)")
        else:
            enrich_with_relevance(rep, mapping, paper_text)

    # canonicalize measurementType names once, over the representative mappings
    # (they already contain every distinct header, so the glossary is complete)
    print("  Canonicalizing measurementType names...")
    agent_canonicalize_measurement_types(rep_by_tid, paper_text, llm=llm)

    # fan the finished mapping out to every fragment; one file per table
    mappings: dict = {}
    fallback: dict = {}
    for sig in order:
        rep_sp = species_by_tid.get(table_id(groups[sig][0]))
        for i, table in enumerate(groups[sig]):
            tid = table_id(table)
            mapping = rep_mapping[sig] if i == 0 else copy.deepcopy(rep_mapping[sig])
            mappings[tid] = mapping
            if rep_sp:                       # fragments share the representative's species
                fallback[tid] = rep_sp
                # Record WHERE this table's verbatimIdentification comes from.
                # Without this the mapping JSON shows no identifier at all and
                # the rows look like they materialised from nowhere.
                mapping[PAPER_SPECIES_KEY] = _paper_species_entry(
                    rep_sp, species_verdict)
            (out_dir / f"{tid}_mapping.json").write_text(
                json.dumps(mapping, indent=2, ensure_ascii=False), encoding="utf-8")

    grouped = build_grouped(tables, mappings, fallback_species=fallback)
    return grouped, tables, mappings


if __name__ == "__main__":
    main = "Abensperg-Traun M. (1991).md"
    paper_text = Path(main).read_text(encoding="utf-8")
    sources = [main]  # add complementary files here, e.g. "..._S1.xlsx"
    grouped, tables, mappings = map_and_group(sources, paper_text)
    json.dump(grouped, open("grouped_by_species.json", "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print(f"Grouped {len(grouped)} species")