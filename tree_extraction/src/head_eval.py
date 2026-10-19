"""
head_eval.py — score a head-reader run against the person's marks of an earlier round:
  right & unchanged  ok
  right & CHANGED    a failure (the person's rule: tables marked right must not change),
                     listed with what changed
  wrong & changed    listed beside the person's note, to judge whether it now matches
  wrong & unchanged  still wrong
"Changed" compares the reading (header_review.reading: body start, cell roles, columns).

    python head_eval.py round3_full [round2] [2]
      run file, the run the marks were given on, the round of the marks
-> output/header_review/EVAL_<run>.txt
"""

from __future__ import annotations

import glob
import json
import os
import sys

import _paths
import header_review as hr
import head_tree_exp as he


def marks(round_no):
    d = hr.OUT / ("answers/reviews" if round_no == 1 else f"answers_r{round_no}/reviews_r{round_no}")
    out = {}
    for f in glob.glob(str(d / "*.json")):
        v = json.loads(open(f, encoding="utf-8").read())
        out[os.path.basename(f)[:-5]] = v.get("data", v)
    return out


def diff(a, b):
    """What changed between two readings of one table, in words."""
    out = []
    if a.get("data_start") != b.get("data_start"):
        out.append(f"body start {a.get('data_start')} -> {b.get('data_start')}")
    ra, rb = hr.roles_of(a), hr.roles_of(b)
    for k in sorted(set(ra) | set(rb)):
        if ra.get(k) != rb.get(k):
            out.append(f"cell {k}: {ra.get(k)} -> {rb.get(k)}")
    ca = {c["col"]: c for c in a.get("columns", [])}
    cb = {c["col"]: c for c in b.get("columns", [])}
    for c in sorted(set(ca) | set(cb)):
        x, y = ca.get(c, {}), cb.get(c, {})
        fa = (" > ".join(x.get("groups", [])), x.get("name", ""), ", ".join(x.get("details", [])))
        fb = (" > ".join(y.get("groups", [])), y.get("name", ""), ", ".join(y.get("details", [])))
        if fa != fb:
            out.append(f"col {c}: {fa} -> {fb}")
    return out


def main(argv):
    run = argv[0] if argv else "round3_full"
    base = argv[1] if len(argv) > 1 else "round2"
    rnd = int(argv[2]) if len(argv) > 2 else 2
    new = json.loads((he.EXP / f"{run}.json").read_text(encoding="utf-8"))
    old = json.loads((he.EXP / f"{base}.json").read_text(encoding="utf-8"))
    m = marks(rnd)
    groups = {"right & unchanged": [], "right & CHANGED": [], "wrong & changed": [],
              "wrong & unchanged": [], "not marked": []}
    for p in sorted(old):
        nb = {t["table"]: t for t in new.get(p, [])}
        for t in sorted(old[p], key=lambda x: x["table"]):
            k = hr.doc_id(p, t["table"])
            u = nb.get(t["table"])
            if u is None:
                continue
            changed = hr.reading(u) != hr.reading(t)
            v = (m.get(k) or {}).get("verdict")
            key = ("not marked" if not v else f"{v} & {'CHANGED' if v == 'right' and changed else 'changed' if changed else 'unchanged'}")
            groups[key].append((k, (m.get(k) or {}).get("note", ""), diff(t, u) if changed else []))
    L = [f"{run} vs {base}, against the person's round-{rnd} marks", ""]
    L += [f"  {g:20s}{len(v):4d}" for g, v in groups.items()]
    for g in ("right & CHANGED", "wrong & changed", "wrong & unchanged"):
        L += ["", f"{g}:"]
        for k, note, d in groups[g]:
            L.append(f"  {k}" + (f"   note: {note}" if note else ""))
            L += [f"      {x}" for x in d[:8]] + (["      …"] if len(d) > 8 else [])
    out = hr.OUT / f"EVAL_{run}.txt"
    out.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[:8]))


if __name__ == "__main__":
    main(sys.argv[1:])
