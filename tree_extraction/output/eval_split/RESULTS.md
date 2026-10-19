# Species-column questions — results (2026-10-18)

Questions frozen after iteration 6 on the dev half (see DESIGN.md); the held half was run
once, unchanged. Held is a held-aside evaluation with some leakage (5 of its papers were
among the 12 diagnosed before the design), not an untouched test.

## 1. Species-column accuracy per table (species_col_eval.py)

Tables whose GT species are printed in them (or built by the pipeline from genus + part):

| half | baseline (v3) | v4 | wrong | missed | tables worse than baseline |
|---|---|---|---|---|---|
| dev  | 99/123 (80%) | 106/124 (85%) | 7 -> 1 | 17 -> 17 | 0 |
| held | 80/100 (80%) | 91/100 (91%)  | 17 -> 3 | 3 -> 6 | 0 |

Tables with no GT species given junk names ('names not in GT'): dev 35 -> 13, held 27 -> 16.

## 2. Row level (evaluate_all, scoped)

| half | mean F1 v3 -> v4 | micro P/R/F1 v3 | micro P/R/F1 v4 | improved | regressed |
|---|---|---|---|---|---|
| dev (54)  | 0.483 -> 0.511 | 0.341/0.335/0.338 | 0.398/0.391/0.395 | 4 | 0 |
| held (55) | 0.470 -> 0.535 | 0.651/0.233/0.343 | 0.768/0.298/0.429 | 7 | 0 |
| all (109) | 0.476 -> 0.523 | | | 11 | 0 |

Held gains: Zhao2024 0 -> 1.000, Normandin2017 0.004 -> 0.923, Fiedler2021 0.003 -> 0.667,
Habustova2017 0.255 -> 0.730, Cao2024 0 -> 0.269, Ji2024 0.761 -> 0.960, MacDonald2021
0.089 -> 0.142. Dev gains: Teder2020 0 -> 0.984, McCravy2019 0 -> 0.379, Cerini2023 0 ->
0.129, Cappellari2022 0.985 -> 1.000.

## 3. Challenge set (not targeted; F1 v3 -> v4)

Gomez2022 0 -> 0, Quicke2023 0 -> 0, Borges2024 0 -> 0, Pessoa2017 0.740 -> 0.740,
Gibb2005 1.000 -> 1.000 (t4 species-as-headers still unread), Cao2024 0 -> 0.269 (t7 fixed by
the questions; t5 species-as-headers still unread), Dejean2019 1.000 -> 1.000 (t3 'Label').

## Known wrong calls

Renoz2020 t1 (a date column: 'yes' 0.96), Braschler2021 t6/t7 ('Studied group' = Snails:
'units' 0.92), Kratschmer2019 'honey bees' (species step, chunked methods summary).
