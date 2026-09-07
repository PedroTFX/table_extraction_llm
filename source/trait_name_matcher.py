"""
Semantic measurementType matcher for the evaluator.

Problem: the pipeline faithfully extracts the paper's own trait names, but the
ground truth uses the volunteers' wording. Same trait, different string:
    'Hibernation_Egg'        vs 'hibernation in egg stage recorded'
    'Diurnal_activity'       vs 'diurnal activity'
    'Body size'              vs 'Body Length'
Exact-string keying scores every one of these as FP+FN even though the species
and value match. This module maps each predicted measurementType onto the GT
measurementType that means the same thing, so the evaluator can credit them.

Two passes, cheap-first:
  1. DETERMINISTIC normalize+match  — catches casing / underscores / spacing /
     unit-parentheticals with zero LLM calls.
  2. LLM CONFIRM (gemma4:e2b via Ollama) — only the names the deterministic pass
     left unmatched are sent to the model, paired with the best remaining
     candidates, asked "same trait? yes/no". Confirmed pairs extend the map.

Only measurementType is matched semantically; verbatimIdentification and
measurementValue are still required to match exactly by the evaluator, so this
cannot invent cross-species or cross-value matches.
"""
import json
import re
import unicodedata
from difflib import SequenceMatcher
from urllib import request as _rq

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "gemma4:e2b"

_UNIT_PAREN = re.compile(r"\((?:[^()]*\b(?:mm|cm|m|km|g|kg|mg|mm2|°c|%|count|n|df)\b[^()]*)\)", re.I)
_NONALNUM = re.compile(r"[^a-z0-9]+")
_STOP = {"recorded", "the", "of", "in", "on", "a", "an", "as", "at", "and",
         "stage", "state", "development", "evaluated", "sources"}


def normalize(name: str) -> str:
    """Aggressive canonical form for cheap matching: lowercase, strip accents,
    drop unit parentheticals, split snake/camel, remove punctuation & stopwords,
    sort tokens so word-order differences collapse."""
    s = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode()
    s = s.lower().strip()
    s = _UNIT_PAREN.sub(" ", s)
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", s)     # camelCase -> words (pre-lower would've caught; safe)
    s = _NONALNUM.sub(" ", s)
    toks = [t for t in s.split() if t and t not in _STOP]
    return " ".join(sorted(toks))


def deterministic_match(gt_names, pred_names):
    """Return (mapping pred->gt, unmatched_pred, unmatched_gt) using normalize()."""
    gt_by_norm = {}
    for g in gt_names:
        gt_by_norm.setdefault(normalize(g), g)
    mapping, unmatched_pred = {}, []
    for p in pred_names:
        g = gt_by_norm.get(normalize(p))
        if g is not None:
            mapping[p] = g
        else:
            unmatched_pred.append(p)
    matched_gt = set(mapping.values())
    unmatched_gt = [g for g in gt_names if g not in matched_gt]
    return mapping, unmatched_pred, unmatched_gt


def containment_match(gt_names, pred_names):
    """Deterministically pair names where one is a QUALIFIED form of the other.

    The commonest wording mismatch in this corpus is a bare head noun on one side
    and the same noun qualified on the other: pred 'body' vs GT 'Body size',
    pred 'proboscis' vs GT 'Proboscis length', GT 'tongue length' vs pred 'mean
    tongue length'. Every one of these has the shorter name's tokens as a SUBSET
    of the longer's.

    Why a subset rule and not a similarity threshold: the pairs above score 0.75
    on token similarity — the identical score as 'forewing length' vs 'hindwing
    length', and below 'fs-15' vs 'fs-5' (0.83). No cutoff separates them.
    Containment does: neither wing pair nor the fs- pair is a subset of the other,
    because each has a token the other lacks (forewing/hindwing, 15/5).

    Two guards keep it honest:
      * UNAMBIGUITY — the subset name must be contained in exactly ONE name on
        the other side. A pred 'length' sitting inside both 'body length' and
        'wing length' is a genuine ambiguity and is left for the LLM.
      * NON-EMPTY, NON-TRIVIAL — the shared tokens must be the whole of the
        shorter name and it must have at least one token after stopword removal,
        so an empty normalisation can't match everything.

    Returns (mapping pred->gt, still_unmatched_pred, still_unmatched_gt).
    """
    gt_toks = {g: set(normalize(g).split()) - {""} for g in gt_names}
    pred_toks = {p: set(normalize(p).split()) - {""} for p in pred_names}

    def contains(a, b):                       # a's tokens ⊆ b's tokens
        return bool(a) and bool(b) and a <= b

    mapping = {}
    taken_gt = set()
    for p, pt in pred_toks.items():
        if not pt:
            continue
        hits = [g for g, gt in gt_toks.items()
                if g not in taken_gt and (contains(pt, gt) or contains(gt, pt))]
        if len(hits) == 1:                    # unambiguous -> accept
            mapping[p] = hits[0]
            taken_gt.add(hits[0])
    un_pred = [p for p in pred_names if p not in mapping]
    un_gt = [g for g in gt_names if g not in taken_gt]
    return mapping, un_pred, un_gt


def _ollama_yes(pred_name, gt_name):
    """Ask gemma4:e2b whether two trait names denote the same trait. Returns bool."""
    prompt = (
        "You compare two biological trait names from a data table. "
        "Answer with exactly one word: YES if they refer to the SAME trait, "
        "NO if they are different traits.\n\n"
        f"Name A: {pred_name}\nName B: {gt_name}\n\n"
        "Same trait? Answer YES or NO only."
    )
    body = {
        "model": OLLAMA_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0},
    }
    req = _rq.Request(OLLAMA_URL, data=json.dumps(body).encode(),
                      headers={"Content-Type": "application/json"})
    with _rq.urlopen(req, timeout=60) as r:
        out = json.loads(r.read())
    ans = out.get("message", {}).get("content", "").strip().upper()
    return ans.startswith("Y")


def _soft_token_sim(a, b):
    """Symmetric, length-normalized character-level token similarity. Each token
    in A is matched to its most similar token in B (and vice versa) by character
    ratio, then averaged over BOTH lengths so differing word counts aren't
    penalized. Used only to RANK candidates for the LLM, never to decide matches:
    it just has to keep the correct GT name in the top-k the model sees. Because
    near-miss distractors (grasses vs herbs) still score non-zero, they fill out
    the candidate slots and the LLM rejects them."""
    at = [t for t in normalize(a).split()]
    bt = [t for t in normalize(b).split()]
    if not at or not bt:
        return 0.0
    def best(t, pool):
        return max(SequenceMatcher(None, t, w).ratio() for w in pool)
    fwd = sum(best(t, bt) for t in at) / len(at)
    bwd = sum(best(t, at) for t in bt) / len(bt)
    return (fwd + bwd) / 2.0


def llm_match(unmatched_pred, unmatched_gt, confirm=_ollama_yes,
              max_candidates=3, floor=0.35, report=None):
    """For each unmatched pred name, rank unmatched GT names by soft-token
    similarity, send the top `max_candidates` to the LLM, first YES wins.
    If even the best candidate scores below `floor`, skip the LLM entirely and
    leave the name unmatched (genuinely novel trait with no GT equivalent, e.g.
    DNA-accession columns) -- saves calls and avoids spurious matches.

    `report` (a dict, optional) collects what happened so the CALLER can say it
    out loud. Previously an Ollama failure returned silently and the evaluator
    printed no remap at all — indistinguishable from "the model said no to
    everything", which is how three traits could be reported as near-identical in
    the coverage table and as total misses in the score with no explanation.
    """
    mapping = {}
    rejected, error = [], None
    remaining_gt = list(unmatched_gt)
    for p in unmatched_pred:
        ranked = sorted(remaining_gt, key=lambda g: _soft_token_sim(p, g),
                        reverse=True)
        if not ranked or _soft_token_sim(p, ranked[0]) < floor:
            continue                      # nothing plausible -> stay unmatched
        if error:                         # LLM already down; don't keep trying
            rejected.append((p, ranked[0], "llm unavailable"))
            continue
        for g in ranked[:max_candidates]:
            try:
                if confirm(p, g):
                    mapping[p] = g
                    remaining_gt.remove(g)
                    break
                rejected.append((p, g, "llm said different traits"))
            except Exception as e:
                error = f"{type(e).__name__}: {e}"
                rejected.append((p, g, "llm unavailable"))
                break
    if report is not None:
        report["llm_error"] = error
        report["llm_rejected"] = rejected
    return mapping


def build_type_map(gt_names, pred_names, use_llm=True, return_report=False):
    """Full pipeline, cheapest and safest first:

      1. NORMALIZE-EQUAL   — casing/underscores/word order (no LLM, exact).
      2. CONTAINMENT       — one name is the other qualified, unambiguously
                             (no LLM, deterministic; see containment_match).
      3. LLM               — everything else that is at least plausible.

    Returns pred->gt dict, or (dict, report) with return_report=True. The report
    records which pass decided each pair and whether the LLM was reachable, so
    the evaluator can explain its own numbers instead of leaving a near-identical
    name silently unscored.
    """
    gt_names = sorted(set(gt_names)); pred_names = sorted(set(pred_names))
    report = {"by_pass": {}, "llm_error": None, "llm_rejected": []}

    mapping, un_pred, un_gt = deterministic_match(gt_names, pred_names)
    for p in mapping:
        report["by_pass"][p] = "normalize"

    contained, un_pred, un_gt = containment_match(un_gt, un_pred)
    for p, g in contained.items():
        report["by_pass"][p] = "containment"
    mapping.update(contained)

    if use_llm and un_pred and un_gt:
        by_llm = llm_match(un_pred, un_gt, report=report)
        for p in by_llm:
            report["by_pass"][p] = "llm"
        mapping.update(by_llm)
    elif not use_llm:
        report["llm_error"] = "disabled (use_llm=False)"

    report["unmatched_pred"] = [p for p in pred_names if p not in mapping]
    report["unmatched_gt"] = [g for g in gt_names if g not in set(mapping.values())]
    return (mapping, report) if return_report else mapping


if __name__ == "__main__":
    import sys
    data = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else {}
    print(json.dumps(build_type_map(data.get("gt", []), data.get("pred", []),
                                    use_llm=False), indent=2))