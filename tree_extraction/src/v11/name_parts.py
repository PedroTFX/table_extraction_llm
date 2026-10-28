"""Trait names v11: header parts, one name per code per paper, and the paper's own name for a
legend definition (output/eval_split/DESIGN_names_v11.md). v9 (legend_names.py) looks a column's
whole name up in the legend inventory, and only when the meaning step left it as printed, so
three cases stay codes:
  parts      Oliveira2022 'Traits AL M': the head reader splits group 'Traits', code 'AL',
             detail 'M'; the meaning step joins them ('Traits AL mean') and v9 skips the column
  elsewhere  Kovacs2008: the meaning step named table 1's column 'AL' ('antennal length');
             table 2 prints the same code as a long-table cell ('AL', 'GL*') and keeps it
  printed    the legend defines 'AL' ('ratio of antenna (...) length to mesosoma length'); the
             paper's own tables print its name ('Antenna length ratio'), the one the GT uses

Code gathers the candidates and orders them; nimble decides, two options at a time (duels.py);
anything not sure leaves the name as v9 has it.

  items      trait columns of wide tables and name cells of long tables whose current name
             (meaning / v9) still holds its code as a word, brackets and footnote marks dropped;
             not a name v9 asked about and nimble surely called 'none' (a category, a heading)
  code       a cell: its text without footnote marks; a column: the head reader's name part,
             else the one group / detail part with candidates
  Q-DEF      the legend's entries for the code (v9's candidates) and the names the meaning
             step / v9 gave the same code elsewhere in the paper: duels, then the one left
             against 'none'
  Q-PRINTED  the trait names the paper's other tables print that share a word with the
             definition (most shared words first, at most POOL): duels, then the one left
             against keeping the definition
  Q-PART     a column's other parts, once per table and part: a statistic, a unit, a heading,
             or something else; Q-STAT names the statistic (measurementStatistic.md's words).
             Something else, or not sure: the column keeps its v9 name.
  Q-DEF and Q-PRINTED are asked once per code per paper: a code that comes back gets the same
  name.

    python full_run_v11.py v11:names <papers>   writes <run>/name_parts/<paper>.json and
                                                updates <run>/meaning/<paper>.json
"""
import json
import re

import duels
import full_run as fr
import head_to_table as h2t
import legend_names as ln

POOL = 8
MARKS = r"[*†‡§¶]+"
STOP = {"the", "and", "for", "from", "with", "per"}
STATS = [("mean", "'mean': the average"), ("median", "'median'"), ("mode", "'mode': the most common state"),
         ("min", "'min': the smallest value"), ("max", "'max': the largest value"),
         ("range", "'range': from low to high"), ("SD", "'SD': the standard deviation"),
         ("SE", "'SE': the standard error"), ("mean ± SD", "'mean ± SD'"), ("mean ± SE", "'mean ± SE'"),
         ("variance", "'variance'"), ("confidence interval", "'confidence interval'"),
         ("ratio", "'ratio'"), ("count", "'count': a number of individuals or events"),
         ("1st quartile", "'1st quartile'"), ("3rd quartile", "'3rd quartile'")]
WHERE_PART = {"group": "printed above it", "detail": "printed with it",
              "name": "printed under it"}


def _flat(s):
    return " ".join(str(s or "").split())


def show(s):
    """A printed name without bracketed units and footnote marks: 'GL* (mm)' -> 'GL'."""
    return _flat(re.sub(MARKS, "", re.sub(r"[\(\[][^)\]]*[\)\]]", " ", str(s or ""))))


def key(s):
    return show(s).lower()


def holds(name, code):
    """The name still holds the code as a word ('Traits AL mean' holds 'AL'; 'antennal length'
    and 'Head width (HW)' do not)."""
    k = key(code)
    return bool(k) and re.search(rf"(?<![a-z0-9]){re.escape(k)}(?![a-z0-9])", key(name)) is not None


def words(s):
    return {w for w in re.findall(r"[a-z]+", key(s)) if len(w) >= 3 and w not in STOP}


def known_names(names, cells):
    """{code key: [full names]}: what the meaning step / v9 gave a printed name elsewhere in the
    paper (column names, long-table cells), when the full name no longer holds it."""
    out = {}
    for printed, full in [*names.items(), *cells.items()]:
        k = key(printed)
        if k and full and not holds(full, printed) and full not in out.setdefault(k, []):
            out[k].append(full)
    return out


def definitions(code, cats, known):
    """[{"term", "entry"}]: the legend's entries for the code (v9's candidates), then the names
    the paper gives the same code elsewhere."""
    out = ln.candidates(show(code), cats)
    have = {ln._base(c["term"]) for c in out}
    for full in known.get(key(code), []):
        if ln._base(full) not in have:
            have.add(ln._base(full))
            out.append({"term": full, "entry": f"the name the paper gives '{show(code)}' in another place"})
    return out


def _long(t, fields):
    """The name column of a long table (a column of trait names beside value columns), else None."""
    types = [c for c in t.columns if fields.get(c.name) == "measurementType"]
    vals = [c for c in t.columns if fields.get(c.name) == "measurementValue"]
    return types[0] if types and vals else None


def printed_names(plan, names, cells):
    """[(table index, name)] in reading order: the trait names the paper's tables print (wide
    trait columns, long-table name cells) as the meaning step / v9 left them, that read as
    words (five letters, three lower-case in a row)."""
    out = []
    for t, fields, _o, _x in plan:
        tcol = _long(t, fields)
        if tcol:
            got = [cells.get(v) or v for v in dict.fromkeys(_flat(r.get(tcol.name)) for r in t.records) if v]
        else:
            got = [names.get(c.name) or c.name for c in t.columns if fields.get(c.name) == "measurementType"]
        for n in got:
            s = show(n)
            if sum(ch.isalpha() for ch in s) >= 5 and re.search(r"[a-z]{3}", s):
                out.append((t.table_index, s))
    return out


def pool(printed, definition, table_index):
    """The printed names of the paper's other tables that share a word with the definition (the
    item's own table prints other traits): most shared words first, then reading order; at most
    POOL, never the definition itself."""
    dw, out = words(definition), []
    for k, n in printed:
        if k != table_index and dw & words(n) and key(n) != key(definition) \
                and key(n) not in {key(x) for x in out}:
            out.append(n)
    return sorted(out, key=lambda n: -len(dw & words(n)))[:POOL]


def column_parts(entries, t):
    """{column name: [(role, text)]}, name part first, for the columns the head reader split (a
    group above or a detail with the name); only where the column is still the head reader's
    (a rotated table has other columns)."""
    e = next((x for x in entries if x["table"] == t.table_index), None)
    by_col = {c["col"]: c for c in (e["full"]["columns"] if e else [])}
    out = {}
    for col in t.columns:
        c = by_col.get(col.index)
        if not c or not c.get("name") or not (c.get("groups") or c.get("details")):
            continue
        if h2t._header(c) != re.sub(r" #\d+$", "", col.name):
            continue
        out[col.name] = ([("name", c["name"])] + [("group", g) for g in c.get("groups") or []]
                         + [("detail", d) for d in c.get("details") or []])
    return out


def code_of(parts, cats, known):
    """(index of the code part, its candidates): the name part when it has candidates, else the
    one group / detail part that has them; (None, []) otherwise."""
    found = [(i, c) for i, c in ((i, definitions(x, cats, known)) for i, (_r, x) in enumerate(parts)) if c]
    if found and (found[0][0] == 0 or len(found) == 1):
        return found[0]
    return None, []


def ask_definition(ask, where, code, cands):
    """Q-DEF: duels among the candidates, then the one left against 'none'."""
    state = (f"A table in a scientific paper has {where}. The options quote what the paper gives "
             f"for '{code}': its legends, and the name it gives '{code}' in other places.")
    q = f"What is the full name of '{code}' in this paper?"
    held, log = duels.duel(ask, state, q, [(c["term"], f"'{c['term']}' — {c['entry']}") for c in cands])
    rec = {"candidates": cands, "duels": log, "term": None}
    if held is None:
        return rec
    c = cands[held]
    ch, probs = ask(state, q, {
        "yes": f"'{c['term']}' — {c['entry']}",
        "none": (f"none: '{c['term']}' is not the full name of '{code}': a heading shared by several "
                 f"columns (a group of traits, or the trait whose categories the columns are), or an "
                 f"unrelated entry")})
    rec["final"] = {"choice": ch, "probs": probs}
    if duels.sure(ch, probs, "yes"):
        rec["term"] = c["term"]
    return rec


def ask_printed(ask, code, definition, names):
    """Q-PRINTED: duels among the printed names, then the one left against the definition."""
    state = (f"In a scientific paper, '{code}' stands for '{definition}'. The paper's tables also "
             f"print trait names; the options quote two of them.")
    held, log = duels.duel(ask, state, f"Which of these two is the paper's own name for '{definition}' ('{code}')?",
                           [(n, f"'{n}'") for n in names])
    rec = {"pool": names, "duels": log, "name": None}
    if held is None:
        return rec
    w = names[held]
    state = (f"In a scientific paper, '{code}' stands for '{definition}'. The paper's tables also "
             f"print the trait name '{w}'.")
    ch, probs = ask(state, f"Does the paper call '{definition}' ('{code}') '{w}'?", {
        "yes": f"yes: '{w}' is the paper's name for the same trait",
        "no": f"no: '{w}' is a different trait, or a broader or narrower one; the name stays '{definition}'"})
    rec["final"] = {"choice": ch, "probs": probs}
    if duels.sure(ch, probs, "yes"):
        rec["name"] = w
    return rec


def ask_part(ask, col, ctx, code, name, role, part):
    """Q-PART (and Q-STAT): what one more part of a column's name says. -> the record, its
    "answer" ("statistic" | "unit" | "heading", text) or None."""
    state = (f"A table in a scientific paper has the columns {ctx}. In the column '{col}', '{code}' "
             f"stands for the trait '{name}', and '{part}' is {WHERE_PART[role]}.")
    ch, probs = ask(state, f"What does '{part}' tell about the values of the column '{col}'?", {
        "statistic": (f"a statistic: '{part}' says which statistic of the trait the values are (such "
                      f"as mean, variance, standard deviation)"),
        "unit": f"a unit: '{part}' is the unit the values are in",
        "heading": (f"a heading: '{part}' is printed over several trait columns and adds nothing to "
                    f"each trait's name"),
        "other": (f"something else: '{part}' tells the sex, caste or life stage measured, a body part, "
                  f"a place or time, or is part of the trait's name")})
    rec = {"role": role, "part": part, "choice": ch, "probs": probs, "answer": None}
    if duels.sure(ch, probs, "statistic"):
        ch2, p2 = ask(state, f"Which statistic is '{part}' in the column '{col}'?",
                      {f"s{i}": d for i, (_w, d) in enumerate(STATS)})
        rec["statistic"] = {"choice": ch2, "probs": p2}
        k = re.fullmatch(r"s(\d+)", str(ch2 or ""))
        if k and p2.get(ch2, 0) >= duels.SURE:
            rec["answer"] = ["statistic", STATS[int(k.group(1))][0]]
    elif duels.sure(ch, probs, "unit", "heading"):
        rec["answer"] = [ch, part]
    return rec


def name_of(ask, res, printed, code, cands, where, table_index):
    """The full name of a code, once per paper (res["codes"]): Q-DEF, then Q-PRINTED when the
    paper's other tables print names that share a word with the definition. None: not sure."""
    k = key(code)
    if k not in res["codes"]:
        d = ask_definition(ask, where, show(code), cands)
        r = {"code": show(code), "definition": d, "name": d["term"]}
        names = pool(printed, d["term"], table_index) if d["term"] else []
        if names:
            r["printed"] = ask_printed(ask, show(code), d["term"], names)
            r["name"] = r["printed"]["name"] or d["term"]
        res["codes"][k] = r
    return res["codes"][k]["name"]


def run(run_dir, papers):
    """One paper at a time; resumable (run_dir/name_parts/<paper>.json). The tables are the
    ones full_run.plan gives (the caller installs its layers)."""
    out = run_dir / "name_parts"
    out.mkdir(parents=True, exist_ok=True)
    head = fr.head_runs()
    ask = duels.Nimble()
    for p in papers:
        f = out / f"{p}.json"
        if f.exists() or p not in head:
            continue
        mf = run_dir / "meaning" / f"{p}.json"
        names = json.loads(mf.read_text(encoding="utf-8")) if mf.exists() else {}
        cells = ln.cell_names(run_dir, p)
        lf = run_dir / "legend_names" / f"{p}.json"
        v9 = json.loads(lf.read_text(encoding="utf-8")) if lf.exists() else {}
        said_none = {k for k, r in v9.items() if duels.sure(r.get("choice"), r.get("probs") or {}, "none")}
        cats = ln.entries(p)
        plan = fr.plan(p, head)
        known, printed = known_names(names, cells), printed_names(plan, names, cells)
        res = {"codes": {}, "parts": {}, "columns": {}, "cells": {}}
        for t, fields, _o, _x in plan:
            tcol = _long(t, fields)
            if tcol:                            # a long table: its name cells
                for v in dict.fromkeys(_flat(r.get(tcol.name)) for r in t.records):
                    if not v or v in res["cells"] or f"cell:{v}" in said_none or not holds(cells.get(v) or v, v):
                        continue
                    cands = definitions(v, cats, known)
                    if cands:
                        where = f"a long table whose column '{tcol.name}' holds trait names, one of them '{v}'"
                        res["cells"][v] = name_of(ask, res, printed, v, cands, where, t.table_index)
                continue
            parts_of = column_parts(head[p], t)
            heads = [c.name for c in t.columns]
            for col in t.columns:
                ck = f"{t.table_index}|{col.name}"
                if fields.get(col.name) != "measurementType" or ck in res["columns"] or col.name in said_none:
                    continue
                parts = parts_of.get(col.name) or [("name", col.name)]
                i, cands = code_of(parts, cats, known)
                if i is None or not holds(names.get(col.name) or col.name, parts[i][1]):
                    continue                    # nothing to offer, or already spelled out
                code = parts[i][1]
                ctx = ", ".join(f"'{h}'" for h in heads[:10] if h != col.name)
                where = f"a trait column '{col.name}'" + (f" (its other columns: {ctx})" if ctx else "")
                name = name_of(ask, res, printed, code, cands, where, t.table_index)
                rec = {"code": show(code), "name": name, "parts": []}
                ok = bool(name)
                for j, (role, x) in enumerate(parts):
                    if j == i or not ok:
                        continue
                    pk = f"{t.table_index}|{role}|{x}"
                    if pk not in res["parts"]:
                        res["parts"][pk] = ask_part(ask, col.name, ctx, show(code), name, role, x)
                    rec["parts"].append(pk)
                    a = res["parts"][pk]["answer"]
                    if not a:
                        ok = False              # something else, or not sure: keep v9's name
                    elif a[0] in ("statistic", "unit"):
                        rec[a[0]] = a[1]
                rec["applied"] = ok
                res["columns"][ck] = rec
                if ok:
                    names[col.name] = name
        if any(r["applied"] for r in res["columns"].values()):
            mf.write_text(json.dumps(names, indent=1, ensure_ascii=False), encoding="utf-8")
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        if res["codes"]:
            got = [f"{k.split('|', 1)[1]} -> {r['name']}" + (f" ({r['statistic']})" if r.get("statistic") else "")
                   for k, r in res["columns"].items() if r["applied"]]
            got += [f"{v} -> {n}" for v, n in res["cells"].items() if n]
            print(f"  [names v11] {p:22s} {len(res['codes'])} code(s) asked; "
                  + ("; ".join(got)[:300] or "nothing changed"), flush=True)
    ask.unload()


def cell_names(run_dir, paper):
    """{printed name cell: full name} of one paper's long tables (sure answers)."""
    f = run_dir / "name_parts" / f"{paper}.json"
    res = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    return {v: n for v, n in (res.get("cells") or {}).items() if n}


def extra_tags(res):
    """{(table index, column name): {"measurementStatistic" / "measurementUnit": text}} from one
    paper's saved answers, for the columns whose name was applied."""
    out = {}
    for ck, r in (res.get("columns") or {}).items():
        x = {field: r[k] for field, k in (("measurementStatistic", "statistic"), ("measurementUnit", "unit"))
             if r.get("applied") and r.get(k)}
        if x:
            ti, name = ck.split("|", 1)
            out[(int(ti), name)] = x
    return out
