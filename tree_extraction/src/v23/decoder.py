"""
decoder.py — EXPERIMENT: decoder v1, a column's printed codes -> the paper's words.

Code finds, gemma organises, code checks, nimble decides:
  gather    (code)   the passages that may define a column's values: prose paragraphs
                     (tables and the bibliography removed), footnote rows inside the
                     table, and the other small tables (possible data dictionaries).
                     A paragraph is picked by how many of the column's values it
                     names as whole tokens (in any printed form: '1.0', '1', '(1)'),
                     plus the column name's words.
  organise  (gemma)  reads the passages and lists every legend entry it finds:
                     {variable, code, term} — the term copied from the passage.
  verify    (code)   an entry is kept only when its term is printed in the passages
                     and its code is printed near it (a parse check: nothing judged);
                     a near-miss quote ('narrow' for 'narrowly') is replaced by the
                     printed phrase, so the term is always the paper's words.
  QK        (nimble) is the cell value a code, or a word written out? (Habustova's
                     'Hygrophilous' has a printed definition, but it is the term itself.)
                     Only codes go on to QV.
  QV        (nimble) per distinct cell (per part, for a list 'MR; OR'): the options are
                     the verified entries whose code is printed like the cell ('1.0',
                     '(1)', '1'), each with the legend gemma says it belongs to — which
                     one is it in this column, or keep as printed. A cell with no such
                     entry gets no question and is kept.
                     (A first version asked nimble to pick the legend per column first;
                     dropped before running: gemma's 'variable' labels do not group
                     reliably — Korosi's M / O / P each came back as its own legend.)

The models never run together: phase 1 (gemma) caches its legends per paper, phase 2
(nimble) reads the cache.

    python decoder.py organise [papers...]     # gemma, -> OUT/organise/<paper>.json
    python decoder.py match [papers...]        # nimble, -> OUT/match/<paper>.json
    python decoder.py score                    # -> OUT/SCORE.txt
Papers default to every paper in the --all key; the 30-paper key's coded papers are
the development set, the rest are held out.
"""

from __future__ import annotations

import collections
import difflib
import json
import re
import sys
import time
import urllib.request as _rq

import _paths
import column_role_bench as crb
import column_tree as ct
import decode_key as dk
import header_tree as ht
import header_tree_bench as hb
from evaluate import load_xlsx
from fill_template import _drop_reference_lists, _looks_like_code

OUT = dk.OUT / "decoder_v1"
KEY_ALL = dk.OUT / "all" / "key.json"
KEY_DEV = dk.OUT / "key.json"
GEMMA = "gemma4:e4b-it-qat"
NIMBLE = "nimble:9b-q4-gpu"
COL_CHARS = 3000          # passages gathered per column
CALL_CHARS = 6000         # passages per gemma call
NEAR = 300                # code printed within this many chars of its term
MAX_ENTRIES = 15          # options per QV
# GT values that are not the paper's words (read by eye, 2026-10-12)
NO_LEGEND = {"not in the paper", "term only (prose)", "not in the paper (binary convention)"}   # decode_key.where: no code = term
UNIT_END = r"\s*(?:mm|cm|µm|μm|m|mg|g|°C|%|days?)\s*$"   # GT records the unit apart
GT_ERRORS = {("Graf2021", "A_E"): "GT 'highly eussocial'; the paper prints '(A_E) highly eusocial'",
             ("Derhe2016", "*"): "GT 'restold restorationation' for 'young/mid-age restoration'"}


# --- geometry ------------------------------------------------------------------

def forms(code):
    """Printed forms of one value: as is, without brackets, '1.0' -> '1'."""
    c = " ".join(str(code or "").split())
    out = [c]
    core = c.strip("()[]{} .").strip()
    out.append(core)
    if re.fullmatch(r"-?\d+[.,]0+", core):
        out.append(re.split(r"[.,]", core)[0])
    return [x for x in dict.fromkeys(out) if x]


def same_form(a, b):
    fa = {f.lower() for f in forms(a)}
    return any(f.lower() in fa for f in forms(b))


def token_re(x):
    return re.compile(r"(?<![\w])" + re.escape(x) + r"(?![\w])")


def list_parts(cell):
    parts = [p.strip() for p in re.split(r"\s*[;,/+]\s*|\s+and\s+", cell) if p.strip()]
    return parts if len(parts) > 1 else [cell]


def column_view(paper, k, c, grid, gt):
    """(header, [distinct body values]) — the body starts at the first row naming a
    species; the header is the column's text above it."""
    r0 = next((r for r in range(grid.nrows)
               if any(gt.match_id(str(grid.at(r, cc).text or "")) for cc in range(grid.ncols)
                      if grid.at(r, cc))), 1)
    head = []
    for r in range(r0):
        x = grid.at(r, c)
        t = " ".join(str(x.text or "").split()) if x else ""
        if t and t not in head and (not x or x.colspan < grid.ncols):
            head.append(t)
    vals = []
    for r in range(r0, grid.nrows):
        x = grid.at(r, c)
        t = " ".join(str(x.text or "").split()) if x else ""
        if t and x.colspan < max(2, grid.ncols) and t not in vals:
            vals.append(t)
    return " / ".join(head), vals


def paragraphs(paper, grids, k):
    raw = (_paths.PAPERS / paper / f"{paper}_full.md").read_text(encoding="utf-8", errors="replace")
    prose = re.sub(r"<table.*?</table>", "\n\n", _drop_reference_lists(raw), flags=re.S | re.I)
    out = [" ".join(p.split()) for p in re.split(r"\n\s*\n", dk.clean(prose)) if p.strip()]
    out = [("prose", p) for p in out if len(p) > 3]
    g = grids[k]                                         # footnote rows of this table
    for r in range(g.nrows):
        filled = {id(g.at(r, cc)): g.at(r, cc) for cc in range(g.ncols) if g.at(r, cc) and g.at(r, cc).text}
        if len(filled) == 1:
            x = next(iter(filled.values()))
            if x.colspan >= 0.6 * g.ncols and len(x.text) > 15:
                out.append(("table footnote", " ".join(x.text.split())))
    for j, gj in grids.items():                          # small tables: dictionaries?
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
        for i in range(0, len(lines), 20):
            out.append((f"table {j}", "\n".join(lines[i:i + 20])))
    return out


def gather(paras, header, values):
    """The passages most likely to define these values, up to COL_CHARS. Only values
    shaped like codes are looked up (_looks_like_code picks what to look up; a
    column of written-out words brings no passages)."""
    pats = []
    for v in values:
        for part in list_parts(v):
            if not _looks_like_code(part):
                continue
            fs = forms(part)
            pats.append((0.3 if any(f.isdigit() for f in fs) else 1.0, [token_re(f) for f in fs]))
    names = [re.compile(re.escape(w), re.I) for w in re.findall(r"[A-Za-z]{4,}", header)]

    def score(p):
        hits = sum(w for w, rs in pats if any(r.search(p) for r in rs))
        return hits + 2 * sum(bool(n.search(p)) for n in names) if hits else 0
    ranked = sorted(((score(p), i) for i, (_s, p) in enumerate(paras)), key=lambda x: (-x[0], x[1]))
    keep, used = [], 0
    for s, i in ranked:
        if s < 1 or used + len(paras[i][1]) > COL_CHARS:  # digits alone ('1', '2') are not enough
            continue
        keep.append(i)
        used += len(paras[i][1])
    return sorted(keep)


# --- gemma: organise --------------------------------------------------------------

ORGANISE = """Below are passages from a scientific paper: prose paragraphs, footnotes of tables, and small tables (cells separated by ' | ').

Find every LEGEND ENTRY: a place where the paper says what a short code, abbreviation, letter, symbol or number stands for when it classifies species or samples into categories. Examples of how papers write them:
  "solitary (SO), primitively eusocial (P_E)"   "G = ground nesting"   "1, hundreds; 2, thousands"   a table row "W | wood"   "(0) absent, (1) present"

For each entry give:
- variable: the trait, characteristic or table column the codes classify, in the paper's own words ("" if the passage does not say)
- code: the code exactly as printed
- term: what the code stands for, COPIED EXACTLY from the passage — no paraphrase, no added or changed words, the paper's spelling

Include only entries the passages actually print. One item per code; the same code under two variables is two items. Ignore abbreviations of statistics, methods or units (SD, ANOVA, mm), and definitions of ordinary words ("Hygrophilous: preferring moist places" explains a word; it is not a code).

Passages:
{passages}

Reply with JSON only."""

SCHEMA = {"type": "object", "required": ["legends"],
          "properties": {"legends": {"type": "array", "items": {
              "type": "object", "required": ["variable", "code", "term"],
              "properties": {"variable": {"type": "string"}, "code": {"type": "string"},
                             "term": {"type": "string"}}}}}}


def gemma(prompt, timeout=900):
    body = {"model": GEMMA, "stream": False, "format": SCHEMA, "think": False,
            "messages": [{"role": "user", "content": prompt}],
            "options": {"temperature": 0, "num_ctx": 16384}}
    for attempt in range(3):
        try:
            req = _rq.Request("http://127.0.0.1:11434/api/chat", data=json.dumps(body).encode(),
                              headers={"Content-Type": "application/json"})
            with _rq.urlopen(req, timeout=timeout) as r:
                msg = json.loads(r.read()).get("message", {}).get("content", "")
            got = json.loads(msg)
            return got.get("legends", []) if isinstance(got, dict) else []
        except json.JSONDecodeError:
            return []
        except Exception:                                # model load timeout, runner restart
            if attempt == 2:
                raise
            time.sleep(10 * (attempt + 1))


def unload(model):
    """Free the model before the other one loads (one model at a time)."""
    body = json.dumps({"model": model, "keep_alive": 0}).encode()
    try:
        _rq.urlopen(_rq.Request("http://127.0.0.1:11434/api/generate", data=body,
                                headers={"Content-Type": "application/json"}), timeout=60).read()
    except Exception:
        pass


def _flat(s):
    return " ".join(re.findall(r"[a-z0-9]+", str(s or "").lower()))


REPAIR = 0.9              # a misquoted term is replaced by a printed phrase this alike


def _printed(term, text):
    words = re.findall(r"[^\W_]+", term)
    if not words:
        return []
    pat = re.compile(r"[\W_]+".join(map(re.escape, words)), re.I)
    return [(m.start(), m.end()) for m in pat.finditer(text)]


def _closest(term, text, near):
    """The printed phrase most like a misquoted term ('narrow oligophagous' ->
    'narrowly oligophagous'), within NEAR chars of a printed code. -> (phrase, ratio)"""
    toks = [(m.group(), m.start(), m.end()) for m in re.finditer(r"[^\W_]+", text)]
    want = " ".join(re.findall(r"[^\W_]+", term.lower()))
    n = len(want.split())
    best = ("", 0.0)
    for i in range(len(toks)):
        for m in (n - 1, n, n + 1):
            if m < 1 or i + m > len(toks):
                continue
            a, b = toks[i][1], toks[i + m - 1][2]
            win = text[max(0, a - NEAR): b + NEAR]
            if not any(r.search(win) for r in near):
                continue
            got = " ".join(t for t, _a, _b in toks[i:i + m]).lower()
            r = difflib.SequenceMatcher(None, want, got).ratio()
            if r > best[1]:
                best = (text[a:b], r)
    return best


def verify(entry, text):
    """Code check: the term is printed in the passages (punctuation/case aside) and a
    printed form of the code sits within NEAR chars of it. A term that is not printed
    but within REPAIR of a printed phrase near the code is replaced by that phrase
    (the paper's words win over the model's). -> reason or '' (entry updated)."""
    term, code = str(entry.get("term") or "").strip(), str(entry.get("code") or "").strip()
    if not term or not code:
        return "empty"
    if not re.search(r"[^\W_]", term):
        return "term has no words"
    near = [token_re(f) for f in forms(code)]
    for a, b in _printed(term, text):
        win = text[max(0, a - NEAR): b + NEAR]
        if any(r.search(win) for r in near):
            return ""
    phrase, r = _closest(term, text, near)
    if r >= REPAIR:
        entry["model_term"], entry["term"] = term, " ".join(phrase.split())
        return ""
    return "term not printed near the code" if _printed(term, text) else "term not printed"


def organise(paper, columns):
    """columns: [(table, col, header, values)]. -> {"calls", "legends", "dropped"}"""
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
        if cur and sum(len(x) for x in cur) + len(piece) > CALL_CHARS:
            calls.append(cur)
            cur = []
        cur.append(piece[:CALL_CHARS])
    if cur:
        calls.append(cur)
    kept, dropped = [], []
    for part in calls:
        text = "\n\n".join(part)
        for e in gemma(ORGANISE.format(passages=text)):
            e = {k2: " ".join(str(e.get(k2) or "").split()) for k2 in ("variable", "code", "term")}
            why = verify(e, text)
            (dropped if why else kept).append({**e, **({"why": why} if why else {})})
    seen, legends = set(), []
    for e in kept:
        key = (e["variable"].lower(), e["code"], e["term"].lower())
        if key not in seen:
            seen.add(key)
            legends.append(e)
    return {"calls": len(calls), "chars": sum(len(x) for p in calls for x in p),
            "passages": [x for p in calls for x in p], "legends": legends, "dropped": dropped}


# --- nimble: match -----------------------------------------------------------------

def entries_for(legends, value):
    """The verified entries whose code is printed like this value (any form), one per
    distinct term. Code picks which definitions to offer; nimble decides."""
    out, seen = [], set()
    for e in legends:
        if same_form(value, e["code"]) and e["term"].lower() not in seen:
            seen.add(e["term"].lower())
            out.append(e)
    return out[:MAX_ENTRIES]


def ask(client, state, instructions, crit):
    a = client.ask(lambda size: state, {"q": {"type": "choice", "instructions": instructions,
                                               "criteria": crit}}).get("q") or {}
    probs = {k: round(float(v or 0), 3) for k, v in (a.get("probabilities") or {}).items()}
    return a.get("choice"), probs


def match_column(client, header, values, legends):
    """QK, then QV, per distinct cell, or per part of a list cell whose parts are all defined
    codes ('MR; OR'): which definition the paper gives it in THIS column, or keep.
    -> {"cells": {cell: {"term", "parts", "options", "probs"}}}"""
    rec = {"cells": {}}
    shown = ", ".join(f"'{v}'" for v in values[:25])
    state = (f"A table in a scientific paper has a column named '{header}'. Its cells hold "
             f"these values: {shown}. The options quote the paper's definitions of a code "
             f"printed like the cell value, and the legend each one belongs to.")
    asked, kinds = {}, {}
    for v in values:
        parts = list_parts(v)
        if len(parts) > 1 and not all(entries_for(legends, p) for p in parts):
            parts = [v]                                  # not a list of defined codes
        terms, probs, options = [], {}, {}
        for p in parts:
            es = entries_for(legends, p)
            if not es:
                terms.append(None)
                continue
            if p not in kinds:
                defs = "; ".join(f"'{e['code']}' = '{e['term']}'" for e in es[:3])
                kinds[p] = ask(client, state + f" The paper writes: {defs}.",
                               f"In the column '{header}', is the cell value '{p}' a code that "
                               f"stands for that term, or a word written out that the paper explains?", {
                    "code": f"a code: '{p}' is a letter, abbreviation, symbol or number that "
                            f"stands for the longer term",
                    "word": f"written out: '{p}' is already the term itself, an ordinary word or "
                            f"phrase; the paper only explains what it means"})
            probs[p + " | QK"] = kinds[p][1]
            options[p] = [e["term"] for e in es]
            if kinds[p][0] != "code":
                terms.append(None)
                continue
            if p not in asked:
                crit = {f"e{i}": f"'{p}' = '{e['term']}'" + (
                    f" (printed '{e['code']}' in the legend)" if e["code"] != p else "") + (
                    f" — the paper's legend for '{e['variable']}'" if e["variable"] else "")
                    for i, e in enumerate(es)}
                crit["keep"] = (f"none of these: '{p}' is already the paper's term (a word, not "
                                f"a code), or in the column '{header}' it does not stand for any "
                                f"of them; keep it as printed")
                asked[p] = ask(client, state, f"In the column '{header}', what does the "
                               f"cell value '{p}' stand for?", crit)
            ch, pr = asked[p]
            probs[p] = pr
            terms.append(es[int(ch[1:])]["term"] if ch and ch != "keep" else None)
        term = None
        if any(t is not None for t in terms):
            term = "; ".join(t if t is not None else p for t, p in zip(terms, parts))
        if options:
            rec["cells"][v] = {"term": term, "parts": parts, "options": options, "probs": probs}
    return rec


# --- inputs, scoring -----------------------------------------------------------------

def load_key(path=KEY_ALL):
    if not path.exists():                                # the --all key is not built yet
        path = KEY_DEV
    return json.loads(path.read_text(encoding="utf-8"))


def dev_papers():
    dev = load_key(KEY_DEV)
    return {p for p, cols in dev.items() if any(e["kind"] == "coded" for e in cols.values())}


def key_columns(paper, key):
    """The key's columns of one paper: [(table, col, header, values, entry)]."""
    gt = crb.GroundTruth(load_xlsx(crb.paper_inputs(_paths.PAPERS / paper)[1]))
    grids = {k: ht.grid_from_html(h) for k, h in enumerate(hb.html_tables(paper))}
    out, seen = [], set()
    for T, e in key.get(paper, {}).items():
        if (e["table"], e["col"]) in seen:
            continue
        seen.add((e["table"], e["col"]))
        header, values = column_view(paper, e["table"], e["col"], grids[e["table"]], gt)
        out.append((e["table"], e["col"], header, values[:25], e))
    return out


def cmd_organise(papers):
    key = load_key()
    (OUT / "organise").mkdir(parents=True, exist_ok=True)
    for paper in papers:
        f = OUT / "organise" / f"{paper}.json"
        if f.exists():
            continue
        cols = [(k, c, h, v) for k, c, h, v, _e in key_columns(paper, key)]
        t0 = time.time()
        res = organise(paper, cols)
        res["seconds"] = round(time.time() - t0, 1)
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  {paper:22s} {res['calls']} call(s) {res['chars']:>6d} chars  "
              f"{len(res['legends'])} entries kept, {len(res['dropped'])} dropped  ({res['seconds']}s)",
              flush=True)
    unload(GEMMA)


def cmd_match(papers):
    key = load_key()
    (OUT / "match").mkdir(parents=True, exist_ok=True)
    client = ct.DecisionClient(NIMBLE, 1)
    for paper in papers:
        f = OUT / "match" / f"{paper}.json"
        org = OUT / "organise" / f"{paper}.json"
        if f.exists() or not org.exists():
            continue
        legends = json.loads(org.read_text(encoding="utf-8"))["legends"]
        t0, c0 = time.time(), client.calls
        res = {}
        for k, c, header, values, _e in key_columns(paper, key):
            r = match_column(client, header, values, legends)
            r["header"] = header
            res[f"{k}:{c}"] = r
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  {paper:22s} {client.calls - c0} question(s)  ({time.time() - t0:.0f}s)", flush=True)
    unload(NIMBLE)


def cmd_score():
    key, dev = load_key(), dev_papers()
    tally = {s: collections.Counter() for s in ("dev", "held-out")}
    lines, per_paper = [], []
    for paper in sorted(key):
        f = OUT / "match" / f"{paper}.json"
        if not f.exists():
            continue
        got = json.loads(f.read_text(encoding="utf-8"))
        gt = crb.GroundTruth(load_xlsx(crb.paper_inputs(_paths.PAPERS / paper)[1]))
        grids = {k: ht.grid_from_html(h) for k, h in enumerate(hb.html_tables(paper))}
        side = "dev" if paper in dev else "held-out"
        pc = collections.Counter()
        for T, e in key[paper].items():
            r = got.get(f"{e['table']}:{e['col']}", {})
            g = grids[e["table"]]
            weight = collections.Counter()               # species rows per cell
            for rr in range(g.nrows):
                x = g.at(rr, e["col"])
                if x and any(gt.match_id(str(g.at(rr, cc).text or "")) for cc in range(g.ncols) if g.at(rr, cc)):
                    weight[" ".join(str(x.text or "").split())] += 1
            for cell, want in e["legend"].items():
                term = (r.get("cells", {}).get(cell) or {}).get("term")
                have = term if term is not None else cell
                coded = dk.n(cell) != dk.n(want)
                if dk.n(have) == dk.n(want) or _flat(have) == _flat(want):
                    out = "right"
                elif coded and e.get("where", {}).get(cell) in NO_LEGEND:
                    out = "no legend printed"
                elif (paper, cell) in GT_ERRORS or ((paper, "*") in GT_ERRORS and coded):
                    out = "GT error"
                elif re.sub(UNIT_END, "", have) != have and _flat(re.sub(UNIT_END, "", have)) == _flat(want):
                    out = "right, unit inside"
                elif coded and term is None:
                    out = "left as printed"
                elif not coded:
                    out = "changed (should keep)"
                else:
                    out = "other term"
                kind = "coded" if coded else "kept"
                w = max(1, weight.get(cell, 0))
                tally[side][(kind, out, "pairs")] += 1
                tally[side][(kind, out, "cells")] += w
                pc[(kind, out)] += w
                if out not in ("right",):
                    lines.append(f"  [{side}] {paper} t{e['table']} '{T}': '{cell}' -> want '{want}', "
                                 f"have '{have}'  [{out}; legend: {r.get('legend')}]")
        cr = pc[("coded", "right")]
        ca = sum(v for (k, _o), v in pc.items() if k == "coded")
        if ca:
            per_paper.append(f"  [{side}] {paper:20s} coded {cr}/{ca}   kept "
                             f"{pc[('kept', 'right')]}/{sum(v for (k, _o), v in pc.items() if k == 'kept')}")
    L = ["decoder v1 against the decoding key (cells = species rows; pairs = distinct cells)", ""]
    for side, t in tally.items():
        for kind in ("coded", "kept"):
            for unit in ("cells", "pairs"):
                tot = sum(v for (k, _o, u), v in t.items() if k == kind and u == unit)
                if not tot:
                    continue
                parts = ", ".join(f"{o} {v}" for (k, o, u), v in sorted(t.items(), key=lambda kv: -kv[1])
                                  if k == kind and u == unit)
                right = t[(kind, "right", unit)]
                L.append(f"{side:9s} {kind:6s} {unit:6s} right {right}/{tot} ({right / tot:.0%})   {parts}")
        L.append("")
    L += ["per paper with coded cells:"] + per_paper + ["", "every miss:"] + lines
    (OUT / "SCORE.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[:40]))


def main(argv):
    cmd, papers = argv[0], argv[1:]
    if cmd != "score" and not papers:
        papers = sorted(load_key())
    {"organise": cmd_organise, "match": cmd_match}.get(cmd, lambda _p: cmd_score())(papers)


if __name__ == "__main__":
    main(sys.argv[1:])
