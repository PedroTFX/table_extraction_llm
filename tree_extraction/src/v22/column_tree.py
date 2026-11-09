"""
column_tree.py — EXPERIMENT (not used by the pipeline yet): tag a table column
with its template field by walking a broad-to-specific DECISION TREE, one
multiple-choice question per step, answered by a decision model (tev1 / nimble
through Ollama's /v1/systemone).

Why a tree: tev1 accepts only ~2k prompt tokens, too few for the full
template_descriptions/*.md (~3.5k). Each node here asks ONE narrow question
whose few options split the fields at that level, so its descriptions can spell
out the traps the .md files warn about exactly where they are decided, without
sending the whole template every time.

    table level   (once per table, becomes context for every column question)
      table_kind        what each row holds: organisms / specimens / long /
                        counts / statistics / other
      organism_column   which column names the organism each row is about
    column level
      (code)            cell facts: numbers once citations/spreads/units are
                        peeled? Latin names? rank endings? 'Author (year)'?
                        numeric columns skip straight to 'kind'
      cell_shape        what the cells look like: Latin binomials | single Latin
                        words | author + year | everyday words | codes | numbers
      is_taxon          (single Latin words only) organisms/groups or not?
      organism_name     the row's organism / a higher rank / an associated
                        organism / a code / not a name after all
      kind              organism property | record or sampling context |
                        about the numbers | other
      <kind>            the specific field, e.g. record context -> sex / life
                        stage / caste / place / coordinates / date / method /
                        protocol / treatment

Every option is either a LEAF ("field": the template field, None = not mapped)
or points to the NEXT node. Edit the text below to improve a decision;
column_tree_bench.py measures the effect against the ground truth.

Decisions are probabilistic: the greedy answer follows the most likely option at
every node; when a runner-up option is likely too (>= EXPLORE), its branch is
asked as well and the 'soft' answer is the field with the most total path
probability. Both are returned.
"""

from __future__ import annotations

import collections
import json
import random
import re
import time
from urllib import error as _er
from urllib import request as _rq

DECISION_URL = "http://127.0.0.1:11434/v1/systemone"
EXPLORE = 0.25          # also ask the branch of a runner-up option this likely
MAX_COLS = 40           # columns asked per table; wider tables are sampled

# --- table level -----------------------------------------------------------------

TABLE_KIND = {
    "question": "What does each row of this table hold?",
    "options": {
        "organism_traits": "Each row is one organism (a species, genus or "
                           "morphospecies) and the columns describe its traits "
                           "or properties.",
        "specimens": "Each row is one collected or measured individual (a "
                     "specimen) with its measurements.",
        "long_format": "Long table: one column's cells NAME the property "
                       "measured (body length, thorax width) and other columns "
                       "hold its values, e.g. one property per row for a "
                       "species named in the caption or the header.",
        "counts": "Each row gives how many individuals of an organism were found "
                  "per site, sample, date or treatment (abundance or occurrence "
                  "data).",
        "statistics": "Each row is a result of a statistical test or model "
                      "(estimates, t, F, p, AIC), not raw data about organisms.",
        "other": "Study sites, environmental variables, definitions of codes or "
                 "abbreviations, or anything else.",
    },
}

ORGANISM_COLUMN = {
    "question": "Which column names the organism that each row is about, the "
                "organism the table's other columns describe? Only a column "
                "whose values are taxon names (Latin species or genus names) "
                "qualifies.",
    "none": "No column names it: the whole table is about one organism named "
            "elsewhere, or its rows are not organisms.",
}

# --- column level ------------------------------------------------------------------

# Before the first question, code reads the shape of the column's cells
# (cell_facts): what is left once citations, spreads, ranges and units are
# peeled off, and how many cells look like Latin names, group names or
# 'Author (year)'. A column whose cells are numbers starts at 'kind' (numbers
# are never organism names; tev1 called a column of p-values names at 0.86).
# Every other column starts at 'cell_shape', and the measured facts are written
# into the question as evidence: the model still decides.
ROOT = "cell_shape"
NUMERIC_START = "kind"
NUMERIC_MIN = 0.8        # share of cells that are numbers once peeled

NODES = {
    "cell_shape": {
        "question": "Column '{h}' (values: {values}).{facts} What do the cells "
                    "look like?",
        "options": {
            "latin_binomials": {
                "description": "Two-word Latin names, a genus and a species "
                               "('Osmia cornuta', 'Formica sp.', 'Sarcophagidae "
                               "sp.1').",
                "next": "organism_name"},
            "single_latin_words": {
                "description": "Single Latin words or group names, often "
                               "capitalised or in capitals ('Osmia', 'Formicinae', "
                               "'Pterostichini', COLLETIDAE, DIPTERA).",
                "next": "is_taxon"},
            "author_year": {
                "description": "Person names with a year ('Matthews (1974)', "
                               "'Linnaeus, 1758'): the author of a name.",
                "field": "verbatimIdentification"},
            "everyday_words": {
                "description": "Ordinary words, categories or phrases, "
                               "capitalised or not ('POLLENIVOROUS', 'Larva', "
                               "'Adult', 'solitary', 'leaf litter', 'yes', "
                               "'May-Aug').",
                "next": "kind"},
            "codes": {
                "description": "Short codes, abbreviations or symbols ('W/S', "
                               "'Ads.ger', 'A', '+', 'S7').",
                "next": "kind"},
            "numbers_with_text": {
                "description": "Numbers with extra text around them: units, a "
                               "spread, a range, a citation in brackets.",
                "next": "kind"},
        },
    },
    "is_taxon": {
        "question": "Column '{h}' (values: {values}).{facts} Are these NAMES "
                    "of organisms or taxonomic groups? Test: read a cell as "
                    "'<the row's organism> has {h} = <cell>'. If that states a "
                    "fact about the organism, the cells are values of a property, "
                    "not names.",
        "options": {
            "yes": {
                "description": "Yes, each cell names a taxon: a genus, or the "
                               "family, subfamily, tribe or order the organism "
                               "belongs to (Latin endings: -idae family, -inae "
                               "subfamily, -ini tribe, -oidea superfamily, -ptera "
                               "order), or a host, prey or plant taxon.",
                "next": "organism_name"},
            "no": {
                "description": "No, the cells are values of a property, state or "
                               "category of the organism (an amount, a guild, a "
                               "habit, a body structure, a stage, yes/no), even "
                               "when capitalised or Latin-looking.",
                "next": "kind"},
        },
    },
    "organism_name": {
        # When the table level found an organism column of full Latin names, the
        # walk drops 'row_organism' here: a second column cannot be the row's
        # organism (tev1 sent 10 category columns of held-out papers this way).
        "drop_if_organism_column_full": ["row_organism"],
        "question": "Column '{h}' (values: {values}).{facts} It names organisms. "
                    "Which ones?",
        "options": {
            "row_organism": {
                "description": "The organism the row is about, the one the table's "
                               "other columns describe: its full name, or one part "
                               "of a name split over columns (genus, species "
                               "epithet).",
                "field": "verbatimIdentification"},
            "higher_rank": {
                "description": "A higher taxonomic rank of the row's organism "
                               "(family, subfamily, tribe, order) or the author and "
                               "year of its name.",
                "field": "verbatimIdentification"},
            "associated_organism": {
                "description": "A DIFFERENT organism linked to the row's organism: "
                               "its host, prey, parasite or parasitoid, food or "
                               "host plant (or the plant's family), or partner.",
                "field": "measurementType"},
            "taxon_code": {
                "description": "A short code or abbreviation standing for the "
                               "row's organism (e.g. 'Ads.ger'), not its name.",
                "field": None},
            "not_a_name": {
                "description": "Not organism names after all: a property, "
                               "category, place or code.",
                "next": "kind"},
        },
    },
    "kind": {
        "question": "Column '{h}' (values: {values}).{facts} What do its cells "
                    "record?",
        "options": {
            "organism_property": {
                "description": "A property of the organism itself, what it has, "
                               "does or where it lives: body size or other "
                               "measurements, diet, behaviour, sociality, "
                               "phenology or flight period, voltinism, "
                               "overwintering stage, nesting, habitat preference, "
                               "host range, geographic or elevation range. As "
                               "numbers, categories, yes/no or codes. Still a "
                               "property when its cells are stages, sexes, months "
                               "or places, if the header names something about "
                               "the species ('Overwintering stage' = larva, "
                               "'Flight period' = May-Aug). Its classification "
                               "(family, order, tribe) is a name, not a property.",
                "next": "organism_property"},
            "record_context": {
                "description": "About the recorded individuals or the sampling, "
                               "not the species' biology: the sex, life stage or "
                               "caste of the specimens measured; the place, "
                               "coordinates or date of sampling; the conditions of "
                               "the site; how specimens were sampled, treated or "
                               "measured.",
                "next": "record_context"},
            "counts_or_statistics": {
                "description": "About the numbers rather than the organism: how "
                               "many individuals were found (abundance, number of "
                               "specimens, frequency, occurrences, totals per "
                               "site), sample sizes, the unit of the values, a "
                               "statistic of a property named elsewhere (header "
                               "'Mean ± SD', 'Median', 'Q1', 'CV'), or test results "
                               "(estimate, t, F, p, AIC, index).",
                "next": "counts_or_statistics"},
            "other": {
                "description": "Notes or remarks, references or citations, links, "
                               "record or specimen numbers, row numbers, glossary "
                               "terms or their definitions, or anything else.",
                "next": "other"},
        },
    },
    "organism_property": {
        # Long vs wide is a property of the TABLE, decided once at the table
        # level: in any table not judged long this node is not asked and the
        # column is a measurementType. (Asked per column, tev1 answered
        # 'cells_are_values' for every wide trait column of Osorio.)
        "only_if_table_kind": ["long_format"],
        "otherwise": "measurementType",
        "question": "Column '{h}' (values: {values}) records a property of the "
                    "organism. What does its HEADER say?",
        "options": {
            "header_names_property": {
                "description": "The header is the NAME of one property ('Body "
                               "length (mm)', 'Diet', 'Voltinism') and the cells "
                               "are its values.",
                "field": "measurementType"},
            "cells_name_property": {
                "description": "The header is generic ('Trait', 'Variable', "
                               "'Character') and the cells are property NAMES "
                               "that change from row to row ('body length', "
                               "'diet').",
                "field": "measurementType"},
            "cells_are_values": {
                "description": "The header is generic or only a statistic "
                               "('Value', 'Measurement', 'Mean ± SD', 'Median') "
                               "and the cells are values whose property is named "
                               "in ANOTHER column of the row.",
                "field": "measurementValue",
                "tag_from_header": "measurementStatistic"},
        },
    },
    "record_context": {
        "question": "Column '{h}' (values: {values}) describes the records or the "
                    "sampling. What exactly?",
        "options": {
            "sex": {
                "description": "The sex of the recorded individuals: male, female, "
                               "both. Not a sex ratio.",
                "field": "sex"},
            "life_stage": {
                "description": "The developmental stage of the recorded "
                               "individuals: egg, larva, pupa, nymph, adult. Not "
                               "the stage the species overwinters in.",
                "field": "lifeStage"},
            "caste": {
                "description": "The caste of the recorded social insects: worker, "
                               "queen, soldier, male.",
                "field": "caste"},
            "sampling_place": {
                "description": "Where the sampling happened, as a place: country, "
                               "region, named site, plot or site code, or the "
                               "habitat that was sampled.",
                "field": "verbatimLocality"},
            "coordinates": {
                "description": "Where the sampling happened, as coordinates: "
                               "latitude/longitude, degrees or decimals.",
                "field": "verbatimCoordinates"},
            "sampling_time": {
                "description": "When the sampling happened: a date, month, year, "
                               "season or date range.",
                "field": "verbatimEventDate"},
            "measurement_method": {
                "description": "How the VALUE was measured: method, instrument, "
                               "formula (e.g. 'ocular micrometer', 'dry weight').",
                "field": "measurementMethod"},
            "sampling_protocol": {
                "description": "How the specimens were COLLECTED: trap type or "
                               "sampling protocol (e.g. 'pitfall trap', 'sweep "
                               "net', 'light trap').",
                "field": "samplingProtocol"},
            "treatment": {
                "description": "What was done to specimens BEFORE analysis or "
                               "storage: preserved in ethanol, dried, fixed.",
                "field": "sampleTreatment"},
            "site_conditions": {
                "description": "Conditions of the sampling site: temperature, "
                               "rainfall, vegetation, land use, distance.",
                "field": None},
        },
    },
    "counts_or_statistics": {
        "question": "Column '{h}' (values: {values}).{facts} It is about the "
                    "numbers. Which?",
        "options": {
            "abundance": {
                "description": "How many individuals were found per site, "
                               "sample or date: abundance, number of specimens "
                               "collected, totals, counts per site.",
                "field": None},
            "statistic_header": {
                "description": "The HEADER names only a statistic, maybe after a "
                               "group ('Mean ± SD', 'Workers Mean ± SD', 'Median', "
                               "'Q1', 'CV') and the cells are its values; the "
                               "property itself is named elsewhere (a trait "
                               "column, the caption).",
                "field": "measurementValue",
                "tag_from_header": "measurementStatistic"},
            "statistic_name": {
                "description": "The cells are WORDS naming which statistic each "
                               "row's value is ('mean', 'SD', 'SE').",
                "field": "measurementStatistic"},
            "property_spread": {
                "description": "The header names a property AND a statistic of it "
                               "('Body length SD', 'Wing length range'): values of "
                               "that property.",
                "field": "measurementType"},
            "sample_size": {
                "description": "The size of the sample behind a value: how many "
                               "individuals, records or occurrences it rests on "
                               "(n, 'Occurrences'), or a length, area or time "
                               "sampled.",
                "field": "sampleSizeValue"},
            "unit": {
                "description": "The unit the values are in: mm, mg, %, days.",
                "field": "measurementUnit"},
            "test_result": {
                "description": "Results of a statistical test or model: estimate, "
                               "t, F, chi-square, p-value, AIC, R2, a diversity or "
                               "other index.",
                "field": None},
        },
    },
    "other": {
        "question": "Column '{h}' (values: {values}). Which of these is it?",
        "options": {
            "remarks": {
                "description": "Notes or remarks about a record or measurement "
                               "('specimen damaged', 'estimated').",
                "field": "measurementRemarks"},
            "references": {
                "description": "References or citations of other publications "
                               "('Smith et al. 2005', a DOI).",
                "field": "associatedReferences"},
            "links": {
                "description": "Web links (URLs) to external resources.",
                "field": "externalLink"},
            "record_ids": {
                "description": "Identifiers of other records of the same "
                               "specimens: museum or occurrence numbers.",
                "field": "associatedOccurrences"},
            "taxon_code": {
                "description": "A short code or abbreviation standing for the "
                               "row's organism (e.g. 'Ads.ger').",
                "field": None},
            "bookkeeping": {
                "description": "Row numbers, glossary terms or definitions, or "
                               "anything else.",
                "field": None},
        },
    },
}


# --- cell shape (code, no model) ------------------------------------------------------

_SUPERSCRIPT = re.compile(r"\$\^\{?[^$]*\}?\$|\^[A-Za-z0-9,]+")
_PEEL = [  # (what, pattern) — removed from a cell, in this order
    ("citations [n]", re.compile(r"\s*\[[\d,;\s\-–]+\]")),
    ("footnote marks", re.compile(r"[†‡§¶*]+")),
    ("(n = x)", re.compile(r"\s*\(\s*n\s*=\s*\d+\s*\)", re.I)),
    ("± spreads", re.compile(r"\s*(?:±|\+/-|\+-|�)\s*\d[\d.,]*")),
    ("spreads in brackets", re.compile(r"\s*\(\s*[\d.,]+\s*\)")),
    ("ranges", re.compile(r"(?<=\d)\s*[-–—]\s*-?\d[\d.,]*")),
    ("units", re.compile(r"\s*(?:[µμu]m|mm|cm|km|mg|µg|kg|g|ml|°C|ºC|%|days?|h|yrs?|years?)\b\.?")),
    ("letters after numbers", re.compile(r"(?<=\d)\s*[a-h]{1,3}$")),
    ("< > signs", re.compile(r"^\s*[<>≤≥~≈]\s*")),
]
_NUMBER = re.compile(r"^-?\d+(?:[.,]\d+)?$")
_BINOMIAL = re.compile(r"^[A-Z][a-z]+(?:\s*\(=?[^)]*\))?\s+(?:[a-z-]*(?:us|um|a|ae|is|i|ii|ensis|oides|or|ix|ax|ex|ys|on)(?:\s+[a-z-]+(?:us|um|a|ae|is|i|ii|ensis))?|spp?\.?\s*\d*|[A-Z]{1,3}\d+|\d-[a-z]+)[*†‡§¶]*(?:\s*[(,]?\s*[A-Z][^,]*(?:,\s*\d{4})?\)?.*)?$")
_SINGLE_LATIN = re.compile(r"^(?:[A-Z][a-z]+|[A-Z]{3,})(?:\s*\([^)]*\))?$")
_AUTHOR_YEAR = re.compile(r"^[A-Z][A-Za-z'\-]+.*\b(1[7-9]\d\d|20\d\d)\b")
_YEAR = re.compile(r"\b(1[7-9]\d\d|20\d\d)\b")
_RANK_ENDINGS = [("idae", "family"), ("inae", "subfamily"), ("ini", "tribe"),
                 ("oidea", "superfamily"), ("ptera", "order"), ("aceae", "plant family")]


def peel(cell: str):
    """-> (core, [what was peeled]). '0,6 [18]' -> ('0,6', ['citation [n]'])."""
    core, peeled = _SUPERSCRIPT.sub("", str(cell or "")).strip(), []
    for what, rx in _PEEL:
        new = rx.sub("", core).strip()
        if new != core:
            peeled.append(what)
            core = new
    return core, peeled


def cell_facts(table, header) -> dict:
    """What the column's cells look like, measured in code."""
    cells = [re.sub(r"\s+", " ", str(c or "")).strip() for c in table.column_values(header)]
    cells = [c for c in cells if c and c not in {"-", "–", "—", "?", "NA", "na"}]
    n = len(cells)
    f = {"n": n, "numeric": 0.0, "peeled": collections.Counter(), "binomial": 0.0,
         "single_latin": 0.0, "author_year": 0.0, "endings": collections.Counter()}
    if not n:
        return f
    numeric = 0
    for c in cells:
        core, peeled = peel(c)
        if _NUMBER.match(core):
            numeric += 1
            f["peeled"].update(peeled)
        words = c.split()
        if _BINOMIAL.match(c):
            f["binomial"] += 1
        elif _SINGLE_LATIN.match(c) and not _YEAR.search(c):
            f["single_latin"] += 1
            w = words[0].lower()
            for end, rank in _RANK_ENDINGS:
                if w.endswith(end):
                    f["endings"][(end, rank)] += 1
                    break
        if _AUTHOR_YEAR.match(c) and not _NUMBER.match(core) and not _BINOMIAL.match(c):
            f["author_year"] += 1
    f["numeric"] = numeric / n
    for k in ("binomial", "single_latin", "author_year"):
        f[k] /= n
    return f


_HEADER_STATS = [  # (pattern, measurementStatistic.md term), most specific first
    (r"mean\s*(?:±|\+/-|\+-|\uFFFD)\s*s\.?d\.?\b", "mean ± SD"),
    (r"mean\s*(?:±|\+/-|\+-|\uFFFD)\s*s\.?e\.?m?\b", "mean ± SE"),
    (r"mean\s*\(\s*s\.?d\.?\s*\)", "mean ± SD"),
    (r"mean\s*\(\s*s\.?e\.?\s*\)", "mean ± SE"),
    (r"\bmedian\b|\bq2\b", "median"),
    (r"\bq1\b|1st quartile|first quartile", "1st quartile"),
    (r"\bq3\b|3rd quartile|third quartile", "3rd quartile"),
    (r"\bmean\b|\baverage\b", "mean"),
    (r"\bs\.?d\.?\b|standard deviation", "SD"),
    (r"\bs\.?e\.?m?\.?\b|standard error", "SE"),
    (r"\bc\.?v\.?\b|coefficient of variation", "CV"),
    (r"\bmin(?:imum)?\b", "min"),
    (r"\bmax(?:imum)?\b", "max"),
    (r"\brange\b", "range"),
    (r"\bmode\b", "mode"),
]


def header_statistic(header) -> str | None:
    """The statistic a header ENDS with ('Workers Mean ± SD' -> 'mean ± SD'),
    in measurementStatistic.md's vocabulary; None when it names none."""
    h = re.sub(r"\s+", " ", str(header or "")).strip().lower()
    for pat, term in _HEADER_STATS:
        m = None
        for m in re.finditer(pat, h):
            pass
        if m and not re.search(r"[a-z]{3,}", h[m.end():]):   # at the end
            return term
    return None


def header_text(header) -> str:
    """Code evidence about the header, for the questions marked {facts}."""
    st = header_statistic(header)
    return f" Header facts (measured): the header ends with a statistic ({st})." if st else ""


def facts_text(f) -> str:
    """The notable facts as one sentence for the question ('' when none)."""
    n = f["n"]
    if not n:
        return " Cell facts: the column is empty."
    bits = []
    if f["numeric"] >= 0.5:
        extra = (f" once {', '.join(k for k, _ in f['peeled'].most_common(3))} "
                 f"are set aside" if f["peeled"] else "")  # e.g. 'citations [n]'
        bits.append(f"{f['numeric']:.0%} of cells are numbers{extra}")
    if f["binomial"] >= 0.3:
        bits.append(f"{f['binomial']:.0%} look like two-word Latin names")
    if f["single_latin"] >= 0.3:
        bits.append(f"{f['single_latin']:.0%} are single capitalised words")
    for (end, rank), c in f["endings"].most_common(1):
        if c / n >= 0.3:
            bits.append(f"{c} of {n} end in -{end} (the Latin {rank} ending)")
    if f["author_year"] >= 0.3:
        bits.append(f"{f['author_year']:.0%} look like a name with a year")
    return (" Cell facts (measured): " + "; ".join(bits) + ".") if bits else ""


def validate():
    """Every 'next' must exist and every node must be reachable from ROOT."""
    seen, todo = set(), [ROOT]
    while todo:
        n = todo.pop()
        if n in seen:
            continue
        assert n in NODES, f"missing node {n!r}"
        seen.add(n)
        for name, opt in NODES[n]["options"].items():
            assert ("next" in opt) != ("field" in opt), f"{n}.{name}: next XOR field"
            assert "tag_from_header" not in opt or "field" in opt, f"{n}.{name}: tag on a leaf only"
            if "next" in opt:
                todo.append(opt["next"])
        if "only_if_table_kind" in NODES[n]:
            assert "otherwise" in NODES[n], f"{n}: only_if_table_kind needs otherwise"
            bad = set(NODES[n]["only_if_table_kind"]) - set(TABLE_KIND["options"])
            assert not bad, f"{n}: unknown table kinds {bad}"
    unused = set(NODES) - seen
    assert not unused, f"unreachable nodes: {unused}"


def render() -> str:
    """The tree as indented text, for reports and for reading."""
    lines = ["TABLE LEVEL",
             f"  table_kind: {TABLE_KIND['question']}"]
    lines += [f"    - {k}: {v}" for k, v in TABLE_KIND["options"].items()]
    lines += [f"  organism_column: {ORGANISM_COLUMN['question']}",
              "    - <one option per text column>", f"    - none: {ORGANISM_COLUMN['none']}",
              "", "COLUMN LEVEL",
              f"  (code) cells >= {NUMERIC_MIN:.0%} numbers once peeled -> start at "
              f"[{NUMERIC_START}]; otherwise start at [{ROOT}]. Measured cell facts "
              f"are added to questions marked {{facts}}."]

    shown = set()

    def walk(node, depth):
        pad = "  " * depth
        if node in shown:
            lines.append(f"{pad}[{node}] (see above)")
            return
        shown.add(node)
        lines.append(f"{pad}[{node}] {NODES[node]['question']}")
        if "only_if_table_kind" in NODES[node]:
            lines.append(f"{pad}  (asked only when table_kind is "
                         f"{'/'.join(NODES[node]['only_if_table_kind'])}; otherwise "
                         f"-> {NODES[node]['otherwise']})")
        for name, opt in NODES[node]["options"].items():
            leaf = (f" -> {opt['field'] or 'none'}" if "field" in opt else "")
            if opt.get("tag_from_header"):
                leaf += f" + {opt['tag_from_header']} from the header"
            lines.append(f"{pad}  - {name}{leaf}: {opt['description']}")
            if "next" in opt:
                walk(opt["next"], depth + 2)
    walk(ROOT, 1)
    return "\n".join(lines)


def reachable_fields(node, _seen=None) -> set:
    """Template fields ('none' for None) any path from `node` can still end in."""
    seen = _seen if _seen is not None else set()
    if node in seen:
        return set()
    seen.add(node)
    out = set()
    if "otherwise" in NODES[node]:
        out.add(NODES[node]["otherwise"])
    for opt in NODES[node]["options"].values():
        if "field" in opt:
            out.add(opt["field"] or "none")
        else:
            out |= reachable_fields(opt["next"], seen)
    return out


def option_fields(node, option) -> set:
    opt = NODES[node]["options"][option]
    return {opt["field"] or "none"} if "field" in opt else reachable_fields(opt["next"])


# --- talking to the decision model ---------------------------------------------------

class DecisionClient:
    """/v1/systemone with the failure handling the benchmark needed:
      - a 5xx or dropped connection is the model's runner dying; Ollama restarts
        it on the next request, so wait and retry the SAME model
      - a 400 'prompt has N tokens' is a prompt over the model's limit (tev1:
        ~2,050): split a multi-question call, or shrink the state of a single one
    `chunk` = questions per call (each question carries the whole set)."""

    def __init__(self, model: str, chunk: int = 1, timeout: int = 600):
        self.model, self.chunk, self.timeout = model, chunk, timeout
        self.calls = 0
        self.seconds = 0.0

    def _post(self, state, questions, retries=2):
        body = json.dumps({"model": self.model, "state": state,
                           "questions": questions}).encode()
        for attempt in range(retries + 1):
            t0 = time.time()
            try:
                req = _rq.Request(DECISION_URL, data=body,
                                  headers={"Content-Type": "application/json"})
                with _rq.urlopen(req, timeout=self.timeout) as r:
                    self.calls += 1
                    return json.loads(r.read()).get("answers", {})
            except _er.HTTPError as e:
                if e.code < 500 or attempt == retries:
                    raise
            except _er.URLError:
                if attempt == retries:
                    raise
            finally:
                self.seconds += time.time() - t0
            time.sleep(5 * (attempt + 1))

    def ask(self, state_at, questions: dict) -> dict:
        """state_at(size) -> state text, size 0 (fullest) .. 2 (smallest)."""
        out = {}
        keys = list(questions)
        for i in range(0, len(keys), self.chunk):
            part = {k: questions[k] for k in keys[i:i + self.chunk]}
            out.update(self._ask_part(state_at, part, 0))
        return out

    def _ask_part(self, state_at, part, size):
        try:
            return self._post(state_at(size), part)
        except _er.HTTPError as e:
            msg = e.read().decode("utf-8", "replace")
            if e.code != 400 or "token" not in msg:
                raise RuntimeError(f"{e.code}: {msg[:200]}")
            if len(part) > 1:
                ks = list(part)
                h = len(ks) // 2
                out = self._ask_part(state_at, {k: part[k] for k in ks[:h]}, size)
                out.update(self._ask_part(state_at, {k: part[k] for k in ks[h:]}, size))
                return out
            if size < 2:
                return self._ask_part(state_at, part, size + 1)
            raise RuntimeError(f"prompt too long even with the smallest state: {msg[:120]}")


# --- prompts --------------------------------------------------------------------------

_NUMERIC_CELL = re.compile(r"^[\d\s.,±()+\-–—%<>/~*]+$")


def _clip(v, n):
    v = re.sub(r"\s+", " ", str(v or "")).strip()
    return v if len(v) <= n else v[:n - 1] + "…"


def sample_values(table, header, k=6, width=50) -> str:
    seen, out = set(), []
    for v in table.column_values(header):
        v = _clip(v, width)
        if v and v.lower() not in seen:
            seen.add(v.lower())
            out.append(v)
        if len(out) >= k:
            break
    return "; ".join(out) if out else "(empty)"


_SIZES = [  # intro chars, rows, columns shown, cell width, headers listed
    (300, 4, 8, 22, 40),
    (120, 3, 6, 16, 25),
    (0, 2, 4, 12, 12),
]


def table_state(table, paper_text, context=(), size=0) -> str:
    intro_len, n_rows, n_cols, width, n_heads = _SIZES[size]
    headers = table.header_names
    shown = headers[:n_cols]
    heads = " | ".join(_clip(h, 40) for h in headers[:n_heads])
    if len(headers) > n_heads:
        heads += f" | ... (+{len(headers) - n_heads} more)"
    grid = "\n".join(" | ".join(_clip(r.get(h, ""), width) for h in shown)
                     for r in table.data_records()[:n_rows])
    parts = ["A table from a scientific paper about insects is being mapped, column "
             "by column, to a species-trait template."]
    if intro_len:
        parts.append("Paper start: " + _clip(paper_text, intro_len))
    parts.append(f"Headers: {heads}")
    parts.append(f"First rows ({len(shown)} of {len(headers)} columns):\n{grid}")
    parts.extend(context)
    return "\n\n".join(parts)


def organism_candidates(table, limit=10) -> list:
    """Columns that can name the organism: their cells look like taxon names
    (two-word Latin names, or single capitalised Latin words such as a genus).
    Measured in code: Kovacs2010's 'Trait' (Thorax width, Mass) was offered as
    the only candidate and picked at 0.96, though the paper's one species is
    named in the text. A table with no such column gets 'none' without a
    question."""
    out = []
    for h in table.header_names:
        f = cell_facts(table, h)
        if f["n"] and (f["binomial"] >= 0.3 or f["single_latin"] >= 0.5):
            out.append(h)
        if len(out) >= limit:
            break
    return out


def _option_labels(headers) -> dict:
    """header -> a unique, short option label."""
    labels, used = {}, set()
    for h in headers:
        base = _clip(h, 50) or "(blank header)"
        lab, i = base, 2
        while lab in used or lab == "none":
            lab, i = f"{base} #{i}", i + 1
        used.add(lab)
        labels[h] = lab
    return labels


def _question(node_id, header, values, facts="", drop=()) -> dict:
    node = NODES[node_id]
    text = (node["question"].replace("{h}", _clip(header, 60))
            .replace("{values}", values).replace("{facts}", facts))
    return {"type": "choice", "instructions": text,
            "criteria": {k: o["description"] for k, o in node["options"].items()
                         if k not in drop}}


# --- the walk -------------------------------------------------------------------------

def classify_table(table, paper_text, client: DecisionClient, table_context=True,
                   explore=EXPLORE, max_cols=MAX_COLS, seed="", extra_context=()) -> dict:
    """Tag every column of `table` by walking the tree.

    Returns {"greedy": {h: (field, p)}, "soft": {h: (field, p)},
             "paths": {h: "kind:x(0.9) > y(0.8)"}, "table_kind": (k, p) | None,
             "organism_column": (h | None, p) | None, "skipped": [h, ...],
             "tags": {h: {"measurementStatistic": "mean ± SD"}}}
    field is a template field name or 'none'; tags are the extra tags an end
    answer carries (a statistic-only header -> measurementValue + its statistic)."""
    headers = list(table.header_names)
    skipped = []
    if len(headers) > max_cols:                     # sample a wide table
        keep = set(organism_candidates(table, limit=3))
        rest = [h for h in headers if h not in keep]
        random.Random(seed or str(len(headers))).shuffle(rest)
        keep |= set(rest[:max_cols - len(keep)])
        skipped = [h for h in headers if h not in keep]
        headers = [h for h in headers if h in keep]

    greedy, soft, paths = {}, {}, {}
    context = list(extra_context)   # lines found outside the header (head_to_table, version 2)
    kind_ans = org_ans = None
    org_full = False                # the organism column holds full Latin names

    if table_context:
        base = lambda size: table_state(table, paper_text, tuple(extra_context), size)
        qs = {"table_kind": {"type": "choice", "instructions": TABLE_KIND["question"],
                             "criteria": dict(TABLE_KIND["options"])}}
        cands = organism_candidates(table)
        labels = _option_labels(cands)
        if cands:
            crit = {labels[h]: f"values: {sample_values(table, h, k=4, width=30)}."
                               f"{facts_text(cell_facts(table, h)) or ' Cell facts: no Latin names.'}"
                    for h in cands}
            crit["none"] = ORGANISM_COLUMN["none"]
            qs["organism_column"] = {"type": "choice",
                                     "instructions": ORGANISM_COLUMN["question"],
                                     "criteria": crit}
        ans = client.ask(base, qs)
        if not cands:                    # decided in code: nothing looks like a taxon
            ans["organism_column"] = {"choice": "none", "probabilities": {"none": 1.0},
                                      "code": True}
        a = ans.get("table_kind") or {}
        if a.get("choice") in TABLE_KIND["options"]:
            kind_ans = (a["choice"], float((a.get("probabilities") or {}).get(a["choice"], 0)))
            context.append("What each row holds (decided earlier): "
                           + TABLE_KIND["options"][kind_ans[0]])
        a = ans.get("organism_column") or {}
        by_label = {v: k for k, v in labels.items()}
        choice = a.get("choice")
        p = float((a.get("probabilities") or {}).get(choice, 0)) if choice else 0.0
        if choice in by_label and by_label[choice] in headers:
            org = by_label[choice]
            org_ans = (org, p)
            org_full = cell_facts(table, org)["binomial"] >= 0.5
            context.append(f"The column naming each row's organism (decided earlier): "
                           f"'{_clip(org, 60)}'.")
            greedy[org] = soft[org] = ("verbatimIdentification", round(p, 3))
            paths[org] = f"table:organism_column({p:.2f})"
        else:
            org_ans = (None, p) if not a.get("code") else (None, "code")
            context.append("No column names each row's organism (decided earlier): "
                           "the table is about one organism named elsewhere, or its "
                           "rows are not organisms.")

    state = lambda size: table_state(table, paper_text, context, size)
    Item = collections.namedtuple("Item", "h node prob path greedy")
    values = {h: sample_values(table, h) for h in headers}
    facts = {h: cell_facts(table, h) for h in headers}
    frontier = []
    for h in headers:
        if h in greedy:
            continue
        if facts[h]["n"] and facts[h]["numeric"] >= NUMERIC_MIN:
            frontier.append(Item(h, NUMERIC_START, 1.0,
                                 [f"code:numeric({facts[h]['numeric']:.2f})"], True))
        else:
            frontier.append(Item(h, ROOT, 1.0, [], True))
    leaves = collections.defaultdict(list)          # h -> [(field, prob, path, greedy)]
    while frontier:
        by_node = collections.defaultdict(list)
        for it in frontier:
            by_node[it.node].append(it)
        frontier = []
        for node_id, items in by_node.items():
            drop = (NODES[node_id].get("drop_if_organism_column_full", ())
                    if org_full else ())
            qs = {f"q{i}": _question(node_id, it.h, values[it.h],
                                     facts_text(facts[it.h]) + header_text(it.h), drop)
                  for i, it in enumerate(items)}
            answers = client.ask(state, qs)
            for i, it in enumerate(items):
                a = answers.get(f"q{i}") or {}
                probs = {k: float(v) for k, v in (a.get("probabilities") or {}).items()}
                best = a.get("choice")
                options = {k: o for k, o in NODES[node_id]["options"].items()
                           if k not in drop}
                if best not in options:
                    leaves[it.h].append(("none", 0.0, it.path + [f"{node_id}:no answer"],
                                         it.greedy, {}))
                    continue
                for opt, p in sorted(probs.items(), key=lambda kv: -kv[1]):
                    if opt not in options or (opt != best and p < explore):
                        continue
                    o = options[opt]
                    step = f"{node_id}:{opt}({p:.2f})"
                    is_greedy = it.greedy and opt == best
                    nxt = NODES.get(o.get("next"), {})
                    if ("only_if_table_kind" in nxt and kind_ans is not None
                            and kind_ans[0] not in nxt["only_if_table_kind"]):
                        # decided at the table level: not asked per column
                        leaves[it.h].append((nxt["otherwise"], it.prob * p,
                                             it.path + [step, f"{o['next']}:by table "
                                                        f"kind {kind_ans[0]}"],
                                             is_greedy, {}))
                    elif "next" in o:
                        frontier.append(Item(it.h, o["next"], it.prob * p,
                                             it.path + [step], is_greedy))
                    else:
                        extra = {}
                        if o.get("tag_from_header"):
                            extra[o["tag_from_header"]] = (header_statistic(it.h)
                                                           or _clip(it.h, 40))
                        leaves[it.h].append((o["field"] or "none", it.prob * p,
                                             it.path + [step], is_greedy, extra))

    tags = {}                                   # h -> {extra tag: value}
    for h in headers:
        if h in greedy:
            continue
        ls = leaves.get(h) or [("none", 0.0, ["no answer"], True, {})]
        g = next((l for l in ls if l[3]), ls[0])
        greedy[h] = (g[0], round(g[1], 3))
        paths[h] = " > ".join(g[2])
        if g[4]:
            tags[h] = g[4]
        mass = collections.Counter()
        for f, p, _, _, _ in ls:
            mass[f] += p
        f, p = mass.most_common(1)[0]
        soft[h] = (f, round(p, 3))
    return {"greedy": greedy, "soft": soft, "paths": paths, "table_kind": kind_ans,
            "organism_column": org_ans, "skipped": skipped, "tags": tags}


validate()
