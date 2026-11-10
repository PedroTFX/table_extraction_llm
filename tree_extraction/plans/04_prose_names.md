# 4. Prose names and positional lists

## The problem

The prose reader finds the right number and species but names it by the bare label.

- "Carapace 4.14 long, 4.05 wide" gave "Carapace" twice.
- "Leg measurements: I 4.69 (1.32, 1.52, 1.10, 0.75)" gave "I", which is then dropped as no trait.
- "2.40 + 0.90 + 1.70 + 1.90 + 1.70 = 8.60" gave the heading for every number.

## What exists

Variants built in the fork, none adopted (t2 is the current default):

| Variant | Change | Jakub tune exact / vague / wrong |
|---|---|---|
| t2 | current | 1,345 / 774 / 498 |
| t5 | name = what was measured, with its qualifier and heading | 1,756 / 540 / 574 |
| t5b | + a heading is context, kept apart from the name | 1,786 / 497 / 535 |

On the 109's three prose papers t5b keeps every value t2 has.

## The plan

1. **Adopt t5b** after one run on the test groups (Jakub test, held_b prose papers, totals only).
2. **Positional lists** (not built). Many papers define an order once, then print bare numbers:
   - Code finds key candidates: a sentence or bracket that lists names in a row near a measurement word ("femur + patella + …", "given as total (a, b, c)").
   - Gemma reads a number list with the key shown and names each number by its place.
   - A sum "a + b + c = total" is read the same way: the parts by the key, the result as the total.
   - No key printed: nothing is guessed; the name stays as printed.
3. **Wrong owner** (8% of Jakub misses sit under another species): show the tracking's diagnostics first, then decide. No fix planned until the cause is seen.

## Risks

- A key from another section applied to the wrong list. The key must be in the same account or in the methods, and the count of names must equal the count of numbers.

## Measure

- Jakub tune: exact matches, wrong rows.
- 109 prose papers: side by side against the text, as always for prose.

## Size

Adoption: a test run. Positional lists: medium, prompt plus a candidate finder.
