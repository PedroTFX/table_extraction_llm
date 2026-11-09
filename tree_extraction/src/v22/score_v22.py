"""v22 against v18 on one paper set (TREE_PAPERS / TREE_OUTPUT): the papers whose table rows changed are scored with
the production scorer into <root>/rescore_v22; every other paper keeps its rescore_v18 report (v18's rows, the same
scorer). Totals by group (split_v15.json): dev and held_a papers named, held_b and grit-only papers as totals only.
-> <root>/V22_TOTALS.txt (the scorer's own output names papers: send it to a log, read only this file)

    python score_v22.py
"""
import collections
import filecmp
import json
import re
import shutil

import _paths
import evaluate as ev

ev.ASSESS_MISS_SEVERITY = False
O = _paths.OUTPUT
V18, V22, RES18, RES22 = O / "full_run_v18", O / "full_run_v22", O / "rescore_v18", O / "rescore_v22"
ASSIGN = json.loads((_paths.SUB / "output/eval_split/split_v15.json").read_text(encoding="utf-8"))["assign"]
NAMED = ("dev", "held_a")


def rep(root, p):
    f = root / p / f"{p}_report.txt"
    t = f.read_text(encoding="utf-8", errors="ignore") if f.exists() else ""
    g = lambda lab: int((re.search(lab + r"\s*:\s*(\d+)", t) or [0, 0])[1])
    m = re.search(r"SCOPED\s+P/R/F1\s*:\s*([\d.]+) / ([\d.]+) / ([\d.]+)", t)
    return {"tp": g(r"matched \(TP\)"), "fn": g(r"missed \(FN\)"), "fp": g(r"spurious, in scope"),
            "f1": float(m[3]) if m else 0.0, "ok": bool(t)}


def main():
    papers = sorted(d.name for d in RES18.iterdir() if (d / f"{d.name}_report.txt").exists())
    changed = []
    for p in papers:
        a, b = V18 / p / f"{p}.csv", V22 / p / f"{p}.csv"
        if b.exists() and not (a.exists() and filecmp.cmp(a, b, shallow=False)):
            changed.append(p)
            (RES22 / p).mkdir(parents=True, exist_ok=True)
            if not (RES22 / p / f"{p}.csv").exists() or not filecmp.cmp(b, RES22 / p / f"{p}.csv", shallow=False):
                shutil.copy(b, RES22 / p / f"{p}.csv")
                (RES22 / p / f"{p}_report.txt").unlink(missing_ok=True)
    if changed:
        ev.evaluate_all(_paths.PAPERS, RES22, ev.DEFAULT_KEY, False, semantic=True, use_llm=True, skip_existing=True)
    acc = collections.Counter()
    for f in (V22 / "account").glob("*.json"):
        g = ASSIGN.get(f.stem, "grit-only")
        for r in json.loads(f.read_text(encoding="utf-8")).values():
            acc[(g, "asked")] += 1
            acc[(g, "given a species")] += bool(r.get("species"))
    groups = collections.defaultdict(list)
    for p in papers:
        old = rep(RES18, p)
        new = rep(RES22, p) if p in changed else old
        groups[ASSIGN.get(p, "grit-only")].append((p, old, new, p in changed))
    L = [f"{O.name}: {len(papers)} papers, {len(changed)} with changed table rows (v22 vs v18; production scorer)"]
    for g in ("dev", "held_a", "held_b", "grit-only"):
        xs = groups.get(g)
        if not xs:
            continue
        n = len(xs)
        mo, mn = sum(x[1]["f1"] for x in xs) / n, sum(x[2]["f1"] for x in xs) / n
        T = lambda i, k: sum(x[i][k] for x in xs)
        mic = lambda i: 2 * T(i, "tp") / max(1, 2 * T(i, "tp") + T(i, "fp") + T(i, "fn"))
        ch = [x for x in xs if x[3]]
        up = sum(x[2]["f1"] > x[1]["f1"] + 0.005 for x in ch)
        down = sum(x[2]["f1"] < x[1]["f1"] - 0.005 for x in ch)
        L.append(f"\n{g}: {n} papers; rows changed in {len(ch)}; F1 up {up}, down {down}; tables asked Q-ACCOUNT "
                 f"{acc[(g, 'asked')]}, given a species {acc[(g, 'given a species')]}")
        L.append(f"  mean F1 {mo:.3f} -> {mn:.3f}; micro F1 {mic(1):.3f} -> {mic(2):.3f} "
                 f"(TP {T(1, 'tp')} -> {T(2, 'tp')}, FP {T(1, 'fp')} -> {T(2, 'fp')}, FN {T(1, 'fn')} -> {T(2, 'fn')})")
        if g in NAMED:
            for p, a, b, c in sorted(ch, key=lambda x: x[2]["f1"] - x[1]["f1"]):
                L.append(f"    {p:24s} {a['f1']:.3f} -> {b['f1']:.3f}  TP {a['tp']} -> {b['tp']}  FP {a['fp']} -> {b['fp']}")
    (O / "V22_TOTALS.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
