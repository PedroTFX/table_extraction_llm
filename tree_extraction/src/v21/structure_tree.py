"""How a table should be read: long, wide, or not at all (output/eval_split/DESIGN_structure.md).
The same questions for every candidate table; nimble decides from printed headers, cells
and the text above the table; code applies the answers to the tags.

  Q-ROW    record / wide / summary / other
  Q-NAMES  (record) which repeating trait column names the traits (trait_tree.ask_names)
  Q-VALUE  (record) yes / no per other column: holds the named trait's value (trait_tree)

    python structure_tree.py <run dir> [paper ...]     writes <run>/structure/<paper>.json
"""
import json

import column_tree as ct
import decoder as v1
import full_run as fr
import trait_tree as tt

SURE = 0.8


def _flat(s):
    return " ".join(str(s or "").split())


def reads_long(fields):
    return (any(f == "measurementType" for f in fields.values())
            and any(f == "measurementValue" for f in fields.values()))


def repeating(t, fields):
    """Trait-tagged columns whose cells repeat (structure: few distinct cells, many rows)."""
    out = []
    for c in t.columns:
        if fields.get(c.name) not in fr.TRAITS:
            continue
        cells = [_flat(r.get(c.name)) for r in t.records if _flat(r.get(c.name))]
        distinct = len(set(cells))
        if 3 <= distinct <= 60 and len(cells) >= 2 * distinct:
            out.append(c)
    return out


ROW_OPTIONS = {           # Q-ROW's options (v13's subject step quotes them in its clash duel)
    "record": ("one organism, specimen or group of organisms (a caste, sex or population) "
               "with one named trait and its measured value or mean (with SD): the trait is "
               "named in a column of its own"),
    "wide": "one organism, species or specimen, with its traits in the columns",
    "summary": ("a statistic relating traits or groups, or describing a distribution: "
                "quartiles, slopes, heritability, correlations, test or model results"),
    "other": "something else: definitions of traits, methods, sites or notes"}


def ask_row(client, t, caption=""):
    heads = [c.name for c in t.columns][:14]
    rows = t.records[:3]
    shown = " | ".join("row %d: " % (i + 1) + "; ".join(
        f"'{c.name}' = '{_flat(r.get(c.name))}'" for c in t.columns[:10] if _flat(r.get(c.name)))
        for i, r in enumerate(rows))
    state = f"A table in a scientific paper has the columns {heads}."
    if caption:
        state += f" The text printed directly above it: '{caption}'."
    state += f" Its first rows read: {shown}."
    return v1.ask(client, state, "What is each row of this table?", dict(ROW_OPTIONS))


def decide_table(client, t, fields, caption=""):
    dec = {"v4_long": reads_long(fields), "caption": caption, "action": "v4"}
    ch, probs = ask_row(client, t, caption)
    dec["row"] = {"choice": ch, "probs": probs}
    if probs.get(ch, 0) < SURE:
        return dec
    if ch == "record":
        for nc in repeating(t, fields):
            c2, p2 = tt.ask_names(client, t, nc, caption)
            dec.setdefault("names", {})[nc.name] = {"choice": c2, "probs": p2}
            if c2 != "names" or p2.get(c2, 0) < SURE:
                continue
            others = [c for c in t.columns if c.name != nc.name
                      and fields.get(c.name) != "verbatimIdentification"]
            values = []
            for c in others:
                c3, p3 = tt.ask_value(client, t, nc, c)
                dec.setdefault("value", {})[c.name] = {"choice": c3, "probs": p3}
                if c3 == "yes" and p3.get("yes", 0) >= SURE:
                    values.append(c.name)
            if values:
                dec.update(action="long", long={"type": nc.name, "values": values})
            break
    elif ch == "wide" and dec["v4_long"]:
        dec["action"] = "wide"
    elif ch in ("summary", "other") and dec["v4_long"]:
        dec["action"] = "no rows"
    return dec


def candidate(t, fields):
    return reads_long(fields) or bool(repeating(t, fields))


def expand(fields, dec):
    """The tags with the decision applied -> [tags] (a long reading gives two readings of the
    same records: long, and wide for the other trait columns)."""
    out = dict(fields)
    if not dec or dec.get("action") == "v4":
        return [out]
    if dec["action"] == "no rows":
        return [{k: ("none" if v in fr.TRAITS else v) for k, v in out.items()}]
    if dec["action"] == "wide":
        return [{k: ("measurementType" if v == "measurementValue" else v) for k, v in out.items()}]
    lg = dec["long"]
    long_ = {k: ("none" if v in fr.TRAITS else v) for k, v in out.items()}
    long_[lg["type"]] = "measurementType"
    for v in lg["values"]:
        long_[v] = "measurementValue"
    wide = {k: ("none" if k == lg["type"] or k in lg["values"] else
                "measurementType" if v == "measurementValue" else v) for k, v in out.items()}
    return [long_] + ([wide] if any(v in fr.TRAITS for v in wide.values()) else [])


def run(run_dir, papers, has_species):
    """One paper at a time; resumable (run_dir/structure/<paper>.json)."""
    import decoder_v3 as v3
    import species_tree as sp
    out = run_dir / "structure"
    out.mkdir(parents=True, exist_ok=True)
    head = fr.head_runs()
    client = None
    for p in papers:
        f = out / f"{p}.json"
        if f.exists() or p not in head:
            continue
        res = {}
        flat, spans = v3.md_tables(p)
        for t, fields, org, _x in fr.plan(p, head):
            if not t.records or not candidate(t, fields) or not has_species(t, fields, org):
                continue
            client = client or ct.DecisionClient(v1.NIMBLE, 1)
            res[str(t.table_index)] = decide_table(client, t, fields, sp.caption_above(t, flat, spans))
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        acts = [f"t{k}:{d['action']}" for k, d in res.items() if d["action"] != "v4"]
        print(f"  [structure] {p:22s} {len(res)} candidates; " + (", ".join(acts) or "no change"), flush=True)
    if client:
        v1.unload(v1.NIMBLE)
