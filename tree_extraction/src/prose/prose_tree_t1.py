"""
prose_tree_t1.py — a second information tree, built apart from v9 (prose_tree.py) (2026-11-05; PROSE_VARIANT=t1).

    species (from the species tracking)
        phrase (a sentence nimble kept, or a list item; can hang under more than one species)
            fact: type, unit, value, sex, who, place, coords, each one a node, each only if present

Nodes have no order: every node knows its facts and every fact knows its nodes, so a fact can be walked from any of
them. One printed 'Male:' or 'in mm' is ONE node shared by all the values it covers, even when it sits in another
phrase ('Measurements in mm.' then 'TL 15' gives TL = 15 mm).

Who does what:
    gemma     reads the passage (the kept sentences together, so 'Male:' stays in sight) or a list item, and answers
              in named fields, any of which may be empty. It does not place anything.
    code      geometry only: finds each answer in the text and hangs it on its phrase; checks each node by itself.
    nimble    the decisions, unchanged (prose_reader.stage_facts), written back on the tree by `treefinal`.

The value check is per node. value: printed in the passage (a trailing unit set aside), or in another passage of the
same reading call, or 'loose': all its words in one sentence in any order, every number exact. Anything else stays on
the tree as 'not printed' and gives no row. unit: printed in the passage, else the nearest phrase of the species.

    python prose_tree_t1.py treeread dev     (then prose_reader.py names, facts)
    python prose_tree_t1.py treefinal dev    (then prose_reader.py assemble)
-> OUT/tree/<paper>.json, OUT/tree_view/<paper>.txt, OUT/read2/<paper>.json for the stages after it
"""
import collections
import json
import re
import sys
import time

import prose_reader as pr

OUT, GEN, printed = pr.OUT, pr.GEN, pr.printed
ROLES = ("type", "unit", "value", "sex", "who", "place", "coords")
SEX = {"male": re.compile(r"(?<![a-z])males?\b|♂", re.I), "female": re.compile(r"\bfemales?\b|♀", re.I)}
WORD = re.compile(r"[^\W_]+")
NUMBER = re.compile(r"\d+(?:[.,]\d+)?")

HEAD = """Below are numbered {what} from the account of {s} in a scientific paper{where}.
{abbrevs}"""
FIELDS = """Give each fact as an object with named fields; a field the text does not give is "":
- "unit": the unit of that number, wherever the text prints it (beside the number, or earlier, as in 'Measurements in mm'), else ""
- "sex": "male" or "female" when the text says it is of males or of females (for example 'Male:', '♂', '♀'), else ""
- "who": "" when it is {s}'s; the organism's name, as printed, only when the text says it of another organism
"""
MEASURE = HEAD + """They give measurements. For EACH passage list every measurement.
""" + FIELDS + """- "what": the label or abbreviation, as printed
- "value": the number or range COPIED exactly, without its unit
Example: a passage "[P1] Measurements in mm. Male: TL 5.2–5.9, WL 3.1. Female: TL 6.0" gives
{{"id": "P1", "facts": [{{"what": "TL", "value": "5.2–5.9", "unit": "mm", "sex": "male", "who": ""}}, {{"what": "WL", "value": "3.1", "unit": "mm", "sex": "male", "who": ""}}, {{"what": "TL", "value": "6.0", "unit": "mm", "sex": "female", "who": ""}}]}}

Passages:
{passages}

Reply with JSON only."""
DESCRIBE = HEAD + """For EACH passage list every characteristic it states.
""" + FIELDS + """- "what": the part or property described, as the text names it (a body part or structure, colour, size, distribution, habitat, host plant, ...)
- "value": what the text says about it, COPIED exactly and in full: the whole clause with its qualifiers, not a shortened part; a lone number without its unit
One entry per part or property. Only characteristics of organisms: not who collected specimens, dates, where specimens are kept, figure numbers, or the name's origin.
Example: a passage "[P1] Pronotum black, shining; legs yellow. Unlike X. other, the tibiae are spined" gives
{{"id": "P1", "facts": [{{"what": "pronotum", "value": "black, shining", "unit": "", "sex": "", "who": ""}}, {{"what": "legs", "value": "yellow", "unit": "", "sex": "", "who": ""}}, {{"what": "tibiae", "value": "spined", "unit": "", "sex": "", "who": ""}}]}}

Passages:
{passages}

Reply with JSON only."""
ITEM = HEAD + """Each item is one record or entry of a list. For EACH item list what it gives.
""" + FIELDS + """- "what": what the item gives (altitude, locality, habitat, host plant, ...)
- "value": COPIED exactly; a number without its unit
Not who collected or identified specimens, dates, specimen numbers or where specimens are kept.
Example: an item "[P1#0] 2♂, 1♀, Mount Kora, forest edge, 1200 m, 12.V.2015, J. Smith leg." gives
{{"id": "P1#0", "facts": [{{"what": "altitude", "value": "1200", "unit": "m", "sex": "", "who": ""}}, {{"what": "locality", "value": "Mount Kora", "unit": "", "sex": "", "who": ""}}, {{"what": "habitat", "value": "forest edge", "unit": "", "sex": "", "who": ""}}]}}

Items:
{passages}

Reply with JSON only."""
SCHEMA = {"type": "object", "required": ["passages"], "properties": {"passages": {"type": "array", "items": {
    "type": "object", "required": ["id", "facts"],
    "properties": {"id": {"type": "string"}, "facts": {"type": "array", "items": {
        "type": "object", "required": ["what", "value", "unit", "sex"],
        "properties": {k: {"type": "string"} for k in ("what", "value", "unit", "sex", "who")}}}}}}}}


def read_raw(tpl, units, s, abbr, where, what="passages"):
    """gemma on units -> {unit id: [answers]}, nothing checked; units answered badly asked once more."""
    def ask(us, note=""):
        text = "\n\n".join(f"[{u['id']}] {u['text']}" for u in us)
        used = {a: m for a, m in abbr.items() if re.search(r"(?<!\w)" + re.escape(a) + r"(?!\w)", text)}
        ab = ("The paper defines these abbreviations: " + "; ".join(f"{a} = {m}" for a, m in used.items()) + ".\n") if used else ""
        got = pr.gemma(tpl.format(what=what, s=s, where=where, abbrevs=ab, passages=text) + note, SCHEMA).get("passages", [])
        ids, res, bad = {u["id"] for u in us}, {}, set()
        for x in got:
            i = str(x.get("id") or "").strip("[] ")
            if i not in ids:
                continue
            rows = res.setdefault(i, [])
            for row in x.get("facts") or []:
                if not isinstance(row, dict):
                    GEN["malformed facts"] += 1
                    bad.add(i)
                    continue
                fa = {k: " ".join(str(row.get(k) or "").split()) for k in ("what", "value", "unit", "sex", "who")}
                if fa["what"] or fa["value"] or fa["unit"]:
                    rows.append(fa)
        return res, bad | (ids - set(res))

    res, bad = ask(units)
    if bad:
        GEN["format retries"] += 1
        again, _ = ask([u for u in units if u["id"] in bad], pr.RETRY_NOTE)
        for i, rows in again.items():
            if rows:
                GEN["format retry units recovered"] += 1
                res[i] = rows
    return {u["id"]: res.get(u["id"], []) for u in units}


def nearest(spans, pos):
    return min(spans, key=lambda a: abs(a[0] - pos))


def loose(value, sents):
    """All the value's words in one sentence, any order, every number exact -> the sentence's index, else None."""
    nums, words = set(NUMBER.findall(value)), set(WORD.findall(NUMBER.sub(" ", value).lower()))
    if not nums and len(words) < 2:
        return None
    for i, t in enumerate(sents):
        if nums <= set(NUMBER.findall(t)) and words <= set(WORD.findall(t.lower())):
            return i
    return None


class Tree:
    def __init__(self):
        self.species, self.phrases, self.nodes, self.facts = {}, {}, {}, {}
        self.index = {}
        self.count = collections.Counter()

    def leaf(self, pid, text, passage, s, cat=""):
        self.species.setdefault(s, {"phrases": []})["phrases"].append(pid)
        self.phrases[pid] = {"text": text, "passage": passage, "species": [s], "cat": cat, "facts": []}

    def node(self, role, text, phrase, start, check):
        k = (role, phrase, start, text.lower())
        if start is not None and k in self.index:
            return self.index[k]
        nid = f"n{len(self.nodes)}"
        self.nodes[nid] = {"role": role, "text": text, "phrase": phrase, "start": start, "check": check, "facts": []}
        if start is not None:
            self.index[k] = nid
        return nid

    def fact(self, phrase, parts, **meta):
        fid = f"f{len(self.facts)}"
        self.facts[fid] = dict(meta, phrase=phrase, parts=parts)
        self.phrases[phrase]["facts"].append(fid)
        for nid in parts.values():
            self.nodes[nid]["facts"].append(fid)
        return fid

    def owner_leaf(self, phrase, s):
        """A phrase with a fact of another species hangs under that species too."""
        ph = self.phrases[phrase]
        if s and s not in ph["species"]:
            ph["species"].append(s)
            self.species.setdefault(s, {"phrases": []})["phrases"].append(phrase)


def at(unit, pos):
    """(phrase id, position inside the phrase) of a position in a unit's text."""
    for pid, a, b in unit["phrases"]:
        if a <= pos < b:
            return pid, pos - a
    pid, a, _b = unit["phrases"][-1]
    return pid, max(0, pos - a)


def place_value(tr, unit, group, row):
    """-> (unit, value text, position or None, unit text from the value, phrase, check). Code only."""
    v, u_from_v = row["value"], ""
    if not v:                                              # a type or unit alone: on the tree, no row
        return unit, "", None, "", unit["phrases"][0][0], "no value"
    for un in [unit] + [x for x in group if x is not unit]:
        apart = pr.number_and_unit(v, un["text"])
        val, ut = apart if apart else (v, "")
        spans = pr.v1._printed(val, un["text"])
        if spans:
            if un is not unit:
                tr.count["value moved to the passage that prints it"] += 1
            return un, val, spans, ut, None, "printed"
    i = loose(v, [t for _p, t in unit["sents"]])
    if i is not None:
        tr.count["value loose (all its words in one sentence)"] += 1
        return unit, v, None, u_from_v, unit["sents"][i][0], "loose"
    tr.count["value not printed"] += 1
    return unit, v, None, u_from_v, unit["phrases"][0][0], "not printed"


def place(tr, unit, group, s, row, cursor, sx="", extra=None, reread=None):
    """One gemma answer -> nodes and a fact on the tree. Returns (passage, flat fact, why or '', new cursor)."""
    un, val, spans, ut, phrase, check = place_value(tr, unit, group, row)
    if spans:
        a, b = next((x for x in spans if x[0] >= cursor), spans[0])
        cursor, pos = b, a
        phrase, start = at(un, a)
    else:
        pos, start = 0, None
        for pid, a, _b in un["phrases"]:
            if pid == phrase:
                pos = a
    parts = {}
    if val:
        parts["value"] = tr.node("value", val, phrase, start, check)
    if row["what"]:
        sp = pr.v1._printed(row["what"], un["text"])
        if sp:
            ph, st = at(un, nearest(sp, pos)[0])
            parts["type"] = tr.node("type", row["what"], ph, st, "printed")
        else:                                              # the model's own name ('altitude' for '1200 m')
            parts["type"] = tr.node("type", row["what"], phrase, None, "named by the model")
    unit_text = row["unit"] or ut
    if unit_text:
        sp = pr.v1._printed(unit_text, un["text"])
        if sp:
            ph, st = at(un, nearest(sp, pos)[0])
            parts["unit"] = tr.node("unit", unit_text, ph, st, "printed")
            if ph != phrase:
                tr.count["unit linked from another phrase of the passage"] += 1
        else:
            leaves = tr.species[s]["phrases"]
            here = leaves.index(phrase) if phrase in leaves else 0
            for q in leaves[here::-1] + leaves[here + 1:]:
                sq = pr.v1._printed(unit_text, tr.phrases[q]["text"])
                if sq:
                    parts["unit"] = tr.node("unit", unit_text, q, sq[0][0], "printed in another phrase of the species")
                    tr.count["unit linked from another passage of the species"] += 1
                    break
            else:
                parts["unit"] = tr.node("unit", unit_text, phrase, None, "not printed")
                tr.count["unit not printed anywhere in the species"] += 1
    sex = (row["sex"] or sx).strip().lower()
    if sex in SEX:
        ms = list(SEX[sex].finditer(un["text"]))
        before = [m for m in ms if m.start() <= pos]
        m = before[-1] if before else (min(ms, key=lambda x: abs(x.start() - pos)) if ms else None)
        if m:
            ph, st = at(un, m.start())
            parts["sex"] = tr.node("sex", sex, ph, st, "printed")
        else:
            parts["sex"] = tr.node("sex", sex, phrase, None, "said by the model")
    who_bad = bool(row["who"]) and not printed(row["who"], un["text"])
    if row["who"]:
        parts["who"] = tr.node("who", row["who"], phrase, None, "not printed" if who_bad else "printed")
    for role, nid in (extra or {}).items():
        parts[role] = nid
    fid = tr.fact(phrase, parts, check=check, reread=reread)
    tr.count[f"facts: {check}"] += 1
    unit_ok = "unit" in parts and tr.nodes[parts["unit"]]["check"] != "not printed"
    flat = {"who": row["who"], "sex": sex if sex in SEX else "", "what": row["what"], "value": val,
            "unit": unit_text if unit_ok else "", "fact_id": fid, "phrase": phrase, "check": check}
    if reread:
        flat["reread"] = reread
    why = ("value not printed in the passage" if check == "not printed"
           else "who not printed in the passage" if who_bad else "")
    return un["passage"], flat, why, cursor


def put(read, passage, flat, why):
    if not flat["what"] or not flat["value"]:              # stays on the tree only: a row needs both
        return
    r = read.setdefault(passage, {"names": [], "facts": [], "dropped": []})
    if why:
        r["dropped"].append(dict(flat, why=why))
    else:
        r["facts"].append(flat)


def stage_treeread(papers):
    (OUT / "tree").mkdir(parents=True, exist_ok=True)
    (OUT / "read2").mkdir(parents=True, exist_ok=True)
    for p in papers:
        f = OUT / "tree" / f"{p}.json"
        if f.exists():
            continue
        t0 = time.time()
        rd = json.loads((pr.PREV_OUT / "read2" / f"{p}.json").read_text(encoding="utf-8"))
        for k in ("read7_done", "units_done", "log", "triggers", "record_only"):
            rd.pop(k, None)
        for r in rd["read"].values():
            r["facts"], r["dropped"] = [], []
        load = lambda d: json.loads((OUT / d / f"{p}.json").read_text(encoding="utf-8"))
        abbr, span, shape, field = (load("abbrev")["abbreviations"], load("walk")["span"], load("shape")["shape"],
                                    load("field")["field"])
        kept = collections.defaultdict(list)
        for r in json.loads((pr._paths.OUTPUT / "prose_sent" / f"{p}.json").read_text(encoding="utf-8"))["units"]:
            if r.get("cat") != "record list" and r["kept"]:
                kept[r["passage"]].append(r)
        under = lambda u: f", under the heading '{u['heading'][:120]}'" if u["heading"] else ""
        tr, log, trig, record_only = Tree(), {}, collections.Counter(), []
        inside = [u for u in rd["passages"] if u["kind"] == "para" and span.get(u["id"])
                  and shape.get(u["id"]) in ("text", "list")]
        # 1. the leaves, in the paper's order, before anything is read
        text_units, list_units = [], {}
        for u in inside:
            pid, s = u["id"], span[u["id"]]
            if shape.get(pid) == "text":
                if not kept.get(pid):
                    continue
                pos, phr, sents = 0, [], []
                for j, r in enumerate(kept[pid]):
                    q = f"{pid}.s{j}"
                    tr.leaf(q, r["text"], pid, s, r.get("cat", ""))
                    phr.append((q, pos, pos + len(r["text"]) + 1))
                    sents.append((q, r["text"]))
                    pos += len(r["text"]) + 1
                text_units.append({"id": pid, "passage": pid, "text": " ".join(r["text"] for r in kept[pid]),
                                   "phrases": phr, "sents": sents, "u": u, "s": s})
            else:
                items, plog = pr.list_items(u)
                trig.update({f"pointers: {k}": v for k, v in plog.items()})
                if len(items) < 2:
                    q = f"{pid}.s0"
                    tr.leaf(q, u["text"], pid, s, "record list")
                    list_units[pid] = [{"id": pid, "passage": pid, "text": u["text"], "s": s, "u": u,
                                        "phrases": [(q, 0, len(u["text"]) + 1)], "sents": [(q, u["text"])]}]
                    log[pid] = {"items": len(items), "kept": "passage reading"}
                    continue
                us = []
                for k, t in enumerate(items):
                    q = f"{pid}#{k}"
                    tr.leaf(q, t, pid, s, "record")
                    us.append({"id": q, "passage": pid, "text": t, "s": s, "u": u,
                               "phrases": [(q, 0, len(t) + 1)], "sents": [(q, t)], "item": True})
                list_units[pid] = us
                log[pid] = {"items": len(items)}
        # 2. reading: same calls as v8b (same account, same question, up to READ_CHARS)
        read = rd["read"]
        groups, cur = [], []
        for x in text_units:
            k = (x["s"], field.get(x["id"], "other"))
            if cur and (cur[0][1] != k or sum(len(y["text"]) for y, _k in cur) + len(x["text"]) > pr.READ_CHARS):
                groups.append(cur)
                cur = []
            cur.append((x, k))
        groups += [cur] if cur else []

        def text_read(g_units, tpl, s, where, tag=None):
            got = read_raw(tpl, g_units, s, abbr, where)
            for x in g_units:
                cursor = 0
                for row in got[x["id"]]:
                    passage, flat, why, cursor = place(tr, x, g_units, s, row, cursor, reread=tag)
                    put(read, passage, flat, why)
            return got

        for g in groups:
            us = [x for x, _k in g]
            s, kind = g[0][1]
            tpl = MEASURE if kind == "measure" else DESCRIBE
            got = text_read(us, tpl, s, under(us[0]["u"]))
            for x in us:                                   # T2: a long run that gave nothing is read again alone
                if kind != "measure" and len(x["text"]) >= 200 and not got[x["id"]]:
                    trig["T2 fired"] += 1
                    trig["T2 answers"] += len(text_read([x], tpl, s, under(x["u"]), "T2")[x["id"]])
        for pid, us in list_units.items():
            s, where = us[0]["s"], under(us[0]["u"])
            if not us[0].get("item"):
                text_read(us, DESCRIBE, s, where)
                continue

            def items_read(chunk, tag=None):
                got = read_raw(ITEM, chunk, s, abbr, where, what="items of one list")
                for x in chunk:
                    t, ph = x["text"], x["id"]
                    sx = "male" if "♂" in t and "♀" not in t else "female" if "♀" in t and "♂" not in t else ""
                    name = lambda r: r["what"].strip().lower().replace("_", " ")
                    extra, loc, coord, others, cursor = {}, [], [], [], 0
                    for r in got[x["id"]]:
                        if name(r) == "sex":
                            continue
                        role = "place" if name(r) in pr.RECORD_LOC else "coords" if name(r) in pr.RECORD_COORD else ""
                        if role and printed(r["value"], t):
                            extra[role] = tr.node(role, r["value"], ph, pr.v1._printed(r["value"], t)[0][0], "printed")
                            (loc if role == "place" else coord).append(r["value"])
                        else:
                            others.append(r)
                    if not others and extra:
                        tr.fact(ph, dict(extra), check="printed", reread=tag)
                        record_only.append({"item": t[:200], "locality": loc, "coordinates": coord})
                    for r in others:
                        passage, flat, why, cursor = place(tr, x, [x], s, r, cursor, sx=sx, extra=extra, reread=tag)
                        if loc:
                            flat["locality"] = "; ".join(loc)
                        if coord:
                            flat["coordinates"] = ", ".join(coord)
                        put(read, passage, flat, why)
                return got

            empty = []
            for k in range(0, len(us), pr.ITEMS_PER_CALL):
                chunk = us[k:k + pr.ITEMS_PER_CALL]
                got = items_read(chunk)
                empty += [x for x in chunk if not got[x["id"]]]
            if empty:
                trig["T3 fired"] += len(empty)
                trig["T3 answers"] += sum(len(v) for v in items_read(empty, "T3").values())
        trig["items with only place fields (no row)"] = len(record_only)
        rd.update(read=read, log=log, triggers=dict(trig), record_only=record_only, tree_done=True)
        (OUT / "read2" / f"{p}.json").write_text(json.dumps(rd, indent=1, ensure_ascii=False), encoding="utf-8")
        f.write_text(json.dumps(dump(tr), indent=1, ensure_ascii=False), encoding="utf-8")
        shared = sum(1 for n in tr.nodes.values() if len(n["facts"]) > 1)
        print(f"  [treeread] {p:20s} {len(tr.species)} species, {len(tr.phrases)} phrases, {len(tr.facts)} facts, "
              f"{len(tr.nodes)} nodes ({shared} shared); {dict(tr.count)}; {dict(trig)} ({time.time() - t0:.0f}s)", flush=True)
    pr.v1.unload(pr.v1.GEMMA)


def dump(tr):
    return {"species": tr.species, "phrases": tr.phrases, "nodes": tr.nodes, "facts": tr.facts, "count": tr.count}


def view(t):
    """The tree as indented text, each node on its own line, only the nodes a fact has."""
    out = []
    for s, sp in t["species"].items():
        out.append(s)
        for q in sp["phrases"]:
            ph = t["phrases"][q]
            out.append(f"    [{q}] {ph['text'][:300]}")
            for fid in ph["facts"]:
                fa = t["facts"][fid]
                if fa.get("owner") and fa["owner"] != s:
                    out.append(f"        ({fid} is of {fa['owner']})")
                    continue
                pad = "        "
                note = f"  <-- no row: {fa.get('why') or fa['check']}" if fa.get("why") or fa["check"] == "not printed" else ""
                for role in ROLES:
                    nid = fa["parts"].get(role)
                    if not nid:
                        continue
                    n = t["nodes"][nid]
                    far = f"  (printed in {n['phrase']})" if n["phrase"] != q else ""
                    shared = f"  (shared by {len(n['facts'])} facts)" if len(n["facts"]) > 1 else ""
                    flag = "" if n["check"] in ("printed", "printed in another phrase of the species") else f"  [{n['check']}]"
                    out.append(f"{pad}{role}: {n['text']}{far}{shared}{flag}{note}")
                    pad += "    "
                    note = ""
        out.append("")
    return "\n".join(out)


def stage_treefinal(papers):
    """nimble's decisions (facts stage) written back on the tree: the owner of each fact, why it gives no row; a phrase
    with a fact of another species hangs under that species too; a described place's facts join the phrase."""
    (OUT / "tree_view").mkdir(parents=True, exist_ok=True)
    for p in papers:
        f = OUT / "tree" / f"{p}.json"
        t = json.loads(f.read_text(encoding="utf-8"))
        if t.get("count_final") is not None:               # decisions already written: only the view is left
            (OUT / "tree_view" / f"{p}.txt").write_text(view(t), encoding="utf-8")
            continue
        tr = Tree()
        tr.species, tr.phrases, tr.nodes, tr.facts = t["species"], t["phrases"], t["nodes"], t["facts"]
        c = collections.Counter()
        for x in json.loads((OUT / "facts" / f"{p}.json").read_text(encoding="utf-8"))["facts"]:
            fid = x.get("fact_id")
            if fid:
                fa = tr.facts[fid]
                fa.update(owner=x.get("owner"), why=x.get("why") or "")
                if x.get("owner") and not x.get("why"):
                    tr.owner_leaf(fa["phrase"], x["owner"])
                    c["kept"] += 1
                continue
            if x.get("owner") and not x.get("why") and x.get("place"):
                q = next((q for q, ph in tr.phrases.items() if ph["passage"] == x["passage"]), None)
                if q:
                    parts = {"type": tr.node("type", x["what"], q, None, f"from the place {x['place']}"),
                             "value": tr.node("value", x["value"], q, None, f"from the place {x['place']}")}
                    tr.fact(q, parts, check="printed", owner=x["owner"], why="", place=x["place"])
                    c["from a described place"] += 1
        t["count_final"] = c
        t["two_species_phrases"] = sum(1 for ph in tr.phrases.values() if len(ph["species"]) > 1)
        f.write_text(json.dumps(t, indent=1, ensure_ascii=False), encoding="utf-8")
        (OUT / "tree_view" / f"{p}.txt").write_text(view(t), encoding="utf-8")
        print(f"  [treefinal] {p:20s} {dict(c)}; phrases under 2+ species: {t['two_species_phrases']}", flush=True)


if __name__ == "__main__":
    stage, *rest = sys.argv[1:]
    if "tree" not in pr.FL:
        sys.exit("run with PROSE_VARIANT=t1")
    papers = pr.papers_of(rest)
    pr.setup()
    {"treeread": stage_treeread, "treefinal": stage_treefinal}[stage](papers)
    if GEN["calls"]:
        print(f"  [gemma] {stage}: " + ", ".join(f"{k} {v:.0f}" for k, v in GEN.items()), flush=True)
