"""v4 = v3 + the species-column questions (organism_tree.py, eval_split/DESIGN.md).

Builds output/full_run_v4 on top of output/full_run_v3 (tags, meaning, decode, species
answers copied; v3 stays as it was). Stages, each resumable:
  organism  Q-KIND / Q-PICK / Q-GENUS per table with candidate species columns
  species   species_tree for tables that now have no species column (one paper at a time)
  assemble  v3's assembly, species from the organism decisions (else the species step)
  score     evaluate_all on the papers whose CSV changed, compared with v3; then the
            species-column accuracy (species_col_eval)

    python full_run_v4.py <stage> dev|held|all|<paper ...>
"""
import json
import shutil
import sys

import full_run as fr
import full_run_v3 as r3
import organism_tree as ot
import species_tree as sp

V3 = fr.OUT.parent / "full_run_v3"
OUT = fr.OUT.parent / "full_run_v4"
SPLIT = json.loads((fr.OUT.parent / "eval_split" / "split.json").read_text(encoding="utf-8"))


def papers_of(args):
    if args and args[0] in ("dev", "held"):
        return [p for p, s in SPLIT["assign"].items() if s == args[0]]
    if args and args[0] == "all":
        return list(SPLIT["assign"])
    return args


def setup():
    OUT.mkdir(parents=True, exist_ok=True)
    for d in ("tags", "meaning", "decode", "species"):
        if not (OUT / d).exists() and (V3 / d).exists():
            shutil.copytree(V3 / d, OUT / d)


def install():
    """full_run.plan tags each table with its paper; full_run.species_of follows the
    organism decisions (tables without one keep the tagged column)."""
    plan, species_of = fr.plan, fr.species_of
    decide = ot.organism_fn(OUT)

    def plan_with_paper(paper, head):
        out = plan(paper, head)
        for t, _f, _o, _x in out:
            t.paper = paper
        return out

    def species_by_decision(t, fields, org, rec):
        return decide(getattr(t, "paper", ""), t, fields, org, rec) if hasattr(t, "paper") \
            else species_of(t, fields, org, rec)

    fr.plan, fr.species_of = plan_with_paper, species_by_decision


def stage_organism(papers):
    setup()
    ot.run(OUT, papers)


def stage_species(papers):
    setup()
    install()
    sp.run(papers, OUT / "species")


def stage_assemble(papers):
    setup()
    install()
    r3.OUT, r3.BASE = OUT, V3
    r3.stage_assemble(papers)


def rebuild_summary():
    """summary.csv from each paper's own report (r3.stage_score starts from v3's summary,
    which would carry v3 numbers for papers scored in an earlier v4 run)."""
    import csv
    import evaluate as ev
    rows = []
    for p in sorted(SPLIT["assign"]):
        rep = OUT / p / f"{p}_report.txt"
        m = ev._metrics_from_report(rep) if rep.exists() else None
        rows.append({"paper": p, "precision": m[0] if m else "", "recall": m[1] if m else "",
                     "f1": m[2] if m else "", "status": "ok" if m else "no report"})
    with open(OUT / "summary.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["paper", "precision", "recall", "f1", "status"])
        w.writeheader()
        w.writerows(rows)


def stage_score(papers):
    r3.OUT, r3.BASE = OUT, V3
    r3.stage_score(papers)
    rebuild_summary()
    import species_col_eval as sce
    rows = sce.evaluate(OUT, organism=ot.organism_fn(OUT))
    text = sce.report(rows, "species columns — full_run_v4 (organism questions)")
    (OUT / "species_columns_eval.txt").write_text(text + "\n", encoding="utf-8")
    (OUT / "species_columns_eval.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False),
                                                   encoding="utf-8")
    print(text.split("\n\n")[0])
    compare(papers)


def compare(papers):
    """Per paper F1, v3 vs v4, on these papers only; regressions = F1 drop > 0.005."""
    import csv

    def load(root):
        with open(root / "summary.csv", encoding="utf-8") as fh:
            return {r["paper"]: r for r in csv.DictReader(fh)}
    a, b = load(V3), load(OUT)
    rows = [(p, float(a[p]["f1"] or 0), float(b[p]["f1"] or 0)) for p in papers if p in a and p in b]
    n = max(1, len(rows))
    L = [f"v4 vs v3 on {len(rows)} papers: mean F1 {sum(r[1] for r in rows) / n:.3f} -> "
         f"{sum(r[2] for r in rows) / n:.3f}",
         f"improved {sum(y > x + 0.005 for _p, x, y in rows)}, "
         f"regressed {sum(y < x - 0.005 for _p, x, y in rows)}", ""]
    for p, x, y in sorted(rows, key=lambda r: r[2] - r[1], reverse=True):
        if abs(y - x) > 0.0005:
            L.append(f"  {p:22s} {x:.3f} -> {y:.3f}  {y - x:+.3f}")
    (OUT / "COMPARE_V4.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


def main(argv):
    stage, papers = argv[0], papers_of(argv[1:])
    {"organism": stage_organism, "species": stage_species, "assemble": stage_assemble,
     "score": stage_score}[stage](papers)


if __name__ == "__main__":
    main(sys.argv[1:])
