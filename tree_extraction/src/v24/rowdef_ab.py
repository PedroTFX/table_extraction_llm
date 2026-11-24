"""
rowdef_ab.py — experiment C (2026-11-24, after the review of inventory_audit.py): legend entries printed one per
cell along a row of a wide table. Kratschmer2019 t8 is a 7-column codebook: 'Nesting type | Nesting habit of
respective … | G= Ground-nesting | A= Above-ground nesting | P= Parasitic'. The inventory reads tables of at most 4
columns, and a table's footnote row only when it is one wide cell, so such a row never reaches gemma.

The change, nothing else: a row of a table wider than 4 columns in which at least 2 cells each START with one
definition — a code (legend_inventory.CODE) then '=' or ': ' then a word ('G= Ground-nesting', 'pl= polylectic'; not
'p = 0.01', not the value 'Spring:summer'), and only one legend shape in the cell (a whole legend in one cell is a
data row's in-row key, Chichorro2022's 'unit_or_levels', set aside) — becomes a source unit of its own, the row's cells joined with ' | ' so the variable named in the row
comes with its codes. Only these units go to gemma, in their own batches, by legend_inventory.build unchanged;
what they yield is added to the existing inventory (header_ab.inventory). Head cells (experiment B) are not
included, so C is measured apart.

  units      (code only) the rows the rule takes on the tuning papers
  inventory  (gemma) the entries added and the key pairs recovered  -> output/rowdef_ab/INVENTORY.txt
  decode     (nimble) the key columns of the papers with added entries, with and without them  -> DECODE.txt
  report     the decode report again

    python rowdef_ab.py units | inventory | decode | report
"""
from __future__ import annotations

import re
import sys

import _paths
import boundary_ab as ba
import full_run_v24 as fr
import header_ab as ha
import header_tree as ht
import header_tree_bench as hb
import legend_inventory as li
import legend_scope as ls

OUT = _paths.OUTPUT / "rowdef_ab"
DEF_CELL = re.compile(rf"\s*{li.CODE}\s*(?:=|:\s)\s*[A-Za-z]")   # 'Spring:summer' is a value, 'A: Paracou' is not


def is_def_cell(t):
    """The cell starts with ONE definition: a whole legend in one cell ('1 = troglobiont, 2 = terricolous, …', a
    data row's in-row key) is not a codebook cell."""
    return bool(DEF_CELL.match(t)) and li.shape_hits(t) == 1


def row_units(paper, head=None):
    """[{id, kind, text}] — rows of tables wider than 4 columns with >= 2 cells that start with a definition."""
    out = []
    for k, h in enumerate(hb.html_tables(paper)):
        g = ht.grid_from_html(h)
        if g.ncols <= 4:
            continue
        for r in range(g.nrows):
            cells = [" ".join(str(g.at(r, c).text or "").split()) for c in range(g.ncols)
                     if g.at(r, c) and (g.at(r, c).r, g.at(r, c).c) == (r, c) and str(g.at(r, c).text or "").strip()]
            if sum(is_def_cell(t) for t in cells) >= 2:
                out.append({"id": f"r{len(out)}", "kind": f"row {r} of table {k}", "text": " | ".join(cells)})
    return out


def units():
    n = 0
    for p in ls.tuning_papers():
        us = row_units(p)
        if us:
            n += len(us)
            print(f"{p} [{ls.SPLIT[p]}]: {len(us)} rows")
            for u in us[:6]:
                print(f"    {u['kind']}: {u['text'][:200]}")
            if len(us) > 6:
                print(f"    … {len(us) - 6} more")
    print(f"{n} rows in the tuning papers")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "units":
        units()
    elif cmd == "inventory":
        ha.inventory(row_units, OUT, "experiment C, definition rows of wide tables as units", "definition row")
    elif cmd == "decode":
        ba.decode(OUT, "experiment C")
    else:
        ba.report(OUT, "experiment C")
