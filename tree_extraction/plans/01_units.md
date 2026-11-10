# 1. Units out of the header into the unit field

## The problem

Papers print the unit in the column header: "Width (mm)", "Mass [mg]", "Incubation duration (days)". We keep it inside the trait name and leave `measurementUnit` empty.

- On matched rows the unit agrees with the GT 0.9% of the time (892 of 99,513 on the 109 set).
- The unit left in the name also hurts name pairing: the scorer strips "(mm)" but not "(days)", so "Incubation duration (days)" never pairs.

## The fix

1. **Code finds candidates**: a trailing bracket or a part after a comma or slash in a column header, a row label or a caption ("all measurements in mm").
2. **Nimble decides** per candidate: is this the unit of the values, a statistic, part of the name, or something else? One question, four options.
3. **Code applies**: a sure "unit" goes to `measurementUnit` and leaves the name. A caption unit applies to the columns that have none.
4. Prose already carries units; no change there.

## Step 0 before building

Check why the existing unit code (`decode_units.py`, the listed tags) leaves these empty, so the fix lands in the right layer and is not a second unit path.

## Risks

- A bracket that is not a unit: "(n)", "(%)", "(female)". That is why the model is asked.
- Ratio and index columns have no unit; the answer "something else" leaves them alone.

## Measure

- Unit agreement on matched rows (now 0.9%).
- Trait pairs gained once the unit leaves the name.
- No change in matched rows on papers without header units.

## Size

Small. One question per distinct header pattern per table, mostly cached.
