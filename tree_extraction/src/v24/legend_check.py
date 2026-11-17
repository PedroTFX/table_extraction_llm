"""Does the legend passage explain this column? (v24 layer 'legend'; REVIEW_Opus5.5xtra_2026-11-16, sections 6 and 11.)
The calibration audit (2026-11-17) found 21 real errors among the decoder's 108 sure answers. Tracing them showed two
gaps in how the decoder picks the legend passage that defines a column's codes (full_run.decode_column):

  'none' ignored    QL asks which passage says what the column's values stand for, with 'none of these'. When nimble
                    answers 'none', the column was still decoded against every entry of the paper's inventory
                    (allowed = cats). Viza2023's 'Altitudinal distribution' cells '1.0' became 'they originated in
                    the tropics' (from an introduction's numbered list) although QL had said 'none' at 0.976; Vidal2023's
                    nesting site '1.0' became 'fire occurred 0 to 4 years ago' after 'none' at 0.853.
  one passage       QL is asked only when two or more passages are offered. With one, it is used unasked: Vidal2023's
                    other columns, Taillefer2018's overwintering stage 'L' -> 'lentic' (a habitat legend).

  rule              a column whose saved QL answer is a sure 'none' is not decoded; a column with one passage offered
                    and no QL answer is asked QL now (the passage, or none), in both option orders, and a sure 'none'
                    in both is not decoded either. Anything else: the saved decoding stands.
  apply             assembly reads the decode record of a rejected column as empty: its cells are written as printed.
                    Reverting a wrong decode gains no F1 (the code no more matches the GT's term than the wrong term
                    did); the measure is right decodes lost (the audit) and wrong terms no longer written.

    python full_run_v24.py v24:legend <papers>      writes <run>/legend_check/<paper>.json
"""
import json
import time

import decode_inv as di
import decode_units as du
import duels
import full_run as fr

Q = "Which passage says what the values in the column '{h}' stand for?"
NONE = ("none of these: no passage here says what this column's values stand for; they are written out as they are, "
        "or the passage is about something else")


def _flat(s):
    return " ".join(str(s or "").split())


def ask_one(ask, header, values, unit, codes):
    """QL with the one passage offered, and 'none', in both option orders -> (sure 'none' in both, log)."""
    shown = ", ".join(f"'{v}'" for v in values[:25])
    state = (f"A table in a scientific paper has a column named '{header}'. Its cells hold these values: {shown}. "
             f"The paper prints this passage that defines some of the same codes.")
    crit = {"p0": f"the passage ({unit['kind']}): \"{du.quote(unit['text'], codes)}\"", "none": NONE}
    log = []
    for c in (crit, dict(reversed(list(crit.items())))):
        ch, probs = ask(state, Q.format(h=header), c)
        log.append({"choice": ch, "probs": probs})
        if duels.sure(ch, probs, "none") != "none":
            return False, log
    return True, log


def run(run_dir, papers):
    """One paper at a time; resumable (run_dir/legend_check/<paper>.json). The tables are full_run.plan's."""
    out = run_dir / "legend_check"
    out.mkdir(parents=True, exist_ok=True)
    head = fr.head_runs()
    ask = duels.Nimble()
    for p in papers:
        f = out / f"{p}.json"
        df = run_dir / "decode" / f"{p}.json"
        if f.exists() or p not in head or not df.exists():
            continue
        t0 = time.time()
        dec = json.loads(df.read_text(encoding="utf-8"))
        cols = {(t.table_index, c.index): (t, c) for t, _f, _o, _x in fr.plan(p, head) for c in t.columns}
        units, cats, res = None, None, {}
        for key, r in dec.items():
            if not isinstance(r, dict) or ":" not in key:
                continue
            if not any((v or {}).get("term") for v in (r.get("cells") or {}).values()):
                continue                                   # nothing decoded in this column
            u = r.get("units") or {}
            if u.get("choice") == "none":
                sure = duels.sure("none", u.get("probs") or {}, "none") == "none"
                res[key] = {"reject": sure, "why": "QL said none" + ("" if sure else ", not sure")}
                continue
            offered = u.get("offered") or []
            if len(offered) != 1 or u.get("choice") is not None:
                continue                                   # QL was asked and chose a passage: the decoding stands
            k, c = map(int, key.split(":"))
            tc = cols.get((k, c))
            if tc is None:
                continue
            t, col = tc
            values = list(dict.fromkeys(_flat(x.get(col.name)) for x in t.records if _flat(x.get(col.name))))
            units = units or du.unit_texts(p)
            cats = cats or di.inventory(p)
            codes = du.column_units(cats, col.name, values).get(offered[0]) or set()
            if offered[0] not in units:
                continue
            ok, log = ask_one(ask, col.name, values, units[offered[0]], codes)
            res[key] = {"reject": ok, "why": "one passage, QL asked now", "unit": offered[0], "asked": log}
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        n = sum(r["reject"] for r in res.values())
        print(f"  [legend] {p:22s} {n} of {len(res)} checked columns not decoded "
              f"({sum('asked' in r for r in res.values())} asked now, {time.time() - t0:.0f}s)", flush=True)
    ask.unload()


def apply(dec, check):
    """The decode record with the rejected columns read as empty (their cells are written as printed)."""
    if not check:
        return dec
    out = dict(dec)
    for key, r in check.items():
        if r.get("reject") and key in out:
            out[key] = {"cells": {}, "units": (dec[key] or {}).get("units"), "legend_check": r.get("why")}
    return out
