"""
decode_chain.py — the decoder (decoder_v2, frozen v2h settings) run on what the CHAIN
chooses, not on the answer key:
  tables   head reader v2 (experiments/round2.json) -> head_to_table (records from the
           first record on, minus section / repeated-header / note rows)
  columns  the ones the column tree (head_column_bench reader2_v2) tagged
           measurementType or measurementValue
  header   the head reader's name (groups + name + details)
  values   the column's distinct cells in those records
Then gemma organises the legends and nimble matches, as in decoder_v2. The key is used
only to SCORE: each key column (table, column) is looked up in what the chain decoded;
one the chain never decoded counts as 'not reached'.

    python decode_chain.py organise | match | score [papers...]
-> output/decode_key/chain/{organise,match}/<paper>.json, SCORE.txt
"""

from __future__ import annotations

import collections
import json
import re
import sys
import time

import column_tree as ct
import column_tree_bench as ctb
import decode_key as dk
import decoder as v1
import decoder_v2 as v2
import head_to_table as h2t
import header_tree_bench as hb

OUT = dk.OUT / "chain"
HEAD = hb.OUT / "experiments" / "reader2_all.json"   # head reader v2: bench + the key's papers
TAGS = ctb.OUT / "head_merge" / "reader2_all.json"
TRAIT_TAGS = {"measurementType", "measurementValue"}
EXTRA = OUT / "tags_extra"   # tables the tagging bench skipped (not drawn on by the GT, or
                             # over 60 columns), tagged here with every column asked


def chain_columns(paper, head, tags):
    """[(table, col, header, values)] the chain decodes, from its own outputs."""
    tagged = {}                                          # table index -> {header: tag}
    for e in tags.get(paper, []):
        k = int(e["table"].split("#")[1])
        pred = next(iter(e["pred"].values()))            # the run's one variant
        tagged[k] = {h: (p or ["none"])[0] for h, p in pred.items()}
    xf = EXTRA / f"{paper}.json"
    if xf.exists():
        for k, pred in json.loads(xf.read_text(encoding="utf-8")).items():
            tagged.setdefault(int(k), {h: (p or ["none"])[0] for h, p in pred.items()})
    out = []
    for t, _ctx in h2t.build_tables(paper, head[paper], h2t.grids_of(paper), context=True):
        tags_t = tagged.get(t.table_index, {})
        for col in t.columns:
            if tags_t.get(col.name) not in TRAIT_TAGS:
                continue
            vals = []
            for rec in t.records:
                v = " ".join(str(rec.get(col.name, "") or "").split())
                if v and v not in vals:
                    vals.append(v)
            if vals:
                out.append((t.table_index, col.index, col.name, vals[:25]))
    return out


def cmd_organise(papers, head, tags):
    (OUT / "organise").mkdir(parents=True, exist_ok=True)
    for paper in papers:
        f = OUT / "organise" / f"{paper}.json"
        if f.exists():
            continue
        cols = chain_columns(paper, head, tags)
        t0 = time.time()
        res = v2.organise(paper, cols) if cols else {"calls": 0, "chars": 0, "passages": [],
                                                     "categories": [], "dropped": []}
        res.update(seconds=round(time.time() - t0, 1), columns=[list(c) for c in cols])
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  {paper:22s} {len(cols)} trait columns, {res['calls']} call(s), "
              f"{len(res['categories'])} categories ({res['seconds']}s)", flush=True)
    v1.unload(v1.GEMMA)


def coded_papers():
    key = v1.load_key()
    return sorted(p for p, cols in key.items() if any(e["kind"] == "coded" for e in cols.values()))


def cmd_tag(papers, head, tags):
    """Tag the tables of these papers that the tagging bench left untagged, every
    column asked (no 40-column sample: Kratschmer's 'Nesting type' sits in 87-column
    tables). Tables with the same header list as one already tagged reuse its tags."""
    EXTRA.mkdir(parents=True, exist_ok=True)
    client = ct.DecisionClient(*ctb_model())
    for paper in papers:
        f = EXTRA / f"{paper}.json"
        if f.exists() or paper not in head:
            continue
        done_idx = {int(e["table"].split("#")[1]) for e in tags.get(paper, [])}
        by_sig = {tuple(e["headers"]): next(iter(e["pred"].values())) for e in tags.get(paper, [])}
        full_md = ct_paper_md(paper)
        out, t0 = {}, time.time()
        for t, ctx in h2t.build_tables(paper, head[paper], h2t.grids_of(paper), context=True):
            if t.table_index in done_idx or not t.columns:
                continue
            sig = tuple(t.header_names)
            if sig not in by_sig:
                r = ct.classify_table(t, full_md, client, table_context=True,
                                      seed=f"{paper}#{t.table_index}", extra_context=ctx,
                                      max_cols=max(ct.MAX_COLS, len(t.header_names)))
                by_sig[sig] = r["greedy"]
            out[str(t.table_index)] = by_sig[sig]
        f.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  {paper:22s} tagged {len(out)} more table(s) ({time.time() - t0:.0f}s)", flush=True)
    v1.unload(v1.NIMBLE)


def ctb_model():
    import head_column_bench as hcb
    return hcb.MODEL


def ct_paper_md(paper):
    import column_role_bench as crb
    return crb.paper_inputs(crb.PAPERS / paper)[0].read_text(encoding="utf-8", errors="replace")


def cmd_refresh(papers, head, tags):
    """Clear saved results only where they are out of date: a paper whose trait columns
    changed (new tags) loses its organise + match; a paper whose saved legends hold a
    term with its own code in it ('G = grasses') loses its match."""
    for paper in papers:
        org, mat = OUT / "organise" / f"{paper}.json", OUT / "match" / f"{paper}.json"
        if not org.exists():
            continue
        o = json.loads(org.read_text(encoding="utf-8"))
        cols = [list(c) for c in chain_columns(paper, head, tags)]
        if cols != o.get("columns"):
            org.unlink()
            mat.unlink(missing_ok=True)
            print(f"  {paper}: trait columns changed ({len(o.get('columns', []))} -> {len(cols)}): "
                  f"organise + match cleared", flush=True)
            continue
        if any(v2.strip_own_code(dict(e)) != e for e in o["categories"]):
            mat.unlink(missing_ok=True)
            print(f"  {paper}: a term held its own code: match cleared", flush=True)


def cmd_match(papers):
    (OUT / "match").mkdir(parents=True, exist_ok=True)
    client = ct.DecisionClient(v1.NIMBLE, 1)
    for paper in papers:
        f, org = OUT / "match" / f"{paper}.json", OUT / "organise" / f"{paper}.json"
        if f.exists() or not org.exists():
            continue
        o = json.loads(org.read_text(encoding="utf-8"))
        cats = [v2.strip_own_code(dict(e)) for e in o["categories"]]
        res, t0, c0 = {}, time.time(), client.calls
        for k, c, header, values in o["columns"]:
            r = v2.match_column(client, header, values, cats)
            r["header"] = header
            res[f"{k}:{c}"] = r
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  {paper:22s} {client.calls - c0} question(s) ({time.time() - t0:.0f}s)", flush=True)
    v1.unload(v1.NIMBLE)


def lookup(decoded, k, c):
    """The chain's record for key column (k, c); a continuation table is joined into an
    earlier one, so fall back to the nearest earlier table decoded at column c."""
    if f"{k}:{c}" in decoded:
        return decoded[f"{k}:{c}"]
    earlier = sorted((int(x.split(":")[0]) for x in decoded if x.split(":")[1] == str(c)
                      and int(x.split(":")[0]) < k), reverse=True)
    return decoded[f"{earlier[0]}:{c}"] if earlier else None


def cmd_score(papers):
    key = v1.load_key()
    rows = []
    for paper in papers:
        f = OUT / "match" / f"{paper}.json"
        if paper not in key or not f.exists():
            continue
        decoded = json.loads(f.read_text(encoding="utf-8"))
        # weights and outcomes as decoder_v2.score_dir, with 'not reached' added
        for r in v2.score_dir_from(paper, key[paper],
                                   lambda e: lookup(decoded, e["table"], e["col"])):
            rows.append(r)
    c = collections.Counter()
    for r in rows:
        c[(r["kind"], r["out"])] += r["w"]
    L = ["decoder on the chain's own columns (head reader v2 -> column tags -> decoder v2)", ""]
    for kind in ("coded", "kept"):
        tot = sum(v for (k, _o), v in c.items() if k == kind)
        if not tot:
            continue
        L.append(f"{kind}: {tot} species rows   " + ", ".join(
            f"{o} {v}" for (k, o), v in sorted(c.items(), key=lambda kv: -kv[1]) if k == kind))
    L += ["", "per paper, coded rows right / reachable (not reached):"]
    by = collections.defaultdict(list)
    for r in rows:
        by[r["paper"]].append(r)
    for p, rs in sorted(by.items()):
        cod = [r for r in rs if r["kind"] == "coded" and r["out"] not in ("no legend printed", "GT error")]
        if cod:
            L.append(f"  {p:20s} {sum(r['w'] for r in cod if r['out'] in ('right', 'right, unit inside'))}"
                     f" / {sum(r['w'] for r in cod)}   (not reached "
                     f"{sum(r['w'] for r in cod if r['out'] == 'not reached')})")
    L += ["", "misses:"] + [f"  {r['paper']} '{r['trait'][:28]}' '{r['cell']}' -> want '{r['want'][:30]}', "
                            f"have '{r['have'][:40]}' [{r['out']}]"
                            for r in rows if r["kind"] == "coded" and r["out"] not in ("right", "no legend printed")]
    (OUT / "SCORE.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[:30]))


def main(argv):
    cmd, papers = argv[0], argv[1:]
    head = json.loads(HEAD.read_text(encoding="utf-8"))
    tags = json.loads(TAGS.read_text(encoding="utf-8")) if TAGS.exists() else {}
    papers = papers or sorted(p for p in head if p in tags)
    if cmd in ("tag", "refresh") and not argv[1:]:
        papers = coded_papers()
    {"organise": lambda: cmd_organise(papers, head, tags), "match": lambda: cmd_match(papers),
     "score": lambda: cmd_score(papers), "tag": lambda: cmd_tag(papers, head, tags),
     "refresh": lambda: cmd_refresh(papers, head, tags)}[cmd]()


if __name__ == "__main__":
    main(sys.argv[1:])
