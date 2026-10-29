# The five listed tags (v14 = v13 + the listed-tag step) — design, 2026-10-29, before any run

## The problem

The annotation template gives five tags a fixed list of values (Excel dropdowns in 155 of the 258 GT
spreadsheets):

| Tag | The template's values |
|---|---|
| sex | both, female, male, unknown |
| caste | queen, male alate, worker, minor worker, major worker, soldier |
| basisOfRecord | MaterialEntity, PreservedSpecimen, FossilSpecimen, LivingSpecimen, MaterialSample, Event, HumanObservation, MachineObservation, Taxon, Occurrence, MaterialCitation |
| lifeStage | all, unknown, egg, larva, mature larva, nymph, caterpillar, pupa, adult, instar 1–20 |
| measurementStatistic | count, mean, median, min, max, single observation, individual, unknown, mean ± SD, mean ± SE, range, mode (+ ratio in some files) |

The GT fills them on every row; v13 almost never does. On the rows v13 gets right (species + trait +
value), v13 vs the GT:

| Tag | Grit: GT filled / equal / different / ours empty | 109 set: GT filled / equal / different / ours empty |
|---|---|---|
| basisOfRecord | 79,917 / 0 / 0 / 79,917 | 121,791 / 0 / 0 / 121,791 |
| sex | 79,917 / 57 / 5,204 / 74,656 | 121,791 / 4 / 41,287 / 80,500 |
| lifeStage | 79,917 / 0 / 0 / 79,917 | 85,688 / 0 / 0 / 85,688 |
| caste | 11,555 / 0 / 0 / 11,555 | 21,940 / 8,174 / 4,174 / 9,592 |
| measurementStatistic | 79,917 / 259 / 194 / 79,464 | 121,791 / 249 / 6 / 121,536 |

Where v13 fills one and differs, it is the printed code, copied from a table column tagged with the
tag: sex 'f', 'maj m', 'min m' (Raine2018), '0' / '1' (Ji2024); caste 'gyne' (Orr2024), group numbers
'1'–'7' tagged caste (Luo2023).

These tags do not enter the headline key (species + trait + value), so this step leaves the headline
F1 alone; it is measured by the per-tag statistic below.

## What the GT does (read before designing; grit, one entry per paper and tag)

| Tag | One value in the paper | One per trait | Varies inside a trait |
|---|---|---|---|
| sex | 81 | 45 | 23 |
| lifeStage | 78 | 66 | 6 |
| caste | 33 | 5 | 2 |
| basisOfRecord | 92 | 52 | 5 |
| measurementStatistic | 50 | 78 | 20 |

A single paper-level answer is wrong for about a third of these. Many values are not printed: 'both'
(sex) appears with no 'both sexes' / 'males and females' in the paper in 105 of 120 entries; 'mode'
(statistic) in 101 entries, 'all' (lifeStage) in 56, both without a word a reader could find. These are
annotation conventions, not reported facts. No annotation guide was found.

## Every expected value gets a class (the measure keeps them apart)

- **reported**: the paper prints it (a word for it in the text, a caption, a header or a cell);
- **inferred**: it follows from what is printed (a column of species means -> 'mean');
- **defaulted**: assigned by convention, nothing printed supports it ('both', 'mode', 'all');
- **not recoverable**: nothing in the paper.

The GT side is classed by a printed-word proxy (scratchpad tag_scope.py's cue words, written before
any run); ours by where the answer came from (below). Defaults are never reported as extracted.

## The step (v14:tags, listed_tags.py) — nimble decides, code picks questions and applies sure answers

Evidence, from the most local to the paper:

1. **Tagged columns.** A table column tagged sex / lifeStage / caste / measurementStatistic: each
   distinct cell is classified into the template's list, or 'not a <tag> value' (Luo2023's group
   numbers). Codes defined in a legend ('0' / '1') go through the legend inventory first, as the decoder
   does. One question per distinct value per column; long lists (lifeStage) in duels (duels.py).
2. **Column headers and parts.** A trait column whose header or header parts name the tag ('Body length
   Female', 'Workers HW', 'Mean ± SD'): the part is classified the same way and applies to that column.
3. **Table caption and the text directly above / below.** Classified per table; applies to its rows.
4. **The paper text.** Sections from the markdown headings and the supplement markers
   (`<!-- ===== Complementary: X ===== -->`): abstract and methods first, then the introduction, then the
   supplements, then results / discussion; references, acknowledgements, funding and data availability
   left out. gemma reads each section and quotes the sentences that say which sex / life stage / caste
   was measured, how the specimens were obtained, and which statistic the values are; code keeps only
   quotes printed in the paper; nimble classifies each kept quote into the list or 'not stated'.
   A later section is read when the earlier ones gave no sure answer **or** gave answers that differ.

Scope is the level the evidence came from: a cell answer applies to its row, a header to its column, a
caption to its table, a text answer to the paper. A more local sure answer wins over a wider one; two
sure answers at the same level that differ go back to nimble in one duel ('neither' allowed); unsure
leaves the tag empty. Nothing overwrites a value v13 already holds unless the value is a code the
column question mapped (the 'f' -> 'female' case); every overwrite is counted.

**Defaults** are a separate, switchable last layer, applied only where no evidence answered: written to
the CSV with the class 'defaulted' in a side file, so the measure can report the tag with and without
them. Which defaults (sex 'both', lifeStage 'adult' or 'all', statistic 'mode' for a categorical value)
is read off the dev GT, not assumed.

**measurementStatistic** per trait column: the structure and value shape of the column (one category per
species, one number per species, a number per individual, 'x ± y') is asked as a column question with
the template's list as options; that is evidence (inferred), not a default.

## The measure (written first; repeatable, no model)

Per tag, on the rows matched on species + trait + value (the scorer's matching, its saved taxon and
trait-name remaps): GT filled / ours filled / equal / different / ours empty / ours only; coverage
(ours filled of GT filled), accuracy (equal of both filled), extras (ours filled, GT empty), overwrites
of v13's values; each split by the GT value's class (reported / defaulted) and by our answer's
evidence level (cell / header / caption / text / default). Per paper and over all rows. Values compare
exactly: both sides come from the same list. Scope accuracy: per paper and tag, the level our answers
vary at vs the GT's level (table above).

The model's sureness is checked against correctness on dev before any threshold is relied on: per tag,
accuracy of answers by probability band (0.5–0.8, 0.8–0.95, ≥ 0.95).

## Dev / held

- 109 set, frozen split (seed 20261018): **dev** = the split's 54 dev papers, **held** = its 55 held
  papers; held is run once, after the questions are frozen.
- Grit: every paper run; reported as split-dev / split-held / grit-only.
- Leak: the cases above were seen while writing this — Raine2018, Orr2024, Luo2023 are dev; Ji2024 is
  held (its '0' / '1' sex codes). Nothing is tuned on held results.

## Accept rule

Adopt when, on dev, coverage of reported values rises and accuracy on what we fill is at least 0.8 for
each tag kept; on held, no tag's accuracy falls below dev's by more than 0.1; the headline F1 of both sets
is unchanged (the key does not use these tags; a change there means a bug); overwrites are only the
mapped codes. A tag that fails is left out of v14, not tuned on held.

## Not in this step

measurementUnit (no list; mostly in column headers, the table side), the free-text tags
(samplingProtocol, sampleTreatment, verbatimLocality, dates, measurementMethod), and prose-only trait
records (Baine2024, Liu2024, RamosGonzalez2024, Ustjuzhanin2024, Xia2022, Xu2024).
