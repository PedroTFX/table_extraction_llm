"""Statistics of the 109 set and grit for the stats page: files only, no model.

Groups (split_v15.json): dev, held_a (tuning), held_b (test); grit papers outside the 109 are grit-only. Only dev and
held_a papers are named or listed one by one; held_b and grit-only appear as totals, counts and distributions only.

  scores      per paper from the reports: rescore_v18 (tables, current scorer) and two_step (tables + prose, current
              scorer); strict and scoped P/R/F1, TP / FN / FP in scope / out of scope; mean and micro per group with
              bootstrap 95% intervals (2,000 resamples of papers, seed 20261109)
  versions    each adopted version's summary.csv, as scored then (the scorer changed on 2026-11-06: matching at the
              shorter side's precision); mean F1 per group
  tests       paired per paper: Wilcoxon signed-rank (normal approximation with tie correction), exact sign test,
              bootstrap interval of the mean difference; improved / regressed = a change of more than 0.005
  loss        missed rows by cause, F1 histogram, zero papers and their share of the lost F1
  fields      agreement on matched rows per column (sex, lifeStage, statistic, unit ...)
  decisions   routes, Q-KIND choices and confidence, structure and yes / no decisions, head reader cost
  data        GT rows, statistics, sex and life stage mix; tables per paper; Spearman correlations of F1 with features

    python collect.py      -> tree_extraction/output/eval_split/stats/stats.json
"""
import collections
import csv
import json
import math
import random
import re
from pathlib import Path

import openpyxl

REPO = Path(__file__).resolve().parents[3]
TE = REPO / "tree_extraction"
SPLIT = json.loads((TE / "output/eval_split/split_v15.json").read_text(encoding="utf-8"))["assign"]
NAMED = ("dev", "held_a")
SURE = 0.8
RNG = random.Random(20261109)
SETS = {"109": {"out": TE / "output", "papers": REPO / "data" / "un_processed_papers"},
        "grit": {"out": TE / "output_grit", "papers": REPO / "data" / "grit_testing"}}
VERSIONS = {"109": ["full_run", "full_run_v3", "full_run_v4", "full_run_v6", "full_run_v7", "full_run_v8", "full_run_v9",
                    "full_run_v11", "full_run_v12", "full_run_v13", "full_run_v14", "full_run_v16", "full_run_v17",
                    "full_run_v18", "rescore_v18", "two_step"],
            "grit": ["full_run_v7", "full_run_v8", "full_run_v9", "full_run_v11", "full_run_v12", "full_run_v13",
                     "full_run_v18", "rescore_v18", "two_step"]}
LABEL = {"full_run": "base", "rescore_v18": "v18 rescored", "two_step": "v18 + prose"}
FIELDS = ["basisOfRecord", "measurementMethod", "measurementUnit", "measurementStatistic", "measurementRemarks", "sex",
          "lifeStage", "caste", "sampleSizeValue", "verbatimLocality", "verbatimEventDate"]


def group(p, s):
    return SPLIT.get(p, "grit-only" if s == "grit" else "?")


def report(f):
    t = f.read_text(encoding="utf-8", errors="ignore") if f.exists() else ""
    if not t:
        return None
    g = lambda lab: int((re.search(lab + r"\s*:\s*(\d+)", t) or [0, 0])[1])
    def prf(lab):
        m = re.search(lab + r"\s+P/R/F1\s*:\s*([\d.]+) / ([\d.]+) / ([\d.]+)", t)
        return [float(x) for x in m.groups()] if m else [0.0, 0.0, 0.0]
    r = {"tp": g(r"matched \(TP\)"), "fn": g(r"missed \(FN\)"), "fp": g(r"spurious, in scope"),
         "oos": g(r"spurious, out of scope"), "strict": prf("STRICT"), "scoped": prf("SCOPED"), "fields": {}, "causes": {}}
    for m in re.finditer(r"^\s{2}(\w+)\s+(\d+)\s+(\d+)\s+([\d.]+|n/a)", t, re.M):
        if m[1] in FIELDS:
            r["fields"][m[1]] = (int(m[2]), int(m[3]))
    sec = re.search(r"WHY THE \d+ MISSED ROWS MISSED\n(.*?)\n\s*\n", t, re.S)
    if sec:
        for m in re.finditer(r"^\s+(.+?)\s{2,}(\d+)\s*$", sec[1], re.M):
            r["causes"][m[1].strip()] = int(m[2])
    return r


def summary(f):
    if not f.exists():
        return {}
    with open(f, encoding="utf-8") as fh:
        return {r["paper"]: float(r["f1"]) for r in csv.DictReader(fh) if r.get("f1") not in (None, "")}


def mean(x):
    return sum(x) / len(x) if x else None


def micro(rows):
    tp, fp, fn = (sum(r[k] for r in rows) for k in ("tp", "fp", "fn"))
    p, rc = tp / max(1, tp + fp), tp / max(1, tp + fn)
    return 2 * p * rc / (p + rc) if p + rc else 0.0


def boot(rows, stat, n=2000):
    if len(rows) < 2:
        return None
    vals = sorted(stat([rows[RNG.randrange(len(rows))] for _ in rows]) for _ in range(n))
    return [round(vals[int(0.025 * n)], 4), round(vals[int(0.975 * n) - 1], 4)]


def wilcoxon(d):
    d = [x for x in d if abs(x) > 1e-12]
    n = len(d)
    if n == 0:
        return {"n": 0, "z": 0.0, "p": 1.0}
    order = sorted(range(n), key=lambda i: abs(d[i]))
    ranks, i = [0.0] * n, 0
    ties = 0.0
    while i < n:
        j = i
        while j + 1 < n and abs(abs(d[order[j + 1]]) - abs(d[order[i]])) < 1e-12:
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2 + 1
        t = j - i + 1
        ties += t ** 3 - t
        i = j + 1
    w = sum(r for r, x in zip(ranks, d) if x > 0)
    mu, var = n * (n + 1) / 4, n * (n + 1) * (2 * n + 1) / 24 - ties / 48
    z = (w - mu) / math.sqrt(var) if var > 0 else 0.0
    return {"n": n, "z": round(z, 3), "p": round(math.erfc(abs(z) / math.sqrt(2)), 4)}


def sign_test(d):
    up, down = sum(x > 1e-12 for x in d), sum(x < -1e-12 for x in d)
    n, k = up + down, min(up, down)
    p = min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0
    return {"up": up, "down": down, "p": round(p, 4)}


def paired(a, b, papers, grp):
    out = {}
    for g in grp:
        ps = [p for p in papers[g] if p in a and p in b]
        d = [b[p] - a[p] for p in ps]
        if not d:
            continue
        out[g] = {"n": len(d), "mean_a": round(mean([a[p] for p in ps]), 4), "mean_b": round(mean([b[p] for p in ps]), 4),
                  "diff": round(mean(d), 4), "ci": boot(d, mean), "improved": sum(x > 0.005 for x in d),
                  "regressed": sum(x < -0.005 for x in d), "wilcoxon": wilcoxon(d), "sign": sign_test(d)}
    return out


def spearman(x, y):
    def rank(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        r, i = [0.0] * len(v), 0
        while i < len(v):
            j = i
            while j + 1 < len(v) and v[o[j + 1]] == v[o[i]]:
                j += 1
            for k in range(i, j + 1):
                r[o[k]] = (i + j) / 2 + 1
            i = j + 1
        return r
    if len(x) < 3:
        return None
    rx, ry = rank(x), rank(y)
    mx, my = mean(rx), mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    rho = num / den if den else 0.0
    t = rho * math.sqrt((len(x) - 2) / max(1e-12, 1 - rho ** 2))
    p = math.erfc(abs(t) / math.sqrt(2))                       # normal approximation, fine for n >= 20
    return {"rho": round(rho, 3), "p": round(p, 4), "n": len(x)}


def gt_profile(f):
    if not f.exists():
        return None
    rows = list(openpyxl.load_workbook(f, read_only=True).active.iter_rows(values_only=True))
    if not rows:
        return None
    h = [str(x).strip() if x is not None else "" for x in rows[0]]
    col = lambda name: next((i for i, k in enumerate(h) if k == name), None)
    it, ist, isx, ils, ib = (col(k) for k in ("measurementType", "measurementStatistic", "sex", "lifeStage", "basisOfRecord"))
    data = [r for r in rows[1:] if r and any(c not in (None, "") for c in r)]
    get = lambda r, i: str(r[i]).strip() if i is not None and i < len(r) and r[i] not in (None, "") else "(blank)"
    return {"rows": len(data), "traits": len({get(r, it) for r in data}),
            "stat": collections.Counter(get(r, ist) for r in data), "sex": collections.Counter(get(r, isx) for r in data),
            "life": collections.Counter(get(r, ils) for r in data), "basis": collections.Counter(get(r, ib) for r in data)}


def collect(s):
    cfg, out = SETS[s], {}
    root, pdir = cfg["out"], cfg["papers"]
    two = summary(root / "two_step" / "summary.csv")
    papers = sorted(set(two) | ({p for p in SPLIT} if s == "109" else set()))
    grp = collections.defaultdict(list)
    for p in papers:
        grp[group(p, s)].append(p)
    groups = [g for g in ("dev", "held_a", "held_b", "grit-only") if grp.get(g)]
    grp["tuning"] = grp["dev"] + grp["held_a"]
    grp["all"] = list(papers)
    gall = groups + ["tuning", "all"]
    out["groups"] = {g: len(grp[g]) for g in gall}

    # versions, as scored then
    vers = []
    for v in VERSIONS[s]:
        sm = summary(root / v / "summary.csv")
        if v in ("rescore_v18", "two_step"):           # their reports are newer than summary.csv (re-scored papers)
            for p in list(sm):
                r = report(root / v / p / f"{p}_report.txt")
                if r:
                    sm[p] = r["scoped"][2]
        if sm:
            vers.append({"version": LABEL.get(v, v.replace("full_run_", "")),
                         "mean": {g: round(mean([sm[p] for p in grp[g] if p in sm]) or 0, 4) for g in gall},
                         "n": {g: sum(p in sm for p in grp[g]) for g in gall}, "_f1": sm})
    out["versions"] = [{k: v for k, v in x.items() if k != "_f1"} for x in vers]
    tests = []
    for a, b in zip(vers, vers[1:]):
        tests.append({"a": a["version"], "b": b["version"], "groups": paired(a["_f1"], b["_f1"], grp, gall)})
    out["tests"] = tests

    # current reports
    rep = {"tables": {p: report(root / "rescore_v18" / p / f"{p}_report.txt") for p in papers},
           "combined": {p: report(root / "two_step" / p / f"{p}_report.txt") for p in papers}}
    cur = {}
    for k, rr in rep.items():
        cur[k] = {}
        for g in gall:
            rows = [rr[p] for p in grp[g] if rr.get(p)]
            if not rows:
                continue
            f1 = [r["scoped"][2] for r in rows]
            sf1 = [r["strict"][2] for r in rows]
            zeros = [r for r in rows if r["scoped"][2] == 0]
            cur[k][g] = {
                "n": len(rows), "mean_f1": round(mean(f1), 4), "mean_f1_ci": boot(f1, mean),
                "mean_strict_f1": round(mean(sf1), 4), "mean_p": round(mean([r["scoped"][0] for r in rows]), 4),
                "mean_r": round(mean([r["scoped"][1] for r in rows]), 4),
                "micro_f1": round(micro(rows), 4), "micro_f1_ci": boot(rows, micro),
                "tp": sum(r["tp"] for r in rows), "fn": sum(r["fn"] for r in rows), "fp": sum(r["fp"] for r in rows),
                "oos": sum(r["oos"] for r in rows),
                "hist": [sum(1 for x in f1 if (i / 10 <= x < (i + 1) / 10) or (i == 9 and x == 1.0)) for i in range(10)],
                "zeros": len(zeros), "zero_gt_rows": sum(r["tp"] + r["fn"] for r in zeros),
                "zero_share_of_loss": round(len(zeros) / max(1e-9, sum(1 - x for x in f1)), 4),
                "at_least_0.9": sum(x >= 0.9 for x in f1),
                "causes": dict(sum((collections.Counter(r["causes"]) for r in rows), collections.Counter())),
                "fields": {fl: [sum(r["fields"].get(fl, (0, 0))[0] for r in rows), sum(r["fields"].get(fl, (0, 0))[1] for r in rows)]
                           for fl in FIELDS}}
    out["current"] = cur
    f1t = {p: r["scoped"][2] for p, r in rep["tables"].items() if r}
    f1c = {p: r["scoped"][2] for p, r in rep["combined"].items() if r}
    out["prose_test"] = paired(f1t, f1c, grp, gall)

    # routes
    st = json.loads((root / "two_step" / "status.json").read_text(encoding="utf-8")) if (root / "two_step" / "status.json").exists() else {}
    out["routes"] = {g: dict(collections.Counter(f"{st.get(p, {}).get('route', '?')}: {st.get(p, {}).get('why', '?')}" for p in grp[g]))
                     for g in gall}
    out["prose_rows"] = {g: sum(int(st.get(p, {}).get("prose_rows") or 0) for p in grp[g]) for g in gall}
    out["route_f1"] = {g: {rt: round(mean([f1c[p] for p in grp[g] if p in f1c and st.get(p, {}).get("route") == rt]) or 0, 4)
                           for rt in ("tables", "prose")} for g in gall}

    # decisions
    kd = root / "full_run_v18" / "kind"
    kinds = {}
    for g in gall:
        ch, act, conf, n_un = collections.Counter(), collections.Counter(), [], 0
        for p in grp[g]:
            f = kd / f"{p}.json"
            if not f.exists():
                continue
            for t, v in json.loads(f.read_text(encoding="utf-8")).items():
                if not isinstance(v, dict) or not v.get("kind"):
                    continue
                c, pr = v["kind"].get("choice"), v["kind"].get("probs") or {}
                ch[c] += 1
                act[v.get("action")] += 1
                m = max(pr.values()) if pr else 0
                conf.append(m)
                n_un += m < SURE
        kinds[g] = {"choice": dict(ch), "action": dict(act), "tables": len(conf), "unsure": n_un,
                    "conf_hist": [sum(1 for x in conf if i / 10 <= x < (i + 1) / 10 or (i == 9 and x == 1)) for i in range(10)]}
    out["kind"] = kinds
    sd = root / "full_run_v18" / "structure"
    out["structure"] = {g: dict(sum((collections.Counter(v.get("action") for v in json.loads((sd / f"{p}.json").read_text(encoding="utf-8")).values()
                                                          if isinstance(v, dict)) for p in grp[g] if (sd / f"{p}.json").exists()), collections.Counter()))
                        for g in gall}
    yd = root / "full_run_v18" / "yes_no"
    yn = {}
    for g in gall:
        asked = flagged = 0
        for p in grp[g]:
            f = yd / f"{p}.json"
            if f.exists():
                d = json.loads(f.read_text(encoding="utf-8"))
                asked += len(d)
                flagged += sum(1 for v in d.values() if isinstance(v, dict) and v.get("yes"))
        yn[g] = {"asked": asked, "yes_no": flagged}
    out["yes_no"] = yn
    hr = json.loads((root / "header_tree_bench" / "experiments" / "reader2_all.json").read_text(encoding="utf-8")) \
        if (root / "header_tree_bench" / "experiments" / "reader2_all.json").exists() else {}
    head = {}
    for g in gall:
        secs = sorted(float(e.get("secs") or 0) for p in grp[g] for e in hr.get(p, []))
        calls = sorted(int(e.get("calls") or 0) for p in grp[g] for e in hr.get(p, []))
        if secs:
            q = lambda v, x: v[min(len(v) - 1, int(x * len(v)))]
            head[g] = {"tables": len(secs), "secs_total_min": round(sum(secs) / 60, 1), "secs_median": q(secs, 0.5),
                       "secs_p90": q(secs, 0.9), "calls_median": q(calls, 0.5), "calls_p90": q(calls, 0.9), "calls_total": sum(calls)}
    out["head_reader"] = head

    # data and features
    prof, feats = {}, {}
    for p in papers:
        d = pdir / p
        gp = gt_profile(d / f"{p}.xlsx")
        md = d / f"{p}_full.md"
        text = md.read_text(encoding="utf-8", errors="ignore") if md.exists() else ""
        sup = [f for f in d.iterdir() if re.search(r"_S\d+\.", f.name) and not f.name.endswith(".md")] if d.exists() else []
        prof[p] = gp
        feats[p] = {"gt_rows": gp["rows"] if gp else 0, "gt_traits": gp["traits"] if gp else 0, "tables": text.count("<table"),
                    "md_kchars": round(len(text) / 1000), "supplements": len(sup)}
    data = {}
    for g in gall:
        ps = [p for p in grp[g] if prof.get(p)]
        rows = sorted(prof[p]["rows"] for p in ps)
        if not rows:
            continue
        agg = lambda k: dict(sum((prof[p][k] for p in ps), collections.Counter()).most_common(10))
        q = lambda v, x: v[min(len(v) - 1, int(x * len(v)))]
        tb = sorted(feats[p]["tables"] for p in ps)
        data[g] = {"papers": len(ps), "gt_rows": sum(rows), "gt_rows_q": [q(rows, .25), q(rows, .5), q(rows, .75)],
                   "gt_traits_median": q(sorted(prof[p]["traits"] for p in ps), .5), "tables_q": [q(tb, .25), q(tb, .5), q(tb, .75)],
                   "no_tables": sum(1 for p in ps if feats[p]["tables"] == 0), "with_supplements": sum(1 for p in ps if feats[p]["supplements"]),
                   "stat": agg("stat"), "sex": agg("sex"), "life": agg("life"), "basis": agg("basis")}
    out["data"] = data
    corr = {}
    for g in ("tuning", "all") + (("grit-only",) if s == "grit" else ("held_b",)):
        ps = [p for p in grp[g] if p in f1c and feats.get(p)]
        corr[g] = {k: spearman([float(feats[p][k]) for p in ps], [f1c[p] for p in ps])
                   for k in ("gt_rows", "gt_traits", "tables", "md_kchars", "supplements")}
    out["correlations"] = corr

    # per paper: tuning papers only
    out["papers"] = []
    for p in grp["tuning"]:
        a, b = rep["tables"].get(p), rep["combined"].get(p)
        if not b:
            continue
        cause = max(b["causes"].items(), key=lambda x: x[1])[0] if b["causes"] else ""
        out["papers"].append({"paper": p, "group": group(p, s), "gt_rows": b["tp"] + b["fn"], "tables_f1": a["scoped"][2] if a else None,
                              "f1": b["scoped"][2], "p": b["scoped"][0], "r": b["scoped"][1], "tp": b["tp"], "fn": b["fn"],
                              "fp": b["fp"], "oos": b["oos"], "route": st.get(p, {}).get("route", ""), "main_miss": cause,
                              **{k: feats[p][k] for k in ("tables", "supplements")}})
    return out


if __name__ == "__main__":
    res = {"made": "2026-11-09", "named_groups": list(NAMED), "sure": SURE, "sets": {s: collect(s) for s in SETS}}
    d = TE / "output" / "eval_split" / "stats"
    d.mkdir(parents=True, exist_ok=True)
    (d / "stats.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    for s, r in res["sets"].items():
        c = r["current"]["combined"].get("all", {})
        print(f"{s}: groups {r['groups']}; v18 + prose mean F1 {c.get('mean_f1')} {c.get('mean_f1_ci')}, micro {c.get('micro_f1')}")
