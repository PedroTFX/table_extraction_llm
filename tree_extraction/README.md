# tree_extraction

A second, experimental way of understanding tables, built beside the main
pipeline (`source/`). It reads the pipeline (table parsing, GT loading, the gemma
mapper as a baseline) but never changes it.

The idea: split table understanding into small decisions — the table's layout
first, then what each column holds — each made by code where the answer is
certain and by a **decision model** (`tev1:4b`, `nimble` via Ollama's
`/v1/systemone`, multiple choice with probabilities) where it is not.

## Layout

```
src/
  _paths.py             paths; puts source/ on the import path
  header_tree.py        LAYOUT from format only: cells -> shape symbols
                        (N, N±, Y, L, C, U, X, STAT, UNIT, CAP, spans), then
                        blocks, header rows, groups, sections; words put back last
  header_tree_bench.py  scores header_tree vs the pipeline's gemma header finder
  column_tree.py        COLUMN TAGS: decision tree (cell facts -> cell shape ->
                        organism name / property / record context / numbers / other)
  column_tree_v3.py     frozen copy of column_tree as scored on the held-out set
  column_tree_bench.py  scores column trees vs gemma and flat tev1/nimble questions
  column_role_bench.py  the flat one-question benchmark; the answer key derived
                        from the GT (derive_labels), shared by the other benches
  bench_report.py       short reports (summary.txt, report.html) for column benches
  gt_value_audit.py     GT rows whose values do not fit their tag (read-only)
output/
  column_role_bench/    flat benchmark results + cached parsed tables (tables_*.pkl)
  column_tree_bench/    column-tree runs (new20 = held-out, all_v5q4 = all papers,
                        combined/ = side-by-side report, GT_ERRORS.txt)
  header_tree_bench/    header-tree runs
  GT_VALUE_AUDIT.txt, GT_REVIEW_CANDIDATES.txt
```

## Scoring

Every bench scores against the ground-truth spreadsheets
(`data/un_processed_papers/<paper>/<paper>.xlsx`) through an answer key derived
from them by values — not against the pipeline's saved mappings, which were made
after gemma's own header choices.

## Running

From `tree_extraction/src/` (Ollama must be running):

```
python header_tree_bench.py --resume --minutes 25
python column_tree_bench.py --new 20 --baselines gemma,tev1 --out new20 --resume --minutes 18
python bench_report.py --out combined --set "Held-out=new20,v5_q4,v5_tev1" --models gemma,tev1,tree5_q4
python gt_value_audit.py
```

Background runs are cut at 30 minutes, so long benches take `--minutes` and
`--resume` and are run several times.

## Models

- `tev1:4b` — prompts up to ~2,050 tokens; fast.
- `nimble:9b-q4-gpu` — nimble Q4_K_M with every layer on the GPU (`num_gpu 99`);
  needs the GPU free of other models (stop MinerU's servers while benchmarking).
