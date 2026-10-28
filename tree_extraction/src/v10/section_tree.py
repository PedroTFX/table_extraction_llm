"""What a table's section labels tell the rows below them (output/eval_split/DESIGN_sections.md).
A section label is a row printed across the table that heads the rows below it ('Calliopsini',
'S Africa', 'C. calcarata', 'Wing length'). head_to_table keeps them (t.sections, and each
record's rec["_sections"]: the indexes of the labels above it); nimble decides what each one is;
code applies the answers to the records below it.

  Q-SECTION  per label: higher / genus / organism / trait / place / context / treatment / other
             (unsure < SURE: a second look with more rows; still unsure: the label is unused)
  Q-CONTEXT  after a sure 'context': caste / sex / lifeStage
  Q-SERIES   when one table's sure answers name two different applied kinds: the labels asked
             once together, which one kind they are (sure: it replaces theirs)

    python full_run_v8.py v8:sections <papers>     writes <run>/sections/<paper>.json
"""
import json
import re

import column_tree as ct
import decoder as v1
import full_run as fr

SURE = 0.8
APPLIED = {"genus", "organism", "trait", "place", "context", "treatment"}
FIELD = {"place": "verbatimLocality", "treatment": "sampleTreatment"}
EPITHET = re.compile(r"[a-z][a-z-]+\.?")

KINDS = {
    "higher": "a family, subfamily, tribe or order that the organisms in the rows below belong to",
    "genus": ("the genus of the organisms in the rows below, whose rows give only the species "
              "name (epithet) without the genus"),
    "organism": ("the organism (species) that the rows below are about; the rows below are not "
                 "organisms themselves (they are sites, groups, sexes, years or measurements)"),
    "trait": "the trait or measurement that the values in the rows below are values of",
    "place": "the site, region or country that the rows below come from",
    "context": "the caste, sex or life stage that the rows below are about",
    "treatment": "the treatment, condition, habitat type or season the rows below were measured under",
    "other": ("none of these: a note, a 'continued' mark, an abbreviation list, an analysis or "
              "model block, or a heading of statistics"),
}


def _flat(s):
    return " ".join(str(s or "").split())


def _below(t, i, n):
    """The first n records under label i (and above the next label)."""
    out = []
    for r in t.records:
        secs = r.get("_sections") or []
        if secs and secs[-1] == i:
            out.append(r)
            if len(out) >= n:
                break
    return out


def _row(r, t, cols=8):
    return "; ".join(f"'{c.name}' = '{_flat(r.get(c.name))}'" for c in t.columns[:cols]
                     if _flat(r.get(c.name)))


def _state(t, i, n):
    labels = t.sections
    rows = _below(t, i, n)
    s = (f"A table in a scientific paper has the columns {[c.name for c in t.columns][:12]}. "
         f"It prints section labels on rows of their own, each heading the rows below it: "
         + ", ".join(f"'{lab}'" for _r, lab in labels[:20])
         + (f" ... ({len(labels)} labels)" if len(labels) > 20 else "") + ". "
         f"The rows below the label '{labels[i][1]}' read: "
         + (" | ".join(f"row {k + 1}: {_row(r, t)}" for k, r in enumerate(rows)) or "(none)") + ".")
    return s


def ask_section(client, t, i, n=3):
    return v1.ask(client, _state(t, i, n),
                  f"What does the section label '{t.sections[i][1]}' tell about the rows below it?",
                  KINDS)


def ask_context(client, t, i):
    return v1.ask(client, _state(t, i, 3),
                  f"Which does the section label '{t.sections[i][1]}' give for the rows below it?", {
                      "caste": "the caste: worker, queen, soldier, male caste",
                      "sex": "the sex: male, female",
                      "lifeStage": "the life stage: larva, pupa, nymph, adult, egg"})


def ask_series(client, t, idx):
    labs = [t.sections[i][1] for i in idx]
    state = _state(t, idx[0], 3)
    return v1.ask(client, state, "These section labels of the table are one series: "
                  + ", ".join(f"'{x}'" for x in labs) + ". Which one kind of label are they?", KINDS)


def decide_table(client, t):
    """-> {"labels": [[row, label]], "answers": {i: {...}}, "series": {...}?}"""
    res = {"labels": [list(x) for x in t.sections], "answers": {}}
    for i in range(len(t.sections)):
        ch, probs = ask_section(client, t, i)
        a = {"choice": ch, "probs": probs}
        if probs.get(ch, 0) < SURE:                     # unsure: a second look, more rows
            ch2, probs2 = ask_section(client, t, i, n=8)
            a["second"] = {"choice": ch2, "probs": probs2}
            ch, probs = ch2, probs2
        a["final"] = ch if probs.get(ch, 0) >= SURE else None
        if a["final"] == "context":
            c2, p2 = ask_context(client, t, i)
            a["context"] = {"choice": c2, "probs": p2}
            if p2.get(c2, 0) < SURE:
                a["final"] = None                       # which field is unsure: nothing applied
        res["answers"][str(i)] = a
    kinds = {a["final"] for a in res["answers"].values() if a["final"] in APPLIED}
    if len(kinds) > 1:                                  # a clash: the labels asked together
        idx = [int(i) for i, a in res["answers"].items() if a["final"] in APPLIED]
        ch, probs = ask_series(client, t, idx)
        res["series"] = {"labels": idx, "choice": ch, "probs": probs}
        if probs.get(ch, 0) >= SURE:
            for i in idx:
                a = res["answers"][str(i)]
                if ch == "context" and a["final"] != "context":
                    a["final"] = None                   # no field answer for this one: unused
                else:
                    a["final"] = ch
    return res


def record_info(dec, rec):
    """{kind: label} for one record: per applied kind, the nearest label above it."""
    out = {}
    if not dec:
        return out
    ans = dec.get("answers") or {}
    for i in reversed(rec.get("_sections") or []):
        a = ans.get(str(i)) or {}
        k = a.get("final")
        if k not in APPLIED:
            continue
        if k == "context":
            k = (a.get("context") or {}).get("choice")
        if k and k not in out:
            out[k] = dec["labels"][i][1]
    return out


def fields_of(info):
    """Row fields the labels fill: place, treatment, caste / sex / lifeStage."""
    out = {FIELD[k]: v for k, v in info.items() if k in FIELD}
    out.update({k: v for k, v in info.items() if k in ("caste", "sex", "lifeStage")})
    return out


def with_genus(info, species):
    """'<genus label> <epithet>' when the species is a lone epithet and a genus label is above."""
    if species and info.get("genus") and EPITHET.fullmatch(species):
        return f"{info['genus']} {species}"
    return species


def candidate(t, fields):
    return bool(getattr(t, "sections", None)) and bool(t.records) and \
        any(v in fr.TRAITS for v in fields.values())


def run(run_dir, papers):
    """One paper at a time; resumable (run_dir/sections/<paper>.json). The tables are the ones
    full_run.plan gives (the caller installs its layers), with trait columns left."""
    out = run_dir / "sections"
    out.mkdir(parents=True, exist_ok=True)
    head = fr.head_runs()
    client = None
    for p in papers:
        f = out / f"{p}.json"
        if f.exists() or p not in head:
            continue
        res, seen = {}, set()
        for t, fields, _org, _x in fr.plan(p, head):
            if t.table_index in seen or not candidate(t, fields):
                continue
            seen.add(t.table_index)
            client = client or ct.DecisionClient(v1.NIMBLE, 1)
            res[str(t.table_index)] = decide_table(client, t)
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        if res:
            print(f"  [sections] {p:22s} " + "; ".join(
                f"t{k}: " + ", ".join(f"{d['labels'][int(i)][1][:18]}={a['final']}"
                                      for i, a in list(d["answers"].items())[:4])
                for k, d in res.items()), flush=True)
    if client:
        v1.unload(v1.NIMBLE)
