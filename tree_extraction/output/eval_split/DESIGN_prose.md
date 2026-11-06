# Prose papers: the set, the text cuts, and what the text looks like (2026-11-03)

## The set (output/eval_split/prose_set.json)

A paper is in the prose set when at least 50% of its GT rows are found in the running text next to
their species (in the same paragraph, under a heading naming the species, or after a paragraph that
starts with it), and under 20% in tables. Code reads only the markdown and the GT; no model, no
pipeline code (scripts in prose_scripts/). The 20% rule removes AmbspergTraun1991: it
matched as text, but v18 already reads it from its tables at F1 0.98.

| | dev | held_a | held_b | grit-only |
|---|---|---|---|---|
| 109 set | 3 | 0 | 3 | – |
| grit | 3 | 0 | 2 | 2 |

The tuning papers are Xia2022, Xu2024 and Ustjuzhanin2024, all at F1 0 in v18. All three are taxonomic
revisions or new-species descriptions in ZooKeys. The test papers are held_b and grit-only (totals only).
Caveat: three tuning papers from one journal's layout. Anything built on them can overfit that layout.
The test papers will show whether it does. Grit's GT for these papers is not the 109 one (Xu2024: 191
rows in grit, 721 in the 109 set).

Close but not in the set: Tsai2020 (a one-species paper; a third of its GT matched numbers in Results,
which are probably chance matches) and Renoz2020 (table values echoed in the abstract and key words).

## Simple cuts (prose_tactics.py), each on top of the one before

Characters kept, and GT rows still found in the kept text with their species:

| cut | dev (3) | held_b (3) | grit-only (2) | GT rows lost |
|---|---|---|---|---|
| full markdown | 100% | 100% | 100% | – |
| − references | 93% | 86% | 90% | 0 |
| − back matter (acknowledgements, funding, contributions, ethics, data availability, ORCIDs) | 92% | 83% | 88% | 0 |
| − page noise (page markers, running heads, page numbers, image placeholders) | 85% | 77% | 80% | 0 |
| − tables | 85% | 73% | 80% | 0 |
| − frame (abstract, introduction, discussion, conclusion) | 79% | 64% | 70% | 0 |
| − identification key | 72% | 62% | 68% | 2 of 1,299 (dev) |
| species accounts + methods only | 70% | 43% | 55% | 1% dev, 11% held_b, 9% grit-only |

The first five cuts lose no GT row in any group. Together they cut 20–35% of the characters.
"Species accounts only" is not safe: the test papers hold about a tenth of their GT outside
species accounts. After the safe cuts a prose paper is still 12k–25k tokens. The cuts help, but the
real saving is in how the text is split (below).

## What the tuning papers look like

The text is lists in disguise. Each paper has one heading per species, followed by the same labelled
fields in the same order (`**Type material.**`, `**Other material examined.**`, `**Diagnosis.**`,
`**Description.**` / `**Redescription.**`, `**Measurements. Male:** … **Female:** …`, `**Head**`,
`**Elytra**`, `**Male genitalia**`, `**Distribution.**`, `**Host plant and habitat.**`,
`**Etymology.**`, `**Remarks.**`), then a dichotomous key, then the references.
A species account is 350–1,650 tokens (median per paper), 6,400 at most.

The GT rows come in four kinds, and each paper leans on a different one:

| kind | example (printed → GT) | Xia2022 | Xu2024 | Ustjuzhanin2024 |
|---|---|---|---|---|
| number lists | `Male: BL: 7.8–8.6 mm, HL: 1.22–1.39` → Body Length = 7.8-8.6, range, male | 92% | 3% | 5% |
| specimen records | `1♂, Xishuangbanna, Menga, 1050–1080 m, 1958.V.13` → Altitude = 1050–1080, one row per record | – | 68% | 17% |
| description clauses | `**Pronotum.** Anterior angles protruding, …` → pronotum morphology = 'Anterior angles protruding, …' | 4% | 22% | 59% |
| short fields | Distribution, habitat, host plant, one per species | 5% | 7% | 19% |

Where the rows sit: Xia2022 87% in `Measurements`; Xu2024 55% in `Other material examined`, the rest
spread one row per field over `Head`, `Pronotum`, `Elytra`, `Leg`, `Male genitalia`, …;
Ustjuzhanin2024 in `External characters`, `Male genitalia`, `Female genitalia` and `Type material`.
`Etymology`, `Remarks`, `Differential diagnosis`, `Introduction`, `Discussion` and the key hold
almost nothing.
`Type material` / `Material examined` must be kept: that's where the altitude rows are.

## Approach for extraction (proposed, not built)

1. **Cut** references, back matter, page noise, tables and frame sections (code; loses nothing on any group).
2. **Split by species account** (code finds the headings; at run time there is no GT, so the model
   confirms that a heading names a species), and within an account by labelled field. Each model call
   then sees one field (tens to hundreds of tokens) plus a small paper-level context: the
   abbreviation list from Materials and methods (`BL = body length`) and the sex signs (♂ ♀).
3. **One question per kind of field**:
   - *number lists*: the model names each abbreviation from the methods' list; splitting `BL: 7.8–8.6`
     pairs and `Male:` / `Female:` into sex is mechanical.
   - *specimen records*: records are split on `•` / `;`; the model says which records give an
     altitude (and sex counts). One GT row per record.
   - *description clauses*: the model splits a field into (body part, clause) pairs; the body part is
     the trait. This is the heaviest text, and the GT's names and clause cuts are the volunteers' own
     choices, so the scorer's name and value matching decides how much counts. Measure that before tuning.
   - *short fields*: label = trait, text = value.
   - Etymology, Remarks, Differential diagnosis and the key are skipped (the model can confirm a
     field holds no trait).
4. **Papers without species headings** (about a tenth of the test GT sits outside accounts):
   paragraphs that name a species, read the same way. This can't be tuned on the three dev papers.

Upper bound: the three dev papers are 3 of 109 (+0.028 to the mean F1 if read perfectly); held_b
holds three more.

## Prose reader v1: built and run on the three dev papers (2026-11-03, src/prose/prose_reader.py)

The code cuts the text into passages; gemma reads who / has what / value per passage; nimble walks the
paper in order holding whose account the text is in (Q-SAME at each heading and at each passage naming
an organism, Q-START two names at a time, then against 'none'), then checks the owner of each fact that
names another organism (Q-OWNER, both orders) and which 'has what' are characteristics (Q-TRAIT).
Output: output/prose_v1. Page: output/eval_split/PROSE_SIDE_BY_SIDE_v1.html (each species once, GT
beside ours, no scorer).

Production scorer, prose rows only: Ustjuzhanin2024 0 -> 0.226, Xia2022 0 -> 0.127, Xu2024 0 -> 0.304.

Where it misses (side by side, no scorer):
- **Accounts opened at the wrong place.** The Chinese common name under each Xia2022 heading
  ('台湾钝胸隐翅虫黄足亚种', 50 rows) and a compared species (T. baoxingensis, 56 rows) took a species'
  rows. Synonyms in the synonymy lists (Leistotrophus birmanus, Crioceris consentanea), genus names
  in the introduction (Thoracostrongylus, Alucita) and compared species (A. bakingili, Alucita jana)
  opened accounts too.
- **Trait names at another level than the GT's.** Xia2022: abbreviations written out with the methods'
  full definitions ('length of head along the midline' for GT 'Head Length'); 185 rows have the GT's
  value under such a name. Xu2024: the GT keeps one row per labelled field ('Elytra morphology' = the
  whole paragraph); we split it into parts ('Humeral groove of elytra', 'Vertex').
- **Clause cuts.** Ustjuzhanin2024: the GT keeps the verb ('is tubulate and sclerotised', 'are long
  and thin', 'There are two …'); we start at the description ('tubulate and sclerotised').
- **Records under-read.** Xu2024: 255 GT altitude rows have nothing of ours beside them (one row per
  specimen record; gemma lists fewer records than a long 'Material examined' passage holds).
  Ustjuzhanin2024: habitat type (26), altitude (23) and distribution (12) from Type material not read.
- GT gaps: 96 Xu2024 GT rows have no trait name.
- Bug fixed during the run: gemma writes the heading's species as who even when the passage does not
  name it; such facts were dropped (Xia2022 556, Ustjuzhanin2024 346) and are now the account's.

## Prose reader v2 (2026-11-03, output/prose_v2; abbreviations, reading and species tracking reused from v1)

Judged side by side, not by the scorer (the user: GT and prose extraction can diverge a lot by nature).
- Body-part labels as context: nimble (Q-LABEL) calls a paragraph's bold label a body part or not;
  under a body-part label each part gets the label in front ('Humeri' under **Elytra** -> 'Elytra humeri').
  Xu2024: Head, Pronotum, Elytra, Leg, Abdominal sternite, Male genitalia, Female reproductive organs,
  'Mesosternum pubescent' (a statement, read as a part); Ustjuzhanin2024: Male / Female genitalia
  ('External characters' left out, right); Xia2022: none (its labels are Description, Measurements, Male).
- Whole-field rows: one per body-part field, type = the label, value = the paragraph (Xu2024 80, Ustjuzhanin2024 8).
- Trait / method: gemma proposes a split, nimble (Q-METHOD) keeps it only when the split-off words tell
  how it was measured. Xia2022 23 of 31 kept ('length of head' + 'along the midline', 'width of pronotum'
  + 'at the widest point'); body-part locations rejected ('cornuti in the aedeagus', 'distal band on the
  fore wing'). Wrongly kept: Xu2024 'middle of' (pronotal disc), a locality.
- Negations kept: of the GT's negated values (Xu2024 49, Ustjuzhanin2024 4, Xia2022 2) only 3 'not X /
  without X' phrases are missing from ours.

## Prose reader v3: species tracking (2026-11-03, output/prose_v3; abbreviations, reading and name splits from v2)

v1's Q-SAME ended accounts with a sure 'no' at synonymy lines ('Ontholestes birmanus: Bernhauer &
Schubert, 1914: 392.', 'T. baoxingensis ... syn. nov.'), figure captions printed inside another account
and comparisons ('resembles Alucita longipenis'); rewording its 'yes' (other names of S, comparisons,
captions) and asking it in both orders did not change those answers. The three papers start accounts
under a heading or at a bold name ('**Alucita fako ... sp. nov.**'), never at a plain paragraph, so v3:
- with an account open, asks only at a break: a heading, or a paragraph whose bold opening holds a name;
  a plain paragraph naming another organism stays in the account (Q-OWNER still decides each fact's
  owner); with no account open, any passage naming an organism is asked, as before;
- Q-RANK once per name: only a Latin species / subspecies name can open an account (genus names,
  'Alucitidae', 'many-plumed moths' and Xia2022's Chinese name now say no);
- a heading's own names are its candidates; 'none' also names key couplets and figure captions.
Accounts: Xia2022 29 -> 16 (T. acerosus 13 -> 65 rows; the synonym T. baoxingensis and the Chinese name
gone), Xu2024 22 -> 11, Ustjuzhanin2024 25 -> 16. Left: L. consentanea and L. semipunctata open a few
passages late (their headings' start question was not sure); a key couplet opens 'A. potockyi' (20 rows);
facts in differential diagnoses go to the compared species through Q-OWNER (A. megaphimus 8, A. chloracta 7).

## Judged evaluation of v3 (2026-11-04, prose_scripts/judge_pairs.py + judge_match.py)

The production scorer misses irregularities (dash styles, units, a leading 'is / are', trait names in
other words), so the rows were also matched by judgement: same species (genus initial + epithet), value
equal once format is set aside, and trait names judged the same. Every (GT name, our name) pair that
shares a value was read by hand: 148 pairs, about 30 rejected as coincidences (e.g. 'Elytra Length' vs
'width of elytra' with equal numbers, 'antennae' vs 'hind legs' both 'pale yellow'). Then near values
for the same trait: GT typos in numbers (Xia2022 '9.02' printed '9.2', '1.95-.39' printed '1.95–2.39')
count as matches; a value that is part of the other ('antennae = yellow' vs GT 'are yellow, with only the
basal area ...') counts only in the lenient line. Precision counts only our extra rows whose trait the GT
also has (as the scorer's scope does).

| paper | scorer F1 | judged R / P / F1 | lenient (parts count) R / P / F1 |
|---|---|---|---|
| Xia2022 | 0.144 | 0.910 / 0.926 / **0.918** | 0.917 / 0.934 / 0.925 |
| Xu2024 | 0.365 | 0.406 / 0.409 / **0.408** | 0.459 / 0.462 / 0.461 |
| Ustjuzhanin2024 | 0.279 | 0.584 / 0.409 / **0.481** | 0.757 / 0.530 / 0.624 |

What is left: Xia2022 misses HL/HW (21 rows, never read). Xu2024 misses 295 altitude records plus 66 GT
rows with no trait name (also altitudes): the under-read 'Other material examined'. Ustjuzhanin2024 misses
habitat type (26), altitude (14) and distribution (9) from Type material. Precision on Xu2024 and
Ustjuzhanin2024 is understated: our part rows ('Elytra humeri') count against the GT's whole-field rows
('Elytra morphology') of the same body part.

## Prose reader v4 (2026-11-04, output/prose_v4): captions, lists, re-reads, heading names

- shape (nimble): Q-CAPTION, then Q-LIST per paragraph. Captions: Ustjuzhanin2024 22, Xia2022 35, Xu2024 42
  (no more 'aedeagus = 17–20' or 'Scale bars = 1 mm'); lists: 18 / 25 / 46.
- items (gemma): list items copied out as printed (checked), read 8 at a time: 109 / 118 / 511 items.
  Passages with >= 3 printed numbers, 30% of them unused, read again in halves: 38 / 28 / 56, facts added 61 / 19 / 103.
- heads (gemma): Xu2024's headings 'Lilioceris consentanea (Lacordaire, 1845)' and L. semipunctata had
  come back from the reading without names, so their accounts opened late and their records were
  dropped ('no account', 18 altitudes of L. consentanea); now asked on their own, the walk rerun.
- Assembly no longer merges the rows of separate list items (17 records at '920 m' are 17 rows).
- Lead word as context: only a paragraph's first piece, asked in both orders ('Peng', 'Yan' from a split
  record paragraph were first accepted as body parts; both orders also drop 'Wings', 'Sacculus').

Judged (same rules as v3; one new coincidence rejected: 'Body color' vs 'antenna', both 'black'):

| paper | v3 judged F1 | v4 judged R / P / F1 | v4 lenient F1 |
|---|---|---|---|
| Xia2022 | 0.918 | 0.910 / 0.926 / 0.918 | 0.925 |
| Xu2024 | 0.408 | 0.775 / 0.506 / **0.613** | 0.652 |
| Ustjuzhanin2024 | 0.481 | 0.609 / 0.381 / 0.469 | 0.609 |

Left: Xia2022's HL/HW ratios (21; 2 numbers of ~32 per Measurements passage, under the re-read
threshold). Ustjuzhanin2024's habitat type from Type material (26). Xu2024 altitudes of L. semipunctata
(37 GT unmatched, 15 of ours unmatched). Precision counts our part rows ('Head labrum', 'Head vertex')
and record locations against the GT's whole-field rows, so it is understated.

## Prose reader v5 (2026-11-04, output/prose_v5): described places, written-out trait names

- HL/HW: read all along, then dropped by Q-TRAIT on the bare name 'hl/hw' ('other' 0.75). Q-TRAIT is now
  asked on the name written out with the paper's abbreviations; Xia2022's 21 HL/HW rows are back.
- places (gemma): places the paper describes outside the species accounts. Ustjuzhanin2024's GT 'habitat
  type' comes from the study sites in Materials and methods ('- Bamboo Camp. ... a lowland rainforest
  ...'), which the records inside the accounts name only. Q-PLACE (nimble): does a passage in an account
  give records of S from a described place it names; a sure yes adds the place's characteristics once per
  mention, except what the record itself gives.
- A first run joined everything (Mount Cameroon 'hosts / harbour / endemism', provinces, 'China': 340
  junk rows), so two checks come before a join: Q-SITE per place (one described site, or a country /
  province / mountain / museum) and Q-ENV per place fact (conditions there, or species, records, history).
  Left: Mount Cameroon passed Q-SITE and its 'presence: of diverse habitats along its elevational ...'
  passed Q-ENV (36 rows of a general statement).

Judged (same rules; one new coincidence rejected: 'Pronotum Width/Elytra Width' vs 'length of head/width of head'):

| paper | v4 judged F1 | v5 judged R / P / F1 | v5 lenient F1 |
|---|---|---|---|
| Xia2022 | 0.918 | 0.960 / 0.927 / **0.943** | 0.951 |
| Xu2024 | 0.613 | 0.775 / 0.506 / 0.613 | 0.652 |
| Ustjuzhanin2024 | 0.469 | 0.691 / 0.403 / **0.509** | 0.645 |

## Test: prose reader v5 run once on the 3 held_b prose papers (2026-11-04; totals only, prose_test.py)

Frozen v5 code (6ea673ce), all stages from scratch, run once; the reader's own log (paper names) not read.
The automatic judging cannot read name pairs by hand: a pair whose names share no word never counts, so
it is stricter than the hand-judged dev numbers; dev run the same way for reference.

| group | v18 mean F1 | production mean F1 (micro) | judged automatic micro R / P / F1 | lenient F1 |
|---|---|---|---|---|
| dev (3) | 0.000 | 0.381 (0.449) | 0.813 / 0.578 / 0.676 | 0.726 |
| held_b (3) | 0.000 | 0.443 (0.477) | 0.702 / 0.772 / 0.735 | 0.782 |

Sanity (held_b, summed): 604 passages, 96 captions, 54 lists, 274 list items, 46 accounts opened, 1,437
facts kept, 0 place joins, 1,383 rows; no paper without rows or without an account.
It holds on the test papers: recall a little lower than dev (0.70 vs 0.81), precision higher (0.77 vs
0.58: fewer part rows against whole-field GT rows), F1 above dev. Nothing was tuned on these numbers.

## Speed line v6 / v7 / v7a (2026-11-04, dev papers, one gemma request at a time)

The time follows how much gemma writes, not the number of calls (v7a: 1,122 of 1,220 gemma seconds in
the reading were generation; ~55 output tokens per fact). Parallel requests were dropped: the reader
must also run on the local PC when the remote is down (memory: local-fallback-design).

| | v6 | v7 | v7a |
|---|---|---|---|
| change | shape before reading (captions not read, lists only item by item) | names first, species tracking before reading, facts only inside accounts, Q-FIELD, answers [who, sex, what, value] by position, re-reads on evidence | v7 with answers as named fields + one worked example per prompt |
| all stages, 3 papers | 2,760 s | 1,976 s | ~1,640 s (1,442 s + ~200 s reused) |
| judged F1 (hand rules) Xia / Xu / Ustjuzhanin | 0.947 / 0.626 / 0.480 | 0.937 / 0.269 / 0.312 | 0.945 / 0.594 / 0.443 |
| automatic judged micro F1 (prose_test) | 0.680 | 0.441 | 0.658 |

v7's Xu2024 collapse was the positional answer: records came back with the record itself as "what"
('Xishuangbanna, Mengla, 620–650 m', 43 rows); named fields bring the altitudes back (359 rows, v6 444).
New in v7a: with "sex" optional gemma leaves it out of every record (Xu2024 0 of 1,945 facts,
Ustjuzhanin2024 0 rows; v6 235 / 189). Re-reads (v7a): T1 never fired; T2 fired 12, added 1; T3 fired
116, added 103.

Queued (2026-11-04, one after another, each one change on the one before; logs ~/run_prose_<v>.log on
the remote): v7b full clauses + sex always answered; v7c list items cut from start words (pointers;
log: starts, not found, fall-backs); v7d format retry (malformed answers asked again once) apart from
the re-reads. To judge each against v6 and v7a by hand rules, with times and tokens.

## The v7 line judged (2026-11-04, 3 dev papers, one gemma request at a time)

Each adds one change to the one before (src/prose/prose_reader.py, PROSE_VARIANT); the names-first, tracking and
Q-FIELD stages are reused from v7, so ~200 s are added below for a full run.

| | v6 | v7a named fields | v7b + full clauses, sex always | v7c + list items from start words | v7d + format retry |
|---|---|---|---|---|---|
| judged F1 Xia2022 | 0.947 | 0.945 | 0.954 | 0.955 | **0.955** |
| judged F1 Xu2024 | 0.626 | 0.594 | 0.563 | 0.624 | **0.702** |
| judged F1 Ustjuzhanin2024 (lenient) | 0.480 (0.605) | 0.443 (0.644) | 0.498 (0.689) | 0.500 (0.689) | 0.489 (0.688) |
| automatic judged micro F1 | 0.680 | 0.658 | 0.657 | 0.687 | **0.726** |
| production micro F1 | 0.447 | 0.389 | 0.381 | 0.410 | 0.452 |
| full run, 3 papers | 46 min | ~27 min | ~31 min | ~33 min | ~35 min |
| reading output tokens | – | 153,606 | 179,330 | 190,886 | 204,908 |

- v7d's format retry is the largest single gain: 59 retries (of 467 calls) recovered 236 passages / items that gemma's
  answer had left out. The empty-item re-read T3 fell from 175 fired to 50: most "empty" items were missing answers.
  Xu2024's unmatched GT altitudes: v7b 163, v7c 109, v7d 22.
- Pointers did not save time (tokens and time rose), their gain is completeness on Xu2024 (605 items, 511 copied) and
  Xia2022 (169, 113), while Ustjuzhanin2024 got fewer (73, 104). 48 of 806 starts not found; 13 of 89 lists fell back.
  Item boundaries were not checked one by one.
- Re-reads in v7d: T1 never fired; T2 fired 15, added 6 (all Ustjuzhanin2024); T3 fired 50, added 48. Whether these
  added facts are GT facts is not yet measured.
- Sex still below v6: rows with sex Xia 387 (433), Xu 107 (235), Ustjuzhanin 108 (189).
- 5-8 min per paper not reached: v7d ~12 min per paper, Xu2024's reading alone 946 s.

## Sentence sorting by nimble, tested without gemma (2026-11-05, src/prose/sentence_test.py, output/prose_sent)

Sources for the idea (filter or classify, then a narrow question): Marcos et al. 2024, Domazetoski et al. 2025, Brinner &
Zarrieß 2025 (a selector can lose data: Marcos's recall fell 0.95 -> 0.55 on outside data; an LLM selector that kept
literature-review sentences made results worse). So the selection was measured before any reading.

Each sentence inside an account: Q-ABOUT (the organism, or records, literature, names, the study; dropped only on a sure
'other' in both orders) and Q-CAT (measurement, description, distribution, habitat, host / food, life, comparison).

| paper | sentences | dropped | characters kept | GT rows found in the account | lost | also in a dropped sentence | time |
|---|---|---|---|---|---|---|---|
| Xia2022 | 187 | 31 | 93% | 376 | 0 | 0 | 37 s |
| Xu2024 | 341 | 55 | 93% | 700 | 0 | 0 | 60 s |
| Ustjuzhanin2024 | 328 | 35 | 92% | 201 | 0 | 0 | 57 s |

Dropped: synonymy and citation lines, type-specimen labels, etymology, what the literature recorded (the T. miyakei sentence
'a male ... not mentioned in Yang et al. (2011)' at 0.968). 80 GT rows are in no sentence of their account (a ceiling this
test cannot see past). Categories are clean where it counts: Xia2022's measurements all 'measurement'; Altitude all 'record
list'; morphology 'description'. Left in: some Etymology and Remarks sentences ('This species seems to be very rare' as
distribution; '... named after Fako' as habitat) and 55 comparison sentences, for a per-fact check. It cuts wrong rows more
than time: only 7-8% of the characters go. Tested on 3 dev papers from one journal; not yet read through by gemma.

## v8: sentences sorted by nimble, read by kind, each text fact checked (2026-11-05, dev papers; not adopted as built)

| | v7d | v8 |
|---|---|---|
| judged F1 Xia / Xu / Ustjuzhanin | 0.955 / 0.702 / 0.489 | 0.943 / 0.687 / 0.468 |
| judged recall Xia / Xu / Ustjuzhanin | 0.975 / 0.834 / 0.597 | 0.972 / 0.838 / 0.580 |
| judged precision Xia / Xu / Ustjuzhanin | 0.935 / 0.606 / 0.414 | 0.915 / 0.582 / 0.393 |
| rows with sex Xia / Xu / Ustjuzhanin | 387 / 107 / 108 | 587 / 1,118 / 164 |
| trait is a sex or specimen word (all) | 19 | 4 |
| full run | ~35 min | ~39 min |

- Works: dropping sentences (the T. miyakei 'male' row is gone, sex-word rows 19 -> 4), and sex from an item's ♂ / ♀ by code.
- Hurts: the question per kind. FIELD8 ('what: distribution, habitat, ...') turns kept sentences that only name places into
  rows: 'distribution' extras Xia 1 -> 10, Xu 1 -> 20, Ustjuzhanin 0 -> 9 ('distribution = Wuyishan City, Guadun Vill. ...',
  'distribution = mainland of east China' for T. miyakei). Sentence runs also bring coarser names (Xu 'Head = frontoclypeal
  area triangular' against 'Head frontoclypeal area = ...'), which count against precision.
- Q-FACT barely acts: 1,823 asked, 11 dropped; mostly collectors and museums read as localities, at least 2 of the 11 wrong
  ('locality = Xinglong', a Wings description).
- Still wrong after both checks: rows whose trait is a species name (Xu 10, Ustjuzhanin 7), a few literature values (7).
- Xu2024 GT writes sex 'both' on the altitude rows, so sex from the record's own ♂ / ♀ will not agree with those GT rows.

## v8b: v7d + only what worked in v8 (2026-11-05, dev papers)

Passages read without the sentences nimble dropped (same questions as v7d, 'Male:' stays in place); sex from a record's own
♂ / ♀ (code); a record's locality and coordinates on its rows (verbatimLocality, verbatimCoordinates), not rows of their own.

| | v7d | v8b |
|---|---|---|
| judged F1 Xia / Xu / Ustjuzhanin | 0.955 / 0.702 / 0.489 | 0.956 / 0.699 / 0.493 |
| judged lenient F1 | 0.960 / 0.741 / 0.688 | 0.961 / 0.738 / 0.696 |
| rows | 3,136 | 2,175 |
| locality + coordinates as rows | 799 + 178 | 3 + 34 (the 34 come from the place joins) |
| rows with verbatimLocality / verbatimCoordinates | 0 / 0 | 607 / 111 |
| rows with sex | 602 | 1,117 |
| trait is a sex or specimen word | 19 | 1 |
| full run | ~35 min | ~36 min |

Same quality with a third fewer rows and the records whole (altitude + sex + locality + coordinates on one row). 104 records held
only place fields, so they give no row; they are logged in read2 ('record_only'), several are fragments from the pointers.
Still wrong: rows whose trait is a species name (20), the 36 Mount Cameroon 'presence' rows and 34 coordinates from place joins,
comparisons kept as values. Nimble's sentence sort exists only for dev (output/prose_sent); held_b needs that stage before its test.

## v8c: cleanup on v8b's reading (2026-11-05, dev papers; decisions only, 74 s + totals)

A trait that is exactly a species name gives no row; facts from a sentence nimble called a comparison asked Q-COMP on the fact
alone (with the whole sentence it dropped real traits such as 'antenna = brownish red ...'); a place named inside another place's
description is the larger area, not a site (Mount Cameroon, Cameroon: asking Q-SITE and Q-ENV in both orders did not stop them, this
did); a place's coordinates give no row; '350 m a.s.l.' split into value and unit.

| | v8b | v8c |
|---|---|---|
| judged F1 Xia / Xu / Ustjuzhanin | 0.956 / 0.699 / 0.493 | 0.956 / 0.699 / **0.606** |
| judged lenient F1 | 0.961 / 0.738 / 0.696 | 0.961 / 0.738 / 0.702 |
| automatic judged micro F1 | 0.726 | **0.747** |
| production micro F1 | 0.452 | **0.475** |
| rows | 2,175 | 2,083 |

Ustjuzhanin2024's jump is the altitude unit (GT writes '350', we wrote '350 m a.s.l.'), not the junk removal: the removed rows were
mostly outside the traits the GT scores. Removed: 36 'presence' rows, 34 place coordinates, 22 comparisons (nearly all right; 'tempora =
slightly shorter' is debatable). Earlier count of 20 'species-name traits' was wrong (pattern also caught 'Lateral metasternum'): 5
real; the rule removes 0 now, 'Thoracostrongylus miyakei = also has ...' remains because its name is cut down after the rule runs.
Left: literature values (7), 104 records without a row (logged). Still dev only.

## Test: v8c run once on the 3 held_b prose papers (2026-11-05; totals only, prose_test.py)

| | v5 held_b | v8c held_b | v8c dev |
|---|---|---|---|
| automatic judged micro R / P / F1 | 0.702 / 0.772 / 0.735 | **0.255 / 0.644 / 0.365** | 0.855 / 0.664 / 0.747 |
| lenient F1 | 0.782 | 0.413 | 0.788 |
| production micro F1 | 0.477 | 0.246 | 0.475 |
| production mean F1 | 0.443 | 0.295 | 0.401 |
| rows | 1,383 | 608 | 2,083 |
| facts kept | 1,437 | 627 | 1,994 |
| stages | | 1,283 s | |

The score is what the run gave and it stands as v8c's test. The drop is a fault in the reading's check, not the model missing the text
(found with summed counts only, prose_scripts/prose_funnel.py, prose_dropped.py, prose_unit_check.py; no paper, row or value looked at):

- GT values printed in their species' account: 908 of 983 for v8c, 910 for v5. Species tracking and the sentence sort lost almost
  nothing (sort: 906 of 907 kept).
- Lost at reading: 550 GT values (v5 18). Lost at the decisions: 4 (v5 24). So the loss is one step.
- Dropped as 'value not printed in the passage': 607 (v5 44, dev 82). 564 of them end in a unit, and in all 564 the number alone IS
  printed in its passage. 531 GT values that no read fact holds would be held by these numbers. On dev the same count is 0.
- Why: v5 asked for the unit in its own field. Since v7a the measurement prompt asks for the value 'with its unit'. When a paper prints
  the unit away from the number, gemma adds it, the words are no longer side by side, and the printed check drops a right number.
  Nearly all of it sits in one paper (papers with 50+ such drops: 1). No dev paper prints units that way, so tuning could not show it.

Proposed fix (not made): in the check, a value ending in a unit whose number is printed in the passage keeps the number and moves the
unit to its own field; code only, no model question changes. Dev should not move (0 such drops). The saved reading holds these dropped
facts, so held_b would not need gemma's reading again, only names, facts and assembly. A rerun would be a second look at held_b, with
the fault found on held_b's totals, so it must be reported as that, next to this result, not in place of it.

## v8d: the unit fix, and a second look at held_b (2026-11-05; totals only)

The printed check now sets a trailing unit aside: the number must be printed, and the unit goes to its own field only when printed in
the same text. No model question changed. v8d starts from v8c's saved reading: the `units` stage rescues the saved drops with no model,
then names (only where facts were rescued), facts and assembly run again. Dev: 75 s; held_b: 82 s (plus totals).

Dev did not move: every total equals v8c's (the run was set to stop before held_b otherwise).

**This is not a clean test.** The fault was found from held_b's totals, so v8c's 0.365 stays the one clean run and v8d is a second look
beside it. No paper, row or value was looked at, and no model question changed.

| held_b | v5 | v8c (clean test) | v8d (second look) |
|---|---|---|---|
| automatic judged micro R / P / F1 | 0.702 / 0.772 / 0.735 | 0.255 / 0.644 / 0.365 | **0.775 / 0.839 / 0.805** |
| automatic judged mean F1 | 0.557 | 0.368 | 0.553 |
| lenient micro F1 | 0.782 | 0.413 | 0.840 |
| production micro F1 | 0.477 | 0.246 | 0.531 |
| production mean F1 | 0.443 | 0.295 | 0.417 |
| rows | 1,383 | 608 | 1,147 |
| GT values lost at reading | 18 | 550 | 27 |
| GT values lost at the decisions | 24 | 4 | 4 |
| list items | 274 | 182 | 182 |
| accounts opened | 46 | 43 | 43 |

Micro rose past v5 while mean F1 did not (judged level, production lower): the gain weighs towards the papers with more rows, and the papers
are not all better. Which one is not looked at. List items stayed below v5 (182 against 274), not explained here. The judged numbers
use the automatic pairing, which is stricter than by hand.

## The information tree: v9, v9b, t1 (2026-11-05, 3 dev papers)

species (from the tracking) -> phrases (kept sentences, list items) -> nodes (type, unit, value, sex, ...), no fixed order, each node checked
by itself. v9 / v9b (prose_tree.py) and t1 (prose_tree_t1.py, gemma reads the whole passage, code places the nodes) were built apart.

| dev | v8d | v9 | v9b | t1 |
|---|---|---|---|---|
| automatic judged micro R / P / F1 | 0.855 / 0.664 / 0.747 | 0.825 / 0.659 / 0.733 | 0.836 / 0.653 / 0.733 | 0.834 / 0.651 / 0.731 |
| lenient F1 | 0.788 | 0.774 | 0.774 | 0.775 |
| production micro F1 | 0.475 | 0.443 | 0.442 | 0.453 |
| rows | 2,083 | 2,034 | 2,075 | 2,134 |

No tree beats v8d yet. GT values v8d has and they lack: t1 40, v9b 37, mostly Xu2024 record altitudes plus some Ustjuzhanin2024 description
and habitat clauses; cause not yet traced. Known t1 bug: an item's place and coords nodes keep only the last one (latitude lost). Not hand-judged.
Commit 6ed31abf overwrote v9 by mistake and crashed v9b at facts; restored in 3cb86290, v9b resumed from saved reading.

## t1 judged by reading (2026-11-06, 3 dev papers, corrected Xu2024 GT)

Every unmatched GT row and extra row read by hand; the disputed values checked in the papers. Extras were judged from species, trait and value, not each against the text.

GT rows 1,326: exact 1,107; same information 105 (parts, wording, GT typos); partial 5; repeats short 46 (value found, fewer record rows); missed 63. Recall 91%.
Misses: sentence sent the measurement question 16; habitat owed per record or to other species 16; repeated line cut as page noise 9; group diagnosis outside the account 8; records unread 9; other 5.
Our rows 2,134: clear junk about 32; wrong owner about 30 (identification key under A. potockyi, comparisons); coordinates and localities as trait rows 49 (true, wrong form). Precision about 95%, F1 about 0.93 (automatic 0.73, production 0.45).
GT errors seen: 9.02, 5.06, 3.08, 1.95-.39, 9.5-1.00, 0.22--0.28, 1.83-2.341.83-2.39, 0.78-0.70, 'terior angles'; Elytra Length 1.33-1.72 is printed as PW.

## t2 and the new evaluator (2026-11-06)

t2 = t1 + three general fixes, all stages fresh: a repeated line that starts with a bold label or ends like a sentence is kept; an
identification key gives no facts (Q-KEY, both orders, treated as a caption; 15 passages on dev, all key text by their openings); non-measurement sentences of a
measurement paragraph also get the description question (16 sentences on dev).

src/prose/prose_judge.py is the hand judgement as a program, using only our rows, the GT and the paper's text, plus nimble. Totals only on held_b. Tested against
prose_judged_t1_dev.json (my labels, line by line; wrong-owner count corrected to 38 on reading the key): agreement 97.5% on GT rows, 96.1% on our unpaired rows.
Rules were adjusted once after reading the disagreements on these same rows, so the agreement is not an independent test. It is lenient: it caught 17 of 32 junk rows and 26 of 38 wrong-owner rows,
so its precision runs high. 'ok' means printed where it belongs, not proved true. On t1 it gives F1 0.923 against about 0.929 by hand.

| prose_judge | recall | precision | F1 | exact | same | repeat | miss | rows |
|---|---|---|---|---|---|---|---|---|
| t1 dev | 0.896 | 0.952 | 0.923 | 1,107 | 81 | 60 | 70 | 2,134 |
| t2 dev | 0.910 | 0.965 | 0.936 | 1,122 | 84 | 61 | 52 | 2,123 |
| v8d held_b | 0.821 | 0.944 | 0.878 | 783 | 54 | 71 | 107 | 1,147 |
| t2 held_b | 0.823 | 0.962 | 0.887 | 794 | 45 | 77 | 99 | 1,178 |

t2 held_b, run once, totals only: production micro 0.528 (v8d 0.531), mean 0.422 (0.417); automatic judged micro 0.803 (0.805), mean 0.580 (0.553). Stages 1,471 s.
Recall is 9 points lower on held_b than dev, so the dev number is not what to expect on new papers. Fixes moved held_b little: precision up, recall flat.
