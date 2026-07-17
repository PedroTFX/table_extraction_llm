"""
Evaluator: compare a pipeline output CSV against a volunteer ground-truth xlsx.

Design goals
------------
- Order-independent: rows are matched as multisets, not by position.
- Field-level metrics: precision / recall / F1 per template column, so you can
  see *which* columns the pipeline gets right and which it misses.
- Row-level metrics: how many GT rows were reproduced, how many were missed,
  how many spurious rows were produced.
- Scoped precision: the ground truth is an answer key only for what the
  volunteers actually recorded. A predicted row for a trait GT never covers has
  nothing to be judged against, so it is reported as OUT-OF-SCOPE rather than as
  a false positive. A predicted row for a trait GT DOES cover, but with a species
  or value GT does not have, stays a false positive — there the GT is a real
  answer key and the row is a real error. See --scope.
- Numeric-aware comparison: the two sides of the comparison have different
  provenance. A predicted value is TEXT read out of the paper ('4.0'), while the
  GT xlsx stores a real number that openpyxl returns as int/float and load_xlsx
  flattens with str() ('4'). Neither is wrong; they just never meet as strings.
  Values that both parse as numbers are compared by VALUE, not spelling.
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
    python evaluate.py output.csv AmbspergTraun1991.xlsx --scope measurementType
"""

import argparse
import csv
import re
import unicodedata
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation

import openpyxl

# Optional: semantic measurementType matching. Import is guarded so the
# evaluator still runs (exact-string keying only) where the matcher or its
# Ollama dependency isn't available.
try:
    from trait_name_matcher import build_type_map
except Exception:
    build_type_map = None

# For the coverage diagnostic: cluster near-identical type strings and pair
# likely same-trait wording mismatches. Reuse the matcher's token similarity if
# present; otherwise fall back to a difflib ratio on a token-sorted key.
try:
    from trait_name_matcher import _soft_token_sim as _type_sim, normalize as _type_key
except Exception:
    from difflib import SequenceMatcher

    def _type_key(s):
        return " ".join(sorted(re.sub(r"[^a-z0-9]+", " ", str(s).lower()).split()))

    def _type_sim(a, b):
        return SequenceMatcher(None, _type_key(a), _type_key(b)).ratio()


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


def canonical_number(s):
    """Canonical spelling of a numeric string, or None if it isn't a number.

    Exists because the pred side and the GT side arrive with different
    provenance: the pipeline reads '4.0' verbatim out of the paper's table (the
    whole extraction IR is cell STRINGS by design — see table_ir.RawTable — since
    a cell may hold '1.9*/4.1**', '<0.001' or '40 ± 3'), while the volunteer
    typed 4 into Excel, openpyxl returns int 4, and load_xlsx renders it str(4)
    -> '4'. Same measurement, two spellings, no string comparison can join them.

    Decimal, not float, and 'f' format, not '%g':
      * float('0.1') + repr round-trips are lossy in ways that surprise;
        Decimal('2.40').normalize() is exactly Decimal('2.4').
      * '%g' flips to exponential past 6 significant digits, so a sample size of
        1234567 would canonicalize to '1.23457e+06' and stop matching itself.
        Quantizing away a positive exponent keeps big integers written out.
    Non-finite input ('nan', 'inf') is deliberately NOT treated as a number —
    such a cell is a literal string in the paper and should compare as one.
    """
    try:
        d = Decimal(s)
    except (InvalidOperation, ValueError, TypeError):
        return None
    if not d.is_finite():
        return None
    d = d.normalize()                       # 4.0 -> 4, 2.40 -> 2.4
    if d.as_tuple().exponent > 0:           # 1E+7 -> 10000000, never exponential
        d = d.quantize(Decimal(1))
    return format(d, "f")


def normalize_value(v, decode=False):
    """Normalize a cell value for comparison.

    Always: strip footnote markers / replacement chars, collapse whitespace,
    NFKC-normalize unicode, lowercase, and fold numeric spelling ('4.0' == '4').
    Optionally decode legend codes.

    Comparison only — the value written to the CSV stays verbatim. Anything that
    is not a number (including '1.9*/4.1**') falls through untouched.
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
    n = canonical_number(s)
    return n if n is not None else s


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


def remap_pred_types(gt_rows, pred_rows, use_llm=True):
    """Rewrite each predicted row's measurementType to the ground-truth wording
    for the SAME trait, so semantically-equal names (e.g. 'Diurnal_activity' vs
    'diurnal activity', 'Body size' vs 'Body Length') are credited by the exact
    key match instead of counting as FP+FN.

    Returns (remapped_pred_rows, nontrivial_map). Only measurementType is
    touched — verbatimIdentification and measurementValue still have to match
    exactly, so this can't manufacture cross-species or cross-value matches.
    """
    if build_type_map is None:
        print("  [semantic] trait_name_matcher not importable — skipping remap")
        return pred_rows, {}

    gt_types = sorted({r.get("measurementType", "") for r in gt_rows
                       if str(r.get("measurementType", "")).strip()})
    pred_types = sorted({r.get("measurementType", "") for r in pred_rows
                         if str(r.get("measurementType", "")).strip()})
    if not gt_types or not pred_types:
        return pred_rows, {}

    type_map = build_type_map(gt_types, pred_types, use_llm=use_llm)
    # keep only pairs that actually change the string (raw-identical pairs are
    # no-ops and just clutter the diagnostic)
    nontrivial = {p: g for p, g in type_map.items() if p != g}
    if not nontrivial:
        return pred_rows, {}

    remapped = []
    for r in pred_rows:
        t = r.get("measurementType", "")
        if t in nontrivial:
            r = {**r, "measurementType": nontrivial[t]}
        remapped.append(r)
    return remapped, nontrivial


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


# --- scoping -------------------------------------------------------------
# Which predicted rows the ground truth is entitled to judge. A GT sheet covers
# a set of traits (and, optionally, a set of species); anything outside that set
# was never in the volunteers' remit, so counting it against precision measures
# the GT's coverage, not the pipeline's correctness.

SCOPE_CHOICES = ["none", "measurementType", "measurementType+verbatimIdentification"]


def build_scope(gt_rows, scope_fields, decode):
    """{field: set of normalized values GT covers} for each scoping field."""
    return {f: {normalize_value(r.get(f, ""), decode) for r in gt_rows
                if str(r.get(f, "")).strip()}
            for f in scope_fields}


def partition_extra(extra, scope, decode):
    """Split spurious rows into (in_scope, out_of_scope).

    in_scope     -> GT covers every scoping field of this row, so GT is a valid
                    answer key for it and the row is a genuine false positive.
    out_of_scope -> GT never covers this trait (or species); there is nothing to
                    score it against. Reported, never counted.
    """
    in_scope, out_of_scope = [], []
    for r in extra:
        uncovered = [f for f, covered in scope.items()
                     if normalize_value(r.get(f, ""), decode) not in covered]
        if uncovered:
            out_of_scope.append((r, uncovered))
        else:
            in_scope.append(r)
    return in_scope, out_of_scope


def prf(tp, fp, fn):
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f = 2 * p * r / (p + r) if (p + r) else 0.0
    return p, r, f


def evaluate(pred_path, gt_path, key_fields, decode, semantic=False, use_llm=True,
             scope="measurementType"):
    gt = load_xlsx(gt_path)
    pred = load_csv(pred_path)

    type_map = {}
    if semantic:
        pred, type_map = remap_pred_types(gt, pred, use_llm=use_llm)

    matched, missing, extra = match_rows(gt, pred, key_fields, decode)

    print("=" * 64)
    print(f"GROUND TRUTH : {gt_path}  ({len(gt)} rows)")
    print(f"PREDICTION   : {pred_path}  ({len(pred)} rows)")
    print(f"KEY          : {key_fields}   decode={decode}  semantic={semantic}")
    print(f"SCOPE        : {scope}")
    print("=" * 64)

    if type_map:
        print(f"\nSEMANTIC measurementType REMAP (pred -> gt, {len(type_map)} pair(s))")
        for p, g in sorted(type_map.items()):
            print(f"  {p!r} -> {g!r}")

    # --- Row-level (based on the key) ---
    scope_fields = [] if scope in (None, "none") else scope.split("+")
    scope_sets = build_scope(gt, scope_fields, decode) if scope_fields else {}
    in_scope, out_of_scope = partition_extra(extra, scope_sets, decode)

    tp, fn = len(matched), len(missing)
    fp_all, fp_scoped = len(extra), len(in_scope)

    # recall never sees spurious rows, so it is identical under both views --
    # it IS the "how much of the GT did we reproduce" number, unscoped by nature.
    p_all, r_all, f_all = prf(tp, fp_all, fn)
    p_sc, r_sc, f_sc = prf(tp, fp_scoped, fn)

    print("\nROW-LEVEL (key match)")
    print(f"  matched (TP)        : {tp}")
    print(f"  missed (FN)         : {fn}")
    print(f"  spurious, in scope  : {fp_scoped}   <- GT covers this trait: real errors")
    print(f"  spurious, out of scope: {len(out_of_scope)}   <- GT never covers this "
          f"trait: nothing to score against")
    print(f"\n  STRICT  P/R/F1      : {p_all:.3f} / {r_all:.3f} / {f_all:.3f}"
          f"   (every extra row counts against precision)")
    print(f"  SCOPED  P/R/F1      : {p_sc:.3f} / {r_sc:.3f} / {f_sc:.3f}"
          f"   (out-of-scope rows excluded)")
    print(f"  RECALL (GT coverage): {r_all:.3f}"
          f"   <- 'how much of the GT did we get' — extras cannot affect this")

    if out_of_scope:
        by_reason = Counter()
        for _, uncovered in out_of_scope:
            by_reason["+".join(uncovered)] += 1
        print("\n  out-of-scope rows by uncovered field:")
        for reason, n in by_reason.most_common():
            print(f"    {reason:<40} {n:>5}")

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

    # --- WHY the misses missed, instead of a sample to read by eye ---
    print_failure_attribution(missing, pred, decode)

    # --- measurementType coverage breakdown (very useful diagnostic) ---
    print_type_coverage(gt, pred, decode)

    return {
        "row": (p_sc, r_sc, f_sc),          # headline: scoped
        "row_strict": (p_all, r_all, f_all),
        "recall": r_all,
        "n_out_of_scope": len(out_of_scope),
        "n_in_scope_fp": fp_scoped,
        "fields": field_stats,
    }


def print_failure_attribution(missing, pred, decode, top=6):
    """Say WHY each missed row missed, instead of printing rows to eyeball.

    A row is keyed on (species, type, value), so a miss failed on exactly one of
    those axes, and which one is computable:

        species absent from the prediction        -> species axis
        species there, that trait not extracted   -> trait axis
        species+trait there, value disagrees      -> value axis

    Then the dominant pattern on each axis is named and counted. Every zero-score
    paper investigated by hand so far turned out to be ONE systematic
    substitution repeated N times ('predator'->'Carnivorous' x43, 'Yes'->
    'macropterous' x87, 'Aphaenogaster ashmeadi' vs the same name with a footnote
    asterisk), so the question worth answering automatically is "is this one bug
    or a hundred?" — the percentage on the verdict line answers it.
    """
    if not missing:
        return
    F_ID, F_TYPE, F_VAL = "verbatimIdentification", "measurementType", "measurementValue"
    n = lambda r, f: normalize_value(r.get(f, ""), decode)

    pred_species = {n(r, F_ID) for r in pred}
    pred_types_of = defaultdict(set)          # species -> {types}
    pred_values_of = defaultdict(list)        # (species, type) -> [values]
    for r in pred:
        s, t = n(r, F_ID), n(r, F_TYPE)
        pred_types_of[s].add(t)
        pred_values_of[(s, t)].append(n(r, F_VAL))

    causes = Counter()
    sub_value = Counter()      # (gt_value, pred_value) -> count
    sub_species = Counter()    # gt_species -> count      (absent from pred)
    sub_trait = Counter()      # (species-less) gt_type -> count
    for r in missing:
        s, t, v = n(r, F_ID), n(r, F_TYPE), n(r, F_VAL)
        if s not in pred_species:
            causes["species not in prediction"] += 1
            sub_species[r.get(F_ID, "")] += 1
        elif t not in pred_types_of[s]:
            causes["species present, trait missing"] += 1
            sub_trait[r.get(F_TYPE, "")] += 1
        else:
            causes["species+trait present, value differs"] += 1
            got = pred_values_of[(s, t)]
            sub_value[(v, got[0] if got else "")] += 1

    total = len(missing)
    print(f"\nWHY THE {total} MISSED ROWS MISSED")
    for label in ("species not in prediction", "species present, trait missing",
                  "species+trait present, value differs"):
        print(f"  {label:<38} {causes.get(label, 0):>6}")

    def verdict(singular, plural, counter):
        if not counter:
            return
        shown = counter.most_common(top)
        covered = sum(c for _, c in shown)
        pct = 100 * covered / total if total else 0
        noun = singular if len(shown) == 1 else plural
        verb = "explains" if len(shown) == 1 else "explain"
        print(f"  -> {len(shown)} {noun} {verb} {covered} of {total} misses "
              f"({pct:.0f}%) — "
              f"{'systematic, not scattered' if pct >= 60 else 'scattered; no single cause'}")

    if sub_value:
        print(f"\n  VALUE SUBSTITUTIONS (gt -> pred), most frequent first:")
        for (g, p), c in sub_value.most_common(top):
            print(f"     {g!r:28} ->  {p!r:28} x{c}")
        verdict("substitution", "substitutions", sub_value)

    if sub_species:
        print(f"\n  SPECIES IN GT BUT NOT IN PREDICTION "
              f"({len(sub_species)} distinct), closest predicted name:")
        preds = sorted({r.get(F_ID, "") for r in pred})
        for name, c in sub_species.most_common(top):
            best, score = "", 0.0
            for p in preds:
                sc = _type_sim(name, p)
                if sc > score:
                    best, score = p, sc
            near = (f"  ~{score:.2f}~  pred {best!r}" if score >= 0.55
                    else "   (nothing similar in the prediction)")
            print(f"     gt {name!r:34}{near}   x{c}")
        verdict("species mismatch", "species mismatches", sub_species)

    if sub_trait:
        print(f"\n  TRAITS THE SPECIES HAS IN GT BUT NOT IN PREDICTION:")
        for name, c in sub_trait.most_common(top):
            print(f"     {name!r:34} x{c}")
        verdict("missing trait", "missing traits", sub_trait)


def print_type_coverage(gt, pred, decode, sim_threshold=0.55):
    """measurementType coverage with wording variants merged inline.

    A GT-side type and a PRED-side type that look like the SAME trait under
    different wording (e.g. 'ecosystem specificity' vs 'ecosystem specifity',
    'tongue length' vs 'mean tongue length') are shown on ONE row, joined by
    'or', with the gt count from the gt-side name and the pred count from the
    pred-side name — so a trait that IS covered on both sides but worded
    differently reads as covered instead of as a miss + a spurious.

    Only cross-side pairs merge (a gt-only name with a pred-only name); two
    same-side names that happen to look alike (e.g. 'fs-15' and 'fs-5', both
    pred-only) are never merged, since those are genuinely different traits.
    A row joined by 'or' is a diagnostic view only — it is credited in the score
    solely when the semantic matcher actually merges the two names.
    """
    gt_types = Counter(normalize_value(r["measurementType"], decode) for r in gt)
    pred_types = Counter(normalize_value(r["measurementType"], decode) for r in pred)

    gt_only = [t for t in gt_types if not pred_types.get(t)]
    pred_only = [t for t in pred_types if not gt_types.get(t)]

    # greedy cross-side pairing, best similarity first, 1:1
    cand = sorted(((_type_sim(g, p), g, p) for g in gt_only for p in pred_only),
                  reverse=True)
    used_g, used_p, merges = set(), set(), []
    for s, g, p in cand:
        if s < sim_threshold or g in used_g or p in used_p:
            continue
        used_g.add(g); used_p.add(p); merges.append((g, p))

    rows = []          # (sort_key, label, gt, pred, note)
    for g, p in merges:
        gc, pc = gt_types[g], pred_types[p]
        note = "" if gc == pc else f"\u0394{pc - gc:+d} (split?)"
        rows.append((_type_key(g), f"{g} or {p}", gc, pc, note))
    for t in set(gt_types) | set(pred_types):
        if t in used_g or t in used_p:
            continue
        gc, pc = gt_types.get(t, 0), pred_types.get(t, 0)
        if gc and pc:
            note = "" if gc == pc else f"\u0394{pc - gc:+d} (split?)"
        else:
            note = "GT-ONLY" if gc else "PRED-ONLY"
        rows.append((_type_key(t), t, gc, pc, note))

    rows.sort(key=lambda r: (r[0], r[1]))
    print("\nmeasurementType COVERAGE")
    print(f"  {'measurementType':<46} {'gt':>4} {'pred':>5}   note")
    for _, label, gc, pc, note in rows:
        print(f"  {label:<46} {gc:>4} {pc:>5}   {note}")
    if merges:
        print("  (rows joined by 'or' are near-identical wording merged for "
              "readability; credited only if the semantic matcher merges them)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pred", help="prediction CSV (your output)")
    ap.add_argument("gt", help="ground-truth xlsx")
    ap.add_argument("--decode", action="store_true",
                    help="apply legend code -> term decoding before comparison")
    ap.add_argument("--key", nargs="+", default=DEFAULT_KEY,
                    help="columns that identify a row for matching")
    ap.add_argument("--semantic-types", action="store_true",
                    help="remap predicted measurementType names onto the "
                         "ground-truth wording for the same trait before matching")
    ap.add_argument("--scope", default="measurementType", choices=SCOPE_CHOICES,
                    help="which predicted rows GT is entitled to judge. "
                         "'measurementType' (default): a row whose trait GT never "
                         "records is out-of-scope, not a false positive. "
                         "'none': strict, every extra row is a false positive.")
    ap.add_argument("--no-llm", action="store_true",
                    help="with --semantic-types, use the deterministic pass only "
                         "(no Ollama calls)")
    args = ap.parse_args()
    evaluate(args.pred, args.gt, args.key, args.decode,
             semantic=args.semantic_types, use_llm=not args.no_llm,
             scope=args.scope)