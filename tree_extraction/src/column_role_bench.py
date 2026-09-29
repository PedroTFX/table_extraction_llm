"""
column_role_bench.py — EXPERIMENT (not wired into the pipeline): can a decision
model (tev1:4b, nimble) tag a table column's role better than the pipeline's
gemma mapper?

The role of a column is the template field it maps to: verbatimIdentification,
measurementType (a wide trait column), measurementValue (the value column of a
long table), a row field (sex, lifeStage, caste, verbatimLocality,
measurementMethod, measurementStatistic), or none. OsorioCanadas2018 scored 0
because gemma made 'Family' the identifier and 'Hosts species' a trait.

The reference label of every column is DERIVED from the ground-truth xlsx, by
values, not by header names:
  - verbatimIdentification: most of its cells are GT species names
  - measurementType: (row species, cell) pairs are GT (species, value) pairs, or
    its header names a GT measurementType
  - measurementValue: as above, in a long table that also has a column of GT
    measurementType names (that column is then the measurementType)
  - row field: most cells are values the GT records in that field
  - none: none of the above; 'unsure' when the evidence is partial (not scored)

Every model sees the SAME parsed tables (pipeline's collect_tables +
maybe_transpose) and the same template field descriptions:
  gemma   — the pipeline's own mapper prompt (table_to_data._map_columns)
  tev1    — /v1/systemone, one choice question per column
  nimble  — same questions as tev1 (compact state: tev1 takes ~2k tokens)
  nimble_full — nimble with gemma's full field descriptions in the state

    python column_role_bench.py                       # Osorio + 20 sampled papers
    python column_role_bench.py --n 5 --models tev1,nimble
    python column_role_bench.py OsorioCanadas2018 Lizee2016

Writes tree_extraction/output/column_role_bench/{results.json, report.txt}. Parsed tables are
cached there (tables_<paper>.pkl) so a re-run skips the LLM header finding.
"""

from __future__ import annotations

import collections
import difflib
import json
import pickle
import random
import re
import sys
import time
import unicodedata
from pathlib import Path

import _paths  # noqa: F401  (puts the pipeline, source/, on the import path)
from decision_judge import _er, _rq
from evaluate import load_xlsx, normalize_value, species_match
from table_to_data import (DICT_FIELDS, MAP_FIELDS, _field_descriptions_block,
                           _map_columns, _finish_mapping, collect_tables,
                           maybe_transpose, MAPPER_CHUNK_COLS)

ROOT = _paths.REPO
PAPERS = _paths.PAPERS
OUT = _paths.OUTPUT / "column_role_bench"
DECISION_URL = "http://127.0.0.1:11434/v1/systemone"
# name -> (ollama model, full .md descriptions in the state?). tev1 accepts only
# ~2k prompt tokens, so tev1 and nimble get the condensed descriptions in
# CRITERIA; nimble_full also gets the full template_descriptions/*.md text that
# gemma's mapper prompt carries.
DECISION_MODELS = {"tev1": ("tev1:4b", False), "nimble": ("nimble:latest", False),
                   "nimble_full": ("nimble:latest", True)}
ALL_MODELS = ["gemma", "tev1", "nimble", "nimble_full"]
# columns per call: every question carries the whole question set, and tev1's
# ~2k-token cap fits the state plus ONE question with the condensed criteria
DECISION_CHUNK = {"tev1": 1, "nimble": 6, "nimble_full": 6}
FOCUS = "OsorioCanadas2018"

ROW_FIELDS = ["sex", "lifeStage", "caste", "verbatimLocality",
              "measurementMethod", "measurementStatistic"]
LABELS = ["verbatimIdentification", "measurementType", "measurementValue",
          *ROW_FIELDS, "none"]
# Template tags the pipeline's mapper cannot output yet (not in MAP_FIELDS), but
# a column can hold. Labelled only when asked (derive_labels(extra=True)), so the
# flat benchmark keeps its 9-field answer key.
EXTRA_FIELDS = ["verbatimEventDate", "verbatimCoordinates", "sampleSizeValue",
                "measurementUnit", "measurementRemarks", "sampleTreatment",
                "samplingProtocol", "associatedReferences", "associatedOccurrences",
                "externalLink"]

# Condensed from template_descriptions/<field>.md, keeping each file's decisive
# rules (taxonomic ranks are identity, hosts/prey are traits, wide vs long).
CRITERIA = {
    "verbatimIdentification": (
        "the name of the focal INSECT taxon the row is about, as printed: a species "
        "or genus, or a higher rank. A taxonomic rank column naming the organism's "
        "own classification (Family, Order, Subfamily, Genus, Tribe, authorship) "
        "also belongs here. NOT a host, prey or plant the insect interacts with, "
        "a place, a group, a treatment or a statistic"),
    "measurementType": (
        "a WIDE trait column: the header names one property of the organism (what "
        "it is, has, does, or where it lives) and the cells are its values, "
        "numeric or categorical: size, diet, voltinism, overwintering stage, "
        "flight period, host/prey/host plant (the associated organism is the "
        "value), the species' range. Not a site condition, abundance, statistic "
        "or taxonomic rank"),
    "measurementValue": (
        "ONLY in a LONG table: the single column of values, while a SEPARATE "
        "column's cells name the trait. In a wide table, where each header names "
        "a trait, no column is measurementValue"),
    "sex": "the sex of the recorded individuals (male, female, both). Not 'sex ratio'",
    "lifeStage": ("the developmental stage of the recorded individuals (egg, larva, "
                  "pupa, adult). Not a species trait like 'overwintering stage'"),
    "caste": "the caste of the recorded social insects (queen, worker, soldier)",
    "verbatimLocality": ("the place where sampling happened: country, region, named "
                         "site, plot or site code, or habitat used as the sampling "
                         "location. Not where the species lives (a trait)"),
    "measurementMethod": "how the value was measured (a method or protocol)",
    "measurementStatistic": ("which statistic the value is: mean, median, SD, SE, "
                             "min, max, range, count"),
    "none": ("fits none of these: abundances or sample sizes, site variables, test "
             "statistics or indices, notes, references, row numbers"),
}


# --- ground-truth labels -------------------------------------------------------

_REF_RE = re.compile(r"\s*\[[\d,;\s\-–]+\]")
_SUP_RE = re.compile(r"\$\^\{?[^$]*\}?\$|\^[A-Za-z0-9,]+")
_DEC_COMMA_RE = re.compile(r"^-?\d+,\d+$")


def norm(v) -> str:
    s = unicodedata.normalize("NFKC", str(v or ""))
    s = _SUP_RE.sub("", _REF_RE.sub("", s)).strip().strip("*").strip()
    if _DEC_COMMA_RE.match(s):
        s = s.replace(",", ".")
    return normalize_value(s)


def parts(v) -> list:
    """A cell and, for a list cell, its items ('W, S' -> ['w, s', 'w', 's'])."""
    n = norm(v)
    out = [n]
    if re.search(r"[,;/]", n) and not re.match(r"^-?[\d.]+,[\d.]+$", n):
        out += [p.strip() for p in re.split(r"[,;/]| and ", n) if p.strip()]
    return out


class GroundTruth:
    def __init__(self, rows):
        self.ids = sorted({r["verbatimIdentification"].strip() for r in rows
                           if r["verbatimIdentification"].strip()})
        self.types = {norm(r["measurementType"]) for r in rows if r["measurementType"].strip()}
        self.type_names = sorted({r["measurementType"].strip() for r in rows
                                  if r["measurementType"].strip()})
        self.pairs = {(r["verbatimIdentification"].strip(), norm(r["measurementValue"]))
                      for r in rows}
        self.values = {norm(r["measurementValue"]) for r in rows}
        self.field_values = {}
        for f in ROW_FIELDS:
            vals = collections.Counter(norm(r[f]) for r in rows if r[f].strip())
            self.field_values[f] = set(vals) if len(vals) >= 2 else set()
        # extra tags are matched by (species, value) PAIRS: their values are
        # often numbers or short strings that a value-set match would find in
        # unrelated columns. A tag with one value for the whole paper never came
        # from a column, so it is not labelled.
        self.extra_pairs = {}
        for f in EXTRA_FIELDS:
            if len({norm(r[f]) for r in rows if r[f].strip()}) >= 2:
                self.extra_pairs[f] = {(r["verbatimIdentification"].strip(), norm(r[f]))
                                       for r in rows if r[f].strip()}
        self._id_cache = {}

    def match_id(self, cell):
        cell = str(cell or "").strip()
        if not cell:
            return None
        if cell not in self._id_cache:
            hit = next((g for g in self.ids if species_match(cell, g)), None)
            if hit is None:   # 'Osmia bicornis (=rufa)' vs 'Osmia bicornis'
                base = re.sub(r"\s*\(.*?\)", "", cell).strip()
                hit = next((g for g in self.ids if base and species_match(base, g)), None)
            self._id_cache[cell] = hit
        return self._id_cache[cell]


def _frac(hits, total):
    return hits / total if total else 0.0


# measurementType.md: a column naming the organism's own classification (Family,
# Order, Genus, ..., authorship) "belongs with verbatimIdentification"
_RANK_HEADER_RE = re.compile(
    r"\b(?:super|sub|infra)?(?:family|order|class|genus|tribe)\b|\bauthor", re.I)
_ASSOC_HEADER_RE = re.compile(r"host|prey|plant|food|symbiont|partner", re.I)
_RANK_CELL_RE = re.compile(
    r"^(?:[A-Za-z]*(?:idae|inae|ini|oidea|ptera)|acari|araneae)\b", re.I)


def is_rank_column(header, cells) -> bool:
    if _ASSOC_HEADER_RE.search(str(header)):
        return False                 # 'Host family' is a trait of the insect
    if _RANK_HEADER_RE.search(str(header)):
        return True
    cells = [c for c in cells if c]
    return bool(cells) and _frac(sum(1 for c in cells if _RANK_CELL_RE.match(c)),
                                 len(cells)) >= 0.6


def _extra_field(gt, row_ids, cells):
    """(field, evidence) when most rows' (species, cell) pairs are GT pairs of
    one EXTRA_FIELDS tag, else None."""
    best = None
    for f, pairs in gt.extra_pairs.items():
        n = hits = 0
        for rid, c in zip(row_ids, cells):
            if not c or rid is None:
                continue
            n += 1
            hits += any((rid, p) in pairs for p in parts(c))
        if n and hits / n >= 0.6 and (best is None or hits / n > best[1]):
            best = (f, hits / n)
    return (best[0], f"{best[1]:.0%} (species,{best[0]}) pairs in GT") if best else None


def header_names_trait(header, gt: GroundTruth) -> bool:
    h = norm(re.sub(r"\(.*?\)", "", str(header)))
    if not h or len(h) < 3:
        return False
    for t in gt.types:
        if h == t or difflib.SequenceMatcher(None, h, t).ratio() >= 0.8:
            return True
    return False


def derive_labels(table, gt: GroundTruth, extra=False) -> dict:
    """{header: (label, evidence)} for one table."""
    headers = table.header_names
    recs = table.data_records()
    cols = {h: [str(r.get(h, "") or "").strip() for r in recs] for h in headers}

    # identifier column
    id_frac = {}
    for h in headers:
        cells = [c for c in cols[h] if c]
        id_frac[h] = _frac(sum(1 for c in cells if gt.match_id(c)), len(cells))
    id_col = max(headers, key=lambda h: id_frac[h]) if headers else None
    if id_col is not None and id_frac[id_col] < 0.5:
        id_col = None
    if id_col is not None:
        row_ids = [gt.match_id(c) for c in cols[id_col]]
    elif len(gt.ids) == 1:                      # single-species paper
        row_ids = [gt.ids[0]] * len(recs)
    else:
        return {}

    # long table: a column of GT trait names
    type_frac = {h: _frac(sum(1 for c in cols[h] if c and norm(c) in gt.types),
                          sum(1 for c in cols[h] if c))
                 for h in headers if h != id_col}
    type_col = max(type_frac, key=type_frac.get) if type_frac else None
    if type_col is not None and type_frac[type_col] < 0.5:
        type_col = None

    labels = {}
    for h in headers:
        if h == id_col:
            labels[h] = ("verbatimIdentification", f"{id_frac[h]:.0%} GT species")
            continue
        if h == type_col:
            labels[h] = ("measurementType", f"{type_frac[h]:.0%} GT trait names (long)")
            continue
        n = hits = 0
        for rid, c in zip(row_ids, cols[h]):
            if not c or rid is None:
                continue
            n += 1
            if any((rid, p) in gt.pairs for p in parts(c)):
                hits += 1
        pair = _frac(hits, n)
        cells = [c for c in cols[h] if c]
        field_hit = {f: _frac(sum(1 for c in cells if any(p in vs for p in parts(c))),
                              len(cells))
                     for f, vs in gt.field_values.items() if vs}
        best_f = max(field_hit, key=field_hit.get) if field_hit else None
        named = header_names_trait(h, gt)
        trait = "measurementValue" if type_col else "measurementType"
        if pair >= 0.4:
            labels[h] = (trait, f"{pair:.0%} (species,value) pairs in GT")
        elif is_rank_column(h, cols[h]):
            labels[h] = ("verbatimIdentification", "taxonomic rank column (identity)")
        elif best_f and field_hit[best_f] >= 0.6:
            labels[h] = (best_f, f"{field_hit[best_f]:.0%} cells are GT {best_f}")
        elif extra and (ef := _extra_field(gt, row_ids, cols[h])):
            labels[h] = ef
        elif named and not type_col:
            labels[h] = (trait, f"header names a GT trait; pairs {pair:.0%}")
        elif pair >= 0.15 or (named and type_col):
            labels[h] = ("unsure", f"pairs {pair:.0%}, header match {named}")
        else:
            labels[h] = ("none", f"pairs {pair:.0%}")
    return labels


# --- models --------------------------------------------------------------------

def _clean_field(f) -> str:
    if not isinstance(f, str) or not f.strip() or f in DICT_FIELDS:
        return "none"
    f = f.strip()
    return f if f in LABELS else "none"


def ask_gemma(table, paper_text) -> dict:
    headers = table.header_names
    if len(headers) > MAPPER_CHUNK_COLS:
        merged = {}
        for i in range(0, len(headers), MAPPER_CHUNK_COLS):
            merged.update(_map_columns(table, headers, headers[i:i + MAPPER_CHUNK_COLS]))
        mapping = _finish_mapping(merged, headers)
    else:
        mapping = _finish_mapping(_map_columns(table, headers, headers), headers)
    return {h: (_clean_field((mapping.get(h) or {}).get("field")), None) for h in headers}


def _sample_values(table, h, k=6):
    seen, out = set(), []
    for v in table.column_values(h):
        v = re.sub(r"\s+", " ", str(v or "")).strip()
        if v and v.lower() not in seen:
            seen.add(v.lower())
            out.append(v[:60])
        if len(out) >= k:
            break
    return out


def _state(table, paper_text, full=False) -> str:
    headers = table.header_names
    n_rows, width, intro_len = (6, 40, 1500) if full else (4, 25, 400)
    rows = table.data_records()[:n_rows]
    grid = "\n".join(" | ".join(str(r.get(h, "") or "")[:width] for h in headers)
                     for r in rows)
    intro = re.sub(r"\s+", " ", paper_text[:intro_len])
    fields = f"\n\nTemplate fields:\n{_field_descriptions_block()}" if full else ""
    return (f"Mapping one column of a scientific species-trait table to a fixed "
            f"template.\n\nPaper start: {intro}{fields}\n\nTable headers: "
            f"{' | '.join(headers)}\nFirst rows:\n{grid}")


def _post(model, state, questions, timeout=600, retries=2):
    """One /v1/systemone call. A 5xx or a dropped connection is retried after a
    pause: it is the model's runner process dying (nimble's llama-server crashed
    with 0xc0000409 on Habustova2017), which Ollama restarts on the next request.
    A 4xx (e.g. prompt too long) is the caller's to handle."""
    body = {"model": model, "state": state, "questions": questions}
    for attempt in range(retries + 1):
        req = _rq.Request(DECISION_URL, data=json.dumps(body).encode(),
                          headers={"Content-Type": "application/json"})
        try:
            with _rq.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read()).get("answers", {})
        except _er.HTTPError as e:
            if e.code < 500 or attempt == retries:
                raise
        except _er.URLError:
            if attempt == retries:
                raise
        time.sleep(5 * (attempt + 1))


def _ask_split(model, state, questions):
    try:
        return _post(model, state, questions)
    except _er.HTTPError as e:
        msg = e.read().decode("utf-8", "replace")
        if e.code != 400 or len(questions) < 2:
            raise RuntimeError(f"{e.code}: {msg[:200]}")
        keys = list(questions)
        half = len(keys) // 2
        out = _ask_split(model, state, {k: questions[k] for k in keys[:half]})
        out.update(_ask_split(model, state, {k: questions[k] for k in keys[half:]}))
        return out


def ask_decision(name, table, paper_text) -> dict:
    model, full = DECISION_MODELS[name]
    headers = table.header_names
    state = _state(table, paper_text, full)
    got = {}
    size = DECISION_CHUNK[name]
    for i in range(0, len(headers), size):
        chunk = headers[i:i + size]
        qs = {f"q{j}": {"type": "choice",
                        "instructions": f"Column '{h}' (values: "
                                        f"{'; '.join(_sample_values(table, h))}). "
                                        f"Which template field is this column?",
                        "criteria": dict(CRITERIA)}
              for j, h in enumerate(chunk)}
        answers = _ask_split(model, state, qs)
        for j, h in enumerate(chunk):
            a = answers.get(f"q{j}") or {}
            probs = a.get("probabilities") or {}
            choice = a.get("choice") or "none"
            got[h] = (_clean_field(choice), round(float(probs.get(choice, 0.0)), 3))
    return got


# --- run -----------------------------------------------------------------------

def paper_inputs(folder: Path):
    full = folder / f"{folder.name}_full.md"
    if not full.exists():
        return None
    gts = [f for f in folder.iterdir() if f.suffix.lower() == ".xlsx"
           and f.stem.replace("-", "").lower() == folder.name.replace("-", "").lower()]
    return (full, gts[0]) if gts else None


def load_tables(paper, full_md):
    OUT.mkdir(parents=True, exist_ok=True)
    cache = OUT / f"tables_{paper}.pkl"
    if cache.exists():
        return pickle.loads(cache.read_bytes())
    tables = [maybe_transpose(t)[0] for t in collect_tables([str(full_md)])]
    tables = [t for t in tables if t.header_names]
    cache.write_bytes(pickle.dumps(tables))
    return tables


def bench_paper(paper, models):
    folder = PAPERS / paper
    full_md, gt_path = paper_inputs(folder)
    gt = GroundTruth(load_xlsx(gt_path))
    paper_text = full_md.read_text(encoding="utf-8", errors="replace")
    tables = load_tables(paper, full_md)
    out = []
    seen_schemas = set()
    for t in tables:
        sig = tuple(t.header_names)
        if sig in seen_schemas:              # page fragments share one mapping
            continue
        seen_schemas.add(sig)
        labels = derive_labels(t, gt)
        if not any(l not in ("none", "unsure") for l, _ in labels.values()):
            continue                         # table the GT never draws on
        entry = {"table": f"{t.source}#{t.table_index}", "headers": t.header_names,
                 "labels": labels, "pred": {}, "secs": {}}
        for m in models:
            t0 = time.time()
            try:
                pred = (ask_gemma(t, paper_text) if m == "gemma"
                        else ask_decision(m, t, paper_text))
            except Exception as e:           # one failure costs one table, not the run
                print(f"    {m} failed on {entry['table']}: {type(e).__name__}: {e}")
                pred = {h: ("error", None) for h in t.header_names}
            entry["pred"][m] = pred
            entry["secs"][m] = round(time.time() - t0, 1)
        out.append(entry)
        print(f"  {entry['table']}: {len(t.header_names)} cols, "
              + ", ".join(f"{m} {entry['secs'][m]}s" for m in models))
    return out


def pick_papers(n, explicit):
    if explicit:
        return explicit
    others = sorted(p.name for p in PAPERS.iterdir()
                    if p.is_dir() and p.name != FOCUS and paper_inputs(p))
    random.Random(0).shuffle(others)
    return [FOCUS] + others, n          # caller draws until n usable


# --- report --------------------------------------------------------------------

def score(results, models):
    lines = []
    cols = [(paper, e, h) for paper, entries in results.items() for e in entries
            for h in e["headers"] if e["labels"].get(h, ("none",))[0] != "unsure"]
    lines.append(f"{len(results)} papers, {sum(len(v) for v in results.values())} tables, "
                 f"{len(cols)} scored columns "
                 f"({sum(1 for p, e, h in cols if e['labels'][h][0] != 'none')} used by GT)\n")

    def acc(model, pick, lenient=False):
        ok = n = 0
        for p, e, h in cols:
            gold = e["labels"][h][0]
            if not pick(gold):
                continue
            guess = e["pred"][model].get(h, ("none",))[0]
            same = guess == gold or (lenient and {guess, gold} <= {"measurementType",
                                                                  "measurementValue"})
            ok += same
            n += 1
        return ok, n

    groups = [("all columns", lambda g: True),
              ("GT-used columns", lambda g: g != "none"),
              ("  identifier", lambda g: g == "verbatimIdentification"),
              ("  trait (type/value)", lambda g: g in ("measurementType", "measurementValue")),
              ("  row fields", lambda g: g in ROW_FIELDS),
              ("GT-unused columns", lambda g: g == "none")]
    lines.append(f"{'accuracy':28s}" + "".join(f"{m:>16s}" for m in models))
    for name, pick in groups:
        row = f"{name:28s}"
        for m in models:
            ok, n = acc(m, pick)
            row += f"{f'{ok}/{n} {ok / n:.0%}' if n else '-':>16s}"
        lines.append(row)
    row = f"{'GT-used, type~value equal':28s}"
    for m in models:
        ok, n = acc(m, lambda g: g != "none", lenient=True)
        row += f"{f'{ok}/{n} {ok / n:.0%}' if n else '-':>16s}"
    lines.append(row)

    # table-level: identifier picked exactly right (the Osorio failure)
    row = f"{'tables, identifier exact':28s}"
    for m in models:
        ok = n = 0
        for entries in results.values():
            for e in entries:
                gold = {h for h in e["headers"]
                        if e["labels"].get(h, ("",))[0] == "verbatimIdentification"}
                if not gold:
                    continue
                pred = {h for h in e["headers"]
                        if e["pred"][m].get(h, ("",))[0] == "verbatimIdentification"}
                ok += pred == gold
                n += 1
        row += f"{f'{ok}/{n} {ok / n:.0%}' if n else '-':>16s}"
    lines.append(row)
    row = f"{'seconds (total)':28s}"
    for m in models:
        row += f"{sum(e['secs'].get(m, 0) for v in results.values() for e in v):>16.0f}"
    lines.append(row)

    lines.append("\nPER PAPER (GT-used columns correct / total)")
    lines.append(f"{'paper':28s}" + "".join(f"{m:>13s}" for m in models))
    for paper, entries in results.items():
        row = f"{paper:28s}"
        for m in models:
            ok = n = 0
            for e in entries:
                for h in e["headers"]:
                    gold = e["labels"].get(h, ("none",))[0]
                    if gold in ("none", "unsure"):
                        continue
                    n += 1
                    ok += e["pred"][m].get(h, ("",))[0] == gold
            row += f"{f'{ok}/{n}' if n else '-':>13s}"
        lines.append(row)

    for m in models:
        conf = collections.Counter()
        for p, e, h in cols:
            gold = e["labels"][h][0]
            guess = e["pred"][m].get(h, ("none",))[0]
            if guess != gold:
                conf[(gold, guess)] += 1
        lines.append(f"\n{m}: most common confusions (gold -> predicted)")
        for (g, q), c in conf.most_common(8):
            lines.append(f"  {g:24s} -> {q:24s} x{c}")

    lines.append("\nDETAIL: columns where models disagree with the GT label")
    for paper, entries in results.items():
        for e in entries:
            for h in e["headers"]:
                gold, ev = e["labels"].get(h, ("none", ""))
                if gold == "unsure":
                    continue
                preds = {m: e["pred"][m].get(h, ("none", None)) for m in models}
                if all(p[0] == gold for p in preds.values()):
                    continue
                ps = ", ".join(f"{m}={p[0]}" + (f"({p[1]})" if p[1] is not None else "")
                               for m, p in preds.items())
                lines.append(f"  {paper} {e['table']} '{h[:40]}': GT={gold} [{ev}] | {ps}")
    return "\n".join(lines)


def main(argv):
    n = int(argv[argv.index("--n") + 1]) if "--n" in argv else 20
    models = (argv[argv.index("--models") + 1].split(",") if "--models" in argv
              else ALL_MODELS)
    skip = {argv[i + 1] for i, a in enumerate(argv) if a in ("--n", "--models")}
    explicit = [a for a in argv if not a.startswith("--") and a not in skip]
    OUT.mkdir(parents=True, exist_ok=True)
    res_path = OUT / "results.json"
    results = {}
    if explicit:
        queue, want = explicit, len(explicit)
    else:
        queue, want = pick_papers(n, None)
        want = n + 1
    for paper in queue:
        if len(results) >= want:
            break
        print(f"\n=== {paper}")
        try:
            entries = bench_paper(paper, models)
        except Exception as e:
            print(f"  skipped: {type(e).__name__}: {e}")
            continue
        if not entries:
            print("  no table the GT draws on — skipped")
            continue
        results[paper] = entries
        res_path.write_text(json.dumps(results, indent=1, ensure_ascii=False),
                            encoding="utf-8")
    report = score(results, models)
    (OUT / "report.txt").write_text(report, encoding="utf-8")
    print("\n" + report)


if __name__ == "__main__":
    main(sys.argv[1:])
