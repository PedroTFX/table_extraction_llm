"""Judged matching: same species, equal value (format differences aside), trait names judged the same."""
import csv, re, sys, collections, json, difflib
sys.argv = [sys.argv[0], sys.argv[1], sys.argv[2]]
exec(open(f"{sys.argv[1]}/judge_pairs.py", encoding="utf-8").read().split("out = {}")[0])
N, root = sys.argv[1], sys.argv[2]
# coincidences: two different traits that happen to share a value (judged by hand, 2026-11-04)
REJECT = {
 "Xia2022": {("Elytra Length","width of elytra"),("Elytra Length","width of head"),("Elytra Length","width of pronotum"),
   ("Elytra Length/Elytra Width","Scale bars"),("Elytra Length/Elytra Width","width of head/width of elytra"),
   ("Elytra Width","length of elytra"),("Elytra Width","width of head"),("Head Length","width of pronotum"),
   ("Head Length/Head Width","width of pronotum/width of elytra"),("Head Width","length of elytra"),
   ("Head Width","width of elytra"),("Head Width/Elytra Width","length of elytra/width of elytra"),
   ("Pronotum Width","length of head")},
 "Xu2024": {("Anterior angles of pronotum","Humeri of Elytra"),("Anterior angles of pronotum","Elytra humeri"),
   ("Anterior angles of pronotum","posterior angles of Pronotum"),("Femora of legs morphology","Female reproductive organs"),
   ("scutellum morphology","Mesosternum pubescent metepisternum"),
   ("scutellum morphology","Abdominal sternite other areas of sternites 1–4 and all of s"),
   ("terior angles of pronotum","Elytra humeri"),("Body color","antenna")},
 "Ustjuzhanin2024": {("antennae","fringe on the wings"),("antennae","hind legs"),("fringe on the wings","antennae"),
   ("fringe on the wings","hind legs"),("head, thorax, and tegulae","hind legs"),("head, thorax, and tegulae","wings"),
   ("hind legs","antennae"),("hind legs","fringe on the wings"),("hind legs","tegulae"),("hind legs","thorax"),("hind legs","head")}}
STOP = {"morphology", "of", "the", "male", "female", "genitalia", "a", "and"}
toks = lambda s: set(re.findall(r"[a-z0-9]+", str(s).lower())) - STOP
def same_trait(p, a, b):
    if (a, b[:60]) in REJECT[p] or (a, b) in REJECT[p]:
        return False
    ta, tb = toks(a), toks(b)
    return not a or (bool(ta and tb) and (ta <= tb or tb <= ta))
res = {}
for p in ["Xia2022", "Xu2024", "Ustjuzhanin2024"]:
    gt = gt_rows(p)
    us = [{"sp": r["verbatimIdentification"], "t": r["measurementType"], "v": r["measurementValue"]}
          for r in csv.DictReader(open(f"{N}/{__import__('os').environ.get('OURS', 'ours3')}/{p}.csv", encoding="utf-8"))]
    used, exact, near, missed = set(), [], [], []
    pool = collections.defaultdict(list)
    for i, r in enumerate(us): pool[key(r["sp"])].append(i)
    left = []
    for g in gt:                                     # pass 1: equal value, same trait
        j = next((i for i in pool[key(g["sp"])] if i not in used and nv(us[i]["v"]) == nv(g["v"])
                  and (same_trait(p, g["t"], us[i]["t"]) or (g["t"], us[i]["t"]) in PAIRS_OK.get(p, set()))), None) \
            if False else next((i for i in pool[key(g["sp"])] if i not in used and nv(us[i]["v"]) == nv(g["v"])
                  and not ((g["t"], us[i]["t"]) in REJECT[p])), None)
        if j is None: left.append(g)
        else: used.add(j); exact.append((g, us[j]))
    for g in left:                                   # pass 2: same trait, one value inside the other / very alike
        best, bj = 0, None
        for i in pool[key(g["sp"])]:
            if i in used or not same_trait(p, g["t"], us[i]["t"]): continue
            a, b = nv(g["v"]), nv(us[i]["v"])
            r = 1.0 if (a and b and (a in b or b in a)) else difflib.SequenceMatcher(None, a, b).ratio()
            if r > best: best, bj = r, i
        if bj is not None and best >= 0.75: used.add(bj); near.append((g, us[bj], round(best, 2)))
        else: missed.append(g)
    extra = [us[i] for i in range(len(us)) if i not in used]
    res[p] = {"exact": exact, "near": near, "missed": missed, "extra": extra}
    print(f"== {p}: GT {len(gt)}, ours {len(us)}: equal {len(exact)}, near {len(near)}, GT unmatched {len(missed)}, ours unmatched {len(extra)}")
json.dump({p: {k: v for k, v in d.items()} for p, d in res.items()}, open(f"{N}/judge_res_{__import__('os').environ.get('OURS', 'ours3')}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
