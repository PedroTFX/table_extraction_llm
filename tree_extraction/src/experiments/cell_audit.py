"""
cell_audit.py — AUDIT (read-only, no model): what do the printed cells look like,
and what did the GT curators take from each?

For every GT row of the 30 benchmark papers, find the table cell it came from: a
cell in a row that also names the GT row's species, whose text IS the GT value or
contains it as one of its parts (column_role_bench.parts). Then, per cell:

  pattern   the cell's written shape (number, number ± number, number (number),
            range, number + unit, number + letters, list, words, code ...) —
            a description for counting, it decides nothing
  GT took   the whole cell or a part; which statistic, unit and sample size the
            GT row records next to the value
  splitter  which of the main program's splitters already turns the cell into the
            GT value (to_output.split_value_parts / split_significance /
            split_superscript_group, tables.split_multivalue, column_tree.peel)

    python cell_audit.py
-> tree_extraction/output/CELL_AUDIT.txt
"""

from __future__ import annotations

import collections
import re

import _paths
import column_role_bench as crb
import column_tree as ct
import header_tree as ht
import header_tree_bench as hb
from evaluate import load_xlsx
from tables import split_multivalue
from to_output import split_significance, split_superscript_group, split_value_parts

NUM = r"[<>~≈]?-?\d+(?:[.,]\d+)?"
UNIT = r"(?:[µμu]m|mm|cm|km|m|mg|µg|g|kg|ml|µl|°C|ºC|%|days?|d|h|hrs?|min|s|yrs?|years?)"
PATTERNS = [  # (name, regex on the stripped cell), first match wins
    ("number", rf"^{NUM}$"),
    ("number ± number", rf"^{NUM}\s*(?:±|\+/-|\+-)\s*{NUM}$"),
    ("number ± number (n)", rf"^{NUM}\s*(?:±|\+/-|\+-)\s*{NUM}\s*\(\s*(?:n\s*=\s*)?\d+\s*\)$"),
    ("number ± number + letters", rf"^{NUM}\s*(?:±|\+/-|\+-)\s*{NUM}\s*[a-h]{{1,4}}(?:\s*\(\s*\d+\s*\))?$"),
    ("number^mark ± number", rf"^{NUM}\^\S+\s*(?:±|\+/-|\+-)\s*{NUM}$"),
    ("number (number)", rf"^{NUM}\s*\(\s*{NUM}\s*\)$"),
    ("number (range)", rf"^{NUM}\s*\(\s*{NUM}\s*[-–—]\s*{NUM}\s*\)$"),
    ("range a–b", rf"^{NUM}\s*[-–—~]\s*{NUM}$"),
    ("number + unit", rf"^{NUM}(?:\s*[-–—]\s*{NUM})?\s*{UNIT}$"),
    ("number + letters", rf"^{NUM}\s*[a-h]{{1,4}}$"),
    ("number + mark", rf"^{NUM}\s*(?:\^\S+|\*+|[†‡§¶]+)$"),
    ("number (n = k)", rf"^{NUM}.*\(\s*n\s*=\s*\d+\s*\)$"),
    ("ratio a/b", rf"^{NUM}\s*/\s*{NUM}$"),
    ("number + citation", rf"^{NUM}\s*(?:\[\d+(?:[,–-]\d+)*\]|\(\d+(?:,\s*\d+)*\))$"),
    ("list of codes", r"^[A-Za-z]{1,4}(?:\s*[,/;]\s*[A-Za-z]{1,4})+$"),
    ("code", r"^[A-Za-z]{1,3}\d?$"),
    ("list of words", r"^[A-Za-z][\w\s-]*(?:\s*[,;/]\s*[A-Za-z][\w\s-]*)+$"),
    ("words", r"^[A-Za-z][A-Za-z\s.'-]*$"),
    ("words + citation", r"^[A-Za-z].*(?:\[\d+\]|\^\S+|[†‡§¶*]+)$"),
]


def pattern(cell):
    c = " ".join(str(cell or "").split())
    for name, rx in PATTERNS:
        if re.match(rx, c):
            return name
    return "other: " + ("mixed text and numbers" if re.search(r"\d", c) else "text")


def splitters(cell, gt_value):
    """Which existing splitters turn the cell into the GT value (normalised)."""
    want = crb.norm(gt_value)
    out = []
    if crb.norm(cell) == want:
        return ["as is"]
    core, _parts = split_value_parts(cell)
    if crb.norm(core) == want:
        out.append("split_value_parts")
    v, _g, _n = split_significance(cell)
    if crb.norm(v) == want and v != cell:
        out.append("split_significance")
    s = split_superscript_group(cell)
    if s and crb.norm(s[0]) == want:
        out.append("split_superscript_group")
    core, _peeled = ct.peel(cell)
    if crb.norm(core) == want:
        out.append("peel")
    try:
        items = split_multivalue(cell)
    except Exception:
        items = []
    if len(items) > 1 and want in {crb.norm(i) for i in items}:
        out.append("split_multivalue")
    return out or ["none"]


def audit():
    found = []                                   # one per (paper, table, row, col, GT row)
    missing = collections.Counter()
    for paper in hb.default_papers():
        gp = crb.paper_inputs(_paths.PAPERS / paper)
        if not gp:
            continue
        rows = load_xlsx(gp[1])
        gt = crb.GroundTruth(rows)
        index = collections.defaultdict(list)    # (species id, part) -> [(table, r, c, cell)]
        for k, table_html in enumerate(hb.html_tables(paper)):
            g = ht.grid_from_html(table_html)
            for r in range(g.nrows):
                cells = [(c, g.at(r, c)) for c in range(g.ncols)]
                texts = [(c, " ".join(str(x.text or "").split())) for c, x in cells if x]
                ids = {gt.match_id(t) for _c, t in texts} - {None}
                if not ids and len(gt.ids) == 1:
                    ids = {gt.ids[0]}           # single-species paper
                for c, t in texts:
                    if not t:
                        continue
                    keys = {crb.norm(t), *crb.parts(t)}
                    for rid in ids:
                        for p in keys:
                            index[(rid, p)].append((k, r, c, t))
        seen = set()
        for row in rows:
            rid = gt.match_id(str(row.get("verbatimIdentification", "")))
            v = crb.norm(row.get("measurementValue"))
            if not v:
                continue
            hits = index.get((rid, v)) or []
            if not hits:
                missing[paper] += 1
                continue
            k, r, c, cell = hits[0]
            key = (paper, k, r, c, row.get("measurementType"), v)
            if key in seen:
                continue
            seen.add(key)
            found.append({"paper": paper, "table": k, "cell": cell, "value": str(row.get("measurementValue")),
                          "type": str(row.get("measurementType") or ""),
                          "statistic": str(row.get("measurementStatistic") or "").strip(),
                          "unit": str(row.get("measurementUnit") or "").strip(),
                          "n": str(row.get("sampleSizeValue") or "").strip(),
                          "pattern": pattern(cell), "whole": crb.norm(cell) == v,
                          "splitters": splitters(cell, row.get("measurementValue"))})
    return found, missing


def report(found, missing):
    pct = lambda a, b: f"{a / b:.0%}" if b else "-"
    by = collections.defaultdict(list)
    for f in found:
        by[f["pattern"]].append(f)
    total = len(found)
    L = [f"GT values traced to a table cell: {total}  (not found in any table cell: "
         f"{sum(missing.values())})", "",
         f"{'cell pattern':28s}{'cells':>7s}{'share':>7s}{'GT=whole':>9s}{'handled':>9s}  "
         f"GT statistic (top)            unit / n recorded",
         "-" * 118]
    for name, fs in sorted(by.items(), key=lambda kv: -len(kv[1])):
        n = len(fs)
        whole = sum(f["whole"] for f in fs)
        handled = sum(f["splitters"] != ["none"] for f in fs)
        stats = collections.Counter(f["statistic"] or "-" for f in fs).most_common(3)
        unit = sum(bool(f["unit"]) for f in fs)
        nn = sum(bool(f["n"]) for f in fs)
        L.append(f"{name:28s}{n:>7d}{pct(n, total):>7s}{pct(whole, n):>9s}{pct(handled, n):>9s}  "
                 f"{', '.join(f'{s} {c}' for s, c in stats):30s} unit {pct(unit, n)} · n {pct(nn, n)}")
    L += ["", "GT=whole: the GT value is the whole printed cell.  handled: an existing splitter",
          "(or no split at all) turns the cell into exactly the GT value.", ""]
    L.append("which splitter does the work, per pattern (cells where the GT took a PART of the cell):")
    for name, fs in sorted(by.items(), key=lambda kv: -len(kv[1])):
        part = [f for f in fs if not f["whole"]]
        if not part:
            continue
        sp = collections.Counter(s for f in part for s in f["splitters"])
        L.append(f"  {name:28s} {len(part):>5d} cells: " + ", ".join(f"{s} {c}" for s, c in sp.most_common()))
    L += ["", "examples per pattern (cell -> GT value | statistic | unit | n), up to 4 from different papers:"]
    for name, fs in sorted(by.items(), key=lambda kv: -len(kv[1])):
        L.append(f"  {name}:")
        shown, papers = 0, set()
        for f in sorted(fs, key=lambda f: f["whole"]):
            if f["paper"] in papers:
                continue
            papers.add(f["paper"])
            L.append(f"    {f['paper']}: '{f['cell'][:50]}' -> '{f['value'][:30]}' | {f['statistic'] or '-'}"
                     f" | {f['unit'] or '-'} | {f['n'] or '-'}  [{', '.join(f['splitters'])}]")
            shown += 1
            if shown == 4:
                break
    L += ["", "not handled by any splitter (the GT value is a part no splitter gives), by pattern:"]
    nh = collections.Counter(f["pattern"] for f in found if f["splitters"] == ["none"])
    L += [f"  {p:28s}{c}" for p, c in nh.most_common()]
    L += ["", "GT values not found in any table cell, per paper (text, legends decoded, other files):"]
    L += [f"  {p:22s}{c}" for p, c in missing.most_common()]
    return "\n".join(L)


def main():
    found, missing = audit()
    text = report(found, missing)
    out = _paths.OUTPUT / "CELL_AUDIT.txt"
    out.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
