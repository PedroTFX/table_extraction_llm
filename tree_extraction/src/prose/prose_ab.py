"""prose_ab.py — the prose route's rows with the old examples (t2o) against the made-up ones (t2n), side by side.

Both variants are t2 run afresh in one session (run_variant_papers.sh t2o ..., then t2n ...). Per paper: the rows each
gives, the rows only one gives (species | trait | value | source), to be read against the paper's text: for prose the
rows are judged by reading, not by the scorer's F1 (the user, 2026-11-03).

    python prose_ab.py [papers]     (default: the prose tuning papers) -> output/prose_ab/COMPARE.txt
"""
import collections
import csv
import json
import os
import sys

import _paths

OUT = _paths.OUTPUT / "prose_ab"
SET = _paths.SUB / "output" / "eval_split" / "prose_set.json"
A, B = "t2o", os.environ.get("PROSE_AB_B", "t2n")     # PROSE_AB_B=t2i: the insect revision -> COMPARE_t2i.txt


def rows(variant, p):
    f = _paths.OUTPUT / f"prose_{variant}" / "prose" / p / f"{p}.csv"
    if not f.exists():
        return None
    with open(f, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def key(r):
    return (r.get("verbatimIdentification", ""), r.get("measurementType", ""), r.get("measurementValue", ""),
            r.get("sex", "") or "")


def main(argv):
    s = json.loads(SET.read_text(encoding="utf-8"))["109"]
    papers = argv or s["dev"] + s["held_a"]
    L = [f"Prose rows: {A} (the old examples) against {B} (made-up examples), t2 both, run afresh.", ""]
    for p in papers:
        ra, rb = rows(A, p), rows(B, p)
        if ra is None or rb is None:
            L.append(f"== {p}: not run ({A}: {ra is not None}, {B}: {rb is not None})")
            continue
        ca, cb = collections.Counter(map(key, ra)), collections.Counter(map(key, rb))
        only_a, only_b = ca - cb, cb - ca
        src = {key(r): (r.get("measurementRemarks") or "")[:90] for r in ra + rb}
        L.append(f"== {p}: {A} {len(ra)} rows, {B} {len(rb)} rows; the same {sum((ca & cb).values())}, "
                 f"only {A} {sum(only_a.values())}, only {B} {sum(only_b.values())}")
        per = collections.Counter(k[0] for k in ca), collections.Counter(k[0] for k in cb)
        for sp in sorted(set(per[0]) | set(per[1])):
            if per[0][sp] != per[1][sp]:
                L.append(f"   species {sp or '(none)'}: {per[0][sp]} -> {per[1][sp]} rows")
        for tag, only in ((A, only_a), (B, only_b)):
            L.append(f"  only in {tag}:")
            for k, n in sorted(only.items()):
                L.append(f"    {k[0][:28]:28s} | {k[1][:40]:40s} | {k[2][:40]:40s} | {k[3][:6]:6s}"
                         f"{' x' + str(n) if n > 1 else ''}  [{src.get(k, '')}]")
        L.append("")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / ("COMPARE.txt" if B == "t2n" else f"COMPARE_{B}.txt")).write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:2] + [x for x in L if x.startswith("==") or x.startswith("   species")]))


if __name__ == "__main__":
    main(sys.argv[1:])
