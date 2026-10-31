# Yes / no columns (v18 = v17 + yes_no.py, 2026-10-31)

## The problem (the user: "has feature X or doesn't have feature X, usually signalled as 1 / 0")

On the tuning papers (dev + held_a) the GT holds 3,159 Yes / No (or Absent) values in 12 papers; in
2,579 of them we have the right species and trait but another value:

| What we wrote | Rows | Papers |
|---|---|---|
| the legend's wording of 0 / 1 ('no hibernation in egg stage recorded') | ~1,340 | Guariento2020 |
| the printed words of the two states ('not' / 'obligate') | 523 | Fiedler2021 |
| the numbers ('0', '1', '0.0', '1.0') | ~620 | Vidal2023, Gathof2022, Viza2023 … |
| a decoded legend term ('fire occurred 0 to 4 years ago') | 91 | Vidal2023 |

The common shape: a trait column with exactly two different printed values, one meaning the organism
has the property and the other that it does not.

## The step — code picks the candidates, nimble decides

- **Candidates (code)**: a trait column of a wide table with exactly two different printed values
  (case and spaces ignored) and at least 3 rows.
- **Q-FLAG (nimble)**: the table, the column, its two values with their row counts and the legend's
  wording for each: is the column a yes / no answer about each organism, or a number, score, rank or
  one of two named categories? Only a sure 'yes / no' goes on.
- **Q-YES (nimble)**: which of the two values means the organism has it? Asked in both orders; the
  two answers must agree.
- **Apply**: the column's cells become 'Yes' / 'No' before decoding, so no legend wording replaces them.

Left as they are: long tables (a value column mixes traits), and an X with blank cells (whether the GT
writes 'No' for the blanks is not known yet).

## Measure and accept

Production and repeatable F1 against v17 on dev + held_a; held_b once with the questions frozen;
grit-only papers as totals only (split_v15.json). Adopt when the tuning F1 rises, no tuning paper falls
by more than 0.01, and held_b does not fall.

## Tuning run (2026-10-31, code 230292d9)

Two-valued columns asked on 42 tuning papers; rows changed in 13, score changed in 5, none fell.
Production F1: Fiedler2021 0.667 -> **1.000**, Guariento2020 0.674 -> **0.795**, Vidal2023 0.260 ->
0.333, Gathof2022 0.818 -> 0.870, Wallon2024 0.340 -> 0.377. Tuning mean 0.644 -> **0.651**.
Repeatable scorer: micro F1 0.719 -> 0.731, true positives 101,245 -> 103,246, false positives
28,677 -> 27,616. Papers with many columns called yes / no (Kratschmer2019 26, Chichorro2022 15,
Cao2024 10) did not change their score.

## Test: held_b run once (2026-10-31, dca7871c; totals only)

37 two-valued columns asked, 4 called yes / no; mean F1 0.494 -> 0.494, none up, none down
(repeatable scorer unchanged too). The accept rule is met; the 4 columns are not among held_b's
scored GT rows, so held_b does not test the step.

## v19: unsure columns beside sure siblings (the user: "everything on Fiedler is yes or no")

Fiedler2021: the model leaned 'yes / no' on all 26 two-valued columns but was sure on 12; the 14
others (Nearctic 0.56, Neuguinea 0.60 ...) sit beside Palaearctic (0.91) with the same 0 / 1. On the
tuning papers 29 such columns in 7 papers. v19 asks each of them once more, naming the sure columns of
its table with the same two values and the value that means 'has it' there; a sure 'same' writes
it Yes / No. (Fiedler2021's region columns are not in its GT, which is at F1 1.0 already.)
