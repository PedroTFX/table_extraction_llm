"""
meaning_bench_v2.py — version 2 of the meaning test, against version 1 (frozen in
output/meaning_bench/). Changes, one per known failure:

  1. QM2 asks what each TOKEN means ('SD' in 'Mean length (mm) ± SD'), and the
     header is written out with the meanings ('Mean length (mm) ± standard
     deviation'); the original header is kept beside it.
  2. Longer quotes, found even when the paper's punctuation differs ('Weber’s');
     finder results that fail objective parse checks ('HW2-HW1)') are dropped.
  3. The synonym judge (QS2) is asked only when every abbreviation-like token of
     the label has a meaning from the paper — the same rule for gemma's names and
     the head reader's — so the judge cannot earn credit by guessing 'RMS'.
     When the label also occurs as a value in the table's body, the question says
     so, as plain evidence, for every label alike.
  4. Three decoys per judged column, scored apart: an unrelated trait of the same
     table, one of the column's own body values, and a trait (from any paper's GT)
     with the same initials.

    python meaning_bench_v2.py
-> tree_extraction/output/meaning_bench_v2/{tokens.json, judge.json, rows.json, summary.txt}
"""

from __future__ import annotations

import collections
import json
import re
import sys

import _paths
import column_role_bench as crb
import column_tree as ct
import header_tree as ht
import header_tree_bench as hb
import meaning as mn
import meaning_bench as mb
from evaluate import load_xlsx

OUT = _paths.OUTPUT / "meaning_bench_v2"
V1 = _paths.OUTPUT / "meaning_bench" / "rows.json"
MODEL = ("nimble:9b-q4-gpu", 1)
_CLIENT = None


def client():
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = ct.DecisionClient(*MODEL)
    return _CLIENT


def _load(name):
    f = OUT / name
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def _save(name, data):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")


# --- meanings (QM2) ---------------------------------------------------------------

TOKENS = {}


def label_meaning(paper, text, name, context=""):
    key = f"{paper}|{name}|{context}"
    if key not in TOKENS:
        rec = mn.read_label(client(), text, name, context)
        TOKENS[key] = {k: rec[k] for k in ("tokens", "expanded", "unresolved", "probs")} | {
            "candidates": {t: [c["term"] for c in cs] for t, cs in rec["candidates"].items()}}
        print(f"  {paper} '{name}' -> {TOKENS[key]['expanded']}"
              f"{'  unresolved ' + str(TOKENS[key]['unresolved']) if TOKENS[key]['unresolved'] else ''}",
              flush=True)
    return TOKENS[key]


# --- the synonym judge (QS2) ------------------------------------------------------------

JUDGE = {}
QSYN = mb.QSYN


def judge(label, said, trait, in_body):
    key = "|".join((label, said, trait, str(in_body)))
    if key not in JUDGE:
        state = "Two names for a trait recorded about insects in a scientific study."
        ins = (f"A table column is named '{label}'"
               + (f" (the paper defines: {said})" if said else "")
               + (f". The string '{label}' also occurs as a value in the body of the table"
                  if in_body else "")
               + f". A trait list names a trait '{trait}'. Do they name the same trait?")
        a = client().ask(lambda size: state, {"q": {"type": "choice", "instructions": ins,
                                                    "criteria": dict(QSYN)}}).get("q") or {}
        ch = a.get("choice") or "no"
        JUDGE[key] = [ch, round(float((a.get("probabilities") or {}).get(ch, 0)), 3)]
        print(f"  judge: '{label}'{' (' + said + ')' if said else ''}"
              f"{' [in body]' if in_body else ''} ~ '{trait}': {ch}", flush=True)
    return JUDGE[key][0] == "yes"


def initials(label):
    words = re.findall(r"[A-Za-z][A-Za-z0-9]*", re.sub(r"\([^)]*\)", "", label))
    if len(words) == 1 and mn.looks_abbreviated(words[0]):
        return "".join(ch for ch in words[0] if ch.isalpha()).lower()
    return "".join(w[0] for w in words).lower()


def same_initials_decoy(label, trait, pool):
    ini = initials(label)
    if len(ini) < 2:
        return None
    for t in pool:
        if "".join(w[0] for w in re.findall(r"[A-Za-z]+", t)).lower() == ini \
                and not hb.name_matches(t, trait) and not hb.name_matches(t, label):
            return t                    # a WRONG trait: not the GT trait, not the label itself
    return None


def body_cells(grid, start):
    return {" ".join(str(grid.at(r, c).text or "").split()).lower()
            for r in range(start, grid.nrows) for c in range(grid.ncols)
            if grid.at(r, c) and grid.at(r, c).r == r}


def body_value(grid, start, col):
    vals = collections.Counter(" ".join(str(grid.at(r, col).text or "").split())
                               for r in range(start, grid.nrows) if grid.at(r, col))
    for v, _n in vals.most_common():
        if v and sum(ch.isalpha() for ch in v) >= 3 and not re.match(r"^[\d.,±\s()-]+$", v):
            return v
    return None


# --- one run ------------------------------------------------------------------------

def run():
    global TOKENS, JUDGE
    TOKENS, JUDGE = _load("tokens.json"), _load("judge.json")
    pool = sorted({str(r["measurementType"]).strip() for p in hb.default_papers()
                   if (gp := crb.paper_inputs(_paths.PAPERS / p))
                   for r in load_xlsx(gp[1]) if str(r.get("measurementType") or "").strip()})
    rows = []
    for paper in hb.default_papers():
        if paper not in mb.HEADS:
            continue
        cols = mb.scored_columns(paper) + mb.scored_columns(paper, dev=True)
        if not cols:
            continue
        text = mn.paper_text(paper)
        tabs = hb.html_tables(paper)
        gt = hb.GT(load_xlsx(crb.paper_inputs(_paths.PAPERS / paper)[1]))
        traits = collections.defaultdict(list)
        for k, c, trait, col, gname in cols:
            traits[k].append(trait)
        grids, starts = {}, {}
        for dev in (False, True):
            for k, c, trait, col, gname in mb.scored_columns(paper, dev):
                if k not in grids:
                    grids[k] = ht.grid_from_html(tabs[k])
                    starts[k] = hb.answer_key(grids[k], gt, ht.Symbols.of(grids[k]))[0] or 0
                g, st = grids[k], starts[k]
                body = body_cells(g, st)
                name = (col or {}).get("name", "")
                groups, details = (col or {}).get("groups", []), (col or {}).get("details", [])
                label = " ".join([*groups, name, *details]).strip()
                r = {"paper": paper, "table": k, "col": c, "dev": dev, "trait": trait,
                     "name": name, "label": label, "gemma_name": gname}
                # meanings: the name, its details, and gemma's name (same rule for both)
                m = label_meaning(paper, text, name, " / ".join(groups)) if name else None
                dm = {d: label_meaning(paper, text, d, f"under '{name}'") for d in details}
                gm = label_meaning(paper, text, gname) if gname else None
                expanded = m["expanded"] if m else ""
                said = "; ".join([f"{t} = {v}" for t, v in (m or {}).get("tokens", {}).items() if v]
                                 + [f"{t} = {v}" for d, x in dm.items()
                                    for t, v in x["tokens"].items() if v])
                gsaid = "; ".join(f"{t} = {v}" for t, v in (gm or {}).get("tokens", {}).items() if v)
                texts = [name, expanded, *groups, *[f"{x} {expanded or name}" for x in groups]]
                r.update(expanded=expanded, said=said, gemma_said=gsaid,
                         unresolved=(m or {}).get("unresolved", [])
                         + [t for x in dm.values() for t in x["unresolved"]],
                         head=mb._match([name, *groups, *[f"{x} {name}" for x in groups]], trait),
                         head_meaning=mb._match(texts, trait),
                         gemma=mb._match([gname], trait),
                         gemma_meaning=mb._match([gname, (gm or {}).get("expanded", "")], trait))
                # the judge, only when every abbreviation-like token has a paper meaning
                for who, lab, s, mm, ok in (("head", label, said, m, r["head_meaning"]),
                                            ("gemma", gname, gsaid, gm, r["gemma_meaning"])):
                    eligible = bool(lab) and not (mm or {}).get("unresolved") and not any(
                        x["unresolved"] for x in (dm.values() if who == "head" else []))
                    r[f"{who}_eligible"] = eligible
                    r[f"{who}_syn"] = ok or (eligible and judge(lab, s, trait, lab.lower() in body))
                    if ok or not eligible:
                        continue
                    others = [t for t in traits[k] if t != trait and not hb.name_matches(t, trait)]
                    if others:
                        r[f"{who}_decoy_unrelated"] = judge(lab, s, others[0], lab.lower() in body)
                    v = body_value(g, st, c)
                    if v:
                        r[f"{who}_decoy_value"] = judge(v, "", trait, True)
                    si = same_initials_decoy(lab, trait, pool)
                    if si:
                        r[f"{who}_decoy_initials"] = judge(lab, s, si, lab.lower() in body)
                rows.append(r)
        _save("tokens.json", TOKENS)
        _save("judge.json", JUDGE)
    _save("rows.json", rows)
    return rows


def summary(rows):
    v1 = {(r["paper"], r["table"], r["col"]): r for r in json.loads(V1.read_text(encoding="utf-8"))}
    pct = lambda a, b: f"{a}/{b} {a / b:.0%}" if b else "-"
    L = []
    for title, sel in (("held-out tables", [r for r in rows if not r["dev"]]),
                       ("development tables", [r for r in rows if r["dev"]])):
        n = len(sel)
        old = [v1.get((r["paper"], r["table"], r["col"]), {}) for r in sel]
        L += [f"{title}: {n} GT-trait columns", "", "  names, no synonyms:"]
        L.append(f"    {'gemma names':52s}{pct(sum(r['gemma'] for r in sel), n):>12s}")
        L.append(f"    {'head reader names':52s}{pct(sum(r['head'] for r in sel), n):>12s}")
        L.append(f"    {'  + finder first definition (v1, code only)':52s}"
                 f"{pct(sum(bool(o.get('head_finder')) for o in old), n):>12s}")
        L.append(f"    {'  + meaning chosen per name (v1, QM)':52s}"
                 f"{pct(sum(bool(o.get('head_meaning')) for o in old), n):>12s}")
        L.append(f"    {'  + meanings chosen per token (v2, QM2)':52s}"
                 f"{pct(sum(r['head_meaning'] for r in sel), n):>12s}")
        L.append(f"    {'gemma names + meanings per token (v2, QM2)':52s}"
                 f"{pct(sum(r['gemma_meaning'] for r in sel), n):>12s}")
        L += ["", "  with the synonym judge:"]
        L.append(f"    {'v1 judge (unrestricted): gemma':52s}"
                 f"{pct(sum(bool(o.get('gemma_syn')) for o in old), n):>12s}")
        L.append(f"    {'v1 judge (unrestricted): head + meaning':52s}"
                 f"{pct(sum(bool(o.get('head_syn')) for o in old), n):>12s}")
        L.append(f"    {'v2 judge (paper meanings only): gemma':52s}"
                 f"{pct(sum(r['gemma_syn'] for r in sel), n):>12s}")
        L.append(f"    {'v2 judge (paper meanings only): head + meanings':52s}"
                 f"{pct(sum(r['head_syn'] for r in sel), n):>12s}")
        L += ["", "  decoys — judge said 'same trait' (lower is better):"]
        for who in ("head", "gemma"):
            for kind in ("unrelated", "value", "initials"):
                ds = [r[f"{who}_decoy_{kind}"] for r in sel if f"{who}_decoy_{kind}" in r]
                L.append(f"    {who:6s} {kind:10s}{pct(sum(ds), len(ds)):>12s}")
        L += ["", "  the three version-1 failures:"]
        for p, name in (("GibbParr2013", "EP"), ("Ibarra2021", "Mean length (mm) ± SD"), ("Leong2023", "WL")):
            for r in sel:
                if r["paper"] == p and r["name"] == name:
                    L.append(f"    {p} '{name}' -> '{r['expanded']}' (GT '{r['trait']}'): "
                             f"{'match' if r['head_meaning'] else 'no match'}")
                    break
        over = [r for r in sel if r["expanded"] and r["expanded"] != r["name"]
                and not r["head_meaning"]]
        L.append(f"  written out but still not the GT trait: {len(over)}")
        for r in over:
            L.append(f"    {r['paper']} t{r['table']}: '{r['label']}' -> '{r['expanded']}' vs '{r['trait']}'")
        acc = [r for r in sel if r["head_syn"] and not r["head_meaning"]]
        L.append(f"  head credited only by the judge (check by eye): {len(acc)}")
        for r in acc:
            L.append(f"    {r['paper']} t{r['table']}: '{r['label']}'"
                     f"{' (' + r['said'] + ')' if r['said'] else ''} ~ '{r['trait']}'")
        gac = [r for r in sel if r["gemma_syn"] and not r["gemma_meaning"]]
        L.append(f"  gemma credited only by the judge: {len(gac)}")
        for r in gac:
            L.append(f"    {r['paper']} t{r['table']}: '{r['gemma_name']}' ~ '{r['trait']}'")
        miss = [r for r in sel if not r["head_syn"]]
        L.append(f"  head still missed: {len(miss)}")
        for r in miss:
            why = ("no name" if not r["name"] else
                   "not eligible, undefined: " + ", ".join(r["unresolved"])
                   if not r["head_eligible"] else "judge said no")
            L.append(f"    {r['paper']} t{r['table']}: '{r['label']}' vs '{r['trait']}' ({why})")
        L.append("")
    return "\n".join(L)


def main(argv):
    rows = run()
    s = summary(rows)
    (OUT / "summary.txt").write_text(s, encoding="utf-8")
    print(s)


if __name__ == "__main__":
    main(sys.argv[1:])
