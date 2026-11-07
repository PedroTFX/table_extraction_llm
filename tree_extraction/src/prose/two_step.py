"""
two_step.py — the main run in two steps. One model at a time, on the remote or the local PC alike.

    step 1, tables   full_run_v18.py on every paper. Results are written as soon as it ends, before any prose starts:
                     output/two_step/<paper>/<paper>.csv and output/two_step/status.json
    step 2, prose    only papers whose tables gave fewer than --min-rows rows (default 20). Each paper runs on its own, so one
                     failure costs that paper only. Its result file then holds the table rows plus the prose rows.

Routing uses the table step's row count, never the GT, so it works on new papers. On the 109 set it sends 13 papers,
including 5 of the 6 prose-set papers at 0 rows and the sixth at 11.

    python two_step.py [papers]                       both steps, every paper when none is named
    python two_step.py --step 1 | --step 2 [papers]   one step; step 2 reads the row counts of step 1's saved rows
    --variant t2   --min-rows 20

Paper names go only to files under output/two_step (logs, status.json), so a run on held papers shows counts on screen.
TREE_PAPERS / TREE_OUTPUT pick another paper set, as for the other runs. Stages already saved for a paper are not redone.
"""
import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _paths

V18_DIR = HERE.parent / "v18"
RUN = _paths.OUTPUT / "full_run_v18"
OUT = _paths.OUTPUT / "two_step"
LOGS = OUT / "logs"


def call(script, args, cwd, log, variant=None):
    env = dict(os.environ)
    if variant:
        env["PROSE_VARIANT"] = variant
    with open(log, "a", encoding="utf-8") as fh:
        return subprocess.run([sys.executable, "-u", script, *args], cwd=cwd, env=env, stdout=fh, stderr=subprocess.STDOUT).returncode == 0


def tree_script():
    return next(s for s in ("prose_tree_t2.py", "prose_tree_t1.py") if (HERE / s).exists())


def rows_in(f):
    if not f.exists():
        return 0
    with open(f, encoding="utf-8", newline="") as fh:
        return sum(1 for _ in csv.DictReader(fh))


def papers_of(named):
    return named or sorted(d.name for d in _paths.PAPERS.iterdir() if (d / f"{d.name}_full.md").exists())


def save(status):
    (OUT / "status.json").write_text(json.dumps(status, indent=1, ensure_ascii=False), encoding="utf-8")


def load():
    f = OUT / "status.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def publish(p, src):
    d = OUT / p
    d.mkdir(parents=True, exist_ok=True)
    if src.exists():
        shutil.copy(src, d / f"{p}.csv")


def step_tables(papers, min_rows):
    t0 = time.time()
    ok = call("full_run_v18.py", ["run", *papers], V18_DIR, LOGS / "tables.log")
    status = load()
    for p in papers:
        src = RUN / p / f"{p}.csv"
        n = rows_in(src)
        publish(p, src)
        status[p] = {"table_rows": n, "route": "prose" if n < min_rows else "tables", "prose": "not run"}
    save(status)
    sent = sum(status[p]["route"] == "prose" for p in papers)
    print(f"step 1 tables: {'done' if ok else 'FAILED, see logs/tables.log'} in {(time.time() - t0) / 60:.0f} min; {len(papers)} papers, "
          f"{sum(status[p]['table_rows'] for p in papers)} rows; {sent} go to prose", flush=True)
    return ok


def step_prose(papers, variant, min_rows):
    status = load()
    for p in papers:
        if p not in status:
            n = rows_in(RUN / p / f"{p}.csv")
            status[p] = {"table_rows": n, "route": "prose" if n < min_rows else "tables", "prose": "not run"}
    todo = [p for p in papers if status[p]["route"] == "prose"]
    tree = tree_script()
    stages = [("prose_reader.py", s) for s in ("abbrev", "shape", "nm", "heads", "walk", "field")] + [("sentence_test.py", None), (tree, "treeread")] \
        + [("prose_reader.py", s) for s in ("names", "places", "facts")] + [(tree, "treefinal"), ("prose_reader.py", "assemble")]
    prose_out = _paths.OUTPUT / f"prose_{variant}"
    done = failed = 0
    t0 = time.time()
    for i, p in enumerate(todo, 1):
        bad = next((f"{sc} {st or ''}".strip() for sc, st in stages
                    if not call(sc, ([st] if st else []) + [p], HERE, LOGS / f"prose_{p}.log", variant)), None)
        status[p]["prose"] = f"failed at {bad}" if bad else "done"
        if bad:
            failed += 1
        else:
            done += 1
            publish(p, prose_out / "combined" / p / f"{p}.csv")
            status[p]["prose_rows"] = rows_in(prose_out / "prose" / p / f"{p}.csv")
        save(status)
        print(f"  prose {i}/{len(todo)}: {done} done, {failed} failed ({(time.time() - t0) / 60:.0f} min)", flush=True)
    print(f"step 2 prose ({variant}): {done} done, {failed} failed; {sum(status[p].get('prose_rows', 0) for p in todo)} prose rows", flush=True)
    return not failed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("papers", nargs="*")
    ap.add_argument("--step", type=int, choices=(1, 2))
    ap.add_argument("--variant", default="t2")
    ap.add_argument("--min-rows", type=int, default=20)
    a = ap.parse_args()
    LOGS.mkdir(parents=True, exist_ok=True)
    papers = papers_of(a.papers)
    ok = True
    if a.step != 2:
        ok = step_tables(papers, a.min_rows)
    if a.step != 1 and ok:
        ok = step_prose(papers, a.variant, a.min_rows)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
