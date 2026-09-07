"""
test_integration.py — verify the wiring inside table_to_data.py:
  * build_grouped routes a tidy table to the long path (row-wise expansion)
  * build_grouped leaves a wide table on the normal path
  * repair_mapping promotes truncated-field trait columns before grouping

No LLM needed: Tables are built with parse_table, mappings are supplied directly.
Run from a dir containing the source modules (or /mnt/user-data/outputs).

    python test_integration.py
"""
import sys
import types

# build_grouped needs no LLM; stub the column_relevance import so table_to_data loads
cr = types.ModuleType("column_relevance")
cr.agent_define_columns_relevance = cr.make_llm = cr.invoke_sized = cr.loads_salvaging = (
    lambda *a, **k: None)
sys.modules.setdefault("column_relevance", cr)

import table_to_data as td
from tables import parse_table
from long_format import detect_long_in_table
from repair_mapping import repair_mapping


def _tidy_table():
    rows = ["Species | Specimen number | Trait | Measurement"]
    data = [("Ataenius_sp1", 1, "HL", 0.83), ("Ataenius_sp1", 1, "HW", 0.51),
            ("Ataenius_sp1", 1, "PW", 0.60), ("Uroxys_sp", 2, "HL", 0.90),
            ("Uroxys_sp", 2, "HW", 0.55), ("Uroxys_sp", 2, "PW", 0.64),
            ("Ataenius_sp1", 3, "HL", 0.81), ("Ataenius_sp1", 3, "HW", 0.52),
            ("Ataenius_sp1", 3, "PW", 0.59), ("Uroxys_sp", 4, "HL", 0.88)]
    for s, n, t, m in data:
        rows.append(f"{s} | {n} | {t} | {m}")
    return parse_table("\n".join(rows), source="p.md", table_index=8)


def _wide_table():
    w = ("Species | Head length | Head width | Thorax width\n"
         "Ataenius sp1 | 0.83 | 0.51 | 0.60\n"
         "Uroxys sp | 0.90 | 0.55 | 0.64")
    return parse_table(w, source="p.md", table_index=0)


def main():
    fails = []
    t_tidy, t_wide = _tidy_table(), _wide_table()

    if detect_long_in_table(t_tidy) is None:
        fails.append("tidy table not detected by detect_long_in_table")
    if detect_long_in_table(t_wide) is not None:
        fails.append("wide table wrongly detected as tidy")

    map_tidy = {
        "Species": {"field": "verbatimIdentification", "category": "Categorical biological trait"},
        "Specimen number": {"field": None, "category": None},
        "Trait": {"field": "measurementType", "category": "Morphological measurement"},
        "Measurement": {"field": None, "category": None}}
    map_wide = {
        "Species": {"field": "verbatimIdentification", "category": "Categorical biological trait"},
        "Head length": {"field": "measurementType", "category": "Morphological measurement", "canonicalType": "Head length"},
        "Head width": {"field": "measurementType", "category": "Morphological measurement", "canonicalType": "Head width"},
        "Thorax width": {"field": "measurementType", "category": "Morphological measurement", "canonicalType": "Thorax width"}}

    g = td.build_grouped([t_tidy, t_wide],
                         {td.table_id(t_tidy): map_tidy, td.table_id(t_wide): map_wide})
    allm = [m for sp in g for m in g[sp]["measurements"]]
    if len(allm) != 10 + 6:
        fails.append(f"expected 16 measurements (10 tidy + 6 wide), got {len(allm)}")
    if any(m["measurementType"] == "Trait" for m in allm):
        fails.append("literal 'Trait' leaked as a measurementType (wide path took the tidy table)")
    if not any(m["measurementType"] == "HL" and m["measurementValue"] == "0.83" for m in allm):
        fails.append("tidy expansion missing HL=0.83")
    if not any(m["measurementType"] == "Head length" for m in allm):
        fails.append("wide table trait names missing")

    # repair path: a truncated-field mapping gains measurementType before grouping
    trunc = {
        "Species": {"field": "verbatimIdentification", "category": "Categorical biological trait"},
        "Body length": {"field": "measurementType", "category": "Morphological measurement"},
        "Head width": {"field": None, "category": "Morphological measurement"},
        "Wing area": {"field": None, "category": "Morphological measurement"}}
    _, n = repair_mapping(trunc)
    if n != 2 or trunc["Head width"]["field"] != "measurementType":
        fails.append(f"repair_mapping did not promote truncated trait columns (n={n})")

    if fails:
        print("FAIL:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("integration checks passed")


if __name__ == "__main__":
    main()
