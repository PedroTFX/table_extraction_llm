"""New examples for the decoder's three legend prompts (the user, 2026-11-18: prompts must not carry the dataset).

  ORGANISE (decoder.py, pass A)   every example came from the papers: Graf2021's '(SO)' and '(P_E)', the bee nesting
                                  trait 'ground nesting' (20 papers), Arnan2012's '1, hundreds; 2, thousands', and a
                                  definition printed word for word in a test (held_b) paper
  LABELS   (decoder_v2.py, B)     Graf2021's 'SO', McCravy2019's 'thousands of workers per colony', 'polyphagous'
  UNCODED  (decoder_v2.py, C)     Normandin2017's 'pollen specialization (oligolectic, polylectic)', 'ground nesting'

Only the examples change: each keeps the shape it teaches (code in brackets, 'code = term', a numbered scale, a table
row, a defined word; a name with an explanation, a number, a bare name) with made-up content from plants, lichens
and rock habitats. Every new phrase was checked against the 271 papers (109, grit, Jakub): none prints it. The texts
are built from the current prompts by replacing the examples, so everything else stays word for word.
"""
import decoder as v1
import decoder_v2 as v2


def _swap(text, pairs):
    for old, new in pairs:
        assert text.count(old) == 1, f"example not found once: {old[:60]}"
        text = text.replace(old, new)
    return text


ORGANISE = _swap(v1.ORGANISE, [
    ('"solitary (SO), primitively eusocial (P_E)"   "G = ground nesting"   "1, hundreds; 2, thousands"   '
     'a table row "W | wood"',
     '"mat-forming (MF), cushion-forming (CF)"   "R = rock ledges"   "1, tens; 2, hundreds"   '
     'a table row "Lc | lichen"'),
    ('"Hygrophilous: preferring moist places"', '"Saxicolous: growing on rocks"'),
])


def _labels():
    lines = v2.LABELS.split("\n")
    new = {'"SO" =': '  "MF" = "mat-forming species spreading by runners" -> "mat-forming"',
           '"2" =': '  "2" = "tens of fruits per stem"                    -> "tens"',
           '"P" =': '  "P" = "planktonic"                                 -> "planktonic"'}
    out, hit = [], set()
    for line in lines:
        k = next((k for k in new if line.strip().startswith(k)), None)
        out.append(new[k] if k else line)
        if k:
            hit.add(k)
    assert hit == set(new), f"LABELS examples not found: {set(new) - hit}"
    return "\n".join(out)


LABELS = _labels()

UNCODED = _swap(v2.UNCODED, [
    ('"pollen specialization (oligolectic, polylectic)" names two categories, \'oligolectic\' and \'polylectic\', '
     'of \'pollen specialization\'; a table row "Ground nesting | Majority of species nest in the soil" names the '
     'category \'Ground nesting\'.',
     '"growth habit (mat-forming, cushion-forming)" names two categories, \'mat-forming\' and \'cushion-forming\', '
     'of \'growth habit\'; a table row "Ledge roosting | Most species roost on rock ledges" names the category '
     '\'Ledge roosting\'.'),
])

# variant -> the prompts it replaces
VARIANTS = {"organise": {"ORGANISE": ORGANISE}, "labels": {"LABELS": LABELS}, "uncoded": {"UNCODED": UNCODED},
            "all": {"ORGANISE": ORGANISE, "LABELS": LABELS, "UNCODED": UNCODED}}
EXAMPLES = ["mat-forming", "cushion-forming", "rock ledges", "1, tens; 2, hundreds", "Lc | lichen", "Saxicolous",
            "growing on rocks", "spreading by runners", "tens of fruits per stem", "planktonic", "growth habit",
            "Ledge roosting", "roost on rock ledges"]
