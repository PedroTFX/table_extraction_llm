"""
prose_judge.py — the judging done by hand on the dev prose papers (2026-11-06), as a program, so papers nobody may
look at can be judged. It reads our rows, the GT and the paper's own text; it uses nothing from the reader's stages.
For held_b it prints TOTALS ONLY: no paper name, row, quote or per-paper number.

GT side, each GT row is one of:
    exact    same species (genus initial + epithet), same value, trait names that share their words
    same     the same information: same value under a related name; a value with only its figure reference or leading
             verb different; our value wider, or the GT's field found as our parts (70% of its words); a GT number not
             printed in the paper when ours is near it and printed (a GT typo)
    partial  35-70% of the field found as parts
    repeat   the value is in our rows, but we wrote fewer rows than the GT asks (one per record)
    miss     not found
Our side, each row without a GT partner is one of:
    unprinted  its value is in no line of the paper
    wrong      printed, but neither in this species' account nor on a line naming it; or nimble is sure, in both orders,
               that a sentence naming another organism says it of that organism
    form       a place or coordinates written as a trait row
    junk       nimble is sure, in both orders, that 'trait: value' is no characteristic of an organism
    ok         printed where it belongs. This does NOT prove it right: it can't tell a true fact from a misread one.

    recall = (exact + same) / GT rows      precision = (our rows - unprinted - wrong - form - junk) / our rows

    PROSE_VARIANT=t2 python prose_judge.py dev|held_b [gold labels file: agreement with the hand judgement, dev only]
"""
import collections
import csv
import difflib
import json
import re
import sys

import prose_reader as pr                                  # first: it sets up the paths
import prose_test as pt
import duels

WORD = re.compile(r"[a-z0-9]+(?:[.,][0-9]+)?")
FIG = re.compile(r"\(\s*figs?\.?[^)]*\)|\bfigs?\.?\s*\d+[a-z]?\b", re.I)
LEAD = {"the", "they", "it", "is", "are", "has", "have", "with", "measure", "measures", "bear", "bears", "appear", "appears",
        "exhibit", "exhibits", "feature", "features", "a", "an", "he", "habitat"}
BINOM = re.compile(r"^[#*_\s]*([A-Z][a-z]+)\s+(?:\([A-Z][a-z]+\)\s+)?([a-z]{3,})\b")
NOT_EPITHET = {"species", "new", "material", "group", "genus", "and", "the", "for", "from", "specimens", "records", "with"}
CLOSE = re.compile(r"key to|identification key|\bkeys?\b|references?|literature cited|acknowledg|discussion|conclusion|appendix|"
                   r"other species|introduction|methods|abstract|checklist|supplementary", re.I)
FORM = re.compile(r"^(type )?(locality|location|region|area|coordinates?|latitude|longitude|collecting place|collection.?location|"
                  r"location of collection|new species location)\b", re.I)
Q_JUNK = "What does a scientific paper give here?"
JUNK = {"trait": "a characteristic of the organism: its body, size, colour, structures, sexes, life, food or host plants, "
                 "habitat, or where it lives",
        "other": "no characteristic: a person's name, a place or camp name in the wrong field, a way of collecting, a specimen "
                 "count or label, or a remark about names, the paper or the study"}
Q_OWNER = "Of which organism does this sentence state it?"


def words(s):
    return WORD.findall(str(s or "").lower())


norm = lambda s: " " + " ".join(words(s)) + " "


def clean(s):
    w = words(FIG.sub(" ", str(s or "")))
    while w and w[0] in LEAD:
        w = w[1:]
    return " ".join(w)


def related(a, b):
    st = lambda s: {x.rstrip("s") for x in words(s)} - pt.STOP - {"morphology", "colour", "color", "type"}
    ta, tb = st(a), st(b)
    return bool(ta & tb) or any(difflib.SequenceMatcher(None, x, y).ratio() >= .8 for x in ta for y in tb if len(x) > 3 and len(y) > 3)


def is_num(v):
    return bool(v) and not re.search(r"[a-z]{3}", str(v).lower())


def read_paper(p):
    """Each line of the paper's text with the species account it sits in, found from its headings alone."""
    raw = (pr._paths.PAPERS / p / f"{p}_full.md").read_text(encoding="utf-8", errors="ignore")
    cur, lines = None, []
    for l in raw.split("\n"):
        s = l.strip()
        if not s:
            continue
        head = s.startswith("#") or (len(s) <= 120 and s[0] in "*_")
        m = BINOM.match(s)
        if head and m and m.group(2) not in NOT_EPITHET:
            cur = pt.key(f"{m.group(1)} {m.group(2)}")
        elif s.startswith("#") and CLOSE.search(s):
            cur = None
        lines.append({"text": s, "n": norm(s), "acct": cur})
    return lines, " ".join(x["n"] for x in lines)


def judge_gt(gt, us, whole):
    """GT rows -> labels; marks the rows of ours paired with a GT row (only exact and same pairs use one up)."""
    pool, used = collections.defaultdict(list), set()
    for i, r in enumerate(us):
        pool[pt.key(r["sp"])].append(i)
    labels = [None] * len(gt)
    for j, g in enumerate(gt):
        i = next((i for i in pool[pt.key(g["sp"])] if i not in used and pt.nv(us[i]["v"]) == pt.nv(g["v"])
                  and (not g["t"] or pt.same_trait(g["t"], us[i]["t"]))), None)
        if i is not None:
            used.add(i)
            labels[j] = "exact"

    def take(i, lab="same"):
        if i in used:
            return "repeat"
        used.add(i)
        return lab

    for j, g in enumerate(gt):
        if labels[j]:
            continue
        rows = pool[pt.key(g["sp"])]
        a, f, cg, gw = pt.nv(g["v"]), norm(g["v"]), clean(g["v"]), words(g["v"])
        if not a:
            labels[j] = "no value"
            continue
        rel = [i for i in rows if related(g["t"], us[i]["t"]) or not g["t"]]
        if is_num(g["v"]):
            eq = next((i for i in rel if pt.nv(us[i]["v"]) == a), None)
            if eq is not None:
                labels[j] = take(eq)
            elif f not in whole and rel and max(difflib.SequenceMatcher(None, a, pt.nv(us[i]["v"])).ratio() for i in rel) >= .75:
                labels[j] = take(max(rel, key=lambda i: difflib.SequenceMatcher(None, a, pt.nv(us[i]["v"])).ratio()))
            elif any(f in norm(us[i]["v"]) for i in rel):
                labels[j] = "repeat"
            elif any(pt.nv(us[i]["v"]) == a for i in rows):
                labels[j] = "repeat"
            else:
                labels[j] = "miss"
            continue
        eq = next((i for i in rows if (pt.nv(us[i]["v"]) == a or clean(us[i]["v"]) == cg) and (len(gw) >= 2 or i in rel)), None)
        if eq is not None:
            labels[j] = take(eq)
            continue
        wider = next((i for i in rows if f in norm(us[i]["v"]) and (i in rel or len(gw) >= 4)), None)
        if wider is not None:
            labels[j] = take(wider)
            continue
        have, pieces = set(), 0
        for i in rows:
            n = norm(us[i]["v"])
            nw = words(us[i]["v"])
            if n.strip() and n in f and (i in rel or len(nw) >= 4) and (len(nw) >= 2 or i in rel):
                have |= set(nw)
                pieces += 1
        cover = len(have & set(gw)) / max(1, len(set(gw)))
        near = max((difflib.SequenceMatcher(None, a, pt.nv(us[i]["v"])).ratio() for i in rel), default=0)
        if cover >= .7 or near >= .85:
            labels[j] = "same"
        elif cover >= .35:
            labels[j] = "partial"
        else:
            labels[j] = "miss"
    return labels, used


def judge_extra(r, lines, ask, cache):
    """A row of ours without a GT partner -> label."""
    k, v = pt.key(r["sp"]), str(r["v"])
    f, epi = norm(v), (k.split()[-1] if k else "")
    hits = [x for x in lines if f in x["n"]]
    if not hits:
        nums, ws = set(re.findall(r"\d+(?:[.,]\d+)?", v)), {w for w in words(re.sub(r"\d+(?:[.,]\d+)?", " ", v)) if len(w) > 2}
        hits = [x for x in lines if nums <= set(re.findall(r"\d+(?:[.,]\d+)?", x["text"])) and ws <= set(words(x["text"]))]
        if not hits:
            return "unprinted"
    named = [x for x in hits if re.search(rf"\b{re.escape(epi)}\b", x["text"].lower())] if epi else []
    if not named and not any(x["acct"] == k for x in hits):
        return "wrong"
    if FORM.match(str(r["t"]).strip()):
        return "form"
    st = f"A scientific paper about {r['sp']} gives '{r['t']}: {v[:200]}'."
    key = ("junk", st)
    if key not in cache:
        ch, pr1 = ask(st, Q_JUNK, dict(JUNK))
        bad = duels.sure(ch, pr1, "other") == "other"
        if bad:
            ch2, pr2 = ask(st, Q_JUNK, {"b": JUNK["other"], "a": JUNK["trait"]})
            bad = duels.sure(ch2, pr2, "b") == "b"
        cache[key] = bad
    if cache[key]:
        return "junk"
    sent = next((s for x in hits if x["acct"] == k or x in named for s in re.split(r"(?<=[.;])\s+", x["text"]) if f in norm(s)), "")
    other = {m.group(0) for m in re.finditer(r"\b[A-Z][a-z]*\.?\s[a-z]{4,}\b", sent) if pt.key(m.group(0)) != k
             and re.match(r"[A-Z]\.\s", m.group(0)) and m.group(0).split()[-1] != epi}
    if other:
        o = sorted(other)[0]
        st = f"In the account of {r['sp']}, a scientific paper says:\n\"\"\"{sent[:700]}\"\"\"\nIt gives '{r['t']}: {v[:150]}'."
        key = ("owner", st)
        if key not in cache:
            ch, pr1 = ask(st, Q_OWNER, {"this": f"of {r['sp']}", "other": f"of {o}"})
            bad = duels.sure(ch, pr1, "other") == "other"
            if bad:
                ch2, pr2 = ask(st, Q_OWNER, {"b": f"of {o}", "a": f"of {r['sp']}"})
                bad = duels.sure(ch2, pr2, "b") == "b"
            cache[key] = bad
        if cache[key]:
            return "wrong"
    return "ok"


def our_rows(p):
    f = pr.OUT / "prose" / p / f"{p}.csv"
    return [{"sp": r["verbatimIdentification"], "t": r["measurementType"], "v": r["measurementValue"]}
            for r in csv.DictReader(open(f, encoding="utf-8"))] if f.exists() else []


def scores(c):
    gt = c["exact"] + c["same"] + c["partial"] + c["repeat"] + c["miss"]
    bad = c["unprinted"] + c["wrong"] + c["form"] + c["junk"]
    R, P = (c["exact"] + c["same"]) / max(1, gt), (c["rows"] - bad) / max(1, c["rows"])
    return R, P, 2 * P * R / max(1e-9, P + R), gt


if __name__ == "__main__":
    group, gold_file = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "")
    if gold_file and group != "dev":
        sys.exit("agreement with hand labels exists for dev only")
    papers = pr.papers_of([group])
    ask, cache, total = pr.Ask(), {}, collections.Counter()
    gold = collections.defaultdict(list)
    if gold_file:
        for x in json.load(open(gold_file, encoding="utf-8")):
            gold[(x["paper"], x["side"], pt.key(x["sp"]), x["t"], x["v"])].append(x["label"])
    conf, wrongs = collections.Counter(), []
    for p in papers:
        gt, us = [g for g in pt.gt_rows(p)], our_rows(p)
        lines, whole = read_paper(p)
        labels, used = judge_gt(gt, us, whole)
        c = collections.Counter(labels)
        c["rows"] = len(us)
        for g, lab in zip(gt, labels):
            h = gold.get((p, "gt", pt.key(g["sp"]), g["t"], g["v"]))
            if h:
                hand = h.pop()
                conf[("gt", hand, lab)] += 1
                if hand != lab:
                    wrongs.append(f"{p[:4]} GT hand={hand} code={lab} | {g['t'][:28]} | {g['v'][:90]}")
        for i, r in enumerate(us):
            if i in used:
                continue
            lab = judge_extra(r, lines, ask, cache)
            c[lab] += 1
            h = gold.get((p, "us", pt.key(r["sp"]), r["t"], r["v"]))
            if h:
                hand = h.pop()
                conf[("us", hand, lab)] += 1
                if hand != lab:
                    wrongs.append(f"{p[:4]} OURS hand={hand} code={lab} | {r['sp'][:18]} | {r['t'][:24]} | {r['v'][:80]}")
        total.update(c)
        if group == "dev":
            R, P, F, n = scores(c)
            print(f"  {p:18s} R {R:.3f} P {P:.3f} F1 {F:.3f}; {dict(c)}", flush=True)
    ask.unload()
    R, P, F, n = scores(total)
    print(f"prose judge ({pr.OUT.name}) on {group}: {len(papers)} papers, totals only")
    print(f"  recall {R:.3f}  precision {P:.3f}  F1 {F:.3f}")
    print(f"  GT rows {n}: exact {total['exact']}, same {total['same']}, partial {total['partial']}, repeat {total['repeat']}, "
          f"miss {total['miss']}, no value {total['no value']}")
    print(f"  our rows {total['rows']}: unprinted {total['unprinted']}, wrong {total['wrong']}, form {total['form']}, "
          f"junk {total['junk']}, ok {total['ok']}")
    if gold_file:
        for side in ("gt", "us"):
            cells = {k[1:]: v for k, v in conf.items() if k[0] == side}
            agree, tot = sum(v for k, v in cells.items() if k[0] == k[1]), sum(cells.values())
            print(f"  agreement with the hand labels, {side}: {agree}/{tot} ({agree / max(1, tot):.1%})")
            for k, v in sorted(cells.items()):
                print(f"    hand {k[0]:8s} code {k[1]:9s} {v}")
        print("\n".join(wrongs))
