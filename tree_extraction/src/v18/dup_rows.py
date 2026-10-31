"""Duplicate rows (v16, output/eval_split/DESIGN_duplicate_rows_v16.md): the same data read more
than once. Code only, no model: both rules are strict enough to be checked on the tuning papers.

  repeat   in one table, every species that takes more than one row has all its rows identical
           (every printed column and the section labels above it): the record is printed again,
           so one copy is kept. Cerini2023's S1 (123 species, each 6-15 identical rows), Graf2021
           t8 (its header row repeated on later pages), Normandin2017 t6. A table where any
           repeated species' rows differ (individuals: Noriega2023, Raine2018, Tsai2020) is left
           as it is.
  copy     a later table of the paper with the same column names, the same number of rows, the
           same first column in the same order and >= 80% of its cells equal to an earlier
           table's: the same data printed again (Cerini2023's S1 as .csv and .xlsx, which differ
           only where Excel turned 'Flight season' cells into dates). It gives no rows.

    python full_run_v16.py v16:dups <papers>     writes <run>/dup_rows/<paper>.json (a record)
"""
import collections
import copy
import json

import full_run as fr

COPY_SHARE = 0.8


def _flat(s):
    return " ".join(str(s or "").split())


def _key(t, r):
    """A row as printed, with the section labels above it (equal cells under 'Females' and
    'Males' are not a repeat)."""
    return tuple(_flat(r.get(c.name)) for c in t.columns) + tuple(r.get("_sections") or [])


def repeats(t, fields, org):
    """-> number of rows to drop when every repeated species' rows are identical, else 0."""
    by = collections.defaultdict(list)
    for r in t.records:
        by[fr.species_of(t, fields, org, r) or _flat(r.get(t.columns[0].name))].append(_key(t, r))
    rep = [v for v in by.values() if len(v) > 1]
    if not rep or any(len(set(v)) > 1 for v in rep):
        return 0
    return sum(len(v) - 1 for v in rep)


def is_copy(a, b):
    if a.table_index == b.table_index:          # one table plan() gives twice (Noriega2023 t8), not a copy
        return False
    if [c.name for c in a.columns] != [c.name for c in b.columns] or len(a.records) != len(b.records) or not a.records:
        return False
    first = a.columns[0].name
    if [_flat(r.get(first)) for r in a.records] != [_flat(r.get(first)) for r in b.records]:
        return False
    cells = [(_flat(x.get(c.name)), _flat(y.get(c.name))) for x, y in zip(a.records, b.records) for c in a.columns]
    return sum(p == q for p, q in cells) >= COPY_SHARE * len(cells)


def run(run_dir, papers):
    """The record of what apply() drops, per paper (run_dir/dup_rows/<paper>.json)."""
    out = run_dir / "dup_rows"
    out.mkdir(parents=True, exist_ok=True)
    head = fr.head_runs()
    for p in papers:
        if p not in head:
            continue
        tables = [x for x in fr.plan(p, head) if x[0].records]
        res = {"repeat": {}, "copy": {}}
        for t, fields, org, _x in tables:
            n = repeats(t, fields, org)
            if n:
                res["repeat"][str(t.table_index)] = {"rows dropped": n, "rows": len(t.records)}
        for i, (a, *_r) in enumerate(tables):
            for b, *_s in tables[i + 1:]:
                if str(b.table_index) not in res["copy"] and is_copy(a, b):
                    res["copy"][str(b.table_index)] = {"copy of": str(a.table_index), "rows": len(b.records)}
        (out / f"{p}.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        if res["repeat"] or res["copy"]:
            print(f"  [dups] {p:22s} repeats {res['repeat'] or '-'} copies {res['copy'] or '-'}", flush=True)


def apply(dec, out):
    """plan()'s list with copied tables left out and repeated records left out (the first of
    each kept), as run() recorded them."""
    if not dec:
        return out
    drop, rep = set(dec.get("copy") or {}), set(dec.get("repeat") or {})
    res = []
    for t, fields, org, x in out:
        k = str(t.table_index)
        if k in drop:
            continue
        if k in rep:
            seen, keep = set(), []
            for r in t.records:
                key = _key(t, r)
                if key not in seen:
                    seen.add(key)
                    keep.append(r)
            t = copy.copy(t)
            t.records = keep
        res.append((t, fields, org, x))
    return res
