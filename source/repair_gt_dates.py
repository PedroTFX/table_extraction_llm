"""
repair_gt_dates.py — undo Excel date corruption in the ground-truth xlsx files,
checked against each paper's own text.

How the corruption happened: a value typed as '2.5' was auto-converted by Excel
into a date (5 February), and data/…/fix_dates_on_xlsx.py later turned every
date back into month.day with the day ZERO-PADDED — so '2.5' came back as
'2.05'. The padding is right for two-digit values ('3.15') but wrong for a
one-digit decimal, and the file alone cannot tell which it was. The paper can.
A locale that reads day.month instead produces the swapped form ('1.08' ->
'8.01', GibbParr2013).

A value is repaired only when ALL hold:
  * it looks like a restored date: M.DD with M in 1..12 and a padded day
    01..09 (e.g. 2.05, 11.02) — never x.00, never 0.xx;
  * that exact value does NOT occur in the paper (markdown incl. supplements);
  * a candidate original DOES occur: 'M.D' (2.05 -> 2.5), or the swapped
    'D.MM' / 'D.M' (8.01 -> 1.08 / 1.8), tried in that order.

    python repair_gt_dates.py            # dry run: writes the change log only
    python repair_gt_dates.py --apply    # also rewrites the xlsx files

Before rewriting, the original xlsx is copied to data/backup/<paper>/ (never
overwritten if a backup already exists). Every change is logged in
../output/gt_date_repairs.csv (paper, sheet cell, trait, species, old, new, rule).
"""

from __future__ import annotations

import csv
import re
import shutil
import sys
from pathlib import Path

import openpyxl

from mineru_extract import classify_folder

ROOT = Path(__file__).resolve().parent.parent
PAPERS = ROOT / "data" / "un_processed_papers"
BACKUP = ROOT / "data" / "backup"
LOG = ROOT / "output" / "gt_date_repairs.csv"

_RESTORED_DATE = re.compile(r"^([1-9]|1[0-2])\.0([1-9])$")


def _in_text(x: str, text: str) -> bool:
    return re.search(rf"(?<![\d.]){re.escape(x)}(?![\d])", text) is not None


def _species_windows(species: str, text: str) -> str:
    """The text of every table row / line where this species is named: from the
    name to the end of its <tr> (or 600 chars). Accepts 'Genus epithet',
    'G. epithet' and 'Genus_epithet'. Empty if the species is never named."""
    words = re.findall(r"[A-Za-z]+", str(species or ""))
    if len(words) < 2:
        return ""
    g, e = re.escape(words[0]), re.escape(words[1])
    pat = re.compile(rf"(?:{g}|{g[0]}\.)[\s_]*{e}\b", re.I)
    out = []
    for m in pat.finditer(text):
        # only a name INSIDE a table cell counts — a mention in prose followed
        # by some unrelated number is not evidence (Scalercio2020)
        if text.rfind("<td", 0, m.start()) <= text.rfind("</td>", 0, m.start()):
            continue
        end = text.find("</tr>", m.end())
        if end == -1 or end - m.end() > 5000:
            continue
        out.append(text[m.end():end])
    return "\n".join(out)


def repaired_value(v: str, text: str, species: str = ""):
    """(new_value, rule) or (None, None). The candidate original must occur in
    THIS species' own row — a number merely present somewhere in the paper is
    not evidence (Scalercio2020's '10.2' sat in another species' row)."""
    m = _RESTORED_DATE.match(v)
    if not m or _in_text(v, text):
        return None, None
    local = _species_windows(species, text)
    if not local:
        return None, None
    month, day = m.group(1), m.group(2)
    for cand, rule in ((f"{month}.{day}", "zero-padded day"),
                       (f"{day}.{int(month):02d}", "swapped day/month"),
                       (f"{day}.{month}", "swapped day/month")):
        if cand != v and _in_text(cand, local):
            return cand, rule
    return None, None


def _verbatim_traits(wb, text, min_share=0.8, min_n=3):
    """{(sheet, measurementType)} whose UNDAMAGED values are copied verbatim from
    the paper: >= min_share of them occur in their own species' table row. Only
    then is a candidate original found in that row real evidence; in a wide row
    of precise numbers ('9.7362 6.8558 …', Raine2018) whose values the volunteer
    rounded, a short '6.8' turning up is chance."""
    ok = set()
    for ws in wb.worksheets:
        hdr = [str(c.value).strip() if c.value is not None else "" for c in ws[1]]
        vcols = [i for i, h in enumerate(hdr) if h.startswith("measurementValue")]
        if not vcols or "measurementType" not in hdr or "verbatimIdentification" not in hdr:
            continue
        ti, si = hdr.index("measurementType"), hdr.index("verbatimIdentification")
        seen, found, windows = {}, {}, {}
        for row in ws.iter_rows(min_row=2, values_only=True):
            trait, sp = row[ti], row[si]
            for vi in vcols:
                val = row[vi] if vi < len(row) else None
                if val is None or trait is None:
                    continue
                v = f"{val:.2f}" if isinstance(val, float) else str(val).strip()
                if not v or _RESTORED_DATE.match(v):
                    continue                     # judge only undamaged values
                if sp not in windows:
                    windows[sp] = _species_windows(sp, text)
                seen[trait] = seen.get(trait, 0) + 1
                found[trait] = found.get(trait, 0) + bool(windows[sp] and _in_text(v, windows[sp]))
        for trait, n in seen.items():
            if n >= min_n and found.get(trait, 0) / n >= min_share:
                ok.add((ws.title, trait))
    return ok


def repair_paper(folder: Path, apply: bool):
    _, gt, _ = classify_folder(folder)
    if not gt:
        return []
    full = folder / f"{folder.name}_full.md"
    if not full.exists():
        return []
    text = full.read_text(encoding="utf-8", errors="replace")
    wb = openpyxl.load_workbook(gt)
    changes = []
    trusted = _verbatim_traits(wb, text)
    for ws in wb.worksheets:
        hdr = [str(c.value).strip() if c.value is not None else "" for c in ws[1]]
        vcols = [i for i, h in enumerate(hdr) if h.startswith("measurementValue")]
        if not vcols:
            continue
        ti = hdr.index("measurementType") if "measurementType" in hdr else None
        si = hdr.index("verbatimIdentification") if "verbatimIdentification" in hdr else None
        for row in ws.iter_rows(min_row=2):
            for vi in vcols:
                cell = row[vi]
                if cell.value is None or isinstance(cell.value, bool):
                    continue
                v = f"{cell.value:.2f}" if isinstance(cell.value, float) else str(cell.value).strip()
                sp = row[si].value if si is not None else ""
                trait = row[ti].value if ti is not None else ""
                if (ws.title, trait) not in trusted:
                    continue
                new, rule = repaired_value(v, text, sp)
                if not new:
                    continue
                changes.append({
                    "paper": folder.name, "file": Path(gt).name, "cell": f"{ws.title}!{cell.coordinate}",
                    "measurementType": row[ti].value if ti is not None else "",
                    "species": row[si].value if si is not None else "",
                    "old": v, "new": new, "rule": rule})
                if apply:
                    # keep a number a number; text stays text
                    cell.value = float(new) if isinstance(cell.value, (int, float)) else new
                    if isinstance(cell.value, float):
                        cell.number_format = "General"
    if changes and apply:
        dest = BACKUP / folder.name / Path(gt).name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            shutil.copy2(gt, dest)
        wb.save(gt)
    return changes


def main(argv):
    apply = "--apply" in argv
    names = [a for a in argv if not a.startswith("--")]
    folders = [PAPERS / n for n in names] if names else \
        sorted(p for p in PAPERS.iterdir() if p.is_dir())
    allc = []
    for f in folders:
        try:
            c = repair_paper(f, apply)
        except Exception as e:
            print(f"skip {f.name}: {e}")
            continue
        if c:
            print(f"{f.name:<22} {len(c):>4} value(s) {'repaired' if apply else 'to repair'}")
            allc += c
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["paper", "file", "cell", "measurementType",
                                           "species", "old", "new", "rule"])
        w.writeheader()
        w.writerows(allc)
    print(f"\n{len(allc)} value(s) in {len({c['paper'] for c in allc})} paper(s) "
          f"{'repaired' if apply else '(dry run)'} -> {LOG}")


if __name__ == "__main__":
    main(sys.argv[1:])
