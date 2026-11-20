"""Session 3 of prompt_ab.py (column_variants.py: A, B, C, D, F alone and all), read column by column: for every
variant against 'old.3' (the adopted tree read again in the same session), tuning papers only (dev + held_a).

  used columns   (the GT draws on them, the reliable key) right before and after, every change with both paths,
                 probabilities and the key's evidence; the columns wrong before, with their new path
  none columns   (the GT does not use them: weak key) counted apart, never as the score; a fixed random sample of the
                 changed ones, both paths, for reading by hand
  papers         Gathof2022, Ji2024, Luo2023, Viza2023, Wallon2024: every column whose path changed (the user's list)
  cost           questions on each column's chosen path, old and new (the explored runner-up branches come on top)

    python tree_ab_report.py      -> output/prompt_ab/TREE_AB_3.txt
"""
import collections
import json
import random

import _paths
import column_variants as cv

OUT = _paths.OUTPUT / "prompt_ab"
SPLIT = json.loads((_paths.SUB / "output/eval_split/split_v15.json").read_text(encoding="utf-8"))["assign"]
TRAITS = {"measurementType", "measurementValue"}
BASE = "old.3"
LOOK = ("Gathof2022", "Ji2024", "Luo2023", "Viza2023", "Wallon2024")


def right(tag, lab):
    return tag == lab or (tag in TRAITS and lab in TRAITS)


def asked(path):
    return sum(1 for s in (path or "").split(" > ") if s and not s.startswith("code:") and ":by table kind" not in s)


def main():
    res = json.loads((OUT / "results.json").read_text(encoding="utf-8"))
    L = ["Column tree, structural revision (column_variants.py), each variant against old.3 (the adopted tree read "
         "again in the same session). Tuning papers only. 'used' = the GT draws on the column (reliable key); 'none' "
         "= the GT does not use it (weak key, never the score).", ""]
    D = []
    for v in cv.VARIANTS:
        c, used_flips, wrong_before, none_flips, look = collections.Counter(), [], [], [], []
        for p, r in sorted(res.items()):
            if SPLIT.get(p) not in ("dev", "held_a"):
                continue
            for e in r["tables"]:
                if v not in e["pred"] or BASE not in e["pred"]:
                    continue
                for h, (lab, why) in e["labels"].items():
                    if lab == "unsure" or h not in e["pred"][BASE] or h not in e["pred"][v]:
                        continue
                    (t0, p0), (t1, p1) = e["pred"][BASE][h], e["pred"][v][h]
                    a, b = e["paths"][BASE].get(h, ""), e["paths"][v].get(h, "")
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
        L.append(f"== {v}")
        for side in ("used", "none"):
            n = c[(side, "n")]
            if n:
                L.append(f"  {side:4s} {n:5d} columns  right {c[(side, 'right before')] / n:6.1%} -> "
                         f"{c[(side, 'right after')] / n:6.1%}   changed {c[(side, 'changed')]:3d} (to right "
                         f"{c[(side, 'to right')]}, to wrong {c[(side, 'to wrong')]})   questions on the path "
                         f"{c[(side, 'asked before')] / n:.2f} -> {c[(side, 'asked after')] / n:.2f} per column")
        L.append("")
        D += [f"######## {v}", f"## used columns that changed: {len(used_flips)}"] + used_flips
        D += [f"## used columns wrong before (old.3), with their path now: {len(wrong_before)}"] + wrong_before
        sample = random.Random(20261120).sample(none_flips, min(40, len(none_flips)))
        D += [f"## none columns that changed: {len(none_flips)}; a fixed sample of {len(sample)} for reading by hand"]
        D += sample
        D += [f"## {', '.join(LOOK)}: every column whose path changed: {len(look)}"] + look + [""]
    (OUT / "TREE_AB_3.txt").write_text("\n".join(L + ["", "DETAIL", ""] + D) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
