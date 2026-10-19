"""Freeze a paper-level evaluation split and a snapshot of the current results, before
the species-column questions change anything.

    python eval_split.py freeze

Writes output/eval_split/:
  split.json            seed, groups, dev / held assignment (a paper's tables stay together;
                        folders of the same paper — CortesGomez2023 / Cortés-Goméz2023 — are
                        one group)
  baseline/summary.csv  per-paper P/R/F1 of output/full_run_v3 (the current result)
  baseline/<paper>.csv  its assembled rows
  baseline/species_columns.json   per table: the columns tagged verbatimIdentification,
                        the organism column used, and the first species it gives
Leakage: the 12 papers whose species columns were diagnosed (in either half) informed the
design of the questions, so the held half is a held-aside check, not an untouched test.
"""
import json
import random
import shutil
import sys
import unicodedata

import full_run as fr

HERE = fr.OUT.parent
RUN = HERE / "full_run_v3"
OUT = HERE / "eval_split"
SEED = 20261018
DIAGNOSED = ["Cao2024", "Chichorro2022", "Teder2020", "Quicke2023", "Cerini2023", "Harmon2013",
             "McCravy2019", "Gomez2022", "Borges2024", "Luo2023", "Tran2022", "Oliveira2022"]
CHALLENGE = {
    "Gomez2022": "species inside a combined label cell: 'Yellow species (major workers) P. beliosa (n = 1)'",
    "Quicke2023": "tribes in 'Clade', the species column tagged measurementType; GT mixes genera and species",
    "Borges2024": "'Species' column lists the prey; the GT organism is the predator (Scymnus nubilus)",
    "Pessoa2017": "species only in the sheet heading printed above each table ('## A.carbonarius')",
    "Gibb2005": "t4: species as column headers (a turned table)",
    "Cao2024": "t5: species as column headers",
    "Dejean2019": "t3: species in a 'Label' column tagged measurementType",
}


def group_key(paper):
    s = unicodedata.normalize("NFKD", paper).encode("ascii", "ignore").decode()
    return "".join(ch for ch in s.lower() if ch.isalnum())


def freeze():
    if (OUT / "split.json").exists():
        sys.exit("split already frozen: output/eval_split/split.json")
    papers = fr.gt_papers()
    groups = {}
    for p in papers:
        groups.setdefault(group_key(p), []).append(p)
    keys = sorted(groups)
    random.Random(SEED).shuffle(keys)
    half = len(keys) // 2
    assign = {}
    for i, k in enumerate(keys):
        for p in groups[k]:
            assign[p] = "dev" if i < half else "held"
    (OUT / "baseline").mkdir(parents=True, exist_ok=True)
    split = {"seed": SEED, "made": "2026-10-18", "groups": {k: groups[k] for k in sorted(groups)},
             "assign": dict(sorted(assign.items())),
             "counts": {s: sum(v == s for v in assign.values()) for s in ("dev", "held")},
             "diagnosed": {p: assign.get(p) for p in DIAGNOSED},
             "challenge": CHALLENGE,
             "note": ("Paper-level split; folders of one paper share a group. The diagnosed papers "
                      "informed the question design, so 'held' is a held-aside evaluation with some "
                      "leakage, not an untouched test; that needs newly annotated papers.")}
    (OUT / "split.json").write_text(json.dumps(split, indent=1, ensure_ascii=False), encoding="utf-8")
    shutil.copy(RUN / "summary.csv", OUT / "baseline" / "summary.csv")
    for p in papers:
        f = RUN / p / f"{p}.csv"
        if f.exists():
            shutil.copy(f, OUT / "baseline" / f"{p}.csv")
    head = fr.head_runs()
    cols = {}
    for p in papers:
        if p not in head:
            continue
        for t, fields, org, _x in fr.plan(p, head):
            ids = [c.name for c in t.columns if fields.get(c.name) == "verbatimIdentification"]
            if not ids:
                continue
            first = next((fr.species_of(t, fields, org, r) for r in t.records
                          if fr.species_of(t, fields, org, r)), "")
            cols.setdefault(p, {})[str(t.table_index)] = {"tagged": ids, "organism_column": org,
                                                          "first_species": first}
    (OUT / "baseline" / "species_columns.json").write_text(
        json.dumps(cols, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{len(papers)} papers in {len(groups)} groups (seed {SEED}): {split['counts']}")
    print("diagnosed papers:", split["diagnosed"])


if __name__ == "__main__":
    {"freeze": freeze}[sys.argv[1]]()
