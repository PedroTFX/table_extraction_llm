# 1. Units in the unit field

## The problem

The template wants the unit of a numeric value in `measurementUnit`. On the rows the scorer matched we set it on 513 of 124,332 tuning rows; the GT gives one on 98,251 (79%).

## Step 0: where the unit is (done 2026-11-10, `src/stats/units_gt.py`)

No layer reads a unit from a header. The column tagger writes `measurementUnit` only for a column whose cells are units, and the header-parts step (v11) only for coded columns. The meaning step drops a bracket when it spells a code out ("BL (µm)" → "body length"), so the unit is lost before assembly.

Where the tuning GT's units are printed, by the largest papers:

| Where | Example | GT rows |
|---|---|---|
| the column's header, lost by the meaning step | Orr2024 "BL (µm)", Mirzaee2023 "Width (mm)" | ~14.5k |
| the legend entry of the column's code | Noriega2023 "HL  Head length (mm)" | 34.6k |
| a heading over several columns | Zhao2024 "Functional traits (mm)" | 0.3k |
| the methods text only | Raine2018 "measurements accurate to ±0.005 mm"; Ji2024 | ~41k |
| "ratio", a GT habit for relative measures (not in the template) | Fontanilla2019, Oliveira2022 | 20.7k |

The GT also leaves a printed unit blank at times (Tonelli2021 "Hind tibiae lenght (mm)": GT unit empty); the scorer counts our unit there as a disagreement.

## The fix (v23, `src/v23/unit_tree.py`)

1. **Code finds candidates** for each numeric trait column (half its cells or more hold a digit), in order: brackets in the printed header and a short part after its last comma; brackets in (or the whole of) a short heading above it; brackets in the legend entries for its code; unit words in the text printed above and below the table. A long table's trait-name cells: brackets in the cell.
2. **Nimble decides** per candidate (Q-PART): the unit of the values, the statistic, part of what is measured, or something else. For the text with the table (Q-TEXT): is this word the unit of this column's values? A heading's answer is reused for every column under it; a caption's is asked per column.
3. **Code applies** the first sure unit (p ≥ 0.8) to the column's numeric values only; a unit the row already has (a unit column) is kept; a unit bracket left in the trait name is taken out of it.

## Not in v23 (decisions for later)

- **The methods text** (Raine2018, Ji2024: ~41k rows). A sentence like "all morphological measurements … mm" covers every length column of the paper. A candidate finder for it is possible (unit words near measurement words in the methods), but a wrong unit then lands on many columns at once. I would try it only after v23's precision is known.
- **"ratio"**: the template says nothing about it. Writing it is a choice of yours.

## Risks

- A bracket that is not a unit: "(n)", "(%)", "(female)", "(own observation)". The model is asked; "something else" leaves it.
- Ratio and index columns: no unit is written unless one is printed.

## Measure (`src/v23/score_v23.py`)

- Unit agreement on matched rows, v18 vs v23, both scored now with the same scorer.
- F1 per paper: the name change ("Width (mm)" → "Width") must not cost pairs.
- Rows given a unit where the GT has none, counted apart.

## Size

Small to medium: one question per candidate, a few per numeric column.
