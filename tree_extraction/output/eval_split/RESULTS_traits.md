# Trait-column questions — results (2026-10-18): NOT adopted

Frozen variant: iteration-4 wording, conservative application (drop columns nimble calls
identifier / organism / other; no long reading). Held half run once with it, no tuning.
Baseline: output/full_run_v4 (species-column questions). v4 stays the current best.

## Dev (54 papers, used for development)

| | v4 | iter 3 (full) | iter 4 (full) | conservative (frozen) |
|---|---|---|---|---|
| mean F1 | 0.511 | 0.511 | 0.512 | 0.514 |
| scoped micro F1 | 0.395 | 0.398 | 0.393 | 0.393 |
| improved / regressed vs v4 | | 2 / 2 | 3 / 1 | 2 / 1 |
| dropped columns holding GT values | | 7 | 6 | 6 |

## Held (55 papers, run once)

| | v4 | conservative |
|---|---|---|
| mean F1 | 0.535 | 0.532 |
| scoped micro P/R/F1 | 0.768 / 0.298 / 0.429 | 0.773 / 0.285 / 0.416 |
| improved / regressed vs v4 | | 1 / 3 |
| dropped columns holding GT values | | 10 (30 junk columns dropped) |

Regressions: Fiedler2021 0.667 -> 0.400 ('Associated_ants': a trait whose values are
organism names, called `organism` 0.98, 523/523 cells GT values), Scalercio2020 0.739 ->
0.691 (flight months 'First_Month' / 'Last_Month', 'TSD' called `other`), Guariento2020
-0.011. Gain: Cady1993 0.438 -> 0.583.

## Why it fails to generalise

`organism` and `other` catch real traits whose values look like something else: an
association whose values are organism names (ants, hosts, prey), phenology given as months
or dates. Dropping on those answers removes GT rows; the junk it removes (IDs, principal
components, site indices) is mostly outside what the GT scores, so precision barely moves.

## Measurement notes

- The scorer's type matching uses gemma: Orr2024's remap differed between two runs (+910
  wrong rows on a run that only REMOVED 4,187 junk rows). Micro F1 differences of a few
  thousandths on big papers are within that noise.
- The column check compares raw cells with GT values, so coded columns (Khayati2024
  'Foraging strategy') can be losses it does not see.
