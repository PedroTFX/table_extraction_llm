"""
legend_calib2.py — the two-stage legend calibration (2026-11-25, after the first calibration run): extraction and
association are separate model tasks, measured apart, on the frozen gold v4. One structural calibration, not a
sequence of prompt tweaks on the same 59 units.

  run    (gemma)
         stage 1  per source unit, NO column information: the unit's definitions (kind, code, term, the variable as
                  the unit prints it or '', and the evidence span that states the pair)
         check    (code, a grounding check, not a decision) see `check`
         stage 2  per unit with checked cell-code entries (code legends and variable abbreviations; never figure
                  keys or other definitions): the entries and the unit's candidate columns (headers, cell values)
                  -> which columns they decode, with which codes. Stage 2 also runs on the gold's cell-code
                  mappings (oracle input), so association is measured without stage 1's errors
         -> TREE_OUTPUT/legend_coverage/calib2_run_<stamp>.json
  score  (code) -> TREE_OUTPUT/legend_coverage/CALIB2_REPORT_<stamp>.txt; optionally also the v3 single-call run
         scored on the same gold v4 (its v3 scores stay the historical baseline on gold v3)

    python legend_calib2.py run
    python legend_calib2.py score <gold_v4.json> <calib2_run.json> [<v3 calib_run.json>]

The evidence check: the evidence must be printed in the unit, up to the PDF reader's artefacts (LaTeX marks, letters
spaced one by one inside $...$, a word broken at a line end, spacing); it must print THIS code next to THIS term (at
most GAP characters apart, the code not inside the term); and a term that is only its code defines nothing. A code
is found as a separate token; a number may be glued to the word before it ('herbivorous2.'), never to a digit or a
decimal.
"""
from __future__ import annotations

import collections
import json
import re
import sys
import time

import _paths  # noqa: F401
import legend_calib as cal

OUT = cal.OUT
KINDS = ["code legend", "variable abbreviation", "figure key", "other definition"]
CELL_KINDS = ("code legend", "variable abbreviation")
GAP = 40

PROMPT1 = """Below is one passage from a scientific paper (a {structure}).

Find every place where the passage states what a label stands for: a code, abbreviation, letter, symbol or number printed together with its meaning. Four kinds:
- "code legend": codes that sort species, samples or sites into categories, e.g. "W = wetland; S = scrub", "(0) absent, (1) present"
- "variable abbreviation": a short name of a measured variable or index, e.g. "shell thickness (ST)", "WL, wing load"
- "figure key": letters, symbols, lines or shadings of a figure, e.g. "(a) first visit, (b) second visit", "hollow squares, burnt plots"
- "other definition": a definition stated under a label that is none of the above, e.g. "criteria: (i) two visits per year, (ii) no gaps"

For each one give:
- kind: one of the four kinds above
- code: the label exactly as printed. In a numbered or lettered list the code is the marker printed before the item ("1." gives "1", "b)" gives "b"); never number the items yourself
- term: what the label stands for, COPIED EXACTLY from the passage, the paper's spelling, no paraphrase
- variable: the passage's own words naming what the codes classify or what the abbreviation measures; "" if the passage does not name it (do not guess it)
- evidence: the shortest exact piece of the passage that states this code means this term, copied character for character

Give nothing for labels the passage mentions without saying what they stand for, for numbered sentences, hypotheses or list items that define no label, for statistics, units, references, or table and figure numbers. If the passage defines nothing, reply with an empty list.

Passage:
{text}

Reply with JSON only."""

SCHEMA1 = {"type": "object", "required": ["definitions"],
           "properties": {"definitions": {"type": "array", "items": {
               "type": "object", "required": ["kind", "code", "term", "variable", "evidence"],
               "properties": {"kind": {"type": "string", "enum": KINDS}, "code": {"type": "string"},
                              "term": {"type": "string"}, "variable": {"type": "string"},
                              "evidence": {"type": "string"}}}}}}

PROMPT2 = """A passage of a scientific paper defines these codes:
{legend}

Below are table columns of the same paper (id | header | cell values). For each column, decide whether its cells hold these codes with these meanings, so that the definitions above tell what the column's cells mean. Cells that only share the same letters, numbers or words but mean something else are not decoded by these definitions.

Columns:
{columns}

For every column give:
- id: the column's id
- decodes: true if the definitions above decode the column's cells, false if not
- codes: the codes above that the column's cells use with these meanings ([] if decodes is false)
- evidence: a short reason, from the column's header or cells

Reply with JSON only."""

SCHEMA2 = {"type": "object", "required": ["columns"],
           "properties": {"columns": {"type": "array", "items": {
               "type": "object", "required": ["id", "decodes", "codes", "evidence"],
               "properties": {"id": {"type": "string"}, "decodes": {"type": "boolean"},
                              "codes": {"type": "array", "items": {"type": "string"}},
                              "evidence": {"type": "string"}}}}}}

# --- the evidence check ------------------------------------------------------------------------------------------

MATH = re.compile(r"\$([^$]*)\$")
MARKS = re.compile(r"\\[A-Za-z]+|[{}_^$\\]")
BROKEN = re.compile(r"([^\W\d_])- (?:[^\w\s] )?([^\W\d_])")     # 'Alvo- ¸ rada' -> 'Alvorada'


def _join(s):
    """Letters the reader spaced one by one: 'P r o b S' -> 'ProbS'."""
    out, run = [], []
    for t in s.split():
        if len(t) == 1 and t.isalnum():
            run.append(t)
            continue
        if run:
            out.append("".join(run))
            run = []
        out.append(t)
    if run:
        out.append("".join(run))
    return " ".join(out)


PLAIN = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "′": "'", "″": '"', "–": "-", "—": "-", "−": "-",
                       " ": " "})


def norm(s):
    s = MATH.sub(lambda m: " " + _join(MARKS.sub(" ", m.group(1))) + " ", str(s or "").translate(PLAIN))
    return " ".join(MARKS.sub("", s).split())


def forms(s):
    a = norm(s)
    b = BROKEN.sub(r"\1\2", a)
    return [a] if a == b else [a, b]


def code_spans(code, s):
    c = norm(code).strip("()[].:=,; ")
    if not c:
        return []
    if c.isdigit():
        pat = rf"(?<!\d){c}(?!\d)(?![.,]\d)"
    else:
        pat = r"(?<![^\W_])" + re.escape(c) + r"(?![^\W_])"
    spans = [(m.start(), m.end()) for m in re.finditer(pat, s)]
    return spans or [(m.start(), m.end()) for m in re.finditer(pat, s, re.I)]


def term_spans(term, s):
    words = re.findall(r"[^\W_]+", term)
    if not words:
        return []
    pat = r"(?<![^\W_])" + r"[\W_]+".join(map(re.escape, words)) + r"(?![^\W_])"
    return [(m.start(), m.end()) for m in re.finditer(pat, s, re.I)]


def check(e, text):
    """'' if the entry is grounded, else the reason."""
    code, term = e["code"], e["term"]
    if not cal.ncode(code) or cal.ncode(term) == cal.ncode(code):
        return "term is the code"
    if not e.get("evidence", "").strip():
        return "no evidence"
    T = [t.casefold() for t in forms(text)]
    evs = [ev for ev in forms(e["evidence"]) if any(ev.casefold() in t for t in T)]
    if not evs:
        return "evidence not printed in the unit"
    reason = "code not in the evidence"
    for ev in dict.fromkeys(evs + [BROKEN.sub(r"\1\2", ev) for ev in evs]):
        cs = code_spans(code, ev)
        if not cs:
            continue
        ts = [sp for f in forms(term) for sp in term_spans(f, ev)]
        if not ts:
            reason = "term not in the evidence"
            continue
        if any(c1 <= t0 and t0 - c1 <= GAP or t1 <= c0 and c0 - t1 <= GAP for c0, c1 in cs for t0, t1 in ts):
            return ""
        reason = "code and term not next to each other"
    return reason


# --- the run ---------------------------------------------------------------------------------------------------

def render_legend(entries):
    return "\n".join(f'- "{e["code"]}" = "{e["term"]}"' + (f' (variable: {e["variable"]})' if e.get("variable") else "")
                     for e in entries)


def stage2(client_chat, entries, cols):
    raw = client_chat(PROMPT2.format(legend=render_legend(entries), columns=cal.render_columns(cols)),
                      SCHEMA2, "columns")
    out = {}
    for a in raw if isinstance(raw, list) else []:
        if not isinstance(a, dict):
            continue
        good, _bad = cal.column_ids([a.get("id", "")], cols)
        for k in good:
            out[k] = {"decodes": bool(a.get("decodes")), "codes": [str(c) for c in a.get("codes") or []],
                      "evidence": " ".join(str(a.get("evidence") or "").split())}
    return out, raw


def run():
    import decoder as v1
    import decoder_v2 as v2
    units = json.loads((OUT / "calib_units.json").read_text(encoding="utf-8"))
    gold = {u["uid"]: u for u in json.loads((OUT / "calib_gold_v4_2026-11-25.json").read_text(encoding="utf-8"))["units"]}
    assert "frozen" in json.loads((OUT / "calib_gold_v4_2026-11-25.json").read_text(encoding="utf-8"))["version"]
    stamp = time.strftime("%Y-%m-%d_%H%M")
    res = []
    for n, x in enumerate(units, 1):
        t0 = time.time()
        raw = v2._chat(PROMPT1.format(structure=x["structure"], text=x["text"]), SCHEMA1, "definitions")
        ents = []
        for e in raw if isinstance(raw, list) else []:
            if isinstance(e, dict):
                ents.append({k: " ".join(str(e.get(k) or "").split()) for k in ("kind", "code", "term", "variable",
                                                                                  "evidence")})
        for e in ents:
            e["check"] = check(e, x["text"])
        cell = [e for e in ents if not e["check"] and e["kind"] in CELL_KINDS]
        cols = x["candidate_columns"]
        e2e, e2e_raw = stage2(v2._chat, cell, cols) if cell else ({}, None)
        gm = [{"code": m["code"], "term": m["term"], "variable": m["variable_printed"]}
              for m in gold[x["uid"]]["mappings"] if m["kind"] in CELL_KINDS]
        orc, orc_raw = stage2(v2._chat, gm, cols) if gm else ({}, None)
        res.append({"uid": x["uid"], "stage1": ents, "stage1_raw": raw, "stage2": e2e, "stage2_raw": e2e_raw,
                    "oracle_input": gm, "oracle": orc, "oracle_raw": orc_raw, "seconds": round(time.time() - t0, 1)})
        print(f"{n:3d}/{len(units)} {x['uid']:28s} stage1 {len(ents):2d} ({len(ents) - len([e for e in ents if e['check']]):2d} "
              f"checked)  stage2 {sum(v['decodes'] for v in e2e.values())}/{len(e2e)}  oracle "
              f"{sum(v['decodes'] for v in orc.values())}/{len(orc)}  {res[-1]['seconds']:5.1f}s", flush=True)
    f = OUT / f"calib2_run_{stamp}.json"
    f.write_text(json.dumps({"model": v1.GEMMA, "date": stamp, "prompt1": PROMPT1, "prompt2": PROMPT2, "gap": GAP,
                             "units": res}, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"-> {f}")


# --- scoring ---------------------------------------------------------------------------------------------------

def stage1_eval(G, ents, equiv):
    """Unit recognition, mapping extraction (exact / cross-source / ordinal substitution / wrong pairing / other /
    missing), kind, variable provenance and unsupported pairs for one set of entries per unit."""
    S, D = [], []
    sub = lambda u: u.get("subtypes") or ([u["subtype"]] if u["is_definition"] else [])
    conf, by_struct, by_sub, kind_ok = (collections.Counter(), collections.defaultdict(collections.Counter),
                                        collections.defaultdict(collections.Counter), collections.Counter())
    for k, u in G.items():
        pos, got = u["is_definition"], bool(ents[k])
        cell = ("TP" if got else "FN") if pos else ("FP" if got else "TN")
        conf[cell] += 1
        by_struct[u["structure"]][cell] += 1
        for s in sub(u) or ["none"]:
            by_sub[s][cell] += 1
            if pos and got:
                kind_ok[(s, any(e["kind"] == s for e in ents[k]))] += 1
        if pos and not got:
            D.append(f"  unit missed: {k} [{u['structure']}] {'/'.join(sub(u))}")
        if not pos and got:
            D.append(f"  unit wrongly recognised: {k} [{u['structure']}]: "
                     + "; ".join(f"{e['code']}={e['term'][:40]}" for e in ents[k])[:250])
    S += ["  unit recognition (does the unit define anything?): "
          f"{cal.pr(conf['TP'], conf['FP'], conf['FN'])}; true negatives {conf['TN']}"]
    for s in KINDS:
        c = by_sub[s]
        S.append(f"    {s:22s} recognised {c['TP']}/{c['TP'] + c['FN']}, with an entry of this kind "
                 f"{kind_ok[(s, True)]}/{c['TP']}")
    S.append(f"    {'none':22s} wrongly recognised {by_sub['none']['FP']}/{by_sub['none']['FP'] + by_sub['none']['TN']}")
    S.append("    by structure (TP FP FN TN): " + "; ".join(
        f"{s} {by_struct[s]['TP']} {by_struct[s]['FP']} {by_struct[s]['FN']} {by_struct[s]['TN']}" for s in cal.STRUCTURES))

    status = collections.defaultdict(collections.Counter)
    kinds, var = collections.Counter(), collections.Counter()
    found, unsupported = {}, []
    for k, u in G.items():
        P = ents[k]
        used = set()
        terms = {cal.nterm(m["term"]): m for m in u["mappings"]}
        for m in u["mappings"]:
            c = cal.ncode(m["code"])
            own = {cal.nterm(m["term"]), cal.nterm(m.get("printed_as", m["term"]))}
            same = [i for i, p in enumerate(P) if cal.ncode(p["code"]) == c and i not in used]
            ex = [i for i in same if cal.nterm(P[i]["term"]) in own]
            eq = equiv.get((u.get("legend_id"), c, cal.nterm(m["term"])), set())
            cr = [i for i in same if cal.nterm(P[i]["term"]) in eq]
            ordinal = [i for i, p in enumerate(P) if u.get("enumerated") and i not in used
                       and cal.nterm(p["term"]) in own and cal.ncode(p["code"]) == str(m["position"]) != c]
            if ex or cr:
                i = (ex or cr)[0]
                st = "exact" if ex else "cross-source equivalent"
            elif ordinal:
                i, st = ordinal[0], "ordinal substitution"
            elif same:
                i = same[0]
                other = terms.get(cal.nterm(P[i]["term"]))
                st = "wrong pairing" if other is not None and cal.ncode(other["code"]) != c else "other wording"
            else:
                i, st = None, "missing"
            if i is not None:
                used.add(i)
                p = P[i]
                if st != "exact":
                    D.append(f"  {st}: {k} {m['code']!r} = {m['term'][:60]!r} / model {p['code']!r} = {p['term'][:60]!r}")
                kinds["same kind" if p["kind"] == m["kind"] else f"{m['kind']} -> {p['kind']}"] += 1
                vp, mv = m["variable_printed"], p.get("variable", "")
                if vp:
                    v = ("printed: given" if cal.words(vp) & cal.words(mv) else "printed: left unknown" if not mv
                         else "printed: differs")
                else:
                    v = "not printed: left unknown (right)" if not mv else "not printed: supplied"
                var[v] += 1
                if v in ("printed: differs", "not printed: supplied"):
                    D.append(f"  variable {v}: {k} {m['code']!r}: gold printed {vp!r} (context "
                             f"{m['variable_context']!r}) / model {mv!r}")
            else:
                D.append(f"  missing: {k} {m['code']!r} = {m['term'][:70]!r} [{m['kind']}]")
            status[m["kind"]][st] += 1
            status["all"][st] += 1
            found.setdefault((u.get("legend_id"), c), {})[k] = st
        for i, p in enumerate(P):
            if i not in used:
                unsupported.append((k, u["is_definition"], p))
    ST = ("exact", "cross-source equivalent", "ordinal substitution", "wrong pairing", "other wording", "missing")
    S.append("  mapping extraction (exact = the wording of the unit the model got, or its printed_as):")
    for s in ["all"] + KINDS:
        c = status[s]
        S.append(f"    {s:22s} {sum(c.values()):3d} pairs: " + ", ".join(f"{x} {c[x]}" for x in ST))
    multi = {key: v for key, v in found.items() if len(v) >= 2}
    S.append(f"    repeated legends: {sum(all(s in ('exact', 'cross-source equivalent') for s in v.values()) for v in multi.values())}"
             f"/{len(multi)} codes read alike in every copy")
    S.append("    kind of the matched pairs: " + ", ".join(f"{a} {b}" for a, b in kinds.most_common()))
    S.append("  variable provenance (matched pairs): " + ", ".join(f"{a} {b}" for a, b in sorted(var.items())))
    up = collections.Counter(("definition unit" if d else "non-definition unit") for _k, d, _p in unsupported)
    S.append(f"  unsupported pairs (not gold mappings of the unit): {len(unsupported)} ("
             + ", ".join(f"{a} {b}" for a, b in sorted(up.items())) + ")")
    for k, d, p in unsupported:
        D.append(f"  unsupported: {k} [{'def' if d else 'none'}] {p['kind']}: {p['code']!r} = {p['term'][:70]!r}"
                 + (f" (check: {p['check'] or 'kept'})" if "check" in p else ""))
    return S, D


def stage2_eval(G, assoc, cols):
    """assoc: uid -> {'t<k>c<c>': codes predicted to decode it}. Three outcomes for each gold-decoded column."""
    S, D = [], []
    for skip in (False, True):
        c = collections.Counter()
        per = collections.defaultdict(collections.Counter)
        for k, u in G.items():
            for t in u["targets"]:
                if skip and t.get("disputed_header"):
                    continue
                col = f"t{t['table']}c{t['col']}"
                held = cal.column_codes(cols[(k, t["table"], t["col"])])
                g = {cal.ncode(x) for x in t["decoded_by"]}
                pc = assoc.get(k, {}).get(col)
                if g:
                    if pc is None:
                        cell = "missed column"
                    elif {cal.ncode(x) for x in pc} & held == g:
                        cell = "right column, right codes"
                    else:
                        cell = "right column, wrong or incomplete codes"
                else:
                    cell = "wrong column" if pc is not None else "TN"
                c[cell] += 1
                per[u["subtype"] if u["is_definition"] else "none"][cell] += 1
                if not skip and cell not in ("TN", "right column, right codes"):
                    D.append(f"  {cell}: {k} -> {col} {t['header'][:45]!r}: gold {sorted(g)} model "
                             f"{sorted(pc) if pc is not None else '-'}")
        rr, rw, mc, wc = (c["right column, right codes"], c["right column, wrong or incomplete codes"],
                          c["missed column"], c["wrong column"])
        S.append(f"  {'without' if skip else 'with'} the disputed-header cases: right column + right codes {rr}, "
                 f"right column + wrong/incomplete codes {rw}, missed column {mc}, wrong column {wc}, TN {c['TN']}")
        S.append(f"    column precision {(rr + rw) / max(1, rr + rw + wc):.2f}, strict (right codes) "
                 f"{rr / max(1, rr + rw + wc):.2f}; column recall {(rr + rw) / max(1, rr + rw + mc):.2f}, strict "
                 f"{rr / max(1, rr + rw + mc):.2f}")
        if not skip:
            for s in KINDS + ["none"]:
                x = per[s]
                if sum(x.values()):
                    S.append(f"    {s:22s} RR {x['right column, right codes']:2d} RW "
                             f"{x['right column, wrong or incomplete codes']:2d} MC {x['missed column']:2d} "
                             f"WC {x['wrong column']:2d} TN {x['TN']:3d}")
            linked = sum(bool(t["decoded_by"]) for u in G.values() for t in u["targets"])
            missed = sum(len(u.get("missed_targets", [])) for u in G.values())
            S.append(f"    end to end: right column + right codes {rr} of {linked + missed} genuine target columns "
                     f"({linked} proposed by the selector + {missed} it missed) = {rr / (linked + missed):.2f}")
    return S, D


def score(gold_file, run_file, v3_file=None):
    import pathlib
    gold = json.loads(open(gold_file, encoding="utf-8").read())
    if "frozen" not in gold.get("version", ""):
        raise SystemExit("the gold is not frozen")
    G = {u["uid"]: u for u in gold["units"]}
    R = json.loads(open(run_file, encoding="utf-8").read())
    run_ = {u["uid"]: u for u in R["units"]}
    assert set(G) == set(run_), set(G) ^ set(run_)
    cols = {(x["uid"], c["table"], c["col"]): c["values"]
            for x in json.loads((pathlib.Path(gold_file).parent / "calib_units.json").read_text(encoding="utf-8"))
            for c in x["candidate_columns"]}
    equiv = {}
    for a in gold["wording_adjudication"]:
        if a["equivalent"]:
            ws = {cal.nterm(w) for w in a["wordings"].values()}
            for w in ws:
                equiv[(a["legend_id"], cal.ncode(a["code"]), w)] = ws
    L = [f"Two-stage legend calibration: {R['model']}, run {R['date']}, gold {gold['version']}, GAP {R['gap']}",
         f"{len(G)} units, {sum(len(u['mappings']) for u in G.values())} gold mappings, "
         f"{sum(len(u['targets']) for u in G.values())} candidate associations.",
         "A stratified set with positive controls: calibration and failure analysis, not corpus-wide precision. "
         "Each unit counts once. Gold v4 differs from v3: v3 scores are not comparable to these; the v3 run "
         "rescored on gold v4 is at the end.", ""]
    details = []
    raw = {k: v["stage1"] for k, v in run_.items()}
    kept = {k: [e for e in v["stage1"] if not e["check"]] for k, v in run_.items()}
    for name, ents in (("STAGE 1, raw entries", raw), ("STAGE 1, after the evidence check", kept)):
        S, D = stage1_eval(G, ents, equiv)
        L += ["=" * 100, name, "=" * 100] + S + [""]
        details += ["", f"--- {name}"] + D

    # the evidence check against the gold: what it keeps of the right pairs, what it removes of the rest
    acc = collections.Counter()
    why = collections.Counter()
    lost = []
    for k, u in G.items():
        gm = {(cal.ncode(m["code"]), cal.nterm(m["term"])) for m in u["mappings"]} | \
             {(cal.ncode(m["code"]), cal.nterm(m.get("printed_as", ""))) for m in u["mappings"]}
        for e in run_[k]["stage1"]:
            right = (cal.ncode(e["code"]), cal.nterm(e["term"])) in gm
            acc[(right, not e["check"])] += 1
            if e["check"]:
                why[e["check"]] += 1
            if right and e["check"]:
                lost.append(f"  rejected a gold pair: {k} {e['code']!r} = {e['term'][:60]!r}: {e['check']} "
                            f"(evidence {e['evidence'][:80]!r})")
    L += ["=" * 100, "EVIDENCE CHECK (exact gold pairs vs the rest of stage 1's entries)", "=" * 100,
          f"  exact gold pairs: kept {acc[(True, True)]}, rejected {acc[(True, False)]}",
          f"  other entries: removed {acc[(False, False)]}, kept {acc[(False, True)]}",
          "  reasons: " + ", ".join(f"{a} {b}" for a, b in why.most_common())] + lost + [""]

    orc = {k: {c: v["codes"] for c, v in r["oracle"].items() if v["decodes"]} for k, r in run_.items()}
    e2e = {k: {c: v["codes"] for c, v in r["stage2"].items() if v["decodes"]} for k, r in run_.items()}
    for name, a in (("STAGE 2, oracle input (the gold's cell-code mappings): association alone", orc),
                    ("STAGE 2, end to end (stage 1's checked cell-code entries)", e2e)):
        S, D = stage2_eval(G, a, cols)
        L += ["=" * 100, name, "=" * 100] + S + [""]
        details += ["", f"--- {name}"] + D
    L.append(f"  stage 2 calls: oracle {sum(r['oracle_raw'] is not None for r in run_.values())}, end to end "
             f"{sum(r['stage2_raw'] is not None for r in run_.values())}")

    if v3_file:
        V = {u["uid"]: u["entries"] for u in json.loads(open(v3_file, encoding="utf-8").read())["units"]}
        S1, D1 = stage1_eval(G, V, equiv)
        a3 = {}
        for k, P in V.items():
            for p in P:
                for c in p["columns"]:
                    a3.setdefault(k, {}).setdefault(c, []).append(p["code"])
        S2, D2 = stage2_eval(G, a3, cols)
        L += ["=" * 100, "REFERENCE: the v3 single-call run (2026-11-24_2345) scored on gold v4, raw entries",
              "=" * 100] + S1 + ["  association:"] + S2 + [""]
        details += ["", "--- v3 run on gold v4"] + D1 + D2
    L += ["=" * 100, "DETAIL", "=" * 100] + details
    f = OUT / f"CALIB2_REPORT_{R['date']}.txt"
    f.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:L.index("DETAIL") - 1]))
    print(f"-> {f}")


if __name__ == "__main__":
    {"run": run, "score": score}[sys.argv[1]](*sys.argv[2:])
