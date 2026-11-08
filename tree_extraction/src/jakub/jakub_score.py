"""Scores for a run on one of Jakub's sets (wst_gt.py writes their GT in our template).

Run with TREE_PAPERS = the set (data/Jakub_papers/<set>) and TREE_OUTPUT = the run's own root, after two_step.py:
  tables     full_run_v18's rows, scored where they are (<root>/full_run_v18/<paper>/<paper>_report.txt)
  combined   two_step's rows (tables + prose where routed); a paper whose rows equal the tables' takes that report
  totals     per paper and over the set -> <root>/jakub_scores.csv: GT rows, route, rows, F1 (tables, combined),
             and the GT rows missed by statistic (the database stores a range as a min row and a max row)

    python jakub_score.py [tables] [combined] [totals]      all three when none is named
The scorer is the production one (semantic trait names, gemma); reports already written are kept.
"""
import collections
import csv
import filecmp
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "prose"))
import _paths
import evaluate as ev

ev.ASSESS_MISS_SEVERITY = False
V18 = _paths.OUTPUT / "full_run_v18"
TWO = _paths.OUTPUT / "two_step"


def papers():
    return sorted(d.name for d in _paths.PAPERS.iterdir() if d.is_dir() and (d / f"{d.name}_full.md").exists())


def score(root):
    ev.evaluate_all(_paths.PAPERS, root, ev.DEFAULT_KEY, False, semantic=True, use_llm=True, skip_existing=True)


def combined():
    same = 0
    for p in papers():
        a, b = TWO / p / f"{p}.csv", V18 / p / f"{p}.csv"
        if a.exists() and b.exists() and filecmp.cmp(a, b, shallow=False) and (V18 / p / f"{p}_report.txt").exists():
            shutil.copy(V18 / p / f"{p}_report.txt", TWO / p / f"{p}_report.txt")
            same += 1
    print(f"{same} papers take the tables' report", flush=True)
    score(TWO)


def report(root, p):
    f = root / p / f"{p}_report.txt"
    t = f.read_text(encoding="utf-8", errors="ignore") if f.exists() else ""
    g = lambda lab: int((re.search(lab + r"\s*:\s*(\d+)", t) or [0, 0])[1])
    m = re.search(r"SCOPED\s+P/R/F1\s*:\s*([\d.]+) / ([\d.]+) / ([\d.]+)", t)
    return dict(tp=g(r"matched \(TP\)"), fn=g(r"missed \(FN\)"), fp=g(r"spurious, in scope"),
                oos=g(r"spurious, out of scope"), f1=float(m[3]) if m else 0.0, ok=bool(t))


def gt_rows(p):
    rows = ev.load_xlsx(str(_paths.PAPERS / p / f"{p}.xlsx"))
    return [{k: ("" if v is None else str(v).strip()) for k, v in r.items()} for r in rows]


def num(v):
    try:
        return f"{float(v):g}"
    except ValueError:
        return v.strip().lower()


def missed_by_stat(p, gt):
    """GT rows missed in the combined run, by the GT row's statistic (the miss file gives species, trait, value)."""
    f = TWO / p / f"{p}_misses.csv"
    if not f.exists():
        return collections.Counter()
    stat = collections.defaultdict(list)
    for r in gt:
        stat[(r.get("verbatimIdentification", ""), r.get("measurementType", ""), num(r.get("measurementValue", "")))].append(
            r.get("measurementStatistic", ""))
    out = collections.Counter()
    with open(f, encoding="utf-8", newline="") as fh:
        for m in csv.DictReader(fh):
            k = (m.get("verbatimIdentification", ""), m.get("measurementType", ""), num(m.get("measurementValue", "")))
            out[(stat.get(k) or ["?"])[0]] += 1
    return out


def totals():
    st = json.loads((TWO / "status.json").read_text(encoding="utf-8")) if (TWO / "status.json").exists() else {}
    rows, by_stat, miss_stat = [], collections.Counter(), collections.Counter()
    for p in papers():
        gt = gt_rows(p)
        a, b, s = report(V18, p), report(TWO, p), st.get(p, {})
        ms = missed_by_stat(p, gt)
        by_stat.update(r.get("measurementStatistic", "") for r in gt)
        miss_stat.update(ms)
        rows.append({"paper": p, "gt_rows": len(gt), "route": s.get("route", ""), "why": s.get("why", ""),
                     "table_rows": s.get("table_rows", ""), "prose_rows": s.get("prose_rows", ""),
                     "tables_f1": a["f1"], "combined_f1": b["f1"], "tp": b["tp"], "fn": b["fn"], "fp": b["fp"],
                     "out_of_scope": b["oos"], "scored": b["ok"]})
    with open(_paths.OUTPUT / "jakub_scores.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    n = max(1, len(rows))
    tp, fn, fp = (sum(r[k] for r in rows) for k in ("tp", "fn", "fp"))
    pr, rc = tp / max(1, tp + fp), tp / max(1, tp + fn)
    print(f"{len(rows)} papers, {sum(r['gt_rows'] for r in rows)} GT rows")
    print(f"mean F1: tables {sum(r['tables_f1'] for r in rows) / n:.3f}, tables + prose {sum(r['combined_f1'] for r in rows) / n:.3f}")
    print(f"micro (tables + prose): TP {tp}, FN {fn}, FP in scope {fp}, out of scope {sum(r['out_of_scope'] for r in rows)}; "
          f"P {pr:.3f} R {rc:.3f} F1 {2 * pr * rc / max(1e-9, pr + rc):.3f}")
    print("routes:", dict(collections.Counter(f"{r['route']} ({r['why']})" for r in rows)))
    print("papers at F1 0:", sum(r["combined_f1"] == 0 for r in rows))
    print("GT rows by statistic, missed / all:",
          {k: f"{miss_stat.get(k, 0)} / {v}" for k, v in by_stat.most_common()})
    for r in sorted(rows, key=lambda r: r["paper"]):
        print(f"  {r['paper']:10s} GT {r['gt_rows']:4d}  {r['route']:6s} table rows {str(r['table_rows']):>4s} "
              f"prose rows {str(r['prose_rows']):>4s}  F1 tables {r['tables_f1']:.3f}  + prose {r['combined_f1']:.3f}")


if __name__ == "__main__":
    steps = sys.argv[1:] or ["tables", "combined", "totals"]
    for s in steps:
        print(f"===== {s}", flush=True)
        {"tables": lambda: score(V18), "combined": combined, "totals": totals}[s]()
