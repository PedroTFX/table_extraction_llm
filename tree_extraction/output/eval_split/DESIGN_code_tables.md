# Code tables: a key table that defines another table's coded columns (design, 2026-10-30)

## The problem

Some papers print their trait data as a table of coded columns and the meaning of the codes in a
separate key table. The GT reads the data table through the key: one row per category an organism
has, the trait named as the key names it, the value the key's category.

| Paper (dev) | Key table | Data table | Cells | GT rows |
|---|---|---|---|---|
| Guareschi2015 | t2: Code / Biological traits / No / Categories (A = Maximal size; 1 = ≤0.25 cm, 2 = >0.25–0.5 cm …) | t3: header row 1 trait letters (A … K), row 2 category numbers (1 … 4) | fuzzy affinity 0–3 | 1,738 |
| Viza2023 | S3: Stage / TRAITS / CODE / CATEGORIES / CODE (Body length = B; < 40 mm = BS, 40 - 60 mm = BM, > 60 mm = BL) | S4: group headers (Body size …) over code columns (BS, BM, BL …) | 0 / 0.5 / 1 | 1,695 |

Guareschi2015's Gyrinus has A = 0, 1, 3, 0 and the GT holds Maximal size = '>0.25-0.5' and
'>0.5-1'. Viza2023's Calopteryx exul has BS 0, BM 1, BL 0 and the GT holds Body Length = '40 - 60';
its trait names are the key's TRAITS column ('Body Length'), not the data table's group header
('Body size').

What the run does today (v15): the key table is read as a data table (wrong rows), and the coded
columns keep their codes as trait names ('A 1', 'Body size BS') with the scores as values:
Guareschi2015 F1 0.072 (3,081 rows), Viza2023 F1 0 (3,192 rows).

What exists: the legend inventory reads small tables (≤ 4 columns) as legend units; the decoder
uses its entries to turn a coded cell into a term ('SO' -> 'solitary'); v9 / v11 use them to name a
column whose whole name is a code ('HW' -> 'head width'). None of them reads a column code as
trait + category, and none stops a key table from producing rows. v10 (category_tree.py, not
adopted) grouped 0/1 columns into one trait from header groups only, with no key.

## The step (v16) — the model decides; code gives geometry, picks questions, applies answers

0. **Count first (code, no model)**: on the tuning papers (dev + held_a), the tables whose cells
   hold at least 3 of the codes another table prints as column headers or header parts. If only
   Guareschi2015 and Viza2023 show up, the family is two papers and the step must change nothing
   anywhere else.
1. **Key candidates (code)**: a table whose cells contain ≥ 3 header codes of another table of the
   same paper (supplements included), with the data table it would key.
2. **Q-KEY (model)**: "Does this table define the codes used in the columns of that table?" Sure
   yes -> the key table produces no rows; anything else -> nothing changes.
3. **Key columns (model)**: per key column, which role it holds — trait name, trait code, category,
   category code, other (stage, group). Code reads the key's rows into entries with those roles,
   carrying a trait name down over the rows it spans (merged cells).
4. **Coded columns (code)**: data-table columns whose header, or header parts joined, is an entry's
   category code ('BM') or trait code + category number ('A' + '1').
5. **Q-HAS (model)**, once per data table and distinct cell value: "In this table, does the value
   '3' (or '0', '0.5') mean the organism has the category?" Sure answers only.
6. **Rows (code)**: one per organism and category it has: measurementType = the key's trait name,
   measurementValue = the key's category as printed. Columns not matched stay as today.

Open: the GT drops the unit from the category ('>0.25-0.5' for '>0.25–0.5 cm', '40 - 60' for
'40 - 60 mm') — the value stays as printed (GT mirrors the paper), and the scorer decides whether
a unit word and a dash variant count as the same value.

## Measure and accept

Production and repeatable F1 against v15 on dev + held_a (tuning), held_b run once with the
questions frozen, grit-only papers as totals only (split_v15.json). Adopt when the tuning F1 rises,
no tuning paper falls, and held_b does not fall.
