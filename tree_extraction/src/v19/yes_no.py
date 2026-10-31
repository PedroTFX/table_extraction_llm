"""Yes / no columns (v18, v19: followup(); output/eval_split/DESIGN_yes_no_v18.md). The GT writes a column that says
whether each organism has a property as 'Yes' / 'No' (Guariento2020 'Hibernation_Larva' 0 / 1, legend
'0 - no hibernation in larval stage recorded'; Fiedler2021 'obligate_myrmecophile' 'obligate' / 'not';
Gathof2022 'Migratory status' 0 / 1). We wrote the legend's wording or the numbers.

  code      candidates: a trait column of a wide table with exactly two different printed values
            (case and spaces ignored) and at least 3 rows; long tables and an X with blank cells are
            left as they are
  Q-FLAG    the table, the column, its two values with their row counts and the legend's wording
            for each: does the column say whether each organism has the property, or is it a number,
            a score or one of two categories?
  Q-YES     a sure flag: which of the two values means the organism has it? (both orders asked;
            the two answers must agree)
  apply     the column's cells become 'Yes' / 'No' before decoding, so no legend wording replaces them

    python full_run_v18.py v18:flags <papers>     writes <run>/yes_no/<paper>.json
"""
import collections
import copy
import json
import time

import duels
import full_run as fr
import kind_tree as kt
import listed_tags as lt

Q_FLAG = "What does the column '{name}' record for each organism?"
FLAG = {"flag": "whether the organism has this property or not: a yes / no answer",
        "value": "a number, an amount, a score or rank, or one of two named categories that is not a yes / no answer"}
Q_YES = "In the column '{name}', which value means that the organism has the property?"


def _flat(s):
    return " ".join(str(s or "").split())


def candidates(t, fields):
    """[(column, [(value, rows), (value, rows)])] for two-valued trait columns of a wide table."""
    names = [c for c in t.columns if fields.get(c.name) == "measurementType"]
    values = [c for c in t.columns if fields.get(c.name) == "measurementValue"]
    if names and values or len(t.records) < 3:
        return []
    out = []
    for c in t.columns:
        if c.name not in lt.trait_columns(t, fields):
            continue
        cnt = collections.Counter(_flat(r.get(c.name)) for r in t.records if _flat(r.get(c.name)))
        low = {v.lower() for v in cnt}
        if len(cnt) == 2 and len(low) == 2:
            out.append((c, cnt.most_common()))
    return out


def ask_column(ask, t, c, vals, terms):
    st = (f"A table in a scientific paper has the columns {[x.name for x in t.columns][:14]}. Its first rows read: "
          f"{kt._shown(t, 3)}. The column '{c.name}' holds only two values: "
          + "; ".join(f"'{v}' in {n} rows" + (f" (the paper's legend: '{terms[v]}')" if terms.get(v) and terms[v] != v else "")
                      for v, n in vals) + ".")
    ch, probs = ask(st, Q_FLAG.format(name=c.name), dict(FLAG))
    rec = {"values": vals, "terms": terms, "choice": ch, "probs": probs}
    if duels.sure(ch, probs, "flag") != "flag":
        return dict(rec, yes=None)
    (a, _n), (b, _m) = vals
    picks = []
    for x, y in ((a, b), (b, a)):                    # both orders: a lean to the first option cannot decide
        o = {"x": f"'{x}'" + (f" ({terms[x]})" if terms.get(x) and terms[x] != x else ""),
             "y": f"'{y}'" + (f" ({terms[y]})" if terms.get(y) and terms[y] != y else "")}
        ch2, p2 = ask(st, Q_YES.format(name=c.name), o)
        picks.append((x if ch2 == "x" else y) if duels.sure(ch2, p2, "x", "y") else None)
    rec["yes_asked"] = picks
    return dict(rec, yes=picks[0] if picks[0] and picks[0] == picks[1] else None)


def run(run_dir, papers, decode_of, decoded):
    """decode_of(paper) -> the decode decisions; decoded(dec, table, column, cell) -> the term."""
    out = run_dir / "yes_no"
    out.mkdir(parents=True, exist_ok=True)
    head = fr.head_runs()
    ask = duels.Nimble()
    for p in papers:
        f = out / f"{p}.json"
        if f.exists() or p not in head:
            continue
        t0 = time.time()
        dec = decode_of(p)
        res = {}
        for t, fields, _org, _x in fr.plan(p, head):
            for c, vals in candidates(t, fields):
                terms = {v: decoded(dec, t.table_index, c.index, v) for v, _n in vals}
                res[f"{t.table_index}:{c.name}"] = ask_column(ask, t, c, vals, terms)
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        flags = [k for k, v in res.items() if v.get("yes")]
        if res:
            print(f"  [yes/no] {p:22s} {len(flags)} of {len(res)} two-valued columns are yes / no ({time.time() - t0:.0f}s)", flush=True)
    ask.unload()


def apply(dec, out):
    """plan()'s list with each sure yes / no column's cells written 'Yes' / 'No'."""
    if not dec:
        return out
    res = []
    for t, fields, org, x in out:
        cols = {k.split(":", 1)[1]: v["yes"] for k, v in dec.items()
                if not k.startswith("_") and v.get("yes") and k.split(":", 1)[0] == str(t.table_index)}
        if cols:
            t = copy.copy(t)
            t.records = [dict(r) for r in t.records]
            for r in t.records:
                for name, yes in cols.items():
                    v = _flat(r.get(name))
                    if v:
                        r[name] = "Yes" if v == yes else "No"
        res.append((t, fields, org, x))
    return res


# --- v19: unsure columns beside sure siblings (the user, 2026-10-31: "everything on Fiedler is yes or no") ---

Q_SIB = "Is the column '{name}' a yes / no answer of the same kind, with '{yes}' meaning that the organism has it?"
SIB = {"same": "yes: like the other columns, it says whether the organism has this property, '{yes}' meaning it has it",
       "other": "no: it records something else (a number, a score, a category) or '{yes}' does not mean 'has it' here"}


def followup(run_dir, papers):
    """v18's answers plus one question for each column the model leaned to call yes / no but not
    surely, when other columns of its table with the same two values were surely yes / no and agree
    on which value means 'has it' (Fiedler2021: Nearctic 0.56 beside Palaearctic 0.91). The sure
    siblings are named in the question; nimble decides. Resumable ('followup' in the file)."""
    head = fr.head_runs()
    ask = duels.Nimble()
    for p in papers:
        f = run_dir / "yes_no" / f"{p}.json"
        if not f.exists() or p not in head:
            continue
        res = json.loads(f.read_text(encoding="utf-8"))
        if res.get("_followup"):
            continue
        groups = collections.defaultdict(list)
        for k, v in res.items():
            if k.startswith("_"):
                continue
            t = k.split(":", 1)[0]
            groups[(t, tuple(sorted(x.lower() for x, _n in v["values"])))].append(k)
        asked = 0
        tables = {str(t.table_index): t for t, *_ in fr.plan(p, head)}
        for (t, _vals), keys in groups.items():
            sure = [k for k in keys if res[k].get("yes")]
            yeses = {res[k]["yes"].lower() for k in sure}
            if not sure or len(yeses) != 1:
                continue
            yes = res[sure[0]]["yes"]
            for k in keys:
                v = res[k]
                if v.get("yes") or v.get("choice") != "flag" or t not in tables:
                    continue
                name = k.split(":", 1)[1]
                tb = tables[t]
                st = (f"A table in a scientific paper has the columns {[x.name for x in tb.columns][:14]}. Its first rows read: "
                      f"{kt._shown(tb, 3)}. The columns {[s.split(':', 1)[1] for s in sure][:12]} hold the same two values "
                      f"and each says whether the organism has that property, '{yes}' meaning it has it. The column "
                      f"'{name}' holds: " + "; ".join(f"'{x}' in {n} rows" for x, n in v["values"]) + ".")
                ch, probs = ask(st, Q_SIB.format(name=name, yes=yes), {a: b.format(yes=yes) for a, b in SIB.items()})
                v["siblings"] = {"named": [s.split(":", 1)[1] for s in sure], "choice": ch, "probs": probs}
                hit = next((x for x, _n in v["values"] if x.lower() == yes.lower()), None)
                if duels.sure(ch, probs, "same") and hit:
                    v["yes"], v["by"] = hit, "siblings"
                asked += 1
        res["_followup"] = True
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        if asked:
            n = sum(1 for k, v in res.items() if not k.startswith("_") and v.get("by") == "siblings")
            print(f"  [yes/no siblings] {p:22s} {n} of {asked} asked now yes / no", flush=True)
    ask.unload()
