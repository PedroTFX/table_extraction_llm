"""
header_ab.py — experiment B (2026-11-24, after the review of inventory_audit.py): legends printed inside the head
cells of wide data tables ('Zigum (1: underdeveloped; 2: developed 3: epizygum)', Tonelli2021 t7). The inventory's
source units are legend-shaped prose paragraphs, footnote rows and tables of at most 4 columns
(legend_inventory.units), so a head cell of a wider table never reaches gemma.

The change, nothing else: a head cell (above the table's first record, as the head reader found it) of a table wider
than 4 columns, with >= 2 legend shapes (legend_inventory.shape_hits, the prose units' threshold), becomes a source
unit of its own ('head cell of table k'). Only these new units are given to gemma, in their own batches, by
legend_inventory.build unchanged (passes A, C, B; the same boundary check), so the paper's existing entries and
batches stay as they are; the new entries are added to them.

  inventory  (gemma) on the tuning papers (dev + held_a): the new units, every entry they add and the decoding key's
             printed pairs it recovers  -> output/header_ab/INVENTORY.txt, added.json, units.json
  decode     (nimble) as boundary_ab.decode: the key columns of the papers with added entries, the inventory as it is
             and with the added entries, in one session  -> output/header_ab/DECODE.txt
  report     the decode report again

    python header_ab.py inventory | decode | report
TREE_OUTPUT picks the root (output_frozen_109: the frozen run's inventory and head reader).
"""
from __future__ import annotations

import collections
import json
import sys

import _paths
import boundary_ab as ba
import decode_inv as di
import decoder as v1
import decoder_v2 as v2
import full_run_v24 as fr
import header_tree as ht
import header_tree_bench as hb
import legend_inventory as li
import legend_scope as ls

OUT = _paths.OUTPUT / "header_ab"


def head_units(paper, head):
    """[{id, kind, text}] — head cells of tables wider than 4 columns with >= 2 legend shapes."""
    first = {e["table"]: e.get("first") or 1 for e in head.get(paper, [])}
    out = []
    for k, h in enumerate(hb.html_tables(paper)):
        g = ht.grid_from_html(h)
        if g.ncols <= 4 or k not in first:
            continue
        seen = set()
        for r in range(min(first[k], g.nrows)):
            for c in range(g.ncols):
                x = g.at(r, c)
                if not x or (x.r, x.c) in seen:
                    continue
                seen.add((x.r, x.c))
                t = " ".join(str(x.text or "").split())
                if li.shape_hits(t) >= 2:
                    out.append({"id": f"h{len(out)}", "kind": f"head cell of table {k}", "text": t})
    return out


def inventory(unit_fn=None, out=OUT, name="experiment B, head cells of wide tables as units", tag="head cell"):
    """unit_fn(paper, head) -> a paper's new units (default head_units; experiment C passes its own)."""
    unit_fn = unit_fn or head_units
    out.mkdir(parents=True, exist_ok=True)
    head = fr.head_runs()
    added, new_units, L = {}, {}, []
    tot = collections.Counter()
    for p in ls.tuning_papers():
        if p not in head or not (li.OUT / f"{p}.json").exists():
            continue
        us = unit_fn(p, head)
        if not us:
            continue
        saved = li.units
        li.units = lambda _paper, us=us: us              # build() reads its units from here; restored below
        try:
            inv = li.build(p)
        finally:
            li.units = saved
        old = json.loads((li.OUT / f"{p}.json").read_text(encoding="utf-8"))["categories"]
        have = {(e.get("variable", "").lower(), e.get("code"), (e.get("term") or e.get("label") or "").lower())
                for e in old}
        extra = [dict(e, added=tag) for e in inv["categories"]
                 if (e.get("variable", "").lower(), e.get("code"), (e.get("term") or e.get("label") or "").lower())
                 not in have]
        new_units[p] = us
        if extra:
            added[p] = extra
        cats = di.inventory(p) or []
        more = cats + [v2.strip_own_code(dict(e)) for e in extra]
        found = ls.key_of(p)
        weight = {(r["trait"], r["cell"]): r["w"] for r in v2.score_dir_from(p, found, lambda e: None)}
        rec = []
        for T, e in found.items():
            if e["kind"] != "coded":
                continue
            for code, term in e["coded"].items():
                if e["where"][code] not in v1.NO_LEGEND and not di.captured(cats, code, term) \
                        and di.captured(more, code, term):
                    rec.append(f"'{code}' -> '{term}' ({T}, x{weight.get((T, code), 1)})")
                    tot["pairs"] += 1
                    tot["rows"] += weight.get((T, code), 1)
        tot["units"] += len(us)
        tot["entries"] += len(extra)
        L.append(f"{p} [{ls.SPLIT[p]}]: {len(us)} new units, {len(extra)} entries added "
                 f"({len(inv['dropped'])} dropped by the boundary check); key pairs recovered: {', '.join(rec) or 'none'}")
        for u in us:
            L.append(f"    unit {u['id']} ({u['kind']}): {u['text'][:200]}")
        for e in extra:
            L.append(f"      + '{e.get('code')}' = '{e.get('term') or e.get('label')}'  (variable '{e.get('variable')}', "
                     f"label '{e.get('label')}', {e.get('unit')})")
        for d in inv["dropped"]:
            L.append(f"      - dropped '{d.get('code')}' = '{d.get('term')}'  ({d.get('why')})")
    v1.unload(v1.GEMMA)
    top = [f"{name}: {tot['units']} units in {len(new_units)} tuning papers, "
           f"{tot['entries']} entries added in {len(added)} papers; key pairs recovered {tot['pairs']} "
           f"({tot['rows']} species rows)", ""]
    (out / "added.json").write_text(json.dumps(added, indent=1, ensure_ascii=False), encoding="utf-8")
    (out / "units.json").write_text(json.dumps(new_units, indent=1, ensure_ascii=False), encoding="utf-8")
    (out / "INVENTORY.txt").write_text("\n".join(top + L) + "\n", encoding="utf-8")
    print("\n".join(top + L))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "inventory":
        inventory()
    elif cmd == "decode":
        ba.decode(OUT, "experiment B")
    else:
        ba.report(OUT, "experiment B")
