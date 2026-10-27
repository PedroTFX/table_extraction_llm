"""
decode_prod_rerun.py — run TODAY's production decoder (source/fill_template.
decode_grouped_values, step 4b, gemma) on copies of the stored per-paper results,
and score it against the decoding key (decode_key.py). Reads the pipeline, changes
nothing in source/ or output/.

Inputs per paper, all from disk: output/<paper>/grouped_by_species.json (copied),
the stored *_mapping.json files, the parsed tables cached by column_role_bench
(tables_<paper>.pkl, same table ids), the paper text and its prose chunks
(run_pipeline.prose_chunks).

    python decode_prod_rerun.py Graf2021 Cappellari2022 ...
    python decode_prod_rerun.py --all <papers>   # scored on the --all key -> prod_rerun_all/
-> tree_extraction/output/decode_key/prod_rerun/{<paper>_grouped.json, <paper>.log, RERUN.txt}
"""

from __future__ import annotations

import collections
import contextlib
import io
import json
import pickle
import shutil
import sys
import time

import _paths
import column_role_bench as crb
import decode_key as dk
from evaluate import load_xlsx
from fill_template import decode_grouped_values
from run_pipeline import prose_chunks

OUT = dk.OUT / "prod_rerun"
KEY = dk.OUT / "key.json"


def rerun(paper):
    src = _paths.REPO / "output" / paper
    OUT.mkdir(parents=True, exist_ok=True)
    grouped = OUT / f"{paper}_grouped.json"
    shutil.copy(src / "grouped_by_species.json", grouped)
    stored = {f.name.replace("_mapping.json", ""): json.loads(f.read_text(encoding="utf-8"))
              for f in src.glob("*_mapping.json")}
    tables = pickle.loads((crb.OUT / f"tables_{paper}.pkl").read_bytes())
    # the cached tables were parsed in another run, so their numbers can differ from
    # the stored mappings': give each table the mapping that holds all its columns
    from table_to_data import table_id
    from tables import clean_text
    mappings = {}
    for tb in tables:
        hs = {clean_text(h) for h in tb.header_names}
        own = stored.get(table_id(tb))
        if own is not None and hs <= {clean_text(h) for h in own}:
            mappings[table_id(tb)] = own
            continue
        fits = [m for m in stored.values() if hs and hs <= {clean_text(h) for h in m}]
        if fits:
            mappings[table_id(tb)] = min(fits, key=len)
    full_md = _paths.PAPERS / paper / f"{paper}_full.md"
    text = full_md.read_text(encoding="utf-8", errors="replace")
    chunks = prose_chunks([str(full_md)])
    buf = io.StringIO()
    t0 = time.time()
    with contextlib.redirect_stdout(buf):
        decode_grouped_values(str(grouped), tables, text, chunks, mappings)
    (OUT / f"{paper}.log").write_text(buf.getvalue(), encoding="utf-8")
    return json.loads(grouped.read_text(encoding="utf-8")), round(time.time() - t0, 1), buf.getvalue()


def score(paper, grouped):
    key = json.loads(KEY.read_text(encoding="utf-8")).get(paper, {})
    gt = crb.GroundTruth(load_xlsx(crb.paper_inputs(_paths.PAPERS / paper)[1]))
    vals = collections.defaultdict(list)                 # species id -> [values]
    for sp, d in grouped.items():
        rid = gt.match_id(sp)
        if rid:
            vals[rid] += [str(m.get("measurementValue", "")) for m in d.get("measurements", [])]
    grids = {k: dk.ht.grid_from_html(h) for k, h in enumerate(dk.hb.html_tables(paper))}
    out = collections.Counter()
    for T, e in key.items():
        if e["kind"] != "coded":
            continue
        g = grids[e["table"]]
        for r in range(g.nrows):
            x = g.at(r, e["col"])
            ids = {gt.match_id(str(g.at(r, c).text or "")) for c in range(g.ncols) if g.at(r, c)} - {None}
            if len(ids) != 1 or not x:
                continue
            cell = " ".join(str(x.text or "").split())
            if cell not in e["coded"]:
                continue
            want, have = dk.n(e["coded"][cell]), [dk.n(v) for v in vals.get(ids.pop(), [])]
            out["right" if want in have else "left as printed" if dk.n(cell) in have
                else "no row" if not have else "other value"] += 1
    return out


def main(argv):
    global OUT, KEY
    if "--all" in argv:                                  # the --all key, its own output folder
        argv = [a for a in argv if a != "--all"]
        OUT, KEY = dk.OUT / "prod_rerun_all", dk.OUT / "all" / "key.json"
    lines = []
    for paper in argv:
        grouped, secs, log = rerun(paper)
        s = score(paper, grouped)
        tot = sum(s.values())
        lines.append(f"{paper:16s} right {s['right']}/{tot}  left as printed {s['left as printed']}  "
                     f"other value {s['other value']}  no row {s['no row']}   ({secs}s)")
        lines += ["    " + l for l in log.splitlines() if l.strip()]
        print(lines[-1 - len([l for l in log.splitlines() if l.strip()])], flush=True)
    (OUT / "RERUN.txt").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1:])
