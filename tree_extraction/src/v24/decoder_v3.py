"""Decoder v3: v2 (frozen run v2d + the adjusted passage choice) plus three things the
full run showed missing. Code gives printed facts and proposes pieces; nimble decides.

1. Table footnotes. A legend printed directly below a table ('P, polyphagous; S, soil;
   W, wood ...' under Ambsperg's table) belongs to that table. The inventory keeps the
   entries but files them under gemma's variable ('Species classification'), so QV saw
   that label beside a 'Feeding group' column and kept 'W' (0.88 keep). v3 says in the
   option that the entry is printed in the footnote directly below this table: layout
   only (where the text sits in the markdown), not the footnote mark characters, which
   MinerU misreads.
2. Cells past the first 25. full_run sent each column's first 25 distinct values only,
   so later cells were never asked (Wallon 330 rows, Scalercio 30). v3 asks the rest with
   the same context (the first 25 listed), so the cells already answered are untouched.
3. Endings. Cells like '2.87 ± 0.05 cd' (comparison-test letters, Gibb) or
   'generalist[16]' (reference numbers, Cecala, Osorio). Code proposes the ending by
   shape; nimble says, once per column and shape, whether it is a mark added after the
   value or part of the value ('<5 mm' must keep its unit).
4. List cells. A cell printed whole as a code ('W/S, wood/soil interface') is decoded
   whole, not as W + S (v2.WHOLE_FIRST); a list of codes ('M, SDW, LDW') becomes one row
   per decoded part, as the GT writes it.
"""
import html
import re

import _paths
import decoder as v1
import decoder_v2 as v2

v2.WHOLE_FIRST = True          # 'W/S' printed as its own code is decoded whole

# ending shapes: (name, regex whose group 1 is the ending; the rest of the cell is the value)
ENDINGS = [
    ("letters", re.compile(r"^(.*?\d[^a-z]*?)\s+([a-z]{1,4}(?:,\s?[a-z]{1,4})*)$")),
    ("bracket number", re.compile(r"^(.*?)\s*(\[\d+(?:\s*[,–-]\s*\d+)*\])$")),
]


# --- 1. table footnotes -----------------------------------------------------------------------

FOOT_GAP = 5          # characters (whitespace-flattened) between '</table>' and the footnote


def _flat(s):
    return " ".join(str(s or "").split())


def md_tables(paper):
    """(flattened markdown, [(start, end, cell text)] of every <table> in it, in order)."""
    f = _paths.PAPERS / paper / f"{paper}_full.md"
    if not f.exists():
        return "", []
    flat = _flat(f.read_text(encoding="utf-8", errors="replace"))
    out = []
    for m in re.finditer(r"<table.*?</table>", flat, re.S):
        cells = _flat(html.unescape(re.sub(r"<[^>]+>", " ", m.group(0))))
        out.append((m.start(), m.end(), cells))
    return flat, out


def locate_table(table, spans):
    """The markdown table holding this reader table: the one containing the most of its cell
    texts (printed text, so robust to numbering shifts). -> index into spans, or None."""
    texts = {_flat(rec.get(col.name)) for rec in table.records for col in table.columns}
    texts = [x for x in texts if len(x) >= 3][:200]
    best, hits = None, 0
    for i, (_s, _e, cells) in enumerate(spans):
        n = sum(1 for x in texts if x in cells)
        if n > hits:
            best, hits = i, n
    return best if hits >= max(2, len(texts) // 4) else None


def footnote_units(flat, span, units):
    """Ids of the inventory units whose text starts directly below the table (layout)."""
    out = set()
    for uid, u in (units or {}).items():
        head = _flat(u.get("text"))[:60]
        if not head:
            continue
        i = flat.find(head, span[1])
        if 0 <= i - span[1] <= FOOT_GAP:
            out.add(uid)
    return out


def with_footnote(cats, feet):
    """Copies of the entries from this table's footnote with a 'mark_note' for v2's QV
    option; the others unchanged (their option text stays v2's). -> (cats, n noted)"""
    if not feet:
        return cats, 0
    out, n = [], 0
    for e in cats:
        if e.get("unit") in feet and e.get("code"):
            e = dict(e, mark_note="printed in the footnote directly below this table")
            n += 1
        out.append(e)
    return out, n


# --- 3. endings -------------------------------------------------------------------------------

def endings(values):
    """{shape: {cell: (value, ending)}} for the cells whose end matches a shape."""
    out = {}
    for v in values:
        for name, rx in ENDINGS:
            m = rx.match(v)
            if m and m.group(1).strip():
                out.setdefault(name, {})[v] = (m.group(1).strip(), m.group(2))
                break
    return out


def reference_list(paper, near=None):
    """{number: entry text} from a numbered reference list ('16. Barthell, J. F. …') after a
    'References' / 'Literature cited' heading. A paper with supplements has several lists:
    with `near` (a cell's text), the first list printed after the table that holds it
    (geometry), else the first list. Empty when no list is numbered."""
    f = _paths.PAPERS / paper / f"{paper}_full.md"
    if not f.exists():
        return {}
    text = f.read_text(encoding="utf-8", errors="replace")
    lists, cur, pos = [], None, 0
    for line in text.splitlines(keepends=True):
        if re.match(r"^#+\s*(references|literature cited|bibliography)\b", line.strip(), re.I):
            cur = (pos, {})
            lists.append(cur)
        elif cur is not None:
            m = re.match(r"^\s*\[?(\d{1,3})[.\]]\s+(\S.*)", line)
            if m:
                cur[1].setdefault(int(m.group(1)), " ".join(m.group(2).split()))
        pos += len(line)
    lists = [x for x in lists if x[1]]
    if not lists:
        return {}
    at = text.find(near) if near else -1
    if at >= 0:
        after = [x for x in lists if x[0] > at]
        if after:
            return after[0][1]
    return lists[0][1]


def ask_ending(client, header, values, shape, cells, paper=None):
    """One question per column and shape -> ('mark' | 'value', probs). For bracket numbers
    the paper's numbered reference entries they match are quoted (printed text)."""
    shown = ", ".join(f"'{v}'" for v in values[:25])
    state = (f"A table in a scientific paper has a column named '{header}'. Its cells hold "
             f"these values: {shown}.")
    ex = list(cells.items())[:4]
    refs = reference_list(paper, near=ex[0][0]) if shape == "bracket number" and paper else {}
    if refs:
        quoted = []
        for _v, (_val, end) in ex:
            for n in re.findall(r"\d+", end):
                if int(n) in refs and len(quoted) < 2 and not any(q.startswith(f"{n}.") for q in quoted):
                    quoted.append(f"{n}. {refs[int(n)][:160]}")
        if quoted:
            state += (" The paper's numbered reference list includes: "
                      + " | ".join(f"'{q}'" for q in quoted) + ".")
    listed = "; ".join(f"'{v}' ends with '{end}'" for v, (_val, end) in ex)
    return v1.ask(client, state,
                  f"In the column '{header}', some cells end with a short piece after the value: "
                  f"{listed}. What is that ending?",
                  {"mark": "a mark added after the value: letters from a statistical comparison "
                           "(values that share a letter do not differ significantly), or the "
                           "number of a cited reference or footnote — not part of the value itself",
                   "value": "part of the value itself: a unit of measurement, a word or category "
                            "name, or a qualifier the value needs"})
