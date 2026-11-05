"""Read-only: where each GT row of the dev papers is lost in a tree run. No pipeline code, no model.
python trace_losses.py <repo> <variant> <out.json>"""
import collections, csv, difflib, json, re, sys
from pathlib import Path
import openpyxl

repo, variant, out = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
O = repo / "tree_extraction" / "output"
PAPERS = ["Xia2022", "Xu2024", "Ustjuzhanin2024"]
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
norm = lambda s: " " + " ".join(re.findall(r"[a-z0-9]+(?:[.,][0-9]+)?", str(s or "").lower())) + " "


def same_trait(a, b):
    ta, tb = toks(a), toks(b)
    return bool(ta and tb) and (ta <= tb or tb <= ta)


def gt_rows(p):
    ws = openpyxl.load_workbook(repo / "data" / "un_processed_papers" / p / f"{p}.xlsx", read_only=True, data_only=True).worksheets[0]
    it = ws.iter_rows(values_only=True)
    h = [str(x or "").strip() for x in next(it)]
    g = lambda r, k: "" if k not in h or h.index(k) >= len(r) or r[h.index(k)] is None else str(r[h.index(k)]).strip()
    return [{"sp": g(r, "verbatimIdentification"), "t": g(r, "measurementType"), "v": g(r, "measurementValue"),
             "u": g(r, "measurementUnit"), "sex": g(r, "sex"), "m": g(r, "measurementMethod")}
            for r in it if g(r, "verbatimIdentification") or g(r, "measurementValue")]


def ours(v, p):
    return [{"sp": r["verbatimIdentification"], "t": r["measurementType"], "v": r["measurementValue"], "u": r["measurementUnit"],
             "sex": r["sex"], "m": r["measurementMethod"], "loc": r.get("verbatimLocality", "")}
            for r in csv.DictReader(open(O / v / "prose" / p / f"{p}.csv", encoding="utf-8"))]


def has(f, t):
    return f.strip() != "" and f in t


res = []
for p in PAPERS:
    load = lambda d: json.loads((O / variant / d / f"{p}.json").read_text(encoding="utf-8"))
    tree, fx, rd, span, shape = load("tree"), load("facts"), load("read2"), load("walk")["span"], load("shape")["shape"]
    sent = json.loads((O / "prose_sent" / f"{p}.json").read_text(encoding="utf-8"))["units"]
    raw = norm((repo / "data" / "un_processed_papers" / p / f"{p}_full.md").read_text(encoding="utf-8", errors="ignore"))
    gt, us = gt_rows(p), ours(variant, p)
    v8d = collections.Counter((key(r["sp"]), nv(r["v"])) for r in ours("prose_v8d", p))
    phr = collections.defaultdict(list)
    for q, ph in tree["phrases"].items():
        for s in ph["species"]:
            phr[key(s)].append((q, ph["text"], norm(ph["text"])))
    reg = set(phr)
    dropped_s, parts = collections.defaultdict(list), collections.defaultdict(list)
    for r in sent:
        if not r["kept"]:
            dropped_s[key(r["account"])].append(r["text"])
    allp = []
    for u in rd["passages"]:
        if u["kind"] == "para":
            s = span.get(u["id"])
            allp.append(u["text"])
            if s:
                parts[key(s)].append((shape.get(u["id"]), u["text"]))
    decisions = collections.defaultdict(list)
    for x in fx["facts"]:
        if x.get("why"):
            decisions[key(x.get("account") or x.get("owner") or "")].append((nv(x["value"]), x["why"], x["what"]))
    check_fail = collections.defaultdict(list)
    for fa in tree["facts"].values():
        if fa.get("check") == "not printed" and "value" in fa["parts"]:
            for s in tree["phrases"][fa["phrase"]]["species"]:
                check_fail[key(s)].append(nv(tree["nodes"][fa["parts"]["value"]]["text"]))
    pool = collections.defaultdict(list)
    for i, r in enumerate(us):
        pool[key(r["sp"])].append(i)
    used = {}
    for j, g in enumerate(gt):
        i = next((i for i in pool[key(g["sp"])] if i not in used and nv(us[i]["v"]) == nv(g["v"]) and (not g["t"] or same_trait(g["t"], us[i]["t"]))), None)
        if i is not None:
            used[i] = j
            g["cause"] = "match"
            g["pair"] = i
    for j, g in enumerate(gt):
        if "cause" in g:
            continue
        k, a, f = key(g["sp"]), nv(g["v"]), norm(g["v"])
        free = [i for i in pool[k] if i not in used]
        i = next((i for i in free if nv(us[i]["v"]) == a), None)
        ev = ""
        if not a:
            c = "gt_empty"
        elif i is not None:
            c, ev = "name", f"we call it: {us[i]['t']}"
        else:
            best = max(((difflib.SequenceMatcher(None, a, nv(us[i]["v"])).ratio() if not (a in nv(us[i]["v"]) or nv(us[i]["v"]) in a) else 1, i)
                        for i in free if same_trait(g["t"], us[i]["t"])), default=(0, None))
            if best[0] >= .75:
                i = best[1]
                c, ev = "part", f"we have: {us[i]['v'][:200]}"
            else:
                i = None
                d = next((x for x in decisions[k] if x[0] == a or (len(a) > 3 and a in x[0])), None)
                if d:
                    c, ev = "decision", f"{d[1]} (fact named '{d[2]}')"
                elif any(x == a or (len(a) > 3 and a in x) for x in check_fail[k]):
                    c = "check"
                else:
                    other = next((r for r in us if key(r["sp"]) != k and nv(r["v"]) == a), None)
                    inside = next((us[i2] for i2 in pool[k] if has(f, norm(us[i2]["v"]))), None)
                    hit = next((x for x in phr[k] if has(f, x[2])), None)
                    if inside:
                        c, ev = "inside", f"{inside['t']}: {inside['v'][:220]}"
                    elif hit:
                        c, ev = "read", f"[{hit[0]}] {hit[1][:320]}"
                    elif any(has(f, norm(t)) for t in dropped_s[k]):
                        c, ev = "sort", next(t for t in dropped_s[k] if has(f, norm(t)))[:320]
                    elif any(has(f, norm(t)) for sh, t in parts[k] if sh == "caption"):
                        c, ev = "caption", next(t for sh, t in parts[k] if sh == "caption" and has(f, norm(t)))[:320]
                    elif any(has(f, norm(t)) for sh, t in parts[k]):
                        c, ev = "leaf", next(t for sh, t in parts[k] if has(f, norm(t)))[:320]
                    elif other:
                        c, ev = "species", f"we gave it to {other['sp']} ({other['t']})"
                    elif any(has(f, norm(t)) for t in allp):
                        hit2 = next(t for t in allp if has(f, norm(t)))
                        c, ev = ("noaccount" if k not in reg else "tracking"), hit2[:320]
                    elif has(f, raw):
                        c, ev = "cut", ""
                    else:
                        c = "worded"
        g["cause"], g["ev"] = c, ev
        if i is not None:
            used[i] = j
            g["pair"] = i
    gtk = collections.defaultdict(list)
    for g in gt:
        gtk[key(g["sp"])].append(g["t"])
    alltr = [g["t"] for g in gt if g["t"]]
    for i, r in enumerate(us):
        r["i"] = i
        r["cause"] = "paired" if i in used else ("x_nosp" if key(r["sp"]) not in gtk else
                     "x_trait" if any(same_trait(t, r["t"]) for t in gtk[key(r["sp"])]) else
                     "x_paper" if any(same_trait(t, r["t"]) for t in alltr) else "x_new")
    sp = collections.OrderedDict()
    for g in gt:
        g["v8d"] = v8d[(key(g["sp"]), nv(g["v"]))] > 0
        sp.setdefault(key(g["sp"]), {"name": g["sp"], "gt": [], "us": []})["gt"].append(g)
    for r in us:
        e = sp.setdefault(key(r["sp"]), {"name": r["sp"], "gt": [], "us": []})
        e["us"].append(r)
    for j, g in enumerate(gt):
        if "pair" in g:
            us[g["pair"]]["pairgt"] = True
    res.append({"paper": p, "species": list(sp.values())})
Path(out).write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
tot = collections.defaultdict(collections.Counter)
for P in res:
    for s in P["species"]:
        for g in s["gt"]:
            tot[g["cause"]][P["paper"]] += 1
        for r in s["us"]:
            tot[r["cause"]][P["paper"]] += 1
for c, v in sorted(tot.items(), key=lambda a: -sum(a[1].values())):
    print(f"{c:12s} {sum(v.values()):5d} {dict(v)}")
