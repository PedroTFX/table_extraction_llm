"""The per-tag measure for the five listed tags (v15: the statistic re-read; DESIGN_listed_tags_v14.md). No model:
both sides come from the template's lists, so values compare exactly (evaluate.normalize_value).

On the GT rows a run matches on species + trait + value (the scorer's key, with the taxon and
trait-name remaps its report saved), per tag: GT filled / ours filled / equal / different / ours empty /
ours only; coverage (ours filled of GT filled) and accuracy (equal of both filled); split by the GT
value's class (reported: a word for it printed in the paper; defaulted: none printed) and by paper
group (the 109 split's dev / held; other). Against the previous run: overwrites (a value it held that
this run changed), fixed (wrong -> right) and broken (right -> wrong). With the step's decisions:
accuracy of its answers by the model's probability, against the paper's GT value for the tag.

    python full_run_v15.py tagscore <papers>      writes <run>/TAGS_V15.txt
"""
import collections
import contextlib
import io
import json
import re

import _paths

TAGS = ["sex", "caste", "basisOfRecord", "lifeStage", "measurementStatistic"]
CUE = {  # a word a reader would find for the value (the reported / defaulted proxy, fixed before any run)
    "female": r"\bfemales?\b|♀", "male": r"\bmales?\b|♂", "both": r"both sexes|males and females|females and males",
    "worker": r"\bworkers?\b", "queen": r"\bqueens?\b|\bgynes?\b", "minor worker": r"\bminor workers?\b|\bminors\b",
    "major worker": r"\bmajor workers?\b|\bmajors\b", "soldier": r"\bsoldiers?\b", "male alate": r"\balate males?\b",
    "adult": r"\badults?\b|\bimago", "larva": r"\blarva[el]?\b", "pupa": r"\bpupa[el]?\b", "egg": r"\beggs?\b",
    "nymph": r"\bnymphs?\b", "caterpillar": r"\bcaterpillars?\b",
    "mean": r"\bmeans?\b|\baverage", "mean ± sd": r"±|\bSD\b|standard deviation", "mean ± se": r"\bSE\b|standard error",
    "range": r"\brange\b|\bmin", "median": r"\bmedian\b", "individual": r"\bindividual|specimens?\b",
    "count": r"\bnumber of\b|\bcounts?\b", "max": r"\bmax", "min": r"\bmin",
    "preservedspecimen": r"\bpinned\b|\bethanol\b|museum|collection|preserved",
    "livingspecimen": r"\breared\b|\blaborator|\bculture", "humanobservation": r"\bobserv",
    "materialcitation": r"\bliterature\b|\bdatabase\b|published",
}


def _ev():
    import evaluate as ev
    return ev


def _gt_path(p):
    from mineru_extract import classify_folder
    with contextlib.redirect_stdout(io.StringIO()):
        return classify_folder(_paths.PAPERS / p)[1]


def _remaps(rep):
    taxa, types = {}, {}
    if not rep.exists():
        return taxa, types
    txt = rep.read_text(encoding="utf-8", errors="ignore")
    for block, d in (("TAXON NAME REMAP", taxa), ("SEMANTIC measurementType REMAP", types)):
        i = txt.find(block)
        if i < 0:
            continue
        for line in txt[i:].splitlines()[1:]:
            m = re.match(r"\s+(['\"])(.*)\1 -> (['\"])(.*)\3\s*$", line)
            if not m:
                break
            d[m.group(2)] = m.group(4)
    return taxa, types


def _sp(s):
    w = re.findall(r"[a-z]+", re.sub(r"\(.*?\)", " ", str(s or "")).lower())
    return " ".join(w[:2])


def matched(p, run_dir, remap_dir=None):
    """[(GT row, our row)] on species + trait + value, the remaps of remap_dir's report (default the
    run's own) applied."""
    ev = _ev()
    gt, cf = _gt_path(p), run_dir / p / f"{p}.csv"
    if not gt or not cf.exists():
        return []
    taxa, types = _remaps((remap_dir or run_dir) / p / f"{p}_report.txt")
    pred = collections.defaultdict(list)
    for r in ev.load_csv(str(cf)):
        sp = taxa.get(r["verbatimIdentification"], r["verbatimIdentification"])
        ty = types.get(r["measurementType"], r["measurementType"])
        pred[(_sp(sp), ev.normalize_value(ty), ev.key_value(r, False))].append(r)
    out = []
    with contextlib.redirect_stdout(io.StringIO()):
        rows = ev.load_xlsx(str(gt))
    for g in rows:
        k = (_sp(g["verbatimIdentification"]), ev.normalize_value(g["measurementType"]), ev.key_value(g, False))
        if pred.get(k):
            out.append((g, pred[k].pop(0)))
    return out


def _paper_text(p):
    f = _paths.PAPERS / p / f"{p}_full.md"
    t = f.read_text(encoding="utf-8", errors="replace") if f.exists() else ""
    return re.split(r"^#+\s*(?:references|literature cited)\b", t, flags=re.I | re.M)[0]


def groups():
    """The v15 split: dev and held_a to tune, held_b to test once (split_v15.json)."""
    f = _paths.SUB / "output" / "eval_split" / "split_v15.json"
    return json.loads(f.read_text(encoding="utf-8"))["assign"] if f.exists() else {}


def measure(papers, run_dir, prev_dir=None):
    """-> {group: {tag: Counter}}, plus calibration bins."""
    ev = _ev()
    grp = groups()
    stats = collections.defaultdict(lambda: {t: collections.Counter() for t in TAGS})
    calib = {t: collections.Counter() for t in TAGS}
    for p in papers:
        pairs = matched(p, run_dir, prev_dir)
        if not pairs:
            continue
        prev_by_key = {}
        if prev_dir:                                  # the same GT rows, matched in the previous run
            for g, r in matched(p, prev_dir):
                prev_by_key.setdefault(tuple(sorted(g.items())), []).append(r)
        text = _paper_text(p)
        cls = {}
        gtv = {t: collections.Counter() for t in TAGS}
        for g, r in pairs:
            for t in TAGS:
                gv, ov = ev.normalize_value(g.get(t, "")), ev.normalize_value(r.get(t, ""))
                if gv:
                    gtv[t][gv] += 1
                    if (t, gv) not in cls:
                        rx = CUE.get(gv.replace(" ", "") if t == "basisOfRecord" else gv)
                        cls[(t, gv)] = ("no cue word" if rx is None else
                                        "reported" if re.search(rx, text, re.I) else "defaulted")
                kind = ("equal" if gv == ov else "different") if gv and ov else \
                    ("ours empty" if gv else "ours only" if ov else None)
                if not kind:
                    continue
                for G in ("all", grp.get(p, "other")):
                    s = stats[G][t]
                    s[kind] += 1
                    if gv:
                        s[f"{cls[(t, gv)]}: {kind}"] += 1
                pk = tuple(sorted(g.items()))
                if prev_dir and prev_by_key.get(pk):
                    pv = ev.normalize_value(prev_by_key[pk][0].get(t, ""))
                    if pv and pv != ov:
                        for G in ("all", grp.get(p, "other")):
                            stats[G][t]["overwritten"] += 1
                            stats[G][t]["fixed" if ov == gv else "broken" if pv == gv else "changed, still wrong"] += 1
        dec_f = run_dir / "listed_tags" / f"{p}.json"
        if dec_f.exists():                            # the model's sureness against the paper's GT value
            dec = json.loads(dec_f.read_text(encoding="utf-8"))
            answers = [(t, a) for cap in (dec.get("captions") or {}).values() for t, a in cap.items()]
            answers += [(t, a) for t, fs in (dec.get("text_found") or {}).items() for a in fs]
            for t, a in answers:
                v = a.get("value")
                if not v or v in ("not", "mixed") or not gtv[t]:
                    continue
                pr = (a.get("probs") or {}).get(v)
                band = "via duels" if pr is None or "duels" in a else \
                    "≥ 0.95" if pr >= 0.95 else "0.8–0.95" if pr >= 0.8 else "< 0.8"
                ok = ev.normalize_value(v) == gtv[t].most_common(1)[0][0]
                calib[t][(band, ok)] += 1
    return stats, calib


def core_same(papers, run_dir, prev_dir):
    """Papers whose rows differ from prev_dir's in species, trait or value (v14 must change none)."""
    ev = _ev()
    key = lambda r: (r["verbatimIdentification"], r["measurementType"], r["measurementValue"])
    out = []
    for p in papers:
        a, b = prev_dir / p / f"{p}.csv", run_dir / p / f"{p}.csv"
        if a.exists() and b.exists() and                 collections.Counter(map(key, ev.load_csv(str(a)))) != collections.Counter(map(key, ev.load_csv(str(b)))):
            out.append(p)
    return out


def report(papers, run_dir, prev_dir, name):
    stats, calib = measure(papers, run_dir, prev_dir)
    L = [f"listed tags of {run_dir.name}" + (f" vs {prev_dir.name}" if prev_dir else "") +
         " on the GT rows matched on species + trait + value"]
    if prev_dir:
        bad = core_same(papers, run_dir, prev_dir)
        L.append(f"core rows (species, trait, value) changed vs {prev_dir.name}: "
                 + (", ".join(bad) if bad else "none"))
    for G in ["all", "dev", "held_a", "held_b", "other", "grit"]:
        if G not in stats:
            continue
        L += ["", f"== {G}",
              f"  {'tag':22s} {'GT filled':>9s} {'ours':>7s} {'equal':>7s} {'differ':>7s} {'empty':>7s} {'extra':>7s}"
              f" {'cover':>6s} {'acc':>6s}   reported acc / defaulted acc   overwritten (fixed / broken)"]
        for t in TAGS:
            s = stats[G][t]
            gt = s["equal"] + s["different"] + s["ours empty"]
            both = s["equal"] + s["different"]
            cov = (both / gt) if gt else 0
            acc = (s["equal"] / both) if both else 0
            ra = s["reported: equal"] / max(1, s["reported: equal"] + s["reported: different"])
            da = s["defaulted: equal"] / max(1, s["defaulted: equal"] + s["defaulted: different"])
            L.append(f"  {t:22s} {gt:9d} {both + s['ours only']:7d} {s['equal']:7d} {s['different']:7d}"
                     f" {s['ours empty']:7d} {s['ours only']:7d} {cov:6.1%} {acc:6.1%}"
                     f"   {ra:5.0%} ({s['reported: equal'] + s['reported: different']}) /"
                     f" {da:5.0%} ({s['defaulted: equal'] + s['defaulted: different']})"
                     f"   {s['overwritten']} ({s['fixed']} / {s['broken']})")
    L += ["", "the step's answers (captions and quotes) vs the paper's GT value, by the model's probability:"]
    for t in TAGS:
        c = calib[t]
        bands = sorted({b for b, _ok in c})
        L.append(f"  {t:22s} " + "; ".join(f"{b}: {c[(b, True)]}/{c[(b, True)] + c[(b, False)]} right" for b in bands))
    (run_dir / name).write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
