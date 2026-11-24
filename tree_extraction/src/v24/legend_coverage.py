"""
legend_coverage.py — coverage audit of code-anchored legend discovery (2026-11-24). NO MODEL CALLS.

The hypothesis under test: a code that occurs in a table column, together with a meaningful reference to that
column's variable elsewhere in the paper, is a general anchor for finding the code's definition, whatever the
document structure that holds it. It replaces selection by legend shape or table size (the experiments A, B and C
were each shaped on one paper; the success criterion here is the whole corpus, not those three).

Columns (every table of the paper, any width). The body starts at the head reader's first record (row 1 when the
reader has no entry for the table). A column takes part when its body has 2..15 distinct values (more is a
measurement or a name column). Its codes are the values, or the parts of list cells, that look like codes:
  numeric      0..99 ('1.0' counts as 1)
  letter code  1-2 letters ('G', 'pl'); a capitalised token of 3-6 characters ('Hdisp', 'Poly'). Lowercase words of
               3+ letters ('low', 'dung') are values, not codes
  distinctive  all capitals 2-5 letters ('TG', 'NSD'), letters with digits ('M11'), an inner capital ('SeG', 'ActDay')
Its header: the head cells above the first record in the column (spanning parents included); its informative
words: 4+ letters, lowercased, a simple stem (-ing/-ed/-es/-s), minus a list of generic words (species, number, …).

Source units (every one, whatever its shape): prose paragraphs (as legend_inventory.units cuts them; 'caption' when a
paragraph starts 'Table …'/'Fig…', 'numbered list' when it holds a run 1, 2, 3 of enumerations), and for every table:
each head cell ('head cell'), a row of one wide cell ('footnote'), every other row ('table row', cells joined ' | ').

A unit-to-column association (codes matched in the unit as whole tokens; a digit may follow a letter, so a glued
enumeration 'predators3.' counts, but not inside a longer number):
  R1   a distinctive code of the column, or a code of the column + an informative word of its header
  R2   a distinctive code, or >= 2 distinct codes of the column + an informative word of its header
  R3   R2, except table rows repeated: when more than MAX_REPEAT rows of one table are R2 candidates for the same
       column, those rows are data (a definition is stated once, a pattern row after row is a data table; found in
       the first run: Noriega2023's other data tables gave 26,772 candidate rows). Other structures as R2
A body row of the column's own table is data, never a candidate for that column (Chichorro2022's in-row key); its
head cells and footnote rows stay candidates. Tables are not excluded whole.

Reported: units enumerated; unique candidate units and associations (R1, R2); by structure; by paper; units the
inventory already reads (the candidate's text inside an inventory unit); the gemma workload of the new ones (3000-
character batches, as legend_inventory.batches); a seeded verification sample for labelling by eye: does the unit
define a coding relationship (definition / data / category without a code / ambiguous), and does it belong to the
column that selected it (yes / another variable / no).

    python legend_coverage.py [papers]     (tuning papers by default)
-> TREE_OUTPUT/legend_coverage/COVERAGE.txt, candidates.json, verification_sample.csv
"""
from __future__ import annotations

import collections
import csv
import json
import math
import random
import re
import sys

import _paths
import decoder as v1
import full_run_v24 as fr
import header_tree as ht
import header_tree_bench as hb
import inventory_audit as ia
import legend_inventory as li
import legend_scope as ls

OUT = _paths.OUTPUT / "legend_coverage"
MAX_DISTINCT = 15
MAX_REPEAT = 3
BATCH = li.BATCH_CHARS
SAMPLE_PER_STRUCTURE = 12
SEED = 20261124
EMPTY = {"", "na", "nd", "n/a", "-", "–", "—", "x", "?", "+", "*", ".", "ns"}
GENERIC = {"species", "table", "number", "numbers", "value", "values", "mean", "total", "data", "with", "from", "that",
           "this", "were", "code", "codes", "column", "category", "categories", "class", "group", "groups", "index",
           "level", "levels", "other", "sample", "samples", "site", "sites", "taxa", "taxon", "name", "names", "info",
           "information", "trait", "traits", "variable", "variables", "abbreviation", "definition", "description",
           "note", "notes", "type", "types", "used", "each", "their", "when", "which", "also", "unit", "units"}
CAPTION = re.compile(r"^(?:supplementary\s+)?(?:table|fig\.?|figure)\s*s?\d", re.I)
ENUM = re.compile(r"(?<![\w.])(\d{1,2})\s*[.)]\s*[A-Za-z]")
NUM_TOKEN = re.compile(r"(?<![\d.,])(\d{1,2})(?![\d])")
WORD = re.compile(r"[A-Za-z][A-Za-z0-9_]*")


def stem(w):
    w = w.lower()
    for suf in ("ing", "ed", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 4:
            return w[: -len(suf)]
    return w


def informative(text):
    return {stem(w) for w in re.findall(r"[A-Za-z]{4,}", text)} - {stem(g) for g in GENERIC}


def code_kind(v):
    """'numeric' | 'distinctive' | 'letter' | None"""
    v = v.strip()
    if v.lower() in EMPTY:
        return None
    if re.fullmatch(r"-?\d{1,2}(?:[.,]0+)?", v):
        return "numeric"
    if re.fullmatch(r"[A-Z]{2,5}", v) or re.fullmatch(r"(?=.*\d)[A-Za-z][A-Za-z0-9]{1,5}", v) \
            or re.fullmatch(r"[A-Za-z][a-z]*[A-Z][A-Za-z]{0,6}", v):
        return "distinctive"
    if re.fullmatch(r"[A-Za-z]{1,2}", v) or re.fullmatch(r"[A-Z][a-z0-9]{2,5}", v):
        return "letter"
    return None


def norm_code(v, kind):
    return str(int(float(v.replace(",", ".")))) if kind == "numeric" else v.strip()


def columns(paper, grids, first):
    """[{table, col, header, words, codes {code: kind}}]"""
    out = []
    for k, g in grids.items():
        top = min(first.get(k, 1), g.nrows)
        for c in range(g.ncols):
            vals = set()
            for r in range(top, g.nrows):
                x = g.at(r, c)
                if x and x.c == c:
                    t = " ".join(str(x.text or "").split())
                    if t and t.lower() not in EMPTY:
                        vals.add(t)
            if not 2 <= len(vals) <= MAX_DISTINCT:
                continue
            codes = {}
            for v in vals:
                for part in v1.list_parts(v):
                    kind = code_kind(part)
                    if kind:
                        codes[norm_code(part, kind)] = kind
            if not codes:
                continue
            head = []
            for r in range(top):
                x = g.at(r, c)
                if x:
                    t = " ".join(str(x.text or "").split())
                    if t and t not in head:
                        head.append(t)
            header = " / ".join(head)
            out.append({"table": k, "col": c, "header": header, "words": informative(header), "codes": codes})
    return out


def units(paper, grids, first):
    """[{id, structure, table, row, text}] — every source unit."""
    out = []
    for p in ia.paragraphs(paper):
        s = "caption" if CAPTION.match(p) else ("numbered list" if numbered(p) else "prose")
        out.append({"structure": s, "table": None, "row": None, "text": p})
    for k, g in grids.items():
        top = min(first.get(k, 1), g.nrows)
        for r in range(g.nrows):
            cells = [g.at(r, c) for c in range(g.ncols)]
            origin = [x for c, x in enumerate(cells) if x and (x.r, x.c) == (r, c) and str(x.text or "").strip()]
            if not origin:
                continue
            if r < top:
                for x in origin:
                    out.append({"structure": "head cell", "table": k, "row": r, "col": x.c,
                                "text": " ".join(str(x.text).split())})
                continue
            filled = {id(x): x for x in cells if x and str(x.text or "").strip()}
            if len(filled) == 1 and next(iter(filled.values())).colspan >= 0.6 * g.ncols and g.ncols > 1:
                out.append({"structure": "footnote", "table": k, "row": r, "text": " ".join(str(origin[0].text).split())})
            else:
                out.append({"structure": "table row", "table": k, "row": r,
                            "text": " | ".join(" ".join(str(x.text).split()) for x in origin)})
    for i, u in enumerate(out):
        u["id"] = i
    return out


def numbered(text):
    ns = [int(m.group(1)) for m in ENUM.finditer(text)]
    run = best = 1
    for a, b in zip(ns, ns[1:]):
        run = run + 1 if b == a + 1 else 1
        best = max(best, run)
    return best >= 3 and 1 in ns


def tokens(text):
    """(letter tokens, numeric tokens, informative stems) of a unit."""
    return set(WORD.findall(text)), {str(int(m.group(1))) for m in NUM_TOKEN.finditer(text)}, informative(text)


def associate(u, tok, col):
    """-> (codes matched, distinctive matched, header words matched) for one unit and one column."""
    letters, nums, stems = tok
    hit = sorted(c for c, kind in col["codes"].items() if (c in nums if kind == "numeric" else c in letters))
    dist = [c for c in hit if col["codes"][c] == "distinctive"]
    return hit, dist, sorted(stems & col["words"])


def audit(papers):
    OUT.mkdir(parents=True, exist_ok=True)
    head = fr.head_runs()
    rows, per_paper, n_units, n_cols = [], {}, collections.Counter(), 0
    for p in papers:
        if p not in head:
            continue
        grids = {k: ht.grid_from_html(h) for k, h in enumerate(hb.html_tables(p))}
        first = {e["table"]: e.get("first") or 1 for e in head[p]}
        cols = columns(p, grids, first)
        us = units(p, grids, first)
        n_cols += len(cols)
        f = li.OUT / f"{p}.json"
        inv_texts = [" ".join(u["text"].split()) for u in json.loads(f.read_text(encoding="utf-8"))["units"]] \
            if f.exists() else []
        for u in us:
            n_units[u["structure"]] += 1
            tok = tokens(u["text"])
            for col in cols:
                if u["table"] == col["table"] and u["structure"] == "table row":
                    continue                     # a body row of the column's own table is data
                hit, dist, words = associate(u, tok, col)
                r1 = bool(dist) or (bool(hit) and bool(words))
                if not r1:
                    continue
                r2 = bool(dist) or (len(hit) >= 2 and bool(words))
                t = " ".join(u["text"].split())
                rows.append({"paper": p, "group": ls.SPLIT.get(p), "unit": u["id"], "structure": u["structure"],
                             "unit_table": u["table"], "unit_row": u["row"], "table": col["table"], "col": col["col"],
                             "header": col["header"][:120], "codes": hit, "distinctive": dist, "words": words,
                             "r2": r2, "in_inventory": any(t in x for x in inv_texts), "chars": len(t),
                             "text": t[:600]})
        per_paper[p] = {"units": len(us), "columns": len(cols)}
        print(f"  {p:22s} {len(us)} units, {len(cols)} coded-looking columns, "
              f"{len({r['unit'] for r in rows if r['paper'] == p})} candidate units", flush=True)
    rep = collections.Counter((r["paper"], r["unit_table"], r["table"], r["col"]) for r in rows
                              if r["r2"] and r["structure"] == "table row")
    for r in rows:
        r["r3"] = r["r2"] and not (r["structure"] == "table row"
                                   and rep[(r["paper"], r["unit_table"], r["table"], r["col"])] > MAX_REPEAT)
    (OUT / "candidates.json").write_text(json.dumps([r for r in rows if r["r3"]], indent=1, ensure_ascii=False),
                                         encoding="utf-8")
    report(rows, per_paper, n_units, n_cols)
    sample(rows)


def summary(rs):
    """(unique units, associations, units new to the inventory, gemma batches for the new ones)"""
    uniq = {(r["paper"], r["unit"]): r for r in rs}
    new = [r for r in uniq.values() if not r["in_inventory"]]
    by_paper = collections.defaultdict(int)
    for r in new:
        by_paper[r["paper"]] += r["chars"] + 12
    return len(uniq), len(rs), len(new), sum(math.ceil(v / BATCH) for v in by_paper.values())


def report(rows, per_paper, n_units, n_cols):
    L = [f"legend coverage audit (code-anchored candidates), {len(per_paper)} papers; no model calls", "",
         f"units enumerated {sum(n_units.values())} (" + ", ".join(f"{k} {v}" for k, v in n_units.most_common())
         + f"); columns with code-like values {n_cols}", ""]
    for name, rs in (("R1", rows), ("R2", [r for r in rows if r["r2"]]), ("R3", [r for r in rows if r["r3"]])):
        u, a, new, b = summary(rs)
        L.append(f"{name}: {u} unique candidate units, {a} unit-to-column associations; {u - new} already read by the "
                 f"inventory, {new} new -> about {b} gemma batches (~{2 * b} calls + labels)")
    L += ["", "by structure (unique units: R1 / R2 / R3; R3 new to the inventory):"]
    for s in ("prose", "caption", "numbered list", "head cell", "footnote", "table row"):
        r1 = {(r["paper"], r["unit"]) for r in rows if r["structure"] == s}
        r2 = {(r["paper"], r["unit"]) for r in rows if r["structure"] == s and r["r2"]}
        r3 = {(r["paper"], r["unit"]) for r in rows if r["structure"] == s and r["r3"]}
        r3n = {(r["paper"], r["unit"]) for r in rows if r["structure"] == s and r["r3"] and not r["in_inventory"]}
        L.append(f"  {s:14s} {len(r1):6d} / {len(r2):6d} / {len(r3):6d}   new {len(r3n):6d}   (of {n_units[s]} units)")
    L += ["", "how R3 associations were made: "
          + ", ".join(f"{k} {v}" for k, v in collections.Counter(
              "distinctive code" if r["distinctive"] else "codes + header word" for r in rows if r["r3"]).items())]
    L += ["", "by paper (R3: unique candidate units, new to the inventory, associations; units enumerated):"]
    pp = collections.defaultdict(lambda: [set(), set(), 0])
    for r in rows:
        if r["r3"]:
            pp[r["paper"]][0].add(r["unit"])
            if not r["in_inventory"]:
                pp[r["paper"]][1].add(r["unit"])
            pp[r["paper"]][2] += 1
    for p in sorted(per_paper, key=lambda p: -len(pp[p][0])):
        L.append(f"  {p:22s} [{ls.SPLIT.get(p)}] {len(pp[p][0]):5d} {len(pp[p][1]):5d} {pp[p][2]:6d}   "
                 f"({per_paper[p]['units']} units, {per_paper[p]['columns']} columns)")
    L += ["", "known cases (a check only; the corpus is the criterion):"]
    for name, needle in (("Uemori2022 glued numbered cell", "herbivorous2."), ("Tonelli2021 head cell", "Zigum (1:"),
                         ("Kratschmer2019 codebook row", "G= Ground-nesting"), ("Vidal2023 year range", "between 0 and 41")):
        hits = [r for r in rows if needle in r["text"]]
        L.append(f"  {name:32s} R1 {'yes' if hits else 'no'}, R2 {'yes' if any(r['r2'] for r in hits) else 'no'}, "
                 f"R3 {'yes' if any(r['r3'] for r in hits) else 'no'}")
    (OUT / "COVERAGE.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


def sample(rows):
    """Seeded: per structure, SAMPLE_PER_STRUCTURE R3 associations new to the inventory, for labelling by eye."""
    rnd = random.Random(SEED)
    out = []
    for s in ("prose", "caption", "numbered list", "head cell", "footnote", "table row"):
        pool = [r for r in rows if r["structure"] == s and r["r3"] and not r["in_inventory"]]
        out += rnd.sample(pool, min(SAMPLE_PER_STRUCTURE, len(pool)))
    with open(OUT / "verification_sample.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["n", "paper", "structure", "unit_table", "unit_row", "target_table", "target_col", "target_header",
                    "matched_codes", "matched_header_words", "text", "defines (definition/data/category/ambiguous)",
                    "belongs (yes/another variable/no)"])
        for i, r in enumerate(out, 1):
            w.writerow([i, r["paper"], r["structure"], r["unit_table"], r["unit_row"], r["table"], r["col"],
                        r["header"], " ".join(r["codes"]), " ".join(r["words"]), r["text"][:400], "", ""])
    print(f"verification sample: {len(out)} associations -> {OUT / 'verification_sample.csv'}")


if __name__ == "__main__":
    audit(sys.argv[1:] or ls.tuning_papers())
