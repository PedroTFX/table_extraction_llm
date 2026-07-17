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
              max_candidates=3, floor=0.35):
    """For each unmatched pred name, rank unmatched GT names by soft-token
    similarity, send the top `max_candidates` to the LLM, first YES wins.
    If even the best candidate scores below `floor`, skip the LLM entirely and
    leave the name unmatched (genuinely novel trait with no GT equivalent, e.g.
    DNA-accession columns) -- saves calls and avoids spurious matches."""
    mapping = {}
    remaining_gt = list(unmatched_gt)
    for p in unmatched_pred:
        ranked = sorted(remaining_gt, key=lambda g: _soft_token_sim(p, g),
                        reverse=True)
        if not ranked or _soft_token_sim(p, ranked[0]) < floor:
            continue                      # nothing plausible -> stay unmatched
        for g in ranked[:max_candidates]:
            try:
                if confirm(p, g):
                    mapping[p] = g
                    remaining_gt.remove(g)
                    break
            except Exception:
                return mapping   # Ollama unreachable -> keep what we have, stop
    return mapping


def build_type_map(gt_names, pred_names, use_llm=True):
    """Full pipeline: deterministic then (optionally) LLM. Returns pred->gt dict."""
    gt_names = sorted(set(gt_names)); pred_names = sorted(set(pred_names))
    mapping, un_pred, un_gt = deterministic_match(gt_names, pred_names)
    if use_llm and un_pred and un_gt:
        mapping.update(llm_match(un_pred, un_gt))
    return mapping


if __name__ == "__main__":
    import sys
    data = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else {}
    print(json.dumps(build_type_map(data.get("gt", []), data.get("pred", []),
                                    use_llm=False), indent=2))
