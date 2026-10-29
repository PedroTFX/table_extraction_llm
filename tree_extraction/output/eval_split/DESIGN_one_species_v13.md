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

## Dev iterations (dev papers only)

- **1** (grit dev, repeatable scorer): Grasser 0 -> 0.165, the others unchanged. Subjects right
  in all 7 (Wright's by duels: the weevil 0.998 over its host tree, then 0.997 over 'several').
  Wrong: a table with no sure Q-ROWS still got the subject (Wright t0: '(no name, column 0)'
  rows); Q-COLUMN called correlations, MS columns (Grasser t0, t1) and definitions (Luo t0)
  'value'; Grasser's 'LAM' unsure between value and group. Not this step: value marks
  ('0.59a', '0.157 ± 0.077A': the endings shape needs a space and a lower-case letter) and
  Luo's names ('HW (mm)': the meaning step left it as printed).
- **2**: a table that gets its species only from this step, or that a clash brings back, needs
  a sure Q-ROWS answer, and for trait rows a sure names column and values column; Q-COLUMN
  gains 'test' (a result of a test, model or comparison) and 'label' covers definitions; the
  value option says its header may name the group it was measured under.
  Result (grit dev, production scorer): Grasser 0 -> 0.384, the others 0. Zhang's names now
  match the GT ('Egg Size (mm)*' -> 'Egg size'); only the marks differ ('1.31 ± 0.04a' vs
  '1.31 ± 0.04'). Luo's definitions table (t0: Trait / Indicator of function / Measure) is read
  as trait rows, and its 'Head width' row takes the GT name the scorer would give 'HW (mm)'.
- **3**: Q-ROWS gains 'definition' (a trait with its definition or method, no measured value):
  such a table gives no rows. For the tables of the subject, v3's ending question (mark or part
  of the value) is asked for trait columns whose cells end in letters stuck to the value
  ('0.59a', '0.077A'; decoder_v3's shape wants a space and lower case); a sure 'mark' is written
  to the column's decode record as v3:endings does. Treatment comparisons print these letters.

## Full run 1 (iteration 3 code, both sets) and what follows from the rules above

- Grit (production) 0.539 -> 0.551, 6 up / 4 down; repeatable 0.538 -> 0.542. 109 set 0.560 ->
  0.576, 4 up / 1 down. Held: Brant2021 0 -> 1.000 (production), Tran2022 0 -> 0.400, Borges
  unchanged. Down: kovacs2010 1.0 -> 0.5, Stemkovski2020 0.97 -> 0.65, PascacioVillafan2022
  0.80 -> 0.50, Buzzone2008 -0.03, Bucher2024 -0.005 (grit); Attiwilli2022 -0.04 (109).
- The gate-'several' branch named '67 bee species' (Stemkovski) and '251 tropical butterfly
  species' (Attiwilli) a paper's one subject: by the rule above it is **dropped** (it gained
  nothing: Borges and Wright did not move).
- The code did not follow this design for trait-per-row tables: it cleared every trait column
  the model was not sure about (kovacs2010's CV columns hold GT values). **Fixed to the design:**
  a trait column not answered stays a trait column (a values column of the long reading).
- Not changed (it would tune on the full run): a structure 'summary' lifted by the clash duel on
  tables of slopes or coefficients (kovacs2010 t4, Bucher2024 t2), and the trait re-reading of
  tables v12 already read (PascacioVillafan2022, Buzzone2008).

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
