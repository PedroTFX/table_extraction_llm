# Names from header parts, the paper's own names, species duels (v11 = v9 + both) — design, 2026-10-28, before any run

## The problems

1. **Header parts.** Oliveira2022 t14 prints `Traits` over `AL` over `M` / `V`. The head reader
   splits them correctly (group `Traits`, code `AL`, detail `M`), head_to_table joins them
   ('Traits AL M'), the meaning step writes 'Traits AL mean', and v9 skips the column because
   the meaning step changed it. v9 would also have compared 'traits al m' to the code `AL` as a
   whole. GT: 'Antenna length ratio' with statistic 'mean'. Oliveira has 400 GT rows in each set,
   for AL, CL, EL and ML; the same table's WL, IOW, P and LEG are missed the same way.
2. **The same code elsewhere.** Kovacs2008: the meaning step named table 1's column `AL`
   'antennal length'. Table 2 prints the same codes as long-table name cells (`AL`, and `GL*`
   with a footnote mark) and keeps them as printed (18 GT rows).
3. **A definition, not the paper's name.** The legend gives `AL` a definition ('ratio of
   antenna (combined funicle and scape) length to mesosoma length'). The paper's own tables print
   the name 'Antenna length ratio' (its trait table and the figure tables). The scorer's
   containment rule cannot pair the definition: it contains both 'Antenna length ratio' and
   'Mesosoma length'. Only the LLM fallback of the production scorer might, and the repeatable
   scorer never does.
4. **Species: four options split the probability.** Luo2023 t4 (both sets): the right species
   gets 0.58–0.69 and 'several' 0.26–0.29 in every round. It never reaches 0.8, so the table
   stays open. The 109 set has the same thing in Brant2021 t8 and Kratschmer2019 t3.

## Code: facts, candidates, order (it never makes a name up)

- **Items:** every trait column of a wide table, and every name cell of a long table, whose
  current name (meaning step / v9) still holds its code as a word once brackets and footnote
  marks are dropped. A name v9 or the meaning step spelled out is never asked again. A name
  v9 asked about and nimble surely called 'none' (a category, a heading) is not asked again
  either.
- **The code:** for a cell, its text without footnote marks (`*`, `†`, `‡`, `§`, `¶`) and
  bracketed units. For a column, the head reader's name part. If the name part has no
  candidates, the one group or detail part that has them is the code; with several or none,
  the column is not asked.
- **Definition candidates:** the legend inventory's entries for the code (v9's candidates:
  variable and term), plus the names the meaning step / v9 gave the same code elsewhere in the
  paper (Kovacs: `AL` → 'antennal length').
- **The paper's own names (pool):** the trait names the paper's tables print (wide trait column
  names, long-table name cells, as v9 left them). A name must have five letters, three of them
  lower case in a row, and share a word with the definition (stop words dropped). The pool is
  ordered by how many words it shares, then by reading order, at most 8 names. Names in the
  item's own table are other traits, so they never enter the pool.
- Code asks once per code per paper. A code that comes back is given the same answers.

## nimble decides, two options at a time (the user's rule)

**DUEL:** the first two candidates, then the winner against the next. A sure answer
(p ≥ 0.8) keeps one; anything less stops the duels, and the item keeps its v9 name. The holder
sits second on every other duel, so a lean towards the first option cannot keep it.

- **Q-DEF:** "What is the full name of 'AL' in this paper?" Duels among the definition
  candidates. Then the winner against 'none' (a heading shared by several columns, or an
  unrelated entry).
- **Q-PRINTED:** "Which of these two is the paper's own name for '<definition>' ('AL')?" Duels
  in the pool. Then: "Does the paper call '<definition>' '<winner>'?", yes or no (a different
  trait, or a broader or narrower one). Yes → the winner; anything else → the definition.
- **Q-PART:** a column's other parts, once per table and part. The options are: a statistic, a
  unit, a heading over several trait columns, or something else (the sex, caste or life stage
  measured, a body part, a place or time, part of the trait's name).
  - **Q-STAT** names the statistic in measurementStatistic.md's words.
  - 'Something else', or anything not sure, means the column keeps its v9 name.
- **Species duels (v11:species):** only papers whose gate said 'one', and only the tables still
  open after every round.
  - Candidates are the gate's names plus 'several organisms', with the same duels.
  - The winner then faces 'none: no organism's measurements'.
  - Not sure anywhere means the table stays open.
  - The clash rule of the per-table question applies unchanged: tables matched to different
    names → the gate is asked again, and the names are withdrawn unless it still says 'one'.

## Assembly

- A column's name goes into the meaning file, as v9 does.
- A long table's cell names come from `cell_names`, with v11's answers over v9's.
- A part answered statistic / unit fills the column's measurementStatistic / measurementUnit
  extra tag, only where the column tagger gave none.
- Species come from the species file, as before.

## Expected reach and risk

- **Grit:** Oliveira2022 (the 8 coded traits of t14), Kovacs2008 (AL, GL* cells), Luo2023 t4.
- **Risk:** v9 left some codes on purpose (a category such as 'Sprawler'); v11 asks them again
  with the duels plus a final 'none' check. Variance columns become rows of the same trait with
  statistic 'variance'. Oliveira's GT takes only the means, so those rows count as extra.

## Measure (dev / held named before any run)

- **Dev** (looked at while designing): Oliveira2022, Kovacs2008, Luo2023. Yates2014, Vidal2023,
  Gomez2022 and Orr2024 were looked at and left out of scope: no printed name, a category
  column, and a v9 case.
- **Held:** every other grit paper where v11 asks something (not opened for this step).
- Per-paper grit F1 v9 → v11 on both scorers, with dev and held reported apart. The v9
  baseline is 0.5327 production. Count decisions separately from rows:
  `name_parts/<paper>.json` holds every question, and the species file's `duel` fields hold the
  species duels.
- **Accept:** held mean F1 does not drop and no held paper drops by more than 0.02. If only dev
  papers improve, the step is unproven on held (v10's rule dropped such a step), and the
  person decides.
