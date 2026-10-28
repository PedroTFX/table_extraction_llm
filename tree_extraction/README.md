# tree_extraction

A second, experimental way of understanding tables, built beside the main
pipeline (`source/`). It reads the pipeline (table parsing, GT loading, the gemma
mapper as a baseline) but never changes it.

The idea: split table understanding into small decisions — the table's layout
first, then what each column holds — each made by code where the answer is
certain and by a **decision model** (`tev1:4b`, `nimble` via Ollama's
`/v1/systemone`, multiple choice with probabilities) where it is not.

## Layout

`src/` has one folder per version. Each holds the version's entry file and every module it
imports, so a folder is everything that version needs to run. The same module is copied into
several folders: a fix to a shared module (e.g. `column_tree.py`) has to be made in each folder
that should get it.

```
src/
  full_run/      the full run (full_run.py): head reader, column tags, meaning, legend
                 inventory, decoder, assembly — 22 files
  v3/            full_run_v3.py: + decoder v3 cells, value endings, species step — 26
  v4/            full_run_v4.py: + which column holds the organisms — 28
  v5/            full_run_v5.py: + trait-column questions (NOT adopted) — 28
  v6/            full_run_v6.py: v4 + long / wide / no rows per table — 28
  v7/            full_run_v7.py: v6 + table kind, Q-ALSO, doubtful columns; grit_run.py — 30
  v8/            full_run_v8.py: v7 + section labels (section_tree.py); grit_run.py — 31
  v9/            full_run_v9.py: v8 + trait names from the paper's legends (legend_names.py) — 32
  v10/           full_run_v10.py: v9 + flag columns that are categories of one trait (category_tree.py)
  v11/           full_run_v11.py: v9 + names still printed as codes (name_parts.py) + species
                 duels (species_duel.py); both ask two options at a time (duels.py) — 35
  experiments/   benches, audits, comparisons and one-off fixes no version runs, with
                 copies of what they import — 49
```

Each `full_run_vN.py` is standalone (no other `full_run_v*` file is imported); the shared step
modules read the current plan through `full_run.plan`, which each version points at its own.
Every folder has its own `_paths.py`, which finds `tree_extraction/` by name.

Main modules (in the folders that use them):

```
  header_tree.py        LAYOUT from format only: cells -> shape symbols
                        (N, N±, Y, L, C, U, X, STAT, UNIT, CAP, spans), then
                        blocks, header rows, groups, sections; words put back last
  head_tree.py          the head reader (frozen); head_more.py runs it on every paper
  column_tree.py        COLUMN TAGS: decision tree (cell facts -> cell shape ->
                        organism name / property / record context / numbers / other)
  decoder*.py           legend codes -> terms (v1, v2 frozen, v3 endings / footnotes)
  species_tree.py       species of tables without a species column           (v3+)
  organism_tree.py      which column holds the organisms                     (v4+)
  trait_tree.py         trait-column questions                               (v5)
  structure_tree.py     long / wide / no rows                                (v6+)
  kind_tree.py          table kind, Q-ALSO, Q-COL / Q-ROLE                   (v7)
  column_tree_v3.py     frozen copy of column_tree as scored on the held-out set (experiments)
  column_tree_bench.py  scores column trees vs gemma and flat tev1/nimble questions
  column_role_bench.py  the flat one-question benchmark; the answer key derived
                        from the GT (derive_labels), shared by the other benches
  bench_report.py       short reports (summary.txt, report.html) for column benches
  gt_value_audit.py     GT rows whose values do not fit their tag (experiments, read-only)
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

A version, from its folder (Ollama must be running; one model at a time):

```
cd tree_extraction/src/v7
python full_run_v7.py run all          # every stage in order, then assemble
python full_run_v7.py v7:kind dev      # one stage; papers: dev | held | all | <paper ...>
python full_run_v7.py score all
python grit_run.py all                 # the whole chain on data/grit_testing
```

The benches, from `tree_extraction/src/experiments/`:

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
