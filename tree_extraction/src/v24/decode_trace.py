"""decode_trace.py (2026-11-23) — where decoding fails, per legend pair (code -> GT term) of each coded column the GT shows (decode_key.build_key).
Stages, first failure wins:
  no decode record   the column was never decoded (not a trait column in the plan, or no inventory)
  not printed        the paper does not print the pair as a legend (decode_key.where: term only, not in the paper,
                     binary convention)
  inventory          printed, but the inventory has no entry for the cell whose term is the GT value
  not offered        the inventory has it, but the cell's record has no options (code form, list split)
  QK word            nimble called the cell a word, not a code
  QV keep / QV other nimble kept the cell / picked another entry
  wording            the right entry, another wording than the GT's
  right
Reads TREE_OUTPUT/full_run_v24/decode (the decode the CSVs use) and the inventory. No model.

    python decode_trace.py <papers>      -> TREE_OUTPUT/decode_trace.json
The review of its 7-paper trace led to legend_scope.py."""
import collections, json, sys
import _paths
import decode_key as dk, decode_inv as di, decoder as v1, decoder_v2 as v2
DEC = _paths.OUTPUT / "full_run_v24" / "decode"


def final(rec, code):
    rc = ((rec or {}).get("cells") or {}).get(code) or {}
    if rc.get("term"):
        return rc["term"]
    for e in ((rec or {}).get("endings") or {}).values():
        if e.get("choice") == "mark" and code in e["cells"]:
            return e["cells"][code]
    return code


def flat(s):
    return f" {v1._flat(s)} "


def same(a, b):
    a, b = flat(a), flat(b)
    return a == b or (b.strip() and b in a) or (a.strip() and a in b)


def trace(paper):
    found, grids = dk.build_key(paper)
    raw = (_paths.PAPERS / paper / f"{paper}_full.md").read_text(encoding="utf-8", errors="replace")
    text, spans = dk.clean(raw), dk.table_spans(raw)
    dec = json.loads((DEC / f"{paper}.json").read_text(encoding="utf-8")) if (DEC / f"{paper}.json").exists() else {}
    cats = di.inventory(paper) or []
    out = []
    for T, e in found.items():
        if e["kind"] != "coded":
            continue
        k, c = e["table"], e["col"]
        rec, under = dec.get(f"{k}:{c}"), None
        if rec is None:                  # a joined continuation table is decoded under the table it continues
            for k2 in range(k - 1, -1, -1):
                r2 = dec.get(f"{k2}:{c}")
                if r2 and any(code in (r2.get("cells") or {}) for code in e["coded"]):
                    rec, under = r2, k2
                    break
        g = grids[k]
        header = " ".join(str(g.at(r, c).text or "") for r in range(min(3, g.nrows)) if g.at(r, c))
        for code, term in e["coded"].items():
            ws = [dk.where(f, term, text, raw, grids, k, spans)[0] for f in v2.forms(code)]
            w = next((x for x in ws if not x.startswith(("term only", "not in the paper"))), ws[0])
            got = final(rec, code)
            rc = ((rec or {}).get("cells") or {}).get(code) or {}
            probs = rc.get("probs") or {}
            qk = (probs.get(f"{code} | QK") or {}).get("code")
            qv = probs.get(code) or {}
            opts = (rc.get("options") or {}).get(code) or {}
            if same(got, term):
                stage = "right" if flat(got) == flat(term) else "wording"
            elif rec is None:
                stage = "no decode record"
            elif w.startswith(("term only", "not in the paper")):
                stage = "not printed"
            elif not di.captured(cats, code, term, header):
                stage = "inventory"
            elif not opts:
                stage = "not offered"
            elif qk is not None and qk < 0.5:
                stage = "QK word"
            elif got == code:
                stage = "QV keep"
            else:
                stage = "QV other"
            best = max(qv.items(), key=lambda kv: float(kv[1] or 0)) if qv and all(not isinstance(v, dict) for v in qv.values()) else None
            out.append(dict(paper=paper, trait=T, table=k, col=c, header=header[:40], code=code, term=term, got=got,
                            stage=stage, where=w, qk=qk, qv=best, n_opts=len(opts.get("labels") or []),
                            labels=(opts.get("labels") or [])[:4], under=under))
    return out


if __name__ == "__main__":
    allrows = []
    for p in sys.argv[1:]:
        try:
            rows = trace(p)
        except Exception as err:
            print(f"### {p}: trace failed ({type(err).__name__}: {err})")
            continue
        allrows += rows
        c = collections.Counter(r["stage"] for r in rows)
        print(f"### {p}: {len(rows)} legend pairs in {len({(r['table'], r['col']) for r in rows})} coded columns: "
              + ", ".join(f"{s} {v}" for s, v in c.most_common()))
        for r in rows:
            if r["stage"] != "right":
                print(f"  t{r['table']}c{r['col']}{'(as t%s)' % r['under'] if r['under'] is not None else ''} {r['trait'][:28]!r} {r['code']!r} -> {r['term'][:30]!r}: got {r['got'][:30]!r} "
                      f"[{r['stage']}] where={r['where']}; QK p(code)={r['qk']}; QV={r['qv']}; "
                      f"{r['n_opts']} options {r['labels']}")
    c = collections.Counter(r["stage"] for r in allrows)
    print("### ALL:", len(allrows), "pairs:", ", ".join(f"{s} {v}" for s, v in c.most_common()))
    json.dump(allrows, open(_paths.OUTPUT / "decode_trace.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
