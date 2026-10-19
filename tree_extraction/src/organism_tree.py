"""Which column names a table's organisms (output/eval_split/DESIGN.md). The same questions
for every table; nimble decides from printed cells, code only offers the columns and joins
the pieces nimble points to.

  Q-KIND   per column tagged verbatimIdentification: species / part / higher / other
           (with the table's section labels when it prints them); below SURE a second look,
           a yes / no question on 20 cells; still unsure -> the column tagger's call stands
  Q-PICK   several 'species' columns: which one names each row's organism, or none
  Q-GENUS  a 'part' column and no 'species' one: where the genus is printed (another
           column, the section labels above the rows, nowhere)
  Q-UNITS  only 'higher' columns: is each row one organism identified only to that rank
           (Espinosa's genera) or a summary of a group of species? units -> that column
           (several: Q-PICK at the finest rank); groups -> no species column
  else     no species column (rejection is valid): the table goes to the species step

    python organism_tree.py <run dir> [paper ...]     writes <run>/organism/<paper>.json
"""
import json
import re
import sys

import column_tree as ct
import decoder as v1
import full_run as fr

SECTION = re.compile(r"'([^']+)' \(row (\d+)\)")


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


def section_labels(ctx):
    """[(row, label)] from the reader's 'Section labels …' context line (printed rows)."""
    for line in ctx or []:
        if str(line).startswith("Section labels"):
            return sorted((int(r), lab) for lab, r in SECTION.findall(str(line)))
    return []


SURE = 0.8


def ask_kind(client, t, col, sections=None, n=8):
    state = (f"A table in a scientific paper has a column named '{col.name}'. Its cells read: "
             + ", ".join(f"'{c}'" for c in _cells(t, col, n)) + ".")
    if sections:                       # printed in the table: labels heading groups of rows
        state += (" The table also prints section labels heading its rows: "
                  + ", ".join(f"'{lab}' (row {r})" for r, lab in sections[:6]) + ".")
    return v1.ask(client, state, f"What do the cells of the column '{col.name}' name?", {
        "species": ("full species names: each cell has both the genus and the species name "
                    "(the genus perhaps abbreviated to its initial, perhaps followed by the "
                    "author), or a numbered morphospecies of a genus ('sp. 1')"),
        "part": ("species names without their genus: each cell has only the species name, "
                 "perhaps followed by its author and year; the genus is printed elsewhere"),
        "higher": "groups above species: genera, tribes, subfamilies, families, orders or other higher taxa",
        "other": "not organisms: references, traits, seasons, dates, places, numbers or descriptions"})


def ask_confirm(client, t, col, sections=None):
    """The second look when Q-KIND is unsure: a yes / no question, more cells."""
    state = (f"A table in a scientific paper has a column named '{col.name}'. Its cells read: "
             + ", ".join(f"'{c}'" for c in _cells(t, col, 20)) + ".")
    if sections:
        state += (" The table also prints section labels heading its rows: "
                  + ", ".join(f"'{lab}' (row {r})" for r, lab in sections[:6]) + ".")
    return v1.ask(client, state, f"Do the cells of the column '{col.name}' name organisms at "
                  f"species level?", {
        "yes": ("yes: each cell names an organism at species level, a species or a numbered "
                "morphospecies of a genus ('sp. 1')"),
        "no": ("no: the cells are something else, such as castes, sexes, seasons, groups above "
               "species, references, traits or places")})


def ask_pick(client, t, cols, finest=False):
    heads = [c.name for c in t.columns][:12]
    state = f"A table in a scientific paper has the columns {heads}."
    crit = {f"c{i}": f"the column '{c.name}', whose cells read " + ", ".join(f"'{x}'" for x in _cells(t, c, 4))
            for i, c in enumerate(cols)}
    crit["none"] = "none of these columns names the organism of each row"
    q = "Which column names the organism each row of the table is about"
    return v1.ask(client, state, q + (", at the finest rank given?" if finest else "?"), crit)


def _row(rec, cols):
    return "; ".join(f"'{c.name}' = '{_flat(rec.get(c.name))}'" for c in cols if _flat(rec.get(c.name)))


def ask_genus(client, t, part, others, sections):
    """Row by row: the first rows' cells, column by column; every other column an option."""
    shown = [part] + others
    rows = [r for r in t.records if _flat(r.get(part.name))][:3]
    state = (f"A table in a scientific paper has a column named '{part.name}' that gives only the "
             f"species name, without the genus. Its first rows read: "
             + " | ".join(f"row {i + 1}: {_row(r, shown[:8])}" for i, r in enumerate(rows)) + ".")
    crit = {f"c{i}": f"the column '{c.name}'" for i, c in enumerate(others)}
    if sections:
        crit["section"] = ("the section labels above the rows: "
                           + ", ".join(f"'{lab}' (row {r})" for r, lab in sections[:6]))
    crit["nowhere"] = "the genus is not printed in the table"
    return v1.ask(client, state, f"Which column gives the genus that goes before each name in "
                  f"'{part.name}'?", crit)


def decide_table(client, t, fields, ctx):
    """-> decision dict (also the record of every answer)."""
    cands = [c for c in t.columns if fields.get(c.name) == "verbatimIdentification"]
    dec = {"candidates": [c.name for c in cands], "kinds": {}, "organism": None,
           "genus_from": None, "outcome": "no species column"}
    if not cands:
        return dec
    sections = section_labels(ctx)
    for c in cands:
        ch, probs = ask_kind(client, t, c, sections)
        rec = {"choice": ch, "probs": probs}
        if probs.get(ch, 0) < SURE:                    # unsure: a second look, yes / no
            ch2, probs2 = ask_confirm(client, t, c, sections)
            rec["second"] = {"choice": ch2, "probs": probs2}
            if probs2.get(ch2, 0) >= SURE:              # 'part' names species too: kept
                rec["choice"] = ("other" if ch2 == "no" else "part" if ch == "part" else "species")
            else:                                       # still unsure: the tagger's call stands
                rec["choice"] = "species"
                rec["kept_tagger"] = True
        dec["kinds"][c.name] = rec
    kind = {c.name: dec["kinds"][c.name]["choice"] for c in cands}
    species = [c for c in cands if kind[c.name] == "species"]
    parts = [c for c in cands if kind[c.name] == "part"]
    if len(species) == 1:
        dec.update(organism=species[0].name, outcome="species column")
    elif len(species) > 1:
        ch, probs = ask_pick(client, t, species)
        dec["pick"] = {"choice": ch, "probs": probs}
        if ch and ch.startswith("c"):
            dec.update(organism=species[int(ch[1:])].name, outcome="species column (picked)")
    elif parts:
        part = parts[0]
        others = [c for c in t.columns if c.name != part.name]
        ch, probs = ask_genus(client, t, part, others, sections)
        dec["genus"] = {"choice": ch, "probs": probs}
        dec["organism"] = part.name
        if ch and ch.startswith("c"):
            dec.update(genus_from={"column": others[int(ch[1:])].name}, outcome="part + genus column")
        elif ch == "section":
            dec.update(genus_from={"sections": sections}, outcome="part + section labels")
        else:
            dec["outcome"] = "part only"
    elif any(kind[c.name] == "higher" for c in cands):
        highers = [c for c in cands if kind[c.name] == "higher"]
        ch, probs = ask_units(client, t, highers)
        dec["units"] = {"choice": ch, "probs": probs}
        if ch == "units" and probs.get(ch, 0) >= SURE:      # identified to genus (Espinosa)
            if len(highers) == 1:
                dec.update(organism=highers[0].name, outcome="identified above species")
            else:
                ch2, probs2 = ask_pick(client, t, highers, finest=True)
                dec["pick"] = {"choice": ch2, "probs": probs2}
                if ch2 and ch2.startswith("c"):
                    dec.update(organism=highers[int(ch2[1:])].name,
                               outcome="identified above species (picked)")
    return dec


def ask_units(client, t, highers):
    """A column of groups above species: is each row one organism identified only to that
    rank (the study's unit), or a summary of a group of several species?"""
    heads = [c.name for c in t.columns][:12]
    state = (f"A table in a scientific paper has the columns {heads}. Its column "
             + " and ".join(f"'{c.name}' reads " + ", ".join(f"'{x}'" for x in _cells(t, c, 6))
                            for c in highers) + ".")
    return v1.ask(client, state, "What is each row of this table about?", {
        "units": ("one kind of organism per row, identified only to genus or a higher rank: the "
                  "finest name the study gives it"),
        "groups": ("a group of several species per row: a tribe, subfamily, family or order "
                   "summarised as a whole")})


def run(run_dir, papers):
    """One paper at a time; resumable (run_dir/organism/<paper>.json)."""
    out = run_dir / "organism"
    out.mkdir(parents=True, exist_ok=True)
    head = fr.head_runs()
    client = None
    for p in papers:
        f = out / f"{p}.json"
        if f.exists() or p not in head:
            continue
        res = {}
        for (t, ctx), (_t, fields, _org, _x) in zip(fr.tables_of(p, head), fr.plan(p, head)):
            if not t.records or not any(fields.get(c.name) in fr.TRAITS for c in t.columns):
                continue
            if not any(fields.get(c.name) == "verbatimIdentification" for c in t.columns):
                continue
            client = client or ct.DecisionClient(v1.NIMBLE, 1)
            res[str(t.table_index)] = decide_table(client, t, fields, ctx)
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  [organism] {p:22s} " + "; ".join(
            f"t{k}: {d['outcome']}{' (' + d['organism'] + ')' if d['organism'] else ''}"
            for k, d in res.items()), flush=True)
    if client:
        v1.unload(v1.NIMBLE)


def species_from(dec, rec):
    """The species for one record under a table's decision ('' when none)."""
    if not dec or not dec.get("organism"):
        return ""
    sp = _flat(rec.get(dec["organism"]))
    g = dec.get("genus_from") or {}
    if sp and g.get("column"):
        genus = _flat(rec.get(g["column"]))
        return f"{genus} {sp}" if genus else sp
    if sp and g.get("sections"):
        row = rec.get("_row_index")
        above = [lab for r, lab in g["sections"] if row is not None and r < row]
        return f"{above[-1]} {sp}" if above else sp
    return sp


def organism_fn(run_dir):
    """f(paper, table, fields, org, rec) -> species, from run_dir/organism decisions; tables
    with no decision keep the tagged organism column (full_run.species_of)."""
    cache, tagged = {}, fr.species_of          # the tagged-column species, captured before
                                                # full_run_v4 points full_run.species_of here

    def f(paper, t, fields, org, rec):
        if paper not in cache:
            fp = run_dir / "organism" / f"{paper}.json"
            cache[paper] = json.loads(fp.read_text(encoding="utf-8")) if fp.exists() else {}
        dec = cache[paper].get(str(t.table_index))
        return species_from(dec, rec) if dec is not None else tagged(t, fields, org, rec)
    return f


if __name__ == "__main__":
    from pathlib import Path
    run(fr.OUT.parent / sys.argv[1], sys.argv[2:] or fr.gt_papers())
