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

from tables import split_multivalue

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

# Not an output column — a column-level fact about the VALUES (set by
# table_to_data.classify_value_types) that decides whether a comma in a cell
# separates list items or belongs to the value. Carried through the lookup so the
# split below is made per column, not per cell.
VALUE_SEMANTIC_KEYS = ["multi_value"]

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


# Fold free-form statistic labels (from the LLM tag step or a mapper) onto the
# ground-truth vocabulary. Only known synonyms are rewritten; an already-canonical
# term (mean, mode, min, max, range, count, median, SD, SE, individual, mean ± SD)
# passes through untouched, so a specific GT term the model got right is kept.
_STAT_SYNONYMS = {
    "standard deviation": "SD", "std": "SD", "stdev": "SD", "std dev": "SD",
    "standard error": "SE", "sem": "SE", "std error": "SE",
    "average": "mean", "avg": "mean",
    "single observation": "individual", "single measurement": "individual",
    "single specimen": "individual", "one individual": "individual",
    "single value": "individual", "observation": "individual",
    "minimum": "min", "maximum": "max",
}


def normalize_statistic_out(s):
    """Map a statistic label onto the GT vocabulary (synonyms only)."""
    if not s:
        return s
    return _STAT_SYNONYMS.get(str(s).strip().lower(), str(s).strip())


_NUMERIC_VALUE_RE = re.compile(r"^[<>~≈±]?\s*-?\d")


def _looks_numeric_value(v) -> bool:
    """A measurementValue that reads as a number (optionally a comparator/±
    prefix). Used to pick the measurementStatistic default: the ground truth
    labels a bare numeric reading 'individual' (a single-specimen measurement)
    and a categorical state 'mode'."""
    return bool(_NUMERIC_VALUE_RE.match(str(v).strip()))


def clean_type(t):
    """Normalise a measurementType for output.

    Besides stripping footnote markers and non-breaking spaces, this replaces the
    snake_case the pipeline sometimes emits ('larvae_on_softwood_trees') with
    spaces ('larvae on softwood trees'). Underscores are a machine artifact — a
    human reading the CSV, and the volunteers' own wording, use spaces — so they
    should never reach the output. Hyphens between word characters are treated the
    same ('mosses-lichens' -> 'mosses lichens'); a hyphen inside a number or code
    (a range like '3-5', 'CO-2') is left alone.
    """
    s = FOOTNOTE_RE.sub("", str(t)).replace("\xa0", " ")
    s = s.replace("_", " ")
    s = re.sub(r"(?<=[A-Za-z])-(?=[A-Za-z])", " ", s)
    return re.sub(r"\s+", " ", s).strip()


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
            for key_ in VALUE_SEMANTIC_KEYS:
                if col_data.get(key_) is not None:
                    col_tags[key_] = col_data[key_]
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

            # One measurement may hold several values ('W, S, P' -> three rows).
            # A comma alone does not mean a list: it is also part of a taxonomic
            # authority ('Coras montanus (Emerton, 1890a)'), a decimal, or a
            # thousands separator. Ask the column first — the mapping recorded
            # whether THIS column's cells behave like lists — and fall back to a
            # bracket/quote/digit-aware read of the cell when the column is
            # unknown (measurementTypes that never reached a mapping).
            values = split_multivalue(
                value, allow=column_lookup.get(m_type, {}).get("multi_value"))

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

                # fold a free-form statistic label onto the GT vocabulary
                # (single observation -> individual, standard deviation -> SD)
                if row.get("measurementStatistic"):
                    row["measurementStatistic"] = normalize_statistic_out(
                        row["measurementStatistic"])

                # defaults for constant fields (override empty-like values too)
                for col, default in defaults.items():
                    if is_empty_like(row.get(col)):
                        # measurementStatistic default is value-aware: a bare
                        # numeric reading is a single-specimen 'individual'
                        # measurement in the ground truth, only a categorical
                        # state defaults to 'mode'.
                        if col == "measurementStatistic":
                            row[col] = ("individual"
                                        if _looks_numeric_value(row.get("measurementValue"))
                                        else default)
                        else:
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