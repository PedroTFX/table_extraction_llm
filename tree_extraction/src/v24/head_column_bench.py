"""
head_column_bench.py — TEST the merge: the column tree (column_tree.py, nimble Q4)
reading tables built from the head reader's answers (head_to_table.py) instead of
the tables the pipeline builds from gemma's header finder.

    version 1  (head_v1)  head-reader names and rows in, everything else unchanged
    version 2  (head_v2)  the same, plus context lines the head reader found: the
                          title, section labels, head-row values

The head reader's answers are read from the frozen run (experiments/step_on.json:
header_tree_bench's head.json with experiment 1 and the title check), so no head
question is asked again. The baseline is the stored column-tree run on the
pipeline's tables for the same papers (column_tree_bench/all_v5q4, tree5_q4).
Each version is scored with the same GT-derived key (column_role_bench.derive_labels)
on its own tables; papers are summed, so the two parsings need not agree on tables.

    python head_column_bench.py --variant head_v1 --resume --minutes 100
    python head_column_bench.py --variant head_v2 --resume --minutes 100
    python head_column_bench.py --variant reader2_v2 --resume   # head reader VERSION 2
                                  (experiments/round2.json, 2026-10-13), v2 context
    python head_column_bench.py --summary
-> tree_extraction/output/column_tree_bench/head_merge/{head_v1.json, head_v2.json, summary.txt}
"""

from __future__ import annotations

import collections
import json
import sys
import time

import _paths
import column_role_bench as crb
import column_tree as ct
import column_tree_bench as ctb
import head_to_table as h2t
import header_tree_bench as hb
from evaluate import load_xlsx

OUT = ctb.OUT / "head_merge"
HEAD = hb.OUT / "experiments" / "step_on.json"
HEADS = {"reader2_v2": hb.OUT / "experiments" / "round2.json",   # variant -> head-reader run
         "reader2_all": hb.OUT / "experiments" / "reader2_all.json"}  # + the decoding key's papers
CONTEXT = {"head_v2", "reader2_v2", "reader2_all"}
ALL_PAPERS = {"reader2_all"}       # every paper of its head run, not only the bench's
BASE = ctb.OUT / "all_v5q4" / "results.json"
MODEL = ("nimble:9b-q4-gpu", 6)
NEW20 = None            # the column tree's held-out papers, from column_tree_bench/new20


def run(variant, resume, budget):
    path = OUT / f"{variant}.json"
    results = json.loads(path.read_text(encoding="utf-8")) if resume and path.exists() else {}
    head = json.loads(HEADS.get(variant, HEAD).read_text(encoding="utf-8"))
    if variant == "reader2_all" and (OUT / "reader2_v2.json").exists():
        for p, es in json.loads((OUT / "reader2_v2.json").read_text(encoding="utf-8")).items():
            if p not in results:                         # the bench papers: same input, reused
                results[p] = [{**e, "pred": {variant: e["pred"]["reader2_v2"]}} for e in es]
    client = ct.DecisionClient(*MODEL)
    started = time.time()
    for paper in (sorted(head) if variant in ALL_PAPERS else hb.default_papers()):
        if paper in results:
            continue
        if budget and time.time() - started > budget:
            print(f"time budget used: stopping before {paper} (resume to continue)")
            return False
        inputs = crb.paper_inputs(crb.PAPERS / paper)
        if not inputs or paper not in head:
            continue
        full_md, gt_path = inputs
        gt = crb.GroundTruth(load_xlsx(gt_path))
        paper_text = full_md.read_text(encoding="utf-8", errors="replace")
        print(f"\n=== {paper} [{variant}]", flush=True)
        tables = h2t.build_tables(paper, head[paper], h2t.grids_of(paper),
                                  context=variant in CONTEXT)
        entries, seen = [], set()
        for t, ctx in tables:
            sig = tuple(t.header_names)
            if sig in seen or len(sig) > ctb.MAX_TABLE_COLS:
                continue
            seen.add(sig)
            labels = crb.derive_labels(t, gt, extra=True)
            if not any(l not in ("none", "unsure") for l, _ in labels.values()):
                continue                         # a table the GT never draws on
            tid = f"{paper}#{t.table_index}"
            t0 = time.time()
            calls0 = client.calls
            try:
                r = ct.classify_table(t, paper_text, client, table_context=True, seed=tid,
                                      extra_context=ctx)
            except Exception as e:
                print(f"    failed on {tid}: {type(e).__name__}: {e}")
                r = {"greedy": {h: ("error", None) for h in t.header_names}, "paths": {}}
            entries.append({"table": tid, "headers": t.header_names, "labels": labels,
                            "pred": {variant: r["greedy"]}, "context": ctx,
                            "paths": r.get("paths", {}), "secs": round(time.time() - t0, 1),
                            "calls": client.calls - calls0})
            print(f"  {tid}: {len(t.header_names)} cols, {entries[-1]['secs']}s", flush=True)
        results[paper] = entries
        OUT.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    return True


def _tally(results, model, papers):
    c = collections.Counter()
    for p in papers:
        for e in results.get(p, []):
            c["tables"] += 1
            for h in e["headers"]:
                gold = e["labels"].get(h, ["none"])[0]
                pred = (e["pred"].get(model) or {}).get(h)
                if gold == "unsure" or pred is None:
                    continue
                guess = pred[0]
                if gold in ctb.NINE:
                    c["used_n"] += 1
                    c["used_ok"] += guess == gold
                    c["used_len"] += guess == gold or {guess, gold} == {"measurementType",
                                                                         "measurementValue"}
                elif gold != "none":
                    c["new_n"] += 1
                    c["new_ok"] += guess == gold
                else:
                    c["none_n"] += 1
                    c["none_ok"] += guess == "none"
            c["secs"] += e.get("secs", 0) if isinstance(e.get("secs"), (int, float)) \
                else e.get("secs", {}).get(model, 0)
    return c


def summary():
    base = json.loads(BASE.read_text(encoding="utf-8"))
    runs = [("gemma's tables (pipeline)", base, "tree5_q4")]
    for v, name in (("head_v1", "head reader 1, v1"), ("head_v2", "head reader 1, v2"),
                    ("reader2_v2", "head reader 2, v2")):
        f = OUT / f"{v}.json"
        if f.exists():
            runs.append((name, json.loads(f.read_text(encoding="utf-8")), v))
    new20 = set(json.loads((ctb.OUT / "new20" / "results.json").read_text(encoding="utf-8")))
    done = set.intersection(*[set(r) for _n, r, _m in runs[1:]]) if len(runs) > 1 else set(base)
    papers_all = [p for p in hb.default_papers() if p in base and p in done]
    pct = lambda a, b: f"{a}/{b} {a / b:.0%}" if b else "-"
    L = []
    for title, papers in (("all papers", papers_all),
                          ("the column tree's held-out papers (new20)",
                           [p for p in papers_all if p in new20]),
                          ("the column tree's tuning papers", [p for p in papers_all if p not in new20])):
        L += [f"{title}: {len(papers)} papers", ""]
        W = 30
        L.append(f"{'':38s}" + "".join(f"{n:>{W}s}" for n, _r, _m in runs))
        T = [_tally(r, m, papers) for _n, r, m in runs]
        L.append(f"{'tables the GT draws on':38s}" + "".join(f"{t['tables']:>{W}d}" for t in T))
        L.append(f"{'GT-used columns, 9 mapper fields':38s}"
                 + "".join(f"{pct(t['used_ok'], t['used_n']):>{W}s}" for t in T))
        L.append(f"{'  (type~value counted equal)':38s}"
                 + "".join(f"{pct(t['used_len'], t['used_n']):>{W}s}" for t in T))
        L.append(f"{'GT-used, new tags (tree only)':38s}"
                 + "".join(f"{pct(t['new_ok'], t['new_n']):>{W}s}" for t in T))
        L.append(f"{'GT-unused columns -> none':38s}"
                 + "".join(f"{pct(t['none_ok'], t['none_n']):>{W}s}" for t in T))
        L.append(f"{'column-tree seconds':38s}" + "".join(f"{t['secs']:>{W}.0f}" for t in T))
        L.append("")
    return "\n".join(L)


def main(argv):
    if "--summary" in argv:
        s = summary()
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "summary.txt").write_text(s, encoding="utf-8")
        print(s)
        return
    variant = argv[argv.index("--variant") + 1]
    budget = float(argv[argv.index("--minutes") + 1]) * 60 if "--minutes" in argv else None
    done = run(variant, "--resume" in argv, budget)
    print(f"\n{variant}: " + ("finished" if done else "NOT FINISHED, resume"))


if __name__ == "__main__":
    main(sys.argv[1:])
