# Section step (v8 = v7 + sections) — design, 2026-10-27, before any run

## The problem

A section row is a label printed across a table that heads the rows below it ("Calliopsini",
"S Africa", "C. calcarata", "Wing length"). The head reader finds them (body / pre rows with
role `section`, head cells with role `section`); then `head_to_table` drops those rows from the
records and keeps only one context line listing at most 12 labels. The only use is the
organism step's genus completion (`organism_tree.species_from`: last label above the record).

109 papers: 42 papers, 85 tables, 194 section rows. Kinds seen: higher taxa (Graf t7/t8 28
tribes, Uemori t3, Melo t4, Taillefer x8, Geraghty, Rebrina, Ambsperg, Gonzalez), genus over
epithets (McCravy t0/t1), species over rows (Brasil t5), trait names (Attiwilli t1/t7), places
(GibbParr t2), analysis blocks (GibbParr t0), notes misread as sections (Eckert t4/t6).

Two faults in the one current use: only 12 labels reach the context line (Graf has 28), and
"last label above" ignores rank in nested sections (subfamily, then tribe).

## Where it lives

A new version folder `src/v8/` (= v7 + this step, standalone like the others) writing
`output/full_run_v8`. Only the v8 copies of `head_to_table.py` / `organism_tree.py` change, so
v3..v7 are untouched. Stages: everything v7 has, plus `v8:sections`, then assemble / score.

## 1. Code keeps the labels (no model)

`head_to_table` (v8 copy) records, for every table, its section labels in row order
`[(row, label)]` — body/pre rows with role `section` AND head cells with role `section`
(Graf's 'Andreninae', Brasil's first species 'A. sericeus' sit in the head) — and gives every
record `_sections`: the indexes of the labels above it. A headless continuation table that
joins the previous one carries the previous table's labels on. The context line keeps all
labels (no 12 cap; shortened in the prompt only).

Code facts only: row order and text. Code does not decide what a label is.

## 2. nimble decides what each label gives (Q-SECTION)

One question per label, on tables that give rows after v7 (kind traits, kept), asked with:
the table's headers, the label, the 3 rows below it, and the table's other labels (so it sees
the series: 'S Africa', 'SE Australia', 'Sweden').

    What does the label '<label>' tell about the rows printed below it?
      higher    a family, subfamily, tribe or order the organisms below belong to
      genus     the genus of the organisms below, whose rows give only the species epithet
      organism  the organism the rows below are about (the rows are not organisms)
      trait     the trait or measurement the values in the rows below are of
      place     the site, region or country the rows below come from
      context   the caste, sex or life stage the rows below are about
      treatment the treatment, condition or season the rows below were measured under
      other     a note, a continuation mark, an analysis block, or none of these

- `context` sure -> Q-CONTEXT: caste / sex / lifeStage (one more question).
- Sure = p >= 0.8. Unsure -> a second look showing 8 rows below; still unsure -> nothing
  applied (the label stays unused, as today).
- Clash: labels of one table that are siblings in the series (same rank of the same kind of
  thing) answered differently, both sure, -> the table's labels re-asked once together
  (one question: which one kind are these labels?), else each keeps its own answer.
  Model decides; code only detects the clash and picks the question.

## 3. Code applies the answers

Per record, for each kind, the nearest label above it with that answer:

| answer | applied to the record |
|---|---|
| genus | species = `<label> <epithet>` when the organism cell is a lone epithet (replaces the organism step's 12-label path) |
| organism | species = label, only when the table has no organism column decided (rows like Brasil's Low / Medium / High) |
| trait | measurementType = label for the record's trait cells, the column name moves to measurementStatistic only when the column tree tagged it a statistic; no change when the record already has a long-read type |
| place | verbatimLocality = label, unless the row already has one |
| context | caste / sex / lifeStage = label, unless the row already has one |
| treatment | sampleTreatment = label, unless the row already has one |
| higher, other | nothing (the GT has no higher-taxon column) |

Nearest-per-kind fixes nesting: a tribe below a subfamily is the nearest `higher`, and a genus
label is found even with a `higher` label between it and the row.

## Checking it (same rules as v4..v7)

- Dev / held split as frozen (output/eval_split/split.json); the papers looked at to write this
  (McCravy, Attiwilli, GibbParr, Graf, Taillefer, Uemori, Brasil, Eckert) count as dev.
- Repeatable scorer (use_llm=False) on dev for each iteration; accept rule: dev mean F1 does not
  drop, no dev paper drops > 0.005, and each applied kind is checked by eye on 10 labels.
  Held run once after freezing.
- A label key from the GT where it can be derived by values (label + epithet = a GT species;
  label = a GT trait name; label = a GT locality) to count right / wrong answers per kind.
- Optional oracle: a review page of the 194 labels (like output/column_review) for the person
  to answer; the oracle run shows what the step gives if nimble answered as the person did.

## What to expect

The score key is species + trait + value, so the gain comes only where a label completes a
species name (genus), names the organism, or names the trait. Many sectioned tables are already
dropped by v7's kind step (Attiwilli t1, Brasil t5, GibbParr t0 are model / statistics tables),
and higher-taxon labels add nothing scored. The expected F1 gain is small; the main gain is
correct fields (locality, caste, sex, treatment) on rows that are already right, and removing
the 12-label and rank faults.

Cost: ~194 labels -> about 200-300 nimble questions on the 109 papers (minutes).
