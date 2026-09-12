"""
evaluate.py — compare a pipeline output CSV against a volunteer ground-truth xlsx.

Reimagined for SPEED and for the fact that the three things a row is keyed on —
the species name, the measurementType, and the (often categorical) value — are
frequently the SAME fact written two different ways. The old evaluator matched
species well but leaned on an LLM for trait names and did almost no fuzzy matching
on values. This version:

  * does every fuzzy comparison on DISTINCT STRINGS, not on rows. For each axis we
    map each distinct PREDICTED string onto the ground-truth string that means the
    same thing (GT is the fixed vocabulary; we only ever rewrite pred toward it,
    never merge GT with itself). Fuzzy work is then O(distinct^2) — a few hundred
    strings — and the row match is a hash-join on canonical keys, which is O(rows).
    That is the whole speed story: no per-pair LLM calls, no O(rows^2) scan.

  * matches all three axes with a graduated, transparent, DETERMINISTIC ladder,
    cheapest test first, so the great majority of equivalences are caught with
    string/token math and nothing else:

      species   token-set with abbreviation + one-char OCR-typo tolerance
                ('A. vilhenae' == 'Andrena vilhenae'; 'Atenius' == 'Ataenius')
      type      normalize (units/casing/word-order) -> token containment ->
                token-Jaccard -> character ratio
                ('Body size' == 'Body Length'? no; 'Diurnal_activity' ==
                'diurnal activity'? yes; 'mean tongue length' == 'tongue length'? yes)
      value     numeric fold ('4.0' == '4') -> exact -> initialism/abbreviation
                ('W' == 'Wood', 'LDW' == 'lying dead wood', 'W/S' == 'wood/soil
                interface') -> token-subset -> OCR-typo -> token-Jaccard

  * treats GENUINE synonyms ('predator' ~ 'carnivorous', 'diurnal' ~ 'active by
    day') — which no cheap string rule can catch — with an OPTIONAL local embedding
    model (sentence-transformers, one batched forward pass, offline, deterministic).
    It is a guarded import: absent or disabled, the evaluator runs deterministic-
    only and says so. Enable with --embed. There is NO LLM in the matching path.

  * is HONEST about what it did. Every species/type remap is printed (they are
    distinct-level, so the list is short); fuzzy VALUE matches are counted by rule
    and sampled, so an inflated score can always be audited. --strict-values turns
    categorical value fuzziness off entirely (numeric fold + exact only).

What is kept from the previous design because it was right: numeric-aware value
folding (Decimal, not float), scoped precision (a predicted row for a trait GT
never records is OUT-OF-SCOPE, not a false positive), per-field accuracy on
matched rows, and miss attribution by axis (species / trait / value) with a
"one bug or a hundred?" verdict. The saved *_misses_summary.json schema is
unchanged, so collect_misses.py keeps working; evaluate()/evaluate_all() keep
their signatures and return shapes, so run_all.py and check_sync.py keep working.

Usage
-----
    python evaluate.py output.csv GT.xlsx
    python evaluate.py output.csv GT.xlsx --embed          # semantic value/type layer
    python evaluate.py output.csv GT.xlsx --strict-values  # no categorical fuzz
    python evaluate.py output.csv GT.xlsx --num-tol 0.02   # 2% numeric tolerance
    python evaluate.py PAPER                                # resolve CSV+GT from dirs
    python evaluate.py --all                                # re-score every paper
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import io
import json
import re
import traceback
import unicodedata
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher
from itertools import combinations
from pathlib import Path

import openpyxl


# ===========================================================================
# Template columns & scoring configuration
# ===========================================================================

COLUMNS = [
    "basisOfRecord", "verbatimIdentification", "measurementType",
    "measurementMethod", "measurementValue", "measurementUnit",
    "measurementStatistic", "measurementRemarks", "sex", "lifeStage",
    "caste", "sampleSizeValue", "sampleSizeUnit", "sampleTreatment",
    "samplingProtocol", "verbatimLocality", "verbatimCoordinates",
    "verbatimEventDate", "associatedOccurrences", "associatedReferences",
    "externalLink",
]

# The identity of a row for matching: which trait of which species, and its value.
DEFAULT_KEY = ["verbatimIdentification", "measurementType", "measurementValue"]

F_ID, F_TYPE, F_VAL = "verbatimIdentification", "measurementType", "measurementValue"

# Scoring categories reported side by side. Adding a field can only lower a score
# (more must agree), so the drop between rows tells you which field costs you.
KEY_SETS = {
    "core": ["verbatimIdentification", "measurementType", "measurementValue"],
    "tags": ["basisOfRecord", "verbatimIdentification", "measurementType",
             "measurementValue", "measurementStatistic", "sex", "lifeStage"],
}
ACTIVE_KEY_SETS = ["core", "tags"]

SCOPE_CHOICES = ["none", "measurementType", "measurementType+verbatimIdentification"]

# LLM severity grading is OFF by default (this evaluator has no LLM in its hot
# path). A deterministic severity is always computed (free, score-neutral). Set
# True (or pass --llm-severity) only if you want the ambiguous misses LLM-graded.
ASSESS_MISS_SEVERITY = False

# --- fuzzy-match thresholds (tune here) ------------------------------------
# Deliberately conservative: it is worse to invent a false match (which silently
# inflates the score) than to miss a fuzzy one (which shows up as a miss you can
# read). Every threshold is a floor a pair must clear to be called equivalent.
TYPE_JACCARD = 0.60      # token overlap for measurementType names
TYPE_RATIO = 0.90        # char ratio on the token-sorted key (typo-level)
TYPE_EMBED = 0.72        # cosine, only if --embed
VALUE_JACCARD = 0.70     # values are shorter -> stricter than types
VALUE_EMBED = 0.78       # cosine, only if --embed
OCR_MIN_LEN = 6          # min token length for a one-char OCR-typo match

# Optional, opt-in (--decode): legend code -> the term volunteers tend to write.
# The initialism matcher below generalises most of these without a table, but a
# curated map still helps for non-initialism codes.
VALUE_DECODE = {
    "w": "wood", "s": "soil", "w/s": "wood/soil interface", "p": "polyphagous",
    "m": "mound", "h": "hypogeal", "a": "arboreal",
    "m(o)": "found in mounds of other termites",
    "ldw": "lying dead wood", "sdw": "standing dead wood", "b": "bait",
}


# ===========================================================================
# Normalization
# ===========================================================================

_FOOTNOTE = re.compile(r"[†‡§¶\uFFFD]")


def normalize_header(h):
    """Strip nbsp, footnote markers and surrounding whitespace from a header."""
    if h is None:
        return ""
    h = str(h).replace("\xa0", " ")
    h = _FOOTNOTE.sub("", h)
    return h.strip()


def canonical_number(s):
    """Canonical spelling of a numeric string, or None if it isn't a number.

    The pred side reads '4.0' verbatim out of the paper; the volunteer typed 4,
    openpyxl returns int 4, str() gives '4'. Same measurement, two spellings, no
    string compare can join them. Decimal (exact) with 'f' format (never
    exponential): Decimal('2.40').normalize() == Decimal('2.4'); a big integer
    stays written out instead of flipping to '1.23e+06'. 'nan'/'inf' are NOT
    numbers here — such a cell is a literal string and compares as one.
    """
    try:
        d = Decimal(str(s))
    except (InvalidOperation, ValueError, TypeError):
        return None
    if not d.is_finite():
        return None
    d = d.normalize()
    if d.as_tuple().exponent > 0:
        d = d.quantize(Decimal(1))
    return format(d, "f")


def normalize_value(v, decode=False):
    """Normalize a cell for comparison: NFKC, strip footnote/replacement chars and
    nbsp, collapse whitespace, lowercase, fold numeric spelling. Optionally decode
    legend codes. Comparison only — the CSV keeps the verbatim value."""
    if v is None:
        return ""
    s = unicodedata.normalize("NFKC", str(v))
    s = _FOOTNOTE.sub("", s).replace("\xa0", " ")
    s = re.sub(r"\s+", " ", s).strip().lower()
    if decode and s in VALUE_DECODE:
        s = VALUE_DECODE[s]
    n = canonical_number(s)
    return n if n is not None else s


# ===========================================================================
# Loading
# ===========================================================================

def load_csv(path):
    with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        raw_to_canon = {c: normalize_header(c) for c in (reader.fieldnames or [])}
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
    if not all_rows:
        return []
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


# ===========================================================================
# Species matching (deterministic; token-set with abbreviation + OCR-typo)
# ===========================================================================
# Volunteers and the pipeline write the same organism differently, but the
# difference is almost never in the WORDS — it is extra classification tokens, a
# duplicated genus, an authority, or an abbreviated genus. So names are compared
# as SETS OF WORDS: an anagram or near-spelling is not a match, the same words
# plus a family name is.

_RANK_SUFFIX = re.compile(r"(idae|inae|aceae|oidea|ptera|formes|morpha|ales)$")
_TAXON_NOISE = {
    "sp", "spp", "ssp", "subsp", "var", "cf", "aff", "nr", "morph",
    "complex", "group", "sensu", "lato", "stricto", "indet", "unknown",
    "undetermined", "nov", "novum", "et", "al",
}


def species_tokens(name) -> frozenset:
    """Identifying words of a taxon name, lowercased, order-independent. Drops
    parentheticals/sample sizes, un-glues 'epithetAuthor' and run-on 'sp. nov.',
    splits on punctuation, removes rank words and qualifiers, de-duplicates."""
    s = unicodedata.normalize("NFKD", str(name or "")).encode("ascii", "ignore").decode()
    s = re.sub(r"\([^)]*\)", " ", s)
    s = re.sub(r"\bn\s*=\s*\d+", " ", s, flags=re.I)
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", s)          # eickstedtaeSchlinger -> two
    s = re.sub(r"([a-z]{3,})(sp{1,2}\.?\s*nov)", r"\1 \2", s, flags=re.I)
    s = s.lower()
    toks = [t for t in re.split(r"[^a-z0-9]+", s) if t]
    kept, ranks = set(), set()
    for t in toks:
        if t in _TAXON_NOISE or t.isdigit():
            continue
        if len(t) > 3 and _RANK_SUFFIX.search(t):
            ranks.add(t)
            continue
        kept.add(t)
    return frozenset(kept or ranks)          # keep rank word if it's all there is


def _edit_distance_le1(a: str, b: str) -> bool:
    """True iff a and b are within one insertion/deletion/substitution."""
    if a == b:
        return True
    la, lb = len(a), len(b)
    if abs(la - lb) > 1:
        return False
    if la == lb:
        return sum(x != y for x, y in zip(a, b)) == 1
    short, long = (a, b) if la < lb else (b, a)
    i = j = edits = 0
    while i < len(short) and j < len(long):
        if short[i] == long[j]:
            i += 1; j += 1
        else:
            edits += 1
            if edits > 1:
                return False
            j += 1
    return True


def _ocr_typo_ok(ta: frozenset, tb: frozenset) -> bool:
    """Names identical except one one-character OCR slip in one token (>=6 chars)."""
    common = ta & tb
    da, db = ta - common, tb - common
    if len(da) != 1 or len(db) != 1:
        return False
    wa, wb = next(iter(da)), next(iter(db))
    if len(wa) < OCR_MIN_LEN or len(wb) < OCR_MIN_LEN:
        return False
    return _edit_distance_le1(wa, wb)


def species_match(a, b) -> bool:
    """Do two taxon names denote the same organism? One name's words all present
    in the other's (extra words tolerated), with guards: a one-word name must
    match exactly; a single-letter word may stand for a longer word beginning with
    it; otherwise every word matches exactly. Plus an OCR-typo pass."""
    ta, tb = species_tokens(a), species_tokens(b)
    if not ta or not tb:
        return False
    if ta == tb:
        return True
    small, large = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
    if len(small) < 2:
        return False
    if small <= large:
        return True

    def _abbrev_ok(x, y):
        missing, extra = x - y, y - x
        if len(missing) != 1 or not extra:
            return False
        m = next(iter(missing))
        return len(m) == 1 and any(e.startswith(m) for e in extra)

    if _abbrev_ok(ta, tb) or _abbrev_ok(tb, ta):
        return True
    return _ocr_typo_ok(ta, tb)


# ===========================================================================
# Generic string helpers (types & values)
# ===========================================================================

_UNIT_PAREN = re.compile(
    r"\((?:[^()]*\b(?:mm|cm|m|km|g|kg|mg|mm2|cm2|m2|ml|l|°c|°f|%|n|df|"
    r"count|ratio|index)\b[^()]*)\)", re.I)
_TYPE_STOP = {
    "recorded", "the", "of", "in", "on", "a", "an", "as", "at", "and", "or",
    "stage", "state", "development", "evaluated", "sources", "mean", "value",
}


def type_key(name: str) -> str:
    """Aggressive canonical form for a measurementType: strip accents & unit
    parentheticals, split camelCase, drop punctuation and stopwords, sort tokens
    so word-order and casing differences collapse. Used for equivalence + display
    clustering, never written out."""
    s = unicodedata.normalize("NFKD", str(name or "")).encode("ascii", "ignore").decode()
    s = s.lower().strip()
    s = _UNIT_PAREN.sub(" ", s)
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    toks = [t for t in s.split() if t and t not in _TYPE_STOP]
    return " ".join(sorted(toks))


def _token_set(s: str) -> set:
    return {t for t in re.split(r"[^a-z0-9]+", str(s).lower()) if t}


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _initialism(short: str, long: str) -> bool:
    """True if `short` is a plausible initialism/abbreviation of `long`:
    'w'->'wood' (prefix of the single word), 'ldw'->'lying dead wood' (initials),
    'ws'->'wood soil interface' (leading initials). Directional; call both ways."""
    sc = re.sub(r"[^a-z0-9]", "", short.lower())
    lw = re.findall(r"[a-z0-9]+", long.lower())
    if not sc or not lw or len(sc) > 5 or " " in short.strip():
        return False
    if len(long) < len(short):
        return False
    if len(sc) == 1:
        return lw[0].startswith(sc)                  # 'w' -> 'wood'
    lead = "".join(w[0] for w in lw[:len(sc)])
    full = "".join(w[0] for w in lw)
    return sc == lead or sc == full                  # 'ldw'/'ws' -> initials


# ===========================================================================
# Optional embedding layer (semantic synonyms; guarded, off by default)
# ===========================================================================

class Embedder:
    """Thin wrapper over a local sentence-transformers model. Encodes lazily and
    caches by string; sim() is a cosine on unit-normalized vectors."""

    def __init__(self, model_name="all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer      # lazy import
        self._model = SentenceTransformer(model_name)
        self._cache = {}

    def warm(self, strings):
        """Batch-encode a set of strings up front (one forward pass) so later
        sim() calls are pure dot products."""
        todo = sorted({str(s) for s in strings if str(s).strip()
                       and str(s) not in self._cache})
        if not todo:
            return
        vecs = self._model.encode(todo, normalize_embeddings=True,
                                  batch_size=256, show_progress_bar=False)
        for s, v in zip(todo, vecs):
            self._cache[s] = v

    def _vec(self, s):
        s = str(s)
        if s not in self._cache:
            self._cache[s] = self._model.encode([s], normalize_embeddings=True)[0]
        return self._cache[s]

    def sim(self, a, b) -> float:
        if not str(a).strip() or not str(b).strip():
            return 0.0
        va, vb = self._vec(a), self._vec(b)
        return float(sum(x * y for x, y in zip(va, vb)))


def make_embedder(enabled: bool):
    if not enabled:
        return None
    try:
        e = Embedder()
        print("  [embed] sentence-transformers loaded — semantic value/type "
              "matching ON")
        return e
    except Exception as ex:
        print(f"  [embed] unavailable ({type(ex).__name__}: {ex}); "
              f"deterministic matching only")
        return None


# ===========================================================================
# Axis equivalence predicates
# ===========================================================================

def type_equiv(a, b, embedder=None, semantic=True) -> bool:
    """Do two measurementType names denote the same trait? Cheapest test first."""
    ka, kb = type_key(a), type_key(b)
    if not ka or not kb:
        return False
    if ka == kb:                                         # casing/units/word-order
        return True
    if not semantic:
        return False
    ta, tb = set(ka.split()), set(kb.split())
    if ta and tb:
        small, large = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
        if small and small <= large:                    # qualified form of the other
            return True
        if _jaccard(ta, tb) >= TYPE_JACCARD:
            return True
    if _ratio(ka, kb) >= TYPE_RATIO:                     # typo-level
        return True
    if embedder is not None and embedder.sim(a, b) >= TYPE_EMBED:
        return True
    return False


def value_equiv(gv, pv, decode=False, embedder=None, semantic=True,
                num_tol=0.0) -> str:
    """Do two values match? Returns the RULE that matched ('exact','numeric',
    'initialism','subset','typo','jaccard','embed') or '' if none — the rule is
    kept so fuzzy matches can be counted and audited.

    Numeric stays strict: two numbers that differ (beyond num_tol) never match,
    and a number never matches a non-number. Categorical fuzziness is skipped
    entirely when semantic=False (numeric fold + exact only)."""
    a, b = normalize_value(gv, decode), normalize_value(pv, decode)
    if a == b:
        return "exact"
    if a == "" or b == "":
        return ""

    na, nb = canonical_number(a), canonical_number(b)
    if na is not None and nb is not None:
        if na == nb:
            return "numeric"
        if num_tol > 0:
            try:
                fa, fb = float(na), float(nb)
                if abs(fa - fb) <= num_tol * max(abs(fa), abs(fb), 1e-9):
                    return "numeric"
            except ValueError:
                pass
        return ""
    if (na is None) != (nb is None):                     # number vs non-number
        return ""
    if not semantic:
        return ""

    # categorical ladder
    if _initialism(a, b) or _initialism(b, a):
        return "initialism"
    ta, tb = _token_set(a), _token_set(b)
    if ta and tb:
        if ta == tb:
            return "subset"
        small, large = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
        if len(small) >= 2 and small <= large:           # multi-word containment
            return "subset"
        if _ocr_typo_ok(frozenset(ta), frozenset(tb)):
            return "typo"
        if _jaccard(ta, tb) >= VALUE_JACCARD:
            return "jaccard"
    if embedder is not None and embedder.sim(gv, pv) >= VALUE_EMBED:
        return "embed"
    return ""


# ===========================================================================
# Distinct-level canonicalization (pred string -> GT string)
# ===========================================================================

def _canon_map(pred_vals, gt_vals, equiv_fn, gt_counts=None):
    """Map each distinct predicted string to the GT string it means, using
    equiv_fn. Only ever rewrites pred toward GT (GT is the fixed vocabulary), so
    it can never move a row between two different organisms/traits.

    Exact-normalized agreement is a no-op (returned in nothing). Several GT hits
    are resolved only when they all denote the same thing (pick the closest by
    token overlap, then most frequent); a genuinely ambiguous pred string is left
    alone and reported. Returns (mapping, unmapped) where unmapped is
    [(pred, reason)]."""
    gt_counts = gt_counts or Counter()
    pred_distinct = sorted({str(v) for v in pred_vals if str(v).strip()})
    gt_distinct = sorted({str(v) for v in gt_vals if str(v).strip()})
    gt_by_norm = {}
    for g in gt_distinct:
        gt_by_norm.setdefault(normalize_value(g), g)

    mapping, unmapped = {}, []
    for p in pred_distinct:
        npm = normalize_value(p)
        if npm in gt_by_norm:
            if gt_by_norm[npm] != p:                     # align exact-but-cased
                mapping[p] = gt_by_norm[npm]
            continue
        hits = [g for g in gt_distinct if equiv_fn(p, g)]
        if not hits:
            unmapped.append((p, "no ground-truth string denotes this"))
        elif len(hits) == 1:
            mapping[p] = hits[0]
        elif all(equiv_fn(x, y) for x, y in combinations(hits, 2)):
            pt = _token_set(p)
            mapping[p] = min(hits, key=lambda g: (len(pt ^ _token_set(g)),
                                                  -gt_counts.get(g, 0), len(g)))
        else:
            unmapped.append(
                (p, f"matches {len(hits)} different targets: "
                    f"{', '.join(repr(h) for h in hits[:4])}"))
    return mapping, unmapped


def _apply_map(rows, field, mapping):
    """Return rows with `field` rewritten per mapping (copies only changed rows)."""
    if not mapping:
        return rows
    out = []
    for r in rows:
        v = r.get(field, "")
        out.append({**r, field: mapping[v]} if v in mapping else r)
    return out


# Back-compat wrappers (run_all/check_sync import remap_pred_species).
def remap_pred_species(gt_rows, pred_rows):
    """Rewrite predicted verbatimIdentification to the GT wording for the same
    organism. Returns (rows, mapping, unmapped)."""
    gt_counts = Counter(r.get(F_ID, "") for r in gt_rows
                        if str(r.get(F_ID, "")).strip())
    mapping, unmapped = _canon_map(
        [r.get(F_ID, "") for r in pred_rows],
        [r.get(F_ID, "") for r in gt_rows], species_match, gt_counts)
    return _apply_map(pred_rows, F_ID, mapping), mapping, unmapped


def remap_pred_types(gt_rows, pred_rows, embedder=None, semantic=True):
    """Rewrite predicted measurementType to the GT wording for the same trait.
    Returns (rows, mapping, unmapped)."""
    gt_counts = Counter(r.get(F_TYPE, "") for r in gt_rows
                        if str(r.get(F_TYPE, "")).strip())
    mapping, unmapped = _canon_map(
        [r.get(F_TYPE, "") for r in pred_rows],
        [r.get(F_TYPE, "") for r in gt_rows],
        lambda a, b: type_equiv(a, b, embedder, semantic), gt_counts)
    return _apply_map(pred_rows, F_TYPE, mapping), mapping, unmapped


# ===========================================================================
# Row matching (hash-join on canonical group key, fuzzy value within group)
# ===========================================================================

# Round-2 fuzzy value matching is O(leftover_gt x leftover_pred) within a group.
# It is meant for the handful of CATEGORICAL leftovers a normal trait column has.
# A single-species numeric paper (Orr2024: 1 species, ~14 traits, ~12k distinct
# numeric values) leaves thousands of unmatched NUMBERS per group — and two
# numbers that survived round 1 can never become equal in round 2 (they are
# already numeric; the categorical ladder does not apply and num_tol was tried).
# So round 2 skips numeric leftovers entirely and only fuzzes categorical ones,
# under a hard product cap so no group can blow up regardless.
_FUZZ_PAIR_CAP = 200_000            # max (gt x pred) categorical comparisons/group


def _is_numeric_value(v, decode) -> bool:
    return canonical_number(normalize_value(v, decode)) is not None


def _match_within_group(gt_list, pred_list, decode, embedder, semantic, num_tol,
                        fuzz_log=None, skipped_groups=None):
    """Match GT rows to pred rows in one (species, type[, tags]) group by value.

    Round 1 (exact/numeric-fold) is a hash-bucket pop — O(g+p) — so the common
    case stays linear even in a huge single-group table. Round 2 fuzzy-matches
    only the CATEGORICAL leftovers (numbers are fully settled by round 1 / num_tol
    and can never fuzzy-match), under a product cap. Returns (matched_pairs,
    unmatched_gt, unmatched_pred)."""
    pred_by_val = defaultdict(list)
    for p in pred_list:
        pred_by_val[normalize_value(p.get(F_VAL, ""), decode)].append(p)

    matched, gt_left = [], []
    for g in gt_list:
        k = normalize_value(g.get(F_VAL, ""), decode)
        bucket = pred_by_val.get(k)
        if bucket:
            matched.append((g, bucket.pop()))
        else:
            gt_left.append(g)
    pred_left = [p for lst in pred_by_val.values() for p in lst]

    if not gt_left or not pred_left:
        return matched, gt_left, pred_left

    # numeric leftovers are already decided — keep them out of the fuzzy loop.
    if num_tol > 0:
        gt_num = [g for g in gt_left if _is_numeric_value(g.get(F_VAL, ""), decode)]
        gt_cat = [g for g in gt_left if g not in gt_num]
        pred_num = [p for p in pred_left
                    if _is_numeric_value(p.get(F_VAL, ""), decode)]
        pred_cat = [p for p in pred_left if p not in pred_num]
        # numeric leftovers still deserve a tolerance pass, but only vs each other
        used_pn = [False] * len(pred_num)
        gt_num_left = []
        for g in gt_num:
            gv = g.get(F_VAL, "")
            hit = -1
            for j, p in enumerate(pred_num):
                if used_pn[j]:
                    continue
                if value_equiv(gv, p.get(F_VAL, ""), decode, None, False, num_tol):
                    hit = j
                    if fuzz_log is not None:
                        fuzz_log.append(("numeric-tol", gv, p.get(F_VAL, "")))
                    break
            if hit >= 0:
                used_pn[hit] = True
                matched.append((g, pred_num[hit]))
            else:
                gt_num_left.append(g)
        pred_num_left = [pred_num[j] for j in range(len(pred_num)) if not used_pn[j]]
    else:
        gt_cat = [g for g in gt_left
                  if not _is_numeric_value(g.get(F_VAL, ""), decode)]
        pred_cat = [p for p in pred_left
                    if not _is_numeric_value(p.get(F_VAL, ""), decode)]
        gt_num_left = [g for g in gt_left if g not in gt_cat]
        pred_num_left = [p for p in pred_left if p not in pred_cat]

    # round 2: fuzzy match, categorical leftovers only, capped.
    if gt_cat and pred_cat and len(gt_cat) * len(pred_cat) > _FUZZ_PAIR_CAP:
        if skipped_groups is not None:
            skipped_groups.append(len(gt_cat) * len(pred_cat))
        return (matched, gt_cat + gt_num_left, pred_cat + pred_num_left)

    used = [False] * len(pred_cat)
    unmatched_gt = []
    for g in gt_cat:
        gv = g.get(F_VAL, "")
        hit = -1
        for j, p in enumerate(pred_cat):
            if used[j]:
                continue
            rule = value_equiv(gv, p.get(F_VAL, ""), decode, embedder, semantic,
                               num_tol)
            if rule:
                hit = j
                if fuzz_log is not None:
                    fuzz_log.append((rule, gv, p.get(F_VAL, "")))
                break
        if hit >= 0:
            used[hit] = True
            matched.append((g, pred_cat[hit]))
        else:
            unmatched_gt.append(g)
    unmatched_pred = [pred_cat[j] for j in range(len(pred_cat)) if not used[j]]
    return (matched, unmatched_gt + gt_num_left, unmatched_pred + pred_num_left)


def match_semantic(gt_rows, pred_rows, key_fields, decode, embedder=None,
                   semantic=True, num_tol=0.0, fuzz_log=None):
    """Match on key_fields with fuzzy VALUE equivalence. Species/type are assumed
    already canonicalized in pred_rows (evaluate() does that once); here we group
    by every key field except measurementValue and value-match within each group.
    Returns (matched, missing, extra)."""
    val_in_key = F_VAL in key_fields
    group_fields = [f for f in key_fields if f != F_VAL]

    def gkey(r):
        return tuple(normalize_value(r.get(f, ""), decode) for f in group_fields)

    gtG, prG = defaultdict(list), defaultdict(list)
    for r in gt_rows:
        gtG[gkey(r)].append(r)
    for r in pred_rows:
        prG[gkey(r)].append(r)

    matched, missing, extra = [], [], []
    skipped_groups = []
    for k in set(gtG) | set(prG):
        g, p = gtG.get(k, []), prG.get(k, [])
        if g and p:
            if val_in_key:
                m, ug, up = _match_within_group(g, p, decode, embedder, semantic,
                                                 num_tol, fuzz_log, skipped_groups)
            else:
                n = min(len(g), len(p))
                m, ug, up = list(zip(g[:n], p[:n])), g[n:], p[n:]
            matched += m
            missing += ug
            extra += up
        elif g:
            missing += g
        else:
            extra += p
    if skipped_groups:
        print(f"  [match] {len(skipped_groups)} group(s) had too many categorical "
              f"leftovers to fuzzy-match (>{_FUZZ_PAIR_CAP:,} pairs); those rows "
              f"were left unmatched. Largest: {max(skipped_groups):,} pairs.")
    return matched, missing, extra


# ===========================================================================
# Scoping
# ===========================================================================

def build_scope(gt_rows, scope_fields, decode):
    """{field: set of normalized values GT covers} for each scoping field."""
    return {f: {normalize_value(r.get(f, ""), decode) for r in gt_rows
                if str(r.get(f, "")).strip()}
            for f in scope_fields}


def partition_extra(extra, scope, decode):
    """Split spurious rows into (in_scope FPs, out_of_scope [(row, uncovered)])."""
    in_scope, out_of_scope = [], []
    for r in extra:
        uncovered = [f for f, covered in scope.items()
                     if normalize_value(r.get(f, ""), decode) not in covered]
        (out_of_scope.append((r, uncovered)) if uncovered
         else in_scope.append(r))
    return in_scope, out_of_scope


# ===========================================================================
# Scoring
# ===========================================================================

def prf(tp, fp, fn):
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f = 2 * p * r / (p + r) if (p + r) else 0.0
    return p, r, f


def score_key_set(gt_rows, pred_rows, fields, decode, scope_sets=None,
                  embedder=None, semantic=True, num_tol=0.0):
    """P/R/F1 for one scoring category, using the SAME matcher and scoping as the
    headline. Returns (p, r, f, (tp, fp_scoped, fn), fp_all)."""
    matched, missing, extra = match_semantic(gt_rows, pred_rows, fields, decode,
                                              embedder, semantic, num_tol)
    in_scope = extra
    if scope_sets:
        in_scope, _ = partition_extra(extra, scope_sets, decode)
    tp, fn = len(matched), len(missing)
    p, r, f = prf(tp, len(in_scope), fn)
    return p, r, f, (tp, len(in_scope), fn), len(extra)


def _short_field(f):
    return {"verbatimIdentification": "id", "measurementType": "type",
            "measurementValue": "value", "measurementStatistic": "stat",
            "basisOfRecord": "basis", "lifeStage": "stage"}.get(f, f)


def _tag_coverage(matched, fields, decode):
    """Share of matched rows where an added (non-core) field was populated on both
    sides — so an identical score between two categories can be read correctly."""
    core = set(KEY_SETS.get("core", []))
    added = [f for f in fields if f not in core]
    if not added or not matched:
        return None
    informative = sum(
        1 for g, p in matched
        if any(normalize_value(g.get(f, ""), decode)
               and normalize_value(p.get(f, ""), decode) for f in added))
    return informative, len(matched), added


def print_key_set_scores(gt, pred, decode, names=None, scope_sets=None,
                         matched=None, embedder=None, semantic=True, num_tol=0.0):
    names = names or ACTIVE_KEY_SETS
    print("\nSCORES BY CATEGORY")
    print(f"  {'category':<10} {'P':>6} {'R':>6} {'F1':>6}  {'TP':>5} {'FP':>5} "
          f"{'FN':>5}   key")
    out, prev_f = {}, None
    for name in names:
        fields = KEY_SETS.get(name)
        if not fields:
            print(f"  {name:<10} (unknown category)")
            continue
        p, r, f, (tp, fp, fn), fp_all = score_key_set(
            gt, pred, fields, decode, scope_sets, embedder, semantic, num_tol)
        out[name] = (p, r, f)
        short = "+".join(_short_field(x) for x in fields)
        print(f"  {name:<10} {p:>6.3f} {r:>6.3f} {f:>6.3f}  {tp:>5} {fp:>5} "
              f"{fn:>5}   {short}")
        if fp_all != fp:
            strict = tp / (tp + fp_all) if (tp + fp_all) else 0.0
            print(f"  {'':<10} ({fp_all - fp} more spurious row(s) out-of-scope; "
                  f"strict P would be {strict:.3f})")
        if prev_f is not None:
            print(f"  {'':<10} (F1 {f - prev_f:+.3f} vs previous)")
        cov = _tag_coverage(matched, fields, decode) if matched else None
        if cov and cov[0] < cov[1]:
            informative, total, added = cov
            print(f"  {'':<10} note: only {informative}/{total} matched row(s) had "
                  f"any of {'/'.join(_short_field(a) for a in added)} populated on "
                  f"both sides — the rest agree by being empty")
        prev_f = f
    return out


# ===========================================================================
# Miss attribution (which axis failed) + saved detail
# ===========================================================================

def attribute_misses(missing, pred, decode, embedder=None, semantic=True,
                     num_tol=0.0):
    """Categorize every missed GT row by the axis it failed on (species / trait /
    value), using the SAME canonical species/type (pred is already remapped) and
    the SAME value_equiv, so the attribution agrees with the score. Returns the
    aggregate counters plus a complete per-row list."""
    n = lambda r, f: normalize_value(r.get(f, ""), decode)

    # Precompute per group ONCE: the set of normalized pred values present, and a
    # representative raw value (for the collision column). Re-normalizing every
    # group's candidate list per missing row was O(misses x group_size) — 17M
    # normalize() calls on a single-species numeric paper (Orr2024). This is O(pred
    # + misses) instead.
    pred_species = {n(r, F_ID) for r in pred}
    pred_types_of = defaultdict(set)
    group_norm_vals = defaultdict(set)                  # (species, type) -> {norm vals}
    group_first_raw = {}                                # (species, type) -> raw val
    for r in pred:
        s, t = n(r, F_ID), n(r, F_TYPE)
        pred_types_of[s].add(t)
        raw = r.get(F_VAL, "")
        group_norm_vals[(s, t)].add(normalize_value(raw, decode))
        group_first_raw.setdefault((s, t), raw)

    causes = Counter()
    sub_value = Counter()
    sub_species = Counter()
    sub_trait = Counter()
    rows = []
    for r in missing:
        s, t = n(r, F_ID), n(r, F_TYPE)
        gid, gtype, gval = r.get(F_ID, ""), r.get(F_TYPE, ""), r.get(F_VAL, "")
        base = {"verbatimIdentification": gid, "measurementType": gtype,
                "measurementValue": gval, "pred_collision_value": ""}
        if s not in pred_species:
            causes["species not in prediction"] += 1
            sub_species[gid] += 1
            rows.append({"cause": "species not in prediction", **base})
        elif t not in pred_types_of[s]:
            causes["species present, trait missing"] += 1
            sub_trait[gtype] += 1
            rows.append({"cause": "species present, trait missing", **base})
        elif n(r, F_VAL) in group_norm_vals.get((s, t), ()):
            causes["value present, extra GT copies not reproduced"] += 1
            rows.append({"cause": "value present, extra GT copies not reproduced",
                         **{**base, "pred_collision_value": gval}})
        else:
            pv = group_first_raw.get((s, t), "")
            causes["species+trait present, value differs"] += 1
            sub_value[(normalize_value(gval, decode),
                       normalize_value(pv, decode))] += 1
            rows.append({"cause": "species+trait present, value differs",
                         **{**base, "pred_collision_value": pv}})
    return {"causes": causes, "sub_value": sub_value, "sub_species": sub_species,
            "sub_trait": sub_trait, "rows": rows, "pred_species": pred_species}


def _closest_pred_species(name, preds):
    best, score = "", 0.0
    for p in preds:
        sc = _ratio(type_key(name), type_key(p))
        if sc > score:
            best, score = p, sc
    return best, score


# --- deterministic severity (LLM optional, off by default) -----------------

def _deterministic_severity(row):
    cause = row.get("cause", "")
    pval = str(row.get("pred_collision_value", "")).strip()
    if cause == "species not in prediction":
        return ("severe", "species not extracted at all")
    if cause == "species present, trait missing":
        return ("moderate", "the trait was not extracted for this species")
    if cause == "value present, extra GT copies not reproduced":
        return ("minor", "value is present; GT simply has more copies of it")
    if cause == "species+trait present, value differs":
        if not pval:
            return ("moderate", "no value was predicted for this trait")
        return ("moderate", "predicted a different value for this trait")
    return ("", "(not assessed)")


def assess_miss_severity(rows, use_llm=False, batch_size=20):
    """Annotate each miss with a deterministic severity + reasoning IN PLACE
    (score-neutral). The LLM path is opt-in and only refines the ambiguous
    'value differs' cases; without it those keep their deterministic label."""
    ambiguous = []
    for i, r in enumerate(rows):
        sev, why = _deterministic_severity(r)
        r["severity"], r["reasoning"] = sev, why
        if use_llm and r.get("cause") == "species+trait present, value differs" \
                and str(r.get("pred_collision_value", "")).strip():
            ambiguous.append(i)

    if not use_llm or not ambiguous:
        return rows
    graded = _llm_grade_severity(rows, ambiguous, batch_size)
    for i, val in graded.items():
        rows[i]["severity"], rows[i]["reasoning"] = val
    return rows


_SEVERITY_SYSTEM = (
    "You grade how SEVERE each extraction miss is, comparing what the ground "
    "truth expected to what the pipeline predicted for the SAME species and "
    "trait. Severity only; you do NOT change any score.\n"
    "- trivial: same meaning, cosmetic difference (authority/family in the value, "
    "punctuation, units written differently, 1 vs 1.0).\n"
    "- minor: same quantity/category, small real difference (rounding, unit "
    "conversion, near-synonym).\n"
    "- moderate: related but not clearly the same.\n"
    "- severe: wrong — different trait or unrelated value.\n"
    'Answer ONLY JSON: {"items":[{"n":<int>,"severity":"trivial|minor|moderate|'
    'severe","reasoning":"<=15 words"}]}'
)


def _llm_grade_severity(rows, idxs, batch_size):
    """Optional Ollama grading of ambiguous misses. Self-contained HTTP call so
    the evaluator needs no pipeline import; any failure leaves rows unchanged."""
    import json as _json
    from urllib import request as _rq
    url = "http://127.0.0.1:11434/api/chat"   # 127.0.0.1, not localhost (IPv6 ::1 refuses)
    model = "gemma4:e2b"
    out = {}
    for start in range(0, len(idxs), batch_size):
        chunk = idxs[start:start + batch_size]
        lines = [
            f'{k}. species "{rows[k].get("verbatimIdentification","")}", trait '
            f'"{rows[k].get("measurementType","")}": ground truth = '
            f'"{rows[k].get("measurementValue","")}", predicted = '
            f'"{rows[k].get("pred_collision_value","") or "(nothing)"}"'
            for k in chunk]
        body = {"model": model, "stream": False,
                "options": {"temperature": 0},
                "messages": [{"role": "system", "content": _SEVERITY_SYSTEM},
                             {"role": "user", "content": "Items:\n" + "\n".join(lines)}]}
        try:
            req = _rq.Request(url, data=_json.dumps(body).encode(),
                              headers={"Content-Type": "application/json"})
            with _rq.urlopen(req, timeout=120) as r:
                content = _json.loads(r.read()).get("message", {}).get("content", "")
            parsed = _json.loads(content[content.find("{"):content.rfind("}") + 1])
        except Exception as e:
            print(f"  [severity] batch unavailable ({type(e).__name__}); "
                  f"deterministic labels kept")
            return out
        for it in parsed.get("items", []) if isinstance(parsed, dict) else []:
            try:
                k = int(it["n"])
            except (KeyError, TypeError, ValueError):
                continue
            sev = str(it.get("severity", "")).strip().lower()
            if sev in {"trivial", "minor", "moderate", "severe"}:
                out[k] = (sev, str(it.get("reasoning", "")).strip()[:200])
    return out


def write_failure_details(attr, pred, path, use_llm_severity=False):
    """Write every missed row to <path>_misses.csv and the full counters to
    <path>_misses_summary.json (schema unchanged, so collect_misses.py still
    reads it)."""
    rows = attr["rows"]
    preds = sorted({r.get(F_ID, "") for r in pred})

    NEAR = 0.55
    closest = {}
    for r in rows:
        if r["cause"] == "species not in prediction":
            gid = r["verbatimIdentification"]
            if gid not in closest:
                best, score = _closest_pred_species(gid, preds)
                closest[gid] = (best, score) if score >= NEAR else ("", score)

    assess_miss_severity(rows, use_llm=use_llm_severity)

    csv_path = f"{path}_misses.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=[
            "cause", "verbatimIdentification", "measurementType",
            "measurementValue", "pred_collision_value",
            "closest_pred_species", "closest_score", "severity", "reasoning"])
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
        "value_substitutions": [{"gt": g, "pred": p, "count": c}
                                for (g, p), c in attr["sub_value"].most_common()],
        "species_absent": [
            {"gt_species": name, "count": c,
             "closest_pred_species": closest.get(name, ("", 0.0))[0],
             "closest_score": round(closest.get(name, ("", 0.0))[1], 3)}
            for name, c in attr["sub_species"].most_common()],
        "traits_missing": [{"measurementType": name, "count": c}
                           for name, c in attr["sub_trait"].most_common()],
    }
    Path(f"{path}_misses_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n  full miss detail saved -> {Path(csv_path).name}, "
          f"{Path(path).name}_misses_summary.json ({len(rows)} row(s))")


def print_failure_attribution(missing, pred, decode, top=6, detail_path=None,
                              embedder=None, semantic=True, num_tol=0.0,
                              use_llm_severity=False):
    if not missing:
        return
    attr = attribute_misses(missing, pred, decode, embedder, semantic, num_tol)
    causes = attr["causes"]
    sub_value, sub_species, sub_trait = (attr["sub_value"], attr["sub_species"],
                                         attr["sub_trait"])
    total = len(missing)
    print(f"\nWHY THE {total} MISSED ROWS MISSED")
    for label in ("species not in prediction", "species present, trait missing",
                  "value present, extra GT copies not reproduced",
                  "species+trait present, value differs"):
        if causes.get(label):
            print(f"  {label:<48} {causes[label]:>6}")

    def verdict(singular, plural, counter):
        if not counter:
            return
        shown = counter.most_common(top)
        covered = sum(c for _, c in shown)
        pct = 100 * covered / total if total else 0
        noun = singular if len(shown) == 1 else plural
        verb = "explains" if len(shown) == 1 else "explain"
        tag = "systematic, not scattered" if pct >= 60 else "scattered; no single cause"
        print(f"  -> {len(shown)} {noun} {verb} {covered} of {total} misses "
              f"({pct:.0f}%) — {tag}")

    if sub_value:
        print("\n  VALUE SUBSTITUTIONS (gt -> pred), most frequent first:")
        for (g, p), c in sub_value.most_common(top):
            print(f"     {g!r:28} ->  {p!r:28} x{c}")
        verdict("substitution", "substitutions", sub_value)
    if sub_species:
        print(f"\n  SPECIES IN GT BUT NOT IN PREDICTION ({len(sub_species)} "
              f"distinct), closest predicted name:")
        preds = sorted({r.get(F_ID, "") for r in pred})
        for name, c in sub_species.most_common(top):
            best, score = _closest_pred_species(name, preds)
            near = (f"  ~{score:.2f}~  pred {best!r}" if score >= 0.55
                    else "   (nothing similar in the prediction)")
            print(f"     gt {name!r:34}{near}   x{c}")
        verdict("species mismatch", "species mismatches", sub_species)
    if sub_trait:
        print("\n  TRAITS THE SPECIES HAS IN GT BUT NOT IN PREDICTION:")
        for name, c in sub_trait.most_common(top):
            print(f"     {name!r:34} x{c}")
        verdict("missing trait", "missing traits", sub_trait)

    if detail_path:
        write_failure_details(attr, pred, detail_path,
                              use_llm_severity=use_llm_severity)


def print_type_coverage(gt, pred, decode, sim_threshold=0.55):
    """measurementType coverage — a VIEW OF THE SCORE. pred arrives already
    remapped, so any pair the scorer credited shares a string and lands on one
    row. What used to be silently merged is listed as UNRESOLVED NEAR-MISSES."""
    gt_types = Counter(normalize_value(r["measurementType"], decode) for r in gt)
    pred_types = Counter(normalize_value(r["measurementType"], decode) for r in pred)
    rows = []
    for t in set(gt_types) | set(pred_types):
        gc, pc = gt_types.get(t, 0), pred_types.get(t, 0)
        note = ("" if gc == pc else f"Δ{pc - gc:+d} (split?)") if (gc and pc) \
            else ("GT-ONLY" if gc else "PRED-ONLY")
        rows.append((type_key(t), t, gc, pc, note))
    rows.sort(key=lambda r: (r[0], r[1]))
    print("\nmeasurementType COVERAGE")
    print(f"  {'measurementType':<46} {'gt':>4} {'pred':>5}   note")
    for _, label, gc, pc, note in rows:
        print(f"  {label:<46} {gc:>4} {pc:>5}   {note}")

    gt_only = [t for t in gt_types if not pred_types.get(t)]
    pred_only = [t for t in pred_types if not gt_types.get(t)]
    near = sorted(((_ratio(type_key(g), type_key(p)), g, p)
                   for g in gt_only for p in pred_only), reverse=True)
    seen_g, seen_p, shown = set(), set(), []
    for s, g, p in near:
        if s < sim_threshold or g in seen_g or p in seen_p:
            continue
        seen_g.add(g); seen_p.add(p); shown.append((s, g, p))
    if shown:
        print("\n  UNRESOLVED NEAR-MISSES (similar wording, NOT credited — cost "
              "both a miss and a spurious row)")
        for s, g, p in shown[:15]:
            print(f"    gt {g!r:34} vs pred {p!r:34} sim={s:.2f}")


def _print_fuzz_summary(fuzz_log):
    """What the fuzzy VALUE matcher accepted, by rule, with a sample — so an
    inflated score can be audited. Exact/numeric folds are not logged (not fuzzy)."""
    if not fuzz_log:
        return
    by_rule = Counter(rule for rule, _, _ in fuzz_log)
    print(f"\nFUZZY VALUE MATCHES ({len(fuzz_log)} accepted beyond exact/numeric)")
    for rule, c in by_rule.most_common():
        print(f"  {rule:<12} {c:>5}")
    print("  sample:")
    seen = set()
    for rule, g, p in fuzz_log:
        sig = (rule, g, p)
        if sig in seen:
            continue
        seen.add(sig)
        print(f"    [{rule}] gt {g!r} == pred {p!r}")
        if len(seen) >= 12:
            break


# ===========================================================================
# Top-level single-paper evaluate
# ===========================================================================

def evaluate(pred_path, gt_path, key_fields, decode, semantic=True, use_llm=False,
             scope="measurementType", key_sets=None, match_species=True,
             embed=False, num_tol=0.0, strict_values=False):
    """Score one prediction CSV against one ground-truth xlsx.

    semantic       fuzzy measurementType matching (and, unless strict_values,
                   fuzzy categorical VALUE matching). False = exact-only baseline.
    match_species  fuzzy species-name matching (token-set/abbrev/OCR). Very cheap.
    embed          load the optional embedding model for genuine synonyms.
    num_tol        relative numeric tolerance for value equality (0 = exact fold).
    strict_values  never fuzzy-match categorical values (numeric fold + exact).
    use_llm        opt-in LLM severity grading of ambiguous misses (score-neutral).

    Returns {"row": (p,r,f) scoped, "row_strict":..., "recall":..., ...}.
    """
    gt = load_xlsx(gt_path)
    pred = load_csv(pred_path)
    val_semantic = semantic and not strict_values

    embedder = make_embedder(embed and semantic)
    if embedder is not None:                       # one batched forward pass
        embedder.warm([r.get(F_TYPE, "") for r in gt]
                      + [r.get(F_TYPE, "") for r in pred]
                      + [r.get(F_VAL, "") for r in gt]
                      + [r.get(F_VAL, "") for r in pred])

    # Canonicalize species then type ONCE (pred -> gt). After this, equivalent
    # rows share an exact key on those axes and only the value stays fuzzy.
    species_map, species_unmapped = {}, []
    if match_species:
        pred, species_map, species_unmapped = remap_pred_species(gt, pred)
    type_map, type_unmapped = {}, []
    if semantic:
        pred, type_map, type_unmapped = remap_pred_types(gt, pred, embedder,
                                                         semantic=True)

    fuzz_log = []
    matched, missing, extra = match_semantic(
        gt, pred, key_fields, decode, embedder, val_semantic, num_tol, fuzz_log)

    print("=" * 64)
    print(f"GROUND TRUTH : {gt_path}  ({len(gt)} rows)")
    print(f"PREDICTION   : {pred_path}  ({len(pred)} rows)")
    print(f"KEY          : {key_fields}   decode={decode}  semantic={semantic}  "
          f"strict_values={strict_values}  embed={'on' if embedder else 'off'}")
    print(f"SCOPE        : {scope}")
    print("=" * 64)

    if species_map:
        print(f"\nTAXON NAME REMAP (pred -> gt, {len(species_map)} pair(s))")
        for p, g in sorted(species_map.items()):
            print(f"  {p!r} -> {g!r}")
    if species_unmapped:
        print(f"\nTAXON NAMES LEFT UNMAPPED ({len(species_unmapped)})")
        for nm, why in sorted(species_unmapped):
            print(f"  {nm!r}: {why}")
    if type_map:
        print(f"\nmeasurementType REMAP (pred -> gt, {len(type_map)} pair(s))")
        for p, g in sorted(type_map.items()):
            print(f"  {p!r} -> {g!r}")
    if type_unmapped:
        print(f"\nmeasurementType LEFT UNMAPPED ({len(type_unmapped)})")
        for nm, why in sorted(type_unmapped)[:20]:
            print(f"  {nm!r}: {why}")

    scope_fields = [] if scope in (None, "none") else scope.split("+")
    scope_sets = build_scope(gt, scope_fields, decode) if scope_fields else {}
    in_scope, out_of_scope = partition_extra(extra, scope_sets, decode)

    tp, fn = len(matched), len(missing)
    fp_all, fp_scoped = len(extra), len(in_scope)
    p_all, r_all, f_all = prf(tp, fp_all, fn)
    p_sc, r_sc, f_sc = prf(tp, fp_scoped, fn)

    print("\nROW-LEVEL (key match)")
    print(f"  matched (TP)          : {tp}")
    print(f"  missed (FN)           : {fn}")
    print(f"  spurious, in scope    : {fp_scoped}   <- GT covers this trait: real errors")
    print(f"  spurious, out of scope: {len(out_of_scope)}   <- GT never covers it: "
          f"nothing to score against")
    print(f"\n  STRICT  P/R/F1        : {p_all:.3f} / {r_all:.3f} / {f_all:.3f}")
    print(f"  SCOPED  P/R/F1        : {p_sc:.3f} / {r_sc:.3f} / {f_sc:.3f}")
    print(f"  RECALL (GT coverage)  : {r_all:.3f}")

    if out_of_scope:
        by_reason = Counter("+".join(u) for _, u in out_of_scope)
        print("\n  out-of-scope rows by uncovered field:")
        for reason, n in by_reason.most_common():
            print(f"    {reason:<40} {n:>5}")

    _print_fuzz_summary(fuzz_log)

    # field-level accuracy on matched rows
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
                continue
            total += 1
            agree += (gv == pv)
        acc = agree / total if total else float("nan")
        field_stats[col] = (agree, total, acc)
        flag = "  <-- low" if (total and acc < 0.5) else ""
        acc_s = "  n/a" if total == 0 else f"{acc:.3f}"
        print(f"  {col:<24} {agree:>6} {total:>6} {acc_s:>6}{flag}")

    detail_stem = str(Path(pred_path).with_suffix("")) if pred_path else None
    print_failure_attribution(missing, pred, decode, detail_path=detail_stem,
                              embedder=embedder, semantic=val_semantic,
                              num_tol=num_tol, use_llm_severity=use_llm)

    print_type_coverage(gt, pred, decode)

    by_key_set = print_key_set_scores(gt, pred, decode, key_sets,
                                      scope_sets=scope_sets, matched=matched,
                                      embedder=embedder, semantic=val_semantic,
                                      num_tol=num_tol)

    return {
        "row": (p_sc, r_sc, f_sc),
        "row_strict": (p_all, r_all, f_all),
        "recall": r_all,
        "n_out_of_scope": len(out_of_scope),
        "n_in_scope_fp": fp_scoped,
        "n_fuzzy_value_matches": len(fuzz_log),
        "fields": field_stats,
        "by_key_set": by_key_set,
        "species_map": species_map,
        "type_map": type_map,
    }


# ===========================================================================
# Batch: re-score every already-extracted paper
# ===========================================================================

def _load_prior_summary(summary_path):
    if not Path(summary_path).exists():
        return {}
    prior = {}
    try:
        with open(summary_path, "r", newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if row.get("paper"):
                    prior[row["paper"]] = row
    except (OSError, csv.Error):
        return {}
    return prior


def _metrics_from_report(report_path):
    try:
        text = Path(report_path).read_text(encoding="utf-8")
    except OSError:
        return None
    m = re.search(r"SCOPED\s+P/R/F1\s*:\s*([0-9.]+)\s*/\s*([0-9.]+)\s*/\s*([0-9.]+)",
                  text)
    if not m:
        return None
    try:
        return float(m.group(1)), float(m.group(2)), float(m.group(3))
    except ValueError:
        return None


def evaluate_all(papers_root, output_root, key_fields, decode, *,
                 semantic=True, use_llm=False, scope="measurementType",
                 key_sets=None, match_species=True, skip_existing=False,
                 embed=False, num_tol=0.0, strict_values=False):
    """Re-run evaluation over every output/<paper>/<paper>.csv against its
    ground-truth xlsx, write per-paper reports + *_misses files, rewrite
    summary.csv. Mirrors run_all.py's evaluation step."""
    from mineru_extract import classify_folder            # lazy: only --all needs it

    papers_root, output_root = Path(papers_root), Path(output_root)
    if not output_root.is_dir():
        raise SystemExit(f"output dir not found: {output_root.resolve()}")

    papers = sorted(d.name for d in output_root.iterdir()
                    if d.is_dir() and (d / f"{d.name}.csv").exists())
    if not papers:
        raise SystemExit(f"no paper CSVs found under {output_root}")

    prior_summary = _load_prior_summary(output_root / "summary.csv") \
        if skip_existing else {}

    print(f"Re-evaluating {len(papers)} paper(s) under {output_root}  "
          f"(semantic={semantic}, embed={embed}, decode={decode}, "
          f"strict_values={strict_values}, skip_existing={skip_existing})\n")

    def ground_truth_for(paper):
        folder = papers_root / paper
        if not folder.is_dir():
            return None
        try:
            _, results_path, _ = classify_folder(folder)
        except Exception:
            return None
        return str(results_path) if results_path else None

    summary, n_skipped = [], 0
    for paper in papers:
        out_csv = output_root / paper / f"{paper}.csv"
        report = output_root / paper / f"{paper}_report.txt"

        if skip_existing and report.exists():
            prev = prior_summary.get(paper)
            if prev and prev.get("status") == "ok":
                summary.append(prev); n_skipped += 1
                print(f"  SKIP {paper:<28} already evaluated  [summary]")
                continue
            m = _metrics_from_report(report)
            if m:
                p, r, f = m
                summary.append({"paper": paper, "precision": round(p, 3),
                                "recall": round(r, 3), "f1": round(f, 3),
                                "status": "ok"})
                n_skipped += 1
                print(f"  SKIP {paper:<28} already evaluated  [report]")
                continue
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
                                   key_sets=key_sets, match_species=match_species,
                                   embed=embed, num_tol=num_tol,
                                   strict_values=strict_values)
            report.write_text(buf.getvalue(), encoding="utf-8")
            p, r, f = metrics["row"]
            print(f"  OK   {paper:<28} P/R/F1 = {p:.3f}/{r:.3f}/{f:.3f}  "
                  f"-> {report.name}")
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


# ===========================================================================
# CLI
# ===========================================================================

DEFAULT_PAPERS = "../data/un_processed_papers"
DEFAULT_OUTPUT = "../output"


def _paper_ground_truth(paper, papers_root):
    from mineru_extract import classify_folder            # lazy
    folder = Path(papers_root) / paper
    if not folder.is_dir():
        return None
    try:
        _, results_path, _ = classify_folder(folder)
    except Exception:
        return None
    return str(results_path) if results_path else None


def main():
    ap = argparse.ArgumentParser(
        description="Evaluate a prediction CSV against ground truth, or --all to "
                    "re-evaluate every already-extracted paper.")
    ap.add_argument("pred", nargs="?",
                    help="prediction CSV, OR a paper name (resolves "
                         "<--output>/<paper>/<paper>.csv and its GT xlsx)")
    ap.add_argument("gt", nargs="?", help="ground-truth xlsx (omit for paper-name)")
    ap.add_argument("--all", action="store_true",
                    help="re-evaluate every output/<paper>/<paper>.csv")
    ap.add_argument("--papers", default=DEFAULT_PAPERS)
    ap.add_argument("--output", default=DEFAULT_OUTPUT)
    ap.add_argument("--decode", action="store_true",
                    help="apply legend code -> term decoding before comparison")
    ap.add_argument("--key", nargs="+", default=DEFAULT_KEY)
    ap.add_argument("--no-semantic", action="store_true",
                    help="disable fuzzy type + fuzzy value matching (exact only)")
    ap.add_argument("--strict-values", action="store_true",
                    help="keep fuzzy TYPE matching but compare values exactly "
                         "(numeric fold only) — conservative value scoring")
    ap.add_argument("--embed", action="store_true",
                    help="load sentence-transformers for semantic value/type "
                         "synonyms (predator~carnivorous). Deterministic if absent.")
    ap.add_argument("--num-tol", type=float, default=0.0,
                    help="relative numeric tolerance for value equality "
                         "(e.g. 0.02 = 2%%). Default 0 = exact numeric fold.")
    ap.add_argument("--scope", default="measurementType", choices=SCOPE_CHOICES)
    ap.add_argument("--no-species-match", action="store_true",
                    help="require verbatimIdentification to match exactly")
    ap.add_argument("--key-sets", nargs="+", default=None, metavar="NAME",
                    help=f"scoring categories to report. Available: "
                         f"{', '.join(KEY_SETS)} (default: {', '.join(ACTIVE_KEY_SETS)})")
    ap.add_argument("--llm-severity", action="store_true",
                    help="opt-in: LLM-grade ambiguous value misses (score-neutral)")
    ap.add_argument("--skip-existing", action="store_true",
                    help="[--all] skip papers with a report + 'ok' summary row")
    args = ap.parse_args()

    semantic = not args.no_semantic

    if args.all:
        evaluate_all(args.papers, args.output, args.key, args.decode,
                     semantic=semantic, use_llm=args.llm_severity, scope=args.scope,
                     key_sets=args.key_sets, match_species=not args.no_species_match,
                     skip_existing=args.skip_existing, embed=args.embed,
                     num_tol=args.num_tol, strict_values=args.strict_values)
        return

    if args.pred and not args.gt:                        # paper-name mode
        paper = args.pred
        out_csv = Path(args.output) / paper / f"{paper}.csv"
        if not out_csv.exists():
            ap.error(f"no prediction CSV for '{paper}': {out_csv} not found.")
        gt = _paper_ground_truth(paper, args.papers)
        if not gt or not Path(gt).exists():
            ap.error(f"found {out_csv} but no ground-truth xlsx for '{paper}'.")
        print(f"Evaluating '{paper}'\n  pred: {out_csv}\n  gt:   {gt}\n")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            metrics = evaluate(str(out_csv), gt, args.key, args.decode,
                               semantic=semantic, use_llm=args.llm_severity,
                               scope=args.scope, key_sets=args.key_sets,
                               match_species=not args.no_species_match,
                               embed=args.embed, num_tol=args.num_tol,
                               strict_values=args.strict_values)
        report = Path(args.output) / paper / f"{paper}_report.txt"
        report.write_text(buf.getvalue(), encoding="utf-8")
        print(buf.getvalue())
        p, r, f = metrics["row"]
        print(f"  -> P/R/F1 = {p:.3f}/{r:.3f}/{f:.3f}   report: {report}")
    elif not args.pred or not args.gt:
        ap.error("give a paper name, or PRED.csv and GT.xlsx, or --all")
    else:
        evaluate(args.pred, args.gt, args.key, args.decode, semantic=semantic,
                 use_llm=args.llm_severity, scope=args.scope,
                 key_sets=args.key_sets, match_species=not args.no_species_match,
                 embed=args.embed, num_tol=args.num_tol,
                 strict_values=args.strict_values)


if __name__ == "__main__":
    main()