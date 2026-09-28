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
VALUE_COL = "measurementValue\xa0"     # the output header really has the NBSP

# A mean ± error followed by post-hoc significance letters (Tukey etc.) and an
# optional '(n)': '2.87 ± 0.05 cd', '4.2 ± 0.1 a (30)'. Only after a ± value, so a
# lone footnote marker ('100^b', Weber2023) or a word is never touched.
_SIG_RE = re.compile(
    r"^\s*(?P<v>-?\d[\d.,]*\s*(?:±|\+/-|\+-)\s*\d[\d.,]*)\s+"
    r"(?P<g>[a-h]{1,4})\s*(?:\(\s*(?P<n>\d+)\s*\))?\s*$")


def split_significance(value):
    """-> (value without letters, letters or '', n or ''). The volunteers always
    drop the letters from measurementValue; they describe a between-species test,
    not the measurement, so they are kept in measurementRemarks instead."""
    m = _SIG_RE.match(str(value or ""))
    if not m:
        return value, "", ""
    return m.group("v").strip(), m.group("g"), m.group("n") or ""


_SUP_GROUP_RE = re.compile(
    r"^\s*(?P<m>-?\d[\d.,]*)\^(?P<g>[A-Za-z0-9]{1,4}(?:,[A-Za-z0-9]{1,4})*)\s*"
    r"(?P<e>(?:±|\+/-|\+-)\s*\d[\d.,]*)\s*$")


def split_superscript_group(value):
    """'3.11^1 ± 0.08' -> ('3.11 ± 0.08', '1'); '2.55^2,3 ± 0.08' -> (.., '2,3').
    The superscript sits on the MEAN of a 'mean ± error' cell (the LaTeX cell
    converter keeps it as '^'), where it can only be a post-hoc group mark
    (Kovacs2008). None when the value has no such mark."""
    m = _SUP_GROUP_RE.match(str(value or ""))
    if not m:
        return None
    err = re.sub(r"\s+", " ", m.group("e"))
    return f"{m.group('m')} {err}", m.group("g")


# --- extra detail riding along in a value -----------------------------------
# The volunteers record the bare value and put the rest in its own field. Split
# it off here rather than scoring 'contains the GT value' as correct, so the
# score stays strict AND the detail is kept (Cady1993, Habustova2017, Fondjo2024).
_VALUE_UNIT_RE = re.compile(
    r"^(?P<v>[<>~≈]?\s*-?\d[\d.,]*(?:\s*(?:±|\+/-|[-–—~])\s*-?\d[\d.,]*)?)\s*"
    r"(?P<u>[µμu]m|mm|cm|m|km|mg|µg|g|kg|ml|µl|°C|ºC|%|days?|d|h|hrs?|min|s|yrs?|years?)$")
_VALUE_N_RE = re.compile(r"^(?P<v>.*?\d.*?)\s*\(\s*n\s*=\s*(?P<n>\d+)\s*\)\s*$", re.I)
# 'Genus epithet' + authority and/or family, incl. an authority glued on by the
# PDF ('Schizocosa rovneriUetz & Dondale,1979 (Lycosidae)')
_TAXON_TAIL_RE = re.compile(
    r"^(?P<name>[\"“'‘]?[A-Z][a-z]+[\"”'’]?\s+(?:sp\.|spp\.|[a-z][a-z-]+?))(?=[A-Z(\s,]|$)(?P<tail>.*)$")
_FAMILY_RE = re.compile(r"\(?\s*([A-Z][a-z]+(?:idae|inae|ini))\s*\)?")
_YEAR_RE = re.compile(r"\b(1[7-9]\d{2}|20\d{2})[a-z]?\b")


def split_value_parts(value):
    """Deterministically SPLIT extra detail off a value; do not decide where it
    goes (fill_template.route_value_extras asks the LLM that, per paper).
    -> (core value, [{"text", "kind", "guess"}]) where kind is one of
    unit / sample_size / authority / family and guess is the default field:
         '6–10.9 mm'            -> '6–10.9',        [mm (unit)]
         '11.62 ± 0.50 (n = 4)' -> '11.62 ± 0.50',  [4 (sample_size)]
         'Coras montanus(Emerton, 1890a)(Agelenidae)'
                                -> 'Coras montanus', [Emerton, 1890a (authority),
                                                      Agelenidae (family)]
    A value that is none of these comes back unchanged with []."""
    v = str(value or "").strip()
    parts = []
    m = _VALUE_N_RE.match(v)
    if m:
        v = m.group("v").strip()
        parts.append({"text": m.group("n"), "kind": "sample_size", "guess": "sampleSizeValue"})
    m = _VALUE_UNIT_RE.match(v)
    if m:
        parts.append({"text": m.group("u"), "kind": "unit", "guess": "measurementUnit"})
        return m.group("v").strip(), parts
    m = _TAXON_TAIL_RE.match(v)
    if m and m.group("tail").strip():
        tail = m.group("tail").strip()
        fam = _FAMILY_RE.search(tail)
        year = _YEAR_RE.search(tail)
        if fam or year:                     # a real authority/family, not prose
            auth = tail[:fam.start()] + tail[fam.end():] if fam else tail
            auth = re.sub(r"[()]", " ", auth)
            auth = re.sub(r"\s*,\s*", ", ", re.sub(r"\s+", " ", auth)).strip(" ,;")
            if auth:
                parts.append({"text": auth, "kind": "authority", "guess": "measurementRemarks"})
            if fam:
                parts.append({"text": fam.group(1), "kind": "family", "guess": "measurementRemarks"})
            return m.group("name").strip(), parts
    return v, parts


def split_value_extras(value):
    """split_value_parts with each part sent to its default field — the
    fallback when the LLM routing is unavailable. -> (clean value, {field: text})."""
    core, parts = split_value_parts(value)
    extras = {}
    for p in parts:
        text = f"{p['kind']}: {p['text']}" if p["guess"] == "measurementRemarks" else p["text"]
        if p["guess"] == "measurementRemarks" and extras.get(p["guess"]):
            extras[p["guess"]] += "; " + text
        else:
            extras.setdefault(p["guess"], text)
    return core, extras

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
    """Map a statistic label onto the GT vocabulary. Known synonyms are rewritten;
    a bare number / percentage / significance mark ('1.25*', '2.5') is NOT a
    statistic (the tag step sometimes leaks a value here) and is cleared to '' so
    the value-aware default fills a real term."""
    if not s:
        return s
    key = str(s).strip().lower()
    if key in _STAT_SYNONYMS:
        return _STAT_SYNONYMS[key]
    val = str(s).strip()
    if re.fullmatch(r"[\d.,*%±()/+\-\s]+", val):
        return ""
    return val


# Valid Darwin Core basisOfRecord terms. The tag step occasionally returns a
# free-text DESCRIPTION here ("Morphological traits (e.g., ...)") instead of a
# term; anything not in this set is discarded so the default can apply.
_VALID_BASIS = {
    "preservedspecimen": "PreservedSpecimen", "livingspecimen": "LivingSpecimen",
    "humanobservation": "HumanObservation", "machineobservation": "MachineObservation",
    "materialsample": "MaterialSample", "materialcitation": "MaterialCitation",
    "fossilspecimen": "FossilSpecimen", "occurrence": "Occurrence", "taxon": "Taxon",
}


def normalize_basis_out(s):
    """Return the canonical DwC basisOfRecord term, or '' if `s` is not one (so
    the default fills in). Guards against the tag step emitting a description."""
    if not s:
        return s
    return _VALID_BASIS.get(str(s).strip().lower(), "")


_NUMERIC_VALUE_RE = re.compile(r"^[<>~≈±]?\s*-?\d")


def _looks_numeric_value(v) -> bool:
    """A measurementValue that reads as a number (optionally a comparator/±
    prefix). Used to pick the value-aware defaults in default_tag."""
    return bool(_NUMERIC_VALUE_RE.match(str(v).strip()))


_MEAN_SD_RE = re.compile(r"^\s*-?\d[\d.,]*\s*(±|\+/-|\+-)\s*\d")
_RANGE_RE = re.compile(r"^\s*-?\d[\d.,]*\s*[-–—]\s*\d[\d.,]*\s*$")


_SE_RE = re.compile(r"±\s*(?:1\s*)?s\.?\s?e\.?m?\b|\bstandard errors?\b|\bmeans?\s*\(?\s*±?\s*se\b", re.I)
_SD_RE = re.compile(r"±\s*(?:1\s*)?s\.?\s?d\.?\b|\bstandard deviations?\b|\bmeans?\s*\(?\s*±?\s*sd\b", re.I)


def pm_statistic_from_text(text):
    """Which error a paper reports after '±': 'mean ± SE' or 'mean ± SD', from
    how often it says each (Gibb2005's Table 2 caption: 'Mean ± SE'). None when
    the paper names neither, so the caller keeps its own default."""
    t = (text or "").replace("$\\pm$", "±").replace("\\pm", "±")
    se, sd = len(_SE_RE.findall(t)), len(_SD_RE.findall(t))
    if se == sd:
        return None
    return "mean ± SE" if se > sd else "mean ± SD"


def default_tag(col, value, pm_statistic=None):
    """Value-aware fallback for a tag the tag step left empty.

    Chosen from the ground-truth conventions (one vote per paper):
      basisOfRecord         numeric -> PreservedSpecimen (56% of papers);
                            categorical -> MaterialCitation (40%, vs 17% for
                            HumanObservation, the old default)
      measurementStatistic  'x ± y' -> the paper's 'mean ± SE'/'mean ± SD'
                            (pm_statistic), else 'mean ± SD'; 'a-b' -> 'range';
                            other numeric -> 'mean'; categorical -> 'mode'
    Returns None for columns without a value-aware default."""
    numeric = _looks_numeric_value(value)
    if col == "basisOfRecord":
        return "PreservedSpecimen" if numeric else "MaterialCitation"
    if col == "measurementStatistic":
        v = str(value or "")
        if _MEAN_SD_RE.match(v):
            return pm_statistic or "mean ± SD"
        if _RANGE_RE.match(v):
            return "range"
        return "mean" if numeric else "mode"
    return None


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


def _significance_types(grouped):
    """measurementTypes whose '± value + letters' suffix really is a post-hoc
    group: the letters VARY down the column (a, ab, b, ...). A constant suffix is
    a unit ('3.2 ± 0.4 d' = days, 'g', 'h') and is left alone."""
    seen = {}
    for sp in grouped.values():
        for m in sp.get("measurements", []):
            g = split_significance(m.get("measurementValue", ""))[1]
            if g:
                seen.setdefault(clean_type(m.get("measurementType", "")), set()).add(g)
    return {t for t, gs in seen.items() if len(gs) >= 2}


def merge_to_rows(grouped, column_lookup, decode, defaults, keep_protocol,
                  pm_statistic=None):
    rows = []
    sig_types = _significance_types(grouped)
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

                # '2.87 ± 0.05 cd' / '4.2 ± 0.1 a (30)': move post-hoc letters
                # to measurementRemarks and a trailing '(n)' to sampleSizeValue
                value_, group, n = split_significance(row[VALUE_COL])
                sup = split_superscript_group(row[VALUE_COL])
                if sup:
                    # '3.11^1 ± 0.08': a superscript on the mean is always a group
                    # mark (a LaTeX '^' is unambiguous, unlike trailing letters)
                    value_, group, n = sup[0], sup[1], ""
                if group and (sup or m_type in sig_types):
                    row[VALUE_COL] = value_
                    note = f"post-hoc significance group: {group}"
                    row["measurementRemarks"] = "; ".join(
                        x for x in (str(row["measurementRemarks"] or "").strip(), note) if x)
                    if n and not row["sampleSizeValue"]:
                        row["sampleSizeValue"] = n

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
                # discard a non-DwC basisOfRecord (a description the tag step
                # returned by mistake) so the default below fills a valid term
                row["basisOfRecord"] = normalize_basis_out(row.get("basisOfRecord"))

                # defaults for constant fields (override empty-like values too);
                # basisOfRecord and measurementStatistic are value-aware (see
                # default_tag), the rest take the constant default.
                for col, default in defaults.items():
                    if is_empty_like(row.get(col)):
                        aware = default_tag(col, row.get(VALUE_COL), pm_statistic)
                        row[col] = aware if aware is not None else default

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
    pm_statistic=None,
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
    rows = merge_to_rows(grouped, column_lookup, decode, defaults, keep_protocol,
                         pm_statistic=pm_statistic)

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  ✓ Wrote {len(rows)} rows to {output_path}")
    return rows


if __name__ == "__main__":
    write_output_csv()