"""Jakub's papers: folders, and their GT (World Spider Trait database rows) written in our template.

The set comes as three flat folders (newPDF, imagePDF, ocrPDF), each paper as three files with one
stem: <stem>.pdf, <stem>.xlsx (the database's export) and <stem>_gt.json (the same rows as JSON).
Stems: n / im / oc (new, image, OCR PDF) + a number + the paper's language (en, ru, fr, chi, de ...).

  group      every <stem>.pdf with its <stem>.xlsx into <set>/<stem>/ (the stem as the PDF spells it:
             'im2-FR.pdf' with 'im2-fr.xlsx' -> im2-FR/im2-FR.xlsx); the JSONs stay outside the folders,
             so MinerU and the pipeline never read them. A stem without a PDF stays as it is.
  translate  each folder's database export is moved out of the folder (<set>/<stem>_wst.xlsx, beside
             the JSON) and the folder gets <stem>.xlsx in our template, so the pipeline, the scorer and
             score_two_step read it as they read every other GT. Run again: the export is read from
             <stem>_wst.xlsx, so the translation can be redone.

The export's own trait_name is empty: the names are the database's (arachnidatraits.sci.muni.cz, trait
list read 2026-11-08). Leg segment codes renamed there since the export (fem1 -> feL1 'Femur I length',
tib1 -> tiL1, pat1 -> paL1, met1 -> mtL1, tar1 -> taL1, femp -> feLp, tibp -> tiLp) take the renamed
entries' names.

Column map (export -> template); the export's other columns are not in our template or are empty:
  original_name -> verbatimIdentification     trait_abbrev -> measurementType (the database's name)
  value -> measurementValue                    measure -> measurementStatistic
  sex -> sex          life_stage -> lifeStage  sample_size -> sampleSizeValue
  treatment -> sampleTreatment                 note -> measurementRemarks
  locality -> verbatimLocality                 reference -> associatedReferences
Statistic: 'single observation' -> individual; min, max, mean as they are. A range is two rows (min and
max), as the database stores it; our GTs write one 'range' row in 17 papers and min / max rows in 7.

    python wst_gt.py group <set dir> ...
    python wst_gt.py translate <set dir> ...
"""
import shutil
import sys
from pathlib import Path

import openpyxl

TEMPLATE = ["basisOfRecord", "verbatimIdentification", "measurementType", "measurementMethod",
            "measurementValue", "measurementUnit", "measurementStatistic", "measurementRemarks", "sex",
            "lifeStage", "caste", "sampleSizeValue", "sampleSizeUnit", "sampleTreatment", "samplingProtocol",
            "verbatimLocality", "verbatimCoordinates", "verbatimEventDate", "associatedOccurrences",
            "associatedReferences", "externalLink"]

TRAITS = {   # the database's trait names (Araneae trait list)
    "bole": "Body length", "cele": "Cephalothorax length", "cewe": "Cephalothorax width",
    "able": "Abdomen length", "abwi": "Abdomen width", "stle": "Sternum length", "stwi": "Sternum width",
    "clhi": "Clypeus height", "chle": "Chelicerae basal part length", "chwi": "Chelicerae width",
    "lale": "Labium length", "lawi": "Labium width", "enle": "Endite length", "enwi": "Endite width",
    "amed": "AME", "aled": "ALE", "pmed": "PME", "pled": "PLE",
    "alsl": "Spinneret ALS", "pmsl": "Spinneret PMS", "plsl": "Spinneret PLS",
    "l1le": "Leg I length", "l2le": "Leg II length", "l3le": "Leg III length", "l4le": "Leg IV length",
    "ptl1": "Pt+Ti I length", "ptl2": "Pt+Ti II length", "ptl3": "Pt+Ti III length", "ptl4": "Pt+Ti IV length",
    "pale": "Palp length", "femp": "Palpal femur", "patp": "Palpal patella", "tibp": "Palpal tibia",
    "tarp": "Palpal tarsus", "bule": "Burrow length", "eggs": "Egg size",
}
for _n, _r in (("1", "I"), ("2", "II"), ("3", "III"), ("4", "IV")):
    for _code, _seg in (("fem", "Femur"), ("pat", "Patella"), ("tib", "Tibia"), ("met", "Metatarsus"),
                        ("tar", "Tarsus")):
        TRAITS[_code + _n] = f"{_seg} {_r} length"

STATISTIC = {"single observation": "individual", "min": "min", "max": "max", "mean": "mean"}
COPY = {"original_name": "verbatimIdentification", "value": "measurementValue", "sex": "sex",
        "life_stage": "lifeStage", "sample_size": "sampleSizeValue", "treatment": "sampleTreatment",
        "note": "measurementRemarks", "locality": "verbatimLocality", "reference": "associatedReferences"}


def group(set_dir):
    set_dir = Path(set_dir)
    xlsx = {f.stem.lower(): f for f in set_dir.glob("*.xlsx") if not f.name.startswith("~$")}
    n = 0
    for pdf in sorted(set_dir.glob("*.pdf")):
        x = xlsx.get(pdf.stem.lower())
        if not x:
            print(f"  {pdf.name}: no export beside it, left as it is")
            continue
        d = set_dir / pdf.stem
        d.mkdir(exist_ok=True)
        shutil.move(str(pdf), d / pdf.name)
        shutil.move(str(x), d / f"{pdf.stem}.xlsx")
        n += 1
    left = sorted(f.name for f in set_dir.glob("*.xlsx") if not f.name.startswith("~$"))
    print(f"{set_dir.name}: {n} papers grouped; exports with no PDF: {left or 'none'}")


def is_export(f):
    return "trait_abbrev" in next(openpyxl.load_workbook(f, read_only=True).active.iter_rows(values_only=True))


def translate_rows(export):
    rows = list(openpyxl.load_workbook(export, read_only=True).active.iter_rows(values_only=True))
    head, out, unknown = [str(h) for h in rows[0]], [], set()
    for r in rows[1:]:
        d = dict(zip(head, r))
        if not d.get("trait_abbrev") or d.get("value") in (None, ""):
            continue
        code = str(d["trait_abbrev"]).strip()
        if code not in TRAITS:
            unknown.add(code)
        row = {t: d.get(k) for k, t in COPY.items() if d.get(k) not in (None, "")}
        row["measurementType"] = TRAITS.get(code, code)
        row["measurementStatistic"] = STATISTIC.get(str(d.get("measure") or "").strip(), d.get("measure"))
        out.append(row)
    return out, unknown


def translate(set_dir):
    set_dir = Path(set_dir)
    total = 0
    for d in sorted(p for p in set_dir.iterdir() if p.is_dir() and list(p.glob("*.pdf"))):
        orig = set_dir / f"{d.name}_wst.xlsx"
        here = d / f"{d.name}.xlsx"
        if not orig.exists():
            if not here.exists() or not is_export(here):
                print(f"  {d.name}: no database export, skipped")
                continue
            shutil.move(str(here), orig)          # the export leaves the folder: nothing reads it there
        rows, unknown = translate_rows(orig)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(TEMPLATE)
        for r in rows:
            ws.append([r.get(c) for c in TEMPLATE])
        wb.save(here)
        total += len(rows)
        print(f"  {d.name}: {len(rows)} rows" + (f"; codes with no name: {sorted(unknown)}" if unknown else ""))
    print(f"{set_dir.name}: {total} GT rows written")


if __name__ == "__main__":
    cmd, dirs = sys.argv[1], sys.argv[2:]
    for s in dirs:
        {"group": group, "translate": translate}[cmd](s)
