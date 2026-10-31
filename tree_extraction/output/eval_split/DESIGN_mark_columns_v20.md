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
