"""
legend_calib.py — the calibration set for model-based legend recognition (2026-11-24, after the review of the
R3abc labels). Each SOURCE UNIT once, with a stable id from its place in the paper and all the columns R3abc linked it
to; the gold labels (written by hand into calib_gold.json) have three levels:
  unit     does it define codes; subtype: code legend / variable abbreviation / figure key / formula / none
  mapping  every exact code -> term pair it prints, with the variable it belongs to
  target   for each candidate column, which of those mappings decode that column

  build   (code only) the units of the two labelled samples that R3abc keeps, matched back to their source units,
          plus the known controls, each with its full text and its candidate columns
          -> TREE_OUTPUT/legend_coverage/calib_units.json, calib_units.txt (for reading and labelling)

Unit ids: '<paper>#p<n>' for the n-th prose paragraph (as legend_inventory cuts them; captions and numbered lists
are paragraphs too), '<paper>#t<k>r<r>' for a table row or footnote row, '<paper>#t<k>r<r>c<c>' for a head cell.
"""
from __future__ import annotations

import csv
import json
import sys

import _paths
import full_run_v24 as fr
import header_tree as ht
import header_tree_bench as hb
import legend_ablation as la
import legend_coverage as lc

OUT = lc.OUT
SAMPLES = [_paths.SUB / "output/legend_coverage/ablation_sample_2026-11-24.csv",
           _paths.SUB / "output/legend_coverage/verification_sample_2026-11-24.csv"]
CONTROLS = [(p, needle) for p, needle, _w in la.POSITIVE] + [
    ("MacDonald2021", "Three hypotheses, each"), ("Scalercio2020", "Populations inhabiting Mediterranean")]


def uid(paper, u):
    if u["table"] is None:
        return f"{paper}#p{u['id']}"
    if u["structure"] == "head cell":
        return f"{paper}#t{u['table']}r{u['row']}c{u['col']}"
    return f"{paper}#t{u['table']}r{u['row']}"


def build():
    wanted = []
    for f in SAMPLES:
        for r in csv.DictReader(open(f, encoding="utf-8")):
            wanted.append((f.stem, r))
    papers = sorted({r["paper"] for _s, r in wanted} | {p for p, _n in CONTROLS})
    rows, _pp, _texts = la.features(papers)
    keep = la.variant(rows, "abc")
    head = fr.head_runs()
    units = {}
    for p in papers:
        grids = {k: ht.grid_from_html(h) for k, h in enumerate(hb.html_tables(p))}
        first = {e["table"]: e.get("first") or 1 for e in head[p]}
        for u in lc.units(p, grids, first):
            units[(p, u["id"])] = u
    by_unit = {}
    for r in keep:
        by_unit.setdefault((r["paper"], r["unit"]), []).append(
            {"table": r["table"], "col": r["col"], "header": r["header"], "codes": r["hit_strict"],
             "explicit": r["explicit_strict"], "why": r["why"]})

    def find(p, structure, ut, ur, text):
        for (pp, i), cols in by_unit.items():
            if pp != p:
                continue
            u = units[(pp, i)]
            if u["structure"] != structure:
                continue
            if u["table"] is None:
                if " ".join(u["text"].split()).startswith(text[:150]):
                    return i
            elif str(u["table"]) == str(ut) and str(u["row"]) == str(ur) \
                    and " ".join(u["text"].split()).startswith(text[:60]):
                return i
        return None

    picked, src, missed = {}, {}, []
    for name, r in wanted:
        i = find(r["paper"], r["structure"], r["unit_table"], r["unit_row"], r["text"])
        if i is None:
            missed.append(f"{name} n{r['n']} {r['paper']} {r['structure']}: not an R3abc candidate")
            continue
        picked[(r["paper"], i)] = True
        src.setdefault((r["paper"], i), []).append(f"{name} n{r['n']}")
    for p, needle in CONTROLS:
        for (pp, i) in by_unit:
            if pp == p and needle in units[(pp, i)]["text"]:
                picked[(pp, i)] = True
                src.setdefault((pp, i), []).append(f"control '{needle}'")
    out = []
    for (p, i) in sorted(picked):
        u = units[(p, i)]
        out.append({"uid": uid(p, u), "paper": p, "group": la.ls.SPLIT.get(p), "structure": u["structure"],
                    "text": " ".join(u["text"].split()), "candidate_columns": by_unit[(p, i)],
                    "from": src[(p, i)]})
    (OUT / "calib_units.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    L = [f"{len(out)} unique units ({sum(len(x['candidate_columns']) for x in out)} candidate columns); "
         f"sample rows not R3abc candidates: {len(missed)}"] + [f"  {m}" for m in missed] + [""]
    for x in out:
        L.append(f"=== {x['uid']} [{x['structure']}] from {', '.join(x['from'])}")
        L.append(x["text"][:2500])
        for c in x["candidate_columns"]:
            L.append(f"   -> t{c['table']}c{c['col']} {c['header'][:70]!r} codes {c['codes']} explicit {c['explicit']} "
                     f"({c['why']})")
        L.append("")
    (OUT / "calib_units.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:len(missed) + 2]))


if __name__ == "__main__":
    {"build": build}[sys.argv[1]]()
