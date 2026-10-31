"""Text clean-up of the written rows (v17; the user, 2026-10-31: "a clean up step for underscores
used as spaces"). Code only. An underscore between two letters or digits is a space written the way
spreadsheets and R exports write it ('plant_parts', 'Flight_season_start', 'Aeshna_canadensis'),
so it becomes a space in the species, the trait name and the value. Other underscores ('_x', a
lone '_') stay as printed."""
import re

FIELDS = ("verbatimIdentification", "measurementType", "measurementValue")
UNDERSCORE = re.compile(r"(?<=[^\W_])_+(?=[^\W_])")


def clean(rows):
    """In place; -> number of rows changed."""
    n = 0
    for r in rows:
        changed = False
        for f in FIELDS:
            v = r.get(f)
            if v and "_" in v:
                w = UNDERSCORE.sub(" ", v)
                if w != v:
                    r[f] = w
                    changed = True
        n += changed
    return n
