# 8. Scoring, tests and GT decisions

Fixes 1–7 change the extraction. This file is about knowing whether a change is real, and about decisions only you can take.

## A. The scorer misses true pairs — done 2026-11-10

**What the evidence turned out to be.** Two of the five examples first listed here ("Dispersal\ncapacity", "Weber s length") were not scorer misses: the scorer pairs them (Hendriks2013 0.989, Fontanilla2019 263 / 263). My `beyond_gt.py` read the pairs back from the reports with a regex that lost names printed with an escaped line break or in double quotes. Fixed (the pairs are read as Python literals): 687 of 121,720 tuning rows moved from "beyond the GT" to matched.

The real list (`src/stats/name_misses.py`: our rows beyond the GT whose species and value equal a missed GT row, 47 name pairs on tuning papers) is mostly extraction, not scoring:

| Kind | Example | Rows | Where it belongs |
|---|---|---|---|
| heading words in our name | "Dispersal predictor Body length" (Raine2018) | 3,382 | fix 2 |
| statistic words in our name | "head width standard deviation" (CamargoVanegas2024) | 1,473 | fix 2 / statistic |
| codes not spelled out | "HW (mm)" (Luo2023), "Biol 1" (Guareschi2015) | ~1,000 | fixes 2, 5 |
| category columns | "LF4" (Guariento2020), "Coprophagous" (Wallon2024) | ~900 | fix 5 |
| the name lacks the measure | "Free-flight chamber" (Tran2022), "Body" (Xu2024) | ~20 | fix 2 / prose |
| **scorer** | "Bodysize" / "Body size", "Weber’s" / "Weber's", "(days)" | ~400 | done here |

**Built** (`source/trait_name_matcher.py`, code only; `EVAL_NAME_NORM=0` gives the old normaliser):
- curly and straight apostrophes read the same;
- time units in a bracket are units ("(days)", "(h)", "(years)"; not "(min)", which is also minimum);
- the words run together are compared when nothing else pairs ("Bodysize", "inter-tegular distance"), only when one GT name matches.

Tried and dropped: taking off " #2". Eckert2023 0.795 → 0.689 and Lizee2016 0.686 → 0.490: "Femur length (mm) #2" is another leg under a heading the name lost, not the same trait.

**Rescore** (papers whose pairs change; `src/stats/norm_compare.py`, `score_8a.py`): dev 3 papers unchanged; held_a 5 papers, Gathof2022 0.870 → 0.963, the rest unchanged; held_b none; grit 13 papers, sum of F1 8.364 → 8.740 (+0.003 on the 147-paper mean). No paper falls.

**Not built: the nimble three-way judge.** No missed pair on the tuning papers needs it; the remaining misses are names we write wrong, and a judge would only hide them.

## B. Testing for papers we have not seen

- Tuning: 109 dev + held_a, Jakub tune.
- Test, run once per fix: held_b, Jakub test, grit-only. Totals only.
- **A fresh set.** held_b has been run many times. I suggest 10–15 new papers from other insect or arthropod groups and journals, GT made by you or a volunteer, never used for tuning. Until then, precision on new papers is estimated by judging a random sample of rows against the text, as done on 2026-11-10.
- Each fix reports how many papers and tables it fired on per set, so a one-paper fix is visible.

## C. GT decisions waiting for you

| Paper | Issue | My suggestion |
|---|---|---|
| Harmon2013 | values are e^(printed ln); 9 names keep a footnote star | printed ln values, stars removed (you said not now) |
| Mirzaee2023 | SD rows named "Ootheca SD …"; SD of incubation 2.7, printed 1.7 | name as the other rows with statistic SD; 1.7 |
| Viza2023 | category words instead of printed scores; two categories joined in one value | keep the categories (fix 5 writes that shape); split the joined values |
| Noriega2023 (grit) | 278 values are Excel dates | restore the printed numbers |
| Xia2022, Xu2024 | typos against the printed text | fix to the print |
| Jakub sets | a range is two rows (min, max); ours is one range row | no GT change; the judge already splits ranges |

## D. Housekeeping

- Commit the statistics scripts (`src/stats/`) and this plan folder.
- v19, v20 and v21 were not adopted; fix 5 replaces v20. I would leave their folders and note it in the README of `src/`.
- A paper whose markdown changes must be re-read in a fresh root (Figueroa2021): make that a script, `reread_paper.sh`.
