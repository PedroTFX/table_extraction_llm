"""Side-by-side page: per paper, each species once, the GT's rows beside ours, straight from the GT
xlsx and our prose CSV (no scorer). Species are grouped by genus initial + epithet ('A. sroczki' =
'Alucita sroczki Ustjuzhanin & Kovtunovich, sp. nov.'); within a species, rows with the same trait
name (case, spaces and punctuation aside) sit on one line, then rows with the same value, then the rest.
    python prose_page.py <papers dir> <our csv dir> <template.html> <out.html> <paper ...>"""
import csv, json, re, sys

import openpyxl

papers_dir, ours_dir, tpl, out, *papers = sys.argv[1:]
KEEP = ["verbatimIdentification", "measurementType", "measurementValue", "measurementUnit", "sex", "measurementStatistic", "measurementMethod"]
nt = lambda s: " ".join(re.findall(r"[a-z0-9]+", str(s or "").lower()))
nv = lambda s: " ".join(re.findall(r"[a-z0-9]+(?:[.,][0-9]+)?", re.sub(r"[–—−]", "-", str(s or "").lower())))


def key(name):
    w = re.findall(r"[A-Za-z]+", str(name or ""))
    if len(w) >= 2 and w[1][0].islower():
        return f"{w[0][0].lower()}. {w[1].lower()}"
    return " ".join(w[:2]).lower() or "(no name)"


def gt_rows(p):
    ws = openpyxl.load_workbook(f"{papers_dir}/{p}/{p}.xlsx", read_only=True, data_only=True).worksheets[0]
    it = ws.iter_rows(values_only=True)
    head = [str(h or "").replace("\xa0", " ").strip() for h in next(it)]
    out = []
    for r in it:
        d = {k: ("" if r[head.index(k)] is None else str(r[head.index(k)]).strip()) if k in head and head.index(k) < len(r) else ""
             for k in KEEP}
        if d["verbatimIdentification"] or d["measurementType"] or d["measurementValue"]:
            out.append(d)
    return out


data = []
for p in papers:
    gt = gt_rows(p)
    ours = [{k: r.get(k, "") or "" for k in KEEP} for r in csv.DictReader(open(f"{ours_dir}/{p}.csv", encoding="utf-8"))]
    groups = {}
    for side, rows in (("gt", gt), ("us", ours)):
        for r in rows:
            g = groups.setdefault(key(r["verbatimIdentification"]), {"gt": [], "us": [], "names_gt": [], "names_us": []})
            g[side].append(r)
            nm = r["verbatimIdentification"]
            if nm not in g["names_" + side]:
                g["names_" + side].append(nm)
    species = []
    for k, g in groups.items():
        us = list(g["us"])
        lines, left = [], list(g["gt"])
        passes = [("same trait, same value", lambda r, x: nt(x["measurementType"]) == nt(r["measurementType"])
                   and nv(x["measurementValue"]) == nv(r["measurementValue"])),
                  ("same value", lambda r, x: nv(x["measurementValue"]) and nv(x["measurementValue"]) == nv(r["measurementValue"])),
                  ("same trait", lambda r, x: nt(x["measurementType"]) == nt(r["measurementType"]))]
        for label, same in passes:                          # equal values first, so 850 sits beside 850
            nxt_left = []
            for r in left:
                j = next((i for i, x in enumerate(us) if same(r, x)), None)
                if j is None:
                    nxt_left.append(r)
                else:
                    lines.append({"gt": r, "us": us.pop(j), "pair": label})
            left = nxt_left
        lines += [{"gt": r, "us": None, "pair": ""} for r in left] + [{"gt": None, "us": x, "pair": ""} for x in us]
        lines.sort(key=lambda l: nt((l["gt"] or l["us"])["measurementType"]))   # a trait's rows together
        species.append({"key": k, "names_gt": g["names_gt"], "names_us": g["names_us"],
                        "n_gt": len(g["gt"]), "n_us": len(g["us"]), "lines": lines})
    species.sort(key=lambda s: (not s["n_gt"], s["names_gt"][0] if s["names_gt"] else s["names_us"][0]))
    data.append({"paper": p, "n_gt": len(gt), "n_us": len(ours), "species": species})

html = open(tpl, encoding="utf-8").read().replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
open(out, "w", encoding="utf-8").write(html)
print(out, [(d["paper"], d["n_gt"], d["n_us"], len(d["species"])) for d in data])
