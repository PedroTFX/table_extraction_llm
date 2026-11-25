"""
tag_strip_check.py — checks of dk.SAFE_TAGS, the tag strip that removes markup only (2026-11-25). NO MODEL CALLS;
nothing in the pipeline is switched: dk.SAFE_TAGS stays off by default.

  1. made-up cases: markup goes (comments, sup/sub, span and a with attributes, details/summary, br, i); every '<'
     that opens no tag stays with its text (comparisons, thresholds, LaTeX, a '<' then a blank line); no removal
     crosses a blank line. The old strip is run on the same cases to show what it deleted.
  2. the tuning papers' prose as inventory_audit.paragraphs builds it, the old strip against the safe one:
     a. no markup left after the safe strip (no comment, no HTML element's tag); tag-shaped text it keeps is listed
     b. the old text is a subsequence of the safe one (characters, whitespace ignored): the fix only keeps text
     c. a paper whose old-strip matches are all markup: the two texts are equal
     d. characters kept that the old strip deleted; paragraphs before and after
  3. regression: the six legends the boundary audit's sample found deleted (by eye, boundary_labels_2026-11-25.csv):
     each needle in a paragraph of the safe cut (required) and in none of the old cut (expected); that paragraph a
     legend_inventory unit (2+ definition shapes)? the frozen R3abc selector's links for it, old cut and safe cut
  4. the calibration units (gold v4.1, ids of the old cut) whose paragraph the safe strip changes

    python tag_strip_check.py
-> TREE_OUTPUT/legend_coverage/TAG_STRIP_CHECK_<date>.txt; exit status 1 if a required check fails
"""
from __future__ import annotations

import contextlib
import io
import json
import re
import sys
import time

import _paths
import decode_key as dk
import inventory_audit as ia
import legend_ablation as la
import legend_coverage as lc
import legend_inventory as li
import legend_scope as ls
from fill_template import _drop_reference_lists

OUT = lc.OUT
CALIB = OUT / "calib_gold_v4.1_2026-11-25.json"
TAG = re.compile(r"<(?:!--.*?--|/?[A-Za-z][A-Za-z0-9]*(?:\s[^<>]*)?/?)>", re.S)   # the boundary audit's

# (text, expected after the safe strip, whitespace collapsed): made up
CASES = [
    ("leaf area (mm<sup>2</sup>) and CO<sub>2</sub> uptake", "leaf area (mm 2 ) and CO 2 uptake"),
    ('<span id="p3-1">Body</span> length', "Body length"),
    ('<a href="https://example.org/x?id=4&amp;v=2">see the data</a>.', "see the data ."),
    ("<!-- page 3 of 9 -->Wing span", "Wing span"),
    ("<details><summary>More</summary>hidden note</details>", "More hidden note"),
    ("first<br/>second<br>third", "first second third"),
    ("<i>Genus species</i> and <strong>bold</strong>", "Genus species and bold"),
    ("significant (p < 0.05); F > 3.2", "significant (p < 0.05); F > 3.2"),
    ("<1% = rare; 1%-10% = scattered; >10% = dense", "<1% = rare; 1%-10% = scattered; >10% = dense"),
    ("x<y and z>w", "x<y and z>w"),
    ("0 < k < 1 and m > 2", "0 < k < 1 and m > 2"),
    ("$p<0.001$ and $R^2>0.5$", "$p<0.001$ and $R^2>0.5$"),
    ("patches <5 ha and >10 ha", "patches <5 ha and >10 ha"),
    ("the ratio <a/b> of lengths", "the ratio <a/b> of lengths"),
    ("a value <Ca> in the soil", "a value <Ca> in the soil"),
]
# (text, expected paragraphs after the safe strip): blank lines are never crossed
PARA_CASES = [
    ("rare: < 0.6% of the catch\n\nCodes: U: one generation, M: several\n\n<!-- page 2 of 11 -->\n\nnext",
     ["rare: < 0.6% of the catch", "Codes: U: one generation, M: several", "next"]),
    ('<span\n\nclass="x">text</span>', ["<span", 'class="x">text']),
    ("<!-- a note\n\nText --> more", ["<!-- a note", "Text --> more"]),
    ("<sup\n>2</sup> ok", ["2 ok"]),
]
# the six legends the boundary audit's tag-strip sample found deleted (boundary_labels_2026-11-25.csv)
NEEDLES = [
    ("Kratschmer2019", "1%–5% = low; 5%–25% = medium"),
    ("Oliveira2022", "CL = ratio of clypeus length to mesosoma length"),
    ("Taillefer2018", "U: univoltine, M: bivoltine"),
    ("Taillefer2018", "E: eggs, L: larvae, P: pupae, A: adults"),
    ("Ji2024", "Number of individuals (Ind; measured/collected)"),
    ("Ji2024", "six elevations (Elev.)"),
    ("Cajaiba2022", "Epigaeic predators (EP) and Epigaeic omnivores (EO)"),
    ("Viza2023", "Reduced: Axis X ≤ 10"),
]


@contextlib.contextmanager
def strip(safe):
    was = dk.SAFE_TAGS
    dk.SAFE_TAGS = safe
    try:
        yield
    finally:
        dk.SAFE_TAGS = was


def flat(t):
    return " ".join(t.split())


def prose(paper):
    raw = (_paths.PAPERS / paper / f"{paper}_full.md").read_text(encoding="utf-8", errors="replace")
    return re.sub(r"<table.*?</table>", "\n\n", _drop_reference_lists(raw), flags=re.S | re.I)


def subsequence(a, b):
    """a's characters appear in b in order."""
    it = iter(b)
    return all(ch in it for ch in a)


def cases():
    L, bad = ["1. MADE-UP CASES (safe strip | old strip)"], 0
    for text, want in CASES:
        with strip(True):
            got = flat(dk.clean(text))
        with strip(False):
            old = flat(dk.clean(text))
        ok = got == flat(want)
        bad += not ok
        L.append(f"  {'ok ' if ok else 'BAD'} {text!r}\n        safe {got!r}" + ("" if ok else f" (want {want!r})")
                 + f"\n        old  {old!r}")
    for text, want in PARA_CASES:
        with strip(True):
            got = [flat(p) for p in re.split(r"\n\s*\n", dk.clean(text)) if flat(p)]
        ok = got == want
        bad += not ok
        L.append(f"  {'ok ' if ok else 'BAD'} {text!r}\n        safe paragraphs {got!r}" + ("" if ok else f" (want {want!r})"))
    return L + [f"  {len(CASES) + len(PARA_CASES) - bad} of {len(CASES) + len(PARA_CASES)} as expected", ""], bad


def papers_check(papers):
    L = ["2. TUNING PAPERS: THE OLD STRIP AGAINST THE SAFE ONE (prose as inventory_audit.paragraphs builds it)"]
    bad, tot = 0, {"old": 0, "safe": 0, "kept": 0, "par_old": 0, "par_safe": 0, "equal": 0, "markup_only": 0}
    kept_shapes, changed = [], []
    for p in papers:
        t = prose(p)
        with strip(False):
            old_t, old_spans = dk.strip_tags(t), [(m.start(), m.end()) for m in dk.LEGACY_TAG.finditer(t)]
            old_par = ia.paragraphs(p)
        with strip(True):
            safe_t = dk.strip_tags(t)
            safe_spans = [(m.start(), m.end()) for m in dk.MARKUP.finditer(t) if dk._markup(m) == " "]
            safe_par = ia.paragraphs(p)
        left = [m.group(0) for m in dk.MARKUP.finditer(safe_t) if dk._markup(m) == " "]          # a
        shapes = [m.group(0) for m in TAG.finditer(safe_t)]
        kept_shapes += [(p, s) for s in shapes]
        a, b = re.sub(r"\s+", "", old_t), re.sub(r"\s+", "", safe_t)
        sub = subsequence(a, b)                                                                    # b
        markup_only = old_spans == safe_spans
        equal = old_t == safe_t
        problems = (["markup left " + repr(left[:3])] if left else []) + ([] if sub else ["old text not a subsequence"]) \
            + (["texts differ although every old match is markup"] if markup_only and not equal else [])      # c
        bad += bool(problems)
        tot["old"] += len(a)
        tot["safe"] += len(b)
        tot["kept"] += len(b) - len(a)
        tot["par_old"] += len(old_par)
        tot["par_safe"] += len(safe_par)
        tot["equal"] += equal
        tot["markup_only"] += markup_only
        if not equal:
            changed.append((p, len(b) - len(a), len(old_par), len(safe_par)))
        if problems:
            L.append(f"  BAD {p}: {'; '.join(problems)}")
    L += [f"  papers {len(papers)}; text unchanged {tot['equal']} (every old match markup: {tot['markup_only']}); "
          f"changed {len(changed)}",
          f"  characters (no whitespace): old {tot['old']}, safe {tot['safe']}, kept that the old strip deleted "
          f"{tot['kept']}",
          f"  paragraphs: old {tot['par_old']}, safe {tot['par_safe']} (+{tot['par_safe'] - tot['par_old']})",
          f"  required: no markup left, the old text a subsequence of the safe one, equal where the old matches are all "
          f"markup -> {'all hold' if not bad else f'{bad} papers fail'}",
          f"  tag-shaped text the safe strip keeps (no HTML element: read by eye) {len(kept_shapes)}"]
    for p, s in kept_shapes[:40]:
        L.append(f"      {p}: {s[:100]!r}")
    L.append("  papers changed (chars kept, paragraphs old -> safe):")
    for p, k, a, b in sorted(changed, key=lambda x: -x[1]):
        L.append(f"      {p:22s} {k:7d}  {a:4d} -> {b:4d}")
    return L + [""], bad


_R3 = {}


def r3abc_links(paper, safe):
    """{unit id: [columns]} the frozen R3abc selector links (a prose unit's id is its paragraph's index)."""
    if (paper, safe) not in _R3:
        with strip(safe), contextlib.redirect_stdout(io.StringIO()):
            rows, _pp, _texts = la.features([paper])
        links = {}
        for r in la.variant(rows, "abc"):
            if r["unit_table"] is None:
                links.setdefault(r["unit"], []).append(f"t{r['table']}c{r['col']} {r['header'][:40]!r}")
        _R3[(paper, safe)] = links
    return _R3[(paper, safe)]


def needles():
    L, bad = ["3. REGRESSION: THE SIX LEGENDS THE OLD STRIP DELETED (needle | old cut | safe cut)"], 0
    for p, n in NEEDLES:
        with strip(False):
            old = [i for i, x in enumerate(ia.paragraphs(p)) if n in x]
        with strip(True):
            paras = ia.paragraphs(p)
        safe = [i for i, x in enumerate(paras) if n in x]
        bad += not safe
        L.append(f"  {'ok ' if safe else 'BAD'} {p:15s} {n!r}: old cut {len(old)} paragraphs, safe cut {len(safe)}")
        for i in safe[:1]:
            x = paras[i]
            r3, r3o = r3abc_links(p, True).get(i), [r3abc_links(p, False).get(k) for k in old]
            L.append(f"        safe p{i} ({len(x)} chars, {li.shape_hits(x)} definition shapes: "
                     f"{'an inventory unit' if li.shape_hits(x) >= 2 else 'no inventory unit'}; "
                     f"{'a numbered list' if lc.numbered(x) else 'caption' if lc.CAPTION.match(x) else 'prose'})")
            L.append(f"        R3abc (frozen) links: safe cut {r3 or 'none'}; old cut "
                     f"{[v for v in r3o if v] or 'none'}")
            k = x.find(n)
            L.append(f"        ...{x[max(0, k - 120):k + len(n) + 120]!r}...")
    return L + [""], bad


def calibration():
    L = ["4. CALIBRATION UNITS (gold v4.1) WHOSE PARAGRAPH THE SAFE STRIP CHANGES"]
    units = [u for u in json.loads(CALIB.read_text(encoding="utf-8"))["units"] if u["structure"] != "table row"]
    by = {}
    for u in units:
        by.setdefault(u["paper"], []).append(u)
    n_prose, moved, changed = 0, 0, []
    for p, us in sorted(by.items()):
        with strip(False):
            old = ia.paragraphs(p)
        with strip(True):
            safe = ia.paragraphs(p)
        for u in us:
            m = re.fullmatch(r".+#p(\d+)", u["uid"])
            if not m or int(m.group(1)) >= len(old) or not old[int(m.group(1))].startswith(flat(u["text"])[:60]):
                continue                      # not a prose paragraph of the old cut
            n_prose += 1
            i = int(m.group(1))
            j = next((k for k, x in enumerate(safe) if x == old[i]), None)
            if j is None:
                j = next((k for k, x in enumerate(safe) if old[i][:60] in x), None)
            moved += j != i
            if j is None or safe[j] != old[i]:
                changed.append((u["uid"], j, len(old[i]), len(safe[j]) if j is not None else 0, old[i], safe[j] if j is not None else ""))
    L.append(f"  prose units {n_prose}; renumbered {moved}; text changed {len(changed)}")
    for uid, j, a, b, o, s in changed:
        L.append(f"    {uid} -> p{j}: {a} -> {b} chars\n        old  ...{o[-160:]!r}\n        safe ...{s[-160:]!r}")
    return L + [""]


def main():
    papers = ls.tuning_papers()
    t0 = time.time()
    L = [f"tag_strip_check ({time.strftime('%Y-%m-%d')}); no model. dk.SAFE_TAGS against the old '<[^>]+>' strip; "
         f"{len(papers)} tuning papers. The pipeline keeps the old strip (SAFE_TAGS off by default).", ""]
    a, bad1 = cases()
    b, bad2 = papers_check(papers)
    c, bad3 = needles()
    d = calibration()
    L += a + b + c + d + [f"required checks: made-up cases {'pass' if not bad1 else f'{bad1} fail'}; papers "
                          f"{'pass' if not bad2 else f'{bad2} fail'}; regression needles "
                          f"{'pass' if not bad3 else f'{bad3} fail'}  ({time.time() - t0:.0f}s)"]
    f = OUT / f"TAG_STRIP_CHECK_{time.strftime('%Y-%m-%d')}.txt"
    f.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    print(f"-> {f}")
    return 1 if bad1 or bad2 or bad3 else 0


if __name__ == "__main__":
    sys.exit(main())
