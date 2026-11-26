"""
legend_selector_misses.py — diagnosis of the frozen R3abc selector's missed targets (2026-11-26). NO MODEL CALLS;
nothing is tuned or switched: R3abc (legend_ablation.variant 'abc'), Stage 2, the decoders and legend_inventory are
unchanged, and dk.SAFE_TAGS stays off by default (it is set per cut here and restored).

A miss counts against the selector only when three conditions hold (the review of 2026-11-26):
  1. the legend text and its variable's identity are in the unit (judged by eye; labels file)
  2. a real table column holding the defined codes is verified
  3. the frozen R3abc does not link that unit to that column
Everything else is an upstream case (unit boundary, the tag strip, the table reading) or no target at all.

Two sources of targets:
  A. GT-anchored, corpus-wide: every coded column of the decoding key (legend_scope.key_of: a column whose cells are
     codes that a consistent legend maps to the GT's terms) on the tuning papers, with the pairs the paper prints
     (dk.where not in decoder.NO_LEGEND). The key verifies condition 2. A unit R3abc enumerates
     (legend_coverage.units) that prints a coded pair (code and GT term within decoder.NEAR, inventory_audit.has_both)
     is a defining unit of the column; a body row of the column's own table is data, as in R3abc, and is counted
     apart. The column is covered when R3abc links a defining unit to it.
  B. Named cases outside the key: the calibration's missed targets and never-proposed units (gold v4.1), and the
     legends the old tag strip deleted (tag_strip_check.NEEDLES). The unit is found by its text; a given target is
     traced, and every column of the paper that shares codes with the unit is listed with its values, so condition 2
     can be checked by eye.

Both run on the old cut (the production text) and the safe cut (dk.SAFE_TAGS), so a target the tag strip hid is told
apart from one the selector drops.

The gate trace of a (unit, column), in R3abc's order; every gate that fails is listed, the first is the reason:
  own table   a body row of the column's own table is data
  column      legend_coverage.columns enumerates it (2..15 distinct body values, some code-like); else the rest is
              traced on the column's raw values
  codes       the column's codes in the unit as tokens (lc.associate); numeric ones also with strict boundaries (b)
  R2          a distinctive code, or >= 2 codes and an informative word of the header; a taxon header gives no
              words (c)
  a           at least one code printed next to a meaning (la.explicit_codes)
  repeat      a table row that is a candidate for the column in more than MAX_REPEAT rows of its table is data
The trace is checked against la.variant(la.features(...), 'abc'): the two must agree on every pair.

    python legend_selector_misses.py [papers]       (tuning papers by default)
-> TREE_OUTPUT/legend_coverage/SELECTOR_MISSES_<date>.txt, selector_misses_<date>.json
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
import decode_key as dk
import decoder as v1
import full_run_v24 as fr
import header_tree as ht
import header_tree_bench as hb
import inventory_audit as ia
import legend_ablation as la
import legend_coverage as lc
import legend_inventory as li
import legend_scope as ls
import tag_strip_check as ts

OUT = lc.OUT
CALIB = OUT / "calib_gold_v4.1_2026-11-25.json"
CUTS = (("old", False), ("safe", True))
TOP_UNITS = 3          # defining units traced per missed column
TOP_COLUMNS = 12       # columns listed per named unit


def flat(t):
    return " ".join(str(t or "").split())


def uid(u):
    if u["table"] is None:
        return f"p{u['id']}"
    return f"t{u['table']}r{u['row']}" + (f"c{u['col']}" if u["structure"] == "head cell" else "")


def raw_column(g, k, c, first):
    """legend_coverage.columns' view of one grid column without its filters: {table, col, header, words, codes,
    values}."""
    top = min(first.get(k, 1), g.nrows)
    vals = set()
    for r in range(top, g.nrows):
        x = g.at(r, c)
        if x and x.c == c:
            t = flat(x.text)
            if t and t.lower() not in lc.EMPTY:
                vals.add(t)
    codes = {}
    for v in vals:
        for part in v1.list_parts(v):
            kind = lc.code_kind(part)
            if kind:
                codes[lc.norm_code(part, kind)] = kind
    head = []
    for r in range(top):
        x = g.at(r, c)
        if x:
            t = flat(x.text)
            if t and t not in head:
                head.append(t)
    header = " / ".join(head)
    return {"table": k, "col": c, "header": header, "words": lc.informative(header), "codes": codes,
            "values": sorted(vals)}


class Paper:
    """One paper in one cut: R3abc's columns and units, the frozen selection, the decoding key."""

    def __init__(self, p, safe, head, names):
        self.p, self.safe = p, safe
        with ts.strip(safe), contextlib.redirect_stdout(io.StringIO()):
            self.grids = {k: ht.grid_from_html(h) for k, h in enumerate(hb.html_tables(p))}
            self.first = {e["table"]: e.get("first") or 1 for e in head[p]}
            self.cols = {(c["table"], c["col"]): c for c in lc.columns(p, self.grids, self.first)}
            self.units = lc.units(p, self.grids, self.first)
            rows, _pp, _t = la.features([p])
            try:
                self.key = ls.key_of(p)
            except Exception as e:                       # no GT for the paper
                self.key, self.key_error = {}, repr(e)[:120]
        self.names = names
        self.genera = {n.split()[0] for n in names if len(n.split()) >= 2}
        for col in self.cols.values():
            col["taxon"] = la.is_taxon_header(col["header"], names, self.genera)
        self.rows = rows
        self.sel = {(r["unit"], r["table"], r["col"]) for r in la.variant(rows, "abc")}
        self.linked = collections.defaultdict(set)       # (k, c) -> unit ids R3abc links to it
        for u, k, c in self.sel:
            self.linked[(k, c)].add(u)
        pre = [r for r in rows if self._abc_gates(r)]
        self.rep = collections.Counter((r["unit_table"], r["table"], r["col"]) for r in pre
                                       if r["structure"] == "table row")
        self.by_id = {u["id"]: u for u in self.units}

    @staticmethod
    def _abc_gates(r):
        """legend_ablation.variant('abc') for one R2 row, before the repeat rule."""
        hit, exp = r["hit_strict"], r["explicit_strict"]
        words = [] if r["taxon"] else r["words"]
        dist = [c for c in r["dist"] if c in hit]
        return bool(dist or (len(hit) >= 2 and words)) and bool(exp)

    def column(self, k, c):
        if (k, c) in self.cols:
            return self.cols[(k, c)], True
        col = raw_column(self.grids[k], k, c, self.first)
        col["taxon"] = la.is_taxon_header(col["header"], self.names, self.genera)
        return col, False

    def trace(self, u, k, c):
        """-> {fails: [gate, ...], first, hit, strict, distinctive, words, explicit, selected}"""
        col, enumerated = self.column(k, c)
        fails = []
        if u["table"] == k and u["structure"] == "table row":
            fails.append("own table: a body row of the column's table is data")
        if not enumerated:
            n = len(col["values"])
            fails.append(f"column not enumerated: {n} distinct values" if not 2 <= n <= lc.MAX_DISTINCT
                         else "column not enumerated: no code-like values")
        t = flat(u["text"])
        tok = lc.tokens(u["text"])
        hit, dist, words = lc.associate(u, tok, col) if col["codes"] else ([], [], [])
        strict = {str(int(m.group(1) or m.group(2))) for m in la.NUM_STRICT.finditer(u["text"])}
        hit_s = [x for x in hit if col["codes"][x] != "numeric" or x in strict]
        dist_s = [x for x in dist if x in hit_s]
        words_c = [] if col["taxon"] else words
        exp = [x for x in la.explicit_codes(t, col) if x in hit_s] if col["codes"] else []
        if not hit:
            fails.append("codes: none of the column's codes in the unit")
        elif not hit_s:
            fails.append("codes (b): the numeric codes only inside longer numbers")
        if hit_s and not (dist_s or (len(hit_s) >= 2 and words_c)):
            if len(hit_s) < 2 and not words_c:
                fails.append("R2: one code, no distinctive code, no header word")
            elif len(hit_s) < 2:
                fails.append("R2: one code, no distinctive code")
            elif words and col["taxon"]:
                fails.append("R2 (c): header words dropped, a taxon header")
            else:
                fails.append("R2: no informative header word in the unit")
        if hit_s and not exp:
            fails.append("a: no code printed next to a meaning")
        if not fails and u["structure"] == "table row" and self.rep[(u["table"], k, c)] > lc.MAX_REPEAT:
            fails.append(f"repeat: {self.rep[(u['table'], k, c)]} rows of its table are candidates (data)")
        selected = (u["id"], k, c) in self.sel
        return {"fails": fails, "first": fails[0] if fails else "selected", "hit": hit, "strict": hit_s,
                "distinctive": dist_s, "words": words, "words_used": words_c, "explicit": exp, "selected": selected,
                "header": col["header"][:100], "taxon": col["taxon"], "enumerated": enumerated,
                "codes": sorted(col["codes"])[:20], "values": col["values"][:15], "n_values": len(col["values"])}

    def agreement(self):
        """Every R2 row: the trace's verdict equals la.variant's. -> number of disagreements"""
        bad = 0
        for r in self.rows:
            tr = self.trace(self.by_id[r["unit"]], r["table"], r["col"])
            bad += (tr["first"] == "selected") != tr["selected"]
        return bad

    def find(self, structure, text, table=None):
        """The unit with this structure whose text starts like the given text (table units on their table)."""
        want = flat(text)[:80]
        for u in self.units:
            if (structure is None or u["structure"] == structure) and (table is None or u["table"] == table) \
                    and flat(u["text"]).startswith(want):
                return u
        for u in self.units:
            if (table is None or u["table"] == table) and want[:50] in flat(u["text"]):
                return u
        return None

    def candidates(self, u, exclude=()):
        """Columns of the paper (enumerated or not) that share codes with the unit, best first."""
        out = []
        for k, g in self.grids.items():
            for c in range(g.ncols):
                if (k, c) in exclude:
                    continue
                tr = self.trace(u, k, c)
                if tr["strict"] and (len(tr["strict"]) >= 2 or tr["distinctive"] or tr["words"]):
                    out.append((k, c, tr))
        out.sort(key=lambda x: (-len(x[2]["explicit"]), -len(x[2]["strict"]), x[0], x[1]))
        return out[:TOP_COLUMNS]


def key_columns(P):
    """Source A for one paper and cut: one record per coded key column."""
    recs = []
    for trait, e in P.key.items():
        if e.get("kind") != "coded":
            continue
        k, c = e["table"], e["col"]
        printed = {code: term for code, term in e["coded"].items() if e["where"].get(code) not in v1.NO_LEGEND}
        rec = {"paper": P.p, "trait": trait, "column": f"t{k}c{c}", "species": e["species"],
               "coded": len(e["coded"]), "printed": len(printed),
               "where": {code: e["where"].get(code) for code in e["coded"]}, "pairs": e["coded"]}
        if not printed:
            rec["outcome"] = "no printed pair"
            recs.append(rec)
            continue
        defining, own = [], 0
        for u in P.units:
            got = [code for code, term in printed.items() if ia.has_both(u["text"], code, term) is not None]
            if not got:
                continue
            if u["table"] == k and u["structure"] == "table row":
                own += 1
                continue
            defining.append((u, got))
        defining.sort(key=lambda x: (-len(x[1]), -li.shape_hits(x[0]["text"]), x[0]["id"]))
        rec["own_table_rows_printing"] = own
        rec["defining_units"] = len(defining)
        linked = P.linked.get((k, c), set())
        cov = [(u, got) for u, got in defining if u["id"] in linked]
        rec["linked_units"] = [uid(P.by_id[i]) for i in sorted(linked)][:10]
        rec["linked_defining"] = [uid(u) for u, _g in cov]
        got_all = sorted({code for _u, got in cov for code in got})
        rec["pairs_covered"] = got_all
        if cov:
            rec["outcome"] = "covered" if len(got_all) == len(printed) else "covered, some pairs in no linked unit"
        elif defining:
            rec["outcome"] = "missed"
        else:
            rec["outcome"] = "no defining unit" + (" (only its own table's rows print pairs)" if own else "")
        traced = defining[:TOP_UNITS] if rec["outcome"] != "covered" else cov[:1]
        rec["traces"] = [dict(P.trace(u, k, c), unit=uid(u), structure=u["structure"], pairs_in_unit=got,
                              shapes=li.shape_hits(u["text"]), text=flat(u["text"])[:400])
                         for u, got in traced]
        recs.append(rec)
    return recs


def named_cases():
    """[(source, paper, structure, text, (table, row) of a table unit or None, [targets (k, c)], note)]"""
    g = json.loads(CALIB.read_text(encoding="utf-8"))
    out = []
    for u in g["units"]:
        if u.get("missed_targets"):
            m = re.fullmatch(r".+#t(\d+)r(\d+).*", u["uid"])
            out.append(("calibration missed target", u["paper"], u["structure"], u["text"],
                        (int(m.group(1)), int(m.group(2))) if m else None,
                        [(t["table"], t["col"]) for t in u["missed_targets"]],
                        u["uid"] + ": " + "; ".join(t.get("note", "") for t in u["missed_targets"])[:200]))
    for x in g["selector_unit_misses"]:
        out.append(("calibration unit never proposed", x["paper"], x["structure"], x["text_starts"], None, [],
                    x.get("note", "")))
    for p, needle in ts.NEEDLES:
        out.append(("restored by the safe strip", p, None, needle, None, [], "needle of tag_strip_check"))
    return out


def find_needle(P, structure, text, at):
    """at: (table, row) of a table unit, else None."""
    if at:
        u = next((x for x in P.units if (x["table"], x["row"]) == at and x["structure"] == structure), None)
        if u is not None and flat(u["text"])[:60] == flat(text)[:60]:
            return u
    u = P.find(structure, text, at[0] if at else None)
    if u is None:
        n = flat(text)
        u = next((x for x in P.units if n in flat(x["text"])), None)
    return u


def named(P, case):
    source, p, structure, text, at, targets, note = case
    u = find_needle(P, structure, text, at)
    rec = {"source": source, "paper": p, "note": note, "needle": flat(text)[:80]}
    if u is None:
        rec["unit"] = None
        return rec
    rec.update(unit=uid(u), structure=u["structure"], shapes=li.shape_hits(u["text"]), text=flat(u["text"])[:700],
               inventory_unit=u["table"] is None and li.shape_hits(u["text"]) >= 2)
    rec["targets"] = [dict(P.trace(u, k, c), column=f"t{k}c{c}") for k, c in targets]
    rec["other_columns"] = [dict(tr, column=f"t{k}c{c}") for k, c, tr in P.candidates(u, exclude=set(targets))]
    rec["linked"] = sorted(f"t{k}c{c}" for i, k, c in P.sel if i == u["id"])
    return rec


def fmt_trace(tr, pad="        "):
    s = (f"{pad}{'SELECTED' if tr['selected'] else 'not selected'}; first failing gate: {tr['first']}"
         + (f" (also: {'; '.join(tr['fails'][1:])})" if len(tr["fails"]) > 1 else "")
         + f"\n{pad}header {tr['header']!r}{' [taxon header]' if tr['taxon'] else ''}; "
         f"{'enumerated' if tr['enumerated'] else 'NOT enumerated'}; {tr['n_values']} values {tr['values'][:10]}"
         f"\n{pad}codes {tr['codes'][:12]}; in the unit {tr['hit']} (strict {tr['strict']}), distinctive "
         f"{tr['distinctive']}, header words {tr['words']}{' (dropped)' if tr['words'] != tr['words_used'] else ''}, "
         f"next to a meaning {tr['explicit']}")
    return s


def report(A, B, agree, papers, skipped, stamp):
    L = [f"R3abc missed-target diagnosis, {len(papers)} tuning papers, old cut (production text) and safe cut "
         f"(dk.SAFE_TAGS); no model calls; R3abc frozen",
         f"{len(skipped)} papers have no coded key column and no named case and are not traced", "",
         "trace agreement with la.variant: " + ", ".join(f"{cut} {agree[cut]} disagreements" for cut, _s in CUTS), ""]
    L += ["A. GT-ANCHORED: CODED COLUMNS OF THE DECODING KEY (condition 2 verified by the key)", ""]
    for cut, _s in CUTS:
        rs = A[cut]
        oc = collections.Counter(r["outcome"] for r in rs)
        sp = collections.Counter()
        for r in rs:
            sp[r["outcome"]] += r["species"]
        L.append(f"  {cut} cut: {len(rs)} coded key columns in {len({r['paper'] for r in rs})} papers")
        for o in ("covered", "covered, some pairs in no linked unit", "missed", "no defining unit",
                  "no defining unit (only its own table's rows print pairs)", "no printed pair"):
            if oc[o]:
                L.append(f"    {o:58s} {oc[o]:3d} columns {sp[o]:5d} species")
        first = collections.Counter(r["traces"][0]["first"] for r in rs if r["outcome"] == "missed" and r["traces"])
        L.append("    missed columns by the first failing gate of their best defining unit: "
                 + "; ".join(f"{g} {n}" for g, n in first.most_common()))
        L.append("")
    old = {(r["paper"], r["column"], r["trait"]): r for r in A["old"]}
    L.append("  old -> safe, columns whose outcome changes:")
    for r in A["safe"]:
        o = old.get((r["paper"], r["column"], r["trait"]))
        if o and o["outcome"] != r["outcome"]:
            L.append(f"    {r['paper']} {r['column']} {r['trait']!r}: {o['outcome']} -> {r['outcome']}")
    L.append("")
    L.append("  safe cut, every column not covered (best defining units traced):")
    for r in sorted(A["safe"], key=lambda r: (r["outcome"], r["paper"], r["column"])):
        if r["outcome"] in ("covered", "no printed pair"):
            continue
        L.append(f"  - {r['paper']} {r['column']} {r['trait']!r} [{ls.SPLIT.get(r['paper'])}]: {r['outcome']}; "
                 f"{r['species']} species; printed {r['printed']} of {r['coded']} coded pairs; defining units "
                 f"{r.get('defining_units', 0)}; own-table rows printing pairs {r.get('own_table_rows_printing', 0)}")
        L.append(f"      pairs {dict(list(r['pairs'].items())[:8])}")
        L.append(f"      where {dict(list(r['where'].items())[:8])}")
        L.append(f"      R3abc links the column to {r.get('linked_units') or 'no unit'}; covered pairs "
                 f"{r.get('pairs_covered') or 'none'}")
        for tr in r.get("traces", []):
            L.append(f"      unit {tr['unit']} [{tr['structure']}, {tr['shapes']} shapes] prints {tr['pairs_in_unit']}: "
                     f"{tr['text'][:240]!r}")
            L.append(fmt_trace(tr))
    L.append("")
    L.append("  safe cut, covered columns: " + "; ".join(
        f"{r['paper']} {r['column']} via {r['linked_defining'][:2]}" for r in A["safe"] if r["outcome"] == "covered"))
    L += ["", "B. NAMED CASES OUTSIDE THE KEY (condition 2 by eye from the listed values)", ""]
    for cut, _s in CUTS:
        L.append(f"  --- {cut} cut ---")
        for r in B[cut]:
            L.append(f"  - [{r['source']}] {r['paper']} {r['needle']!r}")
            if r.get("unit") is None:
                L.append("      no unit holds it")
                continue
            L.append(f"      unit {r['unit']} [{r['structure']}, {r['shapes']} shapes"
                     f"{', an inventory unit' if r['inventory_unit'] else ''}]; R3abc links {r['linked'] or 'nothing'}")
            L.append(f"      {r['text'][:500]!r}")
            for tr in r["targets"]:
                L.append(f"      target {tr['column']}:")
                L.append(fmt_trace(tr))
            for tr in r["other_columns"]:
                L.append(f"      column sharing codes {tr['column']}:")
                L.append(fmt_trace(tr))
        L.append("")
    (OUT / f"SELECTOR_MISSES_{stamp}.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    return L


def main(papers):
    OUT.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y-%m-%d")
    head = fr.head_runs()
    cases = named_cases()
    named_papers = {c[1] for c in cases}
    A, B, agree = {}, {}, {}
    for cut, safe in CUTS:
        A[cut], B[cut], agree[cut] = [], [], 0
    skipped = []
    for p in papers:
        if p not in head:
            continue
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                coded = any(e.get("kind") == "coded" for e in dk.build_key(p)[0].values())
        except Exception:
            coded = False
        if not coded and p not in named_papers:
            skipped.append(p)                            # no coded key column and no named case: nothing to trace
            continue
        names = la.organism_names(p, head)
        for cut, safe in CUTS:
            t0 = time.time()
            P = Paper(p, safe, head, names)
            kc = key_columns(P)
            A[cut] += kc
            agree[cut] += P.agreement()
            for case in cases:
                if case[1] == p:
                    B[cut].append(named(P, case))
            print(f"  {p:22s} {cut:4s} {len(kc)} coded key columns, {len(P.sel)} R3abc links, "
                  f"{time.time() - t0:.0f}s", flush=True)
    (OUT / f"selector_misses_{stamp}.json").write_text(
        json.dumps({"A": A, "B": B, "agreement": agree, "skipped": skipped}, indent=1, ensure_ascii=False),
        encoding="utf-8")
    print("\n".join(report(A, B, agree, papers, skipped, stamp)))


if __name__ == "__main__":
    main(sys.argv[1:] or ls.tuning_papers())
