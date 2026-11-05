"""What are the facts dropped as 'value not printed in the passage'? COUNTS ONLY, summed over a group; no paper
name, value or quote is printed. No model is called.
   python prose_dropped.py <output folder name> <group>"""
import collections
import json
import re
import sys

import prose_reader as pr
import prose_test as pt

base = pr._paths.OUTPUT / sys.argv[1]
papers = pr.papers_of(sys.argv[2:])
c = collections.Counter()
big = 0
W = lambda s: re.findall(r"[^\W_]+", str(s or "").lower())
for p in papers:
    rd = json.loads((base / "read2" / f"{p}.json").read_text(encoding="utf-8"))
    span = json.loads((base / "walk" / f"{p}.json").read_text(encoding="utf-8"))["span"]
    ps = {u["id"]: u for u in pr.passages(p)}
    same = collections.defaultdict(list)
    for i, u in ps.items():
        if span.get(i):
            same[span[i]].append(u["text"])
    whole = "\n".join(u["text"] for u in ps.values())
    gt = {" ".join(W(g["v"])) for g in pt.gt_rows(p)}
    n = 0
    for pid, r in rd["read"].items():
        own = ps[pid]["text"] if pid in ps else ""
        ow = set(W(own))
        for x in r.get("dropped", []):
            if x.get("why") != "value not printed in the passage":
                continue
            n += 1
            v = x["value"]
            vw = W(v)
            c["dropped"] += 1
            c["words in the values"] += len(vw)
            if " ".join(vw) in gt:
                c["equal to a GT value of the paper"] += 1
            if pr.printed(v, own):
                c["printed in its whole passage (a dropped sentence had it)"] += 1
            elif any(pr.printed(v, t) for t in same.get(span.get(pid), [])):
                c["printed in another passage of the same account"] += 1
            elif pr.printed(v, whole):
                c["printed elsewhere in the paper"] += 1
            else:
                share = sum(w in ow for w in vw) / max(1, len(vw))
                c["not printed anywhere, " + ("all its words in its passage" if share == 1 else
                                              "80%+ of its words in its passage" if share >= .8 else
                                              "under 80% of its words in its passage")] += 1
            if re.search(r"[^\x00-\x7f]", v):
                c["value holds a non-ASCII character"] += 1
            if not re.search(r"\d", v):
                c["value without a digit"] += 1
    big += n >= 50
    letters = re.findall(r"[^\W\d_]", whole)
    c["papers mostly non-Latin letters"] += sum(ord(x) > 0x24f for x in letters) > len(letters) / 2
print(f"== {sys.argv[1]} on {' '.join(sys.argv[2:])}: {len(papers)} papers, counts only")
for k in sorted(c):
    print(f"  {k}: {c[k]}")
print(f"  papers with 50+ such drops: {big}")
