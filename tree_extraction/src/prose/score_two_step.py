"""
score_two_step.py — production scores for a two_step.py run, written apart so v18's own reports stay as the baseline.

    tables     v18's rows, scored into output/rescore_v18 with the current scorer and GT
    combined   output/two_step scored; a paper whose rows equal the tables' takes that report, so only papers with prose rows cost a call
    results    totals against the old baseline (output/full_run_v18/summary.csv), by paper group. Only dev and held_a papers are named.

    python score_two_step.py tables|combined|results         TREE_PAPERS / TREE_OUTPUT pick the set
Both scoring steps can be re-run after a stop: reports already written are kept.
"""
import collections
import csv
import filecmp
import json
import re
import shutil
import sys

import _paths
import evaluate as ev

ev.ASSESS_MISS_SEVERITY = False                  # asks gemma once per missed row: hours, and not part of the score
V18 = _paths.OUTPUT / "full_run_v18"
RES = _paths.OUTPUT / "rescore_v18"
TWO = _paths.OUTPUT / "two_step"
ASSIGN = json.loads((_paths.SUB / "output/eval_split/split_v15.json").read_text(encoding="utf-8"))["assign"]


def base():
    with open(V18 / "summary.csv", encoding="utf-8") as fh:
        return {r["paper"]: r for r in csv.DictReader(fh)}


def score(root):
    ev.evaluate_all(_paths.PAPERS, root, ev.DEFAULT_KEY, False, semantic=True, use_llm=True, skip_existing=True)


def tables():
    for p in base():
        src = V18 / p / f"{p}.csv"
        if src.exists():
            (RES / p).mkdir(parents=True, exist_ok=True)
            if not (RES / p / f"{p}.csv").exists() or not filecmp.cmp(src, RES / p / f"{p}.csv", shallow=False):
                shutil.copy(src, RES / p / f"{p}.csv")
                (RES / p / f"{p}_report.txt").unlink(missing_ok=True)
    score(RES)


def combined():
    same = 0
    for p in base():
        a, b = TWO / p / f"{p}.csv", RES / p / f"{p}.csv"
        if a.exists() and b.exists() and filecmp.cmp(a, b, shallow=False) and (RES / p / f"{p}_report.txt").exists():
            shutil.copy(RES / p / f"{p}_report.txt", TWO / p / f"{p}_report.txt")
            same += 1
    print(f"{same} papers take the tables' report", flush=True)
    score(TWO)


def read(root):
    out = {}
    for p in base():
        rep = root / p / f"{p}_report.txt"
        t = rep.read_text(encoding="utf-8", errors="ignore") if rep.exists() else ""
        g = lambda lab: int((re.search(lab + r"\s*:\s*(\d+)", t) or [0, 0])[1])
        m = ev._metrics_from_report(rep) if rep.exists() else None
        out[p] = {"f1": float(m[2]) if m else 0.0, "tp": g(r"matched \(TP\)"), "fn": g(r"missed \(FN\)"), "fp": g(r"spurious, in scope"), "ok": bool(m)}
    return out


def line(tag, ps, d):
    if not ps:
        return ""
    tp, fp, fn = (sum(d[p][k] for p in ps) for k in ("tp", "fp", "fn"))
    f = [d[p]["f1"] for p in ps]
    micro = 2 * tp / max(1, 2 * tp + fp + fn)
    return (f"  {tag:18s} {len(ps):3d} papers  mean F1 {sum(f) / len(ps):.3f}  micro F1 {micro:.3f}  R {tp / max(1, tp + fn):.3f}  P {tp / max(1, tp + fp):.3f}  "
            f"zero {sum(x == 0 for x in f)}, under .5 {sum(0 < x < .5 for x in f)}, .5-.9 {sum(.5 <= x < .9 for x in f)}, .9+ {sum(x >= .9 for x in f)}")


def results():
    b = base()
    groups = collections.defaultdict(list)
    for p in b:
        groups[ASSIGN.get(p, "grit-only")].append(p)
    print(f"old baseline, summary.csv: mean F1 {sum(float(r['f1'] or 0) for r in b.values()) / max(1, len(b)):.3f}, {len(b)} papers")
    for label, root in (("tables only (v18 rows, current scorer and GT)", RES), ("tables + prose (two_step)", TWO)):
        d = read(root)
        print(label + f"; reports {sum(x['ok'] for x in d.values())} of {len(d)}")
        print(line("all", list(b), d))
        for g in ("dev", "held_a", "held_b", "grit-only"):
            if groups[g]:
                print(line(g, groups[g], d))
        olds = {p: float(b[p]["f1"] or 0) for p in b}
        print(f"  against the old baseline: up {sum(d[p]['f1'] > olds[p] + .005 for p in b)}, down {sum(d[p]['f1'] < olds[p] - .005 for p in b)}")
        moved = sorted((p for p in b if ASSIGN.get(p) in ("dev", "held_a")), key=lambda p: abs(d[p]["f1"] - olds[p]), reverse=True)
        print("  tuning papers moved most: " + ", ".join(f"{p} {olds[p]:.3f}->{d[p]['f1']:.3f}" for p in moved[:10] if abs(d[p]["f1"] - olds[p]) > .005))
    st = TWO / "status.json"
    if st.exists():
        s = json.loads(st.read_text(encoding="utf-8"))
        ps = [v for k, v in s.items() if k in b]
        print(f"routing: {len(ps)} papers, sent to prose {sum(v['route'] == 'prose' for v in ps)}, prose done {sum(v.get('prose') == 'done' for v in ps)}, "
              f"failed {sum(str(v.get('prose', '')).startswith('failed') for v in ps)}, prose rows {sum(v.get('prose_rows', 0) for v in ps)}")


if __name__ == "__main__":
    {"tables": tables, "combined": combined, "results": results}[sys.argv[1]]()
