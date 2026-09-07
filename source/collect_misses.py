"""
collect_misses.py — gather every per-paper <stem>_misses_summary.json produced by
evaluate.py into ONE combined JSON.

Each paper's evaluation writes output/<paper>/<paper>_misses_summary.json with:
    total_missed, causes, value_substitutions, species_absent, traits_missing
(see evaluate.write_miss_detail). This walks the output tree, loads every one it
finds, and writes a single file:

    {
      "papers":   { "<paper>": <that paper's summary, verbatim>, ... },
      "aggregate": { cross-paper roll-up (see below) },
      "_meta":    { which files were read, which failed to parse }
    }

The aggregate sums causes across papers and merges the ranked lists
(traits_missing, species_absent, value_substitutions) so the most frequent
problems ACROSS the whole corpus surface at the top — the thing you actually want
when deciding what to fix first.

Usage:
    python collect_misses.py                          # reads ../output, writes ../output/all_misses.json
    python collect_misses.py --root output            # different output root
    python collect_misses.py --out combined.json      # different destination
    python collect_misses.py --root output --top 40   # keep top-N in each aggregate list
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

SUFFIX = "_misses_summary.json"


def paper_name(path: Path) -> str:
    """Name the paper this file belongs to. Prefer the containing folder (the
    pipeline puts each paper in output/<paper>/); fall back to the filename stem
    with the suffix stripped, for flat layouts."""
    stem = path.name[: -len(SUFFIX)] if path.name.endswith(SUFFIX) else path.stem
    parent = path.parent.name
    return parent or stem or path.stem


def find_summaries(root: Path) -> list[Path]:
    """Every *_misses_summary.json under root, sorted for stable output."""
    return sorted(root.rglob(f"*{SUFFIX}"))


def build_aggregate(papers: dict, top: int | None) -> dict:
    """Roll the per-paper summaries up into corpus-wide totals.

    - causes / total_missed: simple sums.
    - traits_missing, species_absent, value_substitutions: merge each ranked list
      by summing counts for the same key across papers, then re-rank. Each entry
      also records `in_papers` (how many papers hit it) — a trait missed once in
      many papers is a systemic gap, not a one-off.
    """
    total_missed = 0
    causes = Counter()

    trait_count = Counter()
    trait_papers = defaultdict(set)

    species_count = Counter()
    species_papers = defaultdict(set)
    species_closest = {}                      # keep one closest-name example

    subs_count = Counter()                    # (gt, pred) -> count
    subs_papers = defaultdict(set)

    for name, s in papers.items():
        total_missed += int(s.get("total_missed", 0) or 0)
        for cause, c in (s.get("causes") or {}).items():
            causes[cause] += int(c or 0)

        for t in s.get("traits_missing") or []:
            key = t.get("measurementType", "")
            trait_count[key] += int(t.get("count", 0) or 0)
            trait_papers[key].add(name)

        for sp in s.get("species_absent") or []:
            key = sp.get("gt_species", "")
            species_count[key] += int(sp.get("count", 0) or 0)
            species_papers[key].add(name)
            if key not in species_closest and sp.get("closest_pred_species"):
                species_closest[key] = {
                    "closest_pred_species": sp.get("closest_pred_species", ""),
                    "closest_score": sp.get("closest_score", 0.0),
                }

        for v in s.get("value_substitutions") or []:
            key = (v.get("gt", ""), v.get("pred", ""))
            subs_count[key] += int(v.get("count", 0) or 0)
            subs_papers[key].add(name)

    def cap(seq):
        return seq[:top] if top else seq

    traits = cap([
        {"measurementType": k, "count": c, "in_papers": len(trait_papers[k])}
        for k, c in trait_count.most_common()
    ])
    species = cap([
        {"gt_species": k, "count": c, "in_papers": len(species_papers[k]),
         **species_closest.get(k, {})}
        for k, c in species_count.most_common()
    ])
    subs = cap([
        {"gt": g, "pred": p, "count": c, "in_papers": len(subs_papers[(g, p)])}
        for (g, p), c in subs_count.most_common()
    ])

    return {
        "papers_with_misses": len(papers),
        "total_missed": total_missed,
        "causes": dict(causes.most_common()),
        "traits_missing": traits,
        "species_absent": species,
        "value_substitutions": subs,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default="../output",
                    help="output root to scan (default: ../output)")
    ap.add_argument("--out", default=None,
                    help="destination JSON (default: <root>/all_misses.json)")
    ap.add_argument("--top", type=int, default=None,
                    help="keep only the top-N entries in each aggregate list "
                         "(default: keep all)")
    args = ap.parse_args()

    root = Path(args.root)
    if not root.is_dir():
        raise SystemExit(f"output root not found: {root}")

    files = find_summaries(root)
    if not files:
        raise SystemExit(f"no *{SUFFIX} files found under {root} "
                         f"(did evaluation run? the pipeline writes these only "
                         f"when scored against a results xlsx)")

    papers: dict = {}
    read, failed = [], []
    for f in files:
        name = paper_name(f)
        try:
            papers[name] = json.loads(f.read_text(encoding="utf-8"))
            read.append(str(f))
        except Exception as e:
            failed.append({"file": str(f), "error": f"{type(e).__name__}: {e}"})

    combined = {
        "papers": papers,
        "aggregate": build_aggregate(papers, args.top),
        "_meta": {
            "root": str(root),
            "files_read": len(read),
            "files_failed": failed,
        },
    }

    out = Path(args.out) if args.out else root / "all_misses.json"
    out.write_text(json.dumps(combined, indent=2, ensure_ascii=False),
                   encoding="utf-8")

    agg = combined["aggregate"]
    print(f"read {len(read)} miss summary file(s) from {root}")
    if failed:
        print(f"  {len(failed)} file(s) failed to parse (see _meta.files_failed)")
    print(f"papers with misses : {agg['papers_with_misses']}")
    print(f"total missed rows  : {agg['total_missed']}")
    if agg["causes"]:
        print("causes (corpus-wide):")
        for cause, c in agg["causes"].items():
            print(f"  {c:>6}  {cause}")
    if agg["traits_missing"]:
        print("top missing traits:")
        for t in agg["traits_missing"][:10]:
            print(f"  {t['count']:>5}  ({t['in_papers']} paper(s))  {t['measurementType']}")
    print(f"\nwritten -> {out}")


if __name__ == "__main__":
    main()
