# Column-identity route: result and decision (run 2026-11-26_1518)

**Decision: not adopted.** The route failed one of its six precommitted criteria (precision). R3abc, Stage 2
(PROMPT2), `legend_inventory`, the decoders and production are unchanged. `dk.SAFE_TAGS` stays opt-in. No revised
test is authorised; the hypothesis below is recorded for a separate experiment.

Code: `src/v24/legend_identity.py`. Pool, gold and criteria were committed before the model call (47088870,
dfa2cb91, 01f823f6). Run and report: 6c4c9244 (`identity_run_2026-11-26_1518.json`,
`IDENTITY_REPORT_2026-11-26_1518.txt`).

## What was tested

The diagnosis (`SELECTOR_MISSES_2026-11-26.txt`) traced five of R3abc's seven validated failures to its
header-word requirement. The route offers gemma (gemma4:e4b-it-qat, temperature 0) only the pairs that R3abc
rejects for lacking a header word, with every other R3abc gate unchanged. For each column, gemma names its
evidence (names the variable, cross-reference, meanings fit, or insufficient) and says whether the passage decodes
the column. Code then links a pair when the answer is "decodes" and the evidence is not "insufficient".

- **Pool (82 tuning papers, safe cut, no model):** 5,610 pairs in 643 units of 64 papers.
  - 5,417 of them match on numbers only, and none of the validated failures is among them.
  - All six validated failure columns are in the 184 pairs with two or more letter codes.
- **Evaluation set:** 281 pairs in 161 units, labelled by Claude by eye before the run (`identity_gold_2026-11-26.csv`).
  - **Letter (scored):** the letter-code pool without Taillefer2018 (upstream): 31 yes, 72 no.
  - **Upstream (run, not scored):** Wallon2024's glued "Dispersaldisp" column and its header-less continuation: 8 pairs.
  - **Not-target:** every numeric pool pair on the 11 key columns whose codes the papers never define: 63, all no.
  - **Decoy:** every numeric pool pair on the calibration's judged decoy columns: 67, all no.
  - **Sample:** a seeded sample of other numeric pairs, Tonelli2021 and Taillefer2018 left out: 40, all no.

## Result against the precommitted criteria

| Criterion | Required | Result | |
|---|---|---|---|
| C1 validated failure columns linked | ≥ 5 of 6 | 6 of 6 (Graf t8c2, Ambsperg t0c4 and t0c5, Wang t1c4 and t1c5, Eckert t4c3) | pass |
| C2 letter-stratum precision | ≥ 0.85 | **0.69** (24 of 35 links) | **fail** |
| C3 letter-stratum recall | ≥ 0.70 | 0.77 (24 of 31) | pass |
| C4 not-target links | ≤ 1 | 0 of 63 | pass |
| C5 decoy links | ≤ 2 | 0 of 67 | pass |
| C6 sample links | ≤ 2 | 0 of 40 | pass |

The route passes only if all six hold, so it fails. The failure is substantive: almost a third of its links in the
stratum it was built for are wrong. The five passes don't offset it.

Other counts:
- Every column got an answer.
- No answer said "decodes" with "insufficient" evidence.
- The upstream stratum (not scored) got 7 links of 8.
- Evidence types of the 35 scored links: names the variable 17, meanings fit 16, cross-reference 2.

## The 11 false links

| # | Pair | Column holds | Evidence given | Error type |
|---|---|---|---|---|
| 1 | Luo2023 p80 → t3c0 (header empty) | park names (Baita, Chenshou, …) | names the variable | named entities mentioned, not defined |
| 2 | Mirzaee2023 p100 → t0c0 "Country" | country names | meanings fit | named entities mentioned, not defined |
| 3 | Mirzaee2023 p115 → t0c0 | country names | meanings fit | named entities mentioned, not defined |
| 4 | Mirzaee2023 p19 → t0c0 | country names | meanings fit | named entities mentioned, not defined |
| 5 | Mirzaee2023 p84 → t0c0 | country names | meanings fit | named entities mentioned, not defined |
| 6 | Noriega2023 p18 → t3c8 "Continent" | continent names | names the variable | named entities mentioned, not defined |
| 7 | Tsai2020 p29 → t0c0 "Region" | site names | names the variable | named entities mentioned, not defined |
| 8 | Tsai2020 p82 → t0c0 | site names | names the variable | named entities mentioned, not defined |
| 9 | Tsai2020 p90 → t0c0 | site names | names the variable | named entities mentioned, not defined |
| 10 | Pessoa2017 p104 → t1c0 "Group" | A, B | names the variable | figure colour key: says which colour each group has, not what the groups are |
| 11 | Raine2018 t3r1c6 "Sex (F, Maj M, Min M)" → t4c2 "Sex" | F, M | names the variable | a header enumeration: lists the codes without meanings |

In the nine named-entity cases, the passage mentions the same places that the column holds, and gemma took the
mention for a definition. Pessoa's colour key and Raine's header enumeration are separate error types. A
safeguard against named entities would not address them.

## The 7 misses

| # | Pair | Codes the column holds | Gemma's reason (short) | Group |
|---|---|---|---|---|
| 1 | Cappellari2022 p129 → t0c0 "Category" | Apis, Temp, FRic, TSim and their interaction terms | not every code in the column is defined | variable names, partly defined |
| 2 | Cappellari2022 p88 → t0c0 | same | same | variable names, partly defined |
| 3 | Wallon2024 t1r2 → t6c1 "Trait" | ActivDay, Hdisp, Ldisp, Body size, … | not every code in the column is defined; the same unit's link to t12c1 was made | variable names, partly defined |
| 4 | Oliveira2022 p57 → t1c0 "Category" | Dg, Dq, Em, Pr (all four defined) | the passage does not say what "Category" records | complete legend, generic header |
| 5 | Tonelli2021 p35 → t1c2 "Data Type" | Qual, Quan (both defined) | the passage does not say what "Data Type" records | complete legend, generic header |
| 6 | Eckert2023 t6r103 → t6c5 "Habitat position" (own table) | Soil, Litter, Veg | the passage "only mentions the column"; the same unit's link to t4c3 with the same codes was made | own-table note refused |
| 7 | Eckert2023 t6r72 → t6c5 (own table) | Soil, Litter, Veg | turned the "printed with its own table" fact against the link; its link to t4c3 was made | own-table note refused |

A correction to my first summary of this run: I called misses 1–5 all variable-name columns refused for
incomplete definitions. That holds only for 1–3. Misses 4 and 5 are complete legends that gemma refused because
the header is generic. The misses need reasoning of their own, apart from the false-link problem.

## Limits of the explanation

- **The named-entity account is a hypothesis.** It rests on 9 cases from 4 papers (Mirzaee 4, Tsai 3, Luo 1,
  Noriega 1) and has not been tested. It must not become a "full words" rule: full-word categorical labels can
  be defined by a passage, and some correct links here have word values (Eckert Soil/Litter/Veg, Wallon's trait
  names).
- **Gemma is not consistent on near-identical pairs.** Eckert's table-6 notes link table 4's column but refuse
  their own table's column with the same codes. Wallon t1r2 links t12c1 but refuses t6c1. One run at
  temperature 0 does not measure this variance.
- **Scoring is at pair level only.** The codes gemma returned were not scored. Some are good (Ambsperg's compound
  W/S and M(O), which R3abc's parser misses). Some are malformed (Wallon p93's "ActDay: diurnal").
- **The gold is Claude's, by eye, and not yet checked by the user.** Two conventions in it are judgement calls:
  - a variable abbreviation decodes a column of variable names (as in gold v4.1);
  - Kovacs2008's mated/unmated groups count as a "yes".
- **Scope:**
  - The numeric part of the pool (5,426 pairs, 574 units) was run only on 170 control and sample pairs. Zero links
    there does not show the route is safe on the whole numeric pool.
  - Taillefer2018, Tonelli2021's numeric pairs and the parser cases (Cappellari's spacing, Espinosa's lowercase
    code) were outside this test.
  - The result holds for the 82 tuning papers and this one model.

## For a separate experiment (not authorised)

The error analysis points to one testable hypothesis: a named-entity safeguard. Mention of the entities a column
holds (places, sites, parks, regions, continents) is not a definition of what the column records. A test of it
would need four things:
- a precise statement of the safeguard;
- the successful cases with full-word categorical labels kept as positives;
- hard negatives, where a passage mentions the same entities without defining the column;
- criteria and gold committed before the run.

Pessoa's colour key, Raine's header enumeration and the seven misses (three groups) are separate questions. They
must not be folded into that test.
