# Table-structure questions — results (2026-10-19)

Frozen: iteration 2 (DESIGN_structure.md). Held half run once, unchanged. Baseline v4.
Held is a held-aside evaluation with leakage (Noriega2023 was diagnosed before the design)
and has a single long-format positive, so the long-recognition result rests on one table.

## Structure accuracy (keyed tables: GT long, GT wide, and no-GT-rows tables v4 reads long)

| half | v4 | v6 |
|---|---|---|
| dev (38 tables)  | 30 | 36 |
| held (35 tables) | 26 | 31 |

Held: Noriega2023 t8 read long (record 0.997; 'Trait' confirmed as trait names 0.997,
'Dung relocation strategy' rightly 'values' 0.951; value column 'Measurement' = yes, Site
Code / Specimen number / dung strategy = no). Leong2023 t1, Tran2022 t0/t1 -> no rows;
Beyer2021 t22 -> wide. Still wrong: CortesGomez t6 (both folders, GT wide, answered
record but no names column confirmed -> v4's long), Orlofsk2014 t3 (summary below 0.8),
Tran2022 t3 (GT wide, answered summary -> no rows; it gave no GT rows under v4 either).

## Rows

| half | repeatable micro F1 (use_llm=False) | production mean F1 | improved / regressed |
|---|---|---|---|
| dev (54)  | 0.396 -> 0.396 (FP -26) | 0.511 -> 0.512 | 2 / 0 |
| held (55) | 0.431 -> 0.747 | 0.535 -> 0.549 | 1 / 1 |

Held: Noriega2023 0.004 -> 0.793 (TP 64 -> 26,491; FP 223 -> 5,256). Beyer2021 0.753 ->
0.736 (t22, a no-GT-rows table, now read wide: +9 wrong rows). The held micro F1 jump is
almost all Noriega2023 (one table of 31,890 records).

## Reading

The structure question removes false long readings on both halves without losing a GT-long
table, and recognised the one held long table, fixing v4's two assembly faults on it (type
column by position, other trait columns lost). One minor regression (Beyer2021 -0.017).
