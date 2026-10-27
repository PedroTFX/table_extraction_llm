"""Why a full-run paper produced few or no rows: per table, the record count, the column
tags, the organism column, trait columns and how many records carry a species.
Reads saved files only, no model.

    python full_run_diagnose.py Tonelli2021 Tsai2020 ...
"""
import collections
import sys

import full_run as fr


def main(papers):
    head = fr.head_runs()
    for paper in papers:
        if paper not in head:
            print(f"{paper}: no head-reader tables")
            continue
        print(f"== {paper}")
        pl = fr.plan(paper, head)
        if not pl:
            print("   no tables")
        for t, fields, org, _x in pl:
            tags = collections.Counter(fields.get(c.name, "untagged") for c in t.columns)
            n_trait = sum(fields.get(c.name) in fr.TRAITS for c in t.columns)
            with_sp = sum(bool(fr.species_of(t, fields, org, r)) for r in t.records)
            heads = [c.name for c in t.columns][:8]
            print(f"   t{t.table_index}: {len(t.records)} records, {len(t.columns)} cols, "
                  f"trait cols {n_trait}, organism {org!r}, records with species {with_sp}")
            print(f"       tags {dict(tags)}")
            print(f"       headers {heads}")


if __name__ == "__main__":
    main(sys.argv[1:])
