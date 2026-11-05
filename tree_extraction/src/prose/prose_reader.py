"""
prose_reader.py — EXPERIMENT (2026-11-03): traits printed in the running text of a paper, not in
its tables (output/eval_split/DESIGN_prose.md; the set: output/eval_split/prose_set.json).

Code cuts the text into passages and keeps the paper's order; the models read and decide:

  cut      (code)    references, back matter, page noise and tables left out (they hold no GT row
                     on any group, DESIGN_prose.md); headings and paragraphs kept in order, a
                     paragraph over MAX_UNIT characters cut at '; ' / '. ' / ' • ' into passages
  abbrev   (gemma)   the abbreviations the paper defines ('BL = body length'), each checked
                     printed; given to the reader with every passage that uses one
  read     (gemma)   per passage: the organisms it names, and every fact it states as
                     who / has what / with what value (+ sex): who as the passage names it, or
                     empty when the passage goes on about the organism above without naming it.
                     Code keeps a name or value only when it is printed in the passage; a who
                     not printed there is taken as unnamed (gemma fills in the heading's species).
  walk     (nimble)  the paper read in order, holding whose account the text is in. At each
                     heading, and at each passage that names an organism, nimble is asked:
                     v3: with an account open, asked only at a break: a heading, or a paragraph whose
                     bold opening holds a name ('**Alucita fako ... sp. nov.**'); a plain paragraph that
                     names another organism (synonymy line, caption, comparison) stays in the account.
                       Q-SAME   does the account of S go on through this part? Another name of S
                                (synonym, older combination, citation, name in another language),
                                a compared species, its host or food, or a figure caption inside the
                                account keep S. v3: asked in both orders; S ends only on two sure 'no'
                       Q-RANK   (v3) once per name: the scientific name of one species or
                                subspecies, or a genus / family / group / common name? Only a sure
                                species opens an account (Xia2022's Chinese name, 'Alucitidae',
                                'many-plumed moths' and genus names opened accounts in v1)
                       Q-START  after S ends, or with no account open: which species named here
                                does the text from here on describe (two at a time), and that one
                                against 'none' (the study, several organisms, a key couplet, a
                                figure caption); not sure opens no account
                     A passage that names no organism and is not a heading stays in the account.
  v7 (speed by asking less; it must also run on the local PC, one request at a time): the time follows
           how much gemma writes, not the number of calls (v6: Xia2022 27 calls instead of 46, only 22%
           faster). Order: abbrev shape nm heads walk field read7 names places facts assemble.
             nm     (gemma) only the names each passage gives (short answers), captions left out
             walk   (nimble) the species tracking, now before any fact is read
             field  (nimble) Q-FIELD per text passage inside an account: measurements, or anything else
             read7  (gemma) facts read only inside accounts (v5 dropped the rest), one question per kind:
                    measurements, descriptions / other text, list items (copied out first); answers as
                    [who, sex, what, value] with who empty for the account's species; re-reads only on
                    evidence (T1 unused numbers in a measurement passage, T2 a text passage with no fact,
                    T3 list items with no fact), each logged with what it recovered
  v6 (speed): shape runs before the reading, which leaves out captions (they give no facts) and list
           passages (read only item by item in the items stage, their names taken from the items);
           gemma requests go out GEMMA_PARALLEL at a time (in order, the same answers); a re-read's
           new facts are tagged, and assembly also writes prose_no_reread/ to measure what they add.
           Stage order: abbrev shape read items names heads walk places facts assemble.
  shape    (nimble)  v4, per paragraph: Q-CAPTION (a figure / table caption gives no facts: v3 read
                     'aedeagus = 17–20' from 'Figures 15–20 ... 17–20 aedeagus'), then Q-LIST (running
                     description, or a list of separate items: records, localities, sites, hosts)
  items    (gemma)   v4: a list passage's items copied out as printed (each checked printed) and read
                     8 at a time, their facts replacing the passage's (v3 read 10 of the 33 altitude
                     records of L. consentanea). Any other passage with at least 3 printed numbers, 30%
                     of them in none of its facts, is read again in two halves (cut at the '; ' / '. '
                     nearest its middle) and the new facts added. No section name or separator is
                     written into code: the model says what is a list and where its items are.
  heads    (gemma)   v4: a heading the reading left without names is asked on its own (Xu2024's
                     'Lilioceris consentanea (Lacordaire, 1845)' had none, so its account opened
                     late and 18 altitude records were dropped); the walk then runs on these names
  places   (gemma)   v5: the places the paper describes outside the species accounts (study sites in
                     Materials and methods: name, habitat, altitude, coordinates), each checked printed
           (nimble)  v5, in facts: Q-PLACE, does a passage in an account give records of S from a
                     described place it names? A sure yes adds the place's characteristics to S once
                     per mention (one per record), except what the record itself gives (its altitude).
                     Ustjuzhanin2024's GT 'habitat type' comes from these site descriptions.
                     Before joining: Q-SITE per place (one described site, or a country / province /
                     mountain / museum: only a sure site joins) and Q-ENV per place fact (the
                     conditions there, or which species live there, records, history: only sure
                     conditions are carried). Without them the first run joined 'Mount Cameroon hosts
                     ...' (211 rows), provinces and 'China'.
                     v5: Q-TRAIT is asked on the name written out with the paper's abbreviations
                     ('hl/hw' alone was 'not a characteristic'; 21 HL/HW rows were dropped)
  facts    (nimble)  Q-OWNER  a fact whose who names another organism than the account's:
                                whose is it (both orders; not sure drops it)
                     Q-TRAIT  per 'has what' of the paper, with three of its values: a
                                characteristic of the organism, or something about the
                                specimens' handling, people, dates, names or literature
                                (only a sure 'characteristic' is kept)
  names    (gemma)   v2: each name part split into the trait and how it was measured ('length of
                     head along the midline' -> 'length of head' + method 'along the midline'),
                     kept when both are printed in the name and nimble (Q-METHOD, in facts) says the
                     split-off words tell how it was measured, not which body part it is ('in the
                     aedeagus' stays in the name)
           (nimble)  v2, in facts: Q-LABEL per bold label a paragraph starts with ('**Elytra**'): a
                     part of the body, or a section / sex / statement
  assemble (code)    one row per kept fact: species = the owner, type = has what (a defined
                     abbreviation written out with the paper's meaning; v2: the method split off,
                     and a body-part label put in front: 'Humeri' under **Elytra** -> 'Elytra
                     humeri'), value as printed (a trailing unit moved to measurementUnit), sex as
                     read; v2: plus one row per body-part field, type = the label, value = its
                     whole text (the level the GT uses: 'Elytra morphology' = the paragraph)
  score              the production scorer on prose rows only and on v18's rows + prose rows
  page     (gemma)   the scorer's matching (species and trait-name remaps) saved for the page

The models never run together: gemma stages first, then nimble, then the scorer.

    python prose_reader.py <stage> dev|<paper ...>      stages: abbrev read names shape items heads walk places facts assemble score page all
"""
import collections
import contextlib
import csv
import io
import json
import os
import re
import sys
import time
import urllib.request as _rq
from pathlib import Path

import _paths
sys.path.insert(1, str(Path(__file__).resolve().parent.parent / "v18"))
import decoder as v1                 # noqa: E402  (GEMMA, NIMBLE, unload, _printed)
import duels                         # noqa: E402

# The v7 line, one change at a time (PROSE_VARIANT; each in output/prose_<variant>):
#   v7a  the reading's answers as named fields ({what, value} + sex / who only when stated) with one
#        worked example per prompt, instead of [who, sex, what, value] by position
#   v7b  + descriptions copied in full (the whole clause with its qualifiers) and sex always answered
#        ("" when not stated: v7a's optional sex was left out of every Xu2024 / Ustjuzhanin2024 record)
#   v7c  + a list's items cut from their start words (gemma gives each item's first six words, code cuts
#        in order) instead of gemma copying every item out
#   v7d  + a malformed answer (a fact without what / value, a passage id missing) asked again once with
#        a format reminder, kept apart from the evidence re-reads T1-T3
VARIANTS = {"v7a": (), "v7b": ("clauses", "sex"), "v7c": ("clauses", "sex", "pointers"),
            "v7d": ("clauses", "sex", "pointers", "retry"),
            "v8": ("clauses", "sex", "pointers", "retry", "sent"),
            "v8b": ("clauses", "sex", "pointers", "retry", "drop", "symbols"),
            "v8c": ("clauses", "sex", "pointers", "retry", "drop", "symbols", "clean"),
            "v8d": ("clauses", "sex", "pointers", "retry", "drop", "symbols", "clean", "units"),
            "t1": ("clauses", "sex", "pointers", "retry", "drop", "symbols", "clean", "units", "tree")}
#   t1   the information tree (prose_tree.py): species -> phrases -> nodes; v8d's tracking, sort and decisions.
#        Stages: prose_tree.py treeread, names, facts, prose_tree.py treefinal, assemble
#   v8d  v8c + the printed check sets a trailing unit aside: the prompt asks for the value 'with its unit', and when a
#        paper prints the unit away from the number gemma adds it, so a right number failed the check (v8c's test on
#        held_b lost 564 facts this way, 0 on dev). The number must be printed; the unit goes to its own field, only
#        when printed in the same text. Stages: units (the saved dropped facts, no reading again) names facts assemble
#   v8c  v8b's reading + cleanup in the fact stage only: a trait that is a species name is no row; facts from a
#        comparison sentence asked Q-COMP; Q-SITE and Q-ENV in both orders; a place's coordinates no row;
#        '350 m a.s.l.' split into value and unit. Stages: facts assemble
#   v8b  v7d + only what worked in v8: passages read without the sentences nimble dropped (output/prose_sent), sex
#        from an item's ♂ / ♀ (code); + a record's locality and coordinates on its rows, not rows of their own.
#        Stages after the v7a reuse: heads read7 names facts assemble
#   v8   + nimble sorts the sentences first (sentence_test.py, output/prose_sent): gemma reads only kept sentences
#        in runs, a question per kind (read8); nimble checks each text fact against its source (Q-FACT);
#        sex from an item's ♂ / ♀; rows keep their source in measurementRemarks. Order after the v7a reuse:
#        heads read8 names facts assemble
VARIANT = os.environ.get("PROSE_VARIANT", "v7a")
FL = set(VARIANTS[VARIANT])
PREV_OUT = _paths.OUTPUT / ("prose_v7" if VARIANT == "v7a" else "prose_v8b" if VARIANT == "v8c"
                            else "prose_v8c" if VARIANT == "v8d" else "prose_v8d" if VARIANT == "t1" else "prose_v7a")
OUT = _paths.OUTPUT / f"prose_{VARIANT}"
REUSED = ("abbrev", "shape", "read", "walk", "field", "places")   # v7's names, tracking, Q-FIELD and v7a's places
if VARIANT in ("v8c", "v8d"):
    REUSED += ("read2", "names")                       # v8b's reading and name splits: only the decisions change
# v7 (speed by asking less): names first, species tracking before the reading, facts read only inside
# accounts with a focused question and a short answer, re-reads only on evidence (prose_v7)
V18 = _paths.OUTPUT / "full_run_v18"
SET = _paths.SUB / "output" / "eval_split" / "prose_set.json"
MAX_UNIT = 1500            # characters per passage
READ_CHARS = 1500          # passage text per gemma read call
ABBREV_CHARS = 4000        # text per gemma abbreviation call
STATE_CHARS = (1200, 700, 350)   # passage text shown to nimble, fullest to smallest
CSV_FIELDS = ["basisOfRecord", "verbatimIdentification", "measurementType", "measurementMethod",
              "measurementValue", "measurementUnit", "measurementStatistic", "measurementRemarks",
              "sex", "lifeStage", "caste", "sampleSizeValue", "sampleSizeUnit", "sampleTreatment",
              "samplingProtocol", "verbatimLocality", "verbatimCoordinates", "verbatimEventDate",
              "associatedOccurrences", "associatedReferences", "externalLink"]


# === cut (code) ===============================================================================

REF_H = re.compile(r"^(references?( cited)?|literature( cited)?|bibliography|works cited|cited literature)\b", re.I)
BACK_H = re.compile(r"^(acknowledge?ments?|funding|author('s|s')? contributions?|contributions|competing interests?|"
                    r"conflicts? of interest|declaration|ethic|data availability|availability of data|"
                    r"author orcids?|orcid|additional information|consent|disclosure|open access|"
                    r"publisher'?s note|supplementary information|electronic supplementary)", re.I)
CITE = re.compile(r"(\(\d{4}[a-z]?\)|\b\d{4}[a-z]?\.)")
CITE2 = re.compile(r"(doi|https?://|\b\d+\s*[:(]\s*\d+|\d+\s*[–-]\s*\d+)", re.I)


def _ref_like(t):
    return len(t) < 700 and bool(CITE.search(t)) and bool(CITE2.search(t)) and \
        bool(re.match(r"^[A-ZÀ-Ž][\w'’-]+,?\s+([A-Z]\.|[A-Z][a-z]+)", t))


def _split_long(t):
    out = []
    while len(t) > MAX_UNIT:
        cut = max(t.rfind(s, 0, MAX_UNIT) for s in ("; ", ". ", " • "))
        cut = cut + 1 if cut > MAX_UNIT // 3 else MAX_UNIT
        out.append(t[:cut].strip())
        t = t[cut:].strip()
    return out + ([t] if t else [])


def passages(paper):
    """[{"id", "kind": heading|para, "text", "heading"}] in the paper's order, after the cut."""
    raw = (_paths.PAPERS / paper / f"{paper}_full.md").read_text(encoding="utf-8", errors="ignore")
    raw = re.sub(r"<table.*?</table>", "\n\n@@TABLE@@\n\n", raw, flags=re.S)
    lines = raw.split("\n")
    count = collections.Counter(l.strip() for l in lines if l.strip())
    blocks, para = [], []

    def flush():
        if para:
            blocks.append(("para", " ".join(para)))
            para.clear()

    for l in lines:
        s = l.strip()
        if not s:
            flush()
        elif s.startswith("#"):
            flush()
            blocks.append(("heading", s.lstrip("#").strip()))
        elif s == "@@TABLE@@" or s.startswith("|") or s.startswith("<!--") or s.startswith("![") \
                or re.fullmatch(r"\d{1,4}", s) or (count[s] >= 3 and len(s) < 150):
            flush()                       # tables, page markers, images, page numbers, running heads
        else:
            para.append(s)
    flush()
    out, zone, heading = [], "keep", ""
    for b, (kind, t) in enumerate(blocks):
        if kind == "heading":
            hh = re.sub(r"[*_\d.\s]+", " ", t).strip()
            zone = "refs" if REF_H.match(hh) else "back" if BACK_H.match(hh) else "keep"
            if zone == "keep":
                heading = t
                out.append({"id": f"P{len(out)}", "kind": "heading", "text": t, "heading": t, "block": b, "label": ""})
            continue
        if zone != "keep" or _ref_like(t):
            continue
        lab, rest = label_of(t)
        for k, piece in enumerate(_split_long(t)):
            out.append({"id": f"P{len(out)}", "kind": "para", "text": piece, "heading": heading, "block": b,
                        "label": lab, "field": rest, "first": k == 0})
    return out


FIGS = re.compile(r"^\s*[(\[]\s*(?:figs?\.?|figures?|pl\.?|plates?)\b[^)\]]*[)\]]\s*[.:]?\s*", re.I)


def label_of(t):
    """(label, text after it) of a paragraph that starts with a bold label ('**Elytra** (Figs 11, 30B).
    Humeri protruding, ...' -> ('Elytra', 'Humeri protruding, ...')); ('', t) when it has none. The label
    ends at its first '.' or ':' ('**Measurements. Male:**' -> 'Measurements'). Geometry only."""
    m = re.match(r"\s*\*\*(.+?)\*\*\s*", t)
    if not m:
        return "", t
    lab = re.split(r"[.:]", m.group(1))[0].strip(" *")
    rest = FIGS.sub("", t[m.end():]).strip()
    return lab[:60], rest


# === gemma =====================================================================================

GEN = collections.Counter()           # gemma calls, tokens and seconds, printed per stage (v7a)


def gemma(prompt, schema, timeout=900):
    body = {"model": v1.GEMMA, "stream": False, "format": schema, "think": False,
            "messages": [{"role": "user", "content": prompt}],
            "options": {"temperature": 0, "num_ctx": 16384, "num_predict": 6000}}
    for attempt in range(3):
        try:
            req = _rq.Request("http://127.0.0.1:11434/api/chat", data=json.dumps(body).encode(),
                              headers={"Content-Type": "application/json"})
            with _rq.urlopen(req, timeout=timeout) as r:
                resp = json.loads(r.read())
            msg = resp.get("message", {}).get("content", "")
            GEN["calls"] += 1                              # v7a: what gemma is asked and writes, per stage
            GEN["output tokens"] += resp.get("eval_count", 0)
            GEN["input tokens"] += resp.get("prompt_eval_count", 0)
            GEN["generating s"] += resp.get("eval_duration", 0) / 1e9
            GEN["total s"] += resp.get("total_duration", 0) / 1e9
            got = json.loads(msg)
            return got if isinstance(got, dict) else {}
        except json.JSONDecodeError:
            return {}
        except Exception:
            if attempt == 2:
                raise
            time.sleep(10 * (attempt + 1))


GEMMA_PARALLEL = int(os.environ.get("GEMMA_PARALLEL", "1"))   # v6: requests sent to the one gemma at once


def gemma_many(prompts, schema):
    """gemma on independent prompts, answers in the prompts' order. With GEMMA_PARALLEL > 1 they are sent
    together to the same model (Ollama serves them in parallel only when OLLAMA_NUM_PARALLEL allows it;
    otherwise it queues them and nothing changes)."""
    if GEMMA_PARALLEL <= 1 or len(prompts) < 2:
        return [gemma(q, schema) for q in prompts]
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(GEMMA_PARALLEL) as ex:
        return list(ex.map(lambda q: gemma(q, schema), prompts))


def printed(phrase, text):
    """The phrase's words printed in this order, anything but letters / digits between them."""
    return bool(v1._printed(str(phrase or ""), text))


ABBREV = """Below is part of a scientific paper about organisms. List every ABBREVIATION the text defines: a short form the paper says stands for a longer term, such as "BL = body length", "HW (head width)", "abbreviations used: FL, forebody length". Copy both exactly as printed. Only abbreviations the text itself defines; none for units (mm), statistics (SD) or institutions' names unless defined here.

Text:
{text}

Reply with JSON only."""
ABBREV_SCHEMA = {"type": "object", "required": ["abbreviations"], "properties": {"abbreviations": {
    "type": "array", "items": {"type": "object", "required": ["abbreviation", "meaning"],
                               "properties": {"abbreviation": {"type": "string"}, "meaning": {"type": "string"}}}}}}


def stage_abbrev(papers):
    d = OUT / "abbrev"
    d.mkdir(parents=True, exist_ok=True)
    for p in papers:
        f = d / f"{p}.json"
        if f.exists():
            continue
        t0 = time.time()
        ps = [u for u in passages(p) if u["kind"] == "para"]
        chunks, cur = [], ""
        for u in ps:
            if cur and len(cur) + len(u["text"]) > ABBREV_CHARS:
                chunks.append(cur)
                cur = ""
            cur += u["text"] + "\n\n"
        chunks += [cur] if cur else []
        kept, dropped = {}, []
        for ch, got in zip(chunks, gemma_many([ABBREV.format(text=c) for c in chunks], ABBREV_SCHEMA)):
            for e in got.get("abbreviations", []):
                a, m = " ".join(str(e.get("abbreviation") or "").split()), " ".join(str(e.get("meaning") or "").split())
                if a and m and re.search(r"(?<!\w)" + re.escape(a) + r"(?!\w)", ch) and printed(m, ch) \
                        and a.lower() != m.lower():
                    kept.setdefault(a, m)
                else:
                    dropped.append({"abbreviation": a, "meaning": m})
        f.write_text(json.dumps({"abbreviations": kept, "dropped": dropped, "calls": len(chunks)},
                                indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  [abbrev] {p:20s} {len(kept)} abbreviations from {len(chunks)} calls ({time.time() - t0:.0f}s)", flush=True)


READ = """Below are numbered passages of a scientific paper about organisms, in the paper's order. {where}
{abbrevs}
For EACH passage give:
- names: the scientific names of organisms the passage names, copied as printed, without author and year (for example "Lilioceris yuae", "L. latissima").
- facts: every characteristic of an organism the passage states, each as
    who:   the organism the fact belongs to, as the passage names it; "" when the passage does not name it because it goes on describing the organism of the text before it
    sex:   "male" or "female" when the passage says the fact is of males or of females (♂ male, ♀ female), else ""
    what:  what the organism has: the body part, structure or property (size, length, colour, shape, altitude, distribution, habitat, host plant, ...), in the paper's words; an abbreviation written out with the meaning the paper gives
    value: what the passage says about it, COPIED EXACTLY as printed (a number or range with its unit, or the words that describe it)
    unit:  the unit printed with a number ("mm", "m"), else ""
  A passage that describes several parts gives one fact per part. A list of specimens or records gives each record's facts separately.
  Only characteristics of organisms: not who collected or identified specimens, dates, where specimens are kept, figure numbers, or the name's origin.

Passages:
{passages}

Reply with JSON only."""
READ_SCHEMA = {"type": "object", "required": ["passages"], "properties": {"passages": {"type": "array", "items": {
    "type": "object", "required": ["id", "names", "facts"],
    "properties": {"id": {"type": "string"}, "names": {"type": "array", "items": {"type": "string"}},
                   "facts": {"type": "array", "items": {
                       "type": "object", "required": ["who", "sex", "what", "value", "unit"],
                       "properties": {k: {"type": "string"} for k in ("who", "sex", "what", "value", "unit")}}}}}}}}


def stage_read(papers):
    d = OUT / "read"
    d.mkdir(parents=True, exist_ok=True)
    for p in papers:
        f = d / f"{p}.json"
        if f.exists():
            continue
        t0 = time.time()
        abbr = json.loads((OUT / "abbrev" / f"{p}.json").read_text(encoding="utf-8"))["abbreviations"]
        ps = passages(p)
        sf = OUT / "shape" / f"{p}.json"                   # v6: shape decided first; a caption gives no facts
        shape = json.loads(sf.read_text(encoding="utf-8"))["shape"] if sf.exists() else {}   # and a list is
        todo = [u for u in ps if shape.get(u["id"]) not in ("caption", "list")]               # read item by item
        groups, cur = [], []
        for u in todo:
            if cur and sum(len(x["text"]) for x in cur) + len(u["text"]) > READ_CHARS:
                groups.append(cur)
                cur = []
            cur.append(u)
        groups += [cur] if cur else []
        res, prompts = {}, []
        for g in groups:
            text = "\n\n".join(f"[{u['id']}] " + ("(heading) " if u["kind"] == "heading" else "") + u["text"] for u in g)
            used = {a: m for a, m in abbr.items() if re.search(r"(?<!\w)" + re.escape(a) + r"(?!\w)", text)}
            where = f"They follow the heading '{g[0]['heading'][:120]}'." if g[0]["kind"] == "para" and g[0]["heading"] else ""
            ab = ("The paper defines these abbreviations: " + "; ".join(f"{a} = {m}" for a, m in used.items()) + ".\n") if used else ""
            prompts.append(READ.format(where=where, abbrevs=ab, passages=text))
        for g, out in zip(groups, gemma_many(prompts, READ_SCHEMA)):
            got = out.get("passages", [])
            by_id = {u["id"]: u for u in g}
            for x in got:
                u = by_id.get(str(x.get("id") or "").strip("[] "))
                if not u:
                    continue
                r = res.setdefault(u["id"], {"names": [], "facts": [], "dropped": []})
                for n in x.get("names") or []:
                    n = " ".join(str(n).split())
                    if n and printed(n, u["text"]) and n not in r["names"]:
                        r["names"].append(n)
                for fa in x.get("facts") or []:
                    fa = {k: " ".join(str(fa.get(k) or "").split()) for k in ("who", "sex", "what", "value", "unit")}
                    if not fa["what"] or not fa["value"]:
                        continue
                    if not printed(fa["value"], u["text"]):
                        r["dropped"].append(dict(fa, why="value not printed in the passage"))
                    elif fa["who"] and not printed(fa["who"], u["text"]):
                        r["dropped"].append(dict(fa, why="who not printed in the passage"))
                    else:
                        r["facts"].append(fa)
        f.write_text(json.dumps({"passages": ps, "read": res, "calls": len(groups)}, indent=1, ensure_ascii=False),
                     encoding="utf-8")
        nf = sum(len(r["facts"]) for r in res.values())
        nd = sum(len(r["dropped"]) for r in res.values())
        print(f"  [read] {p:20s} {len(ps)} passages, {len(groups)} calls: {nf} facts kept, {nd} dropped "
              f"({time.time() - t0:.0f}s)", flush=True)
    v1.unload(v1.GEMMA)


# === nimble ====================================================================================

STATE_IN = "A scientific paper about organisms is read part by part, in order. The text read so far ended inside the account of {s}: there the paper describes {s}."
STATE_OUT = "A scientific paper about organisms is read part by part, in order. The text read so far is not the account of one organism."
STATE_PART = " The next part of the text{under} reads:\n\"\"\"{text}\"\"\""
Q_SAME = "Does the account of {s} go on through this part of the text?"
SAME = {"yes": "yes: this part still belongs to the account of {s}, even where it names other organisms: another name "
               "of {s} (a synonym, an older combination, a citation of where {s} was named or described, its name in "
               "another language), an organism compared with {s}, its host, food or partner, or a figure caption "
               "printed inside the account",
        "no": "no: the account of {s} ends here: the account of another species starts (usually under its own heading "
              "or a bold name, often with 'sp. nov.'), or the text turns to several organisms together, a key to "
              "identify species, or the study itself (its methods, results or discussion)"}
Q_RANK = "What is '{n}'?"
RANK = {"yes": "the scientific (Latin) name of one species or subspecies, written as a genus and an epithet "
               "(possibly abbreviated, as in 'T. acerosus')",
        "no": "something else: a genus, family or larger group, a common or vernacular name, a name in another "
              "language, or not an organism"}
Q_START = "Which organism does the text from this part on describe?"
START = "{n}: from here on the text describes {n} (its specimens, body, measurements, distribution)"
NONE = ("none: no single organism's account starts here; the text is about the study, several organisms together, "
        "a key couplet that leads to a species, or a figure caption, or it names {n} only in passing")
Q_OWNER = "Whose characteristic does the text give as '{what}: {value}'?"
OWNER = "{n}'s: the text says this about {n}"
Q_LABEL = "What does the label '{label}' name?"
LABEL = {"part": "a part of the organism's body: the structures described in the paragraph belong to it "
                 "(for example 'Elytra', 'Head', 'Male genitalia', 'Pronotum', 'Leg')",
         "other": "something else: a section of the description (diagnosis, description, measurements, material "
                  "examined, type material, distribution, habitat, remarks, etymology), a sex, or a statement"}
Q_METHOD = "In the name '{n}', what does '{m}' say?"
METHOD = {"how": "how, where or under which condition the measurement of '{t}' was taken (for example "
                 "'along the midline', 'at the widest point', 'of the holotype', 'in dorsal view')",
          "part": "which part of the body '{t}' is or sits on, so it belongs to the characteristic's name "
                  "(for example 'in the aedeagus', 'on the fore wing', 'of the elytra')"}
STATE_PASSAGE = "A passage of a scientific paper about organisms{under} reads:\n\"\"\"{text}\"\"\""
Q_CAPTION = "What is this passage of the paper?"
CAPTION = {"caption": "a caption of a figure or a table: it says what the figure or table shows (figure numbers, "
                      "views, scale bars)",
           "text": "text of the paper: a description, a list of material or records, a key, a discussion, or any "
                   "other running text"}
Q_LIST = "How is this passage written?"
LISTED = {"list": "as a list of separate items one after another, each with its own values: specimens or records "
                  "(place, altitude, date, collector), localities, sites, host plants or other entries",
          "prose": "as running description or discussion: sentences about characteristics, not a list of entries"}
Q_PLACE = "Does this passage give records of {s} from the place '{n}' that the paper describes?"
PLACE = {"yes": "yes: specimens or observations of {s} come from '{n}' (the passage names it as where they were found)",
         "no": "no: '{n}' is named here for something else, or it is another place with a similar name"}
Q_SITE = "What is '{n}' in this paper?"
SITE = {"site": "one collecting or observation site the paper describes: a camp, station, plot, trail or locality "
                "with its own habitat, altitude or coordinates",
        "area": "something larger or different: a country, province, region, island or mountain as a whole, a "
                "museum or collection, or a place the paper only names"}
Q_ENV = "What does '{what}: {value}' say about the place '{n}'?"
ENV = {"env": "the conditions at the place: its habitat, vegetation, forest type, altitude, coordinates or climate",
       "other": "something else: which organisms live or were found there, records, history, its size or "
                "importance, or where it lies within a larger area"}
Q_TRAIT = "What does '{what}' tell about an organism?"
TRAIT = {"trait": "a characteristic of the organism: its body, size, measurements, colour, structures or genitalia, "
                  "its life, behaviour, habitat, food or hosts, its distribution, or the places or altitudes where it lives or was found",
         "other": "something else: who collected or identified the specimens, collection dates, where specimens are kept "
                  "or their labels, the name or its origin, a figure, a publication, or a statistical result"}


def _state(intro, u, nxt=None):
    """state_at(size) for DecisionClient: the passage (a heading with the start of the text after it)."""
    def at(size):
        n = STATE_CHARS[size]
        if u["kind"] == "heading":
            text = f"(heading) {u['text']}" + (f"\n{nxt['text'][:n]}" if nxt else "")
        else:                            # v3: a bold-name line is shown with what follows, as a heading is
            text = u["text"][:n] + (f"\n{nxt['text'][:n // 2]}" if nxt and len(u["text"]) < 300 else "")
        under = f", under the heading '{u['heading'][:100]}'," if u["kind"] == "para" and u["heading"] else ""
        return intro + STATE_PART.format(under=under, text=text)
    return at


class Ask:
    """nimble with a size-aware state (a state over the model's limit is shown shorter)."""

    def __init__(self):
        self.n = duels.Nimble()

    def __call__(self, state_at, question, crit):
        a = self.n.get().ask(state_at if callable(state_at) else (lambda size: state_at),
                             {"q": {"type": "choice", "instructions": question, "criteria": crit}}).get("q") or {}
        probs = {k: round(float(v or 0), 3) for k, v in (a.get("probabilities") or {}).items()}
        return a.get("choice"), probs

    def unload(self):
        self.n.unload()


def _key(name):
    w = re.findall(r"[a-z]+", str(name or "").lower())
    return (w[0][0], w[1]) if len(w) >= 2 else (w[0][:1], w[0]) if w else None


def same_name(a, b):
    """'Lilioceris latissima' = 'L. latissima' (genus initial + epithet); a name check, nothing judged."""
    ka, kb = _key(a), _key(b)
    return bool(ka and kb and ka == kb)


def pick_start(ask, state_at, names):
    """Q-START: the names two at a time, the one left against 'none'. -> (name | None, log)"""
    names = list(dict.fromkeys(names))
    if not names:
        return None, []
    log = []
    if len(names) > 1:
        i, l = duels.duel(lambda st, q, c: ask(state_at, q, c), None, Q_START,
                          [(n, START.format(n=n)) for n in names])
        log += l
        if i is None:
            return None, log
        names = [names[i]]
    n = names[0]
    picks = []
    for a, b in (("a", "b"), ("b", "a")):            # both orders
        crit = {a: START.format(n=n), b: NONE.format(n=n)}
        ch, pr = ask(state_at, Q_START, crit)
        log.append({"a": crit["a"][:60], "b": crit["b"][:60], "choice": ch, "probs": pr})
        picks.append(duels.sure(ch, pr, a, b) == a)
    return (n if all(picks) else None), log


def stage_walk(papers):
    d = OUT / "walk"
    d.mkdir(parents=True, exist_ok=True)
    ask = Ask()
    for p in papers:
        f = d / f"{p}.json"
        if f.exists():
            continue
        t0 = time.time()
        rd = load_read(p)                                  # v4: with the heading names added (heads)
        ps, read = rd["passages"], rd["read"]
        cur, span, log, rank = None, {}, [], {}

        def species(n):
            """Q-RANK, once per name of the paper: only a species or subspecies name opens an account."""
            if n not in rank:
                ch, pr = ask(f"A scientific paper about organisms names '{n}'.", Q_RANK.format(n=n), dict(RANK))
                rank[n] = {"choice": ch, "probs": pr, "species": duels.sure(ch, pr, "yes") == "yes"}
            return rank[n]["species"]

        for i, u in enumerate(ps):
            nxt = ps[i + 1] if i + 1 < len(ps) else None
            names = list(read.get(u["id"], {}).get("names", []))
            if u["kind"] == "heading" and nxt and not names:        # v3: a heading's own names first
                names = list(read.get(nxt["id"], {}).get("names", []))
            bold = re.match(r"\s*\*\*(.+?)\*\*", u["text"]) if u["kind"] == "para" else None
            brk = u["kind"] == "heading" or bool(bold and any(printed(n, bold.group(1)) for n in names))
            # v3: with an account open, only a break (a heading, or a bold opening that holds a name) is
            # asked; a plain paragraph naming another organism (a synonymy line, a caption, a comparison)
            # stays in the account. With none open, any passage naming an organism is asked.
            if (cur and brk) or (not cur and (u["kind"] == "heading" or names)):
                rec = {"id": u["id"], "before": cur, "names": names}
                if cur:
                    st = _state(STATE_IN.format(s=cur), u, nxt)
                    sames = []
                    for a, b in (("yes", "no"), ("no", "yes")):          # both orders; ends only on two sure 'no'
                        crit = {"a": SAME[a].format(s=cur), "b": SAME[b].format(s=cur)}
                        ch, pr = ask(st, Q_SAME.format(s=cur), crit)
                        sames.append([{"a": a, "b": b}.get(ch), pr])
                    rec["same"] = sames
                    if all(x == "no" and max(pr.values() or [0]) >= duels.SURE for x, pr in sames):
                        cands = [n for n in names if not same_name(n, cur) and species(n)]
                        new, l = pick_start(ask, _state(STATE_OUT, u, nxt), cands)
                        cur, rec["start"] = new, l
                else:
                    new, l = pick_start(ask, _state(STATE_OUT, u, nxt), [n for n in names if species(n)])
                    cur, rec["start"] = new, l
                rec["after"] = cur
                log.append(rec)
            span[u["id"]] = cur
        f.write_text(json.dumps({"span": span, "log": log, "rank": rank}, indent=1, ensure_ascii=False), encoding="utf-8")
        accounts = [x["after"] for x in log if x["after"] != x["before"] and x["after"]]
        print(f"  [walk] {p:20s} {len(log)} questions asked, {len(accounts)} accounts opened: "
              f"{', '.join(accounts)[:300]} ({time.time() - t0:.0f}s)", flush=True)
    ask.unload()


def stage_facts(papers):
    d = OUT / "facts"
    d.mkdir(parents=True, exist_ok=True)
    ask = Ask()
    for p in papers:
        f = d / f"{p}.json"
        if f.exists():
            continue
        t0 = time.time()
        rd = load_read(p)
        span = json.loads((OUT / "walk" / f"{p}.json").read_text(encoding="utf-8"))["span"]
        sf = OUT / "shape" / f"{p}.json"
        shape = json.loads(sf.read_text(encoding="utf-8"))["shape"] if sf.exists() else {}
        by_id = {u["id"]: u for u in rd["passages"]}
        facts, owners = [], []
        for pid, fa in read_facts(rd):
            s = span.get(pid)
            x = dict(fa, passage=pid, account=s)
            if shape.get(pid) == "caption":                # v4: a caption describes a figure, not the organism
                x["owner"], x["why"] = None, "figure or table caption"
            elif not fa["who"] or (s and same_name(fa["who"], s)):
                x["owner"] = s
                x["why"] = "no account" if not s else ""
            elif not s:
                x["owner"], x["why"] = None, "names another organism, outside any account"
            else:
                u = by_id[pid]
                st = (f"This part of a scientific paper is in the account of {s}:\n\"\"\"{u['text'][:1200]}\"\"\"")
                picks = []
                for a, b in (("a", "b"), ("b", "a")):
                    crit = {a: OWNER.format(n=s), b: OWNER.format(n=fa["who"])}
                    ch, pr = ask(st, Q_OWNER.format(what=fa["what"], value=fa["value"][:150]), crit)
                    picks.append(s if duels.sure(ch, pr, a) else fa["who"] if duels.sure(ch, pr, b) else None)
                    owners.append({"passage": pid, "fact": fa, "choice": ch, "probs": pr})
                x["owner"] = picks[0] if picks[0] and picks[0] == picks[1] else None
                x["why"] = "" if x["owner"] else "owner not sure"
            facts.append(x)
        abbr = json.loads((OUT / "abbrev" / f"{p}.json").read_text(encoding="utf-8"))["abbreviations"]
        pf = OUT / "places" / f"{p}.json"
        places = json.loads(pf.read_text(encoding="utf-8"))["places"] if pf.exists() else {}
        joins, sites = [], {}                              # v5: Q-PLACE, records joined to described places

        def twice(st, q, crit, yes):
            """v8c: a yes only when sure in both orders (one order before; a lean to the first option decided
            'Mount Cameroon is one site' and 'presence: of diverse habitats ... is a condition there')."""
            ch, pr = ask(st, q, crit)
            if duels.sure(ch, pr, yes) != yes:
                return False, ch, pr
            if "clean" not in FL:
                return True, ch, pr
            flip = {k: crit[k] for k in reversed(list(crit))}
            ch2, pr2 = ask(st, q, flip)
            return duels.sure(ch2, pr2, yes) == yes, ch2, pr2

        if "clean" in FL:                                  # v8c: a place named inside another's description is the
            for name in list(places):                      # larger area, not a site ('Bamboo Camp: Mount Cameroon (SW slope)')
                if any(o != name and printed(name, " ".join(x["value"] for x in v)) for o, v in places.items()):
                    sites[name] = {"site": False, "why": "named inside another place's description", "env": {}}
            for name, v in sites.items():
                places.pop(name, None)
        for name, pfacts in list(places.items()):          # Q-SITE per place, Q-ENV per place fact
            desc = "; ".join(f"{x['what']}: {x['value']}" for x in pfacts)[:500]
            st = f"A scientific paper about organisms describes the place '{name}': {desc}."
            ok, ch, pr = twice(st, Q_SITE.format(n=name), dict(SITE), "site")
            sites[name] = {"choice": ch, "probs": pr, "site": ok, "env": {}}
            if not sites[name]["site"]:
                places.pop(name)
                continue
            keep = []
            for x in pfacts:
                if "clean" in FL and x["what"].strip().lower().replace("_", " ") in RECORD_LOC | RECORD_COORD:
                    continue                               # v8c: a place's own coordinates are no row of the organism
                ok, ch, pr = twice(st, Q_ENV.format(what=x["what"], value=x["value"][:150], n=name), dict(ENV), "env")
                sites[name]["env"][f"{x['what']}: {x['value'][:60]}"] = [ch, pr]
                if ok:
                    keep.append(x)
            places[name] = keep
        places = {k: v for k, v in places.items() if v}
        for u in rd["passages"]:
            s = span.get(u["id"])
            if u["kind"] != "para" or not s or shape.get(u["id"]) == "caption":
                continue
            own = {x["what"].lower() for x in facts if x["passage"] == u["id"]}
            for name, pfacts in places.items():
                k = len(re.findall(r"(?<![\w])" + re.escape(name) + r"(?![\w])", u["text"]))
                if not k:
                    continue
                desc = "; ".join(f"{f['what']}: {f['value']}" for f in pfacts)[:400]
                st = (f"In the account of {s}, a passage of a scientific paper reads:\n\"\"\"{u['text'][:1000]}\"\"\"\n"
                      f"Elsewhere the paper describes the place '{name}': {desc}.")
                ch, pr = ask(st, Q_PLACE.format(s=s, n=name), {k2: v.format(s=s, n=name) for k2, v in PLACE.items()})
                ok = duels.sure(ch, pr, "yes") == "yes"
                joins.append({"passage": u["id"], "place": name, "mentions": k, "choice": ch, "probs": pr, "join": ok})
                if not ok:
                    continue
                for _ in range(k):                         # one set per mention: one per record
                    for pfa in pfacts:
                        if pfa["what"].lower() in own:     # the record's own value (its altitude) wins
                            continue
                        facts.append({"who": "", "sex": "", "what": pfa["what"], "value": pfa["value"], "unit": "",
                                      "passage": u["id"], "account": s, "owner": s, "why": "", "place": name,
                                      "record": True})
        whats = collections.defaultdict(list)
        for x in facts:
            if x["owner"]:
                whats[x["what"].lower()].append(x["value"])
        trait = {}
        for w, vals in whats.items():
            ex = "; ".join(f"'{v[:100]}'" for v in list(dict.fromkeys(vals))[:3])
            wn = spelled(w, {a.lower(): m for a, m in abbr.items()})   # v5: 'hl/hw' asked as the paper's words
            st = f"A scientific paper describing organisms gives '{wn}' for them, for example: {ex}."
            ch, pr = ask(st, Q_TRAIT.format(what=wn), dict(TRAIT))
            trait[w] = {"choice": ch, "probs": pr, "keep": duels.sure(ch, pr, "trait") == "trait"}
        for x in facts:
            if x["owner"] and not trait.get(x["what"].lower(), {}).get("keep"):
                x["why"] = "not a characteristic (Q-TRAIT)"
        factq = collections.Counter()                      # v8: Q-FACT, each text fact against its source
        if "clean" in FL:
            # v8c: a 'trait' that is a species name is no trait ('Thoracostrongylus miyakei = also has ...'); code,
            # against the names Q-RANK called species
            rank = json.loads((OUT / "walk" / f"{p}.json").read_text(encoding="utf-8")).get("rank", {})
            spk = {_key(n) for n, v in rank.items() if v.get("species")}
            for x in facts:
                if x["owner"] and not x["why"] and _key(x["what"]) in spk and len(x["what"].split()) == 2:
                    x["why"] = "the trait is a species name"
                    factq["species-name traits"] += 1
            # v8c: Q-COMP, facts from a sentence nimble called a comparison: only sure in both orders drops
            sort = json.loads((_paths.OUTPUT / "prose_sent" / f"{p}.json").read_text(encoding="utf-8"))["units"]
            comp = collections.defaultdict(list)
            for r in sort:
                if r["kept"] and r.get("cat") == "comparison":
                    comp[r["passage"]].append(r["text"])
            for x in facts:
                if not x["owner"] or x["why"] or x.get("place"):
                    continue
                src = next((t for t in comp.get(x["passage"], []) if printed(x["value"], t)), None)
                if not src:
                    continue
                st = f"A scientific paper says about {x['owner']}: '{x['what']}: {x['value'][:200]}'."   # the fact alone:
                crit = dict(COMP)                          # with its comparison sentence, real traits read as comparisons
                factq["comparison facts asked"] += 1
                ok, _ch, _pr = twice(st, Q_FACT.format(what=x["what"], value=x["value"][:150]), crit, "compare")
                if ok:
                    x["why"] = "only a comparison (Q-COMP)"
                    factq["comparison facts dropped"] += 1
        if "sent" in FL:
            for x in facts:
                if not x["owner"] or x["why"] or not x.get("src") or not re.search(r"[A-Za-z]{3}", x["value"]):
                    continue                               # a number is not asked; only sure twice drops
                st = f"In the account of {x['owner']}, a scientific paper says:\n\"\"\"{x['src']}\"\"\""
                q = Q_FACT.format(what=x["what"], value=x["value"][:150])
                crit = {k: v.format(s=x["owner"]) for k, v in FACT.items()}
                ch, pr = ask(st, q, crit)
                factq["asked"] += 1
                if duels.sure(ch, pr, "other") == "other":
                    ch2, pr2 = ask(st, q, {"b": crit["other"], "a": crit["trait"]})
                    if duels.sure(ch2, pr2, "b") == "b":
                        x["why"] = "not a characteristic (Q-FACT)"
                        factq["dropped"] += 1
        labels = {}                                        # v2: Q-LABEL once per label of the paper
        with_facts = {x["passage"] for x in facts}
        for u in passages(p):
            lab = u.get("label") or (lead_of(u) if u["id"] in with_facts else "")   # v4: a lead word too
            if u["kind"] != "para" or not lab or lab in labels:
                continue
            how = "starts with the label" if u.get("label") else "starts with the word"
            st = (f"In a paper that describes species, a paragraph {how} '{lab}' and reads:\n"
                  f"\"\"\"{u['text'][:500]}\"\"\"")
            ch, pr = ask(st, Q_LABEL.format(label=lab), dict(LABEL))
            labels[lab] = {"choice": ch, "probs": pr, "part": duels.sure(ch, pr, "part") == "part"}
            if labels[lab]["part"] and not u.get("label"):  # v4: a lead word asked again, options swapped
                crit = {"a": LABEL["other"], "b": LABEL["part"]}
                ch2, pr2 = ask(st, Q_LABEL.format(label=lab), crit)
                labels[lab].update(swapped=[ch2, pr2], part=duels.sure(ch2, pr2, "b") == "b")
        methods = {}                                       # v2: Q-METHOD per split gemma proposed
        split = json.loads((OUT / "names" / f"{p}.json").read_text(encoding="utf-8"))["split"]
        for n, sp in split.items():
            st = f"A scientific paper names a characteristic of an organism '{n}'."
            crit = {k: v.format(m=sp["method"], t=sp["trait"]) for k, v in METHOD.items()}
            ch, pr = ask(st, Q_METHOD.format(m=sp["method"], n=n), crit)
            methods[n] = {"choice": ch, "probs": pr, "keep": duels.sure(ch, pr, "how") == "how"}
        f.write_text(json.dumps({"facts": facts, "owners": owners, "trait": trait, "labels": labels,
                                 "methods": methods, "joins": joins, "sites": sites, "q_fact": factq},
                                indent=1, ensure_ascii=False),
                     encoding="utf-8")
        kept = sum(1 for x in facts if x["owner"] and not x["why"])
        print(f"  [facts] {p:20s} {len(facts)} facts, {len(owners) // 2} owner questions, {len(trait)} names asked: "
              f"{kept} kept; labels naming a body part: {[k for k, v in labels.items() if v['part']]} "
              f"({time.time() - t0:.0f}s)", flush=True)
    ask.unload()


def read_facts(rd):
    """(passage id, fact) for every fact the read kept. gemma often writes the account's species as who
    although the passage does not name it (Ustjuzhanin2024: 346 of 624 facts): such a fact is unnamed,
    so it is the account's."""
    for pid, r in rd["read"].items():
        unnamed = [dict({k: v for k, v in x.items() if k != "why"}, who="", who_read=x["who"])
                   for x in r["dropped"] if x["why"] == "who not printed in the passage"]
        for fa in r["facts"] + unnamed:
            yield pid, fa


def load_read(p):
    """v4's reading (list items, re-reads) when there is one, else the passage reading."""
    f = OUT / "read2" / f"{p}.json"
    return json.loads((f if f.exists() else OUT / "read" / f"{p}.json").read_text(encoding="utf-8"))


def stage_shape(papers):
    """v4 (nimble), per paragraph: Q-CAPTION (a figure / table caption gives no facts), then Q-LIST (a list of
    separate items is read item by item in the items stage)."""
    d = OUT / "shape"
    d.mkdir(parents=True, exist_ok=True)
    ask = Ask()
    for p in papers:
        f = d / f"{p}.json"
        if f.exists():
            continue
        t0 = time.time()
        shape, log = {}, {}
        for u in passages(p):                              # v6: before the reading, so it can skip captions
            if u["kind"] != "para":
                continue
            under = f", under the heading '{u['heading'][:100]}'," if u["heading"] else ""
            st = lambda size, u=u, under=under: STATE_PASSAGE.format(under=under, text=u["text"][:STATE_CHARS[size]])
            ch, pr = ask(st, Q_CAPTION, dict(CAPTION))
            log[u["id"]] = {"caption": [ch, pr]}
            if duels.sure(ch, pr, "caption") == "caption":
                shape[u["id"]] = "caption"
                continue
            ch, pr = ask(st, Q_LIST, dict(LISTED))
            log[u["id"]]["list"] = [ch, pr]
            shape[u["id"]] = "list" if duels.sure(ch, pr, "list") == "list" else "text"
        f.write_text(json.dumps({"shape": shape, "log": log}, indent=1, ensure_ascii=False), encoding="utf-8")
        c = collections.Counter(shape.values())
        print(f"  [shape] {p:20s} {dict(c)} ({time.time() - t0:.0f}s)", flush=True)
    ask.unload()


ITEMS = """The passage below, from a scientific paper about organisms, lists separate items one after another (for example specimens or records, localities, sites, host plants). Copy out EACH item exactly as printed, in order, one entry per item. Leave none out, do not merge items, do not change any character.

Passage:
{text}

Reply with JSON only."""
ITEMS_SCHEMA = {"type": "object", "required": ["items"], "properties": {"items": {"type": "array", "items": {"type": "string"}}}}
ITEMS_PER_CALL = 8
NUMS = re.compile(r"\d+(?:[.,]\d+)?(?:\s*[–—-]\s*\d+(?:[.,]\d+)?)?")
_num = lambda s: re.sub(r"\s+", "", re.sub(r"[–—]", "-", s))


def read_units(units, abbr, where):
    """gemma READ on [(id, text)] -> {id: {"names", "facts", "dropped"}}, each name / value checked printed
    in its own unit's text (as stage_read does)."""
    text = "\n\n".join(f"[{i}] {t}" for i, t in units)
    used = {a: m for a, m in abbr.items() if re.search(r"(?<!\w)" + re.escape(a) + r"(?!\w)", text)}
    ab = ("The paper defines these abbreviations: " + "; ".join(f"{a} = {m}" for a, m in used.items()) + ".\n") if used else ""
    got = gemma(READ.format(where=where, abbrevs=ab, passages=text), READ_SCHEMA).get("passages", [])
    by_id, res = dict(units), {}
    for x in got:
        i = str(x.get("id") or "").strip("[] ")
        if i not in by_id:
            continue
        r = res.setdefault(i, {"names": [], "facts": [], "dropped": []})
        for n in x.get("names") or []:
            n = " ".join(str(n).split())
            if n and printed(n, by_id[i]) and n not in r["names"]:
                r["names"].append(n)
        for fa in x.get("facts") or []:
            fa = {k: " ".join(str(fa.get(k) or "").split()) for k in ("who", "sex", "what", "value", "unit")}
            if not fa["what"] or not fa["value"]:
                continue
            if not printed(fa["value"], by_id[i]):
                r["dropped"].append(dict(fa, why="value not printed in the passage"))
            elif fa["who"] and not printed(fa["who"], by_id[i]):
                r["dropped"].append(dict(fa, why="who not printed in the passage"))
            else:
                r["facts"].append(fa)
    return res


def _halves(t):
    """A passage cut in two at the '; ' or '. ' nearest its middle (geometry only)."""
    mid = len(t) // 2
    cuts = [m.end() for m in re.finditer(r"[;.]\s", t)]
    if not cuts:
        return [t]
    c = min(cuts, key=lambda x: abs(x - mid))
    return [x for x in (t[:c].strip(), t[c:].strip()) if x]


def stage_items(papers):
    """v4 (gemma). A list passage (Q-LIST): gemma copies out its items (each checked printed), then reads
    them ITEMS_PER_CALL at a time; their facts replace the passage's. Any other passage whose printed
    numbers mostly appear in none of its facts (at least 3 and 30% unused) is read again in two halves;
    new facts are added. -> OUT/read2/<paper>.json, the read file with these changes."""
    d = OUT / "read2"
    d.mkdir(parents=True, exist_ok=True)
    for p in papers:
        f = d / f"{p}.json"
        if f.exists():
            continue
        t0 = time.time()
        rd = json.loads((OUT / "read" / f"{p}.json").read_text(encoding="utf-8"))
        shape = json.loads((OUT / "shape" / f"{p}.json").read_text(encoding="utf-8"))["shape"]
        abbr = json.loads((OUT / "abbrev" / f"{p}.json").read_text(encoding="utf-8"))["abbreviations"]
        read, log = rd["read"], {}
        n_items = n_reread = n_added = 0

        def work(u):
            """One passage's gemma work -> (new read entry or None, log entry or None); shared state only read."""
            pid, kind = u["id"], shape.get(u["id"])
            where = f"They follow the heading '{u['heading'][:120]}'." if u["heading"] else ""
            if kind == "list":
                items = [" ".join(str(x).split()) for x in gemma(ITEMS.format(text=u["text"]), ITEMS_SCHEMA).get("items", [])]
                items = [x for x in dict.fromkeys(items) if x and printed(x, u["text"])]
                if len(items) < 2:                          # v6: lists are not in the passage reading, so
                    r = read_units([(pid, u["text"])], abbr, where).get(pid)   # read it whole here
                    return (r or {"names": [], "facts": [], "dropped": []}), {"items": len(items), "kept": "passage reading"}
                new = {"names": [], "facts": [], "dropped": []}
                for k in range(0, len(items), ITEMS_PER_CALL):
                    units = [(f"{pid}#{k + j}", t) for j, t in enumerate(items[k:k + ITEMS_PER_CALL])]
                    for r in read_units(units, abbr, where + " They are items of one list in the paper.").values():
                        new["names"] += [n for n in r["names"] if n not in new["names"]]
                        new["facts"] += r["facts"]
                        new["dropped"] += r["dropped"]
                return new, {"items": len(items), "facts_after": len(new["facts"])}
            if kind != "text" or pid not in read:
                return None, None
            nums = [_num(x) for x in NUMS.findall(u["text"])]
            vals = " | ".join(_num(fa["value"]) for fa in read[pid]["facts"] + read[pid]["dropped"])
            unused = [x for x in nums if x not in vals]
            if len(unused) < 3 or len(unused) < 0.3 * len(nums):
                return None, None
            have = {(fa["what"].lower(), fa["value"]) for fa in read[pid]["facts"] + read[pid]["dropped"]}
            new = {"names": list(read[pid]["names"]), "facts": list(read[pid]["facts"]), "dropped": list(read[pid]["dropped"])}
            added = 0
            for r in read_units([(f"{pid}h{j}", t) for j, t in enumerate(_halves(u["text"]))], abbr, where).values():
                for fa in r["facts"] + [x for x in r["dropped"] if x["why"] == "who not printed in the passage"]:
                    if (fa["what"].lower(), fa["value"]) not in have:
                        have.add((fa["what"].lower(), fa["value"]))
                        (new["facts"] if fa in r["facts"] else new["dropped"]).append(dict(fa, reread=True))
                        added += 1                          # v6: tagged, so what re-reads recover can be measured
            return new, {"reread": True, "unused_numbers": len(unused), "of": len(nums), "added": added}

        todo = [u for u in rd["passages"] if shape.get(u["id"]) in ("list", "text")]
        if GEMMA_PARALLEL > 1:
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(GEMMA_PARALLEL) as ex:
                done = list(ex.map(work, todo))
        else:
            done = [work(u) for u in todo]
        for u, (new, lg) in zip(todo, done):              # applied in the passages' order
            if new is not None:
                read[u["id"]] = new
            if lg:
                log[u["id"]] = lg
                n_items += lg.get("items", 0) if "facts_after" in lg else 0
                if lg.get("reread"):
                    n_reread += 1
                    n_added += lg["added"]
        f.write_text(json.dumps({"passages": rd["passages"], "read": read, "log": log}, indent=1, ensure_ascii=False),
                     encoding="utf-8")
        print(f"  [items] {p:20s} {sum(1 for v in shape.values() if v == 'list')} list passages, {n_items} items; "
              f"{n_reread} passages read again, {n_added} facts added ({time.time() - t0:.0f}s)", flush=True)
    v1.unload(v1.GEMMA)


HEADS = """Below is a heading from a scientific paper about organisms. List the scientific names of organisms it names, copied as printed, without author and year (for example "Lilioceris consentanea"). An empty list when it names none.

Heading: {text}

Reply with JSON only."""
HEADS_SCHEMA = {"type": "object", "required": ["names"], "properties": {"names": {"type": "array", "items": {"type": "string"}}}}


def stage_heads(papers):
    """v4 (gemma): a heading the reading left without names asked on its own (Xu2024 'Lilioceris
    consentanea (Lacordaire, 1845)' came back with none, so its account opened late and its records
    were dropped); each name checked printed. Updates OUT/read2."""
    d = OUT / "read2"
    d.mkdir(parents=True, exist_ok=True)
    for p in papers:
        rd = load_read(p)
        if rd.get("heads_done"):
            continue
        t0, added = time.time(), {}
        for u in rd["passages"]:
            if u["kind"] != "heading" or rd["read"].get(u["id"], {}).get("names"):
                continue
            names = [" ".join(str(n).split()) for n in gemma(HEADS.format(text=u["text"]), HEADS_SCHEMA).get("names", [])]
            names = [n for n in dict.fromkeys(names) if n and printed(n, u["text"])]
            if names:
                rd["read"].setdefault(u["id"], {"names": [], "facts": [], "dropped": []})["names"] = names
                added[u["id"]] = names
        rd["heads_done"], rd["heads"] = True, added
        (d / f"{p}.json").write_text(json.dumps(rd, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  [heads] {p:20s} {len(added)} headings given names: {list(added.values())[:8]} "
              f"({time.time() - t0:.0f}s)", flush=True)
    v1.unload(v1.GEMMA)


PLACES = """Below are passages of a scientific paper about organisms. List each PLACE (a site, station, locality or area where organisms were collected or observed) that the passages DESCRIBE, with what they say about it:
- place: its name, copied exactly as printed (the short name the paper uses for it, e.g. "Bamboo Camp")
- facts: each thing the passages give for that place, as what / value, the value COPIED exactly (habitat or vegetation, altitude, coordinates, ...)
Only places the passages describe; not a place that is merely named.

Passages:
{text}

Reply with JSON only."""
PLACES_SCHEMA = {"type": "object", "required": ["places"], "properties": {"places": {"type": "array", "items": {
    "type": "object", "required": ["place", "facts"],
    "properties": {"place": {"type": "string"}, "facts": {"type": "array", "items": {
        "type": "object", "required": ["what", "value"],
        "properties": {"what": {"type": "string"}, "value": {"type": "string"}}}}}}}}}
PLACES_CHARS = 3000


def stage_places(papers):
    """v5 (gemma): the places the paper describes outside the species accounts (Ustjuzhanin2024's
    Materials and methods: '- Bamboo Camp. Bamboo Camp (350 m a.s.l.), ...; a lowland rainforest with
    historical disturbances ...'), each name and value checked printed. The records inside the accounts
    name the place only; Q-PLACE (facts) joins them."""
    d = OUT / "places"
    d.mkdir(parents=True, exist_ok=True)
    for p in papers:
        f = d / f"{p}.json"
        if f.exists():
            continue
        t0 = time.time()
        rd = load_read(p)
        span = json.loads((OUT / "walk" / f"{p}.json").read_text(encoding="utf-8"))["span"]
        sf = OUT / "shape" / f"{p}.json"
        shape = json.loads(sf.read_text(encoding="utf-8"))["shape"] if sf.exists() else {}
        outside = [u for u in rd["passages"] if u["kind"] == "para" and not span.get(u["id"])
                   and shape.get(u["id"]) != "caption"]
        chunks, cur = [], ""
        for u in outside:
            if cur and len(cur) + len(u["text"]) > PLACES_CHARS:
                chunks.append(cur)
                cur = ""
            cur += u["text"] + "\n\n"
        chunks += [cur] if cur else []
        places = {}
        for ch in chunks:
            for e in gemma(PLACES.format(text=ch), PLACES_SCHEMA).get("places", []):
                name = " ".join(str(e.get("place") or "").split())
                if len(name) < 3 or not re.search(r"(?<![\w])" + re.escape(name) + r"(?![\w])", ch):
                    continue
                for fa in e.get("facts") or []:
                    w, v = (" ".join(str(fa.get(k) or "").split()) for k in ("what", "value"))
                    if w and v and printed(v, ch) and {"what": w, "value": v} not in places.setdefault(name, []):
                        places[name].append({"what": w, "value": v})
        places = {k: v for k, v in places.items() if v}
        f.write_text(json.dumps({"places": places, "calls": len(chunks)}, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  [places] {p:20s} {len(places)} places described: {list(places)[:10]} ({time.time() - t0:.0f}s)", flush=True)
    v1.unload(v1.GEMMA)


# === v7: names first, species tracking before the reading, focused short reading =================

NAMES_ONLY = """Below are numbered passages of a scientific paper about organisms. For EACH passage list the scientific names of organisms it names, copied as printed, without author and year (for example "Lilioceris yuae", "L. latissima"). An empty list when it names none.

Passages:
{passages}

Reply with JSON only."""
NAMES_ONLY_SCHEMA = {"type": "object", "required": ["passages"], "properties": {"passages": {"type": "array", "items": {
    "type": "object", "required": ["id", "names"],
    "properties": {"id": {"type": "string"}, "names": {"type": "array", "items": {"type": "string"}}}}}}}
NAMES_CHARS = 4000


def stage_nm(papers):
    """v7 (gemma): only which organisms each passage names (short answers), so the species tracking can run
    before any fact is read. Captions are left out (they never open or keep an account).
    -> OUT/read/<paper>.json with names and no facts."""
    d = OUT / "read"
    d.mkdir(parents=True, exist_ok=True)
    for p in papers:
        f = d / f"{p}.json"
        if f.exists():
            continue
        t0 = time.time()
        ps = passages(p)
        shape = json.loads((OUT / "shape" / f"{p}.json").read_text(encoding="utf-8"))["shape"]
        todo = [u for u in ps if shape.get(u["id"]) != "caption"]
        groups, cur = [], []
        for u in todo:
            if cur and sum(len(x["text"]) for x in cur) + len(u["text"]) > NAMES_CHARS:
                groups.append(cur)
                cur = []
            cur.append(u)
        groups += [cur] if cur else []
        prompts = [NAMES_ONLY.format(passages="\n\n".join(
            f"[{u['id']}] " + ("(heading) " if u["kind"] == "heading" else "") + u["text"] for u in g)) for g in groups]
        res = {}
        for g, out in zip(groups, gemma_many(prompts, NAMES_ONLY_SCHEMA)):
            by_id = {u["id"]: u for u in g}
            for x in out.get("passages", []):
                u = by_id.get(str(x.get("id") or "").strip("[] "))
                if not u:
                    continue
                names = [n for n in dict.fromkeys(" ".join(str(n).split()) for n in x.get("names") or [])
                         if n and printed(n, u["text"])]
                res[u["id"]] = {"names": names, "facts": [], "dropped": []}
        f.write_text(json.dumps({"passages": ps, "read": res, "calls": len(groups)}, indent=1, ensure_ascii=False),
                     encoding="utf-8")
        print(f"  [nm] {p:20s} {len(todo)} passages, {len(groups)} calls: "
              f"{sum(1 for r in res.values() if r['names'])} name organisms ({time.time() - t0:.0f}s)", flush=True)
    v1.unload(v1.GEMMA)


Q_FIELD = "What does this passage give?"
FIELD = {"measure": "measurements: labels or abbreviations, each with a number or a range (for example 'BL: 7.8–8.6 mm, "
                    "HW: 1.72 mm', 'wingspan 14 mm')",
         "other": "anything else: a description of the body or its parts in words, distribution, habitat, hosts, "
                  "biology, a diagnosis or remarks"}


def stage_field(papers):
    """v7 (nimble), per running-text passage inside an account: Q-FIELD, a measurement list or anything else;
    it picks which reading question gemma gets (not sure: the description question)."""
    d = OUT / "field"
    d.mkdir(parents=True, exist_ok=True)
    ask = Ask()
    for p in papers:
        f = d / f"{p}.json"
        if f.exists():
            continue
        t0 = time.time()
        rd = load_read(p)
        span = json.loads((OUT / "walk" / f"{p}.json").read_text(encoding="utf-8"))["span"]
        shape = json.loads((OUT / "shape" / f"{p}.json").read_text(encoding="utf-8"))["shape"]
        field, log = {}, {}
        for u in rd["passages"]:
            if u["kind"] != "para" or not span.get(u["id"]) or shape.get(u["id"]) != "text":
                continue
            under = f", under the heading '{u['heading'][:100]}'," if u["heading"] else ""
            st = lambda size, u=u, under=under: STATE_PASSAGE.format(under=under, text=u["text"][:STATE_CHARS[size]])
            ch, pr = ask(st, Q_FIELD, dict(FIELD))
            log[u["id"]] = [ch, pr]
            field[u["id"]] = "measure" if duels.sure(ch, pr, "measure") == "measure" else "other"
        f.write_text(json.dumps({"field": field, "log": log}, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  [field] {p:20s} {dict(collections.Counter(field.values()))} ({time.time() - t0:.0f}s)", flush=True)
    ask.unload()


READ7_HEAD = """Below are numbered {what} from the account of {s} in a scientific paper{where}.
{abbrevs}"""
WHO7 = """Give each fact as an object with named fields:
- "what" and "value": always
- "sex": "male" or "female" only when the text says it is of males or of females (for example 'Male:', '♂', '♀'); leave it out otherwise
- "who": leave it out when it is {s}'s; the organism's name, as printed, only when the text says it of another organism"""
MEASURE7 = READ7_HEAD + """They give measurements. For EACH passage list every measurement.
""" + WHO7 + """
- what: the label or abbreviation, as printed
- value: the number or range COPIED exactly, with its unit
Example: a passage "[P1] Male: TL 5.2–5.9 mm, WL 3.1 mm. Female: TL 6.0 mm" gives
{{"id": "P1", "facts": [{{"sex": "male", "what": "TL", "value": "5.2–5.9 mm"}}, {{"sex": "male", "what": "WL", "value": "3.1 mm"}}, {{"sex": "female", "what": "TL", "value": "6.0 mm"}}]}}

Passages:
{passages}

Reply with JSON only."""
DESCRIBE7 = READ7_HEAD + """For EACH passage list every characteristic it states.
""" + WHO7 + """
- what: the part or property described, as the text names it (a body part or structure, colour, size, distribution, habitat, host plant, ...)
- value: what the text says about it, COPIED exactly
One entry per part or property. Only characteristics of organisms: not who collected specimens, dates, where specimens are kept, figure numbers, or the name's origin.
Example: a passage "[P1] Pronotum black, shining; legs yellow. Unlike X. other, the tibiae are spined" gives
{{"id": "P1", "facts": [{{"what": "pronotum", "value": "black, shining"}}, {{"what": "legs", "value": "yellow"}}, {{"what": "tibiae", "value": "spined"}}]}}

Passages:
{passages}

Reply with JSON only."""
ITEM7 = READ7_HEAD + """Each item is one record or entry of a list. For EACH item list what it gives.
""" + WHO7 + """
- what: what the item gives (altitude, locality, habitat, host plant, ...)
- value: COPIED exactly
Not who collected or identified specimens, dates, specimen numbers or where specimens are kept.
Example: an item "[P1#0] 2♂, 1♀, Mount Kora, forest edge, 1200 m, 12.V.2015, J. Smith leg." gives
{{"id": "P1#0", "facts": [{{"sex": "male", "what": "altitude", "value": "1200 m"}}, {{"what": "locality", "value": "Mount Kora"}}, {{"what": "habitat", "value": "forest edge"}}]}}

Items:
{passages}

Reply with JSON only."""
READ7_SCHEMA = {"type": "object", "required": ["passages"], "properties": {"passages": {"type": "array", "items": {
    "type": "object", "required": ["id", "facts"],
    "properties": {"id": {"type": "string"}, "facts": {"type": "array", "items": {   # v7a: named keys
        "type": "object", "required": ["what", "value"],
        "properties": {k: {"type": "string"} for k in ("what", "value", "sex", "who")}}}}}}}}


def tpl7(t):
    """The v7a prompt with this variant's changes (v7b: sex always answered, descriptions in full)."""
    if "sex" in FL:
        t = (t.replace('"sex": "male" or "female" only when', '"sex": "male" or "female" when')
              .replace("; leave it out otherwise", ', "" when it does not say (always give it)')
              .replace('{{"what": "', '{{"sex": "", "what": "'))
    if "clauses" in FL:
        t = t.replace("- value: what the text says about it, COPIED exactly\n",
                      "- value: what the text says about it, COPIED exactly and in full: the whole clause with its "
                      "qualifiers, not a shortened part\n")
    return t


def schema7():
    if "sex" not in FL:
        return READ7_SCHEMA
    s = json.loads(json.dumps(READ7_SCHEMA))
    s["properties"]["passages"]["items"]["properties"]["facts"]["items"]["required"] = ["what", "value", "sex"]
    return s


RETRY_NOTE = ("\nYour previous answer to this was not valid. Give every passage or item id listed, and every fact "
              "as an object with \"what\" and \"value\".")


UNIT_END = re.compile(r"^(.*\d[^A-Za-z]*?)\s*(mm|cm|µm|μm|um|m|km|g|mg|kg|ml|°c)\.?$", re.I)


def number_and_unit(value, text):
    """v8d, geometry only: a value ending in a unit whose number is printed in this text -> (number, unit), the unit
    only when it is printed in the same text too ('5.2–5.9 mm' where the paper prints 'in mm: TL 5.2–5.9'). Else None."""
    m = UNIT_END.match(value.strip())
    if not m or not printed(m.group(1), text):
        return None
    return m.group(1).strip(), m.group(2) if printed(m.group(2), text) else ""


def stage_units(papers):
    """v8d (no model): the saved reading's facts dropped as 'value not printed', asked the new check against the text
    gemma read (kept sentences, or the list passage). A paper with rescued facts has its name splits asked again,
    since their names were not there. Updates OUT/read2."""
    for p in papers:
        f = OUT / "read2" / f"{p}.json"
        rd = json.loads(f.read_text(encoding="utf-8"))
        if rd.get("units_done"):
            continue
        by_id = {u["id"]: u for u in rd["passages"]}
        kept = collections.defaultdict(list)
        for r in json.loads((_paths.OUTPUT / "prose_sent" / f"{p}.json").read_text(encoding="utf-8"))["units"]:
            if r.get("cat") != "record list" and r["kept"]:
                kept[r["passage"]].append(r["text"])
        n = 0
        for pid, r in rd["read"].items():
            text = " ".join(kept[pid]) if kept.get(pid) else by_id[pid]["text"]
            left = []
            for x in r["dropped"]:
                apart = number_and_unit(x["value"], text) if x.get("why") == "value not printed in the passage" else None
                if not apart:
                    left.append(x)
                    continue
                n += 1
                fa = {k: v for k, v in x.items() if k != "why"}
                fa.update(value=apart[0], unit=apart[1], unit_rescued=True)
                if fa["who"] and not printed(fa["who"], text):
                    left.append(dict(fa, why="who not printed in the passage"))
                else:
                    r["facts"].append(fa)
            r["dropped"] = left
        rd["units_done"] = True
        f.write_text(json.dumps(rd, indent=1, ensure_ascii=False), encoding="utf-8")
        if n:
            (OUT / "names" / f"{p}.json").unlink(missing_ok=True)
        print(f"  [units] {p:20s} {n} facts rescued", flush=True)


def read7(prompt_tpl, units, s, abbr, where, what="passages"):
    """gemma on [(id, text)] with named fields per fact -> {id: (facts, dropped)}; values and names checked
    printed in their own unit (as stage_read does), the unit split off later. v7d: units whose answer was
    malformed or missing are asked again once with a format reminder (a format failure, not a re-read)."""
    text = "\n\n".join(f"[{i}] {t}" for i, t in units)
    used = {a: m for a, m in abbr.items() if re.search(r"(?<!\w)" + re.escape(a) + r"(?!\w)", text)}
    ab = ("The paper defines these abbreviations: " + "; ".join(f"{a} = {m}" for a, m in used.items()) + ".\n") if used else ""
    by_id = dict(units)

    def parse(got):
        res, bad = {}, set()
        for x in got:
            i = str(x.get("id") or "").strip("[] ")
            if i not in by_id:
                continue
            r = res.setdefault(i, ([], []))
            for row in x.get("facts") or []:
                if not isinstance(row, dict):              # v7a: named keys; anything else is a format failure,
                    GEN["malformed facts"] += 1            # never read by position
                    bad.add(i)
                    continue
                fa = {k: " ".join(str(row.get(k) or "").split()) for k in ("who", "sex", "what", "value")}
                fa["unit"] = ""
                if not fa["what"] or not fa["value"]:
                    GEN["malformed facts"] += 1
                    bad.add(i)
                    continue
                if "units" in FL and not printed(fa["value"], by_id[i]):
                    apart = number_and_unit(fa["value"], by_id[i])
                    if apart:
                        fa["value"], fa["unit"] = apart
                if not printed(fa["value"], by_id[i]):
                    r[1].append(dict(fa, why="value not printed in the passage"))
                elif fa["who"] and not printed(fa["who"], by_id[i]):
                    r[1].append(dict(fa, why="who not printed in the passage"))
                else:
                    r[0].append(fa)
        return res, bad | (set(by_id) - set(res))

    prompt = tpl7(prompt_tpl).format(what=what, s=s, where=where, abbrevs=ab, passages=text)
    res, bad = parse(gemma(prompt, schema7()).get("passages", []))
    if "retry" in FL and bad:                              # v7d: format retry, only the failed units
        GEN["format retries"] += 1
        sub = [(i, t) for i, t in units if i in bad]
        sub_text = "\n\n".join(f"[{i}] {t}" for i, t in sub)
        again, _bad2 = parse(gemma(tpl7(prompt_tpl).format(what=what, s=s, where=where, abbrevs=ab, passages=sub_text)
                                   + RETRY_NOTE, schema7()).get("passages", []))
        for i, r in again.items():
            if r[0] or r[1]:
                GEN["format retry units recovered"] += 1
                res[i] = r
    return {i: res.get(i, ([], [])) for i, _t in units}


STARTS = """The passage below, from a scientific paper about organisms, lists separate items one after another (for example specimens or records, localities, entries). For EACH item give its first six words, copied exactly as printed, in order. Leave none out and do not merge items.

Passage:
{text}

Reply with JSON only."""
STARTS_SCHEMA = {"type": "object", "required": ["starts"], "properties": {"starts": {"type": "array", "items": {"type": "string"}}}}


def list_items(u):
    """A list passage's items -> (items, log). v7c: gemma gives each item's first six words; code finds them
    in order (each searched from the end of the one before, so repeated starts such as '1♂, Lingshui, ...'
    resolve one by one) and cuts the passage there; an item runs to the next item's start. A start not
    found is logged, never matched loosely; fewer than 2 found falls back to gemma copying the items out.
    Earlier variants: gemma copies every item out (as v4)."""
    text, log = u["text"], collections.Counter()

    def copied():
        items = [" ".join(str(x).split()) for x in gemma(ITEMS.format(text=text), ITEMS_SCHEMA).get("items", [])]
        return [x for x in dict.fromkeys(items) if x and printed(x, text)]

    if "pointers" not in FL:
        return copied(), log
    starts = [" ".join(str(x).split()) for x in gemma(STARTS.format(text=text), STARTS_SCHEMA).get("starts", [])]
    pos, cuts = 0, []
    for a in starts:
        words = re.findall(r"[^\W_]+", a)
        log["starts"] += 1
        if not words:
            log["empty starts"] += 1
            continue
        m = re.compile(r"[\W_]+".join(map(re.escape, words)), re.I).search(text, pos)
        if not m:
            log["starts not found"] += 1
            continue
        cuts.append(m.start())
        pos = m.end()
    if len(cuts) < 2:
        log["fell back to copying"] += 1
        return copied(), log
    log["intro characters"] += cuts[0]
    items = [text[a:b].strip(" ;,•\n") for a, b in zip(cuts, cuts[1:] + [len(text)])]
    return [x for x in items if x], log


RECORD_LOC = {"locality", "location"}                  # names the model gives a record's place fields (v8b)
RECORD_COORD = {"coordinates", "latitude", "longitude"}


def stage_read7(papers):
    """v7 (gemma): facts read only from passages inside an account (the walk ran first; v5 dropped every fact
    outside an account anyway), with the question the passage type calls for: measurements (Q-FIELD),
    descriptions and other text, or a list's items (copied out first, as in v4). Re-reads only on evidence,
    each logged with what it recovered:
      T1  a measurement passage with 2+ printed numbers in none of its facts: read again alone
      T2  a running-text passage of 200+ characters that gave no fact: read again alone
      T3  list items that gave no fact: read again, those items only
    -> OUT/read2/<paper>.json (names from the names-first stage and heads, facts from here)."""
    d = OUT / "read2"
    d.mkdir(parents=True, exist_ok=True)
    for p in papers:
        rd = load_read(p)
        if rd.get("read7_done"):
            continue
        t0 = time.time()
        abbr = json.loads((OUT / "abbrev" / f"{p}.json").read_text(encoding="utf-8"))["abbreviations"]
        span = json.loads((OUT / "walk" / f"{p}.json").read_text(encoding="utf-8"))["span"]
        shape = json.loads((OUT / "shape" / f"{p}.json").read_text(encoding="utf-8"))["shape"]
        field = json.loads((OUT / "field" / f"{p}.json").read_text(encoding="utf-8"))["field"]
        read, log = rd["read"], {}
        trig = collections.Counter()
        inside = [u for u in rd["passages"] if u["kind"] == "para" and span.get(u["id"])
                  and shape.get(u["id"]) in ("text", "list")]
        under = lambda u: f", under the heading '{u['heading'][:120]}'" if u["heading"] else ""

        def put(pid, facts, dropped, tag=None):
            r = read.setdefault(pid, {"names": [], "facts": [], "dropped": []})
            have = {(x["what"].lower(), x["value"]) for x in r["facts"] + r["dropped"]}
            n = 0
            for fa, dest in [(x, "facts") for x in facts] + [(x, "dropped") for x in dropped]:
                if tag and (fa["what"].lower(), fa["value"]) in have:
                    continue
                r[dest].append(dict(fa, reread=tag) if tag else fa)
                n += dest == "facts" or fa.get("why") == "who not printed in the passage"
            return n

        texts = [x for x in inside if shape.get(x["id"]) == "text"]
        if "drop" in FL:                                   # v8b: only the sentences nimble kept, read as v7d reads
            kept = collections.defaultdict(list)           # a passage (same questions, 'Male:' stays in place)
            sort = json.loads((_paths.OUTPUT / "prose_sent" / f"{p}.json").read_text(encoding="utf-8"))["units"]
            for r in sort:
                if r.get("cat") != "record list" and r["kept"]:
                    kept[r["passage"]].append(r["text"])
            texts = [dict(x, text=" ".join(kept[x["id"]])) for x in texts if kept.get(x["id"])]
        record_only = []

        def rec(t, res):
            """A list item's facts (v8b, code only): ♂ alone / ♀ alone in the item gives the sex to facts with none,
            a 'sex' fact is no row; what the model named locality or coordinates goes on the item's other facts
            (verbatimLocality, verbatimCoordinates), and an item with nothing else is logged, not a row."""
            if "symbols" not in FL:
                return res
            sx = "male" if "♂" in t and "♀" not in t else "female" if "♀" in t and "♂" not in t else ""
            name = lambda fa: fa["what"].strip().lower().replace("_", " ")
            usable = lambda j, fa: j == 0 or fa.get("why") == "who not printed in the passage"
            loc, coord, out = [], [], ([], [])
            for j in (0, 1):
                for fa in res[j]:
                    if name(fa) == "sex":
                        continue
                    if usable(j, fa) and name(fa) in RECORD_LOC:
                        loc.append(fa["value"])
                    elif usable(j, fa) and name(fa) in RECORD_COORD:
                        coord.append(fa["value"])
                    else:
                        out[j].append(dict(fa, sex=fa["sex"] or sx))
            if not out[0] and not out[1] and (loc or coord):
                record_only.append({"item": t[:200], "locality": loc, "coordinates": coord})
            for j in (0, 1):
                for fa in out[j]:
                    if loc:
                        fa["locality"] = "; ".join(loc)
                    if coord:
                        fa["coordinates"] = ", ".join(coord)
            return out

        groups, cur = [], []                               # running text: same account, same question
        for u in texts:
            k = (span[u["id"]], field.get(u["id"], "other"))
            if cur and (cur[0][1] != k or sum(len(x["text"]) for x, _k in cur) + len(u["text"]) > READ_CHARS):
                groups.append(cur)
                cur = []
            cur.append((u, k))
        groups += [cur] if cur else []
        for g in groups:
            (s, kind) = g[0][1]
            tpl = MEASURE7 if kind == "measure" else DESCRIBE7
            got = read7(tpl, [(u["id"], u["text"]) for u, _k in g], s, abbr, under(g[0][0]))
            for u, _k in g:
                facts, dropped = got[u["id"]]
                put(u["id"], facts, dropped)
                if kind == "measure":                      # T1
                    nums = [_num(x) for x in NUMS.findall(u["text"])]
                    vals = " | ".join(_num(x["value"]) for x in facts + dropped)
                    if sum(1 for x in nums if x not in vals) >= 2:
                        again = read7(tpl, [(u["id"], u["text"])], s, abbr, under(u))[u["id"]]
                        trig["T1 fired"] += 1
                        trig["T1 added"] += put(u["id"], again[0], again[1], "T1")
                elif len(u["text"]) >= 200 and not facts and not dropped:   # T2
                    again = read7(tpl, [(u["id"], u["text"])], s, abbr, under(u))[u["id"]]
                    trig["T2 fired"] += 1
                    trig["T2 added"] += put(u["id"], again[0], again[1], "T2")
        n_items = 0
        for u in (x for x in inside if shape.get(x["id"]) == "list"):
            s, pid = span[u["id"]], u["id"]
            items, plog = list_items(u)                    # v7c: cut from start words, or copied out
            trig.update({f"pointers: {k}": v for k, v in plog.items()})
            if len(items) < 2:
                got = read7(DESCRIBE7, [(pid, u["text"])], s, abbr, under(u))[pid]
                put(pid, *got)
                log[pid] = {"items": len(items), "kept": "passage reading"}
                continue
            empty = []
            for k in range(0, len(items), ITEMS_PER_CALL):
                units = [(f"{pid}#{k + j}", t) for j, t in enumerate(items[k:k + ITEMS_PER_CALL])]
                got = read7(ITEM7, units, s, abbr, under(u), what="items of one list")
                for i, t in units:
                    put(pid, *rec(t, got[i]))
                    if not got[i][0] and not got[i][1]:
                        empty.append((i, t))
            if empty:                                      # T3
                got = read7(ITEM7, empty, s, abbr, under(u), what="items of one list")
                trig["T3 fired"] += len(empty)
                trig["T3 added"] += sum(put(pid, *rec(t, got[i]), "T3") for i, t in empty)
            log[pid] = {"items": len(items)}
            n_items += len(items)
        trig["items with only place fields (no row)"] = len(record_only)
        rd.update(read=read, log=log, triggers=dict(trig), read7_done=True, record_only=record_only)
        (d / f"{p}.json").write_text(json.dumps(rd, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  [read7] {p:20s} {len(inside)} passages inside accounts ({len(groups)} text calls), {n_items} list "
              f"items; re-reads {dict(trig)}; {sum(len(r['facts']) for r in read.values())} facts "
              f"({time.time() - t0:.0f}s)", flush=True)
    v1.unload(v1.GEMMA)


# === v8: nimble sorts the sentences, gemma reads only what is kept, nimble checks each text fact ==

FIELD8 = READ7_HEAD + """They say where the organism occurs, its habitat, or its food or hosts. For EACH passage list every such fact.
""" + WHO7 + """
- what: distribution, habitat, host plant, food or prey, as the text says
- value: what the text says about it, COPIED exactly
Example: a passage "[P1] Known from Kenya and Uganda; in montane forest, on Acacia" gives
{{"id": "P1", "facts": [{{"what": "distribution", "value": "Kenya and Uganda"}}, {{"what": "habitat", "value": "montane forest"}}, {{"what": "host plant", "value": "Acacia"}}]}}

Passages:
{passages}

Reply with JSON only."""
KIND8 = {"measurement": "measure", "distribution": "field", "habitat": "field", "host_food": "field"}
TPL8 = {"measure": MEASURE7, "field": FIELD8, "describe": DESCRIBE7}
COMP = {"own": "a characteristic the organism has, stated by itself: readable without knowing the other species",
        "compare": "only a comparison: that it resembles, is similar to, differs from, or is larger or smaller than "
                   "another species, without saying what it is like"}
Q_FACT = "What does the text say with '{what}: {value}'?"
FACT = {"trait": "something about {s} itself: its body, size, colour, structures, sexes, life, behaviour, food, hosts, "
                 "habitat, or where it lives or was found",
        "other": "something else: a specimen as a record (its label, number, or where it is kept), who collected or "
                 "published it, what the literature says, the species' name or its origin"}


def source_of(value, sents, whole):
    """The sentence a fact's value is printed in, else the whole unit: the row keeps its source."""
    for x in sents:
        if printed(value, x):
            return x[:400]
    return whole[:400]


def stage_read8(papers):
    """v8 (gemma). Sentences nimble kept (sentence_test.py: Q-ABOUT, Q-CAT; output/prose_sent) are read in runs:
    consecutive kept sentences of a passage with the same kind of question stay together, so 'Male:' stays with
    its numbers. measurement -> MEASURE7; distribution, habitat, host_food -> FIELD8; the rest -> DESCRIBE7.
    Lists as v7d, item by item from start words. An item printing only ♂ or only ♀ gives that sex to its facts
    with none (the symbol says it; code only), and a 'sex' fact of an item is no row. Facts keep their source.
    Re-reads: T2 (a run of 200+ characters with no fact), T3 (items with no fact); T1 never fired in v7, dropped."""
    d = OUT / "read2"
    d.mkdir(parents=True, exist_ok=True)
    for p in papers:
        rd = load_read(p)
        if rd.get("read8_done"):
            continue
        t0 = time.time()
        abbr = json.loads((OUT / "abbrev" / f"{p}.json").read_text(encoding="utf-8"))["abbreviations"]
        span = json.loads((OUT / "walk" / f"{p}.json").read_text(encoding="utf-8"))["span"]
        shape = json.loads((OUT / "shape" / f"{p}.json").read_text(encoding="utf-8"))["shape"]
        units = json.loads((_paths.OUTPUT / "prose_sent" / f"{p}.json").read_text(encoding="utf-8"))["units"]
        by_pid = collections.defaultdict(list)
        for r in units:
            by_pid[r["passage"]].append(r)
        read, log, trig = rd["read"], {}, collections.Counter()
        inside = [u for u in rd["passages"] if u["kind"] == "para" and span.get(u["id"])
                  and shape.get(u["id"]) in ("text", "list")]
        under = lambda u: f", under the heading '{u['heading'][:120]}'" if u["heading"] else ""

        def put(pid, facts, dropped, tag=None):
            r = read.setdefault(pid, {"names": [], "facts": [], "dropped": []})
            have = {(x["what"].lower(), x["value"]) for x in r["facts"] + r["dropped"]}
            n = 0
            for fa, dest in [(x, "facts") for x in facts] + [(x, "dropped") for x in dropped]:
                if tag and (fa["what"].lower(), fa["value"]) in have:
                    continue
                r[dest].append(dict(fa, reread=tag) if tag else fa)
                n += dest == "facts" or fa.get("why") == "who not printed in the passage"
            return n

        runs = []                                          # (passage, account, kind, sentences)
        for u in (x for x in inside if shape.get(x["id"]) == "text"):
            cur, kind = [], None
            for r in by_pid.get(u["id"], []):
                k = None if not r["kept"] else KIND8.get(r.get("cat"), "describe")
                if cur and k != kind:
                    runs.append((u, span[u["id"]], kind, cur))
                    cur = []
                if k:
                    cur.append(r["text"])
                kind = k
            if cur:
                runs.append((u, span[u["id"]], kind, cur))
        groups, g = [], []                                 # calls: same account, same question
        for run in runs:
            size = sum(len(" ".join(x[3])) for x in g)
            if g and (g[0][1:3] != run[1:3] or size + len(" ".join(run[3])) > READ_CHARS):
                groups.append(g)
                g = []
            g.append(run)
        groups += [g] if g else []
        nrun = 0
        for g in groups:
            s, kind = g[0][1], g[0][2]
            items = []
            for u, _s, _k, sents in g:
                nrun += 1
                items.append((f"{u['id']}~{nrun}", " ".join(sents), u, sents))
            got = read7(TPL8[kind], [(i, t) for i, t, _u, _x in items], s, abbr, under(g[0][0]))
            for i, t, u, sents in items:
                facts, dropped = got[i]
                src = lambda fa: dict(fa, src=source_of(fa["value"], sents, t))
                put(u["id"], [src(x) for x in facts], [src(x) for x in dropped])
                if len(t) >= 200 and not facts and not dropped:   # T2
                    again = read7(TPL8[kind], [(i, t)], s, abbr, under(u))[i]
                    trig["T2 fired"] += 1
                    trig["T2 added"] += put(u["id"], [src(x) for x in again[0]], [src(x) for x in again[1]], "T2")
        n_items = 0
        for u in (x for x in inside if shape.get(x["id"]) == "list"):
            s, pid = span[u["id"]], u["id"]
            items, plog = list_items(u)
            trig.update({f"pointers: {k}": v for k, v in plog.items()})
            if len(items) < 2:
                got = read7(DESCRIBE7, [(pid, u["text"])], s, abbr, under(u))[pid]
                put(pid, [dict(x, src=u["text"][:400]) for x in got[0]], [dict(x, src=u["text"][:400]) for x in got[1]])
                log[pid] = {"items": len(items), "kept": "passage reading"}
                continue

            def item_facts(i, t, res):
                """Code only: ♂ alone / ♀ alone in the item gives the sex; a 'sex' fact is no row."""
                sx = "male" if "♂" in t and "♀" not in t else "female" if "♀" in t and "♂" not in t else ""
                out = ([], [])
                for j in (0, 1):
                    for fa in res[j]:
                        if fa["what"].strip().lower() != "sex":
                            out[j].append(dict(fa, src=t[:400], sex=fa["sex"] or sx))
                return out

            empty = []
            for k in range(0, len(items), ITEMS_PER_CALL):
                units_ = [(f"{pid}#{k + j}", t) for j, t in enumerate(items[k:k + ITEMS_PER_CALL])]
                got = read7(ITEM7, units_, s, abbr, under(u), what="items of one list")
                for i, t in units_:
                    put(pid, *item_facts(i, t, got[i]))
                    if not got[i][0] and not got[i][1]:
                        empty.append((i, t))
            if empty:                                      # T3
                got = read7(ITEM7, empty, s, abbr, under(u), what="items of one list")
                trig["T3 fired"] += len(empty)
                trig["T3 added"] += sum(put(pid, *item_facts(i, t, got[i]), "T3") for i, t in empty)
            log[pid] = {"items": len(items)}
            n_items += len(items)
        rd.update(read=read, log=log, triggers=dict(trig), read8_done=True)
        (d / f"{p}.json").write_text(json.dumps(rd, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  [read8] {p:20s} {len(runs)} runs in {len(groups)} calls, {n_items} list items; re-reads {dict(trig)}; "
              f"{sum(len(r['facts']) for r in read.values())} facts ({time.time() - t0:.0f}s)", flush=True)
    v1.unload(v1.GEMMA)


def lead_of(u):
    """The first word of a paragraph without a bold label ('Head slightly wider ...' -> 'Head'), offered to
    Q-LABEL as its context; geometry only."""
    if u["kind"] != "para" or u.get("label") or not u.get("first", True):   # a paragraph's start only:
        # Xia2022's split record paragraph went on with 'Peng, Song, Yan & Yu leg.', read as body parts
        return ""
    m = re.match(r"\s*([A-Z][a-z]{2,})\b", u["text"])
    return m.group(1) if m else ""


NAMES = """Each line below is the name a scientific paper gives to a characteristic of an organism. Some names also say HOW, WHERE or UNDER WHICH CONDITION it was measured, for example
  "length of head along the midline"        -> trait "length of head", method "along the midline"
  "width of pronotum at the widest point"   -> trait "width of pronotum", method "at the widest point"
  "wingspan of the holotype"                -> trait "wingspan", method "of the holotype"
For each name give trait and method, both COPIED from the name, no words added. When the name says nothing about how it was measured, method is "" and trait is the whole name.

Names:
{names}

Reply with JSON only."""
NAMES_SCHEMA = {"type": "object", "required": ["names"], "properties": {"names": {"type": "array", "items": {
    "type": "object", "required": ["name", "trait", "method"],
    "properties": {"name": {"type": "string"}, "trait": {"type": "string"}, "method": {"type": "string"}}}}}}


def stage_names(papers):
    """v2 (gemma): each name part ('length of head along the midline') split into the trait and how it was
    measured; kept only when both are printed in the name and the trait is not the whole name."""
    d = OUT / "names"
    d.mkdir(parents=True, exist_ok=True)
    for p in papers:
        f = d / f"{p}.json"
        if f.exists():
            continue
        t0 = time.time()
        rd = load_read(p)                                  # v6: after the items stage (list items' facts)
        abbr = json.loads((OUT / "abbrev" / f"{p}.json").read_text(encoding="utf-8"))["abbreviations"]
        parts = list(dict.fromkeys(x.strip() for _pid, fa in read_facts(rd)
                                   for x in spelled(fa["what"], abbr).split("/") if x.strip()))
        split, calls = {}, 0
        batches = [parts[i:i + 40] for i in range(0, len(parts), 40)]
        for out in gemma_many([NAMES.format(names="\n".join(b)) for b in batches], NAMES_SCHEMA):
            calls += 1
            got = out.get("names", [])
            for e in got:
                n, t, m = (" ".join(str(e.get(k) or "").split()) for k in ("name", "trait", "method"))
                if n in parts and t and m and printed(t, n) and printed(m, n) and t.lower() != n.lower():
                    split[n] = {"trait": t, "method": m}
        f.write_text(json.dumps({"split": split, "asked": len(parts), "calls": calls}, indent=1, ensure_ascii=False),
                     encoding="utf-8")
        print(f"  [names] {p:20s} {len(split)} of {len(parts)} names carry a method: "
              f"{list(split.items())[:4]} ({time.time() - t0:.0f}s)", flush=True)
    v1.unload(v1.GEMMA)


# === assemble, score, page ==========================================================================

RANGE = re.compile(r"^[~<>≈]?\s*\d+(?:[.,]\d+)?\s*[–—-]\s*\d+(?:[.,]\d+)?$")
NUM = re.compile(r"^[~<>≈]?\s*\d+(?:[.,]\d+)?$")


def _row(x):
    v, unit = x["value"], x["unit"]
    if unit and v.endswith(unit) and len(v) > len(unit):
        v = v[: -len(unit)].strip()
    m = re.fullmatch(r"(.*\d)\s*(mm|cm|µm|μm|m)(?:\s*a\.\s*s\.\s*l\.?)?", v) if not unit else None   # v4: '850 m' without a unit
    if m:
        v, unit = m.group(1), m.group(2)
    stat = "range" if RANGE.match(v) else "individual" if NUM.match(v) else ""
    r = {"verbatimIdentification": x["owner"], "measurementType": x["what"], "measurementValue": v,
         "measurementUnit": unit, "measurementStatistic": stat,
         "sex": x["sex"] if x["sex"] in ("male", "female") else ""}
    if x.get("locality"):                                  # v8b: the record's place, on its rows
        r["verbatimLocality"] = x["locality"]
    if x.get("coordinates"):
        r["verbatimCoordinates"] = x["coordinates"]
    return r


def _write(f, rows):
    f.parent.mkdir(parents=True, exist_ok=True)
    with open(f, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def spelled(what, abbr):
    """A has-what that is one of the paper's defined abbreviations, or a ratio of them ('HL/HW'),
    written with the paper's own meanings (gemma often keeps the abbreviation)."""
    parts = [x.strip() for x in what.split("/")]
    if parts and all(x in abbr for x in parts):
        return "/".join(abbr[x] for x in parts)
    return what


_words = lambda s: set(re.findall(r"[a-z0-9]+", str(s or "").lower()))


def named(what, abbr, split, label):
    """(trait, method): abbreviations written out, each part's method split off ('length of head along
    the midline' -> 'length of head' + 'along the midline'), and the body-part label the passage starts
    with put in front when the name does not already say it ('Humeri' under **Elytra** -> 'Elytra humeri')."""
    traits, methods = [], []
    for part in (x.strip() for x in spelled(what, abbr).split("/")):
        sp = split.get(part)
        traits.append(sp["trait"] if sp else part)
        if sp:
            methods.append(sp["method"])
    trait = "/".join(traits)
    if label and not _words(label) <= _words(trait):
        trait = f"{label} {trait[:1].lower() + trait[1:]}"
    return trait, "; ".join(methods)


def stage_assemble(papers):
    for p in papers:
        fx = json.loads((OUT / "facts" / f"{p}.json").read_text(encoding="utf-8"))
        abbr = json.loads((OUT / "abbrev" / f"{p}.json").read_text(encoding="utf-8"))["abbreviations"]
        split = {n: s for n, s in json.loads((OUT / "names" / f"{p}.json").read_text(encoding="utf-8"))["split"].items()
                 if fx.get("methods", {}).get(n, {}).get("keep")}     # only splits nimble calls 'how measured'
        span = json.loads((OUT / "walk" / f"{p}.json").read_text(encoding="utf-8"))["span"]
        ps = passages(p)
        by_id = {u["id"]: u for u in ps}
        part = {k for k, v in fx.get("labels", {}).items() if v["part"]}
        rows, seen, reread = [], set(), []                 # reread[i]: row i came only from a re-read (v6)

        def add(r, rr=False):
            k = tuple(r.values())
            if k not in seen:
                seen.add(k)
                rows.append(r)
                reread.append(rr)

        n_field = 0
        sf = OUT / "shape" / f"{p}.json"
        shape = json.loads(sf.read_text(encoding="utf-8"))["shape"] if sf.exists() else {}
        for x in fx["facts"]:
            if x["owner"] and not x["why"]:
                u = by_id[x["passage"]]
                lab = u.get("label") or lead_of(u)          # v4: the lead word when there is no bold label
                trait, method = named(x["what"], abbr, split, lab if lab in part else "")
                r = dict(_row(dict(x, what=trait)), measurementMethod=method)
                if x.get("src"):                            # v8: the sentence it came from
                    r["measurementRemarks"] = x["src"]
                if shape.get(x["passage"]) == "list" or x.get("record"):   # v4: each item is its own record: 17 records
                    rows.append(r)                          # at '920 m' are 17 rows, not one
                    reread.append(bool(x.get("reread")))
                else:
                    add(r, bool(x.get("reread")))
        done = set()                                       # v2: one row per body-part field, the whole text
        for u in ps:
            b = u["block"]
            if u["kind"] != "para" or u.get("label") not in part or b in done or not span.get(u["id"]):
                continue
            done.add(b)
            if u.get("field"):
                add({"verbatimIdentification": span[u["id"]], "measurementType": u["label"],
                     "measurementValue": u["field"], "measurementUnit": "", "measurementStatistic": "", "sex": ""})
                n_field += 1
        _write(OUT / "prose" / p / f"{p}.csv", rows)
        _write(OUT / "prose_no_reread" / p / f"{p}.csv", [r for r, rr in zip(rows, reread) if not rr])   # v6
        old = V18 / p / f"{p}.csv"
        prev = list(csv.DictReader(open(old, encoding="utf-8", newline=""))) if old.exists() else []
        _write(OUT / "combined" / p / f"{p}.csv", prev + rows)
        print(f"  [assemble] {p:20s} prose rows {len(rows)} ({n_field} whole fields), v18 rows {len(prev)}", flush=True)


def setup():
    """Each v7 variant reuses the abbreviations, shapes, names, species tracking and Q-FIELD (unchanged code
    paths): v7a from v7, v7b-v7d from v7a."""
    import shutil
    for d in REUSED:
        if not (OUT / d).exists() and (PREV_OUT / d).exists():
            shutil.copytree(PREV_OUT / d, OUT / d)


def stage_score(papers):
    import evaluate as ev
    ev.ASSESS_MISS_SEVERITY = False
    for root in ("prose", "combined"):
        ev.evaluate_all(_paths.PAPERS, OUT / root, ev.DEFAULT_KEY, False, semantic=True, use_llm=True)
        print(f"== {root}:\n" + (OUT / root / "summary.csv").read_text(encoding="utf-8"), flush=True)


def stage_page(papers):
    """The scorer's own matching on the combined rows (species remap, trait-name remap with the LLM,
    match on species + trait + value), saved per paper for the comparison page."""
    import evaluate as ev
    from mineru_extract import classify_folder
    d = OUT / "page"
    d.mkdir(parents=True, exist_ok=True)
    keep = ["verbatimIdentification", "measurementType", "measurementValue", "measurementStatistic", "sex",
            "measurementUnit"]
    for p in papers:
        _, gt_f, _ = classify_folder(_paths.PAPERS / p)
        gt = ev.load_xlsx(str(gt_f))
        pred = ev.load_csv(str(OUT / "combined" / p / f"{p}.csv"))
        orig = [dict(r) for r in pred]
        with contextlib.redirect_stdout(io.StringIO()):
            pred, sp_map, _un = ev.remap_pred_species(gt, pred)
            pred, ty_map = ev.remap_pred_types(gt, pred, use_llm=True)
        for r, o in zip(pred, orig):
            r["_printed_type"], r["_printed_species"] = o.get("measurementType", ""), o.get("verbatimIdentification", "")
        matched, missing, extra = ev.match_rows(gt, pred, ev.DEFAULT_KEY, False)
        scope = ev.build_scope(gt, ["measurementType"], False)
        ins, outs = ev.partition_extra(extra, scope, False)
        cut = lambda r: {k: str(r.get(k, "") or "") for k in keep + ["_printed_type", "_printed_species"] if k in r}
        out = {"matched": [[cut(g), cut(x)] for g, x in matched], "missed": [cut(g) for g in missing],
               "extra_in_scope": [cut(x) for x in ins], "extra_out_of_scope": [cut(x) for x, _u in outs],
               "species_map": sp_map, "type_map": ty_map}
        (d / f"{p}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  [page] {p:20s} matched {len(matched)}, missed {len(missing)}, extra {len(ins)} in scope "
              f"+ {len(outs)} out of scope", flush=True)


STAGES = {"abbrev": stage_abbrev, "read": stage_read, "names": stage_names, "walk": stage_walk,
          "shape": stage_shape, "items": stage_items, "heads": stage_heads, "places": stage_places,
          "nm": stage_nm, "field": stage_field, "read7": stage_read7, "read8": stage_read8,
          "facts": stage_facts, "units": stage_units,
          "assemble": stage_assemble,
          "score": stage_score, "page": stage_page}
ALL = ["abbrev", "shape", "nm", "heads", "walk", "field", "read7", "names", "places", "facts", "assemble"]


def papers_of(args):
    if args == ["dev"]:
        s = json.loads(SET.read_text(encoding="utf-8"))["109"]
        return s["dev"] + s["held_a"]          # tuning papers only; held_b and grit-only are the test
    if args == ["held_b"]:                     # the test, run once: names read from the set, never printed;
        return json.loads(SET.read_text(encoding="utf-8"))["109"]["held_b"]   # report with prose_test.py
    return args


if __name__ == "__main__":
    stage, *rest = sys.argv[1:]
    papers = papers_of(rest)
    setup()
    for name in (ALL if stage == "all" else [stage]):
        print(f"=== {name} on {len(papers)} papers", flush=True)
        GEN.clear()
        STAGES[name](papers)
        if GEN["calls"]:
            print(f"  [gemma] {name}: " + ", ".join(f"{k} {v:.0f}" for k, v in GEN.items()), flush=True)
