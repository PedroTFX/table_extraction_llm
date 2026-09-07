"""
scan_tables.py — read the tables the PIPELINE sees in each paper, and say why a
paper would (or wouldn't) produce specimen rows.

This is the Step-0 diagnostic. run_all/run_pipeline read each paper's combined
``<paper>_full.md`` (built earlier by mineru_extract) plus any complementary
xlsx/csv, turn every <table> into a Table, and keep only tables that have a
taxon *identifier* column. When a paper comes out with 0 rows, nothing in the
evaluation report tells you which of those stages was empty. This script makes
that stage visible, per source file and per table, WITHOUT the LLM — so it runs
offline and even when Ollama is down.

For every paper it reports, per table:
    rows × cols, the header, the best identifier-column candidate and its taxon
    fraction, whether that column passes the pipeline's own structural
    identifier test (_looks_like_identifier_column), and whether the table looks
    transposed (species in the header — the melt-risk / false-"no id" case).

and per paper, a one-line VERDICT explaining a 0-row outcome:
    no _full.md · no tables · tables but no identifier column · looks transposed
    · data only in an unmerged supplementary xlsx · has id tables (cause is
    downstream: mapping / grouping / LLM).

It re-uses the pipeline's own functions (get_tables, parse_table,
_looks_like_identifier_column, taxon_fraction, detect_transposed), so its verdict
matches what the pipeline actually does. If any of those are renamed, update the
imports here (check_sync.py will also flag the drift).

Usage
-----
    python scan_tables.py                          # scan every paper folder
    python scan_tables.py --only Guariento2020,Renoz2020,Franzen2025
    python scan_tables.py --papers ../data/un_processed_papers --out ../output/_scan
    python scan_tables.py --zero-only              # only print papers likely to yield 0 rows
    python scan_tables.py --full                   # dump every header, not just a preview
    python scan_tables.py path/to/OnePaperFolder   # a single folder or a single file

Writes <out>/<paper>.scan.json (machine) and prints an aligned summary. Nothing
is modified; this only reads.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import traceback
from pathlib import Path

# Pipeline modules — imported so this stays in lock-step with real behaviour.
from text_manager import get_tables, xlsx_to_table, csv_to_table
from tables import parse_table, taxon_fraction, looks_like_taxon, detect_transposed
from table_to_data import _looks_like_identifier_column

DEFAULT_PAPERS = Path("../data/un_processed_papers")

# A column is treated as a usable identifier when it is mostly taxon-shaped AND
# passes the pipeline's structural backstop. 0.60 mirrors detect_transposed's
# min_header_frac; tune here if the pipeline's mapper is more/less permissive.
TAXON_ID_THRESHOLD = 0.60

DOC_EXTS = {".pdf", ".docx"}
SHEET_EXTS = {".xlsx", ".xls", ".csv", ".tsv"}
TEXT_EXTS = {".md", ".html", ".htm", ".txt"}


# ---------------------------------------------------------------------------
# markdown markup diagnosis (for the TABLES=0 case)
# ---------------------------------------------------------------------------

# A markdown pipe-table's tell-tale is its DELIMITER row: | --- | :---: | etc.
# Matching the delimiter (not just any pipe line) avoids counting prose that
# happens to contain a '|'. get_tables() only parses <table> HTML, so a file
# built entirely of pipe tables scans as TABLES=0 while being full of data.
_MD_DELIM_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?\s*$")
_MD_PIPEROW_RE = re.compile(r"^\s*\|.*\|.*$")     # a row with >=2 pipes
_MD_IMG_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")   # ![alt](path) image embed


def md_table_diagnostics(path: Path) -> dict:
    """Peek at a markdown file and report which table markup it actually uses.

    Distinguishes the two very different causes hiding under 'TABLES=0':
      * markdown PIPE tables  -> get_tables can't see them (parses <table> only)
      * tables rendered as IMAGES -> MinerU didn't recognise them; needs OCR
      * nearly-empty markdown -> MinerU produced almost nothing
    """
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}

    lines = text.splitlines()
    html_tables = len(re.findall(r"<table[\s>]", text, re.IGNORECASE))
    delim_rows = sum(1 for ln in lines if _MD_DELIM_RE.match(ln))
    pipe_rows = sum(1 for ln in lines if _MD_PIPEROW_RE.match(ln))
    images = len(_MD_IMG_RE.findall(text))
    return {
        "chars": len(text),
        "html_tables": html_tables,
        "md_delimiter_rows": delim_rows,     # ~ number of markdown tables
        "md_pipe_rows": pipe_rows,           # ~ total markdown table body rows
        "image_embeds": images,
        "error": None,
    }


def _md_cause(diag: dict) -> str:
    """Turn the markup counts into a one-line cause for a no-parsed-tables file."""
    if not diag or diag.get("error"):
        return "could not read markdown"
    if diag["md_delimiter_rows"] >= 1:
        return (f"MARKDOWN PIPE TABLES ({diag['md_delimiter_rows']} table(s), "
                f"{diag['md_pipe_rows']} row(s)) — get_tables parses <table> only; "
                "add pipe-table parsing to recover these")
    if diag["image_embeds"] >= 1:
        return (f"TABLES AS IMAGES ({diag['image_embeds']} image ref(s), no pipe "
                "tables) — MinerU didn't recognise them; needs OCR / re-extract")
    if diag["chars"] < 500:
        return f"MARKDOWN NEARLY EMPTY ({diag['chars']} chars) — MinerU produced almost nothing"
    return "markdown has text but no recognisable table markup (HTML or pipe)"


# ---------------------------------------------------------------------------
# source discovery (mirrors what the pipeline actually feeds itself)
# ---------------------------------------------------------------------------

def _ground_truth_sheets(folder: Path) -> set:
    """Spreadsheets that are the volunteers' answer key, not source data. A sheet
    is ground-truth if its stem matches a document in the folder (Barber2017.xlsx
    next to Barber2017.pdf/.docx) or the paper folder's own name. Same rule as
    read_tables._ground_truth_files, plus the folder-name case."""
    doc_stems = {p.stem.lower() for p in folder.iterdir()
                 if p.is_file() and p.suffix.lower() in DOC_EXTS}
    doc_stems.add(folder.name.lower())
    return {p.name for p in folder.iterdir()
            if p.is_file() and p.suffix.lower() in {".xlsx", ".xls"}
            and p.stem.lower() in doc_stems}


def pipeline_sources(folder: Path) -> dict:
    """What the pipeline reads for THIS folder: the combined <paper>_full.md, and
    any non-ground-truth spreadsheet/csv. Returns a dict describing presence so
    the verdict can distinguish 'no markdown' from 'markdown has no tables'."""
    paper = folder.name
    full_md = folder / f"{paper}_full.md"
    gt = _ground_truth_sheets(folder)

    supplementary = sorted(
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in SHEET_EXTS and p.name not in gt)
    other_md = sorted(
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in TEXT_EXTS and p != full_md)
    docs = sorted(p for p in folder.iterdir()
                  if p.is_file() and p.suffix.lower() in DOC_EXTS)

    return {
        "full_md": full_md if full_md.exists() else None,
        "supplementary": supplementary,        # xlsx/csv the pipeline COULD use
        "other_text": other_md,
        "docs": docs,                          # pdf/docx (upstream of mineru)
        "ground_truth": sorted(gt),
    }


# ---------------------------------------------------------------------------
# per-table analysis (no LLM)
# ---------------------------------------------------------------------------

def _tables_from_source(path: Path) -> list:
    """Parse one source file into Table objects using the deterministic header
    (row 0) — the same cleaned pipe-tables the pipeline builds, minus the LLM
    header finder. Never raises; returns [] and lets the caller record the error."""
    ext = path.suffix.lower()
    if ext in TEXT_EXTS:
        text = path.read_text(encoding="utf-8", errors="replace")
        return [parse_table(t["content"], source=path.name, table_index=i)
                for i, t in enumerate(get_tables(text))]
    if ext in {".xlsx", ".xls"}:
        raw = xlsx_to_table(str(path))
        return [parse_table(raw, source=path.name, table_index=0)]
    if ext in {".csv", ".tsv"}:
        raw = csv_to_table(path.read_text(encoding="utf-8", errors="replace"))
        return [parse_table(raw, source=path.name, table_index=0)]
    return []


def _best_identifier(table) -> dict:
    """Score every column as a possible identifier and return the best one.

    A column qualifies when it is mostly taxon-shaped (taxon_fraction) AND passes
    the pipeline's structural backstop. We report the best column either way, so a
    near-miss ('0.55 taxon, failed') is visible rather than just 'none'."""
    best = {"column": None, "taxon_fraction": 0.0, "passes_structural": False,
            "qualifies": False}
    for name in table.header_names:
        vals = table.column_values(name)
        tf = taxon_fraction(vals)
        if tf <= best["taxon_fraction"]:
            continue
        passes = _looks_like_identifier_column(table, name)
        best = {
            "column": name,
            "taxon_fraction": round(tf, 3),
            "passes_structural": passes,
            "qualifies": bool(tf >= TAXON_ID_THRESHOLD and passes),
        }
    return best


def analyse_table(table) -> dict:
    hdr = table.header_names
    recs = table.data_records()
    ident = _best_identifier(table)
    transposed, ev = detect_transposed(table)
    n_trait_cols = max(0, len(hdr) - (1 if ident["column"] else 0))
    return {
        "source": table.source,
        "table_index": table.table_index,
        "n_rows": len(recs),
        "n_cols": len(hdr),
        "header": hdr,
        "identifier": ident,
        "transposed": bool(transposed),
        "transpose_reason": ev.get("reason", ""),
        # what the pipeline needs to emit rows: an id column + >=1 other column
        "would_yield_rows": bool(ident["qualifies"] and n_trait_cols >= 1),
    }


def _distinct_species(analyses, tables) -> int:
    names = set()
    for a, t in zip(analyses, tables):
        col = a["identifier"]["column"]
        if a["identifier"]["qualifies"] and col:
            for v in t.column_values(col):
                v = (v or "").strip()
                if v and looks_like_taxon(v):
                    names.add(v.lower())
    return len(names)


# ---------------------------------------------------------------------------
# per-paper verdict
# ---------------------------------------------------------------------------

def _verdict(src: dict, md_id: int, supp_id: int,
             transposed_tables: int, total_tables: int, md_diag: dict = None) -> str:
    """One line explaining a likely 0-row outcome, in the pipeline's terms.

    The key split: an identifier table in the MARKDOWN is data the runner feeds;
    an identifier table only in a SUPPLEMENTARY sheet is data run_all never passes
    (it calls run_pipeline with no complementary_files) — a different, specific fix.
    """
    if src["full_md"] is None:
        if src["supplementary"]:
            return ("NO _full.md — mineru output missing; specimen data sits in a "
                    "supplementary sheet the runner never passes. Rebuild the "
                    "markdown (mineru_extract) or pass the sheet to run_pipeline")
        return "NO _full.md and no supplementary data — nothing for the pipeline to read"

    if md_id >= 1:
        return (f"OK — {md_id} identifier table(s) in the markdown; a 0-row result "
                "is downstream (LLM mapping / relevance gate / grouping), not here")

    # markdown yields nothing on its own from here down
    if supp_id >= 1:
        names = ", ".join(p.name for p in src["supplementary"]) or "a supplementary sheet"
        return (f"MARKDOWN has no identifier table, but {supp_id} exist in {names}; "
                "run_all does not pass complementary files — pass them to "
                "run_pipeline to recover this paper")
    if total_tables == 0:
        # sub-diagnose: pipe tables vs images vs empty (get_tables sees <table> only)
        return "TABLES=0 — " + _md_cause(md_diag)
    if transposed_tables:
        return (f"NO identifier column — but {transposed_tables} table(s) look "
                "TRANSPOSED (species in the header); the transpose pass or the "
                "mapper should rotate them before grouping")
    return ("identifier column NOT found in any table — all look like "
            "stats/summary tables, or the taxon column wasn't recognised")


def scan_paper(folder: Path, full: bool = False) -> dict:
    src = pipeline_sources(folder)
    out = {
        "paper": folder.name,
        "has_full_md": src["full_md"] is not None,
        "supplementary": [p.name for p in src["supplementary"]],
        "ground_truth": src["ground_truth"],
        "sources": [], "tables": [], "error": None,
    }

    md_name = src["full_md"].name if src["full_md"] else None
    read_list = ([src["full_md"]] if src["full_md"] else []) + src["supplementary"]
    per_source = []
    all_tables, all_analyses = [], []
    # id-yielding tables split by WHERE they live — the markdown the runner
    # actually feeds vs a supplementary sheet run_all never passes.
    md_id = supp_id = 0
    try:
        for path in read_list:
            try:
                tbls = _tables_from_source(path)
                err = None
            except Exception as e:
                tbls, err = [], f"{type(e).__name__}: {e}"
            per_source.append({"file": path.name, "n_tables": len(tbls),
                               "error": err})
            for t in tbls:
                a = analyse_table(t)
                all_tables.append(t)
                all_analyses.append(a)
                if a["would_yield_rows"]:
                    if path.name == md_name:
                        md_id += 1
                    else:
                        supp_id += 1
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"
        out["trace"] = traceback.format_exc(limit=3)
        return out

    id_tables = sum(1 for a in all_analyses if a["identifier"]["qualifies"])
    transposed_tables = sum(1 for a in all_analyses if a["transposed"])

    out["sources"] = per_source
    out["tables"] = all_analyses
    out["n_tables"] = len(all_analyses)
    out["n_identifier_tables"] = id_tables
    out["n_identifier_tables_markdown"] = md_id
    out["n_identifier_tables_supplementary"] = supp_id
    out["n_transposed_tables"] = transposed_tables
    out["n_rows_total"] = sum(a["n_rows"] for a in all_analyses)
    out["n_distinct_species"] = _distinct_species(all_analyses, all_tables)
    # rows the pipeline gets AS CURRENTLY RUN (markdown only); the supplementary
    # path is a fix, not current behaviour.
    out["would_yield_rows"] = md_id >= 1
    out["would_yield_rows_if_supplements_passed"] = (md_id + supp_id) >= 1
    # markup diagnosis of the markdown — decisive when no tables parsed
    md_diag = md_table_diagnostics(src["full_md"]) if src["full_md"] else None
    out["md_diag"] = md_diag
    out["verdict"] = _verdict(src, md_id, supp_id, transposed_tables,
                              len(all_analyses), md_diag)
    if not full:                       # trim long headers in the machine file too
        for a in out["tables"]:
            if len(a["header"]) > 12:
                a["header"] = a["header"][:12] + [f"...(+{len(a['header']) - 12})"]
    return out


# ---------------------------------------------------------------------------
# printing
# ---------------------------------------------------------------------------

def _print_paper(rep: dict, full: bool):
    print(f"\n{'='*78}\n{rep['paper']}")
    if rep["error"]:
        print(f"  ERROR {rep['error']}")
        return
    md = "yes" if rep["has_full_md"] else "NO"
    supp = ", ".join(rep["supplementary"]) or "-"
    print(f"  _full.md: {md}   supplementary: {supp}")
    for s in rep["sources"]:
        e = f"  ERROR {s['error']}" if s["error"] else ""
        print(f"    {s['file']:<40} {s['n_tables']:>3} table(s){e}")

    # when the markdown yielded no tables, show what markup it actually has
    diag = rep.get("md_diag")
    if diag and not diag.get("error") and rep.get("n_identifier_tables_markdown", 0) == 0:
        print(f"    markdown markup: html_tables={diag['html_tables']} "
              f"pipe_tables≈{diag['md_delimiter_rows']} "
              f"pipe_rows={diag['md_pipe_rows']} images={diag['image_embeds']} "
              f"chars={diag['chars']}")

    for a in rep["tables"]:
        idc = a["identifier"]
        mark = "ID" if idc["qualifies"] else ("~id" if idc["column"] else "  ")
        flags = []
        if a["transposed"]:
            flags.append("TRANSPOSED")
        if not a["would_yield_rows"]:
            flags.append("no rows")
        flag = ("  [" + ", ".join(flags) + "]") if flags else ""
        iddesc = (f"id='{idc['column']}' taxon={idc['taxon_fraction']} "
                  f"struct={'y' if idc['passes_structural'] else 'n'}"
                  if idc["column"] else "id=none")
        print(f"    [{mark}] {a['source']}#{a['table_index']}  "
              f"{a['n_rows']}r×{a['n_cols']}c  {iddesc}{flag}")
        if full:
            print(f"          header: {a['header']}")

    print(f"  -> tables={rep['n_tables']}  id_tables={rep['n_identifier_tables']}  "
          f"species≈{rep['n_distinct_species']}  rows={rep['n_rows_total']}")
    print(f"  VERDICT: {rep['verdict']}")


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------

def _is_paper_dir(p: Path) -> bool:
    """A real paper folder is not a hidden/scratch dir (._scan, .git) and holds
    at least one thing the pipeline could read."""
    if p.name.startswith((".", "_")):
        return False
    return ((p / f"{p.name}_full.md").exists()
            or any(p.glob("*.xlsx")) or any(p.glob("*.csv"))
            or any(p.glob("*.md")))


def _iter_folders(target: Path, only, out_dir: Path):
    if target.is_file():
        return [("__file__", target)]
    if _is_paper_dir(target):
        # target itself looks like a single paper folder
        if only is None or target.name in only:
            return [(target.name, target)]
    out_res = out_dir.resolve()
    folders = sorted(p for p in target.iterdir()
                     if p.is_dir() and p.resolve() != out_res and _is_paper_dir(p))
    if only:
        folders = [f for f in folders if f.name in only]
    return [(f.name, f) for f in folders]


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", nargs="?", default=str(DEFAULT_PAPERS),
                    help="papers root, a single paper folder, or a single file")
    ap.add_argument("--papers", help="papers root (overrides positional target)")
    ap.add_argument("--only", help="comma-separated paper folder names")
    ap.add_argument("--out", default="../output/_scan", help="where to write *.scan.json")
    ap.add_argument("--zero-only", action="store_true",
                    help="print only papers unlikely to yield any rows")
    ap.add_argument("--full", action="store_true", help="dump full headers")
    args = ap.parse_args()

    target = Path(args.papers) if args.papers else Path(args.target)
    if not target.exists():
        sys.exit(f"not found: {target}")
    only = set(args.only.split(",")) if args.only else None

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    entries = _iter_folders(target, only, out_dir)
    if not entries:
        sys.exit("no matching paper folders")

    summary = []
    for name, path in entries:
        if path.is_file():
            # single-file mode: wrap it as a pseudo-paper
            rep = {"paper": path.stem, "has_full_md": True, "supplementary": [],
                   "ground_truth": [], "sources": [], "tables": [], "error": None}
            try:
                tbls = _tables_from_source(path)
                rep["sources"] = [{"file": path.name, "n_tables": len(tbls), "error": None}]
                rep["tables"] = [analyse_table(t) for t in tbls]
                rep["n_tables"] = len(tbls)
                rep["n_identifier_tables"] = sum(
                    1 for a in rep["tables"] if a["identifier"]["qualifies"])
                rep["n_transposed_tables"] = sum(1 for a in rep["tables"] if a["transposed"])
                rep["n_rows_total"] = sum(a["n_rows"] for a in rep["tables"])
                rep["n_distinct_species"] = _distinct_species(rep["tables"], tbls)
                rep["would_yield_rows"] = any(a["would_yield_rows"] for a in rep["tables"])
                rep["verdict"] = ("OK — has identifier table(s)"
                                  if rep["n_identifier_tables"]
                                  else "no identifier column found")
            except Exception as e:
                rep["error"] = f"{type(e).__name__}: {e}"
        else:
            rep = scan_paper(path, full=args.full)

        (out_dir / f"{rep['paper']}.scan.json").write_text(
            json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")

        likely_zero = not rep.get("would_yield_rows", False) or rep.get("error")
        if not args.zero_only or likely_zero:
            _print_paper(rep, args.full)
        summary.append((rep["paper"], rep.get("n_tables", 0),
                        rep.get("n_identifier_tables", 0),
                        rep.get("n_rows_total", 0), likely_zero,
                        rep.get("verdict", "")))

    # roll-up
    print("\n" + "#" * 78)
    zero = [s for s in summary if s[4]]
    print(f"scanned {len(summary)} paper(s); {len(zero)} likely to yield 0 rows\n")
    print(f"  {'paper':24s} {'tbls':>4} {'idtbl':>5} {'rows':>7}  verdict")
    for paper, nt, nid, nr, lz, verdict in summary:
        mark = "!!" if lz else "  "
        print(f"{mark}{paper:24s} {nt:>4} {nid:>5} {nr:>7}  {verdict[:60]}")
    print(f"\nmachine output -> {out_dir}/<paper>.scan.json")


if __name__ == "__main__":
    main()