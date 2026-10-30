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

## Results, all papers (2026-10-29, code 9700a883; TAGS_V14.txt in each set's full_run_v14)

Core rows (species, trait, value) changed vs v13: none on either set. Overwrites: all fixed, none broken
(109: sex 23,008, caste 4,121, statistic 2).

109 set, coverage / accuracy on the matched GT rows (v13 filled almost none of these):

| tag | dev | held | accept rule |
|---|---|---|---|
| sex | 74.3% / 98.1% | 23.3% / 94.9% | passes |
| caste | 82.5% / 97.5% | 52.4% / 100% | passes |
| lifeStage | 94.3% / 80.2% | 32.9% / 75.5% | passes (dev just at 0.8) |
| basisOfRecord | 98.6% / 62.2% | 99.7% / 92.5% | fails: dev accuracy < 0.8 |
| measurementStatistic | 99.3% / 90.9% | 42.9% / 60.7% | fails: held falls 0.30 below dev |

Grit (all 148): sex 33.6% / 76.1%, caste 42.3% / 92.6%, basisOfRecord 98.6% / 57.0%, lifeStage
59.0% / 71.1%, statistic 82.3% / 67.7%. Grit-only papers are weakest (sex 30.8%, basisOfRecord 35.5%).

Where the losses sit (tag_losses.py, scratch):
- Missing values are mostly defaults the paper never prints: Noriega2023 alone is 34.6k of the 109
  set's sex / lifeStage / statistic misses (GT unknown / adult / individual; no quote found). Caste
  misses are "worker" on ant papers that never say it (Normandin2017, CamargoVanegas2024, Cappellari2022).
- basisOfRecord wrong both ways on the origin question: own data called compiled (Tingting2023,
  Griffiths2016, MiddletonWelling2018, Korosi2022, Arnan2014, Gathof2022, Brant2021) and compiled not
  seen (Guariento2020, Graf2021, Eckert2023, Cappellari2022); Orr2024 Living vs Preserved is 11.8k rows.
- Statistic: whole-paper answers that fit only some tables (Ji2024 individual vs mean, Guariento2020
  mean vs mode / count, Fiedler2021).
- Calibration: probability is not a sureness signal for basisOfRecord (≥ 0.95 right 53%) or statistic
  (≥ 0.95 right 27%); it is for caste (90%) and lifeStage (0.8–0.95 right 81%).

## basisOfRecord fix (dev only; held is not used for tuning from here on)

The GT sets basisOfRecord per trait: the traits taken from the literature are MaterialCitation and the
traits measured by the authors take the specimens' kind (Cappellari2022 foraging range vs body size,
Eckert2023 eye size / feeding strategy vs body length, Graf2021 nesting site, social behaviour). Two questions:
- **source** (per trait column, or per trait name of a long table, answered only when every trait agrees):
  "Where do the values of the trait 'X' come from?" measured in this study / taken from the literature.
  Evidence: the table and the paper's sentences naming the trait; a trait no sentence names is not asked.
  (First try also gave the paper-wide quotes: Raine2018's measured traits became 'literature', 10.6k rows;
  dev 62.2% -> 65.7% with Orr2024 fixed.)
  Literature -> MaterialCitation for that trait; measured -> the caption's or the paper's specimen value
  (never the origin's MaterialCitation; empty if there is none). Before the paper-level answer.
- **specimen** (only when the paper's value rests on quotes nimble gave it under 0.95): the methods'
  sentences on collecting, keeping and storing the organisms -> alive / preserved / observed (Orr2024's
  "wet mass of each individual" gave LivingSpecimen at 0.82; its wasps were collected and stored).
GT cases that contradict their paper (left as they are, for the user to check by eye): Korosi2022 (traits
from a database, GT HumanObservation), Cecala2021 (traits from the literature, GT LivingSpecimen),
CamargoVanegas2024 (Winkler samples measured under a micrometer, GT LivingSpecimen).
Dev result (code 03a1fad9): basisOfRecord 62.2% -> 88.0% accuracy, coverage 98.5%; reported values 92%.
Orr2024 right (specimen question: "euthanized ... stored at -20 °C" -> PreservedSpecimen 0.98), Raine2018
kept. Left on dev: the three GT cases above (2.2k rows), Graf2021 and Cappellari2022 (the paper does not
say these traits came from the literature), Wallon2024, Uemori2021. Other tags unchanged; core rows none.

## measurementStatistic fix (dev only)

Dev losses: GT mean / ours individual 1,724 rows (Gossner2013, Eckert2023: "Body length" called individual
at 0.99 while the methods say "an average body length" per species), mean / mode 633, mean / mean ± SD 488
(CamargoVanegas2024 splits Mean and SD columns: GT mean and sd). The column question saw only the table.
Now it is asked after the text rounds, with two more facts: what one row is (code counts the species of
the rows as assembly reads them: one species per row, or species over several rows) and the paper's sure
sentences about the statistic. nimble still decides; the column answer still comes before the paper's.
Dev result (code 6b633ca6): measurementStatistic 90.9% -> 93.6% accuracy, coverage 99.3% -> 99.8%; mean /
individual 1,724 -> 745 rows (Gossner2013 right). Left: CamargoVanegas2024 Mean / SD columns (GT mean and
sd; 'sd' is not on the template list), Korosi2022 (GT mean for class traits), Cerini2023, Khayati2024.
basisOfRecord 87.8% in this run (88.0% before; same questions), other tags unchanged, core rows none.

## Held, run once (2026-10-30, questions frozen at 6b633ca6) and the accept rule

| tag | dev acc | held acc | held cover | rule |
|---|---|---|---|---|
| sex | 98.1% | 94.9% | 23.3% | passes |
| caste | 97.5% | 100% | 52.4% | passes |
| basisOfRecord | 87.8% | 93.1% | 97.5% | passes (was 62.2% on dev) |
| lifeStage | 80.2% | 74.0% | 33.8% | passes (0.06 below dev) |
| measurementStatistic | 93.6% | 63.2% | 42.6% | fails: 0.30 below dev (was 60.7% held) |

Core rows changed vs v13: none; overwrites fixed only. Per the rule, measurementStatistic is left out of
v14 and not tuned on held. Held coverage stays low because most of its empty values are ones the paper
never prints (Noriega2023 alone, see above): the defaults layer, still off.

## Split for the statistic work from v15 on (2026-10-30, the user's rule)

output/eval_split/split_v15.json (seed 20261030): tune on **dev** (54) + **held_a** (28), test once on
**held_b** (27). held_a = the 24 held papers already named in loss lists, quotes or logs, plus 4 drawn.
Grit-only papers (not in the 109 split) are not looked at: no per-paper views, only totals at test time.
First fix planned (v15): statistic sentences about the analysis (community weighted means, diversity
indices, model results, site averages) dropped from the evidence; the user's example, Guariento2020:
"The community weighted means of nearly all individual functional traits showed significant ecological
patterns" was classified mean 0.85 and became the paper's value. 38 such quotes in the 109 set.

## v15 run 1 (2026-10-30, code c62811d9): analysis sentences left out — tuning papers only

gemma read the text for the statistic alone; nimble judged 104 of 305 quotes to be about the analysis.
measurementStatistic accuracy (coverage): dev 93.6% -> 92.9% (99.6%), held_a 61.1% -> 67.5% (40.3%);
dev + held_a together 83.4% -> 84.9%. Other tags and core rows unchanged. 11 papers up, 12 down.
- Up: Guariento2020 +1,996 rows (the user's CWM example no longer used), CamargoVanegas2024 +276,
  Normandin2017 +197, Eckert2023 +129, Leong2023 +116, Korosi2022 +102.
- Down: Teder2020 -731, Scalercio2020 -219, GibbParr2013 -161, Wallon2024 -142. Teder2020's numeric
  column (wingspan) lost its sentence "Average wingspan ... an average of mean male and female": with two
  sentences per chunk, gemma now quotes the class traits (voltinism, overwintering stage) and the paper
  value turned mode. Papers mix numeric traits (GT mean) and class traits (GT mode): one paper value
  cannot fit both, and sentences about one kind steer the other kind's columns.
- The paper-level value changed in 35 more papers with no row changed: it is unstable.
Next: give each column the sentences that name its trait (as the basisOfRecord source question).
