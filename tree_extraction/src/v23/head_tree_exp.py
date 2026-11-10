"""
head_tree_exp.py — one-switch experiments on the held-out bench, run only where the
switch can fire, each with a control (same tables, switch off), so a difference
between the two is the switch and not the model's run-to-run noise.

Every other table keeps its stored answer from header_tree_bench's head.json; each
run is written as a full copy of it, so header_tree_bench's scoring can read it.

    python head_tree_exp.py cont    # HEAD_CONTINUE on the tables with head rows below non-head rows
    python head_tree_exp.py title   # SPEC_TITLE on the tables with a QSPEC question
    python head_tree_exp.py both    # the two together, on the union
    python head_tree_exp.py step    # experiment 1 kept in both; SPEC_TITLE_STEP off vs on
-> tree_extraction/output/header_tree_bench/experiments/<name>_{on,off}.json
"""

from __future__ import annotations

import json
import sys

import _paths
import column_tree as ct
import header_tree as ht
import header_tree_bench as hb
import head_tree as hd

EXP = _paths.OUTPUT / "header_tree_bench" / "experiments"


def fires(base, which):
    """The tables where the switch can change anything, from the stored run."""
    out = []
    for p, entries in base.items():
        for e in entries:
            f = e["full"]
            late = any(len(x) > 2 and x[2] == "head after the head ended"
                       for x in f["q1"]["rows"].values())
            if (which in ("cont", "both", "step") and late) or \
                    (which in ("title", "both", "step") and f["spec"]):
                out.append((p, e["table"]))
    return out


def run(base, tables, flags, client):
    res = json.loads(json.dumps(base))                   # a full copy, entries replaced
    saved = {name: getattr(hd, name) for name in flags}
    for name, value in flags.items():
        setattr(hd, name, value)
    keyed = {}
    for p, k in tables:
        if p not in keyed:
            keyed[p] = hb.keyed_tables(p)
        grid = ht.grid_from_html(hb.html_tables(p)[k])
        r = hd.read_table(grid, client, "B", body=k in keyed[p])
        r.update(paper=p, table=k)
        i = next(i for i, e in enumerate(res[p]) if e["table"] == k)
        res[p][i] = {"table": k, "nrows": grid.nrows, "ncols": grid.ncols,
                     "data_start": r["head_end"], "first": r["start"], "columns": r["columns"],
                     "secs": r["secs"], "calls": r["calls"], "full": r}
        print(f"  {p} t{k}: first {r['start']}, head {r['head_start']}-{r['head_end'] - 1}, "
              f"{r['calls']} calls", flush=True)
    for name, value in saved.items():
        setattr(hd, name, value)
    return res


def main(argv):
    which = argv[0]
    EXP.mkdir(parents=True, exist_ok=True)
    base = json.loads((hb.OUT / "head.json").read_text(encoding="utf-8"))
    tables = fires(base, which)
    sides = {"cont": ({"HEAD_CONTINUE": False}, {"HEAD_CONTINUE": True}),
             "title": ({"HEAD_CONTINUE": False, "SPEC_TITLE": False},
                       {"HEAD_CONTINUE": False, "SPEC_TITLE": True}),
             "both": ({"HEAD_CONTINUE": False, "SPEC_TITLE": False},
                      {"HEAD_CONTINUE": True, "SPEC_TITLE": True}),
             "step": ({"HEAD_CONTINUE": True, "SPEC_TITLE_STEP": False},
                      {"HEAD_CONTINUE": True, "SPEC_TITLE_STEP": True})}[which]
    client = ct.DecisionClient(*hd.MODELS["nimble"][:2])
    print(f"{which}: {len(tables)} tables")
    for side, fl in zip(("off", "on"), sides):
        print(f"--- switch {side}", flush=True)
        res = run(base, tables, fl, client)
        (EXP / f"{which}_{side}.json").write_text(json.dumps(res, indent=1, ensure_ascii=False),
                                                 encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1:])
