"""
meaning.py — EXPERIMENT: what a column's name means, from the paper itself.

Code finds, nimble decides:
  candidates  code looks up the column's name — the whole name, and each token that
              looks like an abbreviation ('HW', 'CTmax', 'HW1', 'Overw.') — in the
              paper text with the pipeline's definition shapes (tables._ABBREV_SHAPES:
              'term (ABBR)', 'ABBR = term', glossary 'ABBR: term; ...'). Every shape
              is tried, so one token can bring several candidates. Code never makes a
              meaning up: each candidate is quoted with the passage that defines it.
  QM          one multiple-choice question per column that has candidates, asked on
              its own (questions batched together shift each other's answers):
              which candidate does the column name mean in this paper — or none?
  details     the same for the labels under a name ('M', 'V' under 'CL'): their
              meaning becomes the column's statistic or other detail.

A column with no candidate gets no question; it is listed as unresolved.
"""

from __future__ import annotations

import re

import _paths  # noqa: F401  (puts source/ on the path)
from tables import _ABBREV_SHAPES
from text_manager import strip_inline_markup

QUOTE_W = 160


def looks_abbreviated(tok: str) -> bool:
    """The trigger for a look-up (it picks WHAT to look up, it decides nothing):
    short tokens with two capitals, letters with digits, or a cut word ('Overw.')."""
    t = tok.rstrip(".")
    if not t or len(t) > 8:
        return False
    caps = sum(ch.isupper() for ch in t)
    return caps >= 2 or (caps >= 1 and any(ch.isdigit() for ch in t)) or \
        (tok.endswith(".") and len(t) >= 3) or (len(t) == 1 and t.isupper())


def tokens_of(name: str) -> list:
    """The strings looked up for one column name: the name without units in
    brackets, and its abbreviation-like tokens."""
    base = re.sub(r"\s*[\(\[][^)\]]*[\)\]]", "", name or "").strip()
    out = [base] if base else []
    for tok in re.findall(r"[A-Za-z][A-Za-z0-9]*\.?", name or ""):
        if looks_abbreviated(tok) and tok not in out:
            out.append(tok.rstrip(".") if not tok.endswith(".") else tok)
    return out


def _quote(text, term, token):
    """The passage where the paper defines the term (for the question)."""
    for pat in (re.escape(term), re.escape(token)):
        m = re.search(pat, text, flags=re.I)
        if m:
            a, b = max(0, m.start() - QUOTE_W // 2), min(len(text), m.end() + QUOTE_W // 2)
            return " ".join(text[a:b].split())
    return ""


def candidates(text: str, name: str) -> list:
    """[{"token", "term", "shape", "quote"}] — every definition the paper gives for
    the name or its abbreviation-like tokens, one per distinct term."""
    out, seen = [], set()
    for tok in tokens_of(name):
        lookups = [tok, tok.rstrip(".")] if tok.endswith(".") else [tok]
        for look in lookups:
            for shape, fn in _ABBREV_SHAPES:
                try:
                    term = fn(look, text)
                except re.error:
                    term = None
                if not term:
                    continue
                term = " ".join(term.split())
                k = re.sub(r"[^a-z0-9]", "", term.lower())   # 'Weber’s' = 'Weber s'
                if k in seen or k == re.sub(r"[^a-z0-9]", "", look.lower()):
                    continue
                seen.add(k)
                out.append({"token": look, "term": term, "shape": shape,
                            "quote": _quote(text, term, look)})
    return out


def paper_text(paper):
    full = _paths.PAPERS / paper / f"{paper}_full.md"
    return strip_inline_markup(full.read_text(encoding="utf-8", errors="replace"))


def ask_meaning(client, name, context, cands):
    """QM: which candidate the column name means, or none. -> (term | None, p, probs)"""
    crit = {f"c{i}": f"'{c['term']}' — the paper: \"{c['quote'][:QUOTE_W]}\""
            for i, c in enumerate(cands)}
    crit["none"] = f"none of these: '{name}' does not mean any of them in this paper"
    state = (f"A column of a table in a scientific paper is named '{name}'"
             + (f" ({context})" if context else "") + ". Passages of the paper that define "
             "terms are quoted in the options.")
    q = {"q": {"type": "choice",
               "instructions": f"In this paper, what does the column name '{name}' mean?",
               "criteria": crit}}
    a = client.ask(lambda size: state, q).get("q") or {}
    ch = a.get("choice")
    probs = {k: round(float(v or 0), 3) for k, v in (a.get("probabilities") or {}).items()}
    p = probs.get(ch, 0.0)
    if not ch or ch == "none":
        return None, p, probs
    return cands[int(ch[1:])]["term"], p, probs


def read_meanings(client, text, columns):
    """columns: head-reader columns of one table. -> {col: {...}} with the meaning of
    the name and of each detail under it."""
    out, asked = {}, {}
    for col in columns:
        name = col.get("name") or ""
        if not name:
            continue
        ctx = " / ".join(col.get("groups", []))
        rec = {"name": name, "candidates": candidates(text, name), "meaning": None,
               "p": None, "details": {}}
        if rec["candidates"]:
            key = (name, ctx)
            if key not in asked:                         # the same name asked once per table
                asked[key] = ask_meaning(client, name, f"under '{ctx}'" if ctx else "",
                                         rec["candidates"])
            rec["meaning"], rec["p"], rec["probs"] = asked[key]
        for d in col.get("details", []):
            dc = candidates(text, d)
            if not dc:
                rec["details"][d] = None
                continue
            key = (d, name)
            if key not in asked:
                asked[key] = ask_meaning(client, d, f"under the column name '{name}'", dc)
            rec["details"][d] = asked[key][0]
        out[col["col"]] = rec
    return out


# --- version 2: one question per TOKEN, the original header kept -------------------

QUOTE_W2 = 320


def well_formed(term: str) -> bool:
    """Objective parse checks on a finder result (they drop artefacts such as
    'HW2-HW1)'; they judge nothing about meaning): starts with a letter, has at
    least three letters, brackets balanced."""
    term = term.strip()
    if not term or not term[0].isalpha() or sum(ch.isalpha() for ch in term) < 3:
        return False
    return all(term.count(o) == term.count(c) for o, c in ("()", "[]"))


def _quote2(text, term, token):
    """A longer passage, preferring one where the term and the token both appear."""
    best = ""
    words = re.findall(r"[A-Za-z0-9]+", term)        # 'Weber s length' finds 'Weber’s length'
    pat = r"[^A-Za-z0-9]+".join(map(re.escape, words)) if words else re.escape(term)
    for m in re.finditer(pat, text, flags=re.I):
        a, b = max(0, m.start() - QUOTE_W2 // 2), min(len(text), m.end() + QUOTE_W2 // 2)
        win = " ".join(text[a:b].split())
        if re.search(r"(?<![A-Za-z0-9])" + re.escape(token) + r"(?![A-Za-z0-9])", win):
            return win
        best = best or win
    return best


def token_candidates(text: str, token: str) -> list:
    out, seen = [], set()
    looks = [token, token.rstrip(".")] if token.endswith(".") else [token]
    for look in looks:
        for shape, fn in _ABBREV_SHAPES:
            try:
                term = fn(look, text)
            except re.error:
                term = None
            if not term:
                continue
            term = " ".join(term.split())
            k = re.sub(r"[^a-z0-9]", "", term.lower())
            if k in seen or k == re.sub(r"[^a-z0-9]", "", look.lower()) or not well_formed(term):
                continue
            seen.add(k)
            out.append({"term": term, "shape": shape, "quote": _quote2(text, term, look)})
    return out


def ask_token(client, token, name, context, cands):
    """QM2: what the token means in this column, or none. -> (term | None, probs)"""
    crit = {f"c{i}": f"'{c['term']}' — the paper: \"{c['quote']}\"" for i, c in enumerate(cands)}
    crit["none"] = f"none of these: the paper does not define '{token}' as any of them"
    where = f"the column '{name}'" + (f" ({context})" if context else "")
    state = (f"A column of a table in a scientific paper is named '{name}'. Passages of "
             f"the paper that define terms are quoted in the options.")
    q = {"q": {"type": "choice",
               "instructions": f"In {where}, what does '{token}' mean in this paper?",
               "criteria": crit}}
    a = client.ask(lambda size: state, q).get("q") or {}
    ch = a.get("choice")
    probs = {k: round(float(v or 0), 3) for k, v in (a.get("probabilities") or {}).items()}
    if not ch or ch == "none":
        return None, probs
    return cands[int(ch[1:])]["term"], probs


def expand(name: str, meanings: dict) -> str:
    """The header with each resolved token written out; the original stays apart.
    A resolved whole name (without its units) becomes its term."""
    base = re.sub(r"\s*[\(\[][^)\]]*[\)\]]", "", name or "").strip()
    if meanings.get(base):
        return meanings[base]
    out = name
    for tok, term in meanings.items():
        if term and tok != base:
            out = re.sub(r"(?<![A-Za-z0-9])" + re.escape(tok) + r"(?![A-Za-z0-9])", term, out)
    return out


def read_label(client, text, name, context="", cache=None):
    """Token-level meanings of one label. -> {"name", "tokens": {tok: term|None},
    "candidates": {tok: [...]}, "expanded", "unresolved": [abbreviation-like tokens
    with no accepted meaning], "probs": {tok: {...}}}"""
    cache = {} if cache is None else cache
    rec = {"name": name, "tokens": {}, "candidates": {}, "probs": {}, "unresolved": []}
    for tok in tokens_of(name):
        cands = token_candidates(text, tok)
        if cands:
            key = (tok, name, context)
            if key not in cache:
                cache[key] = ask_token(client, tok, name, context, cands)
            rec["tokens"][tok], rec["probs"][tok] = cache[key]
            rec["candidates"][tok] = cands
        elif looks_abbreviated(tok):
            rec["tokens"][tok] = None
    base = re.sub(r"\s*[\(\[][^)\]]*[\)\]]", "", name or "").strip()
    rec["unresolved"] = [t for t, v in rec["tokens"].items()
                         if v is None and looks_abbreviated(t) and not rec["tokens"].get(base)]
    rec["expanded"] = expand(name, rec["tokens"])
    return rec
