"""
tables.py — robust, table-agnostic parsing for MinerU-style pipe tables.

Why this module exists
----------------------
The old pipeline parsed each table in several places with
``headers = [h for h in line.split('|') if h.strip()]`` (empties dropped) while
rows were split *positionally*. Any blank or merged header cell shifted every
later column onto the wrong data cell, so some columns silently picked up the
wrong value — or none at all when ``headers.index(header)`` raised and the
column was skipped.

The fix is to parse every table exactly once into an aligned, addressable
structure and never index a row by a recomputed header position again.

A ``Table`` exposes:
  - ``columns``  : list[Column] with a STABLE positional ``index`` and a
                   cleaned ``name`` (footnote markers / nbsp / whitespace
                   normalised) plus the original ``raw`` header text.
  - ``records``  : list[dict] keyed by column ``name`` (group/subheader rows are
                   flagged, not silently dropped, so callers decide what to do).
  - ``resolve()``: match an externally-supplied header string (e.g. a key the
                   LLM returned in its mapping JSON) back to a Column by cleaned
                   name, so encoding/whitespace drift never desyncs the join.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Optional

# Footnote markers + the U+FFFD replacement char MinerU emits on bad bytes.
_FOOTNOTE_RE = re.compile(r"[\u2020\u2021\u00a7\u00b6\uFFFD]")  # † ‡ § ¶ �
_WS_RE = re.compile(r"\s+")


def clean_text(s: object) -> str:
    """Canonical form for headers/values: strip footnote markers + nbsp, collapse
    whitespace. Used for *matching*; the raw text is preserved separately."""
    if s is None:
        return ""
    s = _FOOTNOTE_RE.sub("", str(s)).replace("\xa0", " ")
    return _WS_RE.sub(" ", s).strip()


def footnote_markers(s: object) -> str:
    """Return the footnote markers present in a header, e.g. 'Feeding group†' -> '†'.
    Used to link a column to the legend line that defines its codes."""
    if s is None:
        return ""
    return "".join(_FOOTNOTE_RE.findall(str(s)))


@dataclass
class Column:
    index: int          # positional index in the raw split row (stable)
    raw: str            # header text exactly as parsed
    name: str           # cleaned header (used as the record key + match key)
    synthetic: bool = False   # True for blank header cells we named ourselves


@dataclass
class Table:
    columns: list[Column]
    records: list[dict] = field(default_factory=list)
    raw: str = ""
    source: Optional[str] = None        # provenance: which file this came from
    table_index: int = 0                # ordinal within that file

    # --- lookup helpers -----------------------------------------------------
    def __post_init__(self):
        self._by_name = {c.name: c for c in self.columns}
        self._by_clean = {clean_text(c.name): c for c in self.columns}
        self._by_raw = {c.raw: c for c in self.columns}

    @property
    def header_names(self) -> list[str]:
        """Real (non-synthetic) column names, in order."""
        return [c.name for c in self.columns if not c.synthetic]

    def resolve(self, header: str) -> Optional[Column]:
        """Map an arbitrary header string back to a Column.

        Tries exact raw, exact name, then cleaned name. This is what makes the
        join robust to the LLM returning 'Feeding group' for a header that was
        physically 'Feeding group†'.
        """
        if header in self._by_raw:
            return self._by_raw[header]
        if header in self._by_name:
            return self._by_name[header]
        return self._by_clean.get(clean_text(header))

    def data_records(self) -> list[dict]:
        """Records that are real data rows (group/subheader rows removed)."""
        return [r for r in self.records if not r["_is_group_row"]]

    def column_values(self, header: str, data_only: bool = True) -> list[str]:
        """All values for a column, addressed by any header spelling."""
        col = self.resolve(header)
        if col is None:
            return []
        src = self.data_records() if data_only else self.records
        return [r[col.name] for r in src]


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _split_row(line: str) -> list[str]:
    return [c.strip() for c in line.split("|")]


def _build_columns(header_cells: list[str]) -> list[Column]:
    """Assign every positional cell a stable Column. Blank header cells are kept
    (so alignment is preserved) but named synthetically and marked, so callers
    can ignore them. Duplicate names are disambiguated."""
    columns: list[Column] = []
    seen: dict[str, int] = {}
    for i, raw in enumerate(header_cells):
        name = clean_text(raw)
        synthetic = name == ""
        if synthetic:
            name = f"__col{i}"
        if name in seen:
            seen[name] += 1
            name = f"{name} ({seen[name]})"
        else:
            seen[name] = 0
        columns.append(Column(index=i, raw=raw, name=name, synthetic=synthetic))
    return columns


def _is_group_row(values: list[str], columns: list[Column]) -> bool:
    """A taxonomic group/subheader row: first real cell populated, every other
    real cell empty (e.g. 'Rhinotermitidae | | | ...')."""
    real = [c for c in columns if not c.synthetic]
    if not real:
        return False
    first, rest = real[0], real[1:]
    if not values[first.index]:
        return False
    return all(not values[c.index] for c in rest if c.index < len(values))


def _looks_like_subheader(cells, header_cols):
    """Heuristic: is this row a CONTINUATION of the header (e.g. a units row like
    '| (mm) | (mm) | (mm) |') rather than data?

    True when, ignoring the first (identifier) cell, the populated cells are
    overwhelmingly 'unit-like': parenthesised (e.g. '(mm)', '(reference)') or a
    bare *lowercase/symbol* unit token (e.g. 'mm', 'cm', '%', 'm^2', 'count').

    Capitalised words are deliberately NOT unit-like: a first data row such as
    '9.0 | Independent | Monogynous | Yes | No' (categorical trait values) must be
    kept as DATA, not merged into the header. Earlier this used a generic
    'short, no-digit, <=2 words' test that wrongly matched 'Independent'/'Yes',
    gluing the first data row onto every column name (e.g. measurementType became
    'Colony founding mode Independent') and zeroing out matches against clean GT.
    """
    rest = [cells[c.index] for c in header_cols[1:] if c.index < len(cells)]
    rest = [v.strip() for v in rest if v and v.strip()]
    if not rest:
        return False
    unit_like = 0
    for v in rest:
        # parenthesised unit/ref e.g. "(mm)", "(reference)", "(own observation)"
        if v.startswith("(") and v.endswith(")"):
            unit_like += 1
            continue
        # bare unit token: starts lowercase or a symbol (mm, cm, g, %, m^2,
        # count, kg), no spaces, short. Capitalised words (Yes, Independent) and
        # anything with a digit-led/number value are NOT units.
        if (v[0].islower() or v[0] in "%") and " " not in v and len(v) <= 12 \
                and not v[0].isdigit():
            unit_like += 1
    return unit_like >= max(1, len(rest) // 2 + 1)   # majority are unit-like


def _merge_header(columns, sub_cells):
    """Append a sub-header row's cells onto the column names: 'Left wing length'
    + '(mm)' -> 'Left wing length (mm)'. Empty sub-cells leave the name as-is."""
    for col in columns:
        extra = sub_cells[col.index].strip() if col.index < len(sub_cells) else ""
        if extra and extra.lower() != col.name.lower():
            merged = f"{col.name} {extra}".strip()
            col.name = clean_text(merged)
    return columns


_CITATION_RE = re.compile(r"\b(1[89]|20)\d{2}\b")  # a 4-digit year 1800-2099


def _is_citation_like(value: str) -> bool:
    """True if a cell value looks like a literature citation rather than a trait
    value — e.g. '(Buchmann, 2004)', '(Silveira & Almeida, 2002)'. Used to tell a
    reference continuation row apart from a genuine second data row that happens
    to share an identifier. Requires BOTH parenthesis-wrapping (or near it) and a
    year, so a real categorical value in parens won't be misread as a citation."""
    v = (value or "").strip()
    if not v:
        return False
    wrapped = v.startswith("(") and v.endswith(")")
    has_year = bool(_CITATION_RE.search(v))
    # citation = parenthesised AND contains a year (e.g. '(Buchmann, 2004)')
    return wrapped and has_year


def parse_table(table: str, source: Optional[str] = None, table_index: int = 0,
                merge_subheaders: bool = True) -> Table:
    """Parse one cleaned pipe-table into a fully-aligned :class:`Table`.

    Tolerant of: trailing pipes, ragged rows (short rows pad with '', long rows
    truncate), blank/merged header cells, footnote markers and nbsp in headers.
    If ``merge_subheaders`` and the second row is a units/continuation row (e.g.
    '| (mm) | (mm) |'), it is folded into the header instead of becoming data.
    """
    lines = [l for l in (ln.strip() for ln in table.strip().splitlines()) if l]
    if not lines:
        return Table(columns=[], raw=table, source=source, table_index=table_index)

    columns = _build_columns(_split_row(lines[0]))
    ncols = len(columns)

    body_start = 1
    if merge_subheaders and len(lines) > 1:
        sub = _split_row(lines[1])
        sub = sub + [""] * (ncols - len(sub)) if len(sub) < ncols else sub
        if _looks_like_subheader(sub, columns):
            columns = _merge_header(columns, sub)
            body_start = 2          # consume the units row
            # rebuild lookups now that names changed
            columns = list(columns)

    records: list[dict] = []
    # Index of the first non-synthetic column = the identifier/anchor column.
    # A row is a CONTINUATION of the row above when either (a) its anchor cell is
    # blank, or (b) its anchor repeats the previous row's anchor. Both arise from
    # the S1/S2 supplements: the reference for each species sits on its own row
    # carrying only a literature citation like '(Buchmann, 2004)' in the last
    # column. Depending on the converter that row either has a blank species cell
    # OR repeats the species name. Either way it must NOT become its own record,
    # and must NOT overwrite a trait cell the species row already filled.
    anchor_idx = next((c.index for c in columns if not c.synthetic), 0)

    def _anchor_of(cells):
        return cells[anchor_idx].strip() if anchor_idx < len(cells) else ""

    for ridx, line in enumerate(lines[body_start:], start=body_start):
        cells = _split_row(line)
        # Align to header width: pad short rows, truncate overflow.
        if len(cells) < ncols:
            cells = cells + [""] * (ncols - len(cells))
        # Skip fully-empty rows.
        if not any(cells[: ncols]):
            continue

        anchor = _anchor_of(cells)
        prev_anchor = (records[-1].get(columns[anchor_idx].name, "").strip()
                       if records and anchor_idx < len(columns) else None)

        is_continuation = False
        if records:
            if not anchor:
                # blank anchor is unambiguously a continuation of the row above
                is_continuation = True
            elif anchor and anchor == prev_anchor:
                # Same identifier as the previous row. Two cases look alike:
                #   (1) a REFERENCE row — the only differing cell is a literature
                #       citation like '(Buchmann, 2004)'; this is a continuation
                #       and the citation should be discarded.
                #   (2) a genuine SECOND measurement row — differing cells hold
                #       real trait values; this must be KEPT as its own record.
                # Distinguish by whether every conflicting value is citation-shaped
                # (wrapped in parentheses). If so -> continuation; else -> keep.
                prev = records[-1]
                conflicts = []
                for col in columns:
                    val = cells[col.index].strip() if col.index < len(cells) else ""
                    if not val:
                        continue
                    prev_val = str(prev.get(col.name, "")).strip()
                    if prev_val and prev_val != val:
                        conflicts.append(val)
                if conflicts:
                    is_continuation = all(_is_citation_like(v) for v in conflicts)
                else:
                    is_continuation = True

        if is_continuation:
            # Fold populated cells into the previous record ONLY where that record
            # left the cell empty. Reference rows (trait cell above already filled)
            # are thus discarded; a genuinely empty cell is still rescued.
            prev = records[-1]
            for col in columns:
                val = cells[col.index].strip() if col.index < len(cells) else ""
                if val and not str(prev.get(col.name, "")).strip():
                    prev[col.name] = val
            continue

        rec = {col.name: (cells[col.index] if col.index < len(cells) else "") for col in columns}
        rec["_row_index"] = ridx
        rec["_is_group_row"] = _is_group_row(cells, columns)
        records.append(rec)

    return Table(columns=columns, records=records, raw=table,
                 source=source, table_index=table_index)


# ---------------------------------------------------------------------------
# Legend / footnote extraction (deterministic first, LLM as fallback elsewhere)
# ---------------------------------------------------------------------------
#
# Volunteers record the *expanded* legend term verbatim (e.g. the code 'W' under
# 'Feeding group†' becomes 'Wood', not 'wood feeders'). MinerU usually keeps the
# footnote text right after the table, e.g.:
#     † Feeding group: W, wood; S, soil; W/S, wood/soil interface.
# or  ‡ W = wood; M = mound
# This parser recovers {column_name: {code: term}} for the common shapes so we
# don't have to rely on the LLM (which tends to paraphrase).

# code<sep>term where sep is ',', '=', ':', '-', or whitespace; term runs to ; or .
_PAIR_RE = re.compile(
    r"([A-Za-z][A-Za-z/()]*)\s*[,=:\-]\s*([^;,.\n]+?)(?=\s*[;.\n]|,(?=\s*[A-Za-z][A-Za-z/()]*\s*[,=:\-])|$)"
)


def _parse_pairs(segment: str) -> dict:
    """Pull {code: term} pairs out of a legend segment, preserving term casing."""
    out = {}
    for code, term in _PAIR_RE.findall(segment):
        code = code.strip()
        term = term.strip().rstrip(".;,")
        if code and term and code.lower() != term.lower():
            out[code] = term
    return out


def parse_legends_from_text(text: str, table: Table) -> dict:
    """Best-effort deterministic legend extraction.

    Returns {column_name: {code: term}} for every relevant column whose footnote
    marker we can locate a definition line for. Columns without a marker, or
    whose definition we can't find, are simply omitted (LLM fallback handles
    those upstream).
    """
    legends: dict[str, dict] = {}
    # Index candidate legend lines by their leading footnote marker.
    marker_lines: dict[str, list[str]] = {}
    for line in text.splitlines():
        ls = line.strip()
        if not ls:
            continue
        lead = footnote_markers(ls[:1])
        if lead:
            marker_lines.setdefault(lead, []).append(ls)

    for col in table.columns:
        if col.synthetic:
            continue
        marks = footnote_markers(col.raw)
        if not marks:
            continue
        pairs: dict = {}
        for m in marks:
            for ln in marker_lines.get(m, []):
                # strip the leading marker and any 'Label:' prefix before pairs
                body = _FOOTNOTE_RE.sub("", ln, count=1).strip()
                body = re.sub(r"^[^:]{0,40}:\s*", "", body, count=1)
                pairs.update(_parse_pairs(body))
        if pairs:
            legends[col.name] = pairs
    return legends


def apply_legend(value: str, legend: dict) -> str:
    """Decode a (possibly comma-joined) cell using a {code: term} legend,
    leaving unknown codes untouched. Order and de-duplication preserved."""
    if not legend or not isinstance(value, str):
        return value
    out, seen = [], set()
    for part in value.split(","):
        p = part.strip()
        if not p:
            continue
        decoded = legend.get(p, legend.get(p.lower(), p))
        if decoded not in seen:
            out.append(decoded)
            seen.add(decoded)
    return ", ".join(out)

# ---------------------------------------------------------------------------
# Abbreviation / acronym definitions (deterministic, paper-wide, marker-free)
# ---------------------------------------------------------------------------
#
# Unlike parse_legends_from_text (which is keyed off a column's footnote MARKER),
# this resolves an acronym used in a column NAME (e.g. 'ITD') to its full term by
# scanning the WHOLE text for the shapes papers actually use. No marker required
# and nothing hardcoded: if the term is not written in the paper, nothing is
# returned. To support more shapes later, add an entry to _ABBREV_SHAPES; each is
# (name, fn(token, text) -> term | None).

def _schwartz_hearst(short: str, long: str) -> Optional[str]:
    """Schwartz & Hearst (2003) best-long-form match: walk both strings right to
    left; every character of `short` must match a character of `long` in order,
    and the FIRST character of `short` must align to the start of a word in
    `long`. Returns the matched long-form substring (short='ITD',
    long='intertegular distance' -> 'intertegular distance') or None. This is why
    'ITD' resolves even though it is not one-letter-per-word."""
    if not short or not long:
        return None
    s_i, l_i = len(short) - 1, len(long) - 1
    while s_i >= 0:
        ch = short[s_i].lower()
        if not ch.isalnum():
            s_i -= 1
            continue
        while ((l_i >= 0 and long[l_i].lower() != ch) or
               (s_i == 0 and l_i > 0 and long[l_i - 1].isalnum())):
            l_i -= 1
        if l_i < 0:
            return None
        l_i -= 1
        s_i -= 1
    l_i += 1
    return long[l_i:].strip() or None


def _abbrev_from_term_paren(token: str, text: str) -> Optional[str]:
    """Shape: 'full term (ABBR)'  e.g. 'intertegular distance (ITD)'."""
    for m in re.finditer(r"\(\s*" + re.escape(token) + r"\s*\)", text):
        words = re.findall(r"[A-Za-z][A-Za-z\-]*", text[:m.start()])
        if not words:
            continue
        window = " ".join(words[-(2 * len(token) + 5):])
        long = _schwartz_hearst(token, window)
        if long and long.lower() != token.lower() and len(long) > len(token):
            return long
    return None


def _abbrev_from_definition(token: str, text: str) -> Optional[str]:
    """Shape: 'ABBR = term' / 'ABBR: term' / 'ABBR, term'
    e.g. 'ITD = intertegular distance'.

    The text after the separator has an ambiguous right edge ('ITS = inter-tegular
    span here' should yield 'inter-tegular span', not '... here'). So we anchor:
    the term must START at a word beginning with the acronym's first letter and
    END at a word beginning with its last letter, and the joined span must
    Schwartz-Hearst-match the acronym. We take the shortest such span. This trims
    trailing filler without dropping real words (CTM -> 'critical thermal
    maximum', whose middle word also contains an 'm', still resolves correctly)."""
    first, last = token[0].lower(), token[-1].lower()
    for m in re.finditer(r"\b" + re.escape(token) + r"\b\s*[=:,]\s*(.+)", text):
        seg = re.split(r"[.;\n]", m.group(1), 1)[0]
        words = re.findall(r"[A-Za-z][A-Za-z\-]*", seg)[:8]
        if not words or words[0][0].lower() != first:
            continue
        for k in range(len(words)):
            if words[k][0].lower() != last:
                continue
            cand = " ".join(words[:k + 1])
            if cand.lower() != token.lower() and _schwartz_hearst(token, cand):
                return cand
    return None


# Ordered: the first shape that resolves a token wins. Extend this list to add
# new definition shapes without touching the caller.
_ABBREV_SHAPES = [
    ("term (ABBR)", _abbrev_from_term_paren),
    ("ABBR = term", _abbrev_from_definition),
]


def find_abbreviation_definitions(text: str, tokens: Iterable[str]) -> dict:
    """Resolve each acronym token to its full term using deterministic, paper-wide
    matching across _ABBREV_SHAPES.

    Returns {token: {"term": <verbatim full term>, "shape": <which shape matched>}}
    for the tokens it could resolve; unresolved tokens are omitted (the caller
    falls back to the LLM for those). Nothing is invented and nothing is
    hardcoded — a token is resolved only if the paper actually defines it."""
    out: dict = {}
    if not text:
        return out
    for token in dict.fromkeys(t for t in tokens if t):
        for shape_name, fn in _ABBREV_SHAPES:
            term = fn(token, text)
            if term:
                out[token] = {"term": term, "shape": shape_name}
                break
    return out