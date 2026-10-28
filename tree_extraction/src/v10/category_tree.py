"""Category columns (v10; output/eval_split/DESIGN_categories.md). A table can print each category
of a trait as its own column, the cell saying whether the organism has it (Wallon2024 FoodPI /
FoodAni / FoodFg; Viza2023 'Body size BS / BM / BL'). Many GTs then record one row per category
the organism has ('Type of Food' = 'Animals'); some keep the columns as printed (Khayati2024).

  code       facts only: which wide trait columns hold nothing but flags (0/1, yes/no, y/n, x,
             +/-, fractions), and for each its structural headings — the header group the head
             reader found spanning it (t.col_groups) and the legend headings its code is listed
             under (the inventory). No grouping by code, no name-prefix rule.
  Q-CAT      per flag column with a heading: which trait is it a category of, or none (a yes/no
             trait of its own). Columns of a table answered (sure) with the same heading form a
             group; a group of one stays as printed. No heading: not asked, left as printed.
  Q-PRESENT  per group with fractions (fuzzy coding): which values mean the organism has the
             category — any above 0, or only the full value. Unsure: the group stays as printed.

    python full_run_v10.py v10:categories <papers>     writes <run>/categories/<paper>.json
"""
import json
import re

import column_tree as ct
import decoder as v1
import full_run as fr
import legend_names as ln

SURE = 0.8
FLAG = re.compile(r"^(0|1|0?\.\d+|0,\d+|[01]\.0+|yes|no|y|n|x|\+|-|–|—)$", re.I)
YES = re.compile(r"^(1|1\.0+|yes|y|x|\+)$", re.I)
FRACTION = re.compile(r"^(0?\.\d+|0,\d+)$")


def _flat(s):
    return " ".join(str(s or "").split())


def cells(t, col):
    return [_flat(r.get(col.name)) for r in t.records if _flat(r.get(col.name))]


def flag_only(t, col):
    vs = cells(t, col)
    return len(vs) >= 3 and all(FLAG.match(v) for v in vs) and any(YES.match(v) or FRACTION.match(v) for v in vs)


def headings(t, col, cats):
    """The column's structural headings: [(name, where)]."""
    out = []
    g = (getattr(t, "col_groups", None) or {}).get(col.name)
    if g:
        out.append((g, "the heading printed over this column in the table"))
    base = ln._base(col.name.replace(g or "", "", 1) if g else col.name) or ln._base(col.name)
    for e in cats:
        code, var = str(e.get("code") or "").strip(), str(e.get("variable") or "").strip()
        if code and var and code.lower() == base and ln._parsed(var) and \
                ln._base(var) not in {ln._base(h) for h, _w in out} and ln._base(var) != base:
            out.append((var, f"the heading the paper's legend lists the code '{code}' under"))
    return out


def ask_cat(client, t, col, spelled, heads, others):
    vals = sorted(set(cells(t, col)))[:8]
    state = (f"A table in a scientific paper has the columns {[c.name for c in t.columns][:14]}. "
             f"The column '{col.name}'" + (f" ('{spelled}')" if spelled and spelled != col.name else "")
             + f" holds only these values: {vals}. Other columns of the table that hold only such "
             f"values: {others[:12]}.")
    crit = {f"c{i}": f"a category of the trait '{h}' ({w}): the cell says whether the organism has "
                     f"this category" for i, (h, w) in enumerate(heads)}
    crit["own"] = (f"none: '{col.name}' is a yes/no trait of its own, not one of several categories "
                   f"of a trait")
    return v1.ask(client, state, f"Which trait is the column '{col.name}' a category of?", crit)


def ask_present(client, t, heading, cols):
    vals = sorted({v for c in cols for v in cells(t, c)})[:10]
    state = (f"A table in a scientific paper gives the categories of the trait '{heading}' as "
             f"columns {[c.name for c in cols][:10]}, whose cells hold values such as {vals}.")
    return v1.ask(client, state, "In these columns, which cell values mean the organism has the category?", {
        "any": "any value above 0: a fraction gives the share of the organism's records in the category",
        "top": "only the full value (1): smaller values are weak or uncertain"})


def is_long(t, fields):
    tags = {fields.get(c.name) for c in t.columns}
    return "measurementType" in tags and "measurementValue" in tags


def wide_flags(t, fields):
    """The wide trait columns holding only flags (as assembly reads wide trait columns)."""
    if is_long(t, fields):
        return []
    return [c for c in t.columns if fields.get(c.name) in fr.TRAITS and flag_only(t, c)]


def decide_table(client, t, fields, names, cats):
    flags = wide_flags(t, fields)
    res = {"columns": {}, "groups": {}}
    if len(flags) < 2:
        return res
    others = [c.name for c in flags]
    for c in flags:
        heads = headings(t, c, cats)
        if not heads:
            continue
        ch, probs = ask_cat(client, t, c, names.get(c.name), heads, [o for o in others if o != c.name])
        sure = probs.get(ch, 0) >= SURE
        h = heads[int(ch[1:])][0] if sure and ch and ch.startswith("c") else None
        res["columns"][c.name] = {"headings": heads, "choice": ch, "probs": probs, "heading": h}
    by = {}
    for name, a in res["columns"].items():
        if a["heading"]:
            by.setdefault(a["heading"], []).append(name)
    for h, cols in by.items():
        if len(cols) < 2:
            continue                                  # one category is not a choice: as printed
        g = {"columns": cols, "present": "yes"}
        colobjs = [c for c in t.columns if c.name in cols]
        if any(FRACTION.match(v) for c in colobjs for v in cells(t, c)):
            ch, probs = ask_present(client, t, h, colobjs)
            g["present_q"] = {"choice": ch, "probs": probs}
            g["present"] = ch if probs.get(ch, 0) >= SURE else None
        if g["present"]:
            res["groups"][h] = g
    return res


def category_of(dec, col_name):
    """(heading, present-rule) for a column in an applied group, else None."""
    for h, g in ((dec or {}).get("groups") or {}).items():
        if col_name in g["columns"]:
            return h, g["present"]
    return None


def has(value, rule):
    v = _flat(value)
    if YES.match(v):
        return True
    if FRACTION.match(v):
        x = float(v.replace(",", "."))
        return rule == "any" and x > 0
    return False


def run(run_dir, papers):
    """One paper at a time; resumable (run_dir/categories/<paper>.json). The tables are the ones
    full_run.plan gives (the caller installs its layers)."""
    out = run_dir / "categories"
    out.mkdir(parents=True, exist_ok=True)
    head = fr.head_runs()
    client = None
    for p in papers:
        f = out / f"{p}.json"
        if f.exists() or p not in head:
            continue
        mf = run_dir / "meaning" / f"{p}.json"
        names = json.loads(mf.read_text(encoding="utf-8")) if mf.exists() else {}
        cats = ln.entries(p)
        res, seen = {}, set()
        for t, fields, _o, _x in fr.plan(p, head):
            if t.table_index in seen:
                continue
            if len(wide_flags(t, fields)) < 2:
                continue
            seen.add(t.table_index)
            client = client or ct.DecisionClient(v1.NIMBLE, 1)
            res[str(t.table_index)] = decide_table(client, t, fields, names, cats)
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        groups = [f"t{k}: {h} <- {g['columns'][:4]}" for k, d in res.items() for h, g in d["groups"].items()]
        if res:
            print(f"  [categories] {p:22s} " + ("; ".join(groups) if groups else "no groups")[:300], flush=True)
    if client:
        v1.unload(v1.NIMBLE)
