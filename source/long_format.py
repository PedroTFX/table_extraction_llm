"""
long_format.py — extract specimen records from LONG / TIDY tables that the wide-
format pipeline cannot read.

The pipeline assumes one column per trait (wide). Some papers ship a tidy table
where the trait NAME is a column of values and the measurement is a paired value
column, e.g. Noriega2023 sheet S: one row per (specimen, trait):

    Site Code | ... | Species | Specimen number | Trait | Measurement
    MEX04Int  | ... | Ataenius_sp1 | 1 | HL | 0.83

Each such row already IS a (verbatimIdentification, measurementType, value)
triple; the wide mapper never expands the Trait column, so all these rows are
lost. This module detects that shape and emits the records directly.

Public API (what table_to_data would call):
    detect_long_tables(md_text)  -> list[LongTable]        # which tables are tidy
    records_from_md(md_text, decode=DUNG_BEETLE_TRAITS)    # emit specimen records

Run standalone to audit a paper:
    python long_format.py path/to/<paper>_full.md
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from dataclasses import dataclass


# --- column-name vocabulary (case-insensitive, exact-ish) ------------------
# A tidy table has a column whose CELLS are trait names, and a paired column
# whose cells are the measurements.
TYPE_COL_NAMES = {"trait", "variable", "parameter", "character",
                  "measurement type", "measurementtype", "trait name", "metric"}
VALUE_COL_NAMES = {"measurement", "value", "result", "measured value",
                   "observation", "reading", "amount", "score"}
ID_COL_NAMES = {"species", "taxon", "taxa", "scientific name", "binomial",
                "morphospecies", "species name"}

# Optional trait-abbreviation legend. Keys are match on a CASE-FOLDED, punctuation-
# stripped form, so 'mTL', 'MTL', 'm.TL' all collapse to one entry. This one
# matches Noriega2023's 'KEY to variables'; pass your own per paper.
DUNG_BEETLE_TRAITS = {
    "hl": "Head length", "hw": "Head width",
    "pl": "Pronotum length", "pw": "Pronotum width", "ph": "Pronotum height",
    "el": "Elytra length",
    "mtl": "Metatibia length", "ptl": "Protibia length", "ptw": "Protibia width",
    "biomass": "Biomass", "biomas": "Biomass",
    "reloc.size": "Relocation size", "relocsize": "Relocation size",
}


def _decode_key(s: str) -> str:
    return re.sub(r"[^a-z0-9.]", "", str(s).strip().lower())


@dataclass
class LongTable:
    index: int                 # position among <table> blocks
    header: list
    rows: list                 # list[list[str]] data rows (header excluded)
    id_col: int
    type_col: int
    value_col: int

    def summary(self) -> str:
        traits = Counter(r[self.type_col] for r in self.rows
                         if len(r) > self.type_col)
        return (f"table #{self.index}: {len(self.rows)} rows | "
                f"id='{self.header[self.id_col]}' "
                f"type='{self.header[self.type_col]}' "
                f"value='{self.header[self.value_col]}' | "
                f"{len(traits)} trait codes")


# --- html -> grid ----------------------------------------------------------

def _tables(md: str):
    return re.findall(r"<table.*?</table>", md, re.DOTALL | re.IGNORECASE)


def _grid(table_html: str):
    grid = []
    for r in re.findall(r"<tr[^>]*>(.*?)</tr>", table_html, re.DOTALL | re.IGNORECASE):
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.DOTALL | re.IGNORECASE)
        grid.append([re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", c)).strip()
                     for c in cells])
    return grid


def _looks_numeric(s: str) -> bool:
    return bool(re.match(r"^[-+]?\d*\.?\d+(e[-+]?\d+)?$", str(s).strip(), re.I))


def _find_col(header, names):
    for i, h in enumerate(header):
        if h.strip().lower() in names:
            return i
    return -1


# --- detection -------------------------------------------------------------

def detect_long_tables(md: str, min_rows=8, max_type_ratio=0.5):
    """Return the LongTables in this markdown.

    A table is tidy when it has, by column name, a type column and a value
    column (or a numeric column right after the type column), plus an identifier
    column. Guard: the type column must REPEAT — its distinct values are at most
    `max_type_ratio` of the row count — otherwise it is free text, not a key.
    """
    found = []
    for ti, html in enumerate(_tables(md)):
        grid = _grid(html)
        if len(grid) < min_rows + 1:
            continue
        header = grid[0]
        body = [r for r in grid[1:] if any(c.strip() for c in r)]
        if len(body) < min_rows:
            continue

        type_col = _find_col(header, TYPE_COL_NAMES)
        if type_col < 0:
            continue
        value_col = _find_col(header, VALUE_COL_NAMES)
        if value_col < 0:                       # fall back: numeric col after type
            for j in range(type_col + 1, len(header)):
                col = [r[j] for r in body if len(r) > j and r[j].strip()]
                if col and sum(_looks_numeric(c) for c in col) >= 0.7 * len(col):
                    value_col = j
                    break
        if value_col < 0:
            continue

        id_col = _find_col(header, ID_COL_NAMES)
        if id_col < 0:
            continue

        # guard: type column must be a repeating key, not prose
        tvals = [r[type_col] for r in body if len(r) > type_col and r[type_col].strip()]
        if not tvals or len(set(tvals)) > max_type_ratio * len(tvals):
            continue

        found.append(LongTable(ti, header, body, id_col, type_col, value_col))
    return found


# --- extraction ------------------------------------------------------------

def records_from_md(md: str, decode: dict | None = None, keep_specimen=False):
    """Emit one record per tidy-table data row.

    Each record: verbatimIdentification, measurementType, measurementValue
    (+ _species_raw, _trait_raw, _table for provenance/debug). `decode` maps a
    trait code (case-folded) to a full name; unknown codes pass through verbatim.
    """
    decode = {} if decode is None else {_decode_key(k): v for k, v in decode.items()}
    out = []
    for lt in detect_long_tables(md):
        for r in lt.rows:
            if len(r) <= max(lt.id_col, lt.type_col, lt.value_col):
                continue
            sp = r[lt.id_col].replace("_", " ").strip()
            code = r[lt.type_col].strip()
            val = r[lt.value_col].strip()
            if not sp or not code or val == "":
                continue
            mtype = decode.get(_decode_key(code), code)
            rec = {"verbatimIdentification": sp,
                   "measurementType": mtype,
                   "measurementValue": val,
                   "_species_raw": r[lt.id_col], "_trait_raw": code,
                   "_table": lt.index}
            if keep_specimen and len(r) > lt.id_col:
                rec["_specimen"] = r[min(lt.type_col - 1, len(r) - 1)]
            out.append(rec)
    return out


# --- Table-object detection (for the pipeline: table_to_data.build_grouped) ---

def detect_long_in_table(table, min_rows=8, max_type_ratio=0.5):
    """Detect a tidy/long table from a parsed Table object (duck-typed: needs
    .header_names and .column_values). Returns {'type_col', 'value_col'} or None.

    Same rule as detect_long_tables but on an already-parsed table: a column named
    like a trait key, a paired value column (named, or the first mostly-numeric
    column after it), and the type column must REPEAT (distinct values <=
    max_type_ratio of rows) so a free-text column is never mistaken for a key.
    This is intentionally strict so it fires ONLY on genuine tidy tables (Noriega)
    and never on wide morphometric/stats tables.
    """
    try:
        headers = list(table.header_names)
    except Exception:
        return None
    if not headers:
        return None
    low = {h: h.strip().lower() for h in headers}

    type_col = next((h for h in headers if low[h] in TYPE_COL_NAMES), None)
    if type_col is None:
        return None

    value_col = next((h for h in headers if low[h] in VALUE_COL_NAMES), None)
    if value_col is None:
        # fall back: first mostly-numeric column AFTER the type column
        after = headers[headers.index(type_col) + 1:]
        for h in after:
            vals = [v for v in table.column_values(h) if str(v).strip()]
            if vals and sum(_looks_numeric(v) for v in vals) >= 0.7 * len(vals):
                value_col = h
                break
    if value_col is None:
        return None

    tvals = [v for v in table.column_values(type_col) if str(v).strip()]
    if len(tvals) < min_rows or len(set(tvals)) > max_type_ratio * len(tvals):
        return None
    return {"type_col": type_col, "value_col": value_col}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    md = open(sys.argv[1], encoding="utf-8").read()
    longs = detect_long_tables(md)
    print(f"{sys.argv[1]}: {len(_tables(md))} table(s), "
          f"{len(longs)} tidy/long table(s) detected\n")
    for lt in longs:
        print("  " + lt.summary())

    recs = records_from_md(md, decode=DUNG_BEETLE_TRAITS)
    species = sorted({r["verbatimIdentification"] for r in recs})
    traits = Counter(r["measurementType"] for r in recs)
    print(f"\nrecords emitted : {len(recs)}")
    print(f"distinct species: {len(species)}")
    print(f"distinct traits : {len(traits)}")
    print("trait -> rows (decoded):")
    for t, n in traits.most_common():
        print(f"   {n:>5}  {t}")


if __name__ == "__main__":
    main()