"""Where each layer fires (REVIEW_Opus5.5xtra_2026-11-16, section 2). A held_b result says little when a layer never
acted on a held_b paper: from v7 to v14 the held_b mean did not move at all. Files only, no model.

  rows      per version, per group: the papers whose rows (species, trait, value, unit, statistic) differ from the
            version before, and the rows added or removed
  layers    per v24 layer, per group: the papers, tables and columns it acted on, from its saved decisions
Groups: dev, held_a (tuning), held_b, and grit-only for papers outside split_v15.json. Paper names are printed for
tuning papers only.

    python fires.py [papers]         TREE_OUTPUT picks the root (grit: output_grit)
-> <root>/full_run_v24_logs/FIRES.txt
"""
import collections
import csv
import json
import sys

import _paths

OUT = _paths.OUTPUT
SPLIT = json.loads((_paths.SUB / "output/eval_split/split_v15.json").read_text(encoding="utf-8"))["assign"]
GROUPS = ("dev", "held_a", "held_b", "grit-only")
VERSIONS = ["full_run", "full_run_v3", "full_run_v4", "full_run_v6", "full_run_v7", "full_run_v8", "full_run_v9",
            "full_run_v11", "full_run_v12", "full_run_v13", "full_run_v14", "full_run_v15", "full_run_v16", "full_run_v17",
            "full_run_v18", "full_run_v24_units", "full_run_v24_account+rowlabel", "full_run_v24_relevance",
            "full_run_v24_legend", "full_run_v24"]
KEY = ("verbatimIdentification", "measurementType", "measurementValue", "measurementUnit", "measurementStatistic")
DROP = ("identifier", "genetic", "count", "statistic")


def group(p):
    return SPLIT.get(p, "grit-only")


def rows(v, p):
    f = OUT / v / p / f"{p}.csv"
    if not f.exists():
        return None
    with open(f, encoding="utf-8", newline="") as fh:
        return collections.Counter(tuple((r.get(k) or "").strip() for k in KEY) for r in csv.DictReader(fh))


def load(d, p):
    f = OUT / "full_run_v24" / d / f"{p}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def layer_counts(p):
    """{layer: (tables acted on, columns or cells acted on)} from v24's saved decisions."""
    out = {}
    u = load("units", p)
    cols = [k for k, r in (u.get("columns") or {}).items() if r.get("unit")]
    cells = [k for k, r in (u.get("cells") or {}).items() if r.get("unit")]
    out["units"] = (len({k.split("|")[0] for k in cols}), len(cols) + len(cells))
    a = load("account", p)
    given = [k for k, r in a.items() if isinstance(r, dict) and r.get("species")]
    out["account"] = (len(given), 0)
    r = load("relevance", p)
    out_cols = [k for k, d in (r.get("columns") or {}).items() if not d.get("keep")]
    out_tabs = [k for k, d in (r.get("organism") or {}).items() if d.get("drop")]
    lifted = [k for k, d in (r.get("also") or {}).items() if d.get("lift")]
    once = [k for k, d in (r.get("level") or {}).items() if d.get("once")]
    out["relevance: columns out"] = (len({k.split("|")[0] for k in out_cols}), len(out_cols))
    out["relevance: tables of other organisms"] = (len(out_tabs), 0)
    out["relevance: sampling tables read again"] = (len(lifted), 0)
    out["relevance: written once per species"] = (len({k.split("|")[0] for k in once}), len(once))
    rl = load("row_label", p)
    roles = [k for k, d in rl.items() if (d.get("labels") or {}).get("roles")]
    objs = [k for k, d in rl.items() if (d.get("object") or {}).get("object")]
    out["rowlabel: row labels used"] = (len(roles), 0)
    out["rowlabel: measured object"] = (len(objs), 0)
    lc = load("legend_check", p)
    rej = [k for k, d in lc.items() if d.get("reject")]
    out["legend: columns not decoded"] = (len({k.split(":")[0] for k in rej}), len(rej))
    return out


def main(argv):
    papers = argv or sorted(d.name for d in (OUT / "full_run_v18").iterdir() if (d / f"{d.name}.csv").exists())
    n = collections.Counter(group(p) for p in papers)
    L = [f"Where each layer fires, {OUT.name}: " + ", ".join(f"{g} {n[g]}" for g in GROUPS if n[g]) + " papers", "",
         "ROWS: papers whose rows differ from the version before (rows added + removed)"]
    L.append(f"  {'version':32s}" + "".join(f"{g:>22s}" for g in GROUPS if n[g]))
    prev, names = None, collections.defaultdict(list)
    for v in VERSIONS:
        if not (OUT / v).is_dir():
            continue
        base = "full_run_v18" if v.startswith("full_run_v24") else prev
        if base is None:
            prev = v
            continue
        cnt, moved = collections.Counter(), collections.Counter()
        for p in papers:
            a, b = rows(base, p), rows(v, p)
            if a is None or b is None or a == b:
                continue
            g = group(p)
            cnt[g] += 1
            moved[g] += sum(((a - b) + (b - a)).values())
            if g in ("dev", "held_a"):
                names[v].append(p)
        label = f"{v} (vs {base.replace('full_run_', '') if base != 'full_run' else 'base'})"
        L.append(f"  {label:32s}" + "".join(f"{f'{cnt[g]} ({moved[g]})':>22s}" for g in GROUPS if n[g]))
        if not v.startswith("full_run_v24"):
            prev = v
    L += ["", "LAYERS (v24): papers / tables / columns or cells each layer acted on"]
    tot = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0, 0]))
    for p in papers:
        for layer, (tabs, items) in layer_counts(p).items():
            t = tot[layer][group(p)]
            t[0] += bool(tabs or items)
            t[1] += tabs
            t[2] += items
    L.append(f"  {'layer':40s}" + "".join(f"{g:>20s}" for g in GROUPS if n[g]))
    for layer, by in tot.items():
        L.append(f"  {layer:40s}" + "".join(f"{'/'.join(str(x) for x in by[g]):>20s}" for g in GROUPS if n[g]))
    L += ["", "Tuning papers whose rows changed, per version:"]
    L += [f"  {v}: {', '.join(ps)}" for v, ps in names.items() if ps]
    out = OUT / "full_run_v24_logs" / "FIRES.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:L.index("Tuning papers whose rows changed, per version:")]))


if __name__ == "__main__":
    main(sys.argv[1:])
