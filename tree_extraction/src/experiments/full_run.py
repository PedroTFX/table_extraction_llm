"""
full_run.py — the tree_extraction section run from start to finish on every paper with
a GT, written as production-format CSVs and scored with production's own evaluator
(evaluate.evaluate_all, the settings run_all.py uses), beside production's saved CSVs
scored the same way (2026-10-14).

Stages (each saved per paper, so a stage resumes; one model at a time):
  head      head reader v2 (head_more.py)              -> experiments/reader2_all.json
  tag       the column tree on EVERY table (tags already made by the benchmarks are
            reused; every column asked; same header list -> same tags)   -> OUT/tags/
  meaning   meaning v2 on each trait column's name (nimble)             -> OUT/meaning/
  inventory the paper-level legend inventory (gemma)                    -> decode_key/inventory/
  decode    the decoder, adjusted passage choice: QL only when >= 2 legend passages are
            offered and it picks one, else every inventory candidate; QK/QV/QB (nimble)
                                                                         -> OUT/decode/
  assemble  (code) one CSV row per species x trait, in production's columns:
              species    the table's organism column (the tree's table-level answer;
                         else the first column tagged verbatimIdentification); a genus
                         column on its left is joined to a lone epithet
              wide       each column tagged measurementType: type = its name, spelled out
                         by the meaning step when it resolved; value = the cell, decoded
              long       a column tagged measurementType holding names + columns tagged
                         measurementValue: type = the name cell, value = the value cell
              row fields columns tagged sex / lifeStage / caste / place / date / method /
                         protocol / treatment / statistic / unit / sample size / remarks /
                         references, and the tree's extra tags, copied onto the record's rows
              cells are kept as printed apart from decoding (no value splitting yet)
                                                                         -> OUT/<paper>/<paper>.csv
  score     evaluate_all on OUT and on OUT_PROD (production's CSVs copied) -> summary.csv

    python full_run.py tag | meaning | inventory | decode | assemble | score [papers...]
-> tree_extraction/output/full_run/
"""

from __future__ import annotations

import collections
import contextlib
import csv
import io
import json
import re
import shutil
import sys
import time

import _paths
import column_role_bench as crb
import column_tree as ct
import column_tree_bench as ctb
import decode_chain as dc
import decode_inv as di
import decode_units as du
import decoder as v1
import decoder_v2 as v2
import head_to_table as h2t
import header_tree_bench as hb
import legend_inventory as li
import meaning

OUT = _paths.OUTPUT / "full_run"
OUT_PROD = _paths.OUTPUT / "full_run_production"
HEAD = hb.OUT / "experiments" / "reader2_all.json"
TRAITS = {"measurementType", "measurementValue"}
ROW_FIELDS = ["sex", "lifeStage", "caste", "verbatimLocality", "verbatimCoordinates",
              "verbatimEventDate", "measurementMethod", "samplingProtocol", "sampleTreatment",
              "measurementStatistic", "measurementUnit", "sampleSizeValue", "measurementRemarks",
              "associatedReferences", "externalLink", "associatedOccurrences"]
CSV_FIELDS = ["basisOfRecord", "verbatimIdentification", "measurementType", "measurementMethod",
              "measurementValue", "measurementUnit", "measurementStatistic", "measurementRemarks",
              "sex", "lifeStage", "caste", "sampleSizeValue", "sampleSizeUnit", "sampleTreatment",
              "samplingProtocol", "verbatimLocality", "verbatimCoordinates", "verbatimEventDate",
              "associatedOccurrences", "associatedReferences", "externalLink"]
EMPTY = {"", "-", "–", "—", "na", "n/a", "nd"}


def gt_papers():
    return sorted(d.name for d in _paths.PAPERS.iterdir() if d.is_dir() and crb.paper_inputs(d))


def head_runs():
    return json.loads(HEAD.read_text(encoding="utf-8"))


def tables_of(paper, head):
    with contextlib.redirect_stdout(io.StringIO()):
        return h2t.build_tables(paper, head[paper], h2t.grids_of(paper), context=True)


# --- tags: every table --------------------------------------------------------------------

def known_tags(paper):
    """{table index: {"fields": {header: [tag, p]}, "organism": header|None}} from the
    benchmark runs (head_merge reader2_all, chain/tags_extra) and this run."""
    out = {}
    bench = json.loads(dc.TAGS.read_text(encoding="utf-8")).get(paper, []) if dc.TAGS.exists() else []
    for e in bench:
        k = int(e["table"].split("#")[1])
        fields = next(iter(e["pred"].values()))
        org = next((h for h, p in (e.get("paths") or {}).items() if "table:organism_column" in str(p)), None)
        out[k] = {"fields": fields, "organism": org}
    xf = dc.EXTRA / f"{paper}.json"
    if xf.exists():
        for k, fields in json.loads(xf.read_text(encoding="utf-8")).items():
            out.setdefault(int(k), {"fields": fields, "organism": None})
    ff = OUT / "tags" / f"{paper}.json"
    if ff.exists():
        for k, v in json.loads(ff.read_text(encoding="utf-8")).items():
            out.setdefault(int(k), v)
    return out


def stage_tag(papers):
    (OUT / "tags").mkdir(parents=True, exist_ok=True)
    head = head_runs()
    client = ct.DecisionClient("nimble:9b-q4-gpu", 6)
    for paper in papers:
        f = OUT / "tags" / f"{paper}.json"
        if f.exists() or paper not in head:
            continue
        have = known_tags(paper)
        by_sig = {}
        text = crb.paper_inputs(_paths.PAPERS / paper)[0].read_text(encoding="utf-8", errors="replace")
        out, t0 = {}, time.time()
        for t, ctx in tables_of(paper, head):
            if t.table_index in have or not t.columns:
                continue
            sig = tuple(t.header_names)
            if sig not in by_sig:
                for attempt in range(3):
                    try:
                        r = ct.classify_table(t, text, client, table_context=True,
                                              seed=f"{paper}#{t.table_index}", extra_context=ctx,
                                              max_cols=max(ct.MAX_COLS, len(t.header_names)))
                        break
                    except RuntimeError as err:
                        if attempt == 2 or "llama-server" not in str(err):
                            raise
                        time.sleep(30)
                org = (r.get("organism_column") or [None])[0]
                by_sig[sig] = {"fields": r["greedy"], "organism": org, "tags": r.get("tags", {})}
            out[str(t.table_index)] = by_sig[sig]
        f.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  [tag] {paper:22s} {len(out)} more table(s) ({time.time() - t0:.0f}s)", flush=True)
    v1.unload(v1.NIMBLE)


# --- the columns the run decodes and names ------------------------------------------------

def plan(paper, head):
    """[(Table, tags {header: tag}, organism header, extra tags)] for every table."""
    tags = known_tags(paper)
    out = []
    for t, _ctx in tables_of(paper, head):
        tg = tags.get(t.table_index, {})
        fields = {h: (v or ["none"])[0] for h, v in (tg.get("fields") or {}).items()}
        out.append((t, fields, tg.get("organism"), tg.get("tags") or {}))
    return out


def trait_columns(t, fields):
    out = []
    for col in t.columns:
        if fields.get(col.name) not in TRAITS:
            continue
        vals = []
        for rec in t.records:
            v = " ".join(str(rec.get(col.name, "") or "").split())
            if v and v not in vals:
                vals.append(v)
        if vals:
            out.append((t.table_index, col.index, col.name, vals[:25]))
    return out


# --- meaning ------------------------------------------------------------------------------

def stage_meaning(papers):
    (OUT / "meaning").mkdir(parents=True, exist_ok=True)
    head = head_runs()
    client = ct.DecisionClient("nimble:9b-q4-gpu", 1)
    for paper in papers:
        f = OUT / "meaning" / f"{paper}.json"
        if f.exists() or paper not in head:
            continue
        text, cache, out, t0 = meaning.paper_text(paper), {}, {}, time.time()
        for t, fields, _org, _x in plan(paper, head):
            for col in t.columns:
                if fields.get(col.name) == "measurementType" and col.name not in out:
                    try:
                        r = meaning.read_label(client, text, col.name, cache=cache)
                        out[col.name] = r.get("expanded") or col.name
                    except RuntimeError:
                        out[col.name] = col.name
        f.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  [meaning] {paper:22s} {len(out)} names ({time.time() - t0:.0f}s)", flush=True)
    v1.unload(v1.NIMBLE)


# --- inventory ----------------------------------------------------------------------------

def stage_inventory(papers):
    li.OUT.mkdir(parents=True, exist_ok=True)
    li.main(["build", *papers])


# --- decode (adjusted passage choice) ---------------------------------------------------------

def decode_column(client, paper, header, values, cats, units):
    by = du.column_units(cats, header, values)
    allowed, rec = cats, {"offered": sorted(by), "choice": None}
    if len(by) >= 2:
        chosen, rec = du.choose_unit(client, header, values, units, by)
        if chosen != "none" and len(chosen) == 1:
            allowed = [e for e in cats if e.get("unit") in chosen]
            rec["chosen"] = sorted(chosen)
    r = v2.match_column(client, header, values, allowed)
    r["units"] = rec
    return r


def stage_decode(papers):
    (OUT / "decode").mkdir(parents=True, exist_ok=True)
    head = head_runs()
    client = ct.DecisionClient(v1.NIMBLE, 1)
    for paper in papers:
        f = OUT / "decode" / f"{paper}.json"
        cats = di.inventory(paper)
        if f.exists() or paper not in head:
            continue
        cols = [c for t, fields, _o, _x in plan(paper, head) for c in trait_columns(t, fields)]
        res, t0 = {}, time.time()
        if cats:
            units = du.unit_texts(paper)
            for k, c, header, values in cols:
                for attempt in range(3):
                    try:
                        r = decode_column(client, paper, header, values, cats, units)
                        break
                    except RuntimeError as err:
                        if attempt == 2 or "llama-server" not in str(err):
                            raise
                        time.sleep(30)
                res[f"{k}:{c}"] = r
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  [decode] {paper:22s} {len(cols)} trait columns ({time.time() - t0:.0f}s)", flush=True)
    v1.unload(v1.NIMBLE)


# --- assemble -----------------------------------------------------------------------------

def _clean(v):
    v = " ".join(str(v or "").split())
    return "" if v.lower() in EMPTY else v


def _decoded(dec, k, c, cell):
    r = dec.get(f"{k}:{c}") or {}
    term = ((r.get("cells") or {}).get(cell) or {}).get("term")
    return term if term else cell


def species_of(t, fields, org, rec):
    ids = [col for col in t.columns if fields.get(col.name) == "verbatimIdentification"]
    col = next((c for c in t.columns if c.name == org), None) or (ids[0] if ids else None)
    if col is None:
        return ""
    sp = _clean(rec.get(col.name))
    left = [c for c in ids if c.index < col.index]
    if sp and re.fullmatch(r"[a-z][a-z-]+\.?", sp) and left:      # a lone epithet: join its genus
        g = _clean(rec.get(left[-1].name))
        if g and g[:1].isupper() and " " not in g:
            sp = f"{g} {sp}"
    return sp


def stage_assemble(papers):
    head = head_runs()
    n_rows = collections.Counter()
    for paper in papers:
        if paper not in head:
            continue
        names = {}
        mf = OUT / "meaning" / f"{paper}.json"
        if mf.exists():
            names = json.loads(mf.read_text(encoding="utf-8"))
        df = OUT / "decode" / f"{paper}.json"
        dec = json.loads(df.read_text(encoding="utf-8")) if df.exists() else {}
        rows = []
        for t, fields, org, xtags in plan(paper, head):
            long_types = [c for c in t.columns if fields.get(c.name) == "measurementType"]
            long_vals = [c for c in t.columns if fields.get(c.name) == "measurementValue"]
            is_long = bool(long_types and long_vals)
            for rec in t.records:
                sp = species_of(t, fields, org, rec)
                if not sp:
                    continue
                base = {"verbatimIdentification": sp}
                for col in t.columns:
                    f = fields.get(col.name)
                    if f in ROW_FIELDS:
                        v = _clean(rec.get(col.name))
                        if v and not base.get(f):
                            base[f] = v
                if is_long:
                    tcol = long_types[0]
                    typ = _clean(rec.get(tcol.name))
                    for vcol in long_vals:
                        v = _clean(rec.get(vcol.name))
                        if typ and v:
                            row = {**base, "measurementType": typ,
                                   "measurementValue": _decoded(dec, t.table_index, vcol.index, v)}
                            row.update({k: x for k, x in (xtags.get(vcol.name) or {}).items() if k in CSV_FIELDS})
                            rows.append(row)
                    continue
                for col in t.columns:
                    if fields.get(col.name) not in TRAITS:
                        continue
                    v = _clean(rec.get(col.name))
                    if not v:
                        continue
                    row = {**base, "measurementType": names.get(col.name) or col.name,
                           "measurementValue": _decoded(dec, t.table_index, col.index, v)}
                    row.update({k: x for k, x in (xtags.get(col.name) or {}).items() if k in CSV_FIELDS})
                    rows.append(row)
        d = OUT / paper
        d.mkdir(parents=True, exist_ok=True)
        with open(d / f"{paper}.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=CSV_FIELDS, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        n_rows[paper] = len(rows)
        print(f"  [assemble] {paper:22s} {len(rows)} rows", flush=True)
    print(f"assembled {len(n_rows)} papers, {sum(n_rows.values())} rows")


# --- score ------------------------------------------------------------------------------------

def stage_score(papers):
    import evaluate as ev
    # miss-severity grading is score-neutral (labels misses only) and costs ~30 s per 20
    # misses: Brant2021's 481 misses alone took 14 min. evaluate.py's batch-run switch.
    ev.ASSESS_MISS_SEVERITY = False
    papers = set(papers)
    OUT_PROD.mkdir(parents=True, exist_ok=True)
    for p in papers:                                   # production's saved CSVs, same papers
        src = _paths.REPO / "output" / p / f"{p}.csv"
        if src.exists() and (OUT / p / f"{p}.csv").exists():
            (OUT_PROD / p).mkdir(parents=True, exist_ok=True)
            shutil.copy(src, OUT_PROD / p / f"{p}.csv")
    for root in (OUT, OUT_PROD):
        print(f"\n=== scoring {root.name}", flush=True)
        ev.evaluate_all(_paths.PAPERS, root, ev.DEFAULT_KEY, False, semantic=True, use_llm=True)


def main(argv):
    stage, papers = argv[0], argv[1:] or gt_papers()
    {"tag": stage_tag, "meaning": stage_meaning, "inventory": stage_inventory,
     "decode": stage_decode, "assemble": stage_assemble, "score": stage_score}[stage](papers)


if __name__ == "__main__":
    main(sys.argv[1:])
