"""
head_wide.py — tables too wide for the head reader (tree_extraction/plans/07_big_tables.md; revised 2026-11-22).

The head reader has one view that grows with the table's width: the whole-row view (the first rows, every filled
cell with its column), used for the first-record question, the rows above it and QSPEC. Everything else (head
cells, names, body rows) already uses pieces of at most 10 columns. On a wide table the whole-row view is over
nimble's context even at the smallest cell width, so head_more.py skips the table and nothing after it sees it.
2026-11-21, the 109 set: Vidal2023 t6 8,552 tokens, MacDonald2021 t4 9,111, Chichorro2022 t9 10,821 (all 620 GT
rows), Noriega2023 t6 31,764; the context holds 8,448.

  only     tables of a paper the head reader has read that have no entry (>= 2 rows and columns, head_more's
           rule); every entry made before stays as it is (entries are only added)
  reading  the frozen reader, head_tree.read_table, unchanged except for the whole-row view: it shows only the
           first ROW_VIEW_COLS columns and says the rest are left out (head_tree.ROW_VIEW_COLS). The widest view
           that fits is used: the whole table first (read exactly as head_more.py would), then each width of
           ROW_VIEWS in turn. nimble refuses an over-long prompt at once, so a width that does not fit costs
           almost no model time. Body questions as in head_more.py (tables the GT draws on)
  left     a table that does not fit even at the narrowest width is reported (reader2_wide_left.json)

    python head_wide.py [papers]      -> experiments/reader2_wide.json, added to reader2_all.json (and to
                                         reader2_more.json for papers it holds)
The paper then needs its later stages again, in a root of its own: bash ../reread_paper.sh <paper>.
"""
from __future__ import annotations

import json
import sys
import time

import column_tree as ct
import head_more as hm
import head_tree as hd
import header_tree as ht
import header_tree_bench as hb

ROW_VIEWS = (None, 64, 48, 32, 24, 16)     # columns in the whole-row view, widest first; None = every column
OUT = hm.he.EXP / "reader2_wide.json"
LEFT = hm.he.EXP / "reader2_wide_left.json"


def read_wide(grid, client, body):
    """-> (head_tree.read_table's result, columns in the whole-row view (None = all), None)
    or (None, None, why it stays skipped)."""
    for n in ROW_VIEWS:
        if n is not None and n >= grid.ncols:
            continue
        hd.ROW_VIEW_COLS = n
        try:
            return hd.read_table(grid, client, "B", body=body), n, None
        except RuntimeError as err:
            if "prompt too long" not in str(err):
                raise
        finally:
            hd.ROW_VIEW_COLS = None
    return None, None, f"too long even with {ROW_VIEWS[-1]} columns in the whole-row view"


def main(argv):
    every = json.loads(hm.ALL.read_text(encoding="utf-8"))
    more = json.loads(hm.OUT.read_text(encoding="utf-8")) if hm.OUT.exists() else {}
    done = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    todo = [p for p in (argv or sorted(every)) if p in every]
    client, left, n = None, {}, 0
    for p in todo:
        have = {e["table"] for e in every[p]} | {e["table"] for e in done.get(p, [])}
        grids = [ht.grid_from_html(h) for h in hb.html_tables(p)]
        new = [k for k, g in enumerate(grids) if k not in have and g.nrows >= 2 and g.ncols >= 2]
        if not new:
            continue
        keyed = hb.keyed_tables(p)
        for k in new:
            grid = grids[k]
            client = client or ct.DecisionClient(*hd.MODELS["nimble"][:2])
            t0, calls0 = time.time(), client.calls
            r, shown, why = read_wide(grid, client, body=k in keyed)
            if r is None:
                left.setdefault(p, []).append([k, why])
                print(f"  LEFT {p} t{k} ({grid.nrows}x{grid.ncols}): {why}", flush=True)
                continue
            r.update(paper=p, table=k, row_view_cols=shown, calls_all=client.calls - calls0)
            done.setdefault(p, []).append({"table": k, "nrows": grid.nrows, "ncols": grid.ncols,
                                           "data_start": r["head_end"], "first": r["start"], "columns": r["columns"],
                                           "secs": r["secs"], "calls": r["calls"], "full": r})
            OUT.write_text(json.dumps(done, indent=1, ensure_ascii=False), encoding="utf-8")
            n += 1
            print(f"  {p} t{k} ({grid.nrows}x{grid.ncols}): whole-row view "
                  f"{'every column' if shown is None else f'{shown} columns'}, first record {r['start']}, "
                  f"head {r['head_start']}-{r['head_end'] - 1}, {sum(bool(c['name']) for c in r['columns'])} of "
                  f"{len(r['columns'])} columns named, {r['calls']} calls ({client.calls - calls0} with the "
                  f"refused ones), {time.time() - t0:.0f}s", flush=True)
    added = 0
    for p, entries in done.items():
        for target in (every, more):
            if p in target:
                have = {e["table"] for e in target[p]}
                new = [e for e in entries if e["table"] not in have]
                target[p] = sorted(target[p] + new, key=lambda e: e["table"])
                added += len(new) if target is every else 0
    hm.ALL.write_text(json.dumps(every, indent=1, ensure_ascii=False), encoding="utf-8")
    if hm.OUT.exists():
        hm.OUT.write_text(json.dumps(more, indent=1, ensure_ascii=False), encoding="utf-8")
    LEFT.write_text(json.dumps(left, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"tables read now: {n}; entries added to {hm.ALL.name}: {added}; left skipped: "
          f"{sum(map(len, left.values()))} {left}")


if __name__ == "__main__":
    main(sys.argv[1:])
