"""
collect_reports.py — gather every *_report.txt under output/ into one place.

Put this file inside your `output/` folder (next to the per-paper subfolders)
and run it from there:

    python collect_reports.py              # prints a sorted F1 summary table
    python collect_reports.py --full       # also writes all_reports.txt (every report concatenated)
    python collect_reports.py --csv         # also writes summary.csv

It looks for files named like '<paper>_report.txt' in any subfolder (and in the
current folder), parses the precision/recall/F1 and row counts, and prints a
table sorted worst-to-best by F1 so the biggest problems are at the top.
"""

import argparse
import csv
import re
import sys
from pathlib import Path

# Regexes tolerant of the report layout (extra spaces, etc.). Newest report
# format only: the STRICT/SCOPED P/R/F1 split and 'spurious, in scope'. Regenerate
# stale reports with `python evaluate.py --all` if they show as unparsed.
RE_PRF_SCOPED = re.compile(
    r"SCOPED\s+P/R/F1\s*:\s*([\d.]+)\s*/\s*([\d.]+)\s*/\s*([\d.]+)"
)
RE_PRF_STRICT = re.compile(
    r"STRICT\s+P/R/F1\s*:\s*([\d.]+)\s*/\s*([\d.]+)\s*/\s*([\d.]+)"
)
RE_TP = re.compile(r"matched \(TP\)\s*:\s*(\d+)")
# 'spurious, in scope' is the scoped FP (matches the SCOPED precision).
RE_FP = re.compile(r"spurious,\s*in scope\s*:\s*(\d+)")
RE_FN = re.compile(r"missed \(FN\)\s*:\s*(\d+)")
RE_GT = re.compile(r"GROUND TRUTH\s*:.*?\((\d+)\s*rows\)")
RE_PRED = re.compile(r"PREDICTION\s*:.*?\((\d+)\s*rows\)")


def find_reports(root: Path):
    """Every *_report.txt at any depth under root (deduped, sorted by name)."""
    seen = {}
    for p in root.rglob("*_report.txt"):
        if p.is_file():
            seen[p.resolve()] = p
    return sorted(seen.values(), key=lambda x: x.name.lower())


def parse_report(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="ignore")

    def grab(rx, default=None, cast=float):
        m = rx.search(text)
        if not m:
            return default
        return cast(m.group(1)) if cast else m.group(1)

    prf = RE_PRF_SCOPED.search(text) or RE_PRF_STRICT.search(text)
    precision = float(prf.group(1)) if prf else None
    recall = float(prf.group(2)) if prf else None
    f1 = float(prf.group(3)) if prf else None

    # paper name = filename minus the _report.txt suffix
    name = path.name
    if name.lower().endswith("_report.txt"):
        name = name[: -len("_report.txt")]

    return {
        "paper": name,
        "path": str(path),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": grab(RE_TP, None, int),
        "fp": grab(RE_FP, None, int),
        "fn": grab(RE_FN, None, int),
        "gt_rows": grab(RE_GT, None, int),
        "pred_rows": grab(RE_PRED, None, int),
    }


def fmt(v, width, prec=None):
    if v is None:
        return "—".rjust(width)
    if prec is not None and isinstance(v, float):
        return f"{v:.{prec}f}".rjust(width)
    return str(v).rjust(width)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="folder to scan (default: current)")
    ap.add_argument("--full", action="store_true",
                    help="also write all_reports.txt with every report's full text")
    ap.add_argument("--csv", action="store_true",
                    help="also write report_summary.csv")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    reports = find_reports(root)
    if not reports:
        print(f"No *_report.txt found under {root}")
        sys.exit(1)

    rows = [parse_report(p) for p in reports]
    # sort worst-to-best by F1; None F1 sinks to the top as "needs attention"
    rows.sort(key=lambda r: (r["f1"] is not None, r["f1"] if r["f1"] is not None else -1))

    # ---- print summary table (worst first) ----
    print(f"\nFound {len(rows)} report(s) under {root}\n")
    header = (f"{'paper':28} {'F1':>6} {'prec':>6} {'rec':>6} "
              f"{'TP':>5} {'FP':>6} {'FN':>6} {'gt':>5} {'pred':>6}")
    print(header)
    print("-" * len(header))
    f1s = []
    for r in rows:
        if r["f1"] is not None:
            f1s.append(r["f1"])
        print(f"{r['paper'][:28]:28} "
              f"{fmt(r['f1'],6,3)} {fmt(r['precision'],6,3)} {fmt(r['recall'],6,3)} "
              f"{fmt(r['tp'],5)} {fmt(r['fp'],6)} {fmt(r['fn'],6)} "
              f"{fmt(r['gt_rows'],5)} {fmt(r['pred_rows'],6)}")
    print("-" * len(header))
    if f1s:
        print(f"mean F1 over {len(f1s)} parsed report(s): {sum(f1s)/len(f1s):.3f}")

    # ---- optional: concatenated full text ----
    if args.full:
        out = root / "all_reports.txt"
        with out.open("w", encoding="utf-8") as fh:
            for p in reports:
                fh.write("#" * 70 + "\n")
                fh.write(f"# {p.name}\n")
                fh.write("#" * 70 + "\n")
                fh.write(p.read_text(encoding="utf-8", errors="ignore"))
                fh.write("\n\n")
        print(f"\nWrote {out}")

    # ---- optional: CSV ----
    if args.csv:
        out = root / "report_summary.csv"
        cols = ["paper", "f1", "precision", "recall",
                "tp", "fp", "fn", "gt_rows", "pred_rows", "path"]
        with out.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            for r in rows:
                w.writerow({k: r.get(k) for k in cols})
        print(f"Wrote {out}")


if __name__ == "__main__":
    main()