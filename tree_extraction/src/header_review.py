"""
header_review.py — builds the header-check page: every table the head reader read, one
at a time, with its header rows and first body rows coloured by the role the reader
gave each cell, and the reading per column. The person marks each table right / wrong;
the page stores it in its `db` (collection "reviews" for round 1, "reviews_r<n>" after),
read back with ArtifactData into output/header_review/answers[_r<n>]/.

    python header_review.py            # round 1: experiments/step_on.json (frozen reader)
    python header_review.py 2          # round 2: experiments/round2.json, with round 1's
                                       # answers shown and changed readings flagged
-> tree_extraction/output/header_review/header_check.html
"""

from __future__ import annotations

import json
import re
import sys

import _paths
import header_tree as ht
import header_tree_bench as hb

EXP = _paths.OUTPUT / "header_tree_bench" / "experiments"
OUT = _paths.OUTPUT / "header_review"
SOURCES = {1: EXP / "step_on.json", 2: EXP / "round2.json", 3: EXP / "round3.json"}
ROW_ROLE = {"section": "section", "note": "footnote", "repeated_header": "column", "empty": "empty"}
BODY_ROWS = 3
CELL_CHARS = 90


def doc_id(paper, table):
    return re.sub(r"[^A-Za-z0-9_.~:@+-]", "_", f"{paper}__t{table}")


def roles_of(t):
    roles = {}
    for piece in t.get("full", {}).get("cells", []):
        for key, v in piece.items():
            roles[key] = v[0]
    return roles


def reading(t):
    """What a reader decided for one table, for comparing rounds."""
    cols = [(c["col"], c.get("name") or "", tuple(c.get("groups", [])), tuple(c.get("details", [])))
            for c in t.get("columns", [])]
    return t.get("data_start"), sorted(roles_of(t).items()), cols


def record(paper, t, grid):
    f = t.get("full", {})
    roles = roles_of(t)
    start = t.get("data_start", f.get("start", 1)) or 0
    head_start = f.get("head_start", 0) or 0
    last = min(grid.nrows, start + BODY_ROWS)
    rows = []
    for r in range(last):
        row = []
        for c in range(grid.ncols):
            x = grid.at(r, c)
            if not x or (x.r, x.c) != (r, c):
                continue
            text = " ".join(str(x.text or "").split())
            if r >= start:
                # the reader's ROW verdict where it gave one: rows between the head and
                # the first record (Q1B) and sparse body rows (QB); else plain data
                verdict = (f.get("pre", {}).get(str(r)) or f.get("body", {}).get(str(r)) or ["data"])[0]
                role = ROW_ROLE.get(verdict, "data")
            elif r < head_start and roles.get(f"{r},{c}") != "section":
                role = "pre"
            else:
                role = roles.get(f"{r},{c}", "none" if text else "empty")
            row.append({"c": c, "t": text[:CELL_CHARS] + ("…" if len(text) > CELL_CHARS else ""),
                        "rs": max(1, min(x.rowspan, last - r)), "cs": x.colspan, "role": role})
        rows.append(row)
    cols = [{"col": c["col"], "name": c.get("name") or "", "groups": c.get("groups", []),
             "details": c.get("details", [])} for c in t.get("columns", [])]
    return {"id": doc_id(paper, t["table"]), "paper": paper, "table": t["table"],
            "nrows": grid.nrows, "ncols": grid.ncols, "start": start, "rows": rows,
            "cols": cols, "sections": f.get("sections", []),
            "dev": (paper, t["table"]) in hb.DEV}


def answers(round_no):
    d = OUT / ("answers" if round_no == 1 else f"answers_r{round_no}") / "reviews"
    if round_no > 1:
        d = OUT / f"answers_r{round_no}" / f"reviews_r{round_no}"
    out = {}
    for f in d.glob("*.json") if d.exists() else []:
        v = json.loads(f.read_text(encoding="utf-8"))
        v = v.get("data", v)
        out[f.stem] = {"verdict": v.get("verdict"), "note": v.get("note", "")}
    return out


def main(argv):
    round_no = int(argv[0]) if argv else 1
    data = json.loads(SOURCES[round_no].read_text(encoding="utf-8"))
    prev_data = json.loads(SOURCES[round_no - 1].read_text(encoding="utf-8")) if round_no > 1 else {}
    prev_ans = answers(round_no - 1) if round_no > 1 else {}
    recs = []
    for paper in sorted(data):
        html = hb.html_tables(paper)
        before = {t["table"]: t for t in prev_data.get(paper, [])}
        for t in sorted(data[paper], key=lambda x: x["table"]):
            rec = record(paper, t, ht.grid_from_html(html[t["table"]]))
            if round_no > 1:
                rec["prev"] = prev_ans.get(rec["id"])
                rec["changed"] = t["table"] in before and reading(t) != reading(before[t["table"]])
            recs.append(rec)
    tpl = (_paths.OUTPUT.parent / "src" / "header_review_template.html").read_text(encoding="utf-8")
    config = {"collection": "reviews" if round_no == 1 else f"reviews_r{round_no}", "round": round_no}
    page = tpl.replace("/*__DATA__*/[]", json.dumps(recs, ensure_ascii=False).replace("</", "<\\/"))
    page = page.replace('/*__CONFIG__*/{"collection": "reviews", "round": 1}', json.dumps(config))
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / "header_check.html"
    out.write_text(page, encoding="utf-8")
    ch = sum(r.get("changed", False) for r in recs)
    print(f"round {round_no}: {len(recs)} tables, {ch} with a changed reading, "
          f"{sum(1 for r in recs if (r.get('prev') or {}).get('verdict') == 'wrong')} wrong last round; "
          f"{out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main(sys.argv[1:])
