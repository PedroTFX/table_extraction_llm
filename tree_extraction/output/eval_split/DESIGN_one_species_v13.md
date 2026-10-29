# One-species experiment tables (v13 = v12 + the subject step) — design, 2026-10-29, before any run

## The problem

Some papers study one species. Their tables do not list species: each row is an individual,
a group under one condition (diet, prey, temperature, age, line), a statistic (minimum, mean,
median), or a trait. The species, kind and structure questions were written for tables of many
species, so these tables are lost at different steps. Grit v12, every one of these at F1 0:

| Paper | Table | Its rows | Where it is lost now |
|---|---|---|---|
| Luo2023 | t4 | 164 workers × HW, ML, EW … | species step never sure (0.43 vs 'several' 0.31), v11 duel 0.65 |
| Brant2021 | t8 | 241 specimens × ITD, head width | kind 'sampling' 0.81, Q-ALSO 'no' -> no rows |
| Tran2022 | t1 | Minimum / Median / Mean / Max × flight measures | structure 'summary' 0.97 -> no rows |
| Grasser2000 | t1 | traits × HAM / LAM | structure 'summary' 0.97 -> no rows |
| Zhang2025 | t2 | oviposition order × egg size … | kind 'model' 0.92 -> no rows |
| Zhang2025 | t0 | age × mated status | Q-ROLE made 'Age (d)' a trait: types '2', '15', '30' |
| TOMBERLIN2002 | t1–t3 | diets × weights, longevity | 'Diet' read as a trait (rows 'Diet = Gainesville diet') |
| Wright1999 | t0 | trait / value | gate 'several' (the host tree is named) -> no species |
| Borges2021/2024 | t0, t1 | prey × fecundity, r_m … | gate 'several' (the prey aphids are named); prey read as organisms |

## The step: v13:subject (one_species.py)

Code picks the questions and applies the sure answers; nimble decides. SURE = 0.8.
Long option lists go to duels (duels.py, v11): two options at a time, anything not sure stops
and changes nothing.

1. **The subject (per paper).** From the species step's saved state:
   - gate 'one' with one name, or gate 'one' and every table it named got the same name: that
     name is the subject (the model already said so; no question);
   - gate 'one' with other names: Q-SUBJECT duels over the names, the one left against
     'several species';
   - gate 'several' or 'undecided' with 1–3 names (Wright: the weevil and its host tree;
     Borges: the ladybird and its prey): the same duels, the one left against 'several
     species'. The final duel is the clash with the gate's 'several': the model decides it.
   - more names, or none: the paper is not touched.
   Q-SUBJECT: "Which organism did this study take its measurements on?" — "'X': the study
   measures X; any other organism named is its food, prey, host, plant or partner" /
   "several species: the study measures more than one species".
2. **The tables (per table of a paper with a subject).** The tables the species step looked at
   (records, a trait column, no organism column). One the species step already gave the subject
   is the subject's; one it gave another name is skipped; the rest are asked
   Q-OWN: "Are the values in this table measurements of X?" — yes: its individuals,
   specimens, colonies or castes, groups of it under different treatments, diets, prey,
   temperatures, ages or times, or summary statistics of them / no: definitions, methods,
   sites, counts per site, test results, or another organism.
3. **Clash with a dropped table.** A sure 'no rows' from the kind step (figure / model /
   sampling / other) meets the table's 'yes' in one duel: the kind's own option text against
   Q-OWN's yes. Only a sure 'yes' lifts it. The structure step's 'no rows' (summary / other)
   meets the Q-ROWS answer (below) the same way.
4. **Q-ROWS** (duels; not asked for a table the structure step already read long or wide,
   whose reading stays): "What does each row of this table stand for?" — individual (one
   individual, specimen, colony or sample of X) / group (one group of X under one condition) /
   statistic (one summary statistic) / trait (one trait, named in the row, its values in the
   other columns).
5. **Q-COLUMN** (duels, rows = group / statistic / trait only), per column not tagged as the
   organism: "What does the column 'C' give for each row?" — value (a value measured on X) /
   group (which group: treatment, diet, prey, temperature, age, sex, caste, line, site, time) /
   statistic (which statistic) / name (the trait the row is about) / label (an identifier,
   sample size, test result or note).

## How the answers are applied (code, v13 layer of plan())

For a table of the subject (step 2 yes, or the species step's own name) whose clashes were won:
- the kind / structure 'no rows' is lifted (those decisions are not applied to this table);
- its rows get the subject as their organism (t.paper_species, as the species step's name);
- individual: read wide (every trait-tagged column is a trait, as structure's 'wide');
- group / statistic: read wide; sure column answers: value -> trait, group -> sampleTreatment,
  statistic -> measurementStatistic, label -> none;
- trait: sure answers: name -> the long table's names column, value -> a values column (its
  header kept as sampleTreatment when there are several), group / statistic / label -> none;
  without a sure name column and a sure value column the tags stay;
- an answer that is not sure leaves the tag as it was.

Not touched: papers without a subject, tables of another organism, tables with an organism
column (Borges t1's 'Species' column holds the prey: not in this step), names (Mirzaee's
'Width (mm)' for the GT's 'Ootheca width'), value marks ('0.104 ± 0.027a').

## Measure

- **Dev (looked at):** Luo2023, Mirzaee2023, Tsai2020 (109 split, dev); TOMBERLIN2002,
  Zhang2025, Grasser2000, Wright1999 (grit only). **Held:** Brant2021, Tran2022, Borges2024
  (Borges2021 on grit). Leak: their first rows and saved decisions were printed while finding
  this group; nothing is tuned on them.
- Decisions reported apart from rows: subjects found, tables owned, clashes won, Q-ROWS and
  Q-COLUMN answers (sure / not sure).
- Per-paper F1 v12 -> v13 on grit and the 109 set, both scorers; regressions counted among
  papers that were right (F1 >= 0.6 before).
- Adopt when the dev papers go up, no held paper goes down, and neither set's mean F1 drops.
  If the gate-'several' branch puts a paper that was right down, that branch is dropped
  (it reaches 48 grit papers, most of them truly of several species).
