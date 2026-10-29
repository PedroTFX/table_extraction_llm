# Papers whose GT needs supplementary material (2026-10-29)

Checked per GT row against the paper's own markdown (`<paper>_full.md`): is the organism printed
anywhere, and is a numeric value printed anywhere (a table cell or the text)? A row with neither
in the paper can only come from material the markdown does not hold. "The paper cites" lists what
the paper itself names (counted mentions). Read-only check, no model.

## Found and added (2026-10-29; F1 after the rerun, grit)

Arnan2014 (S1.xlsx, 0.644), Wijas2021 (S1.csv, 0.442), Ambrozova2022 (S1.docx, 0.930), Crabot2022
(S2.xlsx from the data repository, 0.862), Tielens2020 (S2.xlsx, 0.397), Tonelli2021 (S1.pdf + S2.xlsx,
0.154), Schat2024 (S1.csv, still 0). Orr2024 needed no supplement: its S1 was in the paper, the scorer
missed the values (float noise, fixed: 0.919). Fiedler2021 and Scalercio2020: the files found repeat
what the paper already had.

## Mostly in a supplement (half or more of the GT rows)

| Paper | Set | GT rows | Not in the paper | F1 now (grit / 109) | The paper cites |
|---|---|---|---|---|---|
| Arnan2014 | grit | 1,352 | 100% | 0.00 | Supporting Information: Appendix S1, S2; Tables S2, S4 |
| Wijas2021 | both | 487 | 100% | 0.00 / 0.00 | Supporting Information; Dryad (10.5061/…) |
| DelToro2015 | grit | 701 | 99% | 0.00 | Appendix S1, S2 |
| Orr2024 | 109 | 12,838 | 99% | — / 0.01 | Supplementary tables; Dryad |
| Fiedler2021 | both | 1,916 / 1,569 | 95–97% | 0.56 / 0.67 | Appendix S1, S2 |
| Ambrozova2022 | grit | 480 | 78% | 0.00 | Supporting Information: Tables S3, S4, S9, S10 |
| Crabot2022 | grit | 722 | 73% | 0.00 | Tables S1–S4; Dryad |
| Schat2024 | grit | 4,330 | 55% | 0.00 | Appendix S1; Dryad (the measurements per specimen) |
| Tonelli2021 | both | 1,106 | 52% | 0.00 / 0.00 | Supplementary material, File S3 |

## Partly in a supplement (30–50%)

| Paper | Set | GT rows | Not in the paper | F1 now (grit / 109) | The paper cites |
|---|---|---|---|---|---|
| Tielens2020 | grit | 142 | 46% | 0.13 | Supporting Information: Tables S1, S4, S7, S8 |
| Scalercio2020 | both | 1,158 | 43% | 0.74 / 0.74 | Appendix S1; Dryad; Tables S4, S6 |
| Figueroa2021 | both | 246 | 42% | 0.00 / 0.00 | Tables S3–S6 |

## Flagged by the check but not a supplement

- **Noriega2023** (60% flagged): the GT's species names have typos ('Digitonthoagus gazla' for
  the printed 'Digitonthophagus_gazella'); the values are in the paper.
- **Harmon2013** (100% flagged): Table S1 is already in its markdown (Harmon2013_S1.docx). Species are
  printed as epithets under subgenus labels ('*ardens*'), so the check missed them; the GT's tongue
  lengths (8.602045…) look computed from the printed ln(tongue length).
- **McCravy2019** (76%): genus and epithet are printed in separate cells; no supplement cited.
- **B.Wang2021 / Wang2021, Gonzalez2016, Gutiérrez‐Chacón2019** (31–42%): names printed with a
  subgenus or as 'sp1' where the GT writes 'sp'; B.Wang and Gonzalez already score 0.94–1.00.

## Not a supplement either: GT taken from the running text

Taxonomic papers whose GT comes from the species descriptions in the text, not from any table:
Baine2024, Liu2024, RamosGonzalez2024, Ustjuzhanin2024, Xia2022, Xu2024 (all F1 0.00).

Sources: `supplement_needed.py` and `reachable.py` (scratchpad, read-only), run on the v12 output
of each set.
