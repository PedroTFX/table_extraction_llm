"""grit_run.py — the whole tree_extraction chain (head reader -> v7) on data/grit_testing,
start to finish, in its own output root (tree_extraction/output_grit): every stage caches
by paper name and 99 grit folders share a name with un_processed_papers.

Blind run: the head reader's body-row check runs on every table (the GT-keyed bench ran it
only on tables the GT draws on), and nothing reads a GT before the score stage.

Stages in order, each resumable (one model at a time, as in the original runs): the head
reader (head_more -> header_tree_bench/experiments), then every stage of full_run_v11.py
(standalone: base -> full_run/, v3 -> full_run_v3/, v4, v6, v7, v8, v9, v11 -> full_run_v11/), then score
(evaluate_all on the v7 CSVs of the papers with a GT xlsx):
  head  base:tag  base:meaning  base:inventory  base:decode  v3:decode  v3:endings  v3:species
  v4:organism  v4:species  v6:structure  v7:kind  v7:decode  v7:meaning  v8:sections  v9:names  v11:names  v11:species  assemble  score

    python grit_run.py all            every stage
    python grit_run.py <stage> ...    from that stage on (papers: every folder with a _full.md)
"""
import json
import os
import sys
import time
from pathlib import Path

REPO = next(p for p in Path(__file__).resolve().parents if p.name == "tree_extraction").parent
os.environ.setdefault("TREE_PAPERS", str(REPO / "data" / "grit_testing"))
os.environ.setdefault("TREE_OUTPUT", str(REPO / "tree_extraction" / "output_grit"))

import _paths  # noqa: E402
import column_role_bench as crb  # noqa: E402


def papers():
    return sorted(d.name for d in _paths.PAPERS.iterdir()
                  if d.is_dir() and (d / f"{d.name}_full.md").exists())


def _inputs(folder):
    """(full markdown, GT xlsx or None): papers without a GT still run."""
    folder = Path(folder)
    full = folder / f"{folder.name}_full.md"
    if not full.exists():
        return None
    gts = [f for f in folder.iterdir() if f.suffix.lower() == ".xlsx"
           and f.stem.replace("-", "").lower() == folder.name.replace("-", "").lower()]
    return full, (gts[0] if gts else None)


crb.paper_inputs = _inputs


def split():
    f = _paths.OUTPUT / "eval_split" / "split.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({"note": "grit_testing: every paper, no dev/held split",
                             "assign": {p: "grit" for p in papers()}}, indent=1), encoding="utf-8")


def stage_head(ps):
    import head_more as hm
    import header_tree_bench as hb
    hm.he.EXP.mkdir(parents=True, exist_ok=True)
    if not hm.BENCH.exists():
        hm.BENCH.write_text("{}", encoding="utf-8")
    hb.keyed_tables = lambda p: set(range(len(hb.html_tables(p))))   # body check everywhere
    hm.main(ps)


def run(stage, ps):
    if stage == "head":
        return stage_head(ps)
    if stage == "score":
        return score(ps)
    import full_run_v11 as r11
    return r11.main([stage, *ps])


STAGES = ["head", "base:tag", "base:meaning", "base:inventory", "base:decode", "v3:decode",
          "v3:endings", "v3:species", "v4:organism", "v4:species", "v6:structure", "v7:kind",
          "v7:decode", "v7:meaning", "v8:sections", "v9:names", "v11:names", "v11:species", "assemble", "score"]
# the names the log used before full_run_v7 was made standalone
OLD_NAMES = {"tag": "base:tag", "meaning": "base:meaning", "inventory": "base:inventory",
             "decode": "base:decode", "decode3": "v3:decode", "endings": "v3:endings",
             "species3": "v3:species", "organism": "v4:organism", "species4": "v4:species",
             "structure": "v6:structure", "kind": "v7:kind", "decode7": "v7:decode",
             "meaning7": "v7:meaning"}


def score(ps):
    import evaluate as ev
    import full_run_v11 as r11
    ev.ASSESS_MISS_SEVERITY = False
    with_gt = [p for p in ps if (_inputs(_paths.PAPERS / p) or (None, None))[1]]
    print(f"scoring {len(with_gt)} papers with a GT: {', '.join(with_gt)}", flush=True)
    ev.evaluate_all(_paths.PAPERS, r11.OUT, ev.DEFAULT_KEY, False, semantic=True, use_llm=True)


def main(argv):
    ps = papers()
    split()
    start = OLD_NAMES.get(argv[0], argv[0]) if argv else "all"
    todo = STAGES if start == "all" else STAGES[STAGES.index(start):]
    print(f"{len(ps)} papers with a _full.md under {_paths.PAPERS}; output {_paths.OUTPUT}", flush=True)
    for s in todo:
        t0 = time.time()
        print(f"\n===== {s} {time.strftime('%H:%M:%S')}", flush=True)
        run(s, ps)
        print(f"===== {s} done in {round((time.time() - t0) / 60)} min", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
