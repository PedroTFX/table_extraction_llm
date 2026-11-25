"""
legend_calib2_values.py — one structural change to stage 2 of the two-stage legend calibration (2026-11-25), tested
on the oracle input only: the model judges every cell value of a column on its own, and code (not the model)
derives the column decision from those judgements.

Why: on the oracle input, stage 2 (legend_calib2.PROMPT2, one yes/no per column) missed 7 target columns, each
because the column also holds values the legend does not define. 14 non-target columns also mix legend codes with
other values (counts, statistics, neighbouring variables); stage 2 refused all of them. This test measures whether
value-level judgements recover the 7 without linking the 14.

Unchanged: the units, the candidate columns and their rendering (legend_calib.render_columns), the oracle input
(read from the calib2 run, the gold's cell-code mappings), the model and its options, stage 1, the evidence check,
R3abc, and legend_calib2.stage2_eval (the scorer).

  run    (gemma) one call per unit with oracle input
         per value: the legend codes it contains, whether the column uses them with the legend's meanings, a reason
         column decision (code): linked if at least one value uses a legend code with its meaning; its codes are the
         union of those codes; a value without a supported code never blocks the others
         -> TREE_OUTPUT/legend_coverage/calib2v_run_<stamp>.json
  score  (code) legend_calib2.stage2_eval on the new and the base oracle decisions, the outcome of every column
         before -> after by group (target or not; all values legend codes / legend codes among other values / no
         legend code), and the value judgements behind every change and every remaining error
         -> TREE_OUTPUT/legend_coverage/CALIB2V_REPORT_<stamp>_gold<version>.txt

    python legend_calib2_values.py run <calib2_run.json>
    python legend_calib2_values.py score <gold.json> <calib2v_run.json> <calib2_run.json>
"""
from __future__ import annotations

import collections
import json
import re
import sys
import time

import _paths  # noqa: F401
import legend_calib as cal
import legend_calib2 as c2

OUT = cal.OUT

PROMPT = """A passage of a scientific paper defines these codes:
{legend}

Below are table columns of the same paper (id | header | cell values). For each column, judge every cell value on its own: does the value use codes above with the meanings above? A column may also hold values the definitions above do not cover (other codes, labels, numbers, formulas, stray header text); such a value says nothing about the column's other values. Cells that only share the same letters, numbers or words but mean something else are not decoded by these definitions.

Columns:
{columns}

For every column give its id and, for every cell value listed for it:
- value: the value as listed
- codes: the codes above that the value contains ([] if none)
- same_meaning: true if, in this column, the value uses those codes with the meanings above; false if not, or if codes is []
- reason: a short reason, from the column's header or cells

Reply with JSON only."""

SCHEMA = {"type": "object", "required": ["columns"],
          "properties": {"columns": {"type": "array", "items": {
              "type": "object", "required": ["id", "values"],
              "properties": {"id": {"type": "string"}, "values": {"type": "array", "items": {
                  "type": "object", "required": ["value", "codes", "same_meaning", "reason"],
                  "properties": {"value": {"type": "string"}, "codes": {"type": "array", "items": {"type": "string"}},
                                 "same_meaning": {"type": "boolean"}, "reason": {"type": "string"}}}}}}}}}


def legend_code(s, legend):
    """The legend code a model-written code stands for, or None: the code itself, or a code written with its term
    ('1: underdeveloped', '0) = "within excrement"'; the same reading as legend_calib2.score)."""
    by = {cal.ncode(c): c for c in legend}
    if cal.ncode(s) in by:
        return by[cal.ncode(s)]
    m = re.match(r"\s*([^\s:=)]+)\s*[:=)]", str(s))
    return by.get(cal.ncode(m.group(1))) if m else None


def parse(raw, legend, cols):
    """-> ({column id: {'values': [judgement], 'codes': supported legend codes}}, ids the model gave that are not
    columns)"""
    out, bad = {}, []
    for a in raw if isinstance(raw, list) else []:
        if not isinstance(a, dict):
            continue
        good, wrong = cal.column_ids([a.get("id", "")], cols)
        bad += wrong
        for k in good:
            vals = []
            for v in a.get("values") or []:
                if not isinstance(v, dict):
                    continue
                written = [str(c) for c in v.get("codes") or []]
                read = [legend_code(c, legend) for c in written]
                vals.append({"value": str(v.get("value", "")), "codes": written,
                             "legend_codes": sorted({r for r in read if r}),
                             "not_legend_codes": [c for c, r in zip(written, read) if not r],
                             "same_meaning": bool(v.get("same_meaning")),
                             "reason": " ".join(str(v.get("reason") or "").split())})
            entry = out.setdefault(k, {"values": [], "codes": []})
            entry["values"] += vals
            entry["codes"] = sorted({c for x in entry["values"] if x["same_meaning"] for c in x["legend_codes"]})
    return out, bad


def run(base_file):
    import decoder as v1
    import decoder_v2 as v2
    units = json.loads((OUT / "calib_units.json").read_text(encoding="utf-8"))
    base = {u["uid"]: u for u in json.loads(open(base_file, encoding="utf-8").read())["units"]}
    stamp = time.strftime("%Y-%m-%d_%H%M")
    res = []
    for x in units:
        gm = base[x["uid"]]["oracle_input"]
        if not gm:
            continue
        t0 = time.time()
        cols = x["candidate_columns"]
        prompt = PROMPT.format(legend=c2.render_legend(gm), columns=cal.render_columns(cols))
        raw = v2._chat(prompt, SCHEMA, "columns")
        dec, bad = parse(raw, [m["code"] for m in gm], cols)
        res.append({"uid": x["uid"], "oracle_input": gm, "raw": raw, "columns": dec, "bad_ids": bad,
                    "assoc": {k: v["codes"] for k, v in dec.items() if v["codes"]},
                    "seconds": round(time.time() - t0, 1)})
        print(f"{len(res):3d} {x['uid']:28s} columns {len(dec)}/{len(cols)} linked {len(res[-1]['assoc'])} "
              f"values {sum(len(v['values']) for v in dec.values())}  {res[-1]['seconds']:5.1f}s", flush=True)
    f = OUT / f"calib2v_run_{stamp}.json"
    f.write_text(json.dumps({"model": v1.GEMMA, "date": stamp, "prompt": PROMPT, "base_run": str(base_file),
                             "units": res}, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"-> {f}")


# --- scoring ---------------------------------------------------------------------------------------------------

def outcome(t, values, pc):
    """The stage2_eval outcome of one candidate column (the same rule)."""
    g = {cal.ncode(x) for x in t["decoded_by"]}
    if g:
        if pc is None:
            return "missed column"
        held = cal.column_codes(values)
        return ("right column, right codes" if {cal.ncode(x) for x in pc} & held == g
                else "right column, wrong or incomplete codes")
    return "wrong column" if pc is not None else "TN"


SHORT = {"right column, right codes": "RR", "right column, wrong or incomplete codes": "RW", "missed column": "MC",
         "wrong column": "WC", "TN": "TN"}


def group(t, values, legend):
    """Mechanical: is the column a target, and do its values all read as legend codes, some, or none?"""
    leg = {cal.ncode(c) for c in legend}
    other = [v for v in values if cal.ncode(v) not in leg]
    some = bool(leg & cal.column_codes(values))
    kind = "all values legend codes" if not other else ("legend codes among other values" if some
                                                        else "no legend code")
    return ("target" if t["decoded_by"] else "not target") + ", " + kind


def score(gold_file, run_file, base_file):
    import pathlib
    gold = json.loads(open(gold_file, encoding="utf-8").read())
    if "frozen" not in gold.get("version", ""):
        raise SystemExit("the gold is not frozen")
    gv = gold["version"].split()[0]
    G = {u["uid"]: u for u in gold["units"]}
    R = json.loads(open(run_file, encoding="utf-8").read())
    new = {u["uid"]: u for u in R["units"]}
    base = {u["uid"]: u for u in json.loads(open(base_file, encoding="utf-8").read())["units"]}
    units = json.loads((pathlib.Path(gold_file).parent / "calib_units.json").read_text(encoding="utf-8"))
    cols = {(x["uid"], c["table"], c["col"]): c["values"] for x in units for c in x["candidate_columns"]}
    for k, u in new.items():
        assert u["oracle_input"] == base[k]["oracle_input"], k

    # the base oracle decisions, read as legend_calib2.score reads them (codes written with their terms)
    b_assoc = {}
    for k, r in base.items():
        leg = [m["code"] for m in r["oracle_input"]]
        for c, v in (r["oracle"] or {}).items():
            if v["decodes"]:
                b_assoc.setdefault(k, {})[c] = [legend_code(s, leg) or s for s in v["codes"]]
    n_assoc = {k: u["assoc"] for k, u in new.items()}

    L = [f"Stage 2 value-level test: {R['model']}, run {R['date']}, gold {gold['version']}, oracle input only "
         f"(the gold's cell-code mappings, as in the base run {pathlib.Path(base_file).name})",
         "One change against the base: the model judges each cell value; code links a column when at least one value "
         "uses a legend code with its meaning. Units, columns, rendering, oracle input, model and scorer unchanged.",
         f"{len(new)} units called; {sum(len(u['raw'] or []) for u in new.values())} column answers; "
         f"{sum(len(v['values']) for u in new.values() for v in u['columns'].values())} value judgements; "
         f"column ids that are not columns: {sum(len(u['bad_ids']) for u in new.values())}", ""]
    for name, a in (("BASE: stage 2 oracle (one yes/no per column)", b_assoc),
                    ("NEW: value-level stage 2 oracle", n_assoc)):
        S, _D = c2.stage2_eval(G, a, cols)
        L += ["=" * 100, name, "=" * 100] + S + [""]

    # every candidate column, before -> after, by group
    trans = collections.defaultdict(collections.Counter)
    detail = collections.defaultdict(list)
    for k, u in G.items():
        leg = [m["code"] for m in (new[k]["oracle_input"] if k in new else [])]
        for t in u["targets"]:
            col = f"t{t['table']}c{t['col']}"
            vals = cols[(k, t["table"], t["col"])]
            b = outcome(t, vals, b_assoc.get(k, {}).get(col))
            n = outcome(t, vals, n_assoc.get(k, {}).get(col))
            gname = group(t, vals, leg) if leg else "no oracle input (not called)"
            trans[gname][(SHORT[b], SHORT[n])] += 1
            if k not in new or (b, n) == ("TN", "TN"):
                continue
            judged = new[k]["columns"].get(col, {}).get("values", [])
            lines = [f"  {k} -> {col} {t['header'][:60]!r}: {SHORT[b]} -> {SHORT[n]}; gold {sorted(t['decoded_by'])}"
                     f", base {sorted(b_assoc.get(k, {}).get(col) or []) or '-'}, new "
                     f"{sorted(n_assoc.get(k, {}).get(col) or []) or '-'}"]
            if t.get("disputed_header"):
                lines[0] += " [disputed header]"
            shown = {v["value"] for v in judged}
            for v in judged:
                lines.append(f"      {v['value'][:40]!r}: codes {v['codes']} same_meaning {v['same_meaning']} "
                             f"| {v['reason'][:150]}")
            for v in vals:
                if v[:cal.VALUE_CHARS] not in shown:
                    lines.append(f"      {v[:40]!r}: (no judgement)")
            detail[gname].append(lines)
    L += ["=" * 100, "EVERY CANDIDATE COLUMN, base -> new (RR right column + right codes, RW right column + wrong or "
          "incomplete codes, MC missed, WC wrong column, TN)", "=" * 100]
    for gname in sorted(trans):
        L.append(f"  {gname}: " + ", ".join(f"{b}->{n} {c}" for (b, n), c in sorted(trans[gname].items())))
    L.append("")
    L += ["  Tonelli2021#p143 -> t7c13 (base wrong column) is an upstream input-boundary case: the unit starts at item "
          "'1.', without the heading '2) Nest type' and the preceding '0. No-nester'. It is scored like every column "
          "but is not what this test addresses; t7c14 (base missed) is the value-level case.", ""]
    cut = len(L)
    L += ["=" * 100, "DETAIL: every called column that is not TN in both runs, with the value judgements", "=" * 100]
    for gname in sorted(detail):
        L += ["", f"--- {gname}"]
        for lines in detail[gname]:
            L += lines
    # value judgements: legend codes the model saw but judged as another meaning
    coinc = [(k, c, v) for k, u in new.items() for c, x in u["columns"].items() for v in x["values"]
             if v["legend_codes"] and not v["same_meaning"]]
    L += ["", "=" * 100, f"VALUES WITH A LEGEND CODE JUDGED NOT TO USE ITS MEANING: {len(coinc)}", "=" * 100]
    L += [f"  {k} {c} {v['value'][:40]!r} codes {v['codes']} | {v['reason'][:150]}" for k, c, v in coinc]
    f = OUT / f"CALIB2V_REPORT_{R['date']}_gold{gv}.txt"
    f.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:cut]))
    print(f"-> {f}")


if __name__ == "__main__":
    {"run": run, "score": score}[sys.argv[1]](*sys.argv[2:])
