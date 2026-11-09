"""
decoder_v2.py — EXPERIMENT: decoder v2. v1 (decoder.py) stays frozen as the baseline.

The four changes, each a hypothesis from v1's held-out misses (2026-10-12):
  1. LABEL vs EXPLANATION — gemma returns the category's name ('none') apart from the
     printed wording that explains it ('only defence of the nest'). The label is the
     candidate output; the explanation is kept for the question and the record.
  2. INITIAL-BASED candidates (a fallback tier) — when no entry prints the cell's code,
     categories whose label starts with / has the initials of the cell ('G' ->
     'Ground nesting', 'TS' -> 'typical specialists') are offered, marked as such.
     The paper does not pair them: nimble decides, and 'keep' is always offered.
     gemma is also asked for categories the paper names WITHOUT codes
     ('pollen specialization (oligolectic, polylectic)').
  3. RETRIEVAL — code forms with arrows / '=' ('→1'); small tables cut into 10-line
     pieces and a slightly larger budget, so a dictionary table is not crowded out
     by one long paragraph (Wölfling).
  4. KEY — 0/1 -> no/yes without a printed mapping is out of reach
     (decode_key.where, 'binary convention'); v1 rescored on the same key.

Evidence classes on every candidate and every decoded cell:
  explicit   the paper prints this code with this label
  initial    the paper names this category; the code is only its initial(s)
  (none)     no supported candidate: the printed value is kept

The development set is every coded paper of the --all key (the 8 v1-dev papers and the
25 v1-held-out papers). A final estimate needs papers not used to build v2.

    python decoder_v2.py organise [papers...]   # gemma -> OUT/organise/
    python decoder_v2.py match [papers...]      # nimble -> OUT/match/
    python decoder_v2.py score                  # -> OUT/SCORE.txt
"""

from __future__ import annotations

import collections
import json
import re
import sys
import time

import column_tree as ct
import decode_key as dk
import decoder as v1
import header_tree as ht
import header_tree_bench as hb
import column_role_bench as crb
import _paths
from evaluate import load_xlsx
from fill_template import _looks_like_code

OUT = dk.OUT / "decoder_v2"
PREV = None          # a run whose organise results may be reused (set by main)
COL_CHARS = 4000
TABLE_LINES = 10
MAX_OPTIONS = 15
WHOLE_FIRST = False  # decoder v3 sets True: a list cell printed whole as a code is not split
BATCH = 10
ARROWS = "→←⇒⇐=:–-†‡§¶*#"   # arrows, '=', footnote markers ('†S' is S)


# --- 3. retrieval ------------------------------------------------------------------

def forms(code):
    """v1's forms plus the code with arrows / '=' / ':' around it removed ('→1' -> '1')."""
    out = list(v1.forms(code))
    for f in list(out):
        bare = f.strip(ARROWS + " ")                     # '‡M(O)' -> 'M(O)'
        for core in (bare, bare.strip("()[]{} .")):
            if core and core not in out:
                out.append(core)
                if re.fullmatch(r"-?\d+[.,]0+", core):
                    out.append(re.split(r"[.,]", core)[0])
    return [x for x in dict.fromkeys(out) if x]


def same_form(a, b):
    fa = {f.lower() for f in forms(a)}
    return any(f.lower() in fa for f in forms(b))


def paragraphs(paper, grids, k):
    """v1's passages, with small tables cut into TABLE_LINES pieces."""
    out = [(s, p) for s, p in v1.paragraphs(paper, grids, k) if not s.startswith("table ")]
    for j, gj in grids.items():
        if j == k or gj.ncols > 4:
            continue
        lines = []
        for r in range(gj.nrows):
            cells = []
            for cc in range(gj.ncols):
                x = gj.at(r, cc)
                if x and (x.r, x.c) == (r, cc) and str(x.text or "").strip():
                    cells.append(" ".join(str(x.text).split()))
            if cells:
                lines.append(" | ".join(cells))
        for i in range(0, len(lines), TABLE_LINES):
            out.append((f"table {j}", "\n".join(lines[i:i + TABLE_LINES])))
    return out


def legend_cells(passage, values):
    """How many of the column's values a small-table passage prints as WHOLE cells
    ('→1', '(G)'): a legend table. Geometry, not meaning."""
    cells = [c.strip() for line in passage.split("\n") for c in line.split(" | ")]
    return sum(any(c and same_form(c, v) for c in cells) for v in set(values))


def gather(paras, header, values):
    """v1's scoring, but small tables printing >= 2 of the values as whole cells are
    taken first (Wölfling's habitat legend lost to wordy prose that repeats the
    header's words; v2d)."""
    first = [i for i, (s, p) in enumerate(paras)
             if s.startswith("table ") and legend_cells(p, values) >= 2]
    pats = []
    for v in values:
        for part in v1.list_parts(v):
            if not _looks_like_code(part):
                continue
            fs = forms(part)
            pats.append((0.3 if any(f.isdigit() for f in fs) else 1.0, [v1.token_re(f) for f in fs]))
    names = [re.compile(re.escape(w), re.I) for w in re.findall(r"[A-Za-z]{4,}", header)]

    def score(p):
        hits = sum(w for w, rs in pats if any(r.search(p) for r in rs))
        return hits + 2 * sum(bool(n.search(p)) for n in names) if hits else 0
    ranked = sorted(((score(p), i) for i, (_s, p) in enumerate(paras)), key=lambda x: (-x[0], x[1]))
    keep, used = [], 0
    for i in first:
        if used + len(paras[i][1]) <= COL_CHARS:
            keep.append(i)
            used += len(paras[i][1])
    for s, i in ranked:
        if i in keep or s < 1 or used + len(paras[i][1]) > COL_CHARS:
            continue
        keep.append(i)
        used += len(paras[i][1])
    return sorted(keep)


# --- column view -------------------------------------------------------------------

def column_view(paper, k, c, grid, gt):
    """v1's view, but the header is every header text over the columns the column's BODY
    cells span: Lizee's HTML shifts header and body colspans by one, so the 'TG' cells
    (cols 5-6) sit under 'Larval diet' (4-5) and 'Functional group' (6-7); code cannot
    tell which, so both are shown."""
    header, values = v1.column_view(paper, k, c, grid, gt)
    r0 = next((r for r in range(grid.nrows)
               if any(gt.match_id(str(grid.at(r, cc).text or "")) for cc in range(grid.ncols)
                      if grid.at(r, cc))), 1)
    cols = {c}
    for r in range(r0, min(grid.nrows, r0 + 5)):
        x = grid.at(r, c)
        if x and x.colspan < grid.ncols:
            cols |= set(range(x.c, x.c + x.colspan))
    if cols == {c}:
        return header, values
    head = []
    for r in range(r0):
        for cc in sorted(cols):
            x = grid.at(r, cc)
            t = " ".join(str(x.text or "").split()) if x else ""
            if t and t not in head and x.colspan < grid.ncols:
                head.append(t)
    return " / ".join(head) or header, values


def inherited_header(paper, k, c, grids, gt):
    """A table with no header rows is a continuation page (Wallon t28, Taillefer t8...):
    the column's header is taken from the nearest EARLIER table of the same width that
    has header rows. Geometry only (column count, order in the paper)."""
    for j in range(k - 1, -1, -1):
        if grids[j].ncols != grids[k].ncols:
            continue
        h, _v = column_view(paper, j, c, grids[j], gt)
        if h.strip():
            return h
    return ""


def key_columns(paper, key):
    gt = crb.GroundTruth(load_xlsx(crb.paper_inputs(_paths.PAPERS / paper)[1]))
    grids = {k: ht.grid_from_html(h) for k, h in enumerate(hb.html_tables(paper))}
    out, seen = [], set()
    for T, e in key.get(paper, {}).items():
        if (e["table"], e["col"]) in seen:
            continue
        seen.add((e["table"], e["col"]))
        header, values = column_view(paper, e["table"], e["col"], grids[e["table"]], gt)
        if not header.strip():
            header = inherited_header(paper, e["table"], e["col"], grids, gt)
        out.append((e["table"], e["col"], header, values[:25], e))
    return out


# --- 1. gemma, three passes ------------------------------------------------------------
# v2a (one prompt asking for variable/code/label/explanation together) extracted legends
# worse than v1: codes landed in 'label' (Espinosa 'og', Habustova 'A', Keller 'M'),
# legends were replaced by trait names (Cappellari C/NC lost). v2b splits the work:
#   A  v1's legend prompt, unchanged, on v2's passages -> {variable, code, term}
#   B  per paper, one call over A's verified entries: the category's name inside each
#      printed term; code keeps it only when it is a contiguous piece of the term
#   C  categories the passages name WITHOUT codes (for the initial-based tier)

def _wb(term, text):
    """Spans where the words of `term` are printed as whole words (punctuation/case
    aside): 'hundred' is not printed inside 'hundreds'."""
    words = re.findall(r"[^\W_]+", term)
    if not words:
        return []
    pat = re.compile(r"(?<![^\W_])" + r"[\W_]+".join(map(re.escape, words)) + r"(?![^\W_])", re.I)
    return [(m.start(), m.end()) for m in pat.finditer(text)]


def _chat(prompt, schema, field, timeout=900):
    import urllib.request as _rq
    body = {"model": v1.GEMMA, "stream": False, "format": schema, "think": False,
            "messages": [{"role": "user", "content": prompt}],
            "options": {"temperature": 0, "num_ctx": 16384}}
    for attempt in range(3):
        try:
            req = _rq.Request("http://127.0.0.1:11434/api/chat", data=json.dumps(body).encode(),
                              headers={"Content-Type": "application/json"})
            with _rq.urlopen(req, timeout=timeout) as r:
                msg = json.loads(r.read()).get("message", {}).get("content", "")
            got = json.loads(msg)
            return got.get(field, []) if isinstance(got, dict) else []
        except json.JSONDecodeError:
            return []
        except Exception:
            if attempt == 2:
                raise
            time.sleep(10 * (attempt + 1))


LABELS = """Each numbered line is a legend entry from a scientific paper: a code and the printed words the paper gives for it.

For each entry, give the category's NAME: the shortest part of the printed words that names the category, copied exactly. Leave out explanations, examples and remarks (in brackets, after a colon or comma, or around the name such as "species that ..."). If the printed words are already just a name, give them unchanged.
  "SO" = "solitary species nesting alone"      -> "solitary"
  "2" = "thousands of workers per colony"       -> "thousands"
  "P" = "polyphagous"                          -> "polyphagous"

Entries:
{entries}

Reply with JSON only."""

LABELS_SCHEMA = {"type": "object", "required": ["labels"],
                 "properties": {"labels": {"type": "array", "items": {
                     "type": "object", "required": ["n", "label"],
                     "properties": {"n": {"type": "integer"}, "label": {"type": "string"}}}}}}

UNCODED = """Below are passages from a scientific paper: prose paragraphs, footnotes of tables, and small tables (cells separated by ' | ').

List the CATEGORIES the passages name for a trait WITHOUT giving them any code, abbreviation or number — for example "pollen specialization (oligolectic, polylectic)" names two categories, 'oligolectic' and 'polylectic', of 'pollen specialization'; a table row "Ground nesting | Majority of species nest in the soil" names the category 'Ground nesting'.

For each category give:
- variable: the trait it belongs to, in the paper's words ("" if not said)
- label: the category's name, copied exactly as printed

One item per category. Skip anything that has a code in a legend, and skip places, methods and statistics.

Passages:
{passages}

Reply with JSON only."""

UNCODED_SCHEMA = {"type": "object", "required": ["categories"],
                  "properties": {"categories": {"type": "array", "items": {
                      "type": "object", "required": ["variable", "label"],
                      "properties": {"variable": {"type": "string"}, "label": {"type": "string"}}}}}}


def verify_a(entry, text):
    """v1.verify with v2's code forms (footnote markers and arrows stripped: gemma
    copied Ambsperg's '†S', '‡H', which v1's forms could not find printed)."""
    term, code = entry["term"].strip(), entry["code"].strip()
    if not term or not code:
        return "empty"
    if not re.search(r"[^\W_]", term):
        return "term has no words"
    near = [v1.token_re(f) for f in forms(code)]
    for a, b in v1._printed(term, text):
        if any(r.search(text[max(0, a - v1.NEAR): b + v1.NEAR]) for r in near):
            return ""
    phrase, r = v1._closest(term, text, near)
    if r >= v1.REPAIR:
        entry["model_term"], entry["term"] = term, " ".join(phrase.split())
        return ""
    return "term not printed near the code" if v1._printed(term, text) else "term not printed"


def strip_own_code(e):
    """A parse check: gemma sometimes copies the code into the term ('G = grasses' for
    code 'G', Teder2020). A term that starts with its own code and '=' / ':' / a dash
    keeps only what follows. Returns the entry (updated)."""
    code = str(e.get("code") or "").strip()
    if not code:
        return e
    pat = re.compile(r"^\s*" + re.escape(code) + r"\s*[=:–—-]\s*(\S.*)$", re.S)
    for f in ("term", "label"):
        m = pat.match(str(e.get(f) or ""))
        if m:
            e.setdefault("model_" + f + "_with_code", e[f])
            e[f] = m.group(1).strip()
    return e


def label_of(term, label):
    """B's label is kept only when it is a contiguous piece of the printed term (word
    boundaries); else the whole term stays the label. -> (label, explanation)"""
    label = " ".join(str(label or "").split())
    spans = _wb(label, term) if label else []
    if not spans:
        return term, ""
    a, b = spans[0]
    rest = (term[:a] + " " + term[b:]).strip(" ,;:()[]-–—")
    return term[a:b], " ".join(rest.split())


def organise(paper, columns, cached=None):
    """cached: an earlier result; reused as is when the passages come out the same
    (no gemma call, so its run-to-run drift stays out of the comparison)."""
    grids = {k: ht.grid_from_html(h) for k, h in enumerate(hb.html_tables(paper))}
    chosen, paras_by = [], {}
    for k, c, header, values in columns:
        if k not in paras_by:
            paras_by[k] = paragraphs(paper, grids, k)
        for i in gather(paras_by[k], header, values):
            s, p = paras_by[k][i]
            label = s if s != "table footnote" else f"footnote of table {k}"
            if (label, p) not in chosen:
                chosen.append((label, p))
    calls, cur = [], []
    for label, p in chosen:
        piece = f"[{label}] {p}"
        if cur and sum(len(x) for x in cur) + len(piece) > v1.CALL_CHARS:
            calls.append(cur)
            cur = []
        cur.append(piece[:v1.CALL_CHARS])
    if cur:
        calls.append(cur)
    if cached and cached.get("passages") == [x for p in calls for x in p]:
        return {**cached, "reused": True}
    entries, dropped, uncoded = [], [], []
    for part in calls:
        text = "\n\n".join(part)
        for e in v1.gemma(v1.ORGANISE.format(passages=text)):             # A
            e = {k2: " ".join(str(e.get(k2) or "").split()) for k2 in ("variable", "code", "term")}
            why = verify_a(e, text)
            strip_own_code(e)
            (dropped if why else entries).append({**e, **({"why": why} if why else {})})
        for e in _chat(UNCODED.format(passages=text), UNCODED_SCHEMA, "categories"):   # C
            lab = " ".join(str(e.get("label") or "").split())
            if lab and re.search(r"[^\W\d_]{3,}", lab) and _wb(lab, text):
                uncoded.append({"variable": " ".join(str(e.get("variable") or "").split()),
                                "code": "", "label": lab, "explanation": "", "evidence": "named"})
            elif lab:
                dropped.append({"variable": e.get("variable", ""), "code": "", "term": lab,
                                "why": "uncoded label not printed as whole words"})
    seen, cats = set(), []
    for e in entries:
        key = (e["variable"].lower(), e["code"], e["term"].lower())
        if key not in seen:
            seen.add(key)
            cats.append(e)
    if cats:                                                                # B
        listing = "\n".join(f"{i}. \"{e['code']}\" = \"{e['term']}\"" for i, e in enumerate(cats, 1))
        got = {int(x.get("n", 0)): x.get("label") for x in
               _chat(LABELS.format(entries=listing), LABELS_SCHEMA, "labels") if isinstance(x, dict)}
        for i, e in enumerate(cats, 1):
            e["model_label"] = got.get(i)
            e["label"], e["explanation"] = label_of(e["term"], got.get(i))
    have = {e["label"].lower() for e in cats}
    seen_u = set()
    for e in uncoded:
        if e["label"].lower() not in have and e["label"].lower() not in seen_u:
            seen_u.add(e["label"].lower())
            cats.append(e)
    return {"calls": len(calls), "chars": sum(len(x) for p in calls for x in p),
            "passages": [x for p in calls for x in p], "categories": cats, "dropped": dropped}


# --- 2. candidates with evidence classes; nimble decides ----------------------------

def initials_match(value, label):
    """'G' / 'Ground nesting', 'TS' / 'typical specialists', 'Poly' / 'Polylectic':
    the value is the label's first letters, or the initials of its first words."""
    v = value.strip().strip(".").lower()
    if not v.isalpha() or len(v) > 4:
        return False
    words = re.findall(r"[^\W\d_]+", label.lower())
    if not words:
        return False
    if words[0].startswith(v):
        return True
    return len(v) > 1 and len(words) >= len(v) and "".join(w[0] for w in words[:len(v)]) == v


def prefixed(value, code, header):
    """The legend prints the cell's code behind a prefix that starts a word of the
    column's header: 'IngCC' / 'CC' under 'Mode of Ingestion' (Wallon). Geometry of the
    strings only; it decides which entries are offered, nimble decides."""
    v, c = value.strip(), code.strip()
    if not v or not c.endswith(v) or len(c) <= len(v):
        return False
    pre = c[: len(c) - len(v)].strip("_-. ").lower()
    return len(pre) >= 2 and any(w.lower().startswith(pre)
                                 for w in re.findall(r"[^\W\d_]+", header or ""))


def candidates(cats, value, header=""):
    """explicit entries (the code printed like the value) — or, only when there is none,
    initial-based ones. -> (evidence, [entries])"""
    out, seen = [], set()
    for e in cats:                   # one per printed TERM: Guariento's larval and pupal
        t = (e.get("term") or e["label"]).lower()   # entries share the label 'no hibernation'
        if e["code"] and (same_form(value, e["code"]) or prefixed(value, e["code"], header)) \
                and t not in seen:
            seen.add(t)
            out.append(e)
    if out:
        return "explicit", out            # no cut: QV batches long lists
    for e in cats:
        if not e["code"] and initials_match(value, e["label"]) and e["label"].lower() not in seen \
                and e["label"].lower() != value.strip().lower():
            seen.add(e["label"].lower())
            out.append(e)
    return ("initial", out) if out else (None, [])


def _option(p, e, evidence):
    """QV identifies the category. Explicit entries keep v1's tested wording ('code' =
    'whole printed term' (the paper's legend for ...)); v2b's rewording without the
    code made nimble keep codes v1 decoded (Arnan, Beyer, McCune). Initial-based
    entries say that no code is printed. Wording of the value is QB's job."""
    if evidence == "explicit":
        printed = f" (printed '{e['code']}' in the legend)" if e["code"] != p else ""
        var = f" — the paper's legend for '{e['variable']}'" if e["variable"] else ""
        if e.get("mark_note"):           # decoder v3 only: the footnote mark shared with the header
            var = " — " + e["mark_note"]
        return f"'{p}' = '{e.get('term') or e['label']}'{printed}{var}"
    var = f" (the paper's '{e['variable']}')" if e["variable"] else ""
    return (f"'{e['label']}'{var}: the paper names this category but prints no code for "
            f"it; '{p}' would be its initial(s)")


def wordings(e):
    """QB's options: gemma's label, the whole printed term, and the term cut at its first
    bracket / colon / comma / semicolon (code proposes the cut; nimble picks)."""
    term = e.get("term") or e["label"]
    out = [e["label"], term]
    cut = re.split(r"\s*[(:;,]", term, maxsplit=1)[0].strip()
    if cut and re.search(r"[^\W_]", cut):
        out.append(cut)
    return [w for w in dict.fromkeys(" ".join(x.split()) for x in out) if w]


def ask_wording(client, header, p, e):
    ws = wordings(e)
    if len(ws) == 1:
        return ws[0], {}
    crit = {f"w{i}": f"'{w}'" for i, w in enumerate(ws)}
    state = (f"A table in a scientific paper has a column named '{header}'. The paper's legend "
             f"gives '{e.get('code') or p}' = '{e.get('term') or e['label']}'. The cell value "
             f"'{p}' is to be recorded as the category's name, in the paper's own words.")
    ch, probs = v1.ask(client, state, f"Which wording is the name of the category that '{p}' "
                       f"stands for — without explanations, examples or remarks?", crit)
    return (ws[int(ch[1:])] if ch and ch.startswith("w") else ws[0]), probs


def _qv_once(client, state, header, p, es, evidence, idx):
    crit = {f"e{i}": _option(p, es[i], evidence) for i in idx}
    crit["keep"] = (f"none of these: '{p}' is already the paper's term (a word, not "
                    f"a code), or in the column '{header}' it does not stand for any "
                    f"of them; keep it as printed")
    return v1.ask(client, state, f"In the column '{header}', what does the cell "
                  f"value '{p}' stand for?", crit)


def qv(client, state, header, p, es, evidence):
    """QV. Up to MAX_OPTIONS candidates: one question, as before. More (Guariento prints
    a 0/1 legend for 18 variables; v2e's cut at 15 dropped 'Adult feeding'): nimble
    picks within batches of BATCH, then among the batch winners. Code drops nothing.
    -> (choice 'e<i>' | 'keep', probs)"""
    if len(es) <= MAX_OPTIONS:
        return _qv_once(client, state, header, p, es, evidence, range(len(es)))
    winners, probs = [], {}
    for b in range(0, len(es), BATCH):
        ch, pr = _qv_once(client, state, header, p, es, evidence, range(b, min(b + BATCH, len(es))))
        probs[f"batch {b // BATCH}"] = pr
        if ch and ch != "keep":
            winners.append(int(ch[1:]))
    if not winners:
        return "keep", probs
    if len(winners) == 1:
        return f"e{winners[0]}", probs
    ch, pr = _qv_once(client, state, header, p, es, evidence, winners)
    probs["final"] = pr
    return ch, probs


def match_column(client, header, values, cats, shown_values=None):
    """shown_values (decoder v3 only): the values the context lists, when only some of the
    column's cells are asked (cells past the first 25); default: the cells asked."""
    rec = {"cells": {}}
    shown = ", ".join(f"'{v}'" for v in (shown_values if shown_values is not None else values)[:25])
    state = (f"A table in a scientific paper has a column named '{header}'. Its cells hold "
             f"these values: {shown}.")
    asked, kinds, worded = {}, {}, {}
    for v in values:
        parts = v1.list_parts(v)
        if len(parts) > 1 and not all(candidates(cats, p, header)[1] for p in parts):
            parts = [v]
        elif len(parts) > 1 and WHOLE_FIRST and candidates(cats, v, header)[0] == "explicit":
            parts = [v]                  # the paper prints 'W/S' itself as a code
        labels, probs, options, evid = [], {}, {}, {}
        for p in parts:
            evidence, es = candidates(cats, p, header)
            if not es:
                labels.append(None)
                continue
            options[p] = {"evidence": evidence, "labels": [e["label"] for e in es]}
            if p not in kinds:
                # explicit: v1's QK exactly (v2c's reworded context made nimble call 'D',
                # 'GO', 'A' words at 0.92-0.98); initial-based: the named categories
                if evidence == "explicit":
                    defs = "; ".join(f"'{e['code']}' = '{e.get('term') or e['label']}'" for e in es[:3])
                    qk_state = (state + " The options quote the paper's definitions of a code "
                                "printed like the cell value, and the legend each one belongs to."
                                + f" The paper writes: {defs}.")
                    qk_q = (f"In the column '{header}', is the cell value '{p}' a code that "
                            f"stands for that term, or a word written out that the paper explains?")
                else:
                    defs = "; ".join(f"'{e['label']}'" for e in es[:3])
                    qk_state = state + f" The paper names these categories, without codes: {defs}."
                    qk_q = (f"In the column '{header}', is the cell value '{p}' a code that "
                            f"stands for a longer term, or a word written out?")
                kinds[p] = v1.ask(client, qk_state, qk_q, {
                    "code": f"a code: '{p}' is a letter, abbreviation, symbol or number that "
                            f"stands for the longer term",
                    "word": f"written out: '{p}' is already the term itself, an ordinary word or "
                            f"phrase; the paper only explains what it means"})
            probs[p + " | QK"] = kinds[p][1]
            if kinds[p][0] != "code":
                labels.append(None)
                continue
            if p not in asked:
                note = (" The options quote the paper's definitions of a code printed like the "
                        "cell value, and the legend each one belongs to." if evidence == "explicit"
                        else " The options are categories the paper names without printing a code.")
                asked[p] = qv(client, state + note, header, p, es, evidence)
            ch, pr = asked[p]
            probs[p] = pr
            if ch and ch != "keep":
                e = es[int(ch[1:])]
                if (p, id(e)) not in worded:
                    worded[(p, id(e))] = ask_wording(client, header, p, e)
                labels.append(worded[(p, id(e))][0])
                probs[p + " | QB"] = worded[(p, id(e))][1]
                evid[p] = evidence
            else:
                labels.append(None)
        term = None
        if any(t is not None for t in labels):
            term = "; ".join(t if t is not None else p for t, p in zip(labels, parts))
        if options:
            rec["cells"][v] = {"term": term, "parts": parts, "options": options,
                               "evidence": evid, "probs": probs}
    return rec


# --- commands ------------------------------------------------------------------------

def cmd_organise(papers):
    key = v1.load_key()
    (OUT / "organise").mkdir(parents=True, exist_ok=True)
    for paper in papers:
        f = OUT / "organise" / f"{paper}.json"
        if f.exists():
            continue
        prev = PREV / "organise" / f"{paper}.json" if PREV else None
        cached = json.loads(prev.read_text(encoding="utf-8")) if prev and prev.exists() else None
        cols = [(k, c, h, v) for k, c, h, v, _e in key_columns(paper, key)]
        t0 = time.time()
        res = organise(paper, cols, cached)
        res["seconds"] = round(time.time() - t0, 1)
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  {paper:22s} {res['calls']} call(s) {res['chars']:>6d} chars  "
              f"{len(res['categories'])} kept ({sum(not e['code'] for e in res['categories'])} without code), "
              f"{len(res['dropped'])} dropped  ({res['seconds']}s){' reused' if res.get('reused') else ''}", flush=True)
    v1.unload(v1.GEMMA)


def cmd_match(papers):
    key = v1.load_key()
    (OUT / "match").mkdir(parents=True, exist_ok=True)
    client = ct.DecisionClient(v1.NIMBLE, 1)
    for paper in papers:
        f = OUT / "match" / f"{paper}.json"
        org = OUT / "organise" / f"{paper}.json"
        if f.exists() or not org.exists():
            continue
        cats = json.loads(org.read_text(encoding="utf-8"))["categories"]
        t0, c0 = time.time(), client.calls
        res = {}
        for k, c, header, values, _e in key_columns(paper, key):
            r = match_column(client, header, values, cats)
            r["header"] = header
            res[f"{k}:{c}"] = r
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  {paper:22s} {client.calls - c0} question(s)  ({time.time() - t0:.0f}s)", flush=True)
    v1.unload(v1.NIMBLE)


def _contains(have, want):
    """The GT's words are a contiguous piece of the decoded wording ('species that are
    primarily monogynous' holds 'primarily monogynous')."""
    h, w = f" {v1._flat(have)} ", f" {v1._flat(want)} "
    return w.strip() != "" and w in h and h != w


def score_dir(out_dir, papers_dev_v1):
    """Outcome per key pair, weighted by species rows (cells) and per distinct cell
    (pairs); the evidence class of every decoded cell."""
    key = v1.load_key()
    rows = []
    for paper in sorted(key):
        f = out_dir / "match" / f"{paper}.json"
        if not f.exists():
            continue
        got = json.loads(f.read_text(encoding="utf-8"))
        side = "v1-dev" if paper in papers_dev_v1 else "v1-held-out"
        rows += [{**r, "side": side} for r in
                 score_dir_from(paper, key[paper], lambda e: got.get(f"{e['table']}:{e['col']}", {}))]
    return rows


def score_dir_from(paper, entries, record_of):
    """The scoring of one paper's key columns; record_of(key entry) gives what was
    decoded for that column ({"cells": ...}), or None when nothing decoded it — then
    every coded cell of the column is 'not reached' (decode_chain.py)."""
    rows = []
    gt = crb.GroundTruth(load_xlsx(crb.paper_inputs(_paths.PAPERS / paper)[1]))
    grids = {k: ht.grid_from_html(h) for k, h in enumerate(hb.html_tables(paper))}
    if True:
        for T, e in entries.items():
            r = record_of(e)
            reached = r is not None
            r = r or {}
            g = grids[e["table"]]
            weight = collections.Counter()
            for rr in range(g.nrows):
                x = g.at(rr, e["col"])
                if x and any(gt.match_id(str(g.at(rr, cc).text or "")) for cc in range(g.ncols) if g.at(rr, cc)):
                    weight[" ".join(str(x.text or "").split())] += 1
            for cell, want in e["legend"].items():
                c = r.get("cells", {}).get(cell) or {}
                term = c.get("term")
                have = term if term is not None else cell
                ev = ",".join(sorted(set((c.get("evidence") or {}).values()))) or None
                coded = dk.n(cell) != dk.n(want)
                if dk.n(have) == dk.n(want) or v1._flat(have) == v1._flat(want):
                    out = "right"
                elif coded and e.get("where", {}).get(cell) in v1.NO_LEGEND:
                    out = "no legend printed"
                elif not reached:
                    out = "not reached"
                elif (paper, cell) in v1.GT_ERRORS or ((paper, "*") in v1.GT_ERRORS and coded):
                    out = "GT error"
                elif re.sub(v1.UNIT_END, "", have) != have and v1._flat(re.sub(v1.UNIT_END, "", have)) == v1._flat(want):
                    out = "right, unit inside"
                elif coded and term is not None and _contains(have, want):
                    out = "right, longer wording"
                elif coded and term is not None and _contains(want, have):
                    out = "right, shorter wording"
                elif coded and term is None:
                    out = "left as printed"
                elif not coded:
                    out = "changed (should keep)"
                else:
                    out = "other term"
                rows.append({"side": "", "paper": paper, "trait": T, "cell": cell, "want": want,
                             "have": have, "kind": "coded" if coded else "kept", "out": out,
                             "evidence": ev, "w": max(1, weight.get(cell, 0))})
    return rows


def report(rows, title):
    L = [title, ""]
    for side in ("v1-dev", "v1-held-out", "all"):
        rs = [r for r in rows if side == "all" or r["side"] == side]
        for kind in ("coded", "kept"):
            for unit in ("cells", "pairs"):
                sel = [r for r in rs if r["kind"] == kind]
                wt = (lambda r: r["w"]) if unit == "cells" else (lambda r: 1)
                tot = sum(map(wt, sel))
                if not tot:
                    continue
                c = collections.Counter()
                for r in sel:
                    c[r["out"]] += wt(r)
                if kind == "coded":
                    reach = tot - c["no legend printed"] - c["GT error"]
                    ok = c["right"] + c["right, unit inside"]
                    L.append(f"{side:12s} coded {unit:5s} reachable {reach:5d}: right {c['right']} "
                             f"+ unit inside {c['right, unit inside']} = {ok} ({ok / reach:.0%})   "
                             + ", ".join(f"{o} {v}" for o, v in c.most_common()))
                    lw = c["right, longer wording"] + c["right, shorter wording"]
                    if lw:
                        L.append(f"{'':12s}       {unit:5s} + longer wording {lw} = {ok + lw} "
                                 f"({(ok + lw) / reach:.0%}) if the boundary is forgiven (longer or shorter wording)")
                else:
                    L.append(f"{side:12s} kept  {unit:5s} {tot:5d}: kept {c['right']} ({c['right'] / tot:.1%})   "
                             + ", ".join(f"{o} {v}" for o, v in c.most_common()))
        L.append("")
    L.append("decoded cells by evidence class (pairs | cells): right / decoded")
    for ev in ("explicit", "initial"):
        sel = [r for r in rows if r["evidence"] and ev in r["evidence"]]
        ok = [r for r in sel if r["out"] in ("right", "right, unit inside")]
        L.append(f"  {ev:9s} {len(ok)}/{len(sel)} | {sum(r['w'] for r in ok)}/{sum(r['w'] for r in sel)}")
    return L


def cmd_score():
    dev_v1 = v1.dev_papers()
    rows = score_dir(OUT, dev_v1)
    L = report(rows, "decoder v2 against the decoding key (corrected 2026-10-12); "
                     "cells = species rows, pairs = distinct cells")
    L += [""] + report(score_dir(v1.OUT, dev_v1), "v1 on the same corrected key, same report (baseline)")
    L += ["", "per paper (coded cells right incl. unit inside / reachable):"]
    by = collections.defaultdict(list)
    for r in rows:
        by[r["paper"]].append(r)
    for p, rs in sorted(by.items()):
        cod = [r for r in rs if r["kind"] == "coded" and r["out"] not in ("no legend printed", "GT error")]
        if cod:
            ok = sum(r["w"] for r in cod if r["out"] in ("right", "right, unit inside"))
            L.append(f"  [{rs[0]['side']}] {p:20s} {ok}/{sum(r['w'] for r in cod)}")
    L += ["", "every miss:"]
    for r in rows:
        if r["out"] not in ("right", "no legend printed"):
            L.append(f"  [{r['side']}] {r['paper']} '{r['trait'][:30]}': '{r['cell']}' -> want "
                     f"'{r['want'][:50]}', have '{r['have'][:60]}'  [{r['out']}; {r['evidence']}]")
    (OUT / "SCORE.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[:30]))


def main(argv):
    global OUT, PREV
    if "--out" in argv:                                  # a new run folder, reusing PREV
        i = argv.index("--out")
        OUT, PREV = dk.OUT / argv[i + 1], dk.OUT / argv[i + 2]
        argv = argv[:i] + argv[i + 3:]
    cmd, papers = argv[0], argv[1:]
    if cmd != "score" and not papers:
        papers = sorted(v1.load_key())
    {"organise": cmd_organise, "match": cmd_match}.get(cmd, lambda _p: cmd_score())(papers)


if __name__ == "__main__":
    main(sys.argv[1:])
