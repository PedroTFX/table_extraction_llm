"""
decode_compare.py — AUDIT (no model): production's decoder (step 4b, re-run on copies by
decode_prod_rerun.py) and decoder v2 (frozen run v2d) scored on the SAME species rows of
the corrected decoding key (output/decode_key/all/key.json), the same way.

Unit: one species row x one coded key column (a cell whose GT value differs from the
printed code). Each decoder's answer for that row is:
  right          the species gets the GT value (production: among its output values for
                 the species; v2: the decoded term of the cell), or the GT value plus a
                 trailing unit
  longer         v2's term holds the GT's words plus more (reported apart, not right)
  left / other   kept the code / gave another value
  no row         production produced no output rows for the species (its decoder never
                 saw the cell; v2 reads the table directly)
Rows split by whether the paper prints the legend (decode_key.where) — 'out of reach'
rows cannot be decoded from the paper by either.

    python decode_compare.py   -> output/decode_key/COMPARE.txt
"""

from __future__ import annotations

import collections
import json

import _paths
import column_role_bench as crb
import decode_chain as dc
import decode_key as dk
import decoder as v1
import decoder_v2 as v2
import header_tree as ht
import header_tree_bench as hb
from evaluate import load_xlsx


def prod_values(paper, gt):
    for d in ("prod_rerun", "prod_rerun_all"):
        f = dk.OUT / d / f"{paper}_grouped.json"
        if f.exists():
            vals = collections.defaultdict(list)
            for sp, rec in json.loads(f.read_text(encoding="utf-8")).items():
                rid = gt.match_id(sp)
                if rid:
                    vals[rid] += [str(m.get("measurementValue", "")) for m in rec.get("measurements", [])]
            return vals
    return None


def same(have, want):
    import re
    if dk.n(have) == dk.n(want) or v1._flat(have) == v1._flat(want):
        return True
    cut = re.sub(v1.UNIT_END, "", have)
    return cut != have and v1._flat(cut) == v1._flat(want)


def main():
    key = v1.load_key()
    rows = []
    for paper in sorted(key):
        coded = {T: e for T, e in key[paper].items() if e["kind"] == "coded"}
        if not coded:
            continue
        gt = crb.GroundTruth(load_xlsx(crb.paper_inputs(_paths.PAPERS / paper)[1]))
        pv = prod_values(paper, gt)
        mf = v2.OUT / "match" / f"{paper}.json"
        if pv is None or not mf.exists():
            continue
        m2 = json.loads(mf.read_text(encoding="utf-8"))
        grids = {k: ht.grid_from_html(h) for k, h in enumerate(hb.html_tables(paper))}
        for T, e in coded.items():
            g = grids[e["table"]]
            # the same lookup as the scorers: a table the chain joined to an earlier one
            # (a continuation) is found under that earlier table, not counted as missed
            dec2 = {k: v for k, v in m2.items() if not k.startswith("_")}
            cells2 = (dc.lookup(dec2, e["table"], e["col"]) or {}).get("cells", {})
            for r in range(g.nrows):
                x = g.at(r, e["col"])
                ids = {gt.match_id(str(g.at(r, c).text or "")) for c in range(g.ncols) if g.at(r, c)} - {None}
                if len(ids) != 1 or not x:
                    continue
                rid = ids.pop()
                cell = " ".join(str(x.text or "").split())
                if cell not in e["coded"]:
                    continue
                want = e["coded"][cell]
                w = e.get("where", {}).get(cell, "")
                reach = "out of reach" if (w in v1.NO_LEGEND or (paper, cell) in v1.GT_ERRORS
                                           or ((paper, "*") in v1.GT_ERRORS)) else "printed"
                have = pv.get(rid, [])
                p_out = ("no row" if not have else "right" if any(same(v, want) for v in have)
                         else "left" if any(dk.n(v) == dk.n(cell) for v in have) else "other")
                term = (cells2.get(cell) or {}).get("term")
                v_out = ("right" if term is not None and same(term, want)
                         else "longer" if term is not None and v2._contains(term, want)
                         else "shorter" if term is not None and v2._contains(want, term)
                         else "left" if term is None else "other")
                rows.append((paper, reach, p_out, v_out))
    L = [f"production (step 4b re-run) vs decoder v2 ({v2.OUT.name}) on the same species rows, "
         f"corrected key", ""]

    def table(sel, title):
        n = len(sel)
        if not n:
            return
        P = collections.Counter(r[2] for r in sel)
        V = collections.Counter(r[3] for r in sel)
        L.append(f"{title}: {n} species rows")
        L.append(f"   production  right {P['right']:5d} ({P['right'] / n:.0%})   left {P['left']}  other {P['other']}  no row {P['no row']}")
        L.append(f"   v2          right {V['right']:5d} ({V['right'] / n:.0%})   left {V['left']}  other {V['other']}  longer wording {V['longer']}  shorter wording {V['shorter']}")
        both = collections.Counter((r[2] == "right", r[3] == "right") for r in sel)
        L.append(f"   both right {both[(True, True)]}, only production {both[(True, False)]}, "
                 f"only v2 {both[(False, True)]}, neither {both[(False, False)]}")
        L.append("")

    printed = [r for r in rows if r[1] == "printed"]
    table(printed, "A. legend printed in the paper (decodable)")
    table([r for r in printed if r[2] != "no row"], "B. legend printed AND production produced the species' rows")
    table([r for r in rows if r[1] == "out of reach"], "C. out of reach (no printed legend / GT error)")
    L.append("per paper, A rows: production right / v2 right / rows (production no-row rows)")
    by = collections.defaultdict(list)
    for r in printed:
        by[r[0]].append(r)
    for p, rs in sorted(by.items()):
        L.append(f"  {p:20s} {sum(r[2] == 'right' for r in rs):5d} {sum(r[3] == 'right' for r in rs):5d} "
                 f"/ {len(rs):5d}   ({sum(r[2] == 'no row' for r in rs)})")
    out = dk.OUT / "COMPARE.txt"
    out.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
