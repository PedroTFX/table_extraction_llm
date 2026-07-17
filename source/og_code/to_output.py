"""
Final pipeline step: turn grouped_by_species.json + *_table_mapping_*.json
straight into the team's output CSV.

This consolidates join_grouped_and_mapping.py and folds in the systematic fixes
that the evaluator surfaced:
  1. strip footnote markers / U+FFFD from measurementType (Feeding group<dagger> -> Feeding group)
  2. optionally decode legend codes in measurementValue (W -> Wood, etc.)
  3. blank out measurementMethod that is actually a sampling-protocol paragraph
  4. drop-in defaults for constant fields the volunteers used (measurementStatistic=mode, sex=both)

Call write_output_csv(...) from run_pipeline as the last step.
"""

import csv
import json
from pathlib import Path
import re
from glob import glob

COLUMNS = [
    "basisOfRecord", "verbatimIdentification", "measurementType",
    "measurementMethod", "measurementValue\xa0", "measurementUnit",
    "measurementStatistic", "measurementRemarks", "sex", "lifeStage",
    "caste", "sampleSizeValue", "sampleSizeUnit", "sampleTreatment",
    "samplingProtocol", "verbatimLocality\xa0", "verbatimCoordinates",
    "verbatimEventDate", "associatedOccurrences", "associatedReferences ",
    "externalLink",
]

JSON_KEY = {
    "measurementValue\xa0": "measurementValue",
    "verbatimLocality\xa0": "verbatimLocality",
    "associatedReferences ": "associatedReferences",
}

COLUMN_LEVEL_TAGS = ["basisOfRecord", "measurementMethod", "measurementUnit", "measurementStatistic"]

# Legend codes -> expanded terms. Edit per-paper; keep keys lowercase.
VALUE_DECODE = {
    "w": "Wood", "s": "Soil", "w/s": "Wood/soil interface", "p": "Polyphagous",
    "m": "Mound", "h": "Hypogeal", "a": "Arboreal",
    "m(o)": "Found in mounds of other termites",
    "ldw": "Lying dead wood", "sdw": "Standing dead wood", "b": "Bait",
}

FOOTNOTE_RE = re.compile(r"[†‡§¶\uFFFD]")

# Values that should be treated as "no value" when applying defaults.
EMPTY_LIKE = {"", "null", "none", "unknown"}


def is_empty_like(v):
    return v is None or str(v).strip().lower() in EMPTY_LIKE


def clean_type(t):
    return FOOTNOTE_RE.sub("", str(t)).replace("\xa0", " ").strip()


def decode_value(v, decode):
    if not decode or not isinstance(v, str):
        return v
    return VALUE_DECODE.get(v.strip().lower(), v)


def looks_like_protocol(text):
    return isinstance(text, str) and len(text) > 120


def build_column_lookup(mapping_paths):
    lookup = {}
    for path in mapping_paths:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            mapping = json.load(f)
        for header, col_data in mapping.items():
            if col_data.get("category") is None:
                continue
            if col_data.get("field") == "verbatimIdentification":
                continue
            col_tags = {}
            for tag in COLUMN_LEVEL_TAGS:
                val = col_data.get(tag)
                if val is None:
                    continue
                # Never carry a protocol blob into the lookup — it is not a
                # short method label and will pollute every row for that column.
                if tag == "measurementMethod" and looks_like_protocol(val):
                    continue
                col_tags[tag] = val
            if col_tags:
                key = col_data.get("canonicalType") or header
                lookup[clean_type(key)] = col_tags
    return lookup


def merge_to_rows(grouped, column_lookup, decode, defaults, keep_protocol):
    rows = []
    for species, species_data in grouped.items():
        species_level = {k: v for k, v in species_data.items() if k != "measurements"}

        for measurement in species_data.get("measurements", []):
            m_type = clean_type(measurement.get("measurementType", ""))
            value = measurement.get("measurementValue", "")

            if isinstance(value, str) and "," in value:
                values = [v.strip() for v in value.split(",") if v.strip()]
            else:
                values = [value]

            for v in values:
                row = {col: "" for col in COLUMNS}

                # species-level
                for col in COLUMNS:
                    key = JSON_KEY.get(col, col)
                    if key in species_level and species_level[key] is not None:
                        row[col] = species_level[key]

                # measurement-level
                for col in COLUMNS:
                    key = JSON_KEY.get(col, col)
                    if key == "measurementValue":
                        row[col] = decode_value(v, decode)
                    elif key == "measurementType":
                        row[col] = m_type
                    elif key in measurement and measurement[key] is not None:
                        row[col] = measurement[key]

                # column-level enrichment (only fill empties)
                if m_type in column_lookup:
                    for col in COLUMNS:
                        key = JSON_KEY.get(col, col)
                        val = column_lookup[m_type].get(key)
                        if val is not None and not row[col]:
                            row[col] = val

                # fix: measurementMethod that is really a protocol blob
                if looks_like_protocol(row["measurementMethod"]):
                    if keep_protocol and not row["samplingProtocol"]:
                        row["samplingProtocol"] = row["measurementMethod"]
                    row["measurementMethod"] = ""

                # defaults for constant fields (override empty-like values too)
                for col, default in defaults.items():
                    if is_empty_like(row.get(col)):
                        row[col] = default

                rows.append(row)
    return rows


def write_output_csv(
    grouped_path="grouped_by_species.json",
    paper_stem="Abensperg-Traun M. (1991)",
    mapping_paths=None,
    output_path="output.csv",
    decode=True,
    defaults=None,
    keep_protocol=False,
):
    if defaults is None:
        defaults = {"measurementStatistic": "mode", "sex": "both"}

    with open(grouped_path, "r", encoding="utf-8", errors="replace") as f:
        grouped = json.load(f)

    # Prefer an explicit list (the pipeline passes per-table mapping files);
    # fall back to the legacy glob-by-stem for standalone use.
    if mapping_paths is None:
        mapping_paths = glob(f"{paper_stem}_table_mapping_*.json")
    mapping_paths = [p for p in mapping_paths if Path(p).exists()]
    column_lookup = build_column_lookup(mapping_paths)
    rows = merge_to_rows(grouped, column_lookup, decode, defaults, keep_protocol)

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  ✓ Wrote {len(rows)} rows to {output_path}")
    return rows


if __name__ == "__main__":
    write_output_csv()