"""New examples for the prose route's prompts (prose_reader.py, prose_tree_t2.py; the user, 2026-11-18: prompts must
not carry the dataset). Almost every example came from the three prose tuning papers, the papers the reader was
built on: Xia2022 ('T. acerosus', 'BL: 7.8–8.6 mm, HW: 1.72 mm', 'forebody length', 'length of head along the
midline', 'width of pronotum at the widest point'), Xu2024 ('Lilioceris consentanea', 'Lilioceris yuae',
'L. latissima', 'of the holotype', 'in dorsal view') and Ustjuzhanin2024 ('Bamboo Camp', 'wingspan 14 mm',
'in the aedeagus', 'on the fore wing'); the body parts were a beetle's ('Elytra', 'Pronotum', 'Male genitalia').

Only the examples change, each keeping what it teaches, with made-up names ('Velora', as in the other trees) and
parts of other organisms (shells, fronds, fins, caps). Generic notation stays ('sp. nov.', 'Male:', '♂', 'TL'). Every
new phrase was checked against the 271 papers (109, grit, Jakub): none prints it.

    READER, TREE: {constant: [(old, new), ...]}; a constant is a string, or a dict of option texts
    swap_into(globals(), READER)   called at the end of each module when 'neutral' is in the variant's flags
"""

READER = {
    "RANK": [("(possibly abbreviated, as in 'T. acerosus')", "(possibly abbreviated, as in 'V. brevis')")],
    "LABEL": [("(for example 'Elytra', 'Head', 'Male genitalia', 'Pronotum', 'Leg')",
               "(for example 'Leaf blade', 'Shell aperture', 'Dorsal fin')")],
    "METHOD": [("'along the midline', 'at the widest point', 'of the holotype', 'in dorsal view')",
                "'across the rim', 'when fully unfurled', 'of the largest specimen', 'in apical view')"),
               ("'in the aedeagus', 'on the fore wing', 'of the elytra')",
                "'on the shell lip', 'of the leaf blade', 'on the dorsal fin')")],
    "HEADS": [('(for example "Lilioceris consentanea")', '(for example "Velora brevis")')],
    "NAMES_ONLY": [('(for example "Lilioceris yuae", "L. latissima")', '(for example "Velora brevis", "V. tenuis")')],
    "PLACES": [('e.g. "Bamboo Camp"', 'e.g. "Heron Ridge"')],
    "ABBREV": [('such as "BL = body length", "HW (head width)", "abbreviations used: FL, forebody length"',
                'such as "CD = cap diameter", "FW (frond width)", "abbreviations used: AH, aperture height"')],
    "FIELD": [("(for example 'BL: 7.8–8.6 mm, HW: 1.72 mm', 'wingspan 14 mm')",
               "(for example 'CD: 4.6–5.3 mm, FW: 2.47 mm', 'frond length 31 mm')")],
    "NAMES": [('"length of head along the midline"', '"length of shell across the rim"'),
              ('trait "length of head", method "along the midline"', 'trait "length of shell", method "across the rim"'),
              ('"width of pronotum at the widest point"', '"width of frond when fully unfurled"'),
              ('trait "width of pronotum", method "at the widest point"',
               'trait "width of frond", method "when fully unfurled"'),
              ('"wingspan of the holotype"', '"cap diameter of the largest specimen"'),
              ('trait "wingspan", method "of the holotype"', 'trait "cap diameter", method "of the largest specimen"')],
}

TREE = {
    "DESCRIBE": [('"[P1] Pronotum black, shining; legs yellow. Unlike X. other, the tibiae are spined"',
                  '"[P1] Shell brown, glossy; foot pale. Unlike X. other, the lip is toothed"'),
                 ('"what": "pronotum", "value": "black, shining"', '"what": "shell", "value": "brown, glossy"'),
                 ('"what": "legs", "value": "yellow"', '"what": "foot", "value": "pale"'),
                 ('"what": "tibiae", "value": "spined"', '"what": "lip", "value": "toothed"')],
    "ITEM": [('"[P1#0] 2♂, 1♀, Mount Kora, forest edge, 1200 m, 12.V.2015, J. Smith leg."',
              '"[P1#0] 2♂, 1♀, Mount Velan, lava field, 2140 m, 14.VI.2011, A. Brook leg."'),
             ('"value": "1200"', '"value": "2140"'),
             ('"value": "Mount Kora"', '"value": "Mount Velan"'),
             ('"value": "forest edge"', '"value": "lava field"')],
}

EXAMPLES = ["V. brevis", "Velora brevis", "V. tenuis", "Leaf blade", "Shell aperture", "Dorsal fin", "across the rim",
            "when fully unfurled", "of the largest specimen", "in apical view", "on the shell lip", "of the leaf blade",
            "on the dorsal fin", "Heron Ridge", "CD = cap diameter", "cap diameter", "FW (frond width)", "frond width",
            "AH, aperture height", "aperture height", "CD: 4.6", "4.6–5.3", "FW: 2.47", "2.47 mm", "frond length 31 mm",
            "length of shell across the rim", "length of shell", "width of frond when fully unfurled", "width of frond",
            "cap diameter of the largest specimen", "Shell brown", "brown, glossy", "foot pale", "lip is toothed",
            "Mount Velan", "lava field", "2140 m", "14.VI.2011", "A. Brook"]


def _swap(text, pairs, name):
    for old, new in pairs:
        if old in text:
            assert text.count(old) == 1, f"{name}: example found more than once: {old[:60]}"
            text = text.replace(old, new)
    return text


def swap_into(g, table):
    """Replace the examples in the module's constants. A constant that already carries the new example (adopted)
    is kept; one that carries neither fails, so a changed prompt is never tested by accident."""
    for name, pairs in table.items():
        val = g[name]
        if isinstance(val, str):
            out = _swap(val, pairs, name)
            texts = [out]
        else:
            out = {k: _swap(v, pairs, name) if isinstance(v, str) else v for k, v in val.items()}
            texts = [v for v in out.values() if isinstance(v, str)]
        for old, new in pairs:
            assert any(new in t for t in texts), f"{name}: example not found: {old[:60]}"
        g[name] = out
