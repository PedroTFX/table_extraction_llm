# 6. Keep out what is not a trait

## The problem

Of the rows we write beyond the GT (200 judged by hand):

| Kind | Share | Examples |
|---|---|---|
| Copied right, not a trait | 24% | microsatellite alleles, colony and individual IDs, PCA scores, site × date counts, common names, higher taxa |
| Wrong | 16.5% | a host-plant matrix read with plant families as the organisms; a region column filled with another column's word; header words as values; plot rows given a species |

On new papers nobody will have a GT to hide these. They are the precision a user sees.

A related miss: Renoz2020's table is sampling by row (colonies), but also gives each colony's host plant and symbionts. The recheck question said "no traits" at 0.96.

## The plan

1. **Q-COL on every trait column** (exists since v7 for doubtful columns only). Asked with the header, legend and five values: does this column give
   - a characteristic of the organism (body, life history, behaviour, ecology, what it lives on or carries);
   - an identifier or label (specimen, colony, code, name, higher taxon);
   - a genetic marker or sequence reference;
   - a count or presence at a site, date or sample;
   - a statistic of an analysis (score, loading, p-value);
   - something else.
   Only the first gives rows. An identifier can still fill other fields.
2. **Organism check**: for a table read as organism × columns, are the row names the organisms the paper studies, or something they use or are compared with (hosts, plants, prey, sites)? Asked once per table with the paper's subject from the title and abstract.
3. **Q-ALSO wording** (the sampling recheck) broadened to "what the organism lives on, eats, hosts or carries", with both option orders.
4. **Repeats**: a species-level category printed once and written again for every specimen record (Noriega2023: 95 rows per fact). Keep one row per species, trait and value when the value column comes from a species-level table. Code, after the model has said which table is the source.

## Risks

- This is the fix most able to lower recall: a real trait called "identifier". So every tuning paper's dropped columns are listed and checked against the GT before adoption; a column the GT uses must not be dropped.
- More questions per table (one per trait column). Cached by header and values.

## Measure

- Rows beyond the GT: share judged not-trait and wrong (now 24% and 16.5%), on a fresh sample.
- Matched rows must not fall on any tuning paper.
- Renoz2020.

## Size

Medium. The question exists; it is widened and asked on every column.
