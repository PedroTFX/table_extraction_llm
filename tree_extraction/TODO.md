# TODO — tree_extraction

## Done (frozen in `src/head_tree.py`, 2026-10-08)

1. **Head reader frozen** with:
   - Q1 variant B (one first-record question on whole rows) — 49/51 first records held-out
   - experiment 1, `HEAD_CONTINUE`: head rows below non-head rows → nimble asked whether
     the head begins/continues there — names 134 → 139/181 held-out
   - title check, `SPEC_TITLE_STEP`: before Q-SPEC, "is this spanning cell a title, or a
     label for the columns under it?" — Uemori captions become titles, score unchanged
   - Q-SPEC with the labels written into its 3 options (column names / specification /
     together); the 4-option version (`SPEC_TITLE`) was tried and not kept

## Head reader: the person's table-by-table check (2026-10-13)

- Page: header_review.py + header_review_template.html -> artifact
  https://claude.ai/artifact/1msSwnuebjNx6F6gFxAM5f (db collections reviews, reviews_r2;
  answers saved in output/header_review/answers*/). 263 tables of the 30 bench papers.
- Round 1 (frozen reader, step_on.json): 222/263 right (84%).
- Round 2 (head_round2.py -> round2.json, all tables re-read; switches SECTION_CELL,
  EMPTY_GROUP_RECHECK (QG), SPEC_STATS): 238/263 right (90%). On the 60 tables whose
  reading changed: 23 fixed, 4 broken. The person's marks moved on 7 of 203 unchanged
  tables (~3% marking noise).
- Round 3 (head_round3.py -> round3.json, a PATCH on round 2: only new questions, so
  untouched tables keep their reading; rule from the person: right tables must not
  change). Judged by me against the notes:
  - QG narrowed ('section' only for a cell alone in its row) — KEPT: Derhe t3, Graf
    t12, Odanaka t4 fixed as the notes ask; Uemori t4 -> title (note: column name);
    no right table changed. Now in head_tree.empty_groups.
  - QL (a lone cell in the last head row: section?) — REJECTED by the rule: fixed Graf
    t7, Rebrina t2, but changed 4 right tables (Barber t5 '2013', Derhe t2 'Species
    metrics', Guareschi t6 'Taxonomic diversity', Leong t6 'Both habitats') — all of
    them sections by the person's own notes on identical rows (Guareschi t1). Kept in
    experiments/round3_with_ql.json in case those marks are revised.
  - Page now shows row verdicts between head and first record and sparse body rows
    (Graf t8's 'Andreninae/Calliopsini' were already read as sections; hidden before).
  - Expected standing: 241/263 (round 2 + 3 QG fixes), not re-checked by the person.
  - Full re-run with the QG fix (round3_full.json): the fix did what the notes ask
    wherever it fired (7 wrong tables now match), but nimble's drift between model
    loads changed 12 right tables -> 233 vs 238. The person chose: KEEP VERSION 2
    (round2.json; head_tree.py defaults = its switches, QG_SECTION_ALONE off) and move
    on (2026-10-13). An answer cache (reuse stored answers for identical questions)
    would stop the drift; not built.
- Still wrong: specification vs together for statistics (Gossner t2/t9/t11; wording
  attempts move nimble the wrong way), Figueroa t2, Tonelli t5, Guareschi t3, row-label
  tables (Korosi t3, Nunes t2, Habustova t0), Braschler t1 first record, Uemori t4,
  Espinosa t7, HTML conversion errors (Rebrina t0 shift, Gossner t2 span, Tsai).

## Chain: head reader v2 -> column tags -> decoder (2026-10-13)

- Tags on v2 tables (head_column_bench --variant reader2_v2): GT-used 212/237 (89%) vs
  head reader 1's 223/244; held-out 136/145 vs 140/145. 7 of the missing columns are
  OsorioCanadas t10 (v2 reads it headerless -> joined as a continuation); the other
  3 differences look like column-tree drift (Kovacs t4, Torok t8, Uemori2021).
- decode_chain.py (decoder_v2 on the chain's own columns: tags measurementType /
  measurementValue, head-reader headers, records minus section/note rows; the key is
  used only to score, 'not reached' when the chain never decoded a key column):
  30 bench papers, 247 trait columns: coded 1286/1325 reachable rows right (97%; 12
  with unit inside), 0 not reached; kept 2676/2702. Same as the key-fed decoder on
  these papers — but only 8 coded papers (the decoder's original dev set).
- All key papers (PAUSED 2026-10-13 during the decoder's nimble stage): head_more.py
  read 494 tables of 47 more papers -> experiments/reader2_all.json (3 skipped as too
  big for the reader's view: Chichorro2022 t9 881x113, Noriega2023 t6 763x290,
  Vidal2023 t6 141x50 -> reader2_more_skipped.json); tags done (head_merge/
  reader2_all.json); decoder organise done for all 77 papers; match done for 57/77.
  Schirmel2012's table is rotated by head_to_table -> 0 trait columns (its key column
  will be 'not reached').
  RESUME: cd tree_extraction/src && python decode_chain.py match && python decode_chain.py score
- DONE (2026-10-13). Coded rows right / reachable, chain vs key-fed decoder v2h:
  8 dev papers 1286/1325 vs 1258/1293 (97% both); 25 other coded papers 3391/5206 (65%)
  vs 4165/5191 (80%). Kept rows 15802/15968. Losses, nearly all in 4 papers:
  - Teder -365: gemma copied the code into the term ('G = grasses') and QB kept it —
    a parse slip code can strip (a term starting with its own code and '=' / ':').
  - Guariento -378: 'Adult feeding' '0' kept as printed; same header, but gemma read
    different passages so the legend list differed — run-to-run variation.
  - Normandin -34: gemma's uncoded-category pass lost 'polylectic' (same variation).
  - Kratschmer -38 'not reached': the tagging bench only tags tables the GT draws on;
    Kratschmer's species are printed as abbreviations ('taxa_abbrev'), so its tables
    were never tagged — a benchmark shortcut, a real chain tags every table.
  Gains: Wölfling +39, Uemori2022 +18, Arnan +4.
- Fixes (PAUSED 2026-10-13 at the start of 'tag'): decoder_v2.strip_own_code ('G =
  grasses' -> 'grasses'); decode_chain 'tag' (tables of the 33 coded papers the bench
  left untagged, every column asked), 'refresh' (clears organise+match only where trait
  columns changed, match only where a saved term held its own code). Results before
  the fixes: output/decode_key/chain_before_fixes/. Tagged so far: AmbspergTraun1991.
  DONE 2026-10-14 (+ head_to_table: never rotate a table of > 100 data rows — Noriega t5,
  1141 sampling rows, had become 950 'trait' columns; every right rotation has <= 33).
  Coded rows right: dev 1263/1325 (was 1286), other 25 papers 3691/5191 (was 3391; key-fed
  4165). Teder 2431 -> 2843/2844 (strip works); Kratschmer reached but 3/38 (gemma lost
  'Ground nesting'); Taillefer +12, Habustova +4. NEW LOSSES from re-running gemma with
  many more columns: Espinosa 27 -> 0 (passages 795 -> 4625 chars, gemma lost 'og'),
  Uemori2022 40 -> 0 (a term spanning two passages: '... feeding on [prose] Hemiptera'),
  Wölfling -69, Wallon -16. Lesson: gemma's legend list moves with whatever passages it
  gets. Proposed: (1) parse check — a term may not cross a passage marker; (2) a paper-
  level legend list built once from legend-like passages, independent of the columns
  asked (same input every run; chain and key-fed share it). Results before the fixes:
  output/decode_key/chain_before_fixes/.

## Legend inventory (2026-10-14, agreed with the person's pasted review) — PAUSED

- legend_inventory.py: per paper, fixed source units (legend-like prose paragraphs:
  >= 2 definition shapes; table footnote rows; small tables in 10-line pieces), never
  chosen by the decoded columns; batches of <= 3000 chars in document order; gemma
  passes A (legends) + C (categories without codes) per batch, B (category names) per
  paper; BOUNDARY CHECK: code and term printed in the SAME unit, terms carrying a unit
  marker rejected; own-code strip. Each entry keeps its unit id.
- Coverage check (code only): 118/125 printed key pairs sit inside one unit; the other
  7 are categories named without a code (Kratschmer, Normandin, Teder 'LP', Uemori '2').
- Size: 33 coded papers, 235 batches (~470 gemma calls, ~1-1.5 h). BUILT 2026-10-14
  (output/decode_key/inventory/). Inventory quality (code only): dev 20/20 printed legend
  pairs, other papers 85/102 (missing: Wallon one-hot 0/1, Keller joined codes, Normandin
  polylectic/oligolectic, Kratschmer 'Above-ground nesting', Guariento 'Adult feeding' '0',
  Uemori2022 '2'/'3', Taillefer 'S', Teder 'LP', Vidal '0.0'; Wallon 'CC' is a scoring
  shortcut — captured() is called without the header, so the prefix rule can't apply).
- decode_inv.py DONE 2026-10-14 (inv_key/, inv_chain/, inv_SCORE.txt, inv_ESPINOSA.txt):
  - INVARIANCE PASSED: Espinosa, one inventory (70 entries): 5 columns -> 27/27, 19 -> 27/27.
  - Three scores (species rows): inventory dev 100%, new 88%; matching (nimble picks the
    entry when the inventory has it) dev 73%, new 83% key-run / 77% chain-run;
    end-to-end dev 73% (was 95-97%), new 73% key-run (v2h key-fed 80%), 68% chain-run
    (was 71%).
  - Why matching fell: the paper-wide inventory gives a short code candidates from
    several legends (Graf 'A' 4 vs 2, 'S' 3 vs 1) and nimble keeps them as printed
    (Graf 781 -> 468, Habustova 16 -> 5, Wölfling chain 202).
  - Proposed next: QL by SOURCE UNIT — per column, nimble picks which legend passage
    (the inventory's unit, quoted) defines its codes, then QV offers only that unit's
    entries. Grouping from the paper's passages, not gemma's labels; inventory stays
    fixed; one extra nimble question per column, no gemma re-run.
- decode_units.py (QL by source unit, options: units + 'several' + 'none'; agreed with
  the person's pasted review) DONE 2026-10-14 (units_key/, units_chain/, units_SCORE.txt,
  units_ESPINOSA.txt):
  - Espinosa invariance: 27/27 with 5 and with 19 columns, same passage chosen per column.
  - dev: passage choice 10/10, matching given the right passage 97%, end-to-end 97% (was
    73% with the plain inventory), kept 100%.
  - other 25: passage choice 83% key / 80% chain (columns); matching given the right
    passage 81% / 78%; end-to-end 55% / 52% (plain inventory 73% / 68%; v2h key-fed 80%);
    kept 99%. Production comparison, rows production reaches: 71% vs 70%.
  - Gains where papers have look-alike legends: Graf 468 -> 781, Arnan 45 -> 90,
    Kratschmer 27 -> 38, Wang 27 -> 32. Losses from 'none' on a right passage: Teder
    'Larval diet breadth' (the ONLY passage offered was right) -710, Guariento pupal +
    adult feeding, Uemori 'Soil dependence', Wallon 'Mode of Ingestion'; 'several'
    pulled Wölfling's food legend into habitat (-203).
  - ADJUSTED (composed from saved answers, no model calls, units2_key/ units2_chain/):
    QL only when >= 2 passages are offered; 'none' / 'several' fall back to the plain
    inventory candidates (the inventory run's answer for that column is exactly that
    question). End-to-end: dev 97%; other 25 papers 73% key-run / 68% chain-run (plain
    inventory 73/68, passage choice 55/52, v2h key-fed 80); kept 99-100%. vs production on
    rows it reaches: key-run 82% (= v2h), chain-run 71% vs 70%. Caveat: answers from two
    nimble sessions combined; a clean re-run would confirm (~30-40 min, nimble only).
    Remaining gaps: matching vs v2h (73 vs 80) and the chain's upstream cost (68 vs 73).
  - Proposed (waiting on the person, it changes the review's 'none' design): (1) no QL
    when only one passage is offered (QK + QV's 'keep' still guard); (2) 'none' and
    'several' fall back to the plain inventory candidates — QL only narrows when it
    picks one passage. Nimble-only re-run of both runs, ~30-40 min.
- Asked by the person: could matching be deterministic? Measured on v2h: 15,308 rows
  already are (no candidate -> kept, no question); a 'one candidate -> take it' rule
  would decode ~2,430 coded rows right (nimble ~2,700) but wrongly change 1,428 rows
  that must stay as printed; 4,355 rows have 2+ candidates (which legend for this
  column — semantic). A narrow auto-accept slice is possible only if the person relaxes
  'model decides' for provably unambiguous cases.
- Then: match with the inventory (chain columns AND key columns), Espinosa invariance
  test (5 vs 19 columns -> identical inventory, the 27 rows survive), and three scores
  apart: inventory quality (key pairs captured), matching quality (nimble picks the
  right entry when it is there), end-to-end; inspect Wölfling, Uemori2022, Teder,
  Kratschmer, Noriega. Remaining source of variation: gemma across separate runs —
  limited by bounded units, fixed prompts, and the cached inventory.

## Next

2. **Ask Q-SPEC questions one at a time**, not batched with other questions.
   Why: the decision endpoint does not score questions independently — Oliveira's M|V
   question gave specification 0.75 alone, 0.92 batched with 5 row questions,
   column names 0.50–0.60 batched with the "Traits" question. Costs a few calls.
   Does not fix the drift between sessions (see 3).

3. **Mark close answers "unsure"** (top probability below ~0.7) in the output instead of
   trying to settle them.
   Why: within one session nimble is deterministic (same input → identical answer), so
   asking 3 times and voting gives the same answer three times. Across model reloads the
   same prompt drifts (Oliveira M|V: 0.83 spec, then 0.60 / 0.52 / 0.50 column names).
   Answers above ~0.9 held in every run; 0.5–0.75 can flip. Don't use a single-call
   probability as a confidence downstream; pass "unsure" on to the meaning step / review.

4. **Meaning step** — in progress (2026-10-10). Frozen: meaning v2 (`meaning.py`
   read_label: one nimble question per abbreviation token, candidates from the paper's
   own definitions, parse checks, fuller quotes). Validated score (held-out direct
   match): **160/181 (88%)**, from 139. Synonym judge (`meaning_bench_v3/v4.py`):
   3-way (same / different / value, not name) + whole-label eligibility gate (v4):
   0 false positives on unrelated / body-value / same-initial decoys held-out, the 7
   hand-checked synonyms kept, Oliveira's low-information labels unresolved —
   synonym-adjusted 167/181 (92%) stays PROVISIONAL (same-initial decoys: 3 per set).
   Original note:
   (legends and abbreviations → what a column means).
   Why: 31 of the head reader's 47 held-out name misses are names printed as
   abbreviations or other wording (WL vs "Weber's length", Dry tolerant vs Drought
   resistance); gemma and code-only miss the same ones. M/V as statistics (mean,
   variance) also belongs here: the legend says so, Q-SPEC wording can't settle it.

5. ~~Merge with the column tree~~ — **done 2026-10-09, head v2 is the merged input.**
   `head_to_table.py` builds the column tree's table from the head reader (names =
   groups + name + details; section / repeated-header / note rows dropped; headless
   continuations joined); v2 adds context lines (title, section labels, head-row
   values). `head_column_bench.py` scores it (output/column_tree_bench/head_merge/).
   Held-out (19 papers): GT-used columns 140/145 vs 141/145 on gemma's tables;
   unused columns left as none 67% vs 48%; 473 s vs 531 s.
   Notes for the record:
   - the key (`derive_labels`) is value-based except ~7 labels decided by header text
     (rank headers; "header names a GT trait" when value pairs are weak)
   - identical header lists are scored once (same rule as column_tree_bench): this
     measures the mappings the pipeline would reuse, not every physical table
   - rotated tables (maybe_transpose) keep only the title as context; row/column
     lines are dropped (fix 2026-10-09, changes nothing in this benchmark)
   - the 11 non-held-out papers trail (84% vs 90%), mostly Tsai2020, where the HTML
     lost the site labels' colspan — a conversion issue, see below

## Still missing for extraction (2026-10-11, with the user)

- **Which tables/columns to extract** — belongs in the column tree's tag assignment
  (a table whose columns all tag 'none' gives no rows), not a separate step.
- **Traits outside tables** (prose, supplementary files) — still to do.
- **End-to-end score** — already done by the main extraction program (evaluate.py):
  the tree parts plug into it, they don't need their own.
- **Cell splitting** — next candidate: a value tree (see the design in the chat of
  2026-10-11).
- Still open from the list: decoding cell CODES via legends (Graf 'SO', 'G'; coded
  names 1–10), and species in hard places (single-species papers, sections).

## Decoder v1 (`src/decoder.py`, 2026-10-12)

- gather (code: paragraphs naming the column's code-shaped values in any printed form,
  table footnote rows, small tables) → gemma e4b lists legend entries {variable, code,
  term} → code keeps an entry only if the term is printed with the code near it (a
  near-miss quote is replaced by the printed phrase: 'narrow' → 'narrowly') → nimble
  QK "code, or a word the paper explains?" → QV "which definition, or keep", options =
  entries whose code is printed like the cell ('1.0' / '(1)'). Gemma phase cached and
  unloaded before nimble runs.
- Dropped before running: a per-column "which legend" question — gemma's variable
  labels don't group (Korosi's M / O / P came back as three legends).
- Dev (the 8 coded papers of the 30-paper key): coded cells a decoder can reach
  1258/1293 right (97%; 16 of them with the unit still inside: Habustova '6–10.9 mm',
  GT keeps the unit apart); kept-as-printed cells 799/799. Production on the same:
  85% of the cells reaching it. Out of reach: GT terms not printed in the paper
  (Uemori 'hyper predator', Wang's C/O/M/B with no printed legend), Derhe's GT typos.
- Open: Uemori '1.0' kept (0.985) while '2.0'/'3.0' decode; Graf 'NA' → 'not
  specified' kept (debatable: NA is also 'missing').
- HELD-OUT (--all key, 25 new coded papers, 2026-10-12): kept cells 15130/15169;
  coded cells 3270/5684 reachable (58%), pairs 62/110. Dev (97%) did not carry over.
  Same papers where production makes rows: production 466/2105, v1 378/2105 — v1
  is WORSE (Arnan 150 vs 78, Lizee 41 vs 24, Taillefer 50 vs 40, Ambsperg 32 vs 26).
  v1's 2892 extra right cells are Teder & co., where production makes no rows at all.
  Held-out misses by stage (pairs): QV other term 21, gemma no entry 14, gather 9,
  QV keep 6. Causes, to fix in v2:
  1. term boundary: GT takes the category label, gemma copies the explanation
     ('species that are primarily monogynous' vs 'primarily monogynous'; 'none (only
     defence of the nest)' vs 'none'). Production asks for a "clean canonical label".
  2. codes never printed next to their term — the code is the term's initials
     (Kratschmer G/A/P, Normandin P/O, Wang C/O/M/B): offer initial-matching entries
     when no same-form entry exists; nimble decides.
  3. code forms '→1' and legends inside wider/same tables (Wölfling).
  4. 0/1 → No/Yes is a GT convention with no printed legend (Vidal, Gathof,
     Guariento): `where` calls it 'same sentence' by accident — score as no legend.
  Outputs: output/decode_key/{all/, decoder_v1/, prod_rerun_all/}.

## Decoder v2 (`src/decoder_v2.py`, FROZEN 2026-10-12 as run v2d) — v1 kept as baseline

- Key corrected first: a 0/1 code whose GT term is yes/no counts as printed only in a
  definition shape ('1 = yes'), else 'not in the paper (binary convention)' (12 pairs).
  v1 rescored on it: decoder_v1/SCORE.txt (original: SCORE_original_key.txt).
- v2 = v1 plus: retrieval (code forms strip arrows/footnote markers '→1', '†S'; small
  tables in 10-line pieces, 4000-char budget); gemma pass A = v1's legend prompt, pass
  B = category name inside each printed term (kept only if a contiguous piece), pass C
  = categories named without codes; initial-based tier (only when no code is printed
  like the cell; marked 'initial'); QB (nimble picks the wording: label / whole term /
  cut at first bracket-comma); explicit QK/QV = v1's wording exactly.
- Iterations, all on the same papers (so all 69 are development data now):
  v2a one 4-field gemma prompt — garbled legends (codes in 'label'); v2b three passes
  but QV reworded without the code — nimble kept codes v1 decoded; v2c v1's QV, but QK
  context reworded — nimble called 'D', 'GO', 'A' words (0.92-0.98); v2d v1's QK.
  Lesson: nimble's answers move with wording at 0.7-0.98; reuse tested questions.
- v2d vs v1 (corrected key, all 69 papers): coded cells 5321/6520 (82%) vs 4528/6448
  (70%); distinct codes 91/126 (72%) vs 83/126 (66%); v1-dev unchanged (97%); kept
  cells changed 65 vs 39 (Rebrina 'chortobiont' -> its definition; Teder 'G(i)').
  Initial tier: 6/6 codes, 161 cells right. 'Longer wording' (GT words inside the
  decoded term) reported apart: +295 cells.
- vs production where production makes rows: v2 595, v1 378, production 466 / 2105 —
  but v2's lead is Wölfling (218) + Uemori2022 (22); without them production still
  wins (Arnan 150 vs 76, Lizee 41 vs 19, Taillefer 50 vs 40): term-boundary choices.
- NOT a generalisation estimate: every GT paper with a key column has been looked at.
  A final test needs new GT papers (9 folders have no GT yet: Boetzl2024, Cawood2026,
  DawesGromadzki2008, GarciaAtencia2024, Nelson2021, Shi2022, Stemkovski2020,
  Sultaire2021, Zhang2022).
- Outputs: output/decode_key/decoder_v2/ (match = v2d; *_v2a/_v2b/_v2c kept).
- Same-rows comparison with production (decode_compare.py, v2d): rows production
  reaches with a printed legend: production 1651/2366 (70%), v2d 1835 (78%); all
  printed-legend rows: production 26% (3943 rows never reach its decoder), v2d 81%.

## Decoder: working on the remaining coded values (PAUSED 2026-10-12)

- decode_misses.py: remaining decodable misses of a run by stage (gather / gemma /
  not offered / QK / QV keep / QV other / QB wording), species rows.
- v2e (decoder_v2e/): code-side fixes — candidates de-duplicated by printed term (not
  label), column header = all header texts over the body cell's span (Lizee's shifted
  colspans), small tables printing >= 2 values as whole cells gathered first (Wölfling).
  organise reuses cached gemma results when the passages are unchanged (`--out NEW PREV`).
  Gained Lizee RS/TS, Wölfling, Arnan; lost Guariento 'Adult feeding' (18 legends for
  '0' cut at 15 options) and Forrest 'poly' (gemma drift: pass C dropped 'polylectic').
- v2f (decoder_v2f/, best so far): QV batches >15 candidates (nimble picks per batch of
  10, then among winners). Coded cells 5391/6484 (83%), distinct codes 95/126 (75%);
  kept changed 65 cells. Legends reused from v2e, nimble only.
- v2g: scoring made symmetric — 'right, shorter wording' (decoded term is a piece of
  the GT's) beside 'longer wording'; the GT cuts explanations in Keller/Arnan but keeps
  bracketed examples in Wölfling, so no wording rule fits both. Prefixed code forms
  ('IngCC' printed, 'CC' in cells, prefix starts a header word). No gain alone: the
  column had no header.
- v2h (decoder_v2h/, BEST, 2026-10-13): headerless continuation tables (26 key columns:
  Wallon t28, Taillefer, Beyer, Weber, Torok...) take the column header from the nearest
  earlier table of the same width that has one. Coded cells 5423/6484 (84%; 96% with
  wording boundaries forgiven), distinct codes 97/126 (77%); kept changed 65 cells.
  Same rows production reaches: v2h 1941/2366 (82%) vs production 1651 (70%).
- Remaining decodable misses (species rows, decode_misses.py on v2h): wording boundary
  775 (Guariento 'No' 498 = GT decision; Wölfling 186 the other way), not offered 129
  (Wallon one-hot 'ActDay'/'FoodPl' 0/1 columns 64, Uemori '2' 50, Taillefer 'S' 14),
  QV keep 67 (Graf 'NA' 35, Arnan colony 20, Uemori '1' 12), QV other 56 (Arnan
  rewordings 36, Teder 'L' -> 'larva' 20), gemma 34 (Vidal 25, Keller joined codes 9).
  These are now small, paper-specific cases: more fixes here risk fitting these papers.

## Decoder (in progress, paused 2026-10-12)

- Done: `decode_key.py` (answer key from GT ↔ cells, 30 papers: 11 coded columns / 8
  papers, 38 legend pairs; reviewed exclusions Guareschi/Tonelli/Odanaka) and
  `decode_prod_rerun.py` (today's production step 4b on copies): 85% of the coded
  cells that reach it decoded right (Graf 776/832, Cappellari 325/325, Korosi
  104/104). Mistakes: not the paper's words (Espinosa 27, Graf spelling 40), code
  forms not matched (Uemori '1.0' vs '(1)', 107), deterministic finders find almost
  nothing (gemma does the work), unit inside the term (Habustova 16), no rows
  upstream (Wang, Derhe). GT errors: Graf 'highly eussocial', Derhe 'restold
  restorationation'. Results: output/decode_key/.
- Next: `python decode_key.py --all` (key over every paper with a GT; ~15–25 min,
  code only; it was stopped before finishing, nothing saved), review the new
  legends by eye, re-run production on the new coded papers, then build decoder
  v1: gather passages (code) → gemma organizes legends {code, term, label, quote}
  → code checks verbatim terms + normalises code forms → nimble matches legend to
  column / code to term, with 'none'.

## Full run, start to finish (full_run.py, 2026-10-14/15) — DONE

- All 109 GT papers -> tree_extraction/output/full_run/<paper>/<paper>.csv in production's
  columns, scored with evaluate.evaluate_all (run_all.py's settings) beside production's
  saved CSVs copied to output/full_run_production/.
- Done: head reader v2 on all 109 (reader2_all.json; 4 tables too big: Chichorro t9,
  Noriega t6, Vidal t6, MacDonald t4), tags on every table (full_run/tags + bench tags),
  meaning v2 on trait names (full_run/meaning), legend inventory for all 109
  (decode_key/inventory). Decode, assemble, score: all 109 (270,665 rows).
- Ollama auto-updated to 0.40.4 overnight and refused the old nimble format; fixed by
  pulling nimble:9b-q4_K_M (Apache 2.0) and re-creating nimble:9b-q4-gpu (see memory
  nimble-model-setup): Espinosa 27/27, 20/20 cell answers identical to the old model.
- Assembly limits to remember when reading the score: no value splitting ('12.3 ± 1.2'
  stays whole), no traits from prose, single-species tables without a species column
  give no rows, Graf's numbered columns become types '1'…'10'.
- Scoring with miss-severity grading OFF (ev.ASSESS_MISS_SEVERITY = False in stage_score):
  score-neutral, but it cost ~30 s per 20 misses (Brant2021 alone 14 min).
- Result (output/full_run/COMPARE.txt, full_run_compare.py): mean F1 tree 0.441 vs
  production 0.317 on all 109 — NOT a fair win: production's saved CSVs (commit b3a829c,
  2026-09-23 regeneration) are header-only for 42 papers that had rows on 2026-09-09
  (then mean F1 0.488 on 114). On the 67 papers where production has rows: mean F1 0.516
  both; scoped micro P/R/F1 tree 0.428/0.501/0.461 vs production 0.700/0.465/0.559.
  Tree's weak side is precision (Cerini2023 18,680 in-scope FP, Raine2018 20,240).
  On the 42 empty ones the tree scores F1 > 0 on 23 (mean 0.320).
- Failure groups of the full run (113,154 GT rows missed; 39 papers at F1 0):
  rows: trait not matched 49,517 (Noriega's long Trait/Measurement table read as wide
  columns; raw headers 'headlenth'), species not found 31,188 (Orr2024 alone 12,838),
  value differs 30,917 (Raine per-individual GT vs one value per species; Noriega GT
  rounded 0.006 vs 0.0055; Guariento trailing '.'), GT duplicates 1,532.
  zero papers: A single-species paper, species only in the title (11: Borges, Brant,
  Franzen, Kovacs2008/2010, Luo, Mirzaee, Oliveira, Orr, Tran, Tsai — production gets
  Brant 0.95, Kovacs 0.70/0.73); B wrong column as species (8: references Cao/Chichorro,
  higher taxa Teder/Quicke, genus only Cerini (21,680 rows), section label Gomez, epithet
  without genus Harmon/McCravy); C trait columns mis-tagged or header misread (7:
  Attiwilli, CortesGomez x2, Figueroa, Melo FG->caste, Orlofsk, Zhao); D values not
  cleaned (3: Ambsperg codes kept, Gibb letters 'cd', Cecala '[16]'); E traits in prose
  or no table read (8: Baine, Fondjo, Hill, Tonelli, Ustjuzhanin, Wijas, Xia, Xu);
  F wrong table (2: Viza predictor table, Renoz).
- Open: production needs a re-run on those 42 for a fair comparison (user to decide).

## Open, smaller

- HTML conversion loses colspans: Tsai2020 t1/t2 site labels ('Mt. Hehuan', 'Mt. Lala'…)
  sit over one column instead of their 3–6 column block, so only the first column of
  each block gets the site. Nothing downstream can recover it; check MinerU's output.
- Column tree on the merged tables: "Family" columns tagged measurementType / none
  (Ibarra2021, Tonelli2021) instead of identity.
- The column tree still uses code-measured cell facts (% numbers, Latin binomials,
  rank endings, header statistic regex) — the kind of code facts dropped from the
  head reader. Decide whether they stay.

- A fair held-out score needs tables nobody has looked at: Brasil2024 and Uemori2021
  became development tables when experiments 1 and the title check were made on them.
- Body rows (QB) still judge sparse rows from the first piece only, not whole rows.
- Barber2017: "Species" called a row label, "Site Year planted" a group — 3 wordings
  failed; next idea is a question triggered where cells were called values ("which cell
  names these values?").
- Korosi2022:0 first record: right only because the whole-row view fixed it; accepted edge case.
- Coded column names (Graf2021 1–10) are only flagged, not resolved.
- README: add head_tree.py, head_view.py, head_tree_exp.py and the `head` bench variant.

## GT decisions waiting on the user

- 1,351 life-stage rows recorded as measurementType in 6 papers (GT_REVIEW_CANDIDATES.txt):
  move to lifeStage? what measurementType/value would they get?
- The items in output/column_tree_bench/GT_ERRORS.txt.
- Sample size convention: does "how many were caught" count as a sample size?
