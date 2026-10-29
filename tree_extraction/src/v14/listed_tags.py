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
        "LivingSpecimen": "living organisms kept or reared (a laboratory culture, rearing, an experiment on live animals)",
        "HumanObservation": "organisms observed in the field or a video, not collected",
        "MachineObservation": "organisms recorded by a device (camera trap, sensor, acoustic recorder)",
        "MaterialSample": "samples taken from organisms (tissue, DNA, gut contents)",
        "MaterialCitation": "data taken from published literature, databases or other studies",
        "Occurrence": "records of where and when the organisms occurred",
        "Taxon": "a description of the taxon itself, not of particular specimens",
        "Event": "a sampling event", "FossilSpecimen": "fossils",
        "MaterialEntity": "a physical object of unspecified kind"},
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


def ask_statistic(ask, t, fields, state):
    out = {}
    if any(fields.get(c.name) == "measurementStatistic" for c in t.columns):
        return out                                   # the table prints it per row
    for name in trait_columns(t, fields)[:MAX_COLS]:
        vals = _distinct(t, name, 8)
        st = state + f" The column '{name}' holds: {', '.join(repr(v) for v in vals)}."
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


def _gemma(prompt):
    body = {"model": v1.GEMMA, "stream": False, "format": READ_SCHEMA, "think": False,
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
        res = {"cells": {}, "labels": {}, "statistic": {}, "captions": {}, "text": {}}
        flat, spans = v3.md_tables(p)
        for t, fields, _o, _x in fr.plan(p, head):
            if not t.records or not trait_columns(t, fields):
                continue
            k = str(t.table_index)
            state = _table_state(t, sp.caption_above(t, flat, spans), kt.caption_below(t, flat, spans))
            res["cells"][k] = ask_cells(ask, t, fields, state)
            res["labels"][k] = ask_labels(ask, t, state)
            res["statistic"][k] = ask_statistic(ask, t, fields, state)
            res["captions"][k] = ask_caption(ask, t, state)
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
            got = ask_text(ask, kind, {tag: quotes[tag] for tag in todo})
            for tag in todo:
                found[tag] += got.get(tag, [])
                value, rec = settle(ask, tag, found[tag])
                if value:
                    res["text"][tag] = {"value": value, "round": kind, "settle": rec}
            ask.unload()
        res["text_found"] = found
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  [tags] {p:22s} " + "; ".join(f"{tag} {res['text'][tag]['value']}" for tag in res["text"])
              + f" | {len(res['captions'])} tables ({time.time() - t0:.0f}s)", flush=True)
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
    for col in trait_columns(t, out):
        tags = x.setdefault(col, {})
        if "measurementStatistic" not in have and (stat.get(col) or {}).get("value"):
            tags["measurementStatistic"] = stat[col]["value"]
        for tag in ("sex", "caste", "basisOfRecord", "lifeStage", "measurementStatistic"):
            if tag in have or tags.get(tag):
                continue
            value = (cap.get(tag) or {}).get("value") or (text.get(tag) or {}).get("value") \
                or (defaults or {}).get(tag)
            if value:
                tags[tag] = value
    return out, x
