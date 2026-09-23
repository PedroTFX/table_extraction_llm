"""gt_from_test.py — adapt the *other team's* test ground truth into the
canonical template columns our evaluator (evaluate.py) understands.

The test papers under data/test/{imagePDF,newPDF,ocrPDF}/ ship a `<name>_gt.json`
(and a parallel `<name>.xlsx`) in a DIFFERENT schema than our Darwin-Core-style
template. This module converts one `_gt.json` into a template-column .xlsx so the
existing `evaluate()` can score our pipeline's CSV against it — no change to the
evaluator itself.

Their _gt.json shape:
    [ { "species_name": str,
        "traits": [ { "name": str,        # trait code, e.g. "bole"
                      "caste": str,        # female | male  (this is SEX for spiders)
                      "stage": str,        # e.g. adult
                      "country": str,      # ISO code, e.g. KEN
                      "value": number,
                      "measure": str } ]  # e.g. obs (single observation)
      }, ... ]

Mapping to our template (evaluate.COLUMNS), keyed for scoring on
[verbatimIdentification, measurementType, measurementValue]:
    species_name -> verbatimIdentification
    trait.name   -> measurementType        (the code as it appears in the paper)
    trait.value  -> measurementValue
    trait.caste  -> sex                     (spiders: female/male IS the sex)
    trait.stage  -> lifeStage
    trait.country-> verbatimLocality
    (basisOfRecord defaults to PreservedSpecimen, matching how these morphology
     traits are recorded; other tag columns left blank — they are not the headline
     'core' score and the two schemas don't carry them comparably.)
"""

from __future__ import annotations

import json
from pathlib import Path

import openpyxl

# Keep in lockstep with evaluate.COLUMNS (clean names; evaluate normalizes headers).
TEMPLATE_COLUMNS = [
    "basisOfRecord", "verbatimIdentification", "measurementType",
    "measurementMethod", "measurementValue", "measurementUnit",
    "measurementStatistic", "measurementRemarks", "sex", "lifeStage",
    "caste", "sampleSizeValue", "sampleSizeUnit", "sampleTreatment",
    "samplingProtocol", "verbatimLocality", "verbatimCoordinates",
    "verbatimEventDate", "associatedOccurrences", "associatedReferences",
    "externalLink",
]


def gt_json_to_rows(gt_json_path):
    """Read one test `_gt.json` and yield template-column dict rows."""
    data = json.loads(Path(gt_json_path).read_text(encoding="utf-8"))
    rows = []
    for entry in data:
        species = (entry.get("species_name") or "").strip()
        for tr in entry.get("traits", []):
            row = {c: None for c in TEMPLATE_COLUMNS}
            row["basisOfRecord"] = "PreservedSpecimen"
            row["verbatimIdentification"] = species
            row["measurementType"] = (tr.get("name") or "").strip()
            row["measurementValue"] = tr.get("value")
            row["sex"] = (tr.get("caste") or "").strip() or None
            row["lifeStage"] = (tr.get("stage") or "").strip() or None
            row["verbatimLocality"] = (tr.get("country") or "").strip() or None
            row["measurementRemarks"] = (tr.get("measure") or "").strip() or None
            rows.append(row)
    return rows


def write_template_xlsx(gt_json_path, out_xlsx_path):
    """Convert `<name>_gt.json` -> a template-column .xlsx at out_xlsx_path.

    Returns the number of GT rows written."""
    rows = gt_json_to_rows(gt_json_path)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Folha1"                      # same sheet name our GT xlsx use
    ws.append(TEMPLATE_COLUMNS)
    for r in rows:
        ws.append([r[c] for c in TEMPLATE_COLUMNS])
    Path(out_xlsx_path).parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_xlsx_path)
    return len(rows)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        raise SystemExit("usage: python gt_from_test.py <name_gt.json> <out.xlsx>")
    n = write_template_xlsx(sys.argv[1], sys.argv[2])
    print(f"wrote {n} GT rows -> {sys.argv[2]}")
