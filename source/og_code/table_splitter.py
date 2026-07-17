"""
table_splitter.py — deterministic decomposition of one raw HTML <table> into a
list of clean rectangular sub-tables, using ONLY signals present in the markup:

  1. colspan-aware grid expansion (a colspan=N cell fills N grid columns),
  2. BAND rows  — a single label spanning (most of) the width = a section banner
                  (e.g. 'Bee functional diversity' / 'Wasp functional diversity');
                  the table is cut into a separate sub-table at each band,
  3. composite HEADER detection — consecutive leading header rows are combined
                  into one header by joining the levels per column
                  (e.g. 'TR vs. PF' + 'Estimate ± SE' -> 'TR vs. PF — Estimate ± SE'),
  4. GROUP-header rows — a row with only the identifier cell populated acts as a
                  prefix for the rows beneath it ('Pollen-carrying structures'
                  -> 'Pollen-carrying structures: Corbicula').

No LLM is involved; every cut is deterministic and unit-testable. The output is a
list of pipe-tables (str) ready for the existing parser/flattener.

The splitter is intentionally conservative: a plain rectangular table with one
header row and no bands/colspans passes through as a single sub-table unchanged.
"""

from __future__ import annotations

import re
from html import unescape
from typing import List


# ---------------------------------------------------------------------------
# 1. HTML -> rectangular grid (expanding colspans)
# ---------------------------------------------------------------------------

def _row_is_band_html(row_html: str, width: int) -> bool:
    """Detect a band/banner row directly from HTML: exactly one non-empty cell,
    and it spans most of the table width (large colspan), or is the lone cell.
    Done on raw HTML so it is independent of grid forward-fill."""
    cells = re.findall(
        r"<(?:td|th)([^>]*)>(.*?)</(?:td|th)>", row_html, flags=re.DOTALL | re.IGNORECASE
    )
    nonempty = []
    for attrs, inner in cells:
        text = re.sub(r"\s+", " ", unescape(inner)).strip()
        span = 1
        m = re.search(r'colspan\s*=\s*"?(\d+)"?', attrs, flags=re.IGNORECASE)
        if m:
            span = max(1, int(m.group(1)))
        if text:
            nonempty.append((text, span))
    if len(nonempty) != 1:
        return False
    text, span = nonempty[0]
    # banner if its single label spans a big chunk of the row...
    if span >= max(3, width // 2):
        return True
    # ...or it is a lone label sitting in an INTERIOR column (not the first
    # column). A single first-column label is a group-header, not a band; a
    # single interior-column label (e.g. MinerU emitting 'Wasp functional
    # diversity' mid-row with no colspan) is a section banner.
    # find its physical column index
    col = 0
    for attrs, inner in cells:
        t = re.sub(r"\s+", " ", unescape(inner)).strip()
        sp = 1
        m = re.search(r'colspan\s*=\s*"?(\d+)"?', attrs, flags=re.IGNORECASE)
        if m:
            sp = max(1, int(m.group(1)))
        if t:
            break
        col += sp
    return col >= 1 and width >= 3


def _split_html_into_block_htmls(html: str) -> List[str]:
    """Cut the raw HTML into block HTMLs at band rows (band row dropped)."""
    rows_html = re.findall(r"<tr[^>]*>.*?</tr>", html, flags=re.DOTALL | re.IGNORECASE)
    # estimate width from the widest row (sum of colspans)
    def row_width(rh):
        w = 0
        for attrs, _ in re.findall(r"<(?:td|th)([^>]*)>(.*?)</(?:td|th)>", rh,
                                   flags=re.DOTALL | re.IGNORECASE):
            m = re.search(r'colspan\s*=\s*"?(\d+)"?', attrs, flags=re.IGNORECASE)
            w += max(1, int(m.group(1))) if m else 1
        return w
    width = max((row_width(r) for r in rows_html), default=0)

    blocks: List[str] = []
    current: List[str] = []
    for rh in rows_html:
        if _row_is_band_html(rh, width):
            if current:
                blocks.append("<table>" + "".join(current) + "</table>")
            current = []
            continue
        current.append(rh)
    if current:
        blocks.append("<table>" + "".join(current) + "</table>")
    return blocks


def _parse_html_grid(html: str, fill_spans_in_headers: bool = True) -> List[List[str]]:
    """Parse <tr>/<td|th> into a rectangular grid, expanding colspan so every row
    has the same physical width. For a colspan=N cell the label is REPEATED across
    all N columns (forward-fill), so a two-level header like 'TR vs. PF' spanning
    two sub-columns labels BOTH of them — otherwise the second sub-column would
    lose its top-level group. (rowspan is uncommon here and is not expanded.)"""
    rows_html = re.findall(r"<tr[^>]*>(.*?)</tr>", html, flags=re.DOTALL | re.IGNORECASE)
    grid: List[List[str]] = []
    for rh in rows_html:
        cells = re.findall(
            r"<(?:td|th)([^>]*)>(.*?)</(?:td|th)>", rh, flags=re.DOTALL | re.IGNORECASE
        )
        row: List[str] = []
        for attrs, inner in cells:
            span = 1
            m = re.search(r'colspan\s*=\s*"?(\d+)"?', attrs, flags=re.IGNORECASE)
            if m:
                span = max(1, int(m.group(1)))
            text = re.sub(r"\s+", " ", unescape(inner)).strip()
            # repeat the label across spanned columns (forward-fill) when it is a
            # spanning label cell; blank cells stay blank.
            row.append(text)
            for _ in range(span - 1):
                row.append(text if (fill_spans_in_headers and text) else "")
        grid.append(row)
    width = max((len(r) for r in grid), default=0)
    for r in grid:
        r.extend([""] * (width - len(r)))
    return grid


# ---------------------------------------------------------------------------
# 2. row classification helpers (all deterministic)
# ---------------------------------------------------------------------------

def _populated(row: List[str]) -> List[int]:
    return [i for i, c in enumerate(row) if c.strip()]


def _is_band_row(row: List[str], width: int) -> bool:
    """A section banner: exactly one populated cell, and it is NOT in the first
    column (a single first-column value is a group/data row, not a band). The
    populated cell typically sat behind a wide colspan, so after expansion only
    one grid cell carries the text and the rest are blank."""
    pop = _populated(row)
    if len(pop) != 1:
        return False
    # band label is somewhere in the interior / not the row-label column
    return pop[0] != 0 and width >= 3


def _is_group_row(row: List[str]) -> bool:
    """Only the first (identifier) column is populated — a sub-heading over the
    block of rows beneath it."""
    pop = _populated(row)
    return pop == [0]


def _looks_like_header(row: List[str]) -> bool:
    """Heuristic: a header row's non-first cells are mostly non-numeric labels
    (e.g. 'Estimate ± SE', 't/z-value', '(mm)', treatment names). Data rows have
    mostly numeric / value cells."""
    cells = [c.strip() for c in row[1:] if c.strip()]
    if not cells:
        return False
    def is_label(c: str) -> bool:
        # contains a letter and is not a bare number / ± value
        has_alpha = bool(re.search(r"[A-Za-z]", c))
        is_valuey = bool(re.fullmatch(r"[-−+]?[\d.,]+(\s*±\s*[\d.,]+)?", c))
        return has_alpha and not is_valuey
    labels = sum(1 for c in cells if is_label(c))
    return labels >= max(1, len(cells) // 2 + 1)


# ---------------------------------------------------------------------------
# 3. split into blocks at band rows
# ---------------------------------------------------------------------------

def _split_blocks(grid: List[List[str]]) -> List[List[List[str]]]:
    """Cut the grid into blocks at band rows. The band label is dropped (it names
    the block but is not itself header or data)."""
    if not grid:
        return []
    width = len(grid[0])
    blocks: List[List[List[str]]] = []
    current: List[List[str]] = []
    for row in grid:
        if _is_band_row(row, width):
            if current:
                blocks.append(current)
            current = []
            continue
        current.append(row)
    if current:
        blocks.append(current)
    return blocks


# ---------------------------------------------------------------------------
# 4. build composite header + emit pipe table for one block
# ---------------------------------------------------------------------------

def _join_levels(levels: List[str]) -> str:
    parts = [p.strip() for p in levels if p and p.strip()]
    # de-duplicate consecutive identical labels (colspan expansion repeats blanks,
    # not labels, but the row-label column often repeats e.g. 'Bee species')
    out: List[str] = []
    for p in parts:
        if not out or out[-1] != p:
            out.append(p)
    return " — ".join(out)


def _block_to_pipe(block: List[List[str]], prefix_groups: bool = False) -> str:
    """Turn one block into a pipe table: combine leading header rows into a single
    composite header. Group-header rows (only first column populated) are by
    default SKIPPED (matching existing pipeline behavior, where a taxonomic family
    banner like 'Rhinotermitidae' is dropped and species keep their bare name).
    Set prefix_groups=True to instead prefix members with the group label."""
    if not block:
        return ""
    width = len(block[0])

    # leading consecutive header rows
    h = 0
    while h < len(block) and _looks_like_header(block[h]):
        h += 1
    header_rows = block[:h] if h > 0 else [block[0]]
    data_rows = block[h:] if h > 0 else block[1:]

    ncols = width
    header: List[str] = []
    for c in range(ncols):
        levels = [hr[c] if c < len(hr) else "" for hr in header_rows]
        header.append(_join_levels(levels) or f"col{c}")

    lines = ["| " + " | ".join(header) + " |"]
    group_prefix = ""
    for row in data_rows:
        if _is_group_row(row):
            group_prefix = row[0].strip()
            continue  # group banner row is not itself a data record
        out = list(row) + [""] * (ncols - len(row))
        if prefix_groups and group_prefix and out[0].strip():
            out[0] = f"{group_prefix}: {out[0].strip()}"
        if any(c.strip() for c in out):
            lines.append("| " + " | ".join(out[:ncols]) + " |")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# public entry point
# ---------------------------------------------------------------------------

def split_table(html: str) -> List[str]:
    """One raw HTML <table> -> list of clean pipe-table strings (usually 1).

    Deterministic pipeline: (1) split into blocks at band rows (read from raw
    colspan), (2) expand each block to a colspan-forward-filled grid, (3) combine
    leading header rows into a composite header, (4) prefix group-row members."""
    block_htmls = _split_html_into_block_htmls(html)
    out: List[str] = []
    for bh in block_htmls:
        grid = _parse_html_grid(bh)
        if not grid:
            continue
        pipe = _block_to_pipe(grid)
        if pipe.strip():
            out.append(pipe)
    return out
