"""
prose_tree.py — EXPERIMENT (2026-11-05): the prose reader on a new backbone, an information tree.

    species register
        phrase (a sentence nimble kept, or a list item)
            fact: a linked list of what the phrase gives, in the order it is printed
                  (type, value, unit, sex, and on a record its locality and coordinates; each only if present)

A phrase can hang under more than one species. The linked list can start at any part: 'Measured in mm: body length 15'
starts at the unit. gemma says which parts belong together; code finds each part in the phrase, and the order they are
printed in links them. So a value is checked by itself, not side by side with its unit:
    printed     the value is printed in its phrase (or in another phrase gemma was shown: the fact moves there)
    words       every word and number of the value is in its phrase, not side by side
    otherwise   rejected: kept on the leaf with the reason, no row
A phrase giving only a unit stays open on its leaf; a later number with no unit in the same paragraph asks nimble if that
unit is its own (Q-UNIT). A sex carries the same way, phrase by phrase, until another is named (Q-SEX). Reused from prose_v8d: abbreviations, shape, species tracking, Q-FIELD, places; prose_sent is the
sentence sort. nimble's decisions (prose_reader.stage_facts) are unchanged and written back on the facts; rows are read from
the tree.

    python prose_tree.py all dev          tree leaves links names facts decide rows
    python prose_tree.py show Xia2022     prints a paper's tree
Output: output/prose_<variant>/tree/<paper>.json, output/prose_<variant>/prose/<paper>/<paper>.csv
v9b: v9 + Q-SEX; a type with no value is a format failure, asked again; 'sex' and 'who' answers are no facts (an item answered
only with them is read again); kept sentences that gave nothing are read again in small groups; Q-COMP by phrase; a part links
to the value by the distance from the value's edges.
"""
import collections
import json
import os
import re
import sys
import time

os.environ.setdefault("PROSE_VARIANT", "v9b")

import prose_reader as pr            # noqa: E402
from prose_reader import v1          # noqa: E402
import duels                         # noqa: E402

OUT = pr.OUT
BASE = pr._paths.OUTPUT / "prose_v8d"
SENT = pr._paths.OUTPUT / "prose_sent"
TREE = OUT / "tree"


# === the question to gemma: one answer per phrase, each part in its own field ====================================

FIELDS = """Give each fact as an object with these named fields, always all of them; a field the text does not give is "":
- "type": what the fact is about
- "value": what the text gives for it
- "unit": the unit of the value (mm, m, ...), wherever the text gives it, also when printed away from the value; never inside "value"
- "sex": "male" or "female" when the text says it is of males or of females (for example 'Male:', '♂', '♀')
- "who": "" when it is {s}'s; the organism's name, as printed, only when the text says it of another organism
A sentence can give only a part, for what comes next (for example 'All measurements in mm.'): give that part, the others "".
"""
MEASURE = pr.READ7_HEAD + """They give measurements. For EACH id list every measurement; an id that gives nothing has "facts": [].
""" + FIELDS + """- type: the label or abbreviation, as printed
- value: the number or range COPIED exactly, without its unit
Example: "[P1.1] All measurements in mm. [P1.2] Male: TL 5.2–5.9, WL 3.1. [P1.3] Female: TL 6.0 mm" gives
{{"phrases": [{{"id": "P1.1", "facts": [{{"type": "", "value": "", "unit": "mm", "sex": "", "who": ""}}]}},
{{"id": "P1.2", "facts": [{{"type": "TL", "value": "5.2–5.9", "unit": "mm", "sex": "male", "who": ""}}, {{"type": "WL", "value": "3.1", "unit": "mm", "sex": "male", "who": ""}}]}},
{{"id": "P1.3", "facts": [{{"type": "TL", "value": "6.0", "unit": "mm", "sex": "female", "who": ""}}]}}]}}

Sentences:
{passages}

Reply with JSON only."""
DESCRIBE = pr.READ7_HEAD + """For EACH id list every characteristic it states; an id that gives none has "facts": [].
""" + FIELDS + """- type: the part or property described, as the text names it (a body part or structure, colour, size, distribution, habitat, host plant, ...)
- value: what the text says about it, COPIED exactly and in full: the whole clause with its qualifiers, not a shortened part
One entry per part or property. Only characteristics of organisms: not who collected specimens, dates, where specimens are kept, figure numbers, or the name's origin.
Example: "[P1.1] Pronotum black, shining; legs yellow. [P1.2] Unlike X. other, the tibiae are spined" gives
{{"phrases": [{{"id": "P1.1", "facts": [{{"type": "pronotum", "value": "black, shining", "unit": "", "sex": "", "who": ""}}, {{"type": "legs", "value": "yellow", "unit": "", "sex": "", "who": ""}}]}},
{{"id": "P1.2", "facts": [{{"type": "tibiae", "value": "spined", "unit": "", "sex": "", "who": ""}}]}}]}}

Sentences:
{passages}

Reply with JSON only."""
ITEM = pr.READ7_HEAD + """Each item is one record or entry of a list. For EACH id list what it gives; an id that gives nothing has "facts": [].
""" + FIELDS + """- type: what the item gives (altitude, locality, habitat, host plant, ...)
- value: COPIED exactly, without its unit
Not who collected or identified specimens, dates, specimen numbers or where specimens are kept.
Example: "[P1#0] 2♂, 1♀, Mount Kora, forest edge, 1200 m, 12.V.2015, J. Smith leg." gives
{{"phrases": [{{"id": "P1#0", "facts": [{{"type": "altitude", "value": "1200", "unit": "m", "sex": "", "who": ""}}, {{"type": "locality", "value": "Mount Kora", "unit": "", "sex": "", "who": ""}}, {{"type": "habitat", "value": "forest edge", "unit": "", "sex": "", "who": ""}}]}}]}}

Items:
{passages}

Reply with JSON only."""
SCHEMA = {"type": "object", "required": ["phrases"], "properties": {"phrases": {"type": "array", "items": {
    "type": "object", "required": ["id", "facts"], "properties": {"id": {"type": "string"}, "facts": {"type": "array", "items": {
        "type": "object", "required": ["type", "value", "unit", "sex"],
        "properties": {k: {"type": "string"} for k in ("type", "value", "unit", "sex", "who")}}}}}}}}

Q_ALSO = "Does this sentence state something about {o} itself?"
ALSO = {"yes": "yes: it states a characteristic that {o} has, also or instead of {s}",
        "no": "no: {o} is only named, to tell {s} apart from it, or to cite a record or a publication"}
Q_OF = "Is '{what}: {value}' said of {o}?"
OF = {"yes": "yes: the sentence says this of {o}", "no": "no: the sentence says this of another organism, not of {o}"}
Q_UNIT = "Is the value {value} of '{what}' given in {unit}?"
UNIT = {"yes": "yes: the text before says values like this one are in {unit}",
        "no": "no: it is a count, a ratio, or in another unit, or the text before is about something else"}
Q_SEX = "Does the last part still give what the {sex} has?"
SEX_ON = {"yes": "yes: it goes on with the {sex}, what it gives is of the {sex}",
          "no": "no: it is about both sexes, the species in general, or something else"}


# === geometry: where each part is printed =========================================================================

UNIT_END = re.compile(r"^(.*\d[^A-Za-z]*?)\s*(mm|cm|µm|μm|um|m|km|g|mg|kg|ml|°c)\.?$", re.I)
TOK = re.compile(r"\d+(?:[.,]\d+)?|[^\W\d_]+")
SEX = {"male": ("♂", "male", "males"), "female": ("♀", "female", "females")}


def spans(term, text):
    """Where the term's words are printed in this order, whole words and whole numbers ('5' is not in '15' or '5.2',
    'm' is not in 'summer'), anything but letters / digits between them."""
    w = re.findall(r"[^\W_]+", str(term or ""))
    if not w:
        return []
    left = r"(?<!\d)(?<!\d[.,])" if w[0][0].isdigit() else r"(?<![^\W\d_])"
    right = r"(?!\d)(?![.,]\d)" if w[-1][-1].isdigit() else r"(?![^\W\d_])"
    return [m.span() for m in re.finditer(left + r"[\W_]+".join(map(re.escape, w)) + right, text, re.I)]


def bag(s):
    return {x.lower() for x in TOK.findall(str(s or ""))}


def apart(value, text):
    """A value ending in a unit whose number is printed in this text -> (number, unit)."""
    m = UNIT_END.match(value.strip())
    return (m.group(1).strip(), m.group(2)) if m and spans(m.group(1), text) else None


def check_value(value, i, order, ph):
    """-> (value, unit written inside it, how it passed, the phrase it is printed in), or None."""
    for j in [i] + [x for x in order if x != i]:
        t = ph[j]["text"]
        a = apart(value, t)
        if a:
            return a[0], a[1], "printed", j
        if spans(value, t):
            return value, "", "printed", j
    if bag(value) and bag(value) <= bag(ph[i]["text"]):
        return value, "", "words", i
    return None


def nest(nodes):
    """The parts as a linked list in the order they are printed; a part not printed by itself goes first."""
    first = None
    for n in sorted(nodes, key=lambda x: -1 if x["at"] is None else x["at"], reverse=True):
        first = dict({k: v for k, v in n.items() if k != "next"}, next=first)
    return first


def flat(first):
    out = []
    while first:
        out.append(first)
        first = first["next"]
    return out


def parts(chain):
    return {n["kind"]: n["text"] for n in flat(chain["first"])}


def node(kind, text, at, where):
    return {"kind": kind, "text": text, "at": at, "where": where}


def closest(sp, v):
    """The printed place nearest the value, measured from the value's edges ('HW: 1.72 mm': the 'mm' after it, not the one
    before 'HW')."""
    return min(sp, key=lambda a: a[0] - v[1] if a[0] >= v[1] else max(v[0] - a[1], 0))[0] if sp else None


def make_chain(fa, value, unit, text, around, start, check):
    """A fact's parts, each found in its phrase, linked in printed order."""
    nodes, vat, edges = [], None, (0, 0)
    if value:
        sp = spans(value, text)
        if sp:
            edges = next((x for x in sp if x[0] >= start), sp[0])
            vat = edges[0]
        nodes.append(node("value", value, vat, "phrase" if sp else "words"))
    near = edges[0]
    if fa["type"]:
        at = closest(spans(fa["type"], text), edges)
        nodes.append(node("type", fa["type"], at, "phrase" if at is not None else "not printed as such"))
    chain = {"who": fa.get("who", ""), "check": check}
    if unit:
        at = closest(spans(unit, text), edges)
        if at is not None:
            nodes.append(node("unit", unit, at, "phrase"))
        elif spans(unit, around):
            nodes.append(node("unit", unit, None, "around"))
        else:
            chain["unit_not_printed"] = unit               # never a unit the text does not give
    sex = fa["sex"].strip().lower()
    if sex in SEX:
        hits = [m.start() for w in SEX[sex] for m in re.finditer(r"(?<![^\W\d_])" + re.escape(w) + r"(?![^\W\d_])", text, re.I)]
        before = [a for a in hits if a <= near] or hits
        at = max(before) if before else None
        nodes.append(node("sex", sex, at, "phrase" if at is not None else "context"))
    chain["first"] = nest(nodes)
    return chain, (vat + 1 if vat is not None else start)


def load(p):
    return json.loads((TREE / f"{p}.json").read_text(encoding="utf-8"))


def save(p, t):
    (TREE / f"{p}.json").write_text(json.dumps(t, indent=1, ensure_ascii=False), encoding="utf-8")


def by_passage(t):
    out = collections.defaultdict(list)
    for i, r in t["phrases"].items():
        out[r["passage"]].append(i)
    return out


def twice(ask, st, q, crit):
    """nimble: yes only when sure in both orders."""
    for c in (crit, {k: crit[k] for k in reversed(list(crit))}):
        ch, prob = ask(st, q, c)
        if duels.sure(ch, prob, "yes") != "yes":
            return False
    return True


# === stages =======================================================================================================

def stage_tree(papers):
    """The registers and their phrases, before any fact is read. gemma only finds where a list's items start; nimble asks
    Q-ALSO when a sentence names another registered species: it hangs under that species too on a sure yes in both orders."""
    TREE.mkdir(parents=True, exist_ok=True)
    for p in papers:
        if (TREE / f"{p}.json").exists():
            continue
        t0 = time.time()
        rd = json.loads((BASE / "read2" / f"{p}.json").read_text(encoding="utf-8"))
        span = json.loads((OUT / "walk" / f"{p}.json").read_text(encoding="utf-8"))["span"]
        shape = json.loads((OUT / "shape" / f"{p}.json").read_text(encoding="utf-8"))["shape"]
        field = json.loads((OUT / "field" / f"{p}.json").read_text(encoding="utf-8"))["field"]
        sent = collections.defaultdict(list)
        for r in json.loads((SENT / f"{p}.json").read_text(encoding="utf-8"))["units"]:
            sent[r["passage"]].append(r)
        species = {s: {"phrases": []} for s in dict.fromkeys(x for x in span.values() if x)}
        ph, left_out, plogs = {}, 0, collections.Counter()

        def add(i, text, kind, u, cat=""):
            ph[i] = {"text": text, "kind": kind, "cat": cat, "passage": u["id"], "account": span[u["id"]],
                     "field": field.get(u["id"], "other"), "registers": [span[u["id"]]],
                     "chains": [], "open": [], "rejected": []}
            species[span[u["id"]]]["phrases"].append(i)

        for u in rd["passages"]:
            pid = u["id"]
            if u["kind"] != "para" or not span.get(pid):
                continue
            if shape.get(pid) == "text":
                k = 0
                for r in sent.get(pid, []):
                    if not r["kept"]:
                        left_out += 1
                        continue
                    k += 1
                    add(f"{pid}.{k}", r["text"], "sentence", u, r.get("cat", ""))
            elif shape.get(pid) == "list":
                items, plog = pr.list_items(u)
                plogs.update(plog)
                if len(items) < 2:
                    add(f"{pid}.1", u["text"], "sentence", u, "list read whole")
                else:
                    for k, x in enumerate(items):
                        add(f"{pid}#{k}", x, "item", u, "record list")
        v1.unload(v1.GEMMA)
        ask, asked = pr.Ask(), []
        for i, r in ph.items():
            if r["kind"] != "sentence":
                continue
            s = r["account"]
            for o in species:
                g = pr._key(o)
                if pr.same_name(o, s) or not g or not re.search(rf"\b{g[0]}[a-z]*\.?\s+{re.escape(g[1])}\b", r["text"], re.I):
                    continue
                st = f"In the account of {s} in a scientific paper, a sentence reads:\n\"\"\"{r['text'][:900]}\"\"\""
                yes = twice(ask, st, Q_ALSO.format(o=o), {k: v.format(o=o, s=s) for k, v in ALSO.items()})
                asked.append({"phrase": i, "other": o, "also": yes})
                if yes:
                    r["registers"].append(o)
                    species[o]["phrases"].append(i)
        ask.unload()
        save(p, {"paper": p, "species": species, "phrases": ph, "left_out": left_out, "also_asked": asked,
                 "item_log": dict(plogs)})
        print(f"  [tree] {p:20s} {len(species)} registers, {len(ph)} phrases ({left_out} sentences left out); "
              f"Q-ALSO asked {len(asked)}, shared {sum(a['also'] for a in asked)} ({time.time() - t0:.0f}s)", flush=True)


def ask_gemma(tpl, units, s, abbr, where, what):
    """gemma on [(phrase id, text)] -> {id: [answers]}; a malformed answer, or no answer at all, is asked again once."""
    text = "\n".join(f"[{i}] {t}" for i, t in units)
    used = {a: m for a, m in abbr.items() if re.search(r"(?<!\w)" + re.escape(a) + r"(?!\w)", text)}
    ab = ("The paper defines these abbreviations: " + "; ".join(f"{a} = {m}" for a, m in used.items()) + ".\n") if used else ""
    ids = {i for i, _t in units}

    def parse(got):
        res, bad = {i: [] for i in ids}, set()
        for x in got:
            i = str(x.get("id") or "").strip("[] ")
            if i not in ids:
                pr.GEN["answers with an unknown id"] += 1
                continue
            for row in x.get("facts") or []:
                if not isinstance(row, dict):
                    pr.GEN["malformed facts"] += 1
                    bad.add(i)
                    continue
                fa = {k: " ".join(str(row.get(k) or "").split()) for k in ("type", "value", "unit", "sex", "who")}
                if fa["type"].lower() in ("sex", "who"):   # a field given as a fact: no fact (an item's sex is its ♂ / ♀)
                    pr.GEN["sex or who as a fact"] += 1
                elif fa["type"] and not (fa["value"] or fa["unit"] or fa["sex"]):
                    pr.GEN["type with no value"] += 1      # it names what it read but gives nothing: asked again
                    bad.add(i)
                elif any(fa[k] for k in ("type", "value", "unit", "sex")):
                    res[i].append(fa)
        return res, bad, not got

    res, bad, none = parse(pr.gemma(tpl.format(what=what, s=s, where=where, abbrevs=ab, passages=text), SCHEMA).get("phrases", []))
    if bad or none:
        pr.GEN["format retries"] += 1
        sub = "\n".join(f"[{i}] {t}" for i, t in units if none or i in bad)
        note = "\nYour previous answer to this was not valid. Give every id listed, and every fact as an object with all its named fields, the value with what the text says about the type."
        again, _b, _n = parse(pr.gemma(tpl.format(what=what, s=s, where=where, abbrevs=ab, passages=sub) + note, SCHEMA).get("phrases", []))
        for i, r in again.items():
            if r:
                res[i] = r
    return res


def stage_leaves(papers):
    """gemma reads the phrases in passage order, with the same question per kind of passage as v8d (a passage's sentences
    stay together, so 'Male:' stays in place), and each answer is stored on its phrase as a linked list. Re-reads on evidence
    only: sentences nimble kept that gave nothing, items that gave nothing, each in small groups."""
    for p in papers:
        t = load(p)
        if t.get("leaves_done"):
            continue
        t0 = time.time()
        ph = t["phrases"]
        abbr = json.loads((OUT / "abbrev" / f"{p}.json").read_text(encoding="utf-8"))["abbreviations"]
        ps = {u["id"]: u for u in pr.passages(p)}
        groups = by_passage(t)
        cursor = collections.Counter()
        count = collections.Counter()
        under = lambda pid: f", under the heading '{ps[pid]['heading'][:120]}'" if ps[pid]["heading"] else ""

        def store(units, got, where):
            order = [i for i, _t in units]
            around = " ".join(x for _i, x in units) + " " + where
            for i in order:
                for fa in got.get(i, []):
                    value, inside, check, j = fa["value"], "", "", i
                    if value:
                        hit = check_value(value, i, order, ph)
                        if not hit:
                            ph[i]["rejected"].append(dict(fa, why="value not printed"))
                            count["rejected"] += 1
                            continue
                        value, inside, check, j = hit
                        count[f"value {check}"] += 1
                        count["moved to the phrase that prints it"] += j != i
                    chain, cursor[j] = make_chain(fa, value, fa["unit"] or inside, ph[j]["text"], around, cursor[j], check)
                    chain["as_read"] = fa
                    (ph[j]["chains"] if value and fa["type"] else ph[j]["open"]).append(chain)

        def run(tpl, ids, s, where, what):
            units = [(i, ph[i]["text"]) for i in ids]
            store(units, ask_gemma(tpl, units, s, abbr, where, what), where)

        cur, ck, size = [], None, 0
        calls = []
        for pid, ids in groups.items():
            if ph[ids[0]]["kind"] == "item":
                continue
            k = (ph[ids[0]]["account"], ph[ids[0]]["field"])
            n = sum(len(ph[i]["text"]) for i in ids)
            if cur and (ck != k or size + n > pr.READ_CHARS):
                calls.append(cur)
                cur, size = [], 0
            cur, ck, size = cur + ids, k, size + n
        calls += [cur] if cur else []
        for ids in calls:
            first = ph[ids[0]]
            run(MEASURE if first["field"] == "measure" else DESCRIBE, ids, first["account"], under(first["passage"]), "sentences")
        again = collections.defaultdict(list)              # kept by nimble, nothing read: again, by account and question
        for ids in calls:
            for i in ids:
                if ph[i]["cat"] != "comparison" and not (ph[i]["chains"] or ph[i]["open"] or ph[i]["rejected"]):
                    again[(ph[i]["account"], ph[i]["field"])].append(i)
        for (s, fld), ids in again.items():
            count["sentences read again"] += len(ids)
            for a in range(0, len(ids), pr.ITEMS_PER_CALL):
                run(MEASURE if fld == "measure" else DESCRIBE, ids[a:a + pr.ITEMS_PER_CALL], s, "", "sentences")
        for pid, ids in groups.items():
            if ph[ids[0]]["kind"] != "item":
                continue
            s = ph[ids[0]]["account"]
            for a in range(0, len(ids), pr.ITEMS_PER_CALL):
                run(ITEM, ids[a:a + pr.ITEMS_PER_CALL], s, under(pid), "items of one list")
            empty = [i for i in ids if not (ph[i]["chains"] or ph[i]["open"])]
            if empty:
                run(ITEM, empty, s, under(pid), "items of one list")
                count["items read again"] += len(empty)
            for i in ids:
                record(ph[i], count)
        t.update(leaves_done=True, counts=dict(count))
        save(p, t)
        print(f"  [leaves] {p:20s} {sum(len(r['chains']) for r in ph.values())} facts, {sum(len(r['open']) for r in ph.values())} "
              f"open, {dict(count)} ({time.time() - t0:.0f}s)", flush=True)
    v1.unload(v1.GEMMA)


def record(r, count):
    """A list item (code only): ♂ alone / ♀ alone gives the sex to facts with none, a 'sex' fact is no row; what gemma named
    locality or coordinates goes on the item's other facts as their own parts; an item with nothing else is logged."""
    sx = "male" if "♂" in r["text"] and "♀" not in r["text"] else "female" if "♀" in r["text"] and "♂" not in r["text"] else ""
    keep, loc, coord = [], [], []
    for c in r["chains"]:
        d = parts(c)
        name = d.get("type", "").strip().lower().replace("_", " ")
        if name == "sex":
            continue
        (loc if name in pr.RECORD_LOC else coord if name in pr.RECORD_COORD else keep).append(c if name not in pr.RECORD_LOC | pr.RECORD_COORD else d["value"])
    for c in keep:
        nodes = flat(c["first"])
        vat = next((n["at"] for n in nodes if n["kind"] == "value"), None)
        extra = [("locality", "; ".join(loc)), ("coordinates", ", ".join(coord))]
        if sx and not any(n["kind"] == "sex" for n in nodes):
            extra.append(("sex", sx))
        for k, v in extra:
            if v:
                sp = spans(v, r["text"])
                nodes.append(node(k, v, sp[0][0] if sp else vat, "phrase" if sp else "item"))
        c["first"] = nest(nodes)
    r["chains"] = keep
    if not keep and (loc or coord):
        r["record_only"] = {"locality": loc, "coordinates": coord}
        count["items with only place fields"] += 1


def stage_links(papers):
    """Parts that carry down a paragraph, nimble deciding. Q-UNIT: a number with no unit, after a phrase that gave only a
    unit. Q-SEX: a phrase with no sex, after a phrase whose facts all say one sex (asked once per phrase, until another is
    named). Then the tree is written out in the form the fact decisions read (read2)."""
    for p in papers:
        t = load(p)
        if t.get("links_done"):
            continue
        t0 = time.time()
        ph, ask, n = t["phrases"], pr.Ask(), collections.Counter()
        rd = json.loads((BASE / "read2" / f"{p}.json").read_text(encoding="utf-8"))
        ps = {u["id"]: u for u in rd["passages"]}
        blocks = collections.defaultdict(list)             # a paragraph cut into pieces is still one paragraph
        for pid, ids in by_passage(t).items():
            blocks[ps[pid]["block"]] += ids
        for ids in blocks.values():
            if ph[ids[0]]["kind"] == "item":
                continue
            opened, sexed = [], None
            for i in ids:
                said = {parts(c)["sex"] for c in ph[i]["chains"] if "sex" in parts(c)}
                if said:
                    sexed = (i, said.pop()) if len(said) == 1 else None
                elif sexed and ph[i]["chains"]:
                    st = (f"A passage of a scientific paper says:\n\"\"\"{ph[sexed[0]]['text'][:500]}\"\"\"\n"
                          f"and then:\n\"\"\"{ph[i]['text'][:500]}\"\"\"")
                    n["sex asked"] += 1
                    if twice(ask, st, Q_SEX.format(sex=sexed[1]), {k: v.format(sex=sexed[1]) for k, v in SEX_ON.items()}):
                        n["sex linked"] += 1
                        for c in ph[i]["chains"]:
                            c["first"] = nest(flat(c["first"]) + [node("sex", sexed[1], None, sexed[0])])
                here = [(i, x["at"], x["text"]) for c in ph[i]["open"] for x in flat(c["first"])
                        if x["kind"] == "unit" and x["at"] is not None and "value" not in parts(c)]
                opened += here
                for c in ph[i]["chains"]:
                    d = parts(c)
                    if "unit" in d or not re.search(r"\d", d["value"]):
                        continue
                    vat = next((x["at"] for x in flat(c["first"]) if x["kind"] == "value"), None)
                    cand = [o for o in opened if o[0] != i or vat is None or o[1] < vat]
                    if not cand:
                        continue
                    src, _at, unit = cand[-1]
                    st = (f"A scientific paper says:\n\"\"\"{ph[src]['text'][:500]}\"\"\"\n"
                          + (f"and then:\n\"\"\"{ph[i]['text'][:500]}\"\"\"" if src != i else ""))
                    n["asked"] += 1
                    if twice(ask, st, Q_UNIT.format(value=d["value"], what=d["type"], unit=unit),
                             {k: v.format(unit=unit) for k, v in UNIT.items()}):
                        c["first"] = nest(flat(c["first"]) + [node("unit", unit, None, src)])
                        n["linked"] += 1
        ask.unload()
        rd["read"] = {k: {"names": v.get("names", []), "facts": [], "dropped": []} for k, v in rd["read"].items()}
        rd["log"] = {}
        for i, r in ph.items():
            e = rd["read"].setdefault(r["passage"], {"names": [], "facts": [], "dropped": []})
            if r["kind"] == "item":
                rd["log"].setdefault(r["passage"], {"items": 0})["items"] += 1
            for k, c in enumerate(r["chains"]):
                d = parts(c)
                who = c["who"] if c["who"] and pr.printed(c["who"], ps[r["passage"]]["text"]) else ""
                e["facts"].append({"who": who, "who_read": c["who"], "sex": d.get("sex", ""), "what": d["type"],
                                   "value": d["value"], "unit": d.get("unit", ""), "locality": d.get("locality", ""),
                                   "coordinates": d.get("coordinates", ""), "phrase": i, "chain": k,
                                   **({"comparison_phrase": r["text"]} if r["cat"] == "comparison" else {})})
        (OUT / "read2").mkdir(parents=True, exist_ok=True)
        (OUT / "read2" / f"{p}.json").write_text(json.dumps(rd, indent=1, ensure_ascii=False), encoding="utf-8")
        t["links_done"] = True
        t["q_unit"] = dict(n)
        save(p, t)
        print(f"  [links] {p:20s} Q-UNIT {dict(n)} ({time.time() - t0:.0f}s)", flush=True)


def stage_decide(papers):
    """nimble's decisions go back on the facts of the tree. A fact on a phrase shared by more species: Q-OF, for each other
    register, sure in both orders."""
    for p in papers:
        t = load(p)
        if t.get("decide_done"):
            continue
        ph, ask, n = t["phrases"], pr.Ask(), collections.Counter()
        fx = json.loads((OUT / "facts" / f"{p}.json").read_text(encoding="utf-8"))
        t["joined"] = [x for x in fx["facts"] if "phrase" not in x]
        for x in fx["facts"]:
            if "phrase" in x:
                c = ph[x["phrase"]]["chains"][x["chain"]]
                c["owner"], c["why"] = x["owner"], x["why"]
        for i, r in ph.items():
            for o in r["registers"][1:]:
                for c in r["chains"]:
                    if c.get("why") or not c.get("owner") or pr.same_name(c["owner"], o):
                        continue
                    d = parts(c)
                    st = f"In the account of {r['account']} in a scientific paper, a sentence reads:\n\"\"\"{r['text'][:900]}\"\"\""
                    n["asked"] += 1
                    if twice(ask, st, Q_OF.format(what=d["type"], value=d["value"][:150], o=o),
                             {k: v.format(o=o) for k, v in OF.items()}):
                        c.setdefault("also", []).append(o)
                        n["also"] += 1
        ask.unload()
        t["decide_done"], t["q_of"] = True, dict(n)
        save(p, t)
        print(f"  [decide] {p:20s} Q-OF {dict(n)}", flush=True)


def stage_rows(papers):
    """Rows are read from the tree: register -> phrase -> linked list. Same naming and whole-field rows as v8d."""
    for p in papers:
        t = load(p)
        ph = t["phrases"]
        fx = json.loads((OUT / "facts" / f"{p}.json").read_text(encoding="utf-8"))
        abbr = json.loads((OUT / "abbrev" / f"{p}.json").read_text(encoding="utf-8"))["abbreviations"]
        split = {n: s for n, s in json.loads((OUT / "names" / f"{p}.json").read_text(encoding="utf-8"))["split"].items()
                 if fx.get("methods", {}).get(n, {}).get("keep")}
        span = json.loads((OUT / "walk" / f"{p}.json").read_text(encoding="utf-8"))["span"]
        ps = pr.passages(p)
        by_id = {u["id"]: u for u in ps}
        part = {k for k, v in fx.get("labels", {}).items() if v["part"]}
        rows, seen = [], set()

        def add(r, list_row):
            k = tuple(v for f, v in r.items() if f != "measurementRemarks")
            if list_row or k not in seen:
                seen.add(k)
                rows.append(r)

        def row(owner, passage, d, text, list_row):
            u = by_id[passage]
            lab = u.get("label") or pr.lead_of(u)
            trait, method = pr.named(d["type"], abbr, split, lab if lab in part else "")
            r = pr._row({"owner": owner, "what": trait, "value": d["value"], "unit": d.get("unit", ""), "sex": d.get("sex", ""),
                         "locality": d.get("locality", ""), "coordinates": d.get("coordinates", "")})
            r["measurementMethod"] = method
            if text:
                r["measurementRemarks"] = text[:400]
            add(r, list_row)

        for name, reg in t["species"].items():
            for i in reg["phrases"]:
                r = ph[i]
                for c in r["chains"]:
                    if c.get("why") or not c.get("owner"):
                        continue
                    if pr.same_name(name, r["account"]):
                        row(c["owner"], r["passage"], parts(c), r["text"], r["kind"] == "item")
                    elif name in c.get("also", []):
                        row(name, r["passage"], parts(c), r["text"], False)
        for x in t.get("joined", []):
            if x["owner"] and not x["why"]:
                row(x["owner"], x["passage"], {"type": x["what"], "value": x["value"], "unit": x.get("unit", ""),
                                               "sex": x.get("sex", "")}, "", True)
        done, whole = set(), 0
        for u in ps:
            if u["kind"] == "para" and u.get("label") in part and u["block"] not in done and span.get(u["id"]):
                done.add(u["block"])
                if u.get("field"):
                    add({"verbatimIdentification": span[u["id"]], "measurementType": u["label"], "measurementValue": u["field"],
                         "measurementUnit": "", "measurementStatistic": "", "sex": ""}, False)
                    whole += 1
        pr._write(OUT / "prose" / p / f"{p}.csv", rows)
        print(f"  [rows] {p:20s} {len(rows)} rows ({whole} whole fields)", flush=True)


def show(p, only=""):
    """The tree as text: register, phrase, then each fact's linked list."""
    t = load(p)
    for name, reg in t["species"].items():
        if only and only.lower() not in name.lower():
            continue
        print(name)
        for i in reg["phrases"]:
            r = t["phrases"][i]
            print(f"    {i} [{r['kind']}{' ' + r['cat'] if r['cat'] else ''}] {r['text'][:110]}")
            for label, cs in (("", r["chains"]), ("open: ", r["open"])):
                for c in cs:
                    line = " -> ".join(f"{n['kind']}={n['text'][:50]}" for n in flat(c["first"]))
                    flag = f"  ({c['why']})" if c.get("why") else f"  ({c['check']})" if c.get("check") == "words" else ""
                    print(f"        {label}{line}{flag}")
            for x in r["rejected"]:
                print(f"        rejected: {x['type']} = {x['value'][:60]}")


STAGES = {"tree": stage_tree, "leaves": stage_leaves, "links": stage_links, "names": pr.stage_names, "facts": pr.stage_facts,
          "decide": stage_decide, "rows": stage_rows}

if __name__ == "__main__":
    stage, *rest = sys.argv[1:]
    if stage == "show":
        show(*rest)
        sys.exit(0)
    papers = pr.papers_of(rest)
    pr.setup()
    for name in (list(STAGES) if stage == "all" else [stage]):
        print(f"=== {name} on {len(papers)} papers", flush=True)
        pr.GEN.clear()
        STAGES[name](papers)
        if pr.GEN["calls"]:
            print(f"  [gemma] {name}: " + ", ".join(f"{k} {v:.0f}" for k, v in pr.GEN.items()), flush=True)
