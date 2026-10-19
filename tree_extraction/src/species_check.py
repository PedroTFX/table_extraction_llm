"""Checks species_tree's answers against the GT, paper by paper. Reads saved files only.

The GT gives the expected paper-level answer: one distinct verbatimIdentification ->
'one' and that species; more -> 'several' (then no table may get a paper-level name).

    python species_check.py key              build output/full_run_v3/species_key.json
    python species_check.py check P [P ...]  one verdict line per paper
    python species_check.py summary          all papers with a species file
"""
import json
import sys
from pathlib import Path

import _paths

HERE = Path(__file__).resolve().parent
RUN = HERE.parent / "output" / "full_run_v3"
KEY = RUN / "species_key.json"
sys.path.insert(0, str(_paths.REPO / "source"))


def build_key():
    import contextlib
    import io
    import evaluate as ev
    from mineru_extract import classify_folder
    import full_run as fr
    key = {}
    for p in fr.gt_papers():
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                _, gt, _ = classify_folder(_paths.PAPERS / p)
                rows = ev.load_xlsx(gt)
        except Exception:
            continue
        names = sorted({" ".join(str(r.get("verbatimIdentification") or "").split()) for r in rows} - {""})
        key[p] = {"n_species": len(names), "expected": "one" if len(names) == 1 else "several",
                  "species": names[0] if len(names) == 1 else None}
    KEY.write_text(json.dumps(key, indent=1, ensure_ascii=False), encoding="utf-8")
    return key


def verdict(p, key=None):
    import evaluate as ev
    key = key or json.loads(KEY.read_text(encoding="utf-8"))
    f = RUN / "species" / f"{p}.json"
    if p not in key or not f.exists():
        return None
    st = json.loads(f.read_text(encoding="utf-8"))
    k = key[p]
    gate = (st.get("paper") or {}).get("answer") or "open"
    named = sorted({x["species"] for x in st["tables"].values() if x.get("species")})
    n_t = len(st["tables"])
    if k["expected"] == "one":
        if named and all(ev.species_match(n, k["species"]) for n in named):
            n_ok = sum(1 for x in st["tables"].values() if x.get("species"))
            v = f"RIGHT  one species, named '{named[0]}' on {n_ok}/{n_t} tables"
        elif named:
            v = f"WRONG  GT '{k['species']}', code named {named}"
        else:
            v = f"MISSED GT one species '{k['species']}', code: {gate}, no name"
    else:
        if named:
            v = f"WRONG  GT {k['n_species']} species, code named {named} (gate {gate})"
        else:
            v = f"RIGHT  GT {k['n_species']} species, code: {gate}, no name given"
    return f"{p:22s} {v}"


def main(argv):
    if argv[0] == "key":
        k = build_key()
        print(f"{len(k)} papers; one species: {sum(v['expected'] == 'one' for v in k.values())}")
    elif argv[0] == "check":
        key = json.loads(KEY.read_text(encoding="utf-8"))
        for p in argv[1:]:
            v = verdict(p, key)
            if v:
                print(v, flush=True)
    elif argv[0] == "summary":
        key = json.loads(KEY.read_text(encoding="utf-8"))
        out = [verdict(f.stem, key) for f in sorted((RUN / "species").glob("*.json"))]
        out = [v for v in out if v]
        for v in out:
            print(v)
        for w in ("RIGHT", "WRONG", "MISSED"):
            print(f"{w}: {sum(1 for v in out if v.split()[1] == w)}")


if __name__ == "__main__":
    main(sys.argv[1:])
