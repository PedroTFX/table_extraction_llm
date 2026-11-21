"""Sessions 3 on of prompt_ab.py (column_variants.py), read column by column: for every variant of a round against
'old.<round>' (the adopted tree read again in the same session), tuning papers only (dev + held_a).

  used columns   (the GT draws on them, the reliable key) right before and after, every change with both paths,
                 probabilities and the key's evidence; the columns wrong before, with their new path
  none columns   (the GT does not use them: weak key) counted apart, never as the score; a fixed random sample of the
                 changed ones, both paths, for reading by hand
  papers         Gathof2022, Ji2024, Luo2023, Viza2023, Wallon2024: every column whose path changed (the user's list)
  cost           questions on each column's chosen path, old and new (the explored runner-up branches come on top)

    python tree_ab_report.py [round]      (default 3) -> output/prompt_ab/TREE_AB_<round>.txt
Round 4 adds the cases the user keeps in view (TRACK), whatever they did.
Round 5 adds, for a variant with a control (column_variants.CONTROL), the comparison with that control too, and two
sections read with the cell values (the tables rebuilt as prompt_ab built them; no model): every column whose path
reaches organism_name:higher_rank in any reading of the round, and every column whose cells are all marks (X, +, ✓).
"""
import collections
import json
import random
import re
import sys

import _paths
import column_variants as cv

OUT = _paths.OUTPUT / "prompt_ab"
SPLIT = json.loads((_paths.SUB / "output/eval_split/split_v15.json").read_text(encoding="utf-8"))["assign"]
TRAITS = {"measurementType", "measurementValue"}
LOOK = ("Gathof2022", "Ji2024", "Luo2023", "Viza2023", "Wallon2024")
# (table, header start): unresolved after round 3, followed in every round from 4 on (the user, 2026-11-21)
TRACK = [("Gathof2022#5", "Caught individuals"), ("Gathof2022#6", "Caught individuals"), ("Tsai2020#1", "amount"),
         ("Viza2023#7", "Suborder"), ("Luo2023#0", "Measure"), ("Cao2024#7", "Locomotion"),
         ("Normandin2017#12", "Social"), ("Torok2022#8", "(no name, column 1)"), ("Dejean2019#1", "Occurrences"),
         ("Viza2023#8", "Suborder"), ("Wallon2024#24", "Class"), ("Wallon2024#30", "Class"),
         ("Brant2021#0", "Intertegular distance"), ("Heiva2013#0", "FG")]
# a cell that is only a mark: presence or absence, a tick, a dash (one or two characters, no other letter than x)
MARK = re.compile(r"[xX+✓✔●•○◦*?\-–—]{1,2}")
HIGHER = "organism_name:higher_rank"


def right(tag, lab):
    return tag == lab or (tag in TRAITS and lab in TRAITS)


def asked(path):
    return sum(1 for s in (path or "").split(" > ") if s and not s.startswith("code:") and ":by table kind" not in s)


def tuning(res):
    return [(p, r) for p, r in sorted(res.items()) if SPLIT.get(p) in ("dev", "held_a")]


def compare(res, v, base, title):
    """One variant against one reading of the same session: the summary lines and the detail lines."""
    c, used_flips, wrong_before, none_flips, look, track = collections.Counter(), [], [], [], [], []
    for p, r in tuning(res):
        for e in r["tables"]:
            if v not in e["pred"] or base not in e["pred"]:
                continue
            for h, (lab, why) in e["labels"].items():
                if lab == "unsure" or h not in e["pred"][base] or h not in e["pred"][v]:
                    continue
                (t0, p0), (t1, p1) = e["pred"][base][h], e["pred"][v][h]
                a, b = e["paths"][base].get(h, ""), e["paths"][v].get(h, "")
                side = "used" if lab != "none" else "none"
                c[(side, "n")] += 1
                c[(side, "right before")] += right(t0 or "none", lab)
                c[(side, "right after")] += right(t1 or "none", lab)
                c[(side, "asked before")] += asked(a)
                c[(side, "asked after")] += asked(b)
                row = (f"  {e['table']:26s} '{h[:40]}'  key {lab} ({why[:70]})\n"
                       f"      before {t0} ({p0}): {a}\n      after  {t1} ({p1}): {b}")
                if t0 != t1:
                    c[(side, "changed")] += 1
                    c[(side, "to right")] += right(t1 or "none", lab) and not right(t0 or "none", lab)
                    c[(side, "to wrong")] += right(t0 or "none", lab) and not right(t1 or "none", lab)
                    (used_flips if side == "used" else none_flips).append(row)
                if side == "used" and not right(t0 or "none", lab):
                    wrong_before.append(row)
                if p in LOOK and a != b:
                    look.append(row)
                if any(e["table"] == tt and h.startswith(hh) for tt, hh in TRACK):
                    track.append(row)
    L = [f"== {title}"]
    for side in ("used", "none"):
        n = c[(side, "n")]
        if n:
            L.append(f"  {side:4s} {n:5d} columns  right {c[(side, 'right before')] / n:6.1%} -> "
                     f"{c[(side, 'right after')] / n:6.1%}   changed {c[(side, 'changed')]:3d} (to right "
                     f"{c[(side, 'to right')]}, to wrong {c[(side, 'to wrong')]})   questions on the path "
                     f"{c[(side, 'asked before')] / n:.2f} -> {c[(side, 'asked after')] / n:.2f} per column")
    L.append("")
    D = [f"######## {title}", f"## used columns that changed: {len(used_flips)}"] + used_flips
    D += [f"## used columns wrong before ({base}), with their path now: {len(wrong_before)}"] + wrong_before
    sample = random.Random(20261120).sample(none_flips, min(40, len(none_flips)))
    D += [f"## none columns that changed: {len(none_flips)}; a fixed sample of {len(sample)} for reading by hand"]
    D += sample
    D += [f"## {', '.join(LOOK)}: every column whose path changed: {len(look)}"] + look
    D += [f"## tracked cases (unresolved after round 3), changed or not: {len(track)}"] + track + [""]
    return L, D


def cell_values(res):
    """The cell values of every tuning column, from the tables rebuilt as prompt_ab built them (no model)."""
    import prompt_ab as pa
    head = json.loads(pa.HEAD.read_text(encoding="utf-8"))
    vals = {}
    for p, _r in tuning(res):
        _gt, _text, tabs = pa.tables_of(p, head)
        for t, _ctx, _labels in tabs:
            recs = t.data_records()
            for h in t.header_names:
                vals[(f"{p}#{t.table_index}", h)] = [str(r.get(h) or "").strip() for r in recs]
    return vals


def all_marks(values):
    cells = [x for x in values if x]
    return bool(cells) and all(MARK.fullmatch(x) for x in cells)


def shown(values):
    seen = list(dict.fromkeys(x for x in values if x))
    s = " | ".join(seen[:6]) + (f" | ... ({len(seen)} distinct)" if len(seen) > 6 else "")
    return s[:150]


def higher_rank_and_marks(res, rnd):
    """Every column reaching higher_rank in any reading of the round, and every column of marks, with their values."""
    R = [f"old.{rnd}"] + [x for x in cv.VARIANTS if x.endswith(f".{rnd}")]
    vals = cell_values(res)
    c, hr, mk = collections.Counter(), {"used": [], "none": []}, []
    for _p, r in tuning(res):
        for e in r["tables"]:
            if not all(x in e["pred"] for x in R):
                continue
            for h, (lab, _why) in e["labels"].items():
                if lab == "unsure" or any(h not in e["pred"][x] for x in R):
                    continue
                v = vals.get((e["table"], h), [])
                side = "used" if lab != "none" else "none"
                reach = [x for x in R if HIGHER in e["paths"][x].get(h, "")]
                tags = {x: e["pred"][x][h][0] for x in R}
                block = ([f"  {e['table']:26s} '{h[:40]}'  key {lab}  values: {shown(v)}"]
                         + [f"      {x:12s} {tags[x]} ({e['pred'][x][h][1]}): {e['paths'][x].get(h, '')}" for x in R])
                if reach:
                    hr[side].append("\n".join(block))
                    c[(side, "n")] += 1
                    for x in R:
                        c[(side, "reach", x)] += x in reach
                        c[(side, "right", x)] += right(tags[x] or "none", lab)
                if all_marks(v):
                    c[("mark", "n")] += 1
                    for x in R:
                        c[("mark", "verbatim", x)] += tags[x] == "verbatimIdentification"
                        c[("mark", "higher", x)] += x in reach
                    if any(tags[x] == "verbatimIdentification" for x in R):
                        mk.append("\n".join(block))
    L = [f"Columns whose path reaches {HIGHER} in any reading of round {rnd} (values from the tables):"]
    for side in ("used", "none"):
        n = c[(side, "n")]
        L.append(f"  {side:4s} {n:4d} columns   reaching it: "
                 + ", ".join(f"{x} {c[(side, 'reach', x)]}" for x in R)
                 + ("   key right: " + ", ".join(f"{x} {c[(side, 'right', x)]}" for x in R) if side == "used" else
                    "   (weak key: never the score)"))
    n = c[("mark", "n")]
    L.append(f"Columns whose cells are all marks (X, +, ✓, a dash; one or two characters): {n}. Tagged "
             f"verbatimIdentification: " + ", ".join(f"{x} {c[('mark', 'verbatim', x)]}" for x in R)
             + "; through higher_rank: " + ", ".join(f"{x} {c[('mark', 'higher', x)]}" for x in R))
    L.append("")
    D = [f"######## round {rnd}: columns reaching {HIGHER} in any reading",
         f"## used (reliable key): {len(hr['used'])}"] + hr["used"]
    D += [f"## none (weak key): {len(hr['none'])}"] + hr["none"]
    D += [f"## columns of marks tagged verbatimIdentification in any reading: {len(mk)}"] + mk + [""]
    return L, D


def main(rnd="3"):
    BASE = f"old.{rnd}"
    res = json.loads((OUT / "results.json").read_text(encoding="utf-8"))
    L = [f"Column tree, structural revision (column_variants.py), round {rnd}: each variant against {BASE} (the adopted tree read "
         "again in the same session). Tuning papers only. 'used' = the GT draws on the column (reliable key); 'none' "
         "= the GT does not use it (weak key, never the score).", ""]
    D = []
    control = getattr(cv, "CONTROL", {})
    for v in [x for x in cv.VARIANTS if x.endswith(f".{rnd}")]:
        a, b = compare(res, v, BASE, v)
        L, D = L + a, D + b
        if v in control:
            a, b = compare(res, v, control[v], f"{v} against {control[v]} (its control, same session)")
            L, D = L + a, D + b
    if int(rnd) >= 5:
        a, b = higher_rank_and_marks(res, rnd)
        L, D = L + a, D + b
    (OUT / f"TREE_AB_{rnd}.txt").write_text("\n".join(L + ["", "DETAIL", ""] + D) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main(*sys.argv[1:2])
