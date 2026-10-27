"""
decode_units.py — decoding with the fixed legend inventory PLUS a per-column choice of
legend passage (2026-10-14, agreed with the person's pasted review).

Why: the paper-wide inventory (decode_inv.py) is stable, but a short code gets look-alike
candidates from every legend of the paper (Graf 'A': 4, 'S': 3) and nimble keeps it as
printed (Graf 781 -> 468). The inventory records each entry's source unit, so:

  QL  (nimble, once per column) "Which passage says what the values in the column
      '<header>' stand for?" — options: the paper's units holding an entry for one of
      the column's codes (quoted around the code, at most MAX_UNITS, most codes first),
      'several of these' (all their entries stay) and 'none of these' (every value is
      kept as printed). No unit -> no question, values kept (as before).
  then decoder_v2.match_column (QK, QV, QB) on the chosen unit's entries only.

The inventory is never rebuilt (invariance kept). Runs: key | chain | espinosa | score.

    python decode_units.py key | chain | espinosa | score
-> output/decode_key/units_key/, units_chain/, units_ESPINOSA.txt, units_SCORE.txt
"""

from __future__ import annotations

import collections
import json
import re
import sys
import time

import column_tree as ct
import decode_chain as dc
import decode_inv as di
import decode_key as dk
import decoder as v1
import decoder_v2 as v2
import legend_inventory as li

RUNS = {"key": dk.OUT / "units_key", "chain": dk.OUT / "units_chain"}
MAX_UNITS = 8
QUOTE = 260


def unit_texts(paper):
    return {u["id"]: u for u in json.loads((li.OUT / f"{paper}.json").read_text(encoding="utf-8"))["units"]}


def column_units(cats, header, values):
    """unit id -> the column's values it holds an entry for (candidates as v2 offers them)."""
    by = collections.defaultdict(set)
    for v in values:
        for p in v1.list_parts(v):
            _ev, es = v2.candidates(cats, p, header)
            for e in es:
                if e.get("unit"):
                    by[e["unit"]].add(p)
    return by


def quote(text, codes):
    """The unit around the first printed code of the column (a window, not the whole unit)."""
    i = min((m.start() for c in codes for f in v2.forms(c)
             for m in [re.search(r"(?<![\w])" + re.escape(f) + r"(?![\w])", text)] if m), default=0)
    a = max(0, i - 80)
    return ("…" if a else "") + " ".join(text[a:a + QUOTE].split()) + ("…" if a + QUOTE < len(text) else "")


def choose_unit(client, header, values, units, by):
    """QL -> (chosen unit ids | 'none', record)."""
    ranked = sorted(by, key=lambda u: (-len(by[u]), int(u[1:])))[:MAX_UNITS]
    shown = ", ".join(f"'{v}'" for v in values[:25])
    crit = {f"p{i}": f"the passage ({units[u]['kind']}): \"{quote(units[u]['text'], by[u])}\""
            for i, u in enumerate(ranked)}
    crit["several"] = "more than one of these passages: the column's codes are defined in several of them"
    crit["none"] = ("none of these: no passage here says what this column's values stand for; they "
                    "are written out as they are, or the passages are about something else")
    state = (f"A table in a scientific paper has a column named '{header}'. Its cells hold these "
             f"values: {shown}. The paper prints these passages that define some of the same codes.")
    ch, probs = v1.ask(client, state, f"Which passage says what the values in the column '{header}' "
                       f"stand for?", crit)
    rec = {"offered": ranked, "choice": ch, "probs": probs}
    if not ch or ch == "none":
        return "none", rec
    if ch == "several":
        return set(ranked), rec
    return {ranked[int(ch[1:])]}, rec


def match_column(client, paper, header, values, cats, units):
    by = column_units(cats, header, values)
    if not by:
        r = v2.match_column(client, header, values, [e for e in cats if not e.get("code")])
        r["units"] = {"offered": [], "choice": None}
        return r
    chosen, rec = choose_unit(client, header, values, units, by)
    if chosen == "none":
        return {"cells": {}, "units": rec}
    allowed = [e for e in cats if e.get("unit") in chosen]
    r = v2.match_column(client, header, values, allowed)
    r["units"] = {**rec, "chosen": sorted(chosen)}
    return r


def _match_safe(client, paper, header, values, cats, units):
    for attempt in range(3):
        try:
            return match_column(client, paper, header, values, cats, units)
        except RuntimeError as err:
            if attempt == 2 or "llama-server" not in str(err):
                raise
            print(f"  model load timed out, retrying in 30s ({paper})", flush=True)
            time.sleep(30)


def match(run, papers):
    out = RUNS[run] / "match"
    out.mkdir(parents=True, exist_ok=True)
    head = json.loads(dc.HEAD.read_text(encoding="utf-8"))
    tags = json.loads(dc.TAGS.read_text(encoding="utf-8"))
    key = v1.load_key()
    client = ct.DecisionClient(v1.NIMBLE, 1)
    for paper in papers:
        f = out / f"{paper}.json"
        cats = di.inventory(paper)
        if f.exists() or cats is None:
            continue
        units = unit_texts(paper)
        cols = di.columns(run, paper, head, tags, key) if (run == "key" or paper in head) else []
        res, t0, c0 = {"_columns": cols}, time.time(), client.calls
        for k, c, header, values in cols:
            r = _match_safe(client, paper, header, values, cats, units)
            r["header"] = header
            res[f"{k}:{c}"] = r
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  [{run}] {paper:22s} {len(cols)} columns, {client.calls - c0} questions "
              f"({time.time() - t0:.0f}s)", flush=True)
    v1.unload(v1.NIMBLE)


def espinosa():
    paper = "Espinosa2023"
    cats, units = di.inventory(paper), unit_texts(paper)
    old = json.loads((dk.OUT / "chain_before_fixes" / "organise" / f"{paper}.json")
                     .read_text(encoding="utf-8"))["columns"]
    head = json.loads(dc.HEAD.read_text(encoding="utf-8"))
    tags = json.loads(dc.TAGS.read_text(encoding="utf-8"))
    new = [list(c) for c in dc.chain_columns(paper, head, tags)]
    client = ct.DecisionClient(v1.NIMBLE, 1)
    key = v1.load_key()
    L = [f"Espinosa2023 invariance with passage choice (inventory {len(cats)} entries, unchanged)"]
    choices = {}
    for name, cols in (("5 columns", old), ("19 columns", new)):
        res = {f"{k}:{c}": _match_safe(client, paper, h, v, cats, units) for k, c, h, v in cols}
        rows = v2.score_dir_from(paper, key[paper], lambda e: dc.lookup(res, e["table"], e["col"]))
        coded = [r for r in rows if r["kind"] == "coded"]
        ok = sum(r["w"] for r in coded if r["out"] in ("right", "right, unit inside"))
        choices[name] = {k: (r.get("units") or {}).get("chosen") or (r.get("units") or {}).get("choice")
                         for k, r in res.items()}
        L.append(f"  {name:11s}: {len(cols)} columns -> coded rows right {ok}/{sum(r['w'] for r in coded)}")
    same = {k: (choices["5 columns"][k], choices["19 columns"].get(k)) for k in choices["5 columns"]}
    L.append("  passage chosen per column, 5-column run vs 19-column run (must agree):")
    L += [f"    {k}: {a} | {b}{'' if a == b else '   <-- DIFFERENT'}" for k, (a, b) in same.items()]
    v1.unload(v1.NIMBLE)
    (dk.OUT / "units_ESPINOSA.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


def right_units(cats, e):
    """The units holding the key's right entries for this column's coded cells."""
    out = set()
    for cell, want in e["coded"].items():
        _ev, es = v2.candidates(cats, cell, "")
        for x in es:
            w, f1, f2 = f" {v1._flat(want)} ", f" {v1._flat(x.get('term') or '')} ", f" {v1._flat(x.get('label') or '')} "
            if x.get("unit") and any(f.strip() and (f == w or w in f or f in w) for f in (f1, f2)):
                out.add(x["unit"])
    return out


def score():
    key = v1.load_key()
    dev = v1.dev_papers()
    L = ["decoding with the fixed inventory + per-column passage choice (QL) — measures apart", ""]
    for run, d in RUNS.items():
        m = collections.Counter()
        per = []
        for paper in li.coded_papers():
            f = d / "match" / f"{paper}.json"
            cats = di.inventory(paper)
            if not f.exists() or cats is None:
                continue
            dec = {k: v for k, v in json.loads(f.read_text(encoding="utf-8")).items() if not k.startswith("_")}
            s = "dev" if paper in dev else "new"
            sel_cols = {}                                  # trait -> passage chosen right?
            for T, e in key[paper].items():
                if e["kind"] != "coded":
                    continue
                r = dc.lookup(dec, e["table"], e["col"])
                good = right_units(cats, e)
                if r is None or not good:
                    continue
                ch = (r.get("units") or {}).get("chosen") or []
                m[(s, "sel_n")] += 1
                m[(s, "sel_ok")] += bool(set(ch) & good)
                sel_cols[T] = bool(set(ch) & good)
            ok_p = n_p = 0
            for row in v2.score_dir_from(paper, key[paper], lambda e: dc.lookup(dec, e["table"], e["col"])):
                if row["kind"] == "kept":
                    m[(s, "kept_n")] += row["w"]
                    m[(s, "kept_ok")] += row["w"] * (row["out"] == "right")
                    continue
                if row["out"] in ("no legend printed", "GT error"):
                    continue
                right = row["out"] in ("right", "right, unit inside")
                cap = di.captured(cats, row["cell"], row["want"])
                m[(s, "e2e_n")] += row["w"]
                m[(s, "e2e_ok")] += row["w"] * right
                m[(s, "inv_n")] += row["w"]
                m[(s, "inv_ok")] += row["w"] * cap
                if cap and sel_cols.get(row["trait"]):
                    m[(s, "mat_n")] += row["w"]
                    m[(s, "mat_ok")] += row["w"] * right
                    m[(s, "mat_wording")] += row["w"] * (row["out"] in ("right, longer wording", "right, shorter wording"))
                ok_p += row["w"] * right
                n_p += row["w"]
            per.append(f"    [{s}] {paper:20s} {ok_p}/{n_p}")
        pct = lambda s, k: f"{m[(s, k + '_ok')]}/{m[(s, k + '_n')]} ({m[(s, k + '_ok')] / m[(s, k + '_n')]:.0%})" \
            if m[(s, k + "_n")] else "-"
        L.append(f"run '{run}' ({'answer-key columns' if run == 'key' else 'end-to-end: the chain picks the columns'}):")
        for s in ("dev", "new"):
            L.append(f"  {s}: passage choice {pct(s, 'sel')} (columns)   inventory {pct(s, 'inv')}   "
                     f"matching given the right passage {pct(s, 'mat')} (+{m[(s, 'mat_wording')]} wording only)   "
                     f"end-to-end {pct(s, 'e2e')}   kept as printed {pct(s, 'kept')}")
        L += ["  per paper, end-to-end (species rows):"] + per + [""]
    (dk.OUT / "units_SCORE.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


def main(argv):
    cmd = argv[0]
    papers = argv[1:] or li.coded_papers()
    if cmd in RUNS:
        match(cmd, papers)
    elif cmd == "espinosa":
        espinosa()
    else:
        score()


if __name__ == "__main__":
    main(sys.argv[1:])
