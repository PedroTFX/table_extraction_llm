"""
legend_calib.py — the calibration set for model-based legend recognition (2026-11-24, after the review of the
R3abc labels). Each SOURCE UNIT once, with a stable id from its place in the paper and all the columns R3abc linked it
to; the gold labels (written by hand into calib_gold.json) have three levels:
  unit     does it define codes; subtype: code legend / variable abbreviation / figure key / formula / none
  mapping  every exact code -> term pair it prints, with the variable it belongs to
  target   for each candidate column, which of those mappings decode that column

  build      (code only) the units of the two labelled samples that R3abc keeps, matched back to their source units,
             plus the known controls, plus every R3abc unit of a structure the set would otherwise barely contain
             (fewer than FILL units: the footnotes), each with its full text and its candidate columns (header and
             cell values)
             -> TREE_OUTPUT/legend_coverage/calib_units.json, calib_units.txt (for reading and labelling)
  calibrate  (gemma) each unit ONCE, with all its candidate columns; gemma names every code -> term pair the unit
             prints (kind, variable, code, term) and the columns each pair decodes
             -> TREE_OUTPUT/legend_coverage/calib_run_<stamp>.json
  score      (code) the run against the FROZEN gold, in three views (the raw entries; after the inventory's own
             checks strip_own_code + verify_a; and also dropping entries whose term is only the code); every level
             reported apart, each subtype and structure apart:
             unit recognition, mapping extraction (source-faithful exact / adjudicated cross-source equivalent /
             other wording), variable attribution, target association (with and without the disputed-header
             cases), unsupported extraction, and the selector's own recall (from the gold only: the model never
             sees the columns and units the selector missed)
             -> TREE_OUTPUT/legend_coverage/CALIB_REPORT_<stamp>.txt

    python legend_calib.py build
    python legend_calib.py calibrate
    python legend_calib.py score <gold.json> <run.json>

Unit ids: '<paper>#p<n>' for the n-th prose paragraph (as legend_inventory cuts them; captions and numbered lists
are paragraphs too), '<paper>#t<k>r<r>' for a table row or footnote row, '<paper>#t<k>r<r>c<c>' for a head cell.

The set is stratified and holds positive controls on purpose: its accuracies are calibration and failure analysis,
not estimates of corpus-wide precision.
"""
from __future__ import annotations

import collections
import csv
import json
import random
import re
import sys
import time

import _paths
import full_run_v24 as fr
import header_tree as ht
import header_tree_bench as hb
import legend_ablation as la
import legend_coverage as lc

OUT = lc.OUT
SAMPLES = [_paths.SUB / "output/legend_coverage/ablation_sample_2026-11-24.csv",
           _paths.SUB / "output/legend_coverage/verification_sample_2026-11-24.csv"]
CONTROLS = [(p, needle) for p, needle, _w in la.POSITIVE] + [
    ("MacDonald2021", "Three hypotheses, each"), ("Scalercio2020", "Populations inhabiting Mediterranean")]
STRUCTURES = ("prose", "caption", "numbered list", "head cell", "footnote", "table row")
FILL = 3           # a structure with fewer units than this in the set gets its R3abc units (up to SAMPLE_PER_STRUCTURE)
VALUE_CHARS = 40   # a cell value shown to the model is cut to this


def uid(paper, u):
    if u["table"] is None:
        return f"{paper}#p{u['id']}"
    if u["structure"] == "head cell":
        return f"{paper}#t{u['table']}r{u['row']}c{u['col']}"
    return f"{paper}#t{u['table']}r{u['row']}"


def build():
    wanted = []
    for f in SAMPLES:
        for r in csv.DictReader(open(f, encoding="utf-8")):
            wanted.append((f.stem, r))
    papers = sorted({r["paper"] for _s, r in wanted} | {p for p, _n in CONTROLS} | set(la.ls.tuning_papers()))
    rows, _pp, _texts = la.features(papers)
    keep = la.variant(rows, "abc")
    head = fr.head_runs()
    units, values = {}, {}
    for p in papers:
        if p not in head:
            continue
        grids = {k: ht.grid_from_html(h) for k, h in enumerate(hb.html_tables(p))}
        first = {e["table"]: e.get("first") or 1 for e in head[p]}
        for u in lc.units(p, grids, first):
            units[(p, u["id"])] = u
        for c in lc.columns(p, grids, first):
            values[(p, c["table"], c["col"])] = c["values"]
    by_unit = {}
    for r in keep:
        by_unit.setdefault((r["paper"], r["unit"]), []).append(
            {"table": r["table"], "col": r["col"], "header": r["header"], "codes": r["hit_strict"],
             "explicit": r["explicit_strict"], "why": r["why"],
             "values": values.get((r["paper"], r["table"], r["col"]), [])})

    def find(p, structure, ut, ur, text):
        for (pp, i), cols in by_unit.items():
            if pp != p:
                continue
            u = units[(pp, i)]
            if u["structure"] != structure:
                continue
            if u["table"] is None:
                if " ".join(u["text"].split()).startswith(text[:150]):
                    return i
            elif str(u["table"]) == str(ut) and str(u["row"]) == str(ur) \
                    and " ".join(u["text"].split()).startswith(text[:60]):
                return i
        return None

    picked, src, missed = {}, {}, []
    for name, r in wanted:
        i = find(r["paper"], r["structure"], r["unit_table"], r["unit_row"], r["text"])
        if i is None:
            missed.append(f"{name} n{r['n']} {r['paper']} {r['structure']}: not an R3abc candidate")
            continue
        picked[(r["paper"], i)] = True
        src.setdefault((r["paper"], i), []).append(f"{name} n{r['n']}")
    for p, needle in CONTROLS:
        for (pp, i) in by_unit:
            if pp == p and needle in units[(pp, i)]["text"]:
                picked[(pp, i)] = True
                src.setdefault((pp, i), []).append(f"control '{needle}'")
    have = collections.Counter(units[k]["structure"] for k in picked)
    fill = []
    for s in STRUCTURES:
        if have[s] >= FILL:
            continue
        pool = sorted(k for k in by_unit if units[k]["structure"] == s and k not in picked)
        for k in random.Random(lc.SEED).sample(pool, min(lc.SAMPLE_PER_STRUCTURE, len(pool))):
            picked[k] = True
            src.setdefault(k, []).append(f"structure fill ({s}: {have[s]} in the set, {len(pool)} R3abc units)")
            fill.append(uid(k[0], units[k]))
    out = []
    for (p, i) in sorted(picked):
        u = units[(p, i)]
        out.append({"uid": uid(p, u), "paper": p, "group": la.ls.SPLIT.get(p), "structure": u["structure"],
                    "text": " ".join(u["text"].split()), "candidate_columns": by_unit[(p, i)],
                    "from": src[(p, i)]})
    (OUT / "calib_units.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    L = [f"{len(out)} unique units ({sum(len(x['candidate_columns']) for x in out)} candidate columns); "
         f"sample rows not R3abc candidates: {len(missed)}; structure fill: {', '.join(fill) or 'none'}"] \
        + [f"  {m}" for m in missed] + [""]
    for x in out:
        L.append(f"=== {x['uid']} [{x['structure']}] from {', '.join(x['from'])}")
        L.append(x["text"][:2500])
        for c in x["candidate_columns"]:
            L.append(f"   -> t{c['table']}c{c['col']} {c['header'][:70]!r} codes {c['codes']} explicit {c['explicit']} "
                     f"({c['why']}) values {c['values'][:lc.MAX_DISTINCT]}")
        L.append("")
    (OUT / "calib_units.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:len(missed) + 2]))


# --- gemma: one call per source unit -----------------------------------------------------------------------------

KINDS = ["code legend", "variable abbreviation", "figure key"]

PROMPT = """Below is one passage from a scientific paper (a {structure}) and some table columns of the same paper.

Find every place where the passage says what a code stands for: a short code, abbreviation, letter, symbol or number printed together with its meaning. Three kinds:
- "code legend": codes that sort species, samples or sites into categories, e.g. "W = wetland; S = scrub", "(0) absent, (1) present"
- "variable abbreviation": a short name of a measured variable or index, e.g. "shell thickness (ST)", "WL, wing load"
- "figure key": letters or symbols naming the panels, areas or symbols of a figure, e.g. "(a) first visit, (b) second visit"

For each one give:
- kind: one of the three kinds above
- variable: what the codes classify, or what the abbreviation measures, in the passage's words ("" if the passage does not say)
- code: the code exactly as printed
- term: what the code stands for, COPIED EXACTLY from the passage, the paper's spelling, no paraphrase
- columns: the ids of the columns below whose cells use this code with this meaning ([] if no column does)

Give nothing for codes the passage mentions without saying what they mean, for numbered sentences, hypotheses or list items, for statistics, units, references, or table and figure numbers. If the passage defines no code, reply with an empty list.

Passage:
{text}

Columns (id | header | cell values):
{columns}

Reply with JSON only."""

SCHEMA = {"type": "object", "required": ["legends"],
          "properties": {"legends": {"type": "array", "items": {
              "type": "object", "required": ["kind", "variable", "code", "term", "columns"],
              "properties": {"kind": {"type": "string", "enum": KINDS}, "variable": {"type": "string"},
                             "code": {"type": "string"}, "term": {"type": "string"},
                             "columns": {"type": "array", "items": {"type": "string"}}}}}}}


def render_columns(cols):
    return "\n".join(f"C{i} | {c['header'][:120]} | " + " ; ".join(v[:VALUE_CHARS] for v in c["values"][:lc.MAX_DISTINCT])
                     for i, c in enumerate(cols, 1))


def column_ids(ids, cols):
    good, bad = [], []
    for s in ids:
        m = re.fullmatch(r"[Cc]?\s*(\d+)", str(s).strip())
        if m and 1 <= int(m.group(1)) <= len(cols):
            c = cols[int(m.group(1)) - 1]
            good.append(f"t{c['table']}c{c['col']}")
        else:
            bad.append(str(s))
    return sorted(set(good)), bad


def calibrate():
    import decoder as v1
    import decoder_v2 as v2
    units = json.loads((OUT / "calib_units.json").read_text(encoding="utf-8"))
    stamp = time.strftime("%Y-%m-%d_%H%M")
    run = []
    for n, x in enumerate(units, 1):
        cols = x["candidate_columns"]
        t0 = time.time()
        raw = v2._chat(PROMPT.format(structure=x["structure"], text=x["text"], columns=render_columns(cols)),
                       SCHEMA, "legends")
        entries = []
        for e in raw if isinstance(raw, list) else []:
            if not isinstance(e, dict):
                continue
            good, bad = column_ids(e.get("columns") or [], cols)
            entries.append({"kind": str(e.get("kind") or ""), "variable": " ".join(str(e.get("variable") or "").split()),
                            "code": " ".join(str(e.get("code") or "").split()),
                            "term": " ".join(str(e.get("term") or "").split()), "columns": good, "bad_columns": bad})
        run.append({"uid": x["uid"], "entries": entries, "raw": raw, "seconds": round(time.time() - t0, 1)})
        print(f"{n:3d}/{len(units)} {x['uid']:28s} {len(entries):3d} entries {run[-1]['seconds']:6.1f}s", flush=True)
    f = OUT / f"calib_run_{stamp}.json"
    f.write_text(json.dumps({"model": v1.GEMMA, "date": stamp, "prompt": PROMPT, "units": run}, indent=1,
                            ensure_ascii=False), encoding="utf-8")
    print(f"-> {f}")


# --- scoring ------------------------------------------------------------------------------------------------------

STOP = {"the", "and", "of", "for", "in", "on", "to", "a", "an", "by", "with", "from", "type", "types", "level", "levels"}


def ncode(s):
    """A code up to spacing and the PDF reader's LaTeX markup: '$P r o b _ { S }$' = 'ProbS', '(1)' = '1'."""
    return re.sub(r"[\s$\\{}_]", "", str(s or "")).strip("()[].,;:=")


def nterm(s):
    """A term up to case, spacing and surrounding punctuation: 'Within food source.' = 'within food source'."""
    return " ".join(str(s or "").split()).strip(" .,;:()[]\"'").casefold()


def words(s):
    return {w[:-1] if w.endswith("s") and len(w) > 3 else w
            for w in re.findall(r"[a-z]{3,}", str(s or "").lower())} - STOP


def printed(e, text):
    import decoder_v2 as v2
    code = re.search(r"(?<![\w])" + re.escape(e["code"]) + r"(?![\w])", text) if e["code"] else None
    return bool(code) and bool(e["term"]) and bool(v2._wb(e["term"], text))


def pr(tp, fp, fn):
    p = f"{tp / (tp + fp):.2f}" if tp + fp else "-"
    r = f"{tp / (tp + fn):.2f}" if tp + fn else "-"
    return f"precision {p} ({tp}/{tp + fp}), recall {r} ({tp}/{tp + fn})"


def checked(entries, text, identity):
    """The inventory's own checks on one unit's entries (strip_own_code, then verify_a: code and term printed
    within one unit, a near-miss term repaired to the printed phrase); with identity, also drop an entry whose
    term is only its code ('PA' = 'PA'). -> the entries kept"""
    import copy
    import decoder_v2 as v2
    keep = []
    for e in entries:
        e = v2.strip_own_code(copy.deepcopy(e))
        if v2.verify_a(e, text):
            continue
        if identity and ncode(e["term"]) == ncode(e["code"]):
            continue
        keep.append(e)
    return keep


def column_codes(values):
    out = set()
    for v in values:
        out.add(ncode(v))
        out |= {ncode(x) for x in re.split(r"\s*[,;/]\s*|\s+", v) if x}
    return out


def evaluate(G, run, equiv, cols):
    """All the measures for one set of model entries per unit. -> (summary lines, detail lines)"""
    sub = lambda u: u.get("subtypes") or ([u["subtype"]] if u["is_definition"] else [])
    S, D = [], []
    # 1 unit recognition
    conf = collections.Counter()
    by_struct = collections.defaultdict(collections.Counter)
    by_sub = collections.defaultdict(collections.Counter)
    for k, u in G.items():
        pos, got = u["is_definition"], bool(run[k])
        cell = ("TP" if got else "FN") if pos else ("FP" if got else "TN")
        conf[cell] += 1
        by_struct[u["structure"]][cell] += 1
        for s in sub(u) or ["none"]:
            by_sub[s][cell] += 1
    S += ["1. UNIT RECOGNITION (does the unit define codes?)",
          f"  all units: {pr(conf['TP'], conf['FP'], conf['FN'])}; true negatives {conf['TN']}"]
    for s in KINDS:
        c = by_sub[s]
        S.append(f"  {s:22s} recognised {c['TP']}/{c['TP'] + c['FN']}")
    S.append(f"  {'none':22s} wrongly recognised {by_sub['none']['FP']}/{by_sub['none']['FP'] + by_sub['none']['TN']}")
    S.append("  by structure (TP FP FN TN):")
    for s in STRUCTURES:
        c = by_struct[s]
        S.append(f"    {s:14s} {c['TP']:3d} {c['FP']:3d} {c['FN']:3d} {c['TN']:3d}")
    for k, u in G.items():
        if u["is_definition"] and not run[k]:
            D.append(f"  unit missed: {k} [{u['structure']}] {'/'.join(sub(u))}")

    # 2 mapping extraction, 3 variable attribution, 6 unsupported
    status = collections.defaultdict(collections.Counter)
    kinds, var = collections.Counter(), collections.Counter()
    var_diff, wording, missing, unsupported = [], [], [], []
    found = {}
    for k, u in G.items():
        P = run[k]
        used = set()
        terms = {nterm(m["term"]): m["code"] for m in u["mappings"]}
        for m in u["mappings"]:
            kind = m.get("kind") or u["subtype"]
            c = ncode(m["code"])
            same = [i for i, p in enumerate(P) if ncode(p["code"]) == c and i not in used]
            if not same:
                st = "missing"
                missing.append(f"  {k} {m['code']!r} = {m['term'][:70]!r}")
            else:
                own = {nterm(m["term"]), nterm(m.get("printed_as", m["term"]))}
                ex = [i for i in same if nterm(P[i]["term"]) in own]
                eq = equiv.get((u["legend_id"], c, nterm(m["term"])), set())
                cr = [i for i in same if nterm(P[i]["term"]) in eq]
                i = (ex or cr or same)[0]
                used.add(i)
                other = terms.get(nterm(P[i]["term"]))
                st = ("exact" if ex else "cross-source equivalent" if cr
                      else "wrong pairing" if other is not None and ncode(other) != c else "other wording")
                if st in ("other wording", "wrong pairing"):
                    wording.append(f"  {st}: {k} {m['code']!r}: gold {m['term'][:70]!r} / model {P[i]['term'][:70]!r}"
                                   + (f" (the term of {other!r})" if st == "wrong pairing" else ""))
                kinds["same kind" if P[i]["kind"] == kind else f"{kind} -> {P[i]['kind']}"] += 1
                gv, pv = words(m["variable"]), words(P[i]["variable"])
                v = "not given" if not pv else "shares a word" if gv & pv else "differs"
                var[v] += 1
                if v != "shares a word":
                    var_diff.append(f"  {k} {m['code']!r}: gold {m['variable']!r} / model {P[i]['variable']!r}")
            status[kind][st] += 1
            status["all"][st] += 1
            found.setdefault((u["legend_id"], c), {})[k] = st
        for i, p in enumerate(P):
            if i not in used:
                unsupported.append((k, u["is_definition"], printed(p, u["text"]), p))
    S += ["", "2. MAPPING EXTRACTION (each gold code -> term pair; exact = the wording of the unit the model got, "
              "up to case, spacing and surrounding punctuation; wrong pairing = the term of another code)"]
    ST = ("exact", "cross-source equivalent", "other wording", "wrong pairing", "missing")
    for s in ["all"] + KINDS:
        c = status[s]
        S.append(f"  {s:22s} {sum(c.values()):3d} pairs: " + ", ".join(f"{x} {c[x]}" for x in ST))
    multi = {key: v for key, v in found.items() if len(v) >= 2}
    agree = sum(all(s in ("exact", "cross-source equivalent") for s in v.values()) for v in multi.values())
    S.append(f"  repeated legends: {agree}/{len(multi)} codes read alike (exact or adjudicated equivalent) in "
             f"every copy")
    S.append("  kind of the matched pairs: " + ", ".join(f"{a} {b}" for a, b in kinds.most_common()))
    D += ["", "2. wording and pairing (for reading)"] + wording + ["", "2. missing pairs"] + missing
    S += ["", "3. VARIABLE ATTRIBUTION (matched pairs; 'shares a word' is a first pass, the rest listed for reading)",
          "  " + ", ".join(f"{a} {b}" for a, b in var.most_common())]
    D += ["", "3. variables that differ or are not given"] + var_diff

    # 4 target association
    def assoc(skip_disputed):
        c = collections.Counter()
        per = collections.defaultdict(collections.Counter)
        codes_ok, detail = 0, []
        for k, u in G.items():
            P = run[k]
            for t in u["targets"]:
                if skip_disputed and t.get("disputed_header"):
                    continue
                col = f"t{t['table']}c{t['col']}"
                held = column_codes(cols[(k, t["table"], t["col"])])
                pc = {ncode(p["code"]) for p in P if col in p["columns"]}
                g, got = bool(t["decoded_by"]), bool(pc)
                cell = ("TP" if got else "FN") if g else ("FP" if got else "TN")
                c[cell] += 1
                per[u["subtype"] if u["is_definition"] else "none"][cell] += 1
                right = cell == "TP" and (pc & held) == {ncode(x) for x in t["decoded_by"]}
                codes_ok += right
                if cell in ("FP", "FN") or (cell == "TP" and not right):
                    detail.append(f"  {cell} {k} -> {col} {t['header'][:50]!r}: gold {sorted(t['decoded_by'])} "
                                  f"model {sorted(pc)} (in the column: {sorted(pc & held)})")
        return c, per, codes_ok, detail
    S += ["", "4. TARGET ASSOCIATION (each candidate column the selector proposed: does the unit decode it? "
              "code set = the model's codes that the column holds)"]
    for skip in (False, True):
        c, per, ok, detail = assoc(skip)
        S.append(f"  {'without' if skip else 'with'} the disputed-header cases: {pr(c['TP'], c['FP'], c['FN'])}; "
                 f"true negatives {c['TN']}; right code set on {ok}/{c['TP']} true positives")
        for s in KINDS + ["none"]:
            x = per[s]
            S.append(f"    {s:22s} TP {x['TP']:3d} FP {x['FP']:3d} FN {x['FN']:3d} TN {x['TN']:3d}")
    D += ["", "4. association errors and code-set differences (with the disputed cases)"] + assoc(False)[3]

    # 6 unsupported extraction
    up = collections.Counter(("definition unit" if d else "non-definition unit", "printed" if pt else "not printed")
                             for _k, d, pt, _p in unsupported)
    ident = sum(ncode(p["term"]) == ncode(p["code"]) for *_x, p in unsupported)
    S += ["", "6. UNSUPPORTED EXTRACTION (pairs the model returned that are not gold mappings of the unit; "
              "'printed' = code and term both printed in the unit)",
          f"  {len(unsupported)} pairs: " + ", ".join(f"{a} / {b} {n}" for (a, b), n in sorted(up.items()))
          + f"; of all of them, term = code {ident}"]
    D += ["", "6. unsupported pairs"]
    for k, d, pt, p in unsupported:
        D.append(f"  {k} [{'def' if d else 'none'}, {'printed' if pt else 'NOT printed'}] {p['kind']}: "
                 f"{p['code']!r} = {p['term'][:80]!r} ({p['variable'][:60]!r}) cols {p['columns']}")
    return S, D


def score(gold_file, run_file):
    import pathlib
    gold = json.loads(open(gold_file, encoding="utf-8").read())
    if "frozen" not in gold.get("version", ""):
        raise SystemExit("the gold is not frozen")
    G = {u["uid"]: u for u in gold["units"]}
    R = json.loads(open(run_file, encoding="utf-8").read())
    raw = {u["uid"]: u["entries"] for u in R["units"]}
    assert set(G) == set(raw), (set(G) ^ set(raw))
    cols = {(x["uid"], c["table"], c["col"]): c["values"]
            for x in json.loads((pathlib.Path(gold_file).parent / "calib_units.json").read_text(encoding="utf-8"))
            for c in x["candidate_columns"]}
    equiv = {}
    for a in gold["wording_adjudication"]:
        if a["equivalent"]:
            ws = {nterm(w) for w in a["wordings"].values()}
            for w in ws:
                equiv[(a["legend_id"], ncode(a["code"]), w)] = ws
    L = [f"Legend calibration: {R['model']}, run {R['date']}, gold {gold['version']}",
         f"{len(G)} source units, {sum(len(u['mappings']) for u in G.values())} gold mappings, "
         f"{sum(len(u['targets']) for u in G.values())} candidate associations.",
         "The set is stratified and holds positive controls: these are calibration and failure-analysis numbers, "
         "not estimates of corpus-wide precision. Each unit counts once (repeated copies of a legend count apart).",
         ""]
    views = [("A. RAW: the model's entries as returned", raw),
             ("B. INVENTORY CHECKS: strip_own_code + verify_a (code and term printed within the unit), as the "
              "inventory already applies", {k: checked(v, G[k]["text"], False) for k, v in raw.items()}),
             ("C. B + TERM IS NOT THE CODE (a candidate check: drops 'PA' = 'PA')",
              {k: checked(v, G[k]["text"], True) for k, v in raw.items()})]
    details = {}
    for name, entries in views:
        S, D = evaluate(G, entries, equiv, cols)
        L += ["=" * 100, name, "=" * 100] + S + [""]
        details[name] = D
    linked = sum(bool(t["decoded_by"]) for u in G.values() for t in u["targets"])
    missed = sum(len(u.get("missed_targets", [])) for u in G.values())
    defs = sum(u["is_definition"] for u in G.values())
    L += ["=" * 100, "5. SELECTOR RECALL (from the gold; the model never received these)",
          f"  target columns: {linked} decoded columns proposed, {missed} missed -> {linked / (linked + missed):.2f}",
          f"  definition units: {defs} proposed, {len(gold['selector_unit_misses'])} never proposed -> "
          f"{defs / (defs + len(gold['selector_unit_misses'])):.2f}"]
    for u in G.values():
        for t in u.get("missed_targets", []):
            L.append(f"  missed target: {u['uid']} -> t{t['table']}c{t['col']} {t['header'][:50]!r} ({t['note'][:80]})")
        if u.get("truncated"):
            L.append(f"  unit boundary: {u['uid']}: {u['truncated']}")
    for x in gold["selector_unit_misses"]:
        L.append(f"  unit never proposed: {x['paper']} [{x['structure']}] {x['text_starts']!r}")
    L += ["", "=" * 100, "DETAIL, view A (raw)", "=" * 100] + details[views[0][0]]
    L += ["", "=" * 100, "PER UNIT (gold subtype; raw model entries)", "=" * 100]
    sub = lambda u: u.get("subtypes") or ([u["subtype"]] if u["is_definition"] else [])
    for k, u in G.items():
        L.append(f"  {k:28s} [{u['structure']}] {'/'.join(sub(u)) or 'none':24s} "
                 + "; ".join(f"{p['code']}={p['term'][:40]}" for p in raw[k]))
    f = OUT / f"CALIB_REPORT_{R['date']}.txt"
    f.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:L.index("DETAIL, view A (raw)") - 1]))
    print(f"-> {f}")


if __name__ == "__main__":
    {"build": build, "calibrate": calibrate, "score": score}[sys.argv[1]](*sys.argv[2:])
