"""
head_to_table.py — the adapter between the head reader and the column tree: turn
head_tree's answers for one HTML table into the pipeline's Table (tables.Table),
the input column_tree.classify_table reads. Code only copies what the answers say:

  columns   one per grid column; the header is the head reader's name with its
            groups before it and its details after it ('Traits CL M'), the way the
            pipeline joins a multi-row header. A column the head reader left
            undecided keeps a visible placeholder ('(no name, column 3)') so it is
            still asked and scored, not silently dropped.
  records   the rows from the first record on, minus the body rows nimble called a
            section, a repeated header or a note; a cell spanning rows is copied
            into each row it covers (as the pipeline's records do).
  headless  a table with no head (head_end 0) continues the previous table when
            the widths match (the pipeline's header_override): its rows join it.
  context   (version 2 only) what the head reader saw that a header cannot carry:
            the title, the section labels and the rows they head, and the values
            of head rows with a label on their left (Barber: year planted per site).

The rotation of species-in-header tables (table_to_data.maybe_transpose) runs after,
as in the pipeline.
"""

from __future__ import annotations

import re

import _paths  # noqa: F401  (puts source/ on the path)
import header_tree as ht
from table_to_data import maybe_transpose
from tables import Column, Table

SKIP_BODY = {"section", "repeated_header", "note"}
MAX_ROTATE_ROWS = 100   # every right rotation in the 77 papers has <= 33 trait rows (2026-10-14)


def _norm(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()


def _header(col):
    if not col or not col.get("name"):
        return ""
    return _norm(" ".join([*col.get("groups", []), col["name"], *col.get("details", [])]))


def _cell(grid, r, c):
    x = grid.at(r, c)
    return _norm(x.text) if x else ""


def _context(grid, full, records_rows):
    """Version 2: the lines the column tree gets as table context."""
    lines = []
    titles = sorted({_norm(grid.at(*map(int, k.split(","))).text)
                     for cells in full["cells"] for k, v in cells.items() if v[0] == "title"})
    if titles:
        lines.append("Table title (found in its head): " + " / ".join(t[:150] for t in titles))
    sections = []
    for k, v in ((k, v) for cells in full["cells"] for k, v in cells.items()):
        if v[0] == "section":                            # head reader v2: a section cell in the head
            r = int(k.split(",")[0])
            if (r, _cell(grid, r, int(k.split(",")[1]))[:60]) not in sections:
                sections.append((r, _cell(grid, r, int(k.split(",")[1]))[:60]))
    for r in sorted({*map(int, full["body"]), *map(int, full.get("pre", {}))}):
        role = (full["body"].get(str(r)) or full["pre"].get(str(r)) or [""])[0]
        if role == "section":
            text = " ".join(dict.fromkeys(t for t in (_cell(grid, r, c) for c in range(grid.ncols))
                                          if t))         # a label repeated in every cell, once
            sections.append((r, _norm(text)[:60]))
    if sections:
        lines.append("Section labels, each heading the rows below it (found in the table): "
                     + ", ".join(f"'{t}' (row {r})" for r, t in sections[:12])
                     + (f" ... ({len(sections)} in all)" if len(sections) > 12 else ""))
    vals = [(c, c_vals) for c, c_vals in ((col["col"], col.get("values") or {})
                                         for col in full["columns"]) if c_vals]
    if vals:
        by_label = {}
        for c, cv in vals:
            for label, v in cv.items():
                by_label.setdefault(label, []).append(f"column {c}: {v}")
        for label, items in list(by_label.items())[:3]:
            lines.append(f"Head row '{label}' gives, per column: " + "; ".join(items[:20]))
    return lines


def build_tables(paper, entries, grids, context=False):
    """entries: header_tree_bench 'head' entries of one paper (each with 'full');
    grids: {table index: Grid}. -> [(Table, [context lines])] in document order."""
    out = []
    for e in sorted(entries, key=lambda e: e["table"]):
        k, full = e["table"], e["full"]
        grid = grids[k]
        start = full["start"]
        rows = [r for r in range(start, grid.nrows)
                if (full["body"].get(str(r)) or [""])[0] not in SKIP_BODY
                and any(_cell(grid, r, c) for c in range(grid.ncols))]
        if full["head_end"] == 0 and out and out[-1][0].columns and \
                len(out[-1][0].columns) == grid.ncols:   # a continuation: join the previous
            t, ctx, rows_prev = out[-1]
            for r in rows:
                rec = {col.name: _cell(grid, r, col.index) for col in t.columns}
                rec.update(_row_index=r, _is_group_row=False)
                t.records.append(rec)
            continue
        by_col = {c["col"]: c for c in full["columns"]}
        columns, used = [], set()
        for c in range(grid.ncols):
            name = _header(by_col.get(c)) or f"(no name, column {c})"
            base, i = name, 2
            while name in used:
                name, i = f"{base} #{i}", i + 1
            used.add(name)
            columns.append(Column(index=c, raw=name, name=name, synthetic=False))
        records = []
        for r in rows:
            rec = {col.name: _cell(grid, r, col.index) for col in columns}
            rec.update(_row_index=r, _is_group_row=False)
            records.append(rec)
        t = Table(columns=columns, records=records, raw="", source=f"{paper}_head",
                  table_index=k)
        out.append((t, _context(grid, full, rows) if context else [], rows))
    result = []
    for t, ctx, _rows in out:
        if len(t.records) > MAX_ROTATE_ROWS:     # species across the header come with a few
            result.append((t, ctx))              # dozen trait rows; a 1140-row sampling table
            continue                             # (Noriega t5) is not one — never rotate it
        t2, _ev = maybe_transpose(t)
        if t2 is not t:             # rotated: lines naming rows or columns would point at
            ctx = [c for c in ctx if c.startswith("Table title")]   # the old orientation
        result.append((t2, ctx))
    return result


def grids_of(paper):
    import header_tree_bench as hb
    return {k: ht.grid_from_html(h) for k, h in enumerate(hb.html_tables(paper))}
