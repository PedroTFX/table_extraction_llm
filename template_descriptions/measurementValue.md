The value of the measurement, fact, characteristic, or assertion.

Examples:
- Numeric values like "3.8", "25.0"
- Codes such as "W", "S", "W/S"

Map a column here ONLY when the table is LONG/tidy: one dedicated column holds the
numbers and a SEPARATE column's cells hold the trait NAMES (that names column is
the measurementType). measurementValue is that single values column.

In a WIDE table — the usual case, where each column's HEADER already names a
distinct trait and its cells are that trait's values — there is NO dedicated
values column: every trait column is a measurementType (its header is the trait,
its cells are the values), never measurementValue. Do not map a wide trait column
to measurementValue just because its cells are numbers.
