"""
diagnose_zeros.py — collect everything needed to explain why a paper scored 0.

For each paper it reports, side by side:
  * the MinerU markdown: which source files were converted, whether every page
    made it in (<!-- page N of M -->), how many <table> blocks there are;
  * the pipeline output: CSV row count, mapping JSONs, report header, the
    misses summary, and a few predicted vs ground-truth rows;
  * file timestamps (an output CSV older than its markdown = stale result);
  * the environment: Ollama reachable + which models are pulled, MinerU version.

Usage (from source/):
    python diagnose_zeros.py                 # every paper with F1 == 0 in output/summary.csv
    python diagnose_zeros.py Baine2024 Cecala2021
Writes ../output/diag_zeros.txt (also printed).
"""

from __future__ import annotations

import csv
import datetime as _dt
import json
import os
import re
import subprocess
import sys
import urllib.request as _rq
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAPERS = ROOT / "data" / "un_processed_papers"
OUTPUT = ROOT / "output"
PAGE_RE = re.compile(r"<!--\s*page\s+(\d+)\s+of\s+(\d+)\s*-->")


def _mtime(p: Path) -> str:
    return _dt.datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")


def _zero_papers() -> list[str]:
    s = OUTPUT / "summary.csv"
    if not s.exists():
        return []
    out = []
    with open(s, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            try:
                if float(row.get("f1") or "nan") == 0.0:
                    out.append(row["paper"])
            except ValueError:
                pass
    return out


def _env(lines: list[str]) -> None:
    lines.append("=" * 78)
    lines.append("ENVIRONMENT")
    lines.append("=" * 78)
    try:
        with _rq.urlopen("http://127.0.0.1:11434/api/tags", timeout=5) as r:
            models = [m["name"] for m in json.load(r).get("models", [])]
        lines.append(f"ollama: reachable, models = {models}")
        for need in ("gemma4:e2b", "gemma4:e4b-it-qat"):
            if need not in models:
                lines.append(f"  !! model used by the pipeline is NOT pulled: {need}")
    except Exception as e:
        lines.append(f"ollama: NOT reachable ({type(e).__name__}: {e})")
    exe = os.environ.get("MINERU_EXE", "mineru")
    try:
        v = subprocess.run([exe, "version"], capture_output=True, text=True, timeout=60)
        lines.append("mineru: " + " | ".join(v.stdout.split("\n")[:2]).strip())
    except Exception as e:
        lines.append(f"mineru: not runnable ({e})")
    lines.append("")


def _md_section(folder: Path, lines: list[str]) -> float | None:
    paper = folder.name
    full = folder / f"{paper}_full.md"
    for md in sorted(folder.glob("*.md")):
        t = md.read_text(encoding="utf-8", errors="replace")
        marks = PAGE_RE.findall(t)
        pages = f"{len({n for n, _ in marks})}/{marks[0][1]} pages" if marks else "no page marks"
        flag = "  !! INCOMPLETE" if marks and len({n for n, _ in marks}) < int(marks[0][1]) else ""
        lines.append(f"  md  {md.name:<40} {len(t):>8} chars  {t.count('<table'):>3} tables  "
                     f"{pages}  ({_mtime(md)}){flag}")
    if not full.exists():
        lines.append(f"  !! {full.name} MISSING")
        return None
    return full.stat().st_mtime


def _gt_sample(folder: Path, n: int = 4) -> list[str]:
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from mineru_extract import classify_folder
        _, gt, _ = classify_folder(folder)
        if not gt:
            return ["  (no ground-truth file found)"]
        import openpyxl
        ws = openpyxl.load_workbook(gt, read_only=True, data_only=True).active
        rows = list(ws.iter_rows(max_row=n + 1, values_only=True))
        return [f"  GT  {Path(gt).name}"] + ["    " + " | ".join("" if c is None else str(c) for c in r)[:220]
                                             for r in rows]
    except Exception as e:
        return [f"  (GT read failed: {e})"]


def _out_section(paper: str, md_mtime: float | None, lines: list[str]) -> None:
    out = OUTPUT / paper
    csv_p = out / f"{paper}.csv"
    if not out.exists():
        lines.append("  !! no output folder")
        return
    lines.append(f"  mapping JSONs: {len(list(out.glob('*_mapping.json')))}   "
                 f"files: {sorted(p.name for p in out.iterdir())[:12]}")
    if not csv_p.exists():
        lines.append("  !! output CSV missing")
    else:
        with open(csv_p, encoding="utf-8", errors="replace") as fh:
            rows = list(csv.reader(fh))
        stale = ""
        if md_mtime and csv_p.stat().st_mtime < md_mtime:
            stale = "  !! CSV OLDER than _full.md (stale result)"
        lines.append(f"  CSV {csv_p.name}: {max(len(rows) - 1, 0)} data rows ({_mtime(csv_p)}){stale}")
        for r in rows[:5]:
            lines.append("    " + " | ".join(r)[:220])
    rep = out / f"{paper}_report.txt"
    if rep.exists():
        head = rep.read_text(encoding="utf-8", errors="replace").splitlines()
        lines.append(f"  report ({_mtime(rep)}):")
        lines += ["    " + l for l in head[:8]]
        # the category/P/R/F1 block and any "cause" tallies
        for i, l in enumerate(head):
            if "category" in l and "TP" in l:
                lines += ["    " + x for x in head[i:i + 6]]
                break
    ms = out / f"{paper}_misses_summary.json"
    if ms.exists():
        try:
            lines.append("  misses_summary: " + json.dumps(json.loads(ms.read_text(encoding="utf-8")))[:900])
        except Exception:
            pass
    mc = out / f"{paper}_misses.csv"
    if mc.exists():
        with open(mc, encoding="utf-8", errors="replace") as fh:
            mrows = list(csv.reader(fh))
        lines.append(f"  misses.csv: {max(len(mrows) - 1, 0)} rows; first few:")
        lines += ["    " + " | ".join(r)[:220] for r in mrows[:6]]


def main(papers: list[str]) -> None:
    lines: list[str] = []
    _env(lines)
    if not papers:
        papers = _zero_papers()
    if not papers:
        papers = sorted(p.name for p in PAPERS.iterdir() if p.is_dir())
    for paper in papers:
        folder = PAPERS / paper
        lines.append("=" * 78)
        lines.append(f"PAPER {paper}")
        lines.append("=" * 78)
        if not folder.is_dir():
            lines.append("  !! no data folder")
            continue
        lines.append(f"  sources: {sorted(p.name for p in folder.iterdir() if not p.name.endswith('.md'))}")
        md_mtime = _md_section(folder, lines)
        _out_section(paper, md_mtime, lines)
        lines += _gt_sample(folder)
        lines.append("")
    text = "\n".join(lines)
    target = OUTPUT / "diag_zeros.txt"
    OUTPUT.mkdir(exist_ok=True)
    target.write_text(text, encoding="utf-8")
    print(text)
    print(f"\n-> written to {target}")


if __name__ == "__main__":
    main(sys.argv[1:])
