# Trait-column questions (trait_tree.py), written 2026-10-18 before implementation

Same split and rules as DESIGN.md (seed 20261018; iterate on dev; held once after freezing).
Baseline = output/full_run_v4 (species-column questions frozen), per-paper scores in its
summary.csv.

## Procedure (every table that gives rows, i.e. has species; nimble decides)

1. Q-COL, per column the tagger called measurementType / measurementValue: the table's
   headers, the column header and up to 8 cells. "What does the column hold?"
   - `trait`: a trait measured or recorded for each organism
   - `trait names`: names of traits (long format: each row names its trait, the value is in
     another column)
   - `identifier`: labels of specimens, individuals, samples, sites or records
   - `genetic`: genetic markers or genotypes
   - `organism`: names of organisms or taxa
   - `other`: test statistics, references, dates, places, methods, notes
2. `trait` -> kept as a trait column. `identifier` / `genetic` / `organism` / `other` -> not
   a trait (dropped from the rows).
3. `trait names` -> Q-VALUE: which column holds the value of the trait each row names
   (every other column offered with 3 cells, or none). Found -> the table is read long:
   that column is the type, the chosen one the value.
4. An answer below 0.8 -> the tagger's call stands (no code tie-break; avoids losing right
   columns on doubt).

## Measures

- Row level P/R/F1 per half, papers improved / regressed (vs full_run_v4).
- Column check against the GT (trait_col_eval in full_run_v5.py): a dropped column whose
  cells are GT values for its rows' species = a loss; dropped columns with no GT values =
  junk removed (or traits the GT does not cover: neutral).

## Iterations (dev only)

1. As above. Mean F1 0.511 -> 0.510; 3 improved (Wallon +0.04, Keller +0.04), 1 regressed
   (Kovacs2010 -0.11: long with one value column, its Gynes column lost). Columns: 104 junk
   dropped, 16 losses: SD columns called 'other' (Camargo, 13), Torok t8 nest site / prey
   called 'organism'; Orr's microsatellite loci called 'trait' (0.98).
2. (a) options: `trait` includes a trait's statistics (mean, SD, SE, range) and diet / prey /
   nest site; `other` = results of tests or models; `organism` = the organisms the rows are
   about. (b) the text printed directly above the table in Q-COL (layout). (c) Q-VALUE yes/no
   per candidate column (a long table may have one value column per caste or sex).
   Result: mean F1 0.511 -> 0.496, 2 improved, 3 regressed (Russo2017 0.934 -> 0.146,
   Kovacs2010 -0.07, Khayati -0.06). Losses 16 -> 7 (options + caption helped). The long path
   hurt: Russo's two-species-per-row table taken as long ('Functional Group' = trait names
   without a check), and reading a table long dropped all its other trait columns.
3. (a) Q-NAMES confirms a 'trait names' column before any long reading (names of different
   traits / values of one trait / organisms; unconfirmed -> the tagger's call); (b) a long
   table is assembled twice from the same records: long (type + value columns) and wide (the
   columns nimble called traits) — nothing else is dropped by reading it long.
   Result: mean F1 0.511 -> 0.511, scoped micro F1 0.395 -> 0.398 (wrong rows -1,800); 2
   improved (Kovacs2008 +0.07, Wallon +0.04), 2 regressed (Khayati -0.06: 'Foraging strategy'
   = group / individual / collective called 'other'; Kovacs2010 -0.07: a trait-by-trait
   correlation table and allometry slopes read long). Losses 7. Russo fixed.
4. FINAL dev iteration (decided with the user: one more, then freeze).
   Definitions: a MEASURED VALUE is what was measured or recorded for the organism for that
   trait, or a statistic of it (mean, SD, SE, range); a STATISTIC RELATING traits or groups
   (correlation, regression slope or coefficient, test statistic, p-value) is not a value.
   `other` narrowed to what does not describe the organism; behaviour joins diet, prey, nest
   site, activity as trait categories. Q-VALUE 'no' names statistics relating traits.
   ACCEPT RULE (set before the run): iteration 4 is kept if, on dev, vs iteration 3: mean F1
   and scoped micro F1 not lower, fewer papers regressed vs v4 (<= 1), and dropped columns
   holding GT values <= 7. Otherwise the CONSERVATIVE variant is frozen: only identifier,
   organism and other (test-result) columns are dropped, no long reading — scored from the
   same answers. Then freeze; held run once; no tuning on held.
   Result (dev): iteration 4 full: mean F1 0.512 (iter3 0.511), scoped micro F1 0.393 (iter3
   0.398: LOWER), 1 regressed (Guareschi -0.07), losses 6. -> accept rule NOT met.
   Conservative variant (same answers): mean F1 0.511 -> 0.514, Kovacs2010 +0.19, Wallon
   +0.04, 1 regressed (Guareschi2015 -0.07: its t3, a transposed fuzzy-coding table, has value
   columns called organism / other). Micro F1 0.395 -> 0.393, but scorer noise: Orr2024's
   type remap (gemma) differed between runs (+910 wrong rows with 4,187 junk rows REMOVED).
   FROZEN (2026-10-18): iteration 4 wording, CONSERVATIVE application (drop identifier,
   organism, other; no long reading). Held run once with it; no tuning on held.
   Held (run once): mean F1 0.535 -> 0.532, scoped micro F1 0.429 -> 0.416, 1 improved, 3
   regressed (Fiedler2021 -0.27 'Associated_ants' = organism; Scalercio2020 -0.05 flight
   months = other). NOT ADOPTED: v4 stays the best version. See RESULTS_traits.md.
