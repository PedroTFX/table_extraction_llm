"""8A: rescore the papers whose trait-name pairs the 2026-11-10 normaliser changes (norm_compare.json), with the full
scorer (gemma judge as before), into output/rescore_8a and output_grit/rescore_8a. The two_step reports stay the
baseline. Tuning papers are named; held_b and grit as totals only.

    python score_8a.py      -> prints the comparison, writes tree_extraction/output/eval_split/stats/score_8a.json
"""
import json
import shutil

import beyond_gt as bg
import norm_compare as nc

ev = bg.ev
ev.ASSESS_MISS_SEVERITY = False


def f1(report):
    m = ev._metrics_from_report(report) if report.exists() else None
    return float(m[2]) if m else 0.0


def main():
    todo = json.loads((bg.OUT / "eval_split/stats/norm_compare.json").read_text(encoding="utf-8"))
    res = {}
    for name, papers_dir, out, plist in (("109", bg.PAPERS, bg.OUT, todo["109"].get("list", [])),
                                         ("grit", nc.GRIT_PAPERS, nc.GRIT_OUT, todo["grit"].get("list", []))):
        root = out / "rescore_8a"
        for p in plist:
            (root / p).mkdir(parents=True, exist_ok=True)
            shutil.copy(out / "two_step" / p / f"{p}.csv", root / p / f"{p}.csv")
        if plist:
            ev.evaluate_all(papers_dir, root, ev.DEFAULT_KEY, False, semantic=True, use_llm=True, skip_existing=True)
        rows = []
        for p in plist:
            old, new = f1(out / "two_step" / p / f"{p}_report.txt"), f1(root / p / f"{p}_report.txt")
            g = bg.SPLIT.get(p, "grit") if name == "109" else "grit"
            rows.append({"paper": p, "group": g, "old": old, "new": new})
        res[name] = rows
    (bg.OUT / "eval_split/stats/score_8a.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    for name, rows in res.items():
        for g in sorted({r["group"] for r in rows}):
            rs = [r for r in rows if r["group"] == g]
            print(f"{name} {g}: {len(rs)} papers, F1 sum {sum(r['old'] for r in rs):.3f} -> {sum(r['new'] for r in rs):.3f}")
            if g in ("dev", "held_a"):
                for r in rs:
                    print(f"   {r['paper']:22s} {r['old']:.3f} -> {r['new']:.3f}")


if __name__ == "__main__":
    main()
