# Fix plan (2026-11-10)

The goal is extraction that works on papers we have never seen, not only the 109, grit and Jakub sets. So every fix here is a general rule about how papers print data, decided by the model, with no paper names and no domain words in code or prompts.

## Built 2026-11-10, not run yet

You said to follow the plans, all but fix 5 (Viza2023 is too much its own case). Everything below is written and compiles; none of it has run, so the first remote run of each stage is also its first test.

| Fix | Where | State |
|---|---|---|
| 1 units | `src/v23/unit_tree.py`; also the `units` layer of `src/v24` | built |
| 2 names from context | `src/v24/row_label.py` (layer `rowlabel`): Q-ROWLABEL, Q-HEADER, Q-OBJECT | built |
| 3 accounts, routing | layer `account` of v24 (v22's step); `two_step.py --route text` and `--once` | built |
| 4 prose names | t5b: only its test run is left; positional lists: variant `t6` (`prose_tree_t2.py`) | built; wrong owner: not started, diagnostics first |
| 5 category groups | | held back |
| 6 relevance | `src/v24/relevance.py` (layer `relevance`): Q-ALSO2, Q-ORG, Q-COL, Q-LEVEL | built |
| 7 big tables | `src/v24/head_wide.py`, then `src/reread_paper.sh keep <paper>` | built |
| 8 evaluation | A done; D: `src/reread_paper.sh`, README note; B (a fresh set) and C (GT decisions) are yours | partly |

`full_run_v24.py` holds the four table layers. The model stages write their answers once (`output/full_run_v24`); `V24_LAYERS` picks the layers that assemble and score use, so each layer is measured alone against v18 from the same answers. Runner: `src/v24/run_v24.sh` (smoke, stages, score); Jakub: `src/jakub/run_v24.sh`.

Where the build differs from the plan text:

- Fix 2: the caption question is asked when every trait column's printed name is one word (layout), not when code judges it "a bare dimension".
- Fix 3: "one fact once" asks that every word of one name is in the other, not only a shared word.
- Fix 6: the repeats rule asks nimble per column (same value on every row of a species: of the species, or of each specimen?) instead of naming a source table. An identifier column is taken out; it does not fill another field yet.
- Fix 7: each window is read by the frozen head reader as a table of its own and all windows must agree on the first record, instead of reusing the first window's answer.

## Where we stand

| Set | Score now | Main loss |
|---|---|---|
| 109 (tables + prose) | mean F1 0.653; tuning 0.690, held_b 0.540 | 10 papers at 0; trait missing 16,800 rows; value differs 10,487 |
| grit (147) | mean F1 0.619; grit-only 0.562 | 18 papers at 0 |
| Jakub tune (50 papers, my judge) | exact 19%, vague 10% of 7,457 GT rows | 36% sit in tables inside species accounts; names lose the leg or dimension |

Beyond the GT we write as many rows again: 99% copied faithfully, about 58% real traits, 24% not traits, 16.5% wrong.

## The fixes, in the order I would build them

| # | Fix | File | Why it is broad | Evidence |
|---|---|---|---|---|
| 1 | Units out of the header into the unit field | [01_units.md](01_units.md) | Almost every measurement table prints "(mm)" in the header | unit agrees on 0.9% of 99,513 matched rows |
| 2 | Trait names completed from the table around them | [02_names_from_context.md](02_names_from_context.md) | Row labels, group headers and captions carry part of the name in most morphometric tables | Jakub v22: 2,360 vague vs 1,362 exact; Mirzaee; Mean / SD rows |
| 3 | Tables inside a species account, and both readers on one paper | [03_accounts_and_routing.md](03_accounts_and_routing.md) | Taxonomic descriptions: the largest paper type we fail on | 36% of Jakub GT rows; 340 rows of text never read |
| 4 | Prose names and positional lists | [04_prose_names.md](04_prose_names.md) | Any description that prints "part 4.1 long, 3.2 wide" or keyed number lists | t5b: exact 1,345 → 1,786 |
| 5 | Category groups and coded columns | [05_category_groups.md](05_category_groups.md) | Fuzzy-coded and presence-marked trait tables are standard in ecology | Viza 1,695 rows; 17.5% of extra rows have code names |
| 6 | Keep out what is not a trait | [06_relevance.md](06_relevance.md) | Every supplement mixes traits with IDs, genetics, counts | 24% of extra rows not traits, 16.5% wrong |
| 7 | Tables too big to read | [07_big_tables.md](07_big_tables.md) | Supplement datasets are often the whole GT | Chichorro 620 rows; any table over the model's context |
| 8 | Scoring, tests and GT decisions | [08_evaluation.md](08_evaluation.md) | Lets us trust a gain on unseen papers | 6.5% of extra rows are GT traits the scorer missed |

## Rules every fix follows

- **The model decides.** Code finds candidates by layout, asks, and applies sure answers (0.8 or more). Not sure means nothing changes.
- **No give-away wording.** Prompts describe a shape ("a part, a number, a qualifier"), never words from our papers. Examples are made up, from another field.
- **A fix must fire in several papers of at least two sets** on tuning data. If it fires in one paper only, it waits.
- **One layer per fix**, on top of v18 / t2, so each can be measured and dropped alone.
- **Measure, then test once.** Tune on 109 dev + held_a and Jakub tune. Then held_b, Jakub test and grit-only once, totals only. Adopt when tuning rises, no tuning paper falls more than 0.01, and the test groups do not fall.
- **Remote only, one model at a time**, and each design must also run on the local PC.

## What I need from you

1. OK on the order, or a different one.
2. The GT decisions listed in [08_evaluation.md](08_evaluation.md).
3. For fix 3: whether prose may run on every paper (it roughly doubles run time on papers that have both).
