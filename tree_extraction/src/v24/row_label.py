"""Trait names completed from the table around them (v24; tree_extraction/plans/02_names_from_context.md, 2026-11-10).
A cell's meaning is often split over the row label, the column and the caption, and we took only the column:
  rows I, II, III, IV x columns F, P, T, Mt     every row gave 'F' = 1.13: the row label is part of the name
  rows 1-4, then 'Mean', 'SD'                   the last rows are statistics of the column, not single measurements
  caption '... of <species> <object>'           columns 'Width', 'Length': the measured object belongs to the name

  code        the label column: the first column that is not the organisms' and not a row field (sex, place, ...),
              printed left of a trait column, its cells short. A table whose rows have organisms of their own is a
              candidate only when the labels repeat (few labels, many rows); a table of one organism (an account's
              table, a paper's one species) always. Long tables and the subject step's tables (v13) are left out.
  Q-ROWLABEL  what the labels stand for: organisms / parts that complete the column's name / statistics of the
              rows / record numbers / something else. An acting answer (parts, statistics) must be sure in both
              option orders. Not sure for the column: each label asked on its own ('1', '2', 'Mean', 'SD').
  Q-HEADER    (parts, the label column has a printed header) is a label complete by itself, or only with its header?
  Q-OBJECT    (every trait column's name is one word, text printed above the table) do the columns measure the organism
              itself, or a structure or object the text above names? Sure 'object' in both orders: the words of that
              text meet in duels, the one left against 'none'.
  apply       parts: the row's trait names become '<label> <column>' ('<header> <label> <column>' when Q-HEADER says
              so); statistics: the label goes to measurementStatistic of the row; the object goes before every name.
              A label column that was read as a trait column gives no rows of its own. Anything not sure: no change.

    python full_run_v24.py v24:rowlabel <papers>     writes <run>/row_label/<paper>.json
"""
import copy
import json
import re
import time

import decoder_v3 as v3
import duels
import full_run as fr
import kind_tree as kt
import species_tree as sp

MAX_LABEL = 40           # characters of a label
MAX_ASKED = 12           # labels asked one by one, and labels shown
MAX_WORDS = 8            # words of the text above the table offered as the measured object
PLACEHOLDER = re.compile(r"^\(no name, column \d+\)$")
COPY = re.compile(r"\s#\d+$")
BRACKET = re.compile(r"\s*[\(\[][^)\]]*[\)\]]")
ACT = ("parts", "statistics")
# function words only (no word of any field of study): never offered as the measured object
STOP = {"the", "and", "for", "from", "with", "per", "this", "that", "these", "those", "each", "were", "was", "are",
        "been", "have", "has", "their", "its", "between", "among", "within", "different", "other", "given", "shown",
        "table", "values", "value", "data", "mean", "means", "number", "numbers", "measurements", "measurement",
        "measured", "species", "specimens", "individuals", "study", "based", "using", "also", "which", "where", "when"}

Q_ROW = "What do the labels in the column '{col}' stand for?"
ROW = {"organisms": "organisms: each label names a different organism, specimen, sex, caste, population or other group "
                    "that was measured",
       "parts": "parts: each label names a part, structure, position or item of the organism; the other columns say "
                "what was measured on it, so a label and a column together name one measurement",
       "statistics": "statistics: the labels name summary statistics of the measurements (such as a mean, a standard "
                     "deviation, a minimum, a maximum, a range or a sample size)",
       "numbers": "numbers: the labels only number or identify the rows (specimen, record or sample numbers)",
       "other": "something else: conditions, treatments, sites, dates, or the categories of a trait"}
Q_ONE = "In the column '{col}', what does the label '{lab}' stand for?"
ONE = {"organisms": "an organism, specimen, sex, caste, population or other group that was measured",
       "parts": "a part, structure, position or item of the organism; with a column's name it names one measurement",
       "statistics": "a summary statistic of the other rows (such as a mean, a standard deviation, a minimum, a "
                     "maximum, a range or a sample size)",
       "numbers": "a number or identifier of the row (a specimen, record or sample number)",
       "other": "something else: a condition, treatment, site, date, or a category of a trait"}
Q_HEAD = "The labels of the column '{col}' name parts or items. How should one of them be written in a trait's name?"
HEAD = {"with": "with the column's header: '{col} {lab}' (the label alone is a number, a letter or a code and does "
                "not say what it is)",
        "alone": "alone: '{lab}' (the label says by itself what it is; '{col}' is only a general word for the column)"}
Q_OBJ = "What was measured to give the values in the columns {cols}?"
OBJ = {"whole": "the organism itself: each column is a measurement or a property of the whole organism, or the "
                "column's name says by itself what was measured",
       "object": "a structure, a product or an object that the text above the table names (not the whole organism): "
                 "each column is a dimension, a count or a property of it",
       "other": "something else, or the text does not say"}
Q_WORD = "Which of these two does the text above the table name as the thing that was measured?"
Q_YES = "Are the values in the columns {cols} measurements of the '{w}' named in the text above the table?"
YES = {"yes": "yes: the columns give dimensions, counts or properties of the {w}",
       "none": "no: '{w}' is not what the columns measure (the organism itself is, or the text does not say)"}


def _flat(s):
    return " ".join(str(s or "").split())


def _label(v):
    return _flat(v).rstrip(":").strip()


def _reversed(crit):
    return dict(reversed(list(crit.items())))


def both(ask, state, q, crit, key):
    """The answer `key` sure in both option orders -> (True / False, [the two answers])."""
    log = []
    for c in (crit, _reversed(crit)):
        ch, probs = ask(state, q, c)
        log.append({"choice": ch, "probs": probs})
        if duels.sure(ch, probs, key) != key:
            return False, log
    return True, log


def label_column(t, fields, org):
    """-> (column, distinct labels, own) or None. own: the rows have organisms of their own (several names)."""
    traits = [c for c in t.columns if fields.get(c.name) in fr.TRAITS]
    names = [c for c in traits if fields.get(c.name) == "measurementType"]
    values = [c for c in traits if fields.get(c.name) == "measurementValue"]
    if not traits or (names and values) or len(t.records) < 2:
        return None
    species = [_flat(fr.species_of(t, fields, org, r)) for r in t.records]
    if not any(species):
        return None
    own = len({s for s in species if s}) > 1 and not getattr(t, "account_species", "")
    for c in t.columns:
        tag = fields.get(c.name)
        if tag in fr.ROW_FIELDS:
            continue
        cells = [_label(r.get(c.name)) for r in t.records]
        if sum(bool(x) and (x == s or x.lower() in s.lower().split()) for x, s in zip(cells, species)) \
                >= 0.5 * len(cells):
            continue                                   # the organisms' column (or its genus)
        right = [x for x in traits if x.index > c.index]
        filled = [x for x in cells if x]
        if not right or len(filled) < max(2, 0.6 * len(cells)) or any(len(x) > MAX_LABEL for x in filled):
            return None
        if tag in fr.TRAITS and sum(bool(re.search(r"\d", x)) for x in filled) > 0.5 * len(filled):
            return None                                # a column of measured values, not of labels
        labels = list(dict.fromkeys(filled))
        if own and (len(labels) > MAX_ASKED or 2 * len(labels) > len(filled)):
            return None                                # one label per organism row: nothing repeats
        return c, labels, own
    return None


def state_of(t, col, labels, above):
    s = f"A table in a scientific paper has the columns {[c.name for c in t.columns][:14]}."
    if above:
        s += f" The text printed directly above it: '{above}'."
    s += f" Its first rows read: {kt._shown(t, 4)}."
    acc = getattr(t, "account_species", "")
    if acc:
        s += f" The table is printed inside the account of {acc} and has no column naming the organism."
    shown = ", ".join(f"'{x}'" for x in labels[:MAX_ASKED])
    return s + f" The column '{col.name}' holds the row labels {shown}" + (" and others." if len(labels) > MAX_ASKED else ".")


def decide_labels(ask, t, col, labels, above):
    rec = {"column": col.name, "labels": labels[:60], "roles": {}, "header": None}
    state = state_of(t, col, labels, above)
    q = Q_ROW.format(col=col.name)
    ch, probs = ask(state, q, dict(ROW))
    rec["whole"] = {"choice": ch, "probs": probs}
    whole = duels.sure(ch, probs, *ROW)
    if whole in ACT:
        ok, log = both(ask, state, q, ROW, whole)
        rec["whole"]["both"] = log
        if ok:
            rec["roles"] = {x: whole for x in labels}
    elif whole is None and len(labels) <= MAX_ASKED:    # mixed: '1', '2', 'Mean', 'SD'
        rec["each"] = {}
        for lab in labels:
            n = sum(_label(r.get(col.name)) == lab for r in t.records)
            st = state + f" The label '{lab}' is printed in {n} row(s)."
            q1 = Q_ONE.format(col=col.name, lab=lab)
            c1, p1 = ask(st, q1, dict(ONE))
            one = {"choice": c1, "probs": p1}
            got = duels.sure(c1, p1, *ACT)
            if got:
                ok, one["both"] = both(ask, st, q1, ONE, got)
                if ok:
                    rec["roles"][lab] = got
            rec["each"][lab] = one
    parts = [x for x, r in rec["roles"].items() if r == "parts"]
    head = COPY.sub("", col.name)
    if parts and not PLACEHOLDER.match(head):
        crit = {k: v.format(col=head, lab=parts[0]) for k, v in HEAD.items()}
        ok, log = both(ask, state, Q_HEAD.format(col=col.name), crit, "with")
        rec["header"] = {"with": ok, "asked": log, "text": head}
    return rec


def one_word_columns(t, fields):
    """The trait columns of a wide table when every one's printed name is a single word (brackets set aside)."""
    traits = [c for c in t.columns if fields.get(c.name) in fr.TRAITS]
    if not traits or any(fields.get(c.name) == "measurementValue" for c in traits):
        return []
    bare = [BRACKET.sub("", COPY.sub("", c.name)).strip() for c in traits]
    return traits if all(b and len(b.split()) == 1 for b in bare) else []


def object_words(above, t):
    """Words of the text above the table that may name the measured object (layout only): lower-case words of four
    letters or more, not a function word, not printed right after a capitalised word (an epithet after its genus),
    not a column's name."""
    cols = {BRACKET.sub("", c.name).strip().lower() for c in t.columns}
    out, prev = [], ""
    for w in re.findall(r"[^\W\d_]+", above):
        if len(w) >= 4 and w.islower() and w not in STOP and w not in cols and not (prev[:1].isupper() and len(prev) > 2) \
                and w not in out:
            out.append(w)
        prev = w
    return out[-MAX_WORDS:]                              # the caption ends the text above the table


def decide_object(ask, t, cols, above):
    names = [c.name for c in cols][:10]
    state = (f"A table in a scientific paper has the columns {[c.name for c in t.columns][:14]}. The text printed "
             f"directly above it: '{above}'. Its first rows read: {kt._shown(t, 3)}.")
    q = Q_OBJ.format(cols=names)
    ok, log = both(ask, state, q, OBJ, "object")
    rec = {"asked": log, "object": None}
    words = object_words(above, t) if ok else []
    if not words:
        return rec
    held, duel_log = duels.duel(ask, state, Q_WORD, [(w, f"'{w}'") for w in words])
    rec.update(words=words, duels=duel_log)
    if held is None:
        return rec
    w = words[held]
    ch, probs = ask(state, Q_YES.format(cols=names, w=w), {k: v.format(w=w) for k, v in YES.items()})
    rec["final"] = {"word": w, "choice": ch, "probs": probs}
    if duels.sure(ch, probs, "yes"):
        rec["object"] = w
    return rec


def run(run_dir, papers, skip=lambda p: set()):
    """One paper at a time; resumable (run_dir/row_label/<paper>.json). skip(paper): tables another step reads row by
    row (v13's tables of the paper's one subject): asked Q-OBJECT only. The tables are the ones full_run.plan gives."""
    out = run_dir / "row_label"
    out.mkdir(parents=True, exist_ok=True)
    head = fr.head_runs()
    ask = duels.Nimble()
    for p in papers:
        f = out / f"{p}.json"
        if f.exists() or p not in head:
            continue
        t0, res, seen = time.time(), {}, set()
        flat, spans = v3.md_tables(p)
        left = skip(p)
        for t, fields, org, _x in fr.plan(p, head):
            k = str(t.table_index)
            if k in seen or not t.records:
                continue
            seen.add(k)
            rec = {}
            above = sp.caption_above(t, flat, spans)
            got = None if t.table_index in left else label_column(t, fields, org)   # the subject step reads those rows
            if got:
                col, labels, own = got
                rec["labels"] = dict(decide_labels(ask, t, col, labels, above), own=own)
            cols = one_word_columns(t, fields)
            if cols and above and any(fr.species_of(t, fields, org, r) for r in t.records):
                rec["object"] = decide_object(ask, t, cols, above)
            if rec:
                res[k] = rec
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        n_l = sum(bool((r.get("labels") or {}).get("roles")) for r in res.values())
        n_o = sum(bool((r.get("object") or {}).get("object")) for r in res.values())
        print(f"  [rowlabel] {p:22s} {len(res)} tables asked; row labels used in {n_l}, a measured object in {n_o} "
              f"({time.time() - t0:.0f}s)", flush=True)
    ask.unload()


def apply(dec, out):
    """plan()'s list with, on the tables the answers act on: rec['_part'] (the words put before the row's trait
    names), rec['_stat'] (the row's statistic), t.caption_object (put before every trait name); a label column that
    was tagged a trait column gives no rows of its own."""
    if not dec:
        return out
    res = []
    for t, fields, org, x in out:
        d = dec.get(str(t.table_index)) or {}
        lab = d.get("labels") or {}
        roles = lab.get("roles") or {}
        obj = (d.get("object") or {}).get("object")
        if roles or obj:
            t = copy.copy(t)
        if obj:
            t.caption_object = obj
        if roles and lab.get("column") in {c.name for c in t.columns}:
            col = lab["column"]
            head = (lab.get("header") or {})
            pre = f"{head['text']} " if head.get("with") else ""
            t.records = [dict(r) for r in t.records]
            for r in t.records:
                v = _label(r.get(col))
                if roles.get(v) == "parts":
                    r["_part"] = pre + v
                elif roles.get(v) == "statistics":
                    r["_stat"] = v
            if fields.get(col) in fr.TRAITS:
                fields = dict(fields, **{col: "none"})
        res.append((t, fields, org, x))
    return res
