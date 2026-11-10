"""
head_more.py — head reader VERSION 2 (head_tree.py defaults) on the papers of the
decoding key that the 30-paper bench does not cover, every table with >= 2 rows and
>= 2 columns (header_tree_bench.collect_head's rule). Saved after every table; a rerun
resumes. Then merged with round2.json into reader2_all.json for the chain.

    python head_more.py            -> experiments/reader2_more.json, reader2_all.json
"""

from __future__ import annotations

import json
import sys
import time

import column_tree as ct
import decoder as v1
import head_tree as hd
import head_tree_exp as he
import header_tree as ht
import header_tree_bench as hb

OUT = he.EXP / "reader2_more.json"
BENCH = he.EXP / "round2.json"
ALL = he.EXP / "reader2_all.json"
SKIPPED = {}                       # paper -> tables too big for the reader (not reached later)


def papers():
    bench = set(json.loads(BENCH.read_text(encoding="utf-8")))
    return sorted(p for p in v1.load_key() if p not in bench)


def main(argv):
    todo = argv or papers()
    done = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    grids = {p: [ht.grid_from_html(h) for h in hb.html_tables(p)] for p in todo}
    total = sum(1 for p in todo for g in grids[p] if g.nrows >= 2 and g.ncols >= 2)
    print(f"{len(todo)} papers, {total} tables", flush=True)
    client = ct.DecisionClient(*hd.MODELS["nimble"][:2])
    n, t0 = 0, time.time()
    for p in todo:
        keyed = hb.keyed_tables(p)
        have = {e["table"] for e in done.get(p, [])}
        done.setdefault(p, [])
        for k, grid in enumerate(grids[p]):
            if grid.nrows < 2 or grid.ncols < 2:
                continue
            n += 1
            if k in have:
                continue
            r = None
            for attempt in range(3):                      # a model reload can time out
                try:
                    r = hd.read_table(grid, client, "B", body=k in keyed)
                    break
                except RuntimeError as err:
                    if "prompt too long" in str(err):      # too big for nimble's context even at
                        print(f"  SKIPPED {p} t{k} ({grid.nrows}x{grid.ncols}): too big for the "
                              f"reader's view", flush=True)  # the smallest view (Chichorro t9, 113 cols)
                        SKIPPED.setdefault(p, []).append(k)
                        break
                    if attempt == 2:
                        raise
                    print(f"  retry {p} t{k}: {err}", flush=True)
                    time.sleep(20)
            if r is None:
                continue
            r.update(paper=p, table=k)
            done[p].append({"table": k, "nrows": grid.nrows, "ncols": grid.ncols,
                            "data_start": r["head_end"], "first": r["start"], "columns": r["columns"],
                            "secs": r["secs"], "calls": r["calls"], "full": r})
            OUT.write_text(json.dumps(done, indent=1, ensure_ascii=False), encoding="utf-8")
            print(f"  [{n}/{total}] {p} t{k}: first {r['start']}, head {r['head_start']}-"
                  f"{r['head_end'] - 1}, {r['calls']} calls, {r['secs']}s", flush=True)
    merged = json.loads(BENCH.read_text(encoding="utf-8"))
    merged.update(done)
    ALL.write_text(json.dumps(merged, indent=1, ensure_ascii=False), encoding="utf-8")
    (he.EXP / "reader2_more_skipped.json").write_text(json.dumps(SKIPPED, indent=1), encoding="utf-8")
    print(f"done: {n} tables, {round((time.time() - t0) / 60)} min; {len(merged)} papers in {ALL.name}; "
          f"skipped as too big: {sum(map(len, SKIPPED.values()))} {SKIPPED}")


if __name__ == "__main__":
    main(sys.argv[1:])
