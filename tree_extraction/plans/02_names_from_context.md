# 2. Trait names completed from the table around them

## The problem

A cell's meaning is often split over three places, and we take only the column header.

| Printed | We write | Should be |
|---|---|---|
| Rows I, II, III, IV; columns F, P, T, Mt, t (leg segments) | "F" = 1.13 for every row | row label + column: leg I, F |
| Rows 1–4, then "Mean", "SD" | every row as a single measurement | the last two rows are statistics of the column |
| Caption "…of *X y* oothecae", columns Width, Length | "Width (mm)" | the measured object belongs to the name |
| Group header "Habitat" over columns HR, HS, HL | "Habitat HL" | covered in fix 5 |

Evidence: with account species given (v22), Jakub tuning tables match 2,360 rows only vaguely against 1,362 exactly, because the row label is missing from the name. Mirzaee2023 scores 0 for the caption case. Mean / SD rows appear in many tables of the 109.

## The fix: one question about the row labels (Q-ROWLABEL)

1. **Code finds candidates**: a table whose first non-species column repeats a small set of labels, or whose rows have no organism of their own (one species, or an account species).
2. **Nimble decides** what the row labels are:
   - separate organisms, specimens or groups (today's reading);
   - parts or items that complete the column's name (the name becomes row label + column);
   - statistics of the rows above (the label goes to `measurementStatistic`, the column keeps its name);
   - specimen or record numbers (no trait, no name part);
   - something else.
3. **Mixed tables**: asked per distinct label when the first answer is not sure, so "1, 2, 3, 4, Mean, SD" splits into records and statistics.
4. **Caption object** (second question, only for tables where every trait column is a bare dimension or count): does the caption name what was measured, other than the organism itself? Candidates are nouns from the caption; "none" is an option.
5. **Code applies** sure answers only. Names stay in the paper's words.

## Risks

- Calling organisms "parts" would merge species into names. The candidates exclude columns already decided as organisms, and the option order is checked both ways.
- Over-naming on nest or colony tables. The caption question is asked only on bare names and has "none".

## Measure

- Jakub tune: vague → exact on table rows.
- 109 tuning: Mirzaee2023, papers with Mean / SD rows; statistic agreement (now 68%).
- Every table whose names change is listed for a look by eye before adoption.

## Size

Medium. One to three questions per candidate table.
