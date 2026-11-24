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
  score      (code) the run against the FROZEN gold; every level reported apart, each subtype and structure apart:
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


def score(gold_file, run_file):
    gold = json.loads(open(gold_file, encoding="utf-8").read())
    if "frozen" not in gold.get("version", ""):
        raise SystemExit("the gold is not frozen")
    G = {u["uid"]: u for u in gold["units"]}
    R = json.loads(open(run_file, encoding="utf-8").read())
    run = {u["uid"]: u for u in R["units"]}
    assert set(G) == set(run), (set(G) ^ set(run))
    equiv = {}
    for a in gold["wording_adjudication"]:
        if a["equivalent"]:
            ws = {nterm(w) for w in a["wordings"].values()}
            for w in ws:
                equiv[(a["legend_id"], ncode(a["code"]), w)] = ws
    sub = lambda u: u.get("subtypes") or ([u["subtype"]] if u["is_definition"] else [])

    L = [f"Legend calibration: {R['model']}, run {R['date']}, gold {gold['version']}",
         f"{len(G)} source units, {sum(len(u['mappings']) for u in G.values())} gold mappings, "
         f"{sum(len(u['targets']) for u in G.values())} candidate associations.",
         "The set is stratified and holds positive controls: these are calibration and failure-analysis numbers, "
         "not estimates of corpus-wide precision.", ""]

    # 1 unit recognition
    conf = collections.Counter()
    by_struct = collections.defaultdict(collections.Counter)
    by_sub = collections.defaultdict(collections.Counter)
    for k, u in G.items():
        pos, got = u["is_definition"], bool(run[k]["entries"])
        cell = ("TP" if got else "FN") if pos else ("FP" if got else "TN")
        conf[cell] += 1
        by_struct[u["structure"]][cell] += 1
        for s in sub(u) or ["none"]:
            by_sub[s][cell] += 1
    L += ["1. UNIT RECOGNITION (does the unit define codes?)",
          f"  all units: {pr(conf['TP'], conf['FP'], conf['FN'])}; true negatives {conf['TN']}"]
    for s in KINDS:
        c = by_sub[s]
        L.append(f"  {s:22s} recognised {c['TP']}/{c['TP'] + c['FN']}")
    L.append(f"  {'none':22s} wrongly recognised {by_sub['none']['FP']}/{by_sub['none']['FP'] + by_sub['none']['TN']}")
    L.append("  by structure (TP FP FN TN):")
    for s in STRUCTURES:
        c = by_struct[s]
        L.append(f"    {s:14s} {c['TP']:3d} {c['FP']:3d} {c['FN']:3d} {c['TN']:3d}")

    # 2 mapping extraction, 3 variable attribution, 6 unsupported
    status = collections.defaultdict(collections.Counter)
    kinds, var = collections.Counter(), collections.Counter()
    var_diff, wording, unsupported = [], [], []
    found = {}                                               # (legend_id, code) -> {uid: status}
    for k, u in G.items():
        P = run[k]["entries"]
        used = set()
        for m in u["mappings"]:
            kind = m.get("kind") or u["subtype"]
            c = ncode(m["code"])
            same = [i for i, p in enumerate(P) if ncode(p["code"]) == c and i not in used]
            if not same:
                st = "missing"
            else:
                own = {nterm(m["term"]), nterm(m.get("printed_as", m["term"]))}
                ex = [i for i in same if nterm(P[i]["term"]) in own]
                eq = equiv.get((u["legend_id"], c, nterm(m["term"])), set())
                cr = [i for i in same if nterm(P[i]["term"]) in eq]
                i = (ex or cr or same)[0]
                used.add(i)
                st = "exact" if ex else "cross-source equivalent" if cr else "other wording"
                if st == "other wording":
                    wording.append(f"  {k} {m['code']!r}: gold {m['term']!r} / model {P[i]['term']!r}")
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
    L += ["", "2. MAPPING EXTRACTION (each gold code -> term pair; exact = the wording of the unit the model got, "
              "up to case, spacing and surrounding punctuation)"]
    for s in ["all"] + KINDS:
        c = status[s]
        n = sum(c.values())
        L.append(f"  {s:22s} {n:3d} pairs: exact {c['exact']}, cross-source equivalent {c['cross-source equivalent']}, "
                 f"other wording {c['other wording']}, missing {c['missing']}")
    multi = {key: v for key, v in found.items() if len(v) >= 2}
    agree = sum(all(s in ("exact", "cross-source equivalent") for s in v.values()) for v in multi.values())
    L.append(f"  repeated legends: {agree}/{len(multi)} codes read alike (exact or adjudicated equivalent) in every copy")
    L.append("  kind of the matched pairs: " + ", ".join(f"{a} {b}" for a, b in kinds.most_common()))
    if wording:
        L += ["  other wording (for reading):"] + wording
    L += ["", "3. VARIABLE ATTRIBUTION (matched pairs; 'shares a word' is a first pass, the differences are listed "
              "for reading)", "  " + ", ".join(f"{a} {b}" for a, b in var.most_common())] + var_diff

    # 4 target association
    def assoc(skip_disputed):
        c = collections.Counter()
        per = collections.defaultdict(collections.Counter)
        codes_ok, detail = 0, []
        for k, u in G.items():
            P = run[k]["entries"]
            for t in u["targets"]:
                if skip_disputed and t.get("disputed_header"):
                    continue
                col = f"t{t['table']}c{t['col']}"
                pc = {ncode(p["code"]) for p in P if col in p["columns"]}
                g, got = bool(t["decoded_by"]), bool(pc)
                cell = ("TP" if got else "FN") if g else ("FP" if got else "TN")
                c[cell] += 1
                per[u["subtype"] if u["is_definition"] else "none"][cell] += 1
                if cell == "TP" and pc == {ncode(x) for x in t["decoded_by"]}:
                    codes_ok += 1
                if cell in ("FP", "FN") or (cell == "TP" and pc != {ncode(x) for x in t["decoded_by"]}):
                    detail.append(f"  {cell} {k} -> {col} {t['header'][:50]!r}: gold {sorted(t['decoded_by'])} "
                                  f"model {sorted(pc)}")
        return c, per, codes_ok, detail
    L += ["", "4. TARGET ASSOCIATION (each candidate column the selector proposed: does the unit decode it?)"]
    for skip in (False, True):
        c, per, ok, detail = assoc(skip)
        L.append(f"  {'without' if skip else 'with'} the disputed-header cases: {pr(c['TP'], c['FP'], c['FN'])}; "
                 f"true negatives {c['TN']}; right code set on {ok}/{c['TP']} true positives")
        for s in KINDS + ["none"]:
            x = per[s]
            L.append(f"    {s:22s} TP {x['TP']:3d} FP {x['FP']:3d} FN {x['FN']:3d} TN {x['TN']:3d}")
    L += ["  errors and code-set differences (with the disputed cases):"] + assoc(False)[3]

    # 5 selector recall (gold only)
    linked = sum(bool(t["decoded_by"]) for u in G.values() for t in u["targets"])
    missed = sum(len(u.get("missed_targets", [])) for u in G.values())
    defs = sum(u["is_definition"] for u in G.values())
    L += ["", "5. SELECTOR RECALL (from the gold; the model never received these)",
          f"  target columns: {linked} decoded columns proposed, {missed} missed -> {linked / (linked + missed):.2f}",
          f"  definition units: {defs} proposed, {len(gold['selector_unit_misses'])} never proposed -> "
          f"{defs / (defs + len(gold['selector_unit_misses'])):.2f}"]
    for u in G.values():
        if u.get("truncated"):
            L.append(f"  unit boundary: {u['uid']}: {u['truncated']}")

    # 6 unsupported extraction
    up = collections.Counter(("definition unit" if d else "non-definition unit", "printed" if pt else "not printed")
                             for _k, d, pt, _p in unsupported)
    L += ["", "6. UNSUPPORTED EXTRACTION (pairs the model returned that are not gold mappings of the unit; "
              "'printed' = code and term both printed in the unit)",
          "  " + ", ".join(f"{a} / {b}: {n}" for (a, b), n in sorted(up.items()))]
    for k, d, pt, p in unsupported:
        L.append(f"  {k} [{'def' if d else 'none'}, {'printed' if pt else 'NOT printed'}] {p['kind']}: "
                 f"{p['code']!r} = {p['term']!r} ({p['variable']!r}) cols {p['columns']}")

    L += ["", "PER UNIT (gold subtype; model entries)"]
    for k, u in G.items():
        L.append(f"  {k:28s} [{u['structure']}] {'/'.join(sub(u)) or 'none':24s} "
                 + "; ".join(f"{p['code']}={p['term'][:40]}" for p in run[k]["entries"])[:300])
    f = OUT / f"CALIB_REPORT_{R['date']}.txt"
    f.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    print(f"-> {f}")


if __name__ == "__main__":
    {"build": build, "calibrate": calibrate, "score": score}[sys.argv[1]](*sys.argv[2:])
