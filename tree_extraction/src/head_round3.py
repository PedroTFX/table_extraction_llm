"""
head_round3.py — round 3 of the head reader, as a PATCH on round 2's stored answers:
only the new questions are asked, only where their geometry fires, so every other
table keeps exactly its round-2 reading (nimble drifts between model loads, and the
person's rule is that tables marked right must not change).

  QG3  a cell QG turned into a section while its row holds other text (Derhe 'Global
       model', Graf 'Areas', Odanaka 'Landscape' sit beside column names): asked again
       without 'section' — a section label is alone in its row.
  QL   a head row whose only text is one cell, directly above the body (the last head
       row, or only such rows between it and the body): section for the rows below,
       a label of the columns, or a title? (Graf t7 'Andreninae', Ibarra 'a) Species
       richness', Rebrina 'Acrididae', Guareschi 'Taxonomic diversity')
The columns are then rebuilt; stacks of names already answered in round 2 are reused.

    python head_round3.py   -> experiments/round3.json
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

SRC = he.EXP / "round2.json"
OUT = he.EXP / "round3.json"
QL = {"section": "a section label: it names the block of data rows below it",
      "columns": "a label of the columns: a column name, or a label over several columns",
      "title": "a title or caption of the whole table"}


def texts_in_row(grid, r):
    """The distinct non-empty cells covering row r (spanning cells from above count)."""
    seen = {}
    for c in range(grid.ncols):
        x = grid.at(r, c)
        if x and str(x.text or "").strip():
            seen[(x.r, x.c)] = x
    return list(seen.values())


def lone_rows(grid, head_end):
    """Head rows whose only text is one cell of their own, directly above the body."""
    out = []
    for r in range(head_end - 1, -1, -1):
        xs = texts_in_row(grid, r)
        if len(xs) == 1 and xs[0].r == r and grid.ncols >= 2:
            out.append(r)
        else:
            break                                        # only rows directly above the body
    return out


def patch(grid, f, client):
    head_end, start, pre = f["head_end"], f["start"], f["pre"]
    if not head_end:
        return None
    cells_by_piece = f["cells"]
    state = hd.head_state(grid, f["pieces"][0], head_end, start, pre)
    asked = {}
    # QG3
    redo = {}
    for k, v in (f.get("regrouped") or {}).items():
        x = hd._cell(grid, k)
        if v[0] == "section" and len(texts_in_row(grid, x.r)) > 1:
            redo[k] = x
    if redo:
        opts = hd.qc_options()
        crit = {r: opts[r] for r in ("column", "title", "footnote")}
        items = list(redo.items())
        qs = {f"q{i}": {"type": "choice",
                        "instructions": f"Row {x.r}, the cell '{hd._clip(x.text)}' was called a label "
                                        f"over several columns, but no head cell sits under it. What is it?",
                        "criteria": crit} for i, (_k, x) in enumerate(items)}
        ans = hd._ask(client, state, qs)
        for i, (k, _x) in enumerate(items):
            a = ans.get(f"q{i}") or {}
            if a.get("choice"):
                asked[k] = [a["choice"], hd._p(a, a["choice"]), "QG3"]
    # QL
    rows = lone_rows(grid, head_end)
    items = []
    for r in rows:
        x = texts_in_row(grid, r)[0]
        k = f"{x.r},{x.c}"
        role = next((cl[k][0] for cl in cells_by_piece if k in cl), None)
        if role != "section" and k not in asked:
            items.append((k, x))
    if items:
        qs = {f"q{i}": {"type": "choice",
                        "instructions": f"Row {x.r} holds only one cell, '{hd._clip(x.text)}', and the "
                                        f"data rows follow below it. What is it?",
                        "criteria": dict(QL)} for i, (_k, x) in enumerate(items)}
        ans = hd._ask(client, state, qs)
        for i, (k, _x) in enumerate(items):
            a = ans.get(f"q{i}") or {}
            ch = a.get("choice")
            if ch in ("section", "title"):
                asked[k] = [ch, hd._p(a, ch), "QL"]
            elif ch:
                asked.setdefault(k, None)                 # asked, kept its role
                f.setdefault("ql_kept", {})[k] = hd._p(a, ch)
    changed = {k: v for k, v in asked.items() if v}
    if not asked:
        return None
    for cl in cells_by_piece:
        for k, v in changed.items():
            if k in cl:
                cl[k] = v
    columns, stacked_all = [], []
    for i, (cols, cells) in enumerate(zip(f["pieces"], cells_by_piece)):
        st = hd.head_state(grid, cols, head_end, start, pre)
        stacked = hd.stacked_names(grid, cols, client, st, cells, head_end, known=f["stacked"][i])
        stacked_all.append(stacked)
        cs = hd.columns_from_cells(grid, cols, cells, stacked, f["joins"], head_end, block=i)
        columns += [c for c in cs if i == 0 or c["col"] != 0]
    labelled = [int(k.split(",")[0]) for cl in cells_by_piece for k, (role, *_r) in cl.items()
                if role in ("group", "column", "joined")]
    f.update(cells=cells_by_piece, stacked=stacked_all, columns=columns,
             head_start=min(labelled) if labelled else 0,
             sections=sorted({hd._cell(grid, k).text for cl in cells_by_piece
                              for k, (role, *_r) in cl.items() if role == "section"}),
             round3={k: v for k, v in asked.items()})
    return f


def main(argv):
    for name in ("SECTION_CELL", "EMPTY_GROUP_RECHECK", "SPEC_STATS"):
        setattr(hd, name, True)                           # round 2's switches stay on
    base = json.loads(SRC.read_text(encoding="utf-8"))
    client = ct.DecisionClient(*hd.MODELS["nimble"][:2])
    out, fired, t0 = json.loads(json.dumps(base)), 0, time.time()
    for p in sorted(out):
        html = hb.html_tables(p)
        for e in out[p]:
            grid = ht.grid_from_html(html[e["table"]])
            f = patch(grid, e["full"], client)
            if f is None:
                continue
            fired += 1
            e["full"], e["columns"] = f, f["columns"]
            print(f"  {p} t{e['table']}: {json.dumps(f['round3'], ensure_ascii=False)}", flush=True)
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"done: new questions fired on {fired} tables, {client.calls} calls, "
          f"{round(time.time() - t0)}s")


if __name__ == "__main__":
    main(sys.argv[1:])
