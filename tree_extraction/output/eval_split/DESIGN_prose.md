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
