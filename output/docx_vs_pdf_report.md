# Docx vs PDF (MinerU) structural audit

35 .docx file(s) examined.

## Summary

- **severe**: 14
- **minor**: 1
- **unknown**: 1
- **ok**: 19

Severity meaning:
- **severe** — the docx path LOST a whole table the PDF kept.
- **moderate** — docx collapsed rows inside tables (fewer cells).
- **minor** — cosmetic / repeated header rows only.
- **unknown** — PDF side could not run (no token/converter).

## Per-paper detail

### Barber2017 — severe
- docx: 0 table(s), 0 non-empty cells
- pdf : 2 table(s), 41 non-empty cells
- docx found 0 table(s), PDF found 2 (docx MISSING 2)
- docx has 0 non-empty cells vs PDF 41 (100% fewer — likely collapsed/lost rows)

| # | docx rows×cols (first cell) | pdf rows×cols (first cell) |
|---|---|---|
| 0 | — | 14×2 ('Fig. 1 Relationships between a abundance') |
| 1 | — | 6×4 ('a 1') |

### Cao2024 — severe
- docx: 0 table(s), 0 non-empty cells
- pdf : 2 table(s), 48 non-empty cells
- docx found 0 table(s), PDF found 2 (docx MISSING 2)
- docx has 0 non-empty cells vs PDF 48 (100% fewer — likely collapsed/lost rows)

| # | docx rows×cols (first cell) | pdf rows×cols (first cell) |
|---|---|---|
| 0 | — | 5×8 ('Sample code Hu 1–10 Ho 11–19') |
| 1 | — | 3×105 ('Conductivity(μS cm-1) 20.34 ~') |

### Cappellari2022_S1 — severe
- docx: 8 table(s), 4111 non-empty cells
- pdf : 11 table(s), 3715 non-empty cells
- docx found 8 table(s), PDF found 11 (docx MISSING 3)

| # | docx rows×cols (first cell) | pdf rows×cols (first cell) |
|---|---|---|
| 0 | 52×9 ('Site code') | 52×9 ('Site code') |
| 1 | 263×4 ('Plant species') | 29×4 ('Plant species') |
| 2 | 326×5 ('Pollinator species') | 96×4 ('Conyza canadensis') |
| 3 | 16×6 ('Pollinator family') | 32×4 ('Prunella vulgaris') |
| 4 | 7×5 ('Type of model') | 9×4 ('Verbascum nigrum') |
| 5 | 16×13 ('Ranking') | 326×5 ('Pollinator species') |
| 6 | 29×13 ('Ranking') | 16×6 ('Pollinator family') |
| 7 | 30×9 ('(a) Proboscis length') | 7×5 ('Type of model') |
| 8 | — | 16×13 ('Ranking') |
| 9 | — | 29×13 ('Ranking') |
| 10 | — | 30×9 ('(a) Proboscis length') |

### Cecala2021_S1 — severe
- docx: 7 table(s), 2751 non-empty cells
- pdf : 9 table(s), 2043 non-empty cells
- docx found 7 table(s), PDF found 9 (docx MISSING 2)

| # | docx rows×cols (first cell) | pdf rows×cols (first cell) |
|---|---|---|
| 0 | 15×11 ('Nursery') | 15×9 ('Nursery') |
| 1 | 16×9 ('Nursery') | 16×9 ('Nursery') |
| 2 | 156×11 ('Taxonomy') | 42×7 ('Taxonomy') |
| 3 | 20×10 ('bee collection method') | 24×6 ('Diadasia') |
| 4 | 9×10 ('model') | 90×5 (']') |
| 5 | 12×4 ('Sweep netting (92 spp.)') | 20×9 ('bee collection method') |
| 6 | 98×4 ('plant species name') | 9×9 ('bee collection method') |
| 7 | — | 12×4 ('Sweep netting (92 spp.)') |
| 8 | — | 98×4 ('plant species name') |

### Eckert2023_S1 — severe
- docx: 7 table(s), 3499 non-empty cells
- pdf : 14 table(s), 2822 non-empty cells
- docx found 7 table(s), PDF found 14 (docx MISSING 7)

| # | docx rows×cols (first cell) | pdf rows×cols (first cell) |
|---|---|---|
| 0 | 15×6 ('Region') | 15×5 ('Region') |
| 1 | 135×12 ('Subfamily') | 70×8 ('Subfamily') |
| 2 | 148×4 ('Author(s)') | 61×8 ('Subfamily') |
| 3 | 104×7 ('Suborder') | 27×4 ('Author(s)') |
| 4 | 12×5 ('Taxon') | 28×4 ('Author(s)') |
| 5 | 37×10 ('Midlands') | 3×4 ('Author(s)') |
| 6 | 11×7 ('Formicidae') | 26×4 ('Heinze et al.') |
| 7 | — | 30×4 ('Author(s)') |
| 8 | — | 26×4 ('Author(s)') |
| 9 | — | 72×7 ('Suborder') |
| 10 | — | 29×7 ('Suborder') |
| 11 | — | 12×4 ('Taxon') |
| 12 | — | 37×10 ('Midlands') |
| 13 | — | 10×7 ('Formicidae') |

### Figueroa2021_S1 — severe
- docx: 4 table(s), 615 non-empty cells
- pdf : 6 table(s), 1064 non-empty cells
- docx found 4 table(s), PDF found 6 (docx MISSING 2)
- docx has 615 non-empty cells vs PDF 1064 (42% fewer — likely collapsed/lost rows)

| # | docx rows×cols (first cell) | pdf rows×cols (first cell) |
|---|---|---|
| 0 | 14×2 ('In planting') | 14×2 ('In planting') |
| 1 | 111×3 ('Bee species') | 110×3 ('Bee species') |
| 2 | 19×5 ('Primers and source') | 18×1 ('Primers and source') |
| 3 | 27×6 ('Pathogen') | 58×10 ('Family') |
| 4 | — | 27×6 ('Pathogen') |
| 5 | — | 25×6 ('Pathogen') |

### Forrest2015 — severe
- docx: 0 table(s), 0 non-empty cells
- pdf : 7 table(s), 206 non-empty cells
- docx found 0 table(s), PDF found 7 (docx MISSING 7)
- docx has 0 non-empty cells vs PDF 206 (100% fewer — likely collapsed/lost rows)

| # | docx rows×cols (first cell) | pdf rows×cols (first cell) |
|---|---|---|
| 0 | — | 11×3 ('Collection, supplemented by museum speci') |
| 1 | — | 7×5 ('Body size') |
| 2 | — | 5×1 ('Species observedOrganic farm') |
| 3 | — | 15×3 ('60*(a) (b)') |
| 4 | — | 5×6 ('0·6') |
| 5 | — | 10×5 ('farm') |
| 6 | — | 16×8 ('Proportion') |

### GibbParr2013_S1 — severe
- docx: 1 table(s), 581 non-empty cells
- pdf : 3 table(s), 845 non-empty cells
- docx found 1 table(s), PDF found 3 (docx MISSING 2)
- docx has 581 non-empty cells vs PDF 845 (31% fewer — likely collapsed/lost rows)

| # | docx rows×cols (first cell) | pdf rows×cols (first cell) |
|---|---|---|
| 0 | 65×10 ('Habitat') | 40×10 ('Species') |
| 1 | — | 48×9 ('1') |
| 2 | — | 37×10 ('Ochetellussp. A') |

### Habustova2017_S1 — severe
- docx: 10 table(s), 1505 non-empty cells
- pdf : 11 table(s), 1484 non-empty cells
- docx found 10 table(s), PDF found 11 (docx MISSING 1)

| # | docx rows×cols (first cell) | pdf rows×cols (first cell) |
|---|---|---|
| 0 | 11×3 ('2014') | 11×3 ('2014') |
| 1 | 33×8 ('Tribe') | 33×8 ('Tribe') |
| 2 | 33×8 ('Tribe') | 33×8 ('Tribe') |
| 3 | 26×8 ('Tribe') | 26×8 ('Tribe') |
| 4 | 17×8 ('Tribe') | 17×8 ('Tribe') |
| 5 | 17×8 ('Tribe') | 17×8 ('Tribe') |
| 6 | 17×8 ('Tribe') | 14×8 ('Tribe') |
| 7 | 17×8 ('Tribe') | 3×8 ('Callistini') |
| 8 | 17×8 ('Tribe') | 17×8 ('Tribe') |
| 9 | 7×8 ('Tribe') | 17×8 ('Tribe') |
| 10 | — | 7×8 ('Tribe') |

### Korosi2022_S1 — severe
- docx: 2 table(s), 1070 non-empty cells
- pdf : 3 table(s), 1077 non-empty cells
- docx found 2 table(s), PDF found 3 (docx MISSING 1)

| # | docx rows×cols (first cell) | pdf rows×cols (first cell) |
|---|---|---|
| 0 | 105×10 ('Species') | 105×10 ('Species') |
| 1 | 4×5 ('Reference dataset') | 4×5 ('Reference dataset') |
| 2 | — | 5×7 ('Aph hyp') |

### Melo2021_S1 — severe
- docx: 1 table(s), 1117 non-empty cells
- pdf : 10 table(s), 1071 non-empty cells
- docx found 1 table(s), PDF found 10 (docx MISSING 9)

| # | docx rows×cols (first cell) | pdf rows×cols (first cell) |
|---|---|---|
| 0 | 184×16 ('SUBFAMILY') | 14×16 ('SUBFAMILYSpecies') |
| 1 | — | 19×14 ('Borgmeier, 1957') |
| 2 | — | 38×15 ('novogranadensis Mayr, 1870') |
| 3 | — | 19×13 ('Emery, 1894') |
| 4 | — | 18×15 ('Pheidole (grupo diligens) sp.12') |
| 5 | — | 18×14 ('sp.14') |
| 6 | — | 21×16 ('Sericomyrmex sp.1') |
| 7 | — | 20×13 ('1912') |
| 8 | — | 18×15 ('Odontomachus haematodus (Linnaeus, 1758)') |
| 9 | — | 3×16 ('Smith, 1877)Pseudomyrmex tenuis(Fabriciu') |

### Nunes2016_S1 — severe
- docx: 1 table(s), 1416 non-empty cells
- pdf : 3 table(s), 1397 non-empty cells
- docx found 1 table(s), PDF found 3 (docx MISSING 2)

| # | docx rows×cols (first cell) | pdf rows×cols (first cell) |
|---|---|---|
| 0 | 59×24 ('Species') | 15×24 ('Species') |
| 1 | — | 21×25 ('Canthidium sp 10') |
| 2 | — | 27×24 ('Eurysternus nigrovirens') |

### Oliveira2022_S1 — severe
- docx: 1 table(s), 1051 non-empty cells
- pdf : 6 table(s), 1988 non-empty cells
- docx found 1 table(s), PDF found 6 (docx MISSING 5)
- docx has 1051 non-empty cells vs PDF 1988 (47% fewer — likely collapsed/lost rows)

| # | docx rows×cols (first cell) | pdf rows×cols (first cell) |
|---|---|---|
| 0 | 53×20 ('Ant species') | 34×19 ('Ant species') |
| 1 | — | 68×20 ('4') |
| 2 | — | 9×9 ('WL') |
| 3 | — | 9×9 ('CL') |
| 4 | — | 9×9 ('WL') |
| 5 | — | 8×8 ('LEG') |

### Wang2021_S1 — severe
- docx: 3 table(s), 298 non-empty cells
- pdf : 4 table(s), 301 non-empty cells
- docx found 3 table(s), PDF found 4 (docx MISSING 1)

| # | docx rows×cols (first cell) | pdf rows×cols (first cell) |
|---|---|---|
| 0 | 17×6 ('Species') | 1×11 ('Low') |
| 1 | 12×12 ('Low VP') | 17×6 ('Species') |
| 2 | 10×7 ('Response variables') | 12×12 ('VP') |
| 3 | — | 9×6 ('Activity density') |

### Wang2021_S1(1) — minor
- docx: 4 table(s), 890 non-empty cells
- pdf : 3 table(s), 880 non-empty cells
- docx found 4 table(s), PDF found 3 (docx has 1 extra)

| # | docx rows×cols (first cell) | pdf rows×cols (first cell) |
|---|---|---|
| 0 | 12×6 ('Study area') | 30×5 ('Study area') |
| 1 | 7×6 ('Habitat type') | 19×2 ('Land use types') |
| 2 | 19×3 ('Land use types') | 119×6 ('Specise') |
| 3 | 120×7 ('Specise') | — |

### Graf2021_S1 — unknown
- docx: 11 table(s), 5920 non-empty cells
- MinerU failed: Server disconnected without sending a response.

| # | docx rows×cols (first cell) | pdf rows×cols (first cell) |
|---|---|---|
| 0 | 11×4 ('Codes') | — |
| 1 | 49×4 ('Responses') | — |
| 2 | 49×4 ('Responses') | — |
| 3 | 49×4 ('Responses') | — |
| 4 | 33×4 ('Responses') | — |
| 5 | 321×12 ('Bee species') | — |
| 6 | 326×4 ('Bee species') | — |
| 7 | 11×12 ('Areas') | — |
| 8 | 21×5 ('Response variable/Predictor variable') | — |
| 9 | 21×5 ('Response variable/Predictor variable') | — |
| 10 | 12×9 ('Areas') | — |

### Araujo2021_S1 — ok
- docx: 1 table(s), 210 non-empty cells
- pdf : 1 table(s), 105 non-empty cells

| # | docx rows×cols (first cell) | pdf rows×cols (first cell) |
|---|---|---|
| 0 | 30×7 ('Bee species') | 15×7 ('Bee species') |

### Araujo2021_S2 — ok
- docx: 1 table(s), 182 non-empty cells
- pdf : 1 table(s), 182 non-empty cells

| # | docx rows×cols (first cell) | pdf rows×cols (first cell) |
|---|---|---|
| 0 | 26×7 ('Wasp species') | 26×7 ('Wasp species') |

### Arnan2012 — ok
- docx: 2 table(s), 496 non-empty cells
- pdf : 2 table(s), 496 non-empty cells

| # | docx rows×cols (first cell) | pdf rows×cols (first cell) |
|---|---|---|
| 0 | 31×8 ('Species') | 31×8 ('Species') |
| 1 | 32×8 ('Species') | 31×8 ('Species') |

### Batista2024_S1 — ok
- docx: 4 table(s), 460 non-empty cells
- pdf : 4 table(s), 290 non-empty cells

| # | docx rows×cols (first cell) | pdf rows×cols (first cell) |
|---|---|---|
| 0 | 9×10 ('Dry season') | 9×6 ('Dry season') |
| 1 | 88×3 ('Species') | 40×3 ('Species') |
| 2 | 2×8 ('Response') | 3×8 ('Response') |
| 3 | 21×5 ('Species') | 21×5 ('Species') |

### Beyer2021_S1 — ok
- docx: 9 table(s), 1537 non-empty cells
- pdf : 9 table(s), 1433 non-empty cells

| # | docx rows×cols (first cell) | pdf rows×cols (first cell) |
|---|---|---|
| 0 | 11×3 ('Habitat type') | 11×3 ('Habitat type') |
| 1 | 32×12 ('early summer') | 32×12 ('early summer') |
| 2 | 67×5 ('species') | 67×5 ('species') |
| 3 | 10×6 ('species') | 10×6 ('species') |
| 4 | 12×12 ('Models') | 12×11 ('Models') |
| 5 | 55×9 ('Response variable') | 60×7 ('Response variable') |
| 6 | 6×9 ('Response variable') | 6×9 ('Response variable') |
| 7 | 3×9 ('Models') | 3×9 ('Models') |
| 8 | 3×5 ('Mass-flowering crop') | 3×5 ('Mass-flowering crop') |

### Cajaiba2022_S1 — ok
- docx: 6 table(s), 2679 non-empty cells
- pdf : 6 table(s), 2416 non-empty cells

| # | docx rows×cols (first cell) | pdf rows×cols (first cell) |
|---|---|---|
| 0 | 6×3 ('Ecosystems') | 6×2 ('Ecosystems') |
| 1 | 15×3 ('Variables') | 15×3 ('Variables') |
| 2 | 16×3 ('Functional traits') | 15×2 ('Functional traits') |
| 3 | 132×8 ('Morphospecies/Species') | 132×8 ('Morphospecies/Species') |
| 4 | 326×6 ('Table A - Comparisons for Abundance and ') | 268×5 ('Table A - Comparisons for Abundance and ') |
| 5 | 14×6 ('ES_FT: Ecosystem specificity') | 14×6 ('ES_FT: Ecosystem specificity') |

### Cajaiba2023_S1 — ok
- docx: 6 table(s), 2679 non-empty cells
- pdf : 6 table(s), 2419 non-empty cells

| # | docx rows×cols (first cell) | pdf rows×cols (first cell) |
|---|---|---|
| 0 | 6×3 ('Ecosystems') | 6×2 ('Ecosystems') |
| 1 | 15×3 ('Variables') | 15×3 ('Variables') |
| 2 | 16×3 ('Functional traits') | 15×2 ('Functional traits') |
| 3 | 132×8 ('Morphospecies/Species') | 132×8 ('Morphospecies/Species') |
| 4 | 326×6 ('Table A - Comparisons for Abundance and ') | 271×5 ('Table A - Comparisons for Abundance and ') |
| 5 | 14×6 ('ES_FT: Ecosystem specificity') | 14×6 ('ES_FT: Ecosystem specificity') |

### Cao2024_S1 — ok
- docx: 1 table(s), 400 non-empty cells
- pdf : 1 table(s), 400 non-empty cells

| # | docx rows×cols (first cell) | pdf rows×cols (first cell) |
|---|---|---|
| 0 | 80×5 ('Species') | 80×5 ('Species') |

### Cawood2026_S1 — ok
- docx: 2 table(s), 474 non-empty cells
- pdf : 2 table(s), 473 non-empty cells

| # | docx rows×cols (first cell) | pdf rows×cols (first cell) |
|---|---|---|
| 0 | 46×6 ('Spp code') | 46×6 ('Spp code') |
| 1 | 22×9 ('Spp Code') | 22×9 ('Spp Code') |

### Derhe2016_S1 — ok
- docx: 6 table(s), 680 non-empty cells
- pdf : 6 table(s), 686 non-empty cells

| # | docx rows×cols (first cell) | pdf rows×cols (first cell) |
|---|---|---|
| 0 | 40×9 ('Species') | 40×9 ('Species') |
| 1 | 22×9 ('Fixed effect: Restoration age') | 22×7 ('Response variable') |
| 2 | 5×3 ('Global model') | 5×3 ('Global model') |
| 3 | 5×6 ('Measure') | 5×6 ('Measure') |
| 4 | 6×12 ('P') | 10×8 ('P') |
| 5 | 33×4 ('Predictor') | 33×4 ('Predictor') |

### Espinosa2023_S1 — ok
- docx: 8 table(s), 1630 non-empty cells
- pdf : 8 table(s), 1685 non-empty cells

| # | docx rows×cols (first cell) | pdf rows×cols (first cell) |
|---|---|---|
| 0 | 74×8 ('Sampling point (stream)') | 74×8 ('Sampling point (stream)') |
| 1 | 11×8 ('Type') | 6×8 ('Type') |
| 2 | 29×6 ('Traits') | 29×6 ('Traits') |
| 3 | 30×4 ('Genus') | 30×4 ('Genus') |
| 4 | 15×3 ('Variable') | 22×3 ('Variable') |
| 5 | 10×6 ('Matrix') | 19×2 ('Matrix') |
| 6 | 11×6 ('Partition') | 11×5 ('Partition') |
| 7 | 85×6 ('Item') | 166×6 ('Item') |

### GarciaAtencia2024_S1 — ok
- docx: 1 table(s), 594 non-empty cells
- pdf : 1 table(s), 594 non-empty cells

| # | docx rows×cols (first cell) | pdf rows×cols (first cell) |
|---|---|---|
| 0 | 33×18 ('Species') | 33×18 ('Species') |

### Gossner2013_S1 — ok
- docx: 7 table(s), 5087 non-empty cells
- pdf : 7 table(s), 5335 non-empty cells

| # | docx rows×cols (first cell) | pdf rows×cols (first cell) |
|---|---|---|
| 0 | 5×6 ('Decay stage:') | 3×5 ('0') |
| 1 | 753×6 ('Family') | 999×6 ('Family') |
| 2 | 25×3 ('Age (million years)') | 25×3 ('Age (million years)') |
| 3 | 16×20 ('Variable type') | 15×13 ('Variable type') |
| 4 | 15×14 ('Variable type') | 15×9 ('Variable type') |
| 5 | 9×19 ('Phylogenetic') | 9×13 ('Variable') |
| 6 | 8×13 ('Body size') | 8×9 ('Variable') |

### Guareschi2015_S1 — ok
- docx: 9 table(s), 4281 non-empty cells
- pdf : 9 table(s), 4109 non-empty cells

| # | docx rows×cols (first cell) | pdf rows×cols (first cell) |
|---|---|---|
| 0 | 41×4 ('Code') | 41×2 ('Code') |
| 1 | 81×41 ('Traits') | 81×41 ('Traits') |
| 2 | 26×7 ('Threshold') | 25×6 ('Threshold') |
| 3 | 25×5 ('Network') | 23×4 ('Network') |
| 4 | 27×12 ('βSIM') | 25×10 ('Network') |
| 5 | 26×3 ('Network') | 23×2 ('Network') |
| 6 | 26×3 ('Network') | 23×2 ('Network') |
| 7 | 13×10 ('βSIM') | 12×7 ('Network') |
| 8 | 14×17 ('βSIM') | 12×7 ('Network') |

### Harmon2013_S1 — ok
- docx: 1 table(s), 340 non-empty cells
- pdf : 1 table(s), 340 non-empty cells

| # | docx rows×cols (first cell) | pdf rows×cols (first cell) |
|---|---|---|
| 0 | 85×4 ('species') | 85×4 ('species') |

### Leong2023_S1 — ok
- docx: 4 table(s), 470 non-empty cells
- pdf : 4 table(s), 495 non-empty cells

| # | docx rows×cols (first cell) | pdf rows×cols (first cell) |
|---|---|---|
| 0 | 8×2 ('Trait &amp; Measurement') | 9×2 ('Trait &amp; Measurement') |
| 1 | 31×10 ('Species') | 35×10 ('Species') |
| 2 | 7×6 ('Estimate') | 7×6 ('Estimate') |
| 3 | 30×4 ('PC1') | 28×4 ('PC1') |

### Russo2017_S1 — ok
- docx: 1 table(s), 1925 non-empty cells
- pdf : 1 table(s), 1071 non-empty cells

| # | docx rows×cols (first cell) | pdf rows×cols (first cell) |
|---|---|---|
| 0 | 108×19 ('Species') | 108×11 ('Species') |

### Stemkovski2020_S1 — ok
- docx: 6 table(s), 950 non-empty cells
- pdf : 6 table(s), 814 non-empty cells

| # | docx rows×cols (first cell) | pdf rows×cols (first cell) |
|---|---|---|
| 0 | 4×5 ('Phenophase') | 4×5 ('Phenophase') |
| 1 | 19×6 ('Site name') | 19×6 ('Site name') |
| 2 | 68×10 ('Family') | 68×8 ('Family') |
| 3 | 11×4 ('Species') | 11×4 ('Species') |
| 4 | 9×5 ('Predictor') | 9×5 ('Predictor') |
| 5 | 10×5 ('Model') | 10×4 ('Model') |

### Zhao2024_S1 — ok
- docx: 7 table(s), 1227 non-empty cells
- pdf : 7 table(s), 1050 non-empty cells

| # | docx rows×cols (first cell) | pdf rows×cols (first cell) |
|---|---|---|
| 0 | 19×7 ('Elevational band') | 19×3 ('Elevational band') |
| 1 | 44×9 ('Subfamily') | 44×8 ('Subfamily') |
| 2 | 7×3 ('Functional trait') | 7×3 ('Functional trait') |
| 3 | 44×8 ('Subfamily') | 44×7 ('Subfamily') |
| 4 | 33×8 ('Subfamily') | 32×7 ('Subfamily') |
| 5 | 13×5 ('Low elevation') | 13×5 ('Low elevation') |
| 6 | 5×4 ('Low elevation') | 5×4 ('Low elevation') |
