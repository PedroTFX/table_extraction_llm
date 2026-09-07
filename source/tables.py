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


_UNIT_WORDS = {
    "mm", "cm", "dm", "m", "km", "\u00b5m", "um", "nm", "\u00e5", "ha",
    "g", "kg", "mg", "\u00b5g", "ug", "ng", "t", "lb", "oz",
    "mol", "mmol", "\u00b5mol", "ml", "l", "dl", "cc",
    "s", "sec", "ms", "min", "h", "hr", "d", "day", "days", "wk", "mo", "yr",
    "%", "\u2030", "ppm", "ppt", "bp", "kb", "mb",
    "k", "j", "kj", "w", "v", "ph", "rpm", "lux", "\u00b0c", "\u00b0f",
}
_UNIT_DIM_RE = re.compile(
    r"^[a-z\u00b5]{1,3}([\u00b2\u00b3]|\^?\d)(\s*/\s*[a-z\u00b50-9\u00b2\u00b3.]+)?$"
    r"|^[a-z\u00b5]{1,4}\s*/\s*[a-z\u00b50-9\u00b2\u00b3.]+$"
    r"|^[%\u2030\u00b0]",
    re.IGNORECASE)


def _is_unit_token(v: str) -> bool:
    v = v.strip()
    if not v:
        return False
    if v.startswith("(") and v.endswith(")"):
        return True
    if v.lower() in _UNIT_WORDS:
        return True
    return bool(_UNIT_DIM_RE.match(v))


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
    unit_like = sum(1 for v in rest if _is_unit_token(v))
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


def _looks_numeric(v: str) -> bool:
    v = v.strip().replace(",", "")
    if not v:
        return False
    try:
        float(v.split()[0].replace("\u00b1", " ").split()[0])
        return True
    except (ValueError, IndexError):
        return False


def _defuse_repeated_header(cells, columns, min_frac=0.6):
    """A page break can glue a repeated column-header line onto a data row, e.g.
    header ['', 'Site', 'AG', ...] fused into a body row as
           ['', '2015Site', '0AG', ...]. Detect (a majority of populated cells
    end with their own column's header text, leaving a non-empty prefix) and
    split back into the underlying DATA row. Returns recovered cells or None."""
    hdr = [c.raw.strip() for c in columns]
    hits = checked = 0
    for i, cell in enumerate(cells):
        if i >= len(hdr):
            break
        v = (cell or "").strip(); h = hdr[i]
        if not v:
            continue
        checked += 1
        if h and len(h) >= 2 and v != h and v.lower().endswith(h.lower()) \
                and v[: len(v) - len(h)].strip():
            hits += 1
    if not (checked and hits / checked >= min_frac and hits >= 2):
        return None
    out = list(cells)
    for i, cell in enumerate(cells):
        if i >= len(hdr):
            break
        v = (cell or "").strip(); h = hdr[i]
        if h and v != h and v.lower().endswith(h.lower()):
            out[i] = v[: len(v) - len(h)].strip()
        else:
            out[i] = v
    return out


def _salvage_identifier_columns(columns, body_rows, ncols):
    """Rescue a blank-header column that actually holds the row identifiers.

    A well-formed table names its key column ('Species', 'Taxon', ...), but MinerU
    often drops that top-left header cell, so the column arrives blank-headered,
    is marked synthetic, and is silently discarded — even though its cells ARE the
    identifiers. We recover it STRUCTURALLY, without knowing what the values mean:
    the identifier is the row-LABEL column — the leftmost synthetic column whose
    cells are populated and mostly text, as opposed to the numeric value columns
    to its right.

    Distinctness is deliberately NOT required. A real key repeats whenever rows
    are grouped — a family spanning 'Mean' and 'Range' sub-rows (a rowspan), a
    genus heading several species — and the old 'mostly distinct' test threw those
    away. Text-vs-numeric is the honest signal for label-vs-value; position
    (leftmost) resolves which text column is the primary key when a secondary
    label column (e.g. a 'Mean'/'Range' dimension) is also present, per table
    convention. That secondary column is left for the mapper to interpret.

    Runs BEFORE record assembly/anchor selection; flips only the `synthetic` flag."""
    for col in columns:
        if not col.synthetic:
            return                         # a real (header-named) identifier exists
        vals = []
        for cells in body_rows:
            v = cells[col.index].strip() if col.index < len(cells) else ""
            vals.append(v)
        nonempty = [v for v in vals if v]
        if len(nonempty) < max(2, len(vals) // 2):
            continue                       # too sparse to be the identifier
        nonnumeric = sum(1 for v in nonempty if not _looks_numeric(v))
        if nonnumeric / len(nonempty) < 0.7:
            continue                       # mostly numbers -> a value column, not labels
        if len(set(nonempty)) < 2:
            continue                       # a single repeated constant is not an identifier
        col.synthetic = False
        # give it a real, neutral name so (a) the LLM mapper doesn't see a
        # literal '__col0' header and (b) it can't be mistaken for a meta key
        # (record meta uses '_'-prefixed keys). Disambiguate on the off chance
        # 'identifier' already exists.
        existing = {c.name for c in columns if c is not col}
        new_name = "identifier"
        k = 2
        while new_name in existing:
            new_name = f"identifier ({k})"; k += 1
        col.name = new_name
        return


def _find_header_line(lines):
    """Return the index of the real header line, skipping leading caption/title
    and blank rows that MinerU sometimes places *inside* a <table> above the true
    header (e.g. 'Table S6. Overview of all 79 species...' as row 0, a blank row,
    then the real 'Species | Bodysize (mm) | ...' header). Only skips a leading
    row when it is clearly NOT a header: fully empty, OR a single populated cell
    among several empty ones (a caption/title spanning the row), OR one long prose
    cell (>=80 chars, caption-like). Stops at (and returns) the first row that
    looks like a real header: two or more populated cells that are short labels.
    Conservative — if nothing looks better, it stays at row 0."""
    def cells(i):
        return [c.strip() for c in _split_row(lines[i])]
    n = len(lines)
    for i in range(n):
        cs = cells(i)
        nonempty = [c for c in cs if c]
        if not nonempty:
            continue                                   # blank row -> skip
        # caption/title: a single cell (often long prose) among empties
        if len(nonempty) == 1 and (len(cs) > 2 or len(nonempty[0]) >= 80):
            continue                                   # caption row -> skip
        # full-width BANNER: the populated cells other than the identifier column
        # are all the SAME label spanning the row (a section title like 'Traits'
        # or 'Morphological trait' that a converter emits as one colspan or N
        # identical <td>s). Taking it as the header makes every value column that
        # one label and pushes the REAL header down into the data. Skip it so the
        # true header below is chosen. The identifier cell (column 0) is excluded
        # from the sameness test because a real table names its id column there
        # ('Species') right beside the banner. Require >=3 identical trait cells
        # and a non-numeric label so a data row of repeated values is never a
        # banner.
        # The identifier cell (column 0) is excluded from the sameness test ONLY
        # when it differs from the banner label — a real table names its id column
        # ('Species') beside the banner. When column 0 IS the banner label
        # (Espinosa's 'Traits | Traits | Traits'), keep it in the test.
        if len(nonempty) > 1 and cs and cs[0].strip() and cs[0].strip() != nonempty[1]:
            banner_cells = nonempty[1:]
        else:
            banner_cells = nonempty
        if (len(banner_cells) >= 3 and len(set(banner_cells)) == 1
                and not _looks_numeric(banner_cells[0])
                and i + 1 < n and len([c for c in cells(i + 1) if c]) >= 2):
            continue                                   # banner row -> skip
        return i                                       # first dense row = header
    return 0


def _looks_numeric(s: str) -> bool:
    return bool(re.match(r"^[-+]?[\d.,]+\s*%?$", str(s).strip()))


_BINOMIAL_RE = re.compile(r"\b([A-Z][a-z]{2,})\s+([a-z]{3,})\b")
_ABBREV_BINOMIAL_RE = re.compile(r"\b([A-Z])\.\s*([a-z]{3,})\b")


def find_binomial_candidates(text: str, top: int = 8) -> list:
    """Rank 'Genus species' candidates in a paper's text, deterministically.

    For a single-species paper the study organism never appears in a table
    column — it is stated in the title/abstract and then referred to throughout —
    so the tables have no identifier column and are dropped. This recovers the
    candidates so a later step can attribute the tables to a species.

    Nothing is hardcoded and no species list is consulted; ranking uses three
    signals that any paper provides:

      * ABBREVIATION SUPPORT (weighted heaviest) — a real binomial gets written
        out once and abbreviated after: 'Halictus ligatus' ... 'H. ligatus'. An
        accidental capitalised word pair ('The following') is never abbreviated
        that way, so this alone separates species from prose noise.
      * FREQUENCY — the study organism is mentioned repeatedly.
      * HEAD POSITION — title/abstract mentions count extra.

    Returns [{name, mentions, abbrev_mentions, score}] best first.
    """
    if not text:
        return []
    counts: dict = {}
    for m in _BINOMIAL_RE.finditer(text):
        key = (m.group(1), m.group(2))
        counts[key] = counts.get(key, 0) + 1
    abbrev: dict = {}
    for m in _ABBREV_BINOMIAL_RE.finditer(text):
        key = (m.group(1), m.group(2))
        abbrev[key] = abbrev.get(key, 0) + 1

    head = text[:3000].lower()
    scored = []
    for (genus, epithet), n in counts.items():
        ab = abbrev.get((genus[0], epithet), 0)
        score = n + 5 * ab + (3 if f"{genus.lower()} {epithet}" in head else 0)
        scored.append((score, n, ab, f"{genus} {epithet}"))
    scored.sort(key=lambda x: (-x[0], -x[1], x[3]))
    return [{"name": nm, "mentions": n, "abbrev_mentions": ab, "score": sc}
            for sc, n, ab, nm in scored[:top]]


def _numeric_profile(rows: list, ncols: int) -> list:
    """Which column positions are predominantly numeric across these rows."""
    prof = []
    for c in range(ncols):
        vals = [r[c] for r in rows if c < len(r) and str(r[c]).strip()]
        if not vals:
            prof.append(False)
            continue
        prof.append(sum(_looks_numeric(v) for v in vals) >= len(vals) * 0.7)
    return prof


def is_headerless_continuation(prev: "Table", raw_text: str) -> bool:
    """True if `raw_text` is the CONTINUATION of `prev` across a page break, with
    no header of its own.

    A long species table split over pages arrives as several <table> blocks, and
    the later blocks usually do not repeat the header — they start straight at a
    data row ('Paradromius linearis | 4 | 3 | carnivorous | 4.5'). parse_table
    would take that first species as the header, losing it AND giving the fragment
    a nonsense schema that never groups with its parent, so every species in the
    fragment silently disappears.

    Detection is deterministic and deliberately conservative — all must hold:
      1. same column count as `prev` (allowing a trailing-pipe off-by-one);
      2. `prev` has at least one column that is numeric in its DATA — the
         signature we can test the fragment's first row against;
      3. the fragment's first row is numeric in those same positions, i.e. it
         reads as DATA, not as labels (a real header puts text in those columns);
      4. the first row does NOT reuse `prev`'s header vocabulary — that would be
         a REPEATED header, which the parser already handles, not a continuation.
    """
    if prev is None or not prev.columns:
        return False
    lines = [l for l in (ln.strip() for ln in raw_text.strip().splitlines()) if l]
    if not lines:
        return False

    ncols = len(prev.columns)
    first = _split_row(lines[0])
    if abs(len(first) - ncols) > 1:                    # (1) width must match
        return False
    first = (first + [""] * ncols)[:ncols]

    prev_rows = [[str(r.get(c.name, "")) for c in prev.columns]
                 for r in prev.data_records()]
    if not prev_rows:
        return False
    prof = _numeric_profile(prev_rows, ncols)
    if not any(prof):                                  # (2) need a numeric signature
        return False

    for c, isnum in enumerate(prof):                   # (3) first row must be data
        if isnum and first[c].strip() and not _looks_numeric(first[c]):
            return False

    # (3b) ...and it must POSITIVELY carry data: at least one of prev's numeric
    # columns holds a real number in this first row. Condition (3) only rejects a
    # NON-numeric value in a numeric column; an EMPTY one slips through, so a row
    # that is blank across the numeric columns — a caption ('Table S1. ...'), a
    # section band, a blank separator — passes (3) vacuously and the whole block
    # gets mis-attached as a continuation. That is exactly how Uemori2022's Table
    # S1 (its own species table, first row the caption) was swallowed by the
    # preceding stats table and every species lost. A genuine continuation starts
    # on a real data row and clears this trivially.
    if not any(isnum and c < len(first) and _looks_numeric(first[c])
               for c, isnum in enumerate(prof)):
        return False

    hdr_tokens = {w for col in prev.columns
                  for w in re.findall(r"[a-z]+", col.name.lower())}
    row_tokens = [w for v in first for w in re.findall(r"[a-z]+", str(v).lower())]
    if row_tokens and hdr_tokens:                      # (4) not a repeated header
        if sum(w in hdr_tokens for w in row_tokens) / len(row_tokens) >= 0.6:
            return False
    return True


def parse_table(table: str, source: Optional[str] = None, table_index: int = 0,
                merge_subheaders: bool = True,
                header_override: Optional[list] = None,
                header_rows: Optional[dict] = None) -> Table:
    """Parse one cleaned pipe-table into a fully-aligned :class:`Table`.

    Tolerant of: trailing pipes, ragged rows (short rows pad with '', long rows
    truncate), blank/merged header cells, footnote markers and nbsp in headers.
    If ``merge_subheaders`` and the second row is a units/continuation row (e.g.
    '| (mm) | (mm) |'), it is folded into the header instead of becoming data.

    ``header_override`` supplies the header from OUTSIDE the text, for a page
    continuation fragment that carries no header of its own (see
    is_headerless_continuation). Every line is then treated as data, so the first
    species is not eaten as a header row.
    """
    lines = [l for l in (ln.strip() for ln in table.strip().splitlines()) if l]
    if not lines:
        return Table(columns=[], raw=table, source=source, table_index=table_index)

    if header_override:
        columns = _build_columns(list(header_override))
        ncols = len(columns)
        body_start = 0                                 # no header line to consume
    elif header_rows and header_rows.get("header_rows"):
        # LLM-driven header selection (full replacement of the deterministic
        # finder). `header_rows` is {"header_rows": [i,...], "join": bool} with
        # indices into `lines`. The CODE reads the cells at those rows and builds
        # the header; the model supplied only the row numbers, never any text.
        idxs = [i for i in header_rows["header_rows"] if 0 <= i < len(lines)]
        if not idxs:
            idxs = [0]
        first = min(idxs)
        if header_rows.get("join") and len(idxs) > 1:
            # vertical-join the selected header rows per column
            rows_cells = [_split_row(lines[i]) for i in idxs]
            width = max(len(r) for r in rows_cells)
            joined = []
            for c in range(width):
                parts = [r[c] for r in rows_cells if c < len(r) and r[c].strip()]
                joined.append(" ".join(parts))
            columns = _build_columns(joined)
        else:
            # single header row = the LAST selected row (banner rows above it are
            # dropped); everything above the header is caption/banner, skipped.
            columns = _build_columns(_split_row(lines[max(idxs)]))
        ncols = len(columns)
        body_start = max(idxs) + 1
    else:
        hdr_i = _find_header_line(lines)
        if hdr_i > 0:
            lines = lines[hdr_i:]                      # drop caption/blank rows above header
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

    # Rescue a dropped-corner identifier column before choosing the anchor, so
    # the anchor lands on the real identifier rather than the next column over.
    _raw_body = [_split_row(l) for l in lines[body_start:]]
    _salvage_identifier_columns(columns, _raw_body, ncols)

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

        defused = _defuse_repeated_header(cells, columns)
        if defused is not None:
            cells = defused

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
    # Index candidate legend SEGMENTS by footnote marker. A single line often
    # carries several legends in a row, e.g.
    #   "\u2020P, polyphagous; ... . \u2021A, arboreal; ... \u00a7B, bait; ..."
    # so we split each line at EVERY marker occurrence (not just the leading one)
    # and file each segment under its own marker. Indexing only the leading marker
    # would dump all codes under the first column and starve the others.
    marker_lines: dict[str, list[str]] = {}
    for line in text.splitlines():
        ls = line.strip()
        if not ls:
            continue
        # legend definitions are prose lines; skip table markup, where a column
        # header's own footnote marker (e.g. 'Microhabitat found\u00a7') would
        # otherwise be mis-read as a legend and capture cell HTML.
        if "<td" in ls or "<tr" in ls or "<table" in ls:
            continue
        # positions of every footnote marker in the line
        hits = [(m.start(), m.group()) for m in _FOOTNOTE_RE.finditer(ls)]
        if not hits:
            continue
        for i, (pos, mark) in enumerate(hits):
            end = hits[i + 1][0] if i + 1 < len(hits) else len(ls)
            segment = ls[pos:end].strip()
            marker_lines.setdefault(mark, []).append(segment)

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
    """Shape: 'full term (ABBR)'  e.g. 'intertegular distance (ITD)'.

    The term is the phrase IMMEDIATELY before '(ABBR)'. In a methods sentence that
    lists many pairs — 'scape length (SL), femur length (FL), ...' — the window
    must not reach back across the previous clause, or Schwartz-Hearst matches a
    garbled span crossing the earlier abbreviation ('femur length' bleeding into
    '...scape length SL ... femur length'). So cut the context at the last
    clause/paren boundary before the match."""
    for m in re.finditer(r"\(\s*" + re.escape(token) + r"\s*\)", text):
        context = text[:m.start()]
        cut = max((context.rfind(ch) for ch in ",;.:()"), default=-1)
        if cut != -1:
            context = context[cut + 1:]            # keep only the current clause
        words = re.findall(r"[A-Za-z][A-Za-z\-]*", context)
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
    # The raw paper still has inline HTML (<sup> footnote markers, entities); the
    # word-extraction below would otherwise pick up a tag name as a word — e.g.
    # 'mandible<sup></sup> length (ML)' resolving ML to 'mandible sup sup length'.
    from text_manager import strip_inline_markup
    text = strip_inline_markup(text)
    for token in dict.fromkeys(t for t in tokens if t):
        for shape_name, fn in _ABBREV_SHAPES:
            term = fn(token, text)
            if term:
                out[token] = {"term": term, "shape": shape_name}
                break
    return out

# ---------------------------------------------------------------------------
# Multi-value cells
# ---------------------------------------------------------------------------
# A cell may hold a LIST ('W, S, P' — three legend codes) or a single value that
# merely CONTAINS a comma ('Coras montanus (Emerton, 1890a) (Agelenidae)' — one
# host spider, with a taxonomic authority). Splitting the second produces two
# half-rows, each with a fragment of a name as its measurementValue.
#
# Nothing here knows about taxonomy. Two general facts do the work:
#   * a comma inside brackets or quotes is part of the enclosed expression, not a
#     separator — true of authorities, ranges, and parenthetical asides alike;
#   * a comma between digits with no space is a decimal/thousands separator.
# And one column-level fact: a real list column shows the pattern in MANY of its
# cells, while a stray internal comma shows up in one or two.

_OPENERS = {"(": ")", "[": "]", "{": "}"}
_QUOTES = {'"', "'", "\u201c", "\u201d", "\u2018", "\u2019"}
_CLOSE_FOR = {v: k for k, v in _OPENERS.items()}


def _separator_positions(s: str) -> list:
    """Indices of commas that are genuine separators: at bracket depth 0, not
    inside quotes, and not sitting between two digits."""
    out, stack, quote = [], [], None
    for i, ch in enumerate(s):
        if quote is not None:
            if ch == quote or (quote in "\u201c\u2018" and ch in "\u201d\u2019"):
                quote = None
            continue
        if ch in _QUOTES:
            quote = ch
            continue
        if ch in _OPENERS:
            stack.append(ch)
            continue
        if ch in _CLOSE_FOR:
            if stack and stack[-1] == _CLOSE_FOR[ch]:
                stack.pop()
            continue
        if ch != ",":
            continue
        if stack:
            continue                                  # inside (...) / [...] / {...}
        if (i and s[i - 1].isdigit()
                and i + 1 < len(s) and s[i + 1].isdigit()):
            continue                                  # 1,200  or  3,5
        out.append(i)
    return out


def split_multivalue(value, allow=None) -> list:
    """Split a cell into its list items, or return it whole.

    ``allow`` is the column-level verdict from ``looks_multivalue_column``:
    True/False to force, None (unknown) to decide from the cell alone. Even when
    forced True the bracket/quote/digit rules still apply — a list column may
    well hold items that each contain an internal comma.

    Never returns an empty list, and never returns parts that are empty or
    whitespace: if the split would produce one, the value is kept intact (a
    trailing comma is punctuation, not a second item).
    """
    if not isinstance(value, str) or "," not in value or allow is False:
        return [value]
    cuts = _separator_positions(value)
    if not cuts:
        return [value]
    parts, prev = [], 0
    for i in cuts:
        parts.append(value[prev:i])
        prev = i + 1
    parts.append(value[prev:])
    parts = [p.strip() for p in parts]
    if any(not p for p in parts):
        return [value.strip()]
    return parts


# Function words that appear in free-text DESCRIPTIONS ('carton nests in
# cavities', 'galleries on tree trunks and branches') but not in value-lists or
# legend codes ('W, S, P'; 'H, M, A'). Their presence across a column is what
# tells a multi-clause description (whose commas are prose punctuation) apart
# from a real list (whose commas separate items). It is a GRAMMAR signal, not a
# length threshold: a genuine multi-word list ('standing dead wood, lying dead
# wood') has long fragments too, but carries no connectives, so it is not caught.
_PROSE_CONNECTIVES = re.compile(
    r"\b(?:in|on|under|over|above|below|against|at|with|within|into|onto|"
    r"of|the|a|an|and|or|near|between|among|through|around|beneath|"
    r"from|to|by|for)\b", re.IGNORECASE)


def _looks_like_prose_column(populated, prose_fraction: float = 0.5) -> bool:
    """True when a column holds free-text descriptions, so its commas must NOT be
    treated as list separators. Two structural signals:

      * SEMICOLONS — a column that uses ';' anywhere is using it as the item
        separator, which makes every ',' intra-clause punctuation.
      * CONNECTIVES — most cells carry prepositions/articles ('in', 'on',
        'against', 'the'): the grammar of prose. Legend codes and value-lists
        carry none, so this stays False for them even when a list item happens
        to be multi-word.
    """
    if any(";" in v for v in populated):
        return True
    hits = sum(1 for v in populated if _PROSE_CONNECTIVES.search(v))
    return hits >= max(1, len(populated) * prose_fraction)


def looks_multivalue_column(values, min_fraction: float = 0.3) -> bool:
    """Does this COLUMN hold lists?

    Decided over the whole column, which is the only place the answer is visible:
    a legend-coded trait column splits in cell after cell, whereas a name column
    has one or two cells whose comma is internal.

    Two ways to qualify, because a fraction alone is not enough:

      1. RECURRENCE OF THE PATTERN — the split shows up in a fraction of the
         populated cells. Strong evidence, and a single unusual cell can never
         reach it.

      2. RECURRENCE OF THE PARTS — a cell splits into parts, and at least one of
         those parts appears elsewhere in the SAME column as a value on its own.
         This rescues the common real case that (1) misses: a legend-coded column
         where only ONE species carries two codes ('H, M(o)' among cells of 'H',
         'M', 'A', 'S'). 'H' standing alone elsewhere proves the comma separates
         two of this column's own values rather than sitting inside one.
         It stays safe on name columns: splitting 'Coras montanus, Emerton 1890'
         yields parts that appear nowhere else as values, so it is not a list.

    Prose guard: a description column (e.g. nest architecture, 'large, triangular
    carton nests, polydomous') carries a comma in nearly every cell and would
    otherwise trip rule 1, shredding each description at its commas. Such columns
    are detected first (grammar, not length — see _looks_like_prose_column) and
    excluded before the positive rules run.
    """
    populated = [v for v in values if isinstance(v, str) and v.strip()]
    if not populated:
        return False

    if _looks_like_prose_column(populated):
        return False

    split_parts = {}
    for v in populated:
        parts = split_multivalue(v)
        if len(parts) > 1:
            split_parts[v] = parts
    if not split_parts:
        return False

    if len(split_parts) >= max(2, len(populated) * min_fraction):
        return True

    def key(s):
        return clean_text(s).casefold()

    singles = {key(v) for v in populated if v not in split_parts}
    return any(key(p) in singles
               for parts in split_parts.values() for p in parts)


# ---------------------------------------------------------------------------
# Transposed ("horizontal") tables: species across the HEADER, traits down the
# first column
# ---------------------------------------------------------------------------
# The pipeline assumes one row per specimen: an identifier column plus trait
# columns. Papers also publish the transpose — traits as rows, one column per
# species — which is structurally identical to a stats table as far as the
# mapper is concerned: no header cell names a species, so no identifier column is
# found, every table is dropped as "not specimen data", and the paper yields zero
# rows. Rotating the grid before mapping turns it back into the shape every later
# stage already handles, so nothing downstream changes.
#
# Detection is COMPARATIVE, not absolute: measure how taxon-like the header is
# against how taxon-like the first column is, and rotate only when the header
# clearly wins. That is what makes it safe — in a normal table the first column
# holds the species and the header holds traits, so the same test says "no" for
# the same reason it says "yes" here.

# Second word of an apparent binomial that is really a measurement noun. Without
# this, 'Body length' and 'Wing width' parse as Genus+epithet and a perfectly
# normal header would be judged a list of species.
_TRAIT_WORDS = {
    "length", "width", "height", "depth", "mass", "weight", "size", "count",
    "number", "ratio", "index", "area", "volume", "diameter", "circumference",
    "color", "colour", "type", "group", "range", "mean", "median", "mode",
    "min", "max", "minimum", "maximum", "total", "density", "duration", "time",
    "date", "rate", "score", "level", "stage", "class", "value", "distance",
    "breadth", "span", "load", "cover", "richness", "abundance", "biomass",
    "activity", "behavior", "behaviour", "season", "period", "temperature",
    "humidity", "treatment", "site", "plot", "sample", "diet", "guild",
    "status", "location", "position", "shape", "pattern", "form", "state",
    "error", "estimate", "deviation", "variance", "interval", "limit",
    "sociality", "voltinism", "nesting", "specificity", "openness", "extent",
    "placement", "symmetry", "hair", "pigment", "trait", "traits", "means",
}

_TAXON_BINOMIAL = re.compile(r"^[A-Z][a-z]{2,}\s+([a-z]{3,})\b")
_TAXON_ABBREV = re.compile(r"^[A-Z]\.\s*([a-z]{3,})\b")
_TAXON_SP = re.compile(r"^[A-Z][a-z]{2,}\s+sp{1,2}\.?\b", re.IGNORECASE)
# Family/order/suborder endings — a single capitalised word is a taxon name only
# if it carries one of these, which is what keeps 'Chicago' and 'Detroit' out.
_TAXON_RANK = re.compile(
    r"^[A-Z][a-z]{3,}(idae|inae|aceae|ini|oidea|ptera|formes|morpha|"
    r"odea|acea|ales)\b")
_PARENS = re.compile(r"\([^)]*\)")
_NEQ = re.compile(r"\bn\s*=\s*\d+", re.IGNORECASE)


def looks_like_taxon(s: object) -> bool:
    """Does this string name an organism (species, genus sp., or family/order)?

    Tolerant of the decoration real headers carry: a trailing sample size
    ('Hesperiidae(n=45)'), a taxonomic authority or subgenus in brackets
    ('Ogcodes pallidipennis (Loew, 1866)'), and abbreviated genera ('A. vilhenae'
    after the paper has written it out once).

    Deliberately NOT a taxonomy lookup — no name list is consulted, only shape,
    so it works on species the corpus has never seen. The one shape that needs
    excluding is Capitalised+lowercase where the second word is a measurement
    noun, since 'Body length' is indistinguishable from 'Genus species' by shape
    alone.
    """
    s = str(s or "").strip()
    if not s:
        return False
    s = _NEQ.sub(" ", _PARENS.sub(" ", s))
    s = re.sub(r"\s+", " ", s).strip(" ,;:")
    if not s:
        return False
    if _TAXON_RANK.match(s) or _TAXON_SP.match(s):
        return True
    for rx in (_TAXON_BINOMIAL, _TAXON_ABBREV):
        m = rx.match(s)
        if m and m.group(1).lower() not in _TRAIT_WORDS:
            return True
    return False


def taxon_fraction(values) -> float:
    """Fraction of populated values that name an organism."""
    vals = [v for v in values if str(v or "").strip()]
    if not vals:
        return 0.0
    return sum(looks_like_taxon(v) for v in vals) / len(vals)


def detect_transposed(table, min_header_frac: float = 0.6,
                      max_body_frac: float = 0.3, min_species_cols: int = 2):
    """Is this table rotated — species in the header, traits in the first column?

    Returns (verdict, evidence). The verdict needs BOTH halves of the comparison:
    the header (excluding its first cell) must be mostly taxon names AND the
    first column must be mostly not, so a normal specimen table can never
    qualify. `evidence` is returned either way for logging and for an optional
    LLM tie-break on the ambiguous middle.
    """
    cols = list(table.columns)
    recs = table.data_records()
    ev = {"header_frac": 0.0, "body_frac": 0.0, "n_species_cols": 0,
          "reason": ""}
    if len(cols) < 1 + min_species_cols or not recs:
        ev["reason"] = "too few columns or no data rows"
        return False, ev

    header_cells = [c.name for c in cols[1:]]
    first_col_values = [r.get(cols[0].name, "") for r in recs]

    ev["header_frac"] = taxon_fraction(header_cells)
    ev["body_frac"] = taxon_fraction(first_col_values)
    ev["n_species_cols"] = sum(looks_like_taxon(h) for h in header_cells)

    if ev["header_frac"] < min_header_frac:
        ev["reason"] = "header is not mostly taxon names"
        return False, ev
    if ev["body_frac"] > max_body_frac:
        ev["reason"] = "first column also looks like taxa — orientation unclear"
        return False, ev
    if ev["n_species_cols"] < min_species_cols:
        ev["reason"] = "fewer than two species columns"
        return False, ev
    ev["reason"] = "header names species, first column does not"
    return True, ev


def _pipe_safe(v: object) -> str:
    """A cell about to be written into a pipe table: no '|' (it would invent a
    column) and no newlines."""
    return re.sub(r"\s+", " ", str(v or "").replace("|", "/")).strip()


def transpose_table(table, identifier_header: str = "Species"):
    """Rotate a species-in-header table into one row per species.

    Rebuilds the grid as pipe text and re-parses it with :func:`parse_table`
    rather than hand-assembling Columns and records, so the rotated table is
    constructed by exactly the same code path as every other table (units-row
    folding, ragged padding, group-row flags) and cannot drift from it.
    Provenance (source, table_index) is preserved so ``table_id`` is unchanged
    and per-table mapping files keep their names.

    Trait names come from the first column and become the new headers; duplicates
    are suffixed rather than merged, because two rows with the same label are two
    distinct measurements (e.g. a 'Mean' and a 'Range' row both labelled 'Body
    length') and collapsing them would silently drop one.
    """
    cols = list(table.columns)
    recs = table.data_records()
    if not cols or not recs:
        return table

    first, others = cols[0], cols[1:]

    trait_names, seen = [], {}
    for i, r in enumerate(recs):
        name = _pipe_safe(r.get(first.name, "")) or f"trait{i + 1}"
        n = seen.get(name, 0) + 1
        seen[name] = n
        trait_names.append(name if n == 1 else f"{name} ({n})")

    lines = [" | ".join([identifier_header] + trait_names)]
    for c in others:
        row = [_pipe_safe(c.name)] + [_pipe_safe(r.get(c.name, "")) for r in recs]
        lines.append(" | ".join(row))

    return parse_table("\n".join(lines), source=table.source,
                       table_index=table.table_index)