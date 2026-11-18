"""species_ab.py — the species tree's READ prompt, old examples against new (species_variants.py).

  papers   the tuning papers (dev + held_a of split_v15.json) where the full run's species step had tables to
           settle (output/full_run_v4/species/<paper>.json with tables)
  run      the species step as the full run runs it (full_run_v24.install(V4, decisions=True), species_tree.run_paper:
           gemma reads the sections, nimble answers the gate and the tables), once with the current READ ('old')
           and once with the new one, in one session
  key      the GT's species of the paper (verbatimIdentification, matched as column_role_bench.species_match)
  score    per table: a paper with ONE GT species -> named right / named wrongly / no name; a paper with several ->
           named a GT species / named another / no name. Per paper: the names gemma read include a GT species,
           and how many read names match none. 'stored': the last full run (an earlier session), a drift reference

    python species_ab.py run [variant ...]     resumable: output/species_ab/<variant>/<paper>.json
    python species_ab.py score                 -> output/species_ab/SCORE.txt
"""
import collections
import contextlib
import json
import sys

import _paths
import column_role_bench as crb
import full_run as fr
import species_tree as sp
import species_variants as sv
from evaluate import load_xlsx

OUT = _paths.OUTPUT / "species_ab"
STORED = _paths.OUTPUT / "full_run_v4" / "species"
SPLIT = json.loads((_paths.SUB / "output/eval_split/split_v15.json").read_text(encoding="utf-8"))["assign"]
TUNING = ("dev", "held_a")
ORDER = ["old", "read"]


@contextlib.contextmanager
def applied(variant):
    saved = {k: getattr(sp, k) for k in ("READ",)}
    try:
        for k, text in sv.VARIANTS.get(variant, {}).items():
            setattr(sp, k, text)
        yield
    finally:
        for k, text in saved.items():
            setattr(sp, k, text)


def papers():
    out = []
    for f in sorted(STORED.glob("*.json")):
        if SPLIT.get(f.stem) in TUNING and json.loads(f.read_text(encoding="utf-8")).get("tables"):
            out.append(f.stem)
    return out


def run(variants):
    import full_run_v24 as f24
    f24.install(f24.V4, decisions=True)
    head = fr.head_runs()
    for p in papers():
        if p not in head:
            continue
        for v in ["old"] + [x for x in variants if x != "old"]:
            d = OUT / v
            d.mkdir(parents=True, exist_ok=True)
            if (d / f"{p}.json").exists():
                continue
            with applied(v):
                sp.run_paper(p, head, d)
            print(f"  [species_ab] {v:5s} done {p}", flush=True)


def gt_ids(p):
    inputs = crb.paper_inputs(crb.PAPERS / p)
    return crb.GroundTruth(load_xlsx(inputs[1])).ids if inputs else []


def match(name, ids):
    return bool(name) and any(crb.species_match(name, g) for g in ids)


def score():
    variants = ["stored"] + [v for v in ORDER if (OUT / v).exists()]
    ids = {p: gt_ids(p) for p in papers()}
    res = {}
    for v in variants:
        d = STORED if v == "stored" else OUT / v
        c, per = collections.Counter(), {}
        for p, gi in ids.items():
            f = d / f"{p}.json"
            if not f.exists():
                continue
            st = json.loads(f.read_text(encoding="utf-8"))
            one = len(gi) == 1
            names = []
            for rd in (st.get("reads") or {}).values():
                names += [n for n in rd.get("organisms") or [] if n not in names]
            for g in ("all", SPLIT[p]):
                c[(g, "papers")] += 1
                c[(g, "read has GT")] += any(match(n, gi) for n in names)
                c[(g, "read names")] += len(names)
                c[(g, "read not GT")] += sum(not match(n, gi) for n in names)
            got = {}
            for k, x in (st.get("tables") or {}).items():
                s = x.get("species")
                out = ("right" if match(s, gi) else "wrong name") if s else "no name"
                side = "one" if one else "several"
                if not one and s:
                    out = "a GT species" if match(s, gi) else "another"
                for g in ("all", SPLIT[p]):
                    c[(g, side, "tables")] += 1
                    c[(g, side, out)] += 1
                got[k] = (s, x.get("answer"))
            per[p] = got
        res[v] = (c, per)
    L = ["Species tree READ prompt: old examples against new. Key: the GT's species (verbatimIdentification).",
         "Tables the species step had to settle; papers with ONE GT species (a name is right or wrong) and with",
         "several. 'stored' is the last full run (an earlier session): a drift reference for 'old'.", ""]
    for v in variants:
        c, _ = res[v]
        L.append(f"== {v}")
        for g in ("all",) + TUNING:
            if not c[(g, "papers")]:
                continue
            L.append(f"  {g:6s} {c[(g, 'papers')]:3d} papers  read names include a GT species: "
                     f"{c[(g, 'read has GT')]}   read names {c[(g, 'read names')]}, matching none "
                     f"{c[(g, 'read not GT')]}")
            L.append(f"         one GT species: {c[(g, 'one', 'tables')]} tables  right {c[(g, 'one', 'right')]}, "
                     f"wrong name {c[(g, 'one', 'wrong name')]}, no name {c[(g, 'one', 'no name')]}")
            L.append(f"         several GT species: {c[(g, 'several', 'tables')]} tables  a GT species "
                     f"{c[(g, 'several', 'a GT species')]}, another {c[(g, 'several', 'another')]}, no name "
                     f"{c[(g, 'several', 'no name')]}")
        L.append("")
    L.append("Tables that changed against 'old' (species, answer):")
    base = res.get("old", (None, {}))[1]
    for v in variants:
        if v == "old":
            continue
        for p, got in res[v][1].items():
            for k, now in got.items():
                was = base.get(p, {}).get(k)
                if was is not None and was != now:
                    L.append(f"  {v:7s} {p:22s} t{k}: {was} -> {now}")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "SCORE.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


def main(argv):
    if argv[:1] == ["score"]:
        return score()
    variants = argv[1:] or ORDER[1:]
    assert all(v in sv.VARIANTS for v in variants), f"unknown variants; known: {list(sv.VARIANTS)}"
    run(variants)


if __name__ == "__main__":
    main(sys.argv[1:])
