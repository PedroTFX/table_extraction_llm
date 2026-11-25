"""
legend_boundary_audit.py — unit-boundary audit of list-like legends (2026-11-25, after the stage 2 tests). NO MODEL
CALLS; the segmentation is not changed.

Question: how often does the unit that holds a list lose material the paper prints next to it (its heading or
lead-in, or items the PDF reader put in a paragraph of their own), what is lost (a code definition, the variable's
name, both), and does the loss reach stage 1 (a definition in no unit that can be selected) or stage 2 (a column's
code or its variable's name outside the unit that decodes it)?

Units: the prose paragraphs exactly as inventory_audit.paragraphs, legend_inventory.units and legend_coverage.units
cut them (the paper's markdown with its supplements, tables and reference lists removed, split at blank lines). The
audit rebuilds them keeping the reader's file and page markers, and checks the texts equal inventory_audit's.

Lists (numbers 0-99 and lower-case letters; a markdown heading '#' is never an item):
  list unit    a paragraph legend_coverage.numbered() calls a numbered list (a run 1, 2, 3 of enumerations)
  split list   paragraphs in a row whose items continue each other: the next paragraph starts with item m+1 where
               the previous one ends with item m (an item paragraph, or a run of >= 2 items); up to SKIP short
               paragraphs (page furniture) between; 3+ items in all
  interrupted  a run of >= 2 items ending at m, and within WINDOW paragraphs (figures, captions, a table's place,
               furniture between) a paragraph whose first item, within CONTINUED characters of its start, is m+1 and
               starts a run (the list broken inside an item, 'metallic | ... | green bees, (4) ...')
Also counted: paragraphs the reader broke at a page (the first paragraph after a page break starting in lower case
continues the one before it), and those whose two halves both hold a definition shape.
For each list, its main unit (the paragraph with most items) and, kept apart:
  leading items       items of the list in paragraphs before the main unit
  trailing items      items in paragraphs after it
  one per paragraph   no paragraph holds 2 items
  heading             the main unit has its own lead-in (text before its first item), or it starts at an item and
                      before the list (within LOOK paragraphs, short ones skipped) there is a markdown heading, a
                      lead-in sentence ending ':', or neither
Downstream (mechanical; every case is listed for checking by eye):
  stage 1   are the separated items in a unit stage 1 can get: an inventory unit (legend_inventory: >= 2 definition
            shapes) or an R3abc candidate (legend_ablation, unchanged)? Is the main unit one?
  stage 2   a table column holding 2+ of the list's codes and a code only the separated items define (its code set is
            incomplete in the main unit); a column holding 2+ of the list's codes whose header shares an informative
            word with the separated heading or lead-in and not with the main unit (the variable's name is outside)

Also measured (found while rebuilding the paragraphs): dk.clean's tag strip '<[^>]+>' deletes text that is no tag,
from a '<' in the text ('p < 0.05') to the next '>'.

    python legend_boundary_audit.py [papers]      (tuning papers by default)
-> TREE_OUTPUT/legend_coverage/BOUNDARY_AUDIT_<date>.txt, boundary_audit_<date>.json, boundary_cases_<date>.csv

    python legend_boundary_audit.py --safe-tags [--against <date>] [papers]
The same audit on the text cut with dk.SAFE_TAGS (the tag strip removes markup only; 2026-11-25), every unit the
audit reads (inventory_audit, legend_inventory, legend_coverage, R3abc's features, unchanged) cut the same way; the
outputs are named <date>_safetags. --against <date> (default 2026-11-25) compares its lists and page splits with that
date's run on the old strip and carries over the labels by eye of boundary_labels_<date>.csv: each case found again
(matched by its text, the paragraph numbers having moved), gone, or new (to label by eye).
"""
from __future__ import annotations

import collections
import contextlib
import csv
import io
import json
import re
import sys
import time

import _paths
import decode_key as dk
import full_run_v24 as fr
import header_tree as ht
import header_tree_bench as hb
import inventory_audit as ia
import legend_ablation as la
import legend_coverage as lc
import legend_inventory as li
import legend_scope as ls
from fill_template import _PAGE_NOISE_RE, _drop_reference_lists

OUT = lc.OUT
SKIP = 3
SHORT = 60
LOOK = 3
WINDOW = 6         # paragraphs an interrupted list may jump (figures, captions, tables' places, furniture)
CONTINUED = 80     # at most this many characters before the first item of an interrupted list's second part
NUM_START = re.compile(r"^\(?(\d{1,2})\s*[.)]\s*(?=[A-Za-z(“\"'])")
LET_START = re.compile(r"^\(([a-z])\)\s*(?=\S)|^([a-z])\)\s*(?=\S)|^([a-z])\.\s+(?=[A-Za-z])")
LET_IN = re.compile(r"(?<![\w.])\(?([a-z])\)\s*(?=[A-Za-z])")
FILE_MARK = re.compile(r"^[ \t]*<!--\s*=+\s*Complementary:\s*(.+?)\s*=+\s*-->[ \t]*$", re.M)
PAGE_MARK = re.compile(r"^[ \t]*<!--\s*page\s+\d+\s+of\s+\d+\s*-->[ \t]*$", re.M)
CALIB = OUT / "calib_gold_v4.1_2026-11-25.json"


TAG = re.compile(r"<(?:!--.*?--|/?[A-Za-z][A-Za-z0-9]*(?:\s[^<>]*)?/?)>", re.S)


def _paras(prose):
    return [" ".join(p.split()) for p in re.split(r"\n\s*\n", dk.clean(prose)) if len(p.strip()) > 3]


def annotated(paper):
    """The paragraphs of inventory_audit.paragraphs, each with its source file and whether a page break comes just
    before it. -> (paragraphs, page markers equal, files aligned, the tag strip's deletions of text that is no tag)

    Page breaks: a marker paragraph is added AFTER each page comment, the comment kept (dk.clean's '<[^>]+>' runs
    from a '<' in the text, 'p < 0.05', to the next '>', often a page comment's end: moving that '>' would change
    what it deletes). Files: _drop_reference_lists removes the supplement marker that follows a reference list, so
    each file is cut on its own and its paragraphs are aligned to the paper's in order."""
    raw = (_paths.PAPERS / paper / f"{paper}_full.md").read_text(encoding="utf-8", errors="replace")
    prose = re.sub(r"<table.*?</table>", "\n\n", _drop_reference_lists(raw), flags=re.S | re.I)
    ref = ia.paragraphs(paper)
    marked = PAGE_MARK.sub(lambda m: m.group(0) + "\n\n⟦PAGE⟧\n\n", prose)
    out, page = [], False
    for t in _paras(marked):
        if t == "⟦PAGE⟧":
            page = True
            continue
        out.append({"text": t, "file": None, "page_break_before": page})
        page = False
    pages_ok = [x["text"] for x in out] == ref
    if not pages_ok:
        out = [{"text": t, "file": None, "page_break_before": None} for t in ref]
    # files
    bounds = [(0, "main")] + [(m.end(), m.group(1)) for m in FILE_MARK.finditer(raw)]
    seq = []
    for (a, name), (b, _n) in zip(bounds, bounds[1:] + [(len(raw), None)]):
        doc = re.sub(r"<table.*?</table>", "\n\n", _drop_reference_lists(raw[a:b]), flags=re.S | re.I)
        seq += [(t, name) for t in _paras(doc)]
    k, aligned = 0, 0
    for x in out:
        hit = next((j for j in range(k, min(k + 6, len(seq))) if seq[j][0] == x["text"]), None)
        if hit is not None:
            x["file"], k = seq[hit][1], hit + 1
            aligned += 1
    # text the tag strip in use deletes although it is no tag (the old strip's from a '<' to the next '>'; with
    # dk.SAFE_TAGS none is expected)
    lost = [s for s in dk.removed(prose) if not TAG.fullmatch(s)]
    return out, pages_ok, (aligned, len(out)), lost


def is_heading(t):
    return t.startswith("#")


def start_marker(t):
    if is_heading(t):
        return None
    m = NUM_START.match(t)
    if m:
        return ("n", int(m.group(1)))
    m = LET_START.match(t)
    if m:
        return ("l", next(g for g in m.groups() if g))
    return None


def markers(t):
    """(numbers, letters) enumerated in the paragraph, in order."""
    if is_heading(t):
        return [], []
    return [int(m.group(1)) for m in lc.ENUM.finditer(t)], [m.group(1) for m in LET_IN.finditer(t)]


def prev(kind, m):
    if kind == "n":
        return m - 1 if m >= 1 else None
    return chr(ord(m) - 1) if m > "a" else None


def run_end(seq, kind):
    """The last marker of the paragraph and the length of the consecutive run ending there."""
    if not seq:
        return None, 0
    n = 1
    for a, b in zip(seq[-2::-1], seq[::-1]):
        if (kind == "n" and a == b - 1) or (kind == "l" and ord(a) == ord(b) - 1):
            n += 1
        else:
            break
    return seq[-1], n


def is_short(t):
    """Page furniture: a short paragraph (no heading, no item), a publisher's running header or footer (the
    patterns fill_template already treats as page noise), or an image placeholder."""
    if is_heading(t) or start_marker(t) is not None:
        return False
    return len(t) < SHORT or bool(_PAGE_NOISE_RE.search(t)) or t.startswith("![")


def lists(paras):
    """-> [{'paragraphs': [i...], 'kind': 'n'|'l', 'items': {i: [markers]}}]"""
    info = []
    for p in paras:
        t = p["text"]
        nums, lets = markers(t)
        info.append({"start": start_marker(t), "n": nums, "l": lets})
    chains, used = [], set()
    i = 0
    while i < len(paras):
        chain, kind = [i], None
        cur = i
        while True:
            j, skipped = cur + 1, 0
            while j < len(paras) and is_short(paras[j]["text"]) and skipped < SKIP:
                j, skipped = j + 1, skipped + 1
            if j >= len(paras) or not info[j]["start"]:
                break
            k, m = info[j]["start"]
            if kind and k != kind:
                break
            last, n = run_end(info[cur][k], k)
            if is_heading(paras[cur]["text"]) or last is None or last != prev(k, m) or \
                    not (info[cur]["start"] or n >= 2):
                break
            kind = k
            chain.append(j)
            cur = j
        if len(chain) >= 2 and sum(len(info[x][kind]) for x in chain) >= 3:
            chains.append({"paragraphs": chain, "kind": kind, "items": {x: info[x][kind] for x in chain}})
            used |= set(chain)
            i = chain[-1] + 1
        else:
            i += 1
    # interrupted lists: a run of >= 2 numbered items ending at m, and within WINDOW paragraphs (any material between:
    # a figure, a caption, a table's place, page furniture) a paragraph whose first item is m + 1 and starts a run of
    # >= 2, the text before that item a continued item, not a lead-in of its own
    for i in range(len(paras)):
        if i in used:
            continue
        last, n = run_end(info[i]["n"], "n")
        if last is None or n < 2:
            continue
        for j in range(i + 1, min(i + 1 + WINDOW, len(paras))):
            ns = info[j]["n"]
            if j in used or is_heading(paras[j]["text"]):
                break
            m0 = lc.ENUM.search(paras[j]["text"])
            if ns and ns[0] == last + 1 and len(ns) >= 2 and ns[1] == last + 2 and m0 and m0.start() <= CONTINUED:
                chains.append({"paragraphs": [i, j], "kind": "n", "items": {i: info[i]["n"], j: ns},
                               "between": list(range(i + 1, j))})
                used |= {i, j}
                break
    for i, p in enumerate(paras):
        if i not in used and lc.numbered(p["text"]):
            chains.append({"paragraphs": [i], "kind": "n", "items": {i: info[i]["n"]}})
    return sorted(chains, key=lambda c: c["paragraphs"][0])


def page_splits(paras):
    """Paragraphs the reader broke at a page: the first paragraph after a page break that starts in lower case
    (a continued sentence), after any furniture, image or caption paragraphs; with the paragraph it continues."""
    out = []
    for j, p in enumerate(paras):
        if not p["page_break_before"]:
            continue
        k = j
        while k < len(paras) and (is_short(paras[k]["text"]) or paras[k]["text"].startswith("![")
                                  or lc.CAPTION.match(paras[k]["text"])):
            k += 1
        if k >= len(paras) or not re.match(r"[a-z]", paras[k]["text"]):
            continue
        i = j - 1
        while i >= 0 and (is_short(paras[i]["text"]) or paras[i]["text"].startswith("![")
                          or lc.CAPTION.match(paras[i]["text"])):
            i -= 1
        if i >= 0:
            out.append((i, k))
    return out


def look_back(paras, s):
    """Before paragraph s: the skipped short paragraphs, the nearest heading and lead-in within LOOK paragraphs."""
    shorts, heading, lead, seen = [], None, None, 0
    j = s - 1
    while j >= 0 and seen < LOOK:
        t = paras[j]["text"]
        if is_short(t):
            shorts.append(j)
            j -= 1
            continue
        if is_heading(t):
            heading = j
            break
        if lead is None and seen == 0 and t.rstrip().endswith(":"):
            lead = j
        seen += 1
        j -= 1
    return shorts, heading, lead, (seen if heading is not None else None)


def describe(paras, c):
    ps, kind = c["paragraphs"], c["kind"]
    main = max(ps, key=lambda x: (len(c["items"][x]), -x))
    lead_items = [m for x in ps if x < main for m in c["items"][x]]
    trail_items = [m for x in ps if x > main for m in c["items"][x]]
    own = start_marker(paras[ps[0]]["text"]) is None
    shorts, heading, lead, hdist = look_back(paras, ps[0])
    if main == ps[0] and own:
        hs = "own lead-in"
    elif own:
        hs = "lead-in with the leading items"
    elif heading is not None and lead is not None:
        hs = "lead-in and heading before"
    elif heading is not None:
        hs = "heading before"
    elif lead is not None:
        hs = "lead-in before"
    else:
        hs = "none found"
    gap_pages = any(paras[x]["page_break_before"] for x in range(ps[0] + 1, ps[-1] + 1)) if len(ps) > 1 else False
    return {"main": main, "leading": lead_items, "trailing": trail_items,
            "one_per_paragraph": len(ps) > 1 and all(len(v) <= 1 for v in c["items"].values()),
            "chain_own_lead_in": own, "heading_status": hs, "heading": heading, "heading_distance": hdist,
            "lead_in": lead, "shorts": shorts,
            "page_break_inside": gap_pages}


def code_of(kind, m):
    return str(m) if kind == "n" else m


def audit(papers):
    OUT.mkdir(parents=True, exist_ok=True)
    head = fr.head_runs()
    calib = {u["uid"]: u for u in json.loads(CALIB.read_text(encoding="utf-8"))["units"]}
    papers = [p for p in papers if p in head]
    with contextlib.redirect_stdout(io.StringIO()):
        rows, _pp, _tx = la.features(papers)
    r3all = collections.defaultdict(lambda: collections.defaultdict(set))
    for r in la.variant(rows, "abc"):
        if r["unit_table"] is None:
            r3all[r["paper"]][r["unit"]].add((r["table"], r["col"]))
    recs, stats = [], collections.Counter()
    mismatch, strip, pages = [], [], []
    for p in papers:
        t0 = time.time()
        paras, same, (aligned, n_par), lost = annotated(p)
        if not same:
            mismatch.append(p)
        stats["paragraphs with a file"] += aligned
        if lost:
            strip.append({"paper": p, "group": ls.SPLIT.get(p), "matches": len(lost),
                          "chars": sum(len(x) for x in lost), "blank_lines_crossed": sum("\n\n" in x for x in lost),
                          "examples": [x[:160] for x in lost[:3]]})
        grids = {k: ht.grid_from_html(h) for k, h in enumerate(hb.html_tables(p))}
        first = {e["table"]: e.get("first") or 1 for e in head[p]}
        cols = lc.columns(p, grids, first)
        inv = {u["text"] for u in li.units(p) if u["kind"] == "prose"}
        r3 = r3all[p]
        assert len(lc.units(p, grids, first)) >= len(paras)
        stats["papers"] += 1
        stats["paragraphs"] += len(paras)
        stats["numbered list units"] += sum(lc.numbered(x["text"]) for x in paras)
        for c in lists(paras):
            d = describe(paras, c)
            ps, kind, main = c["paragraphs"], c["kind"], d["main"]
            codes = {code_of(kind, m) for v in c["items"].values() for m in v}
            sep = {code_of(kind, m) for m in d["leading"] + d["trailing"]} - {code_of(kind, m) for m in c["items"][main]}
            outside = [x for x in (d["heading"], d["lead_in"]) if x is not None] \
                if d["heading_status"] != "own lead-in" else []
            out_words = set().union(*[lc.informative(paras[x]["text"]) for x in outside]) if outside else set()
            unit_words = lc.informative(paras[main]["text"])
            list_words = unit_words | out_words | set().union(*[lc.informative(paras[x]["text"]) for x in ps])
            incomplete, named_out, related = [], [], 0
            for col in cols:
                held = set(col["codes"]) & codes
                if len(held) < 2:
                    continue
                tag = f"t{col['table']}c{col['col']} {col['header'][:60]!r} codes {sorted(held)}"
                if sep & set(col["codes"]):
                    rel = bool(col["words"] & list_words) or (col["table"], col["col"]) in r3[main]
                    related += rel
                    incomplete.append(tag + f" + separated {sorted(sep & set(col['codes']))}"
                                      + (" [main unit R3abc-linked]" if (col["table"], col["col"]) in r3[main] else "")
                                      + ("" if rel else " [header unrelated to the list]"))
                w = (col["words"] & out_words) - unit_words
                if w:
                    named_out.append(tag + f" header words only outside {sorted(w)}"
                                     + (" [main unit R3abc-linked]" if (col["table"], col["col"]) in r3[main] else ""))
            between = c.get("between", [])
            rec = {"paper": p, "group": ls.SPLIT.get(p), "file": paras[ps[0]]["file"],
                   "paragraphs": ps, "kind": ("interrupted list" if "between" in c else "split list") if len(ps) > 1
                   else "list unit", "between": between,
                   "between_kinds": ["image" if paras[x]["text"].startswith("![") else "page furniture" if
                                     is_short(paras[x]["text"]) else "caption" if lc.CAPTION.match(paras[x]["text"])
                                     else "text" for x in between],
                   "items": {str(x): [code_of(kind, m) for m in c["items"][x]] for x in ps}, **d,
                   "main_is_list_unit": lc.numbered(paras[main]["text"]),
                   "main_inventory": paras[main]["text"] in inv, "main_r3abc": bool(r3[main]),
                   "separated_items_units": [{"paragraph": x, "inventory": paras[x]["text"] in inv,
                                              "r3abc": bool(r3[x])} for x in ps if x != main],
                   "outside_paragraphs": [{"paragraph": x, "inventory": paras[x]["text"] in inv,
                                           "r3abc": bool(r3[x])} for x in outside],
                   "stage2_incomplete": incomplete, "stage2_incomplete_related": related,
                   "stage2_name_outside": named_out,
                   "calib": [u for x in ps for u, cu in calib.items() if cu["paper"] == p and (
                       _same(paras[x]["text"], cu["text"]) if dk.SAFE_TAGS else u == f"{p}#p{x}")],   # ids: old cut
                   "texts": {str(x): paras[x]["text"][:400]
                             for x in sorted(set(ps) | set(outside) | set(d["shorts"]) | set(between))}}
            recs.append(rec)
        for i, k in page_splits(paras):
            a, b = paras[i]["text"], paras[k]["text"]
            stats["paragraphs continued across a page"] += 1
            ha, hb_ = li.shape_hits(a), li.shape_hits(b)
            if ha or hb_:
                stats["continued across a page, a definition shape in either half"] += 1
            if (ha >= 2) != (hb_ >= 2) and ha + hb_ >= 2:
                stats["continued across a page, inventory unit in one half only (2+ shapes there)"] += 1
            if ha and hb_:
                stats["continued across a page, definition shapes in both halves"] += 1
                pages.append({"paper": p, "before": i, "after": k, "shapes": [ha, hb_], "end": a[-160:],
                              "start": b[:160], "inventory": [a in inv, b in inv]})
        stats["tag-strip spans with a definition shape"] += sum(li.shape_hits(x) >= 1 for x in lost)
        stats["tag-strip spans with 2+ definition shapes"] += sum(li.shape_hits(x) >= 2 for x in lost)
        print(f"  {p:22s} {len(paras):4d} paragraphs, {sum(1 for r in recs if r['paper'] == p):3d} lists, files "
              f"aligned {aligned}/{n_par}{'' if same else '  (page markers: paragraph mismatch, not used)'}"
              f"{f'  tag strip deletes {sum(len(x) for x in lost)} chars' if lost else ''}  {time.time() - t0:5.1f}s",
              flush=True)
    return recs, stats, mismatch, strip, pages


HEADING_APART = ("heading before", "lead-in before", "lead-in and heading before")


def is_flagged(r):
    """A list the report lists in full: items separated, a heading or lead-in apart, or one item per paragraph."""
    return bool(r["leading"] or r["trailing"] or r["heading_status"] in HEADING_APART or r["one_per_paragraph"])


def _key(t, n=80):
    return " ".join(str(t or "").split())[:n]


def _same(a, b, n=60):
    """Two paragraph texts are one case: one's start is in the other (a corrected paragraph can be longer)."""
    a, b = _key(a, 400), _key(b, 400)
    return bool(a and b) and (a[:n] in b or b[:n] in a)


def compare(recs, pages, against):
    """The lists and page splits of this run against the run on the old strip of date `against`, with the labels by
    eye carried over (matched by text: the corrected cutting renumbers paragraphs). -> report lines"""
    old = json.loads((OUT / f"boundary_audit_{against}.json").read_text(encoding="utf-8"))
    lab_f = OUT / f"boundary_labels_{against}.csv"
    labels = list(csv.DictReader(open(lab_f, encoding="utf-8"))) if lab_f.exists() else []
    L = ["=" * 100, f"AGAINST THE RUN ON THE OLD STRIP ({against}); labels by eye from {lab_f.name}", "=" * 100]

    def lab(kind, paper, where):
        hit = [x for x in labels if x["kind"].startswith(kind) and x["paper"] == paper and x["where"] == where]
        return (hit[0]["legend"] + (f" ({hit[0]['note'][:90]})" if hit[0]["note"] else "")) if hit else "no label"

    def main_text(r):
        return r["texts"][str(r["main"])]

    flagged_old = [r for r in old["lists"] if is_flagged(r)]
    flagged_new = [r for r in recs if is_flagged(r)]
    L.append(f"  lists: old {len(old['lists'])} ({len(flagged_old)} with something separated), now {len(recs)} "
             f"({len(flagged_new)})")
    seen = set()
    for r in flagged_old:
        where = f"p{','.join(map(str, r['paragraphs']))}"[:60]
        m = next((i for i, x in enumerate(flagged_new) if x["paper"] == r["paper"] and i not in seen
                  and _same(main_text(x), main_text(r))), None)
        if m is None:
            m_any = next((x for x in recs if x["paper"] == r["paper"] and _same(main_text(x), main_text(r))), None)
            state = (f"FOUND, NOTHING SEPARATED NOW (p{m_any['main']}, heading {m_any['heading_status']})" if m_any
                     else "GONE (no list with this text)")
        else:
            seen.add(m)
            x = flagged_new[m]
            same = (x["leading"], x["trailing"], x["heading_status"]) == (r["leading"], r["trailing"], r["heading_status"])
            state = (f"found p{x['main']}" + ("" if same else f" CHANGED: leading {r['leading']}->{x['leading']}, "
                     f"trailing {r['trailing']}->{x['trailing']}, heading {r['heading_status']}->{x['heading_status']}"))
        L.append(f"    {r['paper']:20s} {where:16s} [{lab('list', r['paper'], where)[:70]}]  {state}")
    for i, x in enumerate(flagged_new):
        if i not in seen:
            L.append(f"    NEW {x['paper']:16s} p{','.join(map(str, x['paragraphs']))} main p{x['main']} ({x['kind']}); "
                     f"leading {x['leading']} trailing {x['trailing']} heading {x['heading_status']}: "
                     f"{main_text(x)[:140]!r}")
    L.append(f"  page splits with definition shapes in both halves: old {len(old['page_splits'])}, now {len(pages)}")
    seen = set()
    for r in old["page_splits"]:
        where = f"p{r['before']}|p{r['after']}"
        m = next((i for i, x in enumerate(pages) if x["paper"] == r["paper"] and i not in seen
                  and _same(x["start"], r["start"], 50)), None)
        tag = lab("page", r["paper"], where)
        if m is None:
            L.append(f"    {r['paper']:20s} {where:12s} [{tag[:70]}]  GONE: ...{r['end'][-70:]!r} || {r['start'][:70]!r}")
        else:
            seen.add(m)
            x = pages[m]
            moved = _key(x["end"][-60:]) != _key(r["end"][-60:])
            L.append(f"    {r['paper']:20s} {where:12s} [{tag[:70]}]  found p{x['before']}|p{x['after']}"
                     + (f"; first half CHANGED: ...{x['end'][-70:]!r}" if moved else ""))
    for i, x in enumerate(pages):
        if i not in seen:
            L.append(f"    NEW {x['paper']:16s} p{x['before']}|p{x['after']} shapes {x['shapes']}: ...{x['end'][-80:]!r} "
                     f"|| {x['start'][:80]!r}")
    return L + [""]


def report(recs, stats, mismatch, strip, pages, against=None):
    stamp = time.strftime("%Y-%m-%d") + ("_safetags" if dk.SAFE_TAGS else "")
    L = [f"Unit-boundary audit of list-like legends ({stamp}); no model. Tag strip: "
         + ("dk.SAFE_TAGS (markup only)" if dk.SAFE_TAGS else "the old '<[^>]+>'") + f". {stats['papers']} tuning papers, "
         f"{stats['paragraphs']} prose paragraphs, {stats['numbered list units']} of them numbered-list units.",
         f"Paragraphs rebuilt with page markers equal inventory_audit's in all papers but {len(mismatch)}"
         + (f": {', '.join(mismatch)}" if mismatch else "") + f"; paragraphs attributed to their file "
         f"{stats['paragraphs with a file']} of {stats['paragraphs']}.", ""]
    by = collections.Counter()
    for r in recs:
        by[r["kind"]] += 1
        if r["leading"]:
            by["leading items in other paragraphs"] += 1
        if r["trailing"]:
            by["trailing items in other paragraphs"] += 1
        if r["one_per_paragraph"]:
            by["one item per paragraph"] += 1
        by["heading: " + r["heading_status"]] += 1
    L += ["=" * 100, "LISTS", "=" * 100,
          f"  lists {len(recs)}: list units {by['list unit']}, split lists {by['split list']}, interrupted lists "
          f"{by['interrupted list']} (between their parts: "
          + ", ".join(f"{k} {v}" for k, v in collections.Counter(x for r in recs for x in r["between_kinds"]).items())
          + ")"]
    for k in ("leading items in other paragraphs", "trailing items in other paragraphs", "one item per paragraph"):
        xs = [r for r in recs if (r["leading"] if k.startswith("leading") else r["trailing"] if k.startswith("trailing")
                                  else r["one_per_paragraph"])]
        L.append(f"  {k}: {len(xs)} lists in {len({r['paper'] for r in xs})} papers; page break inside the list "
                 f"{sum(bool(r['page_break_inside']) for r in xs)}; in a supplement "
                 f"{sum(1 for r in xs if r['file'] not in ('main', None))}")
    L.append("  heading of the main unit:")
    for k in ("own lead-in", "lead-in with the leading items", "heading before", "lead-in before",
              "lead-in and heading before", "none found"):
        xs = [r for r in recs if r["heading_status"] == k]
        L.append(f"    {k:28s} {len(xs):4d} lists in {len({r['paper'] for r in xs}):3d} papers")
    sep = [r for r in recs if r["leading"] or r["trailing"]]
    hd = [r for r in recs if r["heading_status"] in HEADING_APART]
    L += ["", "=" * 100, "WHAT IS SEPARATED, AND WHERE IT GOES", "=" * 100,
          f"  items separated (leading or trailing): {len(sep)} lists",
          f"    separated item paragraphs: {sum(len(r['separated_items_units']) for r in sep)}; an inventory unit "
          f"{sum(x['inventory'] for r in sep for x in r['separated_items_units'])}; an R3abc candidate "
          f"{sum(x['r3abc'] for r in sep for x in r['separated_items_units'])}",
          f"    main unit an R3abc candidate: {sum(r['main_r3abc'] for r in sep)}; an inventory unit "
          f"{sum(r['main_inventory'] for r in sep)}",
          f"    a column holds 2+ of the list's codes and a separated code: {sum(bool(r['stage2_incomplete']) for r in sep)}"
          f" lists; with a header related to the list (an informative word shared, or R3abc-linked): "
          f"{sum(bool(r['stage2_incomplete_related']) for r in sep)} lists",
          f"  heading or lead-in in a separate paragraph: {len(hd)} lists",
          f"    that paragraph an inventory unit {sum(x['inventory'] for r in hd for x in r['outside_paragraphs'])}, "
          f"an R3abc candidate {sum(x['r3abc'] for r in hd for x in r['outside_paragraphs'])} "
          f"(of {sum(len(r['outside_paragraphs']) for r in hd)})",
          f"    main unit an R3abc candidate: {sum(r['main_r3abc'] for r in hd)}",
          f"    a column holds 2+ of the list's codes and its header words are only outside the unit: "
          f"{sum(bool(r['stage2_name_outside']) for r in hd)}",
          f"  both (items and heading separated): {len([r for r in sep if r in hd])} lists", ""]
    L += ["=" * 100, "THE TAG STRIP: TEXT IT DELETES THAT IS NO TAG", "=" * 100,
          ("  dk.SAFE_TAGS: only markup is removed (a comment, an HTML element's tag); a removal the audit's tag "
           "pattern calls no tag is counted here (none expected)." if dk.SAFE_TAGS else
           "  dk.clean removes '<[^>]+>' before the paragraphs are cut. A '<' that opens no tag ('p < 0.05') starts a "
           "match that runs to the next '>' (often a page comment's end), deleting the text between, blank lines "
           "included."),
          f"  papers {len(strip)} of {stats['papers']}; matches {sum(x['matches'] for x in strip)}; characters deleted "
          f"{sum(x['chars'] for x in strip)}; matches that cross a blank line (paragraphs merged or lost) "
          f"{sum(x['blank_lines_crossed'] for x in strip)}",
          f"  deleted spans with a definition shape (legend_inventory.SHAPES) {stats['tag-strip spans with a definition shape']},"
          f" with 2+ {stats['tag-strip spans with 2+ definition shapes']}"]
    for x in sorted(strip, key=lambda x: -x["chars"]):
        name = x["paper"] if x["group"] in ls.TUNING else "(a paper outside the tuning set)"
        L.append(f"    {name:22s} {x['matches']:3d} matches {x['chars']:6d} chars, {x['blank_lines_crossed']} across "
                 f"blank lines; e.g. {x['examples'][0][:110]!r}")
    L.append("")
    L += ["=" * 100, "THE SAME MECHANISM OUTSIDE LISTS: PARAGRAPHS BROKEN AT A PAGE", "=" * 100,
          "  The reader does not join a paragraph across pages: the first paragraph after a page break that starts in "
          "lower case (after furniture, images, captions) continues the paragraph before it, in another unit.",
          f"  continued paragraphs {stats['paragraphs continued across a page']}; a definition shape in either half "
          f"{stats['continued across a page, a definition shape in either half']}; in both halves (a legend may "
          f"straddle the break) {stats['continued across a page, definition shapes in both halves']}; one half an "
          f"inventory unit (2+ shapes) and the other not "
          f"{stats['continued across a page, inventory unit in one half only (2+ shapes there)']}"]
    for x in pages[:60]:
        L.append(f"    {x['paper']} p{x['before']}|p{x['after']} shapes {x['shapes']} inventory {x['inventory']}: "
                 f"...{x['end'][-90:]!r} || {x['start'][:90]!r}...")
    L.append("")
    cal = [r for r in recs if r["calib"]]
    L += ["=" * 100, "CALIBRATION UNITS AMONG THE LISTS", "=" * 100]
    L += [f"  {', '.join(r['calib'])}: {r['kind']}, leading {r['leading']}, trailing {r['trailing']}, heading "
          f"{r['heading_status']}" for r in cal] + [""]
    if against:
        L += compare(recs, pages, against)
    cut = len(L)
    L += ["=" * 100, "EVERY LIST WITH SOMETHING SEPARATED (items, or a heading / lead-in before a unit that starts at an "
          "item)", "=" * 100]
    flagged = [r for r in recs if is_flagged(r)]
    for r in flagged:
        L.append(f"\n  {r['paper']} [{r['file']}] paragraphs {r['paragraphs']} main p{r['main']} ({r['kind']}); "
                 f"items {r['items']}; leading {r['leading']} trailing {r['trailing']}; heading {r['heading_status']}"
                 + (f" ({r['heading_distance']} paragraphs between)" if r["heading_distance"] else "")
                 + (f"; between the parts: {r['between_kinds']}" if r["between"] else "")
                 + ("; page break inside" if r["page_break_inside"] else ""))
        for x, t in r["texts"].items():
            role = ("MAIN" if int(x) == r["main"] else "item" if int(x) in r["paragraphs"] else
                    "between" if int(x) in r["between"] else
                    "heading" if int(x) == r["heading"] else "lead-in" if int(x) == r["lead_in"] else "short")
            L.append(f"      p{x} {role:7s} {t[:240]!r}")
        for s in r["stage2_incomplete"]:
            L.append(f"      stage 2, incomplete code set: {s}")
        for s in r["stage2_name_outside"]:
            L.append(f"      stage 2, name only outside: {s}")
        L.append(f"      stage 1: main inventory {r['main_inventory']} R3abc {r['main_r3abc']}; separated items "
                 f"{r['separated_items_units']}; outside {r['outside_paragraphs']}")
    f = OUT / f"BOUNDARY_AUDIT_{stamp}.txt"
    f.write_text("\n".join(L) + "\n", encoding="utf-8")
    (OUT / f"boundary_audit_{stamp}.json").write_text(json.dumps({"stats": stats, "lists": recs, "page_splits": pages,
                                                                  "tag_strip": strip}, indent=1, ensure_ascii=False),
                                                      encoding="utf-8")
    with open(OUT / f"boundary_cases_{stamp}.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["paper", "file", "paragraphs", "main", "kind", "leading", "trailing", "one_per_paragraph",
                    "heading_status", "heading_text", "lead_in_text", "main_start", "stage2_incomplete",
                    "stage2_name_outside", "label_boundary_loss", "label_lost_content", "label_downstream", "note"])
        for r in flagged:
            w.writerow([r["paper"], r["file"], " ".join(map(str, r["paragraphs"])), r["main"], r["kind"],
                        " ".join(r["leading"] and map(str, r["leading"]) or []),
                        " ".join(r["trailing"] and map(str, r["trailing"]) or []), r["one_per_paragraph"],
                        r["heading_status"], r["texts"].get(str(r["heading"]), "") if r["heading"] is not None else "",
                        r["texts"].get(str(r["lead_in"]), "") if r["lead_in"] is not None else "",
                        r["texts"][str(r["main"])][:200], " || ".join(r["stage2_incomplete"]),
                        " || ".join(r["stage2_name_outside"]), "", "", "", ""])
    print("\n".join(L[:cut]))
    print(f"-> {f}")


if __name__ == "__main__":
    args, against = sys.argv[1:], None
    if "--safe-tags" in args:
        args.remove("--safe-tags")
        dk.SAFE_TAGS, against = True, "2026-11-25"
    if "--against" in args:
        i = args.index("--against")
        against = args[i + 1]
        del args[i:i + 2]
    ps = args or ls.tuning_papers()
    report(*audit(ps), against=against)
