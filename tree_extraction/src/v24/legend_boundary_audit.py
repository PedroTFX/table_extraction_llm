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

    python legend_boundary_audit.py [papers]      (tuning papers by default)
-> TREE_OUTPUT/legend_coverage/BOUNDARY_AUDIT_<date>.txt, boundary_audit_<date>.json, boundary_cases_<date>.csv
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
from fill_template import _drop_reference_lists

OUT = lc.OUT
SKIP = 3
SHORT = 60
LOOK = 3
NUM_START = re.compile(r"^\(?(\d{1,2})\s*[.)]\s*(?=[A-Za-z(“\"'])")
LET_START = re.compile(r"^\(([a-z])\)\s*(?=\S)|^([a-z])\)\s*(?=\S)|^([a-z])\.\s+(?=[A-Za-z])")
LET_IN = re.compile(r"(?<![\w.])\(?([a-z])\)\s*(?=[A-Za-z])")
FILE_MARK = re.compile(r"^[ \t]*<!--\s*=+\s*Complementary:\s*(.+?)\s*=+\s*-->[ \t]*$", re.M)
PAGE_MARK = re.compile(r"^[ \t]*<!--\s*page\s+\d+\s+of\s+\d+\s*-->[ \t]*$", re.M)
CALIB = OUT / "calib_gold_v4.1_2026-11-25.json"


def annotated(paper):
    """The paragraphs of inventory_audit.paragraphs, each with its source file and whether a page break comes just
    before it. -> (paragraphs, equal to inventory_audit's)"""
    raw = (_paths.PAPERS / paper / f"{paper}_full.md").read_text(encoding="utf-8", errors="replace")
    prose = re.sub(r"<table.*?</table>", "\n\n", _drop_reference_lists(raw), flags=re.S | re.I)
    prose = FILE_MARK.sub(lambda m: f"\n\n⟦FILE {m.group(1)}⟧\n\n", prose)
    prose = PAGE_MARK.sub("\n\n⟦PAGE⟧\n\n", prose)
    out, src, page = [], "main", False
    for p in re.split(r"\n\s*\n", dk.clean(prose)):
        t = " ".join(p.split())
        if t.startswith("⟦FILE ") and t.endswith("⟧"):
            src, page = t[6:-1], False
            continue
        if t == "⟦PAGE⟧":
            page = True
            continue
        if len(p.strip()) > 3:
            out.append({"text": t, "file": src, "page_break_before": page})
            page = False
    ref = ia.paragraphs(paper)
    same = [x["text"] for x in out] == ref
    if not same:
        out = [{"text": t, "file": None, "page_break_before": None} for t in ref]
    return out, same


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
    return len(t) < SHORT and not is_heading(t) and start_marker(t) is None


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
    for i, p in enumerate(paras):
        if i not in used and lc.numbered(p["text"]):
            chains.append({"paragraphs": [i], "kind": "n", "items": {i: info[i]["n"]}})
    return sorted(chains, key=lambda c: c["paragraphs"][0])


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
    gap_pages = any(paras[x]["page_break_before"] for x in ps[1:]) if len(ps) > 1 else False
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
    mismatch = []
    for p in papers:
        t0 = time.time()
        paras, same = annotated(p)
        if not same:
            mismatch.append(p)
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
            incomplete, named_out = [], []
            for col in cols:
                held = set(col["codes"]) & codes
                if len(held) < 2:
                    continue
                tag = f"t{col['table']}c{col['col']} {col['header'][:60]!r} codes {sorted(held)}"
                if sep & set(col["codes"]):
                    incomplete.append(tag + f" + separated {sorted(sep & set(col['codes']))}"
                                      + (" [main unit R3abc-linked]" if (col["table"], col["col"]) in r3[main] else ""))
                w = (col["words"] & out_words) - unit_words
                if w:
                    named_out.append(tag + f" header words only outside {sorted(w)}"
                                     + (" [main unit R3abc-linked]" if (col["table"], col["col"]) in r3[main] else ""))
            rec = {"paper": p, "group": ls.SPLIT.get(p), "file": paras[ps[0]]["file"],
                   "paragraphs": ps, "kind": "split list" if len(ps) > 1 else "list unit",
                   "items": {str(x): [code_of(kind, m) for m in c["items"][x]] for x in ps}, **d,
                   "main_is_list_unit": lc.numbered(paras[main]["text"]),
                   "main_inventory": paras[main]["text"] in inv, "main_r3abc": bool(r3[main]),
                   "separated_items_units": [{"paragraph": x, "inventory": paras[x]["text"] in inv,
                                              "r3abc": bool(r3[x])} for x in ps if x != main],
                   "outside_paragraphs": [{"paragraph": x, "inventory": paras[x]["text"] in inv,
                                           "r3abc": bool(r3[x])} for x in outside],
                   "stage2_incomplete": incomplete, "stage2_name_outside": named_out,
                   "calib": [f"{p}#p{x}" for x in ps if f"{p}#p{x}" in calib],
                   "texts": {str(x): paras[x]["text"][:400] for x in sorted(set(ps) | set(outside) | set(d["shorts"]))}}
            recs.append(rec)
        print(f"  {p:22s} {len(paras):4d} paragraphs, {sum(1 for r in recs if r['paper'] == p):3d} lists"
              f"{'' if same else '  (file/page markers: paragraph mismatch, not used)'}  {time.time() - t0:5.1f}s",
              flush=True)
    return recs, stats, mismatch


def report(recs, stats, mismatch):
    stamp = time.strftime("%Y-%m-%d")
    L = [f"Unit-boundary audit of list-like legends ({stamp}); no model. {stats['papers']} tuning papers, "
         f"{stats['paragraphs']} prose paragraphs, {stats['numbered list units']} of them numbered-list units.",
         f"Paragraphs rebuilt with file and page markers equal inventory_audit's in all papers but {len(mismatch)}"
         + (f": {', '.join(mismatch)}" if mismatch else "") + ".", ""]
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
          f"  lists {len(recs)}: list units {by['list unit']}, split lists {by['split list']}"]
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
    hd = [r for r in recs if r["heading_status"] in ("heading before", "lead-in before", "lead-in and heading before")]
    L += ["", "=" * 100, "WHAT IS SEPARATED, AND WHERE IT GOES", "=" * 100,
          f"  items separated (leading or trailing): {len(sep)} lists",
          f"    separated item paragraphs: {sum(len(r['separated_items_units']) for r in sep)}; an inventory unit "
          f"{sum(x['inventory'] for r in sep for x in r['separated_items_units'])}; an R3abc candidate "
          f"{sum(x['r3abc'] for r in sep for x in r['separated_items_units'])}",
          f"    main unit an R3abc candidate: {sum(r['main_r3abc'] for r in sep)}; an inventory unit "
          f"{sum(r['main_inventory'] for r in sep)}",
          f"    a column holds 2+ of the list's codes and a separated code: {sum(bool(r['stage2_incomplete']) for r in sep)}",
          f"  heading or lead-in in a separate paragraph: {len(hd)} lists",
          f"    that paragraph an inventory unit {sum(x['inventory'] for r in hd for x in r['outside_paragraphs'])}, "
          f"an R3abc candidate {sum(x['r3abc'] for r in hd for x in r['outside_paragraphs'])} "
          f"(of {sum(len(r['outside_paragraphs']) for r in hd)})",
          f"    main unit an R3abc candidate: {sum(r['main_r3abc'] for r in hd)}",
          f"    a column holds 2+ of the list's codes and its header words are only outside the unit: "
          f"{sum(bool(r['stage2_name_outside']) for r in hd)}",
          f"  both (items and heading separated): {len([r for r in sep if r in hd])} lists", ""]
    cal = [r for r in recs if r["calib"]]
    L += ["=" * 100, "CALIBRATION UNITS AMONG THE LISTS", "=" * 100]
    L += [f"  {', '.join(r['calib'])}: {r['kind']}, leading {r['leading']}, trailing {r['trailing']}, heading "
          f"{r['heading_status']}" for r in cal] + [""]
    cut = len(L)
    L += ["=" * 100, "EVERY LIST WITH SOMETHING SEPARATED (items, or a heading / lead-in before a unit that starts at an "
          "item)", "=" * 100]
    flagged = [r for r in recs if r in sep or r in hd or r["one_per_paragraph"]]
    for r in flagged:
        L.append(f"\n  {r['paper']} [{r['file']}] paragraphs {r['paragraphs']} main p{r['main']} ({r['kind']}); "
                 f"items {r['items']}; leading {r['leading']} trailing {r['trailing']}; heading {r['heading_status']}"
                 + (f" ({r['heading_distance']} paragraphs between)" if r["heading_distance"] else "")
                 + ("; page break inside" if r["page_break_inside"] else ""))
        for x, t in r["texts"].items():
            role = ("MAIN" if int(x) == r["main"] else "item" if int(x) in r["paragraphs"] else
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
    (OUT / f"boundary_audit_{stamp}.json").write_text(json.dumps({"stats": stats, "lists": recs}, indent=1,
                                                                 ensure_ascii=False), encoding="utf-8")
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
    ps = sys.argv[1:] or ls.tuning_papers()
    report(*audit(ps))
