# Duplicate rows (v16 = v15 + dup_rows.py, design 2026-10-30)

## The problem

Too many rows is the largest precision loss on the tuning papers. Part of it is the same data
read more than once:

- **Repeated records in one table.** Cerini2023's trait table (S1) prints each of its 123 species
  on up to 15 rows identical in every column (Pantala flavescens 15 times); the GT has one row
  per species. Ours: about 1,500 rows per trait, GT 120.
- **The same table twice.** Cerini2023 has S1 as both .csv and .xlsx (t4 and t5, 758 rows each);
  Fiedler2021's S2.xlsx repeats S1's table (the user kept it), and S2 is there as .pdf too.

The GT keeps repeated (species, trait, value) rows in 28 tuning papers (individuals with the same
value: Noriega2023, Raine2018, Orr2024, Tsai2020 …), so a rule may not drop equal rows in general:
only where a table's repeated species never differ (below).

## The step — code only (the user, 2026-10-30: "why not straight code?")

A model question was the first design; the rules below are strict enough to check on the tuning
papers, so v16 is code only.

- **Repeat**: in one table, every species that takes more than one row has all its rows identical
  (every printed column and the section labels above) -> one copy kept. On the tuning papers this
  fires on 4 tables only: Cerini2023 t4, t5 (123 species, 6-15 identical rows each), Graf2021 t8
  (its header row repeated on later pages), Normandin2017 t6 ('H.LIGATUS ~100 ...' twice); none of
  their GTs keeps the repeats. It never fires where the GT keeps equal rows (Noriega2023,
  Raine2018, Tsai2020): there a repeated species' rows differ somewhere.
- **Copy**: a later table with the same column names, the same number of rows, the same first
  column in the same order and >= 80% of its cells equal to an earlier table's gives no rows
  (Cerini2023 S1 as .csv and .xlsx differ only where Excel made dates of 'Flight season' cells).

Recorded per paper in full_run_v16/dup_rows/<paper>.json; applied in plan() after the listed tags.

## Measure and accept

Production and repeatable F1 against v15 on dev + held_a; held_b once with the questions frozen;
grit-only papers as totals only (split_v15.json). Adopt when the tuning F1 rises, no tuning paper
falls by more than noise (0.01), and held_b does not fall.

## Tuning run (2026-10-30, code ca87d4c1)

Fired on 7 tuning papers; species / trait / value rows changed in 3. Production F1:
Cerini2023 0.129 -> **0.894**, Fiedler2021 0.444 -> **0.667**, Zhao2024 1.0 -> 1.0 (its repeated
table is a figure's Source/Target network data that gives no scored rows). No paper fell.
Mean F1: dev 0.564 -> 0.578, held_a 0.757 -> 0.765, tuning 0.630 -> **0.642**. Repeatable scorer:
micro F1 0.660 -> 0.705, false positives 49,283 -> 30,413, true positives unchanged (99,062).
First attempt caught before scoring: Noriega2023 t8 matched itself as a copy (plan() gives it twice).

## Test: held_b run once (2026-10-30, fddaadac; totals only)

The rules fired in 0 of the 27 held_b papers: mean F1 0.462 -> 0.462, none up, none down. The
accept rule is met, but held_b says nothing about the step (it holds no duplicated data). The
repeatable scorer's micro F1 0.439 -> 0.447 there is v15's statistic column (v16 vs v14's CSVs).
