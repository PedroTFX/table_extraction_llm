"""
head_view.py — colour view of what head_tree decided, table by table.

Each table is drawn with its real spans; every head cell is coloured by the role
the model gave it (title, group, column name, row label, value, specification...),
other rows by the row's role (section, data...). Hover a cell for the role and
probability. Under each table: the QSPEC questions with QC's answers before them,
and the column names, groups, details and values that come out.
"""

from __future__ import annotations

import html
import re

import header_tree as ht
import header_tree_bench as hb

SHOW_ROWS = 30          # rows drawn from the top; asked body rows are added after

ROLES = [  # role, label, description
    ("caption", "Title", "a title or caption of the table"),
    ("group", "Group label", "a label over several columns"),
    ("names", "Column name", "the name of a column"),
    ("specification", "Specification", "says more about the column name above it"),
    ("joined", "Joined", "one name together with the label under it"),
    ("row_label", "Row label", "names the values to its right"),
    ("value", "Value", "belongs to the row label on its left"),
    ("footnote", "Footnote", "a note about the table or a cell"),
    ("unanswered", "Unanswered", "the model gave no valid answer"),
    ("empty", "Empty", "an empty row"),
    ("data", "Data", "records"),
    ("section", "Section", "a label for the data rows below it"),
    ("rhead", "Header repeated", "the column names repeated"),
    ("missing", "Data, cells missing", "a record with most cells empty"),
    ("bnote", "Note / total", "a note, total or footnote inside the data"),
]

CSS = """
:root{--bg:#fbfbfa;--fg:#1d1d1f;--muted:#6b6b70;--line:#d9d9d5;--card:#fff;--head:#f2f2ef;
--caption:#e9dcf7;--group:#fde3c8;--names:#d6e6fb;--values:#cdeee6;--units:#dde3ea;
--empty:#ececec;--stat:#f9d3e3;--spec:#e6efc4;--data:#ffffff;--section:#fff1a8;--missing:#fff9dd;
--bnote:#e4e4e4;--warn:#b3261e;--ok:#1e7a3c}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#161617;--fg:#ececee;
--muted:#9a9aa0;--line:#38383c;--card:#1e1e20;--head:#232326;--caption:#3d2f52;--group:#4d3620;
--names:#1f3552;--values:#163f38;--units:#2c333b;--empty:#2b2b2e;--stat:#4f2338;--spec:#39421c;
--data:#1e1e20;--section:#4a4316;--missing:#33301e;--bnote:#2a2a2a;--warn:#ff9b8f;--ok:#7fd69a}}
:root[data-theme="dark"]{--bg:#161617;--fg:#ececee;--muted:#9a9aa0;--line:#38383c;--card:#1e1e20;
--head:#232326;--caption:#3d2f52;--group:#4d3620;--names:#1f3552;--values:#163f38;--units:#2c333b;
--empty:#2b2b2e;--stat:#4f2338;--spec:#39421c;--data:#1e1e20;--section:#4a4316;--missing:#33301e;
--bnote:#2a2a2a;--warn:#ff9b8f;--ok:#7fd69a}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1280px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:22px;margin:0 0 4px}h2{font-size:17px;margin:36px 0 4px}
.sub{color:var(--muted);margin:0 0 12px}
.legend{display:flex;flex-wrap:wrap;gap:6px 14px;margin:8px 0 4px;font-size:13px}
.legend span{display:inline-flex;align-items:center;gap:6px}
.sw{width:16px;height:16px;border:1px solid var(--line);border-radius:3px;display:inline-block}
.wrap{overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:var(--card);margin-top:8px}
table{border-collapse:collapse;font-size:12px;font-variant-numeric:tabular-nums}
td,th{border:1px solid var(--line);padding:3px 6px;vertical-align:top;white-space:nowrap;
max-width:220px;overflow:hidden;text-overflow:ellipsis}
th.rn{background:var(--head);color:var(--muted);font-weight:500;position:sticky;left:0}
td.gap{background:var(--head);color:var(--muted);text-align:center;font-style:italic}
.r-caption{background:var(--caption)}.r-group{background:var(--group)}.r-names{background:var(--names)}
.r-specification{background:var(--spec)}.r-joined{background:var(--names);font-style:italic}
.r-row_label{background:var(--stat)}.r-value{background:var(--values)}.r-empty{background:var(--empty)}
.r-data{background:var(--data)}.r-section{background:var(--section)}.r-missing{background:var(--missing)}
.r-bnote{background:var(--bnote)}.r-footnote{background:var(--bnote);font-style:italic}
.r-unanswered{background:repeating-linear-gradient(45deg,var(--empty) 0 6px,var(--card) 6px 12px)}
.r-rhead{background:var(--names);font-style:italic}
.coded{font-size:11px;color:var(--muted);border:1px solid var(--line);border-radius:4px;padding:0 4px;margin-left:4px}
.flag{color:var(--warn);font-weight:600}
table.cols td,table.spec td{white-space:normal;max-width:none}
details{margin-top:8px}summary{cursor:pointer;color:var(--muted)}
.changed{color:var(--warn)}.same{color:var(--muted)}
"""


def _e(x):
    return html.escape(str(x))


def _piece_of(res, c):
    for i, cols in enumerate(res["pieces"]):
        if c in cols:
            return i
    return 0


def _role(grid, res, r, c):
    """(css role, tooltip) for the cell at row r, column c."""
    start, head_end = res["start"], res.get("head_end", res["start"])
    cat = {"section": "section", "repeated_header": "rhead", "note": "bnote", "empty": "empty",
           "data": "missing", "head": "names"}
    if r < head_end:
        x = grid.at(r, c)
        if not x or not str(x.text or "").strip():
            return "empty", f"row {r}: empty"
        role, p, *note = res["cells"][_piece_of(res, c)].get(f"{x.r},{x.c}", ["unanswered", 0])
        css = {"title": "caption", "column": "names", "head_row_label": "row_label"}.get(role, role)
        return css, f"'{x.text}': {role}" + (f" (p={p})" if p else "") \
            + (f" · {note[0]}" if note else "")
    if r < start:
        role, p = res.get("pre", {}).get(str(r), ["note", 0])[:2]
        return cat.get(role, "bnote"), f"row {r}: {role} (p={p}), before the first record"
    b = res["body"].get(str(r))
    if b:
        role, p = b
        css = {"section": "section", "data": "missing", "note": "bnote",
               "repeated_header": "rhead"}.get(role, "data")
        return css, f"row {r}: {role} (p={p})"
    return "data", f"row {r}: data"


def _rows_to_draw(grid, res):
    rows = set(range(min(grid.nrows, max(SHOW_ROWS, res["start"] + 6))))
    for r in map(int, res["body"]):
        rows |= {x for x in (r - 1, r, r + 1) if 0 <= x < grid.nrows}
    return sorted(rows)


def table_html(grid, res):
    rows = _rows_to_draw(grid, res)
    segs, cur = [], []
    for r in rows:
        if cur and r != cur[-1] + 1:
            segs.append(cur)
            cur = []
        cur.append(r)
    if cur:
        segs.append(cur)
    out = ["<table>"]
    for si, seg in enumerate(segs):
        if si:
            out.append(f'<tr><td class="gap" colspan="{grid.ncols + 1}">… rows '
                       f'{segs[si - 1][-1] + 1}–{seg[0] - 1} not shown …</td></tr>')
        last = seg[-1]
        for r in seg:
            cells = [f'<th class="rn">{r}</th>']
            for c in range(grid.ncols):
                x = grid.at(r, c)
                css, tip = _role(grid, res, r, c)
                if not x:
                    cells.append(f'<td class="r-{css}" title="{_e(tip)}"></td>')
                    continue
                if x.c != c:
                    continue                                   # inside a colspan
                if x.r != r and r != seg[0]:
                    continue                                   # inside a rowspan
                rs = min(x.r + x.rowspan, last + 1) - r
                text = x.text if x.r == r else f"(↑ {x.text})"
                span = (f' rowspan="{rs}"' if rs > 1 else "") + \
                       (f' colspan="{x.colspan}"' if x.colspan > 1 else "")
                cells.append(f'<td class="r-{css}"{span} title="{_e(tip)}">{_e(text)}</td>')
            out.append("<tr>" + "".join(cells) + "</tr>")
    if grid.nrows > rows[-1] + 1:
        out.append(f'<tr><td class="gap" colspan="{grid.ncols + 1}">… rows '
                   f'{rows[-1] + 1}–{grid.nrows - 1} not shown …</td></tr>')
    out.append("</table>")
    return '<div class="wrap">' + "".join(out) + "</div>"


def spec_html(grid, res):
    """The QSPEC questions: which uppers over which cells, the answer, and what QC
    had said about those cells before it."""
    if not res.get("spec"):
        return ""
    after = {"column_names": ("group", "column"), "specification": ("column", "specification"),
             "together": ("joined", "column"), "title": ("title", None)}
    rows = []
    for s in res["spec"]:
        up_role, low_role = after.get(s["answer"], ("?", "?"))
        before = []
        for k, role in s["qc_before"].items():
            x = grid.at(*map(int, k.split(",")))
            new = up_role if k in s.get("upper_keys", []) else (low_role or role)
            cls = "same" if role == new else "changed"
            before.append(f'<span class="{cls}">{_e(x.text)}: {_e(role)}</span>')
        seen, uniq = set(), []
        for b in before:                                 # 'M: column' once, not 8 times
            if b not in seen:
                seen.add(b)
                uniq.append(b)
        rows.append(f"<tr><td>{_e(', '.join(s['uppers']))}</td><td>{_e(' | '.join(s['labels']))}</td>"
                    f"<td><b>{_e(s['answer'])}</b> (p={s['p']})"
                    + ("<br><span class='same'>" + _e(" · ".join(f"{k} {v}" for k, v in
                                                               s.get("probs", {}).items()))
                       + "</span>" if s.get("probs") else "")
                    + f"</td><td>{', '.join(uniq)}</td></tr>")
    return ('<details open><summary>QSPEC: cells spanning several columns, asked with the '
            'cells under them</summary><div class="wrap"><table class="spec"><tr>'
            '<th>Label(s) above</th><th>Cells under each</th><th>Answer</th>'
            '<th>QC before (red = changed by QSPEC)</th></tr>' + "".join(rows)
            + "</table></div></details>")


def columns_html(res):
    rows = []
    for c in res["columns"]:
        vals = "; ".join(f"{k} = {v}" for k, v in c.get("values", {}).items())
        coded = ('<span class="coded">coded name</span>'
                 if re.fullmatch(r"\s*(\d+|[A-Z]{1,3}\d*)\s*", c["name"] or "") else "")
        und = '<span class="flag">undecided</span>' if c.get("undecided") else ""
        rows.append(f"<tr><td>{c['col']}</td><td><b>{_e(c['name'])}</b>{coded}{und}</td>"
                    f"<td>{_e(' / '.join(c['groups']))}</td>"
                    f"<td>{_e(' / '.join(c.get('details', [])))}</td>"
                    f"<td>{_e(vals)}</td></tr>")
    return ('<details open><summary>Columns that come out</summary><div class="wrap">'
            '<table class="cols"><tr><th>Col</th><th>Name</th><th>Groups</th>'
            '<th>Under the name</th><th>Row-label values</th></tr>' + "".join(rows)
            + "</table></div></details>")


def write(results, path, label="nimble"):
    legend = "".join(f'<span><i class="sw r-{k}"></i>{_e(lab)}</span>' for k, lab, _d in ROLES)
    body = [f"<h1>Head reading — {_e(label)}</h1>",
            "<p class='sub'>Each head cell is coloured by the role the model gave it; other "
            "rows by the row's role; hover a cell for the role and its probability. Rows "
            "inside the data are only asked about when they fill far fewer cells than "
            "their neighbours.</p>",
            f'<div class="legend">{legend}</div>']
    for spec, res in results.items():
        grid = ht.grid_from_html(hb.html_tables(res["paper"])[res["table"]])
        q1 = res.get("q1", {})
        how = ("Q1 row by row" if res.get("variant") == "A" else
               "one first-record question (top answers: " + ", ".join(
                   f"{k[3:]}: {v}" for k, v in q1.get("options", {}).items()) + ")")
        n = len(res["pieces"])
        body += [f"<h2>{_e(res['paper'])} · table {res['table']}</h2>",
                 f"<p class='sub'>{grid.nrows} rows × {grid.ncols} columns · head rows "
                 f"{res.get('head_start', 0)}–{res['head_end'] - 1} · first record at "
                 f"<b>row {res['start']}</b> (p={q1.get('p')}, {_e(how)}) · "
                 f"{res['calls']} model calls · {res['secs']} s"
                 + (f" · cells asked in {n} pieces" if n > 1 else "") + "</p>",
                 table_html(grid, res), spec_html(grid, res), columns_html(res)]
    page = ("<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>Head reading</title><style>{CSS}</style></head><body><main>"
            + "".join(body) + "</main></body></html>")
    path.write_text(page, encoding="utf-8")
