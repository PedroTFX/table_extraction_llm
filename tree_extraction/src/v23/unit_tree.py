"""Units (v23; tree_extraction/plans/01_units.md, 2026-11-10). The template wants the unit of a numeric value in
measurementUnit; we left it empty on all but 513 of 124,332 tuning rows the scorer matched, while the GT gives one on 98k.
Where the paper prints it (output/eval_split/stats/units_gt.json, tuning papers):
  the column's header      'BL (µm)', 'Width (mm)', 'Voltinity (generations/year)'; the meaning step drops the bracket
                           when it spells a code out ('body length'), so the unit is lost before assembly
  a heading above it       'Functional traits (mm)' over several columns (the head reader's group part)
  the legend of its code   'HL  Head length (mm)' in a legend table
  the text with the table  a caption or a footnote: 'all measurements in mm'

  code      candidates for each numeric trait column of a wide table (half its cells or more hold a digit), in that
            order: bracketed text and a short part after the last comma of the printed header; bracketed text in, or
            the whole of, a short heading part; bracketed text in the legend entries for the column's code; unit words
            in the text printed above and below the table. A long table's trait-name cells: bracketed text in the cell
  Q-PART    one question per candidate (header, heading, legend, name cell): what does it tell about the column's
            values: the unit, the statistic, part of what is measured, or something else
  Q-TEXT    one question per column with no unit from its own text, for each unit word of the caption: is it the unit
            of this column's values?
  apply     the first sure unit (p >= 0.8) is the column's unit, written on its numeric values only (a word value has no
            unit); a unit the row already has (a unit column) is kept. A unit bracket left in the trait name is taken out
            of it ('Width (mm)' -> 'Width'). Not sure: nothing changes.

    python full_run_v23.py v23:units <papers>     writes <run>/units/<paper>.json
"""
import json
import re
import time

import decoder_v3 as v3
import duels
import full_run as fr
import kind_tree as kt
import legend_names as ln
import name_parts as nps

BRACKET = re.compile(r"[\(\[]\s*([^()\[\]]{1,24}?)\s*[\)\]]")
COMMA = re.compile(r",\s*([^,]{1,10})\s*$")
COPY = re.compile(r"\s#\d+$")
# unit words looked for in the text around a table only (a header's or a legend's bracket is asked whatever it holds)
UNIT_WORD = (r"(?:[µμu]m|mm|cm|km|nm|m|mg|µg|μg|kg|g|ml|µl|μl|l|mm²|mm2|mm³|mm3|cm²|cm2|m²|°C|ºC|%|s|sec|min|h|hrs?|"
             r"days?|weeks?|months?|years?|millimet(?:re|er)s?|micromet(?:re|er)s?|microns?|centimet(?:re|er)s?|"
             r"milligrams?|grams?|seconds?|minutes?|hours?)")
TEXT_UNIT = re.compile(r"(?:\(\s*|\bin\s+|\bas\s+)(" + UNIT_WORD + r")(?![\w²³])", re.I)
WHERE = {"header": "is printed in the column's header",
         "comma": "is printed after a comma in the column's header",
         "heading": "is printed in the heading '{h}' above the column",
         "legend": "is printed in the paper's legend for '{code}': '{h}'",
         "cell": "is printed in the trait name '{h}' of this row"}
Q_PART = "What does '{part}' tell about the values of the column '{col}'?"
PART = {"unit": "the unit the values are in",
        "statistic": "which statistic the values are (such as mean, standard deviation, range, sample size)",
        "name": "part of what is measured: a structure, a sex, caste or life stage, a condition or a method",
        "other": "something else: a code, an abbreviation's meaning, a note or footnote mark, or nothing about these values"}
Q_TEXT = "Is '{part}' the unit of the values in the column '{col}'?"
TEXT = {"yes": "yes: the values of '{col}' are in {part}",
        "no": "no: '{part}' is the unit of other columns or other numbers in the text, or these values have no unit"}


def _flat(s):
    return " ".join(str(s or "").split())


def numeric(values):
    vals = [v for v in values if v]
    return bool(vals) and sum(bool(re.search(r"\d", v)) for v in vals) >= 0.5 * len(vals)


def header_candidates(name):
    """[(source, text)] from a printed header: each bracket, then a short part after the last comma."""
    h = COPY.sub("", _flat(name))
    out = [("header", m[1]) for m in BRACKET.finditer(h)]
    m = COMMA.search(BRACKET.sub(" ", h))
    if m and not re.search(r"\d", m[1]):
        out.append(("comma", _flat(m[1])))
    return out


def part_candidates(parts):
    """[(source, text, heading)] from the head reader's group / detail parts: brackets in them, or a short part whole."""
    out = []
    for role, x in parts:
        if role == "name":
            continue
        x = _flat(x)
        got = [m[1] for m in BRACKET.finditer(x)] or ([x] if len(x) <= 12 and not re.search(r"\d", x) else [])
        out += [("heading", g, x) for g in got]
    return out


def legend_candidates(code, cats):
    """[(source, text, entry)]: brackets in the legend entries for the column's code."""
    out = []
    for c in nps.definitions(code, cats, {}) if code else []:
        for txt in (c.get("term"), c.get("entry")):
            for m in BRACKET.finditer(_flat(txt)):
                if (m[1], _flat(txt)) not in [(a, b) for _s, a, b in out]:
                    out.append(("legend", m[1], _flat(txt)))
    return out[:4]


def text_units(text):
    """The unit words of the text around a table, each with a window of the sentence it is in."""
    out = {}
    for m in TEXT_UNIT.finditer(text or ""):
        u = m[1]
        if u.lower() not in {k.lower() for k in out}:
            a = max(0, m.start() - 160)
            out[u] = ("…" if a else "") + _flat(text[a:m.end() + 60]) + "…"
    return list(out.items())[:4]


def state_of(t, col, values, extra=""):
    heads = [c.name for c in t.columns][:12]
    return (f"A table in a scientific paper has the columns {heads}. Its first rows read: {kt._shown(t, 3)}. The column "
            f"'{col}' holds values such as {', '.join(repr(v) for v in values[:6])}." + extra)


def ask_part(ask, state, col, part, where):
    ch, probs = ask(state + f" '{part}' {where}.", Q_PART.format(part=part, col=col), dict(PART))
    return {"part": part, "where": where, "choice": ch, "probs": probs, "unit": bool(duels.sure(ch, probs, "unit"))}


def ask_text(ask, state, col, part, window, where):
    st = state + f" The text printed {where} the table reads: '{window}'."
    ch, probs = ask(st, Q_TEXT.format(part=part, col=col),
                    {k: v.format(col=col, part=part) for k, v in TEXT.items()})
    return {"part": part, "where": f"text {where}", "choice": ch, "probs": probs,
            "unit": bool(duels.sure(ch, probs, "yes"))}


def strip_unit(name, unit):
    """The trait name without the bracket that holds the unit ('Width (mm)' -> 'Width'), else unchanged."""
    s = re.sub(r"\s*[\(\[]\s*" + re.escape(unit) + r"\s*[\)\]]", " ", str(name))
    s = re.sub(r",\s*" + re.escape(unit) + r"\s*$", "", s)
    return _flat(s) or name


def column_unit(ask, t, col, values, parts, code, cats, text, seen):
    """-> record: the questions asked, in order, and the first sure unit (or None). seen: the table's answers about a
    heading, asked once for all the columns under it (the text with the table is asked per column: a caption's unit
    may be some columns' only)."""
    st = state_of(t, col.name, values)
    rec = {"asked": [], "unit": None, "source": None}
    cands = [(s, x, WHERE[s]) for s, x in header_candidates(col.name)]
    cands += [(s, x, WHERE[s].format(h=h)) for s, x, h in part_candidates(parts)]
    cands += [(s, x, WHERE[s].format(code=code, h=h)) for s, x, h in legend_candidates(code, cats)]
    for s, x, where in cands:
        k = (t.table_index, x, where)
        if s == "heading" and k in seen:
            r = dict(seen[k], reused=True)
        else:
            r = ask_part(ask, st, col.name, x, where)
            if s == "heading":
                seen[k] = r
        rec["asked"].append(dict(r, source=s))
        if r["unit"]:
            rec.update(unit=x, source=s)
            return rec
    for where, txt in (("above", text[0]), ("below", text[1])):
        for u, window in text_units(txt):
            r = ask_text(ask, st, col.name, u, window, where)
            rec["asked"].append(dict(r, source="text"))
            if r["unit"]:
                rec.update(unit=u, source="text")
                return rec
    return rec


def run(run_dir, papers):
    """One paper at a time; resumable (run_dir/units/<paper>.json). The tables are the ones full_run.plan gives (the
    caller installs its layers). Trait names are updated in run_dir/meaning/<paper>.json when a unit leaves them."""
    out = run_dir / "units"
    out.mkdir(parents=True, exist_ok=True)
    head = fr.head_runs()
    ask = duels.Nimble()
    for p in papers:
        f = out / f"{p}.json"
        if f.exists() or p not in head:
            continue
        t0, n_q = time.time(), 0
        mf = run_dir / "meaning" / f"{p}.json"
        names = json.loads(mf.read_text(encoding="utf-8")) if mf.exists() else {}
        cats = ln.entries(p)
        md = None
        res = {"columns": {}, "cells": {}}
        for t, fields, _o, _x in fr.plan(p, head):
            names_col = [c for c in t.columns if fields.get(c.name) == "measurementType"]
            vals_col = [c for c in t.columns if fields.get(c.name) == "measurementValue"]
            if names_col and vals_col:                    # a long table: brackets in its trait-name cells
                tcol = names_col[0]
                vals = [_flat(r.get(vals_col[0].name)) for r in t.records]
                if not numeric(vals):
                    continue
                for cell in dict.fromkeys(_flat(r.get(tcol.name)) for r in t.records):
                    if not cell or cell in res["cells"]:
                        continue
                    cands = header_candidates(cell)
                    if not cands:
                        continue
                    shown = [_flat(r.get(vals_col[0].name)) for r in t.records if _flat(r.get(tcol.name)) == cell]
                    st = state_of(t, vals_col[0].name, shown)
                    rec = {"asked": [], "unit": None}
                    for s, x in cands:
                        r = ask_part(ask, st, vals_col[0].name, x, WHERE["cell"].format(h=cell))
                        rec["asked"].append(dict(r, source="cell"))
                        if r["unit"]:
                            rec.update(unit=x, name=strip_unit(cell, x))
                            break
                    n_q += sum(not a.get("reused") for a in rec["asked"])
                    res["cells"][cell] = rec
                continue
            parts_of = nps.column_parts(head[p], t)
            seen = {}
            text = None
            for col in t.columns:
                if fields.get(col.name) not in ("measurementType", "measurementValue"):
                    continue
                key = f"{t.table_index}|{col.name}"
                vals = list(dict.fromkeys(_flat(r.get(col.name)) for r in t.records if _flat(r.get(col.name))))
                if key in res["columns"] or not numeric(vals):
                    continue
                if text is None:
                    md = md or v3.md_tables(p)
                    text = nps.around(t, md)
                parts = parts_of.get(col.name) or [("name", col.name)]
                code = nps.show(next((x for r, x in parts if r == "name"), col.name))
                rec = column_unit(ask, t, col, vals, parts, code, cats, text, seen)
                n_q += sum(not a.get("reused") for a in rec["asked"])
                if rec["unit"]:
                    shown = names.get(col.name) or col.name
                    new = strip_unit(shown, rec["unit"])
                    if new != shown:
                        rec["name"] = names[col.name] = new
                res["columns"][key] = rec
        if any(r.get("name") for r in res["columns"].values()):
            mf.write_text(json.dumps(names, indent=1, ensure_ascii=False), encoding="utf-8")
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        got = sum(bool(r["unit"]) for r in [*res["columns"].values(), *res["cells"].values()])
        print(f"  [units] {p:22s} {got} of {len(res['columns']) + len(res['cells'])} columns / name cells have a unit "
              f"({n_q} questions, {time.time() - t0:.0f}s)", flush=True)
    ask.unload()


def apply(dec, out):
    """plan()'s list with t.col_units {column: unit} and t.cell_units {name cell: (unit, name)} from the saved answers."""
    if not dec:
        return out
    for t, _fields, _org, _x in out:
        t.col_units = {k.split("|", 1)[1]: r["unit"] for k, r in (dec.get("columns") or {}).items()
                       if r.get("unit") and k.split("|", 1)[0] == str(t.table_index)}
        t.cell_units = {c: (r["unit"], r.get("name") or c) for c, r in (dec.get("cells") or {}).items() if r.get("unit")}
    return out
