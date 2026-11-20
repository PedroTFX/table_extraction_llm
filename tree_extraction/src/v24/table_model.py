"""The table model, phase 1 (2026-11-20; REVIEW_Opus5.5xtra section 4 and 13.5, REVIEW_Fable5.2 section 4). Today six
questions each ask their own version of "what is a row / what does this table hold" (Q-KIND, Q-ALSO, Q-ALSO2, structure
Q-ROW, one_species ROWS, row_label Q_ROW), and later layers carry lift machinery to undo each other (Renoz2020 went
through Q-KIND, Q-ALSO and Q-ALSO2 on one decision). Here one tree asks each distinction once per table and stores it.
It runs beside today's reading and changes nothing in it; stats/table_model_check.py compares the two.

Version 2 (2026-11-20, after v1 dropped 17 GT tables against today's 2). v1's faults, each answered here:
  - N1 defined its options by the rows ("each row is a site, plot, sample"), so it was a second row question; a table of
    specimens with a plot column fitted both 'organisms' and 'places'. N1 now asks only what the table is used for.
  - 'places' and 'analysis' closed tables, but most trait tables are mixed (traits beside counts per site, or beside one
    test column). Only a key, a methods table and numbers read off a figure take a table out of the data now; counts,
    site columns and test columns are column decisions.
  - A group named after its place, time or condition was read as a place; something an organism makes (an egg case)
    was neither organism nor part; descriptive statistics were read as results of an analysis. Each is written into
    the options.
  - Rows that are statistics (minimum, mean, maximum) are the organism's measurements as summaries and stay read.
  - One duel settled a node (organisms against places, then 'places' won every later duel sure). Each node now runs its
    duels in both option orders and keeps an answer only when both agree; the row nodes have at most four options.
  - The text below a table is cut where the next table's caption starts.

  N2   rows      organisms / parts / variables / other                    (asked first, on every table with rows)
  N2b  how       (organisms) taxon / individual / group / measurement
  N2c  variable  (variables) characteristic / statistic
  N1   purpose   data / results / key / methods / figure                  (every table; key, methods, figure close it)

nimble decides; code gives the layout (columns, first-column labels, text above and below) and stores the answers.
The wording is generic to organism groups and carries no example from the papers (the user, 2026-11-17).

    python table_model.py run [papers]      (default: the tuning papers, dev + held_a)  -> <run>/table_model_v2/<paper>.json
"""
import json
import re
import sys

import _paths
import decoder_v3 as v3
import duels
import full_run_v24 as f24
import kind_tree as kt
import species_tree as sp

OUT = _paths.OUTPUT / "table_model_v2"
SPLIT = json.loads((_paths.SUB / "output/eval_split/split_v15.json").read_text(encoding="utf-8"))["assign"]

Q_ROWS = "What does each row of this table stand for?"
ROWS = [
    ("organisms", "an organism or a group of organisms: a species or other taxon, a specimen, a colony, or a group such "
                  "as one sex, caste, life stage, population or treatment. A group is often labelled with the place, "
                  "time or condition it comes from, and it is still a group of organisms"),
    ("parts", "a part of an organism or something it makes: a body part, an organ, a segment, an egg case, a nest or "
              "another structure, with the values recorded on it"),
    ("variables", "a characteristic, a variable or a statistic named in the row (such as a length, a mean or a "
                  "maximum), with its values in the columns"),
    ("other", "a site, sampling event or date that names no organism, a definition or method, a reference, or "
              "something else")]

Q_HOW = "How does each row give the organism and what was recorded on it?"
HOW = [
    ("taxon", "the row is one species or other taxon (a genus, family or morphospecies), and its values describe the "
              "taxon as a whole"),
    ("individual", "the row is one individual, specimen, colony, nest or sample, and its values were recorded on it"),
    ("group", "the row is one group of organisms under one condition (a sex, caste, life stage, population, "
              "treatment, site or date), and its values were recorded on that group"),
    ("measurement", "the row is one measurement: the organism, the name of the characteristic and its value each sit "
                    "in a column of their own, so one organism takes several rows")]

Q_VAR = "What is named in each row?"
VAR = [
    ("characteristic", "a characteristic or variable that was measured or recorded, with its values for different "
                       "organisms, groups or conditions in the columns"),
    ("statistic", "a summary statistic (such as a minimum, mean, median, maximum, standard deviation or sample size) "
                  "of the values recorded, with the columns giving what it summarises")]

Q_PURPOSE = "What is this table used for in the paper?"
PURPOSE = [
    ("data", "it reports data the study recorded or compiled: measurements, observations, counts, categories, or "
             "summaries of them such as sample sizes, means, standard deviations, coefficients of variation or "
             "ranges, whatever the rows are"),
    ("results", "it reports results computed by a statistical analysis: test statistics, model estimates, p-values, "
                "correlations, loadings or ordination scores. A summary of the measurements (sample size, mean, SD, "
                "range) is data, not a result of an analysis"),
    ("key", "it is a key or legend: it explains the codes, abbreviations, categories or scores used in another table "
            "or in the text"),
    ("methods", "it describes methods, protocols, study sites or design, or lists names or references without "
                "recorded values"),
    ("figure", "it gives numbers read off a figure (a plot, chart or boxplot), often approximate, not a table printed "
               "in the paper")]
CLOSES = {"key", "methods", "figure"}

NEXT_CAPTION = re.compile(r"(?i)\bt\s?a\s?b\s?l\s?e\s+S?\d")


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


def text_below(t, flat, spans):
    """The text below the table, up to where the next table's caption starts (layout)."""
    below = kt.caption_below(t, flat, spans)
    m = NEXT_CAPTION.search(below)
    return below[:m.start()].strip() if m else below


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
    """The duels over the options in both orders; an answer is kept only when both orders give it.
    -> {"choice": label or None (not sure), "orders": [choice in the given order, in the reversed order], "log"}"""
    got, logs = [], []
    for opts in (options, list(reversed(options))):
        i, log = duels.duel(ask, state, question, opts)
        got.append(opts[i][0] if i is not None else None)
        logs.append(log)
    return {"choice": got[0] if got[0] is not None and got[0] == got[1] else None, "orders": got, "log": logs}


def decide(ask, t, above, below):
    state = table_state(t, above, below)
    res = {"rows": node(ask, state, Q_ROWS, ROWS)}
    if res["rows"]["choice"] == "organisms":
        res["how"] = node(ask, state, Q_HOW, HOW)
    elif res["rows"]["choice"] == "variables":
        res["var"] = node(ask, state, Q_VAR, VAR)
    res["purpose"] = node(ask, state, Q_PURPOSE, PURPOSE)
    return res


def leaf(d):
    """The row reading in one word: the deepest sure answer ('not sure' when the first node is not)."""
    top = d["rows"]["choice"]
    sub = (d.get("how") or d.get("var") or {}).get("choice")
    return sub or top or "not sure"


def tuning():
    return sorted(p for p, g in SPLIT.items() if g in ("dev", "held_a"))


def run(papers):
    """One paper at a time, resumable (<run>/table_model_v2/<paper>.json); every table with rows is asked."""
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
                res[str(t.table_index)] = decide(ask, t, sp.caption_above(t, flat, spans), text_below(t, flat, spans))
            f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
            got = ", ".join(f"t{k}:{leaf(d)}/{d['purpose']['choice'] or '?'}" for k, d in res.items())
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
