"""Marked columns read as categories (v20; output/eval_split/DESIGN_mark_columns_v20.md). A table that
marks an organism with an X under each category it belongs to and leaves the rest blank (Odanaka2019
t7: 'Un-grazed landscapes', 'Low / Moderate / High management intensity'). The GT writes one trait for
the group and the marked column's name as the value (Management intensity = Un-grazed landscapes);
we wrote each column as its own trait with the value 'x'.

  code     groups: in a wide table, two or more trait columns holding the same single mark and blank
           cells elsewhere (at least 3 rows)
  gemma    a short name for the property the columns could be categories of, from the caption, the
           text below the table and the column names (it names; it does not decide)
  Q-CAT    nimble: are the columns categories of one property of each organism (a mark puts the
           organism in that category), or separate things (places, samples, plots, separate traits)?
  Q-NAME   nimble, after a sure 'categories': does gemma's name fit that property?
  apply    (assembly) a row of a group's column whose value is the mark becomes trait = the name,
           value = the column's name; blank cells give no row, as before

    python full_run_v20.py v20:marks <papers>     writes <run>/marks/<paper>.json
"""
import collections
import json
import time

import decoder as v1
import decoder_v3 as v3
import duels
import full_run as fr
import kind_tree as kt
import listed_tags as lt
import species_tree as sp

NAME_SCHEMA = {"type": "object", "required": ["name"], "properties": {"name": {"type": "string"}}}
NAME_PROMPT = """A table in a scientific paper about insects marks each species with '{mark}' under some of these columns and leaves the others blank: {cols}.
The text printed above the table: '{above}'
The text printed below the table: '{below}'

If these columns are categories of one property of each species, give that property's name in a few words, as the paper would call it (for example 'Management intensity' for columns 'Low management intensity', 'High management intensity'). Answer with the name only."""
Q_CAT = "What are the columns {cols} of this table?"
CAT = {"categories": "categories of one property of each organism: a mark puts the organism in that category",
       "separate": "separate things: places, sites, plots or samples where the organism was found, or separate traits"}
Q_NAME = "Is '{name}' a fitting name for the property these columns are categories of?"
NAME = {"yes": "yes, '{name}' names that property", "no": "no, it does not name that property"}


def _flat(s):
    return " ".join(str(s or "").split())


def groups(t, fields):
    """{mark: [column]} for marks shared by two or more trait columns of a wide table."""
    names = [c for c in t.columns if fields.get(c.name) == "measurementType"]
    values = [c for c in t.columns if fields.get(c.name) == "measurementValue"]
    if names and values or len(t.records) < 3:
        return {}
    by = collections.defaultdict(list)
    for c in t.columns:
        if c.name not in lt.trait_columns(t, fields):
            continue
        vals = [_flat(r.get(c.name)) for r in t.records]
        marks = {v for v in vals if v}
        if len(marks) == 1 and "" in vals:
            by[next(iter(marks)).lower()].append(c)
    return {m: cs for m, cs in by.items() if len(cs) >= 2}


def run(run_dir, papers):
    out = run_dir / "marks"
    out.mkdir(parents=True, exist_ok=True)
    head = fr.head_runs()
    ask = duels.Nimble()
    for p in papers:
        f = out / f"{p}.json"
        if f.exists() or p not in head:
            continue
        t0 = time.time()
        mf = run_dir / "meaning" / f"{p}.json"
        names = json.loads(mf.read_text(encoding="utf-8")) if mf.exists() else {}
        flat, spans = v3.md_tables(p)
        todo = []
        for t, fields, _org, _x in fr.plan(p, head):
            for mark, cs in groups(t, fields).items():
                above, below = sp.caption_above(t, flat, spans) or "", kt.caption_below(t, flat, spans) or ""
                todo.append((t, mark, cs, above, below))
        res = {"groups": []}
        for t, mark, cs, above, below in todo:              # gemma names every group first (one model at a time)
            cols = [c.name for c in cs]
            got = lt._gemma(NAME_PROMPT.format(mark=_flat(t.records[0].get(cs[0].name)) or mark, cols=cols,
                                               above=above[:900], below=below[:600]), NAME_SCHEMA)
            res["groups"].append({"table": str(t.table_index), "mark": mark, "columns": cols,
                                  "out_names": [names.get(c) if isinstance(names.get(c), str) else c for c in cols],
                                  "proposed": _flat((got or {}).get("name"))[:80]})
        if todo:
            v1.unload(v1.GEMMA)
        for g, (t, mark, cs, above, below) in zip(res["groups"], todo):
            st = (f"A table in a scientific paper has the columns {[c.name for c in t.columns][:14]}. The text above it: "
                  f"'{above[:700]}'. Its first rows read: {kt._shown(t, 3, 12)}. The columns {g['columns']} hold only "
                  f"'{mark}' or nothing.")
            ch, probs = ask(st, Q_CAT.format(cols=g["columns"]), dict(CAT))
            g["cat"] = {"choice": ch, "probs": probs}
            g["name"] = None
            if duels.sure(ch, probs, "categories") and g["proposed"]:
                ch2, p2 = ask(st, Q_NAME.format(name=g["proposed"]), {k: v.format(name=g["proposed"]) for k, v in NAME.items()})
                g["name_check"] = {"choice": ch2, "probs": p2}
                if duels.sure(ch2, p2, "yes"):
                    g["name"] = g["proposed"]
        ask.unload()
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        if res["groups"]:
            ok = [g for g in res["groups"] if g["name"]]
            print(f"  [marks] {p:22s} {len(ok)} of {len(res['groups'])} groups read as categories "
                  f"{[g['name'] for g in ok]} ({time.time() - t0:.0f}s)", flush=True)
    ask.unload()


def apply(dec, rows):
    """Assembled rows of a sure group: trait = the group's name, value = the column's name. In place;
    -> number of rows changed."""
    n = 0
    for g in (dec or {}).get("groups") or []:
        if not g.get("name"):
            continue
        cols = {c.lower(): c for c in g["columns"]} | {o.lower(): o for o in g["out_names"] if o}
        for r in rows:
            k = (r.get("measurementType") or "").lower()
            if k in cols and _flat(r.get("measurementValue")).lower() == g["mark"]:
                r["measurementValue"], r["measurementType"] = cols[k], g["name"]
                n += 1
    return n
