"""
reocr_papers.py — re-extract specific paper folders through MinerU with OCR ON,
for papers whose tables MinerU cropped to images (scan_tables: "TABLES AS IMAGES").

Why this exists
---------------
The normal run uses is_ocr=False because the papers are born-digital. For a few
papers MinerU could not parse the table structure from the text layer and dumped
each table as an IMAGE (![](...)), so the pipeline — which reads only the
<table> HTML in <paper>_full.md — gets zero tables and the paper yields no rows.
Forcing is_ocr=True makes MinerU transcribe the table region instead of cropping
it. The transcription can be imperfect (split headers, merged columns — that is
why OCR is off by default), but a table the pipeline can read beats an image it
cannot.

What it does, per paper folder
------------------------------
  1. find the main PDF (the non-ground-truth .pdf; usually <folder>.pdf)
  2. back up the existing <folder>_full.md  ->  <folder>_full.md.pretxt.bak
     (so you can revert, or diff OCR vs text-layer output)
  3. call mineru_api.extract_one(pdf, ocr=True)
  4. write the result to <folder>_full.md — the exact name run_all/run_pipeline
     read — so the next pipeline run picks it up with no other change.

It writes NOTHING until a successful extraction, and never deletes the backup.

Safety / cost
-------------
This UPLOADS each PDF to the hosted MinerU API and consumes quota. Start with the
--dry-run to see what it WOULD do, then run one small paper before the rest:

    set MINERU_TOKEN=...
    python reocr_papers.py --only Franzen2025 --dry-run
    python reocr_papers.py --only Franzen2025
    python scan_tables.py --only Franzen2025          # confirm tables now parse
    # if good, do the rest:
    python reocr_papers.py --only Hill2024,Ustjuzhanin2024,Xia2022,Xu2024

Then re-run the pipeline for those papers (e.g. run_all.py <paper>) and evaluate.

If OCR does not help, note that model_version="MinerU-HTML" is a table-optimized
backend (see mineru_api.request_upload_urls); --model MinerU-HTML is worth a try
either instead of or together with --ocr.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import mineru_api

DEFAULT_PAPERS = Path("../data/un_processed_papers")
BACKUP_SUFFIX = ".pretxt.bak"          # marks the pre-OCR (text-layer) markdown

DOC_EXTS = {".pdf"}


def _ground_truth_pdf_stems(folder: Path) -> set:
    """Stems that are answer keys, not source docs (a results .xlsx whose stem
    matches the folder/paper). We only pick PDFs, so this mostly guards the rare
    case of a stray non-source PDF; kept for symmetry with the rest of the code."""
    return {folder.name.lower()}


def find_main_pdf(folder: Path) -> Path | None:
    """The paper's own PDF. Prefer <folder>.pdf; else the only PDF present; else
    None (and the caller reports it) when there are zero or several candidates."""
    pdfs = sorted(p for p in folder.iterdir()
                  if p.is_file() and p.suffix.lower() == ".pdf")
    if not pdfs:
        return None
    exact = folder / f"{folder.name}.pdf"
    if exact.exists():
        return exact
    if len(pdfs) == 1:
        return pdfs[0]
    # several PDFs and none named after the folder — ambiguous, let caller warn
    return None


def reextract_folder(folder: Path, token: str, *, model: str, language: str,
                     dry_run: bool) -> str:
    """Re-OCR one paper folder. Returns a short status string for the summary."""
    paper = folder.name
    pdf = find_main_pdf(folder)
    if pdf is None:
        pdfs = [p.name for p in folder.iterdir()
                if p.is_file() and p.suffix.lower() == ".pdf"]
        if not pdfs:
            return "no PDF in folder"
        return f"ambiguous PDF ({len(pdfs)} present, none named {paper}.pdf): {pdfs}"

    target_md = folder / f"{paper}_full.md"
    backup = folder / f"{paper}_full.md{BACKUP_SUFFIX}"

    if dry_run:
        would_backup = "back up existing md" if target_md.exists() else "no md to back up"
        return f"DRY RUN — would OCR {pdf.name} -> {target_md.name} ({would_backup})"

    print(f"  OCR re-extract: {pdf.name}")
    md = mineru_api.extract_one(pdf, token, model=model, language=language, ocr=True)
    if not md:
        return "FAILED — MinerU returned no markdown (nothing written; md untouched)"

    # only now that we have new content: back up the old md, then overwrite
    if target_md.exists():
        # don't clobber an existing backup — keep the FIRST (true text-layer) one
        if not backup.exists():
            target_md.replace(backup)
            print(f"    backed up old md -> {backup.name}")
        else:
            print(f"    backup {backup.name} already exists — keeping it")
            target_md.unlink()
    target_md.write_text(md, encoding="utf-8")
    html_tables = md.lower().count("<table")
    return f"OK — wrote {len(md)} chars, {html_tables} <table> block(s)"


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--papers", default=str(DEFAULT_PAPERS),
                    help="papers root (default ../data/un_processed_papers)")
    ap.add_argument("--only", required=True,
                    help="comma-separated paper folder names to re-OCR "
                         "(required — this is a targeted repair, not a batch)")
    ap.add_argument("--model", default="vlm",
                    help="model_version (default vlm; try MinerU-HTML for tables)")
    ap.add_argument("--language", default="en")
    ap.add_argument("--dry-run", action="store_true",
                    help="show what would happen, upload nothing")
    args = ap.parse_args()

    root = Path(args.papers)
    if not root.is_dir():
        sys.exit(f"papers root not found: {root}")

    token = os.environ.get("MINERU_TOKEN")
    if not token and not args.dry_run:
        sys.exit("Set MINERU_TOKEN first:  set MINERU_TOKEN=...")

    names = [n.strip() for n in args.only.split(",") if n.strip()]
    summary = []
    for name in names:
        folder = root / name
        print("=" * 70)
        print(name)
        if not folder.is_dir():
            print("  (folder not found)")
            summary.append((name, "folder not found"))
            continue
        try:
            status = reextract_folder(folder, token or "", model=args.model,
                                      language=args.language, dry_run=args.dry_run)
        except Exception as e:
            status = f"ERROR {type(e).__name__}: {e}"
        print(f"  {status}")
        summary.append((name, status))

    print("\n" + "#" * 70)
    for name, status in summary:
        print(f"  {name:24s} {status}")
    if not args.dry_run:
        print("\nNext: python scan_tables.py --only " + ",".join(names))
        print("      then re-run the pipeline for these papers and evaluate.")


if __name__ == "__main__":
    main()
