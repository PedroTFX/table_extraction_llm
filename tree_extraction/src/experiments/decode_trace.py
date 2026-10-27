"""Where the full run's coded cells stopped in the decoder: for every trait column whose
cells look like codes (short tokens, 0/1), the decoder outcome per cell, weighted by the
number of records. Reads saved files only, no model.

    python decode_trace.py [paper ...]
"""
import collections
import json
import re
import sys

import full_run as fr

CODEY = re.compile(r"^(?:[01]|[A-Za-z]{1,4}\d?|[A-Z][A-Za-z]{0,5}(?:[/,; ]+[A-Z][A-Za-z]{0,5})*)$")


def best(qv):
    out = {}
    for k, x in (qv or {}).items():
        if isinstance(x, dict):
            for k2, y in x.items():
                out[k2] = max(out.get(k2, 0), y)
        else:
            out[k] = x
    return out


def outcome(rec, cell):
    if rec is None:
        return "column not decoded"
    c = (rec.get("cells") or {}).get(cell)
    if c is None:
        ch = (rec.get("units") or {}).get("choice")
        return "no candidates" + (f" (QL: {ch})" if ch else "")
    if c.get("term"):
        return "decoded"
    pr = c.get("probs") or {}
    qk = pr.get(cell + " | QK") or {}
    if qk and qk.get("word", 0) > qk.get("code", 0):
        return "QK: word"
    return "QV: keep"


def main(papers):
    head = fr.head_runs()
    papers = papers or fr.gt_papers()
    total = collections.Counter()
    for paper in papers:
        if paper not in head:
            continue
        df = fr.OUT / "decode" / f"{paper}.json"
        dec = json.loads(df.read_text(encoding="utf-8")) if df.exists() else {}
        per = collections.Counter()
        ex = {}
        for t, fields, _o, _x in fr.plan(paper, head):
            for col in t.columns:
                if fields.get(col.name) not in fr.TRAITS:
                    continue
                vals = collections.Counter(fr._clean(r.get(col.name)) for r in t.records)
                vals.pop("", None)
                if not vals or not all(CODEY.match(v) for v in vals):
                    continue
                if all(re.fullmatch(r"\d+", v) and v not in ("0", "1") for v in vals):
                    continue
                distinct = list(dict.fromkeys(fr._clean(r.get(col.name)) for r in t.records if fr._clean(r.get(col.name))))
                rec = dec.get(f"{t.table_index}:{col.index}")
                for v, n in vals.items():
                    o = outcome(rec, v)
                    if v not in distinct[:25]:
                        o = "beyond the 25 values sent"
                    per[o] += n
                    ex.setdefault(o, f"t{t.table_index} '{col.name[:30]}' {v!r}")
        if per:
            total.update(per)
            print(f"{paper:22s} " + "; ".join(f"{k} {v}" for k, v in per.most_common()))
            for k, e in ex.items():
                if k != "decoded":
                    print(f"{'':24s}{k}: {e}")
    print("\nTOTAL", dict(total.most_common()))


if __name__ == "__main__":
    main(sys.argv[1:])
