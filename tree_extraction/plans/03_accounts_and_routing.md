# 3. Tables inside a species account, and both readers on one paper

## The problem

Taxonomic papers describe one species after another. Each account has its own text and often its own small table, with no species column. Two things go wrong:

- **The table gets no species.** The species question sees a paper with several species and closes every table without a species column: 36% of Jakub tuning GT rows.
- **A paper goes to one reader only.** Routed to tables, its text is never read (340 Jakub rows; the body measurements of every table-routed newPDF paper). Routed to prose, it still gets its table rows, so only the first direction loses.

## What exists

`v22` (built in the fork, not adopted): a table under an account heading takes that account's species. Code finds the heading by layout, nimble confirms the table kind and the account.

- 109 and grit: no score change (0 and 2 papers with changed rows). Safe.
- Jakub tune: 321 tables given a species, 296 of them a GT species. Matched rows 2,119 → 3,722, most of them vague until fix 2 names them.

`two_step --route both` runs both readers.

## The plan

1. **Adopt v22's account step** together with fix 2, since its rows need the row labels to be exact.
2. **Routing**: run prose on every paper whose text nimble says describes organisms (the existing Q-TEXT), whether or not it has a traits table. Papers that only report a study keep tables only.
3. **One fact once**: a prose row and a table row with the same species, value and a name sharing its words are the same fact; keep the table row. Code only, exact value match.
4. **New false positives of v22**, each a model question, not a code rule:
   - a table comparing other species inside an account: the account species is given only when the table has no organism column;
   - ratio and index columns: handled by fix 6.

## Your decision

Prose on every describing paper costs time: about 5 minutes per paper on the remote. On the 109 set that is the 6 prose papers today against perhaps 15–25.

## Measure

- Jakub tune and test: rows matched, false positives.
- 109 and grit: no paper down; count of prose rows added to table-routed papers and how many are in scope.

## Size

Small for adoption and routing; the duplicate rule is code only.
