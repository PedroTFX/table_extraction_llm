#!/usr/bin/env python3
"""
fix_dates_on_xlsx.py — repair date-corrupted ratio cells across paper folders.

Some complementary spreadsheets were typed into General-format cells, so a value
like '3.15' was read by Excel as 15 March and stored as a DATE. This walks every
paper folder, finds those datetime cells, and rewrites them to the numeric
month.day value (day zero-padded: '1.08', not '1.8', matching the two-decimal
convention those ratio columns use).

This is the batch/one-shot version. The SAME repair also runs automatically,
per-paper, inside mineru_extract.xlsx_to_html_tables (via _repair_date_ratio), so
new pipeline runs are fixed on the fly. Use this script to clean the source files
on disk once.

IMPORTANT — read before running:
  This assumes every datetime cell it finds is a corrupted ratio, never a real
  calendar date. If any sheet has a genuine date column, this would destroy it.
  So it DEFAULTS TO A DRY RUN: it prints what it WOULD change and writes nothing.
  Inspect the output, then re-run with --apply to save. --max-month skips
  datetimes whose month exceeds a threshold (a guard against real dates).

Usage:
    python fix_dates_on_xlsx.py --parent "C:/.../un_processed_papers"          # dry run
    python fix_dates_on_xlsx.py --parent "C:/.../un_processed_papers" --apply   # write
"""

from __future__ import annotations

import argparse
from datetime import date, datetime
from pathlib import Path

from openpyxl import load_workbook


def repair_value(value):
    """datetime -> float month.day, else None. Same logic as the pipeline's
    mineru_extract._repair_date_ratio."""
    if not isinstance(value, (datetime, date)):
        return None
    return float(f"{value.month}.{value.day:02d}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parent", required=True,
                    help="folder containing the per-paper subfolders")
    ap.add_argument("--apply", action="store_true",
                    help="actually write changes (default: dry run, writes nothing)")
    ap.add_argument("--max-month", type=int, default=12,
                    help="skip a datetime whose month exceeds this — guards "
                         "against rewriting a genuine date (default 12)")
    args = ap.parse_args()

    parent = Path(args.parent)
    if not parent.is_dir():
        raise SystemExit(f"not a folder: {parent}")

    total_files = total_repairs = skipped = 0

    for folder in sorted(parent.iterdir()):
        if not folder.is_dir():
            continue
        for excel_file in sorted(folder.glob("*.xlsx")):
            wb = load_workbook(excel_file)
            modified = False
            repaired_here = 0
            file_lines = []

            for ws in wb.worksheets:
                for row in ws.iter_rows():
                    for cell in row:
                        if not isinstance(cell.value, (datetime, date)):
                            continue
                        if cell.value.month > args.max_month:
                            skipped += 1
                            continue
                        repaired = repair_value(cell.value)
                        try:
                            shown = cell.value.strftime("%d-%b")
                        except Exception:
                            shown = str(cell.value)
                        file_lines.append(
                            f"    {ws.title} {cell.coordinate}: "
                            f"{shown} -> {repaired:.2f}")
                        if args.apply:
                            cell.style = "Normal"
                            cell.value = repaired
                            cell.number_format = "0.00"
                        modified = True
                        repaired_here += 1

            if modified:
                print(f"\n{excel_file.relative_to(parent)}  ({repaired_here} cell(s))")
                for ln in file_lines:
                    print(ln)
                if args.apply:
                    wb.save(excel_file)
                    print("    saved.")
                total_repairs += repaired_here
            total_files += 1

    mode = "APPLIED" if args.apply else "DRY RUN (nothing written)"
    print("\n" + "-" * 40)
    print(f"mode           : {mode}")
    print(f"files scanned  : {total_files}")
    print(f"cells repaired : {total_repairs}")
    if skipped:
        print(f"skipped (month > {args.max_month}): {skipped}")
    if not args.apply and total_repairs:
        print("\nRe-run with --apply to write these changes.")
    print("-" * 40)


if __name__ == "__main__":
    main()
