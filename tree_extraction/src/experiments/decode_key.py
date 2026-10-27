"""
decode_key.py — AUDIT (code only, no model): the decoding answer key, read off the GT,
and production's decoding scored against it from its stored outputs.

1. KEY. For a GT row (species S, trait T, value V) and the table cell of S in the
   column that holds T, the pair (cell -> V) is how the curators decoded that cell.
   A column holds T when, over >= 3 species, each distinct cell maps to one GT value
   (>= 85% consistent). Columns where cell == V almost always are PLAIN columns (the
   key for 'keep as printed'); columns where some cell != V are CODED columns, and
   their pairs are the column's legend ('SO' -> 'solitary').
2. WHERE each legend pair lives in the paper (normalised text: markdown escapes,
   HTML and emphasis removed): a dictionary table (a row holding the code and the
   term), a definition shape ('SO: term', '(SO) term', 'term (SO)', '*SO* term',
   'SO - term', 'SO, term'), code and term in one sentence, the term only (prose
   with no code next to it), or not in the paper at all. 'near the table' when the
   passage sits within the table's caption/footnote span.
3. PRODUCTION (stored output/<paper>/<paper>.csv): for each key pair, the species'
   output row for that column is decoded right / left as the code / given another
   value / missing; for plain columns, kept as printed or changed.

    python decode_key.py
-> tree_extraction/output/decode_key/{key.json, DECODE_AUDIT.txt}
"""

from __future__ import annotations

import collections
import csv
import html as _html
import json
import re

import _paths
import column_role_bench as crb
import header_tree as ht
import header_tree_bench as hb
from evaluate import load_xlsx

OUT = _paths.OUTPUT / "decode_key"
PROD = _paths.REPO / "output"
MIN_SPECIES = 3
# read by eye (2026-10-12): columns the rules accept that are not legends
# keys: (paper, table), (paper, table, col) or (paper, table, col, trait)
NOT_LEGENDS = {("Guareschi2015", 3): "a 0-3 affinity-score matrix (fuzzy coding), not codes",
               ("Tonelli2021", 3): "a family column that lines up with traits",
               ("Odanaka2019", 7): "two neighbouring columns that line up",
               # read by eye on the --all key (2026-10-12)
               ("Fondjo2024", 2): "specimen numbers / places / dates / authors line up with descriptions",
               ("Fondjo2024", 3): "same", ("Fondjo2024", 4): "same",
               ("Hill2024", 0): "colours line up with measurements",
               ("Penick2017", 0): "numbers line up with other numbers",
               ("Lichtenberg2017", 1): "numbers with superscripts line up with other numbers",
               ("Araujo2021", 3, 4): "a neighbouring column (nest material) lines up",
               ("Eckert2023", 6, 2): "a proxy (antenna length) lines up with habitat position",
               ("Viza2023", 5, 7): "'x' marks of a month grid",
               ("Fiedler2021", 6): "0/1 region columns and counts line up by chance (7 species)",
               ("Cajaiba2023", 8, 6): "case/hyphen differences only, not codes",
               ("Wallon2024", 34, 15): "spacing differences only ('ReddishBrown'), not codes",
               ("Cao2024", 7, 1, "Mentum ratio"): "a second trait read from the same code (M2...M11)",
               ("Lizee2016", 6, 3): "univoltine/bivoltine swapped between table and GT: a GT question"}


def not_legend(paper, k, c, trait):
    return any(key in NOT_LEGENDS for key in ((paper, k), (paper, k, c), (paper, k, c, trait)))
CONSISTENT = 0.85


def clean(text):
    """Normalise paper text for searching: HTML, markdown escapes and emphasis."""
    t = re.sub(r"<[^>]+>", " ", text)
    t = _html.unescape(t)
    t = t.replace("\\_", "_").replace("\\*", "*")
    t = re.sub(r"(?<!\w)[*_]{1,2}([^*_\n]{1,60}?)[*_]{1,2}(?!\w)", r"\1", t)   # *C* -> C
    return re.sub(r"[ \t]+", " ", t)


def n(s):
    return crb.norm(str(s or ""))


def table_spans(raw):
    """(start, end) of each <table> in the raw md, to find captions/footnotes."""
    return [(m.start(), m.end()) for m in re.finditer(r"<table.*?</table>", raw, flags=re.S | re.I)]


def code_shaped(cell):
    """A cell that can be a code: short, not a decimal measurement, not a
    reference with a year."""
    c = cell.strip()
    if not c or len(c) > 25 or re.search(r"(1[89]|20)\d\d", c):
        return False
    if re.search(r"(idae|inae|ini|oidea)", c, flags=re.I):
        return False                                     # a taxon (Dorylinae), not a code
    if re.fullmatch(r"-?\d+[.,]\d+", c) and not re.fullmatch(r"-?\d+[.,]0+", c):
        return False                                     # 42.4 is a measurement; 1.0 can be a code
    return True


def is_list(cell, values):
    """'Arboreal/ Geophilous' when each part is one of the species' GT values."""
    parts = [p for p in re.split(r"\s*[/,;+&]\s*|\s+and\s+", cell) if p.strip()]
    vs = {n(v) for v in values}
    return len(parts) > 1 and all(n(p) in vs for p in parts)


def build_key(paper):
    gp = crb.paper_inputs(_paths.PAPERS / paper)
    rows = load_xlsx(gp[1])
    gt = crb.GroundTruth(rows)
    by = collections.defaultdict(list)                   # (species id, trait) -> [values]
    for r in rows:
        rid = gt.match_id(str(r.get("verbatimIdentification", "")))
        if rid and str(r.get("measurementValue") or "").strip():
            by[(rid, str(r.get("measurementType") or "").strip())].append(str(r["measurementValue"]).strip())
    traits = {t for _rid, t in by}
    grids = {k: ht.grid_from_html(h) for k, h in enumerate(hb.html_tables(paper))}
    found = {}                                           # trait -> best column entry
    for k, g in grids.items():
        obs = collections.defaultdict(list)              # col -> [(species id, cell)]
        for r in range(g.nrows):
            texts = {c: " ".join(str(g.at(r, c).text or "").split()) for c in range(g.ncols) if g.at(r, c)}
            ids = {gt.match_id(t) for t in texts.values()} - {None}
            if len(ids) != 1:
                continue
            rid = ids.pop()
            for c, t in texts.items():
                if t and not gt.match_id(t):
                    obs[c].append((rid, t))
        for c, pairs in obs.items():
            cells = {n(t) for _r, t in pairs}
            if not cells or len(cells) > 25:
                continue
            for T in traits:
                pv = [(t, by[(rid, T)]) for rid, t in pairs if (rid, T) in by]
                if len({rid for rid, _t in pairs if (rid, T) in by}) < MIN_SPECIES:
                    continue
                lists = [(t, vs) for t, vs in pv if is_list(t, vs)]
                pv = [(t, vs) for t, vs in pv if not is_list(t, vs)]
                if len(pv) < MIN_SPECIES:
                    continue
                maj = {}
                for t, vs in pv:                         # the cell's most common GT value
                    maj.setdefault(t, collections.Counter()).update(vs)
                legend = {t: cnt.most_common(1)[0][0] for t, cnt in maj.items()}
                agree = sum(legend[t] in vs for t, vs in pv) / len(pv)
                base = collections.Counter(v for _t, vs in pv for v in vs).most_common(1)[0][1] /                     sum(len(vs) for _t, vs in pv)       # guessing the trait's commonest value
                if agree < CONSISTENT:
                    continue
                if len(set(map(n, legend.values()))) < 2 and any(n(t) != n(v) for t, v in legend.items()):
                    continue                             # every code -> one term: not a legend
                if any(n(t) != n(v) for t, v in legend.items()) and agree - base < 0.15:
                    continue                             # no better than the commonest value
                coded = {t: v for t, v in legend.items() if n(t) != n(v)}
                if coded:
                    support = collections.Counter(t for t, _vs in pv)
                    if not all(code_shaped(t) for t in coded) or len(legend) > 15 or                             sum(support[t] >= 2 for t in legend) < 2:
                        continue                         # not a legend: measurements, references, one-offs
                    if len(set(map(n, legend.values()))) < 0.75 * len(legend):
                        continue                         # many codes -> few terms: a score or a proxy, not a legend
                entry = {"table": k, "col": c, "trait": T, "species": len(pv), "agree": round(agree, 3),
                         "legend": legend, "coded": coded, "lists": len(lists),
                         "kind": "coded" if coded else "plain"}
                if coded and not_legend(paper, k, c, T):
                    continue
                entry["gain"] = round(agree - base, 3)
                if T not in found or (entry["gain"], entry["species"]) > (found[T]["gain"], found[T]["species"]):
                    found[T] = entry
    return found, grids


DEF_SHAPES = [
    ("CODE: term / CODE = term", r"(?<![\w]){c}\s*[:=]\s*{t}"),
    ("(CODE) term", r"\(\s*{c}\s*\)\s*{t}"),
    ("term (CODE)", r"{t}\s*\(\s*{c}\s*\)"),
    ("CODE – term", r"(?<![\w]){c}\s*[-–—]\s*{t}"),
    ("CODE, term", r"(?<![\w]){c}\s*,\s*{t}"),
    ("CODE term", r"(?<![\w]){c}\s+{t}"),
]


BINARY_TERMS = {"yes", "no", "y", "n", "present", "absent", "true", "false"}


def where(code, term, text, raw, grids, table_k, spans):
    """Where the paper defines code -> term (first match wins).
    A 0/1 code whose GT term is yes/no counts as printed only in a definition shape
    ('1 = yes', '(1) yes'): 'no' and '0' share some sentence in almost any paper, so
    'same sentence' / 'term only' there is chance, and the GT's yes/no is a curator
    convention (correction 2026-10-12, after decoder v1's held-out run)."""
    c, t = re.escape(code), re.escape(term)
    binary = n(term) in BINARY_TERMS and re.fullmatch(r"-?\d+(?:[.,]0+)?", code.strip())
    for k, g in grids.items():                           # a dictionary table row:
        if k == table_k or g.ncols > 4:                  # another, small table
            continue
        for r in range(g.nrows):
            cells = [n(g.at(r, cc).text) for cc in range(g.ncols) if g.at(r, cc)]
            if n(code) in cells and any(n(term) in x and x != n(code) for x in cells):
                return "dictionary table", k
    for name, pat in DEF_SHAPES:
        m = re.search(pat.format(c=c, t=t), text, flags=re.I)
        if m:
            return f"definition: {name}", m.start()
    if binary:
        return "not in the paper (binary convention)", None
    for sent in re.split(r"(?<=[.!?])\s+|\n", text):
        if re.search(rf"(?<![\w]){c}(?![\w])", sent) and re.search(t, sent, flags=re.I):
            return "same sentence", text.find(sent)
    m = re.search(t, text, flags=re.I)
    if m:
        return "term only (prose)", m.start()
    return "not in the paper", None


def production(paper):
    f = PROD / paper / f"{paper}.csv"
    if not f.exists():
        return None
    rows = list(csv.DictReader(open(f, encoding="utf-8")))
    if not rows:
        return []
    kt = next(k for k in rows[0] if "measurementType" in k)
    kv = next(k for k in rows[0] if "measurementValue" in k)
    ki = next(k for k in rows[0] if "verbatimIdentification" in k)
    return [(r[ki], r[kt], r[kv]) for r in rows]


def score_production(paper, found, grids):
    prod = production(paper)
    if prod is None:
        return None
    gt = crb.GroundTruth(load_xlsx(crb.paper_inputs(_paths.PAPERS / paper)[1]))
    by_sp = collections.defaultdict(list)
    for sp, typ, val in prod:
        rid = gt.match_id(sp)
        if rid:
            by_sp[rid].append((typ, val))
    res = []
    for T, e in found.items():
        g = grids[e["table"]]
        header = " ".join(str(g.at(r, e["col"]).text or "") for r in range(min(3, g.nrows))
                          if g.at(r, e["col"]))
        for r in range(g.nrows):
            x = g.at(r, e["col"])
            texts = [str(g.at(r, c).text or "") for c in range(g.ncols) if g.at(r, c)]
            ids = {gt.match_id(t) for t in texts} - {None}
            if len(ids) != 1 or not x:
                continue
            rid = ids.pop()
            cell = " ".join(str(x.text or "").split())
            if cell not in e["legend"]:
                continue
            want = e["legend"][cell]
            vals = [v for _t, v in by_sp.get(rid, [])]
            if any(n(v) == n(want) for v in vals):
                outcome = "right"
            elif any(n(v) == n(cell) for v in vals):
                outcome = "left as printed" if e["kind"] == "coded" and n(cell) != n(want) else "right"
            else:
                typed = [v for t, v in by_sp.get(rid, []) if hb.name_matches(t, T) or hb.name_matches(t, header)]
                outcome = f"other value" if typed else "no row"
            res.append({"trait": T, "kind": e["kind"], "cell": cell, "want": want,
                        "coded_pair": n(cell) != n(want), "outcome": outcome})
    return res


def papers(all_papers=False):
    if not all_papers:
        return hb.default_papers()
    return sorted(d.name for d in _paths.PAPERS.iterdir() if d.is_dir() and crb.paper_inputs(d))


def main(argv=()):
    global OUT
    if "--all" in argv:
        OUT = OUT / "all"
    OUT.mkdir(parents=True, exist_ok=True)
    key, src_counts, prod_counts = {}, collections.Counter(), collections.Counter()
    detail, coded_cols, plain_cols = [], 0, 0
    per_paper = []
    for paper in papers("--all" in argv):
        if not crb.paper_inputs(_paths.PAPERS / paper):
            continue
        try:
            found, grids = build_key(paper)
        except Exception as e:                           # a paper whose GT or tables do not parse
            print(f"  {paper}: skipped ({type(e).__name__}: {e})")
            continue
        print(f"  {paper}: {sum(e['kind'] == 'coded' for e in found.values())} coded, "
              f"{sum(e['kind'] == 'plain' for e in found.values())} plain", flush=True)
        if not found:
            continue
        raw =(_paths.PAPERS / paper / f"{paper}_full.md").read_text(encoding="utf-8", errors="replace")
        text = clean(raw)
        spans = table_spans(raw)
        key[paper] = found
        for T, e in found.items():
            if e["kind"] == "plain":
                plain_cols += 1
                continue
            coded_cols += 1
            for code, term in e["coded"].items():
                w, _pos = where(code, term, text, raw, grids, e["table"], spans)
                e.setdefault("where", {})[code] = w
                src_counts[w] += 1
                detail.append(f"  {paper} t{e['table']} '{T}': '{code}' -> '{term}'  [{w}]")
        pr = score_production(paper, found, grids)
        if pr is not None:
            c = collections.Counter((p["kind"], p["coded_pair"], p["outcome"]) for p in pr)
            prod_counts.update(c)
            coded_right = c[("coded", True, "right")]
            coded_all = sum(v for (k, cp, _o), v in c.items() if k == "coded" and cp)
            if coded_all:
                per_paper.append((paper, coded_right, coded_all,
                                  c[("coded", True, "left as printed")], c[("coded", True, "other value")],
                                  c[("coded", True, "no row")]))
    (OUT / "key.json").write_text(json.dumps(key, indent=1, ensure_ascii=False), encoding="utf-8")
    pct = lambda a, b: f"{a}/{b} ({a / b:.0%})" if b else "-"
    L = [f"Decoding answer key, {len(key)} papers: {coded_cols} CODED columns (some cell != GT value), "
         f"{plain_cols} PLAIN columns (cells kept as printed)", "",
         f"where the {sum(src_counts.values())} legend pairs of the coded columns live in the paper:"]
    L += [f"  {w:34s}{v:>5d}" for w, v in src_counts.most_common()]
    cc = {o: v for (k, cp, o), v in prod_counts.items() if k == "coded" and cp}
    tot = sum(cc.values())
    L += ["", f"production (stored outputs) on coded cells — {tot} species x code cells:"]
    L += [f"  {o:34s}{pct(v, tot)}" for o, v in sorted(cc.items(), key=lambda kv: -kv[1])]
    pc = {o: v for (k, cp, o), v in prod_counts.items() if k == "plain" or not cp}
    tp = sum(pc.values())
    L += ["", f"production on plain cells (should be kept as printed) — {tp} cells:"]
    L += [f"  {o:34s}{pct(v, tp)}" for o, v in sorted(pc.items(), key=lambda kv: -kv[1])]
    L += ["", "per paper, coded cells: right / all  (left as printed, other value, no row)"]
    L += [f"  {p:20s}{pct(a, b):>16s}   ({l}, {o}, {nr})" for p, a, b, l, o, nr in sorted(per_paper, key=lambda x: x[1] / x[2])]
    L += ["", "every legend pair and where it lives:"] + detail
    (OUT / "DECODE_AUDIT.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[:60]))


if __name__ == "__main__":
    import sys
    main(sys.argv[1:])
