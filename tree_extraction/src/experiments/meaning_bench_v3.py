"""
meaning_bench_v3.py — the synonym judge with THREE outcomes, everything else frozen.

Meaning v2 (meaning_bench_v2: one question per token) is frozen: its stored token
meanings are read and no meaning question is asked again (a missing label raises).
The eligibility rule, the name sets and the three decoys are v2's. Only the judge
changes:
    same       both name the same measured trait, in different words   -> credit
    different  different traits, or nothing shows they are the same
    value      one is a value, observation or category belonging to a trait,
               not another name for it
v2's two-way answers (yes/no) are kept beside each item for comparison.

    python meaning_bench_v3.py
-> tree_extraction/output/meaning_bench_v3/{judge3.json, rows.json, summary.txt, report.html}
"""

from __future__ import annotations

import collections
import json
import sys

import _paths
import column_role_bench as crb
import header_tree as ht
import header_tree_bench as hb
import meaning as mn
import meaning_bench as mb
import meaning_bench_v2 as mb2
from evaluate import load_xlsx

OUT = _paths.OUTPUT / "meaning_bench_v3"
V2 = _paths.OUTPUT / "meaning_bench_v2"
Q3 = {"same": "same trait: both name the same measured trait, in different words",
      "different": "different traits: they name different traits, or nothing shows they "
                   "are the same",
      "value": "value, not name: one of them is a value, observation or category "
               "belonging to a trait, not another name for the trait"}
EXPECT = {"unrelated": "different", "value": "value", "initials": "different"}


def frozen_meaning(paper, text, name, context=""):
    """Meaning v2 is frozen: read its stored answer; a missing label is an error."""
    key = f"{paper}|{name}|{context}"
    if key not in mb2.TOKENS:
        raise RuntimeError(f"meaning v2 is frozen, but '{key}' is not in its store")
    return mb2.TOKENS[key]


JUDGE3, V2JUDGE = {}, {}
GATE = None     # v4 sets a function (who, context) -> (eligible, reason)


def question(label, said, trait, in_body):
    return (f"A table column is named '{label}'"
            + (f" (the paper defines: {said})" if said else "")
            + (f". The string '{label}' also occurs as a value in the body of the table"
               if in_body else "")
            + f". A trait list names a trait '{trait}'. How are they related?")


def judge3(label, said, trait, in_body):
    key = "|".join((label, said, trait, str(in_body)))
    if key not in JUDGE3:
        state = "Two names for a trait recorded about insects in a scientific study."
        a = mb2.client().ask(lambda size: state, {"q": {
            "type": "choice", "instructions": question(label, said, trait, in_body),
            "criteria": dict(Q3)}}).get("q") or {}
        ch = a.get("choice") or "different"
        JUDGE3[key] = {"answer": ch, "probs": {k: round(float(v or 0), 3) for k, v in
                                               (a.get("probabilities") or {}).items()}}
        print(f"  judge3: '{label}'{' [in body]' if in_body else ''} ~ '{trait}': {ch}", flush=True)
    v2 = V2JUDGE.get(key)
    return {"label": label, "said": said, "trait": trait, "in_body": in_body,
            "question": question(label, said, trait, in_body),
            "answer": JUDGE3[key]["answer"], "probs": JUDGE3[key]["probs"],
            "v2": v2[0] if v2 else None}


def definitions(text, m):
    """The paper's definitions for each token of a label, with the chosen one."""
    out = []
    for tok, term in (m or {}).get("tokens", {}).items():
        cands = mn.token_candidates(text, tok)
        out.append({"token": tok, "chosen": term,
                    "probs": (m.get("probs") or {}).get(tok, {}),
                    "candidates": [{"term": c["term"], "shape": c["shape"], "quote": c["quote"]}
                                   for c in cands]})
    return out


def run():
    global JUDGE3, V2JUDGE
    mb2.TOKENS = json.loads((V2 / "tokens.json").read_text(encoding="utf-8"))
    V2JUDGE = json.loads((V2 / "judge.json").read_text(encoding="utf-8"))
    f = OUT / "judge3.json"
    JUDGE3 = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    pool = sorted({str(r["measurementType"]).strip() for p in hb.default_papers()
                   if (gp := crb.paper_inputs(_paths.PAPERS / p))
                   for r in load_xlsx(gp[1]) if str(r.get("measurementType") or "").strip()})
    rows = []
    for paper in hb.default_papers():
        if paper not in mb.HEADS:
            continue
        if not (mb.scored_columns(paper) + mb.scored_columns(paper, dev=True)):
            continue
        text = mn.paper_text(paper)
        tabs = hb.html_tables(paper)
        gt = hb.GT(load_xlsx(crb.paper_inputs(_paths.PAPERS / paper)[1]))
        cols_all = mb.scored_columns(paper) + mb.scored_columns(paper, dev=True)
        traits = collections.defaultdict(list)
        for k, c, trait, _col, _g in cols_all:
            traits[k].append(trait)
        grids, starts = {}, {}
        for dev in (False, True):
            for k, c, trait, col, gname in mb.scored_columns(paper, dev):
                if k not in grids:
                    grids[k] = ht.grid_from_html(tabs[k])
                    starts[k] = hb.answer_key(grids[k], gt, ht.Symbols.of(grids[k]))[0] or 0
                g, st = grids[k], starts[k]
                body = mb2.body_cells(g, st)
                name = (col or {}).get("name", "")
                groups, details = (col or {}).get("groups", []), (col or {}).get("details", [])
                label = " ".join([*groups, name, *details]).strip()
                m = frozen_meaning(paper, text, name, " / ".join(groups)) if name else None
                dm = {d: frozen_meaning(paper, text, d, f"under '{name}'") for d in details}
                gm = frozen_meaning(paper, text, gname) if gname else None
                expanded = m["expanded"] if m else ""
                said = "; ".join([f"{t} = {v}" for t, v in (m or {}).get("tokens", {}).items() if v]
                                 + [f"{t} = {v}" for x in dm.values()
                                    for t, v in x["tokens"].items() if v])
                gsaid = "; ".join(f"{t} = {v}" for t, v in (gm or {}).get("tokens", {}).items() if v)
                texts = [name, expanded, *groups, *[f"{x} {expanded or name}" for x in groups]]
                r = {"paper": paper, "table": k, "col": c, "dev": dev, "trait": trait,
                     "name": name, "label": label, "expanded": expanded, "said": said,
                     "gemma_name": gname, "gemma_said": gsaid,
                     "unresolved": (m or {}).get("unresolved", [])
                     + [t for x in dm.values() for t in x["unresolved"]],
                     "head": mb._match([name, *groups, *[f"{x} {name}" for x in groups]], trait),
                     "head_meaning": mb._match(texts, trait),
                     "gemma": mb._match([gname], trait),
                     "gemma_meaning": mb._match([gname, (gm or {}).get("expanded", "")], trait),
                     "definitions": definitions(text, m) + [d for x in dm.values()
                                                            for d in definitions(text, x)],
                     "gemma_definitions": definitions(text, gm), "judge": {}, "decoys": []}
                for who, lab, s, mm, ok in (("head", label, said, m, r["head_meaning"]),
                                            ("gemma", gname, gsaid, gm, r["gemma_meaning"])):
                    eligible = bool(lab) and not (mm or {}).get("unresolved") and not any(
                        x["unresolved"] for x in (dm.values() if who == "head" else []))
                    if GATE is not None:                 # v4: who may be judged at all
                        eligible, why = GATE(who, {
                            "paper": paper, "table": k, "label": lab, "name": name,
                            "groups": groups, "details": details, "m": m, "dm": dm, "gm": gm,
                            "gemma_names": list((next((e for e in mb.GEMMA.get(paper, [])
                                                       if e["table"] == k), {}).get("names")
                                                 or {}).values()),
                            "head_labels": [" ".join([*x.get("groups", []), x.get("name", ""),
                                                      *x.get("details", [])]).strip()
                                            for x in next(e for e in mb.HEADS[paper]
                                                          if e["table"] == k)["columns"]],
                            "eligible_v3": eligible})
                        r[f"{who}_gate"] = why
                    r[f"{who}_eligible"] = eligible
                    r[f"{who}_syn"] = ok
                    if ok or not eligible:
                        continue
                    j = judge3(lab, s, trait, lab.lower() in body)
                    r["judge"][who] = j
                    r[f"{who}_syn"] = j["answer"] == "same"
                    others = [t for t in traits[k] if t != trait and not hb.name_matches(t, trait)]
                    if others:
                        r["decoys"].append({"who": who, "kind": "unrelated",
                                            **judge3(lab, s, others[0], lab.lower() in body)})
                    v = mb2.body_value(g, st, c)
                    if v:
                        r["decoys"].append({"who": who, "kind": "value",
                                            **judge3(v, "", trait, True)})
                    si = mb2.same_initials_decoy(lab, trait, pool)
                    if si:
                        r["decoys"].append({"who": who, "kind": "initials",
                                            **judge3(lab, s, si, lab.lower() in body)})
                for d in r["decoys"]:
                    d["expected"] = EXPECT[d["kind"]]
                    d["false_positive"] = d["answer"] == "same"
                r["status"] = status(r)
                rows.append(r)
        OUT.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(JUDGE3, indent=1, ensure_ascii=False), encoding="utf-8")
    (OUT / "rows.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")
    return rows


def status(r):
    if not r["name"]:
        return "no name"
    if r["head"]:
        return "direct match"
    if r["head_meaning"]:
        return "direct match via meaning"
    if not r["head_eligible"]:
        return "unresolved"
    a = r["judge"].get("head", {}).get("answer")
    return {"same": "synonym only", "value": "value, not name"}.get(a, "rejected synonym")


def tallies(sel):
    n = len(sel)
    t = {"n": n,
         "gemma": sum(r["gemma"] for r in sel), "head": sum(r["head"] for r in sel),
         "gemma_meaning": sum(r["gemma_meaning"] for r in sel),
         "head_meaning": sum(r["head_meaning"] for r in sel),
         "gemma_syn3": sum(r["gemma_syn"] for r in sel), "head_syn3": sum(r["head_syn"] for r in sel),
         "gemma_syn2": sum(r["gemma_meaning"] or (r["judge"].get("gemma", {}).get("v2") == "yes")
                           for r in sel),
         "head_syn2": sum(r["head_meaning"] or (r["judge"].get("head", {}).get("v2") == "yes")
                          for r in sel)}
    for who in ("head", "gemma"):
        for kind in ("unrelated", "value", "initials"):
            ds = [d for r in sel for d in r["decoys"] if d["who"] == who and d["kind"] == kind]
            t[f"{who}_{kind}"] = (sum(d["answer"] == "same" for d in ds),
                                  sum(d["v2"] == "yes" for d in ds), len(ds))
    return t


def summary(rows):
    pct = lambda a, b: f"{a}/{b} {a / b:.0%}" if b else "-"
    L = []
    for title, sel in (("held-out tables", [r for r in rows if not r["dev"]]),
                       ("development tables", [r for r in rows if r["dev"]])):
        t = tallies(sel)
        n = t["n"]
        L += [f"{title}: {n} GT-trait columns", "",
              "  direct name match (no judge):",
              f"    {'gemma names':44s}{pct(t['gemma'], n):>12s}",
              f"    {'head reader names':44s}{pct(t['head'], n):>12s}",
              f"    {'gemma + meaning v2':44s}{pct(t['gemma_meaning'], n):>12s}",
              f"    {'head + meaning v2   <- the score':44s}{pct(t['head_meaning'], n):>12s}",
              "", "  with the synonym judge (provisional):",
              f"    {'gemma, 2-way judge (v2)':44s}{pct(t['gemma_syn2'], n):>12s}",
              f"    {'gemma, 3-way judge (v3)':44s}{pct(t['gemma_syn3'], n):>12s}",
              f"    {'head, 2-way judge (v2)':44s}{pct(t['head_syn2'], n):>12s}",
              f"    {'head, 3-way judge (v3)':44s}{pct(t['head_syn3'], n):>12s}",
              "", "  decoys judged 'same trait' (false positives; 3-way / 2-way):"]
        for who in ("head", "gemma"):
            for kind in ("unrelated", "value", "initials"):
                fp3, fp2, m = t[f"{who}_{kind}"]
                L.append(f"    {who:6s} {kind:10s}  3-way {pct(fp3, m):>10s}   2-way {pct(fp2, m):>10s}")
        L += ["", "  credited only by the judge (3-way 'same'):"]
        for r in sel:
            for who in ("head", "gemma"):
                j = r["judge"].get(who)
                if j and j["answer"] == "same":
                    L.append(f"    {who:5s} {r['paper']} t{r['table']}: '{j['label']}' ~ '{r['trait']}'")
        L += ["", "  body values judged 'same trait' (false positives):"]
        for r in sel:
            for d in r["decoys"]:
                if d["kind"] == "value" and d["answer"] == "same":
                    L.append(f"    {d['who']:5s} {r['paper']} t{r['table']}: '{d['label']}' ~ '{d['trait']}'")
        L += ["", "  judge answers that changed from v2 (2-way -> 3-way):"]
        for r in sel:
            for d in [*[{"kind": "main", "who": w, **j} for w, j in r["judge"].items()], *r["decoys"]]:
                if d.get("v2") and (d["v2"] == "yes") != (d["answer"] == "same"):
                    L.append(f"    {d['who']:5s} {d['kind']:9s} {r['paper']} t{r['table']}: "
                             f"'{d['label']}' ~ '{d['trait']}': {d['v2']} -> {d['answer']}")
        L.append("")
    return "\n".join(L)


def main(argv):
    rows = run()
    s = summary(rows)
    (OUT / "summary.txt").write_text(s, encoding="utf-8")
    import meaning_report
    meaning_report.write(rows, {"held-out": tallies([r for r in rows if not r["dev"]]),
                                "development": tallies([r for r in rows if r["dev"]])},
                         OUT / "report.html")
    print(s)
    print(f"-> {OUT / 'report.html'}")


if __name__ == "__main__":
    main(sys.argv[1:])
