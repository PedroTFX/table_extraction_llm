# 7. Tables too big to read

## The problem

The head reader shows nimble the top of a table to find the header rows and name the columns. A table with very many columns does not fit even at the smallest view, so it is skipped, and nothing after it ever sees the table.

- Chichorro2022: the dataset sheet (881 rows, 113 grid columns) holds all 620 GT rows. Score 0.
- Supplement datasets like this are often the whole of a paper's trait data, so on new papers this costs entire papers.

## The plan

1. **Only for a table that fails as too big**; every table read today stays exactly as it is.
2. **Read the head in column windows**: the first columns (the row identity) stay in every window, the rest are shown in slices that fit. The header-row decision is taken on the first window and reused; column names are read per window and joined.
3. **Check by layout**: every window must agree on where the data starts. If they disagree, the table stays skipped and is reported.
4. The later steps already work per column, so they need no change. Cost is checked on this table before the full run.

## Risks

- A group header that spans a window border. Windows overlap by the width of the widest spanning header cell.
- Long run time on one table: a cap on columns asked, reported when hit.

## Measure

- Chichorro2022 goes above 0; tables skipped as too big: 1 on the 109, counted on grit and Jakub.
- The head-reader results of all other tables are byte-identical.

## Size

Small to medium, all in the head reader's fallback path.
