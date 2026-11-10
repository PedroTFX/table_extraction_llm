"""8A: which papers the name normaliser of 2026-11-10 changes. Files only, no model: the scorer's two passes without the
model (normalise, containment) are run with the old and the new normaliser on each paper's GT and two_step names.

  109    papers named for dev and held_a; held_b as a count only
  grit   a count only (grit-only papers are never named; papers also in the 109 are named under the 109)

    python norm_compare.py      -> tree_extraction/output/eval_split/stats/norm_compare.json (+ the papers to rescore)
"""
import importlib.util
import json
import os
import sys

import beyond_gt as bg

ev = bg.ev
SRC = bg.REPO / "source" / "trait_name_matcher.py"
GRIT_PAPERS = bg.REPO / "data" / "grit_testing"
GRIT_OUT = bg.TE / "output_grit"


def matcher(flag):
    os.environ["EVAL_NAME_NORM"] = flag
    spec = importlib.util.spec_from_file_location(f"tnm_{flag}", SRC)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


OLD, NEW = matcher("0"), matcher("1")
os.environ["EVAL_NAME_NORM"] = "1"


def maps(m, gt_names, pred_names):
    gt_names, pred_names = sorted(set(gt_names)), sorted(set(pred_names))
    a, up, ug = m.deterministic_match(gt_names, pred_names)
    b, _up, _ug = m.containment_match(ug, up)
    return {**a, **b}


def main():
    res = {"109": {"changed": [], "held_b changed": 0, "papers": 0}, "grit": {"changed": 0, "papers": 0, "list": []}}
    for name, papers, out, assign in (("109", bg.PAPERS, bg.OUT, bg.SPLIT),
                                      ("grit", GRIT_PAPERS, GRIT_OUT, None)):
        for d in sorted(papers.iterdir()):
            p = d.name
            pred_f, gt_f = out / "two_step" / p / f"{p}.csv", d / f"{p}.xlsx"
            if not (pred_f.exists() and gt_f.exists()):
                continue
            gt = {bg.flat(r.get("measurementType")) for r in ev.load_xlsx(str(gt_f))} - {""}
            pred = {bg.flat(r.get("measurementType")) for r in ev.load_csv(str(pred_f))} - {""}
            a, b = maps(OLD, gt, pred), maps(NEW, gt, pred)
            res[name]["papers"] += 1
            if a == b:
                continue
            diff = {k: [a.get(k), b.get(k)] for k in set(a) | set(b) if a.get(k) != b.get(k)}
            res["grit" if name == "grit" else "109"].setdefault("list", []).append(p)
            if name == "grit":
                res["grit"]["changed"] += 1
            elif assign.get(p) in ("dev", "held_a"):
                res["109"]["changed"].append({"paper": p, "group": assign[p], "pairs": diff})
            else:
                res["109"]["held_b changed"] += 1
    f = bg.OUT / "eval_split/stats/norm_compare.json"
    f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print("109:", res["109"]["papers"], "papers,", len(res["109"]["changed"]), "tuning changed,",
          res["109"]["held_b changed"], "held_b changed")
    print("grit:", res["grit"]["papers"], "papers,", res["grit"]["changed"], "changed")
    for x in res["109"]["changed"]:
        for k, (o, n) in x["pairs"].items():
            print(f"  {x['paper']:22s} {k!r}: {o!r} -> {n!r}")


if __name__ == "__main__":
    sys.exit(main())
