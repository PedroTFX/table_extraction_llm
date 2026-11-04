"""
prose_test.py — the prose reader's test on a group of papers, reported as TOTALS ONLY (2026-11-04).
No paper name, row, quote or per-paper number is printed: held_b is the test set and is never looked
at paper by paper (output/eval_split/split_v15.json rule; DESIGN_prose.md).

  production   the production scorer on each paper (output kept quiet), summed: mean F1 and micro P / R / F1
  judged       the judging used on the dev papers, run automatically: same species (genus initial +
               epithet), value equal once format is set aside (dashes, units, a leading 'is / are',
               trailing punctuation, 1.00 = 1), trait names that share their words (one name's words
               inside the other's, 'morphology', 'of', 'the', 'male / female genitalia' aside). On dev
               the name pairs were read by hand; here no pair can be read, so a pair whose names share
               no word never counts: stricter than on dev. Near values (a GT typo in a number, one
               value inside the other) as on dev; precision counts only extra rows whose trait the GT has.
  sanity       summed counts: passages, captions, lists, list items, accounts opened, facts kept, place
               joins, rows; papers with no rows or no account (as a count)

    python prose_test.py held_b|dev
"""
import collections
import contextlib
import csv
import difflib
import io
import json
import re
import sys

import _paths
import prose_reader as pr

UNIT = r"(?:mm|cm|µm|μm|m|°c|%)"
STOP = {"morphology", "of", "the", "male", "female", "genitalia", "a", "and"}


def key(name):
    w = re.findall(r"[A-Za-z]+", str(name or ""))
    return f"{w[0][0].lower()}. {w[1].lower()}" if len(w) >= 2 and w[1][0].islower() else " ".join(w[:2]).lower()


def nv(v):
    s = str(v or "").lower().replace("–", "-").replace("—", "-").replace("−", "-").replace("×", "x")
    s = re.sub(r"\s*-\s*", "-", s)
    s = re.sub(r"^(there (is|are)|is|are|it is|they are)\s+", "", s.strip())
    s = re.sub(rf"(?<=\d)\s*{UNIT}\b", "", s)
    s = re.sub(r"\b(\d+)\.0+\b", r"\1", s)
    s = re.sub(r"(\d\.\d*?)0+\b", r"\1", s)
    s = re.sub(r"[\s.;:,]+$", "", s)
    return " ".join(s.split())


toks = lambda s: set(re.findall(r"[a-z0-9]+", str(s).lower())) - STOP
num = lambda s: bool(re.fullmatch(r"[\d.,\s\-–~<>]+", nv(s))) and any(c.isdigit() for c in s)


def same_trait(a, b):
    ta, tb = toks(a), toks(b)
    return bool(ta and tb) and (ta <= tb or tb <= ta)


def gt_rows(p):
    import openpyxl
    ws = openpyxl.load_workbook(_paths.PAPERS / p / f"{p}.xlsx", read_only=True, data_only=True).worksheets[0]
    it = ws.iter_rows(values_only=True)
    h = [str(x or "").strip() for x in next(it)]
    g = lambda r, k: ("" if k not in h or h.index(k) >= len(r) or r[h.index(k)] is None else str(r[h.index(k)]).strip())
    return [{"sp": g(r, "verbatimIdentification"), "t": g(r, "measurementType"), "v": g(r, "measurementValue")}
            for r in it if g(r, "verbatimIdentification") or g(r, "measurementValue")]


def judged(p):
    gt = gt_rows(p)
    f = pr.OUT / "prose" / p / f"{p}.csv"
    us = [{"sp": r["verbatimIdentification"], "t": r["measurementType"], "v": r["measurementValue"]}
          for r in csv.DictReader(open(f, encoding="utf-8"))] if f.exists() else []
    pool = collections.defaultdict(list)
    for i, r in enumerate(us):
        pool[key(r["sp"])].append(i)
    used, c = set(), collections.Counter()
    left = []
    for g in gt:                                     # equal value, names sharing their words
        j = next((i for i in pool[key(g["sp"])] if i not in used and nv(us[i]["v"]) == nv(g["v"])
                  and (not g["t"] or same_trait(g["t"], us[i]["t"]))), None)
        if j is None:
            left.append(g)
        else:
            used.add(j)
            c["equal"] += 1
    for g in left:                                   # near values for the same trait
        best, bj = 0, None
        for i in pool[key(g["sp"])]:
            if i in used or not same_trait(g["t"], us[i]["t"]):
                continue
            a, b = nv(g["v"]), nv(us[i]["v"])
            r = 1.0 if (a and b and (a in b or b in a)) else difflib.SequenceMatcher(None, a, b).ratio()
            if r > best:
                best, bj = r, i
        if bj is None or best < 0.75:
            c["missed"] += 1
            continue
        a, b = nv(g["v"]), nv(us[bj]["v"])
        ratio = difflib.SequenceMatcher(None, a, b).ratio()
        if num(g["v"]) and num(us[bj]["v"]):
            if ratio < 0.85:
                c["missed"] += 1
                continue
            c["typo"] += 1
        elif a == b or ratio >= 0.9:
            c["typo"] += 1
        else:
            c["part"] += 1
        used.add(bj)
    gt_types = {g["t"] for g in gt if g["t"]}
    c["extra_in_scope"] = sum(1 for i, u in enumerate(us) if i not in used and any(same_trait(t, u["t"]) for t in gt_types))
    c["gt"], c["ours"] = len(gt), len(us)
    return c


def production(p):
    import evaluate as ev
    from mineru_extract import classify_folder
    ev.ASSESS_MISS_SEVERITY = False
    f = pr.OUT / "prose" / p / f"{p}.csv"
    if not f.exists():
        return None
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        _, gt, _ = classify_folder(_paths.PAPERS / p)
        ev.evaluate(str(f), str(gt), ev.DEFAULT_KEY, False, semantic=True, use_llm=True)
    t = buf.getvalue()
    g = lambda lab: int((re.search(lab + r"\s*:\s*(\d+)", t) or [0, 0])[1])
    return {"tp": g(r"matched \(TP\)"), "fn": g(r"missed \(FN\)"), "fp": g(r"spurious, in scope")}


def sanity(p):
    c = collections.Counter()
    load = lambda d: json.loads((pr.OUT / d / f"{p}.json").read_text(encoding="utf-8")) if (pr.OUT / d / f"{p}.json").exists() else {}
    sh = load("shape").get("shape", {})
    c.update({"passages": len(sh), "captions": sum(v == "caption" for v in sh.values()),
              "lists": sum(v == "list" for v in sh.values())})
    rd = load("read2")
    c["list items"] = sum(x.get("items", 0) for x in rd.get("log", {}).values() if "items" in x)
    w = load("walk")
    c["accounts opened"] = sum(1 for x in w.get("log", []) if x["after"] and x["after"] != x["before"])
    fx = load("facts")
    c["facts kept"] = sum(1 for x in fx.get("facts", []) if x["owner"] and not x["why"])
    c["place joins"] = sum(1 for x in fx.get("joins", []) if x["join"])
    f = pr.OUT / "prose" / p / f"{p}.csv"
    c["rows"] = sum(1 for _ in csv.DictReader(open(f, encoding="utf-8"))) if f.exists() else 0
    c["papers with no rows"] = int(not c["rows"])
    c["papers with no account"] = int(not c["accounts opened"])
    return c


def prf(tp, fp, fn):
    P = tp / (tp + fp) if tp + fp else 0
    R = tp / (tp + fn) if tp + fn else 0
    return R, P, (2 * P * R / (P + R) if P + R else 0)


if __name__ == "__main__":
    group = sys.argv[1]
    papers = pr.papers_of([group])
    S, J, prod, f1s, jf1s = collections.Counter(), collections.Counter(), collections.Counter(), [], []
    for p in papers:
        S.update(sanity(p))
        j = judged(p)
        J.update(j)
        jf1s.append(prf(j["equal"] + j["typo"], j["extra_in_scope"] + j["part"], j["missed"] + j["part"])[2])
        d = production(p)
        if d:
            prod.update(d)
            f1s.append(prf(d["tp"], d["fp"], d["fn"])[2])
    n = len(papers)
    print(f"prose reader ({pr.OUT.name}) on {group}: {n} papers, totals only")
    print("  sanity: " + ", ".join(f"{k} {v}" for k, v in S.items()))
    R, P, F = prf(prod["tp"], prod["fp"], prod["fn"])
    print(f"  production scorer: mean F1 {sum(f1s) / max(1, n):.3f}; micro R {R:.3f} P {P:.3f} F1 {F:.3f} "
          f"(TP {prod['tp']}, FP {prod['fp']}, FN {prod['fn']})")
    tp = J["equal"] + J["typo"]
    R, P, F = prf(tp, J["extra_in_scope"] + J["part"], J["gt"] - tp)
    R2, P2, F2 = prf(tp + J["part"], J["extra_in_scope"], J["gt"] - tp - J["part"])
    print(f"  judged (automatic, stricter than by hand): mean F1 {sum(jf1s) / max(1, n):.3f}; micro R {R:.3f} "
          f"P {P:.3f} F1 {F:.3f}; lenient R {R2:.3f} P {P2:.3f} F1 {F2:.3f}")
    print(f"    GT rows {J['gt']}, ours {J['ours']}: equal {J['equal']}, typo / format {J['typo']}, part {J['part']}, "
          f"GT unmatched {J['missed']}, our extra rows in GT traits {J['extra_in_scope']}")
