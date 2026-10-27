"""
legend_inventory.py — EXPERIMENT: one legend inventory per paper, built from fixed
source units, independent of which columns are decoded (2026-10-14).

Why: decoder_v2 gathered passages per decoded column, so decoding more columns changed
gemma's input and its legend list (Espinosa: 5 columns -> 'og'/'nog' found, 27/27 rows
right; 19 columns -> 'og' lost, 0/27). Here the evidence is a property of the paper.

  units    (code) the paper's source units, each kept apart with an id:
             prose paragraphs that LOOK like legends (>= 2 definition shapes: 'X = term',
             'X: term', '(X) term', 'term (X)', 'X, term;', '(C central-place …', or a
             bracketed list of categories '(oligolectic, polylectic)'),
             footnote rows of every table, every small table (<= 4 columns, 10-row pieces)
  batches  units in document order, packed into batches of <= BATCH_CHARS — the units
           are fixed, so the batches are too
  gemma    per batch: pass A (decoder v1's legend prompt), pass C (categories named
           without codes); then pass B (the category name inside each term) per paper
  checks   (code) BOUNDARY: an entry is kept only if its code and term are printed in the
           SAME unit (decoder_v2.verify_a run unit by unit) — a code in one passage is
           never paired with words of the next; the own-code strip ('G = grasses');
           each entry keeps its unit id and the unit's text is in the file

    python legend_inventory.py build [papers...]   -> output/decode_key/inventory/<paper>.json
    python legend_inventory.py units [papers...]   (code only: units and batches per paper)
"""

from __future__ import annotations

import json
import re
import sys
import time

import _paths
import decode_key as dk
import decoder as v1
import decoder_v2 as v2
import header_tree as ht
import header_tree_bench as hb
from fill_template import _drop_reference_lists

OUT = dk.OUT / "inventory"
BATCH_CHARS = 3000
TABLE_LINES = 10
CODE = r"(?:[A-Z][A-Za-z0-9_.]{0,7}|\d{1,2}(?:[.,]0)?|[a-z]{1,4})"
SHAPES = [
    re.compile(rf"(?<![\w]){CODE}\s*[=:–—]\s*[A-Za-z><˃˂\d]"),            # X = term, X: term
    re.compile(r"\(\s*[A-Za-z0-9_]{1,6}\s*\)\s*[A-Za-z]"),                 # (X) term
    re.compile(r"[a-z]{3,}\s*\(\s*(?:[A-Z][A-Za-z0-9_]{0,5}|\d)\s*\)"),    # term (X)
    re.compile(r"(?<![\w])(?:[A-Z]{1,4}|\d)\s*,\s*[a-z]{3,}[^;.]{0,60};"), # X, term;
    re.compile(r"[(,;]\s*(?:[A-Z]{1,4}|\d)\s+[a-z]{3,}"),                  # (C central-place, NC …
    re.compile(r"\(\s*[a-z]{4,}(?:\s*[,/]\s*[a-z][a-z /-]{2,}){1,}\s*\)"), # (oligolectic, polylectic)
]
MARKER = re.compile(r"\[(?:u\d+|prose|table[^\]]*|footnote[^\]]*)\]")


def shape_hits(text):
    return sum(len(p.findall(text)) for p in SHAPES)


def units(paper):
    """[{id, kind, text}] — the paper's source units, independent of any column."""
    raw = (_paths.PAPERS / paper / f"{paper}_full.md").read_text(encoding="utf-8", errors="replace")
    prose = re.sub(r"<table.*?</table>", "\n\n", _drop_reference_lists(raw), flags=re.S | re.I)
    out = []
    for p in re.split(r"\n\s*\n", dk.clean(prose)):
        t = " ".join(p.split())
        if len(t) > 3 and shape_hits(t) >= 2:
            out.append(("prose", t))
    for j, h in enumerate(hb.html_tables(paper)):
        g = ht.grid_from_html(h)
        for r in range(g.nrows):                                         # footnote rows
            filled = {id(g.at(r, c)): g.at(r, c) for c in range(g.ncols)
                      if g.at(r, c) and str(g.at(r, c).text or "").strip()}
            if len(filled) == 1:
                x = next(iter(filled.values()))
                if x.colspan >= 0.6 * g.ncols and len(x.text) > 15 and shape_hits(x.text) >= 1:
                    out.append((f"footnote of table {j}", " ".join(x.text.split())))
        if g.ncols <= 4:                                                 # small tables
            lines = []
            for r in range(g.nrows):
                cells = [" ".join(str(g.at(r, c).text).split()) for c in range(g.ncols)
                         if g.at(r, c) and (g.at(r, c).r, g.at(r, c).c) == (r, c)
                         and str(g.at(r, c).text or "").strip()]
                if cells:
                    lines.append(" | ".join(cells))
            for i in range(0, len(lines), TABLE_LINES):
                out.append((f"table {j}", "\n".join(lines[i:i + TABLE_LINES])))
    return [{"id": f"u{i}", "kind": k, "text": t} for i, (k, t) in enumerate(out)]


def batches(us):
    out, cur, size = [], [], 0
    for u in us:
        piece = len(u["text"]) + 12
        if cur and size + piece > BATCH_CHARS:
            out.append(cur)
            cur, size = [], 0
        cur.append(u)
        size += piece
    if cur:
        out.append(cur)
    return out


def render(batch):
    return "\n\n".join(f"[{u['id']}] ({u['kind']}) {u['text'][:BATCH_CHARS]}" for u in batch)


def grounded(entry, batch, uncoded=False):
    """The boundary check: the unit that prints both code and term (or, for a category
    without a code, the label as whole words). -> unit id or None (entry updated by
    verify_a when a near-miss term is replaced by the printed phrase)."""
    if MARKER.search(entry.get("term", "") + " " + entry.get("label", "")):
        return None                                                      # crossed a unit
    for u in batch:
        if uncoded:
            if v2._wb(entry["label"], u["text"]):
                return u["id"]
        else:
            e = dict(entry)
            if v2.verify_a(e, u["text"]) == "":
                entry.update(e)
                return u["id"]
    return None


def build(paper):
    us = units(paper)
    entries, cats_u, dropped, calls = [], [], [], 0
    for b in batches(us):
        text = render(b)
        calls += 1
        for e in v1.gemma(v1.ORGANISE.format(passages=text)):            # pass A
            e = {k: " ".join(str(e.get(k) or "").split()) for k in ("variable", "code", "term")}
            v2.strip_own_code(e)
            uid = grounded(e, b) if e["code"] and e["term"] else None
            (entries if uid else dropped).append({**e, "unit": uid} if uid else
                                                 {**e, "why": "not printed within one unit"})
        calls += 1
        for e in v2._chat(v2.UNCODED.format(passages=text), v2.UNCODED_SCHEMA, "categories"):  # C
            lab = " ".join(str(e.get("label") or "").split())
            c = {"variable": " ".join(str(e.get("variable") or "").split()), "code": "",
                 "label": lab, "explanation": "", "evidence": "named"}
            uid = grounded(c, b, uncoded=True) if lab and re.search(r"[^\W\d_]{3,}", lab) else None
            if uid:
                cats_u.append({**c, "unit": uid})
    seen, cats = set(), []
    for e in entries:
        k = (e["variable"].lower(), e["code"], e["term"].lower())
        if k not in seen:
            seen.add(k)
            cats.append(e)
    for i in range(0, len(cats), 40):                                    # pass B
        part = cats[i:i + 40]
        listing = "\n".join(f"{n}. \"{e['code']}\" = \"{e['term']}\"" for n, e in enumerate(part, 1))
        calls += 1
        got = {int(x.get("n", 0)): x.get("label") for x in
               v2._chat(v2.LABELS.format(entries=listing), v2.LABELS_SCHEMA, "labels") if isinstance(x, dict)}
        for n, e in enumerate(part, 1):
            e["model_label"] = got.get(n)
            e["label"], e["explanation"] = v2.label_of(e["term"], got.get(n))
    have = {e["label"].lower() for e in cats}
    for c in cats_u:
        if c["label"].lower() not in have:
            have.add(c["label"].lower())
            cats.append(c)
    return {"paper": paper, "units": us, "batches": [[u["id"] for u in b] for b in batches(us)],
            "calls": calls, "categories": cats, "dropped": dropped}


def coded_papers():
    key = v1.load_key()
    return sorted(p for p, cols in key.items() if any(e["kind"] == "coded" for e in cols.values()))


def main(argv):
    cmd, papers = argv[0], argv[1:] or coded_papers()
    if cmd == "units":
        tot = 0
        for p in papers:
            us = units(p)
            bs = batches(us)
            tot += len(bs)
            print(f"  {p:22s} {len(us):3d} units {sum(len(u['text']) for u in us):7d} chars {len(bs):3d} batches")
        print(f"{len(papers)} papers, {tot} batches -> about {tot * 2} gemma calls + pass B")
        return
    OUT.mkdir(parents=True, exist_ok=True)
    for p in papers:
        f = OUT / f"{p}.json"
        if f.exists():
            continue
        t0 = time.time()
        inv = build(p)
        inv["seconds"] = round(time.time() - t0, 1)
        f.write_text(json.dumps(inv, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  {p:22s} {len(inv['units'])} units, {inv['calls']} calls, {len(inv['categories'])} "
              f"entries, {len(inv['dropped'])} dropped ({inv['seconds']}s)", flush=True)
    v1.unload(v1.GEMMA)


if __name__ == "__main__":
    main(sys.argv[1:])
