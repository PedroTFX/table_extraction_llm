"""
head_tree.py — EXPERIMENT: a model reads the HEAD of a table (its first rows, as
written, with the cell spans marked) and decides where the data starts and what
each head cell is. Code only copies text, marks the spans, picks which question
a piece of geometry gets, asks, and puts the words where the answers say; it
decides nothing. Where answers do not fit together, the model is asked again.

Why: code "facts" (where each column's values start, which cells repeat) are
guesses too — if they were certain, the code would be right and no model would
be needed. So the model gets the raw head. Spans stay, because they are written
in the HTML ('Workers' spans 3 columns), not inferred.

    1. rows        Q1 sees WHOLE rows, written compactly: only the filled cells,
                   each with its column number ('c4 0.25 | c8 -0.17'), so a wide
                   table is never judged from part of a row
                   variant A  Q1  for each row: data, part of the head, or neither?
                                  (the head ends at the first row that is not
                                  head; the first 'data' row starts the records)
                              Q1C a 'head' answer after the head ended is asked
                                  again: data or neither?
                   variant B  QF  one question: which row is the first record?
                              QH  the rows above it: part of the head, or neither?
                   both       Q1B a 'neither' row: section label for the rows
                                  below / header repeated / note or total / empty
    2. pieces      only for the cell questions: a head wider than 10 columns is
                   cut into pieces of columns, at the cut that splits the fewest
                   cells; every piece keeps the first column
    3. cells       QC  each head cell: title / group / column name / row label /
                       value / footnote
                   QR  a cell asked in two pieces with two answers: asked once
                       more, choosing between those answers
                   QSPEC  every head cell spanning several columns with head
                       cells under it (geometry, whatever QC said), asked on the
                       whole head; uppers with the same cells under them ('M | V')
                       are asked together: what are the lower labels relative to
                       the label above? column names / specification / together.
                       Its answer replaces QC's for those cells.
                   QS  two or more cells over one column still called column
                       names: which one names the column?
    4. body        rows inside the data with far fewer filled cells than their
                   neighbours (the only trigger code uses: it picks WHAT to ask)
                   -> section name / data with missing cells / note
    5. words back  name = the column name the answers chose; groups = group
                   cells above it; details = specifications under it; values =
                   value cells, under the row label on their left. A column no
                   answer names is marked undecided.

    python head_tree.py Oliveira2022:14 Korosi2022:0 ...      # the frozen version:
        # Q1 variant B, QSPEC options written with the labels -> output/head_tree/nimble_B/
    python head_tree.py --q1 A --spec-abstract [--empty] [--row-label-v2] ...   # the
        # experiments, one switch per run -> output/head_tree/<model>_<A|B>_<switches>/
"""

from __future__ import annotations

import collections
import json
import statistics
import sys
import time
import urllib.request as _rq

import _paths
import column_tree as ct
import header_tree as ht

MODELS = {  # name -> (ollama model, questions per call, client)
    "nimble": ("nimble:9b-q4-gpu", 6, "decision"),
    "tev1": ("tev1:4b", 1, "decision"),
    "gemma": ("gemma4:e2b", 6, "chat"),
}
HEAD_ROWS = 12
MAX_WINDOWS = 3
CHUNK_COLS = 10
CELL_W = (40, 20, 12)              # cell width by state size (smaller when a prompt is too long)
BODY_ASK_MAX = 40
OUT = _paths.OUTPUT / "head_tree"
# experiment switches, one change per run (main: --empty, --spec-labels, --row-label-v2)
EMPTY_STRETCHES = False        # whole-row view also writes the empty stretches: 'c1-11 empty'
SPEC_LITERAL = True            # QSPEC options written with the actual labels (run 3: kept)
ROW_LABEL_V2 = False           # QC: the row label is "a label for this head row"
HEAD_CONTINUE = True           # B: head rows below a non-head row -> ask if the head goes on there
                               #    (experiment 1, kept 2026-10-08: names 134 -> 139/181)
SPEC_TITLE = False             # QSPEC: a 4th option, the label above is a title (tried: unsettled
                               #    11 other tables, Oliveira 0.83 -> 0.35; not kept)
# VERSION 2 (frozen 2026-10-13 by the person: experiments/round2.json, 238/263 tables
# right on their table-by-table check, header_review.py; v1 = step_on.json, 222/263):
SECTION_CELL = True            # QC offers 'section': a label for the block of data rows below it
EMPTY_GROUP_RECHECK = True     # QG: a cell answered 'group' with no head cell under it is asked again
SPEC_STATS = True              # QSPEC 'specification' names statistics as an example (estimate, p...)
QG_SECTION_ALONE = False       # round 3 (not kept): QG offers 'section' only for a cell alone in its row
SPEC_TITLE_STEP = True         # QT before QSPEC (kept 2026-10-08: Uemori captions -> titles): is the spanning cell a title, or a label for the
                               #    columns under it? Only a label goes on to the 3-way QSPEC

# the piece view (cell and body questions): cells in place, separated by ' | '
INTRO = ("The first rows of a table from a scientific paper. Cells are separated by "
         "' | '. [N rows tall: x] and [spans N columns: x] mark a cell covering "
         "several rows or columns; (covered) is a position inside a cell from "
         "above; [continues: x] is a cell that started in columns not shown.")
# the whole-row view (row questions, QSPEC): only the filled cells, numbered
INTRO_ROWS = ("Rows of a table from a scientific paper. The table has {n} columns, c0 to "
              "c{last}. Each row lists only its filled cells, each with its column (c4), "
              "or its columns (c4-6) when it spans several; [N rows tall: x] marks a "
              "cell covering several rows; (covered) is a position inside a cell from a "
              "row above. Columns not listed are empty.")
INTRO_ROWS_EMPTY = INTRO_ROWS.replace("Columns not listed are empty.",
                                      "Empty columns are written as a range: 'c1-11 empty'.")

Q1 = {"data": "a data row: one record of the table",
      "head": "part of the head: a title, column names, group labels, units, or "
              "other information about the columns",
      "neither": "neither: not a record and not about the columns (for example a "
                 "label for the rows below it, a note, or an empty row)"}
# second branch: what a 'neither' row is
Q1B = {"section": "a section label for the data rows below it (it can be the first "
                  "row under the column names)",
       "repeated_header": "the column names repeated",
       "note": "a note, a total, or a footnote",
       "empty": "an empty row"}
# a row answered 'head' after the head already ended: the head is one block at
# the top, so it is asked again without that option
Q1C = {"data": Q1["data"], "neither": Q1["neither"]}
# variant B: one boundary question, then the rows above it
QF = ("Which row is the first data record? A data record is one row representing one "
      "observation or entry of the table; it can contain text, numbers, or both. Do "
      "not choose a row merely because it contains numbers: a section label, a note, "
      "a repeated header, or any other row that is not a record is not a data record. "
      "Choose exactly one row.")
QH = {"head": Q1["head"], "neither": Q1["neither"]}
# head rows found below rows that are not head (a title, then an empty row, then the
# column names): does the column head begin or continue there?
QHC = {"yes": "yes: the column head begins or continues at row {c}",
       "no": "no: rows {c}-{d} are not part of the column head"}
# head CELLS, not rows: one row can hold group labels and column names side by
# side (Korosi2022 row 0: 'Year' over 2 columns next to 2-rows-tall 'Elevation')
QC = {"title": "a title or caption of the whole table",
      "group": "a label over several columns, each with its own column name under it",
      "column": "a column name: what that column holds (it can be several rows tall)",
      "row_label": "a row label: names the values that fill its row to the right, one "
                   "per column; a cell at the left edge is not a row label just "
                   "because it is at the left edge",
      "value": "a value that belongs to a row label on its left, one per column",
      "footnote": "a note about the table or about a cell"}
QC_V2 = {("head_row_label" if k == "row_label" else k):
         ("a label for this head row: it names what the other cells in its row are; "
          "it is not a row label merely because it is at the left edge"
          if k == "row_label" else v) for k, v in QC.items()}
# 'value' points at the renamed label
QC_V2["value"] = "a value that belongs to the label of its head row on its left, one per column"
ROW_LABELS = ("row_label", "head_row_label")


QC_SECTION = ("a section label: it names a block of data rows below it (often one cell "
              "across the whole table), not a column")


def qc_options():
    opts = dict(QC_V2 if ROW_LABEL_V2 else QC)
    if SECTION_CELL:
        opts["section"] = QC_SECTION
    return opts


# a cell spanning several columns over other head cells: what are those cells?
QSPEC = {"column_names": "each lower label names its own column; the label above "
                         "groups them",
         "specification": "the label above names the columns; the lower labels say "
                          "more about it",
         "together": "the label above and each lower label together make one "
                     "column name"}
QB = {"section": "a section label for the data rows below it",
      "data": "a data row with some cells missing",
      "repeated_header": "the column names repeated",
      "note": "a note, a total, or a footnote"}


def _clip(t, n=CELL_W[0]):
    t = " ".join(str(t or "").split())
    return t if len(t) <= n else t[:n - 1] + "…"


def _cell(grid, key):
    r, c = map(int, key.split(","))
    return grid.at(r, c)


# --- the two views -------------------------------------------------------------

def cell_text(grid, r, c, cols, w=CELL_W[0]):
    """Piece view: how one position is written; None = inside a colspan
    already written."""
    x = grid.at(r, c)
    if not x:
        return ""
    if x.r != r:
        return "(covered)"
    if x.c != c:
        i = cols.index(c)
        piece_start = i == 0 or cols[i - 1] != c - 1     # first column after a cut
        if piece_start and x.c < c:                       # started in columns not shown
            n = sum(1 for cc in cols if x.c <= cc < x.c + x.colspan)
            return f"[continues, {n} columns here: {_clip(x.text, w)}]"
        return None
    tags = []
    if x.rowspan > 1:
        tags.append(f"{x.rowspan} rows tall")
    covered = [cc for cc in cols if x.c <= cc < x.c + x.colspan]
    if x.colspan > 1:
        tags.append(f"spans {len(covered)} columns"
                    + (f" of {x.colspan}" if len(covered) < x.colspan else ""))
    t = _clip(x.text, w)
    return f"[{', '.join(tags)}: {t}]" if tags else t


def render_row(grid, r, cols, w=CELL_W[0]):
    parts = [cell_text(grid, r, c, cols, w) for c in cols]
    return " | ".join(p for p in parts if p is not None)


def compact_row(grid, r, w=CELL_W[0]):
    """Whole-row view: only the filled cells, each with its column number(s);
    with EMPTY_STRETCHES the empty columns too, as ranges ('c1-11 empty')."""
    parts, gap = [], []

    def flush():
        if gap:
            parts.append(f"c{gap[0]}" + (f"-{gap[-1]}" if len(gap) > 1 else "") + " empty")
            gap.clear()
    for c in range(grid.ncols):
        x = grid.at(r, c)
        if not x or not str(x.text or "").strip():
            if EMPTY_STRETCHES:
                gap.append(c)
            continue
        if x.c != c:
            continue                                     # inside a colspan already written
        flush()
        cs = f"c{c}" if x.colspan == 1 else f"c{c}-{c + x.colspan - 1}"
        if x.r != r:
            parts.append(f"{cs} (covered)")
        elif x.rowspan > 1:
            parts.append(f"{cs} [{x.rowspan} rows tall: {_clip(x.text, w)}]")
        else:
            parts.append(f"{cs} {_clip(x.text, w)}")
    flush()
    return " | ".join(parts) or "(empty)"


def rows_state(grid, rows, marks=None, tail=""):
    """A state function (cell width -> text) showing whole rows; marks: {row:
    'section'} written next to the row number."""
    marks = marks or {}

    def state(width):
        intro = (INTRO_ROWS_EMPTY if EMPTY_STRETCHES else INTRO_ROWS).format(
            n=grid.ncols, last=grid.ncols - 1)
        lines = [f"row {r}" + (f" ({marks[r]})" if r in marks else "")
                 + f": {compact_row(grid, r, width)}" for r in rows]
        return intro + "\n\n" + "\n".join(lines) + (f"\n\n{tail}" if tail else "")
    return state


def pieces(grid):
    """Column pieces of at most CHUNK_COLS, balanced, each starting with column 0.
    Each cut is placed, near the balanced spot, where it splits the fewest cells
    of the first rows (so 'P' over its M and V stays in one piece)."""
    ncols = grid.ncols
    if ncols <= CHUNK_COLS:
        return [list(range(ncols))]
    top = range(min(grid.nrows, HEAD_ROWS))

    def crossing(c):                                     # cells split by a cut before c
        return len({(x.r, x.c) for r in top for x in [grid.at(r, c)]
                    if x and x.c < c < x.c + x.colspan})

    out, start = [], 1
    while start < ncols:
        rem = ncols - start
        if rem <= CHUNK_COLS - 1:
            out.append(list(range(start, ncols)))
            break
        n = -(-rem // (CHUNK_COLS - 1))
        target = start + -(-rem // n)
        cands = range(max(start + 1, target - 2), min(start + CHUNK_COLS - 1, ncols - 1) + 1)
        cut = min(cands, key=lambda c: (crossing(c), abs(c - target)))
        out.append(list(range(start, cut)))
        start = cut
    return [[0] + p for p in out]


# --- clients -----------------------------------------------------------------

class ChatClient:
    """Asks a model without the decision endpoint (gemma) the same multiple-choice
    questions through chat; a JSON schema allows only the option labels. No
    probabilities; a reply that is not one of the options is asked once more."""

    def __init__(self, model, chunk=6, timeout=600):
        self.model, self.chunk, self.timeout = model, chunk, timeout
        self.calls = 0

    def _post(self, prompt, schema):
        body = {"model": self.model, "stream": False, "format": schema, "think": False,
                "messages": [{"role": "user", "content": prompt}],
                "options": {"temperature": 0, "num_ctx": 8192}}
        req = _rq.Request("http://127.0.0.1:11434/api/chat", data=json.dumps(body).encode(),
                          headers={"Content-Type": "application/json"})
        with _rq.urlopen(req, timeout=self.timeout) as r:
            self.calls += 1
            msg = json.loads(r.read()).get("message", {}).get("content", "")
        try:
            out = json.loads(msg)
            return out if isinstance(out, dict) else {}
        except json.JSONDecodeError:
            return {}

    def _ask_part(self, state, part):
        qs = "\n\n".join(f"{k}: {q['instructions']}\n" + "\n".join(
            f"  - {lab}: {desc}" for lab, desc in q["criteria"].items()) for k, q in part.items())
        prompt = (f"{state}\n\nAnswer each question with exactly one of its option labels.\n\n"
                  f"{qs}\n\nReply with JSON only, one label per question: "
                  + json.dumps({k: "<label>" for k in part}))
        schema = {"type": "object", "required": list(part),     # only the option labels
                  "properties": {k: {"type": "string", "enum": list(q["criteria"])}
                                 for k, q in part.items()}}
        got = self._post(prompt, schema)
        return {k: {"choice": got[k], "probabilities": {}} for k in part
                if isinstance(got.get(k), str) and got[k] in part[k]["criteria"]}

    def ask(self, state_at, questions):
        out, keys = {}, list(questions)
        for i in range(0, len(keys), self.chunk):
            part = {k: questions[k] for k in keys[i:i + self.chunk]}
            got = self._ask_part(state_at(0), part)
            miss = {k: v for k, v in part.items() if k not in got}
            if miss:
                got.update(self._ask_part(state_at(0), miss))
            out.update(got)
        return out


def client_for(name):
    model, chunk, kind = MODELS[name]
    return ct.DecisionClient(model, chunk) if kind == "decision" else ChatClient(model, chunk)


def _ask(client, state, qs):
    """state: text, or a function of the cell width (shrunk when the prompt is
    over the model's limit)."""
    if callable(state):
        return client.ask(lambda size: state(CELL_W[size]), qs)
    return client.ask(lambda size: state, qs)


def _p(a, ch):
    return round(float((a.get("probabilities") or {}).get(ch, 0.0) or 0.0), 3)


# --- rows ----------------------------------------------------------------------

def _second_branch(client, state, out, neither):
    """Q1B for the 'neither' rows."""
    if not neither:
        return
    qs = {f"q{r}": {"type": "choice",
                    "instructions": f"Row {r} is neither a record nor part of the head. "
                                    f"What is it?",
                    "criteria": dict(Q1B)} for r in neither}
    ans = _ask(client, state, qs)
    for r in neither:
        a = ans.get(f"q{r}") or {}
        ch = a.get("choice") or "note"
        out["rows"][r] = [ch, _p(a, ch)] + out["rows"][r][2:]


def first_data_row(grid, client):
    """Variant A. Q1 row by row, top-down, on whole rows; a 'neither' row goes to
    the second branch (Q1B). -> {"row": first data row | None, "p": p(data) there,
    "head_end": first row that is not head, "rows": {row: [answer, p]}}"""
    out = {"row": None, "p": 0.0, "head_end": None, "rows": {}}
    for w in range(MAX_WINDOWS):
        rows = list(range(w * HEAD_ROWS, min(grid.nrows, (w + 1) * HEAD_ROWS)))
        if not rows:
            break
        state = rows_state(grid, list(range(max(0, rows[0] - 2), rows[-1] + 1)))
        qs = {f"q{r}": {"type": "choice",
                        "instructions": f"Row {r}: is it a data row, part of the head, or neither?",
                        "criteria": dict(Q1)} for r in rows}
        ans = _ask(client, state, qs)
        neither, late = [], []
        for r in rows:
            a = ans.get(f"q{r}") or {}
            ch = a.get("choice") or "data"
            p = _p(a, ch)
            out["rows"][r] = [ch, p]
            if ch == "head" and out["head_end"] is not None:
                late.append(r)
                continue
            if ch != "head" and out["head_end"] is None:
                out["head_end"] = r
            if ch == "neither":
                neither.append(r)
            if ch == "data":
                out["row"], out["p"] = r, p
                break
        if late:                                         # head after the head ended
            qs = {f"q{r}": {"type": "choice",
                            "instructions": f"The head ends before row {out['head_end']}. "
                                            f"Row {r}: is it a data row, or neither?",
                            "criteria": dict(Q1C)} for r in late}
            a1c = _ask(client, state, qs)
            for r in late:
                a = a1c.get(f"q{r}") or {}
                ch = a.get("choice") or "data"
                p = _p(a, ch)
                out["rows"][r] = [ch, p, "asked again"]
                if ch == "data" and (out["row"] is None or r < out["row"]):
                    out["row"], out["p"] = r, p
                elif ch == "neither":
                    neither.append(r)
        if out["row"] is not None:                       # nothing after the first record
            neither = [r for r in neither if r < out["row"]]
            for r in [r for r in out["rows"] if r > out["row"]]:
                del out["rows"][r]
        _second_branch(client, state, out, neither)
        if out["row"] is not None:
            break
    if out["head_end"] is None:
        out["head_end"] = out["row"] or 0
    return out


def first_record_one(grid, client):
    """Variant B. QF: one question, which of the first rows is the first record;
    then QH for the rows above it (head or neither) and Q1B for the 'neither'
    ones. A 'head' answer after the head ended goes to Q1B too (the head is one
    block at the top). Same output as first_data_row, plus the QF options."""
    rows = list(range(min(grid.nrows, HEAD_ROWS)))
    state = rows_state(grid, rows)
    qs = {"q": {"type": "choice", "instructions": QF,
                "criteria": {f"row{r}": f"row {r}: " + _clip(compact_row(grid, r, 16), 100)
                             for r in rows}}}
    a = _ask(client, state, qs).get("q") or {}
    ch = a.get("choice")
    probs = sorted((a.get("probabilities") or {}).items(), key=lambda kv: -float(kv[1] or 0))
    out = {"row": None, "p": 0.0, "head_end": None, "rows": {},
           "options": {k: round(float(v or 0), 3) for k, v in probs[:4]}}
    if not ch:
        out["head_end"] = 0
        return out
    start = int(ch[3:])
    out["row"], out["p"] = start, _p(a, ch)
    out["rows"][start] = ["data", out["p"]]
    if start:
        qs = {f"q{r}": {"type": "choice",
                        "instructions": f"Row {r} is above the first data record (row {start}). "
                                        f"Is it part of the head, or neither?",
                        "criteria": dict(QH)} for r in range(start)}
        ans = _ask(client, state, qs)
        neither = []
        for r in range(start):
            x = ans.get(f"q{r}") or {}
            got = x.get("choice") or "neither"
            out["rows"][r] = [got, _p(x, got)]
            if got == "head" and out["head_end"] is None:
                continue                                 # still in the head
            if out["head_end"] is None:
                out["head_end"] = r
            if got == "head":
                out["rows"][r].append("head after the head ended")
            neither.append(r)
        if HEAD_CONTINUE:
            neither = _head_continues(client, state, out, start, neither)
        _second_branch(client, state, out, neither)
    if out["head_end"] is None:
        out["head_end"] = start
    return out


def _head_continues(client, state, out, start, neither):
    """QHC: each run of rows answered 'head' below rows that are not head is asked
    once: does the column head begin or continue there? 'yes' keeps them as head
    (the head then ends after the last of them); 'no' sends them to Q1B."""
    late = [r for r in neither if out["rows"][r][0] == "head"]
    runs = []
    for r in late:
        if runs and r == runs[-1][-1] + 1:
            runs[-1].append(r)
        else:
            runs.append([r])
    if not runs:
        return neither
    qs = {}
    for i, run in enumerate(runs):
        c, d = run[0], run[-1]
        above = [r for r in range(c) if out["rows"][r][0] != "head"
                 or len(out["rows"][r]) > 2]
        qs[f"q{i}"] = {"type": "choice",
                       "instructions": f"Row(s) {', '.join(map(str, above))} above are not part "
                                       f"of the head. Rows {c}-{d} were judged to be part of the "
                                       f"column head. Does the column head begin or continue at "
                                       f"row {c}, after the rows above it?",
                       "criteria": {k: v.format(c=c, d=d) for k, v in QHC.items()}}
    ans = _ask(client, state, qs)
    keep = set()
    for i, run in enumerate(runs):
        a = ans.get(f"q{i}") or {}
        ch = a.get("choice") or "no"
        for r in run:
            out["rows"][r] = ["head", out["rows"][r][1], f"head continues: {ch} ({_p(a, ch)})"]
        if ch == "yes":
            keep |= set(run)
            out["head_end"] = max(out["head_end"], run[-1] + 1)
    return [r for r in neither if r not in keep]


# --- head cells ----------------------------------------------------------------

def head_state(grid, cols, head_end, start, pre):
    """Piece view for the cell questions: the head, then the rows between it and
    the first record with Q1's answer, then the first record."""
    def state(width):
        lines = [f"row {r}: {render_row(grid, r, cols, width)}" for r in range(head_end)]
        lines += [f"row {r} ({pre.get(str(r), ['note'])[0].replace('_', ' ')}): "
                  f"{render_row(grid, r, cols, width)}" for r in range(head_end, start)]
        if start < grid.nrows:
            lines.append(f"row {start} (first record): {render_row(grid, start, cols, width)}")
        return INTRO + "\n\n" + "\n".join(lines) + f"\n\nRows 0-{head_end - 1} are the head."
    return state


def head_cells(grid, cols, client, state, head_end):
    """QC: {"r,c": [role, p]} for every non-empty head cell of one piece (keyed by
    the cell's top-left position). A cell spanning columns or rows is asked once;
    the same text repeated along a row ('M', 'V' under each trait) is asked once."""
    same = {}                                            # (row, text) -> {"r,c"}
    for r in range(head_end):
        for c in cols:
            x = grid.at(r, c)
            if x and str(x.text or "").strip():
                same.setdefault((x.r, _clip(x.text)), set()).add(f"{x.r},{x.c}")
    items = list(same.items())
    qs = {f"q{i}": {"type": "choice",
                    "instructions": f"Row {r}, the cell '{t}': what is it?",
                    "criteria": dict(qc_options())} for i, ((r, t), _k) in enumerate(items)}
    ans = _ask(client, state, qs) if qs else {}
    out = {}
    for i, (_rt, keys) in enumerate(items):
        a = ans.get(f"q{i}") or {}
        ch = a.get("choice")
        for k in keys:
            out[k] = [ch, _p(a, ch)] if ch else ["unanswered", 0.0]
    return out


def reconcile(grid, client, states, cells_by_piece):
    """QR: a cell asked in several pieces with different answers is asked once
    more (in the first piece's view), choosing only between those answers."""
    seen = collections.defaultdict(dict)                 # "r,c" -> {role: p}
    for cells in cells_by_piece:
        for k, (role, p, *_n) in cells.items():
            if role != "unanswered":
                seen[k][role] = max(p, seen[k].get(role, 0))
    clash = {k: roles for k, roles in seen.items() if len(roles) > 1}
    if not clash:
        return {}
    keys = list(clash)
    qs = {f"q{i}": {"type": "choice",
                    "instructions": f"Row {k.split(',')[0]}, the cell "
                                    f"'{_clip(_cell(grid, k).text)}': what is it?",
                    "criteria": {role: qc_options()[role] for role in clash[k]}}
          for i, k in enumerate(keys)}
    ans = _ask(client, states[0], qs)
    out = {}
    for i, k in enumerate(keys):
        a = ans.get(f"q{i}") or {}
        if a.get("choice"):
            out[k] = [a["choice"], _p(a, a["choice"]), "asked again"]
    for cells in cells_by_piece:
        for k, v in out.items():
            if k in cells:
                cells[k] = v
    return out


def _quoted(xs):
    q = [f"'{x}'" for x in xs[:6]]
    if len(xs) > 6:
        return ", ".join(q) + ", …"
    return q[0] if len(q) == 1 else ", ".join(q[:-1]) + " and " + q[-1]


def spec_criteria(ups, labels):
    """The QSPEC options; with SPEC_LITERAL written with the labels themselves,
    as QS does ('WL' names the column; 'M' says more about it)."""
    if not SPEC_LITERAL:
        return dict(QSPEC, **({"title": "the label above is a title or caption of the table, "
                                        "not a label for these columns"} if SPEC_TITLE else {}))
    one = len(ups) == 1
    lows = (f"{_quoted(labels)} names its own column" if len(labels) == 1
            else f"{_quoted(labels)} each name their own column")
    joined = [f"'{u} {l}'" for u in ups[:2] for l in labels[:2]]
    more = ", …" if len(ups) > 2 or len(labels) > 2 else ""
    return {"column_names": f"{lows}; {_quoted(ups)} {'groups' if one else 'group'} them",
            "specification": f"{_quoted(ups)} {'names' if one else 'name'} the columns; "
                             f"{_quoted(labels)} say more about {'it' if one else 'them'}"
                             + (" (for example statistics of it: estimate, SE, t-, z- or p-value)"
                                if SPEC_STATS else ""),
            "together": "each lower label makes one column name with the label above it: "
                        + ", ".join(joined) + more,
            **({"title": f"{_quoted(ups)} {'is a title' if one else 'are titles'} or caption of "
                         f"the table, not a label for {_quoted(labels)}"} if SPEC_TITLE else {})}


def spec_patterns(grid, head_end):
    """QSPEC candidates, from geometry alone: every head cell spanning several
    columns with head cells under it. Its cells-under are those in the first row
    below it that start and end inside its columns. Uppers in the same row whose
    cells-under repeat the same pattern (same texts at the same places: 'M | V')
    are one candidate. -> [{"uppers": [key], "under": {upper: [keys]}, "labels": [text]}]"""
    cells = {}
    for r in range(head_end):
        for c in range(grid.ncols):
            x = grid.at(r, c)
            if x and x.r == r and x.c == c and str(x.text or "").strip():
                cells[f"{r},{c}"] = x
    found = {}
    for k, u in cells.items():
        if u.colspan < 2:
            continue
        under = [x for x in cells.values() if x.r >= u.r + u.rowspan and x.c >= u.c
                 and x.c + x.colspan <= u.c + u.colspan]
        if not under:
            continue
        top = min(x.r for x in under)
        kids = sorted((x for x in under if x.r == top), key=lambda x: x.c)
        pattern = (u.r, tuple((x.r - u.r, x.c - u.c, x.colspan, _clip(x.text)) for x in kids))
        g = found.setdefault(pattern, {"uppers": [], "under": {},
                                       "labels": [_clip(x.text) for x in kids]})
        g["uppers"].append(k)
        g["under"][k] = [f"{x.r},{x.c}" for x in kids]
    return sorted(found.values(), key=lambda g: int(g["uppers"][0].split(",")[0]))


def ask_spec(grid, client, head_end, start, pre, cells_by_piece):
    """QSPEC on the whole head (whole-row view). Applied top-down, so a cell that
    is under one candidate and the upper of another takes its role from the one
    where it is the upper. Its answers replace QC's for those cells.
    -> (records for the report, {lower key: upper key} for 'together')"""
    pats = spec_patterns(grid, head_end)
    if not pats:
        return [], {}
    marks = {r: pre.get(str(r), ["note"])[0].replace("_", " ") for r in range(head_end, start)}
    shown = list(range(min(grid.nrows, start + 1)))
    if start < grid.nrows:
        marks[start] = "first record"
    state = rows_state(grid, shown, marks, tail=f"Rows 0-{head_end - 1} are the head.")
    titles, checks = {}, {}
    if SPEC_TITLE_STEP:                                  # QT: title, or a label for the columns?
        tq = {}
        for i, g in enumerate(pats):
            ups = [_clip(_cell(grid, k).text) for k in g["uppers"]]
            one, lab = len(ups) == 1, _quoted(g["labels"])
            tq[f"q{i}"] = {"type": "choice",
                           "instructions": f"Is {_quoted(ups)} "
                                           f"{'a title or caption' if one else 'titles or captions'} "
                                           f"of the table, or {'a label' if one else 'labels'} for "
                                           f"the columns under {'it' if one else 'them'} ({lab})?",
                           "criteria": {"title": f"{_quoted(ups)} {'is a title' if one else 'are titles'}"
                                                 f" or caption of the table",
                                        "label": f"{_quoted(ups)} {'is a label' if one else 'are labels'}"
                                                 f" for the columns under {'it' if one else 'them'}"}}
        ta = _ask(client, state, tq)
        for i in range(len(pats)):
            a = ta.get(f"q{i}") or {}
            checks[i] = {k: round(float(v or 0), 3) for k, v in (a.get("probabilities") or {}).items()}
            if a.get("choice") == "title":
                titles[i] = _p(a, "title")
    qs = {}
    for i, g in enumerate(pats):
        if i in titles:
            continue
        lab = " | ".join(g["labels"])
        ups = [_clip(_cell(grid, k).text) for k in g["uppers"]]
        if len(ups) == 1:
            ins = (f"'{ups[0]}' is directly above: {lab}. What are these lower labels "
                   f"relative to '{ups[0]}'?")
        else:
            ins = ("Each of these labels is directly above the same labels: "
                   + "; ".join(f"'{u}' → {lab}" for u in ups)
                   + f". What are {lab} relative to the label above?")
        qs[f"q{i}"] = {"type": "choice", "instructions": ins,
                       "criteria": spec_criteria(ups, g["labels"])}
    ans = _ask(client, state, qs) if qs else {}
    before = {}
    for cells in cells_by_piece:
        for k, v in cells.items():
            before.setdefault(k, v[0])
    final, joins, records = {}, {}, []
    for i, g in enumerate(pats):
        a = ans.get(f"q{i}") or {}
        ch = a.get("choice")
        p = _p(a, ch) if ch else 0.0
        if i in titles:                                  # QT said title: no QSPEC question
            ch, p = "title", titles[i]
        lower = [k for ks in g["under"].values() for k in ks]
        records.append({"uppers": [_cell(grid, k).text for k in g["uppers"]],
                        "upper_keys": g["uppers"],
                        "labels": g["labels"], "answer": ch, "p": p,
                        "probs": {k: round(float(v or 0), 3)
                                  for k, v in (a.get("probabilities") or {}).items()},
                        "qc_before": {k: before.get(k, "?") for k in g["uppers"] + lower},
                        **({"title_check": checks[i]} if i in checks else {})})
        if not ch:
            continue
        for u, kids in g["under"].items():
            if ch == "column_names":
                final[u] = ["group", p, "QSPEC"]
                final.update({k: ["column", p, "QSPEC"] for k in kids})
            elif ch == "specification":
                final[u] = ["column", p, "QSPEC"]
                final.update({k: ["specification", p, "QSPEC"] for k in kids})
            elif ch == "title":                          # only the upper cell: the cells
                final[u] = ["title", p, "QSPEC"]         # under it keep their QC answers
            else:                                        # together
                final[u] = ["joined", p, "QSPEC"]
                final.update({k: ["column", p, "QSPEC"] for k in kids})
                joins.update({k: u for k in kids})
    for cells in cells_by_piece:
        for k, v in final.items():
            if k in cells:
                cells[k] = v
    return records, joins


def empty_groups(grid, client, state, cells_by_piece, head_end):
    """QG: a cell answered 'group' that has no head cell under it inside its columns
    (Graf 'Landscape Predictors', Gossner 'Europe', both in the last head row) is asked
    again, told that nothing sits under it. The model decides; code only sees the
    geometry. -> {key: [role, p, "QG"]}"""
    keys = {}
    for cells in cells_by_piece:
        for k, (role, *_r) in cells.items():
            if role != "group" or k in keys:
                continue
            x = _cell(grid, k)
            below = any(grid.at(r, c) and str(grid.at(r, c).text or "").strip()
                        and grid.at(r, c).r > x.r
                        for r in range(x.r + x.rowspan, head_end)
                        for c in range(x.c, x.c + x.colspan))
            if not below:
                keys[k] = x
    if not keys:
        return {}
    opts = qc_options()

    def alone(x):                                        # no other text in its row
        return not any(grid.at(x.r, c) and grid.at(x.r, c) is not x
                       and str(grid.at(x.r, c).text or "").strip() for c in range(grid.ncols))
    # QG_SECTION_ALONE (round 3, not kept): 'section' only for a cell alone in its row —
    # fixed Derhe 'Global model', Graf 'Areas', Odanaka 'Landscape' as the notes ask, but
    # a full re-run also changed 12 right tables through nimble's drift between loads
    items = list(keys.items())
    qs = {f"q{i}": {"type": "choice",
                    "instructions": f"Row {x.r}, the cell '{_clip(x.text)}' was called a label over "
                                    f"several columns, but no head cell sits under it. What is it?",
                    "criteria": {r: opts[r] for r in ("column", "title", "section", "footnote")
                                 if r in opts and (r != "section" or not QG_SECTION_ALONE
                                                   or alone(x))}}
          for i, (_k, x) in enumerate(items)}
    ans = _ask(client, state, qs)
    out = {}
    for i, (k, _x) in enumerate(items):
        a = ans.get(f"q{i}") or {}
        if a.get("choice"):
            out[k] = [a["choice"], _p(a, a["choice"]), "QG"]
    for cells in cells_by_piece:
        for k, v in out.items():
            if k in cells:
                cells[k] = v
    return out


def _stack(grid, c, cells, head_end):
    """The head cells over column c that have answers, top-down, each once."""
    out, seen = [], set()
    for r in range(head_end):
        x = grid.at(r, c)
        k = x and f"{x.r},{x.c}"
        if k and k in cells and k not in seen:
            seen.add(k)
            out.append((k, x, cells[k][0]))
    return out


def stacked_names(grid, cols, client, state, cells, head_end, known=None):
    """QS: where two or more cells over one column are still all called column
    names, ask which one names the column. -> {"k1|k2": [choice, p]}
    known: answers already given (an earlier round); only new stacks are asked."""
    todo = {}
    for c in cols:
        named = [(k, x) for k, x, role in _stack(grid, c, cells, head_end) if role == "column"]
        if len(named) > 1:
            todo["|".join(k for k, _x in named)] = named
    if known:
        todo = {k: v for k, v in todo.items() if k not in known}
    if not todo:
        return dict(known or {})
    keys = list(todo)
    qs = {}
    for i, key in enumerate(keys):
        named = todo[key]
        texts = [_clip(x.text) for _k, x in named]
        together = {"together": "together they make one name: '" + " ".join(texts) + "'"}
        if len(named) == 2:
            (u, l), (ru, rl) = texts, (named[0][1].r, named[1][1].r)
            crit = {"upper": f"'{u}' names the column; '{l}' says more about it",
                    "lower": f"'{l}' names the column; '{u}' groups it with other columns",
                    **together}
            ins = (f"Two labels stacked over one column were both called column names: "
                   f"'{u}' (row {ru}) above '{l}' (row {rl}). Which one names the column?")
        else:
            crit = {f"c{j}": f"'{t}' names the column" for j, t in enumerate(texts)}
            crit.update(together)
            ins = ("Labels stacked over one column were all called column names: "
                   + ", ".join(f"'{t}' (row {x.r})" for t, (_k, x) in zip(texts, named))
                   + ". Which one names the column?")
        qs[f"q{i}"] = {"type": "choice", "instructions": ins, "criteria": crit}
    ans = _ask(client, state, qs)
    out = {}
    for i, key in enumerate(keys):
        a = ans.get(f"q{i}") or {}
        if a.get("choice"):
            out[key] = [a["choice"], _p(a, a["choice"])]
    return {**(known or {}), **out}


def columns_from_cells(grid, cols, cells, stacked, joins, head_end, block=0):
    """Put the words where the answers say:
      name     the one cell called column name; when several were stacked, the
               one QS chose ('upper'/'lower'/'cN'), or all of them 'together';
               a name QSPEC joined to the label above it is written after it
      groups   group cells above the name, and stacked names above it
      details  specifications, and stacked names below the chosen name
      values   value cells, under the row label on their left in the same row
    A column no answer names is 'undecided'."""
    out = []
    for c in cols:
        stack = _stack(grid, c, cells, head_end)
        named = [(k, x) for k, x, role in stack if role == "column"]
        name_key, name_cell, name, details, above_named, undecided = None, None, "", [], [], False
        decided_by = "QS" if len(named) > 1 else None
        if len(named) == 1:
            name_key, name_cell = named[0]
        elif len(named) > 1:
            ch = (stacked.get("|".join(k for k, _x in named)) or [None])[0]
            idx = {"upper": 0, "lower": len(named) - 1}.get(ch)
            if ch and ch.startswith("c") and ch[1:].isdigit():
                idx = int(ch[1:])
            if ch == "together":
                name = " ".join(x.text for _k, x in named)
                name_key, name_cell = named[0]           # groups: what sits above them all
            elif idx is not None and idx < len(named):
                name_key, name_cell = named[idx]
                above_named = [x.text for _k, x in named[:idx]]
                details = [x.text for _k, x in named[idx + 1:]]
            else:
                undecided = True
        else:
            undecided = True
        if decided_by is None and name_key is not None:
            decided_by = "QSPEC" if cells[name_key][2:3] == ["QSPEC"] else "QC"
        if name_cell is not None and not name:
            name = name_cell.text
            if name_key in joins:                        # QSPEC 'together'
                name = f"{_cell(grid, joins[name_key]).text} {name}"
        top = name_cell.r if name_cell is not None else head_end
        groups = []
        for _k, x, role in stack:
            if role == "group" and x.r < top and x.text not in groups:
                groups.append(x.text)
        groups += [t for t in above_named if t not in groups]
        details += [x.text for _k, x, role in stack if role == "specification"]
        values = {}
        for _k, x, role in stack:
            if role != "value":
                continue
            label = next((grid.at(x.r, cc).text for cc in range(c - 1, -1, -1)
                          if grid.at(x.r, cc) and cells.get(f"{grid.at(x.r, cc).r},"
                                                            f"{grid.at(x.r, cc).c}",
                                                            [None])[0] in ROW_LABELS),
                         f"row {x.r}")
            values[label] = x.text
        out.append({"col": c, "block": block, "name": name, "groups": groups,
                    "details": details, "values": values, "undecided": undecided,
                    "decided_by": "undecided" if undecided else decided_by,
                    "row_label_over": any(role in ROW_LABELS for _k, _x, role in stack)})
    return out


# --- body ----------------------------------------------------------------------

def body_rows(grid, cols, client, start):
    """{row: (role, p)} for the data rows that fill far fewer cells than usual."""
    filled = {r: sum(1 for c in range(grid.ncols) if grid.origin(r, c) and grid.origin(r, c).text)
              for r in range(start, grid.nrows)}
    if not filled:
        return {}
    med = statistics.median(filled.values())
    odd = [r for r, n in filled.items() if 0 < n <= max(1, 0.4 * med) and med >= 2][:BODY_ASK_MAX]
    out = {}
    for i in range(0, len(odd), 6):
        part = odd[i:i + 6]

        def state(width, part=part):
            blocks = []
            for r in part:
                ctx = range(max(start, r - 2), min(grid.nrows, r + 3))
                blocks.append("\n".join(f"{'>>' if rr == r else '  '} row {rr}: "
                                        f"{render_row(grid, rr, cols, width)}" for rr in ctx))
            return INTRO + "\n\nRows inside the data, each shown with its neighbours:\n\n" \
                + "\n\n".join(blocks)
        qs = {f"q{r}": {"type": "choice", "instructions": f"Row {r} (marked >>) has few "
                                                          f"filled cells. What is it?",
                        "criteria": dict(QB)} for r in part}
        ans = _ask(client, state, qs)
        for r in part:
            a = ans.get(f"q{r}") or {}
            ch = a.get("choice") or "data"
            out[r] = (ch, _p(a, ch))
    return out


# --- one table -----------------------------------------------------------------

def read_table(grid, client, variant="B", body=True):
    t0 = time.time()
    calls0 = client.calls
    q1 = first_data_row(grid, client) if variant == "A" else first_record_one(grid, client)
    start = q1["row"] if q1["row"] is not None else 0
    head_end = min(q1["head_end"], start)
    # rows between the head and the first record: their second-branch category
    pre = {str(r): q1["rows"].get(r, ["note", 0]) for r in range(head_end, start)}
    ps = pieces(grid)
    states = [head_state(grid, cols, head_end, start, pre) for cols in ps]
    cells_by_piece = [head_cells(grid, cols, client, st, head_end) if head_end else {}
                      for cols, st in zip(ps, states)]
    asked_again = reconcile(grid, client, states, cells_by_piece) if len(ps) > 1 else {}
    spec, joins = ask_spec(grid, client, head_end, start, pre, cells_by_piece) if head_end \
        else ([], {})
    regrouped = empty_groups(grid, client, states[0], cells_by_piece, head_end) \
        if head_end and EMPTY_GROUP_RECHECK else {}
    stacked_by_piece, columns = [], []
    for i, (cols, st, cells) in enumerate(zip(ps, states, cells_by_piece)):
        stacked = stacked_names(grid, cols, client, st, cells, head_end) if head_end else {}
        stacked_by_piece.append(stacked)
        cs = columns_from_cells(grid, cols, cells, stacked, joins, head_end, block=i)
        columns += [c for c in cs if i == 0 or c["col"] != 0]
    # the head starts at the first row holding a group or a column name
    labelled = [int(k.split(",")[0]) for cl in cells_by_piece for k, (role, *_r) in cl.items()
                if role in ("group", "column", "joined")]
    head_start = min(labelled) if labelled else 0
    body = body_rows(grid, ps[0], client, start) if body else {}
    return {"variant": variant, "start": start, "head_start": head_start, "head_end": head_end,
            "pre": pre, "q1": {"p": q1["p"], "rows": {str(k): v for k, v in q1["rows"].items()},
                               "options": q1.get("options", {})},
            "pieces": ps, "cells": cells_by_piece, "asked_again": asked_again,
            "spec": spec, "joins": joins, "stacked": stacked_by_piece, "regrouped": regrouped,
            "sections": sorted({_cell(grid, k).text for cl in cells_by_piece
                                for k, (role, *_r) in cl.items() if role == "section"}),
            "body": {str(r): [ro, round(p, 3)] for r, (ro, p) in body.items()},
            "columns": columns, "calls": client.calls - calls0,
            "secs": round(time.time() - t0, 1)}


def main(argv):
    import header_tree_bench as hb
    import head_view
    name, variant, tags = "nimble", "B", []
    switches = {"--empty": ("EMPTY_STRETCHES", True), "--spec-abstract": ("SPEC_LITERAL", False),
                "--row-label-v2": ("ROW_LABEL_V2", True), "--head-continue": ("HEAD_CONTINUE", True),
                "--spec-title": ("SPEC_TITLE", True), "--title-step": ("SPEC_TITLE_STEP", True),
                "--no-head-continue": ("HEAD_CONTINUE", False)}
    while argv[:1] and argv[0].startswith("--"):
        if argv[0] in switches:
            flag, value = switches[argv[0]]
            globals()[flag] = value
            tags.append(argv[0][2:])
            argv = argv[1:]
            continue
        if argv[0] == "--model":
            name = argv[1]
        elif argv[0] == "--q1":
            variant = argv[1].upper()
        elif argv[0] == "--tag":
            tags.append(argv[1])
        argv = argv[2:]
    out = OUT / "_".join([name, variant] + tags)
    out.mkdir(parents=True, exist_ok=True)
    client = client_for(name)
    old = out / "results.json"                           # a re-run of some tables keeps the rest
    results = json.loads(old.read_text(encoding="utf-8")) if old.exists() else {}
    for spec in argv:
        paper, k = spec.split(":")
        grid = ht.grid_from_html(hb.html_tables(paper)[int(k)])
        print(f"=== {paper} #{k} ({grid.nrows}x{grid.ncols})", flush=True)
        r = read_table(grid, client, variant)
        r.update(paper=paper, table=int(k), model=MODELS[name][0])
        results[spec] = r
        print(f"  first record row {r['start']}, head rows {r['head_start']}-{r['head_end'] - 1}, "
              f"{r['calls']} calls, {r['secs']}s", flush=True)
        old.write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    head_view.write(results, out / "report.html", f"{MODELS[name][0]}, Q1 variant {variant}"
                    + "".join(f" + {t}" for t in tags))
    print(f"-> {out / 'report.html'}")


if __name__ == "__main__":
    main(sys.argv[1:])
