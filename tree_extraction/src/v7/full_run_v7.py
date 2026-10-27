"""full_run_v7 — standalone: the full run + v3 + v4 + v6 + the table-kind and column questions
(kind_tree.py, from the person's review in output/column_review/). v5 was not adopted and is
not in it. No other full_run_v* file is imported.

What each layer adds:
  base  the full run: column tags on every table, trait names spelled out (meaning v2), the
        legend inventory, the decoder, one CSV row per species x trait
  v3    decoder v3 cells, value endings, the species step for tables without a species column
  v4    which column holds the organisms (organism_tree.py)
  v6    a table read long (names + values) or wide, or no rows (structure_tree.py)
  v7    Q-KIND per table (traits / figure / model / sampling / other; Q-ALSO after a sure
        'sampling'), Q-COL / Q-ROLE per doubtful column; '(n=45)' split off organism labels

Each stage writes where it always did, so earlier results stay valid: base -> output/full_run,
v3 -> output/full_run_v3, v4 -> output/full_run_v4, ...; each layer's setup copies the earlier
answers it builds on (tags, meaning, decode, species, ...) into its own folder once.
The shared step modules (organism_tree, species_tree, structure_tree, kind_tree, trait_tree)
read the current plan from full_run.plan / full_run.species_of: install() points those at this
file's plan, with the layers the stage needs.

Stages, each resumable (one model at a time):
  base:tag        column tags on every table (nimble)
  base:meaning    trait names spelled out (nimble)
  base:inventory  the paper's legend inventory (gemma)
  base:decode     legend codes per trait column (nimble)
  v3:decode       re-ask the cells decoder v3 changes (nimble)
  v3:endings      value endings: mark or part of the value (nimble)
  v3:species      species of tables without a species column (gemma + nimble)
  v4:organism     which column holds the organisms (nimble)
  v4:species      species step for tables that now have none (gemma + nimble)
  v6:structure    long / wide / no rows per table (nimble)
  v7:kind         table kind, Q-ALSO, Q-COL / Q-ROLE (nimble)
  v7:decode       legends for columns that became trait columns (nimble)
  v7:meaning      names for columns that became trait columns (nimble)
  v7:oracle       kind/ from the review's answers instead of nimble (no model)
  assemble        the CSVs -> output/full_run_v7
  score           production scorer vs v6, then the repeatable scorer
  det             repeatable scorer only, v6 vs v7
  run             the model stages above in order (base:tag ...), then assemble

    python full_run_v7.py <stage> dev|held|all|<paper ...>
"""
import collections
import contextlib
import csv
import filecmp
import io
import json
import os
import re
import shutil
import sys
import time

import _paths
import column_role_bench as crb
import column_tree as ct
import decode_chain as dc
import decode_inv as di
import decode_units as du
import decoder as v1
import decoder_v2 as v2
import decoder_v3 as v3
import full_run as fr                 # only as the hook the shared step modules read (install)
import head_to_table as h2t
import header_tree_bench as hb
import legend_inventory as li
import meaning
import organism_tree as ot
import species_tree as sp
import kind_tree as kt
import structure_tree as st


# === base: the full run (as full_run.py) ===================================================

FULL = _paths.OUTPUT / "full_run"
V3 = _paths.OUTPUT / "full_run_v3"
V4 = _paths.OUTPUT / "full_run_v4"
V5 = _paths.OUTPUT / ("full_run_v5c" if os.environ.get("TRAIT_MODE") == "conservative" else "full_run_v5")
V6 = _paths.OUTPUT / "full_run_v6"
V7 = _paths.OUTPUT / "full_run_v7"
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
SPLIT_MARK = "\x1f"     # between the decoded parts of a list cell; assemble makes one row each


def gt_papers():
    return sorted(d.name for d in _paths.PAPERS.iterdir() if d.is_dir() and crb.paper_inputs(d))


def split():
    return json.loads((_paths.OUTPUT / "eval_split" / "split.json").read_text(encoding="utf-8"))


def papers_of(args):
    if args and args[0] in ("dev", "held"):
        return [p for p, s in split()["assign"].items() if s == args[0]]
    if args and args[0] == "all":
        return list(split()["assign"])
    return args or gt_papers()


def head_runs():
    return json.loads(HEAD.read_text(encoding="utf-8"))


def tables_of(paper, head):
    with contextlib.redirect_stdout(io.StringIO()):
        return h2t.build_tables(paper, head[paper], h2t.grids_of(paper), context=True)


def _retry(fn):
    for attempt in range(3):
        try:
            return fn()
        except RuntimeError as err:
            if attempt == 2 or "llama-server" not in str(err):
                raise
            time.sleep(30)


def known_tags(paper, root=FULL):
    """{table index: {"fields": {header: [tag, p]}, "organism": header|None}} from the
    benchmark runs (head_merge reader2_all, chain/tags_extra) and root/tags."""
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
    ff = root / "tags" / f"{paper}.json"
    if ff.exists():
        for k, v in json.loads(ff.read_text(encoding="utf-8")).items():
            out.setdefault(int(k), v)
    return out


def stage_tag(papers):
    (FULL / "tags").mkdir(parents=True, exist_ok=True)
    head = head_runs()
    client = ct.DecisionClient("nimble:9b-q4-gpu", 6)
    for paper in papers:
        f = FULL / "tags" / f"{paper}.json"
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


def base_plan(paper, head, root=FULL):
    """[(Table, tags {header: tag}, organism header, extra tags)] for every table."""
    tags = known_tags(paper, root)
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


def stage_meaning(papers):
    (FULL / "meaning").mkdir(parents=True, exist_ok=True)
    head = head_runs()
    client = ct.DecisionClient("nimble:9b-q4-gpu", 1)
    for paper in papers:
        f = FULL / "meaning" / f"{paper}.json"
        if f.exists() or paper not in head:
            continue
        text, cache, out, t0 = meaning.paper_text(paper), {}, {}, time.time()
        for t, fields, _org, _x in base_plan(paper, head):
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


def stage_inventory(papers):
    li.OUT.mkdir(parents=True, exist_ok=True)
    li.main(["build", *papers])


def decode_column(client, paper, header, values, cats, units):
    """Adjusted passage choice: QL only when >= 2 legend passages are offered and it picks
    one, else every inventory candidate; then QK/QV/QB per cell."""
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
    (FULL / "decode").mkdir(parents=True, exist_ok=True)
    head = head_runs()
    client = ct.DecisionClient(v1.NIMBLE, 1)
    for paper in papers:
        f = FULL / "decode" / f"{paper}.json"
        cats = di.inventory(paper)
        if f.exists() or paper not in head:
            continue
        cols = [c for t, fields, _o, _x in base_plan(paper, head) for c in trait_columns(t, fields)]
        res, t0 = {}, time.time()
        if cats:
            units = du.unit_texts(paper)
            for k, c, header, values in cols:
                res[f"{k}:{c}"] = _retry(lambda: decode_column(client, paper, header, values, cats, units))
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  [decode] {paper:22s} {len(cols)} trait columns ({time.time() - t0:.0f}s)", flush=True)
    v1.unload(v1.NIMBLE)


def _clean(v):
    v = " ".join(str(v or "").split())
    return "" if v.lower() in EMPTY else v


def base_species_of(t, fields, org, rec):
    """The table's organism column (the tree's table-level answer; else the first column
    tagged verbatimIdentification); a genus column on its left is joined to a lone epithet."""
    ids = [col for col in t.columns if fields.get(col.name) == "verbatimIdentification"]
    col = next((c for c in t.columns if c.name == org), None) or (ids[0] if ids else None)
    if col is None:
        return ""
    s = _clean(rec.get(col.name))
    left = [c for c in ids if c.index < col.index]
    if s and re.fullmatch(r"[a-z][a-z-]+\.?", s) and left:      # a lone epithet: join its genus
        g = _clean(rec.get(left[-1].name))
        if g and g[:1].isupper() and " " not in g:
            s = f"{g} {s}"
    return s


def assemble_csvs(papers, root, plan_of, species_of, decoded):
    """One CSV row per species x trait, in production's columns, -> root/<paper>/<paper>.csv.
      wide   each column tagged measurementType: type = its name, spelled out by the meaning
             step when it resolved; value = the cell, decoded
      long   a column tagged measurementType holding names + columns tagged measurementValue
      row fields (sex, place, date, statistic, unit, ...) and the tree's extra tags copied on."""
    head = head_runs()
    n_rows = collections.Counter()
    for paper in papers:
        if paper not in head:
            continue
        mf = root / "meaning" / f"{paper}.json"
        names = json.loads(mf.read_text(encoding="utf-8")) if mf.exists() else {}
        df = root / "decode" / f"{paper}.json"
        dec = json.loads(df.read_text(encoding="utf-8")) if df.exists() else {}
        rows = []
        for t, fields, org, xtags in plan_of(paper, head):
            long_types = [c for c in t.columns if fields.get(c.name) == "measurementType"]
            long_vals = [c for c in t.columns if fields.get(c.name) == "measurementValue"]
            is_long = bool(long_types and long_vals)
            for rec in t.records:
                s = species_of(t, fields, org, rec)
                if not s:
                    continue
                base = {"verbatimIdentification": s}
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
                                   "measurementValue": decoded(dec, t.table_index, vcol.index, v)}
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
                           "measurementValue": decoded(dec, t.table_index, col.index, v)}
                    row.update({k: x for k, x in (xtags.get(col.name) or {}).items() if k in CSV_FIELDS})
                    rows.append(row)
        write_csv(root / paper / f"{paper}.csv", rows)
        n_rows[paper] = len(rows)
        print(f"  [assemble] {paper:22s} {len(rows)} rows", flush=True)
    print(f"assembled {len(n_rows)} papers, {sum(n_rows.values())} rows")
    n = 0
    for p in papers:                     # one row per decoded part of a list cell ('M, SDW, LDW')
        rows = read_csv(root / p / f"{p}.csv")
        if rows is None or not any(SPLIT_MARK in (r.get("measurementValue") or "") for r in rows):
            continue
        out = [dict(r, measurementValue=piece) for r in rows
               for piece in (r.get("measurementValue") or "").split(SPLIT_MARK)]
        n += len(out) - len(rows)
        write_csv(root / p / f"{p}.csv", out)
    print(f"list cells split into parts: {n} extra rows")


def read_csv(f):
    if not f.exists():
        return None
    with open(f, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(f, rows):
    f.parent.mkdir(parents=True, exist_ok=True)
    with open(f, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


# === v3: decoder v3 cells, value endings, the species step (as full_run_v3.py) ==============

def v3_setup():
    V3.mkdir(parents=True, exist_ok=True)
    for d in ("tags", "meaning"):
        if not (V3 / d).exists() and (FULL / d).exists():
            shutil.copytree(FULL / d, V3 / d)
    (V3 / "decode").mkdir(exist_ok=True)


def v3_columns(paper, head):
    """(table, col index, header, all distinct values) for every trait column — the values
    normalised as trait_columns does, so the first 25 are the ones the base decode sent."""
    out = []
    for t, fields, _o, _x in base_plan(paper, head):
        for col in t.columns:
            if fields.get(col.name) not in TRAITS:
                continue
            vals = []
            for rec in t.records:
                v = " ".join(str(rec.get(col.name, "") or "").split())
                if v and v not in vals:
                    vals.append(v)
            if vals:
                out.append((t.table_index, col.index, col.name, vals))
    return out


def footnotes(paper, head, units):
    """{table index: ids of inventory units printed directly below that table} (layout)."""
    flat, spans = v3.md_tables(paper)
    out = {}
    for t, _f, _o, _x in base_plan(paper, head):
        i = v3.locate_table(t, spans)
        if i is not None:
            feet = v3.footnote_units(flat, spans[i], units)
            if feet:
                out[t.table_index] = feet
    return out


def _allowed(cats, rec):
    """The entries the column's passage choice allowed (the saved choice, not re-asked)."""
    chosen = ((rec or {}).get("units") or {}).get("chosen")
    return [e for e in cats if e.get("unit") in chosen] if chosen else cats


def stage_v3_decode(papers):
    """Per trait column, re-ask only: cells past the 25th, cells the paper prints whole as a
    code, and cells whose legend entries come from the footnote below their own table
    (asked with that fact). Everything else keeps the base decode's record."""
    v3_setup()
    head = head_runs()
    client = ct.DecisionClient(v1.NIMBLE, 1)
    for paper in papers:
        f = V3 / "decode" / f"{paper}.json"
        if f.exists() or paper not in head:
            continue
        pf = FULL / "decode" / f"{paper}.json"
        prev = json.loads(pf.read_text(encoding="utf-8")) if pf.exists() else {}
        res = dict(prev)
        cats = di.inventory(paper)
        t0, n_cols, n_foot = time.time(), 0, 0
        if cats:
            units = du.unit_texts(paper)
            feet_of = footnotes(paper, head, units)
            for k, c, header, values in v3_columns(paper, head):
                key = f"{k}:{c}"
                rec = prev.get(key)
                if rec is None and len(values) <= 25:
                    continue
                if rec is None:
                    rec = _retry(lambda: decode_column(client, paper, header, values[:25], cats, units))
                allowed = _allowed(cats, rec)
                feet = feet_of.get(k, set())
                noted, nf = v3.with_footnote(allowed, feet)
                foot = [v for v in values if nf and any(
                    e.get("unit") in feet for p in v1.list_parts(v) for e in v2.candidates(allowed, p, header)[1])]
                split_cells = [v for v, cv in (rec.get("cells") or {}).items()
                               if len(cv.get("parts") or []) > 1
                               and v2.candidates(allowed, v, header)[0] == "explicit"]
                ask = list(dict.fromkeys(values[25:] + split_cells + foot))
                if not ask:
                    continue
                rec = dict(rec, cells=dict(rec.get("cells") or {}))
                more = _retry(lambda: v2.match_column(client, header, ask, noted, shown_values=values[:25]))
                rec["cells"].update(more["cells"])
                rec["v3"] = (f"cells past 25: {len(values[25:])}, printed whole: {len(split_cells)}, "
                             f"table footnote: {len(foot)}")
                res[key] = rec
                n_cols += 1
                n_foot += len(foot)
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  [decode v3] {paper:22s} re-asked cells in {n_cols} cols, of them {n_foot} "
              f"from the table's footnote ({time.time() - t0:.0f}s)", flush=True)
    v1.unload(v1.NIMBLE)


def stage_v3_endings(papers):
    v3_setup()
    head = head_runs()
    client = ct.DecisionClient(v1.NIMBLE, 1)
    for paper in papers:
        f = V3 / "decode" / f"{paper}.json"
        if paper not in head or not f.exists():
            continue
        res = json.loads(f.read_text(encoding="utf-8"))
        if res.get("_endings_done"):
            continue
        n = 0
        for k, c, header, values in v3_columns(paper, head):
            found = v3.endings(values)
            for shape, cells in found.items():
                if len(cells) < 2 and shape == "letters":
                    continue                       # one cell is not a column's habit
                ch, probs = _retry(lambda: v3.ask_ending(client, header, values, shape, cells, paper))
                rec = res.setdefault(f"{k}:{c}", {"cells": {}})
                rec.setdefault("endings", {})[shape] = {"choice": ch, "probs": probs,
                                                        "cells": {v: val for v, (val, _e) in cells.items()}}
                n += 1
        res["_endings_done"] = True
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        if n:
            print(f"  [endings] {paper:22s} {n} questions", flush=True)
    v1.unload(v1.NIMBLE)


def stage_v3_species(papers):
    v3_setup()
    install(V3)
    sp.run(papers, V3 / "species")


def decoded(dec, k, c, cell):
    """The cell's decoded term (each part on its own when parts were decoded apart, joined
    by SPLIT_MARK); else the value without the ending nimble called a mark; else the cell."""
    r = dec.get(f"{k}:{c}") or {}
    rc = (r.get("cells") or {}).get(cell) or {}
    term = rc.get("term")
    if term:
        parts = rc.get("parts") or []
        pieces = term.split("; ")
        if len(parts) > 1 and len(pieces) == len(parts):
            return SPLIT_MARK.join(pieces)
        return term
    for e in (r.get("endings") or {}).values():
        if e.get("choice") == "mark" and cell in e["cells"]:
            return e["cells"][cell]
    return cell


# === v4: which column holds the organisms (as full_run_v4.py) ================================

def v4_setup():
    V4.mkdir(parents=True, exist_ok=True)
    for d in ("tags", "meaning", "decode", "species"):
        if not (V4 / d).exists() and (V3 / d).exists():
            shutil.copytree(V3 / d, V4 / d)


def stage_v4_organism(papers):
    v4_setup()
    install(V4)
    ot.run(V4, papers)


def stage_v4_species(papers):
    v4_setup()
    install(V4, decisions=True)
    sp.run(papers, V4 / "species")


def has_species(root):
    """f(t, fields, org): the table gives species — its organism column, or the species step."""
    def f(t, fields, org):
        if any(fr.species_of(t, fields, org, r) for r in t.records):
            return True
        return bool(sp.species_of_tables(root / "species", getattr(t, "paper", "")).get(t.table_index))
    return f


# === v6: long / wide / no rows per table (as full_run_v6.py) ================================

def v6_setup():
    V6.mkdir(parents=True, exist_ok=True)
    for d in ("tags", "meaning", "decode", "species", "organism"):
        if not (V6 / d).exists() and (V4 / d).exists():
            shutil.copytree(V4 / d, V6 / d)


def stage_v6_structure(papers):
    v6_setup()
    install(V6, decisions=True)
    st.run(V6, papers, has_species(V6))


# === v7: table kind and doubtful columns (as full_run_v7.py) =================================

REVIEW = _paths.OUTPUT / "column_review" / "reviews"
REVIEWED = ["Attiwilli2022", "CortesGomez2023", "Cortés-Goméz2023", "Figueroa2021",
            "Melo2021", "Orlofsk2014"]
SAME_PAPER = {"Cortés-Goméz2023": "CortesGomez2023"}
# answers the person gave in the chat after the review (2026-10-21)
VERDICT_FIX = {("Figueroa2021", 1): "yes"}       # 'not on the GT but should have been extracted'


def v7_setup():
    V7.mkdir(parents=True, exist_ok=True)
    for d in ("tags", "meaning", "decode", "species", "organism", "structure"):
        if not (V7 / d).exists() and (V6 / d).exists():
            shutil.copytree(V6 / d, V7 / d)


def structure_of(paper):
    return _load(V7 / "structure" / f"{paper}.json")


def stage_v7_kind(papers):
    v7_setup()
    install(V7, decisions=True, structure=True)
    kt.run(V7, papers, has_species(V7), structure_of)


def stage_v7_oracle(papers):
    """kind/<paper>.json from the review: a table marked 'no' (or noted 'do not extract')
    gives no rows; a column's corrected tag replaces the tree's."""
    v7_setup()
    (V7 / "kind").mkdir(parents=True, exist_ok=True)
    for p in papers:
        if p not in REVIEWED:
            continue
        src = SAME_PAPER.get(p, p)
        orgs = kt.organism_decisions(V7, p)
        res = {}
        for f in sorted(REVIEW.glob(f"{src}__t*.json")):
            d = json.loads(f.read_text(encoding="utf-8"))
            d = d.get("data", d)
            t = int(d["table"])
            verdict = VERDICT_FIX.get((src, t), d.get("verdict") or "")
            if verdict == "no" or (verdict in ("", "unsure") and "do not extract" in (d.get("note") or "").lower()):
                res[str(t)] = {"action": "no rows", "kind": {"choice": "review", "probs": {}}, "cols": {}}
                continue
            cols = {c["header"]: {"q": "oracle", "tag": c["tag"]}
                    for c in (d.get("cols") or {}).values() if c.get("tag")}
            res[str(t)] = {"action": "keep", "kind": {"choice": "review", "probs": {}}, "cols": cols}
            gcol = kt.groups_column(orgs.get(str(t)))
            kept = {c["header"] for c in (d.get("cols") or {}).values()
                    if (c.get("tag") or c.get("tree")) == "verbatimIdentification"}
            if gcol and (gcol in kept or not any(c["header"] == gcol for c in (d.get("cols") or {}).values())):
                res[str(t)]["organism"] = gcol
        (V7 / "kind" / f"{p}.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  [oracle] {p:22s} {sum(r['action'] == 'no rows' for r in res.values())} tables no rows, "
              f"{sum(len(r['cols']) for r in res.values())} column tags", flush=True)


def stage_v7_decode(papers):
    """Legends for trait columns the earlier decode never saw (a column that became a trait)."""
    v7_setup()
    install(V7, decisions=True, structure=True, kind=True)
    head = head_runs()
    client = None
    for p in papers:
        f = V7 / "decode" / f"{p}.json"
        dec = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
        todo = [c for t, fields, _o, _x in fr.plan(p, head) for c in trait_columns(t, fields)
                if f"{c[0]}:{c[1]}" not in dec]
        cats = di.inventory(p) if todo else None
        if not todo or not cats:
            continue
        client = client or ct.DecisionClient(v1.NIMBLE, 1)
        units, t0 = du.unit_texts(p), time.time()
        for k, c, header, values in todo:
            dec[f"{k}:{c}"] = _retry(lambda: decode_column(client, p, header, values, cats, units))
        f.write_text(json.dumps(dec, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  [decode v7] {p:22s} {len(todo)} new trait columns ({time.time() - t0:.0f}s)", flush=True)
    if client:
        v1.unload(v1.NIMBLE)


def stage_v7_meaning(papers):
    """Names for trait columns the earlier meaning step never saw ('FG' -> 'Functional Groups')."""
    v7_setup()
    install(V7, decisions=True, structure=True, kind=True)
    head = head_runs()
    client = None
    for p in papers:
        f = V7 / "meaning" / f"{p}.json"
        names = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
        todo = list(dict.fromkeys(c.name for t, fields, _o, _x in fr.plan(p, head) for c in t.columns
                                  if fields.get(c.name) == "measurementType" and c.name not in names))
        if not todo:
            continue
        client = client or ct.DecisionClient(v1.NIMBLE, 1)
        text, cache = meaning.paper_text(p), {}
        for h in todo:
            try:
                names[h] = meaning.read_label(client, text, h, cache=cache).get("expanded") or h
            except RuntimeError:
                names[h] = h
        f.write_text(json.dumps(names, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  [meaning v7] {p:22s} {len(todo)} new names", flush=True)
    if client:
        v1.unload(v1.NIMBLE)


# === the plan: every layer applied in order ===================================================

_CACHE = {}


def _load(f):
    """A decision file, read once per process (decisions are written before they are read)."""
    if f not in _CACHE:
        _CACHE[f] = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    return _CACHE[f]


def plan(paper, head, root, *, tags=FULL, species=False, decisions=False, structure=False, kind=False):
    """[(Table, tags, organism header, extra tags)] for every table, with the layers asked for,
    in the order they were built:
      tags       the column tags (base; read from `tags`)
      decisions  t.paper is set: species follow root/organism (v4)
      structure  root/structure: a long reading, wide, or no rows (v6)
      kind       root/kind applied to the tags; t.kind_organism (v7)
      species    t.paper_species from root/species, for tables with no species column (v3)"""
    out = base_plan(paper, head, tags)
    if decisions:
        for t, _f, _o, _x in out:
            t.paper = paper
    if structure:
        dec = _load(root / "structure" / f"{paper}.json")
        out = [(t, f, org, x) for t, fields, org, x in out
               for f in st.expand(fields, dec.get(str(t.table_index)))]
    if kind:
        dec = _load(root / "kind" / f"{paper}.json")
        res = []
        for t, fields, org, x in out:
            d = dec.get(str(t.table_index))
            t.kind_organism = kt.organism_column(d)
            res.append((t, kt.apply(fields, d), org, x))
        out = res
    if species:                                    # the table's species, if nimble named one
        named = sp.species_of_tables(root / "species", paper)
        for t, _f, _o, _x in out:
            t.paper_species = named.get(t.table_index, "")
    return out


def species_fn(root, decisions=False):
    """f(t, fields, org, rec) -> the record's species, by the same layers as plan():
    the kind step's organism column (v7), else
    the organism decision (v4, tables plan() gave t.paper), else
    the tagged organism column (base); else the species step's name (v3)."""
    fr.species_of = base_species_of               # organism_fn keeps the one installed now
    decide = ot.organism_fn(root) if decisions else None

    def f(t, fields, org, rec):
        col = getattr(t, "kind_organism", None)
        if col:
            s = _clean(rec.get(col))
        elif decide and hasattr(t, "paper"):
            s = decide(t.paper, t, fields, org, rec)
        else:
            s = base_species_of(t, fields, org, rec)
        return s or getattr(t, "paper_species", "")
    return f


def install(root, decisions=False, structure=False, kind=False):
    """Point full_run.plan / full_run.species_of (read by the shared step modules) at this
    file's plan with these layers; base species always, decisions when asked."""
    fr.plan = lambda paper, head: plan(paper, head, root, decisions=decisions, structure=structure, kind=kind)
    fr.species_of = species_fn(root, decisions)


# === score ===================================================================================

def score_changed(papers, out, prev):
    """evaluate_all on out, re-evaluating only papers whose CSV differs from prev's (a paper
    with the same CSV takes prev's report); miss-severity grading off, as in the full run."""
    import evaluate as ev
    ev.ASSESS_MISS_SEVERITY = False
    changed = []
    for p in papers:
        new, old = out / p / f"{p}.csv", prev / p / f"{p}.csv"
        if not new.exists():
            continue
        if old.exists() and filecmp.cmp(new, old, shallow=False):
            for g in (prev / p).iterdir():          # same CSV: same score, copy the report
                if g.name != f"{p}.csv":
                    shutil.copy(g, out / p / g.name)
        else:
            changed.append(p)
            for g in (out / p).glob(f"{p}_report.txt"):
                g.unlink()
    if (prev / "summary.csv").exists():
        shutil.copy(prev / "summary.csv", out / "summary.csv")
    print(f"re-scoring {len(changed)} changed papers: {', '.join(changed)}", flush=True)
    ev.evaluate_all(_paths.PAPERS, out, ev.DEFAULT_KEY, False, semantic=True, use_llm=True,
                    skip_existing=True)
    return changed


def rebuild_summary(out):
    """summary.csv from each paper's own report (score_changed starts from prev's summary,
    which would carry prev's numbers for papers scored in an earlier run)."""
    import evaluate as ev
    rows = []
    for p in sorted(split()["assign"]):
        rep = out / p / f"{p}_report.txt"
        m = ev._metrics_from_report(rep) if rep.exists() else None
        rows.append({"paper": p, "precision": m[0] if m else "", "recall": m[1] if m else "",
                     "f1": m[2] if m else "", "status": "ok" if m else "no report"})
    with open(out / "summary.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["paper", "precision", "recall", "f1", "status"])
        w.writeheader()
        w.writerows(rows)


def compare(papers, prev, out, old, new, name):
    """Per paper F1, old vs new, on these papers only; regressions = F1 drop > 0.005."""
    def load(root):
        with open(root / "summary.csv", encoding="utf-8") as fh:
            return {r["paper"]: r for r in csv.DictReader(fh)}
    a, b = load(prev), load(out)
    rows = [(p, float(a[p]["f1"] or 0), float(b[p]["f1"] or 0)) for p in papers if p in a and p in b]
    n = max(1, len(rows))
    L = [f"{new} vs {old} on {len(rows)} papers: mean F1 {sum(r[1] for r in rows) / n:.3f} -> "
         f"{sum(r[2] for r in rows) / n:.3f}",
         f"improved {sum(y > x + 0.005 for _p, x, y in rows)}, "
         f"regressed {sum(y < x - 0.005 for _p, x, y in rows)}", ""]
    for p, x, y in sorted(rows, key=lambda r: r[2] - r[1], reverse=True):
        if abs(y - x) > 0.0005:
            L.append(f"  {p:22s} {x:.3f} -> {y:.3f}  {y - x:+.3f}")
    (out / name).write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


def det_score(root, p):
    """evaluate() with the LLM pass off: trait names matched by strings and values only."""
    import evaluate as ev
    from mineru_extract import classify_folder
    pred = root / p / f"{p}.csv"
    if not pred.exists():
        return None
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        _, gt, _ = classify_folder(_paths.PAPERS / p)
        if not gt:
            return None
        ev.evaluate(str(pred), str(gt), ev.DEFAULT_KEY, False, semantic=True, use_llm=False)
    t = buf.getvalue()
    g = lambda lab: int((re.search(lab + r"\s*:\s*(\d+)", t) or [0, 0])[1])
    return {"tp": g(r"matched \(TP\)"), "fn": g(r"missed \(FN\)"), "fp": g(r"spurious, in scope")}


def _f1(d):
    p = d["tp"] / (d["tp"] + d["fp"]) if d["tp"] + d["fp"] else 0.0
    r = d["tp"] / (d["tp"] + d["fn"]) if d["tp"] + d["fn"] else 0.0
    return 2 * p * r / (p + r) if p + r else 0.0


def det_compare(papers, prev, out, old, new, name):
    """The repeatable scorer (use_llm=False) on prev and out alike."""
    rows = []
    for p in papers:
        a, b = det_score(prev, p), det_score(out, p)
        if a and b:
            rows.append((p, a, b))
    tot = lambda i: {k: sum(r[i][k] for r in rows) for k in ("tp", "fn", "fp")}
    a, b = tot(1), tot(2)
    L = [f"repeatable scorer (use_llm=False), {len(rows)} papers: micro F1 {old} {_f1(a):.3f} -> "
         f"{new} {_f1(b):.3f}  (TP {a['tp']} -> {b['tp']}, FP {a['fp']} -> {b['fp']}, FN {a['fn']} -> {b['fn']})"]
    fa = [_f1(x) for _p, x, _y in rows]
    fb = [_f1(y) for _p, _x, y in rows]
    L.append(f"mean F1 {sum(fa) / max(1, len(fa)):.3f} -> {sum(fb) / max(1, len(fb)):.3f}; "
             f"improved {sum(y > x + 0.005 for x, y in zip(fa, fb))}, "
             f"regressed {sum(y < x - 0.005 for x, y in zip(fa, fb))}")
    for (p, x, y), u, w in sorted(zip(rows, fa, fb), key=lambda r: r[2] - r[1], reverse=True):
        if abs(w - u) > 0.0005 or x != y:
            L.append(f"  {p:22s} {u:.3f} -> {w:.3f}  TP {x['tp']}->{y['tp']} FP {x['fp']}->{y['fp']}")
    (out / name).write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


# === v7's own: assemble and score ============================================================

OUT, PREV = V7, V6


def stage_assemble(papers):
    v7_setup()
    install(OUT, decisions=True, structure=True, kind=True)
    assemble_csvs(papers, OUT, lambda p, h: plan(p, h, OUT, tags=OUT, decisions=True, structure=True,
                                                 kind=True, species=True),
                  species_fn(OUT, decisions=True), decoded)
    n = 0
    for p in papers:                     # 'Hesperiidae(n=45)' -> organism + sample size
        rows = read_csv(OUT / p / f"{p}.csv")
        if rows is None:
            continue
        k = kt.split_n(rows)
        if k:
            n += k
            write_csv(OUT / p / f"{p}.csv", rows)
    print(f"sample sizes split off organism labels: {n} rows")


def stage_score(papers):
    score_changed(papers, OUT, PREV)
    rebuild_summary(OUT)
    compare(papers, PREV, OUT, "v6", "v7", "COMPARE_V7_production.txt")
    det_compare(papers, PREV, OUT, "v6", "v7", "COMPARE_V7_repeatable.txt")


OWN_STAGES = {"v7:oracle": stage_v7_oracle, "assemble": stage_assemble, "score": stage_score,
              "det": lambda papers: det_compare(papers, PREV, OUT, "v6", "v7", "COMPARE_V7_repeatable.txt")}


# === stages =================================================================================

PIPELINE = {
    "base:tag": stage_tag,
    "base:meaning": stage_meaning,
    "base:inventory": stage_inventory,
    "base:decode": stage_decode,
    "v3:decode": stage_v3_decode,
    "v3:endings": stage_v3_endings,
    "v3:species": stage_v3_species,
    "v4:organism": stage_v4_organism,
    "v4:species": stage_v4_species,
    "v6:structure": stage_v6_structure,
    "v7:kind": stage_v7_kind,
    "v7:decode": stage_v7_decode,
    "v7:meaning": stage_v7_meaning,
}
# the stage names this file had before it was made standalone (callers still use them)
ALIASES = {"kind": "v7:kind", "oracle": "v7:oracle", "decode": "v7:decode", "meaning": "v7:meaning"}
STAGES = {**PIPELINE, **OWN_STAGES}
STAGES.update({a: STAGES[b] for a, b in ALIASES.items()})


def run_all(papers):
    """Every pipeline stage in order, then assemble (score separately: it needs a GT)."""
    for name, fn in [*PIPELINE.items(), ("assemble", stage_assemble)]:
        t0 = time.time()
        print(f"\n===== {name} {time.strftime('%H:%M:%S')}", flush=True)
        fn(papers)
        print(f"===== {name} done in {round((time.time() - t0) / 60)} min", flush=True)


def main(argv):
    stage, papers = argv[0], papers_of(argv[1:])
    if stage != "run" and stage not in STAGES:
        raise SystemExit(f"unknown stage {stage!r}; stages: run, {', '.join(STAGES)}")
    (run_all if stage == "run" else STAGES[stage])(papers)


if __name__ == "__main__":
    main(sys.argv[1:])
