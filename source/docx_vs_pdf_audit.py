#!/usr/bin/env python3
"""
docx_vs_pdf_audit.py — measure how many papers are hurt by "the Docx Problem".

For every .docx under data/un_processed_papers/, this:
  1. extracts it the CURRENT way (mineru_extract.docx_to_markdown, python-docx);
  2. converts the SAME .docx to PDF (LibreOffice headless) and runs MinerU on it,
     exactly as the pipeline would for a native PDF (mineru_extract.doc_to_markdown);
  3. compares the two markdowns STRUCTURALLY and reports where they differ.

Why not a byte diff: the two converters never produce byte-identical output —
MinerU adds LaTeX for superscripts ($x^A$), spacing differs, footnote markers
render differently. A raw diff would flag 100% of files and tell you nothing. The
signal that matters is STRUCTURE: how many tables each path found, how many rows
per table, and — the actual Docx Problem — tables the docx path LOST or COLLAPSED
that the PDF path preserved (merged-cell groups, multi-row primer blocks, whole
tables dropped). Byte-equal files are skipped as requested; in practice there
will be none, so the report is the structural comparison.

Usage:
    python docx_vs_pdf_audit.py [--papers DIR] [--out REPORT.md] [--force]

Requires:
    - LibreOffice (soffice) on PATH for docx->pdf, OR docx2pdf installed.
    - MINERU_TOKEN set (same as the normal pipeline) for the PDF path.
      Without it, the PDF side is skipped and the report says so per paper.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import mineru_extract as M

try:
    import docx_pdf_diff as DIFF          # side-by-side per-paper view
except Exception:
    DIFF = None


# ---------------------------------------------------------------------------
# docx -> pdf
# ---------------------------------------------------------------------------

def _find_soffice(verbose: bool = False):
    tried = []
    # 1. explicit override wins
    env = os.environ.get("SOFFICE_PATH")
    if env:
        tried.append(env)
        if Path(env).exists():
            return env
    # 2. on PATH (Linux/macOS, or Windows if the user added it)
    for name in ("soffice", "libreoffice", "soffice.exe", "libreoffice.exe"):
        p = shutil.which(name)
        tried.append(f"PATH:{name}")
        if p:
            return p
    # 3. common install locations, Windows then macOS
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
              "full path of soffice.exe.")
    return None


def docx_to_pdf(docx_path: Path, out_dir: Path, prefer: str = "word") -> Path | None:
    """Convert a .docx to .pdf. Returns the pdf path, or None if no converter.

    Converter order matters: Microsoft Word (via docx2pdf/COM) renders complex
    tables FAITHFULLY, while LibreOffice headless has been observed to mangle them
    — rotating narrow first columns into per-letter vertical text, losing the
    table grid entirely (Oliveira2022's species column came out as stray digits).
    So on Windows we try Word FIRST and fall back to LibreOffice only if Word is
    absent. `prefer='libre'` forces the old order.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / (docx_path.stem + ".pdf")
    if target.exists():
        return target

    def _via_word():
        try:
            from docx2pdf import convert        # Word COM automation (Windows/macOS)
            convert(str(docx_path), str(target))
            return target if target.exists() else None
        except Exception as e:
            print(f"    [pdf] Word/docx2pdf unavailable or failed: "
                  f"{type(e).__name__}")
            return None

    def _via_libre():
        soffice = _find_soffice()
        if not soffice:
            return None
        try:
            subprocess.run(
                [soffice, "--headless", "--convert-to", "pdf",
                 "--outdir", str(out_dir), str(docx_path)],
                check=True, capture_output=True, timeout=180,
                env={**os.environ, "HOME": str(out_dir)})
            return target if target.exists() else None
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"    [pdf] soffice failed on {docx_path.name}: {e}")
            return None

    chain = [_via_word, _via_libre] if prefer == "word" else [_via_libre, _via_word]
    for conv in chain:
        r = conv()
        if r:
            return r
    return None


# ---------------------------------------------------------------------------
# structural fingerprint of a markdown's tables
# ---------------------------------------------------------------------------

_TABLE_RE = re.compile(r"<table>.*?</table>", re.S | re.I)
_TR_RE = re.compile(r"<tr>.*?</tr>", re.S | re.I)
_CELL_RE = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.S | re.I)
_TAG_RE = re.compile(r"<[^>]+>")


def _cell_text(html: str) -> str:
    t = _TAG_RE.sub("", html)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def fingerprint(md_text: str) -> dict:
    """Structural summary of a markdown: per-table row/col counts and first cell."""
    tables = _TABLE_RE.findall(md_text)
    out = []
    for tb in tables:
        rows = _TR_RE.findall(tb)
        row_cells = [[_cell_text(c) for c in _CELL_RE.findall(r)] for r in rows]
        first = ""
        for rc in row_cells:
            nz = [c for c in rc if c]
            if nz:
                first = nz[0][:40]
                break
        widths = [len(rc) for rc in row_cells] or [0]
        out.append({
            "n_rows": len(rows),
            "modal_cols": max(set(widths), key=widths.count),
            "first_cell": first,
            "n_cells_nonempty": sum(1 for rc in row_cells for c in rc if c),
            # duplicate-header signature: identical consecutive rows at the top
            "leading_dup_rows": _leading_dup_rows(row_cells),
        })
    return {"n_tables": len(tables), "tables": out,
            "total_nonempty_cells": sum(t["n_cells_nonempty"] for t in out)}


def _leading_dup_rows(row_cells) -> int:
    """How many of the first rows are exact duplicates of row 0 (the docx
    header-repeat signature)."""
    if not row_cells:
        return 0
    first = row_cells[0]
    n = 1
    for rc in row_cells[1:]:
        if rc == first:
            n += 1
        else:
            break
    return n if n > 1 else 0


# ---------------------------------------------------------------------------
# comparison + per-paper verdict
# ---------------------------------------------------------------------------

def compare(docx_fp: dict, pdf_fp: dict) -> dict:
    """Compare two fingerprints; classify the difference."""
    issues = []
    dt, pt = docx_fp["n_tables"], pdf_fp["n_tables"]
    if dt < pt:
        issues.append(f"docx found {dt} table(s), PDF found {pt} "
                      f"(docx MISSING {pt - dt})")
    elif dt > pt:
        issues.append(f"docx found {dt} table(s), PDF found {pt} "
                      f"(docx has {dt - pt} extra)")

    # cell-count gap: docx losing data inside tables (collapsed rowspans, dropped
    # primer/sequence rows)
    dc, pc = docx_fp["total_nonempty_cells"], pdf_fp["total_nonempty_cells"]
    if pc and dc < pc * 0.85:
        issues.append(f"docx has {dc} non-empty cells vs PDF {pc} "
                      f"({100*(pc-dc)//pc}% fewer — likely collapsed/lost rows)")

    # header-repeat signature in docx
    dup = [i for i, t in enumerate(docx_fp["tables"]) if t["leading_dup_rows"]]
    if dup:
        issues.append(f"docx has repeated header rows in table(s) {dup} "
                      f"(the multi-level-header duplication bug)")

    severity = "ok"
    if any("MISSING" in s for s in issues):
        severity = "severe"          # whole table lost
    elif any("fewer" in s for s in issues):
        severity = "moderate"        # data collapsed inside tables
    elif issues:
        severity = "minor"           # cosmetic/header repeat only
    return {"severity": severity, "issues": issues}


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------

def find_docx(papers_root: Path):
    return sorted(papers_root.rglob("*.docx"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--papers", default="../data/un_processed_papers",
                    help="root folder of paper subfolders")
    ap.add_argument("--out", default="../output/docx_vs_pdf_report.md",
                    help="report path. Both a .md and a .html are written; "
                         "if this ends in .html the .md is written alongside it "
                         "(and vice-versa).")
    ap.add_argument("--md", default=None,
                    help="explicit path for the markdown report (optional; by "
                         "default it is derived from --out)")
    ap.add_argument("--workdir", default="./docx_audit",
                    help="workspace for generated PDFs, MinerU markdown, and the "
                         "side-by-side diffs (created under source/ by default)")
    ap.add_argument("--force", action="store_true",
                    help="re-convert even if cached outputs exist")
    ap.add_argument("--converter", choices=["word", "libre"], default="word",
                    help="docx->pdf engine to prefer. 'word' (default) uses "
                         "Microsoft Word via docx2pdf — renders complex tables "
                         "far better; 'libre' forces LibreOffice.")
    args = ap.parse_args()

    papers_root = Path(args.papers).resolve()
    workdir = Path(args.workdir).resolve()
    workdir.mkdir(parents=True, exist_ok=True)

    if not papers_root.exists():
        sys.exit(f"papers root not found: {papers_root}")

    docx_files = find_docx(papers_root)
    if not docx_files:
        sys.exit(f"no .docx files under {papers_root}")

    soffice_path = _find_soffice()
    have_soffice = soffice_path is not None
    have_token = bool(os.environ.get("MINERU_TOKEN"))
    print(f"found {len(docx_files)} .docx file(s)")
    if have_soffice:
        print(f"docx->pdf converter: LibreOffice ({soffice_path})")
    else:
        print("docx->pdf converter: NONE")
        _find_soffice(verbose=True)          # print where it looked
    print(f"MINERU_TOKEN set:    {have_token}")
    if not have_soffice:
        print("  -> cannot convert to PDF; will only fingerprint the docx side.")
    if not have_token:
        print("  -> MinerU disabled; PDF side skipped. Set MINERU_TOKEN to enable.")

    results = []
    for i, docx in enumerate(docx_files, 1):
        print(f"\n[{i}/{len(docx_files)}] {docx.relative_to(papers_root)}")
        rec = {"paper": docx.stem, "path": str(docx)}

        # 1. current docx path
        try:
            docx_md = Path(M.docx_to_markdown(str(docx))).read_text(
                encoding="utf-8", errors="replace")
        except Exception as e:
            rec["error"] = f"docx_to_markdown failed: {e}"
            results.append(rec)
            print(f"    docx extraction FAILED: {e}")
            continue
        docx_fp = fingerprint(docx_md)
        rec["docx"] = docx_fp

        # 2. pdf path
        if not (have_soffice and have_token):
            rec["pdf"] = None
            rec["verdict"] = {"severity": "unknown",
                              "issues": ["PDF path unavailable "
                                         "(no converter or no MINERU_TOKEN)"]}
            results.append(rec)
            continue

        pdf = docx_to_pdf(docx, workdir, prefer=args.converter)
        if pdf is None:
            rec["pdf"] = None
            rec["verdict"] = {"severity": "unknown",
                              "issues": ["docx->pdf conversion failed"]}
            results.append(rec)
            continue
        try:
            pdf_md_path = Path(M.doc_to_markdown(pdf, force=args.force))
            pdf_md = pdf_md_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            rec["pdf"] = None
            rec["verdict"] = {"severity": "unknown",
                              "issues": [f"MinerU failed: {e}"]}
            results.append(rec)
            print(f"    MinerU FAILED: {e}")
            continue

        # Collect the MinerU markdown into one browsable folder under the
        # workspace, named by paper, so all the *.pdf.md are together and easy to
        # open — not scattered next to the generated PDFs.
        mineru_dir = workdir / "mineru_md"
        mineru_dir.mkdir(parents=True, exist_ok=True)
        collected = mineru_dir / f"{docx.stem}.pdf.md"
        try:
            collected.write_text(pdf_md, encoding="utf-8")
            rec["mineru_md"] = str(collected)
            print(f"    [mineru] markdown -> {collected}")
        except Exception as e:
            print(f"    [mineru] could not copy markdown: {e}")

        # byte-equal short-circuit (requested) — essentially never true
        if docx_md == pdf_md:
            rec["pdf"] = fingerprint(pdf_md)
            rec["verdict"] = {"severity": "identical",
                              "issues": ["byte-identical output — skipped"]}
            results.append(rec)
            print("    byte-identical — skipped")
            continue

        pdf_fp = fingerprint(pdf_md)
        rec["pdf"] = pdf_fp
        rec["verdict"] = compare(docx_fp, pdf_fp)

        # per-paper side-by-side HTML (VS-Code-like), so the report links to a
        # browsable view of exactly what differs for this paper.
        if DIFF is not None:
            try:
                diff_dir = workdir / "diffs"
                diff_dir.mkdir(parents=True, exist_ok=True)
                dtabs = DIFF.parse_tables(docx_md)
                ptabs = DIFF.parse_tables(pdf_md)
                pairs = DIFF.pair_tables(dtabs, ptabs)
                html_path = diff_dir / f"{docx.stem}_diff.html"
                html_path.write_text(
                    DIFF.render_html(dtabs, ptabs, pairs, docx.stem),
                    encoding="utf-8")
                rec["diff_html"] = str(html_path)
            except Exception as e:
                print(f"    [diff] side-by-side failed: {e}")

        results.append(rec)
        v = rec["verdict"]
        print(f"    verdict: {v['severity']}")
        for msg in v["issues"]:
            print(f"      - {msg}")

    write_report(results, Path(args.out).resolve(),
                 md_path=Path(args.md).resolve() if args.md else None)

    mineru_dir = workdir / "mineru_md"
    if mineru_dir.exists():
        n = len(list(mineru_dir.glob("*.pdf.md")))
        print(f"\nMinerU markdown files ({n}) -> {mineru_dir}")
        print("  (all the *.pdf.md are collected here for browsing)")


def write_report(results, out_path: Path, md_path: Path = None):
    # The audit always emits BOTH a markdown report and an HTML index. Resolve
    # them to DISTINCT paths from whatever --out was given, so the two never
    # write to the same file:
    #   --out foo.html  -> index=foo.html,  md=foo.md
    #   --out foo.md    -> md=foo.md,        index=foo.html
    #   --md bar.md overrides the markdown path explicitly.
    if out_path.suffix.lower() == ".html":
        _index_path = out_path
        _report_md = md_path or out_path.with_suffix(".md")
    else:
        _report_md = md_path or out_path
        _index_path = out_path.with_suffix(".html")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    order = {"severe": 0, "moderate": 1, "minor": 2, "unknown": 3,
             "identical": 4, "ok": 5}
    results = sorted(results, key=lambda r: order.get(
        r.get("verdict", {}).get("severity", "ok"), 9))

    from collections import Counter
    counts = Counter(r.get("verdict", {}).get("severity", "error")
                     for r in results)

    lines = ["# Docx vs PDF (MinerU) structural audit", "",
             f"{len(results)} .docx file(s) examined.", "",
             "## Summary", ""]
    for sev in ("severe", "moderate", "minor", "unknown", "identical", "ok",
                "error"):
        if counts.get(sev):
            lines.append(f"- **{sev}**: {counts[sev]}")
    lines += ["", "Severity meaning:",
              "- **severe** — the docx path LOST a whole table the PDF kept.",
              "- **moderate** — docx collapsed rows inside tables (fewer cells).",
              "- **minor** — cosmetic / repeated header rows only.",
              "- **unknown** — PDF side could not run (no token/converter).",
              "", "## Per-paper detail", ""]

    for r in results:
        v = r.get("verdict", {})
        lines.append(f"### {r['paper']} — {v.get('severity','?')}")
        if r.get("diff_html"):
            rel = Path(r["diff_html"])
            lines.append(f"- side-by-side: [{rel.name}]({rel.as_uri()})")
        if r.get("mineru_md"):
            mm = Path(r["mineru_md"])
            lines.append(f"- MinerU markdown: [{mm.name}]({mm.as_uri()})")
        if r.get("error"):
            lines.append(f"- ERROR: {r['error']}")
            lines.append("")
            continue
        d = r.get("docx") or {}
        p = r.get("pdf") or {}
        lines.append(f"- docx: {d.get('n_tables','?')} table(s), "
                     f"{d.get('total_nonempty_cells','?')} non-empty cells")
        if p:
            lines.append(f"- pdf : {p.get('n_tables','?')} table(s), "
                         f"{p.get('total_nonempty_cells','?')} non-empty cells")
        for msg in v.get("issues", []):
            lines.append(f"- {msg}")
        # side-by-side table list
        if d.get("tables") or p.get("tables"):
            lines.append("")
            lines.append("| # | docx rows×cols (first cell) | pdf rows×cols (first cell) |")
            lines.append("|---|---|---|")
            n = max(len(d.get("tables", [])), len(p.get("tables", [])))
            for k in range(n):
                dt = d.get("tables", [])
                pt = p.get("tables", [])
                dcell = (f"{dt[k]['n_rows']}×{dt[k]['modal_cols']} "
                         f"({dt[k]['first_cell']!r})") if k < len(dt) else "—"
                pcell = (f"{pt[k]['n_rows']}×{pt[k]['modal_cols']} "
                         f"({pt[k]['first_cell']!r})") if k < len(pt) else "—"
                lines.append(f"| {k} | {dcell} | {pcell} |")
        lines.append("")

    _report_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nreport (markdown) -> {_report_md}")
    print("severity counts:", dict(counts))

    _write_index_html(results, counts, _index_path)
    print(f"index  (html)     -> {_index_path}")


def _write_index_html(results, counts, index_path):
    sev_color = {"severe": "#d03b3b", "moderate": "#eda100", "minor": "#3987e5",
                 "unknown": "#888", "identical": "#199e70", "ok": "#199e70"}
    order = {"severe": 0, "moderate": 1, "minor": 2, "unknown": 3,
             "identical": 4, "ok": 5}
    rows = sorted(results, key=lambda r: order.get(
        r.get("verdict", {}).get("severity", "ok"), 9))
    parts = [
        "<!doctype html><meta charset='utf-8'><title>docx vs pdf audit</title>",
        "<style>",
        "body{font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;",
        "margin:0;background:#f6f7f9;color:#1a1a1a}",
        "header{background:#fff;border-bottom:1px solid #ddd;padding:16px 24px}",
        "h1{font-size:18px;margin:0 0 8px}",
        ".counts span{margin-right:14px;font-size:13px}",
        ".wrap{padding:16px 24px}",
        "table{border-collapse:collapse;width:100%;background:#fff;",
        "border:1px solid #e2e4e8;border-radius:8px;overflow:hidden}",
        "th,td{text-align:left;padding:8px 12px;border-bottom:1px solid #eee;font-size:13px}",
        "th{background:#f0f2f5}",
        ".pill{display:inline-block;padding:1px 8px;border-radius:10px;color:#fff;font-size:12px}",
        "a{color:#0a56b3;text-decoration:none}a:hover{text-decoration:underline}",
        "</style>",
        "<header><h1>docx vs pdf / MinerU — structural audit</h1>",
        "<div class='counts'>"]
    for sev in ("severe", "moderate", "minor", "unknown", "identical", "ok"):
        if counts.get(sev):
            parts.append(f"<span><b style='color:{sev_color[sev]}'>●</b> "
                         f"{sev}: {counts[sev]}</span>")
    parts.append("</div></header><div class='wrap'><table>")
    parts.append("<tr><th>severity</th><th>paper</th><th>docx tbl</th>"
                 "<th>pdf tbl</th><th>docx cells</th><th>pdf cells</th>"
                 "<th>side-by-side</th></tr>")
    for r in rows:
        v = r.get("verdict", {})
        sev = v.get("severity", "?")
        d = r.get("docx") or {}
        p = r.get("pdf") or {}
        link = ""
        if r.get("diff_html"):
            link = f"<a href='{Path(r['diff_html']).as_uri()}'>view →</a>"
        parts.append(
            f"<tr><td><span class='pill' style='background:{sev_color.get(sev,'#888')}'>"
            f"{sev}</span></td><td>{html_escape(r['paper'])}</td>"
            f"<td>{d.get('n_tables','—')}</td><td>{p.get('n_tables','—')}</td>"
            f"<td>{d.get('total_nonempty_cells','—')}</td>"
            f"<td>{p.get('total_nonempty_cells','—')}</td><td>{link}</td></tr>")
    parts.append("</table></div>")
    index_path.write_text("".join(parts), encoding="utf-8")


def html_escape(s):
    import html as _h
    return _h.escape(str(s))


if __name__ == "__main__":
    main()