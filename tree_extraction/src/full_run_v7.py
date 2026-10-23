"""v7 = v6 (structure questions) + the table-kind and column questions (kind_tree.py), from
the person's review of the 'trait columns mis-tagged' papers (output/column_review/).

Builds output/full_run_v7 on top of output/full_run_v6 (tags, meaning, decode, species,
organism, structure copied). Stages, each resumable:
  kind      Q-KIND per table, Q-COL / Q-ROLE per doubtful column            (nimble)
  oracle    writes kind/ from the review's answers instead (the 5 reviewed papers only):
            what the tree would give if nimble answered as the person did — no model
  decode    legends for columns that became trait columns (Melo 'FG')       (nimble)
  meaning   names for columns that became trait columns ('FG' -> ...)       (nimble)
  assemble  v3's assembly with the kind answers applied; '(n=45)' split off organism labels
  score     production scorer on these papers vs v6, the repeatable scorer, as v6
  det       repeatable scorer only (use_llm=False), v6 vs v7

    python full_run_v7.py <stage> dev|held|all|<paper ...>

The five reviewed papers are all in the HELD half: they are development papers now.
"""
import csv
import json
import shutil
import sys
import time

import _paths  # noqa: F401
import full_run as fr
import full_run_v3 as r3
import full_run_v4 as r4
import full_run_v6 as r6
import kind_tree as kt

V6 = r6.OUT
OUT = fr.OUT.parent / "full_run_v7"
REVIEW = fr.OUT.parent / "column_review" / "reviews"
REVIEWED = ["Attiwilli2022", "CortesGomez2023", "Cortés-Goméz2023", "Figueroa2021",
            "Melo2021", "Orlofsk2014"]
SAME_PAPER = {"Cortés-Goméz2023": "CortesGomez2023"}
# answers the person gave in the chat after the review (2026-10-21)
VERDICT_FIX = {("Figueroa2021", 1): "yes"}       # 'not on the GT but should have been extracted'


def setup():
    OUT.mkdir(parents=True, exist_ok=True)
    for d in ("tags", "meaning", "decode", "species", "organism", "structure"):
        if not (OUT / d).exists() and (V6 / d).exists():
            shutil.copytree(V6 / d, OUT / d)


def structure_of(paper):
    f = OUT / "structure" / f"{paper}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def install(apply=True):
    r6.OUT = OUT                       # v6's structure answers, read from the v7 copy
    r6.install()
    if not apply:
        return
    plan, species_of = fr.plan, fr.species_of
    cache = {}

    def plan_with_kind(paper, head):
        if paper not in cache:
            f = OUT / "kind" / f"{paper}.json"
            cache[paper] = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
        out = []
        for t, fields, org, x in plan(paper, head):
            res = cache[paper].get(str(t.table_index))
            t.kind_organism = kt.organism_column(res)
            out.append((t, kt.apply(fields, res), org, x))
        return out

    def species_or_kind(t, fields, org, rec):
        col = getattr(t, "kind_organism", None)
        if col:
            return fr._clean(rec.get(col))
        return species_of(t, fields, org, rec)

    fr.plan, fr.species_of = plan_with_kind, species_or_kind


def stage_kind(papers):
    setup()
    install(apply=False)
    kt.run(OUT, papers, r6.has_species, structure_of)


def stage_oracle(papers):
    """kind/<paper>.json from the review: a table marked 'no' (or noted 'do not extract')
    gives no rows; a column's corrected tag replaces the tree's."""
    setup()
    (OUT / "kind").mkdir(parents=True, exist_ok=True)
    for p in papers:
        if p not in REVIEWED:
            continue
        src = SAME_PAPER.get(p, p)
        orgs = kt.organism_decisions(OUT, p)
        res = {}
        for f in sorted(REVIEW.glob(f"{src}__t*.json")):
            d = json.loads(f.read_text(encoding="utf-8"))
            d = d.get("data", d)
            t = int(d["table"])
            verdict = VERDICT_FIX.get((src, t), d.get("verdict") or "")
            if verdict == "no" or (verdict in ("", "unsure") and "do not extract" in (d.get("note") or "").lower()):
                res[str(t)] = {"action": "no rows", "kind": {"choice": "review", "probs": {}}, "cols": {}}
                continue
            cols = {c["header"]: {"q": "oracle", "tag": c["tag"]}
                    for c in (d.get("cols") or {}).values() if c.get("tag")}
            res[str(t)] = {"action": "keep", "kind": {"choice": "review", "probs": {}}, "cols": cols}
            gcol = kt.groups_column(orgs.get(str(t)))
            kept = {c["header"] for c in (d.get("cols") or {}).values()
                    if (c.get("tag") or c.get("tree")) == "verbatimIdentification"}
            if gcol and (gcol in kept or not any(c["header"] == gcol for c in (d.get("cols") or {}).values())):
                res[str(t)]["organism"] = gcol
        (OUT / "kind" / f"{p}.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  [oracle] {p:22s} {sum(r['action'] == 'no rows' for r in res.values())} tables no rows, "
              f"{sum(len(r['cols']) for r in res.values())} column tags", flush=True)


def stage_decode(papers):
    """Legends for trait columns the v6 decode never saw (a column that became a trait)."""
    import column_tree as ct
    import decode_inv as di
    import decode_units as du
    import decoder as v1
    setup()
    install()
    head = fr.head_runs()
    client = None
    for p in papers:
        f = OUT / "decode" / f"{p}.json"
        dec = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
        todo = [c for t, fields, _o, _x in fr.plan(p, head) for c in fr.trait_columns(t, fields)
                if f"{c[0]}:{c[1]}" not in dec]
        cats = di.inventory(p) if todo else None
        if not todo or not cats:
            continue
        client = client or ct.DecisionClient(v1.NIMBLE, 1)
        units, t0 = du.unit_texts(p), time.time()
        for k, c, header, values in todo:
            dec[f"{k}:{c}"] = r3._retry(lambda: fr.decode_column(client, p, header, values, cats, units))
        f.write_text(json.dumps(dec, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  [decode v7] {p:22s} {len(todo)} new trait columns ({time.time() - t0:.0f}s)", flush=True)
    if client:
        v1.unload(v1.NIMBLE)


def stage_meaning(papers):
    """Names for trait columns the v6 meaning step never saw ('FG' -> 'Functional Groups')."""
    import column_tree as ct
    import decoder as v1
    import meaning
    setup()
    install()
    head = fr.head_runs()
    client = None
    for p in papers:
        f = OUT / "meaning" / f"{p}.json"
        names = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
        todo = list(dict.fromkeys(c.name for t, fields, _o, _x in fr.plan(p, head) for c in t.columns
                                  if fields.get(c.name) == "measurementType" and c.name not in names))
        if not todo:
            continue
        client = client or ct.DecisionClient(v1.NIMBLE, 1)
        text, cache = meaning.paper_text(p), {}
        for h in todo:
            try:
                names[h] = meaning.read_label(client, text, h, cache=cache).get("expanded") or h
            except RuntimeError:
                names[h] = h
        f.write_text(json.dumps(names, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  [meaning v7] {p:22s} {len(todo)} new names", flush=True)
    if client:
        v1.unload(v1.NIMBLE)


def stage_assemble(papers):
    setup()
    install()
    r3.OUT, r3.BASE = OUT, V6
    r3.stage_assemble(papers)
    n = 0
    for p in papers:
        f = OUT / p / f"{p}.csv"
        if not f.exists():
            continue
        with open(f, encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        k = kt.split_n(rows)
        if k:
            n += k
            with open(f, "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=fr.CSV_FIELDS, extrasaction="ignore")
                w.writeheader()
                w.writerows(rows)
    print(f"sample sizes split off organism labels: {n} rows")


def det_compare(papers):
    r6.V4, r6.OUT = V6, OUT
    r6.det_compare(papers)
    src, dst = OUT / "COMPARE_V6_repeatable.txt", OUT / "COMPARE_V7_repeatable.txt"
    if src.exists():
        dst.write_text(src.read_text(encoding="utf-8").replace("v4", "v6").replace("-> v6 ", "-> v7 "),
                       encoding="utf-8")
        src.unlink()


def stage_score(papers):
    r3.OUT, r3.BASE = OUT, V6
    r3.stage_score(papers)
    r4.OUT, r4.V3 = OUT, V6
    r4.rebuild_summary()
    r4.compare(papers)
    shutil.move(OUT / "COMPARE_V4.txt", OUT / "COMPARE_V7_production.txt")
    det_compare(papers)


def main(argv):
    stage, papers = argv[0], r4.papers_of(argv[1:])
    {"kind": stage_kind, "oracle": stage_oracle, "decode": stage_decode, "meaning": stage_meaning,
     "assemble": stage_assemble, "score": stage_score, "det": det_compare}[stage](papers)


if __name__ == "__main__":
    main(sys.argv[1:])
