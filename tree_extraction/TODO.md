# TODO — tree_extraction

## Done (frozen in `src/*/head_tree.py`, 2026-10-08)

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

## Decoder v1 (`src/*/decoder.py`, 2026-10-12)

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

## Decoder v2 (`src/*/decoder_v2.py`, FROZEN 2026-10-12 as run v2d) — v1 kept as baseline

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

## Decoder v3 (decoder_v3.py, full_run_v3.py, 2026-10-17) — on top of the full run

- Output: output/full_run_v3 (baseline output/full_run untouched); COMPARE_V3.txt.
  Only what v3 changes is re-asked; every other column keeps the full run's answers.
- 1. Table footnotes (layout, not mark characters — the user: MinerU misreads the '†'
  marks, so v3 must not depend on them). A legend whose text starts directly below the
  table's '</table>' (table found in the markdown by its cell text; 119/843 reader tables
  don't follow markdown order) -> QV option says "printed in the footnote directly below
  this table" (mark_note hook). Only those cells are re-asked (11 papers). Ambsperg 0 ->
  0.984, same as the first try with the marks (kept as output/full_run_v3_marks).
  Jones 'Expert opinion' 1 -> 'medium' and Wiescher 1.00 kept: out of GT scope, F1 same.
- 2. Cells past the first 25 of a column are now asked (shown_values hook keeps the
  context). Gained nothing: those cells had no legend candidates (numeric columns). My
  first trace matched values across columns and overstated it.
- 3. Endings, one nimble question per column and shape: comparison letters ('2.87 ± 0.05
  cd') -> mark on Gibb, Borges, Eckert (0.99), units ('<5 mm') -> value (1.0) on Cao,
  Guareschi, Viza. Bracket numbers: the matching entry of the reference list printed
  after the table is quoted (geometry: Osorio's table is in S1 with its own list).
  Cecala 3/3 mark, Osorio 3/5 — 'PREPUPA [1-2]', 'BIVOLTINE [14-16]' still 'value'
  (ranges); not reworded to fit two columns. Gibb 0 -> 1.000, Cecala 0 -> 0.996.
- 4. v2.WHOLE_FIRST: 'W/S' printed as its own code is decoded whole (wood/soil interface),
  and a list of decoded codes becomes one row per part (GT does this: Ambsperg, Pereira
  +0.25). Derhe -0.058: its GT writes 'old restoration rainforest' as ONE value (two
  habitats) — GT inconsistency for the user to decide; Keller -0.009 (extra row).
- Mean F1 0.441 -> 0.470 (9 papers changed).
- Still open in the decoder: legends missing from the inventory (Wallon ActDay 0/1 =
  night/day, Guariento pupal stage, Viza fuzzy 0/0.5/1, Kratschmer/Forrest 'pl'/'poly'),
  GT binary convention Yes/No vs the legend's term (Guariento).

## Species for tables without a species column (species_tree.py, 2026-10-17)

- One paper at a time: gemma reads a section (title+abstract, introduction, methods,
  results, discussion) -> printed species-level names + a summary of the paper's own
  study; nimble: gate per paper (one species / several) then, for 'one', per table which
  name (options frozen when the gate said 'one'). Unsure (< 0.8) -> next section. Clash
  (tables named differently) -> gate re-asked once, else names withdrawn.
- Checked against the GT (species_check.py, species_key.json): 86 right, 1 wrong, 0
  missed. All 9 single-species papers named right; Kratschmer2019 WRONG ('honey bees':
  the methods were read in 3000-char pieces and one piece's summary said the study
  compared honey bees -> gate 'one' 0.91). Fix to try: one gemma call per section
  (sections are <= 9000 chars). Borges2024 (single species) never reached: its species
  column is a wrong column (trait names).
- Mean F1 0.470 -> 0.476 (Kovacs2010 +0.36, Mirzaee +0.19, Tsai +0.16). Brant, Franzen,
  Kovacs2008, Orr, Luo, Tran get the right species but score ~0 for other reasons:
  Brant's data table t8 stayed open (0.68), Kovacs2008 '2.73^2 ± 0.09' superscripts and
  a traits-as-rows table, Orr's genotype loci tagged as traits, Franzen's GT table not read.
- Tables without species in multi-species papers (species_missed.py): 253/271 hold no GT
  species; exceptions: Pessoa2017 (species in the sheet heading above, 14 tables),
  Gibb2005 t4 / Cao2024 t5 (species as column headers), Dejean2019 t3 ('Label' tagged
  measurementType).

## Species-column questions (organism_tree.py, full_run_v4.py, 2026-10-18)

- Evaluation split frozen first (output/eval_split: split.json seed 20261018, 54 dev / 55
  held, baseline snapshot, DESIGN.md written before results, RESULTS.md). Iterated on dev
  only (6 iterations, each logged); held run once after freezing.
- Questions: Q-KIND (species / part / higher / other, section labels as context; unsure ->
  yes/no second look; still unsure -> tagger's call), Q-PICK, Q-GENUS (row by row, any
  column or the section labels), Q-UNITS (higher-only: one organism per row identified to
  that rank, or a group summary). Rejection is valid -> species step.
- Held: species columns right 80 -> 91/100, mean F1 0.470 -> 0.535, 7 improved, 0 regressed.
  Dev: 99 -> 106/124, 0.483 -> 0.511. All: mean F1 0.476 -> 0.523, 11 improved, 0 regressed.
- Lesson: genus-level GTs (Espinosa, Guareschi) — a 'higher' column can be the right one;
  the first species-column measure only matched two-word names and missed it.
- Open: challenge set (Gomez, Quicke, Borges, Pessoa, Gibb t4, Cao t5, Dejean t3), Renoz t1,
  Braschler t6/t7, Kratschmer species step (one gemma call per section).

## Trait-column questions (trait_tree.py, full_run_v5.py, 2026-10-18) — NOT adopted

- Same split and rules; 4 dev iterations (accept rule set before the last), frozen as the
  conservative variant (drop identifier / organism / other, no long reading), held run once:
  mean F1 0.535 -> 0.532, 3 regressed (Fiedler 'Associated_ants' called organism; Scalercio
  flight months called other). v4 (species-column questions) stays the best version.
- What it showed: column ROLE questions misfire on traits whose values look like organisms
  or dates; long-format reading needs a confirmation (trait names) and must not drop the
  other columns (Russo's two-species-per-row table); the scorer's gemma type remap is noisy
  on big papers. Noriega2023's long table (the biggest single loss) remains unsolved.

## Table-structure questions (structure_tree.py, full_run_v6.py, 2026-10-19)

- GT-derived structure key (structure_key.py, by values): only 2 GT-long tables in 109
  papers (Kovacs2010 t0 dev, Noriega2023 t8 held); v4 read 13 tables long wrongly.
- Q-ROW (record / wide / summary / other) per candidate table; record -> Q-NAMES +
  Q-VALUE -> long + wide readings (fixes v4's type-column-by-position bug); wide -> wide;
  summary / other -> no rows. Repeatable scorer (use_llm=False) for decisions.
- 2 dev iterations (iteration 1 broke Kovacs2010 t0: a caste's mean +- SD is a measured
  value, not a 'summary'); iteration 2 met the accept rule; held once: structure 26 -> 31/35,
  Noriega2023 0.004 -> 0.793, held repeatable micro F1 0.431 -> 0.747, mean F1 0.535 ->
  0.549, 1 regression (Beyer2021 -0.017). Candidate for adoption (user decides).
- Open: CortesGomez t6 (record, no names column), Orlofsk t3, Tran t3; Noriega trait codes
  (EL, HL) still undecoded (the scorer's value match maps them).

## Table-kind and column questions (kind_tree.py, full_run_v7.py, 2026-10-21) — run 2026-10-22, best so far

- From the person's table-by-table review of the 'trait columns mis-tagged' group (Attiwilli,
  CortesGomez, Figueroa, Melo, Orlofsk; 29 tables): page https://claude.ai/artifact/1yvRVLdYnYJvXKMUQe59qy,
  answers in output/column_review/reviews/, paper/table context in output/column_review/context.json.
  ALL FIVE ARE HELD PAPERS: they are development papers now (held minus these = 50 papers).
- Rules from the review: (1) numbers read off a figure give no rows (13 tables); (2) model /
  test output gives no rows; (3) sampling, abundance, pollen load, site data are not traits;
  (4) a column naming each row's statistic (Attiwilli 'Mean' / 'Range') is measurementStatistic;
  (5) '(n=45)' in the organism label is the sample size; (6) a coded column can be the trait
  (Melo 'FG', tagged caste 0.30); (7) model terms named after taxa are not organism rows.
- kind_tree.py: Q-KIND per table (traits / figure / model / sampling / other; not traits >= 0.8
  -> no rows), Q-COL per measurementValue column of a table read long WITHOUT the structure
  step's confirmation (statistic / trait / label; applied only when all are sure), Q-ROLE per
  caste / sex / lifeStage column (context / trait). Code: '(n=45)' split. Organism: a higher-rank
  column v4's Q-UNITS turned down as 'groups' is taken back when Q-KIND says traits (sure) —
  the GT records group summaries at that rank (Attiwilli families). Watch it on all papers.
- Oracle (full_run_v7.py oracle: the review's answers in place of nimble, 6 folders), repeatable
  scorer: CortesGomez2023 0 -> 0.538, Attiwilli2022 0 -> 0.455, Cortés-Goméz2023 0 -> 0.239
  (its own GT file); Melo2021 stays 0 until decode + meaning run on 'FG' (inventory has the
  legend: DCR = dominant arboreal ants…); Figueroa2021 0 (GT from an image table); Orlofsk2014 0
  (t3 left unsure in the review).
- Attiwilli mean rows still miss: printed '91.1 (61.29)', GT '91.1 ± 61.29' (a GT convention
  for mean (SD)); 'Pooled' row is not in the GT (6 extra rows).
- Run on nimble, all 109 (2026-10-22): mean F1 0.531 -> 0.530 (8 up, 6 down). Almost all of the
  loss: Q-KIND called species lists 'sampling' (sure) though they print traits beside the counts
  (Pereira t0, Nunes t2, McCune t0, Kratschmer t10-t13: 0.897/0.830/0.667/0.532 -> 0). First run
  kept in output/full_run_v7/iter1/.
- Q-ALSO (kind_tree.ask_also), asked only after a sure 'sampling': does the table also give each
  organism a characteristic of its own? Sure yes -> kept (column questions then run). 17 tables
  asked, 7 kept (the 4 papers above), 10 still dropped, none of those papers lost score.
  Mean F1 0.531 -> 0.556 (repeatable 0.530 -> 0.555, micro 0.582 -> 0.584); 8 up, 3 down
  (MacDonald 0.142 -> 0.089, Cappellari 1.000 -> 0.985 (+30 rows), Orr -0.001).
  Caveat: the fix was made after seeing scores on all 109, held included: not a clean held number.
- Zero-score papers, checked against GT / markdown / stage answers (2026-10-22): 12 have the GT
  values outside any table (prose, or not in the markdown: Baine, Franzen, Hill, Quicke,
  Ustjuzhanin, Xia, Xu, Wijas, Tonelli, Harmon, Figueroa, Fondjo mostly). Table data lost in:
  Chichorro t9 (reader: too big), Brant t8 / Luo t4 (paper gate 'one' sure, per-table species
  question never >= 0.8 -> no species), Tran t0/t1/t3 (structure 'summary' -> no rows; GT keeps
  the means), Renoz t1 (sampling), Gomez (group label + abbreviated genus in species cells),
  Borges (prey species taken as organism), Oliveira t14 (M/V columns, names unexpanded),
  Orlofsk t3 (SD value read as the trait name), Kovacs2008 (traits-as-rows, LaTeX values),
  Viza (0/1 codes undecoded).

## GRIT test set (grit_run.py, data/grit_testing, 2026-10-22) — IN PROGRESS

- 150 folders (99 share a name with un_processed_papers), GT xlsx copied in from data/GRITTesting.
  MinerU done for 148 (Chichorro2022, V.Gomez2022 have no paper PDF). mineru_extract.classify_folder
  now also takes the spreadsheet named after the folder as the GT (16 folders had a main PDF named
  otherwise, e.g. 'Araujo_2021 (1).pdf', and the GT would have been converted into the markdown).
- Whole chain head -> v7 -> score, in its own root (TREE_PAPERS / TREE_OUTPUT -> output_grit/).
  Blind: the head reader's body check runs on every table (no GT-keyed tables), ~32-50 s per table.
- Paused 2026-10-23 17:09 in the head stage: 837 of ~1236 tables saved (102 papers). Skipped as too
  big: Bucher2024 t4, McDonald2021 t4, Noriega2023 t6. Resume (from src/v7): python grit_run.py all

## Grit GT Excel dates repaired (2026-10-28)

- source/repair_gt_excel_dates.py (pass 1: trait verbatim + one candidate in the species' row): 371 cells.
  Pass 2 (the person's idea: search the paper for the date's possible originals, keep the one that
  makes sense next to the trait's other values): 4,211 more (one candidate in the species' row, or one
  in the paper that fits). 4,582 cells in 28 papers; backups in data/backup/grit_testing/, logs in
  data/grit_gt_date_repairs*.csv (data is not in git). ~5,976 left: mostly Noriega2023 rows whose GT
  species is misspelled ('Onthoagus', 'Sisyus'), so its row is not found and several readings fit.
- More passes (2026-10-29): misspelled species matched to the printed name (+2,040), Noriega2023 lined up
  row by row with its per-specimen table (+2,852), loose names / case-blind codes / epithet tie-break
  (+721): 10,195 of 10,558 date cells repaired; 363 on the review page
  https://claude.ai/artifact/Ucz5RZoJBpodZ7b7pHDCYz (answers in its db, collection 'answers').
  Rescored: 0.5314 -> 0.5327 (Nunes +0.054, Arnan2012 +0.049, Noriega +0.029, GibbParr +0.029).
- v9 rescored on the repaired GT: grit mean F1 0.5215 -> 0.5314 (24 papers up, none down; Scalercio
  +0.163, Nelson +0.149, Fontanilla +0.138, Uemori2021 +0.121, Noriega +0.073).

## Listed tags (v14 = v13 + listed_tags.py, 2026-10-29/30) — ADOPTED with four tags: the new baseline

- Design and every run: output/eval_split/DESIGN_listed_tags_v14.md; measure tag_score.py (TAGS_V14.txt).
- Fills sex, caste, basisOfRecord, lifeStage from the template's lists (cells, section labels, captions,
  paper text in rounds; basisOfRecord also per trait: literature -> MaterialCitation, and the methods
  re-asked when the specimen value rests on quotes under 0.95). Core rows unchanged: F1 = v13's.
- Accept rule on the 109 split, held run once (questions frozen at 6b633ca6): accuracy dev / held
  sex 98.1 / 94.9, caste 97.5 / 100, basisOfRecord 87.8 / 93.1, lifeStage 80.2 / 74.0.
- Baseline tag accuracy (coverage), v14 adopted, 2026-10-30 run: 109 set sex 97.3% (46.7%), caste 97.9%
  (75.6%), basisOfRecord 90.7% (98.2%), lifeStage 77.7% (54.8%); grit sex 76.1% (33.6%), caste 92.6%
  (42.4%), basisOfRecord 71.4% (90.1%; was 57.0%), lifeStage 70.7% (59.8%). Grit-only papers (totals
  only): basisOfRecord 44.9% (was 35.5%), sex 30.8% (its misses are values the papers never print).
- measurementStatistic FAILED held (dev 93.6, held 63.2): still asked and recorded, not applied
  (listed_tags.ADOPTED). Not to be tuned on the 109 held papers.
- Open: the defaults layer (TAG_DEFAULTS, off) for values the paper never prints (Noriega2023 alone is
  most of held's empty sex / lifeStage); GT cases to check by eye: Korosi2022, Cecala2021,
  CamargoVanegas2024 (basisOfRecord contradicts the paper); 'sd' is not on the template's statistic list.

## One-species papers (v13 = v12 + the subject step, one_species.py, 2026-10-29) — ADOPTED (was the baseline)

- Design: output/eval_split/DESIGN_one_species_v13.md (3 dev iterations, then 2 full runs).
- Run 2 (gate-'several' branch dropped by the design's rule; unanswered trait columns kept):
  grit production 0.539 -> 0.554 (6 up / 4 down), repeatable 0.538 -> 0.546; 109 set
  0.560 -> 0.576 (4 up / 1 down), repeatable 0.559 -> 0.558.
- Up: Brant2021 0 -> 1.000 (held, production only), Tran2022 0 -> 0.400 (held), Zhang2025 0 -> 0.745,
  TOMBERLIN2002 0 -> 0.475, Grasser2000 0 -> 0.384, Luo2023 (109) 0 -> 0.466, Kovacs2008 small.
- Down: kovacs2010 1.0 -> 0.667 (grit), Kovacs2010 0.667 -> 0.500 (109, dev), PascacioVillafan2022
  0.80 -> 0.50, Buzzone2008 -0.03, Bucher2024 -0.007. Causes: a structure 'summary' table of slopes
  lifted by the clash duel (kovacs t4, Bucher t2); tables v12 already read re-read as trait rows.
- Open: restrict the re-reading to tables v12 gave no rows (or groups only), and the structure clash.
- Also: output/SUPPLEMENTS_NEEDED.md lists papers whose GT is not in the paper's markdown.

- **Baseline from 2026-10-29: v13 with the supplements the user found** (production scorer, mean F1):
  grit 0.577 (v12 0.539), 109 set 0.582 (v12 0.568, Orr2024 re-scored under the float-noise fold).
  Supplements added (grit folders; data/grit_testing is not in git, kept in sync by hand on both
  machines): Arnan2014_S1.xlsx (0.644), Wijas2021_S1.csv (0.442), Ambrozova2022_S1.docx (0.930),
  Crabot2022_S2.xlsx (0.862, with the GT fix below), Tielens2020_S2.xlsx (0.397), Tonelli2021_S1.pdf +
  _S2.xlsx (0.154), Schat2024_S1.csv (still 0: species printed as epithets). 109 set: Fiedler2021_S2.xlsx
  and _S2.pdf kept (0.667 -> 0.444: S2.xlsx repeats S1's table).
- GT fix: data/grit_testing/Crabot2022/Crabot2022.xlsx, 52 measurementValue cells Excel had turned into
  dates restored as typed ('4.5', '3.06'); the original kept as Crabot2022.xlsx.before_date_fix.
  Four differ from the trait data file (Coenagrion scitulum E10/E200/E390, Lestes virens E98): to check.
- Scorer (source/evaluate.py): spreadsheet float noise folded (220.8099999486709 == 220.81).
- Open: v13's drops (kovacs2010, PascacioVillafan2022, Buzzone2008, Bucher2024); Schat2024 genus join;
  Wijas list cells; Tonelli numeric codes; Scalercio 'Wingspan' (five columns, one GT name).

## Continuation tables whose head has no names (v12 = v11 + the join, 2026-10-28) — RUN, no paper down

- Results (remote): grit mean F1 0.536 -> 0.539 (production), 0.536 -> 0.538 (repeatable); 109 set
  0.559 -> 0.560. Only Taillefer2018 changed: grit 0.012 -> 0.324 (TP 11 -> 508), 109 set 0.099 -> 0.143
  (its head reader joins only t8 there). Chichorro2022 (held) still writes no rows. Every other CSV is
  byte for byte v11's. Left in Taillefer: Voltinism 'M' / 'U' and Overwintering 'A' / 'L' stay undecoded;
  the GT's 'Feeding' is the paper's 'Spe/Gen' column and its 'Larval feeding habit' is the paper's 'Feeding'.

- Design: output/eval_split/DESIGN_continuation_v12.md. Taillefer2018 t8 / t11 start with a family label
  the head reader read as a head with no names, so they were not joined to t7 and their columns came
  out '(no name, column N)' (grit F1 0.012). Rule: a head with no column name at all joins like no head
  (same width). Reach: grit Taillefer t8, t11; 109 set Taillefer t8, Chichorro2022 t6 (a legend table).
- v12:decode asks only the cells of joined tables the saved decode never saw ('PA', 'PR', 'S', ...).
- Not in it: continuations of another width (Torok2022 t8, M.Wang2021 t11: number merged into the
  species cell) need their columns lined up: a question for the model.

## Names still printed as codes + species duels (v11 = v9 + both, 2026-10-28) — ADOPTED, best so far

- Results (remote, 2026-10-28): grit mean F1 0.533 -> 0.536 (production), 0.532 -> 0.536 (repeatable),
  2 up 0 down; 109 set 0.554 -> 0.559, 1 up 0 down. Oliveira2022 0.000 -> 0.516 (both sets), Kovacs2008
  0.088 -> 0.121. Gains only in dev papers; no held paper moved (nothing for the step to act on there).
  The person adopted it (2026-10-28) and judged IOW -> 'ratio of inter-ocular width to mesosoma length'
  more correct than the GT's 'Eye position ratio'.
- Iteration 2: Q-PART now quotes the text around the table and the meaning step's reading; in iteration 1
  nimble called 'M'/'V' 'something else' (0.92) and all 16 Oliveira columns kept v9's names.
- Left: Oliveira 'P' (0.78 < SURE; GT Pilosity); variance rows count as extra (GT keeps means only);
  Fondjo HeadL / HeadW / AntenL stop in a duel between two wordings; Luo2023 t4 species duel 0.65 (open).
- The repeatable scorer as its own stage ('det') asked gemma once per missed row (miss severity left on):
  > 4 h on grit; fixed in det_score (5f73d2e).

- Design (before any run): output/eval_split/DESIGN_names_v11.md. The user's rule for choices with
  many options: two at a time until one or none is left (duels.py). Not sure anywhere -> v9 as is.
- name_parts.py (v11:names): only names whose current form still holds the code. The code part of a
  split header ('Traits AL M' -> 'AL'); Q-DEF duels over the legend's entries plus the names the
  paper gives the same code elsewhere (Kovacs 'AL', 'GL*' cells); Q-PRINTED duels over the names
  the paper's other tables print that share a word with the definition ('Antenna length ratio');
  Q-PART / Q-STAT for the other parts (statistic / unit / heading -> measurementStatistic, unit).
- species_duel.py (v11:species): tables still open in 'one'-species papers (Luo2023 t4), the
  gate's names + 'several' in duels, then the one left against 'none'; the clash rule unchanged.
- Run (grit): cd src/v11; python -u grit_run.py v11:names  (v11:names, v11:species, assemble,
  score); then python -u full_run_v11.py det all with the grit TREE_PAPERS / TREE_OUTPUT.
- Dev: Oliveira2022, Kovacs2008, Luo2023; held: every other paper asked. Accept as in the design.

## Category columns (v10, category_tree.py, 2026-10-28) — RUN on grit, NOT adopted (v9 stays best)

- Grit (remote): mean F1 0.522 -> 0.521. 152 columns asked (had a heading): 77 category, 48 own, 27 unsure;
  14 groups, 11 of them in dev papers. Changes only in dev papers: Bucher +0.018, Wallon +0.018,
  Martins -0.079 (its GT keeps 'seasonality - spring/summer/fall' as separate 0/1 types, like Khayati).
  The 3 held papers that formed groups (Cao, Fiedler, Gutierrez-Chacon) did not change at all.
  By the design's own rule (only dev improves) the step is dropped as overfit; kept as an experiment.
- Viza2023 formed 6 groups but stays at F1 0: the category values are the printed column names
  ('Body size BS'), not the legend's terms, and its GT traits ('Flight Behaviour' = 'Perchers') differ
  from the table's coded traits altogether.

- Design (before any run): output/eval_split/DESIGN_categories.md. Flag-only wide trait columns
  (0/1, yes/no, x, +/-, fractions) that are categories of one trait: code gives structural headings
  only (the header group spanning the column, the legend heading its code is listed under); no
  name-prefix rule (it fitted the sample). Q-CAT per column, Q-PRESENT per fuzzy group; a sure group
  of >= 2 columns becomes one row per category the organism has. Dev/held named in the design.

## Trait names from the legends (v9, legend_names.py, 2026-10-28) — BUILT, to run on the remote

- The meaning step finds a name's definition only through text shapes and only for tokens that look
  abbreviated; names a legend table defines stay as printed (Noriega2023 HW / PH: 3,476 GT rows each
  missed + 3,476 extra on grit). The legend inventory holds them (code 'HW' under 'Head width (mm)').
- v9:names: for each trait column left as printed, the inventory variables whose code is its name;
  Q-NAME (which is its full name, or none); sure -> the name. 149 questions on grit, 136 on the 109.
  Guariento2020's GT names ('larval feeding on grasses') are not printed in the paper: not covered.
- Checked without a model: v9 with no answers = v8's grit CSVs (148 papers).
- Iteration 1 on grit (remote): mean F1 0.518 -> 0.515 (Martins 0.94 -> 0.64, Yates 0.33 -> 0.18,
  Bucher 0.25 -> 0.17; Noriega +0.015, Gutierrez-Chacon +0.044): only the entry's variable was offered,
  and nimble took lone group headings ('HL' -> 'Morphological trait', 'S1' -> 'seasonality').
  Iteration 2: the entry's term too, the other codes sharing each name, 'none' covers shared headings.

## Section step (v8, section_tree.py, 2026-10-27) — BUILT, not run yet

- Design: output/eval_split/DESIGN_sections.md (written before any run). src/v8 = v7 + sections:
  head_to_table keeps every section label (head cells too) as t.sections and each record's
  rec['_sections']; Q-SECTION per label (higher / genus / organism / trait / place / context /
  treatment / other), Q-CONTEXT, Q-SERIES on a clash; applied per record from the nearest label
  of each kind above it. Replaces the organism step's 12-label genus path.
- Checked without a model: v8 with no answers gives v7's CSVs byte for byte (109 papers); v3..v7
  regenerated with the optional assembly hook still give their saved CSVs. 109 papers: 74 tables,
  231 labels, 3736 records under a label.
- TO RUN on the remote PC only (the user: not on this PC): grit set, v8:sections, assemble, score;
  compare with grit v7 (mean F1 0.517).

## Source layout (2026-10-24)

- src/ split into one folder per version (full_run, v3, v4, v5, v6, v7) plus experiments/: each
  folder holds its entry file and every module it imports (copies). full_run_v3..v7 are
  standalone (no version imports another); checked: each version's assemble from its folder
  gives the saved output/full_run_vN CSVs byte for byte (v3, v4, v6, v7; v5's saved output
  predates later shared-module changes, the old v5 code gives the same as the new one).
  A fix to a shared module must be copied into each folder that should get it.

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

- Figueroa2021 Table S2 (plant families visited per bee species, with n): not in the GT, but
  the person says it should have been extracted (2026-10-21) — add it to the GT?
- Orlofsk2014 Appendix S2: the person is unsure how it should be read (GT: Total block only,
  Mean and SD joined, Min and Max apart; per-site blocks unused).

- 1,351 life-stage rows recorded as measurementType in 6 papers (GT_REVIEW_CANDIDATES.txt):
  move to lifeStage? what measurementType/value would they get?
- The items in output/column_tree_bench/GT_ERRORS.txt.
- Sample size convention: does "how many were caught" count as a sample size?
