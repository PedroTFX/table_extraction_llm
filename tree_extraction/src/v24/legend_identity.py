"""
legend_identity.py — a separate column-identity route for legends that do not print a word of the column's header
(2026-11-26, after legend_selector_misses.py). R3abc stays frozen and is not changed: this route is evaluated on its
own, and nothing is wired into the pipeline.

The diagnosis found the frozen selector's header-word requirement (R2: a distinctive code, or >= 2 codes AND an
informative header word) behind 5 of its 7 validated failures, in three forms: a synonym (Graf2021 'Nidification'
for 'Nesting site'), a cross-reference mark shared by the header and the note (AmbspergTraun1991 † ‡), and identity
through the meanings only (Wang2021's caption, Eckert2023's own-table note). The code/meaning adjacency case
(Cappellari2022) and the lowercase code (Espinosa2023) are parser questions, kept apart.

  pool   (no model) the pairs (unit, column) R3abc rejects ONLY for want of a header word: every other R3abc gate holds
         as it is (the column enumerated; >= 2 of its codes in the unit with strict number boundaries (b); at least
         one printed next to a meaning (a); a table row not repeated for the column in more than MAX_REPEAT rows of
         its table; a body row of the column's own table is data) and no distinctive code. A taxon header's dropped
         words (c) count as no header word. Safe cut (dk.SAFE_TAGS): the corrected text. Each pair carries
         descriptive source facts for the model: the unit's structure; whether it is by the column's own table (its
         row, a caption within 3000 characters before it, a note within 1500 after it); a mark (†‡§¶*#) printed both
         in the header and in the unit. The facts select nothing.
         -> TREE_OUTPUT/legend_coverage/identity_pool_<date>.json, IDENTITY_POOL_<date>.txt
         Result (2026-11-26, 82 tuning papers): 5,610 pairs in 643 units of 64 papers; 5,417 match numbers only, and
         none of the validated failures is among them. All six validated header-identity failure columns are in the
         184 pairs with >= 2 letter codes (78 units, 27 papers; Taillefer's split table 73 of them).

  gold   the evaluation set and its labels, fixed BEFORE any model call (Claude's by eye, the user to check), in
         EVAL_* and GOLD_YES below -> identity_gold_<date>.csv. Strata:
           letter      every pool pair with >= 2 letter codes; Taillefer2018 (page-split table, upstream) is left out,
                       Wallon2024's glued 'Dispersaldisp' column and its header-less continuation are run but not
                       scored (upstream). Labels: yes = the unit defines what the column's cells mean (a variable
                       abbreviation decoding a column of variable names counts, as in gold v4.1)
           not-target  every numeric pool pair on the 11 key columns the diagnosis judged no target (the codes are
                       never defined in the paper): all no
           decoy       every numeric pool pair on the calibration's judged decoy columns (rejected_unlinked_columns of
                       gold v4.1): all no
           sample      a seeded sample (SEED) of 40 other numeric pairs, Tonelli2021 (boundary queue) and Taillefer2018
                       left out: all no by eye
  run    (gemma, v1.GEMMA) one prompt per unit with all its evaluation columns: the passage, where it is printed,
         and per column its header path, cell values and the source facts. The model gives per column the evidence
         type (names the variable / cross-reference / meanings fit / insufficient), decodes, codes, reason. Code
         applies the answer: a link is decodes = true with evidence other than insufficient. The prompt's examples are
         made up; the run first checks that none of them is printed in any paper.
         -> identity_run_<stamp>.json
  score  -> IDENTITY_REPORT_<stamp>.txt, against the criteria fixed here before the run:
           C1  at least 5 of the 6 validated failure columns linked by a unit labelled yes for them (Graf2021 t8c2,
               AmbspergTraun1991 t0c4 and t0c5, Wang2021 t1c4 and t1c5, Eckert2023 t4c3)
           C2  letter stratum precision (links labelled yes / links) >= 0.85
           C3  letter stratum recall (yes pairs linked / yes pairs) >= 0.70
           C4  not-target stratum: at most 1 link
           C5  decoy stratum: at most 2 links
           C6  sample stratum: at most 2 links
         The route passes only if all six hold. Nothing is wired in either way without the user's word.
         Result (run 2026-11-26_1518, gemma4:e4b-it-qat): FAILS C2, precision 0.69 (24 of 35 links); C1 6 of 6,
         recall 0.77, 0 links on the 170 numeric control and sample pairs. NOT ADOPTED; no revised test authorised.
         False links: 9 columns of named entities (countries, sites, parks, continents) that a passage only
         mentions, Pessoa2017's figure colour key, Raine2018's header enumeration. Misses: 3 variable-name columns
         refused for partial definitions, 2 complete legends refused for a generic header, 2 Eckert2023 own-table
         notes. Write-up: output/legend_coverage/IDENTITY_ROUTE_RESULT_2026-11-27.md.

    python legend_identity.py pool [papers]       (tuning papers by default)
    python legend_identity.py gold
    python legend_identity.py run
    python legend_identity.py score <identity_run.json>
"""
from __future__ import annotations

import collections
import contextlib
import csv
import io
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
import legend_inventory as li
import legend_scope as ls
import tag_strip_check as ts

OUT = lc.OUT
MARKS = "†‡§¶*#"
POOL = OUT / "identity_pool_2026-11-26.json"
GOLD = OUT / "identity_gold_2026-11-26.csv"
SEED = 20261126
N_SAMPLE = 40
EVAL_LEFT_OUT = {"Taillefer2018"}                        # upstream: page-split table, header on the first part only
SAMPLE_LEFT_OUT = {"Taillefer2018", "Tonelli2021"}       # Tonelli: the list-boundary queue
UPSTREAM_COLUMNS = {("Wallon2024", "t24c14"), ("Wallon2024", "t29c14")}   # glued header; header-less continuation
NOT_TARGET = {("Vidal2023", c) for c in ("t11c9", "t11c10", "t11c11", "t11c14", "t12c4", "t12c5", "t12c6")} | {
    ("Fiedler2021", "t7c2"), ("Fiedler2021", "t7c15"), ("Normandin2017", "t8c4"), ("Wallon2024", "t28c5"),
    ("Wallon2024", "t28c11")}
DECOYS = {("Cappellari2022", "t8c2"), ("Cappellari2022", "t8c3"), ("Cecala2021", "t2c7"), ("Cecala2021", "t2c8"),
          ("Guareschi2015", "t2c0"), ("Jones2015", "t2c4"), ("Uemori2022", "t3c2"), ("Uemori2022", "t3c5"),
          ("Uemori2022", "t3c6"), ("Uemori2022", "t3c7")}
VALIDATED = [("Graf2021", "t8c2"), ("AmbspergTraun1991", "t0c4"), ("AmbspergTraun1991", "t0c5"),
             ("Wang2021", "t1c4"), ("Wang2021", "t1c5"), ("Eckert2023", "t4c3")]
# letter stratum, labelled yes by eye (every other scored letter pair is no): (paper, unit, column): note
GOLD_YES = {
    ("AmbspergTraun1991", "p37", "t0c4"): "cross-reference † (table note)",
    ("AmbspergTraun1991", "p37", "t0c5"): "cross-reference ‡ (table note)",
    ("Cappellari2022", "p129", "t0c0"): "variable abbreviations Apis, Temp; a column of variable names",
    ("Cappellari2022", "p88", "t0c0"): "variable abbreviations Apis, Temp; a column of variable names",
    ("Derhe2016", "p160", "t4c0"): "Sobs, Sest; a column of measure names",
    ("Eckert2023", "t4r134", "t4c3"): "own table note; habitat codes",
    ("Eckert2023", "t4r134", "t6c5"): "the same habitat codes in another table",
    ("Eckert2023", "t4r70", "t4c3"): "own table note; habitat codes",
    ("Eckert2023", "t4r70", "t6c5"): "the same habitat codes in another table",
    ("Eckert2023", "t6r103", "t4c3"): "the same habitat codes in another table",
    ("Eckert2023", "t6r103", "t6c5"): "own table note; habitat codes",
    ("Eckert2023", "t6r103", "t6c6"): "own table note; Chew, Suck mandibles",
    ("Eckert2023", "t6r72", "t4c3"): "the same habitat codes in another table",
    ("Eckert2023", "t6r72", "t6c5"): "own table note; habitat codes",
    ("Eckert2023", "t6r72", "t6c6"): "own table note; Chew, Suck mandibles",
    ("Graf2021", "p141", "t8c2"): "synonym 'Nidification'",
    ("Kovacs2008", "p78", "t2c1"): "mated (M) and unmated (U) gynes; the 'Group' column of the table before",
    ("Oliveira2022", "p57", "t1c0"): "species abbreviations; a 'Category' column of the same codes",
    ("Tonelli2021", "p35", "t1c2"): "Quan, Qual; the 'Data Type' column",
    ("Wallon2024", "p190", "t6c1"): "trait abbreviations; a column of trait names",
    ("Wallon2024", "p190", "t12c1"): "trait abbreviations; a column of trait names",
    ("Wallon2024", "p199", "t6c1"): "trait abbreviations; a column of trait names",
    ("Wallon2024", "p199", "t12c1"): "trait abbreviations; a column of trait names",
    ("Wallon2024", "p93", "t6c1"): "trait abbreviations; a column of trait names",
    ("Wallon2024", "p93", "t12c1"): "trait abbreviations; a column of trait names",
    ("Wallon2024", "t1r2", "t6c1"): "trait abbreviations; a column of trait names",
    ("Wallon2024", "t1r2", "t12c1"): "trait abbreviations; a column of trait names",
    ("Wallon2024", "p220", "t15c1"): "trait abbreviations Hdisp, Black; a column of trait names",
    ("Wallon2024", "p229", "t15c1"): "trait abbreviations Hdisp, Black; a column of trait names",
    ("Wang2021", "p117", "t1c4"): "meanings only: carnivorous (C), omnivorous (O)",
    ("Wang2021", "p117", "t1c5"): "meanings only: macropterous (M), brachypterous (B)",
}
EVIDENCE = ["names the variable", "cross-reference", "meanings fit", "insufficient"]
EXAMPLES = ["Substrate: B, bark", "S, stone", "Diet*", "*H, herbivore", "C, carnivore", "dry (D)", "wet (W)",
            "Habitat moisture"]

PROMPT = """Below is a passage from a scientific paper ({where}) and some table columns of the same paper. Each column's cells hold short codes, and the passage prints some of these codes next to words. The passage does not repeat the words of the columns' headers, so decide from the evidence whether the passage tells what THIS column's codes mean.

Passage:
{text}

Columns (id | header | cell values | facts):
{columns}

For each column give:
- id: the column's id
- evidence: one of
  "names the variable": the passage names what the column records, in other words than its header (e.g. a passage "Substrate: B, bark; S, stone" for a column headed "Microhabitat")
  "cross-reference": a mark or label printed in the column's header is printed in the passage right before the definitions (e.g. a header "Diet*" and a note "*H, herbivore; C, carnivore")
  "meanings fit": the passage does not name the variable, but the meanings it gives these codes are values of exactly what the column records (e.g. "dry (D) or wet (W) sites" for a column headed "Habitat moisture")
  "insufficient": anything else, e.g. the codes only happen to be printed in the passage (initials, names, references, statistics, numbered sentences or hypotheses, figure panels); the passage defines the codes for another variable than this column's; or it prints the codes without saying what they mean
- decodes: true if the passage's definitions tell what this column's cells mean, false if not
- codes: the column's codes that the passage defines ([] if decodes is false)
- reason: a short reason

Reply with JSON only."""

SCHEMA = {"type": "object", "required": ["columns"],
          "properties": {"columns": {"type": "array", "items": {
              "type": "object", "required": ["id", "evidence", "decodes", "codes", "reason"],
              "properties": {"id": {"type": "string"}, "evidence": {"type": "string", "enum": EVIDENCE},
                             "decodes": {"type": "boolean"}, "codes": {"type": "array", "items": {"type": "string"}},
                             "reason": {"type": "string"}}}}}}


def flat(t):
    return " ".join(str(t or "").split())


def uid(u):
    if u["table"] is None:
        return f"p{u['id']}"
    return f"t{u['table']}r{u['row']}" + (f"c{u['col']}" if u["structure"] == "head cell" else "")


def near(u, raw, spans):
    if u["table"] is not None:
        return {"table": u["table"]}
    words = re.findall(r"\S+", u["text"])[:8]
    m = re.search(r"\s+".join(map(re.escape, words)), raw) if words else None
    if not m:
        return {}
    a = m.start()
    nxt = next(((k, s - a) for k, (s, _e) in enumerate(spans) if s > a), None)
    prv = next(((k, a - e) for k, (_s, e) in reversed(list(enumerate(spans))) if e <= a), None)
    return {"next": nxt, "prev": prv}


def own(nr, k):
    nxt, prv = nr.get("next") or (None, 0), nr.get("prev") or (None, 0)
    return nr.get("table") == k or (nxt[0] == k and nxt[1] < 3000) or (prv[0] == k and prv[1] < 1500)


# --- pool (no model) -------------------------------------------------------------------------------------------------

def paper_pool(p, head):
    """The pool pairs of one paper (safe cut)."""
    with ts.strip(True), contextlib.redirect_stdout(io.StringIO()):
        grids = {k: ht.grid_from_html(h) for k, h in enumerate(hb.html_tables(p))}
        first = {e["table"]: e.get("first") or 1 for e in head[p]}
        cols = lc.columns(p, grids, first)
        units = lc.units(p, grids, first)
        names = la.organism_names(p, head)
    genera = {n.split()[0] for n in names if len(n.split()) >= 2}
    for col in cols:
        col["taxon"] = la.is_taxon_header(col["header"], names, genera)
    raw = (_paths.PAPERS / p / f"{p}_full.md").read_text(encoding="utf-8", errors="replace")
    spans = [(m.start(), m.end()) for m in re.finditer(r"<table.*?</table>", raw, flags=re.S | re.I)]
    pairs = []
    for u in units:
        letters, nums, stems = lc.tokens(u["text"])
        strict = {str(int(m.group(1) or m.group(2))) for m in la.NUM_STRICT.finditer(u["text"])}
        t = flat(u["text"])
        nr = None
        for col in cols:
            if u["table"] == col["table"] and u["structure"] == "table row":
                continue
            hit, dist, words = lc.associate(u, (letters, nums, stems), col)
            hit_s = [x for x in hit if col["codes"][x] != "numeric" or x in strict]
            if len(hit_s) < 2:
                continue
            dist_s = [x for x in dist if x in hit_s]
            words_c = [] if col["taxon"] else words
            if dist_s or words_c:
                continue                                  # R2 holds: R3abc's own route decides this pair
            exp = [x for x in la.explicit_codes(t, col) if x in hit_s]
            if not exp:
                continue                                  # gate a fails: not this route's question
            if nr is None:
                nr = near(u, raw, spans)
            hm = {ch for ch in MARKS if ch in col["header"]}
            pairs.append({"paper": p, "unit": uid(u), "unit_id": u["id"], "structure": u["structure"],
                          "unit_table": u["table"], "column": f"t{col['table']}c{col['col']}", "table": col["table"],
                          "header": col["header"], "values": col["values"][:lc.MAX_DISTINCT],
                          "codes": hit_s, "explicit": exp, "taxon_header": col["taxon"],
                          "header_words_dropped": words if col["taxon"] else [],
                          "own_table": own(nr, col["table"]), "near": nr,
                          "shared_mark": sorted(ch for ch in hm if ch in t), "shapes": li.shape_hits(u["text"]),
                          "text": t[:1500]})
    rep = collections.Counter((x["unit_table"], x["column"]) for x in pairs if x["structure"] == "table row")
    return [x for x in pairs if not (x["structure"] == "table row" and rep[(x["unit_table"], x["column"])] > lc.MAX_REPEAT)]


def pool(papers):
    OUT.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y-%m-%d")
    head = fr.head_runs()
    allp = []
    for p in papers:
        if p not in head:
            continue
        t0 = time.time()
        ps = paper_pool(p, head)
        allp += ps
        print(f"  {p:22s} {len(ps):5d} pairs, {len({x['unit'] for x in ps}):4d} units  {time.time() - t0:.0f}s", flush=True)
    units = {(x["paper"], x["unit"]) for x in allp}
    letter = [x for x in allp if is_letter(x)]
    L = [f"identity-route pool (R3abc rejects the pair only for want of a header word), {len(papers)} tuning papers, "
         f"safe cut; no model", "",
         f"pairs {len(allp)}, units {len(units)}, papers {len({x['paper'] for x in allp})}",
         f"pairs with >= 2 letter codes {len(letter)} (units {len({(x['paper'], x['unit']) for x in letter})}, papers "
         f"{len({x['paper'] for x in letter})}); numbers only {sum(not is_letter(x) for x in allp)}",
         "by structure (pairs / units): " + ", ".join(
             f"{s} {sum(x['structure'] == s for x in allp)} / {len({(x['paper'], x['unit']) for x in allp if x['structure'] == s})}"
             for s in ("prose", "caption", "numbered list", "head cell", "footnote", "table row")),
         f"by the column's own table {sum(x['own_table'] for x in allp)}; a shared mark {sum(bool(x['shared_mark']) for x in allp)}; "
         f"taxon header (words dropped) {sum(x['taxon_header'] for x in allp)}",
         f"gemma prompts if one per unit (all its pool columns together): {len(units)}", "", "by paper (pairs, units):"]
    pp = collections.Counter(x["paper"] for x in allp)
    for p, n in pp.most_common():
        L.append(f"  {p:22s} [{ls.SPLIT.get(p)}] {n:5d} {len({x['unit'] for x in allp if x['paper'] == p}):4d}")
    (OUT / f"identity_pool_{stamp}.json").write_text(json.dumps(allp, indent=1, ensure_ascii=False), encoding="utf-8")
    (OUT / f"IDENTITY_POOL_{stamp}.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


# --- evaluation set and gold ---------------------------------------------------------------------------------------

def is_letter(x):
    return sum(not re.fullmatch(r"\d{1,2}", c) for c in x["codes"]) >= 2


def evalset():
    """[(stratum, pair)]; strata letter / upstream / not-target / decoy / sample."""
    P = json.loads(POOL.read_text(encoding="utf-8"))
    out = []
    rest = []
    for x in P:
        key = (x["paper"], x["column"])
        if is_letter(x):
            if x["paper"] in EVAL_LEFT_OUT:
                continue
            out.append(("upstream" if key in UPSTREAM_COLUMNS else "letter", x))
        elif key in NOT_TARGET:
            out.append(("not-target", x))
        elif key in DECOYS:
            out.append(("decoy", x))
        elif x["paper"] not in SAMPLE_LEFT_OUT:
            rest.append(x)
    out += [("sample", x) for x in random.Random(SEED).sample(rest, N_SAMPLE)]
    return out


def label(stratum, x):
    if stratum == "upstream":
        return "upstream"
    if stratum == "letter":
        return "yes" if (x["paper"], x["unit"], x["column"]) in GOLD_YES else "no"
    return "no"


def gold():
    E = evalset()
    with open(GOLD, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["stratum", "paper", "unit", "column", "header_last", "codes", "label", "note"])
        for s, x in E:
            w.writerow([s, x["paper"], x["unit"], x["column"], x["header"].split(" / ")[-1][:80], " ".join(x["codes"]),
                        label(s, x), GOLD_YES.get((x["paper"], x["unit"], x["column"]), "")])
    c = collections.Counter((s, label(s, x)) for s, x in E)
    print(f"{len(E)} pairs in {len({(x['paper'], x['unit']) for _s, x in E})} units -> {GOLD}")
    for k, v in sorted(c.items()):
        print(f"  {k[0]:11s} {k[1]:9s} {v}")
    missing = [k for k in GOLD_YES if not any((x["paper"], x["unit"], x["column"]) == k for _s, x in E)]
    assert not missing, f"GOLD_YES pairs not in the evaluation set: {missing}"


# --- run (gemma) -----------------------------------------------------------------------------------------------------

def where_text(x):
    s = x["structure"]
    if s == "head cell":
        return f"a header cell of table {x['unit_table']}"
    if s == "footnote":
        return f"a note row of table {x['unit_table']}"
    if s == "table row":
        return f"a row of table {x['unit_table']}"
    return {"caption": "a figure or table caption", "numbered list": "a paragraph with a numbered list"}.get(s, "a paragraph")


def header_path(h):
    parts = [flat(p) for p in h.split(" / ") if flat(p)]
    return " / ".join([p[:70] + ("..." if len(p) > 70 else "") for p in parts[:-1]] + [p[:90] for p in parts[-1:]])


def render(cols):
    lines = []
    for i, x in enumerate(cols, 1):
        facts = []
        if x["own_table"]:
            facts.append("the passage is printed with this column's own table")
        if x["shared_mark"]:
            facts.append("the header and the passage both print " + ", ".join(f"'{m}'" for m in x["shared_mark"]))
        lines.append(f"C{i} | {header_path(x['header'])} | " + " ; ".join(v[:40] for v in x["values"])
                     + f" | {'; '.join(facts) if facts else '-'}")
    return "\n".join(lines)


def examples_unprinted():
    hits = []
    for f in sorted(_paths.PAPERS.glob("*/*_full.md")):
        t = f.read_text(encoding="utf-8", errors="replace")
        hits += [(f.parent.name, e) for e in EXAMPLES if e in t]
    return hits


def run():
    import decoder as v1
    import decoder_v2 as v2
    hits = examples_unprinted()
    if hits:
        sys.exit(f"prompt examples printed in papers: {hits[:5]}")
    print(f"prompt examples printed in no paper ({len(list(_paths.PAPERS.glob('*/*_full.md')))} papers checked)")
    E = evalset()
    by = collections.defaultdict(list)
    for s, x in E:
        by[(x["paper"], x["unit"])].append((s, x))
    stamp = time.strftime("%Y-%m-%d_%H%M")
    res = []
    for n, ((p, u), items) in enumerate(sorted(by.items()), 1):
        cols = [x for _s, x in items]
        prompt = PROMPT.format(where=where_text(cols[0]), text=cols[0]["text"], columns=render(cols))
        t0 = time.time()
        raw = v2._chat(prompt, SCHEMA, "columns")
        ans = {}
        for a in raw if isinstance(raw, list) else []:
            m = re.fullmatch(r"[Cc]?\s*(\d+)", str(a.get("id", "")).strip()) if isinstance(a, dict) else None
            if m and 1 <= int(m.group(1)) <= len(cols):
                ans[int(m.group(1)) - 1] = a
        for i, (s, x) in enumerate(items):
            a = ans.get(i, {})
            ev = a.get("evidence") if a.get("evidence") in EVIDENCE else None
            res.append({"stratum": s, "paper": p, "unit": u, "column": x["column"], "label": label(s, x),
                        "evidence": ev, "decodes": bool(a.get("decodes")), "codes": [str(c) for c in a.get("codes") or []],
                        "reason": flat(a.get("reason")), "answered": bool(a),
                        "link": bool(a.get("decodes")) and ev not in (None, "insufficient")})
        print(f"{n:3d}/{len(by)} {p:20s} {u:9s} {len(cols):2d} columns, links {sum(r['link'] for r in res[-len(items):])} "
              f"{time.time() - t0:5.1f}s", flush=True)
    f = OUT / f"identity_run_{stamp}.json"
    f.write_text(json.dumps({"model": v1.GEMMA, "date": stamp, "prompt": PROMPT, "pairs": res}, indent=1,
                            ensure_ascii=False), encoding="utf-8")
    print(f"-> {f}")
    score(f)


# --- score -----------------------------------------------------------------------------------------------------------

def score(run_file):
    from pathlib import Path
    run_file = Path(run_file)
    R = json.loads(run_file.read_text(encoding="utf-8"))["pairs"]
    stamp = run_file.stem.replace("identity_run_", "")
    by = collections.defaultdict(list)
    for r in R:
        by[r["stratum"]].append(r)
    let = by["letter"]
    links = [r for r in let if r["link"]]
    yes = [r for r in let if r["label"] == "yes"]
    prec = sum(r["label"] == "yes" for r in links) / len(links) if links else 0.0
    rec = sum(r["link"] for r in yes) / len(yes) if yes else 0.0
    val = [k for k in VALIDATED if any(r["link"] and r["label"] == "yes" and (r["paper"], r["column"]) == k for r in let)]
    nl = {s: sum(r["link"] for r in by[s]) for s in ("not-target", "decoy", "sample", "upstream")}
    crit = [("C1 validated failure columns linked >= 5 of 6", len(val) >= 5, f"{len(val)} of 6: {val}"),
            ("C2 letter precision >= 0.85", prec >= 0.85, f"{prec:.2f} ({sum(r['label'] == 'yes' for r in links)}/{len(links)})"),
            ("C3 letter recall >= 0.70", rec >= 0.70, f"{rec:.2f} ({sum(r['link'] for r in yes)}/{len(yes)})"),
            ("C4 not-target links <= 1", nl["not-target"] <= 1, f"{nl['not-target']} of {len(by['not-target'])}"),
            ("C5 decoy links <= 2", nl["decoy"] <= 2, f"{nl['decoy']} of {len(by['decoy'])}"),
            ("C6 sample links <= 2", nl["sample"] <= 2, f"{nl['sample']} of {len(by['sample'])}")]
    L = [f"column-identity route, gemma run {stamp}; {len(R)} pairs in {len({(r['paper'], r['unit']) for r in R})} "
         f"units; criteria fixed before the run", ""]
    for name, ok, detail in crit:
        L.append(f"  {'PASS' if ok else 'FAIL'}  {name}: {detail}")
    L.append(f"  -> the route {'PASSES' if all(c[1] for c in crit) else 'FAILS'} the precommitted criteria")
    L += ["", f"  not answered (no entry for the column): {sum(not r['answered'] for r in R)}; decodes true but evidence "
          f"insufficient (not linked): {sum(r['decodes'] and r['evidence'] == 'insufficient' for r in R)}",
          f"  upstream stratum (not scored): {nl['upstream']} links of {len(by['upstream'])}", "",
          "  evidence types of the links: " + ", ".join(f"{k} {v}" for k, v in collections.Counter(
              r["evidence"] for r in R if r["link"]).most_common()), ""]
    L.append("letter stratum, every pair (label, link, evidence, reason):")
    for r in sorted(let, key=lambda r: (r["label"] != "yes", r["paper"], r["unit"], r["column"])):
        mark = "ok " if (r["label"] == "yes") == r["link"] else "ERR"
        L.append(f"  {mark} {r['label']:3s} {'LINK' if r['link'] else '-   '} {r['paper']} {r['unit']} -> {r['column']}: "
                 f"{r['evidence']}; codes {r['codes']}; {r['reason'][:160]}")
    for s in ("not-target", "decoy", "sample", "upstream"):
        L += ["", f"{s} stratum, links:"]
        L += [f"  {r['paper']} {r['unit']} -> {r['column']}: {r['evidence']}; codes {r['codes']}; {r['reason'][:160]}"
              for r in by[s] if r["link"]] or ["  none"]
    (OUT / f"IDENTITY_REPORT_{stamp}.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    cmd, args = (sys.argv[1], sys.argv[2:]) if len(sys.argv) > 1 else ("pool", [])
    if cmd == "pool":
        pool(args or ls.tuning_papers())
    elif cmd == "gold":
        gold()
    elif cmd == "run":
        run()
    elif cmd == "score":
        score(args[0])
    else:
        sys.exit(f"unknown command {cmd}")
