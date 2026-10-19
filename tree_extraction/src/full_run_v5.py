"""v5 = v4 (species-column questions, frozen) + the trait-column questions (trait_tree.py,
eval_split/DESIGN_traits.md).

Builds output/full_run_v5 on top of output/full_run_v4 (tags, meaning, decode, species,
organism copied; v4 stays as it was). Stages, each resumable:
  traits    Q-COL / Q-VALUE per table that gives rows
  assemble  v3's assembly with the trait answers applied to the tags
  score     evaluate_all on the papers whose CSV changed, compared with v4; the column check

    python full_run_v5.py <stage> dev|held|all|<paper ...>
"""
import collections
import contextlib
import io
import json
import shutil
import sys

import _paths
import full_run as fr
import full_run_v3 as r3
import full_run_v4 as r4
import species_missed as sm
import species_tree as sp
import trait_tree as tt

import os

V4 = fr.OUT.parent / "full_run_v4"
OUT = fr.OUT.parent / "full_run_v5"
CONSERVATIVE = os.environ.get("TRAIT_MODE") == "conservative"
if CONSERVATIVE:               # same answers, only identifier / organism / other dropped, no long
    tt.MODE = "conservative"
    OUT = fr.OUT.parent / "full_run_v5c"
SPLIT = r4.SPLIT
sys.path.insert(0, str(_paths.REPO / "source"))


def setup():
    OUT.mkdir(parents=True, exist_ok=True)
    for d in ("tags", "meaning", "decode", "species", "organism"):
        if not (OUT / d).exists() and (V4 / d).exists():
            shutil.copytree(V4 / d, OUT / d)
    full = fr.OUT.parent / "full_run_v5"
    if CONSERVATIVE and (full / "traits").exists():   # the answers of the full run, re-copied
        if (OUT / "traits").exists():
            shutil.rmtree(OUT / "traits")
        shutil.copytree(full / "traits", OUT / "traits")


def install(apply_traits=True):
    """v4's species wiring on OUT, then the trait answers applied to each table's tags."""
    r4.OUT = OUT
    r4.install()
    plan = fr.plan
    cache = {}

    def plan_with_traits(paper, head):
        out = plan(paper, head)
        if paper not in cache:
            f = OUT / "traits" / f"{paper}.json"
            cache[paper] = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
        if not apply_traits:
            return out
        res = []                                   # a long table: two readings, same records
        for t, fields, org, x in out:
            for f in tt.expand(fields, cache[paper].get(str(t.table_index))):
                res.append((t, f, org, x))
        return res

    fr.plan = plan_with_traits


def has_species(t, fields, org):
    if any(fr.species_of(t, fields, org, r) for r in t.records):
        return True
    return bool(sp.species_of_tables(OUT / "species", getattr(t, "paper", "")).get(t.table_index))


def stage_traits(papers):
    setup()
    install(apply_traits=False)
    tt.run(OUT, papers, has_species)


def stage_assemble(papers):
    setup()
    install()
    r3.OUT, r3.BASE = OUT, V4
    r3.stage_assemble(papers)


def stage_score(papers):
    r3.OUT, r3.BASE = OUT, V4
    r3.stage_score(papers)
    r4.OUT, r4.V3 = OUT, V4                     # rebuild + compare: v5 against v4
    r4.rebuild_summary()
    r4.compare(papers)
    shutil.copy(OUT / "COMPARE_V4.txt", OUT / "COMPARE_V5.txt")
    col_check(papers)


# --- the column check against the GT ---------------------------------------------------------

def gt_values(paper):
    import evaluate as ev
    from mineru_extract import classify_folder
    with contextlib.redirect_stdout(io.StringIO()):
        _, gt, _ = classify_folder(_paths.PAPERS / paper)
        rows = ev.load_xlsx(gt)
    out = collections.defaultdict(set)
    for r in rows:
        k = sm._key(r.get("verbatimIdentification"))
        if k:
            out[k].add(ev.normalize_value(r.get("measurementValue", "")))
    return out


def col_check(papers):
    """Per decided column: do its cells (with the row's species) equal GT values?"""
    import evaluate as ev
    setup()
    install(apply_traits=False)
    head = fr.head_runs()
    tally = collections.Counter()
    lines = []
    for p in papers:
        f = OUT / "traits" / f"{p}.json"
        if not f.exists() or p not in head:
            continue
        dec = json.loads(f.read_text(encoding="utf-8"))
        try:
            gv = gt_values(p)
        except Exception:
            continue
        named = sp.species_of_tables(OUT / "species", p)
        for t, fields, org, _x in fr.plan(p, head):
            d = dec.get(str(t.table_index))
            if not d:
                continue
            for name, c in d["cols"].items():
                hits = n = 0
                for r in t.records:
                    s = fr.species_of(t, fields, org, r) or named.get(t.table_index, "")
                    v = _flat(r.get(name))
                    if not s or not v:
                        continue
                    n += 1
                    k = sm._key(s)
                    hits += bool(k and ev.normalize_value(v) in gv.get(k, ()))
                gt = hits > 0
                kept = c["applied"] not in (tt.CONSERVATIVE_DROP if tt.MODE == "conservative" else tt.DROP)
                kind = ("kept, GT values" if kept and gt else "kept, no GT values" if kept else
                        "DROPPED, GT values (loss)" if gt else "dropped, no GT values")
                tally[(SPLIT["assign"].get(p), kind)] += 1
                if kind.startswith("DROPPED"):
                    lines.append(f"  {p:20s} t{t.table_index:<3} '{name[:28]}' {c['choice']} "
                                 f"{max(c['probs'].values()):.2f}: {hits}/{n} cells are GT values")
            if d.get("long"):
                lines.append(f"  {p:20s} t{t.table_index:<3} long: type '{d['long']['type']}', "
                             f"values {d['long'].get('values') or [d['long'].get('value')]}")
    text = ["trait columns vs GT (cells equal to a GT value of the row's species)", ""]
    for s in ("dev", "held"):
        text.append(f"{s}: " + ", ".join(f"{k} {v}" for (h, k), v in sorted(tally.items()) if h == s))
    text += [""] + lines
    (OUT / "trait_columns_eval.txt").write_text("\n".join(text) + "\n", encoding="utf-8")
    print("\n".join(text[:4]))


def _flat(s):
    return " ".join(str(s or "").split())


def main(argv):
    stage, papers = argv[0], r4.papers_of(argv[1:])
    {"traits": stage_traits, "assemble": stage_assemble, "score": stage_score,
     "check": col_check}[stage](papers)


if __name__ == "__main__":
    main(sys.argv[1:])
