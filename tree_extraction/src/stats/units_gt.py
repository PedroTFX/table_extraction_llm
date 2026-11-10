"""Fix 1, step 0 (plans/01_units.md): where the GT's measurementUnit is, against our rows. Files only, no model.

On the scorer's matched rows (two_step run, the scorer's steps replayed as in beyond_gt.py):
  gt unit        the GT row has a unit; ours has one; they agree (the scorer's normalize_value)
  in our name    the unit sits in our trait name: a trailing bracket, or the part after the last comma
                 ("Width (mm)", "Mass [mg]", "Body length, mm"); the bracket equals the GT unit or not
  in gt name     the GT keeps a bracket in its own trait name too ("Development rate (year)")
  name only      our name holds a bracket while the GT row has no unit
Totals per group; per paper and examples for tuning papers only (dev, held_a).

    python units_gt.py      -> tree_extraction/output/eval_split/stats/units_gt.json
"""
import collections
import json
import re

import beyond_gt as bg

ev = bg.ev
TAIL = re.compile(r"^(.*?)\s*(?:[\(\[]([^()\[\]]{1,25})[\)\]]|,\s*([^,]{1,12}))\s*$")


def tail_unit(name):
    """The candidate unit at the end of a trait name, else ''."""
    m = TAIL.match(bg.flat(name))
    return bg.flat(m[2] or m[3]) if m else ""


def same(a, b):
    k = lambda s: re.sub(r"[\s.]", "", str(s).lower().replace("μ", "µ"))
    return bool(a) and k(a) == k(b)


def main():
    groups = collections.defaultdict(collections.Counter)
    papers, gt_units = {}, collections.Counter()
    for p in sorted(bg.SPLIT):
        g = bg.SPLIT[p]
        pred_f = bg.OUT / "two_step" / p / f"{p}.csv"
        gt_f = bg.PAPERS / p / f"{p}.xlsx"
        if not (pred_f.exists() and gt_f.exists()):
            continue
        gt, pred = ev.load_xlsx(str(gt_f)), ev.load_csv(str(pred_f))
        for r in pred:
            r["_name"] = r.get("measurementType")              # our printed name, before the scorer's renaming
        pred, _sm, _su = ev.remap_pred_species(gt, pred)
        tm = bg.type_map(bg.OUT / "two_step" / p / f"{p}_report.txt")
        for r in pred:
            if r.get("measurementType") in tm:
                r["measurementType"] = tm[r["measurementType"]]
        matched, _missing, _extra = ev.match_rows(gt, pred, ev.DEFAULT_KEY, False)
        c, pc, ex = groups[g], collections.Counter(), collections.Counter()
        for gr, pr in matched:
            gu = bg.flat(gr.get("measurementUnit"))
            pu = bg.flat(pr.get("measurementUnit"))
            cand = tail_unit(pr["_name"])
            k = collections.Counter({"matched": 1})
            if gu:
                k["gt unit"] += 1
                k["gt unit, ours set"] += bool(pu)
                k["gt unit, ours agrees"] += ev.normalize_value(gu) == ev.normalize_value(pu)
                k["gt unit, bracket in our name"] += bool(cand)
                k["gt unit, bracket in our name = gt unit"] += same(cand, gu)
                k["gt unit, bracket in gt name"] += bool(tail_unit(gr.get("measurementType")))
                k["gt unit, no bracket in our name"] += not cand
                if g in ("dev", "held_a"):
                    gt_units[gu] += 1
                    if not same(cand, gu):
                        ex[(gu, bg.flat(pr["_name"]), bg.flat(gr.get("measurementType")))] += 1
            elif cand:
                k["no gt unit, bracket in our name"] += 1
                if g in ("dev", "held_a"):
                    ex[("", bg.flat(pr["_name"]), bg.flat(gr.get("measurementType")))] += 1
            c.update(k)
            pc.update(k)
        c["papers"] += 1
        c["papers with gt units"] += bool(pc["gt unit"])
        if g in ("dev", "held_a"):
            papers[p] = {"group": g, **pc,
                         "examples": [{"gt_unit": a, "our_name": b, "gt_name": n, "rows": m}
                                      for (a, b, n), m in ex.most_common(6)]}
    res = {"totals": {g: dict(c) for g, c in groups.items()}, "gt_units_tuning": gt_units.most_common(60),
           "papers": papers}
    f = bg.OUT / "eval_split/stats/units_gt.json"
    f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    for g, c in groups.items():
        print(g, dict(c))


if __name__ == "__main__":
    main()
