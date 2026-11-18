"""prompt_ab.py — the base column tree's old wording against the new (prompt_variants.py), one node at a time
(REVIEW_Opus5.5xtra_2026-11-16, section 7; the decoder notes: rewording a tested question moves results by itself).

  tables    the head reader's tables (experiments/reader2_all.json, with its context lines), as head_column_bench
            builds them, of the tuning papers (dev + held_a of split_v15.json); only tables the GT draws on
  key       column_role_bench.derive_labels (the GT's species / value pairs in each column): the column tag key the
            calibration audit found best calibrated
  old, new  each table is read by the old tree, then once per variant with ONE node (or the intro line, or a table
            question) replaced, in the same session with the same batching as production (nimble, 6 questions a
            call). Identical questions are asked once and their answer reused, so a node variant costs only the
            questions its node changes; the intro and the table questions sit in every column's state and cost a
            full reading each
  score     per variant: right tags on the columns the GT draws on (exact, and with measurementType / Value as one),
            'none' on the columns it does not use, the answers that changed (right -> wrong, wrong -> right), and the
            columns whose path went through the node

    python prompt_ab.py run [variant ...]       resumable: output/prompt_ab/results.json (per paper)
    python prompt_ab.py run node:kind.2 table_kind.2 node:organism_name.2 all.2
                                                revision 2, compared with 'old.2' (the old wording read again in the
                                                same session; 'old' against 'old.2' is the drift between sessions)
    python prompt_ab.py score                   -> output/prompt_ab/SCORE.txt
    python prompt_ab.py run --group held_b ...  another group (default: tuning); held_b only as totals, run once

Adopted 2026-11-18 (the user): column_tree.py now carries 'all.2' (SCORE.txt: every block within the drift between
sessions). From then on 'old' in this file means that adopted wording; results.json keeps the readings of the
earlier wording, and the 'intro' variant asserts on the earlier intro line, so it cannot be run against the new tree.
"""
import collections
import contextlib
import copy
import json
import sys
import time

import _paths
import column_role_bench as crb
import column_tree as ct
import column_tree_bench as ctb
import head_to_table as h2t
import header_tree_bench as hb
import prompt_variants as pv
from evaluate import load_xlsx

OUT = _paths.OUTPUT / "prompt_ab"
HEAD = hb.OUT / "experiments" / "reader2_all.json"
SPLIT = json.loads((_paths.SUB / "output/eval_split/split_v15.json").read_text(encoding="utf-8"))["assign"]
TRAITS = {"measurementType", "measurementValue"}
OLD_INTRO = ("A table from a scientific paper about insects is being mapped, column by column, to a species-trait "
             "template.")
MODEL = ("nimble:9b-q4-gpu", 6)
# the cheap variants first (one node's questions), the full re-readings last
ORDER = ([v for v in pv.VARIANTS if v.startswith("node:") and "." not in v] + ["organism_column", "table_kind", "intro"]
         + [v for v in pv.VARIANTS if "." in v and v != "all.2"] + ["all.2"])


def base_of(v):
    """The old wording read in the same session as variant v: 'old' for the first session's variants, 'old.2' for
    those named '<x>.2'. nimble's answers drift between model loads, so a variant is compared with its own session."""
    return f"old.{v.rsplit('.', 1)[1]}" if "." in v.rsplit(":", 1)[-1] else "old"


class Memo:
    """client.ask with identical questions (same state, same question set) answered once per session."""

    def __init__(self, client):
        self.client, self.cache, self.asked, self.reused = client, {}, 0, 0

    @property
    def calls(self):
        return self.client.calls

    def ask(self, state_at, questions):
        key = json.dumps([state_at(0), questions], sort_keys=True, ensure_ascii=False)
        if key in self.cache:
            self.reused += 1
        else:
            self.cache[key] = self.client.ask(state_at, questions)
            self.asked += 1
        return copy.deepcopy(self.cache[key])


@contextlib.contextmanager
def applied(name):
    """column_tree with one variant in place; everything restored after."""
    kind, val = pv.VARIANTS[name]
    saved = (ct.TABLE_KIND, ct.ORGANISM_COLUMN, ct.NODES, ct.table_state)
    try:
        if kind == "combined":                      # every listed variant at once
            with contextlib.ExitStack() as stack:
                for v in val:
                    stack.enter_context(applied(v))
                yield
            return
        if kind == "intro":
            orig = ct.table_state
            assert OLD_INTRO in orig(_Probe(), "", (), 0), "the old intro line is not where expected"
            ct.table_state = lambda *a, **k: orig(*a, **k).replace(OLD_INTRO, val)
        elif kind == "table_kind":
            ct.TABLE_KIND = val
        elif kind == "organism_column":
            ct.ORGANISM_COLUMN = val
        else:
            node, text = val
            assert set(text["options"]) == set(ct.NODES[node]["options"]), f"{node}: options differ"
            ct.NODES = {**ct.NODES, node: text}
        yield
    finally:
        ct.TABLE_KIND, ct.ORGANISM_COLUMN, ct.NODES, ct.table_state = saved


class _Probe:
    """A one-column table for checking where the intro line sits."""
    header_names = ["x"]

    def data_records(self):
        return [{"x": "1"}]


def tables_of(paper, head):
    inputs = crb.paper_inputs(crb.PAPERS / paper)
    if not inputs or paper not in head:
        return None, None, []
    full_md, gt_path = inputs
    gt = crb.GroundTruth(load_xlsx(gt_path))
    text = full_md.read_text(encoding="utf-8", errors="replace")
    out, seen = [], set()
    for t, ctx in h2t.build_tables(paper, head[paper], h2t.grids_of(paper), context=True):
        sig = tuple(t.header_names)
        if sig in seen or len(sig) > ctb.MAX_TABLE_COLS:
            continue
        seen.add(sig)
        labels = crb.derive_labels(t, gt, extra=True)
        if any(lab not in ("none", "unsure") for lab, _e in labels.values()):
            out.append((t, ctx, labels))
    return gt, text, out


def run(variants, papers, base="old"):
    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / "results.json"
    res = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    head = json.loads(HEAD.read_text(encoding="utf-8"))
    client = Memo(ct.DecisionClient(*MODEL))
    for p in papers:
        done = res.get(p) or {}
        if done and all(v in done.get("variants", []) for v in variants):
            continue
        _gt, text, tables = tables_of(p, head)
        if not tables:
            continue
        t0 = time.time()
        entries = {e["table"]: e for e in done.get("tables", [])}
        for t, ctx, labels in tables:
            tid = f"{p}#{t.table_index}"
            e = entries.get(tid) or {"table": tid, "labels": labels, "pred": {}, "paths": {}}
            todo = [v for v in [base] + variants if v not in e["pred"]]
            for v in todo:
                with (applied(v) if not v.startswith("old") else contextlib.nullcontext()):
                    r = ct.classify_table(t, text, client, table_context=True, seed=tid, extra_context=ctx)
                e["pred"][v] = r["greedy"]
                e["paths"][v] = r.get("paths", {})
            entries[tid] = e
        res[p] = {"tables": list(entries.values()), "variants": sorted(set(done.get("variants", [])) | set(variants))}
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        name = p if SPLIT.get(p) in ("dev", "held_a") else "(a test paper)"
        print(f"  [prompt_ab] {name:22s} {len(tables)} tables, {client.asked} calls asked, {client.reused} reused "
              f"({time.time() - t0:.0f}s)", flush=True)
    import decoder as v1
    v1.unload(MODEL[0])


def right(pred, lab):
    return pred == lab or (pred in TRAITS and lab in TRAITS)


def score():
    res = json.loads((OUT / "results.json").read_text(encoding="utf-8"))
    variants = [v for v in ORDER if any(v in e["pred"] for r in res.values() for e in r["tables"])]
    if any("old.2" in e["pred"] for r in res.values() for e in r["tables"]):
        variants = ["old.2"] + variants             # drift: the old wording read again in a later session
    L = ["Base column tree: old wording against new, one variant at a time. Key: column_role_bench.derive_labels.",
         "Columns the GT draws on ('used') and columns it does not use ('none'); per group; flips listed for tuning "
         "papers. Each variant is compared with the old wording read in its own session ('old' or 'old.2'); the",
         "'old.2' block is the drift between the two sessions: the noise floor for every other block.", ""]
    flips_all = []
    for v in variants:
        node = v.split(":", 1)[1] if v.startswith("node:") else None
        c = collections.Counter()
        for p, r in res.items():
            g = SPLIT.get(p, "?")
            for e in r["tables"]:
                if v not in e["pred"]:
                    continue
                for h, (lab, _ev) in e["labels"].items():
                    if lab == "unsure":
                        continue
                    b = "old" if v == "old.2" else base_of(v)
                    if b not in e["pred"]:
                        continue
                    old = (e["pred"][b].get(h) or [None])[0]
                    new = (e["pred"][v].get(h) or [None])[0]
                    if old is None or new is None:
                        continue
                    side = "used" if lab != "none" else "none"
                    via = node is None or any(node.split(".")[0] + ":" in (e["paths"].get(w, {}).get(h) or "")
                                              for w in (b, v))
                    c[(g, side, "n")] += 1
                    c[(g, side, "old")] += right(old, lab)
                    c[(g, side, "new")] += right(new, lab)
                    c[(g, side, "via")] += via
                    if old != new:
                        c[(g, side, "changed")] += 1
                        c[(g, side, "to right")] += right(new, lab) and not right(old, lab)
                        c[(g, side, "to wrong")] += right(old, lab) and not right(new, lab)
                        if g in ("dev", "held_a"):
                            flips_all.append(f"  {v:28s} {e['table']:26s} '{h[:40]}': {old} -> {new} (GT {lab})")
        L.append(f"== {v}")
        for g in ("dev", "held_a", "held_b"):
            for side in ("used", "none"):
                n = c[(g, side, "n")]
                if not n:
                    continue
                L.append(f"  {g:7s} {side:5s} {n:5d} columns  right {c[(g, side, 'old')] / n:6.1%} -> "
                         f"{c[(g, side, 'new')] / n:6.1%}   changed {c[(g, side, 'changed')]:3d} (to right "
                         f"{c[(g, side, 'to right')]}, to wrong {c[(g, side, 'to wrong')]})"
                         + (f"   path through the node: {c[(g, side, 'via')]}" if node else ""))
        L.append("")
    L += ["Changed answers on tuning papers:"] + flips_all
    (OUT / "SCORE.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:L.index("Changed answers on tuning papers:")]))


def main(argv):
    if argv[:1] == ["score"]:
        return score()
    args = argv[1:]
    group = "tuning"
    if args[:1] == ["--group"]:
        group, args = args[1], args[2:]
    variants = args or ORDER
    bad = [v for v in variants if v not in pv.VARIANTS]
    assert not bad, f"unknown variants {bad}; known: {list(pv.VARIANTS)}"
    bases = {base_of(v) for v in variants}
    assert len(bases) == 1, f"one session at a time: {bases}"
    want = ("dev", "held_a") if group == "tuning" else (group,)
    run(variants, sorted(p for p, g in SPLIT.items() if g in want), bases.pop())


if __name__ == "__main__":
    main(sys.argv[1:])
