"""Species-column accuracy per table, against the GT names, split dev / held (eval_split).
Separate from row-level P/R/F1. Reads saved files only, no model.

Per table with trait columns and records:
  expected  'species' when the GT's species are printed in it (a cell, a header, the text
            directly above) or the paper's GT has one species; else 'none'
  given     records that get a species (organism column or species step)
  verdict   expected species: right (>= half the given names are GT species) / wrong / missed
            expected none:    right (empty) / names-not-in-GT (reported, not counted wrong:
            the GT need not cover every table)

    python species_col_eval.py baseline        the full run v3 (organism column as tagged)
    python species_col_eval.py run <dir>       a run with organism decisions (organism/*.json)
"""
import collections
import json
import sys

import decoder_v3 as v3
import full_run as fr
import species_missed as sm
import species_tree as sp

HERE = fr.OUT.parent
SPLIT = json.loads((HERE / "eval_split" / "split.json").read_text(encoding="utf-8"))


def species_per_table(paper, head, run_dir, organism=None):
    """[(table, [species per record])] as the assembly would give them."""
    named = sp.species_of_tables(run_dir / "species", paper)
    out = []
    for t, fields, org, _x in fr.plan(paper, head):
        if not t.records or not any(fields.get(c.name) in fr.TRAITS for c in t.columns):
            continue
        if organism is not None:
            names = [organism(paper, t, fields, org, r) for r in t.records]
        else:
            names = [fr.species_of(t, fields, org, r) for r in t.records]
        if not any(names) and named.get(t.table_index):
            names = [named[t.table_index]] * len(t.records)
        out.append((t, names))
    return out


def evaluate(run_dir, organism=None, papers=None):
    head = fr.head_runs()
    rows = []
    for p in papers or fr.gt_papers():
        if p not in head:
            continue
        try:
            full, short = sm.gt_keys(p)
        except Exception:
            continue
        flat, spans = v3.md_tables(p)
        for t, names in species_per_table(p, head, run_dir, organism):
            printed = (any(sm.hit(r.get(c.name), full, short) for r in t.records for c in t.columns)
                       or any(sm.hit(c.name, full, short) for c in t.columns)
                       or sm.hit(sp.caption_above(t, flat, spans).split("##")[-1], full, short))
            given = [n for n in names if n]
            ok = sum(sm.hit(n, full, short) for n in given)
            # GT species in the table: printed there, the paper has one, or the names the
            # pipeline built (genus + species part) are GT species
            expected = "species" if printed or len(full) == 1 or ok else "none"
            if expected == "species":
                v = "missed" if not given else "right" if ok * 2 >= len(given) else "wrong"
            else:
                v = "right (empty)" if not given else "names not in GT"
            rows.append({"paper": p, "table": t.table_index, "split": SPLIT["assign"].get(p),
                         "expected": expected, "given": len(given), "ok": ok, "verdict": v,
                         "first": given[0] if given else ""})
    return rows


def report(rows, title):
    L = [title, ""]
    for s in ("dev", "held", None):
        sel = [r for r in rows if s is None or r["split"] == s]
        c = collections.Counter(r["verdict"] for r in sel)
        exp = [r for r in sel if r["expected"] == "species"]
        right = sum(r["verdict"] == "right" for r in exp)
        L.append(f"{s or 'all':5s} tables {len(sel):4d} | expected species {len(exp):3d}: right {right} "
                 f"({100 * right / max(1, len(exp)):.0f}%), wrong {c['wrong']}, missed {c['missed']} | "
                 f"expected none: right {c['right (empty)']}, names not in GT {c['names not in GT']}")
    L.append("")
    for r in rows:
        if r["verdict"] in ("wrong", "missed"):
            L.append(f"  {r['split']:4s} {r['paper']:20s} t{r['table']:<3d} {r['verdict']:6s} "
                     f"{r['ok']}/{r['given']} GT names, e.g. {r['first'][:40]!r}")
    return "\n".join(L)


def main(argv):
    if argv[0] == "baseline":
        rows = evaluate(HERE / "full_run_v3")
        out = HERE / "eval_split" / "baseline" / "species_columns_eval"
        title = "species columns — baseline (full_run_v3, organism column as tagged)"
    else:
        import organism_tree as ot
        run = HERE / argv[1]
        rows = evaluate(run, organism=ot.organism_fn(run))
        out = run / "species_columns_eval"
        title = f"species columns — {argv[1]} (organism questions)"
    text = report(rows, title)
    out.with_suffix(".txt").write_text(text + "\n", encoding="utf-8")
    out.with_suffix(".json").write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main(sys.argv[1:])
