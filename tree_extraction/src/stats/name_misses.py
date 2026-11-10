"""8A evidence (plans/08_evaluation.md): trait-name pairs the scorer leaves apart. Files only, no model.

A row of ours beyond the GT whose species and value equal a missed GT row of the same paper is, most often, the same
fact under a name the scorer did not pair (or under a wrong name). Counted per (our name, GT name) pair after the
scorer's steps are replayed as in beyond_gt.py.

  pairs      tuning papers (dev, held_a): each pair with its rows and how the scorer's normaliser sees both names
  totals     per group: rows beyond the GT, of them with a missed GT twin (same species, same value)

    python name_misses.py      -> tree_extraction/output/eval_split/stats/name_misses.json
"""
import collections
import json

import beyond_gt as bg

ev = bg.ev
from trait_name_matcher import normalize            # noqa: E402  (source/ is on the path through beyond_gt)


def main():
    groups = collections.defaultdict(collections.Counter)
    pairs = []
    for p in sorted(bg.SPLIT):
        g = bg.SPLIT[p]
        pred_f = bg.OUT / "two_step" / p / f"{p}.csv"
        gt_f = bg.PAPERS / p / f"{p}.xlsx"
        if not (pred_f.exists() and gt_f.exists()):
            continue
        gt, pred = ev.load_xlsx(str(gt_f)), ev.load_csv(str(pred_f))
        pred, _sm, _su = ev.remap_pred_species(gt, pred)
        tm = bg.type_map(bg.OUT / "two_step" / p / f"{p}_report.txt")
        for r in pred:
            if r.get("measurementType") in tm:
                r["measurementType"] = tm[r["measurementType"]]
        matched, missing, extra = ev.match_rows(gt, pred, ev.DEFAULT_KEY, False)
        scope = ev.build_scope(gt, ["measurementType"], False)
        _ins, oos = ev.partition_extra(extra, scope, False)
        twin = collections.defaultdict(list)          # (species, value) -> missed GT names
        for r in missing:
            twin[(bg.flat(r.get("verbatimIdentification")), ev.normalize_value(r.get("measurementValue")))].append(
                bg.flat(r.get("measurementType")))
        cnt = collections.Counter()
        rows = [r for r, _u in oos]
        for r in rows:
            k = (bg.flat(r.get("verbatimIdentification")), ev.normalize_value(r.get("measurementValue")))
            for gname in dict.fromkeys(twin.get(k, [])):
                cnt[(bg.flat(r.get("measurementType")), gname)] += 1
        c = groups[g]
        c["papers"] += 1
        c["beyond GT"] += len(rows)
        c["beyond GT with a missed GT twin"] += sum(bool(twin.get((bg.flat(r.get("verbatimIdentification")),
                                                                    ev.normalize_value(r.get("measurementValue")))))
                                                    for r in rows)
        if g not in ("dev", "held_a"):
            continue
        gt_rows = collections.Counter(bg.flat(r.get("measurementType")) for r in gt)
        for (ours, gname), n in cnt.items():
            if n >= 3 and n >= 0.3 * gt_rows[gname]:       # a name-level pairing, not values that happen to agree
                pairs.append({"paper": p, "group": g, "ours": ours, "gt": gname, "rows": n, "gt_rows": gt_rows[gname],
                              "ours_norm": normalize(ours), "gt_norm": normalize(gname)})
    pairs.sort(key=lambda x: -x["rows"])
    res = {"totals": {g: dict(c) for g, c in groups.items()}, "pairs": pairs}
    (bg.OUT / "eval_split/stats/name_misses.json").write_text(json.dumps(res, indent=1, ensure_ascii=False),
                                                             encoding="utf-8")
    for g, c in groups.items():
        print(g, dict(c))
    print(len(pairs), "pairs on tuning papers")


if __name__ == "__main__":
    main()
