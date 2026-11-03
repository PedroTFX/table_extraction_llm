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

    python prose_reader.py <stage> dev|<paper ...>      stages: abbrev read names walk facts assemble score page all
"""
import collections
import contextlib
import csv
import io
import json
import re
import sys
import time
import urllib.request as _rq
from pathlib import Path

import _paths
sys.path.insert(1, str(Path(__file__).resolve().parent.parent / "v18"))
import decoder as v1                 # noqa: E402  (GEMMA, NIMBLE, unload, _printed)
import duels                         # noqa: E402

PREV_OUT = _paths.OUTPUT / "prose_v2"
OUT = _paths.OUTPUT / "prose_v3"      # v3: species tracking (Q-SAME both orders, Q-RANK, wider 'none')
REUSED = ("abbrev", "read", "names")  # v3 changes nothing before the walk: these come from v2
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
        for piece in _split_long(t):
            out.append({"id": f"P{len(out)}", "kind": "para", "text": piece, "heading": heading, "block": b,
                        "label": lab, "field": rest})
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

def gemma(prompt, schema, timeout=900):
    body = {"model": v1.GEMMA, "stream": False, "format": schema, "think": False,
            "messages": [{"role": "user", "content": prompt}],
            "options": {"temperature": 0, "num_ctx": 16384, "num_predict": 6000}}
    for attempt in range(3):
        try:
            req = _rq.Request("http://127.0.0.1:11434/api/chat", data=json.dumps(body).encode(),
                              headers={"Content-Type": "application/json"})
            with _rq.urlopen(req, timeout=timeout) as r:
                msg = json.loads(r.read()).get("message", {}).get("content", "")
            got = json.loads(msg)
            return got if isinstance(got, dict) else {}
        except json.JSONDecodeError:
            return {}
        except Exception:
            if attempt == 2:
                raise
            time.sleep(10 * (attempt + 1))


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
        for ch in chunks:
            for e in gemma(ABBREV.format(text=ch), ABBREV_SCHEMA).get("abbreviations", []):
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
        groups, cur = [], []
        for u in ps:
            if cur and sum(len(x["text"]) for x in cur) + len(u["text"]) > READ_CHARS:
                groups.append(cur)
                cur = []
            cur.append(u)
        groups += [cur] if cur else []
        res = {}
        for g in groups:
            text = "\n\n".join(f"[{u['id']}] " + ("(heading) " if u["kind"] == "heading" else "") + u["text"] for u in g)
            used = {a: m for a, m in abbr.items() if re.search(r"(?<!\w)" + re.escape(a) + r"(?!\w)", text)}
            where = f"They follow the heading '{g[0]['heading'][:120]}'." if g[0]["kind"] == "para" and g[0]["heading"] else ""
            ab = ("The paper defines these abbreviations: " + "; ".join(f"{a} = {m}" for a, m in used.items()) + ".\n") if used else ""
            got = gemma(READ.format(where=where, abbrevs=ab, passages=text), READ_SCHEMA).get("passages", [])
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
        rd = json.loads((OUT / "read" / f"{p}.json").read_text(encoding="utf-8"))
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
        rd = json.loads((OUT / "read" / f"{p}.json").read_text(encoding="utf-8"))
        span = json.loads((OUT / "walk" / f"{p}.json").read_text(encoding="utf-8"))["span"]
        by_id = {u["id"]: u for u in rd["passages"]}
        facts, owners = [], []
        for pid, fa in read_facts(rd):
            s = span.get(pid)
            x = dict(fa, passage=pid, account=s)
            if not fa["who"] or (s and same_name(fa["who"], s)):
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
        whats = collections.defaultdict(list)
        for x in facts:
            if x["owner"]:
                whats[x["what"].lower()].append(x["value"])
        trait = {}
        for w, vals in whats.items():
            ex = "; ".join(f"'{v[:100]}'" for v in list(dict.fromkeys(vals))[:3])
            st = f"A scientific paper describing organisms gives '{w}' for them, for example: {ex}."
            ch, pr = ask(st, Q_TRAIT.format(what=w), dict(TRAIT))
            trait[w] = {"choice": ch, "probs": pr, "keep": duels.sure(ch, pr, "trait") == "trait"}
        for x in facts:
            if x["owner"] and not trait.get(x["what"].lower(), {}).get("keep"):
                x["why"] = "not a characteristic (Q-TRAIT)"
        labels = {}                                        # v2: Q-LABEL once per label of the paper
        for u in passages(p):
            lab = u.get("label")
            if u["kind"] != "para" or not lab or lab in labels:
                continue
            st = (f"In a paper that describes species, a paragraph starts with the label '{lab}' and reads:\n"
                  f"\"\"\"{u['text'][:500]}\"\"\"")
            ch, pr = ask(st, Q_LABEL.format(label=lab), dict(LABEL))
            labels[lab] = {"choice": ch, "probs": pr, "part": duels.sure(ch, pr, "part") == "part"}
        methods = {}                                       # v2: Q-METHOD per split gemma proposed
        split = json.loads((OUT / "names" / f"{p}.json").read_text(encoding="utf-8"))["split"]
        for n, sp in split.items():
            st = f"A scientific paper names a characteristic of an organism '{n}'."
            crit = {k: v.format(m=sp["method"], t=sp["trait"]) for k, v in METHOD.items()}
            ch, pr = ask(st, Q_METHOD.format(m=sp["method"], n=n), crit)
            methods[n] = {"choice": ch, "probs": pr, "keep": duels.sure(ch, pr, "how") == "how"}
        f.write_text(json.dumps({"facts": facts, "owners": owners, "trait": trait, "labels": labels,
                                 "methods": methods}, indent=1, ensure_ascii=False), encoding="utf-8")
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
        rd = json.loads((OUT / "read" / f"{p}.json").read_text(encoding="utf-8"))
        abbr = json.loads((OUT / "abbrev" / f"{p}.json").read_text(encoding="utf-8"))["abbreviations"]
        parts = list(dict.fromkeys(x.strip() for _pid, fa in read_facts(rd)
                                   for x in spelled(fa["what"], abbr).split("/") if x.strip()))
        split, calls = {}, 0
        for i in range(0, len(parts), 40):
            calls += 1
            got = gemma(NAMES.format(names="\n".join(parts[i:i + 40])), NAMES_SCHEMA).get("names", [])
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
    stat = "range" if RANGE.match(v) else "individual" if NUM.match(v) else ""
    return {"verbatimIdentification": x["owner"], "measurementType": x["what"], "measurementValue": v,
            "measurementUnit": unit, "measurementStatistic": stat,
            "sex": x["sex"] if x["sex"] in ("male", "female") else ""}


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
        rows, seen = [], set()

        def add(r):
            k = tuple(r.values())
            if k not in seen:
                seen.add(k)
                rows.append(r)

        n_field = 0
        for x in fx["facts"]:
            if x["owner"] and not x["why"]:
                lab = by_id[x["passage"]].get("label")
                trait, method = named(x["what"], abbr, split, lab if lab in part else "")
                add(dict(_row(dict(x, what=trait)), measurementMethod=method))
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
        old = V18 / p / f"{p}.csv"
        prev = list(csv.DictReader(open(old, encoding="utf-8", newline=""))) if old.exists() else []
        _write(OUT / "combined" / p / f"{p}.csv", prev + rows)
        print(f"  [assemble] {p:20s} prose rows {len(rows)} ({n_field} whole fields), v18 rows {len(prev)}", flush=True)


def setup():
    """v3 reuses v2's abbreviations, reading and name splits (unchanged code paths)."""
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
          "facts": stage_facts, "assemble": stage_assemble, "score": stage_score, "page": stage_page}
ALL = ["abbrev", "read", "names", "walk", "facts", "assemble", "score"]


def papers_of(args):
    if args == ["dev"]:
        s = json.loads(SET.read_text(encoding="utf-8"))["109"]
        return s["dev"] + s["held_a"]          # tuning papers only; held_b and grit-only are the test
    return args


if __name__ == "__main__":
    stage, *rest = sys.argv[1:]
    papers = papers_of(rest)
    setup()
    for name in (ALL if stage == "all" else [stage]):
        print(f"=== {name} on {len(papers)} papers", flush=True)
        STAGES[name](papers)
