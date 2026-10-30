"""The five listed tags (v14, output/eval_split/DESIGN_listed_tags_v14.md): sex, caste, basisOfRecord,
lifeStage and measurementStatistic, each from the annotation template's own list of values. nimble
classifies evidence into the list (one question; the top options in duels when it is not sure); code
picks the questions and applies the sure answers at the level the evidence came from.

  cells      a table column tagged with the tag, and section labels the section step gave the tag:
             each distinct printed value -> a value of the list, or 'not a <tag>'          (row level)
  statistic  per trait column of a table with no statistic column: which statistic its values are
                                                                                      (column level)
  captions   per table, per tag but the statistic: what the caption and the text above / below say
                                                                                       (table level)
  text       the paper read in rounds (abstract + methods, introduction, supplements, results +
             discussion; references and the like left out): gemma quotes the sentences about each
             tag, code keeps the quotes printed in the paper, nimble classifies each; differing sure
             answers are asked again together; a round with no sure answer reads the next
                                                                                       (paper level)
  specimen   basisOfRecord resting on quotes nimble gave it under 0.95 only: the methods' sentences on
             collecting and keeping the organisms asked again (alive / preserved / observed)
  source     per trait (column, or trait name of a long table): measured in this study or taken from
             the literature; the literature -> MaterialCitation for that trait, before the paper's answer
                                                                                     (column level)

    python full_run_v14.py v14:tags <papers>     writes <run>/listed_tags/<paper>.json
"""
import copy
import json
import re
import time
import urllib.request

import _paths
import decoder as v1
import decoder_v3 as v3
import duels
import full_run as fr
import kind_tree as kt
import section_tree as sec
import species_tree as sp

SURE = duels.SURE
TAGS = ["sex", "caste", "basisOfRecord", "lifeStage", "measurementStatistic"]
# the tags apply() fills. v14 adopted the first four (measurementStatistic failed held); v15 re-reads
# the statistic (restat: sentences about the analysis dropped) and applies it, to be measured on
# dev + held_a (output/eval_split/split_v15.json)
ADOPTED = ["sex", "caste", "basisOfRecord", "lifeStage", "measurementStatistic"]
NAME = {"sex": "sex", "caste": "caste", "basisOfRecord": "kind of record", "lifeStage": "life stage",
        "measurementStatistic": "statistic"}
# the template's lists (Excel dropdowns of the GT spreadsheets), each with what it means
LISTS = {
    "sex": {"both": "both sexes: males and females together, or not separated",
            "female": "females", "male": "males", "unknown": "the sex is not known"},
    "caste": {"queen": "queens (gynes)", "male alate": "winged males of a social insect colony",
              "worker": "workers", "minor worker": "minor (small) workers", "major worker": "major (large) workers",
              "soldier": "soldiers"},
    "basisOfRecord": {
        "PreservedSpecimen": "specimens collected and preserved (pinned, dried, in ethanol, in a collection)",
        "LivingSpecimen": "organisms kept alive or reared during the study (a laboratory culture, rearing, experiments on live animals), not ones collected and killed for measuring",
        "HumanObservation": "organisms observed in the field or a video, not collected",
        "MachineObservation": "organisms recorded by a device (camera trap, sensor, acoustic recorder)",
        "MaterialSample": "samples taken from organisms (tissue, DNA, gut contents)",
        "MaterialCitation": "data taken from published literature, databases or other studies",
        "Occurrence": "records of where and when the organisms occurred",
        "Taxon": "a description of the taxon itself, not of particular specimens"},
        # the template also lists Event, FossilSpecimen and MaterialEntity; no GT of either set uses them
    "lifeStage": {"adult": "adults (imagines)", "larva": "larvae", "mature larva": "mature (last stage) larvae",
                  "nymph": "nymphs", "caterpillar": "caterpillars", "pupa": "pupae", "egg": "eggs",
                  "instar": "a numbered larval or nymphal instar", "all": "all life stages together",
                  "unknown": "the life stage is not known"},
    "measurementStatistic": {
        "individual": "values of single individuals or specimens", "mean": "means (averages), no spread given",
        "mean ± SD": "means with their standard deviation", "mean ± SE": "means with their standard error",
        "range": "ranges (minimum to maximum)", "min": "minimum values", "max": "maximum values",
        "median": "medians", "count": "counts (numbers of individuals or items)",
        "mode": "a category or class given to each species or group (a categorical trait)",
        "single observation": "one observation", "unknown": "the statistic is not stated"},
}
NOT = {"cell": "none of these: the value is not a {name} (an identifier, a group number, a count or other information)",
       "said": "the text does not say which {name}"}
CHUNK, MAX_CHUNKS = 3000, 6            # characters per gemma call, calls per round
MAX_COLS = 40                          # statistic questions per table
MAX_VALUES = 30                        # distinct values asked per column
MAX_QUOTES = 4                         # quotes classified per tag per round
ROUNDS = [("abstract and methods", ("title and abstract", "methods")), ("introduction", ("introduction",)),
          ("supplementary material", ("supplements",)), ("results and discussion", ("results", "discussion"))]
SUPP = re.compile(r"<!--\s*=+\s*Complementary:.*?-->", re.I)


def _flat(s):
    return " ".join(str(s or "").split())


def _words(s):
    return re.findall(r"[a-z0-9]+", str(s or "").lower())


# --- one question over a list -----------------------------------------------------------------

def classify(ask, state, question, tag, extra=None):
    """The list of `tag` (plus `extra` {label: text}) as options. One question; when it is not sure,
    its three likeliest options meet in duels and the one left meets the extra option(s).
    -> (label or None, record)."""
    opts = {f"o{i}": (v, t) for i, (v, t) in enumerate(LISTS[tag].items())}
    opts.update({k: (k, t) for k, t in (extra or {}).items()})
    ch, probs = ask(state, question, {k: t for k, (_v, t) in opts.items()})
    rec = {"choice": opts.get(ch, (ch,))[0], "probs": {opts[k][0]: p for k, p in probs.items() if k in opts}}
    if duels.sure(ch, probs, *opts):
        return opts[ch][0], rec
    top = [k for k, _p in sorted(probs.items(), key=lambda kv: -kv[1]) if k in opts and k not in (extra or {})][:3]
    held, log = duels.duel(ask, state, question, [(k, opts[k][1]) for k in top])
    rec["duels"] = log
    if held is None:
        return None, rec
    if not extra:                                    # the list has its own 'unknown'
        return opts[top[held]][0], rec
    final = {"pick": opts[top[held]][1], **extra}
    ch2, p2 = ask(state, question, final)
    rec["final"] = {"choice": ch2, "probs": p2}
    if duels.sure(ch2, p2, "pick"):
        return opts[top[held]][0], rec
    if extra and duels.sure(ch2, p2, *extra):
        return ch2, rec
    return None, rec


def _instar(value, evidence):
    """'instar' -> 'instar N' when the evidence prints the number; else not a list value."""
    if value != "instar":
        return value
    m = re.search(r"\b(\d{1,2})\b", str(evidence or ""))
    return f"instar {m.group(1)}" if m else None


# --- the evidence -------------------------------------------------------------------------------

def _table_state(t, above, below):
    s = f"A table in a scientific paper has the columns {[c.name for c in t.columns][:14]}."
    if above:
        s += f" The text printed directly above it: '{above}'."
    if below:
        s += f" The text printed directly below it: '{below}'."
    return s + f" Its first rows read: {kt._shown(t, 3)}."


def _distinct(t, col, k=MAX_VALUES):
    out = []
    for r in t.records:
        v = _flat(r.get(col))
        if v and v not in out:
            out.append(v)
    return out[:k]


def ask_cells(ask, t, fields, state):
    """Columns tagged with a listed tag: each distinct value classified. -> {column: {tag, values}}"""
    out = {}
    for col in t.columns:
        tag = fields.get(col.name)
        if tag not in LISTS:
            continue
        vals = _distinct(t, col.name)
        st = state + f" The column '{col.name}' holds: {', '.join(repr(v) for v in vals)}."
        res = {}
        for v in vals:
            label, rec = classify(ask, st, f"Which {NAME[tag]} does the cell '{v}' of the column '{col.name}' give?",
                                  tag, {"not": NOT["cell"].format(name=NAME[tag])})
            res[v] = dict(rec, value=_instar(label, v) if label else None)
        out[col.name] = {"tag": tag, "values": res}
    return out


def ask_labels(ask, t, state):
    """Section labels the section step gave sex / caste / life stage: each label classified."""
    dec = getattr(t, "section_dec", None) or {}
    out = {}
    for i, a in (dec.get("answers") or {}).items():
        k = a.get("final")
        if k == "context":
            k = (a.get("context") or {}).get("choice")
        tag = {"sex": "sex", "caste": "caste", "lifeStage": "lifeStage"}.get(k)
        if not tag:
            continue
        label = dec["labels"][int(i)][1]
        got, rec = classify(ask, state, f"Which {NAME[tag]} does the section label '{label}' in this table give?",
                            tag, {"not": NOT["cell"].format(name=NAME[tag])})
        out[i] = dict(rec, tag=tag, label=label, value=_instar(got, label) if got else None)
    return out


def trait_columns(t, fields):
    """The columns whose cells are trait values: the value columns of a long reading, else every
    trait column."""
    names = [c.name for c in t.columns if fields.get(c.name) == "measurementType"]
    values = [c.name for c in t.columns if fields.get(c.name) == "measurementValue"]
    return values if names and values else names + values


def grain(t, fields, org):
    """What one row of the table is, as the rows will be read: one species per row, or species
    repeating over rows (single specimens or groups). -> sentence or ''."""
    sps = [s for s in (fr.species_of(t, fields, org, r) for r in t.records) if s]
    if len(sps) < 3:
        return ""
    n = len(set(sps))
    return (f" Each of its {n} species takes one row." if n == len(sps)
            else f" Its {len(sps)} rows hold {n} species, so a species takes several rows.")


def ask_statistic(ask, t, fields, state, rows="", quotes=()):
    """Per trait column: which statistic its values are. The table, what one row is, and the paper's
    sure sentences about the statistic (Eckert2023: 'an average body length' per species)."""
    out = {}
    if any(fields.get(c.name) == "measurementStatistic" for c in t.columns):
        return out                                   # the table prints it per row
    said = (" The paper says about its values: " + " ".join(f"'{q}'" for q in quotes[:MAX_QUOTES])) if quotes else ""
    for name in trait_columns(t, fields)[:MAX_COLS]:
        vals = _distinct(t, name, 8)
        st = state + rows + said + f" The column '{name}' holds: {', '.join(repr(v) for v in vals)}."
        got, rec = classify(ask, st, f"What are the values in the column '{name}'?", "measurementStatistic")
        out[name] = dict(rec, value=got)
    return out


def ask_caption(ask, t, state):
    out = {}
    for tag in ("sex", "caste", "basisOfRecord", "lifeStage"):
        q = ("Where do the records in this table come from?" if tag == "basisOfRecord"
             else f"Which {NAME[tag]} were the measurements in this table taken on?")
        got, rec = classify(ask, state, q, tag, {"not": f"the table and the text around it do not say which {NAME[tag]}"})
        out[tag] = dict(rec, value=got if got != "not" else None)
    return out


# --- the paper text ------------------------------------------------------------------------------

def sections(paper):
    """{part: text}: the paper split at its headings as species_tree reads it (end matter left out),
    and 'supplements': the text of every complementary file. Tables are left out."""
    f = _paths.PAPERS / paper / f"{paper}_full.md"
    if not f.exists():
        return {}
    raw = f.read_text(encoding="utf-8", errors="replace")
    pieces = SUPP.split(raw)
    out, kind = {}, "title and abstract"
    for line in pieces[0].splitlines():
        if line.lstrip().startswith("#"):
            for name, rx in sp.KIND:
                if rx.search(line):
                    kind = name
                    break
        out.setdefault(kind, []).append(line)
    res = {k: _flat(sp._clean_md("\n".join(v))) for k, v in out.items() if k != "end"}
    res["supplements"] = _flat(sp._clean_md("\n".join(pieces[1:])))
    return {k: v for k, v in res.items() if v}


READ = """Below is part of the {kind} of a scientific paper about insects and their traits.

Copy, word for word, the sentences that say (at most two sentences per item; leave an item empty when this text does not say it):
- sex: which sex or sexes of the organisms were measured or recorded
- caste: which caste of a social insect was measured (workers, queens, soldiers, males)
- basisOfRecord: how the organisms or the data were obtained: specimens collected and preserved, living or reared organisms, field observations, or data taken from the literature or databases
- lifeStage: which life stage was measured (eggs, larvae, nymphs, pupae, adults)
- measurementStatistic: what the reported trait values are: individual measurements, means, means with SD or SE, ranges, counts

Text:
{text}"""
READ_SCHEMA = {"type": "object", "required": TAGS,
               "properties": {t: {"type": "array", "items": {"type": "string"}} for t in TAGS}}


def _gemma(prompt, schema=READ_SCHEMA):
    body = {"model": v1.GEMMA, "stream": False, "format": schema, "think": False,
            "messages": [{"role": "user", "content": prompt}], "options": {"temperature": 0, "num_ctx": 16384}}
    for attempt in range(3):
        try:
            req = urllib.request.Request("http://127.0.0.1:11434/api/chat", data=json.dumps(body).encode(),
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=900) as r:
                got = json.loads(json.loads(r.read()).get("message", {}).get("content", "") or "{}")
            return got if isinstance(got, dict) else {}
        except json.JSONDecodeError:
            return {}
        except Exception:
            if attempt == 2:
                raise
            time.sleep(10 * (attempt + 1))


def read_round(kind, text):
    """gemma over the round's text in chunks -> {tag: [quotes printed in the text]}."""
    out = {t: [] for t in TAGS}
    for i in range(0, min(len(text), CHUNK * MAX_CHUNKS), CHUNK):
        piece = text[i:i + CHUNK]
        flat = " ".join(_words(piece))
        got = _gemma(READ.format(kind=kind, text=piece))
        for t in TAGS:
            for q in got.get(t) or []:
                q = _flat(q)
                w = " ".join(_words(q))
                if len(w) > 15 and w in flat and q not in out[t]:      # printed in this text
                    out[t].append(q)
    return out


def ask_text(ask, kind, quotes):
    """Each quote classified -> {tag: [{quote, value, record}]} (sure answers have a value)."""
    out = {}
    for tag, qs in quotes.items():
        for q in qs[:MAX_QUOTES]:
            st = f"The {kind} of a scientific paper about insect traits says: '{q}'."
            q2 = ("How were the organisms or data in this paper obtained?" if tag == "basisOfRecord"
                  else f"Which {NAME[tag]} were the paper's measurements taken on?" if tag != "measurementStatistic"
                  else "What are the trait values the paper reports?")
            got, rec = classify(ask, st, q2, tag, {"not": NOT["said"].format(name=NAME[tag])})
            out.setdefault(tag, []).append(dict(rec, quote=q, value=_instar(got, q) if got not in (None, "not") else None))
    return out


ORIGIN_Q = "Where do the trait data of this paper come from?"
ORIGIN = {"own": "the authors collected, observed or reared the organisms themselves for this study and measured them",
          "compiled": "the trait data were compiled from published literature, databases or other studies"}


def ask_origin(ask, secs, quotes):
    """Own data or compiled from the literature (-> MaterialCitation): the abstract and the quotes about
    how the data were obtained. -> (choice or None, record)."""
    st = ("A scientific paper about insect traits. Its title and abstract: '"
          + secs.get("title and abstract", "")[:1500] + "'.")
    if quotes:
        st += " It also says: " + " ".join(f"'{q}'" for q in quotes[:MAX_QUOTES])
    ch, probs = ask(st, ORIGIN_Q, dict(ORIGIN))
    return duels.sure(ch, probs, *ORIGIN), {"choice": ch, "probs": probs}


def _sentences(secs, parts):
    return [s for x in parts for s in re.split(r"(?<=[.!?])\s+", secs.get(x, "")) if len(s) > 20]


SOURCE_Q = "Where do the values of the trait '{name}' in this table come from?"
SOURCE = {"measured": "the authors measured, scored or observed it on the organisms of this study",
          "literature": "it was taken from published literature, databases or other studies"}


def trait_items(t, fields):
    """The traits of a table as the source question names them: the trait columns of a wide reading,
    the trait names a long reading prints. -> (long?, [name])."""
    names = [c.name for c in t.columns if fields.get(c.name) == "measurementType"]
    values = [c.name for c in t.columns if fields.get(c.name) == "measurementValue"]
    if names and values:
        return True, _distinct(t, names[0])
    return False, trait_columns(t, fields)[:MAX_COLS]


def ask_source(ask, state, items, secs):
    """Per trait the paper names in a sentence: measured in this study or taken from the literature
    (-> MaterialCitation). The table and those sentences only; a trait no sentence names is not asked
    and keeps the paper's answer (with the paper-wide quotes, Raine2018's measured traits became
    'literature'). -> {name: record with value 'measured' / 'literature' / None}."""
    pool = _sentences(secs, ("methods", "title and abstract", "supplements", "results"))
    out = {}
    for name in items:
        w = [x for x in _words(name) if len(x) >= 3 and not x.isdigit()]
        said = [s for s in pool if w and all(x in _words(s) for x in w)][:2]
        if not said:
            out[name] = {"said": [], "value": None}
            continue
        st = state + f" About '{name}' the paper says: " + " ".join(f"'{s[:400]}'" for s in said)
        ch, probs = ask(st, SOURCE_Q.format(name=name), dict(SOURCE))
        out[name] = {"choice": ch, "probs": probs, "said": said, "value": ch if duels.sure(ch, probs, *SOURCE) else None}
    return out


SPECIMEN_Q = "In what state were the organisms when the paper's traits were measured on them?"
SPECIMEN = {"LivingSpecimen": "alive: kept alive, reared or used in experiments on live animals during the study",
            "PreservedSpecimen": "collected and killed, then preserved (pinned, dried, frozen, in ethanol) or kept in a collection",
            "HumanObservation": "not collected: observed or counted in the field",
            "not": "the text does not say"}
SPECIMEN_WORDS = re.compile(r"collect|sampl|preserv|ethanol|alcohol|pinn|frozen|freez|dried|alive|live\b|living|"
                            r"rear|laborator|kept|killed|stored|museum|specimen|captur|trap|observ", re.I)
WEAK = 0.95                                          # one quote under this is asked again with the methods


def ask_specimen(ask, secs):
    """The methods' sentences about collecting, keeping and storing the organisms -> one value of
    SPECIMEN (or None), and the record."""
    said = [s for s in _sentences(secs, ("methods",)) if SPECIMEN_WORDS.search(s)][:8]
    if not said:
        return None, {"said": []}
    st = "The methods of a scientific paper about insect traits say: " + " ".join(f"'{s[:400]}'" for s in said)
    ch, probs = ask(st, SPECIMEN_Q, dict(SPECIMEN))
    ok = duels.sure(ch, probs, *SPECIMEN) and ch != "not"
    return (ch if ok else None), {"choice": ch, "probs": probs, "said": said}


def _weak(tag, found, value):
    """The settled value rests only on quotes nimble gave it under WEAK."""
    ps = [(f.get("probs") or {}).get(value) for f in found if f.get("value") == value]
    return bool(ps) and all(p is not None and p < WEAK for p in ps)


def settle(ask, tag, found):
    """The sure answers of one tag so far -> (value or None, record). One value: it. Several: all
    their quotes asked together, with 'different values for different parts of the study'."""
    vals = {}
    for f in found:
        if f.get("value"):
            vals.setdefault(f["value"], f["quote"])
    if not vals:
        return None, None
    if len(vals) == 1:
        return next(iter(vals)), {"by": "one value"}
    st = "A scientific paper about insect traits says: " + " ".join(f"'{q}'" for q in vals.values())
    got, rec = classify(ask, st, f"Which {NAME[tag]} were the paper's measurements taken on?", tag,
                        {"mixed": "different ones for different parts of the study"})
    return (got if got not in (None, "mixed") else None), dict(rec, by="clash", values=list(vals))


# --- the stage ------------------------------------------------------------------------------------

def run(run_dir, papers):
    """One paper at a time; resumable (run_dir/listed_tags/<paper>.json). fr.plan must give v13's
    reading of the tables (install(run, every layer))."""
    out = run_dir / "listed_tags"
    out.mkdir(parents=True, exist_ok=True)
    head = fr.head_runs()
    ask = duels.Nimble()
    for p in papers:
        f = out / f"{p}.json"
        if f.exists() or p not in head:
            continue
        t0 = time.time()
        res = {"cells": {}, "labels": {}, "statistic": {}, "captions": {}, "text": {}, "source": {}}
        flat, spans = v3.md_tables(p)
        traits = {}
        for t, fields, org, _x in fr.plan(p, head):
            if not t.records or not trait_columns(t, fields):
                continue
            k = str(t.table_index)
            state = _table_state(t, sp.caption_above(t, flat, spans), kt.caption_below(t, flat, spans))
            res["cells"][k] = ask_cells(ask, t, fields, state)
            res["labels"][k] = ask_labels(ask, t, state)
            res["captions"][k] = ask_caption(ask, t, state)
            traits[k] = (state, trait_items(t, fields), t, fields, grain(t, fields, org))
        ask.unload()
        secs = sections(p)
        found = {tag: [] for tag in TAGS}
        for kind, parts in ROUNDS:
            todo = [tag for tag in TAGS if tag not in res["text"]]
            text = " ".join(secs.get(x, "") for x in parts)
            if not todo or not text:
                continue
            quotes = read_round(kind, text)
            v1.unload(v1.GEMMA)
            if "basisOfRecord" in todo and "origin" not in res:     # own data, or compiled (MaterialCitation)
                got, rec = ask_origin(ask, secs, quotes["basisOfRecord"])
                res["origin"] = dict(rec, value=got)
                if got == "compiled":
                    res["text"]["basisOfRecord"] = {"value": "MaterialCitation", "round": kind,
                                                    "settle": {"by": "origin"}}
                    todo = [t for t in todo if t != "basisOfRecord"]
            got = ask_text(ask, kind, {tag: quotes[tag] for tag in todo})
            for tag in todo:
                found[tag] += got.get(tag, [])
                value, rec = settle(ask, tag, found[tag])
                if value:
                    res["text"][tag] = {"value": value, "round": kind, "settle": rec}
            ask.unload()
        b = res["text"].get("basisOfRecord") or {}
        if b.get("value") in SPECIMEN and (b.get("settle") or {}).get("by") == "one value" \
                and _weak("basisOfRecord", found["basisOfRecord"], b["value"]):
            got, rec = ask_specimen(ask, secs)       # one weak quote: the methods asked again
            res["specimen"] = dict(rec, value=got, was=b["value"])
            if got:
                res["text"]["basisOfRecord"] = dict(b, value=got, settle={"by": "specimen"})
        stat_quotes = [f["quote"] for f in found["measurementStatistic"] if f.get("value")]
        for k, (state, (long_, items), t, fields, rows) in traits.items():
            res["source"][k] = {"long": long_, "traits": ask_source(ask, state, items, secs)}
            res["statistic"][k] = ask_statistic(ask, t, fields, state, rows, stat_quotes)
            res["rows"] = dict(res.get("rows") or {}, **{k: rows})
        ask.unload()
        res["text_found"] = found
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  [tags] {p:22s} " + "; ".join(f"{tag} {res['text'][tag]['value']}" for tag in res["text"])
              + f" | {len(res['captions'])} tables ({time.time() - t0:.0f}s)", flush=True)
    ask.unload()


# --- v15: the statistic read again, sentences about the analysis left out --------------------------

READ_STAT = """Below is part of the {kind} of a scientific paper about insects and their traits.

Copy, word for word, at most two sentences that say what the paper's trait values of the organisms are: values of single individuals or specimens, means per species (with or without SD or SE), ranges, medians, counts, or a class given to each species. Leave the list empty when this text does not say it.
Do not copy sentences about statistics of the analysis instead of the organisms' trait values: community weighted means, diversity or richness indices, model results or errors, averages per site, plot or sample, or captions of figures and tables showing such results.

Text:
{text}"""
STAT_SCHEMA = {"type": "object", "required": ["measurementStatistic"],
               "properties": {"measurementStatistic": {"type": "array", "items": {"type": "string"}}}}
ANALYSIS = ("the sentence is about a statistic of the analysis (community weighted means, diversity indices, "
            "model results, averages per site or plot), not about the trait values of the organisms")


def read_stat(kind, text):
    """gemma over the round's text in chunks -> [statistic quotes printed in the text]."""
    out = []
    for i in range(0, min(len(text), CHUNK * MAX_CHUNKS), CHUNK):
        piece = text[i:i + CHUNK]
        flat = " ".join(_words(piece))
        got = _gemma(READ_STAT.format(kind=kind, text=piece), STAT_SCHEMA)
        for q in got.get("measurementStatistic") or []:
            q = _flat(q)
            w = " ".join(_words(q))
            if len(w) > 15 and w in flat and q not in out:
                out.append(q)
    return out


def ask_stat_text(ask, kind, quotes):
    """Each quote classified, with 'about the analysis' as a way out -> [{quote, value, record}]."""
    out = []
    for q in quotes[:MAX_QUOTES]:
        st = f"The {kind} of a scientific paper about insect traits says: '{q}'."
        got, rec = classify(ask, st, "What are the trait values the paper reports?", "measurementStatistic",
                            {"not": NOT["said"].format(name=NAME["measurementStatistic"]), "analysis": ANALYSIS})
        out.append(dict(rec, quote=q, value=got if got not in (None, "not", "analysis") else None))
    return out


def restat(run_dir, prev_dir, papers):
    """v14's decisions with the statistic asked again: the paper text read for it alone (READ_STAT),
    each quote classified with ANALYSIS as an option, settled as before; then every trait column
    asked again with the sure quotes left. Resumable: run_dir/listed_tags/<paper>.json."""
    out = run_dir / "listed_tags"
    out.mkdir(parents=True, exist_ok=True)
    head = fr.head_runs()
    ask = duels.Nimble()
    tag = "measurementStatistic"
    for p in papers:
        f, src = out / f"{p}.json", prev_dir / "listed_tags" / f"{p}.json"
        if f.exists() or not src.exists() or p not in head:
            continue
        t0 = time.time()
        res = json.loads(src.read_text(encoding="utf-8"))
        res["text"].pop(tag, None)
        secs = sections(p)
        found = []
        for kind, parts in ROUNDS:
            text = " ".join(secs.get(x, "") for x in parts)
            if not text:
                continue
            quotes = read_stat(kind, text)
            v1.unload(v1.GEMMA)
            found += ask_stat_text(ask, kind, quotes)
            value, rec = settle(ask, tag, found)
            ask.unload()
            if value:
                res["text"][tag] = {"value": value, "round": kind, "settle": rec}
                break
        res["text_found"][tag] = found
        sure = [x["quote"] for x in found if x.get("value")]
        res["statistic"], res["rows"] = {}, {}
        flat, spans = v3.md_tables(p)
        for t, fields, org, _x in fr.plan(p, head):
            if not t.records or not trait_columns(t, fields):
                continue
            k = str(t.table_index)
            state = _table_state(t, sp.caption_above(t, flat, spans), kt.caption_below(t, flat, spans))
            res["rows"][k] = grain(t, fields, org)
            res["statistic"][k] = ask_statistic(ask, t, fields, state, res["rows"][k], sure)
        ask.unload()
        res["v15"] = "statistic read again; sentences about the analysis left out"
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        n_out = sum(1 for x in found if x.get("choice") == "analysis")
        print(f"  [stat] {p:22s} {(res['text'].get(tag) or {}).get('value')} | {len(found)} quotes, "
              f"{n_out} about the analysis ({time.time() - t0:.0f}s)", flush=True)
    ask.unload()


STAT_WORDS = {"mean", "means", "average", "sd", "se", "std", "error", "range", "min", "max", "median",
              "total", "value", "values", "number", "per", "and", "the", "of"}


def trait_sentences(pool, name, k=2):
    """The sentences that name the trait (every word of the column name, its statistic words and
    units left out); none when nothing but those is left."""
    w = [x for x in _words(name) if len(x) >= 3 and not x.isdigit() and x not in STAT_WORDS]
    return [s for s in pool if w and all(x in _words(s) for x in w)][:k] if w else []


def ask_statistic_named(ask, t, fields, state, rows, pool):
    """Per trait column: which statistic its values are, with the sentences that name this trait only
    (v15 run 2: one paper value cannot fit a paper's numeric and class traits; Teder2020's wingspan
    column needs 'Average wingspan ...', its voltinism column the voltinism sentence)."""
    out = {}
    if any(fields.get(c.name) == "measurementStatistic" for c in t.columns):
        return out                                   # the table prints it per row
    for name in trait_columns(t, fields)[:MAX_COLS]:
        vals = _distinct(t, name, 8)
        said = trait_sentences(pool, name)
        st = state + rows + (f" About '{name}' the paper says: " + " ".join(f"'{s[:400]}'" for s in said) if said else "") \
            + f" The column '{name}' holds: {', '.join(repr(v) for v in vals)}."
        got, rec = classify(ask, st, f"What are the values in the column '{name}'?", "measurementStatistic")
        out[name] = dict(rec, value=got, said=said)
    return out


def restat_columns(run_dir, papers):
    """Run 2 on restat's decisions: every trait column asked again with the methods' and supplements'
    sentences that name its trait, instead of the paper-wide quotes; the paper value is kept.
    Resumable ('v15_cols': 2)."""
    head = fr.head_runs()
    ask = duels.Nimble()
    for p in papers:
        f = run_dir / "listed_tags" / f"{p}.json"
        if not f.exists() or p not in head:
            continue
        res = json.loads(f.read_text(encoding="utf-8"))
        if res.get("v15_cols") == 2:
            continue
        t0 = time.time()
        pool = _sentences(sections(p), ("methods", "supplements"))
        flat, spans = v3.md_tables(p)
        res["statistic"] = {}
        for t, fields, org, _x in fr.plan(p, head):
            if not t.records or not trait_columns(t, fields):
                continue
            k = str(t.table_index)
            state = _table_state(t, sp.caption_above(t, flat, spans), kt.caption_below(t, flat, spans))
            res["statistic"][k] = ask_statistic_named(ask, t, fields, state, (res.get("rows") or {}).get(k, ""), pool)
        res["v15_cols"] = 2
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        n = sum(1 for s in res["statistic"].values() for a in s.values() if a.get("said"))
        m = sum(len(s) for s in res["statistic"].values())
        print(f"  [cols] {p:22s} {m} columns, {n} with a sentence naming the trait ({time.time() - t0:.0f}s)", flush=True)
    ask.unload()


# --- applying the answers (the v14 layer of plan()) -------------------------------------------------

def apply(dec, t, fields, xtags, defaults=None):
    """One table: printed values mapped onto the list in its records and section labels (row level),
    the statistic per trait column (column level), the caption's answer, else the paper's (table and
    paper level) for the tags no column or label of the table gives; `defaults` {tag: value} last.
    -> (tags, extra tags)."""
    if not dec:
        return fields, xtags
    k = str(t.table_index)
    out, x = dict(fields), {c: dict(v) for c, v in xtags.items()}
    have = set()
    for col, d in ((dec.get("cells") or {}).get(k) or {}).items():
        if d["tag"] not in ADOPTED:                  # left as printed (v13)
            continue
        answers = {v: a.get("value") for v, a in d["values"].items()}
        if answers and all(a == "not" for a in answers.values()):
            out[col] = "none"                        # not this tag at all (Luo2023's group numbers)
            continue
        have.add(d["tag"])
        for rec in t.records:
            v = _flat(rec.get(col))
            if answers.get(v) and answers[v] != "not":
                rec[col] = answers[v]
    labels = (dec.get("labels") or {}).get(k) or {}
    if labels and getattr(t, "section_dec", None):
        t.section_dec = copy.deepcopy(t.section_dec)
        for i, a in labels.items():
            if a.get("value") and a["value"] != "not":
                t.section_dec["labels"][int(i)][1] = a["value"]
                have.add(a["tag"])
    for rec in t.records:                            # what section labels still give, as printed
        have.update(sec.fields_of(sec.record_info(getattr(t, "section_dec", None), rec)))
    stat = (dec.get("statistic") or {}).get(k) or {}
    cap = (dec.get("captions") or {}).get(k) or {}
    text = dec.get("text") or {}
    compiled = ((text.get("basisOfRecord") or {}).get("settle") or {}).get("by") == "origin"
    src = (dec.get("source") or {}).get(k) or {}
    per = {n: a.get("value") for n, a in (src.get("traits") or {}).items()}
    if src.get("long"):                              # one answer for all value columns, only when every trait agrees
        vals = set(per.values())
        one = next(iter(vals)) if len(vals) == 1 else None
        per = {c: one for c in trait_columns(t, out)} if one else {}
    measured = (cap.get("basisOfRecord") or {}).get("value") or \
        (None if compiled else (text.get("basisOfRecord") or {}).get("value"))
    own = {"literature": "MaterialCitation",         # the trait's own source before the paper's answer;
           "measured": measured if measured != "MaterialCitation" else ""}   # measured here: the specimens' kind
    for col in trait_columns(t, out):
        tags = x.setdefault(col, {})
        if "measurementStatistic" in ADOPTED and "measurementStatistic" not in have and (stat.get(col) or {}).get("value"):
            tags["measurementStatistic"] = stat[col]["value"]
        for tag in ADOPTED:
            if tag in have or tags.get(tag):
                continue
            if tag == "basisOfRecord" and per.get(col):
                if own[per[col]]:
                    tags[tag] = own[per[col]]
                continue
            if tag == "basisOfRecord" and compiled:      # compiled data: the paper-level answer wins
                tags[tag] = "MaterialCitation"
                continue
            value = (cap.get(tag) or {}).get("value") or (text.get(tag) or {}).get("value") \
                or (defaults or {}).get(tag)
            if value:
                tags[tag] = value
    return out, x
