"""v6 = v4 (species-column questions) + the table-structure questions (structure_tree.py,
eval_split/DESIGN_structure.md). v5 (trait-column filter) was not adopted and is not used.

Builds output/full_run_v6 on top of output/full_run_v4 (tags, meaning, decode, species,
organism copied). Stages, each resumable:
  structure  Q-ROW / Q-NAMES / Q-VALUE per candidate table
  assemble   v3's assembly with the structure decisions applied to the tags
  score      production scorer (use_llm=True) on changed papers vs v4, the repeatable
             scorer (use_llm=False) on v4 and v6 alike, and the structure check vs the key

    python full_run_v6.py <stage> dev|held|all|<paper ...>
"""
import collections
import contextlib
import io
import json
import re
import shutil
import sys

import _paths
import full_run as fr
import full_run_v3 as r3
import full_run_v4 as r4
import species_tree as sp
import structure_tree as st

V4 = fr.OUT.parent / "full_run_v4"
OUT = fr.OUT.parent / "full_run_v6"
KEY = fr.OUT.parent / "eval_split" / "structure_key.json"
SPLIT = r4.SPLIT
sys.path.insert(0, str(_paths.REPO / "source"))


def setup():
    OUT.mkdir(parents=True, exist_ok=True)
    for d in ("tags", "meaning", "decode", "species", "organism"):
        if not (OUT / d).exists() and (V4 / d).exists():
            shutil.copytree(V4 / d, OUT / d)


def install(apply=True):
    r4.OUT = OUT
    r4.install()
    plan = fr.plan
    cache = {}

    def plan_with_structure(paper, head):
        out = plan(paper, head)
        if not apply:
            return out
        if paper not in cache:
            f = OUT / "structure" / f"{paper}.json"
            cache[paper] = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
        res = []
        for t, fields, org, x in out:
            for f in st.expand(fields, cache[paper].get(str(t.table_index))):
                res.append((t, f, org, x))
        return res

    fr.plan = plan_with_structure


def has_species(t, fields, org):
    if any(fr.species_of(t, fields, org, r) for r in t.records):
        return True
    return bool(sp.species_of_tables(OUT / "species", getattr(t, "paper", "")).get(t.table_index))


def stage_structure(papers):
    setup()
    install(apply=False)
    st.run(OUT, papers, has_species)


def stage_assemble(papers):
    setup()
    install()
    r3.OUT, r3.BASE = OUT, V4
    r3.stage_assemble(papers)


def stage_score(papers):
    r3.OUT, r3.BASE = OUT, V4
    r3.stage_score(papers)
    r4.OUT, r4.V3 = OUT, V4
    r4.rebuild_summary()
    r4.compare(papers)
    shutil.copy(OUT / "COMPARE_V4.txt", OUT / "COMPARE_V6_production.txt")
    det_compare(papers)
    structure_eval(papers)


# --- the repeatable scorer ------------------------------------------------------------------

def det_score(root, p):
    """evaluate() with the LLM pass off: trait names matched by strings and values only."""
    import evaluate as ev
    from mineru_extract import classify_folder
    pred = root / p / f"{p}.csv"
    if not pred.exists():
        return None
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        _, gt, _ = classify_folder(_paths.PAPERS / p)
        if not gt:
            return None
        ev.evaluate(str(pred), str(gt), ev.DEFAULT_KEY, False, semantic=True, use_llm=False)
    t = buf.getvalue()
    g = lambda lab: int((re.search(lab + r"\s*:\s*(\d+)", t) or [0, 0])[1])
    return {"tp": g(r"matched \(TP\)"), "fn": g(r"missed \(FN\)"), "fp": g(r"spurious, in scope")}


def _f1(d):
    p = d["tp"] / (d["tp"] + d["fp"]) if d["tp"] + d["fp"] else 0.0
    r = d["tp"] / (d["tp"] + d["fn"]) if d["tp"] + d["fn"] else 0.0
    return 2 * p * r / (p + r) if p + r else 0.0


def det_compare(papers):
    rows = []
    for p in papers:
        a, b = det_score(V4, p), det_score(OUT, p)
        if a and b:
            rows.append((p, a, b))
    tot = lambda i: {k: sum(r[i][k] for r in rows) for k in ("tp", "fn", "fp")}
    a, b = tot(1), tot(2)
    L = [f"repeatable scorer (use_llm=False), {len(rows)} papers: micro F1 v4 {_f1(a):.3f} -> "
         f"v6 {_f1(b):.3f}  (TP {a['tp']} -> {b['tp']}, FP {a['fp']} -> {b['fp']}, FN {a['fn']} -> {b['fn']})"]
    fa = [_f1(x) for _p, x, _y in rows]
    fb = [_f1(y) for _p, _x, y in rows]
    L.append(f"mean F1 {sum(fa) / max(1, len(fa)):.3f} -> {sum(fb) / max(1, len(fb)):.3f}; "
             f"improved {sum(y > x + 0.005 for x, y in zip(fa, fb))}, "
             f"regressed {sum(y < x - 0.005 for x, y in zip(fa, fb))}")
    for (p, x, y), u, v in sorted(zip(rows, fa, fb), key=lambda r: r[2] - r[1], reverse=True):
        if abs(v - u) > 0.0005 or x != y:
            L.append(f"  {p:22s} {u:.3f} -> {v:.3f}  TP {x['tp']}->{y['tp']} FP {x['fp']}->{y['fp']}")
    (OUT / "COMPARE_V6_repeatable.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


# --- the structure check against the key ----------------------------------------------------------

def structure_eval(papers):
    key = [r for r in json.loads(KEY.read_text(encoding="utf-8")) if r["paper"] in set(papers)]
    tally = collections.Counter()
    L = []
    for r in key:
        f = OUT / "structure" / f"{r['paper']}.json"
        d = (json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}).get(str(r["table"])) or {}
        act = d.get("action", "v4")
        v6 = {"long": "long", "wide": "wide", "no rows": "no rows"}.get(act, r["v4"])
        if r["gt"] == "GT long":
            ok_v4, ok_v6 = r["v4"] == "long", v6 == "long" and d.get("long", {}).get("type") in (None, r["info"]["names"])
        elif r["gt"] == "GT wide":
            ok_v4, ok_v6 = r["v4"] == "wide", v6 == "wide"
        elif r["v4"] == "long":                       # no GT rows, read long by v4
            ok_v4, ok_v6 = False, v6 != "long"
        else:
            continue                                  # wide tables without GT rows: not scored
        tally[("v4", ok_v4)] += 1
        tally[("v6", ok_v6)] += 1
        if ok_v4 != ok_v6 or not ok_v6:
            L.append(f"  {'fixed ' if ok_v6 else 'BROKEN' if ok_v4 else 'still '} {r['split']:4s} "
                     f"{r['paper']:20s} t{r['table']:<3} {r['gt']:10s} v4 {r['v4']:4s} -> v6 {v6} "
                     f"({act}; row {d.get('row', {}).get('choice')})")
    n = tally[("v4", True)] + tally[("v4", False)]
    head = (f"structure on the keyed tables ({n}): right v4 {tally[('v4', True)]} -> "
            f"v6 {tally[('v6', True)]}")
    (OUT / "structure_eval.txt").write_text(head + "\n\n" + "\n".join(L) + "\n", encoding="utf-8")
    print(head)
    print("\n".join(L))


def main(argv):
    stage, papers = argv[0], r4.papers_of(argv[1:])
    {"structure": stage_structure, "assemble": stage_assemble, "score": stage_score,
     "check": structure_eval, "det": det_compare}[stage](papers)


if __name__ == "__main__":
    main(sys.argv[1:])
