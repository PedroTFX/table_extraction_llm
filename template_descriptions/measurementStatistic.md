Definition: The statistical measure that the measurementValue represents.

Valid values for measurementStatistic:
- individual
- mean
- median
- mode
- min
- max
- range
- SD
- SE
- mean ± SD
- mean ± SE
- variance
- confidence interval
- ratio
- count
- 1st quartile
- 3rd quartile
- unknown

How to choose (match the ground-truth convention):
- A single, direct reading of ONE specimen or event — a bare number with no
  aggregation — is 'individual'. This is the most common case for per-specimen
  morphometric tables; use 'individual', NOT 'single observation'.
- A CATEGORICAL state (a word, not a number: a feeding guild, a habitat, a
  yes/no) is 'mode' (the reported/most-common state).
- An aggregate names its statistic: 'mean', 'median', 'range', 'count'.
- Dispersion uses the ABBREVIATION: standard deviation -> 'SD', standard error
  -> 'SE' (never spell them out).
- A combined "value ± spread" cell (e.g. "2.31 ± 0.24") is 'mean ± SD' (or
  'mean ± SE' when the spread is a standard error).
- A value written as "low – high" (a spanning range) is 'range'; the single end
  of a min/max column is 'min' / 'max'.

Notes:
- If not explicitly stated, infer from the value itself: numeric single reading
  -> 'individual'; categorical -> 'mode'; a header word (Mean/SD/Range) names it.
- Add a brief explanation in the reasoning field when the value is inferred
  rather than explicitly stated.
