# 5. Category groups and coded columns

## The problem

Trait databases and ecology supplements print a categorical trait as a group of columns, one per category, with a mark or a score in each cell.

```
Species | Habitat          | Flight season
        | HR  HS  HL  Hpd  | FSW FSp FSu
A. b.   | 0   0   0   0.6  | 0   0.5 0.5
```

A legend table elsewhere says Hpd = "Ponds and wetlands". A curator wants "Habitat = Ponds and wetlands". We write "Habitat Hpd = 0.6", one row per column, zeros included.

Evidence:
- Viza2023: 1,695 GT rows, score 0.
- The same shape with marks ("X", "+", 1 / 0) in Guareschi2015, Kratschmer2019, Heiva2013, Odanaka2019, Fontanilla2019, Wallon2024, Renoz2020.
- 17.5% of our rows beyond the GT are true values under a code name (MN1, A 2, BS).

## What exists

- v18 writes Yes / No for two-valued columns.
- v20 reads a group of columns marked with one sign as categories. Nimble accepted none on tuning, so it changed nothing.

## The plan

1. **Candidates (code)**: columns under one group header, or columns whose headers share a code stem, whose cells are all marks, blanks, 0 / 1 or scores between 0 and 1.
2. **Q-GROUP (nimble)**, with the group header, the column names, their legend entries and three rows: are these columns the categories of one trait, separate yes / no traits, or measurements?
3. **Apply**:
   - categories of one trait → one row per category the organism has (marked, or score above 0); trait = group header, value = the category's legend words; the score kept in `measurementRemarks`;
   - separate yes / no traits → today's v18 reading;
   - measurements → unchanged.
4. **Legend look-up for header codes**: the decode step reads codes in cells. Extend the same look-up to codes in header rows, using legend tables (code beside meaning) and legend lines under tables.
5. v18's yes / no step skips columns Q-GROUP took.

## Why v20 said no, and what changes

v20 asked without the legend and only for mark-and-blank columns. The question now shows the legend words and covers scores.

## Risks

- Site or plot columns with marks (species present at a site) are sampling, not categories of a trait. The question keeps "something else", and Q-KIND still runs first.
- The GT is not uniform (Viza joins two altitude categories into one value). Expect near, not full, match.

## Measure

- Viza2023 and the mark papers above; rows with code names beyond the GT.
- Papers v18's yes / no step improved must not fall.

## Size

Large: a new layer with one question per group, plus the header legend look-up.
