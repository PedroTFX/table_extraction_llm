"""
meaning_bench.py — TEST the meaning step (meaning.py) on the header bench's
held-out tables, and let nimble judge synonyms when scoring.

Names are scored as in header_tree_bench (a column's name, or a group label, or
group + name, matches the GT trait), now also accepting:
  finder    the first definition the pipeline's finder gives (code only)
  meaning   the meaning nimble chose among the paper's definitions (QM)
  synonyms  QS2, asked by the scorer for every remaining miss: does the column's
            name (and its meaning) name the same trait as the GT trait? The GT
            names traits its own way ('Drought Resistance' for the paper's 'Dry
            tolerant'); nimble decides whether that is the same trait. The same
            question is asked for gemma's names, so the comparison stays fair.

    python meaning_bench.py            # collect (nimble) + score
    python meaning_bench.py --score    # score only, from the stored answers
-> tree_extraction/output/meaning_bench/{meanings.json, synonyms.json, summary.txt}
"""

from __future__ import annotations

import collections
import json
import sys

import _paths
import column_role_bench as crb
import column_tree as ct
import header_tree as ht
import header_tree_bench as hb
import meaning as mn
from evaluate import load_xlsx

OUT = _paths.OUTPUT / "meaning_bench"
HEAD = hb.OUT / "experiments" / "step_on.json"
MODEL = ("nimble:9b-q4-gpu", 1)         # one question per call
QSYN = {"yes": "yes: the same trait, said in other words",
        "no": "no: different traits"}


def scored_columns(paper, dev=False):
    """(table, col, GT trait, head column, gemma name) for the tables the key draws on."""
    gp = crb.paper_inputs(_paths.PAPERS / paper)
    if not gp:
        return []
    gt = hb.GT(load_xlsx(gp[1]))
    tabs = hb.html_tables(paper)
    head = {e["table"]: e for e in hb._inherit(json.loads(json.dumps(HEADS[paper])))}
    gem = {e["table"]: e for e in GEMMA.get(paper, [])}
    out = []
    for k, e in head.items():
        if ((paper, k) in hb.DEV) != dev:
            continue
        g = ht.grid_from_html(tabs[k])
        key, _unsure = hb.answer_key(g, gt, ht.Symbols.of(g))
        if key is None:
            continue
        for c, (trait, _m) in hb.key_columns(g, gt, key).items():
            if not trait:
                continue
            col = next((x for x in e["columns"] if x["col"] == c), None)
            gname = (gem.get(k, {}).get("names") or {}).get(str(c), "")
            out.append((k, c, trait, col, gname))
    return out


def collect():
    client = ct.DecisionClient(*MODEL)
    path = OUT / "meanings.json"
    res = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    for paper in hb.default_papers():
        if paper in res or paper not in HEADS:
            continue
        rows = scored_columns(paper) + scored_columns(paper, dev=True)
        if not rows:
            continue
        text = mn.paper_text(paper)
        res[paper] = {}
        for k in sorted({r[0] for r in rows}):
            e = next(x for x in hb._inherit(json.loads(json.dumps(HEADS[paper]))) if x["table"] == k)
            m = mn.read_meanings(client, text, e["columns"])
            res[paper][str(k)] = {str(c): v for c, v in m.items()}
            print(f"  {paper} t{k}: " + ", ".join(
                f"{v['name']}->{v['meaning']}" for v in m.values() if v["candidates"])[:300], flush=True)
        OUT.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    return res


def _match(texts, trait):
    return any(t and hb.name_matches(t, trait) for t in texts)


def synonyms(pairs):
    """QS2 for (label, meaning, trait) triples not yet asked."""
    path = OUT / "synonyms.json"
    done = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    todo = [p for p in pairs if "|".join(p) not in done]
    if todo:
        client = ct.DecisionClient(*MODEL)
        for label, meaning, trait in todo:
            state = "Two names for a trait recorded about insects in a scientific study."
            ins = (f"A table column is named '{label}'"
                   + (f" (the paper defines: {meaning})" if meaning else "")
                   + f". A trait list names a trait '{trait}'. Do they name the same trait?")
            a = client.ask(lambda size: state, {"q": {"type": "choice", "instructions": ins,
                                                      "criteria": dict(QSYN)}}).get("q") or {}
            ch = a.get("choice") or "no"
            done["|".join((label, meaning, trait))] = [ch, round(float((a.get("probabilities")
                                                                         or {}).get(ch, 0)), 3)]
            print(f"  synonym? '{label}'{' = ' + meaning if meaning else ''} ~ '{trait}': {ch}",
                  flush=True)
        path.write_text(json.dumps(done, indent=1, ensure_ascii=False), encoding="utf-8")
    return done


def score(meanings, ask_synonyms=True):
    rows = []
    for paper in hb.default_papers():
        if paper not in HEADS:
            continue
        for dev in (False, True):
            for k, c, trait, col, gname in scored_columns(paper, dev):
                m = (meanings.get(paper, {}).get(str(k), {}) or {}).get(str(c), {})
                name = (col or {}).get("name", "")
                groups = (col or {}).get("groups", [])
                texts = [name, *groups, *[f"{g} {name}" for g in groups]]
                finder = m["candidates"][0]["term"] if m.get("candidates") else None
                details = (col or {}).get("details", [])
                label = " ".join([*groups, name, *details]).strip()   # as the merged table writes it
                parts = [f"{name} = {m['meaning']}"] if m.get("meaning") else []
                parts += [f"{d} = {v}" for d, v in (m.get("details") or {}).items() if v]
                rows.append({"paper": paper, "table": k, "col": c, "dev": dev, "trait": trait,
                             "name": name, "label": label, "said": "; ".join(parts),
                             "meaning": m.get("meaning"), "finder": finder,
                             "head": _match(texts, trait),
                             "head_finder": _match(texts + [finder], trait),
                             "head_meaning": _match(texts + [m.get("meaning")], trait),
                             "gemma_name": gname, "gemma": _match([gname], trait)})
    if ask_synonyms:
        # a decoy per miss: the same label against ANOTHER GT trait of the same table;
        # 'yes' to a decoy measures how lenient the synonym judge is
        traits = collections.defaultdict(list)
        for r in rows:
            traits[(r["paper"], r["table"])].append(r["trait"])
        def decoy(r):
            others = [t for t in traits[(r["paper"], r["table"])]
                      if t != r["trait"] and not hb.name_matches(t, r["trait"])]
            return others[0] if others else None
        pairs = set()
        for r in rows:
            if not r["head_meaning"] and r["name"]:
                pairs.add((r["label"], r["said"], r["trait"]))
                if decoy(r):
                    pairs.add((r["label"], r["said"], decoy(r)))
            if not r["gemma"] and r["gemma_name"]:
                pairs.add((r["gemma_name"], "", r["trait"]))
                if decoy(r):
                    pairs.add((r["gemma_name"], "", decoy(r)))
        syn = synonyms(sorted(pairs))
        yes = lambda *k: syn.get("|".join(k), ["no"])[0] == "yes"
        for r in rows:
            d = decoy(r)
            r["head_syn"] = r["head_meaning"] or (bool(r["name"]) and yes(r["label"], r["said"], r["trait"]))
            r["gemma_syn"] = r["gemma"] or (bool(r["gemma_name"]) and yes(r["gemma_name"], "", r["trait"]))
            r["head_decoy"] = (None if r["head_meaning"] or not r["name"] or not d
                               else yes(r["label"], r["said"], d))
            r["gemma_decoy"] = (None if r["gemma"] or not r["gemma_name"] or not d
                                else yes(r["gemma_name"], "", d))
    return rows


def summary(rows):
    pct = lambda a, b: f"{a}/{b} {a / b:.0%}" if b else "-"
    L = []
    for title, sel in (("held-out tables", [r for r in rows if not r["dev"]]),
                       ("development tables", [r for r in rows if r["dev"]])):
        n = len(sel)
        L += [f"{title}: {n} GT-trait columns", ""]
        for label, key in (("gemma's names (pipeline)", "gemma"),
                           ("head reader names", "head"),
                           ("  + finder's first definition (code only)", "head_finder"),
                           ("  + meaning nimble chose (QM)", "head_meaning"),
                           ("gemma's names + synonyms (nimble)", "gemma_syn"),
                           ("head + meaning + synonyms (nimble)", "head_syn")):
            if sel and key in sel[0]:
                L.append(f"  {label:44s}{pct(sum(r[key] for r in sel), n):>12s}")
        L.append("")
        for who in ("head", "gemma"):
            ds = [r[f"{who}_decoy"] for r in sel if r.get(f"{who}_decoy") is not None]
            if ds:
                L.append(f"  decoys ({who}): judge said 'same trait' to a WRONG trait "
                         f"{pct(sum(ds), len(ds))}")
        L.append("")
        wrong_finder = [r for r in sel if r["finder"] and not hb.name_matches(r["finder"], r["trait"])
                        and r["meaning"] != r["finder"]]
        L.append(f"  finder definitions nimble overruled: {len(wrong_finder)}")
        for r in wrong_finder[:12]:
            L.append(f"    {r['paper']} t{r['table']} '{r['name']}': finder '{r['finder']}' -> "
                     f"nimble '{r['meaning']}' (GT '{r['trait']}')")
        miss = [r for r in sel if not r.get("head_syn", r["head_meaning"])]
        L.append(f"  still missed: {len(miss)}")
        for r in miss:
            L.append(f"    {r['paper']} t{r['table']} c{r['col']}: '{r['label']}'"
                     f"{' (' + r['said'] + ')' if r['said'] else ''} vs GT '{r['trait']}'")
        acc = [r for r in sel if r.get("head_syn") and not r["head_meaning"]]
        L.append(f"  accepted only as synonyms (check by eye): {len(acc)}")
        for r in acc:
            L.append(f"    {r['paper']} t{r['table']} c{r['col']}: '{r['label']}'"
                     f"{' (' + r['said'] + ')' if r['said'] else ''} ~ GT '{r['trait']}'")
        L.append("")
    return "\n".join(L)


HEADS = json.loads(HEAD.read_text(encoding="utf-8"))
GEMMA = json.loads((hb.OUT / "gemma.json").read_text(encoding="utf-8"))


def main(argv):
    OUT.mkdir(parents=True, exist_ok=True)
    meanings = (json.loads((OUT / "meanings.json").read_text(encoding="utf-8"))
                if "--score" in argv else collect())
    rows = score(meanings, ask_synonyms="--no-synonyms" not in argv)
    (OUT / "rows.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")
    s = summary(rows)
    (OUT / "summary.txt").write_text(s, encoding="utf-8")
    print(s)


if __name__ == "__main__":
    main(sys.argv[1:])
