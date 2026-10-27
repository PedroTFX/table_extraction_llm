"""The structure each table should be read with, derived from the GT, and the structure v4
reads it with. Reads saved files only, no model.

Per table that gives rows (species from v4's decisions):
  GT long   a column whose cells are GT trait names (>= half of its distinct cells, >= 3)
            and another column whose cells, with the row's species, are GT values
  GT wide   >= 2 headers that are GT trait names, their cells GT values
  no GT rows  neither (statistics, or traits the GT does not cover)
  v4 reads  long (a type column + value columns tagged) / wide

    python structure_key.py [paper ...]   -> output/eval_split/structure_key.json + .txt
"""
import collections
import contextlib
import io
import json
import sys

import _paths
import full_run as fr
import full_run_v4 as r4
import species_missed as sm
import species_tree as sp

sys.path.insert(0, str(_paths.REPO / "source"))
OUT = fr.OUT.parent / "eval_split"
V4 = fr.OUT.parent / "full_run_v4"


def _flat(s):
    return " ".join(str(s or "").split())


def gt_of(paper):
    import evaluate as ev
    from mineru_extract import classify_folder
    with contextlib.redirect_stdout(io.StringIO()):
        _, gt, _ = classify_folder(_paths.PAPERS / paper)
        rows = ev.load_xlsx(gt)
    types = {ev._type_key(r.get("measurementType", "")): r.get("measurementType", "") for r in rows}
    types.pop("", None)
    vals = collections.defaultdict(set)          # species key -> normalised values
    vtypes = collections.defaultdict(set)        # (species key, value) -> GT trait names
    for r in rows:
        k = sm._key(r.get("verbatimIdentification"))
        if k:
            v = ev.normalize_value(r.get("measurementValue", ""))
            vals[k].add(v)
            vtypes[(k, v)].add(ev._type_key(r.get("measurementType", "")))
    vals["_vtypes"] = vtypes
    return types, vals


def is_type(cell, types):
    import evaluate as ev
    k = ev._type_key(cell)
    if not k:
        return False
    return k in types or any(ev._type_sim(cell, t) >= 0.85 for t in types.values())


def value_rate(t, col, species, vals):
    import evaluate as ev
    n = hit = 0
    for r, s in zip(t.records, species):
        v = _flat(r.get(col.name))
        if not s or not v:
            continue
        n += 1
        k = sm._key(s)
        hit += bool(k and ev.normalize_value(v) in vals.get(k, ()))
    return hit / n if n else 0.0


def long_by_values(t, species, vals):
    """Name-independent: a column whose values (with the row's species) are GT values of
    >= 3 different GT traits, and a column whose cells line up with those traits."""
    import evaluate as ev
    vtypes = vals["_vtypes"]
    for vc in t.columns:
        matched = []                                 # (row index, GT trait names)
        n = 0
        for i, (r, s) in enumerate(zip(t.records, species)):
            v = _flat(r.get(vc.name))
            if not s or not v:
                continue
            n += 1
            k = sm._key(s)
            ts = vtypes.get((k, ev.normalize_value(v))) if k else None
            if ts:
                matched.append((i, ts))
        if not n or len(matched) < 0.3 * n:
            continue
        if len(set().union(*[ts for _i, ts in matched])) < 3:
            continue
        best, score = None, 0.0
        for nc in t.columns:
            if nc.name == vc.name:
                continue
            by = collections.defaultdict(collections.Counter)
            sp_of = collections.defaultdict(set)
            for i, ts in matched:
                cell = _flat(t.records[i].get(nc.name))
                by[cell].update(ts)
                sp_of[cell].add(species[i])
            cells = [c for c in by if sum(by[c].values()) >= 5]
            # a names column: few distinct cells, each with several species, each pointing
            # mainly to one GT trait, and different cells to different traits
            if len(cells) < 3 or len(by) > 60 or any(len(sp_of[c]) < 2 for c in cells):
                continue
            top = [by[c].most_common(1)[0] for c in cells]
            share = sum(n / sum(by[c].values()) for c, (_ty, n) in zip(cells, top)) / len(cells)
            distinct = len({ty for ty, _n in top}) / len(cells)
            if share >= 0.5 and distinct >= 0.7 and share * distinct > score:
                best, score = nc.name, share * distinct
        if best:
            return {"names": best, "values": [vc.name], "score": round(score, 2)}
    return None


def label(t, species, types, vals, dec=None):
    """dec: the saved decoder record of the paper; a cell's decoded term counts too
    ('EL' -> 'elytra length')."""
    def term(c, x):
        r = (dec or {}).get(f"{t.table_index}:{c.index}") or {}
        return ((r.get("cells") or {}).get(x) or {}).get("term") or x
    for c in t.columns:
        cells = list(dict.fromkeys(_flat(r.get(c.name)) for r in t.records if _flat(r.get(c.name))))
        if len(cells) >= 3 and sum(is_type(x, types) or is_type(term(c, x), types)
                                   for x in cells) * 2 >= len(cells):
            vcols = [o.name for o in t.columns if o.name != c.name and value_rate(t, o, species, vals) >= 0.3]
            if vcols:
                return "GT long", {"names": c.name, "values": vcols}
    lg = long_by_values(t, species, vals)
    if lg:
        return "GT long", lg
    wide = [c.name for c in t.columns if is_type(c.name, types) and value_rate(t, c, species, vals) >= 0.3]
    if len(wide) >= 2:
        return "GT wide", {"columns": wide}
    return "no GT rows", {}


def main(papers):
    r4.install(V4, decisions=True)
    head = fr.head_runs()
    papers = papers or fr.gt_papers()
    rows = []
    for p in papers:
        if p not in head:
            continue
        try:
            types, vals = gt_of(p)
        except Exception:
            continue
        named = sp.species_of_tables(V4 / "species", p)
        df = V4 / "decode" / f"{p}.json"
        dec = json.loads(df.read_text(encoding="utf-8")) if df.exists() else {}
        for t, fields, org, _x in fr.plan(p, head):
            if not t.records or not any(fields.get(c.name) in fr.TRAITS for c in t.columns):
                continue
            species = [fr.species_of(t, fields, org, r) or named.get(t.table_index, "") for r in t.records]
            if not any(species):
                continue
            gt, info = label(t, species, types, vals, dec)
            tagged_t = [c.name for c in t.columns if fields.get(c.name) == "measurementType"]
            tagged_v = [c.name for c in t.columns if fields.get(c.name) == "measurementValue"]
            reads = "long" if tagged_t and tagged_v else "wide"
            rows.append({"paper": p, "split": r4.split()["assign"].get(p), "table": t.table_index,
                         "records": len(t.records), "gt": gt, "info": info, "v4": reads,
                         "v4_type": tagged_t[:1], "v4_values": tagged_v})
    (OUT / "structure_key.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")
    c = collections.Counter((r["split"], r["gt"], r["v4"]) for r in rows)
    L = ["table structure: GT-derived vs how v4 reads it (tables that give rows)", ""]
    for s in ("dev", "held"):
        L.append(f"{s}: " + "; ".join(f"{g} read {v}: {n}" for (h, g, v), n in sorted(c.items()) if h == s))
    L.append("")
    for r in rows:
        if r["gt"] == "GT long" or r["v4"] == "long":
            ok = "OK " if (r["gt"] == "GT long") == (r["v4"] == "long") else "XX "
            L.append(f"  {ok}{r['split']:4s} {r['paper']:20s} t{r['table']:<3} {r['records']:6d} rec  "
                     f"{r['gt']:10s} v4 reads {r['v4']:4s} {r['info'] or ''} {r['v4_type']} {r['v4_values'][:4]}")
    (OUT / "structure_key.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main(sys.argv[1:])
