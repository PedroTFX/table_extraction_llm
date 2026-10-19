# Species-column questions (organism_tree.py), frozen 2026-10-18 before implementation

## Evaluation

- Split: `split.json`, seed 20261018, paper-level, 108 groups (the two Cortés-Gómez folders are
  one group): dev 54 papers, held 55. Iterate on dev only; run held once at the end.
- Leakage: the 12 diagnosed papers (7 dev, 5 held) informed this design, so held is a
  held-aside evaluation, not an untouched test. A real test needs newly annotated papers.
- Baseline (before any change): `baseline/` — per-paper scores (`summary.csv`), assembled
  rows, the tagged species columns per table (`species_columns.json`) and the species-column
  accuracy (`species_columns_eval.txt`): expected-species tables right dev 97/122 (80%),
  held 78/98 (80%).
- Reported separately: (1) species-column accuracy per table (`species_col_eval.py`),
  (2) row-level P/R/F1 (evaluate_all), (3) papers whose F1 drops — regressions.
- Challenge set (not targeted in this cycle, still reported): Gomez2022, Quicke2023,
  Borges2024, Pessoa2017, Gibb2005 t4, Cao2024 t5, Dejean2019 t3 (`split.json`).

## Procedure (the same for every table; nimble decides, code supplies printed cells)

For each table with trait columns, the candidate columns are those the column tagger
called verbatimIdentification.

1. Q-KIND, per candidate column: header + up to 8 distinct cells. "What do the cells of
   the column name?"
   - `species`: organisms named to species (genus and species, perhaps abbreviated or with
     the author; numbered morphospecies such as 'Adesha sp. 1')
   - `part`: only the species part of a name; the genus is printed elsewhere
   - `higher`: groups above species (genera, tribes, subfamilies, families, orders)
   - `other`: not organisms (references, traits, seasons, dates, places, descriptions)
2. One `species` column -> it names the rows. Several -> Q-PICK: which one names the
   organism each row is about, or none.
3. No `species` but a `part` column -> Q-GENUS: where is the genus printed? Options: each
   other non-trait column (3 sample cells), the section labels above the rows (when the
   table has them), or nowhere. Code joins genus + part (a section label applies to the
   rows below it until the next label: printed row numbers). Nowhere -> the part alone.
4. Otherwise (only `higher` or `other`, or Q-PICK said none) -> rejection is a valid
   outcome: the table has no species column and goes to the species step (species_tree:
   one paper at a time, gate one / several).

No paper-specific rules; no content-type facts in code (no Latin-name or capital-letter
tests): the kind of a column is nimble's answer.

## Iterations (dev only)

1. As above. Expected-species right 97 -> 100/122, wrong 7 -> 3, names not in GT 37 -> 12,
   no dev table worse. Errors: a species part with its author read as a full name (Teder
   'apollo (Linnaeus, 1758)' 0.98, McCravy 'sericeus (Förster)' 0.93); 7/160 answers < 0.8.
2. Q-KIND `species` / `part` reworded to name the difference (genus + species name vs the
   species name without its genus, perhaps with author and year). Generic wording, no
   paper's cells quoted.
   Result: right 100/122 (same), wrong 3 -> 2, Teder's column now 'part' (0.53), Renoz's
   dates now 'other'; 16/160 answers < 0.8 (was 7); no dev table worse.
3. (a) Q-KIND states the table's section labels when it prints them; (b) Q-GENUS shows the
   first rows column by column and offers every other column (trait-tagged ones too); (c)
   a Q-KIND answer below 0.8 gets a second look with up to 20 cells; still below 0.8 ->
   'unsure', not used as the species column (the table may go to the species step).
   Result: wrong 2 -> 0 (Teder joined with its Genus column = the GT form; McCravy part +
   section labels; Kovacs2010 'Gynes' no longer used), but Eckert2023 t4 and Laha2020 t6,
   right in the baseline, were lost: unsure twice (0.77-0.79) -> rejected. Too harsh.
   Measure fixed: a table also expects species when the names the pipeline builds (genus +
   part) are GT species (baseline numbers unchanged by the fix).
4. The second look is a yes / no question ('do these cells name organisms at species level?',
   20 cells); still unsure -> the column tagger's call stands (no code tie-break).
   Result: right 101/123, wrong 2, missed 20, no dev table worse than the baseline; the yes/no
   second look settled 15/16 unsure answers (0.85-0.996). Side effect: Teder's 'part' (first
   answer, unsure) became 'species' after 'yes', losing the genus join.
5. A second-look 'yes' keeps a first answer of 'part' (a species name without its genus is
   a species-level name: the two answers agree).
   Result: right 102/123 (83%; baseline 97), wrong 1 (Renoz2020 t1: a date column, yes 0.96),
   missed 20, no dev table worse than the baseline. Questions settled here (not reworded
   for one table). Next: species step, assembly, row-level score on dev; then held once.
   Row level (dev, 54 papers): mean F1 0.483 -> 0.491, scoped micro F1 0.338 -> 0.393;
   Teder +0.98, McCravy +0.38, Cerini +0.13 — but Espinosa2023 1.000 -> 0.000 and
   Guareschi2015 0.072 -> 0: their GT identifies to GENUS ('Zelusia', 'Gyrinus'); a
   'higher' column was rejected. Design error (step 4 too strict), and the measure missed it:
   it only matched two-word names. Measure fixed (genus-level names count; baseline
   re-run: dev 99/123, held 80/100). Iteration 5 under it: dev 104/124, 2 regressions.
6. Q-UNITS for tables whose candidates are only 'higher': one organism per row identified
   only to that rank (the study's unit) -> that column (several: Q-PICK at the finest
   rank), or a group of several species per row -> no species column.
   Result (dev): species columns right 106/124 (85%; baseline 99/123), 0 tables worse;
   row level mean F1 0.483 -> 0.511, scoped micro F1 0.338 -> 0.395; 4 papers improved
   (Teder +0.98, McCravy +0.38, Cerini +0.13, Cappellari +0.015), 0 regressed. Espinosa and
   Guareschi back (units 0.998 / 0.993). Known wrong call: Braschler t6/t7 'Studied group'
   ('Snails') -> units 0.92.
   QUESTIONS FROZEN after iteration 6 (2026-10-18). Held half run once, unchanged.
   Held (run once, unchanged): species columns right 80 -> 91/100, 0 tables worse; mean F1
   0.470 -> 0.535, 7 improved, 0 regressed. See RESULTS.md.
