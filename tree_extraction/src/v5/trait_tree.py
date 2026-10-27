"""Which tagged trait columns hold traits, and which tables are long format
(output/eval_split/DESIGN_traits.md). The same questions for every table; nimble decides
from printed headers and cells; code applies the answers to the tags.

  Q-COL    per column tagged measurementType / measurementValue: trait / trait names /
           identifier / genetic / organism / other
  Q-NAMES  'trait names' confirmed: names of different traits / values of one trait /
           organisms (unconfirmed -> the tagger's call stands)
  Q-VALUE  yes / no per other column, does it hold each row's value -> the table is read
           long (one value column per group allowed) AND wide for its other trait columns
  below SURE the tagger's call stands

    python trait_tree.py <run dir> [paper ...]      writes <run>/traits/<paper>.json
"""
import json
import sys

import column_tree as ct
import decoder as v1
import full_run as fr

SURE = 0.8
KEEP = "trait"
DROP = ("identifier", "genetic", "organism", "other")
MODE = "full"          # 'conservative': drop only identifier / organism / other, no long reading
CONSERVATIVE_DROP = ("identifier", "organism", "other")


def _flat(s):
    return " ".join(str(s or "").split())


def _cells(t, col, n=8):
    out = []
    for r in t.records:
        v = _flat(r.get(col.name))
        if v and v not in out:
            out.append(v)
        if len(out) >= n:
            break
    return out


def ask_col(client, t, col, caption=""):
    heads = [c.name for c in t.columns][:14]
    state = f"A table in a scientific paper has the columns {heads}."
    if caption:                                   # layout: the text printed above the table
        state += f" The text printed directly above it: '{caption}'."
    state += (f" The column '{col.name}' holds: " + ", ".join(f"'{x}'" for x in _cells(t, col)) + ".")
    return v1.ask(client, state, f"What does the column '{col.name}' hold?", {
        "trait": ("a trait recorded for each organism, or a statistic of it (mean, SD, SE, range): "
                  "a size, mass, count or ratio, or a category describing the organism, such as "
                  "its diet, prey, nest site, behaviour or activity"),
        "trait names": ("names of traits: each row says which trait its value belongs to, and the "
                        "value is in another column"),
        "identifier": "labels of specimens, individuals, samples, sites or records",
        "genetic": "genetic markers or genotypes, such as allele sizes at microsatellite loci",
        "organism": "the names of the organisms the rows are about (their species or taxa)",
        "other": ("something that does not describe the organism: results of statistical tests "
                  "or models relating traits or groups (p-values, F, t, coefficients, "
                  "correlations, slopes, principal components), references, dates, methods "
                  "or notes")})


def ask_value(client, t, names, col):
    """Yes / no per candidate column: a long table can have one value column per group."""
    heads = [c.name for c in t.columns][:14]
    state = (f"A table in a scientific paper has the columns {heads}. The column '{names.name}' "
             f"names a trait in each row: " + ", ".join(f"'{x}'" for x in _cells(t, names, 6))
             + f". The column '{col.name}' holds: " + ", ".join(f"'{x}'" for x in _cells(t, col, 4)) + ".")
    return v1.ask(client, state, f"Does the column '{col.name}' hold the values of the traits "
                  f"named in '{names.name}'?", {
        "yes": ("yes: each row's cell is the value measured or recorded for the organism for the "
                "trait that row names, or a statistic of it (mean, SD, SE, range)"),
        "no": ("no: it holds something else: a statistic relating traits or groups (a "
               "correlation, a regression slope or coefficient, a test result), labels, groups, "
               "sample sizes or notes")})


def ask_names(client, t, col, caption=""):
    """Before reading a table long: are the cells names of different traits?"""
    heads = [c.name for c in t.columns][:14]
    state = f"A table in a scientific paper has the columns {heads}."
    if caption:
        state += f" The text printed directly above it: '{caption}'."
    state += f" The column '{col.name}' holds: " + ", ".join(f"'{x}'" for x in _cells(t, col, 10)) + "."
    return v1.ask(client, state, f"What are the cells of the column '{col.name}'?", {
        "names": ("names of different traits, one per row (such as 'Body length', 'Head width', "
                  "'Mass'), whose values are in other columns"),
        "values": "values of one trait (such as 'predator', 'herbivore' or 'solitary')",
        "organisms": "names of organisms or taxa"})


def decide_table(client, t, fields, caption=""):
    cols = [c for c in t.columns if fields.get(c.name) in fr.TRAITS]
    dec = {"cols": {}, "long": None, "caption": caption}
    for c in cols:
        ch, probs = ask_col(client, t, c, caption)
        sure = probs.get(ch, 0) >= SURE
        dec["cols"][c.name] = {"choice": ch, "probs": probs, "tag": fields.get(c.name),
                               "applied": ch if sure else "tagger"}
    for nc in [c for c in cols if dec["cols"][c.name]["applied"] == "trait names"]:
        ch, probs = ask_names(client, t, nc, caption)
        dec["names"] = {"column": nc.name, "choice": ch, "probs": probs}
        if not (ch == "names" and probs.get(ch, 0) >= SURE):
            dec["cols"][nc.name]["applied"] = "tagger"  # not confirmed: the tagger's call stands
            continue
        others = [c for c in t.columns if c.name != nc.name
                  and fields.get(c.name) != "verbatimIdentification"]
        dec["value"] = {}
        for c in others:
            ch, probs = ask_value(client, t, nc, c)
            dec["value"][c.name] = {"choice": ch, "probs": probs}
        values = [c.name for c in others if dec["value"][c.name]["choice"] == "yes"
                  and dec["value"][c.name]["probs"].get("yes", 0) >= SURE]
        if values:
            dec["long"] = {"type": nc.name, "values": values}
        else:
            dec["cols"][nc.name]["applied"] = "tagger"
        break
    return dec


def expand(fields, dec):
    """The tags with the answers applied -> [tags] (a long table gives two readings of the
    same records: the long one, type + value columns, and the wide one, the other columns
    nimble called traits)."""
    out = dict(fields)
    if not dec:
        return [out]
    drop = CONSERVATIVE_DROP if MODE == "conservative" else DROP
    for name, d in dec["cols"].items():
        if d["applied"] in drop:
            out[name] = "none"
    lg = dec.get("long") if MODE != "conservative" else None
    if not lg:
        return [out]
    vals = lg.get("values") or [lg.get("value")]
    long_ = {k: ("none" if v in fr.TRAITS else v) for k, v in out.items()}
    long_[lg["type"]] = "measurementType"
    for v in vals:
        long_[v] = "measurementValue"
    wide = {k: ("none" if k == lg["type"] or k in vals else v) for k, v in out.items()}
    wide = {k: ("measurementType" if v == "measurementValue" else v) for k, v in wide.items()}
    return [long_] + ([wide] if any(v in fr.TRAITS for v in wide.values()) else [])


def apply(fields, dec):
    return expand(fields, dec)[0]


def run(run_dir, papers, has_species):
    """One paper at a time; resumable (run_dir/traits/<paper>.json). has_species(t, fields,
    org) -> whether the table gives rows (only those are asked)."""
    import decoder_v3 as v3
    import species_tree as sp
    out = run_dir / "traits"
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
            if not t.records or not any(fields.get(c.name) in fr.TRAITS for c in t.columns):
                continue
            if not has_species(t, fields, org):
                continue
            client = client or ct.DecisionClient(v1.NIMBLE, 1)
            res[str(t.table_index)] = decide_table(client, t, fields, sp.caption_above(t, flat, spans))
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        n_drop = sum(d["applied"] in DROP for x in res.values() for d in x["cols"].values())
        n_long = sum(1 for x in res.values() if x.get("long"))
        print(f"  [traits] {p:22s} {len(res)} tables, dropped {n_drop} cols, long {n_long}", flush=True)
    if client:
        v1.unload(v1.NIMBLE)
