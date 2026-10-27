"""
head_round2.py — round 2 of the head reader on EVERY table of the frozen run
(experiments/step_on.json), with the three switches from the person's table-by-table
check turned on: SECTION_CELL, EMPTY_GROUP_RECHECK, SPEC_STATS. Same table format as
the frozen run, so header_review.py builds the next check page from it. Saved after
every table; a rerun resumes.

    python head_round2.py   -> tree_extraction/output/header_tree_bench/experiments/round2.json
"""

from __future__ import annotations

import json
import sys
import time

import column_tree as ct
import head_tree as hd
import head_tree_exp as he
import header_tree as ht
import header_tree_bench as hb

SRC = he.EXP / "step_on.json"
OUT = he.EXP / "round2.json"
FLAGS = {"SECTION_CELL": True, "EMPTY_GROUP_RECHECK": True, "SPEC_STATS": True}


def main(argv):
    global OUT
    if "--out" in argv:                                  # another full run (round 3: QG narrowed)
        i = argv.index("--out")
        OUT = he.EXP / f"{argv[i + 1]}.json"
        argv = argv[:i] + argv[i + 2:]
    base = json.loads(SRC.read_text(encoding="utf-8"))
    done = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    for name, value in FLAGS.items():
        setattr(hd, name, value)
    client = ct.DecisionClient(*hd.MODELS["nimble"][:2])
    papers = argv or sorted(base)
    total = sum(len(base[p]) for p in papers)
    n, t0 = 0, time.time()
    for p in papers:
        keyed = hb.keyed_tables(p)
        html = hb.html_tables(p)
        have = {e["table"] for e in done.get(p, [])}
        for e in sorted(base[p], key=lambda x: x["table"]):
            k = e["table"]
            n += 1
            if k in have:
                continue
            grid = ht.grid_from_html(html[k])
            for attempt in range(3):                      # a model reload can time out
                try:
                    r = hd.read_table(grid, client, "B", body=k in keyed)
                    break
                except RuntimeError as err:
                    if attempt == 2:
                        raise
                    print(f"  retry {p} t{k}: {err}", flush=True)
                    time.sleep(20)
            r.update(paper=p, table=k)
            done.setdefault(p, []).append({"table": k, "nrows": grid.nrows, "ncols": grid.ncols,
                                           "data_start": r["head_end"], "first": r["start"],
                                           "columns": r["columns"], "secs": r["secs"],
                                           "calls": r["calls"], "full": r})
            OUT.write_text(json.dumps(done, indent=1, ensure_ascii=False), encoding="utf-8")
            print(f"  [{n}/{total}] {p} t{k}: first {r['start']}, head {r['head_start']}-"
                  f"{r['head_end'] - 1}, sections {len(r['sections'])}, regrouped {len(r['regrouped'])}, "
                  f"{r['calls']} calls, {r['secs']}s", flush=True)
    print(f"done: {n} tables, {round((time.time() - t0) / 60)} min")


if __name__ == "__main__":
    main(sys.argv[1:])
