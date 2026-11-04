"""Pairs of (GT trait name, our trait name) that share a value for the same species, for judging by hand."""
import csv, re, sys, collections, json, openpyxl
N, root = sys.argv[1], sys.argv[2]
def key(name):
    w = re.findall(r"[A-Za-z]+", str(name or ""))
    return f"{w[0][0].lower()}. {w[1].lower()}" if len(w) >= 2 and w[1][0].islower() else " ".join(w[:2]).lower()
UNIT = r"(?:mm|cm|µm|μm|m|°c|%)"
def nv(v):
    s = str(v or "").lower().replace("–", "-").replace("—", "-").replace("−", "-").replace("×", "x")
    s = re.sub(r"\s*-\s*", "-", s)
    s = re.sub(r"^(there (is|are)|is|are|it is|they are)\s+", "", s.strip())
    s = re.sub(rf"(?<=\d)\s*{UNIT}\b", "", s)
    s = re.sub(r"\b(\d+)\.0+\b", r"\1", s)
    s = re.sub(r"(\d\.\d*?)0+\b", r"\1", s)
    s = re.sub(r"[\s.;:,]+$", "", s)
    return " ".join(s.split())
def gt_rows(p):
    ws = openpyxl.load_workbook(f"{root}/data/un_processed_papers/{p}/{p}.xlsx", read_only=True, data_only=True).worksheets[0]
    it = ws.iter_rows(values_only=True); h = [str(x or "").strip() for x in next(it)]
    g = lambda r, k: ("" if r[h.index(k)] is None else str(r[h.index(k)]).strip()) if k in h else ""
    return [{"sp": g(r, "verbatimIdentification"), "t": g(r, "measurementType"), "v": g(r, "measurementValue")} for r in it
            if g(r, "verbatimIdentification") or g(r, "measurementValue")]
out = {}
for p in ["Xia2022", "Xu2024", "Ustjuzhanin2024"]:
    gt = gt_rows(p)
    us = [{"sp": r["verbatimIdentification"], "t": r["measurementType"], "v": r["measurementValue"]}
          for r in csv.DictReader(open(f"{N}/{__import__('os').environ.get('OURS', 'ours3')}/{p}.csv", encoding="utf-8"))]
    idx = collections.defaultdict(list)
    for r in us: idx[(key(r["sp"]), nv(r["v"]))].append(r["t"])
    pairs = collections.Counter()
    for g in gt:
        for t in set(idx.get((key(g["sp"]), nv(g["v"])), [])):
            pairs[(g["t"], t)] += 1
    out[p] = pairs
    print(f"===== {p}: {len(pairs)} distinct name pairs sharing a value")
    for (a, b), c in sorted(pairs.items(), key=lambda x: (x[0][0].lower(), -x[1])):
        print(f"  {c:4d}  GT {a[:45]!r:47s} ours {b[:60]!r}")
