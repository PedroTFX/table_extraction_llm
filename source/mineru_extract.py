"""
mineru_extract.py — convert documents to Markdown with MinerU, and unite a whole
paper folder (main paper + complementary files) into ONE markdown the existing
pipeline can run on, while keeping the volunteer "results" spreadsheet aside as
ground truth.

Why the CLI: the package was renamed magic-pdf -> mineru and the in-process API
keeps shifting, whereas `mineru -p IN -o OUT` is stable. MinerU's CLI accepts
pdf/image/docx/pptx; we route those through it. xlsx/csv are embedded as HTML
<table> blocks instead (lossless via openpyxl/csv) because MinerU's layout/OCR
stage mangles dense numeric data sheets.

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

# Types MinerU converts to markdown.
MINERU_DOC_EXTS = {".pdf", ".pptx", ".png", ".jpg", ".jpeg"}
# docx is extracted directly with python-docx (its tables are real tables, not OCR).
DOCX_EXTS = {".docx"}
# Types embedded directly as HTML tables (read losslessly, not via MinerU).
NATIVE_TABLE_EXTS = {".xlsx", ".xls", ".csv", ".tsv"}
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

    import mineru_api  # local module: hosted v4 client

    token = os.environ.get("MINERU_TOKEN")
    if not token:
        raise RuntimeError(
            "MINERU_TOKEN is not set. Get a token at "
            "https://mineru.net/apiManage/token and set MINERU_TOKEN.")

    model = "vlm" if backend not in ("pipeline",) else "pipeline"
    print(f"  [mineru-api] converting {doc_path.name} (model={model}, lang={lang})")
    md_text = mineru_api.extract_one(
        doc_path, token, model=model, language=(lang or "en"))
    if md_text is None:
        raise RuntimeError(f"hosted API returned no markdown for {doc_path.name}")
    target.write_text(md_text, encoding="utf-8")
    print(f"  [mineru-api] wrote: {target.name}  ({len(md_text)} chars)")
    return target


def pdf_to_markdown(pdf_path, **kw):           # backwards-compatible alias
    return doc_to_markdown(pdf_path, **kw)


def ensure_markdown(path, **kw):
    """docx -> .md via python-docx; pdf/pptx/image -> .md via MinerU;
    xlsx/csv/md/html -> unchanged."""
    p = Path(path)
    if p.suffix.lower() in DOCX_EXTS:
        return docx_to_markdown(p)          # MinerU kwargs don't apply
    if p.suffix.lower() in MINERU_DOC_EXTS:
        return doc_to_markdown(p, **kw)
    return p


# ---------------------------------------------------------------------------
# Spreadsheet / CSV -> HTML <table> (the shape text_manager.get_tables expects)
# ---------------------------------------------------------------------------

def _rows_to_html_table(rows):
    rows = [list(r) for r in rows if r is not None]
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


def xlsx_to_html_tables(xlsx_path):
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    blocks = []
    for ws in wb.worksheets:
        rows = list(ws.iter_rows(values_only=True))
        if any(any(c is not None for c in r) for r in rows):
            heading = f"### {ws.title}" if ws.title else ""
            blocks.append((heading + "\n" + _rows_to_html_table(rows)).strip())
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
             (MINERU_DOC_EXTS | DOCX_EXTS | NATIVE_TABLE_EXTS | TEXT_EXTS)
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
    comps = []
    for c in complementary:
        if c.suffix.lower() in (DOCX_EXTS | MINERU_DOC_EXTS):
            comps.append(str(ensure_markdown(c, force=force, backend=backend, lang=lang)))
        else:                                   # xlsx/csv/text -> kept as-is
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
                     (MINERU_DOC_EXTS | DOCX_EXTS))   # e.g. '.pdf.md', '.docx.md'
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
    DEFAULT_BASE = ("C:/Users/Pedro Trindade/Documents/github"
                    "/agents_test/data/un_processed_papers")

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