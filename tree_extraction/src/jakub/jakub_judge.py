"""A second scorer for Jakub's sets: our trait names judged against the database's names by hand (Claude,
2026-11-08), because the production scorer's small model did not pair 'carapace length' with 'Cephalothorax
length', 'opisthosoma' with 'Abdomen', 'длина карапакса' or '头胸部长' with either.

  NAMES     every distinct trait name with a numeric value in newPDF + imagePDF (355), judged once:
            exact  the name means that database trait ('carapace length' -> Cephalothorax length)
            vague  the right part, the dimension or the leg lost ('carapace' -> Cephalothorax length or width,
                   'leg iii' -> any leg III trait): counted apart, never as an exact match
            a name not listed means no database trait (ratios, indices, eye areas, leg formulas, altitude ...)
  species   a row of ours matches a GT species with the same epithet whose genus is the same, abbreviated
            ('C. jinggangica sp. n.' = Calommata jinggangica) or not printed; 'sp. n.', 'sp. nov.', a
            subgenus in brackets and footnote marks are dropped
  values    numbers equal at the shorter side's precision (5.0 = 5, 1,25 = 1.25); a range 'a-b' of ours can
            match the GT's min row with a and its max row with b
  matching  one GT row per row of ours (a range: one per end); exact names first, then vague ones

Out of scope: rows of ours whose name means no database trait or whose value is not a number. In scope and
unmatched: a false positive.

    python jakub_judge.py <set> [<set> ...]      TREE_OUTPUT not needed: reads output_jakub_<set>/two_step
-> output_jakub_<set>/jakub_judge.csv per paper, totals on screen, and a sample of matches to check by eye.
"""
import collections
import csv
import random
import re
import sys
from pathlib import Path

import openpyxl

REPO = Path(__file__).resolve().parents[3]

LEGS = {"i": "I", "ii": "II", "iii": "III", "iv": "IV"}
SEG = {"femur": "Femur", "patella": "Patella", "tibia": "Tibia", "metatarsus": "Metatarsus", "tarsus": "Tarsus"}


def leg_traits(r):
    return [f"Leg {r} length", f"Pt+Ti {r} length"] + [f"{s} {r} length" for s in SEG.values()]


ALL_LEGS = [t for r in LEGS.values() for t in leg_traits(r)]
CL, CW = "Cephalothorax length", "Cephalothorax width"
AL, AW = "Abdomen length", "Abdomen width"
SL, SW = "Sternum length", "Sternum width"
BL = "Body length"

EXACT = {
    # body
    "total length": BL, "body length": BL, "total l": BL, "longueur totale": BL, "long. totale": BL, "总长": BL,
    "体长": BL, "общая длина": BL, "one of them total length": BL, "first instar spiderlings total length": BL,
    "larvae total length": BL, "second instar total length": BL,
    # cephalothorax / carapace / prosoma
    "carapace length": CL, "prosoma length": CL, "céphalothorax plus long": CL, "длина карапакса": CL,
    "длина головогруди": CL, "длина головогруди голотипа, мм": CL, "头胸部长": CL, "背甲长": CL,
    "cephalothorax-länge": CL, "abdominal paratype carapace length": CL,
    "first instar spiderlings carapace length": CL, "larvae carapace length": CL, "second instar carapace length": CL,
    "carapace width": CW, "prosoma width": CW, "céphalothorax large": CW, "头胸部宽": CW, "背甲宽": CW,
    "abdominal paratype carapace width": CW, "first instar spiderlings carapace width": CW,
    "larvae carapace width": CW, "second instar carapace width": CW,
    # abdomen / opisthosoma
    "abdomen length": AL, "opisthosoma length": AL, "длина абдомена": AL, "длина брюшка": AL, "腹部长": AL,
    "abdomen-länge": AL,
    "abdomen width": AW, "opisthosoma width": AW, "максимальная ширина брюшка": AW, "腹部宽": AW, "abdomen-breite": AW,
    # sternum, clypeus, mouth parts
    "sternum length": SL, "sternum long": SL, "sternum width": SW, "sternum large": SW, "腹甲宽": SW,
    "clypeus": "Clypeus height", "clypeus height": "Clypeus height", "clypeus-höhe": "Clypeus height",
    "labium length": "Labium length", "labium width": "Labium width",
    "endite length": "Endite length", "endite width": "Endite width",
    # eyes
    **{k: "AME" for k in ("anterior median eye", "anterior median eyes", "eyes anterior median eye",
                          "carapace anterior median eyes", "vordere mittelaugen")},
    **{k: "ALE" for k in ("anterior lateral eye", "anterior lateral eyes", "eyes anterior lateral eye",
                          "carapace anterior lateral eyes")},
    **{k: "PME" for k in ("posterior median eye", "posterior median eyes", "eyes posterior median eye",
                          "hinteren mittelaugen")},
    **{k: "PLE" for k in ("posterior lateral eye", "posterior lateral eyes", "eyes posterior lateral eye",
                          "hinteren seitenaugen")},
    # spinnerets (whole spinneret only; its joints are not the database's trait)
    **{k: "Spinneret PLS" for k in ("abdomen posterior lateral spinneret", "posterior lateral spinnerets",
                                    "dorsum posterior lateral spinneret", "posterior lateral spinneret")},
    **{k: "Spinneret PMS" for k in ("abdomen posterior median spinneret", "posterior median spinnerets",
                                    "dorsum posterior median spinneret")},
    **{k: "Spinneret ALS" for k in ("abdomen anterior lateral spinneret", "anterior lateral spinnerets",
                                    "dorsum anterior lateral spinneret")},
    # palp, legs written out, other
    "palp": "Palp length", "average egg diameter": "Egg size",
    "tibia+patella i": "Pt+Ti I length",
    **{f"length of legs {k}": f"Leg {r} length" for k, r in LEGS.items()},
    **{f"länge der femora {k}": f"Femur {r} length" for k, r in LEGS.items()},
}
for _pre in ("", "carapace "):                       # 'leg i: femur', 'leg i femur', 'carapace leg i: femur' ...
    for _k, _r in LEGS.items():
        for _sep in (": ", " "):
            EXACT[f"{_pre}leg {_k}{_sep}total length"] = f"Leg {_r} length"
            for _s, _S in SEG.items():
                EXACT[f"{_pre}leg {_k}{_sep}{_s}"] = f"{_S} {_r} length"

VAGUE = {
    "carapace": [CL, CW], "prosoma": [CL, CW], "cephalothorax": [CL, CW], "céphalothorax": [CL, CW],
    "головогрудь": [CL, CW], "prosoma carapace": [CL, CW], "carapa": [CL, CW],
    "abdomen": [AL, AW], "opisthosoma": [AL, AW],
    "sternum": [SL, SW], "labium": ["Labium length", "Labium width"],
    "endite": ["Endite length", "Endite width"], "eyes maxillae": ["Endite length", "Endite width"],
    "chelicerae": ["Chelicerae basal part length", "Chelicerae width"],
    "chelicera": ["Chelicerae basal part length", "Chelicerae width"],
    "chélicères": ["Chelicerae basal part length", "Chelicerae width"],
    "body": [BL], "size": [BL], "longueur": [BL], "length": [BL], "long.": [BL],
    "long": [BL, CL, AL, SL], "wide": [CW, AW, SW], "width": [CW, AW, SW], "maximum width": [CW, AW, SW],
    "total": [BL] + [f"Leg {r} length" for r in LEGS.values()],
    "pedipalp": ["Palp length"], "cymbium": ["Palpal tarsus"], "cymbium length": ["Palpal tarsus"],
    "maximum burrow depth": ["Burrow length"], "total length of tube": ["Burrow length"],
    "tube total length of tubes": ["Burrow length"],
    **{f"leg {k}": leg_traits(r) for k, r in LEGS.items()},
    **{k: leg_traits(r) for k, r in LEGS.items()},
    **{f"{n}. bacak": leg_traits(r) for n, r in zip("1234", LEGS.values())},
    **{f"endites measurements of legs: {k}": leg_traits(r) for k, r in LEGS.items()},
    **{k: ALL_LEGS for k in ("leg", "legs", "leg segment", "leg segments", "lengths of legs",
                             "length of leg segments, and total", "leg measurements", "步足量度")},
    **{k: [f"Femur {r} length" for r in LEGS.values()] + ["Palpal femur"] for k in ("femur", "fémur", "腿节")},
    **{k: [f"Patella {r} length" for r in LEGS.values()] + ["Palpal patella"] for k in ("patella", "patelle")},
    **{k: [f"Tibia {r} length" for r in LEGS.values()] + ["Palpal tibia"] for k in ("tibia",)},
    **{k: [f"Metatarsus {r} length" for r in LEGS.values()] for k in ("metatarsus", "métatarse", "后附节")},
    **{k: [f"Tarsus {r} length" for r in LEGS.values()] + ["Palpal tarsus"] for k in ("tarsus", "tarse")},
    **{k: [f"Pt+Ti {r} length" for r in LEGS.values()] for k in ("patella + tibia", "膝、胫节")},
}


def key(name):
    return " ".join(str(name or "").lower().split())


def nums(v):
    """The numbers a cell holds: one, or the two ends of a range ('4.2-5.1', '0,6–0,8'). -> [(value, decimals)]"""
    s = str(v or "").strip()
    parts = re.split(r"\s*[-–—]\s*", s) if re.fullmatch(r"\d+([.,]\d+)?\s*[-–—]\s*\d+([.,]\d+)?", s) else [s]
    out = []
    for p in parts:
        p = re.sub(r"\s*(mm|µm|um)$", "", p).replace(",", ".")
        if re.fullmatch(r"\d+(\.\d+)?", p):
            out.append((float(p), len(p.split(".")[1]) if "." in p else 0))
    return out


def same(a, b):
    d = min(a[1], b[1])
    return round(a[0], d) == round(b[0], d)


def clean_sp(s):
    s = re.sub(r"\([^)]*\)", " ", str(s or ""))
    s = re.sub(r"\b(sp|n|nov|spec|comb)\.?(?=\s|$)", " ", s)
    s = re.sub(r"[*†‡§¶#]", " ", s)
    return [t for t in re.findall(r"[A-Za-z][A-Za-z.\-]*", s) if t not in (".",)]


def species_of(ours, gts):
    """The GT species a printed name of ours is, or None."""
    t = clean_sp(ours)
    if not t:
        return None
    ep = t[-1].lower().strip(".")
    gen = t[0] if len(t) > 1 else ""
    hits = [g for g in gts if clean_sp(g) and clean_sp(g)[-1].lower() == ep]
    if gen:
        full = [g for g in hits if clean_sp(g)[0].lower() == gen.lower()]
        if full:
            return full[0]
        if gen.endswith(".") and len(gen.rstrip(".")) <= 2:
            hits = [g for g in hits if clean_sp(g)[0].lower().startswith(gen.rstrip(".").lower())]
        else:
            hits = []
    return hits[0] if len(hits) == 1 else None


def judge(paper_dir, csv_file):
    p = paper_dir.name
    rows = list(openpyxl.load_workbook(paper_dir / f"{p}.xlsx", read_only=True).active.iter_rows(values_only=True))
    gt = [dict(zip(rows[0], r)) for r in rows[1:]]
    gt = [g for g in gt if g.get("measurementType") and nums(g.get("measurementValue"))]
    ours = list(csv.DictReader(open(csv_file, encoding="utf-8"))) if csv_file.exists() else []
    gts = sorted({str(g["verbatimIdentification"]) for g in gt})
    traits = {g["measurementType"] for g in gt}
    cand = []
    oos = 0
    for i, r in enumerate(ours):
        k, ns = key(r.get("measurementType")), nums(r.get("measurementValue"))
        to, kind = ([EXACT[k]], "exact") if k in EXACT else (VAGUE[k], "vague") if k in VAGUE else ([], None)
        to = [t for t in to if t in traits]
        if not ns or not to:
            oos += 1
            continue
        cand.append({"i": i, "sp": species_of(r.get("verbatimIdentification"), gts), "to": set(to), "kind": kind,
                     "ns": ns, "left": len(ns), "row": r})
    used = set()
    matches = []
    for kind in ("exact", "vague"):
        for gi, g in enumerate(gt):
            if gi in used:
                continue
            gv = nums(g["measurementValue"])[0]
            for c in cand:
                if c["kind"] != kind or c["left"] == 0 or c["sp"] != str(g["verbatimIdentification"]):
                    continue
                if g["measurementType"] in c["to"] and any(same(gv, n) for n in c["ns"]):
                    used.add(gi)
                    c["left"] -= 1
                    matches.append((kind, g, c["row"]))
                    break
    tp_e = sum(m[0] == "exact" for m in matches)
    tp_v = len(matches) - tp_e
    fp = sum(1 for c in cand if c["left"] == len(c["ns"]))
    missed = collections.Counter(str(g.get("measurementStatistic")) for gi, g in enumerate(gt) if gi not in used)
    return {"paper": p, "gt": len(gt), "ours": len(ours), "tp_exact": tp_e, "tp_vague": tp_v, "fp": fp,
            "out_of_scope": oos, "missed": missed}, matches, [c["row"] for c in cand if c["left"] == len(c["ns"])]


def prf(tp, fp, fn):
    p, r = tp / max(1, tp + fp), tp / max(1, tp + fn)
    return p, r, 2 * p * r / max(1e-9, p + r)


def main(sets):
    random.seed(20261108)
    for s in sets:
        base = REPO / "data" / "Jakub_papers" / s
        out = REPO / "tree_extraction" / f"output_jakub_{s}"
        res, allm, allfp = [], [], []
        for d in sorted(x for x in base.iterdir() if x.is_dir() and (x / f"{x.name}_full.md").exists()):
            r, m, fp = judge(d, out / "two_step" / d.name / f"{d.name}.csv")
            res.append(r)
            allm += [(d.name, *x) for x in m]
            allfp += [(d.name, x) for x in fp]
        with open(out / "jakub_judge.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["paper", "gt_rows", "our_rows", "tp_exact", "tp_vague", "fp", "out_of_scope", "f1_exact", "f1_with_vague"])
            for r in res:
                fe = prf(r["tp_exact"], r["fp"] + r["tp_vague"], r["gt"] - r["tp_exact"])[2]
                fv = prf(r["tp_exact"] + r["tp_vague"], r["fp"], r["gt"] - r["tp_exact"] - r["tp_vague"])[2]
                w.writerow([r["paper"], r["gt"], r["ours"], r["tp_exact"], r["tp_vague"], r["fp"], r["out_of_scope"],
                            f"{fe:.3f}", f"{fv:.3f}"])
                r["fe"], r["fv"] = fe, fv
        T = lambda k: sum(r[k] for r in res)
        gt, te, tv, fp = T("gt"), T("tp_exact"), T("tp_vague"), T("fp")
        miss = sum((r["missed"] for r in res), collections.Counter())
        n = max(1, len(res))
        print(f"################ {s}: {len(res)} papers, {gt} GT rows")
        print("exact names only: P %.3f R %.3f F1 %.3f" % prf(te, fp + tv, gt - te))
        print("exact + vague:    P %.3f R %.3f F1 %.3f" % prf(te + tv, fp, gt - te - tv))
        print(f"TP exact {te}, TP vague {tv}, FP in scope {fp}, out of scope {T('out_of_scope')}; "
              f"mean F1 per paper {sum(r['fe'] for r in res) / n:.3f} (exact), {sum(r['fv'] for r in res) / n:.3f} (with vague)")
        print("GT rows missed by statistic:", dict(miss))
        for r in res:
            print(f"  {r['paper']:10s} GT {r['gt']:4d}  exact {r['tp_exact']:4d}  vague {r['tp_vague']:4d}  FP {r['fp']:4d}  "
                  f"F1 {r['fe']:.3f} / {r['fv']:.3f}")
        print("-- sample of matches (paper | kind | GT species, trait, value | ours species, trait, value)")
        for p, kind, g, o in random.sample(allm, min(25, len(allm))):
            print(f"  {p} | {kind} | {g['verbatimIdentification']}, {g['measurementType']}, {g['measurementValue']} | "
                  f"{o['verbatimIdentification']}, {o['measurementType']}, {o['measurementValue']}")
        print("-- sample of false positives (paper | ours species, trait, value)")
        for p, o in random.sample(allfp, min(15, len(allfp))):
            print(f"  {p} | {o['verbatimIdentification']}, {o['measurementType']}, {o['measurementValue']}")


if __name__ == "__main__":
    main(sys.argv[1:])
