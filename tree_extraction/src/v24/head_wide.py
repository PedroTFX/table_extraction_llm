"""
head_wide.py — tables too big for the head reader, read in column windows (tree_extraction/plans/07_big_tables.md,
2026-11-10). The head reader shows whole rows to find the first record; a table with very many columns does not fit
nimble's context even at the smallest cell width, so head_more.py skips it and nothing after it sees the table
(Chichorro2022's dataset sheet: 881 rows x 113 columns, all 620 GT rows).

  only    tables of a paper the head reader has read that have no entry and more than WINDOW columns; every table
          read before keeps its entry byte for byte (entries are only added)
  windows the first ID_COLS columns (what the rows are) stay in every window; the other columns are cut into slices
          of at most WINDOW - ID_COLS, each cut placed where it splits the fewest cells of the first rows. Each
          window is a table of its own for the frozen reader (head_tree.read_table, unchanged): a cell that spans
          past a cut is shown in both windows with the columns it covers there
  check   layout: every window must give the same first record and the same end of the head. If they differ the
          table stays skipped and is reported
  join    the windows' column names, with their real column numbers; head cells by their real positions; a body row
          is a section / note / repeated header only when it is sparse in the whole table and every window that was
          asked about it gave the same answer

    python head_wide.py [papers]      -> experiments/reader2_wide.json, added to reader2_all.json (and to
                                         reader2_more.json for papers it holds)
The paper then needs its later stages again, in a root of its own: bash ../reread_paper.sh <paper>.
"""
from __future__ import annotations

import json
import statistics
import sys
import time

import column_tree as ct
import head_more as hm
import head_tree as hd
import header_tree as ht
import header_tree_bench as hb

WINDOW = 32                 # columns per window, the ID columns included
ID_COLS = 2
MAX_WINDOWS = 12            # the cap: a table needing more windows is reported and left
OUT = hm.he.EXP / "reader2_wide.json"


def sub_grid(grid, cols):
    """The grid with only these columns (sorted): a cell keeps its rows; its width is the window columns it covers."""
    cells = {}
    for x in {(x.r, x.c): x for x in grid.cells.values()}.values():
        js = [j for j, c in enumerate(cols) if x.c <= c < x.c + x.colspan]
        if not js:
            continue
        cell = ht.Cell(x.text, x.r, js[0], x.rowspan, len(js))
        for dr in range(x.rowspan):
            for j in js:
                cells[(x.r + dr, j)] = cell
    return ht.Grid(cells, grid.nrows, len(cols))


def windows(grid):
    """[columns] per window: the ID columns, then a slice; cuts where the fewest head cells are split."""
    top = range(min(grid.nrows, hd.HEAD_ROWS))

    def crossing(c):
        return len({(x.r, x.c) for r in top for x in [grid.at(r, c)] if x and x.c < c < x.c + x.colspan})

    ids = list(range(min(ID_COLS, grid.ncols)))
    step = WINDOW - len(ids)
    out, start = [], len(ids)
    while start < grid.ncols:
        if grid.ncols - start <= step:
            out.append(ids + list(range(start, grid.ncols)))
            break
        target = start + step
        cut = min(range(max(start + 1, target - 4), target + 1), key=lambda c: (crossing(c), target - c))
        out.append(ids + list(range(start, cut)))
        start = cut
    return out


def sparse_rows(grid, start):
    """The rows head_tree.body_rows would ask about, counted on the whole table."""
    filled = {r: sum(1 for c in range(grid.ncols) if grid.origin(r, c) and grid.origin(r, c).text)
              for r in range(start, grid.nrows)}
    if not filled:
        return set()
    med = statistics.median(filled.values())
    return {r for r, n in filled.items() if 0 < n <= max(1, 0.4 * med) and med >= 2}


def read_wide(grid, client):
    """-> (the joined result in head_tree.read_table's form, None) or (None, why it stays skipped)."""
    wins = windows(grid)
    if len(wins) > MAX_WINDOWS:
        return None, f"{len(wins)} windows needed, over the cap of {MAX_WINDOWS}"
    reads = []
    for cols in wins:
        r = hd.read_table(sub_grid(grid, cols), client, "B", body=True)
        reads.append(r)
        if (r["start"], r["head_end"]) != (reads[0]["start"], reads[0]["head_end"]):
            return None, (f"windows disagree on where the data starts: first record {reads[0]['start']} / head end "
                          f"{reads[0]['head_end']} in window 1, {r['start']} / {r['head_end']} in window {len(reads)}")
    first = reads[0]
    ids = set(wins[0][:ID_COLS])
    columns, cells, pieces, block = [], [], [], 0
    for i, (cols, r) in enumerate(zip(wins, reads)):
        for c in r["columns"]:
            real = cols[c["col"]]
            if i and real in ids:
                continue
            columns.append(dict(c, col=real, block=block + c["block"]))
        block += len(r["pieces"])
        pieces += [[cols[j] for j in piece] for piece in r["pieces"]]
        for cl in r["cells"]:
            cells.append({f"{k.split(',')[0]},{cols[int(k.split(',')[1])]}": v for k, v in cl.items()})
    body = {}
    for row in sparse_rows(grid, first["start"]):
        got = {tuple(r["body"][str(row)])[0] for r in reads if str(row) in r["body"]}
        if len(got) == 1:
            role = got.pop()
            ps = [r["body"][str(row)][1] for r in reads if str(row) in r["body"]]
            body[str(row)] = [role, round(min(ps), 3)]
    return {"variant": first["variant"], "start": first["start"],
            "head_start": min(r["head_start"] for r in reads), "head_end": first["head_end"], "pre": first["pre"],
            "q1": first["q1"], "pieces": pieces, "cells": cells, "asked_again": {}, "spec": [], "joins": {},
            "stacked": [], "regrouped": {}, "sections": sorted({s for r in reads for s in r["sections"]}),
            "body": body, "columns": sorted(columns, key=lambda c: c["col"]),
            "calls": sum(r["calls"] for r in reads), "secs": round(sum(r["secs"] for r in reads), 1),
            "windows": wins}, None


def main(argv):
    every = json.loads(hm.ALL.read_text(encoding="utf-8"))
    more = json.loads(hm.OUT.read_text(encoding="utf-8")) if hm.OUT.exists() else {}
    done = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    todo = [p for p in (argv or sorted(every)) if p in every]
    client, left, n = None, {}, 0
    for p in todo:
        have = {e["table"] for e in every[p]} | {e["table"] for e in done.get(p, [])}
        for k, html in enumerate(hb.html_tables(p)):
            grid = ht.grid_from_html(html)
            if k in have or grid.nrows < 2 or grid.ncols <= WINDOW:
                continue
            client = client or ct.DecisionClient(*hd.MODELS["nimble"][:2])
            t0 = time.time()
            try:
                r, why = read_wide(grid, client)
            except RuntimeError as err:
                r, why = None, str(err)[:160]
            if r is None:
                left.setdefault(p, []).append([k, why])
                print(f"  LEFT {p} t{k} ({grid.nrows}x{grid.ncols}): {why}", flush=True)
                continue
            r.update(paper=p, table=k)
            done.setdefault(p, []).append({"table": k, "nrows": grid.nrows, "ncols": grid.ncols,
                                           "data_start": r["head_end"], "first": r["start"], "columns": r["columns"],
                                           "secs": r["secs"], "calls": r["calls"], "full": r})
            OUT.write_text(json.dumps(done, indent=1, ensure_ascii=False), encoding="utf-8")
            n += 1
            print(f"  {p} t{k} ({grid.nrows}x{grid.ncols}): {len(r['windows'])} windows, first record {r['start']}, "
                  f"head {r['head_start']}-{r['head_end'] - 1}, {sum(bool(c['name']) for c in r['columns'])} of "
                  f"{len(r['columns'])} columns named, {r['calls']} calls, {time.time() - t0:.0f}s", flush=True)
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
    (hm.he.EXP / "reader2_wide_left.json").write_text(json.dumps(left, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"wide tables read now: {n}; entries added to {hm.ALL.name}: {added}; left skipped: "
          f"{sum(map(len, left.values()))} {left}")


if __name__ == "__main__":
    main(sys.argv[1:])
