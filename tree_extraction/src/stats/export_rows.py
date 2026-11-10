"""stats.json (collect.py) as row tables for the stats page: one JSON object, one list of rows per section, each row
with an `id` that names it. Per-paper rows are tuning papers only (dev, held_a), as in stats.json.

    python export_rows.py   -> tree_extraction/output/eval_split/stats/stats_rows.json
"""
import json
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "output" / "eval_split" / "stats"
S = json.loads((D / "stats.json").read_text(encoding="utf-8"))["sets"]
RUN = {"tables": "v18 rescored (tables)", "combined": "v18 + prose"}
out = {k: [] for k in ("scores", "versions", "tests", "hist", "causes", "fields", "decisions", "confidence", "head",
                       "data", "mix", "corr", "papers")}
for s, r in S.items():
    for run, groups in r["current"].items():
        for g, c in groups.items():
            out["scores"].append({"id": f"{s}|{run}|{g}", "set": s, "run": RUN[run], "group": g, "papers": c["n"],
                                  "mean_f1": c["mean_f1"], "mean_f1_lo": (c["mean_f1_ci"] or [None, None])[0],
                                  "mean_f1_hi": (c["mean_f1_ci"] or [None, None])[1], "micro_f1": c["micro_f1"],
                                  "micro_f1_lo": (c["micro_f1_ci"] or [None, None])[0], "micro_f1_hi": (c["micro_f1_ci"] or [None, None])[1],
                                  "mean_precision": c["mean_p"], "mean_recall": c["mean_r"], "mean_strict_f1": c["mean_strict_f1"],
                                  "tp": c["tp"], "fn": c["fn"], "fp_in_scope": c["fp"], "out_of_scope": c["oos"],
                                  "zero_papers": c["zeros"], "zero_gt_rows": c["zero_gt_rows"], "zero_share_of_loss": c["zero_share_of_loss"],
                                  "papers_at_least_0_9": c["at_least_0.9"]})
            for i, n in enumerate(c["hist"]):
                out["hist"].append({"id": f"{s}|{run}|{g}|{i}", "set": s, "run": RUN[run], "group": g,
                                    "bin": f"{i / 10:.1f}–{(i + 1) / 10:.1f}", "bin_lo": i / 10, "papers": n})
            if run == "combined":
                for cause, n in c["causes"].items():
                    out["causes"].append({"id": f"{s}|{g}|{cause}", "set": s, "group": g, "cause": cause, "rows": n})
                for f, (a, t) in c["fields"].items():
                    out["fields"].append({"id": f"{s}|{g}|{f}", "set": s, "group": g, "field": f, "agree": a, "matched_rows": t,
                                          "agreement": round(a / t, 4) if t else None})
    for i, v in enumerate(r["versions"]):
        for g, m in v["mean"].items():
            out["versions"].append({"id": f"{s}|{v['version']}|{g}", "set": s, "version": v["version"], "order": i,
                                    "group": g, "mean_f1": m, "papers": v["n"][g]})
    for t in r["tests"]:
        for g, x in t["groups"].items():
            out["tests"].append({"id": f"{s}|{t['a']}>{t['b']}|{g}", "set": s, "from": t["a"], "to": t["b"], "group": g,
                                 "papers": x["n"], "mean_from": x["mean_a"], "mean_to": x["mean_b"], "diff": x["diff"],
                                 "diff_lo": (x["ci"] or [None, None])[0], "diff_hi": (x["ci"] or [None, None])[1],
                                 "improved": x["improved"], "regressed": x["regressed"], "changed": x["wilcoxon"]["n"],
                                 "wilcoxon_z": x["wilcoxon"]["z"], "wilcoxon_p": x["wilcoxon"]["p"], "sign_p": x["sign"]["p"]})
    for g in r["groups"]:
        for q, counts in (("route", r["routes"].get(g, {})), ("Q-KIND answer", r["kind"].get(g, {}).get("choice", {})),
                          ("Q-KIND action", r["kind"].get(g, {}).get("action", {})), ("structure", r["structure"].get(g, {}))):
            for a, n in counts.items():
                out["decisions"].append({"id": f"{s}|{g}|{q}|{a}", "set": s, "group": g, "question": q, "answer": str(a), "count": n})
        k = r["kind"].get(g, {})
        out["decisions"].append({"id": f"{s}|{g}|yes/no|asked", "set": s, "group": g, "question": "yes / no columns",
                                 "answer": "asked", "count": r["yes_no"][g]["asked"]})
        out["decisions"].append({"id": f"{s}|{g}|yes/no|written", "set": s, "group": g, "question": "yes / no columns",
                                 "answer": "written Yes / No", "count": r["yes_no"][g]["yes_no"]})
        out["decisions"].append({"id": f"{s}|{g}|Q-KIND|unsure", "set": s, "group": g, "question": "Q-KIND confidence",
                                 "answer": "below 0.8", "count": k.get("unsure", 0)})
        out["decisions"].append({"id": f"{s}|{g}|Q-KIND|tables", "set": s, "group": g, "question": "Q-KIND confidence",
                                 "answer": "tables asked", "count": k.get("tables", 0)})
        out["decisions"].append({"id": f"{s}|{g}|prose rows", "set": s, "group": g, "question": "prose rows", "answer": "rows",
                                 "count": r["prose_rows"][g]})
        for rt, f1 in r["route_f1"].get(g, {}).items():
            out["decisions"].append({"id": f"{s}|{g}|route F1|{rt}", "set": s, "group": g, "question": "mean F1 by route",
                                     "answer": rt, "count": f1})
        for i, n in enumerate(k.get("conf_hist", [])):
            out["confidence"].append({"id": f"{s}|{g}|{i}", "set": s, "group": g, "bin": f"{i / 10:.1f}–{(i + 1) / 10:.1f}",
                                      "bin_lo": i / 10, "tables": n})
        h = r["head_reader"].get(g)
        if h:
            out["head"].append({"id": f"{s}|{g}", "set": s, "group": g, "tables": h["tables"], "minutes": h["secs_total_min"],
                                "seconds_median": h["secs_median"], "seconds_p90": h["secs_p90"], "calls_median": h["calls_median"],
                                "calls_p90": h["calls_p90"], "calls": h["calls_total"]})
        d = r["data"].get(g)
        if d:
            out["data"].append({"id": f"{s}|{g}", "set": s, "group": g, "papers": d["papers"], "gt_rows": d["gt_rows"],
                                "gt_rows_q1": d["gt_rows_q"][0], "gt_rows_median": d["gt_rows_q"][1], "gt_rows_q3": d["gt_rows_q"][2],
                                "traits_median": d["gt_traits_median"], "tables_q1": d["tables_q"][0], "tables_median": d["tables_q"][1],
                                "tables_q3": d["tables_q"][2], "no_tables": d["no_tables"], "with_supplements": d["with_supplements"]})
            for f, lab in (("stat", "measurementStatistic"), ("sex", "sex"), ("life", "lifeStage")):
                for v, n in d[f].items():
                    out["mix"].append({"id": f"{s}|{g}|{lab}|{v}", "set": s, "group": g, "field": lab, "value": v, "rows": n})
    for g, fs in r["correlations"].items():
        for f, c in fs.items():
            if c:
                out["corr"].append({"id": f"{s}|{g}|{f}", "set": s, "group": g, "feature": f, "rho": c["rho"], "p": c["p"], "papers": c["n"]})
    for p in r["papers"]:
        out["papers"].append({"id": f"{s}|{p['paper']}", "set": s, **p})
(D / "stats_rows.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
print({k: len(v) for k, v in out.items()}, (D / "stats_rows.json").stat().st_size, "bytes")
