"""
column_tree_bench.py — TEST: does walking the decision tree in column_tree.py let
tev1 / nimble tag each column the way the ground truth has it?

Same parsed tables and answer key as column_role_bench.py (labels derived
from the GT xlsx; Family/Order/Tribe columns count as identity), extended with
the template tags the pipeline's mapper cannot output yet (event date,
coordinates, sample size, unit, remarks, treatment, protocol, references,
occurrences, links): scored separately, since the baselines cannot answer them. The
baselines (gemma's mapper, and tev1/nimble asked ONE flat question) are reused
from output/column_role_bench/results.json when that run covered the table,
and computed here otherwise (or when they ended in a server error).

Tree variants (default: tree_tev1, tree_nimble):
  tree_tev1        tev1 walks the tree, with the table-level answers as context
  tree_tev1_noctx  same without the table level (it scored 34% vs 95%; opt-in)
  tree_nimble      nimble walks the tree, with the table-level context

    python column_tree_bench.py                    # papers column_role_bench covered
    python column_tree_bench.py --all              # every paper with _full.md + GT
    python column_tree_bench.py Korosi2022 Rebrina2022
    python column_tree_bench.py --variants tree_tev1 --no-baselines
    python column_tree_bench.py --new 20 --baselines gemma,tev1 --out new20
        # 20 papers the tree was NOT tuned on (sampled, seed 1), written to
        # output/column_tree_bench/new20/
    ... --resume --minutes 25
        # keep the papers already in results.json (and those already found
        # unusable), and stop starting new papers after 25 minutes: background
        # runs are cut at 30, so a long test is done as several resumed runs

Writes tree_extraction/output/column_tree_bench/{results.json, report.txt, tree.txt}.
"""

from __future__ import annotations

import collections
import importlib
import json
import sys
import time
from pathlib import Path

import _paths
import column_role_bench as crb
import column_tree as ct
from evaluate import load_xlsx

OUT = _paths.OUTPUT / "column_tree_bench"
ROLE_RESULTS = crb.OUT / "results.json"
NINE = {"verbatimIdentification", "measurementType", "measurementValue", *crb.ROW_FIELDS}
DEFAULT_VARIANTS = ["tree5_tev1", "tree5_q4"]
# The 10 papers the tree was tuned on (column_role_bench's first run). --new
# samples only outside them, so its score is a held-out score.
TUNING = ["OsorioCanadas2018", "Dejean2019", "Attiwilli2022", "Oliveira2022",
          "Korosi2022", "Habustova2017", "Derhe2016", "Wiescher2012", "Rebrina2022",
          "Figueroa2021"]
MAX_TABLE_COLS = 60     # wider tables are skipped: the flat baselines ask every column
BASELINES = list(crb.ALL_MODELS)             # gemma, tev1, nimble, nimble_full
VARIANTS = {                                  # name -> (model, questions per call, table level)
    "tree_tev1": ("tev1:4b", 1, True),
    "tree_tev1_noctx": ("tev1:4b", 1, False),
    "tree_nimble": ("nimble:latest", 6, True),
    # same tree as the scored tree_nimble (frozen before fixes A-C), Q4 weights,
    # all layers on the GPU (num_gpu 99), 8k and 4k context
    "tree_nimble_q4": ("nimble:9b-q4-gpu", 6, True, "column_tree_v3"),
    "tree_nimble_q4_4k": ("nimble:9b-q4-4k", 6, True, "column_tree_v3"),
    # the CURRENT tree (column_tree.py): fixes A-C, taxon-only organism candidates,
    # statistic-only headers -> measurementValue + their statistic
    "tree5_tev1": ("tev1:4b", 1, True),
    "tree5_q4": ("nimble:9b-q4-gpu", 6, True),
}


def _tid(t):
    return f"{t.source}#{t.table_index}"


def run_baseline(model, table, paper_text):
    if model == "gemma":
        return crb.ask_gemma(table, paper_text)
    return crb.ask_decision(model, table, paper_text)


def bench_paper(paper, variants, old_entries, baselines=BASELINES):
    full_md, gt_path = crb.paper_inputs(crb.PAPERS / paper)
    gt = crb.GroundTruth(load_xlsx(gt_path))
    paper_text = full_md.read_text(encoding="utf-8", errors="replace")
    tables = crb.load_tables(paper, full_md)
    old = {e["table"]: e for e in old_entries}
    out, seen = [], set()
    for t in tables:
        sig = tuple(t.header_names)
        if sig in seen:                        # page fragments share one mapping
            continue
        seen.add(sig)
        if len(sig) > MAX_TABLE_COLS:
            print(f"  {_tid(t)}: {len(sig)} columns, skipped (wider than {MAX_TABLE_COLS})")
            continue
        labels = crb.derive_labels(t, gt, extra=True)
        if not any(l not in ("none", "unsure") for l, _ in labels.values()):
            continue                           # a table the GT never draws on
        tid = _tid(t)
        entry = {"table": tid, "headers": t.header_names, "labels": labels,
                 "pred": {}, "secs": {}, "tree": {}}
        prev = old.get(tid, {})
        for m in baselines:
            p = (prev.get("pred") or {}).get(m)
            if p and not any(v[0] == "error" for v in p.values()):
                entry["pred"][m] = p
                entry["secs"][m] = (prev.get("secs") or {}).get(m, 0)
            else:
                t0 = time.time()
                try:
                    entry["pred"][m] = run_baseline(m, t, paper_text)
                except Exception as e:
                    print(f"    {m} failed on {tid}: {type(e).__name__}: {e}")
                    entry["pred"][m] = {h: ("error", None) for h in t.header_names}
                entry["secs"][m] = round(time.time() - t0, 1)
        for v in variants:
            model, chunk, ctx, *mod = VARIANTS[v]
            tree = importlib.import_module(mod[0]) if mod else ct
            client = tree.DecisionClient(model, chunk)
            t0 = time.time()
            try:
                r = tree.classify_table(t, paper_text, client, table_context=ctx, seed=tid)
            except Exception as e:
                print(f"    {v} failed on {tid}: {type(e).__name__}: {e}")
                r = {"greedy": {h: ("error", None) for h in t.header_names},
                     "soft": {}, "paths": {}, "table_kind": None,
                     "organism_column": None, "skipped": []}
            entry["pred"][v] = r["greedy"]
            entry["secs"][v] = round(time.time() - t0, 1)
            entry["tree"][v] = {k: r.get(k) for k in ("soft", "paths", "table_kind",
                                                      "organism_column", "skipped", "tags")}
            entry["tree"][v]["calls"] = client.calls
        out.append(entry)
        print(f"  {tid}: {len(t.header_names)} cols, "
              + ", ".join(f"{m} {entry['secs'][m]}s" for m in variants))
    return out


# --- scoring ------------------------------------------------------------------------

def _gold(e, h):
    return e["labels"].get(h, ("none", ""))[0]


def _guess(e, m, h):
    p = e["pred"].get(m, {}).get(h)
    return p[0] if p else None


def _scored(results, models):
    """(paper, entry, header) every model answered (sampled-out columns excluded)."""
    out = []
    for paper, entries in results.items():
        for e in entries:
            for h in e["headers"]:
                if _gold(e, h) == "unsure":
                    continue
                if all(_guess(e, m, h) is not None for m in models):
                    out.append((paper, e, h))
    return out


def _cell(ok, n):
    return f"{ok}/{n} {ok / n:.0%}" if n else "-"


def first_wrong_turn(path: str, gold: str) -> str:
    """The first step of a greedy path after which `gold` was out of reach."""
    if not path:
        return "no answer"
    for step in path.split(" > "):
        node, _, rest = step.partition(":")
        opt = rest.split("(")[0]
        if node == "table":
            return "table level: organism column"
        if node == "code":
            continue
        if node not in ct.NODES:
            return step
        if opt.startswith("by table kind"):
            if ct.NODES[node]["otherwise"] != gold:
                return f"{node}: {opt}"
            continue
        if opt in ct.NODES[node]["options"] and gold not in ct.option_fields(node, opt):
            return f"{node}:{opt}"
    return "last step"


def report(results, models, variants):
    cols = _scored(results, models)
    used = [c for c in cols if _gold(c[1], c[2]) != "none"]
    L = [f"{len(results)} papers, {sum(len(v) for v in results.values())} tables, "
         f"{len(cols)} scored columns ({len(used)} used by the GT)", ""]
    W = max(15, max(len(m) for m in models) + 2)   # columns as wide as the longest name
    L.append(f"{'accuracy':30s}" + "".join(f"{m:>{W}s}" for m in models))

    def row(name, pick, lenient=False):
        s = f"{name:30s}"
        for m in models:
            ok = n = 0
            for p, e, h in cols:
                g = _gold(e, h)
                if not pick(g):
                    continue
                q = _guess(e, m, h)
                ok += q == g or (lenient and {q, g} <= {"measurementType", "measurementValue"})
                n += 1
            s += f"{_cell(ok, n):>{W}s}"
        L.append(s)

    row("GT-used columns, 9 mapper fields", lambda g: g in NINE)
    row("  identifier", lambda g: g == "verbatimIdentification")
    row("  trait (type/value)", lambda g: g in ("measurementType", "measurementValue"))
    row("  row fields", lambda g: g in crb.ROW_FIELDS)
    row("  (type~value counted equal)", lambda g: g in NINE, lenient=True)
    row("GT-used, new tags (tree only)", lambda g: g not in NINE and g != "none")
    row("GT-unused columns (weak key)", lambda g: g == "none")
    row("all columns", lambda g: True)
    s = f"{'tables, identifier exact':30s}"
    for m in models:
        ok = n = 0
        for entries in results.values():
            for e in entries:
                hs = [h for h in e["headers"] if _guess(e, m, h) is not None]
                gold = {h for h in hs if _gold(e, h) == "verbatimIdentification"}
                if gold:
                    ok += gold == {h for h in hs if _guess(e, m, h) == "verbatimIdentification"}
                    n += 1
        s += f"{_cell(ok, n):>{W}s}"
    L.append(s)
    L.append(f"{'seconds':30s}" + "".join(
        f"{sum(e['secs'].get(m, 0) for v in results.values() for e in v):>{W}.0f}"
        for m in models))

    # --- tree diagnostics
    for v in variants:
        if v not in models:
            continue
        L += ["", f"TREE {v}"]
        ok = n = 0
        for p, e, h in used:
            sp = e["tree"][v]["soft"].get(h) or e["pred"][v][h]
            ok += sp[0] == _gold(e, h)
            n += 1
        L.append(f"  soft answer (most path probability), GT-used: {_cell(ok, n)}")
        calls = sum(e["tree"][v].get("calls", 0) for es in results.values() for e in es)
        L.append(f"  decision calls: {calls}")
        # table level
        kinds = collections.Counter()
        o_ok = o_n = 0
        for es in results.values():
            for e in es:
                tk = e["tree"][v].get("table_kind")
                if tk:
                    kinds[tk[0]] += 1
                oc = e["tree"][v].get("organism_column")
                if oc is None:
                    continue
                species_cols = {h for h in e["headers"]
                                if e["labels"].get(h, ("", ""))[0] == "verbatimIdentification"
                                and "GT species" in e["labels"][h][1]}
                o_n += 1
                o_ok += (oc[0] in species_cols) if species_cols else oc[0] is None
        if o_n:
            L.append(f"  organism column picked right: {_cell(o_ok, o_n)}")
            L.append("  table kinds chosen: " + ", ".join(f"{k} x{c}" for k, c in kinds.most_common()))
        # where each wrong answer left the right path: the first step after which
        # the GT field could no longer be reached
        for title, group in (("GT-used", used),
                             ("GT-unused (weak key)",
                              [c for c in cols if _gold(c[1], c[2]) == "none"])):
            turns = collections.Counter()
            for p, e, h in group:
                g = _gold(e, h)
                if _guess(e, v, h) == g:
                    continue
                turns[(g, first_wrong_turn(e["tree"][v]["paths"].get(h, ""), g))] += 1
            if turns:
                L.append(f"  first wrong turn, {title} columns (GT field <- step):")
                for (g, t), c in turns.most_common(10):
                    L.append(f"    {g:24s} <- {t:45s} x{c}")

    L += ["", "PER PAPER (GT-used columns correct / total)",
          f"{'paper':28s}" + "".join(f"{m:>{W}s}" for m in models)]
    for paper, entries in results.items():
        s = f"{paper:28s}"
        for m in models:
            ok = n = 0
            for e in entries:
                for h in e["headers"]:
                    g = _gold(e, h)
                    if g in ("none", "unsure") or _guess(e, m, h) is None:
                        continue
                    n += 1
                    ok += _guess(e, m, h) == g
            s += f"{f'{ok}/{n}' if n else '-':>{W}s}"
        L.append(s)

    L += ["", "DETAIL: columns where a tree variant disagrees with the GT label "
          "(path = the tree's greedy route)"]
    for paper, e, h in cols:
        g = _gold(e, h)
        if all(_guess(e, v, h) == g for v in variants if v in models):
            continue
        base = ", ".join(f"{m}={_guess(e, m, h)}" for m in models if m not in variants)
        L.append(f"  {paper} {e['table']} '{h[:40]}': GT={g} [{e['labels'][h][1]}]")
        if base:                      # no baselines in a tree-only run
            L.append(f"      {base}")
        for v in variants:
            if v in models:
                L.append(f"      {v}={_guess(e, v, h)}  via {e['tree'][v]['paths'].get(h, '')}")
    return "\n".join(L)


def main(argv):
    variants = (argv[argv.index("--variants") + 1].split(",") if "--variants" in argv
                else list(DEFAULT_VARIANTS))
    baselines = ([] if "--no-baselines" in argv
                 else argv[argv.index("--baselines") + 1].split(",") if "--baselines" in argv
                 else list(BASELINES))
    global OUT
    if "--out" in argv:
        OUT = OUT / argv[argv.index("--out") + 1]
    want = int(argv[argv.index("--new") + 1]) if "--new" in argv else None
    budget = float(argv[argv.index("--minutes") + 1]) * 60 if "--minutes" in argv else None
    skip = {argv[i + 1] for i, a in enumerate(argv)
            if a in ("--variants", "--baselines", "--out", "--new", "--minutes",
                     "--baselines-from")}
    explicit = [a for a in argv if not a.startswith("--") and a not in skip]
    old = (json.loads(ROLE_RESULTS.read_text(encoding="utf-8"))
           if ROLE_RESULTS.exists() else {})
    # baselines this bench already (re)computed win: e.g. nimble on Habustova2017,
    # re-run with the retry after its server crash in column_role_bench.
    # --baselines-from dir1,dir2 adds other bench outputs (to re-run only the
    # trees in a new --out without recomputing gemma/tev1).
    sources = [OUT / "results.json"]
    if "--baselines-from" in argv:
        sources += [_paths.OUTPUT / "column_tree_bench" / d / "results.json"
                    if d else _paths.OUTPUT / "column_tree_bench" / "results.json"
                    for d in argv[argv.index("--baselines-from") + 1].split(",")]
    for prev in sources:
        if not prev.exists():
            continue
        for paper, entries in json.loads(prev.read_text(encoding="utf-8")).items():
            by_t = {e["table"]: e for e in old.get(paper, [])}  # noqa: B020
            for e in entries:
                keep = {m: e["pred"][m] for m in BASELINES if m in e.get("pred", {})}
                if e["table"] in by_t:
                    by_t[e["table"]]["pred"].update(keep)
                else:
                    by_t[e["table"]] = {"table": e["table"], "pred": keep,
                                        "secs": e.get("secs", {})}
            old[paper] = list(by_t.values())
    if explicit:
        papers = explicit
    elif want:
        import random
        papers = sorted(p.name for p in crb.PAPERS.iterdir()
                        if p.is_dir() and p.name not in TUNING and crb.paper_inputs(p))
        random.Random(1).shuffle(papers)
    elif "--all" in argv:
        papers = sorted(p.name for p in crb.PAPERS.iterdir()
                        if p.is_dir() and crb.paper_inputs(p))
    else:
        papers = list(old)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "tree.txt").write_text(ct.render(), encoding="utf-8")
    results, unusable = {}, set()
    unusable_path = OUT / "unusable.json"
    if "--resume" in argv:
        if (OUT / "results.json").exists():
            results = json.loads((OUT / "results.json").read_text(encoding="utf-8"))
        if unusable_path.exists():
            unusable = set(json.loads(unusable_path.read_text(encoding="utf-8")))
    started = time.time()
    finished = True
    for paper in papers:
        if want and len(results) >= want:
            break
        if paper in results or paper in unusable:
            continue
        if budget and time.time() - started > budget:
            finished = False
            print(f"\ntime budget used: stopping before {paper} (resume to continue)")
            break
        print(f"\n=== {paper}")
        try:
            entries = bench_paper(paper, variants, old.get(paper, []), baselines)
        except Exception as e:
            print(f"  skipped: {type(e).__name__}: {e}")
            continue
        if entries:
            results[paper] = entries
            (OUT / "results.json").write_text(
                json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
        else:
            print("  no table the GT draws on — skipped")
            unusable.add(paper)
            unusable_path.write_text(json.dumps(sorted(unusable)), encoding="utf-8")
    models = [m for m in baselines + variants
              if any(m in e["pred"] for es in results.values() for e in es)]
    text = report(results, models, variants)
    (OUT / "report_detail.txt").write_text(text, encoding="utf-8")
    import bench_report
    summary = bench_report.write(OUT, [(OUT.name, results)], models, variants)
    print("\n" + summary)
    print(f"\n{len(results)} usable paper(s) done" + ("" if finished else " - NOT FINISHED, resume"))


if __name__ == "__main__":
    main(sys.argv[1:])
