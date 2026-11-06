"""
sentence_test.py — EXPERIMENT (2026-11-05): can nimble sort the sentences before gemma reads anything?
No gemma here. The papers' passages, shapes (caption / list / text) and species tracking come from prose_v7a.

  sentences (code)   running-text passages inside an account cut at sentence ends ('. ' before a capital, not
                     after an initial or a short abbreviation); a fragment under 25 characters joins the next
  Q-ABOUT (nimble)   about the organism, or about records, literature, names, the study? Dropped only on a
                     sure 'other' in both orders; not sure keeps the sentence
  Q-CAT (nimble)     one category for each sentence kept (measurement, description, distribution, habitat,
                     host or food, life, comparison); under SURE counts as 'unsure'
  list passages      kept whole as 'record list' (their items are read one by one anyway)
  measure            GT rows whose value is printed in a sentence of its species' account: all sentences
                     (the ceiling) against sentences kept; characters dropped; each trait's categories

    python sentence_test.py dev            -> output/prose_sent/<paper>.json, totals printed
"""
import collections
import json
import re
import sys
import time

import prose_reader as pr
import prose_test as pt
import duels

OUT = pr.SENT_DIR
ABBR = {"fig", "figs", "alt", "sp", "spp", "nov", "coll", "leg", "det", "cf", "ca", "vs", "al", "prov", "vill", "mt",
        "st", "nat", "res", "no", "dr", "prof", "var", "ssp", "subsp", "tab", "e.g", "i.e", "approx"}
END = re.compile(r"[.!?]\**\s+(?=[*\"“(\[]*[A-Z♂♀])")

Q_ABOUT = "What is this sentence about?"
ABOUT = {"organism": "the organism itself: its body, size, colour, structures, sexes, life, behaviour, food, hosts, "
                     "habitat, or where it lives or was found",
         "other": "something else: how a record or specimen was published, identified or is doubtful, the literature, "
                  "names and taxonomy, what the authors did or conclude, or a figure"}
Q_CAT = "What kind of information does this sentence give about the organism?"
CATS = {"measurement": "measurements: labels or body parts with numbers or ranges",
        "description": "a description of the body or its parts in words: shape, colour, structures, genitalia",
        "distribution": "the countries or regions where the organism occurs",
        "habitat": "the habitat or environment where it lives or was found",
        "host_food": "its food, prey, host plants or hosts",
        "life": "its life or behaviour: activity, season, reproduction, nesting",
        "comparison": "how it differs from or resembles another species"}


def sentences(t):
    """A passage's sentences, geometry only."""
    cuts, out = [0], []
    for m in END.finditer(t):
        before = re.findall(r"[\w.]+", t[:m.start()])[-1:] or [""]
        w = before[0].rstrip(".").lower()
        if w in ABBR or re.fullmatch(r"[A-Za-z]", before[0].rstrip(".")):   # 'Figs. 3', 'T. acerosus'
            continue
        cuts.append(m.end())
    parts = [t[a:b].strip() for a, b in zip(cuts, cuts[1:] + [len(t)])]
    for x in parts:
        if out and len(out[-1]) < 25:
            out[-1] = out[-1] + " " + x
        elif x:
            out.append(x)
    return out


norm = lambda s: " " + " ".join(re.findall(r"[a-z0-9]+(?:[.,][0-9]+)?", str(s or "").lower())) + " "


def forms(v):
    n = norm(v).strip()
    if not n or (len(n) < 2 and n.isdigit()):
        return None
    w = n.split()
    return " " + " ".join(w[:8]) + " "


def run(papers):
    OUT.mkdir(parents=True, exist_ok=True)
    ask = pr.Ask()
    totals = collections.Counter()
    for p in papers:
        t0 = time.time()
        ps = pr.passages(p)
        span = json.loads((pr.OUT / "walk" / f"{p}.json").read_text(encoding="utf-8"))["span"]
        shape = json.loads((pr.OUT / "shape" / f"{p}.json").read_text(encoding="utf-8"))["shape"]
        units = []
        for u in ps:
            s = span.get(u["id"])
            if u["kind"] != "para" or not s or shape.get(u["id"]) == "caption":
                continue
            if shape.get(u["id"]) == "list":
                units.append({"passage": u["id"], "account": s, "text": u["text"], "kept": True, "cat": "record list",
                              "label": u.get("label", "")})
                continue
            sn = sentences(u["text"])
            for i, x in enumerate(sn):
                around = " ".join(sn[max(0, i - 1):i + 2])[:900]
                st = (f"In the account of {s} in a scientific paper, under the heading '{u['heading'][:80]}', a passage "
                      f"reads:\n\"\"\"{around}\"\"\"\nThe sentence in question is:\n\"\"\"{x[:900]}\"\"\"")
                rec = {"passage": u["id"], "account": s, "text": x, "label": u.get("label", "")}
                ch, pr1 = ask(st, Q_ABOUT, dict(ABOUT))
                rec["about"] = [ch, pr1]
                drop = duels.sure(ch, pr1, "other") == "other"
                if drop:                                   # both orders before a sentence is dropped
                    ch2, pr2 = ask(st, Q_ABOUT, {"b": ABOUT["other"], "a": ABOUT["organism"]})
                    rec["about2"] = [ch2, pr2]
                    drop = duels.sure(ch2, pr2, "b") == "b"
                rec["kept"] = not drop
                if not drop:
                    ch3, pr3 = ask(st, Q_CAT, dict(CATS))
                    rec["cat"] = ch3 if duels.sure(ch3, pr3, *CATS) else "unsure"
                    rec["cat_read"] = [ch3, pr3]
                units.append(rec)
        for r in units:
            r["n"] = norm(r["text"])
        by_sp = collections.defaultdict(list)
        for r in units:
            by_sp[pt.key(r["account"])].append(r)
        gt = pt.gt_rows(p)
        lost, seen = [], collections.Counter()
        cross = collections.defaultdict(collections.Counter)
        for g in gt:
            f = forms(g["v"])
            if not f:
                seen["no value"] += 1
                continue
            hits = [r for r in by_sp.get(pt.key(g["sp"]), []) if f in r["n"]]
            if not hits:
                seen["not in any sentence of its account"] += 1
                continue
            seen["in the account"] += 1
            kept = [r for r in hits if r["kept"]]
            if kept:
                seen["in a kept sentence"] += 1
                cross[g["t"] or "(no name)"][kept[0]["cat"]] += 1
            else:
                lost.append({"trait": g["t"], "value": g["v"][:80], "species": g["sp"][:40], "sentence": hits[0]["text"][:220]})
        sents = [r for r in units if r.get("cat") != "record list"]
        ch_all = sum(len(r["text"]) for r in units)
        ch_kept = sum(len(r["text"]) for r in units if r["kept"])
        cats = collections.Counter(r.get("cat", "dropped") for r in units)
        for r in units:
            r.pop("n")
        (OUT / f"{p}.json").write_text(json.dumps({"units": units, "lost": lost, "cross": cross, "seen": seen},
                                                  indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"\n== {p}: {len(sents)} sentences + {len(units) - len(sents)} list passages; dropped "
              f"{sum(1 for r in units if not r['kept'])}; characters kept {ch_kept} of {ch_all} ({ch_kept / max(1, ch_all):.0%}) "
              f"({time.time() - t0:.0f}s)", flush=True)
        print(f"   GT rows {len(gt)}: {dict(seen)}; lost {len(lost)}", flush=True)
        print(f"   categories: {dict(cats)}", flush=True)
        totals.update(seen)
        totals["lost"] += len(lost)
    print("\ntotals:", dict(totals), flush=True)
    ask.unload()


if __name__ == "__main__":
    run(pr.papers_of(sys.argv[1:]))
