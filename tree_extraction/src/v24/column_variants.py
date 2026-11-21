"""The column tree's structural revision (2026-11-20; the user's review of TAG_MISTAKE_PATHS.txt and
output/column_tree_bench/tree_proposed_2026-11-20.txt). Each change is built on a copy of column_tree.NODES as adopted
(all.2) and tested alone, then all together, by prompt_ab.py against that tree read again in the same session
('old.3'). Every replaced text is asserted, so a change never edits more than it says.

  A  the table-kind shortcut becomes a question: in a table not read long, a column the tree called a characteristic
     is confirmed (property_check); if it is not one, property_role asks its role (classification, sample size,
     method, records, or another role / unclear). The long-table header question gains 'not a characteristic'.
     The shortcut stays closed to the long-format readings: asked per column in wide tables they were answered
     'cells_are_values' for every trait column (column_tree.py's note on organism_property).
  B  is_taxon asks whether the cells are scientific names (of the row's organism, a group it belongs to at any rank,
     or another organism linked to it), not whether they state a fact; ranks are listed as 'including', the author
     and year of a name get an option of their own instead of sitting in higher_rank
  C  abundance and sample size are confirmed by the count's purpose (count_purpose): a result of the sampling, the
     number of observations behind another value, or a number that describes the organism
  D  a place, coordinates, a date or site conditions are confirmed by their scope: the organism's own (its known
     range, its season) or one record's (one copy of the question per record_context answer, so each keeps its field)
  F  how a value was measured or obtained, named the same way in kind, record_context and property_role
The table-level organism check (E) is not part of this test (the user, 2026-11-20).

Frozen 2026-11-21 (the user's decision rule after round 6): Bn + Bx are now column_tree.py's own texts. Every change
here was built on the tree as it stood before that (commit 77ea6456); build() with a B code now fails its text checks
by design, since the texts it replaces are gone.

    build({"A", "B"}) -> NODES          VARIANTS: the prompt_ab.py entries, session 3
"""
import copy

import column_tree as ct


def _sub(text, old, new, where):
    assert text.count(old) == 1, f"{where}: expected once: {old[:70]!r}"
    return text.replace(old, new)


def _opt(nodes, node, opt):
    return nodes[node]["options"][opt]


# round 5 (the user, 2026-11-21): under B0.4 the wider higher_rank took Fontanilla2019's site columns of presence marks
# ('X' under '3600 3605') as group names once cell_shape had misread them as Latin names. The guard tests the cell
# values themselves, at the one decision point; cell_shape's misreading stays a diagnostic of its own.
HIGHER_RANK_GUARD = ("The cell values themselves must be names of taxa at such a rank: presence or absence marks and "
                     "other symbols (such as X, + or ✓) are not names of taxa.")
# round 6 (the user, 2026-11-21): the guard changed none of the 8 mark columns; not_a_name, the only exit from
# organism_name, named no place for a mark. The exit names it; 'or a phrase' left out so one clause is tested at a time.
NOT_A_NAME_ADOPTED = "Not names of organisms after all: a characteristic, a category, a place or a code."
NOT_A_NAME_MARKS = ("Not names of organisms after all: the cells hold something else, such as a characteristic, a "
                    "category, a place, a code, or a mark indicating presence or absence (e.g. X, + or ✓).")

METHOD = ("How the VALUE was measured or obtained: the method, the instrument, the formula or the way it was scored "
          "(for example 'dial gauge', 'water displacement').")

PROPERTY_CHECK = {
    "question": "Column '{h}' (values: {values}).{facts} In this table, is the column a characteristic of the row's "
                "organism, with each cell giving that organism's value?",
    "options": {
        "characteristic": {
            "description": "Yes: the header names something the organism is like, does or uses, or where and when it "
                           "lives, and each cell gives the row's organism's value of it (a number, a category, yes / "
                           "no or a code).",
            "field": "measurementType",
        },
        "another_role": {
            "description": "No: the column plays another role in the table: it places the organism in the "
                           "classification, counts the individuals behind the values, says how the values were "
                           "measured, describes the records or the sampling, or does something else.",
            "next": "property_role",
        },
    },
}

PROPERTY_ROLE = {
    "question": "Column '{h}' (values: {values}).{facts} What role does it play in the table?",
    "options": {
        "classification": {
            "description": "It places the row's organism in the classification: its genus, or a group it belongs to "
                           "at any rank above the genus (including a family, an order or a class).",
            "field": "verbatimIdentification",
        },
        "sample_size": {
            "description": "How many individuals, records or measurements another value of the row rests on.",
            "field": "sampleSizeValue",
        },
        "method": {
            "description": "How a value of the row was measured or obtained: the method, the instrument, the formula "
                           "or the way it was scored.",
            "field": "measurementMethod",
        },
        "records": {
            "description": "Something about the individuals recorded or the sampling: their sex, stage or social "
                           "role, or the place, date, protocol or conditions of the sampling.",
            "next": "record_context",
        },
        "other_or_unclear": {
            "description": "Another role, or the table does not show which: none of the above.",
            "field": None,
        },
    },
}

COUNT_PURPOSE = {
    "question": "Column '{h}' (values: {values}).{facts} The column gives counts. Is the count itself a result "
                "reported from the study's sampling, the number of observations used to obtain another value in the "
                "table, or a number that describes the organism itself?",
    "options": {
        "sampling_outcome": {
            "description": "A result of the study's sampling: how many individuals or occurrences of the organism "
                           "were found, caught or seen at its sites, plots, samples or dates, or in total.",
            "field": None,
        },
        "sample_size": {
            "description": "The number of observations behind another value of the row: how many individuals, "
                           "records or measurements were measured, observed or collected to give it.",
            "field": "sampleSizeValue",
        },
        "characteristic": {
            "description": "A number that describes the organism itself: how many of something it has, makes or "
                           "forms (individuals in a colony, eggs in a clutch, teeth on a jaw, generations a year), "
                           "or its abundance or rarity reported as data about the species rather than as a result of "
                           "the study's own sampling.",
            "field": "measurementType",
        },
    },
}


PROPERTY_CHECK_4 = {
    "question": "Column '{h}' (values: {values}).{facts} In this table, is the column a characteristic of the row's "
                "organism, with each cell giving that organism's value?",
    "options": {
        "characteristic": {
            "description": "Yes: the header names something the organism is like, does or uses, or where and when it "
                           "lives, and each cell gives the row's organism's value of it (a number, a category, a group "
                           "defined by how it lives or feeds, yes / no or a code).",
            "field": "measurementType",
        },
        "another_role": {
            "description": "No: the column plays another role in the table: it gives the organism's taxonomic "
                           "classification, counts the individuals behind the values, says how the values were "
                           "measured, describes the records or the sampling, or does something else.",
            "next": "property_role",
        },
    },
}

PROPERTY_ROLE_4 = {
    "question": "Column '{h}' (values: {values}).{facts} What role does it play in the table?",
    "options": {
        "classification": {
            "description": "Its taxonomic classification: the organism's position in biological taxonomy, such as its "
                           "genus, family, order, class or another formal taxonomic rank. Groups defined by how it "
                           "lives or feeds are not taxonomic ranks: they describe characteristics, its ways of life.",
            "field": "verbatimIdentification",
        },
        "sample_size": {
            "description": "How many individuals, records or measurements another value of the row rests on.",
            "field": "sampleSizeValue",
        },
        "method": {
            "description": "How a value of the row was measured or obtained: the method, the instrument, the formula "
                           "or the way it was scored.",
            "field": "measurementMethod",
        },
        "records": {
            "description": "Something about the individuals recorded or the sampling: their sex, stage or social "
                           "role, or the place, date, protocol or conditions of the sampling.",
            "next": "record_context",
        },
        "other_role": {
            "description": "Another role, none of the above: the table shows what the column is, and it is not a "
                           "characteristic of the organism.",
            "field": None,
        },
        "unclear": {
            "description": "Unclear: the table does not show what role the column plays.",
            "field": "(set by build: the shortcut's own answer)",
        },
    },
}

COUNT_PURPOSE_4 = {
    "question": "Column '{h}' (values: {values}).{facts} The column gives a number of individuals or records, or "
                "another sampling quantity. What does that quantity represent in this table?",
    "options": {
        "sampling_outcome": {
            "description": "A result of the sampling: the count itself is reported as what the study's sampling "
                           "found: how many individuals or occurrences of the organism were found, caught or seen at "
                           "its sites, plots, samples or dates, or in total.",
            "field": None,
        },
        "sample_size": {
            "description": "A sample size: the count tells how many individuals, observations or records support "
                           "another value or measurement reported in the same row.",
            "field": "sampleSizeValue",
        },
        "sampling_effort": {
            "description": "The sampling effort: how much was sampled rather than what was found, such as the length, "
                           "area or time sampled, or the number of traps, visits or samples.",
            "field": "sampleSizeValue",
        },
        "characteristic": {
            "description": "A characteristic of the organism given as a number: how many of something it has, makes "
                           "or forms (individuals in a colony, eggs in a clutch, teeth on a jaw, generations a year).",
            "field": "measurementType",
        },
    },
}


def scope(record_field):
    return {
        "question": "Column '{h}' (values: {values}).{facts} The column gives a place, coordinates, a time or "
                    "conditions. Do they describe the organism, or one record of it?",
        "options": {
            "organism": {
                "description": "The organism itself: where or when the species is known to live or occur (the "
                               "countries, regions, coordinates or altitudes it is known from, the months or "
                               "seasons when it is active), or the conditions it needs or tolerates, reported as a characteristic of "
                               "the species.",
                "field": "measurementType",
            },
            "record": {
                "description": "One record or the study's own sampling: where, when or under what conditions these "
                               "particular individuals were collected, observed or kept.",
                "field": record_field,
            },
        },
    }


def build(changes):
    """NODES with the listed changes applied to a copy of the adopted tree. Round 3's codes: A, B (= Bk + Bn), C, D,
    F. Round 4's: Bk (kind's classification sentence alone), Bn (the names part of B), Bt (Bn plus one sentence on
    names inside a table of characteristics), C4 (count_purpose narrowed), A4 (property_check for the shortcut only).
    Round 5's: Bg (Bn plus the guard on higher_rank: the cell values must be names of taxa, marks are not).
    Round 6's: Bx (Bn plus not_a_name naming a mark of presence or absence)."""
    changes = set(changes)
    if "B" in changes:
        changes |= {"Bk", "Bn"}
    if "Bg" in changes or "Bx" in changes:      # rounds 5 and 6: tested on top of B0's names part
        changes |= {"Bn"}
    n = copy.deepcopy(ct.NODES)
    kind = _opt(n, "kind", "organism_property")
    anchor = "(that is about the sampling)"
    if "A" in changes:
        op = n["organism_property"]
        assert op.get("otherwise") == "measurementType" and op.get("only_if_table_kind") == ["long_format"]
        del op["otherwise"]
        op["otherwise_next"] = "property_check"
        op["options"]["not_a_characteristic"] = {
            "description": "None of these: the column plays another role in the table (it places the organism in the "
                           "classification, counts the individuals behind the values, says how the values were "
                           "measured, describes the records or the sampling, or does something else).",
            "next": "property_role"}
        n["property_check"] = copy.deepcopy(PROPERTY_CHECK)
        n["property_role"] = copy.deepcopy(PROPERTY_ROLE)
        kind["description"] = _sub(kind["description"], anchor, anchor + ", how many individuals a value rests on",
                                   "A kind")
    if "F" in changes:
        kind["description"] = _sub(kind["description"], anchor,
                                   anchor + ", how a value was measured or obtained (a method, an instrument, a "
                                            "formula)", "F kind")
        mm = _opt(n, "record_context", "measurement_method")
        assert mm["description"].startswith("How the VALUE was measured"), mm["description"][:60]
        mm["description"] = METHOD
    if "Bk" in changes:
        kind["description"] = _sub(kind["description"], "and its classification (family, order), which is a name.",
                                   "and its classification at any rank (including genus, family, order and class), "
                                   "which is a name.", "B kind")
    if "Bn" in changes or "Bt" in changes:
        hr = _opt(n, "organism_name", "higher_rank")
        hr["description"] = _sub(hr["description"], "A group that the row's own organism belongs to: its family, its "
                                 "order, or another rank above the genus.",
                                 "A group that the row's own organism belongs to, at any rank above the genus "
                                 "(including a tribe, a subfamily, a family, a suborder, an order or a class).",
                                 "B higher_rank")
        hr["description"] = _sub(hr["description"], " Also the author and year of the organism's name.", "",
                                 "B higher_rank author")
        names = n["organism_name"]["options"]
        n["organism_name"]["options"] = {**{k: v for k, v in names.items() if k != "not_a_name"},
                                         "name_author": {"description": "The author and year of the organism's "
                                                                        "name ('Halvorsen, 1931'), not a name of an "
                                                                        "organism.",
                                                         "field": "verbatimIdentification"},
                                         "not_a_name": names["not_a_name"]}
        sl = _opt(n, "cell_shape", "single_latin_words")
        sl["description"] = _sub(sl["description"], "a genus, or a group above it such as a family or an order",
                                 "a genus, or a group above it at any rank, such as a family, an order or a class",
                                 "B single_latin_words")
        it = n["is_taxon"]
        assert "Test: read a cell as" in it["question"], it["question"][:80]
        it["question"] = ("Column '{h}' (values: {values}).{facts} Do the cells contain scientific names rather than "
                          "values of a characteristic of the organism? A name may identify the row's organism, a "
                          "group it belongs to at any rank, or a different organism linked to it, such as a host or "
                          "a prey. A taxonomic group stays a name even though belonging to it is also true of the "
                          "organism.")
        it["options"]["yes"]["description"] = (
            "Names: each cell is a scientific name: the organism's genus, a group it belongs to at any rank above "
            "the genus (including a tribe, a family, a suborder, an order or a class; family names often end in "
            "-idae for animals or -aceae for plants), or another organism linked to it, such as a host or a prey.")
        it["options"]["no"]["description"] = (
            "A characteristic: the cells are values of something the organism is like, does or uses (a category, a "
            "state, a habit, a group defined by how it lives or feeds, a part of the body, a stage, yes / no), even "
            "when they are capitalised or look Latin.")
        if "Bt" in changes:
            it["question"] += (" A column that names the group each row's organism belongs to is a column of names "
                               "even when the table's other columns give characteristics.")
        if "Bg" in changes:
            hr["description"] = _sub(hr["description"], "an order or a class).",
                                     "an order or a class). " + HIGHER_RANK_GUARD, "Bg higher_rank")
        if "Bx" in changes:
            nn = _opt(n, "organism_name", "not_a_name")
            assert nn["description"] == NOT_A_NAME_ADOPTED, nn["description"]
            nn["description"] = NOT_A_NAME_MARKS
    if "A4" in changes:
        op = n["organism_property"]
        assert op.get("otherwise") == "measurementType" and op.get("only_if_table_kind") == ["long_format"]
        previous = op.pop("otherwise")          # what the shortcut gave: kept when the role stays unclear
        op["otherwise_next"] = "property_check"
        n["property_check"] = copy.deepcopy(PROPERTY_CHECK_4)
        n["property_role"] = copy.deepcopy(PROPERTY_ROLE_4)
        n["property_role"]["options"]["unclear"]["field"] = previous
        # one route to measurementMethod: the direct 'method' answer; the records reached from here go to a copy of
        # record_context without its measurement_method option (the user, 2026-11-21)
        rc4 = copy.deepcopy(n["record_context"])
        del rc4["options"]["measurement_method"]
        n["record_context_a4"] = rc4
        n["property_role"]["options"]["records"]["next"] = "record_context_a4"
    if "C4" in changes:
        cs = n["counts_or_statistics"]["options"]
        for o in ("abundance", "sample_size"):
            assert "field" in cs[o], o
            del cs[o]["field"]
            cs[o]["next"] = "count_purpose"
        n["count_purpose"] = copy.deepcopy(COUNT_PURPOSE_4)
    if "C" in changes:
        cs = n["counts_or_statistics"]["options"]
        for o in ("abundance", "sample_size"):
            assert "field" in cs[o], o
            del cs[o]["field"]
            cs[o]["next"] = "count_purpose"
        n["count_purpose"] = copy.deepcopy(COUNT_PURPOSE)
    if "D" in changes:
        rc = n["record_context"]["options"]
        for o in ("sampling_place", "coordinates", "sampling_time", "site_conditions"):
            field = rc[o].pop("field")
            rc[o]["next"] = f"scope_{o}"
            n[f"scope_{o}"] = scope(field)
    saved = ct.NODES
    try:
        ct.NODES = n
        ct.validate()
    finally:
        ct.NODES = saved
    return n


ALL = ("A", "B", "C", "D", "F")
VARIANTS = {f"tree:{c}.3": ("nodes", (c,)) for c in ALL}
VARIANTS["tree:all.3"] = ("nodes", ALL)
# round 4 (the user, 2026-11-21): B kept with its kind sentence tracked apart, C narrowed, A as a check of the shortcut
# only; D and F dropped. BCA.4 is run only if A.4 earns it alone.
VARIANTS.update({"tree:K.4": ("nodes", ("Bk",)), "tree:B0.4": ("nodes", ("Bn",)), "tree:B.4": ("nodes", ("Bt",)),
                 "tree:C.4": ("nodes", ("C4",)), "tree:BC.4": ("nodes", ("Bt", "C4")), "tree:A.4": ("nodes", ("A4",)),
                 "tree:BCA.4": ("nodes", ("Bt", "C4", "A4"))})
ROUND4 = ["tree:K.4", "tree:B0.4", "tree:B.4", "tree:C.4", "tree:BC.4", "tree:A.4"]
# round 5 (the user, 2026-11-21): B0.4 is the candidate; its guard against marks read as group names is tested against
# B0 alone and the adopted tree ('old.5'), all in one session, with the neutral -ptera fact of column_tree.py
VARIANTS.update({"tree:B0.5": ("nodes", ("Bn",)), "tree:B0g.5": ("nodes", ("Bg",))})
ROUND5 = ["tree:B0.5", "tree:B0g.5"]
# round 6 (the user, 2026-11-21): the exit of organism_name names a mark of presence or absence; the last round on this
# case: if the marks stay, B0.4 is frozen and cell_shape's misreading kept as a diagnostic
VARIANTS.update({"tree:B0.6": ("nodes", ("Bn",)), "tree:B0x.6": ("nodes", ("Bx",))})
ROUND6 = ["tree:B0.6", "tree:B0x.6"]
CONTROL = {"tree:B0g.5": "tree:B0.5",           # a change's own effect: read against B0 in the same session
           "tree:B0x.6": "tree:B0.6"}

# example phrases new in this revision, checked against the 271 papers before the test
EXAMPLES = ["individuals in a colony", "eggs in a clutch", "teeth on a jaw", "generations a year",
            "the way it was scored", "altitudes it is known from", "months or seasons when it is active",
            "Halvorsen, 1931", "including a tribe", "how many individuals a value rests on"]
# round 4 (checked 2026-11-21): "formal taxonomic rank", "position in biological taxonomy", "ways of life", "a column of
# names", "support another value", "groups defined by how it lives or feeds": none printed. "feeding guilds" (12
# papers) and "functional groups" (65) are the field's own words and were not used.
# replaced after the check: "body segments", "known range" (each printed in a Jakub paper), "season of activity"
# (printed in Figueroa2021, a tuning paper; the adopted kind text carries it too, left as it is for this test)
