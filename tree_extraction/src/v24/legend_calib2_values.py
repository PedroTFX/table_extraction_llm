"""
legend_calib2_values.py — structural tests of stage 2 of the two-stage legend calibration (2026-11-25), each on the
oracle input only and each one change against the base stage 2 (legend_calib2.PROMPT2, one yes/no per column:
"do the definitions decode the column's cells?").

Why: on the oracle input the base stage 2 missed 7 target columns, each because the column also holds values the
legend does not define; 14 non-target columns also mix legend codes with other values (counts, statistics,
neighbouring variables), and the base refused all of them.

  values  (run 2026-11-25_1642, failed) the model judges every cell value on its own; code links a column when at
          least one value uses a legend code with its meaning. 7 misses recovered, 10 of the 14 decoys linked.
  gate    (run 2026-11-25_1652, failed; the last stage 2 test on this calibration set) the column question becomes
          "does this column, header and cells taken together, record what the definitions describe?"; values the
          definitions do not cover do not decide it. Same output otherwise (id, the gate, codes, evidence); the
          column is linked when the gate is true, with the codes the model gives. 3 of the 7 misses recovered; the
          other 4 still refused for an undefined value, among them Kratschmer t12c2/t13c2 while the same header
          t11c2 is accepted 'H is an unmapped value'; 3 of the 14 decoys linked (Cajaiba's numeric sub-columns,
          where a code stands once among numbers).

Decision (fixed before the gate run): the base stage 2 stays. A column that a legend decodes only in part (it also
holds undefined codes, stray header text or other variables) is refused: a known recall limitation of stage 2, 7 of
the 31 proposed target columns on the oracle input of this calibration set. Stage 2 is not tuned further on these
59 units.

Unchanged: the units, the candidate columns and their rendering (legend_calib.render_columns), the oracle input
(read from the calib2 run: the gold's cell-code mappings), the model and its options, stage 1, the evidence check,
R3abc, and legend_calib2.stage2_eval (the scorer).

The acceptance criteria were fixed before the gate run (review, 2026-11-25) and are checked by `score`:
  C1 the 7 columns the base missed: all right column + right codes
  C2 the 24 columns the base got right: all still right
  C3 the 14 non-target columns that mix legend codes with other values: all refused
  C4 the non-target columns whose values are all legend codes, that the values test linked and the base refused
     (2): refused
  C5 the base's other wrong column (Cecala's row numbers): refused
  Tonelli2021#p143 -> t7c13 is reported apart: an upstream input-boundary case (the unit lacks the heading and the
  preceding '0.'), evidence neither for nor against a stage 2 change.

    python legend_calib2_values.py run <calib2_run.json> values|gate
    python legend_calib2_values.py score <gold.json> <calib2v_run.json> <calib2_run.json> [<values run.json>]
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
BOUNDARY = {("Tonelli2021#p143", "t7c13")}

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

PROMPT_GATE = """A passage of a scientific paper defines these codes:
{legend}

Below are table columns of the same paper (id | header | cell values). For each column, decide from its header and its cells taken together whether the column records what these definitions describe: whether its cells use these codes for the same thing the definitions are about. A column can record it and still hold values the definitions do not cover (other codes, labels, numbers, formulas, stray header text); such values do not decide it. Cells that only share the same letters, numbers or words but mean something else are not decoded by these definitions.

Columns:
{columns}

For every column give:
- id: the column's id
- records: true if the column records what these definitions describe, false if not
- codes: the codes above that the column's cells use with these meanings ([] if records is false)
- evidence: a short reason, from the column's header or cells

Reply with JSON only."""

SCHEMA_GATE = {"type": "object", "required": ["columns"],
               "properties": {"columns": {"type": "array", "items": {
                   "type": "object", "required": ["id", "records", "codes", "evidence"],
                   "properties": {"id": {"type": "string"}, "records": {"type": "boolean"},
                                  "codes": {"type": "array", "items": {"type": "string"}},
                                  "evidence": {"type": "string"}}}}}}


def legend_code(s, legend):
    """The legend code a model-written code stands for, or None: the code itself, or a code written with its term
    ('1: underdeveloped', '0) = "within excrement"'; the same reading as legend_calib2.score)."""
    by = {cal.ncode(c): c for c in legend}
    if cal.ncode(s) in by:
        return by[cal.ncode(s)]
    m = re.match(r"\s*([^\s:=)]+)\s*[:=)]", str(s))
    return by.get(cal.ncode(m.group(1))) if m else None


def parse(raw, legend, cols):
    """values test -> ({column id: {'values': [judgement], 'codes': supported legend codes}}, ids that are not
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


def parse_gate(raw, legend, cols):
    """gate test -> ({column id: {'records', 'codes' (read as legend codes where they are), 'written', 'evidence'}},
    ids that are not columns)"""
    out, bad = {}, []
    for a in raw if isinstance(raw, list) else []:
        if not isinstance(a, dict):
            continue
        good, wrong = cal.column_ids([a.get("id", "")], cols)
        bad += wrong
        written = [str(c) for c in a.get("codes") or []]
        for k in good:
            out[k] = {"records": bool(a.get("records")), "written": written,
                      "codes": [legend_code(c, legend) or c for c in written],
                      "evidence": " ".join(str(a.get("evidence") or "").split())}
    return out, bad


def run(base_file, test):
    import decoder as v1
    import decoder_v2 as v2
    assert test in ("values", "gate"), test
    units = json.loads((OUT / "calib_units.json").read_text(encoding="utf-8"))
    base = {u["uid"]: u for u in json.loads(open(base_file, encoding="utf-8").read())["units"]}
    stamp = time.strftime("%Y-%m-%d_%H%M")
    prompt_, schema_ = (PROMPT, SCHEMA) if test == "values" else (PROMPT_GATE, SCHEMA_GATE)
    res = []
    for x in units:
        gm = base[x["uid"]]["oracle_input"]
        if not gm:
            continue
        t0 = time.time()
        cols = x["candidate_columns"]
        raw = v2._chat(prompt_.format(legend=c2.render_legend(gm), columns=cal.render_columns(cols)), schema_,
                       "columns")
        legend = [m["code"] for m in gm]
        if test == "values":
            dec, bad = parse(raw, legend, cols)
            assoc = {k: v["codes"] for k, v in dec.items() if v["codes"]}
        else:
            dec, bad = parse_gate(raw, legend, cols)
            assoc = {k: v["codes"] for k, v in dec.items() if v["records"]}
        res.append({"uid": x["uid"], "oracle_input": gm, "raw": raw, "columns": dec, "bad_ids": bad, "assoc": assoc,
                    "seconds": round(time.time() - t0, 1)})
        print(f"{len(res):3d} {x['uid']:28s} columns {len(dec)}/{len(cols)} linked {len(assoc)}  "
              f"{res[-1]['seconds']:5.1f}s", flush=True)
    f = OUT / f"calib2{'v' if test == 'values' else 'g'}_run_{stamp}.json"
    f.write_text(json.dumps({"model": v1.GEMMA, "date": stamp, "test": test, "prompt": prompt_,
                             "base_run": str(base_file), "units": res}, indent=1, ensure_ascii=False), encoding="utf-8")
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


def read_run(f):
    R = json.loads(open(f, encoding="utf-8").read())
    return R, {u["uid"]: u for u in R["units"]}


def score(gold_file, run_file, base_file, values_file=None):
    import pathlib
    gold = json.loads(open(gold_file, encoding="utf-8").read())
    if "frozen" not in gold.get("version", ""):
        raise SystemExit("the gold is not frozen")
    gv = gold["version"].split()[0]
    G = {u["uid"]: u for u in gold["units"]}
    R, new = read_run(run_file)
    test = R.get("test", "values")
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
    v_assoc = {u["uid"]: u["assoc"] for u in read_run(values_file)[1].values()} if values_file else None

    change = ("the model judges each cell value; code links a column when at least one value uses a legend code "
              "with its meaning" if test == "values" else
              "the column question is whether the column, header and cells together, records what the definitions "
              "describe; values the definitions do not cover do not decide it")
    L = [f"Stage 2 {test} test: {R['model']}, run {R['date']}, gold {gold['version']}, oracle input only "
         f"(the gold's cell-code mappings, as in the base run {pathlib.Path(base_file).name})",
         f"One change against the base: {change}. Units, columns, rendering, oracle input, model and scorer unchanged.",
         f"{len(new)} units called; {sum(len(u['raw'] or []) for u in new.values())} column answers; "
         f"column ids that are not columns: {sum(len(u['bad_ids']) for u in new.values())}", ""]
    for name, a in (("BASE: stage 2 oracle (one yes/no per column)", b_assoc), (f"NEW: {test} stage 2 oracle", n_assoc)):
        S, _D = c2.stage2_eval(G, a, cols)
        L += ["=" * 100, name, "=" * 100] + S + [""]

    # every candidate column, before -> after, by group; the criteria
    trans = collections.defaultdict(collections.Counter)
    detail = collections.defaultdict(list)
    crit = collections.defaultdict(list)
    newly = []
    for k, u in G.items():
        leg = [m["code"] for m in (new[k]["oracle_input"] if k in new else [])]
        for t in u["targets"]:
            col = f"t{t['table']}c{t['col']}"
            vals = cols[(k, t["table"], t["col"])]
            b = outcome(t, vals, b_assoc.get(k, {}).get(col))
            n = outcome(t, vals, n_assoc.get(k, {}).get(col))
            gname = group(t, vals, leg) if leg else "no oracle input (not called)"
            trans[gname][(SHORT[b], SHORT[n])] += 1
            tag = f"{k} -> {col} {t['header'][:50]!r}: {SHORT[b]} -> {SHORT[n]}"
            if (k, col) in BOUNDARY:
                crit["boundary"].append((n == "TN", tag))
            elif b == "missed column":
                crit["C1"].append((n == "right column, right codes", tag))
            elif b == "right column, right codes":
                crit["C2"].append((n == "right column, right codes", tag))
            elif gname == "not target, legend codes among other values":
                crit["C3"].append((n == "TN", tag))
            elif b == "wrong column":
                crit["C5"].append((n == "TN", tag))
            if (gname == "not target, all values legend codes" and b == "TN" and v_assoc is not None
                    and col in v_assoc.get(k, {})):
                crit["C4"].append((n == "TN", tag))
            if k not in new or (b, n) == ("TN", "TN"):
                continue
            if b_assoc.get(k, {}).get(col) is None and n_assoc.get(k, {}).get(col) is not None:
                newly.append(tag)
            lines = [f"  {tag}; gold {sorted(t['decoded_by'])}, base {sorted(b_assoc.get(k, {}).get(col) or []) or '-'}"
                     f", new {sorted(n_assoc.get(k, {}).get(col) or []) or '-'}"
                     + (" [disputed header]" if t.get("disputed_header") else "")]
            judged = new[k]["columns"].get(col, {})
            if test == "values":
                shown = {v["value"] for v in judged.get("values", [])}
                for v in judged.get("values", []):
                    lines.append(f"      {v['value'][:40]!r}: codes {v['codes']} same_meaning {v['same_meaning']} "
                                 f"| {v['reason'][:150]}")
                for v in vals:
                    if v[:cal.VALUE_CHARS] not in shown:
                        lines.append(f"      {v[:40]!r}: (no judgement)")
            else:
                lines.append(f"      records {judged.get('records')} codes {judged.get('written')} | "
                             f"{judged.get('evidence', '')[:220]}" if judged else "      (no answer for this column)")
            lines.append(f"      base: {(base[k]['oracle'] or {}).get(col, {}).get('evidence', '')[:220]}")
            detail[gname].append(lines)
    L += ["=" * 100, "EVERY CANDIDATE COLUMN, base -> new (RR right column + right codes, RW right column + wrong or "
          "incomplete codes, MC missed, WC wrong column, TN)", "=" * 100]
    for gname in sorted(trans):
        L.append(f"  {gname}: " + ", ".join(f"{b}->{n} {c}" for (b, n), c in sorted(trans[gname].items())))
    L.append("")
    names = {"C1": "the columns the base missed: right column + right codes",
             "C2": "the columns the base got right: still right",
             "C3": "non-target columns mixing legend codes with other values: refused",
             "C4": "non-target all-code columns the values test linked and the base refused: refused",
             "C5": "the base's other wrong columns: refused"}
    L += ["=" * 100, "ACCEPTANCE CRITERIA (fixed before the gate run)", "=" * 100]
    ok_all = True
    for c in ("C1", "C2", "C3", "C4", "C5"):
        xs = crit[c]
        if c == "C4" and v_assoc is None:
            L.append(f"  {c} {names[c]}: not checked (no values run given)")
            ok_all = False
            continue
        ok = sum(o for o, _ in xs)
        ok_all &= ok == len(xs)
        L.append(f"  {c} {names[c]}: {ok}/{len(xs)} {'PASS' if ok == len(xs) else 'FAIL'}")
        L += [f"      fails: {tag}" for o, tag in xs if not o]
    L.append(f"  overall: {'PASS' if ok_all else 'FAIL'}")
    L += [f"  apart (upstream input boundary, not evidence for or against): {tag}" for _o, tag in crit["boundary"]]
    L += ["", f"  newly linked columns (no link in the base): {len(newly)}"] + [f"      {t}" for t in newly] + [""]
    cut = len(L)
    L += ["=" * 100, "DETAIL: every called column that is not TN in both runs, with the model's answers", "=" * 100]
    for gname in sorted(detail):
        L += ["", f"--- {gname}"]
        for lines in detail[gname]:
            L += lines
    if test == "values":
        coinc = [(k, c, v) for k, u in new.items() for c, x in u["columns"].items() for v in x["values"]
                 if v["legend_codes"] and not v["same_meaning"]]
        L += ["", "=" * 100, f"VALUES WITH A LEGEND CODE JUDGED NOT TO USE ITS MEANING: {len(coinc)}", "=" * 100]
        L += [f"  {k} {c} {v['value'][:40]!r} codes {v['codes']} | {v['reason'][:150]}" for k, c, v in coinc]
    f = OUT / f"CALIB2{'V' if test == 'values' else 'G'}_REPORT_{R['date']}_gold{gv}.txt"
    f.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:cut]))
    print(f"-> {f}")


if __name__ == "__main__":
    {"run": run, "score": score}[sys.argv[1]](*sys.argv[2:])
