"""
read_tables.py — orchestrate the whole table-reading pipeline and report.

For a file or a paper folder it: runs every applicable backend, reconciles their
readings (cross-checking for errors), and writes:

  <out>/<name>.tables.json   — reconciled tables as records, with provenance
  <out>/<name>.report.txt    — human-readable: each table as an aligned grid,
                               plus a CONFLICTS section listing cells where
                               backends disagreed (the ones to eyeball)

Usage:
    python read_tables.py paper.pdf
    python read_tables.py path/to/PaperFolder
    python read_tables.py folder --enable pdfplumber,geometry,docx
    python read_tables.py folder --out results
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from table_ir import RawTable
from backends import backends_for, ALL_BACKENDS
from reconcile import reconcile, ReconciledTable

SOURCE_EXTS = {".pdf", ".docx", ".xlsx", ".xls"}


# ---------------------------------------------------------------------------
# extraction
# ---------------------------------------------------------------------------

def extract_all(path: str, enable=None):
    """Run every applicable, available backend on one file. Returns (raw_tables,
    per-backend counts)."""
    raws, counts = [], {}
    for b in backends_for(path, enable):
        try:
            got = b.extract(path)
        except Exception as e:
            counts[b.name] = f"error: {e}"
            continue
        counts[b.name] = len(got)
        raws.extend(got)
    return raws, counts


def _ground_truth_files(files):
    """A paper folder ships a volunteer answer-key spreadsheet whose stem matches
    a document in the folder (Barber2017.xlsx next to Barber2017.pdf/.docx).
    Ingesting it as a SOURCE makes evaluation circular, so it must be excluded."""
    doc_stems = {p.stem.lower() for p in files
                 if p.suffix.lower() in (".pdf", ".docx")}
    return {p.name for p in files
            if p.suffix.lower() in (".xlsx", ".xls") and p.stem.lower() in doc_stems}


def source_files(target: Path, exclude=()):
    if target.is_file():
        return [target]
    files = sorted(p for p in target.iterdir()
                   if p.is_file() and p.suffix.lower() in SOURCE_EXTS)
    skip = set(exclude) | _ground_truth_files(files)
    kept = [p for p in files if p.name not in skip]
    for name in sorted(skip):
        print(f"  [skip] {name} (ground-truth / excluded)")
    return kept


# ---------------------------------------------------------------------------
# rendering
# ---------------------------------------------------------------------------

def render_grid(grid, max_cell=24) -> str:
    if not grid:
        return "(empty)"
    ncols = max(len(r) for r in grid)
    grid = [r + [""] * (ncols - len(r)) for r in grid]

    def clip(s):
        return s if len(s) <= max_cell else s[:max_cell - 1] + "\u2026"

    widths = [min(max_cell, max(len(clip(r[c])) for r in grid)) for c in range(ncols)]
    line = lambda cells: " | ".join(clip(c).ljust(widths[i]) for i, c in enumerate(cells))
    return "\n".join([line(grid[0]), "-+-".join("-" * w for w in widths)]
                     + [line(r) for r in grid[1:]])


def render_reconciled(rt: ReconciledTable, tno: int) -> str:
    out = [f"\n===== TABLE {tno}  [{rt.confidence}]  backends={rt.backends} ====="]
    out.append(f"primary: {rt.primary_backend}   header: {rt.header}")
    out.append(f"records: {len(rt.records)}   conflicts: {rt.n_conflicts}")
    # a compact grid view of the primary records
    if rt.records:
        grid = [rt.header] + [[str(r.get(h, "")) for h in rt.header] for r in rt.records]
        out.append(render_grid(grid))
    if rt.disagreements:
        out.append("\n  -- DISAGREEMENTS (check these) --")
        for d in rt.disagreements[:40]:
            if d.kind == "cell":
                vs = "  ".join(f"{b}={v!r}" for b, v in d.values.items())
                out.append(f"   cell  [{d.identifier}] {d.column}: {vs}")
            elif d.kind == "missing_row":
                vs = " ".join(f"{b}:{v}" for b, v in d.values.items())
                out.append(f"   row   [{d.identifier}] present: {vs}")
            else:
                out.append(f"   {d.kind}: {d.identifier} {d.note}")
        if len(rt.disagreements) > 40:
            out.append(f"   ... (+{len(rt.disagreements) - 40} more)")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------

def process(target: Path, out_dir: Path, enable=None, exclude=()):
    files = source_files(target, exclude)
    name = target.stem if target.is_file() else target.name
    report = ["#" * 74, f"# {name}", "#" * 74]
    all_reconciled = []

    for f in files:
        report.append(f"\n### source: {f.name}")
        raws, counts = extract_all(str(f), enable)
        report.append(f"  backends: {counts}")
        if not raws:
            report.append("  (no tables from any backend)")
            continue
        reconciled = reconcile(raws)
        for i, rt in enumerate(reconciled):
            report.append(render_reconciled(rt, len(all_reconciled) + i))
        all_reconciled.extend(reconciled)

    # machine output
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = [{
        "primary_backend": rt.primary_backend,
        "backends": rt.backends,
        "confidence": rt.confidence,
        "header": rt.header,
        "records": rt.records,
        "conflicts": [{"identifier": d.identifier, "column": d.column,
                       "values": d.values, "kind": d.kind}
                      for d in rt.disagreements],
    } for rt in all_reconciled]
    (out_dir / f"{name}.tables.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / f"{name}.report.txt").write_text("\n".join(report), encoding="utf-8")

    n_conf = sum(rt.n_conflicts for rt in all_reconciled)
    n_single = sum(1 for rt in all_reconciled if rt.confidence == "single")
    print(f"{name}: {len(all_reconciled)} table(s), {n_conf} conflicting cell(s), "
          f"{n_single} single-source; -> {out_dir}/{name}.report.txt")
    return all_reconciled


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        print("\nAvailable backends:")
        for b in ALL_BACKENDS:
            print(f"  {b.name:<12} {'available' if b.available() else 'not installed'}"
                  f"  ({', '.join(b.exts)})")
        return
    enable = None
    out_dir = Path("table_results")
    pos = []
    i = 0
    while i < len(args):
        if args[i] == "--enable":
            enable = set(args[i + 1].split(",")); i += 2
        elif args[i] == "--out":
            out_dir = Path(args[i + 1]); i += 2
        else:
            pos.append(args[i]); i += 1
    target = Path(pos[0])
    process(target, out_dir, enable)


if __name__ == "__main__":
    main()
