"""The subject step (v13, output/eval_split/DESIGN_one_species_v13.md). Papers about one species
print tables whose rows are individuals, groups under one condition, statistics or traits, not
species (Luo2023 t4, Brant2021 t8, Tran2022 t1, Grasser2000 t1, Zhang2025 t2, TOMBERLIN2002 t1):
the species, kind and structure questions, written for tables of many species, lose them at
different steps. nimble decides, two options at a time where there are more (duels.py); code
picks the questions and applies the sure answers.

  subject   the paper's one organism: the species step's own answer when it gave one (gate 'one'
            with one name, or every table it named got the same name); else Q-SUBJECT duels over
            the names (gate 'one'; or 'several' / 'undecided' with at most MAX_NAMES names), the
            one left against 'several species'
  Q-OWN     per table the species step looked at that it did not name: are its values
            measurements of the subject? A sure 'none' / 'several' from the species step meets a
            sure yes in one duel
  clash     a table the kind step dropped (sure): the kind's own option against Q-OWN's yes
  Q-ROWS    individual / group / statistic / trait / definition (duels); a definitions table
            gives no rows
  clash     a table the structure step dropped (sure): its row option against the Q-ROWS answer
  Q-COLUMN  (group / statistic / trait rows) per column: value / group / statistic / name / test /
            label
  endings   v3's mark-or-value question for trait columns whose cells end in letters stuck to the
            value ('0.59a': significance letters of treatment comparisons)

The tables are read with the tags the species step saw (no kind, no structure). Only sure answers
count; anything else leaves the table as v12 reads it.

    python full_run_v13.py v13:subject <papers>     writes <run>/one_species/<paper>.json
"""
import json
import re

import decoder_v3 as v3
import duels
import full_run as fr
import kind_tree as kt
import species_tree as sp
import structure_tree as st

MAX_NAMES = 3            # a gate-'several' paper is asked only with this many names or fewer
MAX_COLS = 14
TRAITS = {"measurementType", "measurementValue"}
CONTEXT = {"sex", "lifeStage", "caste"}

SUBJECT_Q = "Which organism did this study take its measurements on?"
SUBJECT = "'{0}': the study measures {0}; any other organism named is its food, prey, host, plant or partner"
SEVERAL = "several species: the study measures more than one species"

OWN_Q = "Are the values in this table measurements of {}?"
OWN_IS = ("measurements of {}: values measured on its individuals, specimens, colonies or castes, on "
          "groups of it under different treatments, diets, prey, temperatures, ages or times, or summary "
          "statistics of them")
OWN_YES = "yes: " + OWN_IS
OWN_NO = ("no: definitions, methods, sites, counts per site, results of statistical tests, or "
          "measurements of another organism")

ROWS_Q = "What does each row of this table stand for?"
ROWS = [("individual", "one individual, specimen, colony, nest or sample of {}, with the values measured on it"),
        ("group", "one group of {} under one condition: a treatment, diet, prey, temperature, age, sex, caste, "
                  "line, population, site or time, with the values measured on that group"),
        ("statistic", "one summary statistic of the measurements: minimum, maximum, mean, median, SD or range"),
        ("trait", "one trait or measured variable, named in the row, with its values in the other columns"),
        ("definition", "one trait or variable with its definition, method or description, and no measured value")]

COL_Q = "What does the column '{}' give for each row?"
COLS = [("value", "a value measured on {} (its header may name the group or condition it was measured "
                  "under): a measurement, count, proportion or category, or a mean with its SD or SE"),
        ("group", "which group of {} the row is about: its treatment, diet, prey, temperature, age, sex, "
                  "caste, line, population, site or time"),
        ("statistic", "which statistic the row gives: minimum, maximum, mean, median, SD or range"),
        ("name", "the name of the trait or measured variable the row is about"),
        ("test", "a result of a statistical test, model or comparison: F, MS, p, a correlation, or a "
                 "difference between groups"),
        ("label", "an identifier of the row or specimen, a sample size, a definition or a note")]


def _flat(s):
    return " ".join(str(s or "").split())


def _paper_state(reads, names):
    s = "A scientific paper."
    for kind, rd in reads:
        if rd.get("summary"):
            s += f" Its {kind}, summarised: '{rd['summary']}'"
    return s + " Organism names printed there: " + ", ".join(f"'{n}'" for n in names) + "."


def _table_state(t, subject, above="", below=""):
    s = (f"A scientific paper studies '{subject}'. One of its tables has the columns "
         f"{[c.name for c in t.columns][:MAX_COLS]}.")
    if above:
        s += f" The text printed directly above it: '{above}'."
    if below:
        s += f" The text printed directly below it: '{below}'."
    return s + f" Its first rows read: {kt._shown(t, 4)}."


def subject_of(ask, state_sp):
    """-> (the subject or None, record)."""
    gate = state_sp.get("paper") or {}
    reads = [(k, state_sp["reads"][k]) for k in sp.ROUNDS if k in (state_sp.get("reads") or {})]
    names = gate.get("names") or sp._names(reads)
    named = sorted({x["species"] for x in state_sp["tables"].values() if x.get("species")})
    a = gate.get("answer")
    if a == "one" and len(names) == 1:
        return names[0], {"how": "gate one, one name"}
    if a == "one" and len(named) == 1:
        return named[0], {"how": "gate one, its tables named one"}
    if not names or a not in ("one", "several", "undecided") or (a != "one" and len(names) > MAX_NAMES):
        return None, {"how": "not asked", "gate": a, "names": len(names)}
    state = _paper_state(reads, names)
    options = [(n, SUBJECT.format(n)) for n in names]
    held, log = duels.duel(ask, state, SUBJECT_Q, options)
    rec = {"how": "duels", "gate": a, "options": names, "duels": log}
    if held is None:
        return None, rec
    ch, probs = ask(state, SUBJECT_Q, {"pick": options[held][1], "several": SEVERAL})
    rec["final"] = {"choice": ch, "probs": probs}
    return (names[held] if duels.sure(ch, probs, "pick") else None), rec


def _distinct(t, col, k=8):
    out = []
    for r in t.records:
        v = _flat(r.get(col.name))
        if v and v not in out:
            out.append(v)
    return out[:k]


def decide_table(ask, t, fields, subject, sp_rec, kind_dec, struct_dec, above, below):
    """One table of a paper with a subject -> its record; rec["use"] when the answers apply."""
    rec = {"use": False}
    lifts = False                                       # a dropped table this step would bring back
    state = _table_state(t, subject, above, below)
    yes, own_is = OWN_YES.format(subject), OWN_IS.format(subject)
    if sp_rec.get("species"):
        if sp_rec["species"] != subject:
            rec["own"] = {"by": "species step", "name": sp_rec["species"]}
            return rec
        rec["own"] = {"by": "species step"}
    else:
        ch, probs = ask(state, OWN_Q.format(subject), {"yes": yes, "no": OWN_NO})
        rec["own"] = {"by": "Q-OWN", "choice": ch, "probs": probs}
        if not duels.sure(ch, probs, "yes"):
            return rec
        before = sp_rec.get("answer")                   # the species step's own sure 'none' / 'several'
        if before in ("none", "several"):
            text = sp.NONE if before == "none" else sp.SEVERAL
            ch, probs = ask(state, sp.QUESTION, {"step": text, "own": own_is})
            rec["species_clash"] = {"step": before, "choice": ch, "probs": probs}
            if not duels.sure(ch, probs, "own"):
                return rec
    if kind_dec and kind_dec.get("action") == "no rows":
        c = (kind_dec.get("kind") or {}).get("choice")
        if c not in kt.KIND_OPTIONS:                    # the person's review ('review'): stays
            rec["kind_clash"] = {"kind": c, "choice": None}
            return rec
        ch, probs = ask(state, "What does this table hold?", {"kind": kt.KIND_OPTIONS[c], "own": own_is})
        rec["kind_clash"] = {"kind": c, "choice": ch, "probs": probs}
        if not duels.sure(ch, probs, "own"):
            return rec
        lifts = True
    if struct_dec and struct_dec.get("action") in ("long", "wide"):
        rec["use"], rec["rows"] = True, {"choice": None, "kept": struct_dec["action"]}
        return rec                                      # the structure step's sure reading stays
    rows = [(k, v.format(subject)) for k, v in ROWS]
    held, log = duels.duel(ask, state, ROWS_Q, rows)
    rec["rows"] = {"choice": rows[held][0] if held is not None else None, "duels": log}
    new = rec["own"]["by"] == "Q-OWN"                   # the table gets its species from this step
    if rec["rows"]["choice"] == "definition":           # nothing measured: no rows
        rec["use"] = not (lifts or new)
        return rec
    if struct_dec and struct_dec.get("action") == "no rows":
        c = (struct_dec.get("row") or {}).get("choice")
        if held is None or c not in st.ROW_OPTIONS:
            rec["structure_clash"] = {"structure": c, "choice": None}
            return rec
        ch, probs = ask(state, "What is each row of this table?",
                        {"structure": st.ROW_OPTIONS[c], "rows": rows[held][1]})
        rec["structure_clash"] = {"structure": c, "choice": ch, "probs": probs}
        if not duels.sure(ch, probs, "rows"):
            return rec
        lifts = True
    if (lifts or new) and held is None:
        return rec                                      # brought back only with a sure reading
    rec["use"] = True
    if rec["rows"]["choice"] in ("group", "statistic", "trait"):
        cols = [(k, v.format(subject)) for k, v in COLS]
        rec["cols"] = {}
        for col in t.columns[:MAX_COLS]:
            if fields.get(col.name) == "verbatimIdentification":
                continue
            vals = ", ".join(f"'{v}'" for v in _distinct(t, col))
            held, log = duels.duel(ask, state + f" The column '{col.name}' holds: {vals}.",
                                   COL_Q.format(col.name), cols)
            rec["cols"][col.name] = {"choice": cols[held][0] if held is not None else None, "duels": log}
        if (lifts or new) and rec["rows"]["choice"] == "trait" and not readable(rec):
            rec["use"] = False                          # no sure names and values column: stays as it was
    return rec


def readable(rec):
    """A trait-per-row table reads long only with a sure names column and a sure values column."""
    got = {a.get("choice") for a in (rec.get("cols") or {}).values()}
    return "name" in got and "value" in got


ATTACHED = re.compile(r"^(.*?\d[^a-zA-Z]*?)\s*([a-zA-Z]{1,3}(?:,\s?[a-zA-Z]{1,3})*)$")


def attached(values):
    """{cell: (value, ending)} for cells ending in letters stuck to the value ('0.59a',
    '0.157 ± 0.077A'), which decoder_v3's shapes (a space before lower-case letters) miss."""
    out = {}
    for v in values:
        if any(rx.match(v) for _n, rx in v3.ENDINGS):
            continue
        m = ATTACHED.match(v)
        if m and m.group(1).strip():
            out[v] = (m.group(1).strip(), m.group(2))
    return out


def ask_endings(ask, run_dir, p, plan, res):
    """v3's ending question (mark or part of the value) for the trait columns of the tables of
    the subject whose cells end in attached letters; a sure 'mark' goes to the column's decode
    record as v3:endings writes it, so assemble drops the mark."""
    f = run_dir / "decode" / f"{p}.json"
    dec = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    n = 0
    for k, d in res["tables"].items():
        if not d.get("use") or k not in plan:
            continue
        t, fields = plan[k]
        tags, _x = apply(d, fields)
        for col in t.columns:
            if tags.get(col.name) not in TRAITS:
                continue
            vals = list(dict.fromkeys(_flat(r.get(col.name)) for r in t.records if _flat(r.get(col.name))))
            cells = attached(vals)
            if len(cells) < 2:
                continue                                # one cell is not a column's habit
            ch, probs = v3.ask_ending(ask.get(), col.name, vals, "letters", cells, p)
            sure = duels.sure(ch, probs, "mark", "value")
            dec.setdefault(f"{k}:{col.index}", {"cells": {}}).setdefault("endings", {})["letters, attached"] = {
                "choice": sure, "probs": probs, "cells": {v: val for v, (val, _e) in cells.items()}, "by": "v13"}
            d.setdefault("endings", {})[col.name] = {"choice": ch, "probs": probs, "cells": len(cells)}
            n += 1
    if n:
        f.write_text(json.dumps(dec, indent=1, ensure_ascii=False), encoding="utf-8")
    return n


def run(run_dir, papers):
    """One paper at a time; resumable (run_dir/one_species/<paper>.json). fr.plan must give the
    tags the species step saw (install(run, decisions=True))."""
    out = run_dir / "one_species"
    out.mkdir(parents=True, exist_ok=True)
    head = fr.head_runs()
    ask = duels.Nimble()
    for p in papers:
        f, sf = out / f"{p}.json", run_dir / "species" / f"{p}.json"
        if f.exists() or p not in head or not sf.exists():
            continue
        state_sp = json.loads(sf.read_text(encoding="utf-8"))
        subject, srec = subject_of(ask, state_sp)
        res = {"subject": dict(srec, name=subject), "tables": {}}
        if subject:
            kinds = json.loads((run_dir / "kind" / f"{p}.json").read_text(encoding="utf-8")) \
                if (run_dir / "kind" / f"{p}.json").exists() else {}
            structs = json.loads((run_dir / "structure" / f"{p}.json").read_text(encoding="utf-8")) \
                if (run_dir / "structure" / f"{p}.json").exists() else {}
            flat, spans = v3.md_tables(p)
            plan = {str(t.table_index): (t, fields) for t, fields, _o, _x in fr.plan(p, head)}
            for k, sp_rec in state_sp["tables"].items():
                if k not in plan or not plan[k][0].records:
                    continue
                t, fields = plan[k]
                res["tables"][k] = decide_table(ask, t, fields, subject, sp_rec, kinds.get(k), structs.get(k),
                                                sp.caption_above(t, flat, spans), kt.caption_below(t, flat, spans))
            res["endings"] = ask_endings(ask, run_dir, p, plan, res)
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        used = [f"t{k}:{d['rows']['choice'] or '?'}" for k, d in res["tables"].items() if d.get("use")]
        print(f"  [subject] {p:22s} {subject or '-'} ({srec['how']}) | {len(res['tables'])} tables asked; "
              f"used: {', '.join(used) or 'none'}", flush=True)
    ask.unload()


# --- applying the answers (the v13 layer of plan()) -------------------------------------------

def lifted(dec):
    """{table index: {'kind', 'structure'}}: the dropped decisions a table of the subject lifts."""
    out = {}
    for k, d in ((dec or {}).get("tables") or {}).items():
        if d.get("use"):
            out[int(k)] = {s for s in ("kind", "structure") if (d.get(f"{s}_clash") or {}).get("choice")}
    return out


def table(dec, k):
    d = ((dec or {}).get("tables") or {}).get(str(k))
    return d if d and d.get("use") else None


def subject_tables(dec):
    """{table index: the subject} for the tables of the subject."""
    name = ((dec or {}).get("subject") or {}).get("name")
    return {int(k): name for k, d in ((dec or {}).get("tables") or {}).items() if d.get("use") and name}


def apply(d, fields):
    """A table of the subject: its tags with the Q-ROWS / Q-COLUMN answers applied -> (tags,
    extra tags {column: {field: value}})."""
    rows = (d.get("rows") or {}).get("choice")
    cols = {c: a.get("choice") for c, a in (d.get("cols") or {}).items() if a.get("choice")}
    out, extra = dict(fields), {}
    if rows is None:
        return out, extra
    if rows == "definition":
        return {c: ("none" if v in TRAITS else v) for c, v in out.items()}, extra
    if rows == "trait":
        names = [c for c, a in cols.items() if a == "name"]
        values = [c for c, a in cols.items() if a == "value"]
        if not (names and values):
            return out, extra
        out = {c: ("none" if v in TRAITS else v) for c, v in out.items()}
        out[names[0]] = "measurementType"
        for c in values:
            out[c] = "measurementValue"
            if len(values) > 1:
                extra[c] = {"sampleTreatment": c}
        return out, extra
    out = {c: ("measurementType" if v == "measurementValue" else v) for c, v in out.items()}   # wide
    for c, a in cols.items():
        tag = out.get(c)
        if a == "value":
            out[c] = "measurementType"
        elif a == "group" and tag not in CONTEXT:
            out[c] = "sampleTreatment"
        elif a == "statistic":
            out[c] = "measurementStatistic"
        elif a in ("label", "test") and tag in TRAITS:
            out[c] = "none"
    return out, extra
