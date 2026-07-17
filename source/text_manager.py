import re
import openpyxl


def clean_tables(text):
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