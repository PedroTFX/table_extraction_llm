"""Full run with decoder v3 (decoder_v3.py), on top of the full run's saved results.

Reads output/full_run (tags, meaning, decode) and writes output/full_run_v3, so the
baseline stays as it was. Re-asks nimble only what v3 changes; every other column keeps
the full run's answers (the cells that are right must not move).

stages (each resumes):
  decode    per trait column, re-ask only the cells v3 changes (past the 25th, printed
            whole as a code, legend from the footnote below their own table — asked with
            that layout fact); every other cell keeps the full run's record
  endings   per trait column and ending shape: nimble says mark or part of the value
  species   tables with no species column: which organism (species_tree.py: gemma reads
            the paper section by section, nimble decides per table)
  assemble  full_run's assembly on full_run_v3 (a cell with no decoded term takes its
            value without the ending nimble called a mark)
  score     evaluate_all on full_run_v3, re-evaluating only papers whose CSV changed
            (miss-severity grading off, as in the full run); then COMPARE_V3.txt
"""
import csv
import filecmp
import json
import shutil
import sys
import time

import _paths  # noqa: F401
import column_tree as ct
import decode_inv as di
import decode_units as du
import decoder as v1
import decoder_v2 as v2
import decoder_v3 as v3
import full_run as fr

BASE = fr.OUT
OUT = BASE.parent / "full_run_v3"


def columns(paper, head):
    """(table, col index, header, all distinct values) for every trait column — the values
    normalised as full_run.trait_columns does, so the first 25 are the ones it sent."""
    out = []
    for t, fields, _o, _x in fr.plan(paper, head):
        for col in t.columns:
            if fields.get(col.name) not in fr.TRAITS:
                continue
            vals = []
            for rec in t.records:
                v = " ".join(str(rec.get(col.name, "") or "").split())
                if v and v not in vals:
                    vals.append(v)
            if vals:
                out.append((t.table_index, col.index, col.name, vals))
    return out


def setup():
    OUT.mkdir(parents=True, exist_ok=True)
    for d in ("tags", "meaning"):
        if not (OUT / d).exists() and (BASE / d).exists():
            shutil.copytree(BASE / d, OUT / d)
    (OUT / "decode").mkdir(exist_ok=True)


def _retry(fn):
    for attempt in range(3):
        try:
            return fn()
        except RuntimeError as err:
            if attempt == 2 or "llama-server" not in str(err):
                raise
            time.sleep(30)


def footnotes(paper, head, units):
    """{table index: ids of inventory units printed directly below that table} (layout)."""
    flat, spans = v3.md_tables(paper)
    out = {}
    for t, _f, _o, _x in fr.plan(paper, head):
        i = v3.locate_table(t, spans)
        if i is not None:
            feet = v3.footnote_units(flat, spans[i], units)
            if feet:
                out[t.table_index] = feet
    return out


def stage_decode(papers):
    """Per trait column, re-ask only: cells past the 25th, cells the paper prints whole as a
    code, and cells whose legend entries come from the footnote below their own table
    (asked with that fact). Everything else keeps the full run's record."""
    setup()
    head = fr.head_runs()
    client = ct.DecisionClient(v1.NIMBLE, 1)
    for paper in papers:
        f = OUT / "decode" / f"{paper}.json"
        if f.exists() or paper not in head:
            continue
        pf = BASE / "decode" / f"{paper}.json"
        prev = json.loads(pf.read_text(encoding="utf-8")) if pf.exists() else {}
        res = dict(prev)
        cats = di.inventory(paper)
        t0, n_cols, n_foot = time.time(), 0, 0
        if cats:
            units = du.unit_texts(paper)
            feet_of = footnotes(paper, head, units)
            for k, c, header, values in columns(paper, head):
                key = f"{k}:{c}"
                rec = prev.get(key)
                if rec is None and len(values) <= 25:
                    continue
                if rec is None:
                    rec = _retry(lambda: fr.decode_column(client, paper, header, values[:25], cats, units))
                allowed = _allowed(cats, rec)
                feet = feet_of.get(k, set())
                noted, nf = v3.with_footnote(allowed, feet)
                foot = [v for v in values if nf and any(
                    e.get("unit") in feet for p in v1.list_parts(v) for e in v2.candidates(allowed, p, header)[1])]
                split = [v for v, cv in (rec.get("cells") or {}).items()
                         if len(cv.get("parts") or []) > 1
                         and v2.candidates(allowed, v, header)[0] == "explicit"]
                ask = list(dict.fromkeys(values[25:] + split + foot))
                if not ask:
                    continue
                rec = dict(rec, cells=dict(rec.get("cells") or {}))
                more = _retry(lambda: v2.match_column(client, header, ask, noted, shown_values=values[:25]))
                rec["cells"].update(more["cells"])
                rec["v3"] = (f"cells past 25: {len(values[25:])}, printed whole: {len(split)}, "
                             f"table footnote: {len(foot)}")
                res[key] = rec
                n_cols += 1
                n_foot += len(foot)
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  [decode v3] {paper:22s} re-asked cells in {n_cols} cols, of them {n_foot} "
              f"from the table's footnote ({time.time() - t0:.0f}s)", flush=True)
    v1.unload(v1.NIMBLE)


def _allowed(cats, rec):
    """The entries the column's passage choice allowed (the saved choice, not re-asked)."""
    chosen = ((rec or {}).get("units") or {}).get("chosen")
    return [e for e in cats if e.get("unit") in chosen] if chosen else cats


def stage_endings(papers):
    setup()
    head = fr.head_runs()
    client = ct.DecisionClient(v1.NIMBLE, 1)
    for paper in papers:
        f = OUT / "decode" / f"{paper}.json"
        if paper not in head or not f.exists():
            continue
        res = json.loads(f.read_text(encoding="utf-8"))
        if res.get("_endings_done"):
            continue
        n = 0
        for k, c, header, values in columns(paper, head):
            found = v3.endings(values)
            for shape, cells in found.items():
                if len(cells) < 2 and shape == "letters":
                    continue                       # one cell is not a column's habit
                ch, probs = _retry(lambda: v3.ask_ending(client, header, values, shape, cells, paper))
                rec = res.setdefault(f"{k}:{c}", {"cells": {}})
                rec.setdefault("endings", {})[shape] = {"choice": ch, "probs": probs,
                                                        "cells": {v: val for v, (val, _e) in cells.items()}}
                n += 1
        res["_endings_done"] = True
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        if n:
            print(f"  [endings] {paper:22s} {n} questions", flush=True)
    v1.unload(v1.NIMBLE)


SPLIT = ""      # between the decoded parts of a list cell; stage_assemble makes one row each


def _decoded(dec, k, c, cell):
    r = dec.get(f"{k}:{c}") or {}
    rc = (r.get("cells") or {}).get(cell) or {}
    term = rc.get("term")
    if term:
        parts = rc.get("parts") or []
        pieces = term.split("; ")
        if len(parts) > 1 and len(pieces) == len(parts):
            return SPLIT.join(pieces)                    # each part was decoded on its own
        return term
    for e in (r.get("endings") or {}).values():
        if e.get("choice") == "mark" and cell in e["cells"]:
            return e["cells"][cell]
    return cell


def stage_species(papers):
    import species_tree as sp
    setup()
    sp.run(papers, OUT / "species")


def stage_assemble(papers):
    import species_tree as sp
    setup()
    fr.OUT = OUT
    fr._decoded = _decoded
    plan, species_of = fr.plan, fr.species_of

    def plan_with_species(paper, head):                # the table's species, if nimble named one
        named = sp.species_of_tables(OUT / "species", paper)
        out = plan(paper, head)
        for t, _f, _o, _x in out:
            t.paper_species = named.get(t.table_index, "")
        return out

    def species_or_table(t, fields, org, rec):
        return species_of(t, fields, org, rec) or getattr(t, "paper_species", "")

    fr.plan, fr.species_of = plan_with_species, species_or_table
    fr.stage_assemble(papers)
    fr.plan, fr.species_of = plan, species_of
    n = 0
    for p in papers:                     # one row per decoded part of a list cell ('M, SDW, LDW')
        f = OUT / p / f"{p}.csv"
        if not f.exists():
            continue
        with open(f, encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        if not any(SPLIT in (r.get("measurementValue") or "") for r in rows):
            continue
        out = []
        for r in rows:
            for piece in (r.get("measurementValue") or "").split(SPLIT):
                out.append(dict(r, measurementValue=piece))
        n += len(out) - len(rows)
        with open(f, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fr.CSV_FIELDS, extrasaction="ignore")
            w.writeheader()
            w.writerows(out)
    print(f"list cells split into parts: {n} extra rows")


def stage_score(papers):
    import evaluate as ev
    ev.ASSESS_MISS_SEVERITY = False
    changed = []
    for p in papers:
        new, old = OUT / p / f"{p}.csv", BASE / p / f"{p}.csv"
        if not new.exists():
            continue
        if old.exists() and filecmp.cmp(new, old, shallow=False):
            for g in (BASE / p).iterdir():          # same CSV: same score, copy the report
                if g.name != f"{p}.csv":
                    shutil.copy(g, OUT / p / g.name)
        else:
            changed.append(p)
            for g in (OUT / p).glob(f"{p}_report.txt"):
                g.unlink()
    shutil.copy(BASE / "summary.csv", OUT / "summary.csv")
    print(f"re-scoring {len(changed)} changed papers: {', '.join(changed)}", flush=True)
    ev.evaluate_all(_paths.PAPERS, OUT, ev.DEFAULT_KEY, False, semantic=True, use_llm=True,
                    skip_existing=True)
    compare(changed)


def compare(changed=None):
    def load(root):
        with open(root / "summary.csv", encoding="utf-8") as fh:
            return {r["paper"]: r for r in csv.DictReader(fh)}
    a, b = load(BASE), load(OUT)
    L = ["decoder v3 vs the full run (both scored by evaluate_all, severity off)", ""]
    fa = [float(a[p]["f1"] or 0) for p in a if a[p]["status"] == "ok"]
    fb = [float(b[p]["f1"] or 0) for p in b if b[p]["status"] == "ok"]
    L.append(f"mean F1: full run {sum(fa) / len(fa):.3f} ({len(fa)} papers)   "
             f"v3 {sum(fb) / len(fb):.3f} ({len(fb)} papers)")
    L.append("")
    L.append(f"{'paper':24s} {'full':>6s} {'v3':>6s} {'diff':>7s}")
    rows = []
    for p in sorted(set(a) & set(b)):
        x, y = float(a[p]["f1"] or 0), float(b[p]["f1"] or 0)
        if abs(x - y) > 0.0005 or (changed and p in changed):
            rows.append((y - x, p, x, y))
    for d, p, x, y in sorted(rows, reverse=True):
        L.append(f"{p:24s} {x:6.3f} {y:6.3f} {d:+7.3f}")
    (OUT / "COMPARE_V3.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


def main(argv):
    stage, papers = argv[0], argv[1:] or fr.gt_papers()
    {"decode": stage_decode, "endings": stage_endings, "species": stage_species, "assemble": stage_assemble,
     "score": stage_score, "compare": lambda _p: compare()}[stage](papers)


if __name__ == "__main__":
    main(sys.argv[1:])
