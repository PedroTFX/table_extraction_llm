"""
header_tree.py — EXPERIMENT: decide a table's LAYOUT (which rows are header,
groups, captions, sections, data; side-by-side blocks) from its FORMAT only, then
put the words back.

Why format only: a header decided by reading the words mixes up a categorical
table, where 'Larval diet' (header) and 'POLLENIVOROUS' (data) are both words.
In format they differ: a label appears once in its column, a category repeats.
So every cell is first replaced by a SYMBOL of its shape, every layout decision
is made on the symbols, and only then are the texts attached to the result.

    symbols   N number · N± mean±spread · N–N range · Y year · L Latin-name shape ·
              C word that repeats in its column · U word that appears once ·
              X long text · STAT statistic word (Mean, SD, n, CV) · UNIT unit ·
              CAP caption ('Table 2. ...') · '·' empty
    spans     [↓k] cell spans k rows, [→k] spans k columns (from the HTML),
              '^' position covered by a rowspan from above, '=' text repeats
              elsewhere in the same row (sub-headers under groups)

STAT, UNIT, CAP and the Latin-name shape are word CLASSES that describe a cell's
role in the format (a statistic, a unit, a caption, a name); no biological
meaning is read.

The tree (node = code check or model question):
  blocks        (code)  split side-by-side blocks at empty columns
  data_start    (code)  every column votes where its values start; the rows
                        above are the header. A weak vote goes to the model:
  ask_data_start(model) on the symbol grid only: which row is the first record?
                        (mode='model': the model answers this, each header row's
                        role and each one-cell body row; code only splits blocks
                        and finds repeated headers)
  header_rows   (code)  role of each header row: caption | group | names |
                        values (one value per column, e.g. the year a site was
                        planted) | units | empty
  body_rows     (code)  data | section (one label splitting the body) |
                        repeated_header
  words back    (code)  per column: name, groups above it, header values, unit;
                        per record: its section label

Not used by the pipeline yet. header_tree_bench.py scores it against the GT.
"""

from __future__ import annotations

import collections
import html as _html
import re
from dataclasses import dataclass, field

import _paths  # noqa: F401  (pipeline on the import path)
from text_manager import latex_cell_to_text, strip_html_markup

import column_tree as ct      # DecisionClient, peel, number shapes, Latin-name test

# --- 1. HTML -> grid that keeps the spans -------------------------------------------

_TR_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S | re.I)
_CELL_RE = re.compile(r"<(td|th)([^>]*)>(.*?)</(?:td|th)>", re.S | re.I)
_SPAN_RE = {"row": re.compile(r'rowspan\s*=\s*["\']?(\d+)', re.I),
            "col": re.compile(r'colspan\s*=\s*["\']?(\d+)', re.I)}


@dataclass
class Cell:
    text: str
    r: int                 # origin row
    c: int                 # origin column
    rowspan: int = 1
    colspan: int = 1


@dataclass
class Grid:
    cells: dict            # (r, c) -> Cell covering that position
    nrows: int
    ncols: int
    html: str = ""

    def at(self, r, c):
        return self.cells.get((r, c))

    def origin(self, r, c):
        """The cell whose top-left corner is (r, c), else None."""
        x = self.cells.get((r, c))
        return x if x and x.r == r and x.c == c else None

    def text(self, r, c):
        x = self.cells.get((r, c))
        return x.text if x else ""


def _clean(inner: str) -> str:
    t = re.sub(r"\s+", " ", inner).strip()
    t = latex_cell_to_text(t)
    t = strip_html_markup(t)
    return re.sub(r"\s+", " ", _html.unescape(t)).replace("\xa0", " ").strip()


def grid_from_html(table_html: str) -> Grid:
    cells, nrows, ncols = {}, 0, 0
    for r, row in enumerate(_TR_RE.findall(table_html)):
        nrows = r + 1
        c = 0
        for _tag, attrs, inner in _CELL_RE.findall(row):
            while (r, c) in cells:              # skip positions a rowspan covers
                c += 1
            rs = int((_SPAN_RE["row"].search(attrs) or [0, 1])[1] or 1)
            cs = int((_SPAN_RE["col"].search(attrs) or [0, 1])[1] or 1)
            cell = Cell(_clean(inner), r, c, max(1, rs), max(1, cs))
            for dr in range(cell.rowspan):
                for dc in range(cell.colspan):
                    cells[(r + dr, c + dc)] = cell
            c += cell.colspan
            ncols = max(ncols, c)
    nrows = max([nrows] + [r + 1 for (r, _c) in cells])
    return Grid(cells, nrows, ncols, table_html)


# --- 2. symbols ------------------------------------------------------------------------

NUMERIC = {"N", "N±", "N–N", "Y"}
_YEAR = re.compile(r"^(1[7-9]\d\d|20\d\d)(\.0)?$")
_CAP = re.compile(r"^\s*(table|tab\.|appendix|supplementary|fig\.?|figure)\s*[s]?\d", re.I)
_STAT_ONLY = re.compile(r"^\(?\s*(n|no\.?|n\s*=?)\s*\)?$")
_UNITS = {"mm", "cm", "m", "km", "µm", "um", "nm", "mg", "g", "kg", "µg", "ml", "µl",
          "%", "°c", "ºc", "days", "day", "d", "h", "hr", "hrs", "min", "s", "yr",
          "yrs", "years", "ha", "m2", "m²", "mm2", "mm²", "mm3", "mm³"}
_REF = re.compile(r"\s*\[[^\]]*\]|\$\^\{?[^$]*\}?\$|\^[\w,]+|[†‡§¶*]+")


def recurrence_key(text: str) -> str:
    """What makes two cells 'the same value': case, citations, footnote marks
    and spacing set aside ('PREPUPA [1]' == 'Prepupa [1-2]')."""
    return re.sub(r"\s+", " ", _REF.sub("", text)).strip().lower()


def _is_unit(t: str) -> bool:
    x = t.strip().lower()
    if x.startswith("(") and x.endswith(")"):
        x = x[1:-1].strip()
    return x in _UNITS


def _is_stat(t: str) -> bool:
    if _STAT_ONLY.match(t.strip()):
        return True
    st = ct.header_statistic(t)
    if not st:
        return False
    # only a statistic: nothing word-like left once the statistic is removed
    rest = re.sub(r"(?i)mean|median|average|s\.?d\.?|s\.?e\.?m?|c\.?v\.?|min(imum)?|"
                  r"max(imum)?|range|mode|q[123]|quartile|±|\+/-|�|[()\s.,]", "", t)
    return not re.search(r"[A-Za-z]{2,}", rest)


def symbol(text: str, repeats: int) -> str:
    """Shape of one cell. `repeats` = how often its recurrence_key occurs in the
    same column (the cell itself included)."""
    t = text.strip()
    if not t or t in {"-", "–", "—"}:
        return "·"
    if _CAP.match(t):
        return "CAP"
    core, peeled = ct.peel(t)
    if ct._NUMBER.match(core):
        if _YEAR.match(t):
            return "Y"
        if "± spreads" in peeled or "spreads in brackets" in peeled:
            return "N±"
        if "ranges" in peeled:
            return "N–N"
        return "N"
    if repeats >= 2:
        return "C"                     # a value that recurs: a category, a code
    if _is_stat(t):
        return "STAT"
    if _is_unit(t):
        return "UNIT"
    if ct._BINOMIAL.match(t):
        return "L"
    if len(t) > 40 or len(t.split()) >= 6:
        return "X"
    return "U"


def family(sym: str) -> str:
    """Shapes that count as the same kind of value when columns vote. Years stay
    apart from other numbers: a row of years over a body of counts is a header
    row (Barber2017 'Year planted'), not the first record."""
    return "NUM" if sym in {"N", "N±", "N–N"} else sym


@dataclass
class Symbols:
    grid: Grid
    sym: dict = field(default_factory=dict)       # (r, c) of ORIGIN cells -> symbol

    @classmethod
    def of(cls, grid: Grid):
        counts = collections.defaultdict(collections.Counter)
        for (r, c), cell in grid.cells.items():
            if cell.r == r and cell.c == c and cell.text:
                counts[c][recurrence_key(cell.text)] += 1
        s = cls(grid)
        for (r, c), cell in grid.cells.items():
            if cell.r == r and cell.c == c:
                s.sym[(r, c)] = symbol(cell.text, counts[c][recurrence_key(cell.text)])
        return s

    def class_at(self, r, c):
        """Symbol at a position; a rowspan copy carries its origin's symbol, a
        colspan copy belongs to the spanning cell (None)."""
        cell = self.grid.at(r, c)
        if not cell:
            return "·"
        if cell.c != c:
            return None
        return self.sym.get((cell.r, cell.c), "·")

    def render_row(self, r, cols=None, width=16) -> str:
        cols = list(range(self.grid.ncols)) if cols is None else cols
        seen_text = collections.Counter(self.grid.origin(r, c).text.lower()
                                        for c in cols if self.grid.origin(r, c)
                                        and self.grid.origin(r, c).text)
        out = []
        for c in cols[:width]:
            cell = self.grid.at(r, c)
            if not cell:
                out.append("·")
            elif cell.r != r and cell.c == c:
                out.append("^")                          # rowspan from above
            elif cell.c != c:
                continue                                 # inside a colspan
            else:
                s = self.sym[(r, c)]
                if cell.rowspan > 1:
                    s += f"[↓{cell.rowspan}]"
                if cell.colspan > 1:
                    s += f"[→{cell.colspan}]"
                if cell.text and seen_text[cell.text.lower()] > 1 and s[0] not in "N·Y":
                    s += "="
                out.append(s)
        more = f" … (+{len(cols) - width} cols)" if len(cols) > width else ""
        return " | ".join(out) + more


# --- 3. layout decisions ------------------------------------------------------------------

@dataclass
class Plan:
    blocks: list                         # [[col, ...], ...]
    data_start: dict                     # block index -> first data row
    decided_by: dict                     # block index -> 'vote (x/y)' | 'model (p)' | ...
    row_roles: dict                      # (block, r) -> role
    columns: list                        # [{col, block, name, groups, values, unit}]
    sections: list                       # [(block, r, label)]
    block_labels: dict                   # block -> label text
    caption: str = ""


def split_blocks(grid: Grid) -> list:
    """Side-by-side blocks: runs of columns separated by (nearly) empty columns,
    when there are at least two runs two columns wide (Tsai2020: six sites)."""
    fill = []
    for c in range(grid.ncols):
        n = sum(1 for r in range(grid.nrows) if grid.text(r, c))
        fill.append(n / max(1, grid.nrows))
    runs, cur = [], []
    for c in range(grid.ncols):
        if fill[c] <= 0.05 and cur:
            runs.append(cur)
            cur = []
        elif fill[c] > 0.05:
            cur.append(c)
    if cur:
        runs.append(cur)
    big = [r for r in runs if len(r) >= 2]
    return big if len(big) >= 2 else [list(range(grid.ncols))]


def vote_data_start(S: Symbols, cols, max_header=10):
    """Each column votes the row where its values start: the first row whose
    symbol has the column's dominant body shape (taken from the lower half of
    the table), confirmed by the next filled cell below. Columns whose body is
    one-off words carry no evidence and abstain. -> (row, votes, voters)."""
    g = S.grid
    votes = collections.Counter()
    for c in cols:
        lower = [family(S.class_at(r, c)) for r in range(g.nrows // 2, g.nrows)]
        lower = [x for x in lower if x and x != "·"]
        if len(lower) < 2:
            continue
        dom, n = collections.Counter(lower).most_common(1)[0]
        if dom in {"U", "STAT", "UNIT", "CAP"} or n / len(lower) < 0.5:
            continue                                    # no format evidence
        seq = [(r, family(S.class_at(r, c))) for r in range(g.nrows)]
        seq = [(r, x) for r, x in seq if x and x != "·"]
        for i, (r, x) in enumerate(seq):
            if r > max_header:
                break
            nxt = seq[i + 1][1] if i + 1 < len(seq) else dom
            if x == dom and nxt == dom:
                votes[r] += 1
                break
    if not votes:
        return None, 0, 0
    voters = sum(votes.values())
    best = max(votes.items(), key=lambda kv: (kv[1], -kv[0]))
    return best[0], best[1], voters


def header_role(S: Symbols, r, cols, last_header) -> str:
    g = S.grid
    origins = [g.origin(r, c) for c in cols]
    filled = [x for x in origins if x and x.text]
    if not filled:
        covered = [g.at(r, c) for c in cols if g.at(r, c) and g.at(r, c).r < r and g.at(r, c).text]
        return "names" if covered else "empty"
    syms = [S.sym[(x.r, x.c)] for x in filled]
    width = len(cols)
    if len(filled) == 1 and r < last_header:
        if 1 < filled[0].colspan < 0.6 * width:
            return "group"
        return "caption"            # a lone cell above the column names
    if len(filled) == 1 and (syms[0] in {"CAP", "X"} or filled[0].colspan >= 0.6 * width):
        return "caption" if r < last_header else "names"
    if all(s == "UNIT" for s in syms):
        return "units"
    if sum(s in NUMERIC for s in syms) / len(syms) > 0.5:
        return "values"
    if r < last_header and any(1 < x.colspan < width for x in filled):
        return "group"
    return "names"


def body_role(S: Symbols, r, cols, names_text: set, median_filled: float) -> str:
    g = S.grid
    filled = [g.origin(r, c) for c in cols if g.origin(r, c) and g.origin(r, c).text]
    if not filled:
        return "empty"
    if len(filled) >= 2 and names_text:
        same = sum(1 for x in filled if x.text.strip().lower() in names_text)
        if same / len(filled) >= 0.6:
            return "repeated_header"
    if len(filled) == 1 and median_filled >= 2 and S.sym[(filled[0].r, filled[0].c)] not in NUMERIC:
        return "section"
    return "data"


LEGEND = ("Each line is one table row written as cell SHAPES, not words: N number, "
          "N± mean±spread, N–N range, Y year, L Latin name, C word repeated in its "
          "column, U word that appears once in its column, X long text, STAT "
          "statistic word, UNIT unit, CAP caption, · empty, [↓k] spans k rows, [→k] "
          "spans k columns, ^ covered by the cell above, = same text elsewhere in "
          "the row.")

DATA_START_Q = "Which row is the FIRST RECORD (the first data row)? Rows above it are captions and headers."

ROW_ROLE_OPTIONS = {
    "caption": "A title of the whole table or a label for a block: one cell (CAP, X or "
               "U), the rest of the row empty, above the column names.",
    "group": "Group labels: cells spanning several columns ([→k]) that group the "
             "column names below them.",
    "names": "The column names: one label per column (U or STAT), with ^ where a "
             "label from the row above covers the column.",
    "values": "One VALUE per column that describes the column itself (mostly N or "
              "Y), inside the header.",
    "units": "Units for the columns (UNIT).",
    "section": "A label for the rows BELOW it: one cell spanning the table, under the "
               "column names and directly above records.",
    "empty": "An empty row.",
}

BODY_OPTIONS = {
    "section": "A label for the rows below it (a group, a variable, a place): one "
               "cell, the rest of the row empty, while the records around it fill "
               "many cells.",
    "record": "A record whose other cells are missing.",
    "note": "A note, a total or a footnote.",
}


def _state(S, cols, size=0):
    n = [14, 10, 6][size]
    return LEGEND + "\n\n" + "\n".join(f"row {r}: {S.render_row(r, cols)}"
                                      for r in range(min(S.grid.nrows, n)))


def _ask(client, S, cols, questions):
    return client.ask(lambda size: _state(S, cols, size), questions)


def model_data_start(S, cols, client, k=9):
    q = {"q0": {"type": "choice", "instructions": DATA_START_Q,
                "criteria": {f"row {r}": S.render_row(r, cols) or "(empty)"
                             for r in range(min(S.grid.nrows, k))}}}
    a = _ask(client, S, cols, q).get("q0") or {}
    ch = a.get("choice") or ""
    if not ch.startswith("row "):
        return None, "model: no answer"
    p = (a.get("probabilities") or {}).get(ch, 0)
    return int(ch.split()[1]), f"model ({p:.2f})"


def model_row_roles(S, cols, client, start):
    qs = {f"q{r}": {"type": "choice",
                    "instructions": f"Row {r} ({S.render_row(r, cols)}) is above the "
                                    f"first record (row {start}). What is it?",
                    "criteria": dict(ROW_ROLE_OPTIONS)}
          for r in range(start)}
    ans = _ask(client, S, cols, qs) if qs else {}
    return {r: (ans.get(f"q{r}") or {}).get("choice") for r in range(start)}


def model_body_roles(S, cols, client, rows):
    qs = {f"q{r}": {"type": "choice",
                    "instructions": f"Row {r} inside the table body has one filled "
                                    f"cell: {S.render_row(r, cols)}. What is it?",
                    "criteria": dict(BODY_OPTIONS)}
          for r in rows}
    ans = _ask(client, S, cols, qs) if qs else {}
    return {r: (ans.get(f"q{r}") or {}).get("choice") for r in rows}


def decide(grid: Grid, client=None, min_share=0.5, mode="code") -> Plan:
    """Decide the layout from symbols only.

    mode='code'   the column vote decides where the data starts and code gives
                  each row its role; `client` (a column_tree DecisionClient), if
                  given, answers only when the vote is weak.
    mode='model'  the decision model answers every question of the tree on the
                  symbol grid: the first record, each header row's role, each
                  one-cell body row. Side-by-side blocks (empty columns) and
                  repeated headers (equal text) stay in code; if the model fails,
                  the code answer is used.
    """
    S = Symbols.of(grid)
    blocks = split_blocks(grid)
    plan = Plan(blocks, {}, {}, {}, [], [], {})
    for b, cols in enumerate(blocks):
        start, votes, voters = vote_data_start(S, cols)
        model_roles = {}
        if mode == "model" and client is not None:
            try:
                m_start, how = model_data_start(S, cols, client)
                if m_start is not None:
                    start = m_start
                plan.decided_by[b] = f"{how}; vote {votes}/{voters}"
                model_roles = model_row_roles(S, cols, client, start or 0)
            except Exception as e:
                plan.decided_by[b] = f"vote, model failed ({type(e).__name__})"
        elif start is not None and votes / voters >= min_share and voters >= 2:
            plan.decided_by[b] = f"vote ({votes}/{voters})"
        elif client is not None:
            try:
                m_start, how = model_data_start(S, cols, client)
                if m_start is not None:
                    start = m_start
                    plan.decided_by[b] = f"{how}; weak vote {votes}/{voters}"
            except Exception as e:                       # model down: keep the vote
                plan.decided_by[b] = f"vote, model failed ({type(e).__name__})"
        if start is None:
            start = 1
            plan.decided_by.setdefault(b, "default row 1 (no evidence)")
        plan.decided_by.setdefault(b, f"weak vote ({votes}/{voters})")
        plan.data_start[b] = start

        # header rows: the model's role where it answered, else code
        last_header = start - 1
        for r in range(start):
            plan.row_roles[(b, r)] = model_roles.get(r) or header_role(S, r, cols, last_header)
        # the last header row opens the body when it is a section ('Body mass'):
        # model mode -> the model said 'section'; code mode -> a lone full-width
        # cell under a real names row
        if start >= 2:
            if mode == "model" and model_roles:
                is_section = plan.row_roles[(b, start - 1)] == "section"
            else:
                lone = [grid.origin(start - 1, c) for c in cols
                        if grid.origin(start - 1, c) and grid.origin(start - 1, c).text]
                names_above = any(
                    sum(1 for c in cols if grid.origin(r, c) and grid.origin(r, c).text) >= 2
                    for r in range(start - 1))
                is_section = (len(lone) == 1 and names_above
                              and S.sym[(lone[0].r, lone[0].c)] not in NUMERIC)
            if is_section:
                plan.row_roles[(b, start - 1)] = "section"
                start -= 1
                plan.data_start[b] = start
                last_header = start - 1
                for r in range(start):
                    plan.row_roles[(b, r)] = (model_roles.get(r) if model_roles.get(r) != "section"
                                              else None) or header_role(S, r, cols, last_header)

        # block label / caption text
        for r in range(start):
            if plan.row_roles[(b, r)] == "caption":
                x = next((grid.origin(r, c) for c in cols if grid.origin(r, c)
                          and grid.origin(r, c).text), None)
                if len(blocks) > 1 and x:
                    plan.block_labels[b] = x.text
                    plan.row_roles[(b, r)] = "block_label"
                elif x:
                    plan.caption = plan.caption or x.text

        # words back: per column
        roles = {r: plan.row_roles[(b, r)] for r in range(start)}
        plan.columns += columns_from_roles(grid, S, cols, roles, block=b)
        names_text = {c["name"].strip().lower() for c in plan.columns
                      if c["block"] == b and c["name"]}

        # body rows: repeated headers by equal text (code); one-cell rows by the
        # model in model mode, by code otherwise
        filled_counts = [sum(1 for c in cols if grid.origin(r, c) and grid.origin(r, c).text)
                         for r in range(start, grid.nrows)]
        med = sorted(filled_counts)[len(filled_counts) // 2] if filled_counts else 0
        code_roles = {r: (plan.row_roles.get((b, r)) if plan.row_roles.get((b, r)) == "section"
                          else body_role(S, r, cols, names_text, med))
                      for r in range(start, grid.nrows)}
        if mode == "model" and client is not None:
            lone = [r for r in range(start, grid.nrows) if filled_counts[r - start] == 1
                    and code_roles[r] != "repeated_header"][:30]
            try:
                said = model_body_roles(S, cols, client, lone)
                for r, ch in said.items():
                    if ch:
                        code_roles[r] = {"record": "data"}.get(ch, ch)
            except Exception:
                pass                                     # keep the code roles
        for r in range(start, grid.nrows):
            role = code_roles[r]
            plan.row_roles[(b, r)] = role
            if role == "section":
                x = next(grid.origin(r, c) for c in cols if grid.origin(r, c) and grid.origin(r, c).text)
                plan.sections.append((b, r, x.text))
    return plan


def columns_from_roles(grid: Grid, S: "Symbols", cols, roles: dict, block: int = 0) -> list:
    """Put the words back: from the header rows' roles, each column's name,
    the group labels above it, the per-column header values and its unit.

    Pure code over the grid, so it can be re-run on stored roles without asking
    any model again.

      name        the LOWEST single-column label of the column. A cell spanning
                  several columns is a group, not the name, while a single-column
                  label sits above it (Nunes2016: 'Transects' spans the first three
                  columns as the label of a header row, below 'Functional Guild').
                  When the lowest label is only a statistic ('Mean (sd)') and a
                  label sits above it, that label is the name and the statistic
                  is kept (CortesGomez2023: 'Body size' over 'Mean (sd)').
      groups      the other labels above, outermost first
      values      {row label: this column's cell} for header rows of values
                  (Barber2017: 'Site Year planted' -> '2013')
    """
    out = []
    starts = sorted(roles)
    for c in cols:
        stack, values, unit, stat_row = [], {}, "", ""   # stack: (cell, role) bottom-up
        for r in reversed(starts):
            role = roles[r]
            cell = grid.at(r, c)
            if not cell or not cell.text:
                continue
            if role == "units":
                unit = unit or cell.text
            elif role == "statistic":                    # a row the model called statistic
                stat_row = stat_row or cell.text
            elif role == "values":
                # the row's label: its first word cell, a rowspan copy included
                # ('Site Year planted' spans down from the row above)
                label = next((grid.at(r, cc).text for cc in cols
                              if grid.at(r, cc) and grid.at(r, cc).text
                              and S.class_at(r, cc) not in NUMERIC | {"·"}
                              and S.sym.get((grid.at(r, cc).r, grid.at(r, cc).c)) not in NUMERIC | {"·"}),
                             f"row {r}")
                if cell.r == r and cell.text != label:      # a spanning value covers each column
                    values[label] = cell.text
            elif role in ("names", "group", "undefined"):  # undefined: position decides
                if not stack or stack[-1][0] is not cell:  # a rowspan is one label
                    stack.append((cell, role))
        labels = [x for x, _role in stack]
        single = [x for x in labels if x.colspan == 1]
        name_cell = single[0] if single else (labels[0] if labels else None)
        statistic = stat_row
        if not statistic and name_cell is not None and S.sym.get((name_cell.r, name_cell.c)) == "STAT":
            above = [x for x in labels if x.r < name_cell.r and x.colspan == 1]
            if above:
                statistic, name_cell = name_cell.text, above[0]
        name = name_cell.text if name_cell else ""
        groups = []
        for x in reversed(labels):                         # outermost first
            # only labels ABOVE the name group it; a spanning cell below the name
            # is the label of a header row ('Transects'), not a group
            if name_cell is not None and x.r >= name_cell.r:
                continue
            if x.text != name and x.text != statistic and x.text not in groups:
                groups.append(x.text)
        out.append({"col": c, "block": block, "name": name, "groups": groups,
                    "statistic": statistic, "values": values, "unit": unit})
    return out


def first_record(plan: Plan, block: int = 0):
    """Row index of the block's first data row (the body may open with a section)."""
    rows = sorted(r for (b, r), role in plan.row_roles.items() if b == block and role == "data")
    return rows[0] if rows else None


def records(grid: Grid, plan: Plan, block: int = 0) -> list:
    """Data rows of one block with the words put back: {col: text} plus the
    '_section' label in force and the '_row' index."""
    cols = plan.blocks[block]
    section, out = "", []
    for r in range(plan.data_start[block], grid.nrows):
        role = plan.row_roles.get((block, r))
        if role == "section":
            section = next((s for b, rr, s in plan.sections if b == block and rr == r), "")
            continue
        if role != "data":
            continue
        rec = {c: grid.text(r, c) for c in cols}
        rec["_section"] = section
        rec["_row"] = r
        out.append(rec)
    return out


def render(grid: Grid, plan: Plan, max_rows=8) -> str:
    """The symbol grid with the decided roles — for reports."""
    S = Symbols.of(grid)
    lines = []
    for b, cols in enumerate(plan.blocks):
        if len(plan.blocks) > 1:
            lines.append(f"block {b} cols {cols[0]}-{cols[-1]}"
                         + (f" '{plan.block_labels[b]}'" if b in plan.block_labels else ""))
        for r in range(min(grid.nrows, plan.data_start[b] + 2, max_rows)):
            lines.append(f"  row {r:>2} {plan.row_roles.get((b, r), '?'):16s} {S.render_row(r, cols)}")
    return "\n".join(lines)
