# Category columns (v10 = v9 + categories) — design, 2026-10-28, before any run

## The problem

Many tables print each category of a trait as its own column, the cell saying whether the
organism has it (0/1, yes/no, x, +/-, or fuzzy 0-1 fractions): Wallon2024 FoodPI / FoodAni /
FoodFg, Viza2023 'Body size BS / BM / BL', Bucher2024 Predator / Herbivore. We write one row per
column ('FoodAni' = 1, 'FoodPI' = 0); many GTs write one row per category the organism has
('Type of Food' = 'Animals'). 22 grit papers have >= 3 flag-only trait columns. Some GTs keep
the columns as printed (Khayati2024 'Food Type: Insects' = 0/1, Pessoa2017): the step must not
convert columns by default.

## Code: facts only (no grouping by code)

For each wide trait column whose cells are all flags (>= 3 filled cells; 0/1, yes/no, y/n, x,
+/-, fractions) code gathers its structural facts:
- header group: the heading cell the head reader found spanning the column ('Body size' over
  BS / BM / BL) — kept per column by v10's head_to_table (t.col_groups);
- legend heading: the inventory variable(s) the column's code is listed under ('Type of food
  ingested' for FoodAni);
- spelled name: the meaning / v9 names of the column ('Fungi (FoodFg)').

No name-prefix or string rule: those fit the papers looked at, not tables in general.

## nimble decides (per column)

Q-CAT, one question per flag column that has at least one structural heading:

    Which trait is the column '<name>' a category of?
      c_i   a category of the trait '<heading>' (the table's header group / the paper's legend)
      own   none: it is a yes/no trait of its own

Sure (p >= 0.8) answers only. Columns of one table answered with the same heading form a
category group; a group of one column stays a yes/no trait (one category is not a choice).
A column with no structural heading is not asked and stays as printed — a known gap
(Wallon's diurnal / nocturnal / twilight if the paper prints no heading over them), not a guess.

Q-PRESENT, once per group whose cells include fractions (fuzzy coding):

    In these columns, which cell values mean the organism has the category?
      any   any value above 0
      top   only the full value (1)

Unsure -> the group is left as printed. Pure 0/1 or yes/no groups need no question
(1, yes, y, x, + = has it; 0, no, n, -, empty = has not).

## Code applies

A record in a category group gets one row per category it has: type = the heading, value =
the column's spelled name; columns it does not have give no row. Everything else unchanged.

## Checking it (dev / held named before any run)

- Dev (looked at while designing): Wallon2024, Viza2023, Bucher2024, MiddletonWelling2018,
  Khayati2024, Pessoa2017, Martins2017, Kratschmer2019.
- Held: every other grit paper with flag columns (not opened for this step).
- Per paper F1 v9 -> v10 on grit, dev and held reported apart. Accept: held mean F1 does not
  drop and no held paper drops > 0.02; if only dev papers improve, the step is dropped as
  overfit. Khayati2024 / Pessoa2017 (GT keeps the columns) must not drop.
- Without a model (on the remote): v10 with no answers = v9's CSVs; v3..v9 regenerated with the
  new optional hook = their saved CSVs.
