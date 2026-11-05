"""Would the 'value not printed' drops pass once a trailing unit is set aside? COUNTS ONLY, summed over a group; no
paper name, value or quote is printed. No model is called, nothing is written.
   python prose_unit_check.py <output folder name> <group>"""
import collections
import json
import re
import sys

import prose_reader as pr
import prose_test as pt

UNIT = re.compile(r"^(.*?\d[^A-Za-z]*?)\s*(mm|cm|µm|μm|um|m|km|g|mg|kg|ml|°c|%)\.?$", re.I)
norm = lambda s: " " + " ".join(re.findall(r"[a-z0-9]+(?:[.,][0-9]+)?", str(s or "").lower())) + " "
base = pr._paths.OUTPUT / sys.argv[1]
papers = pr.papers_of(sys.argv[2:])
c = collections.Counter()
for p in papers:
    rd = json.loads((base / "read2" / f"{p}.json").read_text(encoding="utf-8"))
    span = json.loads((base / "walk" / f"{p}.json").read_text(encoding="utf-8"))["span"]
    ps = {u["id"]: u for u in pr.passages(p)}
    read_v, rescued = collections.defaultdict(set), collections.defaultdict(set)
    for pid, r in rd["read"].items():
        s = span.get(pid)
        own = ps[pid]["text"] if pid in ps else ""
        if s:
            for x in r.get("facts", []) + [y for y in r.get("dropped", []) if y.get("why") == "who not printed in the passage"]:
                read_v[pt.key(s)].add(norm(x["value"]).strip())
        for x in r.get("dropped", []):
            if x.get("why") != "value not printed in the passage":
                continue
            c["dropped"] += 1
            m = UNIT.match(x["value"].strip())
            if not m:
                c["no trailing unit"] += 1
                continue
            c["ends in a unit"] += 1
            if pr.printed(m.group(1), own):
                c["ends in a unit, the number IS printed in its passage"] += 1
                if s:
                    rescued[pt.key(s)].add(norm(m.group(1)).strip())
            else:
                c["ends in a unit, the number is not printed either"] += 1
    has = lambda f, vals: any(f in v or (len(v) > 3 and v in f) for v in vals)
    for g in pt.gt_rows(p):
        f = norm(g["v"]).strip()
        if not f or (len(f) < 2 and f.isdigit()):
            continue
        k = pt.key(g["sp"])
        if not has(f, read_v.get(k, ())):
            c["GT values no read fact holds"] += 1
            if has(f, rescued.get(k, ())):
                c["GT values no read fact holds, but a rescued number does"] += 1
print(f"== {sys.argv[1]} on {' '.join(sys.argv[2:])}: {len(papers)} papers, counts only")
for k in sorted(c):
    print(f"  {k}: {c[k]}")
