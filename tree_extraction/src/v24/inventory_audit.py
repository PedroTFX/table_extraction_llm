"""
inventory_audit.py — where the legend inventory loses printed legend pairs (2026-11-24, after legend_scope.py: the
passage choice cannot add a right decode, only the inventory can). Code only, no model; nothing is rebuilt.

For every coded pair (code -> GT term) of the decoding key (decode_key.build_key, as legend_scope.key_of reads it) on
the tuning papers (dev + held_a of split_v15) whose pair the paper prints (decode_key.where is not 'term only',
'not in the paper', 'binary convention'):

  captured        the inventory holds an entry for the cell with the GT term (decode_inv.captured)
  dropped         gemma listed it, the boundary check dropped it (the inventory's 'dropped' list)
  in a unit       a source unit prints code and term, gemma did not list it
  table header    not in a unit: a head cell (above the table's first record) of a table wider than 4 columns
                  prints both ('Zigum (1: underdeveloped; 2: developed …)')
  table body      not in a unit: a body cell, or a row with the code in one cell and the term in another, of a
                  table wider than 4 columns
  prose           not in a unit: a paragraph prints both but has fewer than 2 legend shapes (legend_inventory.SHAPES);
                  'numbered' when the paragraph prints the code as '1)' before the term
  not located     printed by decode_key.where, but none of the above found it

Weighted by species rows (the key's cells, as decoder_v2.score_dir_from counts them). Each lost pair is listed
with the text around it, grouped by class, so the missing source structures can be read.

    python inventory_audit.py [papers]      -> output/inventory_audit/AUDIT.txt, audit.json
TREE_OUTPUT picks the root whose inventory is audited (output_frozen_109: the frozen run's).
"""
from __future__ import annotations

import collections
import json
import re
import sys

import _paths
import decode_inv as di
import decode_key as dk
import decoder as v1
import decoder_v2 as v2
import full_run_v24 as fr
import header_tree as ht
import header_tree_bench as hb
import legend_inventory as li
import legend_scope as ls
from fill_template import _drop_reference_lists

OUT = _paths.OUTPUT / "inventory_audit"
WINDOW = 110


def code_re(code):
    return [re.compile(rf"(?<![\w]){re.escape(f)}(?![\w])") for f in v2.forms(code)]


def term_re(term):
    words = re.findall(r"[^\W_]+", term)
    return re.compile(r"[\W_]+".join(map(re.escape, words)), re.I) if words else None


def has_both(text, code, term):
    """The start of the code form printed nearest the term, when it is within decoder.NEAR characters of it
    (the boundary check's reach); else None."""
    tr = term_re(term)
    if not tr:
        return None
    terms = [m.start() for m in tr.finditer(text)]
    codes = [m.start() for r in code_re(code) for m in r.finditer(text)]
    if not terms or not codes:
        return None
    d, i = min((abs(a - b), a) for a in codes for b in terms)
    return i if d <= v1.NEAR else None


def around(text, i):
    a = max(0, i - WINDOW)
    return ("…" if a else "") + " ".join(text[a:i + WINDOW].split()) + ("…" if i + WINDOW < len(text) else "")


def paragraphs(paper):
    raw = (_paths.PAPERS / paper / f"{paper}_full.md").read_text(encoding="utf-8", errors="replace")
    prose = re.sub(r"<table.*?</table>", "\n\n", _drop_reference_lists(raw), flags=re.S | re.I)
    return [" ".join(p.split()) for p in re.split(r"\n\s*\n", dk.clean(prose)) if len(p.strip()) > 3]


def locate(paper, code, term, inv, grids, first, paras):
    """-> (class, detail, snippet)"""
    for e in inv.get("dropped", []):
        if e.get("code") and v2.same_form(code, e["code"]) and f" {v1._flat(term)} " in f" {v1._flat(e.get('term'))} ":
            return "dropped", e.get("why", ""), f"gemma: '{e['code']}' = '{e.get('term')}' ({e.get('variable')})"
    for u in inv.get("units", []):
        i = has_both(u["text"], code, term)
        if i is not None:
            return "in a unit", f"{u['id']} ({u['kind']})", around(u["text"], i)
    for k, g in grids.items():
        if g.ncols <= 4:
            continue
        top = first.get(k, 1)
        seen = set()
        for r in range(g.nrows):
            cells = []
            for c in range(g.ncols):
                x = g.at(r, c)
                if not x or (x.r, x.c) in seen:
                    continue
                seen.add((x.r, x.c))
                t = " ".join(str(x.text or "").split())
                cells.append(t)
                i = has_both(t, code, term)
                if i is not None:
                    where = "table header" if r < top else "table body"
                    return where, f"t{k} ({g.nrows}x{g.ncols}) row {r} col {c}", around(t, i)
            if any(any(rx.fullmatch(t) for rx in code_re(code)) for t in cells) and \
                    any(f" {v1._flat(term)} " in f" {v1._flat(t)} " for t in cells):
                where = "table header" if r < top else "table body"
                return where, f"t{k} ({g.nrows}x{g.ncols}) row {r}: code and term in separate cells", \
                    around(" | ".join(cells), 0)
    for p in paras:
        i = has_both(p, code, term)
        if i is not None:
            numbered = any(re.search(rf"(?<![\w(]){re.escape(f)}\)\s", p) for f in v2.forms(code))
            return "prose", f"{li.shape_hits(p)} legend shapes{'; numbered' if numbered else ''}", around(p, i)
    return "not located", "", ""


def audit(papers):
    OUT.mkdir(parents=True, exist_ok=True)
    head = fr.head_runs()
    rows = []
    for p in papers:
        if ls.SPLIT.get(p) not in ls.TUNING:
            continue
        f = li.OUT / f"{p}.json"
        if not f.exists():
            continue
        inv = json.loads(f.read_text(encoding="utf-8"))
        cats = di.inventory(p) or []
        found = ls.key_of(p)
        if not any(e["kind"] == "coded" for e in found.values()):
            continue
        weight = {(r["trait"], r["cell"]): r["w"] for r in v2.score_dir_from(p, found, lambda e: None)}
        grids = {k: ht.grid_from_html(h) for k, h in enumerate(hb.html_tables(p))}
        first = {e["table"]: e.get("first") or 1 for e in head.get(p, [])}
        paras = paragraphs(p)
        for T, e in found.items():
            if e["kind"] != "coded":
                continue
            g = grids[e["table"]]
            header = " ".join(str(g.at(r, e["col"]).text or "") for r in range(min(3, g.nrows)) if g.at(r, e["col"]))
            for code, term in e["coded"].items():
                w = e["where"][code]
                if w in v1.NO_LEGEND or (p, code) in v1.GT_ERRORS:
                    continue
                if di.captured(cats, code, term, header):
                    cls, det, snip = "captured", "", ""
                else:
                    cls, det, snip = locate(p, code, term, inv, grids, first, paras)
                rows.append({"paper": p, "group": ls.SPLIT[p], "trait": T, "table": e["table"], "col": e["col"],
                             "code": code, "term": term, "where": w, "class": cls, "detail": det, "text": snip,
                             "w": weight.get((T, code), 1)})
        print(f"  {p:22s} {sum(r['paper'] == p for r in rows)} printed pairs", flush=True)
    (OUT / "audit.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")
    order = ["captured", "dropped", "in a unit", "table header", "table body", "prose", "not located"]
    c, cw = collections.Counter(r["class"] for r in rows), collections.Counter()
    for r in rows:
        cw[r["class"]] += r["w"]
    L = [f"inventory audit: printed legend pairs of the decoding key, {len({r['paper'] for r in rows})} tuning papers, "
         f"{len(rows)} pairs ({sum(cw.values())} species rows)", ""]
    L += [f"  {k:13s} {c[k]:>4d} pairs  {cw[k]:>6d} rows" for k in order if c[k]]
    L.append("")
    L.append("by paper (pairs: captured / lost):")
    for p in sorted({r["paper"] for r in rows}):
        rs = [r for r in rows if r["paper"] == p]
        lost = collections.Counter(r["class"] for r in rs if r["class"] != "captured")
        L.append(f"  {p:22s} [{rs[0]['group']}] {sum(r['class'] == 'captured' for r in rs)} / "
                 f"{sum(lost.values())}  " + ", ".join(f"{k} {v}" for k, v in lost.most_common()))
    for k in order[1:]:
        rs = sorted((r for r in rows if r["class"] == k), key=lambda r: (r["paper"], r["table"], r["col"]))
        if not rs:
            continue
        L += ["", f"### {k} ({len(rs)} pairs, {sum(r['w'] for r in rs)} rows)"]
        for r in rs:
            L.append(f"  {r['paper']} t{r['table']}c{r['col']} {r['trait'][:30]!r}: '{r['code']}' -> '{r['term'][:40]}' "
                     f"(x{r['w']}; where: {r['where']}) {r['detail']}")
            if r["text"]:
                L.append(f"      {r['text']}")
    (OUT / "AUDIT.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:40]))


if __name__ == "__main__":
    audit(sys.argv[1:] or ls.tuning_papers())
