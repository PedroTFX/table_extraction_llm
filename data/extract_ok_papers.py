"""
extract_ok_papers.py

Reads the Papers4Training CSV, finds rows whose 'Notes' column ends with 'OK',
and for each such row searches the 'papers_done' folder for files whose names
match the row's Filename. Matching files are placed (copied or moved) into a
per-row subfolder under 'un_processed_papers/'.

Layout produced:
    un_processed_papers/
        Ahmad2024/
            Ahmad2024.pdf
            Ahmad2024.xlsx
        Araujo2021/
            Araujo2021.xlsx
            Araujo2021_S1 (1).docx
            Araujo_2021 (1).pdf      <-- caught by 'loose' matching

Edit the CONFIG block to point at your paths or change copy/move/match mode.
"""

import csv
import re
import shutil
import sys
from pathlib import Path

# -------------------- CONFIG --------------------
# If CSV_PATH is None, the script auto-discovers the first file matching
# 'Papers4Training*.csv' in the working directory.
CSV_PATH: Path | None = None

SOURCE_DIR = Path("papers_done")
DEST_DIR = Path("un_processed_papers")

# "copy" leaves papers_done untouched (safe default).
# "move" removes the file from papers_done after placing it in un_processed_papers.
MODE = "copy"   # "copy" or "move"

# How to match files in SOURCE_DIR against the row Filename.
#   "loose"  -> ignore case, underscores, spaces, dashes when comparing prefixes.
#               Handles both 'Araujo2021.pdf' and 'Araujo_2021 (1).pdf' for row
#               'Araujo2021'. RECOMMENDED DEFAULT.
#   "prefix" -> filename must start exactly with the row name.
#   "exact"  -> filename without extension must equal the row name.
MATCH = "loose"
# ------------------------------------------------


def row_is_ok(notes: str) -> bool:
    """True if the Notes cell ends with 'OK' (case-insensitive, tolerant of trailing punctuation)."""
    if not notes:
        return False
    return notes.strip().rstrip(".;,: ").upper().endswith("OK")


def normalize(s: str) -> str:
    """Lowercase and strip non-alphanumerics. Used for 'loose' matching."""
    return re.sub(r"[^a-z0-9]", "", s.lower())


def discover_csv() -> Path:
    if CSV_PATH is not None:
        if not CSV_PATH.exists():
            sys.exit(f"ERROR: CSV not found at {CSV_PATH.resolve()}")
        return CSV_PATH
    candidates = sorted(Path.cwd().glob("Papers4Training*.csv"))
    if not candidates:
        sys.exit("ERROR: no file matching 'Papers4Training*.csv' in the current "
                 f"directory ({Path.cwd()}). Set CSV_PATH explicitly in the script.")
    if len(candidates) > 1:
        print(f"Multiple CSV candidates found, using the first: {candidates[0].name}")
    return candidates[0]


def read_ok_filenames(csv_path: Path) -> list[str]:
    """De-duplicated, order-preserving list of Filenames whose Notes end with OK."""
    seen: set[str] = set()
    ordered: list[str] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if "Filename" not in reader.fieldnames or "Notes" not in reader.fieldnames:
            sys.exit(f"ERROR: CSV must have 'Filename' and 'Notes' columns. "
                     f"Found: {reader.fieldnames}")
        for row in reader:
            name = (row.get("Filename") or "").strip()
            notes = row.get("Notes") or ""
            if name and row_is_ok(notes) and name not in seen:
                seen.add(name)
                ordered.append(name)
    return ordered


def find_matches(source_dir: Path, row_name: str) -> list[Path]:
    """Find files in source_dir matching the row name according to MATCH mode."""
    files = [p for p in source_dir.iterdir() if p.is_file()]
    if MATCH == "exact":
        return sorted(p for p in files if p.stem == row_name)
    if MATCH == "prefix":
        return sorted(p for p in files if p.name.startswith(row_name))
    # loose
    target = normalize(row_name)
    return sorted(p for p in files if normalize(p.stem).startswith(target))


def transfer(src: Path, dst: Path) -> None:
    if MODE == "move":
        shutil.move(str(src), str(dst))
    else:
        shutil.copy2(src, dst)


def main() -> None:
    if MODE not in {"copy", "move"}:
        sys.exit(f"ERROR: MODE must be 'copy' or 'move', got {MODE!r}")
    if MATCH not in {"loose", "prefix", "exact"}:
        sys.exit(f"ERROR: MATCH must be 'loose', 'prefix', or 'exact', got {MATCH!r}")
    if not SOURCE_DIR.is_dir():
        sys.exit(f"ERROR: source folder not found: {SOURCE_DIR.resolve()}")

    csv_path = discover_csv()
    DEST_DIR.mkdir(parents=True, exist_ok=True)

    ok_names = read_ok_filenames(csv_path)
    print(f"Using CSV: {csv_path.name}")
    print(f"Found {len(ok_names)} unique OK rows")
    print(f"Mode: {MODE.upper()} | Match: {MATCH} | "
          f"Source: {SOURCE_DIR} -> Dest: {DEST_DIR}\n")

    rows_with_matches = 0
    rows_without_matches: list[str] = []
    total_files = 0

    for name in ok_names:
        matches = find_matches(SOURCE_DIR, name)
        if not matches:
            rows_without_matches.append(name)
            continue

        target_folder = DEST_DIR / name
        target_folder.mkdir(parents=True, exist_ok=True)

        for src in matches:
            dst = target_folder / src.name
            if dst.exists():
                print(f"  skip (already exists): {dst}")
                continue
            transfer(src, dst)
            total_files += 1
            print(f"  {MODE}: {src.name} -> {target_folder.name}/")

        rows_with_matches += 1

    verb_past = "moved" if MODE == "move" else "copied"
    print("\n--- Summary ---")
    print(f"OK rows with at least one matching file: {rows_with_matches}")
    print(f"OK rows with NO matching file:           {len(rows_without_matches)}")
    print(f"Total files {verb_past}:                {total_files}")
    if rows_without_matches:
        print("\nRows with no matching files in papers_done/:")
        for n in rows_without_matches:
            print(f"  - {n}")


if __name__ == "__main__":
    main()
