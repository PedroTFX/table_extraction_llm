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
                    find_binomial_candidates, looks_multivalue_column,
                    is_headerless_continuation,
                    detect_transposed, transpose_table)
from text_manager import get_tables, xlsx_to_table, csv_to_table
from column_relevance import (agent_define_columns_relevance, make_llm,
                              invoke_sized, loads_salvaging)
from repair_mapping import repair_mapping
from long_format import detect_long_in_table, _decode_key

# MODEL = "gemma4:e4b-it-qat"
MODEL = "gemma4:e2b"


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

def tables_from_text(text: str, source: str, llm=None) -> list[Table]:
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
            # Full-replacement header finding: the LLM reads the first rows and
            # says which is the header. Falls back to row 0 on any failure.
            hp = _header_plan_for(raw, llm=llm)
            tbl = parse_table(raw, source=source, table_index=i, header_rows=hp)
            parent = tbl                     # this one owns its header
        out.append(tbl)
    return out


def _header_plan_for(raw_grid: str, llm=None) -> dict:
    """Compute the {header_rows, join} plan for one raw pipe-grid via the LLM
    header-finder. Isolated so callers stay simple and the finder can be tested
    on its own."""
    lines = [l for l in (ln.strip() for ln in raw_grid.strip().splitlines()) if l]
    return agent_find_header(lines, llm=llm)


def collect_tables(sources: Iterable, llm=None) -> list[Table]:
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
            out.extend(tables_from_text(text, source=p.name, llm=llm))
        elif ext in {".xlsx", ".xls"}:
            raw = xlsx_to_table(str(p))
            out.append(parse_table(raw, source=p.name, table_index=0,
                                   header_rows=_header_plan_for(raw, llm=llm)))
        elif ext in {".csv", ".tsv"}:
            text = p.read_text(encoding="utf-8", errors="replace")
            raw = csv_to_table(text)
            out.append(parse_table(raw, source=p.name, table_index=0,
                                   header_rows=_header_plan_for(raw, llm=llm)))
        else:
            print(f"  (skipping unsupported file type: {p.name})")
    return out


def maybe_transpose(table: Table):
    """Rotate a species-in-header table; leave every other table untouched.

    Returns (table, evidence). Safety is by construction: the rotation is only
    applied when :func:`detect_transposed` sees taxon names along the header AND
    not down the first column, and the result is checked to still hold every
    populated cell before it is accepted. If anything is lost — a ragged row, a
    trait label that collided — the original is kept, because a table the mapper
    drops is a recoverable miss whereas a table it silently corrupts is not.
    """
    try:
        verdict, ev = detect_transposed(table)
    except Exception as e:                       # never let this stop a run
        print(f"    orientation check failed for {table_id(table)}: {e}")
        return table, {"reason": f"error: {e}"}
    if not verdict:
        return table, ev

    rotated = transpose_table(table)

    # Cell-count guard: rotation must preserve the populated data cells.
    def _cells(t):
        return sorted(clean_text(v) for r in t.data_records()
                      for k, v in r.items()
                      if not k.startswith("_") and str(v or "").strip())

    before, after = _cells(table), _cells(rotated)
    if len(after) < len(before):
        print(f"    transpose: discarded for {table_id(table)} — would lose "
              f"{len(before) - len(after)} cell(s); keeping original orientation")
        return table, {**ev, "reason": "rejected: cell loss"}

    print(f"    transpose: {table_id(table)} rotated — {len(rotated.data_records())} "
          f"species x {len(rotated.header_names) - 1} trait(s) "
          f"(header {ev['header_frac']:.0%} taxon-like, first column "
          f"{ev['body_frac']:.0%})")
    return rotated, ev


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


def _preview_split_row(line: str) -> list:
    """Split a pipe line into cells for the header preview (trailing/leading pipe
    tolerant). Kept local so this module doesn't reach into tables' internals."""
    parts = [c.strip() for c in line.split("|")]
    if parts and parts[0] == "":
        parts = parts[1:]
    if parts and parts[-1] == "":
        parts = parts[:-1]
    return parts


def agent_find_header(grid_lines: list, llm=None, preview_rows: int = 4) -> dict:
    """Ask the model which of the first few rows form the column header.

    REPLACES the deterministic header heuristics (banner-skip, units-row merge,
    numeric-header detection). The model reads the top `preview_rows` rows, shown
    as a NUMBERED list, and answers which row numbers are the header — a choice
    among a small visible set (0,1,2,3), never an index it had to count to, so a
    weak model stays reliable.

    It classifies rows it can see; it never rewrites a value. The returned indices
    are used by the CODE to read the actual header cells, so no header text ever
    comes from the model.

    Returns {"header_rows": [i, ...], "join": bool}. On any LLM error or unusable
    reply, returns {"header_rows": [0], "join": False} — the naive default — so a
    down model degrades to 'row 0 is the header', never a crash.
    """
    # Decision — trust the model. Header selection is the LLM's job (this agent
    # REPLACED the old deterministic heuristics on purpose). We deliberately do
    # NOT add a deterministic caption/banner floor here: if a small model mispicks
    # — e.g. takes the 'Table S1. ...' caption as the header and pushes the real
    # 'Species | ...' row into the data — we want that to SHOW, and to fix it in
    # the prompt (see the CAPTION trap above) or the model, not to paper over it
    # with per-shape rules that don't generalise ('Table S1' today, 'Appendix 2'
    # tomorrow). So the default below stays naive: row 0. It is reached only when
    # the LLM is genuinely unavailable or returns nothing usable; in this
    # deployment the model is always present, so this is a last resort, not a
    # routine path. If it ever fires on a captioned table it WILL pick the caption
    # — that misparse is the intended visible signal to revisit, not a silent bug.
    default = {"header_rows": [0], "join": False}
    if not grid_lines:
        return default

    preview = grid_lines[:preview_rows]
    shown = "\n".join(f"row {i}: {ln}" for i, ln in enumerate(preview))

    system = (
        "You identify the HEADER of a data table from a scientific paper. You are "
        "shown the first few rows, each labelled 'row N:', cells separated by "
        "' | '. Decide which row(s) name the columns (e.g. 'Species | Body length "
        "| Feeding group').\n\n"
        "Traps:\n"
        "- A CAPTION/TITLE names the whole table, not its columns ('Table S1. All "
        "functional traits...', 'Table 3 Overview of species'). It is usually one "
        "long cell with the rest of the row empty and sits ABOVE the header. It is "
        "never the header; the header is the row just below it. Judge this by "
        "meaning, not by the word 'Table' — 'Table S1', 'Appendix 2', or a title "
        "in another language are all captions.\n"
        "- A BANNER repeats one label across the width ('Traits | Traits | "
        "Traits', or 'Morphological trait' filling every column). It is NOT the "
        "header; the real header is the row just below it.\n"
        "- A STACKED header spans two rows: a grouping label on top ('Successional "
        "stages') over the real names below ('G | H | C'). Then BOTH rows are the "
        "header and should be joined.\n"
        "- A DATA row holds mostly numbers or specimen names; never the header.\n\n"
        "Answer ONLY JSON: {\"header_rows\": [<row numbers>], \"join\": "
        "true|false}. 'join' is true only when header_rows has more than one row "
        "to combine. Do not rewrite any text; only give row numbers."
    )
    user = "Rows:\n" + shown

    try:
        content = (llm.invoke([{"role": "system", "content": system},
                               {"role": "user", "content": user}]).content
                   if llm else
                   invoke_sized([{"role": "system", "content": system},
                                 {"role": "user", "content": user}]))
        out = loads_salvaging(content)
    except Exception as e:
        print(f"    [header] LLM unavailable ({type(e).__name__}); row 0 default")
        return default

    rows = out.get("header_rows") if isinstance(out, dict) else None
    if not isinstance(rows, list) or not rows:
        return default
    clean = sorted({r for r in rows if isinstance(r, int) and 0 <= r < len(preview)})
    if not clean:
        return default
    return {"header_rows": clean, "join": bool(out.get("join")) and len(clean) > 1}


def _header_is_degenerate(header_names) -> bool:
    """Does this header show the collapsed-banner signature?

    True when the real column names were lost to a spanning label, which leaves
    one of these fingerprints in the parsed header:
      * DEDUP SUFFIXES — the same base repeated as 'X', 'X (1)', 'X (2)'... (what
        a single banner name becomes when forward-filled across N columns);
      * ONE LABEL REPEATED — the non-identifier headers are all the same string
        ('Traits | Traits | Traits');
      * NUMERIC HEADERS — the header row is mostly numbers, i.e. a data row got
        taken as the header;
      * PLACEHOLDER NAMES — mostly 'colN'/'identifier' fallbacks, meaning no real
        header was found.

    A normal header ('Species | Body length | Wing width') matches none of these,
    so a clean table is never eligible for the LLM rewrite. Judged on the
    non-identifier columns (index 1+), since the id column legitimately varies.
    """
    hs = [str(h or "").strip() for h in header_names]
    if len(hs) < 2:
        return False
    body = hs[1:]
    nonempty = [h for h in body if h]
    if not nonempty:
        return True

    # dedup suffixes: strip a trailing ' (k)' and see if the bases collapse
    bases = [re.sub(r"\s*\(\d+\)\s*$", "", h) for h in nonempty]
    if len(set(bases)) == 1 and len(nonempty) >= 3:
        return True

    # one label repeated verbatim
    if len(set(nonempty)) == 1 and len(nonempty) >= 3:
        return True

    # mostly numeric headers (a data row misread as the header)
    numeric = sum(1 for h in nonempty if re.match(r"^[-+]?[\d.,]+%?$", h))
    if numeric >= max(2, len(nonempty) * 0.6):
        return True

    # mostly placeholder fallbacks
    placeholder = sum(1 for h in nonempty
                      if re.match(r"^(col\d+|identifier|column\d+)$", h, re.I))
    if placeholder >= max(2, len(nonempty) * 0.6):
        return True

    return False


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
    # non-blank header) AND its header is not degenerate, it is a clean
    # identifier x trait grid and must NOT be decomposed. Decomposition exists to
    # rescue banded tables whose identifier is missing/blank-headered, OR whose
    # real column names were lost to a spanning banner (a degenerate header — see
    # _header_is_degenerate); a table with a good identifier but a collapsed
    # header still needs the rewrite, so we do NOT skip it.
    if not _header_is_degenerate(table.header_names):
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

    # Accept a single-table rewrite ONLY when it repairs a degenerate header —
    # the collapsed-banner family, where a spanning label overwrote the real
    # column names (every trait becomes 'Traits'/'Traits (1)'/'Morphological
    # trait (2)'...). That is not a split, so the len<2 rule below would discard
    # the fix; but it is exactly what the agent is meant to correct. A rewrite is
    # allowed through when the ORIGINAL header is degenerate and the NEW one is
    # not — never for a table whose header was already fine (which protects clean
    # tables from being churned).
    if len(subs) == 1 and _header_is_degenerate(table.header_names) \
            and not _header_is_degenerate(subs[0].header_names):
        # data-preservation still applies below; fall through to that check by
        # NOT returning here, but skip the len<2 discard.
        pass
    elif len(subs) < 2:
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
            len(subs[0].columns) == len(table.columns) and \
            not (_header_is_degenerate(table.header_names)
                 and not _header_is_degenerate(subs[0].header_names)):
        # effectively unchanged — unless the rewrite fixed a degenerate header
        # (same data, same width, but real column names now), which we keep.
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
        values = [v for v in table.column_values(header) if v != ""]
        # Does this column hold LISTS ('W, S, P') or single values that merely
        # contain a comma ('Coras montanus (Emerton, 1890a)')? Only the whole
        # column can answer that, and only here is the whole column in scope —
        # to_output sees one cell at a time and, splitting on any comma, cut a
        # host-spider name in half at its authority citation. Recorded on the
        # mapping so the split decision downstream is column-wide, not per-cell.
        m["multi_value"] = looks_multivalue_column(values)
        if m.get("category") == "Categorical biological trait":
            m["value_type"] = "categorical"
            continue
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
The field descriptions above define measurementType vs measurementValue (a wide
trait column is a measurementType even when its cells are numbers).
Return ONLY a JSON object keyed by header name."""

    print(f"  Mapping table {table.source}#{table.table_index} ({len(headers)} cols)")
    # The reply is one object per header, but its size cannot be predicted from
    # the width alone (the same 3-column prompt has answered in 165 tokens and
    # run away past 1500). invoke_sized grows num_ctx and retries when a reply is
    # cut off, so there is no budget to estimate here.
    content = (llm.invoke(prompt).content if llm else invoke_sized(prompt))
    mapping = loads_salvaging(content)
    if not isinstance(mapping, dict):
        mapping = {}
    # A smaller model sometimes maps a header to a bare string ("measurementType")
    # instead of the {field, value_column, ...} object. Coerce any non-dict entry
    # to an unmapped column so every downstream `.get()` on a mapping entry is safe.
    for h, v in list(mapping.items()):
        if not isinstance(v, dict):
            mapping[h] = {"field": (v if isinstance(v, str) and v in MAP_FIELDS else None),
                          "value_column": False,
                          "reasoning": "coerced from a non-object mapper reply"}
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
    # A few example cell values per column let the relevance agent judge a column
    # by its CONTENTS, not just its name and the prose — decisive for trait
    # columns the paper never discusses (e.g. a supplement's 'wing_pigment_color'
    # with values 'amber'/'hyaline'/'black').
    samples = {}
    for h in headers:
        vals = []
        seen = set()
        for v in table.column_values(h):
            v = (v or "").strip()
            if v and v.lower() not in seen:
                seen.add(v.lower())
                vals.append(v)
            if len(vals) >= 6:
                break
        samples[h] = vals
    start = time.perf_counter()
    relevance = agent_define_columns_relevance(headers, paper_text, samples=samples)
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


_ID_PARENS = re.compile(r"\([^()]*\)")


def strip_identifier_parentheticals(name: str) -> str:
    """Drop every parenthesised group, and its contents, from a taxon name.

    Everything papers put in brackets after a name is metadata about the record
    rather than part of the name itself, and none of it belongs in
    verbatimIdentification:

        'Hesperiidae(n=45)'                    -> 'Hesperiidae'
        'Ogcodes pallidipennis (Loew, 1866)'   -> 'Ogcodes pallidipennis'
        'Xylocopa frontalis (Olivier)'          -> 'Xylocopa frontalis'
        'Bombus terrestris (n = 12, reared)'    -> 'Bombus terrestris'

    Applied repeatedly so nested brackets go too, then whitespace and dangling
    punctuation are tidied. A sample size lost here is not lost from the record —
    sampleSizeValue is its own field — and a taxonomic authority is recoverable
    from the paper, whereas a name carrying either one matches nothing.
    """
    s = str(name or "")
    prev = None
    while prev != s:                       # nested brackets need more than one pass
        prev = s
        s = _ID_PARENS.sub(" ", s)
    # an unclosed bracket ('Bombus terrestris (Linnaeus' ) would otherwise survive
    s = re.sub(r"[\(\)\[\]]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s.strip(" ,;:-")


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

    Parenthesised groups are removed FIRST (see
    strip_identifier_parentheticals): an authority like '(Loew, 1866)' would
    otherwise contribute tokens to the dedup passes and end up in the name.
    """
    parts = [strip_identifier_parentheticals(p) for p in parts]
    parts = [p.strip() for p in parts if p and p.strip()]
    if len(parts) <= 1:
        return _drop_leading_family((parts[0] if parts else "").split())

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

    return _drop_leading_family(out)


# Family/superfamily/subfamily rank suffixes. A family name also tends to be
# ALL CAPS in these tables, whereas a genus and a subgenus are Title-case — that
# case difference is what tells 'FAMILY Genus epithet' apart from a genuine
# 'Genus Subgenus epithet'.
_FAMILY_SUFFIX = re.compile(r"(?:idae|inae|ini|oidea|aceae|idea)$", re.IGNORECASE)


def _looks_like_family(tok: str) -> bool:
    """A family-rank name: ALL CAPS (len>=4, so it isn't an abbreviation like
    'NA') or a recognisable family suffix. Handles a truncated 'MELANDRYID'
    (wrapped '-AE' lost) via the all-caps test, since the suffix is gone."""
    return (tok.isupper() and len(tok) >= 4) or bool(_FAMILY_SUFFIX.search(tok))


def _drop_leading_family(tokens) -> str:
    """Drop a FAMILY joined onto the front of a binomial, KEEPING the subgenus.

    A family column joined onto the species column yields 'FAMILY Genus epithet'
    (e.g. 'MELANDRYID Abdera affinis'). The family is not part of the name the
    ground truth records, so it is removed here -> 'Abdera affinis'. A family is
    detected by rank — ALL CAPS (also catching a line-wrapped 'MELANDRYID' that
    lost its '-AE') or a family suffix — and only dropped when a Title-case genus
    follows it, so 'MELANDRYIDAE sp.' (no genus) keeps the family as its identifier.

    The SUBGENUS is deliberately KEPT. An unbracketed subgenus ('Agabus Ilybius
    affinis', from a 'Genus (Subgenus) epithet' whose brackets MinerU dropped) is
    left intact as the most complete extraction. Collapsing it to the bare
    binomial is a MATCH-TIME concern, and the evaluator already handles it:
    species_match tolerates the extra word and remap_pred_species relabels the
    name onto the ground-truth binomial. So keeping it here loses no matches and
    preserves information the old drop-heuristic discarded (and which it
    mistakenly applied to genera in the family case).
    """
    if len(tokens) < 2:
        return " ".join(tokens)
    first, second = tokens[0], tokens[1]
    if _looks_like_family(first) and second[:1].isupper() and not second.isupper():
        return " ".join(tokens[1:])          # drop family; keep genus (+subgenus) + epithet
    return " ".join(tokens)


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

    # Iterate ALL records (not just data_records) so the parser's group/subheader
    # rows stay in view: in a BANDED taxonomic list the genus sits alone on such a
    # row and the species beneath it carry only the epithet ('Agapostemon' / then
    # 'sericeus', 'virescens'). We read the genus off the band row and rebuild the
    # full binomial for the rows below it; the band row itself is not emitted.
    band_genus = None          # genus carried down from a section-header row
    for rec in table.records:
        # join the identifier parts for THIS row (genus + species -> binomial),
        # dropping duplicated genus/subgenus and dotted-code twins (see
        # _join_identifier) so the name matches the plain binomial. With no
        # identifier column at all, the paper-level species applies to every row.
        if id_cols:
            species = _join_identifier(rec.get(c, "") for c in id_cols)
            if rec.get("_is_group_row"):
                # a lone genus heading its species — remember it, emit nothing
                if species and species[:1].isupper() and len(species.split()) == 1:
                    band_genus = species
                continue
            # Under an active band, a lone epithet (incl. a glued authority like
            # 'abruptaSay') is only the species half; prepend the genus and keep
            # just the leading lowercase run as the epithet (drops the authority).
            if band_genus and species[:1].islower():
                m = re.match(r"[^\WA-Z\d_]+", species)
                epithet = m.group(0) if m else species
                species = f"{band_genus} {epithet}"
        else:
            if rec.get("_is_group_row"):
                continue
            species = fallback_species
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
            # The extracted value is kept VERBATIM — including a taxon name's
            # authority/family ('Schizocosa rovneriUetz & Dondale,1979
            # (Lycosidae)'). Splitting a glued authority deterministically risks
            # dropping real information (a morphospecies letter 'sp. A', an
            # internal-capital epithet), so we do not mutate it here. The
            # evaluator instead judges such value differences as trivial in its
            # severity pass, and the CSV carries the faithful full name.
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


def _looks_cryptic_code(header: str) -> bool:
    """True for a dataset COLUMN CODE that a reader can't take at face value —
    'WingsHR', 'Volt', 'Tmean', 'T95L', 'Flight_Months', 'hp'. These come from
    supplement spreadsheets and must be interpreted from the paper, whereas a
    plain header ('Body length (mm)', 'Tongue Length') is already the trait name.

    Cryptic = no internal space (after dropping a trailing unit paren) AND a
    STRONG machine-code signal: an underscore, an embedded digit, or a camelCase
    boundary (lower->UPPER). We deliberately do NOT treat a plain short word as
    cryptic — a short jargon label ('Lecty', 'Mass', 'Volt') is often exactly the
    term the ground truth uses, so rewriting it would break a match that already
    worked. Plain multi-word headers always have a space and are never cryptic."""
    if not isinstance(header, str):
        return False
    h = re.sub(r"\s*\([^()]*\)\s*$", "", header).strip()   # drop a trailing unit
    if not h or " " in h:
        return False
    has_underscore = "_" in h
    has_digit = any(c.isdigit() for c in h)
    camel = any(h[i].islower() and h[i + 1].isupper() for i in range(len(h) - 1))
    return has_underscore or has_digit or camel


def agent_humanize_cryptic_types(headers: list, paper_text: str, llm=None) -> dict:
    """Ask the LLM to name cryptic dataset codes from the paper's methods.

    Only the codes flagged by _looks_cryptic_code are sent; a plain header is
    already its own trait name and is never rewritten. The model returns
    {code: human-readable trait name} grounded in the paper's own wording; a code
    it cannot place (or one that is already an ordinary word) is returned
    unchanged and dropped by the caller. This is the ONE place the model is
    allowed to reword a header, and only for codes a reader could not interpret."""
    cryptic = [h for h in headers if _looks_cryptic_code(h)]
    if not cryptic:
        return {}
    system = (
        "You are given cryptic COLUMN CODES from one scientific paper's dataset "
        "and the paper's text. For each code, return a short human-readable trait "
        "name (2-5 words) for WHAT that column records, grounded in the paper's "
        "methods and its own wording. Examples of the reasoning: a code 'Volt' in "
        "a paper that discusses 'voltinism' -> 'voltinism'; 'Flight_Months' where "
        "the methods say 'number of months during which adults occur' -> 'number "
        "of months adults fly'; 'hp' where the text says 'number of host plant "
        "genera' -> 'number of host plant genera'.\n\n"
        "RULES:\n"
        "- Use only meanings the paper's text supports; never invent a trait.\n"
        "- If a code is already an ordinary English trait word, or you cannot tell "
        "what it means from the text, return it UNCHANGED.\n"
        "- Return ONLY a JSON object {\"<code>\": \"<trait name>\", ...} for the "
        "codes given, nothing else."
    )
    # The codes are defined in the methods, which sit early in the paper; send a
    # bounded slice so this second whole-paper pass stays fast (the full text can
    # be 100k+ chars, which times the small model out).
    text = paper_text[:20000]
    user = ("Codes:\n" + json.dumps(cryptic, ensure_ascii=False, indent=2)
            + "\n\nPaper text:\n" + text)
    try:
        content = (llm.invoke([{"role": "system", "content": system},
                               {"role": "user", "content": user}]).content
                   if llm else
                   invoke_sized([{"role": "system", "content": system},
                                 {"role": "user", "content": user}]))
        parsed = loads_salvaging(content)
    except Exception as ex:
        # Humanization is a best-effort enhancement; never let it fail the paper.
        print(f"  humanize: skipped ({type(ex).__name__}); keeping raw codes")
        return {}
    if not isinstance(parsed, dict):
        return {}
    # Keep only real, changed, multi-informative names (a bare echo or a value
    # that is itself still cryptic is dropped, so nothing gets worse).
    out = {}
    for code in cryptic:
        name = parsed.get(code)
        if (isinstance(name, str) and name.strip()
                and name.strip().lower() != code.strip().lower()
                and not _looks_cryptic_code(name.strip())):
            out[code] = name.strip()
    return out


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

    # Cryptic supplement codes ('WingsHR', 'Volt', 'Flight_Months', 'hp') are not
    # abbreviations the glossary catches (nothing in the text says 'WingsHR =
    # ...'), yet they are unreadable as trait names. Have the LLM name them from
    # the methods prose; only the codes _looks_cryptic_code flags are touched, so
    # plain headers on other papers are never reworded.
    humanized = agent_humanize_cryptic_types(headers, paper_text, llm=llm)

    n = 0
    n_stat = 0
    for mapping in mappings.values():
        # one sample-size column per table, linked to that table's aggregates
        size_col = _find_sample_size_column(mapping)
        for header, m in mapping.items():
            if not (m.get("field") == "measurementType" and m.get("category") is not None):
                continue
            expanded = _apply_glossary(header, glossary)
            # If the glossary left a cryptic code unchanged, fall back to the
            # LLM-humanized name (grounded in the methods) so 'WingsHR' -> 'wingspan'.
            if expanded == header and header in humanized:
                expanded = humanized[header]
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

def add_long_table_to_grouped(table: Table, mapping: dict, grouped: dict,
                              longspec: dict, fallback_species: Optional[str] = None,
                              decode: Optional[dict] = None) -> dict:
    """Emit records from a LONG/TIDY table, where each ROW is already one
    measurement: the measurementType is the value of the trait-name column and
    the value is the paired measurement column (Noriega2023: Species | ... |
    Trait | Measurement). The wide path (add_table_to_grouped) can't read this —
    it would map Trait/Measurement as two columns and never expand the rows.

    `longspec` = {'type_col', 'value_col'} from long_format.detect_long_in_table.
    `decode` optionally maps a trait code (case-folded) to a full name; unknown
    codes pass through verbatim.
    """
    type_col = table.resolve(longspec["type_col"])
    value_col = table.resolve(longspec["value_col"])
    if type_col is None or value_col is None:
        return grouped
    id_cols = _identifier_columns(table, mapping)
    if not id_cols and not fallback_species:
        print(f"    skip long table {table.source}#{table.table_index} — "
              f"no identifier column and no paper-level species")
        return grouped
    dmap = {_decode_key(k): v for k, v in (decode or {}).items()}

    n = 0
    for rec in table.data_records():
        species = (_join_identifier(rec.get(c, "") for c in id_cols) if id_cols
                   else fallback_species)
        if not species:
            continue
        code = (rec.get(type_col.name, "") or "").strip()
        value = (rec.get(value_col.name, "") or "").strip()
        if not code or value == "":
            continue
        mtype = dmap.get(_decode_key(code), code)
        entry = grouped.setdefault(species, {
            "verbatimIdentification": species,
            "measurements": [],
        })
        entry["measurements"].append({
            "measurementType": mtype,
            "measurementValue": value,
        })
        n += 1
    print(f"    [long] {table.source}#{table.table_index}: {n} record(s) from "
          f"tidy table (type='{type_col.name}', value='{value_col.name}')")
    return grouped


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
        if not mapping:
            continue
        # A tidy/long table (trait-name column + value column) is read row-wise;
        # everything else goes through the normal wide path.
        longspec = detect_long_in_table(table)
        if longspec:
            add_long_table_to_grouped(table, mapping, grouped, longspec,
                                      fallback_species=fallback_species.get(tid))
        else:
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

    # The tables' own headers are strong role evidence: a species that shows up
    # as a column header or treatment label is a condition, not the subject.
    headers = [", ".join(t.header_names) for t, _ in mapped if t.header_names]
    verdict = agent_resolve_paper_species(cands, paper_text,
                                          table_headers=headers, llm=llm)

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
        # What the OTHER binomials in the paper were judged to be (diet, host,
        # cited comparison...). This is the audit trail for the risky call: if a
        # species that was really measured got filed as 'diet', the rows keyed to
        # the wrong organism are explained here rather than being a mystery.
        "roles": v.get("roles", {}),
        "candidates": v.get("candidates", []),
    }


def agent_resolve_paper_species(candidates: list, paper_text: str,
                                table_headers=None, llm=None) -> Optional[dict]:
    """One call per paper: whose measurements are in these tables?

    NOT "does the paper mention one species" — that question is too coarse and
    got Ferreira wrong. A paper naming three binomials can still measure exactly
    one of them: 'Scymnus nubilus fed on Aphis fabae or Myzus persicae' measures
    the predator, while the two aphids are the DIET, i.e. a treatment level. Asked
    "is this a single-species study?" a model correctly answers no, and the
    tables — all of them measurements of the predator — get dropped.

    So the model is asked to assign a ROLE to every candidate (measured subject /
    diet / prey / host / parasite / habitat / cited-comparison) and to name the
    one that is MEASURED. The safety valve is unchanged in effect: if two
    candidates are both measured subjects, the answer is null and nothing is
    attributed — which is still the right outcome when identifier detection has
    quietly failed on a genuinely multi-species table.

    The model picks only from `candidates` — the binomials the deterministic scan
    actually found — so it chooses among evidence rather than generating a name.
    It also sees the mention/abbreviation counts (the study organism is written
    out once and abbreviated thereafter) and the tables' COLUMN HEADERS, which
    often settle the role question outright: a species appearing as a column
    header or a treatment label is a condition, not a subject.

    Returns {single_species, species, roles, reasoning, decided_by} — or None if
    the call failed or the reply was unusable, which tells the caller to fall back
    to the deterministic test rather than guess.
    """
    names = [c["name"] for c in candidates[:5]]
    evidence = "\n".join(
        f'- "{c["name"]}": written in full {c["mentions"]}x, '
        f'abbreviated ("{c["name"][0]}. {c["name"].split()[-1]}") '
        f'{c["abbrev_mentions"]}x'
        for c in candidates[:5])
    headers_block = ""
    if table_headers:
        shown = "\n".join(f"- table {i}: {h}" for i, h in enumerate(table_headers))
        headers_block = f"""
Column headers of the paper's tables (none of them names a species — that is why
you are being asked). A candidate that appears here, or as a treatment/group
label, is a CONDITION of the experiment, not its subject:
{shown}
"""

    prompt = f"""A biological paper's tables report measurements, but no table has
a species column. Your task: identify WHICH species those measurements are OF, or
say that they are not all of one species.

A paper commonly names several species while measuring only one. The others
appear in supporting roles:
  - diet / prey / food source (e.g. "<predator> fed on <prey species>")
  - host plant, host animal, or parasite
  - a species compared against only by citing other papers
  - the source of a habitat or nest the subject occupies
None of those are measured. The measured subject is the organism whose body,
behaviour, survival, development or performance the numbers describe.

Answer with null ONLY when the measurements themselves span more than one
species — the paper reports per-species results for two or more organisms it
measured. In that case attributing one name would be wrong.

Candidate names found in the text, with how they are used:
{evidence}

A name written out once and then abbreviated many times is being used as a
principal organism. Abbreviation alone does not make it the MEASURED one — a
diet species gets abbreviated too — so use the text.
{headers_block}
Paper text (excerpt):
{paper_text[:8000]}

Answer JSON only. "species" must be copied exactly from {names}, or be null.
Give a role for every candidate you can place.
{{"species": "<name or null>",
  "roles": {{"<candidate name>": "measured subject|diet|prey|host|parasite|habitat|cited comparison|unclear"}},
  "reasoning": "<at most 25 words: what the measurements are of, and what the other names are doing>"}}"""

    try:
        content = (llm.invoke(prompt).content if llm else invoke_sized(prompt))
        out = loads_salvaging(content)
    except Exception as e:
        print(f"    [species] LLM call failed ({type(e).__name__}: {e}); "
              f"falling back to the deterministic test")
        return None
    if not isinstance(out, dict) or "species" not in out:
        print(f"    [species] unusable reply {str(out)[:120]!r}; "
              f"falling back to the deterministic test")
        return None

    species = str(out.get("species") or "").strip()
    # 'null species' IS the multi-species verdict now — there is no separate
    # boolean for the model to contradict itself with.
    single = bool(species) and species.lower() not in {"null", "none"}
    roles = out.get("roles") if isinstance(out.get("roles"), dict) else {}
    reasoning = str(out.get("reasoning") or "").strip()

    if single and species not in names:
        # Refuse a name the text scan never found: that is generation, not choice.
        print(f"    [species] rejected {species!r} — not among the candidates "
              f"{names}; leaving unattributed")
        return {"single_species": False, "species": None, "roles": roles,
                "reasoning": f"model proposed {species!r}, which is not a "
                             f"binomial found in the paper text",
                "decided_by": "llm-rejected"}

    if roles:
        print("    [species] roles: " + ", ".join(
            f"{k} = {v}" for k, v in list(roles.items())[:5]))
    print(f"    [species] measured subject = {species or None!r} ({reasoning})")
    return {"single_species": single, "species": species or None, "roles": roles,
            "reasoning": reasoning or "(model gave no reasoning)",
            "decided_by": "llm"}


# ---------------------------------------------------------------------------
# Convenience orchestration
# ---------------------------------------------------------------------------

def map_and_group(sources, paper_text, out_dir=".", llm=None):
    out_dir = Path(out_dir)
    sources = list(sources)
    tables = collect_tables(sources, llm=llm)
    print(f"Collected {len(tables)} table(s) from {len(sources)} file(s)")

    # Orientation pass: some papers publish the TRANSPOSE — species across the
    # header, traits down the first column. To the mapper that is
    # indistinguishable from a stats table (no header names a species), so every
    # such table is dropped as "not specimen data" and the paper yields nothing.
    # Rotating here, before anything else looks at the header, means the rest of
    # the pipeline never has to know: it sees an ordinary identifier x trait grid.
    print("  Checking table orientation (transposed tables)...")
    oriented: list[Table] = []
    for table in tables:
        rotated, ev = maybe_transpose(table)
        oriented.append(rotated)
    tables = oriented

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

    # Recover trait columns the mapper CATEGORIZED as measurements but left with
    # field=None because its field-assignment reply truncated on a wide table
    # (Raine2018: 21 of 31 columns, ~35k rows, dropped silently). Runs AFTER
    # relevance (so 'category' is populated) and BEFORE canonicalize (so the
    # recovered columns also get a canonicalType). See repair_mapping.
    for sig in order:
        _, n_fix = repair_mapping(rep_mapping[sig])
        if n_fix:
            rep = groups[sig][0]
            print(f"    repaired {n_fix} truncated field(s) in "
                  f"{rep.source}#{rep.table_index}")

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