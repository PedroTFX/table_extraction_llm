"""Where GT values are lost, stage by stage: SUMMED over a group, no paper name, row or quote printed.
   python prose_funnel.py <output folder name> <group>   (no model is called)"""
import collections
import csv
import json
import re
import sys

import prose_reader as pr
import prose_test as pt

norm = lambda s: " " + " ".join(re.findall(r"[a-z0-9]+(?:[.,][0-9]+)?", str(s or "").lower())) + " "
base = pr._paths.OUTPUT / sys.argv[1]
papers = pr.papers_of(sys.argv[2:])
c, why, trig = collections.Counter(), collections.Counter(), collections.Counter()


def has(f, vals):
    return any(f in v or (len(v) > 3 and v in f) for v in vals)


for p in papers:
    load = lambda d: json.loads((base / d / f"{p}.json").read_text(encoding="utf-8"))
    ps = pr.passages(p)
    span, shape = load("walk")["span"], load("shape")["shape"]
    rd = load("read2")
    for k, v in (rd.get("triggers") or {}).items():
        trig[k] += v
    c["items in the log"] += sum(int(e.get("items", 0)) for e in (rd.get("log") or {}).values() if isinstance(e, dict))
    c["record_only items"] += len(rd.get("record_only") or [])
    text = collections.defaultdict(list)
    for u in ps:
        if u["kind"] != "para":
            continue
        c["paragraphs"] += 1
        sh = shape.get(u["id"], "text")
        c[f"paragraphs {sh}"] += 1
        c[f"chars {sh}"] += len(u["text"])
        if span.get(u["id"]):
            c["paragraphs in an account"] += 1
            c[f"in account, {sh}"] += 1
            c[f"chars in account, {sh}"] += len(u["text"])
            text[pt.key(span[u["id"]])].append((sh, norm(u["text"])))
    read_v = collections.defaultdict(set)
    for pid, r in rd["read"].items():
        s = span.get(pid)
        c["read facts"] += len(r.get("facts", []))
        c["read dropped"] += len(r.get("dropped", []))
        for x in r.get("dropped", []):
            why[f"read: {x.get('why', '')}"] += 1
        if s:
            for x in r.get("facts", []) + [y for y in r.get("dropped", []) if y.get("why") == "who not printed in the passage"]:
                read_v[pt.key(s)].add(norm(x["value"]).strip())
    fx = load("facts")
    kept_v, all_kept = collections.defaultdict(set), set()
    for x in fx["facts"]:
        c["facts in"] += 1
        if x["owner"] and not x["why"]:
            c["facts kept"] += 1
            kept_v[pt.key(x["owner"])].add(norm(x["value"]).strip())
            all_kept.add(norm(x["value"]).strip())
        else:
            why[f"facts: {x['why'] if x['owner'] or x['why'] else 'no owner'}"] += 1
    f = base / "prose" / p / f"{p}.csv"
    rows = list(csv.DictReader(open(f, encoding="utf-8")))
    c["rows"] += len(rows)
    row_v = collections.defaultdict(set)
    for r in rows:
        row_v[pt.key(r["verbatimIdentification"])].add(norm(r["measurementValue"]).strip())
    for g in pt.gt_rows(p):
        fv = norm(g["v"]).strip()
        if not fv or (len(fv) < 2 and fv.isdigit()):
            c["GT no value"] += 1
            continue
        c["GT with a value"] += 1
        k = pt.key(g["sp"])
        where = [sh for sh, t in text.get(k, []) if f" {' '.join(fv.split()[:8])} " in t]
        if not where:
            c["GT not printed in its account"] += 1
            continue
        sh = "list" if "list" in where else where[0]
        c[f"GT printed, {sh}"] += 1
        if not has(fv, read_v.get(k, ())):
            c[f"GT lost at reading, {sh}"] += 1
            continue
        if not has(fv, kept_v.get(k, ())):
            c[f"GT lost at the decisions, {sh}"] += 1
            continue
        if not has(fv, row_v.get(k, ())):
            c[f"GT lost at assembly, {sh}"] += 1
            continue
        c[f"GT reached a row, {sh}"] += 1

print(f"== {sys.argv[1]} on {' '.join(sys.argv[2:])}: {len(papers)} papers, totals only")
for k in sorted(c):
    print(f"  {k}: {c[k]}")
print("  triggers:", dict(trig))
print("  reasons:", dict(why))
