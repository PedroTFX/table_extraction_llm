"""
legend_ablation.py — R3 feature ablation (2026-11-24, after the review of legend_coverage.py's audit). NO MODEL CALLS.

R3 (legend_coverage.py) is the fixed baseline: units and columns as there, a body row of the column's own table never
a candidate, table rows repeated for one column (more than MAX_REPEAT rows of a table) treated as data. Three general
evidence features, each alone and all together; each variant is R3 recomputed with it, the repeat rule included:

  a  explicit evidence: at least one of the column's codes printed next to a meaning in the unit — code then a
     delimiter then a word ('1: diurnal', 'G= Ground-nesting', '1) underdeveloped', '1. Autumn', 'Hu-Sphagnum',
     'Lc | lichen'), '(code) word' or 'word (code)'. The number of such codes is kept: 2 or more is strong
     evidence; one is a separate, recorded path (a single explicit pair, often a distinctive code)
  b  numeric code boundaries: a number counts as a code only when no letter, digit, point or comma comes before it,
     or, glued to a letter, when an enumeration delimiter and a space follow ('predators3. hyper' counts; 'sp1',
     'sp4.MEX02' do not). The inventory's own check (experiment A) is a different job and is not changed here
  c  taxon headers: a column whose header names an organism the paper's organism columns list (the frozen run's
     tags: the organism column and columns tagged verbatimIdentification; a header that is a listed name, or starts
     with a listed genus and goes on) gives no header words as anchors. No list of name endings is used

Reported per variant: candidate units, new to the inventory, associations, gemma batches, units by structure, why
each association survived (distinctive code / >= 2 explicit / 1 explicit / codes + header word only), and the
controls: known positives (the unit and its right target column kept) and known negatives (the unit dropped).
The controls are a check; the corpus counts are the measure. A seeded sample of the combined variant, with the
reason each association survived, is written for labelling.

    python legend_ablation.py [papers]      (tuning papers by default)
-> TREE_OUTPUT/legend_coverage/ABLATION.txt, ablation_sample.csv
"""
from __future__ import annotations

import collections
import contextlib
import csv
import io
import json
import math
import random
import re
import sys

import _paths
import full_run_v24 as fr
import header_tree as ht
import header_tree_bench as hb
import legend_coverage as lc
import legend_inventory as li
import legend_scope as ls

OUT = lc.OUT
MAX_REPEAT = lc.MAX_REPEAT
VARIANTS = {"R3": "", "R3a": "a", "R3b": "b", "R3c": "c", "R3abc": "abc"}
NUM_STRICT = re.compile(r"(?<![\w.,])(\d{1,2})(?![\d])|(?<=[A-Za-z])(\d{1,2})(?=[.):]\s)")
DELIM = r"\s*(?:[=:–—)|]|\.(?=\s)|,(?=\s)|-(?=[A-Za-z]))\s*"
MEANING = r"[A-Za-z][A-Za-z'’-]{2,}"
# positives: (paper, text in the unit, word in the right target column's header); negatives: (paper, text in the unit)
POSITIVE = [("Uemori2022", "herbivorous2.", "trophic"), ("Tonelli2021", "Zigum (1:", "zigum"),
            ("Tonelli2021", "zygum is the central", "zigum"), ("Kratschmer2019", "G= Ground-nesting", "nest")]
NEGATIVE = [("Vidal2023", "between 0 and 41"), ("Noriega2023", "Ataenius_sp1.MEX02"),
            ("MacDonald2021", "Three hypotheses, each"), ("Scalercio2020", "Populations inhabiting Mediterranean"),
            ("Uemori2021", "Department of Agro-environmental")]


def explicit_codes(text, col):
    """The column's codes printed next to a meaning in the text."""
    out = []
    for c, kind in col["codes"].items():
        e = re.escape(c)
        left = r"(?<![\w.,])" if kind == "numeric" else r"(?<![A-Za-z0-9_])"
        glued = rf"(?<=[A-Za-z]){e}(?=[.):]\s)" if kind == "numeric" else None
        pats = [rf"{left}{e}{DELIM}{MEANING}", rf"\(\s*{e}\s*\)\s*{MEANING}", rf"{MEANING}\s*\(\s*{e}\s*\)"]
        if glued:
            pats.append(rf"{glued}{DELIM}{MEANING}")
        if any(re.search(p, text) for p in pats):
            out.append(c)
    return out


def organism_names(paper, head):
    """Lowercased names in the frozen run's organism columns (and columns tagged verbatimIdentification)."""
    names = set()
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            plan = fr.base_plan(paper, head)
    except Exception:
        return names
    for t, fields, org, _x in plan:
        cols = {org} | {h for h, tag in fields.items() if tag == "verbatimIdentification"}
        for rec in t.records:
            for h in cols:
                v = " ".join(str(rec.get(h, "") or "").replace("_", " ").split()).lower()
                if v:
                    names.add(v)
    return names


def is_taxon_header(header, names, genera):
    h = " ".join(re.sub(r"\(.*?\)", " ", header.split(" / ")[-1]).replace("_", " ").split()).lower()
    if not h:
        return False
    toks = h.split()
    return h in names or (len(toks) >= 2 and toks[0] in genera)


def features(papers):
    head = fr.head_runs()
    rows, per_paper, texts = [], {}, {}
    for p in papers:
        if p not in head:
            continue
        grids = {k: ht.grid_from_html(h) for k, h in enumerate(hb.html_tables(p))}
        first = {e["table"]: e.get("first") or 1 for e in head[p]}
        cols = lc.columns(p, grids, first)
        names = organism_names(p, head)
        genera = {n.split()[0] for n in names if len(n.split()) >= 2}
        for col in cols:
            col["taxon"] = is_taxon_header(col["header"], names, genera)
        us = lc.units(p, grids, first)
        f = li.OUT / f"{p}.json"
        inv_texts = [" ".join(u["text"].split()) for u in json.loads(f.read_text(encoding="utf-8"))["units"]] \
            if f.exists() else []
        for u in us:
            letters, nums, stems = lc.tokens(u["text"])
            strict = {str(int(m.group(1) or m.group(2))) for m in NUM_STRICT.finditer(u["text"])}
            t = " ".join(u["text"].split())
            inv = None
            for col in cols:
                if u["table"] == col["table"] and u["structure"] == "table row":
                    continue
                hit, dist, words = lc.associate(u, (letters, nums, stems), col)
                if not (dist or (len(hit) >= 2 and words)):
                    continue                     # not R2: no variant can take it
                hit_s = [c for c in hit if col["codes"][c] != "numeric" or c in strict]
                exp = explicit_codes(t, col)
                if inv is None:
                    inv = any(t in x for x in inv_texts)
                    texts[(p, u["id"])] = t[:500]
                rows.append({"paper": p, "unit": u["id"], "structure": u["structure"], "unit_table": u["table"],
                             "unit_row": u["row"], "table": col["table"], "col": col["col"], "header": col["header"][:120],
                             "hit": hit, "hit_strict": hit_s, "dist": dist, "words": words,
                             "taxon": col["taxon"], "explicit": [c for c in exp if c in hit],
                             "explicit_strict": [c for c in exp if c in hit_s], "in_inventory": inv, "chars": len(t)})
        per_paper[p] = len(us)
        print(f"  {p:22s} {len(us)} units, {len(cols)} columns ({sum(c['taxon'] for c in cols)} taxon headers)", flush=True)
    return rows, per_paper, texts


def variant(rows, flags):
    """The associations a variant keeps, each with the reason it survived."""
    keep = []
    for r in rows:
        hit = r["hit_strict"] if "b" in flags else r["hit"]
        exp = r["explicit_strict"] if "b" in flags else r["explicit"]
        words = [] if ("c" in flags and r["taxon"]) else r["words"]
        dist = [c for c in r["dist"] if c in hit]
        if not (dist or (len(hit) >= 2 and words)):
            continue
        if "a" in flags and not exp:
            continue
        why = ("distinctive code" if dist and not exp else ">= 2 explicit" if len(exp) >= 2
               else "1 explicit" if exp else "codes + header word")
        keep.append(dict(r, why=why))
    rep = collections.Counter((r["paper"], r["unit_table"], r["table"], r["col"]) for r in keep
                              if r["structure"] == "table row")
    return [r for r in keep if not (r["structure"] == "table row"
                                    and rep[(r["paper"], r["unit_table"], r["table"], r["col"])] > MAX_REPEAT)]


def controls(keep, texts):
    pos = []
    for p, needle, word in POSITIVE:
        hits = [r for r in keep if r["paper"] == p and needle in texts[(p, r["unit"])]]
        right = [r for r in hits if word in r["header"].lower()]
        pos.append(f"{p} '{needle}': {'kept' if hits else 'DROPPED'}"
                   + (f", right target {'kept' if right else 'MISSING'}" if hits else ""))
    neg = [f"{p} '{needle}': {'KEPT' if any(r['paper'] == p and needle in texts[(p, r['unit'])] for r in keep) else 'dropped'}"
           for p, needle in NEGATIVE]
    return pos, neg


def main(papers):
    OUT.mkdir(parents=True, exist_ok=True)
    rows, per_paper, texts = features(papers)
    L = [f"R3 feature ablation, {len(per_paper)} papers, {sum(per_paper.values())} units; no model calls", ""]
    L.append(f"  {'variant':7s} {'units':>6s} {'new':>6s} {'assoc':>7s} {'batches':>7s}   by structure (units)")
    kept = {}
    for name, flags in VARIANTS.items():
        k = variant(rows, flags)
        kept[name] = k
        uniq = {(r["paper"], r["unit"]): r for r in k}
        new = [r for r in uniq.values() if not r["in_inventory"]]
        chars = collections.defaultdict(int)
        for r in new:
            chars[r["paper"]] += r["chars"] + 12
        batches = sum(math.ceil(v / li.BATCH_CHARS) for v in chars.values())
        st = collections.Counter(r["structure"] for r in uniq.values())
        L.append(f"  {name:7s} {len(uniq):6d} {len(new):6d} {len(k):7d} {batches:7d}   "
                 + ", ".join(f"{s} {st[s]}" for s in ("prose", "caption", "numbered list", "head cell", "footnote",
                                                       "table row")))
    for name in VARIANTS:
        k = kept[name]
        why = collections.Counter(r["why"] for r in k)
        pos, neg = controls(k, texts)
        papers_with = len({r["paper"] for r in k})
        L += ["", f"{name}: associations by why they survived: " + ", ".join(f"{w} {v}" for w, v in why.most_common())
              + f"; papers with candidates {papers_with}",
              "  positives: " + "; ".join(pos), "  negatives: " + "; ".join(neg)]
    k = kept["R3abc"]
    L += ["", "R3abc by paper (units, new, associations):"]
    pp = collections.defaultdict(lambda: [set(), set(), 0])
    for r in k:
        pp[r["paper"]][0].add(r["unit"])
        if not r["in_inventory"]:
            pp[r["paper"]][1].add(r["unit"])
        pp[r["paper"]][2] += 1
    for p in sorted(pp, key=lambda p: -len(pp[p][0])):
        L.append(f"  {p:22s} [{ls.SPLIT.get(p)}] {len(pp[p][0]):5d} {len(pp[p][1]):5d} {pp[p][2]:6d}")
    (OUT / "ABLATION.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    rnd = random.Random(lc.SEED)
    sample = []
    for s in ("prose", "caption", "numbered list", "head cell", "footnote", "table row"):
        pool = list({(r["paper"], r["unit"]): r for r in k if r["structure"] == s and not r["in_inventory"]}.values())
        sample += rnd.sample(pool, min(lc.SAMPLE_PER_STRUCTURE, len(pool)))
    with open(OUT / "ablation_sample.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["n", "paper", "structure", "unit_table", "unit_row", "target_table", "target_col", "target_header",
                    "why", "codes", "explicit", "header_words", "text", "is_definition", "defined_variable",
                    "matches_target"])
        for i, r in enumerate(sample, 1):
            w.writerow([i, r["paper"], r["structure"], r["unit_table"], r["unit_row"], r["table"], r["col"],
                        r["header"], r["why"], " ".join(r["hit_strict"]), " ".join(r["explicit_strict"]),
                        " ".join(r["words"]), texts[(r["paper"], r["unit"])][:400], "", "", ""])
    print(f"sample: {len(sample)} units -> {OUT / 'ablation_sample.csv'}")


if __name__ == "__main__":
    main(sys.argv[1:] or ls.tuning_papers())
