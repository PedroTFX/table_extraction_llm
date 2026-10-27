"""Side-by-side of the full run and production, both scored by evaluate.evaluate_all.

Reads output/full_run/summary.csv and output/full_run_production/summary.csv plus each
paper's _report.txt (TP / FN / spurious counts for micro scores). Writes
output/full_run/COMPARE.txt and COMPARE.csv. Reads saved files only, no model.
"""
import csv
import re
import sys

import _paths

OUT = _paths.OUTPUT / "full_run"
OUT_PROD = _paths.OUTPUT / "full_run_production"


def summary(root):
    with open(root / "summary.csv", encoding="utf-8") as fh:
        return {r["paper"]: r for r in csv.DictReader(fh)}


def counts(root, paper):
    f = root / paper / f"{paper}_report.txt"
    if not f.exists():
        return None
    t = f.read_text(encoding="utf-8", errors="replace")
    def grab(label):
        m = re.search(label + r"\s*:\s*(\d+)", t)
        return int(m.group(1)) if m else 0
    return {"tp": grab(r"matched \(TP\)"), "fn": grab(r"missed \(FN\)"),
            "fp_in": grab(r"spurious, in scope"), "fp_out": grab(r"spurious, out of scope")}


def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return p, r, (2 * p * r / (p + r) if p + r else 0.0)


def main():
    ours, prod = summary(OUT), summary(OUT_PROD)
    papers = sorted(set(ours) | set(prod))
    rows = []
    for p in papers:
        o, q = ours.get(p), prod.get(p)
        rows.append({"paper": p,
                     "tree_f1": float(o["f1"]) if o and o.get("status") == "ok" else None,
                     "prod_f1": float(q["f1"]) if q and q.get("status") == "ok" else None,
                     "tree_status": o["status"] if o else "no output",
                     "prod_status": q["status"] if q else "no output",
                     "tree": counts(OUT, p), "prod": counts(OUT_PROD, p)})

    L = ["Full run (tree_extraction) vs production — evaluate.evaluate_all,",
         "key = verbatimIdentification + measurementType + measurementValue, semantic types, decode=False",
         "(miss-severity grading off on both sides: score-neutral)", ""]

    both = [r for r in rows if r["tree_f1"] is not None and r["prod_f1"] is not None]
    only_t = [r for r in rows if r["tree_f1"] is not None and r["prod_f1"] is None]
    only_p = [r for r in rows if r["prod_f1"] is not None and r["tree_f1"] is None]
    L.append(f"papers scored: tree {sum(r['tree_f1'] is not None for r in rows)}, "
             f"production {sum(r['prod_f1'] is not None for r in rows)}, both {len(both)}")
    if only_t:
        L.append("  tree only: " + ", ".join(r["paper"] for r in only_t))
    if only_p:
        L.append("  production only: " + ", ".join(r["paper"] for r in only_p))
    L.append("")

    def block(title, sel):
        L.append(title)
        for side in ("tree", "prod"):
            f1s = [r[side + "_f1"] for r in sel]
            tp = sum((r[side] or {}).get("tp", 0) for r in sel)
            fn = sum((r[side] or {}).get("fn", 0) for r in sel)
            fpi = sum((r[side] or {}).get("fp_in", 0) for r in sel)
            fpo = sum((r[side] or {}).get("fp_out", 0) for r in sel)
            sp, sr, sf = prf(tp, fpi + fpo, fn)
            cp, cr, cf = prf(tp, fpi, fn)
            name = "tree      " if side == "tree" else "production"
            L.append(f"  {name}  mean F1 {sum(f1s) / len(f1s):.3f}   micro strict P/R/F1 "
                     f"{sp:.3f}/{sr:.3f}/{sf:.3f}   scoped {cp:.3f}/{cr:.3f}/{cf:.3f}   "
                     f"TP {tp}  FN {fn}  FP in/out {fpi}/{fpo}")
        L.append("")

    block(f"ON THE {len(both)} PAPERS BOTH SIDES SCORED", both)
    # production's saved CSVs (commit b3a829c, 2026-09-23 regeneration) are header-only for
    # some papers that had rows on 2026-09-09; split them out so the comparison is fair.
    def n_rows(root, p):
        f = root / p / f"{p}.csv"
        with open(f, encoding="utf-8", errors="replace") as fh:
            return max(0, sum(1 for _ in fh) - 1)
    empty = [r for r in both if n_rows(OUT_PROD, r["paper"]) == 0]
    has = [r for r in both if r not in empty]
    block(f"ON THE {len(has)} PAPERS WHERE PRODUCTION'S SAVED CSV HAS ROWS", has)
    L.append(f"{len(empty)} papers where production's saved CSV is empty (header only): tree F1 > 0 on "
             f"{sum(r['tree_f1'] > 0 for r in empty)}, mean tree F1 "
             f"{sum(r['tree_f1'] for r in empty) / max(1, len(empty)):.3f}")
    L.append("  " + ", ".join(r["paper"] for r in empty))
    L.append("")
    win = [r for r in both if r["tree_f1"] > r["prod_f1"] + 0.005]
    loss = [r for r in both if r["prod_f1"] > r["tree_f1"] + 0.005]
    L.append(f"per paper: tree better {len(win)}, production better {len(loss)}, "
             f"tie {len(both) - len(win) - len(loss)}")
    zero_t = [r for r in both if r["tree_f1"] == 0]
    zero_p = [r for r in both if r["prod_f1"] == 0]
    L.append(f"F1 = 0: tree {len(zero_t)}, production {len(zero_p)}, both {len(set(r['paper'] for r in zero_t) & set(r['paper'] for r in zero_p))}")
    L.append("")
    L.append(f"{'paper':24s} {'tree':>6s} {'prod':>6s} {'diff':>7s}   tree TP/FN/FPin    prod TP/FN/FPin")
    for r in sorted(both, key=lambda r: r["tree_f1"] - r["prod_f1"], reverse=True):
        t, q = r["tree"] or {}, r["prod"] or {}
        L.append(f"{r['paper']:24s} {r['tree_f1']:6.3f} {r['prod_f1']:6.3f} {r['tree_f1'] - r['prod_f1']:+7.3f}   "
                 f"{t.get('tp', 0):5d}/{t.get('fn', 0):5d}/{t.get('fp_in', 0):5d}   "
                 f"{q.get('tp', 0):5d}/{q.get('fn', 0):5d}/{q.get('fp_in', 0):5d}")
    for r in only_t + only_p:
        L.append(f"{r['paper']:24s} tree {r['tree_status']}  {r['tree_f1']}   production {r['prod_status']}  {r['prod_f1']}")

    (OUT / "COMPARE.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    with open(OUT / "COMPARE.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["paper", "tree_f1", "prod_f1", "tree_tp", "tree_fn", "tree_fp_in", "tree_fp_out",
                    "prod_tp", "prod_fn", "prod_fp_in", "prod_fp_out", "tree_status", "prod_status"])
        for r in rows:
            t, q = r["tree"] or {}, r["prod"] or {}
            w.writerow([r["paper"], r["tree_f1"], r["prod_f1"],
                        t.get("tp"), t.get("fn"), t.get("fp_in"), t.get("fp_out"),
                        q.get("tp"), q.get("fn"), q.get("fp_in"), q.get("fp_out"),
                        r["tree_status"], r["prod_status"]])
    print("\n".join(L[:20]))


if __name__ == "__main__":
    sys.exit(main())
