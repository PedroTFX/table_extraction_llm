"""Two table runs of the same papers, read paper by paper from their scored reports (tables only): a new root against an
earlier one, so a change shows apart from the baseline in summary.csv. Only the papers SCORE_BASELINE lists are read;
tuning papers (dev + held_a) are named, any other paper only counted.

    python compare_roots.py <new root> <old root> [tables]      (tables: v24 by default, the rescore_<tables> folder)
TREE_PAPERS picks the paper set, SCORE_BASELINE the summary.csv listing the papers (as for score_two_step.py).
2026-11-21: the frozen column tree (8007174e) against all.2 (output_fresh_109, 2026-11-19) on the tuning papers.
"""
import sys
from pathlib import Path

import score_two_step as sts

TUNING = ("dev", "held_a")


def main(new, old, tables="v24"):
    a = sts.read(Path(new) / f"rescore_{tables}")
    b = sts.read(Path(old) / f"rescore_{tables}")
    papers = list(sts.base())
    group = {p: sts.ASSIGN.get(p, "grit-only") for p in papers}
    print(f"reports: new {sum(x['ok'] for x in a.values())} of {len(a)}, old {sum(x['ok'] for x in b.values())} of {len(b)}")
    for g in ("dev", "held_a", "tuning", "held_b", "grit-only"):
        ps = [p for p in papers if (group[p] in TUNING if g == "tuning" else group[p] == g)]
        if ps:
            print(f"{g}:")
            print("  new " + sts.line("", ps, a).strip())
            print("  old " + sts.line("", ps, b).strip())
    up = [p for p in papers if a[p]["f1"] > b[p]["f1"] + .005]
    down = [p for p in papers if a[p]["f1"] < b[p]["f1"] - .005]
    print(f"papers up {len(up)}, down {len(down)}, the same {len(papers) - len(up) - len(down)}")
    for k in ("tp", "fp", "fn"):
        print(f"  {k.upper()} {sum(b[p][k] for p in papers)} -> {sum(a[p][k] for p in papers)}")
    print("tuning papers that moved (F1 old -> new; TP, FP, FN change):")
    moved = sorted((p for p in up + down if group[p] in TUNING), key=lambda p: a[p]["f1"] - b[p]["f1"])
    for p in moved:
        d = {k: a[p][k] - b[p][k] for k in ("tp", "fp", "fn")}
        print(f"  {p:26s} {group[p]:7s} {b[p]['f1']:.3f} -> {a[p]['f1']:.3f}   TP {d['tp']:+d}  FP {d['fp']:+d}  FN {d['fn']:+d}")
    other = [p for p in up + down if group[p] not in TUNING]
    if other:
        print(f"other papers that moved: {len(other)} (not named)")


if __name__ == "__main__":
    main(*sys.argv[1:4])
