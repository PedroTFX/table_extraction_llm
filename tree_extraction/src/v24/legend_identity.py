"""
legend_identity.py — a separate column-identity route for legends that do not print a word of the column's header
(2026-11-26, after legend_selector_misses.py). R3abc stays frozen and is not changed: this route is evaluated on its
own, and nothing is wired into the pipeline.

The diagnosis found the frozen selector's header-word requirement (R2: a distinctive code, or >= 2 codes AND an
informative header word) behind 5 of its 7 validated failures, in three forms: a synonym (Graf2021 'Nidification'
for 'Nesting site'), a cross-reference mark shared by the header and the note (AmbspergTraun1991 † ‡), and identity
through the meanings only (Wang2021's caption, Eckert2023's own-table note). The code/meaning adjacency case
(Cappellari2022) and the lowercase code (Espinosa2023) are parser questions, kept apart.

  pool   (no model) the pairs (unit, column) R3abc rejects ONLY for want of a header word: every other R3abc gate holds
         as it is (the column enumerated; >= 2 of its codes in the unit with strict number boundaries (b); at least
         one printed next to a meaning (a); a table row not repeated for the column in more than MAX_REPEAT rows of
         its table; a body row of the column's own table is data) and no distinctive code. A taxon header's dropped
         words (c) count as no header word. Safe cut (dk.SAFE_TAGS): the corrected text. Each pair carries
         descriptive source facts for the model: the unit's structure; whether it is by the column's own table (its
         row, a caption within 3000 characters before it, a note within 1500 after it); a mark (†‡§¶*#) printed both
         in the header and in the unit. The facts select nothing.
         -> TREE_OUTPUT/legend_coverage/identity_pool_<date>.json, IDENTITY_POOL_<date>.txt

    python legend_identity.py pool [papers]       (tuning papers by default)
"""
from __future__ import annotations

import collections
import contextlib
import io
import json
import re
import sys
import time

import _paths
import full_run_v24 as fr
import header_tree as ht
import header_tree_bench as hb
import legend_ablation as la
import legend_coverage as lc
import legend_inventory as li
import legend_scope as ls
import tag_strip_check as ts

OUT = lc.OUT
MARKS = "†‡§¶*#"


def flat(t):
    return " ".join(str(t or "").split())


def uid(u):
    if u["table"] is None:
        return f"p{u['id']}"
    return f"t{u['table']}r{u['row']}" + (f"c{u['col']}" if u["structure"] == "head cell" else "")


def near(u, raw, spans):
    if u["table"] is not None:
        return {"table": u["table"]}
    words = re.findall(r"\S+", u["text"])[:8]
    m = re.search(r"\s+".join(map(re.escape, words)), raw) if words else None
    if not m:
        return {}
    a = m.start()
    nxt = next(((k, s - a) for k, (s, _e) in enumerate(spans) if s > a), None)
    prv = next(((k, a - e) for k, (_s, e) in reversed(list(enumerate(spans))) if e <= a), None)
    return {"next": nxt, "prev": prv}


def own(nr, k):
    nxt, prv = nr.get("next") or (None, 0), nr.get("prev") or (None, 0)
    return nr.get("table") == k or (nxt[0] == k and nxt[1] < 3000) or (prv[0] == k and prv[1] < 1500)


def paper_pool(p, head):
    """The pool pairs of one paper (safe cut), and the number of R3abc links for comparison."""
    with ts.strip(True), contextlib.redirect_stdout(io.StringIO()):
        grids = {k: ht.grid_from_html(h) for k, h in enumerate(hb.html_tables(p))}
        first = {e["table"]: e.get("first") or 1 for e in head[p]}
        cols = lc.columns(p, grids, first)
        units = lc.units(p, grids, first)
        names = la.organism_names(p, head)
    genera = {n.split()[0] for n in names if len(n.split()) >= 2}
    for col in cols:
        col["taxon"] = la.is_taxon_header(col["header"], names, genera)
    raw = (_paths.PAPERS / p / f"{p}_full.md").read_text(encoding="utf-8", errors="replace")
    spans = [(m.start(), m.end()) for m in re.finditer(r"<table.*?</table>", raw, flags=re.S | re.I)]
    pairs = []
    for u in units:
        letters, nums, stems = lc.tokens(u["text"])
        strict = {str(int(m.group(1) or m.group(2))) for m in la.NUM_STRICT.finditer(u["text"])}
        t = flat(u["text"])
        nr = None
        for col in cols:
            if u["table"] == col["table"] and u["structure"] == "table row":
                continue
            hit, dist, words = lc.associate(u, (letters, nums, stems), col)
            hit_s = [x for x in hit if col["codes"][x] != "numeric" or x in strict]
            if len(hit_s) < 2:
                continue
            dist_s = [x for x in dist if x in hit_s]
            words_c = [] if col["taxon"] else words
            if dist_s or words_c:
                continue                                  # R2 holds: R3abc's own route decides this pair
            exp = [x for x in la.explicit_codes(t, col) if x in hit_s]
            if not exp:
                continue                                  # gate a fails: not this route's question
            if nr is None:
                nr = near(u, raw, spans)
            hm = {ch for ch in MARKS if ch in col["header"]}
            pairs.append({"paper": p, "unit": uid(u), "unit_id": u["id"], "structure": u["structure"],
                          "unit_table": u["table"], "column": f"t{col['table']}c{col['col']}", "table": col["table"],
                          "header": col["header"][:160], "values": col["values"][:lc.MAX_DISTINCT],
                          "codes": hit_s, "explicit": exp, "taxon_header": col["taxon"],
                          "header_words_dropped": words if col["taxon"] else [],
                          "own_table": own(nr, col["table"]), "near": nr,
                          "shared_mark": sorted(ch for ch in hm if ch in t), "shapes": li.shape_hits(u["text"]),
                          "text": t[:1500]})
    rep = collections.Counter((x["unit_table"], x["column"]) for x in pairs if x["structure"] == "table row")
    pairs = [x for x in pairs if not (x["structure"] == "table row" and rep[(x["unit_table"], x["column"])] > lc.MAX_REPEAT)]
    return pairs


def pool(papers):
    OUT.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y-%m-%d")
    head = fr.head_runs()
    allp = []
    for p in papers:
        if p not in head:
            continue
        t0 = time.time()
        ps = paper_pool(p, head)
        allp += ps
        print(f"  {p:22s} {len(ps):5d} pairs, {len({x['unit'] for x in ps}):4d} units  {time.time() - t0:.0f}s", flush=True)
    units = {(x["paper"], x["unit"]) for x in allp}
    L = [f"identity-route pool (R3abc rejects the pair only for want of a header word), {len(papers)} tuning papers, "
         f"safe cut; no model", "",
         f"pairs {len(allp)}, units {len(units)}, papers {len({x['paper'] for x in allp})}",
         "by structure (pairs / units): " + ", ".join(
             f"{s} {sum(x['structure'] == s for x in allp)} / {len({(x['paper'], x['unit']) for x in allp if x['structure'] == s})}"
             for s in ("prose", "caption", "numbered list", "head cell", "footnote", "table row")),
         f"by the column's own table {sum(x['own_table'] for x in allp)}; a shared mark {sum(bool(x['shared_mark']) for x in allp)}; "
         f"taxon header (words dropped) {sum(x['taxon_header'] for x in allp)}",
         f"gemma prompts if one per unit (all its pool columns together): {len(units)}", "", "by paper (pairs, units):"]
    pp = collections.Counter(x["paper"] for x in allp)
    for p, n in pp.most_common():
        L.append(f"  {p:22s} [{ls.SPLIT.get(p)}] {n:5d} {len({x['unit'] for x in allp if x['paper'] == p}):4d}")
    (OUT / f"identity_pool_{stamp}.json").write_text(json.dumps(allp, indent=1, ensure_ascii=False), encoding="utf-8")
    (OUT / f"IDENTITY_POOL_{stamp}.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    cmd, args = (sys.argv[1], sys.argv[2:]) if len(sys.argv) > 1 else ("pool", [])
    if cmd == "pool":
        pool(args or ls.tuning_papers())
    else:
        sys.exit(f"unknown command {cmd}")
