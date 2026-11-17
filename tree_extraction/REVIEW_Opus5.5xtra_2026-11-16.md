# Review of `tree_extraction`: the Fable review checked against the data (Opus 5.5, 2026-11-17)

The Fable review (`REVIEW_Fable5.2_2026-11-16.md`, written 2026-11-16 and revised on 11-17) made a series of claims about the project and recommended what to do next. This review takes each claim in turn, says briefly what Fable said, and checks it against the data now available. That data is the calibration audit (`output/eval_split/CALIBRATION.txt`, `CALIBRATION_WRONG.txt`), the per-version score summaries, and the saved answers and outputs on the remote. Each point ends in one verdict:

- **Confirm**: the data supports the claim as stated.
- **Deny**: the data contradicts it.
- **Change**: the data supports part of it, or points to a different conclusion or action.

All per-paper evidence is from tuning papers (dev + held_a). held_b and grit-only appear as totals only.

## Summary

| # | Fable's claim | Verdict |
|---|---|---|
| 1 | Steps lose 10 to 30 points on papers they were not developed on: overfitting | **Change.** The gap is real and grew, but it is almost all zero papers, and most layers never fired on held_b |
| 2 | held_b "does not fall" is a test | **Change.** The gate has little power: the held_b mean did not move for most versions |
| 3 | Row F1 cannot see several kinds of change | **Confirm** |
| 4 | The table is read as patches on a per-column tag | **Confirm** |
| 5 | A sure answer is not a reliable answer | **Change.** Reliability differs by question; the base column tree is the most reliable part |
| 6 | Move or set thresholds from the curves (and my own follow-up: a decoder threshold what-if) | **Deny.** A higher threshold removes fewer errors than it costs, and for the decoder it cannot raise F1 |
| 7 | Prompts carry the dataset | **Confirm,** at Fable's priority |
| 8 | Viza2023: category tables; the key table is read as data | **Confirm the first; deny the second** |
| 9 | 23 copies of modules: a source of silent divergence | **Deny the divergence**; the copying cost stands |
| 10 | No explicit uncertainty or provenance in the output | **Confirm** |
| 11 | Evidence retrieval is uneven | **Confirm, with more cases** |
| 12 | About 17 to 19 zero papers cannot be reached | **Change.** That count is a month old; the current zeros each have a known cause |
| 13 | Experiments in priority order | **Change the order** (section 13) |

## 1. Generalisation: "10 to 30 points are lost on papers that did not shape the step"

**Fable said.** Every comparison of development papers with other papers shows a drop (decoder 97% to 63%; tables 0.651 to 0.494; units 61.7% to 38.1%), so the steps overfit the papers they were built on.

**Data.** Mean F1 per version, tuning (82 papers) against held_b (27), from each run's `summary.csv`:

| Run | Tuning mean (zeros) | held_b mean (zeros) | Gap |
|---|---|---|---|
| Production pipeline (gemma; not tree_extraction) | 0.299 (45) | 0.372 (12) | −0.073 |
| tree_extraction base | 0.469 (27) | 0.353 (12) | +0.116 |
| v4 | 0.570 (15) | 0.381 (12) | +0.189 |
| v7 | 0.587 (15) | 0.462 (8) | +0.125 |
| v13 | 0.622 (11) | 0.462 (8) | +0.159 |
| v18 | 0.663 (8) | 0.494 (8) | +0.169 |
| v24, all layers | 0.680 (7) | 0.489 (8) | +0.191 |

On papers above zero only, the gap is −0.007 for the production pipeline, +0.064 for the tree_extraction base and +0.033 for v18.

- **held_b was not harder to begin with.** Under the independent production pipeline it scored higher than tuning. So the later gap is not the papers' difficulty.
- **The gap is almost all zero papers.** Development took tuning zeros from 27 to 8 and held_b zeros only from 12 to 8. On the papers we do read, held_b is within 0.03 of tuning.
- **Part of the gap is there from the first tree_extraction run** (+0.116), because the base was built on the bench papers, which sit in tuning.

**Verdict: Change.** The gap is real and it grew with development, as Fable said. But "10 to 30 points lost" describes the wrong thing. What fails to carry over is the rescue of whole papers. Each zero-paper fix targeted a tuning paper's own failure, and held_b's zero papers are other failures. On papers both sides read, accuracy carries over well. For new papers, expect accuracy on readable papers to hold, and expect roughly one paper in three to fail completely, with failure types not yet seen.

## 2. "held_b does not fall" as the adoption gate

**Fable said.** Layers are adopted when tuning rises and held_b does not fall.

**Data.** The held_b mean is exactly 0.462 at v7, v8, v9, v11, v12, v13 and v14, and 0.494 at v16, v17 and v18. `src/v24/fires.py` (built 2026-11-17 for this point) counts, per version, the papers whose rows changed from the version before:

| Version | dev (54) | held_a (28) | held_b (27) |
|---|---|---|---|
| v8 sections | 0 | 0 | 2 |
| v9 legend names | 2 | 2 | 3 |
| v11 name parts | 2 | 1 | 1 |
| v12 continuations | 1 | 0 | 0 |
| v13 one-species | 4 | 3 | 0 |
| v14 listed tags | 2 | 0 | 0 |
| v24 units | 26 | 12 | 14 |
| v24 account + row labels | 0 | 0 | 1 |
| v24 relevance | 25 | 12 | 4 |

From v8 to v14 every layer touched at most 4 dev papers. v12, v13 and v14 changed no held_b paper, and v8, v9 and v11 changed one to three held_b papers without moving their score. Within v24, relevance's "written once per species" and the row labels acted on no tuning paper.

**Verdict: Change** (a new point the data shows; Fable did not make it). "Does not fall" was passed mostly by default: several layers did not reach held_b at all, and the rest reached a handful of papers. The gate checks for harm but cannot show generality. `fires.py` now reports where each layer acted per group (held_b and grit-only as totals), and every run should be read with it.

## 3. Row F1 cannot see several kinds of change

**Fable said.** The unit is not in the pairing key; GT conventions differ between papers; the scorer's name pairing is noisy; one paper is under 1% of the mean.

**Data.**
- The units layer put a unit on 47,679 dev rows, and F1 moved only from 0.756 to 0.769. Noriega2023's unit agreement went from 0 to 31,161 of 34,617 matched rows with F1 unchanged (0.679).
- GT conventions, checked in the files: Ji2024's GT gives "mm" to 5,184 rows while the paper prints "mm" once, for precipitation. Noriega2023's GT recorded species-level biomass in "mm" (fixed to g, 4dfa8f90). Khayati2024 keeps category columns as printed while Viza2023 converts them.
- The scorer compares units as exact text: "grams" ≠ "g", and a printed unit where the GT is blank counts against us (`evaluate.py`, field-level accuracy).
- One tuning paper is 1/82 = 1.2% of the tuning mean, and 0.7% of the grit mean. Fable's "under 1%" holds for grit only.

**Verdict: Confirm,** with the share corrected. The recommendation stands, and the audit shows it works: decision keys scored where the decision is made, and a precision sample of output rows.

## 4. The table is read as patches on a per-column tag

**Fable said.** About fifteen layers each repair one failure class. Six questions ask "what is a row" in different ways. Answers clash and need "lift" machinery. The head reader's parts are flattened and later split again. Answers are cached by table position.

**Data.**
- `plan()` in `full_run_v24.py` applies 15 layers, and the assembled row reads `fields[column]`.
- The six questions and their option sets are as Fable quoted them, checked in the code.
- Renoz2020's one table was asked Q-KIND ("sampling", 0.979), Q-ALSO ("no", 0.964) and Q-ALSO2 ("no", 0.887).
- `head_to_table._header` joins groups, name and details into one string, and `name_parts.column_parts` reads the head reader's parts again.
- Answers are keyed by `str(table_index)`, and Figueroa2021 scored 0 from stale positions until it was re-read in a fresh root.
- On Viza2023 (corrected in the Fable revision), RU and RL under "Iberian Peninsula Range" became Yes / No while RC, with the same 0 / 1 values, stayed 1.0 / 0.0.

**Verdict: Confirm.** The table model Fable proposes is still a hypothesis: no data yet shows it would recover the losses. Section 13 says how to test it.

## 5. "A sure answer is not a reliable answer"

**Fable said** (as revised on 11-17 with the audit). One threshold is used for questions of very different reliability.

**Data.** Sure answers (p ≥ 0.8) wrong against a key that does not come from the model, every case checked by hand:

| Question | Sure | Wrong | Real errors after the hand check |
|---|---|---|---|
| Organism column | 182 | 0.5% | 1 |
| Column tags, GT columns | 699 | 1.0% | 7, all real |
| Head reader, weakest head cell | 152 | 3.9% | human key |
| Relevance Q-COL, GT trait columns | 377 | 5.6% | 21, all real (12 are CamargoVanegas2024's SD columns) |
| Long or wide | 29 | 6.9% | 2 |
| Table kind | 97 | 7.2% | 7, all real |
| Head reader, first record | 182 | 9.3% | human key, whole-table verdict |
| Decoder | 108 | 26.9% | 21 real (19%); 8 are key wording or GT conventions |
| Units from a legend row | 17 | 35% | 6, all real |
| Units from the methods | 33 | 0% | |

**Verdict: Change.** The narrowed claim holds, but its emphasis should move. The base column tree, the organism column and the head cells are well calibrated, and they are the parts every later layer stands on. The weak answers are concentrated in a few places, each with a nameable cause:
- **The decoder** accepts legend entries from numbered lists in running text. Viza2023's "(1) they originated in the tropics" and Vidal2023's "fire occurred 0 to 4 years ago" were both applied to trait codes.
- **Table kind** fails on tables that mix traits with counts or statistics.
- **Relevance's "statistic of an analysis" option** catches a trait's SD columns.
- **The legend-row unit source** reads data rows of other tables.

One row of the table should not be read as calibration: the head reader's first record. Its key is your verdict on the whole table, so a wrong verdict may come from any answer in it.

## 6. Thresholds from the curves, and the decoder threshold what-if

**Fable said** (in the 11-17 revision): set the threshold per question from its curve, and give the decoder a threshold, tested by a what-if on the saved answers. In my last message I proposed running that what-if at 0.8, 0.95 and 0.99.

**Data.** For each question: its sure-and-wrong answers, how many of them sit below 0.95 (so that a 0.95 threshold could remove them), and how many right answers sit between 0.80 and 0.95 (which a 0.95 threshold would remove too):

| Question | Sure-wrong | Of them below 0.95 | Right answers 0.80–0.95 |
|---|---|---|---|
| Column tags | 7 | 6 | 96 |
| Decoder | 29 | 14 | 16 |
| Head reader, head cells | 6 | 5 | 28 |
| Head reader, first record | 17 | 5 | 23 |
| Organism column | 1 | 1 | 10 |
| Table kind | 7 | 3 | 7 |
| Units from a legend row | 6 | 4 | 0 |

For questions where only some answers act, the cost has to be counted on the acting answers alone:
- **Table kind:** 12 non-traits answers sit between 0.80 and 0.95 across all tuning tables, and only 3 of them are known errors. The other 9 cannot be judged by the key.
- **Relevance:** the 12 SD-column errors are among 33 "statistic" answers between 0.80 and 0.95.

The decoder adds a reason specific to it. Reverting a wrong decode leaves the printed code, which does not match the GT's term either, so it gains no match. Reverting a right decode loses one. A decoder threshold can only keep F1 level or lower it.

**Verdict: Deny.** The audit already answers the threshold question, and no what-if is needed:
- For the decoder, column tags, head reader and organism column, a higher threshold costs more right answers than it removes errors.
- For table kind and relevance, it trades known errors for an unknown number of right drops.
- Most of the costliest errors (Q-KIND at 0.96 to 0.997, the decoder's Viza2023 and Vidal2023 cases at up to 0.97) sit above any workable threshold.

The one place a higher bar is free is the legend-row unit source (4 of 6 errors below 0.95, no right answers there). Even there, limiting the source to code tables is the actual fix.

**Advice.** Keep 0.8. Fix each weak question where its errors come from:

| Question | Fix | Kind of fix |
|---|---|---|
| Decoder | Reject a legend entry whose code is a list number inside a sentence | Evidence check, code |
| Relevance | Separate "a statistic of a trait (SD, SE, range)" from "a statistic of an analysis (score, loading, p)" | Question design |
| Table kind | The table-model nodes (section 13) | Structure |
| Legend-row units | Only rows of tables that define codes | Evidence check |

Each fix is measured by rerunning the audit, which takes minutes.

## 7. Prompts carry the dataset

**Fable said.** The base column tree's examples are copied from dataset papers, and the prompts say "about insects". Part of the tuning to held gap may come from here, so rewrite the base nodes.

**Data.**
- The copied examples are there: 'POLLENIVOROUS', 'Sarcophagidae sp.1' and 'Osmia cornuta' from OsorioCanadas2018; 'Ads.ger' from Korosi2022; 'Pterostichini' from Habustova2017; 'W/S' from AmbspergTraun1991.
- "about insects" is in `column_tree.py` and in both listed-tag reading prompts.
- But the audit shows the column tags are the best-calibrated question (1.0% sure-wrong).
- Section 1 shows the gap is zero papers, not accuracy on read papers, which is the opposite of what wording-led overfitting would produce.

**Verdict: Confirm, at Fable's priority** (your decision, 2026-11-17). I first proposed lowering it, because the audit shows no cost on tuning. That misses the point. The tuning papers are exactly where copied examples would not show a cost, since the examples come from them, so the audit cannot clear them. Wording copied from the dataset is the overfitting the project means to prevent, whether or not today's scores reveal it. The decoder notes still apply: rewording a tested question moves results by itself. So the rewrite is done one node at a time, old against new, on the synthetic suite and the decision keys.

## 8. Viza2023 and the category tables

**Fable said.** Viza2023's habitat and body-size tables are categories of a trait with fuzzy scores. We write 3,192 rows, zeros included, and score 0. The key table S3 is itself read as data. Three attempts asked one question for four decisions; the template mapping should be a separate policy.

**Data.**
- v18 writes 3,192 Viza2023 rows, 1,438 of them with value 0; v24 writes 3,024. F1 is 0.
- No row in either output comes from S3: no row carries S3's stage, trait-code or category columns.
- The attempts are as Fable listed them (v10 not adopted; v20 0 of 10 groups; plan 5 held back).
- The decoder writes "they originated in the tropics" into Viza2023's "1.0" cells in 9 columns (section 5).

**Verdict: Confirm the first part, deny "the key table is read as data".** That claim came from the code-tables design note, written at v15, and no longer holds. The four-decision analysis and the separate mapping policy stay as recommendations. The data cannot test them until they are built.

## 9. Module copies: "a standing source of silent divergence"

**Fable said.** Twenty-three version folders each hold a copy of about forty modules, so a fix must be made in every copy, and what was tested drifts from what runs.

**Data.** `column_tree.py`, `head_tree.py`, `decoder_v2.py` and `full_run.py` are identical in all 24 folders that hold them. `kind_tree.py` has two versions, split cleanly at v13 (v7–v12 against v13 onwards), and `species_tree.py` has two, split at v11. Both splits are deliberate changes at a version boundary.

**Verdict: Deny the divergence.** The copying costs space and attention, but there is no sign of silent drift.

## 10. No explicit uncertainty or provenance in the output

**Fable said.** "Not sure" means an earlier reading stands, and nothing in the CSV says which answers produced a row.

**Data.** `CSV_FIELDS` has no provenance or resolved / unresolved field. Every hand check in this audit had to trace a row back through the decision files.

**Verdict: Confirm.** This is code-only work, and it would have made the audit's hand checks much cheaper.

## 11. Evidence retrieval is uneven

**Fable said.** The legend inventory (built once by gemma) filed Noriega2023's legend table under the code "S5, S6", and nothing noticed.

**Data.** Confirmed for Noriega2023. The audit adds the opposite failure, entries accepted that are no legend at all:
- Viza2023's "(1) they originated in the tropics" was taken as code 1.
- Vidal2023's numbered fire-age classes were applied to worker polymorphism, nesting site and foraging strategy, 9 sure answers.
- Uemori2022's nesting position "1" became "North of Hokkaido".

**Verdict: Confirm, and strengthen.** This is the largest single source of sure-and-wrong decodes. The check is structural (section 6) and should come before any new decoder question.

## 12. "About 17 to 19 zero papers cannot be reached"

**Fable said.** That many zero papers have GT not printed in the parsed text, and should be reported apart, not chased.

**Data.** The figure is a grit count from v12 (2026-10-29). Today, 7 tuning papers are at 0 in v24's table run:

| Paper | Why it is at 0 |
|---|---|
| Ustjuzhanin2024, Xia2022, Xu2024 | Prose papers: their rows come from the prose reader, scored in the combined run |
| Harmon2013 | The GT holds exponentials of the printed logs |
| Chichorro2022 | The table is too wide for the head reader; `head_wide.py` is built but has not run |
| Renoz2020 | Table kind "sampling" at 0.979 |
| Viza2023 | Category columns (plan 5, held back) |

held_b has 8 zero papers, counted only.

**Verdict: Change.** Replace the old count with this list. Only Harmon2013 is truly out of reach; the other six have a step that would reach them.

## 13. What to do next, in the order the data supports

Fable's order was: calibration, synthetic suite, old against new wording, table-model tree, category groups, fresh test set, precision sample. Changed as follows:

1. **The audit-led fixes of section 6**, each re-audited and scored on tuning:
   - the decoder's legend-entry check (expected: Viza2023 and Vidal2023's sure errors gone, no right decode lost);
   - relevance's split "statistic" option (expected: CamargoVanegas2024's SD columns kept);
   - legend rows limited to code tables (expected: the 6 errors gone, Noriega2023's 31,161 agreeing rows kept).

   These are small, general and measurable now.
2. **Report where each layer fires** (section 2): papers and tables per group for every run. Without it, a held_b result says little.
3. **The synthetic table suite** (Fable's 2), designed in full before any of it is built. Section 1 makes it more important, not less. New papers fail by being shapes nobody has built for, and the suite is the only development data with unlimited shapes.
4. **Rewrite the copied examples** (Fable's 3, kept at its priority): one node at a time, old against new, on the suite and the decision keys (section 7).
5. **The table-model tree as a parallel reading** (Fable's 4), first for table kind, the question with the costliest sure errors. Test it on the suite, then compare with today's answers on tuning.
6. **Chichorro2022 through `head_wide.py`**: built, never run. One run decides whether it reaches the paper.
7. **The fresh test set** (Fable's 6): unchanged. It remains the only real test.
8. **The precision sample** (Fable's 7): unchanged.
