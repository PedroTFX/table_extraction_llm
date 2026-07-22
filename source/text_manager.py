import html as _html
import re
import openpyxl


# --- HTML markup normalisation -------------------------------------------------
# MinerU emits a grab-bag of inline/block HTML inside and around tables. Only the
# table-structural tags (<td>/<th>/<tr>/<table>) are handled specially elsewhere;
# everything else is normalised here so no tag name or entity leaks into the text
# a later non-alphanumeric clean would mangle (e.g. '<sup></sup>' -> 'sup sup').
_COMMENT_RE = re.compile(r'<!--.*?-->', re.DOTALL)          # <!-- Complementary: X -->
_BR_RE = re.compile(r'<br\s*/?>', re.IGNORECASE)            # line break -> space
# Block-level boundaries inside a cell also become a space so words don't glue.
_BLOCK_RE = re.compile(r'</?(?:p|div|li|ul|ol|blockquote|h[1-6])[^>]*>',
                       re.IGNORECASE)
_VOID_RE = re.compile(r'<(?:img|hr|input|source|col)[^>]*>', re.IGNORECASE)  # no text
# Any remaining inline tag (<sup>, <sub>, <b>, <i>, <em>, <strong>, <span>,
# <font>, <a>, <mark>, <small>, <u>, <thead>/<tbody> wrappers, ...): drop the tag
# but KEEP its inner content. '<' not starting a tag (e.g. '<0.05') is left alone.
_TAG_RE = re.compile(r'</?[A-Za-z][^>]*>')


def strip_html_markup(text: str) -> str:
    """Remove non-table HTML markup while preserving the visible text.

    Order matters: comments and void elements go first (no content to keep);
    <br> and block tags become spaces (avoid gluing 'material<br>(obs)' into
    'material(obs)'); remaining inline tags are dropped keeping content; finally
    HTML entities are unescaped ('&lt;' -> '<', '&amp;' -> '&', '&nbsp;' -> space)
    so values like p '&lt;0.001' match their ground-truth form."""
    text = _COMMENT_RE.sub('', text)
    text = _VOID_RE.sub('', text)
    text = _BR_RE.sub(' ', text)
    text = _BLOCK_RE.sub(' ', text)
    text = _TAG_RE.sub('', text)
    text = _html.unescape(text)
    text = text.replace('\xa0', ' ')
    return text


# Inline formatting tags only — NOT the table-structural ones. Used where the
# text must keep its <table>/<tr>/<td> layout (e.g. scanning the raw paper for
# abbreviation definitions): stripping <td> there would glue adjacent cells and
# invent spurious words.
_INLINE_TAG_RE = re.compile(
    r'</?(?:sup|sub|b|i|em|strong|span|font|u|mark|small|big|s|strike|abbr|'
    r'cite|q|code|kbd|samp|var|time|a|label)\b[^>]*>',
    re.IGNORECASE)


def strip_inline_markup(text: str) -> str:
    """Like strip_html_markup but PRESERVES table tags (<table>/<tr>/<td>/<th>).

    For raw text whose table layout still matters: removes inline formatting
    (<sup>, <sub>, <b>, <a>, …) and unescapes entities so a '<sup>' can't survive
    as the literal word 'sup' (e.g. 'mandible<sup></sup> length (ML)' -> 'mandible
    length (ML)'), without collapsing table cells into one another."""
    text = _COMMENT_RE.sub('', text)
    text = _BR_RE.sub(' ', text)
    text = _INLINE_TAG_RE.sub('', text)
    text = _html.unescape(text)
    return text.replace('\xa0', ' ')


_TR_RE = re.compile(r'<tr[^>]*>(.*?)</tr>', re.DOTALL | re.IGNORECASE)
_CELL_RE = re.compile(r'<(td|th)([^>]*)>(.*?)</(?:td|th)>', re.DOTALL | re.IGNORECASE)


def _rowspan_of(attrs):
    m = re.search(r'rowspan\s*=\s*["\']?(\d+)', attrs, re.IGNORECASE)
    try:
        return max(1, int(m.group(1))) if m else 1
    except (TypeError, ValueError):
        return 1


def expand_rowspans(table_html):
    """Rewrite a <table> so every rowspan is made explicit: a cell with
    rowspan=N is copied DOWN into the N-1 rows it covers.

    Why only rowspan (not colspan): the per-row pipe conversion below drops the
    covered cells, so a row under a rowspan loses that cell and every cell to its
    right shifts left — the identifier disappears and values land in the wrong
    columns (e.g. a family name spanning a 'Mean' and a 'Range' row leaves the
    Range row headerless). Carrying the value down restores alignment.

    colspan is deliberately left as a single cell: parse_table treats a lone
    populated cell as a band/section row (_is_group_row), which is how full-width
    'colspan' banners are meant to read. Forward-filling colspan would turn a
    banner into a full data row and break that detection.

    Rowspans in leading grouping columns (the common case) are handled exactly;
    a rowspan in a trailing column of a short row may still shift, which no real
    table in the corpus does.
    """
    rows = _TR_RE.findall(table_html)
    if not rows:
        return table_html
    carry = {}                         # col -> [rows_remaining, value]
    out = ["<table>"]
    for r in rows:
        cells = [(re.sub(r'\s+', ' ', inner).strip(), _rowspan_of(attrs))
                 for _tag, attrs, inner in _CELL_RE.findall(r)]
        row, col, ci = [], 0, 0
        while ci < len(cells) or (col in carry and carry[col][0] > 0):
            if col in carry and carry[col][0] > 0:      # a rowspan covers this col
                row.append(carry[col][1])
                carry[col][0] -= 1
                col += 1
                continue
            val, rs = cells[ci]
            ci += 1
            row.append(val)
            if rs > 1:
                carry[col] = [rs - 1, val]
            col += 1
        out.append("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>")
    out.append("</table>")
    return "\n".join(out)


def clean_tables(text):
    # Make rowspans explicit BEFORE the per-row flattening below, which would
    # otherwise drop the covered cells and misalign every row under a rowspan.
    text = expand_rowspans(text)
    # Collapse whitespace (incl. newlines) INSIDE each cell first, so a <td>/<th>
    # containing line breaks (e.g. "Nesting material\n\n(own observation)")
    # doesn't get split into bogus extra rows when <tr> becomes a newline.
    # NOTE: <th> (header cells) must be handled identically to <td>. MinerU emits
    # header rows as <th>; if we don't convert them, the real header survives as
    # literal "<th>..</th>" with no '|' separators, and the parser then mistakes
    # the FIRST data row for the header — gluing data values into column names.
    def _flatten_cell(m):
        inner = re.sub(r'\s+', ' ', m.group(2)).strip()
        return f'<{m.group(1)}>{inner}</{m.group(1)}>'
    text = re.sub(r'<(td|th)[^>]*>(.*?)</(?:td|th)>', _flatten_cell, text,
                  flags=re.DOTALL | re.IGNORECASE)

    text = re.sub(r'<tr[^>]*>', '\n', text)
    text = re.sub(r'</tr>', '', text)
    text = re.sub(r'<(?:td|th)[^>]*>', '', text)
    text = re.sub(r'</(?:td|th)>', ' | ', text)
    text = re.sub(r'<table[^>]*>', '', text)
    text = re.sub(r'</table>', '', text)
    # Normalise everything else MinerU may have left in the cells: inline tags
    # (<sup>, <sub>, <b>, ...), <br>/blocks -> space, comments/images dropped,
    # and HTML entities unescaped. See strip_html_markup.
    text = strip_html_markup(text)
    return text

def get_tables(text):
    tables_list = []
    parts = re.split(r'(<table.*?</table>)', text, flags=re.DOTALL | re.IGNORECASE)    
    for part in parts:
        if not part:
            continue
        if re.fullmatch(r'<table.*?</table>', part, flags=re.DOTALL | re.IGNORECASE):
            # print(clean_tables(part))
            table = clean_tables(part)
            tables_list.append({"type": "table", "content": table, "size":len(table)})
    return tables_list

def table_processing(table):
    lines = [l.strip() for l in table.strip().split('\n')]
    headers = [h.strip() for h in lines[0].split('|') if h.strip()]
    return headers, lines


def table_to_records(table, skip_group_rows=True):
    """Parse a cleaned pipe-table into (headers, records).

    records is a list of {header: value} dicts — the dataframe-like view the
    rest of the pipeline never built. By default, taxonomic group/subheader
    rows (only the first cell populated, e.g. 'Rhinotermitidae | | | ...') are
    skipped, since they carry no per-species values.
    """
    headers, lines = table_processing(table)
    records = []
    for line in lines[1:]:
        cells = [c.strip() for c in line.split('|')]
        row = {h: (cells[i] if i < len(cells) else '') for i, h in enumerate(headers)}
        if not any(row.values()):
            continue
        if skip_group_rows and row.get(headers[0]) and all(not row[h] for h in headers[1:]):
            continue
        records.append(row)
    return headers, records


def table_to_columns(table, skip_group_rows=True):
    """Column-oriented view: (headers, {header: [values...]})."""
    headers, records = table_to_records(table, skip_group_rows)
    return headers, {h: [r[h] for r in records] for h in headers}


def get_text(text, size):
    def clean_cut_text(text, size):
        def clean_cut(part_of_text, size):
            phrases = re.findall(r'[^.]+\.?', part_of_text)
            result = ""

            for i in range(len(phrases)):
                candidate = result + phrases[i]
                if len(candidate) <= size or len(result) == 0:
                    result = candidate
                else:
                    return result, ''.join(phrases[i:])
            return result, ""

        result = []
        parts = [text]
        while len(parts) > 0:
            if len(parts[0]) == 0:
                parts = parts[1:]
                continue

            cutted_text, remained = clean_cut(parts[0], size)
            if not cutted_text:
                result.append(parts[0])
                parts = parts[1:]
                continue
            
            result.append(cutted_text)
            parts = ([remained] if remained else []) + parts[1:]
            
        return result

    def clean_latex(text):
        def humanize_math(m):
            content = m.group(1)
            content = re.sub(r'\\circ', '°', content)
            content = re.sub(r'\\prime', "'", content)
            content = re.sub(r'\\mathrm\s*\{\s*([^}]+)\s*\}', r'\1', content)
            content = re.sub(r'[\^{}\\]', ' ', content)
            content = re.sub(r'(\d)\s+(\d)', r'\1\2', content)
            content = re.sub(r'\s+', '', content)
            return content.strip()

        text = re.sub(r'\$([^$]+)\$', humanize_math, text)
        text = re.sub(r'[†‡§¶]', '', text)
        # Prose from MinerU carries the same inline HTML/entities as tables
        # (<sup> footnote markers, &amp;, &nbsp;, <br>); normalise them so the
        # tag agents don't see 'sup'/'&amp;' noise.
        text = strip_html_markup(text)
        text = re.sub(r' +', ' ', text)
        return text.strip()
    
    result = []
    parts = re.split(r'(<table.*?</table>)', text, flags=re.DOTALL | re.IGNORECASE)    
    for part in parts:
        if not part:
            continue
        if re.fullmatch(r'<table.*?</table>', part, flags=re.DOTALL | re.IGNORECASE):
            # print(clean_tables(part))
            # table = clean_tables(part)
            # result.append({"type": "table", "content": part, "size":len(part)})
            continue
        else:
            for p in clean_cut_text(part, size):
                clean_text = clean_latex(p)
                result.append({"type": "text", "content": clean_text, "size": len(clean_text)})
    
    return result


def csv_to_table(csv_text):
    import csv as _csv
    import io as _io
    rows = list(_csv.reader(_io.StringIO(csv_text)))  # handles quoted commas
    return _rows_to_pipe_table(rows)


def xlsx_to_table(xlsx_path):
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb.active
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    return _rows_to_pipe_table(rows)


def _rows_to_pipe_table(rows):
    """Turn a list-of-lists into a pipe table with the SAME join for header and
    body, padding ragged rows so columns stay positionally aligned, and never
    dropping empty/None cells (alignment matters more than tidiness)."""
    if not rows:
        return ""
    width = max(len(r) for r in rows)

    def cell(c):
        return "" if c is None else str(c).strip()

    out = []
    for r in rows:
        padded = list(r) + [None] * (width - len(r))
        out.append(" | ".join(cell(c) for c in padded))
    return "\n".join(out)


if __name__ == "__main__":
    
    from pathlib import Path
    file = Path("Abensperg-Traun M. (1991).md")
    paper_text = file.read_text(encoding="utf-8")
    print(paper_text[:5000])
    text = get_text(paper_text, len(paper_text))
    print(text)