"""
two_step.py — the main run in two steps. One model at a time, on the remote or the local PC alike.

    step 1, tables   full_run_v18.py on every paper. Results are written as soon as it ends, before any prose starts:
                     output/two_step/<paper>/<paper>.csv and output/two_step/status.json
    step 2, prose    only papers routed to prose. Each paper runs on its own, so one failure costs that paper only. Its result
                     file then holds the table rows plus the prose rows.

Routing (--route kind, the default; 2026-11-07, the user): prose when no table is a traits table (Q-KIND, saved by the table
step: every table is statistical results, figure numbers, sampling or other, or there is none) AND nimble does not say, sure in
both orders, that the paper's text reports a study rather than describing organisms (Q-TEXT, on the title, abstract and
headings). Tran2022, an experiment whose tables are figure numbers, got 58 prose rows of methods and results text and none
matched. --route rows is the old rule: fewer than --min-rows table rows. Never the GT, so it works on new papers.
    --step 0        decide the routes only (status.json), no prose run

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


Q_TEXT = "What does the text of this paper mainly do?"
TEXT = {"describes": "describes organisms: species descriptions or accounts written out, with their characters, colour, size, "
                     "distribution, habitat or hosts (taxonomy, faunistics, natural history)",
        "reports": "reports a study: an experiment, survey or analysis, with methods and results, its data in tables, figures "
                   "or supplements"}


def traits_table(p):
    """True when the table step's Q-KIND kept a table as traits; None when it left no record and the paper has tables."""
    kf = RUN / "kind" / f"{p}.json"
    if kf.exists():
        k = json.loads(kf.read_text(encoding="utf-8"))
        return any(isinstance(v, dict) and v.get("action") == "keep" and (v.get("kind") or {}).get("choice") == "traits"
                   for v in k.values())
    md = _paths.PAPERS / p / f"{p}_full.md"
    return None if md.exists() and "<table" in md.read_text(encoding="utf-8", errors="ignore") else False


def paper_view(p):
    """Title, abstract and headings: geometry only."""
    import re
    t = (_paths.PAPERS / p / f"{p}_full.md").read_text(encoding="utf-8", errors="ignore")
    heads = [l.lstrip("#").strip() for l in t.split("\n") if l.startswith("#")]
    title = next((h for h in heads if len(h) > 25), heads[0] if heads else "")
    m = re.search(r"(?ims)^#+\s*abstract\s*$(.*?)^#", t)
    abstract = " ".join((m.group(1) if m else t[:1500]).split())[:1200]
    return (f"A scientific paper is titled '{title[:200]}'. Its abstract reads: '{abstract}'. "
            f"Its section headings are: {'; '.join(h[:60] for h in heads[:40])}.")


def decide(papers, status, how, min_rows):
    """Each paper's route, with why; the answers are kept in status.json."""
    ask = None
    for p in papers:
        n = rows_in(RUN / p / f"{p}.csv")
        s = status.setdefault(p, {"prose": "not run"})
        s["table_rows"] = n
        if how == "rows":
            s["route"], s["why"] = ("prose" if n < min_rows else "tables"), f"rows < {min_rows}"
            continue
        if not (_paths.PAPERS / p / f"{p}_full.md").exists():
            s["route"], s["why"] = "tables", "no paper text"
            continue
        tt = traits_table(p)
        if tt is not False:
            s["route"], s["why"] = "tables", ("a traits table" if tt else "tables without a kind record")
            continue
        if ask is None:
            import prose_reader as pr                 # first: it sets up the paths
            import duels
            ask = pr.Ask()
        st = paper_view(p)
        ch, pr1 = ask(st, Q_TEXT, dict(TEXT))
        reports = duels.sure(ch, pr1, "reports") == "reports"
        log = {"a": [ch, pr1]}
        if reports:
            ch2, pr2 = ask(st, Q_TEXT, {"b": TEXT["reports"], "a": TEXT["describes"]})
            log["b"] = [ch2, pr2]
            reports = duels.sure(ch2, pr2, "b") == "b"
        s["q_text"] = log
        s["route"], s["why"] = ("tables", "no traits table; text reports a study") if reports else ("prose", "no traits table; text not a report")
        if s["route"] == "tables":
            publish(p, RUN / p / f"{p}.csv")          # a paper routed away from prose gets its table rows back
    if ask is not None:
        ask.unload()
    for p in papers:
        if status[p]["route"] == "tables":
            publish(p, RUN / p / f"{p}.csv")
    import collections
    c = collections.Counter(status[p]["why"] for p in papers)
    print(f"routes ({how}): {sum(status[p]['route'] == 'prose' for p in papers)} of {len(papers)} to prose; {dict(c)}", flush=True)


def step_tables(papers, min_rows, how="kind"):
    t0 = time.time()
    ok = call("full_run_v18.py", ["run", *papers], V18_DIR, LOGS / "tables.log")
    status = load()
    for p in papers:
        publish(p, RUN / p / f"{p}.csv")
        status[p] = {"prose": "not run"}
    decide(papers, status, how, min_rows)
    save(status)
    sent = sum(status[p]["route"] == "prose" for p in papers)
    print(f"step 1 tables: {'done' if ok else 'FAILED, see logs/tables.log'} in {(time.time() - t0) / 60:.0f} min; {len(papers)} papers, "
          f"{sum(status[p]['table_rows'] for p in papers)} rows; {sent} go to prose", flush=True)
    return ok


def step_prose(papers, variant, min_rows):
    status = load()
    for p in papers:
        if p not in status or "why" not in status[p]:
            sys.exit("routes not decided for every paper: run --step 0 first")
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
    ap.add_argument("--step", type=int, choices=(0, 1, 2))
    ap.add_argument("--route", choices=("kind", "rows"), default="kind")
    ap.add_argument("--variant", default="t2")
    ap.add_argument("--min-rows", type=int, default=20)
    a = ap.parse_args()
    LOGS.mkdir(parents=True, exist_ok=True)
    papers = papers_of(a.papers)
    ok = True
    if a.step == 0:
        status = load()
        decide(papers, status, a.route, a.min_rows)
        save(status)
        sys.exit(0)
    if a.step != 2:
        ok = step_tables(papers, a.min_rows, a.route)
    if a.step != 1 and ok:
        ok = step_prose(papers, a.variant, a.min_rows)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
