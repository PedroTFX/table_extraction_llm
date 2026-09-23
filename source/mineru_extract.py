"""
mineru_extract.py — convert documents to Markdown with MinerU, and unite a whole
paper folder (main paper + complementary files) into ONE markdown the existing
pipeline can run on, while keeping the volunteer "results" spreadsheet aside as
ground truth.

Routing by type: MinerU 4.x reads Office documents natively, so pdf/image/pptx,
Word (.doc/.docx) AND spreadsheets (.xlsx/.xls) all go STRAIGHT to MinerU — no
more docx->PDF render step. csv/tsv are still embedded as HTML <table> blocks
(lossless via csv) because MinerU has no native csv reader.

Escape hatches (see the flags below): set DOCX_VIA_PDF=True to revert Word to the
old render-to-PDF path (Microsoft Word/docx2pdf, else LibreOffice), or
XLSX_VIA_MINERU=False to revert spreadsheets to the lossless openpyxl HTML embed.
The python-docx exact-table reader also remains available via docx_to_markdown.

Note on the PDF fallback's fidelity: LibreOffice headless can mangle complex
tables (see docx_vs_pdf_audit) — Microsoft Word via docx2pdf renders them
faithfully and is preferred when present.

File roles inside a paper folder (folder is named after the paper):
  - main paper   : the non-_S document (PDF preferred)
  - results (GT) : the spreadsheet whose stem == the main's stem (e.g. X.xlsx
                   next to X.pdf) -> NOT a source; returned for evaluation
  - complementary: everything else (any _S* file, AND any .docx, etc.)

Converted markdown is named after the FULL source filename (X.pdf.md, X.docx.md)
so a docx and pdf that share a stem never collide.

Requires:  pip install "mineru[all]"   and  mineru-models-download  (first run)
"""

from __future__ import annotations

import csv as _csv
import html as _html
import os
import re
import shutil
import subprocess
import tempfile
import unicodedata
from pathlib import Path

import openpyxl

# Types MinerU converts to markdown natively (MinerU 4.x reads Office files too).
MINERU_DOC_EXTS = {".pdf", ".pptx", ".png", ".jpg", ".jpeg"}
# Word documents (legacy .doc + .docx). By default these go STRAIGHT to MinerU 4.x
# (which reads .docx/.doc natively); set DOCX_VIA_PDF=True to revert to the old
# render-to-PDF path (see office_to_markdown).
WORD_EXTS = {".doc", ".docx"}
# Spreadsheets. By default sent to MinerU 4.x (XLSX_VIA_MINERU); set that False to
# revert to the lossless openpyxl HTML embed (see xlsx_to_html_tables).
SPREADSHEET_EXTS = {".xlsx", ".xls"}

# Revert .doc/.docx to the old render-to-PDF + MinerU path (True) instead of
# feeding them to MinerU 4.x directly (False, the default now that MinerU reads
# Word natively). The python-docx exact-table reader also stays available via
# docx_to_markdown.
DOCX_VIA_PDF = False
# Send .xlsx/.xls to MinerU 4.x (True, default) or fall back to the lossless
# openpyxl HTML embed (False). The embed path also runs the date-ratio repair
# (see xlsx_to_html_tables / REPAIR_DATE_RATIOS), which MinerU does not.
XLSX_VIA_MINERU = True
# Types embedded directly as HTML tables (read losslessly, not via MinerU).
NATIVE_TABLE_EXTS = {".csv", ".tsv"}
# Already text/markup.
TEXT_EXTS = {".md", ".html", ".htm", ".txt"}
# Types eligible to be the MAIN document (never docx/pptx — those are always
# complementary — and never a spreadsheet).
MAIN_DOC_EXTS = {".pdf", ".html", ".htm"}

_SUPP_RE = re.compile(r"_S\d+$", re.IGNORECASE)   # e.g. X_S1, X_S2


# ---------------------------------------------------------------------------
# MinerU conversion
# ---------------------------------------------------------------------------

def doc_to_markdown(doc_path, backend="vlm", lang="en", force=False, extra_args=None):
    """Convert one PDF/image to Markdown via MinerU's HOSTED v4 API (VLM backend),
    named after the FULL source filename (e.g. X.pdf -> X.pdf.md) to avoid stem
    collisions. Cached.

    Switched from the local `mineru` CLI to the hosted API because the local
    pipeline backend mis-aligns multi-line table cells (values drift into the
    wrong row) and the local VLM backend needs a CUDA toolkit we don't have. The
    hosted VLM reads tables correctly. Requires env var MINERU_TOKEN.

    `backend` here maps to the API's model_version: "vlm" (high accuracy) or
    "pipeline". `extra_args` is accepted for signature compatibility but ignored.
    """
    doc_path = Path(doc_path).resolve()
    if not doc_path.exists():
        raise FileNotFoundError(doc_path)

    target = doc_path.parent / (doc_path.name + ".md")    # X.pdf -> X.pdf.md
    if target.exists() and not force:
        print(f"  [mineru-api] cached: {target.name}")
        return target

    md_text = _mineru_markdown_for(doc_path, backend=backend, lang=lang)
    target.write_text(md_text, encoding="utf-8")
    print(f"  [mineru-api] wrote: {target.name}  ({len(md_text)} chars)")
    return target


def _mineru_exe() -> str:
    """Path to the MinerU 4.x CLI in the project's isolated venv (overridable)."""
    env = os.environ.get("MINERU_EXE")
    if env:
        return env
    repo = Path(__file__).resolve().parent.parent
    exe = repo / ".mineru_venv" / "Scripts" / "mineru.exe"
    return str(exe) if exe.exists() else "mineru"


def _mineru_workdir() -> str:
    """Scratch cwd for MinerU processes: the server drops its `blobs/` cache in
    its working directory, so keep that out of the repo root / source/."""
    d = Path(__file__).resolve().parent.parent / "bin"
    d.mkdir(exist_ok=True)
    return str(d)


def _ensure_mineru_server(exe: str) -> None:
    """Start the local managed parse-server if it isn't already up (idempotent)."""
    try:
        subprocess.run([exe, "server", "start"], capture_output=True, timeout=120,
                       cwd=_mineru_workdir())
    except Exception:
        pass


def _mineru_markdown_for(doc_path, backend="vlm", lang="en") -> str:
    """Run the LOCAL MinerU 4.x (advanced tier) on ONE pdf/image and return the
    markdown TEXT (no file written next to the source).

    Uses the CLI in the project's .mineru_venv, talking to the managed local
    parse-server. The advanced/VLM tier gives clean figure/table SEPARATION —
    charts are emitted as images, not poured into <table> blocks — which is why
    this replaced the older hosted-API path. Tier is overridable via MINERU_TIER.
    """
    exe = _mineru_exe()
    ext = Path(doc_path).suffix.lower()
    # advanced/VLM tier is PDF/image-only; Office files (docx/xlsx/pptx) must use
    # the 'flash' tier and parse the whole document (no --pages).
    is_pdf_or_image = ext in {".pdf", ".png", ".jpg", ".jpeg"}
    default_tier = "advanced" if is_pdf_or_image else "flash"
    tier = os.environ.get("MINERU_TIER", default_tier)
    if not is_pdf_or_image:
        tier = "flash"          # advanced/other tiers are rejected for Office files
    _ensure_mineru_server(exe)
    print(f"  [mineru-local] converting {Path(doc_path).name} (tier={tier}, lang={lang})")
    page_args = ["--pages", "all"] if ext == ".pdf" else []
    # The server can hand back a PARTIAL result (only the pages done so far —
    # e.g. Oliveira2022_S1.docx came back as page 1 of 4, losing the table).
    # Check the `<!-- page N of M -->` markers and re-ask until all M pages are
    # in; a still-partial result raises so Word files fall back to the PDF path.
    for attempt in range(1, 4):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "out.md"
            r = subprocess.run(
                [exe, "parse", str(Path(doc_path).resolve()), "--tier", tier, *page_args,
                 "--wait", "1800", "-o", str(out)],
                capture_output=True, text=True, timeout=2400, cwd=_mineru_workdir())
            if r.returncode != 0 or not out.exists():
                raise RuntimeError(
                    f"local MinerU failed for {Path(doc_path).name}: "
                    f"{(r.stderr or r.stdout or '').strip()[-300:]}")
            text = out.read_text(encoding="utf-8", errors="replace")
        marks = [(int(n), int(m)) for n, m in
                 re.findall(r"<!--\s*page\s+(\d+)\s+of\s+(\d+)\s*-->", text)]
        if not marks or len({n for n, _ in marks}) >= marks[0][1]:
            return text
        print(f"  [mineru-local] partial result for {Path(doc_path).name} "
              f"({len({n for n, _ in marks})}/{marks[0][1]} pages), retry {attempt}")
    raise RuntimeError(f"MinerU returned an incomplete parse for {Path(doc_path).name}")


def pdf_to_markdown(pdf_path, **kw):           # backwards-compatible alias
    return doc_to_markdown(pdf_path, **kw)


def _find_soffice(verbose: bool = False):
    """Locate a LibreOffice/soffice executable for docx->pdf. Honours the
    SOFFICE_PATH env var first, then PATH, then common install locations."""
    tried = []
    env = os.environ.get("SOFFICE_PATH")
    if env:
        tried.append(env)
        if Path(env).exists():
            return env
    for name in ("soffice", "libreoffice", "soffice.exe", "libreoffice.exe"):
        p = shutil.which(name)
        tried.append(f"PATH:{name}")
        if p:
            return p
    candidates = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        "/usr/bin/soffice", "/usr/bin/libreoffice",
    ]
    for c in candidates:
        tried.append(c)
        if Path(c).exists():
            return c
    if verbose:
        print("  [soffice] not found. Looked in:")
        for t in tried:
            print(f"      - {t}")
        print("  If LibreOffice is installed elsewhere, set SOFFICE_PATH to the "
              "full path of soffice(.exe).")
    return None


def _office_to_pdf(src: Path, out_dir: Path, prefer: str = "word"):
    """Render a .doc/.docx to PDF in ``out_dir``. Returns the pdf Path or None.

    Converter order matters (see docx_vs_pdf_audit): Microsoft Word (via
    docx2pdf/COM) renders complex tables FAITHFULLY, while LibreOffice headless
    has been observed to mangle them — rotating a narrow first column into
    per-letter vertical text and losing the grid. So Word is tried first and
    LibreOffice is the fallback; ``prefer='libre'`` forces the old order.
    """
    src = Path(src)
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / (src.stem + ".pdf")
    if target.exists():
        return target

    def _via_word():
        try:
            from docx2pdf import convert          # Word COM automation (Win/mac)
            convert(str(src), str(target))
            return target if target.exists() else None
        except Exception as e:
            print(f"    [pdf] Word/docx2pdf unavailable or failed: {type(e).__name__}")
            return None

    def _via_libre():
        soffice = _find_soffice()
        if not soffice:
            return None
        try:
            subprocess.run(
                [soffice, "--headless", "--convert-to", "pdf",
                 "--outdir", str(out_dir), str(src)],
                check=True, capture_output=True, timeout=180,
                env={**os.environ, "HOME": str(out_dir)})
            return target if target.exists() else None
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"    [pdf] soffice failed on {src.name}: {e}")
            return None

    chain = [_via_word, _via_libre] if prefer == "word" else [_via_libre, _via_word]
    for conv in chain:
        r = conv()
        if r:
            return r
    return None


def office_to_markdown(path, backend="vlm", lang="en", force=False,
                       prefer="word", **_ignored):
    """Convert a .doc/.docx to Markdown by rendering it to PDF first, then running
    MinerU's hosted API on that PDF.

    The intermediate PDF is written to a TEMP dir, never into the paper folder —
    a stray sibling .pdf would otherwise be mis-picked as a source (or even the
    main paper) by classify_folder. The markdown is named after the ORIGINAL file
    (X.docx -> X.docx.md), matching the rest of the pipeline and clean_markdowns,
    and is cached (reused unless force=True).
    """
    path = Path(path).resolve()
    if not path.exists():
        raise FileNotFoundError(path)

    target = path.parent / (path.name + ".md")     # X.docx -> X.docx.md
    if target.exists() and not force:
        print(f"  [office->pdf] cached: {target.name}")
        return target

    with tempfile.TemporaryDirectory() as tmp:
        pdf = _office_to_pdf(path, Path(tmp), prefer=prefer)
        if pdf is None:
            raise RuntimeError(
                f"could not convert {path.name} to PDF. Install Microsoft Word "
                "(docx2pdf) or LibreOffice; if LibreOffice is not on PATH set "
                "SOFFICE_PATH to soffice(.exe).")
        print(f"  [office->pdf] {path.name} -> {pdf.name} (temp); running MinerU...")
        md_text = _mineru_markdown_for(pdf, backend=backend, lang=lang)

    target.write_text(md_text, encoding="utf-8")
    print(f"  [office->pdf] wrote: {target.name}  ({len(md_text)} chars)")
    return target


def ensure_markdown(path, **kw):
    """pdf/pptx/image/doc/docx/xlsx/xls -> .md via MinerU 4.x; csv/md/html ->
    unchanged. Set DOCX_VIA_PDF=True to route Word via render-to-PDF, or
    XLSX_VIA_MINERU=False to keep spreadsheets as the openpyxl HTML embed."""
    p = Path(path)
    ext = p.suffix.lower()
    if ext in WORD_EXTS:
        if DOCX_VIA_PDF:
            return office_to_markdown(p, **kw)
        try:
            return doc_to_markdown(p, **kw)     # MinerU 4.x reads Word natively
        except Exception as e:
            # MinerU can choke on some .docx (e.g. Google-Docs heading anchors).
            # Fall back to rendering the doc to PDF and running MinerU's advanced
            # tier on that PDF (office_to_markdown -> _mineru_markdown_for picks
            # 'advanced' for the .pdf input).
            print(f"  [word] MinerU failed on {p.name} ({type(e).__name__}); "
                  f"rendering to PDF and retrying with advanced tier")
            return office_to_markdown(p, **kw)
    if ext in SPREADSHEET_EXTS and XLSX_VIA_MINERU:
        return doc_to_markdown(p, **kw)     # MinerU 4.x reads spreadsheets natively
    if ext in MINERU_DOC_EXTS:
        return doc_to_markdown(p, **kw)
    return p


# ---------------------------------------------------------------------------
# Spreadsheet / CSV -> HTML <table> (the shape text_manager.get_tables expects)
# ---------------------------------------------------------------------------

def _trim_trailing_empty(rows):
    """Drop wholly-empty trailing rows and trailing columns.

    openpyxl's iter_rows returns the sheet's used-range, which usually extends
    below and to the right of the real data (blank cells Excel still tracks).
    Emitting a <tr>/<td> for each bloats the embedded table for no content, so
    strip trailing blanks. Interior blanks are left alone (they may separate
    sub-tables); only the trailing padding is removed."""
    def empty(c):
        return c is None or str(c).strip() == ""

    grid = [list(r) for r in rows if r is not None]
    while grid and all(empty(c) for c in grid[-1]):
        grid.pop()
    if not grid:
        return []
    last_col = -1
    for r in grid:
        for i, c in enumerate(r):
            if not empty(c):
                last_col = max(last_col, i)
    return [r[:last_col + 1] for r in grid]


def _rows_to_html_table(rows):
    rows = _trim_trailing_empty(rows)
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    out = ["<table>"]
    for r in rows:
        cells = list(r) + [None] * (width - len(r))
        out.append("<tr>" + "".join(
            f"<td>{'' if c is None else _html.escape(str(c).strip())}</td>"
            for c in cells) + "</tr>")
    out.append("</table>")
    return "\n".join(out)


def _repair_date_ratio(value):
    """Undo Excel's auto-conversion of a typed 'month.day' ratio into a date.

    Some complementary spreadsheets were typed into General-format cells, so a
    value like '3.15' was interpreted as 15 March and stored as a date. This
    reverses that: a datetime -> the float month.day (day zero-padded to two
    places, matching the two-decimal convention those columns use: '1.08', not
    '1.8').

    Returns the repaired float, or None if `value` is not a datetime (caller
    leaves the cell untouched). NOTE: this assumes every datetime in these
    complementary sheets is a corrupted ratio, never a real calendar date — which
    held for the papers checked (Fontanilla2019). If a sheet has a genuine date
    column, guard or disable this via REPAIR_DATE_RATIOS.
    """
    from datetime import datetime, date
    if not isinstance(value, (datetime, date)):
        return None
    return float(f"{value.month}.{value.day:02d}")


# Turn the per-paper date repair on/off. On by default because the corrupted
# ratios otherwise reach the model as dates ('2019-03-15') and never match GT.
REPAIR_DATE_RATIOS = True


def xlsx_to_html_tables(xlsx_path):
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    blocks = []
    repaired = 0
    for ws in wb.worksheets:
        rows = list(ws.iter_rows(values_only=True))
        if REPAIR_DATE_RATIOS:
            fixed_rows = []
            for r in rows:
                new_r = []
                for c in r:
                    rc = _repair_date_ratio(c) if REPAIR_DATE_RATIOS else None
                    if rc is not None:
                        new_r.append(rc)
                        repaired += 1
                    else:
                        new_r.append(c)
                fixed_rows.append(tuple(new_r))
            rows = fixed_rows
        if any(any(c is not None for c in r) for r in rows):
            heading = f"### {ws.title}" if ws.title else ""
            blocks.append((heading + "\n" + _rows_to_html_table(rows)).strip())
    if repaired:
        print(f"  [xlsx] repaired {repaired} date-corrupted ratio cell(s) in "
              f"{Path(xlsx_path).name}")
    return blocks


def csv_to_html_table(csv_path):
    with open(csv_path, "r", encoding="utf-8", errors="replace", newline="") as f:
        rows = list(_csv.reader(f))
    return [_rows_to_html_table(rows)] if rows else []


def docx_to_markdown(path):
    """Extract a .docx as markdown WITHOUT MinerU: paragraphs become text and
    Word tables become HTML <table> blocks (exact cell values, no OCR). Walks the
    body in document order so a table stays next to its caption. Returns the path
    to a written <name>.docx.md (cached)."""
    from docx import Document

    path = Path(path).resolve()
    target = path.parent / (path.name + ".md")
    if target.exists():
        print(f"  [docx] cached: {target.name}")
        return target

    doc = Document(str(path))
    paras = {p._p: p for p in doc.paragraphs}
    tables = {t._tbl: t for t in doc.tables}
    out = []
    for child in doc.element.body.iterchildren():
        if child in paras:
            txt = paras[child].text.strip()
            if txt:
                out.append(txt)
        elif child in tables:
            tbl = tables[child]
            rows = []
            for row in tbl.rows:
                tds = "".join(f"<td>{_html.escape(c.text.strip())}</td>"
                              for c in row.cells)
                rows.append(f"<tr>{tds}</tr>")
            if rows:
                out.append("<table>\n" + "\n".join(rows) + "\n</table>")
    target.write_text("\n\n".join(out), encoding="utf-8")
    print(f"  [docx] wrote: {target.name}")
    return target


def _embed_as_html(path):
    ext = Path(path).suffix.lower()
    if ext in {".xlsx", ".xls"}:
        return xlsx_to_html_tables(path)
    if ext in {".csv", ".tsv"}:
        return csv_to_html_table(path)
    return []


# ---------------------------------------------------------------------------
# Folder orchestration
# ---------------------------------------------------------------------------

def _norm_stem(stem):
    """Normalise a filename stem for tolerant matching: strip accents, lowercase,
    drop spaces/underscores/hyphens. 'Araújo 2021' == 'araujo2021'."""
    s = "".join(c for c in unicodedata.normalize("NFKD", str(stem))
                if not unicodedata.combining(c))
    return re.sub(r"[\s_\-]+", "", s).casefold()


def classify_folder(folder):
    """Return (main, results, complementary[]) Paths for one paper folder."""
    folder = Path(folder)
    files = [f for f in folder.iterdir()
             if f.is_file() and f.suffix.lower() in
             (MINERU_DOC_EXTS | WORD_EXTS | SPREADSHEET_EXTS
              | NATIVE_TABLE_EXTS | TEXT_EXTS)
             and f.suffix.lower() != ".md"]      # ignore produced markdown

    # main: a pdf/html, non-_S preferred, pdf preferred
    main_candidates = [f for f in files if f.suffix.lower() in MAIN_DOC_EXTS]
    main_candidates.sort(key=lambda f: (f.suffix.lower() != ".pdf",
                                        bool(_SUPP_RE.search(f.stem)), f.name))
    if not main_candidates:
        raise FileNotFoundError(f"No main pdf/html document in {folder}")
    main = main_candidates[0]

    # results: spreadsheet sharing the main's stem (tolerant of accent/case/space
    # differences, e.g. main 'Araújo2021.pdf' vs results 'Araujo2021.xlsx')
    main_key = _norm_stem(main.stem)
    results = next((f for f in files
                    if f.suffix.lower() in {".xlsx", ".xls"}
                    and _norm_stem(f.stem) == main_key
                    and f != main),
                   None)

    # complementary: everything else that is a source
    complementary = [f for f in files if f != main and f != results]
    complementary.sort(key=lambda f: f.name)
    return main, results, complementary


def prepare_document_set(folder, force=False, backend="vlm", lang="en"):
    """Convert main + complementary to per-file markdown/native sources.
    Returns (main_md, [complementary_source_paths], results_or_None)."""
    main, results, complementary = classify_folder(folder)
    print(f"\nPreparing {Path(folder).name}: main={main.name}, "
          f"results={results.name if results else None}, "
          f"complementary={[c.name for c in complementary]}")

    main_md = ensure_markdown(main, force=force, backend=backend, lang=lang)
    convertible = WORD_EXTS | MINERU_DOC_EXTS | (
        SPREADSHEET_EXTS if XLSX_VIA_MINERU else set())
    comps = []
    for c in complementary:
        if c.suffix.lower() in convertible:
            comps.append(str(ensure_markdown(c, force=force, backend=backend, lang=lang)))
        else:                                   # csv/text (or xlsx if embedding) -> as-is
            comps.append(str(c))
    return str(main_md), comps, (str(results) if results else None)


def combine_paper_to_markdown(folder, force=False, backend="vlm", lang="en"):
    """Unite main + all complementary content into ONE markdown per paper.
    docx/pptx/pdf complementary are MinerU-converted and their text appended;
    xlsx/csv are embedded as HTML <table>. Returns (combined_md, results_or_None).
    Output: <folder>/<folder name>_full.md
    """
    folder = Path(folder)
    main_md, comps, results = prepare_document_set(
        folder, force=force, backend=backend, lang=lang)

    parts = [Path(main_md).read_text(encoding="utf-8", errors="replace")]
    for c in comps:
        cp = Path(c)
        parts.append(f"\n\n<!-- ===== Complementary: {cp.name} ===== -->\n")
        if cp.suffix.lower() in TEXT_EXTS:                  # converted .md/.html
            parts.append(cp.read_text(encoding="utf-8", errors="replace"))
        else:                                               # xlsx/csv -> HTML tables
            parts.extend(_embed_as_html(cp))

    combined = folder / f"{folder.name}_full.md"
    combined.write_text("\n\n".join(parts), encoding="utf-8")
    print(f"  [combine] wrote single paper markdown: {combined.name}")
    return str(combined), results


# ---------------------------------------------------------------------------
# Cleanup: delete generated markdown so you can redo conversions
# ---------------------------------------------------------------------------

def clean_markdowns(base, dry_run=True):
    """Delete pipeline-generated markdown under `base` (recursively), leaving all
    originals (.pdf/.docx/.xlsx/.csv/...) untouched.

    Targets only files this module writes:
      *.pdf.md, *.docx.md, *.pptx.md, *.png.md/.jpg.md/.jpeg.md  (converted docs)
      *_full.md                                                  (combined paper)
    By default dry_run=True only lists what WOULD be deleted; pass dry_run=False
    to actually delete.
    """
    base = Path(base)
    suffixes = tuple(f"{e}.md" for e in
                     (MINERU_DOC_EXTS | WORD_EXTS
                      | SPREADSHEET_EXTS))   # e.g. '.pdf.md', '.docx.md', '.xlsx.md'
    victims = [p for p in base.rglob("*.md")
               if p.name.endswith(suffixes) or p.name.endswith("_full.md")]

    if not victims:
        print(f"No generated markdown found under {base}")
        return []

    print(f"{'[DRY RUN] would delete' if dry_run else 'Deleting'} "
          f"{len(victims)} file(s):")
    for p in victims:
        print("   ", p.relative_to(base))
        if not dry_run:
            p.unlink()
    if dry_run:
        print("Re-run with dry_run=False to actually delete.")
    return victims


# ---------------------------------------------------------------------------
# CLI: process EVERY paper folder under a base directory
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    # Default base; override by passing a folder path as the first non-flag arg.
    DEFAULT_BASE = ("../data/un_processed_papers")

    args = sys.argv[1:]
    do_clean = "--clean" in args        # wipe generated markdown first, then rebuild
    force = "--force" in args           # re-convert even if a cached .md exists
    positional = [a for a in args if not a.startswith("--")]
    base = Path(positional[0]) if positional else Path(DEFAULT_BASE)

    if do_clean:
        clean_markdowns(base, dry_run=False)

    folders = sorted(p for p in base.iterdir() if p.is_dir())
    print(f"\nFound {len(folders)} paper folder(s) under {base}")

    for folder in folders:
        combined_path = folder / f"{folder.name}_full.md"
        if combined_path.exists() and not force:
            print(f"  SKIP {folder.name} (already built: {combined_path.name})")
            continue
        try:
            combined, results = combine_paper_to_markdown(folder, force=force)
            print(f"  OK   {folder.name} -> {Path(combined).name}")
        except Exception as e:
            print(f"  FAIL {folder.name}: {e}")