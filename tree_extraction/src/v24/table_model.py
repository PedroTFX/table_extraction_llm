"""The table model, phase 1 (2026-11-20; REVIEW_Opus5.5xtra section 4 and 13.5, REVIEW_Fable5.2 section 4). Today six
questions each ask their own version of "what is a row / what does this table hold" (Q-KIND, Q-ALSO, Q-ALSO2, structure
Q-ROW, one_species ROWS, row_label Q_ROW), and later layers carry lift machinery to undo each other (Renoz2020 went
through Q-KIND, Q-ALSO and Q-ALSO2 on one decision). Here one tree asks each distinction once per table and stores it.
It runs beside today's reading and changes nothing in it; table_model_check.py compares the two.

  N1  purpose   what the table is for: organisms / places / analysis / key / methods / figure. It does not close the
                table: a table about organisms that also prints counts per site is 'organisms', and its count columns
                are a column decision (relevance Q-COL), not a reason to drop the whole table.
  N2  row       what one row stands for: organism / part / measurement / characteristic / statistic / other
                (asked when N1 is 'organisms' or not sure)
  N2b who       (N2 'organism', sure) taxon / individual / group

Each node is a chain of two-option duels (duels.duel, as one_species asks its rows): many options at once split
nimble's probability. A duel that is not sure stops the node: 'not sure', and the reading of today stands. The
wording is generic to organism groups and carries no example from the papers (the user, 2026-11-17).
nimble decides; code gives the layout (columns, first-column labels, text above and below) and stores the answers.

    python table_model.py run [papers]      (default: the tuning papers, dev + held_a)  -> <run>/table_model/<paper>.json
"""
import json
import sys

import _paths
import decoder_v3 as v3
import duels
import full_run_v24 as f24
import kind_tree as kt
import species_tree as sp

OUT = _paths.OUTPUT / "table_model"
SPLIT = json.loads((_paths.SUB / "output/eval_split/split_v15.json").read_text(encoding="utf-8"))["assign"]

Q_PURPOSE = "What is this table for?"
PURPOSE = [
    ("organisms", "data about organisms: each row (or, in a turned table, each column) is an organism, a taxon, a "
                  "specimen or a group of organisms, and the table gives what was measured, observed, counted or "
                  "recorded about it"),
    ("places", "data about places or samples: each row is a site, plot, trap, sample or date, and the table gives what "
               "was found, counted or measured there"),
    ("analysis", "results of an analysis: test statistics, model estimates, p-values, correlations, loadings, "
                 "ordination or index scores computed from the data"),
    ("key", "a key or legend: it explains the codes, abbreviations, categories or scores used in another table or in "
            "the text"),
    ("methods", "a description of methods, protocols, study sites or design, or a list of names without data"),
    ("figure", "numbers read off a figure (a plot, chart or boxplot), often approximate, not a table printed in the "
               "paper")]

Q_ROW = "What does each row of this table stand for?"
ROW = [
    ("organism", "one organism or group of organisms: a species or other taxon, a specimen, a colony, or a group such "
                 "as one sex, caste, life stage, population or treatment"),
    ("part", "one part of an organism, such as a body part, an organ, a segment or another structure, with the values "
             "recorded on that part"),
    ("measurement", "one measurement: the organism, the name of the characteristic measured and its value, each in a "
                    "column of its own, so that one organism takes several rows"),
    ("characteristic", "one characteristic or variable, named in the row, with its values for different organisms or "
                       "groups in the columns"),
    ("statistic", "one summary statistic (mean, SD, minimum, maximum, range or sample size) of values given elsewhere "
                  "in the table"),
    ("other", "a site, sample or date, a definition or method, or something else")]

Q_WHO = "Which kind of organism or group does each row stand for?"
WHO = [
    ("taxon", "one species or other taxon (a genus, family or morphospecies), with values that describe the taxon as "
              "a whole"),
    ("individual", "one individual, specimen, colony, nest or sample, with the values recorded on it"),
    ("group", "one group of organisms under one condition: a sex, caste, life stage, population, treatment, site or "
              "date, with the values recorded on that group")]


def _flat(s):
    return " ".join(str(s or "").split())


def first_labels(t, k=8):
    """The first column's distinct cells (layout: what the rows are labelled with)."""
    if not t.columns:
        return []
    out = []
    for r in t.records:
        v = _flat(r.get(t.columns[0].name))
        if v and v not in out:
            out.append(v[:60])
    return out[:k]


def table_state(t, above="", below=""):
    state = f"A table in a scientific paper has the columns {[c.name for c in t.columns][:14]}."
    if above:
        state += f" The text printed directly above it: '{above}'."
    if below:
        state += f" The text printed directly below it: '{below}'."
    state += f" It has {len(t.records)} rows."
    labs = first_labels(t)
    if labs:
        state += f" Its first column's labels include: {', '.join(repr(x) for x in labs)}."
    return state + f" Its first rows read: {kt._shown(t)}."


def node(ask, state, question, options):
    """One node: the duels over its options -> {"choice": label or None (not sure), "log": the duels}."""
    i, log = duels.duel(ask, state, question, options)
    return {"choice": options[i][0] if i is not None else None, "log": log}


def decide(ask, t, above, below):
    state = table_state(t, above, below)
    res = {"purpose": node(ask, state, Q_PURPOSE, PURPOSE)}
    if res["purpose"]["choice"] in ("organisms", None):
        res["row"] = node(ask, state, Q_ROW, ROW)
        if res["row"]["choice"] == "organism":
            res["who"] = node(ask, state, Q_WHO, WHO)
    return res


def tuning():
    return sorted(p for p, g in SPLIT.items() if g in ("dev", "held_a"))


def run(papers):
    """One paper at a time, resumable (<run>/table_model/<paper>.json); every table with rows is asked."""
    OUT.mkdir(parents=True, exist_ok=True)
    head = f24.head_runs()
    ask = duels.Nimble()
    try:
        for p in papers:
            f = OUT / f"{p}.json"
            if f.exists() or p not in head:
                continue
            flat, spans = v3.md_tables(p)
            res = {}
            for t, _ctx in f24.tables_of(p, head):
                if not t.records or str(t.table_index) in res:
                    continue
                above, below = sp.caption_above(t, flat, spans), kt.caption_below(t, flat, spans)
                res[str(t.table_index)] = decide(ask, t, above, below)
            f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
            got = ", ".join(f"t{k}:{d['purpose']['choice'] or '?'}/{(d.get('row') or {}).get('choice') or '-'}"
                            for k, d in res.items())
            print(f"  [table_model] {p:22s} {len(res)} tables; {got[:200]}", flush=True)
    finally:
        ask.unload()


def load(p):
    f = OUT / f"{p}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


if __name__ == "__main__":
    if sys.argv[1:2] == ["run"]:
        run(sys.argv[2:] or tuning())
    else:
        print(__doc__)
