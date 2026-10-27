"""
gt_value_audit.py — find ground-truth rows whose VALUES do not fit the tag they
were recorded under (read-only; nothing in the GT is changed).

The trigger: OsorioCanadas2018 and Korosi2022 record life stages (Prepupa,
Larva, Adult, Egg) as a measurementType ('Wintering stage', 'Overwintering
stage') with lifeStage = 'all'. This script looks for that pattern in every GT:

  1. a measurementType whose values belong to another field's vocabulary
     (lifeStage, sex, caste, measurementStatistic, units, taxon names, months),
  2. a lifeStage / sex / caste field holding values outside its own vocabulary.

The vocabularies follow template_descriptions/<field>.md. A hit is a CANDIDATE:
a species trait can legitimately take stage-like or month-like values (the
current measurementType.md says "Overwintering stage" is a measurementType), so
the report shows the evidence and leaves the verdict to a person.

    python gt_value_audit.py            # -> tree_extraction/output/GT_VALUE_AUDIT.txt
"""

from __future__ import annotations

import collections
import re
import sys
from pathlib import Path

import _paths
from evaluate import load_xlsx

ROOT = _paths.REPO
PAPERS = _paths.PAPERS
OUT = _paths.OUTPUT / "GT_VALUE_AUDIT.txt"
MIN_SHARE = 0.5          # share of a measurementType's values in another vocabulary

VOCAB = {
    # lifeStage.md valid values, plurals/adjectives, and the stages GTs use
    "lifeStage": {"egg", "eggs", "larva", "larvae", "larval", "caterpillar",
                  "caterpillars", "nymph", "nymphs", "nymphal", "instar", "pupa",
                  "pupae", "pupal", "prepupa", "prepupae", "prepupal", "adult",
                  "adults", "imago", "imagines", "immature", "immatures",
                  "inmature", "inamature", "juvenile", "juveniles", "subadult",
                  "teneral", "i", "ii", "iii", "iv", "v", "first", "second",
                  "third", "fourth", "fifth", "1st", "2nd", "3rd", "4th", "5th"},
    # sex.md
    "sex": {"male", "males", "female", "females", "both", "hermaphrodite"},
    # caste.md
    "caste": {"queen", "queens", "king", "kings", "worker", "workers", "soldier",
              "soldiers", "minor", "major", "majors", "minors", "media", "gyne",
              "gynes", "drone", "drones", "alate", "alates", "dealate",
              "reproductive", "reproductives", "male", "female"},
    # measurementStatistic.md
    "measurementStatistic": {"mean", "median", "mode", "min", "max", "minimum",
                             "maximum", "range", "sd", "se", "variance", "ratio",
                             "count", "individual", "quartile"},
    "measurementUnit": {"mm", "cm", "m", "km", "mg", "g", "kg", "µm", "um", "°c",
                        "%", "day", "days", "h", "hours", "years", "year"},
    "month": {"jan", "january", "feb", "february", "mar", "march", "apr", "april",
              "may", "jun", "june", "jul", "july", "aug", "august", "sep", "sept",
              "september", "oct", "october", "nov", "november", "dec", "december"},
}
# filler words that may sit next to vocabulary words ('adult and larva')
FILLER = {"and", "or", "&", "/", "both", "all", "stage", "stages", "the", "in",
          "of", "as", "only", "mostly", "unknown", "na", "-", "to"}
# the column tree's Latin-name test (Latin epithet endings, sp./spp., authority)
from column_tree import _BINOMIAL as BINOMIAL
WORD = re.compile(r"[A-Za-z°µ%]+|\d+(?:st|nd|rd|th)")


def words(v) -> list:
    v = re.sub(r"\[[^\]]*\]|\([^)]*\)", " ", str(v or ""))      # citations, notes
    return [w.lower() for w in WORD.findall(v)]


def in_vocab(v, field) -> bool:
    """Every content word of the value is in the field's vocabulary."""
    ws = [w for w in words(v) if w not in FILLER]
    return bool(ws) and all(w in VOCAB[field] for w in ws)


def looks_taxon(v) -> bool:
    return bool(BINOMIAL.match(str(v or "").strip()))


def audit_paper(paper, rows):
    """-> list of findings for one GT."""
    vcol = next((k for k in rows[0] if k.startswith("measurementValue")), "measurementValue") if rows else ""
    by_type = collections.defaultdict(list)
    for r in rows:
        t = str(r.get("measurementType", "") or "").strip()
        if t:
            by_type[t].append(r)
    found = []
    # 1. measurementType values that belong to another field
    for t, rs in by_type.items():
        vals = [str(r.get(vcol, "") or "").strip() for r in rs]
        vals = [v for v in vals if v]
        if not vals:
            continue
        for field in ("lifeStage", "sex", "caste", "measurementStatistic",
                      "measurementUnit", "month"):
            hits = [v for v in vals if in_vocab(v, field)]
            if len(hits) / len(vals) >= MIN_SHARE:
                same = collections.Counter(str(r.get(field, "") or "").strip()
                                           for r in rs if field in r)
                found.append({"kind": "measurementType holds " + field, "paper": paper,
                              "type": t, "n": len(vals), "share": len(hits) / len(vals),
                              "examples": collections.Counter(hits).most_common(5),
                              "field_in_gt": same.most_common(3)})
                break
        taxa = [v for v in vals if looks_taxon(v)]
        if len(taxa) / len(vals) >= MIN_SHARE:
            found.append({"kind": "measurementType holds taxon names", "paper": paper,
                          "type": t, "n": len(vals), "share": len(taxa) / len(vals),
                          "examples": collections.Counter(taxa).most_common(5),
                          "field_in_gt": []})
    # 2. a row field holding values outside its own vocabulary
    for field in ("lifeStage", "sex", "caste"):
        vals = [str(r.get(field, "") or "").strip() for r in rows]
        bad = collections.Counter(v for v in vals if v and not in_vocab(v, field)
                                  and v.lower() not in {"all", "unknown", "both", "na",
                                                        "null", "none", "-"})
        if bad:
            found.append({"kind": f"{field} holds values outside its vocabulary",
                          "paper": paper, "type": "", "n": sum(bad.values()),
                          "share": sum(bad.values()) / max(1, sum(1 for v in vals if v)),
                          "examples": bad.most_common(5), "field_in_gt": []})
    return found


def find_gt(folder: Path):
    key = folder.name.replace("-", "").lower()
    return next((f for f in folder.iterdir() if f.suffix.lower() == ".xlsx"
                 and f.stem.replace("-", "").lower() == key), None)


def main(argv):
    findings, n_papers = [], 0
    for folder in sorted(p for p in PAPERS.iterdir() if p.is_dir()):
        gt = find_gt(folder)
        if not gt:
            continue
        try:
            rows = load_xlsx(gt)
        except Exception as e:
            print(f"  {folder.name}: unreadable ({type(e).__name__})")
            continue
        n_papers += 1
        findings += audit_paper(folder.name, rows)

    kinds = collections.defaultdict(list)
    for f in findings:
        kinds[f["kind"]].append(f)
    L = [f"GT VALUE AUDIT — {n_papers} ground-truth spreadsheets, "
         f"{len(findings)} candidate(s)",
         "Rows whose values do not fit the tag they were recorded under. CANDIDATES:",
         "a species trait can legitimately take stage-, sex- or month-like values;",
         "the verdict is a person's. 'GT also records' = what the same rows say in",
         "that field (e.g. lifeStage = 'all' next to a 'Wintering stage' of Larva).", ""]
    order = ["measurementType holds lifeStage", "measurementType holds sex",
             "measurementType holds caste", "measurementType holds measurementStatistic",
             "measurementType holds measurementUnit", "measurementType holds taxon names",
             "measurementType holds month", "lifeStage holds values outside its vocabulary",
             "sex holds values outside its vocabulary",
             "caste holds values outside its vocabulary"]
    for kind in order + [k for k in kinds if k not in order]:
        fs = sorted(kinds.get(kind, []), key=lambda f: -f["n"])
        if not fs:
            continue
        L += ["=" * 90, f"{kind.upper()}  ({len(fs)} paper/type pair(s), "
              f"{sum(f['n'] for f in fs)} rows)", "=" * 90]
        for f in fs:
            ex = "; ".join(f"{v} x{c}" for v, c in f["examples"])
            head = f"  {f['paper']}" + (f"  '{f['type']}'" if f["type"] else "")
            L.append(f"{head}  — {f['n']} rows, {f['share']:.0%} match")
            L.append(f"      values: {ex}")
            if f["field_in_gt"]:
                L.append("      GT also records: " + "; ".join(
                    f"{f['kind'].split()[-1]} = {v or '(empty)'} x{c}" for v, c in f["field_in_gt"]))
        L.append("")
    OUT.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[:6]))
    print(f"-> {OUT}")


if __name__ == "__main__":
    main(sys.argv[1:])
