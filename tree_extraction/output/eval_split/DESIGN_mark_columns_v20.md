# Marked columns read as categories (v20 = v18 + mark_columns.py, 2026-10-31)

## The problem

Some tables mark each organism with one sign under the categories it belongs to and leave the rest
blank. Today every such column is its own trait with the value 'x' (Odanaka2019: 'Un-grazed
landscapes = x'); the GT writes one trait for the group and the column's name as the value
(Management intensity = Un-grazed landscapes; two marks joined with '; ').

On the tuning papers 108 columns in 8 papers hold one mark and blanks (output/eval_split/
PRESENT_OR_BLANK_COLUMNS.html). No GT writes 'No' for a blank. Most groups are not categories of a
property: sampling sites (Heiva2013), plots by elevation (Fontanilla2019), a table describing the
traits (Espinosa2023). The trait name is rarely printed over the group (Odanaka2019 has it only in the
caption), and the user expects the volunteers' names to differ from any name we give: the scorer's
name matching by meaning decides whether ours counts.

## The step — code finds groups, gemma names, nimble decides

- **Groups (code)**: in a wide table, two or more trait columns with the same single mark and blank
  cells elsewhere, at least 3 rows.
- **Name (gemma)**: a short name for the property the columns could be categories of, from the
  caption, the text below the table and the column names. Gemma only proposes.
- **Q-CAT (nimble)**: categories of one property of each organism, or separate things (places, sites,
  plots, samples, separate traits)? Only a sure 'categories' goes on.
- **Q-NAME (nimble)**: does gemma's name fit that property? Only a sure yes is used.
- **Apply (assembly)**: each marked cell's row becomes trait = the name, value = the column's name;
  blanks give no row, as before. One row per marked column (the GT joins two marks with '; ').

## Measure and accept

Production and repeatable F1 against v18 on dev + held_a; the scorer's report shows whether it
matched our name to a GT trait. held_b once if adopted; grit-only papers as totals only.

## Tuning run (2026-10-31, code 4bb89324) and a what-if

10 groups on 6 tuning papers; nimble read none as categories, so v20 changed no row (tuning mean F1
0.651, as v18). Right for sampling sites (Heiva2013), plots by elevation (Fontanilla2019) and tables
describing traits (Espinosa2023); wrong for Odanaka2019 t7 (management intensity), called 'separate'
at 0.99, gemma's name 'Habitat/Condition'.
What-if (every group applied with gemma's name, nimble ignored; output/full_run_v20_whatif on the
remote, 6 papers scored): the scorer matched 'Habitat/Condition' to the GT's 'Management intensity'
(9 rows), Odanaka2019 0.786 -> 0.912; the other 5 papers unchanged (their extra rows are outside what
the GT scores). Page: output/eval_split/MARK_COLUMNS_v20.html. Not adopted (no change).

## Test: held_b run once (2026-10-31; totals only)

0 marked-column groups in the 27 held_b papers; mean F1 0.494 -> 0.494, none up or down. held_b
holds no case of this layout, so it cannot test the step.

## Side finding: Fontanilla2019's '(no name, column N)' rows

Its tables 5 and 6 (species incidence per study plot, plots grouped by elevation) span several pages;
MinerU split them into page pieces, and only the first piece (t17, t19) has the header rows. v12 joins
a headless piece to the table before it only when both have the same number of columns, but MinerU
drops empty cells at the end of rows, so the pieces come out 21, 20, 19 and 17 columns wide. None is
joined, each becomes its own headless table, and 828 rows are named '(no name, column N)'. The GT does
not score these tables (the paper is at F1 0.996), so no F1 is lost; the rows are wrong output.
