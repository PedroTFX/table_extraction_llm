"""
header_tree_bench.py — TEST: does header_tree.py find each table's layout better
than the pipeline's gemma header finder (table_to_data.agent_find_header)?

Two steps, so no model is ever re-run to change the scoring:

  1. COLLECT — one variant per run, ONE model at a time, every table of every
     paper, stored complete (first record, every column's name and groups):
        --variant gemma   the pipeline's way: continuation fragments inherit the
                          previous table's header (tables.is_headerless_continuation),
                          every other table asks agent_find_header (gemma)
        --variant code    header_tree, code only (column vote + code roles)
        --variant q4      header_tree, nimble Q4 answers every question of the tree
        --variant tev1    header_tree, tev1 answers every question of the tree
        --variant head    head_tree (the frozen head reader: whole-row first record,
                          cell roles, QSPEC with the labels in its options), nimble;
                          body rows are asked only on the tables the GT draws on
     The tree models see the symbol grid only (header_tree mode 'model'). A tree
     table with no header inherits the previous table's names, as the pipeline
     does for gemma.

  2. SCORE (--summary) — against an answer key derived from the GT:
     first record  the first row holding a GT species, or >= 2 GT values whose cells
                   have the same shape as the cells below them (a header label that
                   is a GT value — 'Ground | Specialist' over 0/1 — is not data); a
                   row with GT species across >= 2 columns over non-names is a
                   transposed header. 'unsure' (not scored) when data the GT does
                   not record sits above: a Latin-name cell, or a row of the same shape.
     names         for each column whose key values the GT records under ONE trait,
                   does the produced name (or a group label + name) match it?
     groups        header_tree only: group labels found, and how many the GT records.
     buckets       head only: every miss filed under the question that decided it
                   (first record, Q-SPEC, QS, a row label over the column, other QC,
                   names inherited). The five DEV tables are left out of every score.

    python header_tree_bench.py --variant gemma --resume --minutes 25
    python header_tree_bench.py --variant code
    python header_tree_bench.py --variant q4 --resume --minutes 25
    python header_tree_bench.py --summary          # -> summary.txt, detail.txt
    python header_tree_bench.py --variant code Kovacs2010 Barber2017   # chosen papers

Writes tree_extraction/output/header_tree_bench/{<variant>.json, summary.txt, detail.txt}.
"""

from __future__ import annotations

import collections
import difflib
import json
import re
import sys
import time

import _paths
import column_role_bench as crb
import column_tree as ct
import header_tree as ht
from evaluate import load_xlsx

OUT = _paths.OUTPUT / "header_tree_bench"
PAPER_LIST = _paths.OUTPUT / "column_tree_bench" / "q4_papers.txt"
EXTRA = ["Tsai2020"]
MAX_KEY_ROW = 12
TREE_VARIANTS = {"code": None, "q4": ("nimble:9b-q4-gpu", 6), "tev1": ("tev1:4b", 1),
                 "head": ("nimble:9b-q4-gpu", 6)}
# the five tables the head reader was developed on: left out of the scores
DEV = {("Oliveira2022", 14), ("Korosi2022", 0), ("GibbParr2013", 0), ("Barber2017", 6),
       ("Graf2021", 7)}
GROUP_FIELDS = ["caste", "sex", "lifeStage", "verbatimLocality", "verbatimEventDate",
                "measurementType", "measurementStatistic", "sampleTreatment"]


def html_tables(paper):
    t = (_paths.PAPERS / paper / f"{paper}_full.md").read_text(encoding="utf-8", errors="replace")
    return re.findall(r"<table.*?</table>", t, flags=re.S | re.I)


def default_papers():
    return PAPER_LIST.read_text(encoding="utf-8").split() + EXTRA


# =============================================================================
# 1. COLLECT
# =============================================================================

def collect_tree(paper, client=None, mode="code"):
    out = []
    for k, table_html in enumerate(html_tables(paper)):
        grid = ht.grid_from_html(table_html)
        if grid.nrows < 2 or grid.ncols < 2:
            continue
        t0 = time.time()
        plan = ht.decide(grid, client=client, mode=mode)
        out.append({
            "table": k, "nrows": grid.nrows, "ncols": grid.ncols,
            "data_start": plan.data_start.get(0), "first": ht.first_record(plan, 0),
            "decided_by": plan.decided_by.get(0), "blocks": len(plan.blocks),
            # the decision itself: block-0 columns and the role of every header
            # row; names are rebuilt from these at scoring (header_tree.
            # columns_from_roles), so a code fix never needs a model re-run
            "cols": plan.blocks[0],
            "roles": {str(r): plan.row_roles[(0, r)] for r in range(plan.data_start.get(0, 0))
                      if (0, r) in plan.row_roles},
            "columns": [{"col": c["col"], "name": c["name"], "groups": c["groups"]}
                        for c in plan.columns if c["block"] == 0],
            "sections": [s for b, _r, s in plan.sections if b == 0][:20],
            "render": ht.render(grid, plan), "secs": round(time.time() - t0, 2)})
    return out


def keyed_tables(paper):
    """The tables the GT draws on (an answer key exists)."""
    gp = crb.paper_inputs(_paths.PAPERS / paper)
    if not gp:
        return set()
    gt = GT(load_xlsx(gp[1]))
    out = set()
    for k, table_html in enumerate(html_tables(paper)):
        grid = ht.grid_from_html(table_html)
        if grid.nrows >= 2 and grid.ncols >= 2 and answer_key(grid, gt, ht.Symbols.of(grid))[0] is not None:
            out.add(k)
    return out


def collect_head(paper, client):
    """head_tree, table by table; the full result is kept for the report."""
    import head_tree as hd
    keyed = keyed_tables(paper)
    out = []
    for k, table_html in enumerate(html_tables(paper)):
        grid = ht.grid_from_html(table_html)
        if grid.nrows < 2 or grid.ncols < 2:
            continue
        r = hd.read_table(grid, client, "B", body=k in keyed)
        r.update(paper=paper, table=k)
        out.append({"table": k, "nrows": grid.nrows, "ncols": grid.ncols,
                    "data_start": r["head_end"], "first": r["start"],
                    "columns": r["columns"], "secs": r["secs"], "calls": r["calls"], "full": r})
        print(f"  table {k} ({grid.nrows}x{grid.ncols}): first record {r['start']}, head rows "
              f"{r['head_start']}-{r['head_end'] - 1}, {r['calls']} calls, {r['secs']}s", flush=True)
    return out


def collect_gemma(paper):
    """The pipeline's header handling, table by table in document order."""
    from table_to_data import agent_find_header
    from tables import is_headerless_continuation, parse_table
    from text_manager import clean_tables
    out, parent = [], None
    for k, table_html in enumerate(html_tables(paper)):
        grid = ht.grid_from_html(table_html)
        if grid.nrows < 2 or grid.ncols < 2:
            continue
        text = clean_tables(table_html)
        lines = [l for l in (ln.strip() for ln in text.strip().splitlines()) if l]
        html_rows = [r for r, row in enumerate(ht._TR_RE.findall(table_html))
                     if ht._CELL_RE.findall(row)]
        t0 = time.time()
        entry = {"table": k, "continuation": False}
        try:
            if parent is not None and is_headerless_continuation(parent, text):
                header = [("" if c.synthetic else c.name) for c in parent.columns]
                table = parse_table("\n".join(lines), header_override=header)
                entry.update(continuation=True, first=html_rows[0] if html_rows else 0,
                             plan=None)
            else:
                plan = agent_find_header(lines)
                table = parse_table("\n".join(lines), header_rows=plan)
                fl = max(plan["header_rows"]) + 1
                entry.update(first=html_rows[fl] if fl < len(html_rows) else None, plan=plan)
                parent = table                           # owns its header
            entry["names"] = {str(c.index): ("" if c.synthetic else c.name) for c in table.columns}
        except Exception as e:
            entry.update(first=None, names={}, error=f"{type(e).__name__}: {e}")
        entry["secs"] = round(time.time() - t0, 2)
        out.append(entry)
        print(f"  table {k}: gemma first {entry.get('first')}"
              f"{' (continuation)' if entry['continuation'] else ''}")
    return out


def run_collect(variant, papers, resume, budget):
    path = OUT / f"{variant}.json"
    results = (json.loads(path.read_text(encoding="utf-8"))
               if resume and path.exists() else {})
    client = None
    if TREE_VARIANTS.get(variant):
        client = ct.DecisionClient(*TREE_VARIANTS[variant])
    started, finished = time.time(), True
    for paper in papers:
        if paper in results:
            continue
        if budget and time.time() - started > budget:
            finished = False
            print(f"time budget used: stopping before {paper} (resume to continue)")
            break
        if not crb.paper_inputs(_paths.PAPERS / paper):
            continue
        print(f"\n=== {paper} [{variant}]")
        try:
            results[paper] = (collect_gemma(paper) if variant == "gemma"
                              else collect_head(paper, client) if variant == "head"
                              else collect_tree(paper, client, "model" if client else "code"))
        except Exception as e:
            print(f"  skipped: {type(e).__name__}: {e}")
            continue
        path.write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\n{variant}: {len(results)} paper(s) collected"
          + ("" if finished else " - NOT FINISHED, resume"))


# =============================================================================
# 2. SCORE
# =============================================================================

class GT:
    def __init__(self, rows):
        self.g = crb.GroundTruth(rows)
        self.by_pair = collections.defaultdict(list)
        self.by_value = collections.defaultdict(list)
        for r in rows:
            v = crb.norm(r["measurementValue"])
            if v:
                self.by_pair[(r["verbatimIdentification"].strip(), v)].append(r)
                self.by_value[v].append(r)

    def value_hit(self, cell) -> bool:
        return any(p in self.by_value and (len(p) >= 3 or "." in p) for p in crb.parts(cell))

    def rows_for(self, rid, cell):
        hits = []
        for p in crb.parts(cell):
            if rid:
                hits += self.by_pair.get((rid, p), [])
        if not hits and not rid:
            for p in crb.parts(cell):
                if len(p) >= 3 or "." in p:
                    hits += self.by_value.get(p, [])
        return hits


def _signature(grid, S, r):
    return tuple(ht.family(S.class_at(r, c) or "<") for c in range(grid.ncols))


def _family_below(grid, S, r, c, n=20):
    fams = [ht.family(S.class_at(rr, c) or "") for rr in range(r + 1, min(grid.nrows, r + 1 + n))]
    fams = [f for f in fams if f and f != "·"]
    return collections.Counter(fams).most_common(1)[0][0] if fams else None


def answer_key(grid, gt: GT, S):
    for r in range(min(grid.nrows, MAX_KEY_ROW)):
        sp_cols, val_cols = [], []
        for c in range(grid.ncols):
            x = grid.origin(r, c)
            if not x or not x.text:
                continue
            if gt.g.match_id(x.text):
                sp_cols.append(c)
            elif gt.value_hit(x.text):
                below = _family_below(grid, S, r, c)
                if below is None or below == ht.family(S.sym[(r, c)]):
                    val_cols.append(c)        # a value shaped like the values below it
        if len(sp_cols) >= 2 and not any(_family_below(grid, S, r, c) == "L" for c in sp_cols):
            continue                          # species ACROSS the header (transposed)
        if sp_cols or len(val_cols) >= 2:
            sig = _signature(grid, S, r)
            unsure = (any(S.sym.get((rr, c)) == "L" for rr in range(r) for c in range(grid.ncols))
                      or any(_signature(grid, S, rr) == sig for rr in range(r)))
            return r, unsure
    return None, False


def _words(s):
    return re.findall(r"[a-z]{2,}", re.sub(r"\([^)]*\)|\[[^\]]*\]", " ", str(s or "").lower()))


def name_matches(name, trait) -> bool:
    a, b = " ".join(_words(name)), " ".join(_words(trait))
    if not a or not b:
        return False
    la, lb = a.replace(" ", ""), b.replace(" ", "")
    if (len(lb) >= 4 and lb in la) or (len(la) >= 4 and la in lb):
        return True
    if difflib.SequenceMatcher(None, a, b).ratio() >= 0.8:
        return True
    wa, wb = set(a.split()), set(b.split())
    return len(wa & wb) / len(wa | wb) >= 0.6


def key_columns(grid, gt: GT, first):
    rows = range(first, grid.nrows)
    hits = {c: sum(1 for r in rows if gt.g.match_id(grid.text(r, c))) for c in range(grid.ncols)}
    id_col = max(hits, key=hits.get) if hits else None
    if id_col is not None and hits[id_col] < 0.3 * max(1, len(rows)):
        id_col = None
    single = gt.g.ids[0] if len(gt.g.ids) == 1 else None
    out = {}
    for c in range(grid.ncols):
        if c == id_col:
            continue
        matched = []
        for r in rows:
            rid = gt.g.match_id(grid.text(r, id_col)) if id_col is not None else single
            matched += gt.rows_for(rid, grid.text(r, c))
        if len(matched) < 2:
            continue
        t, n = collections.Counter(m["measurementType"].strip() for m in matched).most_common(1)[0]
        out[c] = (t if n / len(matched) >= 0.7 else None, matched)
    return out


def _inherit(entries):
    """A tree table without a header takes the column names of the last table
    that had one, when the widths match (what the pipeline does for gemma)."""
    parent = None
    for e in entries:
        if e.get("data_start") == 0 and parent and parent["ncols"] == e["ncols"]:
            e["names_from"] = parent["table"]
            e["columns"] = parent["columns"]
        elif e.get("data_start"):
            parent = e
    return entries


def score(papers=None):
    runs = {}
    for v in ["gemma", *TREE_VARIANTS]:
        f = OUT / f"{v}.json"
        if f.exists():
            runs[v] = json.loads(f.read_text(encoding="utf-8"))
    if not runs:
        return "no results", ""
    papers = papers or sorted(set.intersection(*[set(r) for r in runs.values()]))
    tree_vs = [v for v in TREE_VARIANTS if v in runs]
    tally = {v: collections.Counter() for v in runs}
    detail, n_tables, n_sure = [], 0, 0
    group_stats = {v: collections.Counter() for v in tree_vs}
    buckets, head_stats, look = collections.Counter(), collections.Counter(), []
    for paper in papers:
        gt_path = crb.paper_inputs(_paths.PAPERS / paper)
        if not gt_path:
            continue
        gt = GT(load_xlsx(gt_path[1]))
        tabs = html_tables(paper)
        by = {v: {e["table"]: e for e in (_inherit(runs[v].get(paper, []))
                                          if v in tree_vs else runs[v].get(paper, []))}
              for v in runs}
        for k, table_html in enumerate(tabs):
            if not all(k in by[v] for v in runs) or (paper, k) in DEV:
                continue
            grid = ht.grid_from_html(table_html)
            S = ht.Symbols.of(grid)
            key, unsure = answer_key(grid, gt, S)
            if key is None:
                continue
            n_tables += 1
            n_sure += not unsure
            kc = key_columns(grid, gt, key)
            for v in tree_vs:                    # rebuild names from the stored roles
                e = by[v][k]
                if "roles" in e and "names_from" not in e:
                    roles = {int(r): role for r, role in e["roles"].items()}
                    e["columns"] = [{"col": c["col"], "name": c["name"], "groups": c["groups"]}
                                    for c in ht.columns_from_roles(grid, S, e["cols"], roles)]
            lines = []
            for v in runs:
                e = by[v][k]
                if not unsure:
                    tally[v]["first_n"] += 1
                    ok = e.get("first") == key
                    tally[v]["first_ok"] += ok
                    if not ok:
                        lines.append(f"    {v:6s} first {e.get('first')} (key {key})"
                                     f" {e.get('decided_by') or ('continuation' if e.get('continuation') else '')}")
                if v == "gemma":
                    names = {int(c): (n, []) for c, n in (e.get("names") or {}).items()}
                else:
                    names = {c["col"]: (c["name"], c["groups"]) for c in e["columns"]}
                first_wrong = not unsure and e.get("first") != key
                if v == "head":
                    buckets["tables: first record wrong"] += first_wrong
                    head_stats["calls"] += e.get("calls", 0)
                    full = e.get("full", {})
                    if full.get("pre"):
                        look.append(f"{paper} table {k}: rows between the head and the first "
                                    f"record: " + ", ".join(f"{r} {v_[0]}" for r, v_ in full["pre"].items()))
                    head_stats["body rows asked"] += len(full.get("body", {}))
                for c, (trait, matched) in kc.items():
                    if not trait:
                        continue
                    name, groups = names.get(c, ("", []))
                    ok = name_matches(name, trait) or any(
                        name_matches(g, trait) or name_matches(f"{g} {name}", trait) for g in groups)
                    tally[v]["names_n"] += 1
                    tally[v]["names_ok"] += ok
                    if v == "head":
                        col = next((x for x in e["columns"] if x["col"] == c), None)
                        by_q = (col or {}).get("decided_by")
                        if by_q == "QSPEC":
                            head_stats["qspec_n"] += 1
                            head_stats["qspec_ok"] += ok
                        if not ok:
                            if first_wrong:
                                b = "names: after a wrong first record"
                            elif "names_from" in e:
                                b = "names: no head found, names inherited"
                            elif col is None:
                                b = "names: column not read"
                            elif by_q == "undecided":
                                b = ("names: undecided, a row label over it" if col.get("row_label_over")
                                     else "names: undecided, other QC")
                            else:
                                b = {"QSPEC": "names: Q-SPEC", "QS": "names: single-column stack (QS)",
                                     "QC": "names: other QC"}.get(by_q, "names: other")
                            buckets[b] += 1
                    if not ok:
                        lines.append(f"    {v:6s} col {c}: '{name[:30]}'"
                                     f"{' [' + '/'.join(groups) + ']' if groups else ''} "
                                     f"vs GT trait '{trait}'")
                if v in tree_vs:
                    for c, (trait, matched) in kc.items():
                        _n, groups = names.get(c, ("", []))
                        for g in groups:
                            group_stats[v]["groups"] += 1
                            gw = {w.rstrip("s") for w in _words(g)}
                            if any(gw & {w.rstrip("s") for m in matched for w in _words(m.get(f, ""))}
                                   for f in GROUP_FIELDS):
                                group_stats[v]["recorded"] += 1
                tally[v]["secs"] += e.get("secs", 0)
            if lines:
                detail.append(f"{paper} table {k} ({grid.nrows}x{grid.ncols}): key {key}"
                              f"{' (unsure)' if unsure else ''}")
                shown = by.get("code") or by.get(tree_vs[0]) if tree_vs else None
                if shown and shown[k].get("render"):
                    detail.append(shown[k]["render"])
                detail += lines
                detail.append("")
    pct = lambda a, b: f"{a}/{b} {a / b:.0%}" if b else "-"
    cols = list(runs)
    W = 18
    L = [f"{len(papers)} papers, {n_tables} tables the GT draws on ({n_sure} with a sure key)",
         "", f"{'':34s}" + "".join(f"{('tree ' + v if v != 'gemma' else 'gemma (pipeline)'):>{W}s}" for v in cols),
         f"{'first record row right':34s}" + "".join(
             f"{pct(tally[v]['first_ok'], tally[v]['first_n']):>{W}s}" for v in cols),
         f"{'column names match the GT trait':34s}" + "".join(
             f"{pct(tally[v]['names_ok'], tally[v]['names_n']):>{W}s}" for v in cols),
         f"{'group labels found / GT records':34s}" + "".join(
             (f"{group_stats[v]['groups']} / {group_stats[v]['recorded']}" if v in tree_vs
              else "joined into names").rjust(W) for v in cols),
         f"{'seconds (tables scored)':34s}" + "".join(f"{tally[v]['secs']:>{W}.0f}" for v in cols)]
    L.insert(1, f"(the {len(DEV)} tables the head reader was developed on are left out)")
    if "head" in runs:
        n = max(1, n_tables)
        L += ["", "head reader, per table scored:",
              f"  model calls {head_stats['calls'] / n:.1f}, seconds {tally['head']['secs'] / n:.1f}",
              f"  Q-SPEC: names it decided that match the GT trait "
              f"{pct(head_stats['qspec_ok'], head_stats['qspec_n'])}",
              f"  body rows asked (QB): {head_stats['body rows asked']} (no GT for them: look in the report)",
              "", "head reader, misses by bucket:"]
        L += [f"  {b:42s}{n_}" for b, n_ in sorted(buckets.items(), key=lambda kv: -kv[1]) if n_]
        if look:
            L += ["", "rows between the head and the first record (head end: no GT, check by eye):"]
            L += [f"  {x}" for x in look]
    return "\n".join(L), "\n".join(detail)


def main(argv):
    OUT.mkdir(parents=True, exist_ok=True)
    budget = float(argv[argv.index("--minutes") + 1]) * 60 if "--minutes" in argv else None
    skip = {argv[i + 1] for i, a in enumerate(argv) if a in ("--variant", "--minutes")}
    papers = [a for a in argv if not a.startswith("--") and a not in skip]
    if "--summary" in argv:
        summary, detail = score(papers or None)
        (OUT / "summary.txt").write_text(summary, encoding="utf-8")
        (OUT / "detail.txt").write_text(detail, encoding="utf-8")
        print(summary)
        return
    variant = argv[argv.index("--variant") + 1] if "--variant" in argv else "code"
    run_collect(variant, papers or default_papers(), "--resume" in argv, budget)


if __name__ == "__main__":
    main(sys.argv[1:])
