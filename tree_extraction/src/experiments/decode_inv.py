"""
decode_inv.py — decoding with the paper-level legend inventory (legend_inventory.py),
scored in three parts (2026-10-14):

  inventory   for each coded key pair whose legend the paper prints: does the inventory
              hold an entry nimble could be offered for the cell (code printed like it,
              or a category named without a code whose initials it is) whose term or
              name is the GT value (wording boundary forgiven)?
  matching    of the pairs the inventory captured, in columns that were decoded: did
              nimble pick the right entry?
  end-to-end  the decoded value is the GT value (as decode_chain / decoder_v2 score it)

Runs (nimble only; the inventory is gemma's, built once per paper):
  chain   the chain's own columns (decode_chain.chain_columns)  -> inv_chain/match/
  key     the key's columns (decoder_v2.key_columns)            -> inv_key/match/
  espinosa  the invariance test: Espinosa2023 matched with the 5 columns of the run
            before the tagging fix and with today's 19, the same inventory

    python decode_inv.py chain | key | espinosa | score
"""

from __future__ import annotations

import collections
import json
import sys
import time

import column_tree as ct
import decode_chain as dc
import decode_key as dk
import decoder as v1
import decoder_v2 as v2
import legend_inventory as li

RUNS = {"chain": dk.OUT / "inv_chain", "key": dk.OUT / "inv_key"}


def inventory(paper):
    f = li.OUT / f"{paper}.json"
    if not f.exists():
        return None
    return [v2.strip_own_code(dict(e)) for e in json.loads(f.read_text(encoding="utf-8"))["categories"]]


def columns(run, paper, head, tags, key):
    if run == "chain":
        return [list(c) for c in dc.chain_columns(paper, head, tags)]
    return [[k, c, h, v] for k, c, h, v, _e in v2.key_columns(paper, key)]


def match(run, papers):
    out = RUNS[run] / "match"
    out.mkdir(parents=True, exist_ok=True)
    head = json.loads(dc.HEAD.read_text(encoding="utf-8"))
    tags = json.loads(dc.TAGS.read_text(encoding="utf-8"))
    key = v1.load_key()
    client = ct.DecisionClient(v1.NIMBLE, 1)
    for paper in papers:
        f = out / f"{paper}.json"
        cats = inventory(paper)
        if f.exists() or cats is None:
            continue
        cols = columns(run, paper, head, tags, key) if (run == "key" or paper in head) else []
        res, t0, c0 = {"_columns": cols}, time.time(), client.calls
        for k, c, header, values in cols:
            for attempt in range(3):                      # a slow model load: 'timed out
                try:                                      # waiting for llama-server to start'
                    r = v2.match_column(client, header, values, cats)
                    break
                except RuntimeError as err:
                    if attempt == 2 or "llama-server" not in str(err):
                        raise
                    print(f"  model load timed out, retrying in 30s ({paper} {k}:{c})", flush=True)
                    time.sleep(30)
            r["header"] = header
            res[f"{k}:{c}"] = r
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  [{run}] {paper:22s} {len(cols)} columns, {client.calls - c0} questions "
              f"({time.time() - t0:.0f}s)", flush=True)
    v1.unload(v1.NIMBLE)


def espinosa():
    """Invariance: the same inventory, 5 columns (before the tagging fix) vs 19."""
    paper = "Espinosa2023"
    cats = inventory(paper)
    old = json.loads((dk.OUT / "chain_before_fixes" / "organise" / f"{paper}.json")
                     .read_text(encoding="utf-8"))["columns"]
    head = json.loads(dc.HEAD.read_text(encoding="utf-8"))
    tags = json.loads(dc.TAGS.read_text(encoding="utf-8"))
    new = [list(c) for c in dc.chain_columns(paper, head, tags)]
    client = ct.DecisionClient(v1.NIMBLE, 1)
    key = v1.load_key()
    out = {}
    for name, cols in (("5 columns", old), ("19 columns", new)):
        res = {f"{k}:{c}": v2.match_column(client, h, v, cats) for k, c, h, v in cols}
        rows = v2.score_dir_from(paper, key[paper], lambda e: dc.lookup(res, e["table"], e["col"]))
        coded = [r for r in rows if r["kind"] == "coded"]
        out[name] = (len(cols), sum(r["w"] for r in coded if r["out"] in ("right", "right, unit inside")),
                     sum(r["w"] for r in coded))
    v1.unload(v1.NIMBLE)
    L = [f"Espinosa2023 invariance (one inventory: {len(cats)} entries, built once from the paper)"]
    L += [f"  {name:11s}: {n} columns decoded -> coded rows right {ok}/{tot}" for name, (n, ok, tot) in out.items()]
    (dk.OUT / "inv_ESPINOSA.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


def captured(cats, cell, want, header=""):
    """The inventory holds an entry for this cell whose term/name is the GT value."""
    ev, es = v2.candidates(cats, cell, header)
    w = f" {v1._flat(want)} "
    for e in es:
        for t in (e.get("term") or "", e.get("label") or ""):
            f = f" {v1._flat(t)} "
            if t and (f == w or w in f or (f.strip() and f in w)):
                return True
    return False


def score():
    key = v1.load_key()
    dev = v1.dev_papers()
    L = ["decoding with the paper-level legend inventory — three scores apart", ""]
    for run, d in RUNS.items():
        inv, mat, e2e = collections.Counter(), collections.Counter(), collections.Counter()
        per = []
        for paper in li.coded_papers():
            f = d / "match" / f"{paper}.json"
            cats = inventory(paper)
            if not f.exists() or cats is None:
                continue
            dec = {k: v for k, v in json.loads(f.read_text(encoding="utf-8")).items()
                   if not k.startswith("_")}              # '_columns': what was decoded
            side = "dev" if paper in dev else "new"
            ok_p = n_p = 0
            for r in v2.score_dir_from(paper, key[paper], lambda e: dc.lookup(dec, e["table"], e["col"])):
                if r["kind"] != "coded" or r["out"] in ("no legend printed", "GT error"):
                    continue
                e = key[paper][r["trait"]]
                cap = captured(cats, r["cell"], r["want"])
                right = r["out"] in ("right", "right, unit inside")
                inv[(side, "n")] += r["w"]
                inv[(side, "ok")] += r["w"] * cap
                if cap and r["out"] != "not reached":
                    mat[(side, "n")] += r["w"]
                    mat[(side, "ok")] += r["w"] * right
                    mat[(side, "wording")] += r["w"] * (r["out"] in ("right, longer wording", "right, shorter wording"))
                e2e[(side, "n")] += r["w"]
                e2e[(side, "ok")] += r["w"] * right
                e2e[(side, "nr")] += r["w"] * (r["out"] == "not reached")
                ok_p += r["w"] * right
                n_p += r["w"]
            per.append(f"    [{side}] {paper:20s} {ok_p}/{n_p}")
        pct = lambda c, s, k="ok": f"{c[(s, k)]}/{c[(s, 'n')]} ({c[(s, k)] / c[(s, 'n')]:.0%})" if c[(s, 'n')] else "-"
        L.append(f"run '{run}' (columns: {'the chain' if run == 'chain' else 'the answer key'}):")
        for s in ("dev", "new"):
            L.append(f"  {s}: inventory {pct(inv, s)}   matching {pct(mat, s)} (+{mat[(s, 'wording')]} "
                     f"wording only)   end-to-end {pct(e2e, s)} (not reached {e2e[(s, 'nr')]})")
        L += ["  per paper, end-to-end:"] + per + [""]
    (dk.OUT / "inv_SCORE.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


def main(argv):
    cmd = argv[0]
    papers = argv[1:] or li.coded_papers()
    if cmd in RUNS:
        match(cmd, papers)
    elif cmd == "espinosa":
        espinosa()
    else:
        score()


if __name__ == "__main__":
    main(sys.argv[1:])
