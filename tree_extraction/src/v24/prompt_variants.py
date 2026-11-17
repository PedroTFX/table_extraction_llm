"""New wording for the base column tree (column_tree.py), one node at a time (REVIEW_Opus5.5xtra_2026-11-16, section 7;
the user, 2026-11-17: prompts must not carry the dataset). The old nodes give examples copied from the papers they
were developed on ('POLLENIVOROUS', 'Sarcophagidae sp.1', 'Osmia cornuta' from OsorioCanadas2018; 'Ads.ger' from
Korosi2022; 'Pterostichini' from Habustova2017; 'W/S' from AmbspergTraun1991) and open with "a paper about insects".

Each new node keeps the old node's options and fields, so the tree and its leaves do not change: only the words
the model reads. Each option is written as a definition with the distinction to its neighbours spelled out, and its
examples are made up: invented scientific names ('Velora brevis', 'Tamnidae') and characteristics from other groups
of organisms. Every example was checked against the papers (none prints it). prompt_ab.py asks the old node and the
new one on the same tables in one session and scores both on the decision key.

    VARIANTS: {name: (kind, value)}; kind 'intro' | 'table_kind' | 'organism_column' | 'node'
"""

INTRO = ("A table from a scientific paper is being mapped, column by column, to a template that records organisms "
         "and their characteristics (traits).")

TABLE_KIND = {
    "question": "What does each row of this table hold?",
    "options": {
        "organism_traits": "One organism per row: a species or another taxon (a genus, a morphospecies), and the "
                           "other columns give characteristics of it (its measurements, its categories, what it "
                           "does or where it lives).",
        "specimens": "One individual per row: a single collected, observed or measured individual, with the values "
                     "recorded on it. Several rows can belong to the same species.",
        "long_format": "One characteristic per row (a long layout): one column names the characteristic (its cells "
                       "read, for example, 'frond length', 'leaf width') and other columns give its value; the "
                       "organism repeats over several rows, or is named in the caption or the header.",
        "counts": "Counts per row: how many individuals of an organism were found at a site, in a sample, on a date "
                  "or under a treatment (abundance, occurrence, presence at sites).",
        "statistics": "A result of an analysis per row: the output of a statistical test or model (estimates, test "
                      "statistics, p-values, correlations, information criteria), not values describing organisms.",
        "other": "Anything else: descriptions of sites or environments, definitions of codes or abbreviations, "
                 "methods, or lists of names without values.",
    },
}

ORGANISM_COLUMN = {
    "question": "Which column names the organism that each row is about, the organism the table's other columns "
                "describe? It is the column whose cells are the scientific names of those organisms: species names, "
                "or genus names when the organisms are identified only to genus ('Velora brevis', 'Velora sp. 2'). "
                "A column of their families or orders does not qualify, nor a column naming another organism they "
                "use, such as a host, a prey or a food plant.",
    "none": "No column names it: the whole table is about one organism named in the caption or the text, or its "
            "rows are not organisms (sites, samples, results).",
}

NODES = {
    "cell_shape": {
        "question": "Column '{h}' (values: {values}).{facts} What do the cells look like?",
        "options": {
            "latin_binomials": {
                "description": "Scientific names of two words: a genus followed by a species epithet or by a "
                               "placeholder for an unnamed species ('Velora brevis', 'Velora sp.', 'Tamnidae sp. 3').",
                "next": "organism_name"},
            "single_latin_words": {
                "description": "Single scientific names of one word, often capitalised or in capitals: a genus, or a "
                               "group above it such as a family or an order ('Velora', 'Tamnidae', 'ORSIFORMES').",
                "next": "is_taxon"},
            "author_year": {
                "description": "The name of a person with a year: who described an organism's name, and when "
                               "('Halvorsen (1931)', 'Duprat, 1888').",
                "field": "verbatimIdentification"},
            "everyday_words": {
                "description": "Ordinary words or short phrases, in any case: categories, states, habitats, periods "
                               "or yes / no ('EVERGREEN', 'fledgling', 'shaded slope', 'yes', 'Mar-Jun').",
                "next": "kind"},
            "codes": {
                "description": "Short codes, abbreviations or symbols whose meaning is given elsewhere ('Rk/Sd', "
                               "'Vel.bre', 'B', '+', 'Q4').",
                "next": "kind"},
            "numbers_with_text": {
                "description": "Numbers with something around them: a unit, a spread, a range or a reference in "
                               "brackets ('12.4 cm', '3.1 ± 0.2', '4–7', '0.8 [12]').",
                "next": "kind"},
        },
    },
    "is_taxon": {
        "question": "Column '{h}' (values: {values}).{facts} Are these the NAMES of organisms or of groups of "
                    "organisms? Test: read a cell as '<the row's organism> has {h} = <cell>'. If that states a fact "
                    "about the organism (what it is like or what it does), the cells are values of a characteristic, "
                    "not names.",
        "options": {
            "yes": {
                "description": "Yes: each cell names a taxon. The organism's genus, a group it belongs to (a family, "
                               "an order or another rank, often recognisable by its ending, such as -idae for a "
                               "family of animals or -aceae for a family of plants), or another organism linked to "
                               "it such as a host or a prey.",
                "next": "organism_name"},
            "no": {
                "description": "No: the cells are values of a characteristic of the organism (a category, a state, "
                               "an amount, a habit, a part of the body, a stage, yes / no), even when they are "
                               "capitalised or look Latin.",
                "next": "kind"},
        },
    },
    "organism_name": {
        "drop_if_organism_column_full": ["row_organism"],
        "question": "Column '{h}' (values: {values}).{facts} It names organisms. Which ones?",
        "options": {
            "row_organism": {
                "description": "The organism the row is about, the one the other columns describe: its full "
                               "scientific name, or one part of it when the name is split over columns (the genus in "
                               "one column, the species epithet in another).",
                "field": "verbatimIdentification"},
            "higher_rank": {
                "description": "A rank above the row's organism (its family, its order or another group above the "
                               "genus), or the author and year of its name.",
                "field": "verbatimIdentification"},
            "associated_organism": {
                "description": "A DIFFERENT organism linked to the row's organism: one it lives on or in, feeds on, "
                               "carries, is eaten or parasitised by, or depends on (a host, a prey, a food plant, a "
                               "partner), or that organism's group.",
                "field": "measurementType"},
            "taxon_code": {
                "description": "A short code standing for the row's organism instead of its name (for example "
                               "'Vel.bre' for Velora brevis).",
                "field": None},
            "not_a_name": {
                "description": "Not names of organisms after all: a characteristic, a category, a place or a code.",
                "next": "kind"},
        },
    },
    "kind": {
        "question": "Column '{h}' (values: {values}).{facts} What do its cells record?",
        "options": {
            "organism_property": {
                "description": "A characteristic of the organism itself: what it is like, what it does, or where and "
                               "when it lives. Measurements of its body or parts, its diet, behaviour, social life or "
                               "reproduction, its number of generations a year, its season of activity, the stage in "
                               "which it passes an unfavourable season, where it lives, breeds or shelters, the hosts "
                               "or foods it uses, its geographic or altitudinal range. As numbers, categories, yes / "
                               "no or codes. Still a characteristic when the cells are stages, sexes, months or "
                               "places, if the header names something about the organism ('Dormant stage' = seed, "
                               "'Breeding months' = Mar-Jun). Its classification (family, order) is a name, not a "
                               "characteristic.",
                "next": "organism_property"},
            "record_context": {
                "description": "About the recorded individuals or the sampling, not about the organism's biology: "
                               "the sex, life stage or social role of the individuals measured; the place, "
                               "coordinates or date of sampling; the conditions at the site; how the individuals were "
                               "collected, treated or measured.",
                "next": "record_context"},
            "counts_or_statistics": {
                "description": "About the numbers rather than the organism: how many individuals were found "
                               "(abundance, number collected, frequency, occurrences, totals per site), sample sizes, "
                               "the unit of the values, a statistic of a characteristic named elsewhere (a header such "
                               "as 'Mean ± SD', 'Median', 'Q1', 'CV'), or results of tests or models (estimates, test "
                               "statistics, p-values, indices).",
                "next": "counts_or_statistics"},
            "other": {
                "description": "Notes or remarks, references to publications, links, record or specimen numbers, row "
                               "numbers, glossary terms or their definitions, or anything else.",
                "next": "other"},
        },
    },
    "organism_property": {
        "only_if_table_kind": ["long_format"],
        "otherwise": "measurementType",
        "question": "Column '{h}' (values: {values}) records a characteristic of the organism. What does its HEADER "
                    "say?",
        "options": {
            "header_names_property": {
                "description": "The header is the NAME of one characteristic ('Frond length (cm)', 'Nest material', 'Broods per "
                               "year') and the cells are its values.",
                "field": "measurementType"},
            "cells_name_property": {
                "description": "The header is a general word ('Trait', 'Variable', 'Character') and the cells are the "
                               "NAMES of characteristics, changing from row to row ('frond length', 'nest material').",
                "field": "measurementType"},
            "cells_are_values": {
                "description": "The header is general or only a statistic ('Value', 'Measurement', 'Mean ± SD', "
                               "'Median') and the cells are values of a characteristic named in ANOTHER column of the "
                               "row.",
                "field": "measurementValue",
                "tag_from_header": "measurementStatistic"},
        },
    },
    "record_context": {
        "question": "Column '{h}' (values: {values}) describes the records or the sampling. What exactly?",
        "options": {
            "sex": {
                "description": "The sex of the individuals recorded: male, female, both, or hermaphrodite. Not a ratio "
                               "of the sexes.",
                "field": "sex"},
            "life_stage": {
                "description": "The developmental stage of the individuals recorded (for example egg, larva, adult, "
                               "seedling). Not the stage in which the organism passes an unfavourable season, "
                               "which is a characteristic of the organism.",
                "field": "lifeStage"},
            "caste": {
                "description": "The social role of the individuals recorded, in a species living in colonies with "
                               "divided roles (for example a reproductive female, a worker, a soldier).",
                "field": "caste"},
            "sampling_place": {
                "description": "Where the sampling happened, as a place: a country, a region, a named site, a plot or "
                               "site code, or the habitat sampled.",
                "field": "verbatimLocality"},
            "coordinates": {
                "description": "Where the sampling happened, as coordinates: latitude and longitude, in degrees or "
                               "decimals.",
                "field": "verbatimCoordinates"},
            "sampling_time": {
                "description": "When the sampling happened: a date, month, year, season or date range.",
                "field": "verbatimEventDate"},
            "measurement_method": {
                "description": "How the VALUE was measured: the method, instrument or formula (for example 'dial gauge', "
                               "'water displacement').",
                "field": "measurementMethod"},
            "sampling_protocol": {
                "description": "How the individuals were COLLECTED or observed: the trap, net, transect or survey "
                               "protocol (for example 'mist net', 'quadrat survey').",
                "field": "samplingProtocol"},
            "treatment": {
                "description": "What was done to the individuals BEFORE they were measured or stored: preserved, "
                               "dried, frozen, fixed.",
                "field": "sampleTreatment"},
            "site_conditions": {
                "description": "Conditions of the sampling site, not of the organism: temperature, rainfall, "
                               "vegetation, land use, distance.",
                "field": None},
        },
    },
    "counts_or_statistics": {
        "question": "Column '{h}' (values: {values}).{facts} It is about the numbers. Which?",
        "options": {
            "abundance": {
                "description": "How many individuals were found per site, sample or date: abundance, number of "
                               "individuals collected, totals, counts per site.",
                "field": None},
            "statistic_header": {
                "description": "The HEADER names only a statistic, perhaps after a group ('Mean ± SD', 'Fledglings Mean "
                               "± SD', 'Median', 'Q1', 'CV'), and the cells are its values; the characteristic itself is "
                               "named elsewhere (in another column, or in the caption).",
                "field": "measurementValue",
                "tag_from_header": "measurementStatistic"},
            "statistic_name": {
                "description": "The cells are WORDS naming which statistic each row's value is ('mean', 'SD', 'SE').",
                "field": "measurementStatistic"},
            "property_spread": {
                "description": "The header names a characteristic AND a statistic of it ('Frond length SD', 'Leaf "
                               "width range'): the cells are values of that characteristic.",
                "field": "measurementType"},
            "sample_size": {
                "description": "The size of the sample behind a value: how many individuals, records or occurrences it "
                               "rests on ('n', 'Occurrences'), or the length, area or time sampled.",
                "field": "sampleSizeValue"},
            "unit": {
                "description": "The unit the values are in: mm, g, %, days.",
                "field": "measurementUnit"},
            "test_result": {
                "description": "Results of a statistical test or model: an estimate, a test statistic (t, F, "
                               "chi-square), a p-value, AIC, R², a diversity or other index.",
                "field": None},
        },
    },
    "other": {
        "question": "Column '{h}' (values: {values}). Which of these is it?",
        "options": {
            "remarks": {
                "description": "Notes or remarks about a record or a measurement ('damaged', 'estimated').",
                "field": "measurementRemarks"},
            "references": {
                "description": "References to other publications ('Halvorsen et al. 1997', a DOI).",
                "field": "associatedReferences"},
            "links": {
                "description": "Web links (URLs) to external resources.",
                "field": "externalLink"},
            "record_ids": {
                "description": "Identifiers of other records of the same individuals: museum, herbarium or database "
                               "numbers.",
                "field": "associatedOccurrences"},
            "taxon_code": {
                "description": "A short code standing for the row's organism instead of its name (for example "
                               "'Vel.bre').",
                "field": None},
            "bookkeeping": {
                "description": "Row numbers, glossary terms or their definitions, or anything else.",
                "field": None},
        },
    },
}

# one variant per name: what it replaces
VARIANTS = {"intro": ("intro", INTRO), "table_kind": ("table_kind", TABLE_KIND),
            "organism_column": ("organism_column", ORGANISM_COLUMN)}
VARIANTS.update({f"node:{k}": ("node", (k, v)) for k, v in NODES.items()})

# the made-up examples, checked against every paper (prompt_ab.py --check)
EXAMPLES = ["Velora brevis", "Velora sp", "Velora", "Tamnidae", "ORSIFORMES", "Halvorsen", "Duprat", "EVERGREEN", "fledgling",
            "shaded slope", "Mar-Jun", "Rk/Sd", "Vel.bre", "Q4", "frond length", "leaf width", "Dormant stage",
            "Breeding months", "Broods per year", "Frond length SD", "Leaf width range", "Fledglings Mean", "dial gauge",
            "water displacement", "mist net", "quadrat survey", "Halvorsen et al. 1997"]
