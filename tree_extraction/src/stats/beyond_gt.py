"""The rows we write beyond the GT (the scorer's 'spurious, out of scope': a trait the GT never covers), on the current
run (output/two_step: v18 tables + prose). Files only, no model: the scorer's own steps are replayed with the trait-name
pairs its model made, read from each paper's report (SEMANTIC measurementType REMAP), so the rows are the report's.

  totals    per group: our rows, matched, wrong in scope, beyond the GT; how many of those carry a number, and how many
            have their value printed in the paper's markdown (exact text, spaces normalised): a faithfulness check
  names     tuning papers only: each paper's trait names beyond the GT with row counts and three example values
  sample    tuning papers only: 200 rows drawn at random over all their rows beyond the GT (seed 20261110), each with
            the passage of the markdown that holds its value and species, for judging by hand

held_b papers appear in the totals only.

    python beyond_gt.py      -> tree_extraction/output/eval_split/stats/beyond_gt.json
"""
import ast
import collections
import json
import random
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "source"))
import evaluate as ev                                        # noqa: E402

TE = REPO / "tree_extraction"
OUT = TE / "output"
PAPERS = REPO / "data" / "un_processed_papers"
SPLIT = json.loads((OUT / "eval_split/split_v15.json").read_text(encoding="utf-8"))["assign"]
RNG = random.Random(20261110)
QUOTED = r"""('(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")"""     # a Python string literal, either quote


def type_map(report):
    """The report prints each pair as repr() -> repr(): a name holding a line break is printed '\\n', one holding an
    apostrophe in double quotes. Read back as literals (before 2026-11-10 a plain regex lost both kinds, and their
    rows were counted beyond the GT)."""
    t = report.read_text(encoding="utf-8", errors="ignore") if report.exists() else ""
    sec = re.search(r"SEMANTIC measurementType REMAP \(pred -> gt, \d+ pair\(s\)\)\n(.*?)\n\s*\n", t, re.S)
    out = {}
    if sec:
        for m in re.finditer(r"^\s+" + QUOTED + r" -> " + QUOTED + r"\s*$", sec[1], re.M):
            out[ast.literal_eval(m[1])] = ast.literal_eval(m[2])
    return out


def flat(s):
    return " ".join(str(s or "").split())


def plain(md):
    t = re.sub(r"</t[dh]>", " | ", md)
    t = re.sub(r"</tr>", "\n", t)
    t = re.sub(r"<[^>]+>|<!--.*?-->", " ", t)
    return t


class Text:
    """A paper's text, with its number tokens and lower-cased copy made once, and each value looked up once."""

    def __init__(self, text):
        self.text, self.low = text, text.lower()
        self.nums = set(re.findall(r"\d+(?:[.,]\d+)*", text))
        self.seen = {}

    def printed(self, value):
        v = flat(value)
        if not v:
            return False
        if v not in self.seen:
            parts = re.findall(r"\d+(?:[.,]\d+)*", v)
            if parts and re.fullmatch(r"[\d.,\-–\s]+", v):
                self.seen[v] = all(x in self.nums for x in parts)
            else:
                self.seen[v] = v.lower() in self.low
        return self.seen[v]


def passage(row, text, lines):
    """The markdown line (a table row or a sentence run) holding the value and, best, the species too."""
    v = flat(row.get("measurementValue"))
    sp = flat(row.get("verbatimIdentification")).split()
    ep = sp[-1].lower() if sp else ""
    tw = [w.lower() for w in re.findall(r"[A-Za-z]{4,}", row.get("measurementType") or "")][:3]
    best, score = "", -1
    for ln in lines:
        if not v or v.lower() not in ln.lower():
            continue
        s = (ep and ep in ln.lower()) * 2 + sum(w in ln.lower() for w in tw)
        if s > score:
            best, score = ln, s
    if best:
        i = best.lower().find(v.lower())
        a = max(0, i - 220)
        return ("…" if a else "") + best[a:i + len(v) + 220].strip() + ("…" if i + len(v) + 220 < len(best) else "")
    return ""


def main():
    groups = collections.defaultdict(collections.Counter)
    names, pool = {}, []
    for p in sorted(SPLIT):
        g = SPLIT[p]
        pred_f = OUT / "two_step" / p / f"{p}.csv"
        gt_f = PAPERS / p / f"{p}.xlsx"
        if not (pred_f.exists() and gt_f.exists()):
            continue
        gt, pred = ev.load_xlsx(str(gt_f)), ev.load_csv(str(pred_f))
        pred, _sm, _su = ev.remap_pred_species(gt, pred)
        tm = type_map(OUT / "two_step" / p / f"{p}_report.txt")
        for r in pred:
            if r.get("measurementType") in tm:
                r["measurementType"] = tm[r["measurementType"]]
        matched, missing, extra = ev.match_rows(gt, pred, ev.DEFAULT_KEY, False)
        scope = ev.build_scope(gt, ["measurementType"], False)
        ins, oos = ev.partition_extra(extra, scope, False)
        md = (PAPERS / p / f"{p}_full.md")
        text = plain(md.read_text(encoding="utf-8", errors="ignore")) if md.exists() else ""
        lines = [ln for ln in re.split(r"\n+", text) if ln.strip()]
        rows = [r for r, _u in oos]
        c = groups[g]
        c["papers"] += 1
        c["papers with rows beyond GT"] += bool(rows)
        c["our rows"] += len(pred)
        c["matched"] += len(matched)
        c["wrong, in scope"] += len(ins)
        c["beyond GT"] += len(rows)
        num = [r for r in rows if re.fullmatch(r"[<>~≈±]?\s*[\d.,\-–]+\s*\w{0,3}", flat(r.get("measurementValue")))]
        c["beyond GT, numeric"] += len(num)
        tx = Text(text)
        c["beyond GT, value printed"] += sum(tx.printed(r.get("measurementValue")) for r in rows)
        c["beyond GT, species printed"] += sum(tx.printed(r.get("verbatimIdentification")) for r in rows)
        if g not in ("dev", "held_a"):
            continue
        cnt = collections.Counter(flat(r.get("measurementType")) for r in rows)
        ex = collections.defaultdict(list)
        for r in rows:
            k = flat(r.get("measurementType"))
            if len(ex[k]) < 3 and flat(r.get("measurementValue")) not in ex[k]:
                ex[k].append(flat(r.get("measurementValue"))[:60])
        names[p] = {"group": g, "gt_traits": sorted({flat(x.get("measurementType")) for x in gt})[:12],
                    "beyond": [{"name": k, "rows": n, "examples": ex[k]} for k, n in cnt.most_common()]}
        for r in rows:
            pool.append((p, g, r, tx, lines))
    sample = []
    for p, g, r, tx, lines in RNG.sample(pool, min(200, len(pool))):
        sample.append({"paper": p, "group": g, "species": flat(r.get("verbatimIdentification")),
                       "trait": flat(r.get("measurementType")), "value": flat(r.get("measurementValue"))[:200],
                       "unit": flat(r.get("measurementUnit")), "statistic": flat(r.get("measurementStatistic")),
                       "sex": flat(r.get("sex")), "printed": tx.printed(r.get("measurementValue")),
                       "passage": passage(r, tx.text, lines)})
    res = {"totals": {g: dict(c) for g, c in groups.items()}, "tuning_rows_beyond": len(pool), "names": names, "sample": sample}
    f = OUT / "eval_split/stats/beyond_gt.json"
    f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    for g, c in groups.items():
        print(g, dict(c))
    print("tuning rows beyond the GT:", len(pool), "-> sample", len(sample))


if __name__ == "__main__":
    main()
