# Table-structure questions (structure_tree.py), written 2026-10-19 before implementation

Same split (seed 20261018). Baseline: output/full_run_v4. Structure key (from the GT, no
model): structure_key.json / .txt — tables that give rows labelled GT long / GT wide / no GT
rows, by values (a long table: one column's values, with the row's species, are GT values of
>= 3 GT traits, and a names column whose cells point consistently to those traits).
Key facts: only 2 GT-long tables in all 109 papers — Kovacs2010 t0 (dev, v4 reads it right)
and Noriega2023 t8 (held, 31,890 records, v4 reads it wide). v4 reads 13 tables long that are
not (10 'no GT rows' statistics / summaries, 3 GT wide). LIMITATION: dev has one positive
(already right), so dev tests false-long removal and keeping Kovacs2010 t0; long recognition
is tested only on held (Noriega2023). Accepted by the user.

## Procedure (nimble decides; code gives cells and layout, applies answers)

Candidate tables (give rows): v4 reads them long, or a trait-tagged column repeats (<= 60
distinct cells, >= 2 rows per cell on average: structure, not content).
1. Q-ROW per candidate: headers, the text printed above, the first rows column by column.
   "What is each row of this table?"
   - `record`: one organism or specimen with one named trait and the value measured for it
   - `wide`: one organism, species or specimen with its traits in the columns
   - `summary`: a statistic about traits: quartiles, slopes, heritability, correlations,
     tests, model results
   - `other`: definitions of traits, methods, sites or notes
2. `record` -> Q-NAMES on the repeating trait-tagged columns (names of different traits /
   values of one trait / organisms); confirmed -> Q-VALUE yes/no per other column ->
   read long (type = the names column, values = the 'yes' columns) AND wide for the
   table's other trait columns. (Fixes v4's assembly: the type column is the confirmed
   one, not the first by position.)
3. `wide` on a table v4 reads long -> read it wide (its value columns become traits).
4. `summary` / `other` on a table v4 reads long -> no rows from it.
5. Anything below 0.8, or a table v4 reads wide answered other than `record` -> v4's tags.

## Measures

- Structure accuracy on the keyed candidate tables vs v4 (structure_eval).
- Rows: repeatable scorer (evaluate, use_llm=False) for decisions; production scorer
  (use_llm=True) reported alongside. Per-paper regressions.
- ACCEPT RULE on dev (before running): repeatable micro F1 not lower than v4, no paper's
  repeatable F1 lower by > 0.005, Kovacs2010 t0 still read long, structure accuracy on
  candidates >= v4's. At most 2 dev iterations; then freeze; held run once, no tuning.

## Iterations (dev only, at most 2)

1. As above. Structure right on keyed tables 30 -> 33/38 (Jones t1 wide; Kovacs2010 t4,
   Oliveira t2, Orr t2 no rows) but Kovacs2010 t0 (mean +- SD per caste, GT long) answered
   'summary' -> no rows: Kovacs2010 0.364 -> 0. Repeatable micro F1 0.396 -> 0.396, 1
   regressed -> accept rule NOT met.
2. Definitions: a trait's mean (+- SD) for a group (caste, sex, population) is a measured
   value -> `record`; `summary` = statistics relating traits or groups or describing a
   distribution (quartiles, slopes, heritability, correlations, tests, models). Last dev
   iteration; then freeze (the variant that meets the rule, else not adopted).
   Result (dev): structure right 30 -> 36/38 (Kovacs2010 t0 stays long); repeatable micro F1
   0.396 -> 0.396 (TP same, FP -26), 2 improved (Kovacs2010 +0.04, Kratschmer +0.006), 0
   regressed; production mean F1 0.511 -> 0.512. Accept rule MET.
   FROZEN (2026-10-19): iteration 2. Held run once, no tuning.
   Held (run once): structure right 26 -> 31/35; Noriega2023 t8 read long (0.997); repeatable
   micro F1 0.431 -> 0.747 (Noriega2023 0.004 -> 0.793), production mean F1 0.535 -> 0.549;
   1 improved, 1 regressed (Beyer2021 -0.017). See RESULTS_structure.md.
