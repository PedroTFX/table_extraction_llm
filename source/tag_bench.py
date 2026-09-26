"""
tag_bench.py — score ONLY the column-tag step (basisOfRecord, measurementMethod,
measurementUnit, measurementStatistic) against the ground truth, without running
the whole pipeline (~8 min/paper). One tag call per ground-truth measurementType,
using the same prose chunks and the same get_measurement_level_tags the pipeline
uses, then the same output-time normalisation/defaults as to_output.

    python tag_bench.py                    # default sample of papers
    python tag_bench.py Barber2017 Beyer2021
    python tag_bench.py --n 30 --traits 4  # sample size / traits per paper

Prints per-field accuracy (all traits pooled, and averaged per paper) and writes
../output/tag_bench.json with every decision for inspection.
"""

from __future__ import annotations

import collections
import json
import random
import sys
from pathlib import Path

import openpyxl

from evaluate import OPTIONAL_GT_FIELDS, normalize_value
from fill_template import get_measurement_level_tags
from mineru_extract import classify_folder
from run_pipeline import prose_chunks
from to_output import _looks_numeric_value, default_tag, is_empty_like, normalize_basis_out

PAPERS = Path(__file__).resolve().parent.parent / "data" / "un_processed_papers"
OUT = Path(__file__).resolve().parent.parent / "output" / "tag_bench.json"
FIELDS = ["basisOfRecord", "measurementMethod", "measurementUnit", "measurementStatistic"]
SHORT = {"basisOfRecord": "basis", "measurementMethod": "method",
         "measurementUnit": "unit", "measurementStatistic": "stat"}


def gt_traits(gt_path):
    """measurementType -> majority GT value per tag + whether values are numeric."""
    ws = openpyxl.load_workbook(gt_path, read_only=True, data_only=True).active
    rows = list(ws.iter_rows(values_only=True))
    hdr = [str(h).strip() if h else "" for h in rows[0]]
    per = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    for r in rows[1:]:
        d = {h: ("" if v is None else str(v).strip()) for h, v in zip(hdr, r)}
        mt = d.get("measurementType", "")
        if not mt or not d.get("verbatimIdentification"):
            continue
        for f in FIELDS:
            per[mt][f][d.get(f, "")] += 1
        val = next((d[k] for k in d if k.startswith("measurementValue")), "")
        per[mt]["_numeric"][_looks_numeric_value(val)] += 1
        per[mt]["_value"][val] += 1
    return {mt: {f: c.most_common(1)[0][0] for f, c in fs.items()} for mt, fs in per.items()}


def predict(mt, numeric, value, chunks):
    """Run the pipeline's tag step for one column, then to_output's fix-ups.
    `value` (a typical GT value) stands in for the value the pipeline extracts,
    which the value-aware defaults look at."""
    mapping = {mt: {"field": "measurementType", "category": "trait",
                    "value_type": "numeric" if numeric else "categorical"}}
    get_measurement_level_tags(mapping, chunks, allowed_tags=set(FIELDS))
    m = mapping[mt]
    row = {f: ("" if is_empty_like(m.get(f)) else str(m.get(f))) for f in FIELDS}
    row["basisOfRecord"] = normalize_basis_out(row["basisOfRecord"])
    for f in ("basisOfRecord", "measurementStatistic"):
        if not row[f]:
            row[f] = default_tag(f, value)
    return row, {f: m.get(f"{f}_reasoning") for f in FIELDS}


def main(argv):
    n = int(argv[argv.index("--n") + 1]) if "--n" in argv else 20
    max_traits = int(argv[argv.index("--traits") + 1]) if "--traits" in argv else 3
    names = [a for a in argv if not a.startswith("--") and not a.isdigit()]
    folders = [PAPERS / p for p in names] if names else \
        random.Random(0).sample(sorted(p for p in PAPERS.iterdir() if p.is_dir()), n)

    results, pooled, per_paper = [], collections.defaultdict(list), collections.defaultdict(list)
    extras = collections.defaultdict(list)
    for folder in folders:
        full = folder / f"{folder.name}_full.md"
        try:
            _, gt, _ = classify_folder(folder)
            traits = gt_traits(gt)
        except Exception as e:
            print(f"skip {folder.name}: {e}")
            continue
        if not full.exists() or not traits:
            continue
        chunks = prose_chunks([full])
        hits = collections.defaultdict(list)
        for mt in list(traits)[:max_traits]:
            g = traits[mt]
            numeric = bool(g.get("_numeric"))
            pred, why = predict(mt, numeric, g.get("_value", ""), chunks)
            rec = {"paper": folder.name, "measurementType": mt, "numeric": numeric}
            for f in FIELDS:
                gv, pv = normalize_value(g.get(f, "")), normalize_value(pred[f])
                if gv == "" and f in OPTIONAL_GT_FIELDS:
                    ok = None                       # GT skipped it: not scored
                    extras[f].append(pv != "")      # found anyway = bonus
                else:
                    ok = gv == pv
                    hits[f].append(ok)
                    pooled[f].append(ok)
                rec[f] = {"gt": g.get(f, ""), "pred": pred[f], "ok": ok, "why": why[f]}
            results.append(rec)
            flags = " ".join(f"{SHORT[f]}={'-' if rec[f]['ok'] is None else 'ok' if rec[f]['ok'] else 'X'}"
                             for f in FIELDS)
            print(f"  {folder.name:<22} {mt[:30]:<30} {flags}")
        for f in FIELDS:
            if hits[f]:
                per_paper[f].append(sum(hits[f]) / len(hits[f]))

    print(f"\n{len(per_paper[FIELDS[0]])} paper(s), {len(pooled[FIELDS[0]])} trait(s)")
    print(f"  {'field':<22} {'pooled':>7} {'per-paper':>10} {'scored':>7}   extra finds")
    for f in FIELDS:
        pp, po = per_paper[f], pooled[f]
        acc = f"{sum(po) / len(po):>7.3f} {sum(pp) / len(pp):>10.3f}" if po else f"{'n/a':>7} {'n/a':>10}"
        ex = f"   {sum(extras[f])}/{len(extras[f])} found where GT blank" if extras[f] else ""
        print(f"  {f:<22} {acc} {len(po):>7}{ex}")
    OUT.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"-> {OUT}")


if __name__ == "__main__":
    main(sys.argv[1:])
