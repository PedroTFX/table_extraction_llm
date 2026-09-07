"""
repair_mapping.py — recover trait columns that the LLM mapper CATEGORIZED but then
left with field=None because its reply truncated partway through a wide table.

The failure (Raine2018 table #2, 31 columns): every morphological column got
`category="Morphological measurement"`, but only the first few got
`field="measurementType"` before the reply was cut off. Downstream emits a trait
only when field=="measurementType", so ~21 real trait columns × 1,692 specimens
(~35k rows) vanished silently.

A column the model already tagged with a trait/measurement CATEGORY is a trait —
it classified it, it just didn't finish writing `field`. This sets the field
deterministically, with guards so it can never promote an identifier, locality,
or an uncategorised column.

    repair_mapping(mapping) -> (mapping, n_repaired)

Call it right after the mapper returns, before grouping/output.
"""

from __future__ import annotations

# Categories the mapper uses for columns that ARE per-specimen traits. A column
# carrying one of these is a measurementType; anything else (or category=None) is
# left untouched.
TRAIT_CATEGORIES = {
    "morphological measurement",
    "categorical biological trait",
    "behavioral observation",
    "behavioural observation",
    "physiological measurement",
    "life history trait",
    "phenological observation",
}

# Fields that must NEVER be overwritten even if a trait-ish category slipped onto
# them — these columns qualify the row, they are not measurements.
PROTECTED_FIELDS = {
    "verbatimIdentification", "verbatimLocality", "verbatimCoordinates",
    "verbatimEventDate", "associatedOccurrences", "associatedReferences",
    "samplingProtocol", "measurementRemarks",
}


def _is_trait_category(cat) -> bool:
    return isinstance(cat, str) and cat.strip().lower() in TRAIT_CATEGORIES


def repair_mapping(mapping: dict, verbose=False):
    """Set field='measurementType' on columns that have a trait category but a
    missing/empty field. Returns (mapping, n_repaired). Mutates in place."""
    n = 0
    for header, col in mapping.items():
        if not isinstance(col, dict):
            continue
        field = col.get("field")
        if field in PROTECTED_FIELDS:
            continue
        if field:                       # already assigned (incl. measurementType)
            continue
        if _is_trait_category(col.get("category")):
            col["field"] = "measurementType"
            n += 1
            if verbose:
                print(f"    repaired field for {header!r} "
                      f"(category={col.get('category')!r})")
    return mapping, n


def repair_mapping_file(path, write=True, verbose=True):
    """Repair a *_mapping.json on disk. Returns n_repaired."""
    import json
    from pathlib import Path
    mapping = json.loads(Path(path).read_text(encoding="utf-8"))
    _, n = repair_mapping(mapping, verbose=verbose)
    if write and n:
        Path(path).write_text(json.dumps(mapping, indent=2, ensure_ascii=False),
                              encoding="utf-8")
    return n


if __name__ == "__main__":
    import sys
    for p in sys.argv[1:]:
        n = repair_mapping_file(p, write=False, verbose=True)
        print(f"{p}: {n} column(s) would be repaired (dry run)")
