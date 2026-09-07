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
import contextlib
import csv
import io
import json
import re
import traceback
import unicodedata
from itertools import combinations
from pathlib import Path
from collections import Counter, defaultdict

try:
    from column_relevance import invoke_sized, loads_salvaging
except Exception:                       # evaluator must run even without Ollama deps
    invoke_sized = None
    loads_salvaging = None
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

# ---------------------------------------------------------------------------
# Scoring categories — edit freely
# ---------------------------------------------------------------------------
# Each entry is one SCORE reported side by side: a name and the fields a
# predicted row must get right to count as a match. Adding a field can only
# lower the score (more must agree), so the sets read as increasing strictness
# and the drop between them tells you which field is costing you rows.
#
# To add or remove a category, edit this dict; to change which ones a run
# reports, edit ACTIVE_KEY_SETS (or pass key_sets= to evaluate()).
KEY_SETS = {
    # what the trait record IS: which trait of which species, and its value
    "core": ["verbatimIdentification", "measurementType", "measurementValue"],
    # the same, plus the descriptive tags the volunteers fill in
    "tags": ["basisOfRecord", "verbatimIdentification", "measurementType",
             "measurementValue", "measurementStatistic", "sex", "lifeStage"],
}

# Which categories every run prints. "core" stays first: it is the headline.
ACTIVE_KEY_SETS = ["core", "tags"]

# Whether the misses CSV is annotated with an LLM-judged severity + reasoning
# (score-neutral diagnostic). Off = no LLM calls in the evaluator.
ASSESS_MISS_SEVERITY = True

# ---------------------------------------------------------------------------
# Taxon-name comparison
# ---------------------------------------------------------------------------
# Volunteers and the pipeline write the same organism differently. The
# differences are almost never in the WORDS — they are extra classification
# tokens, a duplicated genus, an authority, or an abbreviated genus:
#
#   'Calopteryx aequabilis'  vs  'Calopteryx.aequabilis Calopteryx aequabilis
#                                 Calopterygidae Zygoptera'   (+family, +suborder)
#   'Anthophora californica' vs  'Anthophora Anthophoroides californica' (+subgenus)
#   'Andrena vilhenae'       vs  'A. vilhenae'                (abbreviated genus)
#
# So names are compared as SETS OF WORDS, not as strings and not by character
# similarity: an anagram or a near-spelling is not a match, while the same words
# plus a family name is. Rank words (family/order/suborder) are dropped outright
# because they classify the organism rather than name it.
# Rank-name endings, deliberately restricted to suffixes that do not occur as
# ordinary species epithets. 'acea'/'odea' were removed: they matched real
# epithets ('ochracea', 'rosacea', 'violacea'), dropping the epithet and making
# the species unmatchable. Family is '-aceae' (Rosaceae), not '-acea'.
_RANK_SUFFIX = re.compile(
    r"(idae|inae|aceae|oidea|ptera|formes|morpha|ales)$")
# Words that qualify a name without identifying it.
_TAXON_NOISE = {
    "sp", "spp", "ssp", "subsp", "var", "cf", "aff", "nr", "morph",
    "complex", "group", "sensu", "lato", "stricto", "indet", "unknown",
    "undetermined", "nov", "novum", "et", "al",
}


def species_tokens(name) -> frozenset:
    """The identifying words of a taxon name, lowercased, order-independent.

    Drops parentheticals (authorities, sample sizes), splits on any punctuation
    so 'Calopteryx.aequabilis' becomes two words, removes rank words and
    qualifiers, and de-duplicates — so a repeated genus collapses instead of
    counting twice.

    Glued author citations are un-glued FIRST. Extraction sometimes runs the
    taxonomic authority straight onto the epithet with no space
    ('eickstedtaeSchlinger, 1972', 'sulphuripesLoew') or runs the status marker
    on ('kenneisp. nov.'). Left alone, 'eickstedtae' and 'eickstedtaeschlinger'
    are different tokens and the same species fails to match. Splitting at the
    lowercase->UPPERCASE boundary (and before a run-on 'sp.'/'ssp.') restores the
    epithet as its own token; the author words then fall away exactly like a
    spaced authority does. This is done ONLY for comparison — the name written to
    verbatimIdentification is never changed, so the authority stays in the data.
    """
    s = unicodedata.normalize("NFKD", str(name or "")).encode("ascii", "ignore").decode()
    s = re.sub(r"\([^)]*\)", " ", s)
    s = re.sub(r"\bn\s*=\s*\d+", " ", s, flags=re.I)
    # un-glue 'epithetAuthor' -> 'epithet Author' while the case boundary is still
    # visible (i.e. before lowercasing)
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", s)
    # un-glue a run-on status marker: 'kenneisp. nov.' -> 'kennei sp. nov.'
    s = re.sub(r"([a-z]{3,})(sp{1,2}\.?\s*nov)", r"\1 \2", s, flags=re.I)
    s = s.lower()
    toks = [t for t in re.split(r"[^a-z0-9]+", s) if t]
    kept, ranks = set(), set()
    for t in toks:
        if t in _TAXON_NOISE:
            continue
        if t.isdigit():
            continue                     # a stray authority year ('1972')
        if len(t) > 3 and _RANK_SUFFIX.search(t):
            ranks.add(t)                 # Calopterygidae, Zygoptera, Halictinae
            continue
        kept.add(t)
    # Rank words are dropped only when they are EXTRA. A record identified to
    # family level ('Hesperiidae') is named by its rank word, and discarding it
    # would leave nothing to compare.
    return frozenset(kept or ranks)


def species_match(a, b) -> bool:
    """Do two taxon names denote the same organism?

    True when one name's words are all present in the other's. Extra words are
    tolerated on either side, which is the whole point: a prediction carrying a
    subgenus, family and suborder still matches the bare binomial.

    Two guards stop that tolerance from over-matching:
      * a ONE-WORD name must match exactly. Otherwise 'Andrena' would be
        credited as 'Andrena vilhenae' — a genus is not one of its species.
      * a single-letter word may stand in for a longer word beginning with that
        letter ('a' ~ 'andrena'), but every other word must still match exactly,
        so 'A. vilhenae' resolves on the epithet rather than on the initial.
    """
    ta, tb = species_tokens(a), species_tokens(b)
    if not ta or not tb:
        return False
    if ta == tb:
        return True
    small, large = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
    if len(small) < 2:
        return False                     # genus/family alone must match exactly
    if small <= large:
        return True

    # Abbreviation-tolerant pass, tried in BOTH directions: which side holds the
    # abbreviation is an accident of who wrote the name.
    def _abbrev_ok(x, y):
        missing, extra = x - y, y - x
        if len(missing) != 1 or not extra:
            return False
        m = next(iter(missing))
        return len(m) == 1 and any(e.startswith(m) for e in extra)

    if _abbrev_ok(ta, tb) or _abbrev_ok(tb, ta):
        return True

    # OCR-typo-tolerant pass. Extraction from a rasterized page drops or doubles
    # single letters in the epithet: 'Ataenius'/'Atenius', 'jelski'/'jelskii',
    # 'Dorymyrex'/'Dorymyrmex', 'appenninicus'/'apenninicus'. Every one of these
    # has ALL tokens equal except ONE, and that one differs by a single-character
    # edit. Accept exactly that case, under strict guards so it can never merge
    # two real taxa:
    #   * exactly one token differs on each side (all others match exactly), so
    #     'Aphodius sp1' vs 'Aphodius sp2' is NOT touched here — that reduces to
    #     the two differing tokens 'sp1'/'sp2' and is handled by the length gate;
    #   * the differing tokens are >=6 chars, so short morphospecies codes
    #     ('sp1'/'sp2', 'fs-5'/'fs-15') and initials never qualify;
    #   * edit distance exactly 1, so 'forewing'/'hindwing' (distance 4) is safe.
    return _ocr_typo_ok(ta, tb)


def _edit_distance_le1(a: str, b: str) -> bool:
    """True iff `a` and `b` are within one insertion/deletion/substitution.
    Cheap early exits on length; no full DP needed for a threshold of 1."""
    if a == b:
        return True
    la, lb = len(a), len(b)
    if abs(la - lb) > 1:
        return False
    if la == lb:                              # at most one substitution
        return sum(x != y for x, y in zip(a, b)) == 1
    # lengths differ by 1: b must be a with one char inserted (try both orders)
    short, long = (a, b) if la < lb else (b, a)
    i = j = edits = 0
    while i < len(short) and j < len(long):
        if short[i] == long[j]:
            i += 1; j += 1
        else:
            edits += 1
            if edits > 1:
                return False
            j += 1                            # skip the inserted char in `long`
    return True


def _ocr_typo_ok(ta: frozenset, tb: frozenset) -> bool:
    """Match names identical except for a single one-character OCR slip in one
    token. See species_match for the guards this enforces."""
    common = ta & tb
    da, db = ta - common, tb - common
    if len(da) != 1 or len(db) != 1:          # exactly one token differs each side
        return False
    wa, wb = next(iter(da)), next(iter(db))
    if len(wa) < 6 or len(wb) < 6:            # never on short morphospecies codes
        return False
    return _edit_distance_le1(wa, wb)


def remap_pred_species(gt_rows, pred_rows):
    """Rewrite each predicted verbatimIdentification to the ground-truth wording
    for the SAME organism, so the exact key match credits it.

    Same design as remap_pred_types, and for the same reason: the score and every
    diagnostic downstream then read one decision instead of forming two opinions.
    A predicted name is only ever rewritten to a GT name it MATCHES, so this
    cannot move rows between different organisms.

    Returns (rows, mapping, unmapped) where `unmapped` explains every predicted
    name that was left alone — an unexplained non-match is what made a whole
    genus look absent from the prediction when the names were in fact present.
    """
    gt_counts = Counter(r.get("verbatimIdentification", "") for r in gt_rows
                        if str(r.get("verbatimIdentification", "")).strip())
    gt_names = sorted(gt_counts)
    pred_names = sorted({r.get("verbatimIdentification", "") for r in pred_rows
                         if str(r.get("verbatimIdentification", "")).strip()})
    exact = {normalize_value(g) for g in gt_names}

    mapping, unmapped = {}, []
    for p in pred_names:
        if normalize_value(p) in exact:
            continue                                  # already agrees
        hits = [g for g in gt_names if species_match(p, g)]
        if not hits:
            unmapped.append((p, "no ground-truth name denotes this organism"))
            continue
        if len(hits) == 1:
            mapping[p] = hits[0]
            continue
        # Several candidates. If they all denote the SAME organism — two spellings
        # of one name, e.g. '(Linnaeus 1761)' and '(Linnaeus, 1761)' — then any of
        # them is the right target and the most frequent is the safest choice.
        # Only candidates that disagree with EACH OTHER are a real ambiguity.
        if all(species_match(a, b) for a, b in combinations(hits, 2)):
            # Prefer the candidate whose WORDS are closest to the prediction's:
            # a bare binomial should resolve to the same name plus an authority
            # (no word difference once the bracket is dropped) rather than to a
            # subspecies, which adds a word. Frequency in GT breaks remaining ties.
            pt = species_tokens(p)
            mapping[p] = min(hits, key=lambda g: (len(pt ^ species_tokens(g)),
                                                  -gt_counts[g], len(g)))
            continue
        unmapped.append(
            (p, f"matches {len(hits)} different organisms, cannot choose: "
                f"{', '.join(repr(h) for h in hits[:4])}"))

    if not mapping:
        return pred_rows, {}, unmapped
    out = []
    for r in pred_rows:
        nm = r.get("verbatimIdentification", "")
        if nm in mapping:
            r = {**r, "verbatimIdentification": mapping[nm]}
        out.append(r)
    return out, mapping, unmapped


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

    try:
        type_map, report = build_type_map(gt_types, pred_types, use_llm=use_llm,
                                          return_report=True)
    except TypeError:                     # older matcher without return_report
        type_map, report = build_type_map(gt_types, pred_types, use_llm=use_llm), {}

    # Say out loud what the matcher could NOT resolve, and why. A silently
    # failing LLM used to look identical to a confident "these are different
    # traits", which is how a name could read as near-identical in the coverage
    # table and as a 100% miss in the score with nothing to explain the gap.
    if report.get("llm_error"):
        print(f"  [semantic] LLM confirm pass unavailable ({report['llm_error']}) "
              f"— deterministic passes only")
    for p, g, why in report.get("llm_rejected", [])[:10]:
        print(f"  [semantic] left unmatched: {p!r} vs {g!r} ({why})")
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


def score_key_set(gt_rows, pred_rows, fields, decode, scope_sets=None):
    """Precision/recall/F1 for one scoring category.

    Uses the SAME matcher and the SAME scoping as the headline score, so a
    category row cannot disagree with the headline about what counts as a false
    positive. Without the scoping, a paper whose ground truth covers only some of
    the traits it mentions shows a low precision here and 1.000 above — the same
    prediction, two verdicts.

    Returns (p, r, f, (tp, fp_scoped, fn), fp_all): both precisions are available,
    the scoped one for the score and the raw one to show what was set aside.
    """
    matched, missing, extra = match_rows(gt_rows, pred_rows, fields, decode)
    in_scope = extra
    if scope_sets:
        in_scope, _out = partition_extra(extra, scope_sets, decode)
    tp, fn = len(matched), len(missing)
    p, r, f = prf(tp, len(in_scope), fn)
    return p, r, f, (tp, len(in_scope), fn), len(extra)


def _tag_coverage(matched, fields, decode):
    """Of the matched rows, how many actually had a value to agree ON for the
    fields this category adds?

    A category built from tags can be satisfied trivially: if GT and prediction
    are BOTH blank in a field, the key matches and nothing was verified. This
    reports the share of matched rows where at least one added field was
    populated on both sides, so an identical score between two categories can be
    read correctly — either the tags genuinely agree, or there were no tags.
    """
    core = set(KEY_SETS.get("core", []))
    added = [f for f in fields if f not in core]
    if not added or not matched:
        return None
    informative = 0
    for g, p in matched:
        if any(normalize_value(g.get(f, ""), decode)
               and normalize_value(p.get(f, ""), decode) for f in added):
            informative += 1
    return informative, len(matched), added


def print_key_set_scores(gt, pred, decode, names=None, scope_sets=None,
                         matched=None):
    """Score each active category side by side.

    Reading it: every category adds fields to the one before, and adding a field
    can only lose matches, so the DROP between two rows is attributable to the
    fields that were added — which is the number you want when deciding what to
    fix next.
    """
    names = names or ACTIVE_KEY_SETS
    print("\nSCORES BY CATEGORY")
    print(f"  {'category':<10} {'P':>6} {'R':>6} {'F1':>6}  {'TP':>5} {'FP':>5} {'FN':>5}   key")
    out = {}
    prev_f = None
    for name in names:
        fields = KEY_SETS.get(name)
        if not fields:
            print(f"  {name:<10} (unknown category — not in KEY_SETS)")
            continue
        p, r, f, (tp, fp, fn), fp_all = score_key_set(
            gt, pred, fields, decode, scope_sets)
        out[name] = (p, r, f)
        short = "+".join(_short_field(x) for x in fields)
        print(f"  {name:<10} {p:>6.3f} {r:>6.3f} {f:>6.3f}  {tp:>5} {fp:>5} {fn:>5}   {short}")
        if fp_all != fp:
            print(f"  {'':<10} ({fp_all - fp} more spurious row(s) set aside as "
                  f"out-of-scope; strict P would be {tp / (tp + fp_all):.3f})")
        if prev_f is not None:
            print(f"  {'':<10} (F1 {f - prev_f:+.3f} vs previous)")
        cov = _tag_coverage(matched, fields, decode) if matched else None
        if cov:
            informative, total, added = cov
            if informative < total:
                print(f"  {'':<10} note: only {informative}/{total} matched row(s) "
                      f"had any of {'/'.join(_short_field(a) for a in added)} "
                      f"populated on both sides — the rest agree by being empty")
        prev_f = f
    return out


def _short_field(f):
    """Compact field label for the key column of the score table."""
    return {"verbatimIdentification": "id", "measurementType": "type",
            "measurementValue": "value", "measurementStatistic": "stat",
            "basisOfRecord": "basis", "lifeStage": "stage"}.get(f, f)


def evaluate(pred_path, gt_path, key_fields, decode, semantic=False, use_llm=True,
             scope="measurementType", key_sets=None, match_species=True):
    gt = load_xlsx(gt_path)
    pred = load_csv(pred_path)

    type_map = {}
    if semantic:
        pred, type_map = remap_pred_types(gt, pred, use_llm=use_llm)

    # Taxon names are reconciled BEFORE matching, and before any diagnostic runs,
    # so the score and every breakdown below agree on which organism a row is
    # about (the same reason measurementType is remapped first).
    species_map, species_unmapped = {}, []
    if match_species:
        pred, species_map, species_unmapped = remap_pred_species(gt, pred)

    matched, missing, extra = match_rows(gt, pred, key_fields, decode)

    print("=" * 64)
    print(f"GROUND TRUTH : {gt_path}  ({len(gt)} rows)")
    print(f"PREDICTION   : {pred_path}  ({len(pred)} rows)")
    print(f"KEY          : {key_fields}   decode={decode}  semantic={semantic}")
    print(f"SCOPE        : {scope}")
    print("=" * 64)

    if species_map:
        print(f"\nTAXON NAME REMAP (pred -> gt, {len(species_map)} pair(s))")
        for p, g in sorted(species_map.items()):
            print(f"  {p!r} -> {g!r}")
    if species_unmapped:
        # Every predicted name left alone, and why. A silent non-match here reads
        # downstream as 'species not in prediction', which is a very different
        # diagnosis from 'the name was there but could not be paired'.
        print(f"\nTAXON NAMES LEFT UNMAPPED ({len(species_unmapped)})")
        for nm, why in sorted(species_unmapped):
            print(f"  {nm!r}: {why}")

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
    # Save the COMPLETE miss breakdown next to the prediction CSV (same folder,
    # same stem): <stem>_misses.csv and <stem>_misses_summary.json.
    from pathlib import Path as _Path
    detail_stem = str(_Path(pred_path).with_suffix("")) if pred_path else None
    print_failure_attribution(missing, pred, decode, detail_path=detail_stem)

    # --- measurementType coverage breakdown (very useful diagnostic) ---
    print_type_coverage(gt, pred, decode)

    # --- scores by category (modular; see KEY_SETS / ACTIVE_KEY_SETS) ---
    by_key_set = print_key_set_scores(gt, pred, decode, key_sets,
                                      scope_sets=scope_sets, matched=matched)

    return {
        "row": (p_sc, r_sc, f_sc),          # headline: scoped
        "row_strict": (p_all, r_all, f_all),
        "recall": r_all,
        "n_out_of_scope": len(out_of_scope),
        "n_in_scope_fp": fp_scoped,
        "fields": field_stats,
        "by_key_set": by_key_set,
        "species_map": species_map,
    }


F_ID, F_TYPE, F_VAL = "verbatimIdentification", "measurementType", "measurementValue"


def attribute_misses(missing, pred, decode):
    """Categorize every missed GT row by WHICH axis it failed on.

    A row is keyed on (species, type, value), so a miss failed on exactly one of
    those axes, and which one is computable:

        species absent from the prediction        -> species axis
        species there, that trait not extracted   -> trait axis
        species+trait there, value disagrees      -> value axis

    Returns a dict with the aggregate counters AND a complete per-row list, so
    both the console summary and the saved files draw from the same computation
    (no risk of the printed top-6 and the saved file disagreeing).
    """
    n = lambda r, f: normalize_value(r.get(f, ""), decode)

    pred_species = {n(r, F_ID) for r in pred}
    pred_types_of = defaultdict(set)          # species -> {types}
    pred_values_of = defaultdict(list)        # (species, type) -> [values]
    for r in pred:
        s, t = n(r, F_ID), n(r, F_TYPE)
        pred_types_of[s].add(t)
        pred_values_of[(s, t)].append(n(r, F_VAL))
    pred_valueset_of = {k: set(v) for k, v in pred_values_of.items()}

    causes = Counter()
    sub_value = Counter()      # (gt_value, pred_value) -> count  (TRUE mismatches)
    sub_species = Counter()    # gt_species -> count      (absent from pred)
    sub_trait = Counter()      # (species-less) gt_type -> count
    rows = []                  # one entry per missed row, fully attributed
    for r in missing:
        s, t, v = n(r, F_ID), n(r, F_TYPE), n(r, F_VAL)
        gid, gtype, gval = r.get(F_ID, ""), r.get(F_TYPE, ""), r.get(F_VAL, "")
        if s not in pred_species:
            causes["species not in prediction"] += 1
            sub_species[gid] += 1
            rows.append({"cause": "species not in prediction",
                         "verbatimIdentification": gid, "measurementType": gtype,
                         "measurementValue": gval, "pred_collision_value": ""})
        elif t not in pred_types_of[s]:
            causes["species present, trait missing"] += 1
            sub_trait[gtype] += 1
            rows.append({"cause": "species present, trait missing",
                         "verbatimIdentification": gid, "measurementType": gtype,
                         "measurementValue": gval, "pred_collision_value": ""})
        elif v in pred_valueset_of.get((s, t), ()):
            # The species, the trait, AND this exact value all exist in the
            # prediction — GT simply has more rows carrying it than the pipeline
            # reproduced (e.g. many specimens measured 0.01). This is a specimen-
            # count shortfall, NOT a value substitution; recording it as
            # '0.01 -> 0.01' made a decode ghost out of an extraction gap.
            causes["value present, extra GT copies not reproduced"] += 1
            rows.append({"cause": "value present, extra GT copies not reproduced",
                         "verbatimIdentification": gid, "measurementType": gtype,
                         "measurementValue": gval, "pred_collision_value": gval})
        else:
            causes["species+trait present, value differs"] += 1
            got = pred_values_of[(s, t)]
            pred_v = got[0] if got else ""
            sub_value[(v, pred_v)] += 1
            rows.append({"cause": "species+trait present, value differs",
                         "verbatimIdentification": gid, "measurementType": gtype,
                         "measurementValue": gval, "pred_collision_value": pred_v})

    return {"causes": causes, "sub_value": sub_value, "sub_species": sub_species,
            "sub_trait": sub_trait, "rows": rows, "pred_species": pred_species}


def _closest_pred_species(name, preds):
    """Best-matching predicted species name and its similarity, or ('', 0.0)."""
    best, score = "", 0.0
    for p in preds:
        sc = _type_sim(name, p)
        if sc > score:
            best, score = p, sc
    return best, score


def _deterministic_severity(row):
    """Cheap severity for the misses whose reason needs no model.

    Returns (severity, reasoning) or None to defer to the LLM. Only the clearest
    cases are decided here: a species genuinely absent with no near neighbour is
    severe; a value miss where prediction had nothing is a plain omission. The
    ambiguous ones — a value that is arguably the same thing worded differently —
    are what the LLM is for, so they return None.
    """
    cause = row.get("cause", "")
    gval = str(row.get("measurementValue", "")).strip()
    pval = str(row.get("pred_collision_value", "")).strip()
    if cause == "species not in prediction":
        return None                      # let the LLM judge vs the closest name
    if cause == "species present, trait missing":
        return ("moderate", "the trait was not extracted for this species")
    if cause == "species+trait present, value differs":
        if not pval:
            return ("moderate", "no value was predicted for this trait")
        # else defer: is the difference trivial (units/authority/wording) or real?
        return None
    return None


_SEVERITY_SYSTEM = (
    "You grade how SEVERE each extraction miss is, comparing what the ground "
    "truth expected to what the pipeline predicted for the SAME species and "
    "trait. You are grading severity only — you do NOT change any score.\n\n"
    "Severity levels:\n"
    "- trivial: same meaning, cosmetic difference only (a taxonomic authority or "
    "family in the predicted value, '(Lycosidae)', 'Uetz & Dondale 1979'; "
    "punctuation; units written differently; '±' spacing; 1 vs 1.0).\n"
    "- minor: same quantity/category but a small real difference (rounding, a "
    "unit conversion, a near-synonym).\n"
    "- moderate: related but not clearly the same (a different measure of the "
    "same structure, a partial value).\n"
    "- severe: wrong — a different species, a different trait, or an unrelated "
    "value (GT 'Coras montanus' vs pred 'Pardosa sp.').\n\n"
    "For each numbered item answer with its number, a severity, and a reason of "
    "at most 15 words. Answer ONLY JSON: "
    "{\"items\": [{\"n\": <int>, \"severity\": \"trivial|minor|moderate|severe\", "
    "\"reasoning\": \"...\"}]}"
)


def _assess_severity_batch(items, llm=None):
    """Grade one batch of deferred misses. `items` is a list of dicts with n,
    gt_value, pred_value, measurementType, gt_species. Returns {n: (sev, why)}."""
    lines = []
    for it in items:
        lines.append(
            f'{it["n"]}. species "{it["gt_species"]}", trait '
            f'"{it["measurementType"]}": ground truth = "{it["gt_value"]}", '
            f'predicted = "{it["pred_value"] or "(nothing)"}"')
    user = "Items:\n" + "\n".join(lines)
    try:
        content = (llm.invoke([{"role": "system", "content": _SEVERITY_SYSTEM},
                               {"role": "user", "content": user}]).content
                   if llm else
                   invoke_sized([{"role": "system", "content": _SEVERITY_SYSTEM},
                                 {"role": "user", "content": user}]))
        out = loads_salvaging(content)
    except Exception as e:
        print(f"  [severity] batch unavailable ({type(e).__name__}); left blank")
        return {}
    got = {}
    for entry in (out.get("items") or []) if isinstance(out, dict) else []:
        try:
            n = int(entry["n"])
        except (KeyError, TypeError, ValueError):
            continue
        sev = str(entry.get("severity", "")).strip().lower()
        if sev not in {"trivial", "minor", "moderate", "severe"}:
            continue
        got[n] = (sev, str(entry.get("reasoning", "")).strip()[:200])
    return got


def assess_miss_severity(rows, use_llm=True, batch_size=20):
    """Annotate each miss row with severity + reasoning IN PLACE.

    Never touches the score — this runs after matching, only to explain the
    misses. Deterministic labels are applied first (free); the ambiguous ones are
    batched to the LLM. If the LLM is unavailable, those rows get a blank severity
    and '(not assessed)', and everything still writes.
    """
    deferred = []
    for i, r in enumerate(rows):
        det = _deterministic_severity(r)
        if det is not None:
            r["severity"], r["reasoning"] = det
        else:
            r["severity"], r["reasoning"] = "", "(not assessed)"
            deferred.append(i)

    if not use_llm or invoke_sized is None or not deferred:
        return rows

    print(f"  [severity] assessing {len(deferred)} ambiguous miss(es) "
          f"in {(len(deferred) + batch_size - 1) // batch_size} batch(es)...")
    for start in range(0, len(deferred), batch_size):
        idxs = deferred[start:start + batch_size]
        items = [{"n": k,
                  "gt_species": rows[k].get("verbatimIdentification", ""),
                  "measurementType": rows[k].get("measurementType", ""),
                  "gt_value": rows[k].get("measurementValue", ""),
                  "pred_value": rows[k].get("pred_collision_value", "")}
                 for k in idxs]
        graded = _assess_severity_batch(items, llm=None)
        for k in idxs:
            if k in graded:
                rows[k]["severity"], rows[k]["reasoning"] = graded[k]
    return rows


def write_failure_details(attr, pred, path):
    """Write EVERY missed row (not just the printed top-6) to two files:

      <path>_misses.csv          one row per miss, tagged with its cause and,
                                 for species misses, the closest predicted name
      <path>_misses_summary.json the full untruncated counters (every value
                                 substitution, every absent species, every
                                 missing trait), most-frequent first

    `path` is a stem (no extension); the suffixes above are appended.
    """
    from pathlib import Path
    rows = attr["rows"]
    preds = sorted({r.get(F_ID, "") for r in pred})

    # cache closest-name lookup per distinct gt species (the expensive part).
    # Below the console's 0.55 threshold there is no plausible match, so store a
    # blank rather than a misleading low-scoring name.
    NEAR = 0.55
    closest = {}
    for r in rows:
        if r["cause"] == "species not in prediction":
            gid = r["verbatimIdentification"]
            if gid not in closest:
                best, score = _closest_pred_species(gid, preds)
                closest[gid] = (best, score) if score >= NEAR else ("", score)

    csv_path = f"{path}_misses.csv"
    # Annotate misses with severity + reasoning (score-neutral; see
    # assess_miss_severity). Controlled by the module flag so a batch run can turn
    # it off.
    assess_miss_severity(rows, use_llm=ASSESS_MISS_SEVERITY)
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=[
            "cause", "verbatimIdentification", "measurementType",
            "measurementValue", "pred_collision_value",
            "closest_pred_species", "closest_score",
            "severity", "reasoning"])
        w.writeheader()
        for r in rows:
            best, score = ("", "")
            if r["cause"] == "species not in prediction":
                b, s = closest.get(r["verbatimIdentification"], ("", 0.0))
                best, score = b, f"{s:.2f}"
            w.writerow({**r, "closest_pred_species": best, "closest_score": score,
                        "severity": r.get("severity", ""),
                        "reasoning": r.get("reasoning", "")})

    summary = {
        "total_missed": len(rows),
        "causes": dict(attr["causes"]),
        "value_substitutions": [
            {"gt": g, "pred": p, "count": c}
            for (g, p), c in attr["sub_value"].most_common()],
        "species_absent": [
            {"gt_species": name, "count": c,
             "closest_pred_species": closest.get(name, ("", 0.0))[0],
             "closest_score": round(closest.get(name, ("", 0.0))[1], 3)}
            for name, c in attr["sub_species"].most_common()],
        "traits_missing": [
            {"measurementType": name, "count": c}
            for name, c in attr["sub_trait"].most_common()],
    }
    json_path = f"{path}_misses_summary.json"
    Path(json_path).write_text(json.dumps(summary, indent=2, ensure_ascii=False),
                               encoding="utf-8")
    print(f"\n  full miss detail saved -> {Path(csv_path).name}, "
          f"{Path(json_path).name} ({len(rows)} row(s))")


def print_failure_attribution(missing, pred, decode, top=6, detail_path=None):
    """Say WHY each missed row missed, instead of printing rows to eyeball.

    The console shows the dominant pattern on each axis (top `top`) and a verdict
    line answering "is this one bug or a hundred?". If `detail_path` is given, the
    COMPLETE, untruncated breakdown is also saved via write_failure_details.

    Every zero-score paper investigated by hand so far turned out to be ONE
    systematic substitution repeated N times ('predator'->'Carnivorous' x43,
    'Yes'->'macropterous' x87, 'Aphaenogaster ashmeadi' vs the same name with a
    footnote asterisk), so the verdict percentage answers whether it's systematic.
    """
    if not missing:
        return
    attr = attribute_misses(missing, pred, decode)
    causes = attr["causes"]
    sub_value, sub_species, sub_trait = (attr["sub_value"], attr["sub_species"],
                                         attr["sub_trait"])

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
            best, score = _closest_pred_species(name, preds)
            near = (f"  ~{score:.2f}~  pred {best!r}" if score >= 0.55
                    else "   (nothing similar in the prediction)")
            print(f"     gt {name!r:34}{near}   x{c}")
        verdict("species mismatch", "species mismatches", sub_species)

    if sub_trait:
        print(f"\n  TRAITS THE SPECIES HAS IN GT BUT NOT IN PREDICTION:")
        for name, c in sub_trait.most_common(top):
            print(f"     {name!r:34} x{c}")
        verdict("missing trait", "missing traits", sub_trait)

    # Everything above is truncated to `top`. Save the COMPLETE breakdown too.
    if detail_path:
        write_failure_details(attr, pred, detail_path)


def print_type_coverage(gt, pred, decode, sim_threshold=0.55):
    """measurementType coverage — a VIEW OF THE SCORE, never a second opinion.

    This table used to run its own similarity pass and merge any GT/pred pair
    scoring above 0.55 onto one row joined by 'or'. Because the scorer used a
    different rule, a trait could read as fully covered here and as a 100% miss
    three lines earlier in the failure breakdown — the same names, two verdicts.

    Now `pred` arrives ALREADY REMAPPED by the semantic matcher, so any pair the
    scorer accepted has the same string on both sides and lands on one row by
    construction. Nothing is merged here. What used to be silently merged is
    listed separately as UNRESOLVED NEAR-MISSES: names that look alike but were
    NOT credited, which is the actionable list — either the matcher needs a rule
    for them or they really are different traits.

    (Similarity is still used, but only to decide what to SHOW in that section.
    It never affects a count.)
    """
    gt_types = Counter(normalize_value(r["measurementType"], decode) for r in gt)
    pred_types = Counter(normalize_value(r["measurementType"], decode) for r in pred)

    rows = []          # (sort_key, label, gt, pred, note)
    for t in set(gt_types) | set(pred_types):
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

    # Near-misses the matcher did NOT accept — shown as unresolved, not merged.
    gt_only = [t for t in gt_types if not pred_types.get(t)]
    pred_only = [t for t in pred_types if not gt_types.get(t)]
    near = sorted(((_type_sim(g, p), g, p) for g in gt_only for p in pred_only),
                  reverse=True)
    seen_g, seen_p, shown = set(), set(), []
    for s, g, p in near:
        if s < sim_threshold or g in seen_g or p in seen_p:
            continue
        seen_g.add(g); seen_p.add(p); shown.append((s, g, p))
    if shown:
        print("\n  UNRESOLVED NEAR-MISSES (similar wording, NOT credited — these "
              "cost you both a miss and a spurious row)")
        for s, g, p in shown[:15]:
            print(f"    gt {g!r:34} vs pred {p!r:34} sim={s:.2f}")


def _metrics_from_report(report_path):
    """Recover (precision, recall, f1) from a saved <paper>_report.txt.

    The report is the stdout of evaluate(), which prints the headline scoped
    score as 'SCOPED  P/R/F1 : p / r / f' — the same triple stored in
    summary.csv. Lets --skip-existing reuse a finished paper's score straight
    from its report, so skipping works even when summary.csv is missing or stale
    (e.g. after an interrupted batch). Returns None if the file is unreadable or
    the line isn't found (older/different report format), so the caller falls
    back to re-evaluating rather than inventing a number.
    """
    try:
        text = Path(report_path).read_text(encoding="utf-8")
    except OSError:
        return None
    m = re.search(r"SCOPED\s+P/R/F1\s*:\s*"
                  r"([0-9.]+)\s*/\s*([0-9.]+)\s*/\s*([0-9.]+)", text)
    if not m:
        return None
    try:
        return float(m.group(1)), float(m.group(2)), float(m.group(3))
    except ValueError:
        return None


def _load_prior_summary(summary_path):
    """Read an existing summary.csv into {paper: row}, or {} if absent/unreadable.

    Used by --skip-existing to carry a skipped paper's already-computed metrics
    forward, so skipping a paper does not drop it from the rewritten summary.csv
    (or from the mean-F1 line).
    """
    if not Path(summary_path).exists():
        return {}
    prior = {}
    try:
        with open(summary_path, "r", newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                paper = row.get("paper")
                if paper:
                    prior[paper] = row
    except (OSError, csv.Error):
        return {}
    return prior


def evaluate_all(papers_root, output_root, key_fields, decode, *,
                 semantic=True, use_llm=True, scope="measurementType",
                 key_sets=None, match_species=True, skip_existing=False):
    """Re-run evaluation over every already-extracted paper (no pipeline).

    For each output/<paper>/<paper>.csv, find the matching ground-truth xlsx in
    that paper's SOURCE folder, evaluate, write <paper>_report.txt (+ the
    *_misses* files), and collect a per-paper row. Rewrites <output>/summary.csv.

    Mirrors run_all.py's evaluation step, so its numbers match summary.csv.

    skip_existing: when True, a paper that already has a <paper>_report.txt AND a
    row in the current summary.csv is left untouched — its prior metrics are
    carried forward into the rewritten summary and no evaluation (and no LLM
    call) runs for it. A paper whose report is missing, or that has no prior
    summary row to reuse, is always (re-)evaluated, so the summary can never end
    up with a skipped-but-scoreless paper. Papers whose prior status was not
    'ok' (e.g. a past FAIL or no_ground_truth) are also retried rather than
    skipped.
    """
    from mineru_extract import classify_folder   # lazy: only --all needs it

    papers_root, output_root = Path(papers_root), Path(output_root)
    if not output_root.is_dir():
        raise SystemExit(f"output dir not found: {output_root.resolve()}")

    papers = sorted(d.name for d in output_root.iterdir()
                    if d.is_dir() and (d / f"{d.name}.csv").exists())
    if not papers:
        raise SystemExit(f"no paper CSVs found under {output_root}")

    # For --skip-existing: prior metrics to carry forward for untouched papers.
    prior_summary = _load_prior_summary(output_root / "summary.csv") \
        if skip_existing else {}

    print(f"Re-evaluating {len(papers)} paper(s) under {output_root}  "
          f"(semantic={semantic}, use_llm={use_llm}, decode={decode}, "
          f"skip_existing={skip_existing})\n")

    def ground_truth_for(paper):
        folder = papers_root / paper
        if not folder.is_dir():
            return None
        try:
            _, results_path, _ = classify_folder(folder)
        except Exception:
            return None
        return str(results_path) if results_path else None

    summary = []
    n_skipped = 0
    for paper in papers:
        out_csv = output_root / paper / f"{paper}.csv"
        report = output_root / paper / f"{paper}_report.txt"

        # --skip-existing: a paper counts as done when its <paper>_report.txt
        # exists — that is the artifact a finished evaluation leaves behind. The
        # score for the rewritten summary.csv is recovered without re-running:
        # first from an 'ok' row in the OLD summary.csv (fast, exact), else parsed
        # from the report itself. Keying on the report (not summary.csv) is what
        # makes this resume an interrupted batch: after a stop, the reports of
        # finished papers exist even though summary.csv was never written. Only if
        # NEITHER source yields a score do we fall through and re-evaluate, so a
        # skipped paper can never land in summary.csv without its numbers.
        if skip_existing and report.exists():
            prev = prior_summary.get(paper)
            if prev and prev.get("status") == "ok":
                summary.append(prev)
                n_skipped += 1
                print(f"  SKIP {paper:<28} already evaluated "
                      f"(P/R/F1 = {prev.get('precision','')}/"
                      f"{prev.get('recall','')}/{prev.get('f1','')})  [summary]")
                continue
            m = _metrics_from_report(report)
            if m:
                p, r, f = m
                summary.append({"paper": paper, "precision": round(p, 3),
                                "recall": round(r, 3), "f1": round(f, 3),
                                "status": "ok"})
                n_skipped += 1
                print(f"  SKIP {paper:<28} already evaluated "
                      f"(P/R/F1 = {p:.3f}/{r:.3f}/{f:.3f})  [report]")
                continue
            # report exists but no score recoverable -> re-evaluate below.
            print(f"  ...  {paper:<28} report present but score unreadable; "
                  f"re-evaluating")

        try:
            gt = ground_truth_for(paper)
            if not gt or not Path(gt).exists():
                print(f"  SKIP {paper}: no ground-truth xlsx")
                summary.append({"paper": paper, "precision": "", "recall": "",
                                "f1": "", "status": "no_ground_truth"})
                continue
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                metrics = evaluate(str(out_csv), gt, key_fields, decode,
                                   semantic=semantic, use_llm=use_llm, scope=scope,
                                   key_sets=key_sets, match_species=match_species)
            report.write_text(buf.getvalue(), encoding="utf-8")
            p, r, f = metrics["row"]
            print(f"  OK   {paper:<28} P/R/F1 = {p:.3f}/{r:.3f}/{f:.3f}"
                  f"  -> {report.name}")
            summary.append({"paper": paper, "precision": round(p, 3),
                            "recall": round(r, 3), "f1": round(f, 3),
                            "status": "ok"})
        except Exception as e:
            print(f"  FAIL {paper}: {e}")
            traceback.print_exc()
            summary.append({"paper": paper, "precision": "", "recall": "",
                            "f1": "", "status": f"FAIL: {e}"})

    summary_path = output_root / "summary.csv"
    with open(summary_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["paper", "precision", "recall",
                                           "f1", "status"])
        w.writeheader()
        w.writerows(summary)

    ok = [s for s in summary if s["status"] == "ok"]
    # Rows carried forward by --skip-existing come from the CSV as strings; the
    # freshly-evaluated rows hold floats. Coerce so the mean covers both.
    def _f1(s):
        try:
            return float(s["f1"])
        except (TypeError, ValueError):
            return None
    f1s = [v for v in (_f1(s) for s in ok) if v is not None]
    print("\n" + "=" * 70)
    done = f"DONE. {len(summary)} paper(s)."
    if skip_existing:
        done += f" ({n_skipped} skipped, {len(summary) - n_skipped} evaluated)"
    print(f"{done} Summary -> {summary_path}")
    if f1s:
        print(f"Scored {len(f1s)} paper(s); mean F1 = {sum(f1s) / len(f1s):.3f}")
    print("=" * 70)
    return summary


# Defaults for --all mode; kept in sync with run_all.py.
DEFAULT_PAPERS = "../data/un_processed_papers"
DEFAULT_OUTPUT = "../output"


def _paper_ground_truth(paper, papers_root):
    """Locate a paper's ground-truth xlsx from its SOURCE folder — the same way
    --all does (classify_folder picks the results spreadsheet). Returns a path
    string, or None if the folder or the spreadsheet is missing."""
    from mineru_extract import classify_folder   # lazy: only paper modes need it
    folder = Path(papers_root) / paper
    if not folder.is_dir():
        return None
    try:
        _, results_path, _ = classify_folder(folder)
    except Exception:
        return None
    return str(results_path) if results_path else None


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Evaluate a prediction CSV against ground truth, or --all "
                    "to re-evaluate every already-extracted paper.")
    ap.add_argument("pred", nargs="?",
                    help="prediction CSV, OR just a paper name (resolves "
                         "<--output>/<paper>/<paper>.csv and its ground-truth "
                         "xlsx automatically)")
    ap.add_argument("gt", nargs="?", help="ground-truth xlsx (omit when the "
                                          "first argument is a paper name)")
    ap.add_argument("--all", action="store_true",
                    help="batch mode: re-evaluate every output/<paper>/<paper>.csv "
                         "against its ground-truth xlsx and rewrite summary.csv "
                         "(ignores the pred/gt positionals)")
    ap.add_argument("--papers", default=DEFAULT_PAPERS,
                    help="[--all] papers source root, for locating ground-truth xlsx")
    ap.add_argument("--output", default=DEFAULT_OUTPUT,
                    help="[--all] output root holding <paper>/<paper>.csv")
    ap.add_argument("--decode", action="store_true",
                    help="apply legend code -> term decoding before comparison")
    ap.add_argument("--key", nargs="+", default=DEFAULT_KEY,
                    help="columns that identify a row for matching")
    ap.add_argument("--semantic-types", action="store_true",
                    help="remap predicted measurementType names onto the "
                         "ground-truth wording for the same trait before matching")
    ap.add_argument("--no-semantic", action="store_true",
                    help="[--all] disable semantic remapping (on by default in "
                         "--all, to match the pipeline / summary.csv)")
    ap.add_argument("--scope", default="measurementType", choices=SCOPE_CHOICES,
                    help="which predicted rows GT is entitled to judge. "
                         "'measurementType' (default): a row whose trait GT never "
                         "records is out-of-scope, not a false positive. "
                         "'none': strict, every extra row is a false positive.")
    ap.add_argument("--no-llm", action="store_true",
                    help="with semantic remapping, use the deterministic pass only "
                         "(no Ollama calls)")
    ap.add_argument("--key-sets", nargs="+", default=None,
                    metavar="NAME",
                    help=f"which scoring categories to report. Available: "
                         f"{', '.join(KEY_SETS)} (default: {', '.join(ACTIVE_KEY_SETS)}). "
                         f"Edit KEY_SETS in evaluate.py to add your own.")
    ap.add_argument("--no-species-match", action="store_true",
                    help="require verbatimIdentification to match exactly, instead "
                         "of treating names with extra classification words "
                         "(subgenus/family/suborder) or an abbreviated genus as equal")
    ap.add_argument("--skip-existing", action="store_true",
                    help="[--all] skip any paper that already has a "
                         "<paper>_report.txt and an 'ok' row in summary.csv; its "
                         "prior score is carried forward. Papers with no report or "
                         "no reusable score are still evaluated. Use to resume an "
                         "interrupted batch without redoing finished papers.")
    args = ap.parse_args()

    if args.all:
        # In batch mode semantic remapping is ON by default (matches run_all.py);
        # --no-semantic turns it off.
        evaluate_all(args.papers, args.output, args.key, args.decode,
                     semantic=not args.no_semantic, use_llm=not args.no_llm,
                     scope=args.scope, key_sets=args.key_sets,
                     match_species=not args.no_species_match,
                     skip_existing=args.skip_existing)
    else:
        # Two single-paper modes:
        #   python evaluate.py PAPER             -> resolve CSV + GT from the
        #       standard dirs (--output / --papers), evaluate, write the report.
        #       Mirrors --all for one paper (semantic ON unless --no-semantic);
        #       does NOT rewrite the aggregate summary.csv.
        #   python evaluate.py PRED.csv GT.xlsx  -> explicit paths (original;
        #       semantic OFF unless --semantic-types).
        if args.pred and not args.gt:
            paper = args.pred
            out_csv = Path(args.output) / paper / f"{paper}.csv"
            if not out_csv.exists():
                ap.error(f"no prediction CSV for '{paper}': {out_csv} not found. "
                         f"Give a paper name (resolved under --output "
                         f"{args.output}) or explicit PRED.csv GT.xlsx paths.")
            gt = _paper_ground_truth(paper, args.papers)
            if not gt or not Path(gt).exists():
                ap.error(f"found {out_csv} but no ground-truth xlsx for '{paper}' "
                         f"under {Path(args.papers) / paper} — is the source "
                         f"folder present in --papers?")
            print(f"Evaluating '{paper}'\n  pred: {out_csv}\n  gt:   {gt}\n")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                metrics = evaluate(str(out_csv), gt, args.key, args.decode,
                                   semantic=not args.no_semantic,
                                   use_llm=not args.no_llm, scope=args.scope,
                                   key_sets=args.key_sets,
                                   match_species=not args.no_species_match)
            report = Path(args.output) / paper / f"{paper}_report.txt"
            report.write_text(buf.getvalue(), encoding="utf-8")
            print(buf.getvalue())
            p, r, f = metrics["row"]
            print(f"  -> P/R/F1 = {p:.3f}/{r:.3f}/{f:.3f}   report: {report}")
        elif not args.pred or not args.gt:
            ap.error("give a paper name, or PRED.csv and GT.xlsx, or --all")
        else:
            evaluate(args.pred, args.gt, args.key, args.decode,
                     semantic=args.semantic_types, use_llm=not args.no_llm,
                     scope=args.scope, key_sets=args.key_sets,
                     match_species=not args.no_species_match)