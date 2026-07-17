"""
backends.py — pluggable table-extraction backends. Each returns list[RawTable].

Design rules:
  * every backend is optional and self-isolating: it imports its heavy dependency
    lazily inside .extract(), so a machine missing (say) Docling can still run the
    pdfplumber + docx backends;
  * no backend filters by content — it returns EVERY table it can find;
  * PDFs are meant to be run through SEVERAL backends; reconcile.py cross-checks
    them. That's the whole point — no single tool is trusted alone.

Backends provided:
  PdfPlumberBackend  — pdfplumber's own table finder (lines + text strategies).
                       Good at ruled/dense tables (the GLMM stats tables).
  GeometryBackend    — word x-position clustering. Good at clean BORDERLESS
                       tables (species×trait) where pdfplumber's text strategy
                       over-splits.
  DocxBackend        — python-docx. Word tables are real cells (no OCR).
  XlsxBackend        — openpyxl. Spreadsheet supplements.
  DoclingBackend     — Docling layout+TableFormer (adapter; enable where present).
  MineruBackend      — hosted MinerU markdown (adapter; needs MINERU_TOKEN).

Use `backends_for(path, enable=...)` to get the right set for a file.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

from table_ir import RawTable, normalize_grid


class Backend:
    name = "base"
    exts: tuple = ()

    def available(self) -> bool:
        return True

    def extract(self, path: str) -> List[RawTable]:
        raise NotImplementedError


# ===========================================================================
# PDF table DETECTION (where is a table?) — separated from reading (what's in
# it?). Detection is the fix for the 36-tables-from-a-7-table-paper bug: readers
# used to run on every page; now they only read detected regions.
# ===========================================================================

_CAPTION = re.compile(r"^\s*table\s*\d", re.IGNORECASE)          # "Table 5" / "Table5"
_FIGCAP = re.compile(r"^\s*(fig(ure)?|appendix|scheme|plate)\b", re.IGNORECASE)
_RUNHEAD_TEXT = re.compile(r"^(©|doi|https?:)", re.IGNORECASE)


def _is_furniture(ln, page_height):
    """Page furniture = running heads, DOIs, and bare page numbers. A bare number
    only counts if it sits in the top/bottom margin — inside the body a lone
    number is a DATA CELL (e.g. the 'Species number' column), and discarding it
    silently corrupts the table."""
    txt = _ltext(ln)
    if _RUNHEAD_TEXT.match(txt):
        return True
    if len(txt) < 2:
        return True
    if txt.strip().isdigit():
        top = min(w["top"] for w in ln)
        return top < page_height * 0.08 or top > page_height * 0.92
    return False


def _page_lines(page):
    """Group words into visual lines. Uses a tolerance derived from text height
    and merges words that vertically overlap, because a column can sit on a
    slightly different baseline (e.g. Barber's 'Species number' column) and a
    rigid y-bucket would split it onto a phantom row of its own."""
    words = page.extract_words(use_text_flow=False)
    if not words:
        return []
    heights = sorted(w["bottom"] - w["top"] for w in words)
    tol = max(3.0, heights[len(heights) // 2] * 0.6)
    lines = []
    for w in sorted(words, key=lambda w: (w["top"], w["x0"])):
        placed = False
        for ln in lines:
            ref = ln[0]
            if abs(w["top"] - ref["top"]) <= tol:
                ln.append(w)
                placed = True
                break
        if not placed:
            lines.append([w])
    lines.sort(key=lambda ln: min(w["top"] for w in ln))
    return [sorted(ln, key=lambda w: w["x0"]) for ln in lines]


def _ltext(ln):
    return " ".join(w["text"] for w in ln)


def _peak_bounds(lines):
    """Column separators from x0 positions recurring across the region's lines."""
    from collections import Counter
    bins, n = Counter(), 0
    for ln in lines:
        n += 1
        for b in {round(w["x0"] / 3) * 3 for w in ln}:
            bins[b] += 1
    if not n:
        return []
    peaks = sorted(b for b, c in bins.items() if c >= max(2, n * 0.35))
    edges = []
    for p in peaks:
        if not edges or p - edges[-1] >= 8:
            edges.append(p)
    return [(edges[i] + edges[i + 1]) / 2 for i in range(len(edges) - 1)]


def _assign(ln, bounds):
    cells = [""] * (len(bounds) + 1)
    for w in sorted(ln, key=lambda w: w["x0"]):
        col = next((i for i, b in enumerate(bounds) if w["x0"] < b), len(bounds))
        cells[col] = (cells[col] + " " + w["text"]).strip()
    return cells


def _is_wide_prose(ln, page_width):
    """A full-width running sentence (one cell spanning most of the page) — the
    signal that the table has ended and body text resumed."""
    if not ln:
        return True
    span = max(w["x1"] for w in ln) - min(w["x0"] for w in ln)
    big_gaps = sum(1 for a, b in zip(ln, ln[1:]) if b["x0"] - a["x1"] > 22)
    return span > page_width * 0.62 and big_gaps < 2


def detect_regions(pdf):
    """Return caption-anchored table regions across the whole PDF, each as a list
    of (page_index, line) rows *below* a 'Table N' caption, stopping at the next
    caption/figure or a run of prose. Multi-page tables are captured because the
    scan continues onto following pages until a stop condition."""
    pages_lines = [_page_lines(p) for p in pdf.pages]
    page_widths = [p.width for p in pdf.pages]
    page_heights = [p.height for p in pdf.pages]

    # flat stream of (page, line_index, line) with caption flags
    stream = []
    for pno, lines in enumerate(pages_lines):
        for li, ln in enumerate(lines):
            stream.append((pno, li, ln))

    cap_positions = [k for k, (_, _, ln) in enumerate(stream)
                     if _CAPTION.match(_ltext(ln))]

    regions = []
    for ci in cap_positions:
        rows = []
        prose_run = 0
        started = False
        cap_page = stream[ci][0]
        for k in range(ci + 1, len(stream)):
            pno, li, ln = stream[k]
            txt = _ltext(ln)
            if _CAPTION.match(txt) or _FIGCAP.match(txt):
                break
            if _is_furniture(ln, page_heights[pno]):
                continue                                   # skip page furniture
            if _is_wide_prose(ln, page_widths[pno]):
                # A repeated column header at the top of a continuation page can
                # look like prose. Only treat prose as the table's end once we
                # are past the first few lines of a page.
                if li <= 3 and pno > cap_page:
                    continue
                prose_run += 1
                if started and prose_run >= 2:
                    break                                  # table body ended
                continue
            prose_run = 0
            started = True
            rows.append((pno, ln))
        if len(rows) >= 2:
            regions.append(rows)
    return regions


def _region_grid(rows):
    """Turn a region's (page, line) rows into an aligned grid.

    Columns come from the DATA rows, not the header: a stacked multi-line header
    ("Wing" over "morphology") puts words at x-positions no data row uses, which
    invents a phantom column and shifts every value one cell right.

    Data rows are taken as the lower ~80% of the region (headers sit at the top)
    with at least as many words as the median. The fallback is always the full
    line set, so this heuristic can never make a region disappear."""
    lines = [ln for _, ln in rows]
    if len(lines) >= 6:
        body = lines[max(1, len(lines) // 6):]        # skip the header band
        counts = sorted(len(ln) for ln in body)
        med = counts[len(counts) // 2] if counts else 0
        data = [ln for ln in body if len(ln) >= med] or body
    else:
        data = lines
    bounds = _peak_bounds(data)
    grid = [_assign(ln, bounds) for ln in lines]
    return normalize_grid(grid)


# ---------------------------------------------------------------------------
# Geometry backend — reads detected regions with word-position clustering
# ---------------------------------------------------------------------------

class GeometryBackend(Backend):
    name = "geometry"
    exts = (".pdf",)

    def available(self) -> bool:
        try:
            import pdfplumber  # noqa
            return True
        except ImportError:
            return False

    def extract(self, path: str) -> List[RawTable]:
        import pdfplumber
        out = []
        with pdfplumber.open(path) as pdf:
            for rows in detect_regions(pdf):
                grid = _region_grid(rows)
                if len(grid) >= 2 and len(grid[0]) >= 2:
                    out.append(RawTable(grid, "geometry", path,
                                        page=rows[0][0]))
        return out


# ---------------------------------------------------------------------------
# pdfplumber-lines backend — reads RULED tables inside detected regions only
# ---------------------------------------------------------------------------

class PdfPlumberBackend(Backend):
    name = "pdfplumber-lines"
    exts = (".pdf",)

    def available(self) -> bool:
        try:
            import pdfplumber  # noqa
            return True
        except ImportError:
            return False

    def extract(self, path: str) -> List[RawTable]:
        import pdfplumber
        settings = {"vertical_strategy": "lines", "horizontal_strategy": "lines"}
        out = []
        with pdfplumber.open(path) as pdf:
            # only read ruled tables that fall within a detected region's pages,
            # so we never resurrect prose as a "table"
            region_pages = {r[0][0] for r in detect_regions(pdf)}
            for pno in region_pages:
                page = pdf.pages[pno]
                try:
                    for t in page.find_tables(settings):
                        grid = t.extract()
                        if grid and sum(any(c for c in r) for r in grid) >= 2:
                            out.append(RawTable(grid, "pdfplumber-lines",
                                                path, pno, t.bbox))
                except Exception:
                    continue
        return out


# ---------------------------------------------------------------------------
# Word / Excel — already-structured, no OCR
# ---------------------------------------------------------------------------

class DocxBackend(Backend):
    name = "docx"
    exts = (".docx",)

    def available(self) -> bool:
        try:
            import docx  # noqa
            return True
        except ImportError:
            return False

    def extract(self, path: str) -> List[RawTable]:
        from docx import Document
        doc = Document(str(path))
        out = []
        for ti, tbl in enumerate(doc.tables):
            grid = [[c.text for c in row.cells] for row in tbl.rows]
            if any(any(x.strip() for x in r) for r in grid):
                out.append(RawTable(grid, "docx", path, None, meta={"table_index": ti}))
        return out


class XlsxBackend(Backend):
    name = "xlsx"
    exts = (".xlsx", ".xls")

    def available(self) -> bool:
        try:
            import openpyxl  # noqa
            return True
        except ImportError:
            return False

    def extract(self, path: str) -> List[RawTable]:
        import openpyxl
        wb = openpyxl.load_workbook(path, data_only=True)
        out = []
        for ws in wb.worksheets:
            grid = [[("" if c is None else c) for c in row]
                    for row in ws.iter_rows(values_only=True)]
            if any(any(str(x).strip() for x in r) for r in grid):
                out.append(RawTable(grid, "xlsx", path, None, meta={"sheet": ws.title}))
        return out


# ---------------------------------------------------------------------------
# Docling — layout model + TableFormer (adapter; enable where installed)
# ---------------------------------------------------------------------------

class DoclingBackend(Backend):
    name = "docling"
    exts = (".pdf", ".docx")

    def available(self) -> bool:
        try:
            import docling  # noqa
            return True
        except ImportError:
            return False

    def extract(self, path: str) -> List[RawTable]:
        from docling.document_converter import DocumentConverter
        from table_parser import from_html          # reuse HTML->grid
        conv = DocumentConverter(format_options=self._format_options())
        doc = conv.convert(path).document
        out = []
        for ti, table in enumerate(getattr(doc, "tables", []) or []):
            try:
                # newer Docling wants the doc; older signature takes none
                try:
                    html = table.export_to_html(doc=doc)
                except TypeError:
                    html = table.export_to_html()
                grid = from_html(html)
            except Exception:
                continue
            if grid:
                page = None
                prov = getattr(table, "prov", None)
                if prov:
                    page = getattr(prov[0], "page_no", None)
                out.append(RawTable(grid, "docling", path, page,
                                    meta={"table_index": ti}))
        return out

    @staticmethod
    def _format_options():
        """Docling defaults rasterize every page and load an OCR model. On a
        born-digital PDF both are pure waste, and on a long document the page
        images exhaust RAM (`std::bad_alloc` in native preprocessing, or a CUDA
        OOM on GPU). Turn them off. Returns {} if the options API differs, so a
        version mismatch degrades to defaults rather than crashing."""
        try:
            from docling.document_converter import PdfFormatOption
            from docling.datamodel.pipeline_options import PdfPipelineOptions
        except ImportError:
            return {}
        opts = PdfPipelineOptions()
        for attr, val in (("do_ocr", False),
                          ("generate_page_images", False),
                          ("generate_picture_images", False),
                          ("generate_table_images", False),
                          ("images_scale", 1.0)):
            if hasattr(opts, attr):
                setattr(opts, attr, val)
        opts.do_table_structure = True            # this is the part we want
        return {"pdf": PdfFormatOption(pipeline_options=opts)}


# ---------------------------------------------------------------------------
# MinerU — hosted markdown (adapter; needs MINERU_TOKEN + mineru_api.py)
# ---------------------------------------------------------------------------

class MineruBackend(Backend):
    name = "mineru"
    exts = (".pdf",)

    def available(self) -> bool:
        import os
        try:
            import mineru_api  # noqa
        except ImportError:
            return False
        return bool(os.environ.get("MINERU_TOKEN"))

    def extract(self, path: str) -> List[RawTable]:
        import os
        import mineru_api
        from table_parser import from_html
        md = mineru_api.extract_one(path, os.environ["MINERU_TOKEN"])
        if not md:
            return []
        out = []
        for i, block in enumerate(re.findall(r"<table.*?</table>", md,
                                             flags=re.DOTALL | re.IGNORECASE)):
            grid = from_html(block)
            if grid:
                out.append(RawTable(grid, "mineru", path, None, meta={"block": i}))
        return out


# ---------------------------------------------------------------------------
# registry
# ---------------------------------------------------------------------------

ALL_BACKENDS = [PdfPlumberBackend(), GeometryBackend(), DocxBackend(),
                XlsxBackend(), DoclingBackend(), MineruBackend()]


def backends_for(path, enable=None) -> List[Backend]:
    """Return the available backends that handle this file type. `enable` (a set
    of backend names) restricts the set; None = all available."""
    ext = Path(path).suffix.lower()
    picked = []
    for b in ALL_BACKENDS:
        if ext not in b.exts:
            continue
        if enable is not None and b.name not in enable:
            continue
        if b.available():
            picked.append(b)
    return picked