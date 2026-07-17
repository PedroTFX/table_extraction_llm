"""
table_parser.py — turn a messy, aligned cell grid into clean sub-tables + records.

This layer does NOT do geometry/column-alignment (that's the PDF/HTML reader's
job). It takes a grid — list of rows, each a list of already-column-aligned cell
strings — and resolves the SEMANTIC structure that every paper does differently:

  edge cases handled
  ------------------
  1  blank rows                      -> dropped (and used as soft section hints)
  2  caption/title lines             -> dropped ("Table 3 ...", "Figure 1 ...")
  3  footnote/legend lines           -> split off from the data (returned aside)
  4  multi-line headers              -> leading label rows joined per column
  5  repeated headers (page breaks)  -> dropped, but VERIFIED against header vocab
  6  section band rows               -> split the table into sections (banner kept)
  7  group / sub-header rows          -> prefix the rows beneath them (optional)
  8  multi-line (wrapped) data rows  -> merged into one record
  9  ragged rows                     -> padded to the header width
  10 sub-tables w/ their own header  -> a section may re-declare its own header
  11 decoy all-identical "band"       -> a colspan banner forward-filled to N cells

What it deliberately does NOT try to do: guess column boundaries, un-OCR glued
text, or resolve true rowspan/colspan merges beyond the forward-filled-banner
case. Feed it a decently aligned grid and it will structure it.

Primary entry points:
    parse(grid_or_html) -> ParsedTable
    from_html(html)     -> grid
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from html import unescape
from typing import List, Optional


# ---------------------------------------------------------------------------
# patterns
# ---------------------------------------------------------------------------

_CAPTION_RE = re.compile(r"^\s*(table|fig(ure)?\.?|appendix|supplementary|scheme)\s*\d",
                         re.IGNORECASE)
_FOOTNOTE_RE = re.compile(r"^\s*([\*\u2020\u2021\u00a7\u00b6a-z]?[\).]|note[s]?\s*[:.]|"
                          r"[\*\u2020\u2021\u00a7\u00b6])", re.IGNORECASE)
_NUMERIC_RE = re.compile(r"^[-\u2212+]?[\d.,]+(\s*[\u00b1\u2013\u2014-]\s*[\d.,]+)?%?$")


class RowType(Enum):
    BLANK = "blank"
    CAPTION = "caption"
    HEADER = "header"
    BAND = "band"          # section banner (one label over the whole width)
    GROUP = "group"        # sub-heading, only the identifier column populated
    DATA = "data"
    CONTINUATION = "cont"  # wrapped continuation of the row above
    FOOTNOTE = "footnote"


@dataclass
class Section:
    label: Optional[str]                 # band/banner text, if any
    header: List[str]
    records: List[dict] = field(default_factory=list)


@dataclass
class ParsedTable:
    sections: List[Section] = field(default_factory=list)
    footnotes: List[str] = field(default_factory=list)

    @property
    def records(self) -> List[dict]:
        """All records across sections (section label attached under '_section')."""
        out = []
        for s in self.sections:
            for r in s.records:
                if s.label:
                    r = {**r, "_section": s.label}
                out.append(r)
        return out


# ---------------------------------------------------------------------------
# grid helpers
# ---------------------------------------------------------------------------

def from_html(html: str) -> List[List[str]]:
    """Parse a single <table> ... </table> (or a fragment of <tr>s) into a grid.
    colspan forward-fills the label across the spanned columns so a banner shows
    up as identical cells (detected as a BAND later); rowspan is not expanded."""
    grid = []
    for rh in re.findall(r"<tr[^>]*>(.*?)</tr>", html, flags=re.DOTALL | re.IGNORECASE):
        row = []
        for attrs, inner in re.findall(r"<(?:td|th)([^>]*)>(.*?)</(?:td|th)>",
                                       rh, flags=re.DOTALL | re.IGNORECASE):
            text = re.sub(r"\s+", " ", unescape(inner)).strip()
            span = 1
            m = re.search(r'colspan\s*=\s*"?(\d+)"?', attrs, re.IGNORECASE)
            if m:
                span = max(1, int(m.group(1)))
            row.append(text)
            row.extend([text] * (span - 1) if text else [""] * (span - 1))
        grid.append(row)
    return normalize_grid(grid)


def normalize_grid(grid: List[List[str]]) -> List[List[str]]:
    """Strip cells and pad ragged rows to the widest row's width."""
    grid = [[("" if c is None else str(c).strip()) for c in row] for row in grid]
    width = max((len(r) for r in grid), default=0)
    return [r + [""] * (width - len(r)) for r in grid]


def _populated(cells) -> List[int]:
    return [i for i, c in enumerate(cells) if c.strip()]


def _looks_numeric(c: str) -> bool:
    return bool(_NUMERIC_RE.match(c.strip()))


def _line_text(cells) -> str:
    return " ".join(c for c in cells if c.strip()).strip()


# ---------------------------------------------------------------------------
# header vocabulary (for verified repeated-header detection)
# ---------------------------------------------------------------------------

def _vocab(header) -> set:
    return {w for c in header for w in re.findall(r"[A-Za-z]+", c.lower())}


def _is_header_like(cells, vocab, thresh=0.6) -> bool:
    if not vocab:
        return False
    words = [w for c in cells for w in re.findall(r"[A-Za-z]+", c.lower())]
    if not words:
        return False
    return sum(w in vocab for w in words) / len(words) >= thresh


# ---------------------------------------------------------------------------
# row classification (structural, then position-aware)
# ---------------------------------------------------------------------------

def _label_heavy(cells) -> bool:
    """A header-ish row: its non-first populated cells are mostly non-numeric."""
    vals = [c for c in cells[1:] if c.strip()]
    if not vals:
        return False
    nonnum = sum(1 for c in vals if not _looks_numeric(c))
    return nonnum >= max(1, len(vals) // 2 + 1)


def _is_banner(cells) -> bool:
    """One label spanning the width: either a single interior populated cell, or
    the SAME (non-numeric) text forward-filled across (almost) the full width — a
    colspan banner. A numeric full-width fill (e.g. all zeros) is not a banner."""
    pop = _populated(cells)
    if len(pop) == 1:
        return pop[0] != 0            # single first-col value is a GROUP, not a band
    nonempty = [cells[i] for i in pop]
    if len(set(nonempty)) == 1 and not _looks_numeric(nonempty[0]):
        return len(pop) >= max(2, len(cells) - 1)   # spans (almost) the full width
    return False


def _col_numeric(grid, types):
    """Vote each column numeric or text using only candidate content rows
    (structural type still undecided)."""
    width = max((len(r) for r in grid), default=0)
    out = []
    for c in range(width):
        vals = [grid[i][c] for i in range(len(grid))
                if types[i] is None and c < len(grid[i]) and grid[i][c].strip()]
        out.append(bool(vals) and sum(_looks_numeric(v) for v in vals) >= len(vals) * 0.5)
    return out


def _header_mismatch(cells, col_num):
    """True if the row puts a text label in a numeric column — the signature of a
    header row over a numeric column."""
    for c, isnum in enumerate(col_num):
        if isnum and c < len(cells) and cells[c].strip() and not _looks_numeric(cells[c]):
            return True
    return False


def classify(grid, id_col=0):
    """[(RowType, cells)] via structure + column-type voting for the header, then
    position for data/continuation and trailing footnotes."""
    n = len(grid)
    types = [None] * n

    for i, cells in enumerate(grid):
        pop = _populated(cells)
        if not pop:
            types[i] = RowType.BLANK
        elif _CAPTION_RE.match(_line_text(cells)):
            types[i] = RowType.CAPTION
        elif _is_banner(cells):
            types[i] = RowType.BAND
        elif pop == [id_col]:
            types[i] = RowType.GROUP

    col_num = _col_numeric(grid, types)
    has_numeric_col = any(col_num)

    # A BAND separates DATA groups, so it cannot precede the first data row.
    # A single-cell row above the data (e.g. the stacked header fragment "Mean"
    # sitting over "bodylength (mm)") is part of the multi-line HEADER; calling
    # it a band splits the table into bogus sections with mismatched headers.
    first_data_idx = None
    for i, cells in enumerate(grid):
        if types[i] is None and (not has_numeric_col or not _header_mismatch(cells, col_num)):
            first_data_idx = i
            break
    if first_data_idx is not None:
        for i in range(first_data_idx):
            if types[i] in (RowType.BAND, RowType.GROUP):
                types[i] = None          # let the header pass claim it

    seen_content = False
    for i, cells in enumerate(grid):
        if types[i] is not None:
            continue
        if not seen_content:
            if has_numeric_col:
                types[i] = RowType.HEADER if _header_mismatch(cells, col_num) else RowType.DATA
                if types[i] == RowType.DATA:
                    seen_content = True
            else:
                types[i] = RowType.HEADER
                seen_content = True
            continue
        first = cells[id_col].strip()
        if not first or first[:1].islower():
            types[i] = RowType.CONTINUATION
        else:
            types[i] = RowType.DATA

    for i in range(n):
        if types[i] is None:
            types[i] = RowType.DATA

    last_data = max((i for i, t in enumerate(types) if t == RowType.DATA), default=-1)
    for i in range(last_data + 1, n):
        cells = grid[i]
        if types[i] in (RowType.GROUP, RowType.CONTINUATION, RowType.BAND):
            if _FOOTNOTE_RE.match(_line_text(cells)) or len(_populated(cells)) == 1:
                types[i] = RowType.FOOTNOTE
    return list(zip(types, grid))


# ---------------------------------------------------------------------------
# assembly
# ---------------------------------------------------------------------------

def _join_header(rows) -> List[str]:
    if not rows:
        return []
    width = max(len(r) for r in rows)
    header = [""] * width
    for r in rows:
        for i in range(width):
            c = r[i] if i < len(r) else ""
            if c.strip():
                header[i] = (header[i] + " " + c).strip()
    return [h or f"col{i}" for i, h in enumerate(header)]


def _assemble_records(header, body_rows, id_col, prefix_groups):
    """Build records from classified body rows, merging continuations and
    applying group prefixes."""
    records = []          # list of cell-lists
    group_prefix = ""
    vocab = _vocab(header)
    width = len(header)

    for rtype, cells in body_rows:
        cells = (cells + [""] * (width - len(cells)))[:width]
        if rtype == RowType.GROUP:
            group_prefix = cells[id_col].strip()
            continue
        if rtype == RowType.CONTINUATION and records:
            prev = records[-1]
            if cells[id_col].strip():
                prev[id_col] = (prev[id_col] + " " + cells[id_col]).strip()
            for i in range(width):
                if i != id_col and cells[i].strip() and not prev[i].strip():
                    prev[i] = cells[i].strip()
            continue
        # DATA — skip a verified repeated header sitting inside the body
        if _is_header_like(cells, vocab):
            continue
        row = list(cells)
        if prefix_groups and group_prefix and row[id_col].strip():
            row[id_col] = f"{group_prefix}: {row[id_col].strip()}"
        records.append(row)

    return [{header[i]: r[i] for i in range(width)} for r in records]


def assemble(classified, id_col=0, prefix_groups=False) -> ParsedTable:
    """Split at BAND rows into sections; each section gets its own header if it
    re-declares one, else inherits the table header."""
    table = ParsedTable()
    # drop blanks/captions up front; keep order
    rows = [(t, c) for t, c in classified if t not in (RowType.BLANK, RowType.CAPTION)]

    # footnotes off the bottom
    table.footnotes = [_line_text(c) for t, c in rows if t == RowType.FOOTNOTE]
    rows = [(t, c) for t, c in rows if t != RowType.FOOTNOTE]

    # leading header block (consecutive HEADER rows at the top)
    hi = 0
    while hi < len(rows) and rows[hi][0] == RowType.HEADER:
        hi += 1
    base_header = _join_header([c for _, c in rows[:hi]]) if hi else \
        [f"col{i}" for i in range(len(rows[0][1]))] if rows else []
    rows = rows[hi:]

    # split into sections at BAND rows
    cur_label, cur_header, buf = None, base_header, []

    def flush():
        if not buf and cur_label is None:
            return
        # a section can re-declare its own header: leading HEADER rows in buf
        j = 0
        while j < len(buf) and buf[j][0] == RowType.HEADER:
            j += 1
        header = _join_header([c for _, c in buf[:j]]) if j else cur_header
        recs = _assemble_records(header, buf[j:], id_col, prefix_groups)
        if recs or cur_label:
            table.sections.append(Section(cur_label, header, recs))

    for t, c in rows:
        if t == RowType.BAND:
            flush()
            band_cells = [x for x in c if x.strip()]
            cur_label = band_cells[0] if band_cells and len(set(band_cells)) == 1 \
                else _line_text(c)
            cur_header = base_header
            buf = []
        else:
            buf.append((t, c))
    flush()
    return table


# ---------------------------------------------------------------------------
# public
# ---------------------------------------------------------------------------

def parse(grid_or_html, *, id_col=0, prefix_groups=False) -> ParsedTable:
    """Parse a grid (list of row-lists) or a <table> HTML string into a
    ParsedTable (sections of records, plus any footnotes)."""
    if isinstance(grid_or_html, str):
        grid = from_html(grid_or_html)
    else:
        grid = normalize_grid(grid_or_html)
    if not grid:
        return ParsedTable()
    return assemble(classify(grid, id_col=id_col), id_col=id_col,
                    prefix_groups=prefix_groups)
