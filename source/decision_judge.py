"""
decision_judge.py — the evaluator's two LLM decisions, made by a DECISION model
(tev1:4b via Ollama's /v1/systemone) instead of free-form gemma replies.

The evaluator asks the LLM two things, and both are multiple choice:
  1. which ground-truth trait name is the SAME trait as a predicted one (or none)
  2. how severe a missed row is (trivial / minor / moderate / severe)

A decision model answers each with a probability per allowed answer: no JSON to
break, up to 64 questions per call, and a number we can threshold and print, so
a borderline match is visible ('p=0.55') instead of silently flipping between
machines. Selected with ``evaluate.py --judge tev1`` (or EVAL_JUDGE=tev1); the
gemma judge stays the default. Needs Ollama >= 0.35.
"""

from __future__ import annotations

import json
import os
from urllib import error as _er
from urllib import request as _rq

DECISION_URL = "http://127.0.0.1:11434/v1/systemone"
DECISION_MODEL = os.environ.get("EVAL_DECISION_MODEL", "tev1:4b")
MAX_QUESTIONS = 64           # per request (endpoint limit)
# A match is accepted only when the model puts at least this much probability on
# one ground-truth name AND that name beats 'none'. Tunable; printed per match.
MIN_MATCH_PROB = float(os.environ.get("EVAL_MATCH_PROB", "0.5"))
NONE_LABEL = "none of these"


def _ask_once(state: str, questions: dict, timeout: int) -> dict:
    body = {"model": DECISION_MODEL, "state": state, "questions": questions}
    req = _rq.Request(DECISION_URL, data=json.dumps(body).encode(),
                      headers={"Content-Type": "application/json"})
    with _rq.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read()).get("answers", {})


def ask(state: str, questions: dict, timeout: int = 300) -> dict:
    """/v1/systemone call(s). Returns the merged 'answers' dict.

    Every question is scored with the state AND the whole question set in its
    prompt, capped at ~8k tokens, so 64 long questions can be refused ('prompt 0
    has 11695 tokens', Raine2018 severity). On that refusal the set is split in
    half and each half asked separately, down to single questions."""
    try:
        return _ask_once(state, questions, timeout)
    except _er.HTTPError as e:
        msg = e.read().decode("utf-8", "replace")
        if e.code != 400 or "tokens" not in msg or len(questions) < 2:
            raise
        keys = list(questions)
        half = len(keys) // 2
        out = ask(state, {k: questions[k] for k in keys[:half]}, timeout)
        out.update(ask(state, {k: questions[k] for k in keys[half:]}, timeout))
        return out


def _batches(items, n=MAX_QUESTIONS):
    for i in range(0, len(items), n):
        yield items[i:i + n]


# --- 1. same-trait matching ------------------------------------------------------

_MATCH_STATE = (
    "Trait names from a biological species-trait table. Each question gives a "
    "PREDICTED trait name and candidate GROUND-TRUTH trait names. The same trait "
    "may be worded differently (abbreviations, units, word order, singular/plural, "
    "'mean'/'total'). Different structures, different measures of a structure, or "
    "different conditions are DIFFERENT traits.")


def decision_match(unmatched_pred, candidates: dict, report=None) -> dict:
    """{pred: gt} from one choice question per predicted name.

    ``candidates`` maps each predicted name to its ranked GT candidate names
    (the caller ranks by string similarity, as for the gemma judge). Accepted
    greedily by probability so each GT name is used once: the most confident
    pairs claim their name first."""
    scored = []                                   # (prob, pred, gt)
    preds = [p for p in unmatched_pred if candidates.get(p)]
    for chunk in _batches(preds):
        qs = {}
        for i, p in enumerate(chunk):
            crit = {g: None for g in candidates[p]}
            crit[NONE_LABEL] = "none of the candidates is the same trait"
            qs[f"q{i}"] = {"type": "choice",
                           "instructions": f"Predicted trait name: '{p}'. Which "
                                           f"ground-truth name is the SAME trait?",
                           "criteria": crit}
        answers = ask(_MATCH_STATE, qs)
        for i, p in enumerate(chunk):
            a = answers.get(f"q{i}") or {}
            probs = a.get("probabilities") or {}
            best = a.get("choice")
            if best and best != NONE_LABEL:
                scored.append((float(probs.get(best, 0.0)), p, best,
                               float(probs.get(NONE_LABEL, 0.0))))
    mapping, used, decisions = {}, set(), []
    for prob, p, g, p_none in sorted(scored, reverse=True):
        ok = prob >= MIN_MATCH_PROB and prob > p_none and g not in used and p not in mapping
        decisions.append((p, g, round(prob, 3), "accepted" if ok else "rejected"))
        if ok:
            mapping[p] = g
            used.add(g)
    if report is not None:
        report["decision_probs"] = decisions
        report["llm_rejected"] = [(p, g, f"tev1 p={pr}") for p, g, pr, s in decisions
                                  if s == "rejected"]
    return mapping


# --- 2. miss severity --------------------------------------------------------------

_SEVERITY_STATE = (
    "Grading extraction misses: for the SAME species and trait, the ground truth "
    "expected one value and the pipeline predicted another. Grade how severe the "
    "difference is. This does not change any score.")

_SEVERITY_CRITERIA = {
    "trivial": "same meaning, cosmetic only: authority or family text, "
               "punctuation, units written differently, spacing, 1 vs 1.0",
    "minor": "same quantity or category with a small real difference: rounding, "
             "unit conversion, near-synonym",
    "moderate": "related but not clearly the same: another measure of the same "
                "structure, a partial value",
    "severe": "wrong: different species, different trait, or unrelated value",
}


_SAME_CRITERIA = {"true": "same value: any difference is cosmetic (formatting, "
                           "rounding, authority/family text, units written differently)",
                   "false": "different value, trait or species"}

# p(same value) -> the old four labels, so the misses CSV keeps its vocabulary
_SEVERITY_BANDS = ((0.8, "trivial"), (0.5, "minor"), (0.2, "moderate"), (0.0, "severe"))


def decision_severity(items) -> dict:
    """{n: (severity, reasoning)} for items with n, gt_species, measurementType,
    gt_value, pred_value — the same contract as the gemma batch grader.

    One TRUE/FALSE question per miss: 'is the predicted value the same as the
    ground truth?'. Its probability IS the severity (1 = cosmetic, 0 = wrong),
    banded into the old labels and kept in the reasoning so the misses CSV can be
    sorted by it. A short boolean question also packs more misses per call than
    a four-way grade with long category descriptions."""
    got = {}
    for chunk in _batches(list(items)):
        qs = {}
        for i, it in enumerate(chunk):
            qs[f"q{i}"] = {"type": "noul",
                           "instructions": (f"Species '{it['gt_species']}', trait "
                                            f"'{it['measurementType']}': ground truth "
                                            f"= '{it['gt_value']}', predicted = "
                                            f"'{it['pred_value'] or '(nothing)'}'. "
                                            f"Is the predicted value the same?"),
                           "criteria": dict(_SAME_CRITERIA)}
        answers = ask(_SEVERITY_STATE, qs)
        for i, it in enumerate(chunk):
            p = (answers.get(f"q{i}") or {}).get("noul")
            if p is None:
                continue
            p = float(p)
            sev = next(label for cut, label in _SEVERITY_BANDS if p >= cut)
            got[it["n"]] = (sev, f"p_same={p:.2f} ({DECISION_MODEL})")
    return got
