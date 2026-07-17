"""
Evaluator: compare a pipeline output CSV against a volunteer ground-truth xlsx.

Design goals
------------
- Order-independent: rows are matched as multisets, not by position.
- Field-level metrics: precision / recall / F1 per template column, so you can
  see *which* columns the pipeline gets right and which it misses.
- Row-level metrics: how many GT rows were reproduced, how many were missed,
  how many spurious rows were produced.
- Honest about normalization: a small, explicit set of normalizers handles
  encoding noise (the U+FFFD replacement char), footnote markers (dagger/etc),
  non-breaking spaces and trailing whitespace in headers. Anything beyond that
  (e.g. decoding W -> Wood) is opt-in via VALUE_DECODE so you can measure both
  "raw" and "decoded" performance and see how much the decoding step buys you.

Usage
-----
    python evaluate.py output.csv AmbspergTraun1991.xlsx
    python evaluate.py output.csv AmbspergTraun1991.xlsx --decode
    python evaluate.py output.csv AmbspergTraun1991.xlsx --key verbatimIdentification measurementType measurementValue
"""

import argparse
import csv
import re
import unicodedata
from collections import Counter, defaultdict

import openpyxl


# Canonical template columns (whitespace/nbsp stripped — see normalize_header).
COLUMNS = [
    "basisOfRecord", "verbatimIdentification", "measurementType",
    "measurementMethod", "measurementValue", "measurementUnit",
    "measurementStatistic", "measurementRemarks", "sex", "lifeStage",
    "caste", "sampleSizeValue", "sampleSizeUnit", "sampleTreatment",
    "samplingProtocol", "verbatimLocality", "verbatimCoordinates",
    "verbatimEventDate", "associatedOccurrences", "associatedReferences",
    "externalLink",
]

# Columns that form the identity of a row for matching. measurementValue is the
# payload, so the natural key is "which trait of which species, with what value".
DEFAULT_KEY = ["verbatimIdentification", "measurementType", "measurementValue"]

# Optional: legend codes -> expanded terms the volunteers used. Opt-in (--decode).
# Keyed by (normalized) measurementType is overkill here since codes are shared,
# so we keep a flat map and apply it to measurementValue.
VALUE_DECODE = {
    "w": "wood",
    "s": "soil",
    "w/s": "wood/soil interface",
    "p": "polyphagous",
    "m": "mound",
    "h": "hypogeal",
    "a": "arboreal",
    "m(o)": "found in mounds of other termites",
    "ldw": "lying dead wood",
    "sdw": "standing dead wood",
    "b": "bait",
}


def normalize_header(h):
    """Strip nbsp, trailing footnote markers and surrounding whitespace from a header."""
    if h is None:
        return ""
    h = str(h).replace("\xa0", " ")
    h = re.sub(r"[†‡§¶\uFFFD]", "", h)  # footnote markers + replacement char
    return h.strip()


def normalize_value(v, decode=False):
    """Normalize a cell value for comparison.

    Always: strip footnote markers / replacement chars, collapse whitespace,
    NFKC-normalize unicode, lowercase. Optionally decode legend codes.
    """
    if v is None:
        return ""
    s = str(v)
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"[†‡§¶\uFFFD]", "", s)
    s = s.replace("\xa0", " ")
    s = re.sub(r"\s+", " ", s).strip().lower()
    if decode and s in VALUE_DECODE:
        s = VALUE_DECODE[s]
    return s


def load_csv(path):
    with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        raw_to_canon = {col: normalize_header(col) for col in reader.fieldnames}
        rows = []
        for raw in reader:
            row = {c: "" for c in COLUMNS}
            for raw_col, val in raw.items():
                canon = raw_to_canon.get(raw_col, "")
                if canon in row:
                    row[canon] = val if val is not None else ""
            rows.append(row)
    return rows


def load_xlsx(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    all_rows = list(ws.iter_rows(values_only=True))
    headers = [normalize_header(h) for h in all_rows[0]]
    rows = []
    for raw in all_rows[1:]:
        if all(c is None or str(c).strip() == "" for c in raw):
            continue
        row = {c: "" for c in COLUMNS}
        for h, val in zip(headers, raw):
            if h in row:
                row[h] = "" if val is None else str(val)
        rows.append(row)
    return rows


def row_key(row, key_fields, decode):
    return tuple(normalize_value(row.get(f, ""), decode) for f in key_fields)


def match_rows(gt_rows, pred_rows, key_fields, decode):
    """Greedy multiset match on the key. Returns matched pairs + unmatched lists."""
    gt_buckets = defaultdict(list)
    for r in gt_rows:
        gt_buckets[row_key(r, key_fields, decode)].append(r)

    matched = []          # (gt_row, pred_row)
    extra = []            # pred rows with no GT counterpart (false positives)
    used = Counter()

    for p in pred_rows:
        k = row_key(p, key_fields, decode)
        bucket = gt_buckets.get(k)
        if bucket and used[k] < len(bucket):
            matched.append((bucket[used[k]], p))
            used[k] += 1
        else:
            extra.append(p)

    missing = []          # GT rows never matched (false negatives)
    for k, bucket in gt_buckets.items():
        for i in range(used[k], len(bucket)):
            missing.append(bucket[i])

    return matched, missing, extra


def prf(tp, fp, fn):
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f = 2 * p * r / (p + r) if (p + r) else 0.0
    return p, r, f


def evaluate(pred_path, gt_path, key_fields, decode):
    gt = load_xlsx(gt_path)
    pred = load_csv(pred_path)

    matched, missing, extra = match_rows(gt, pred, key_fields, decode)

    print("=" * 64)
    print(f"GROUND TRUTH : {gt_path}  ({len(gt)} rows)")
    print(f"PREDICTION   : {pred_path}  ({len(pred)} rows)")
    print(f"KEY          : {key_fields}   decode={decode}")
    print("=" * 64)

    # --- Row-level (based on the key) ---
    tp, fp, fn = len(matched), len(extra), len(missing)
    p, r, f = prf(tp, fp, fn)
    print("\nROW-LEVEL (key match)")
    print(f"  matched (TP)        : {tp}")
    print(f"  spurious (FP)       : {fp}")
    print(f"  missed (FN)         : {fn}")
    print(f"  precision/recall/F1 : {p:.3f} / {r:.3f} / {f:.3f}")

    # --- Field-level accuracy on matched rows ---
    # For each non-key column, of the matched rows, how often do values agree?
    nonkey = [c for c in COLUMNS if c not in key_fields]
    print("\nFIELD-LEVEL ACCURACY (on matched rows only)")
    print(f"  {'column':<24} {'agree':>6} {'total':>6} {'acc':>6}")
    field_stats = {}
    for col in nonkey:
        agree = total = 0
        for g, pr in matched:
            gv = normalize_value(g.get(col, ""), decode)
            pv = normalize_value(pr.get(col, ""), decode)
            if gv == "" and pv == "":
                continue  # both empty: not informative
            total += 1
            if gv == pv:
                agree += 1
        acc = agree / total if total else float("nan")
        field_stats[col] = (agree, total, acc)
        flag = "" if total == 0 else ("  <-- low" if acc < 0.5 else "")
        acc_s = "  n/a" if total == 0 else f"{acc:.3f}"
        print(f"  {col:<24} {agree:>6} {total:>6} {acc_s:>6}{flag}")

    # --- A few concrete examples of misses, to make the report actionable ---
    if missing:
        print(f"\nSAMPLE MISSED GT ROWS (first 8 of {len(missing)})")
        for row in missing[:8]:
            print("   ", " | ".join(f"{f}={row.get(f, '')!r}" for f in key_fields))
    if extra:
        print(f"\nSAMPLE SPURIOUS PRED ROWS (first 8 of {len(extra)})")
        for row in extra[:8]:
            print("   ", " | ".join(f"{f}={row.get(f, '')!r}" for f in key_fields))

    # --- measurementType coverage breakdown (very useful diagnostic) ---
    print("\nmeasurementType COVERAGE")
    gt_types = Counter(normalize_value(r["measurementType"], decode) for r in gt)
    pred_types = Counter(normalize_value(r["measurementType"], decode) for r in pred)
    for t in sorted(set(gt_types) | set(pred_types)):
        print(f"  {t:<28} gt={gt_types.get(t,0):>3}  pred={pred_types.get(t,0):>3}")

    return {"row": (p, r, f), "fields": field_stats}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pred", help="prediction CSV (your output)")
    ap.add_argument("gt", help="ground-truth xlsx")
    ap.add_argument("--decode", action="store_true",
                    help="apply legend code -> term decoding before comparison")
    ap.add_argument("--key", nargs="+", default=DEFAULT_KEY,
                    help="columns that identify a row for matching")
    args = ap.parse_args()
    evaluate(args.pred, args.gt, args.key, args.decode)
