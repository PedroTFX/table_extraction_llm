# Continuation tables whose head has no names (v12 = v11 + the join) — design, 2026-10-28, before any run

## The problem

A table split across pages comes out of MinerU as several HTML tables. head_to_table joins a
table to the previous one only when the head reader found no head at all (head_end 0) and the
widths match. Taillefer2018 t8 and t11 (11 columns, as t7) start with a family label
('Tephritidae'), so the head reader read that row as a head (a section cell). The head has no
column names, so the table is not joined: t9 and t10 then join t8, and every column of these
continuation pages comes out as '(no name, column N)'. Taillefer's GT rows for Voltinism, Size,
Feeding … are missing for every species printed after t7 (about 1,000 grit rows; F1 0.012).

## The rule (geometry only, no question)

A table whose head rows give no column name at all is treated like a table with no head: when
its width matches the previous table it continues it. Its rows from the first record on are the
previous table's records, and its section cells (the family label) stay as section labels.
A head with at least one column name is never joined, so a table the head reader named does not
change.

Reach (counted before any run, from the head reader's saved answers):
- grit: Taillefer2018 t8 and t11 join t7;
- 109 set: Taillefer2018 t8 joins t7, and Chichorro2022 t6 joins t4 (a legend table, no traits).

## What the earlier answers cover, and what is asked again

Answers are kept per table: t7's tags, kind, structure, organism and sections now apply to the
joined rows. The one gap is decode: t7's legend answers cover only the codes printed in t7, and
the continuation pages print others ('PA', 'PR', 'S', 'L', 'B', …).

**v12:decode** asks only those: for each trait column of a joined table, the cells the saved
decode never saw, as v3 asks cells past the 25th (the column's first values shown). Every saved
answer is kept. Section labels new to a joined table get no section answer (record_info skips
labels without one): they change nothing.

## Not in this step

- Continuations whose width differs from the previous table (Torok2022 t8: '39. Tachysphex'
  merges the number into the species cell, 6 columns after 7; M.Wang2021 t11, likewise) need
  their columns lined up with the previous table's. That is a question for the model, not this
  rule.

## Measure

- **Dev:** Taillefer2018 (looked at). **Held:** Chichorro2022.
- Per-paper F1 v11 → v12 on both sets and both scorers. Every other paper must give v11's CSV
  byte for byte, since nothing else changes.
