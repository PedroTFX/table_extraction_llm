"""score_v24.py — one v24 layer set (V24_LAYERS, as full_run_v24.py reads it) against v18, both scored now with the same
scorer, on the papers whose table rows differ in any field (a unit alone changes no key, so v18's saved reports cannot
be reused for the unit agreement).

  <root>/rescore_v24/v18/<paper>, <root>/rescore_v24/<layers>/<paper>     (TREE_OUTPUT picks another set's root)
  printed: per group (dev, held_a by name; held_b, grit only as totals) mean F1 over the group's changed papers, the
  papers that fall more than 0.01, measurementUnit agreement on matched rows, rows carrying a unit, rows written
  -> <root>/rescore_v24/V24_<layers>_TOTALS.txt

    V24_LAYERS=units python score_v24.py [papers]       resumable: reports already written are kept
"""
import csv
import filecmp
import json
import os
import re
import shutil
import sys

import _paths
import evaluate as ev

ev.ASSESS_MISS_SEVERITY = False
ALL_LAYERS = ("units", "account", "relevance", "rowlabel")
LAYERS = tuple(x for x in ALL_LAYERS
               if x in (os.environ.get("V24_LAYERS") or ",".join(ALL_LAYERS)).replace("+", ",").split(","))
TAG = "all" if LAYERS == ALL_LAYERS else "+".join(LAYERS)
V18 = _paths.OUTPUT / "full_run_v18"
V24 = _paths.OUTPUT / ("full_run_v24" if LAYERS == ALL_LAYERS else "full_run_v24_" + "+".join(LAYERS))
ROOT = _paths.OUTPUT / "rescore_v24"
SPLITS = [_paths.SUB / "output/eval_split/split_v15.json", _paths.OUTPUT / "eval_split/split_grit.json"]


def groups():
    out = {}
    for f in SPLITS:
        if f.exists():
            for p, g in json.loads(f.read_text(encoding="utf-8"))["assign"].items():
                out.setdefault(p, g)
    return out


def changed(papers):
    out = []
    for p in papers:
        a, b = V18 / p / f"{p}.csv", V24 / p / f"{p}.csv"
        if a.exists() and b.exists() and not filecmp.cmp(a, b, shallow=False):
            out.append(p)
    return out


def rows_of(f):
    with open(f, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def read(rep):
    t = rep.read_text(encoding="utf-8", errors="ignore") if rep.exists() else ""
    m = ev._metrics_from_report(rep) if rep.exists() else None
    u = re.search(r"^\s*measurementUnit\s+(\d+)\s+(\d+)", t, re.M)
    return {"f1": float(m[2]) if m else 0.0, "u_ok": int(u[1]) if u else 0, "u_n": int(u[2]) if u else 0}


def main(argv):
    every = sorted(d.name for d in V24.iterdir() if (d / f"{d.name}.csv").exists())
    papers = changed(argv or every)
    for name, src in (("v18", V18), (TAG, V24)):
        for p in papers:
            (ROOT / name / p).mkdir(parents=True, exist_ok=True)
            dst = ROOT / name / p / f"{p}.csv"
            if not dst.exists() or not filecmp.cmp(src / p / f"{p}.csv", dst, shallow=False):
                shutil.copy(src / p / f"{p}.csv", dst)
                (ROOT / name / p / f"{p}_report.txt").unlink(missing_ok=True)
        print(f"=== scoring {name}: {len(papers)} papers", flush=True)
        ev.evaluate_all(_paths.PAPERS, ROOT / name, ev.DEFAULT_KEY, False, semantic=True, use_llm=True,
                        skip_existing=True)
    grp = groups()
    L = [f"v24 {TAG} vs v18: {len(papers)} papers whose rows differ (of {len(every)})"]
    for g in ("dev", "held_a", "held_b", "grit"):
        ps = [p for p in papers if grp.get(p, "grit") == g]
        if not ps:
            continue
        a = {p: read(ROOT / "v18" / p / f"{p}_report.txt") for p in ps}
        b = {p: read(ROOT / TAG / p / f"{p}_report.txt") for p in ps}
        ra = {p: rows_of(V18 / p / f"{p}.csv") for p in ps}
        rb = {p: rows_of(V24 / p / f"{p}.csv") for p in ps}
        units = lambda d: sum(bool((r.get("measurementUnit") or "").strip()) for rows in d.values() for r in rows)
        s = lambda d, k: sum(x[k] for x in d.values())
        down = [p for p in ps if b[p]["f1"] < a[p]["f1"] - 0.01]
        L.append(f"  {g:7s} {len(ps):3d} papers  mean F1 {s(a, 'f1') / len(ps):.3f} -> {s(b, 'f1') / len(ps):.3f}   "
                 f"up {sum(b[p]['f1'] > a[p]['f1'] + 0.01 for p in ps)}, down more than 0.01: {len(down)}   "
                 f"unit agrees on matched rows {s(a, 'u_ok')}/{s(a, 'u_n')} -> {s(b, 'u_ok')}/{s(b, 'u_n')}   "
                 f"rows with a unit {units(ra)} -> {units(rb)}   rows {sum(map(len, ra.values()))} -> "
                 f"{sum(map(len, rb.values()))}")
        if g in ("dev", "held_a"):
            for p in ps:
                L.append(f"      {p:22s} F1 {a[p]['f1']:.3f} -> {b[p]['f1']:.3f}   unit {a[p]['u_ok']}/{a[p]['u_n']} -> "
                         f"{b[p]['u_ok']}/{b[p]['u_n']}   rows {len(ra[p])} -> {len(rb[p])}")
    (ROOT / f"V24_{TAG}_TOTALS.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main(sys.argv[1:])
