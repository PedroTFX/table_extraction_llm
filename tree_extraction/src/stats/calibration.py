"""Calibration audit (REVIEW 2026-11-16, experiment 1): is a 'sure' answer (p >= 0.8) a right answer? Files only, no
model. For each question type with a key that does not come from the model, the saved answers of full_run_v24 are
binned by the probability of the answer given and checked against the key. Tuning papers only (dev + held_a of
split_v15.json); totals only, no paper named except in the examples, which are tuning papers.

  question                key (independent of the model)
  head reader (QF + QC)   your verdict per table, header review round 2 (answers_r2): right / wrong
  column tag              column_role_bench.derive_labels: the GT's (species, value) pairs in the column
  Q-KIND                  a table the GT draws on (derive_labels gives a trait column) should be 'traits'
  Q-ROW (structure)       a GT table read long (GT trait names in a column) -> 'record', else 'wide'
  organism Q-KIND         the column holding >= 50% GT species -> 'species'; any other candidate -> not 'species'
  relevance Q-COL         a column the GT draws on is a trait: any of identifier / genetic / count / statistic is wrong
  decoder (QK / QV / QB)  the decoding key (decode_key/all/key.json): the term a coded cell stands for
  units (Q-PART, Q-TEXT)  the GT unit of the rows whose (species, value) pairs the column holds

The keys are noisy (a GT convention is not always the paper's), so 'wrong' here means 'disagrees with the GT'.
What matters is the shape: does accuracy rise with p, and how often is an answer at 0.8 or more wrong?

    python calibration.py          -> tree_extraction/output/eval_split/CALIBRATION.txt (+ CALIBRATION.json)
"""
import collections
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TE = HERE.parents[1]
sys.path.insert(0, str(TE / "src" / "v24"))
import _paths  # noqa: E402,F401  (puts source/ on the path)
import column_role_bench as crb  # noqa: E402
import evaluate as ev  # noqa: E402
import full_run_v24 as f24  # noqa: E402

OUT = TE / "output"
V24 = OUT / "full_run_v24"
SPLIT = json.loads((OUT / "eval_split/split_v15.json").read_text(encoding="utf-8"))["assign"]
TUNING = sorted(p for p, g in SPLIT.items() if g in ("dev", "held_a"))
BINS = [(0.0, 0.5), (0.5, 0.8), (0.8, 0.9), (0.9, 0.95), (0.95, 0.99), (0.99, 1.01)]
TRAITS = {"measurementType", "measurementValue"}
DROP = ("identifier", "genetic", "count", "statistic")

rec = collections.defaultdict(list)       # question -> [(p, right, example)]


def load(f):
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def add(q, p, right, ex=""):
    if p is not None:
        rec[q].append((float(p), bool(right), ex))


def words(s):
    return " ".join(re.findall(r"[^\W_]+", str(s or "").lower().replace("μ", "µ")))


def same_unit(a, b):
    k = lambda s: re.sub(r"[\s.]", "", str(s or "").lower().replace("μ", "µ").replace("um", "µm"))
    return bool(a) and k(a) == k(b)


def main():
    head = f24.head_runs()
    key = load(OUT / "decode_key/all/key.json")
    reviews = {}
    for f in (OUT / "header_review/answers_r2/reviews_r2").glob("*.json"):
        d = load(f)
        reviews[(d["paper"], int(d["table"]))] = d.get("verdict")
    round2 = load(OUT / "header_tree_bench/experiments/round2.json")
    n_papers = 0
    for p in TUNING:
        if p not in head:
            continue
        inp = crb.paper_inputs(_paths.PAPERS / p)
        if not inp:
            continue
        n_papers += 1
        rows = ev.load_xlsx(str(inp[1]))
        gt = crb.GroundTruth(rows)
        units_of = collections.defaultdict(collections.Counter)      # (species, value) -> GT units
        for r in rows:
            units_of[(r["verbatimIdentification"].strip(), crb.norm(r["measurementValue"]))][
                (r.get("measurementUnit") or "").strip()] += 1

        # head reader: your verdict per table against the first-record answer and the weakest head-cell answer
        for e in round2.get(p, []):
            v = reviews.get((p, int(e["table"])))
            if v not in ("right", "wrong"):
                continue
            full = e.get("full") or e
            add("head reader: first record (QF)", (full.get("q1") or {}).get("p"), v == "right", f"{p} t{e['table']}")
            cells = [x[1] for piece in full.get("cells") or [] for x in piece.values() if len(x) > 1]
            if cells:
                add("head reader: weakest head cell (QC)", min(cells), v == "right", f"{p} t{e['table']}")

        known = f24.known_tags(p, V24)
        kind, struct, org = load(V24 / "kind" / f"{p}.json"), load(V24 / "structure" / f"{p}.json"), \
            load(V24 / "organism" / f"{p}.json")
        relev, dec, units = load(V24 / "relevance" / f"{p}.json"), load(V24 / "decode" / f"{p}.json"), \
            load(V24 / "units" / f"{p}.json")
        for t, _ctx in f24.tables_of(p, head):
            k = t.table_index
            labels = crb.derive_labels(t, gt)
            if not labels:
                continue
            lab = {h: L for h, (L, _e) in labels.items()}
            gt_table = any(L in TRAITS for L in lab.values())
            # column tags
            for h, v in ((known.get(k) or {}).get("fields") or {}).items():
                L = lab.get(h)
                if not v or L in (None, "unsure") or len(v) < 2:
                    continue
                tag = v[0] or "none"
                right = (tag in TRAITS and L in TRAITS) or tag == L
                q = "column tag, a column the GT draws on" if L != "none" else "column tag, a column the GT does not use"
                add(q, v[1], right, f"{p} t{k} '{h}': {tag} (GT {L})")
            # Q-KIND
            d = kind.get(str(k))
            if gt_table and d and (d.get("kind") or {}).get("choice") in ("traits", "figure", "model", "sampling", "other"):
                ch, pr = d["kind"]["choice"], d["kind"]["probs"]
                add("Q-KIND (table kind)", pr.get(ch), ch == "traits", f"{p} t{k}: {ch}")
            # Q-ROW
            d = struct.get(str(k))
            if gt_table and d and d.get("row"):
                want = "record" if any(L == "measurementValue" for L in lab.values()) else "wide"
                ch, pr = d["row"]["choice"], d["row"]["probs"]
                add("Q-ROW (structure)", pr.get(ch), ch == want, f"{p} t{k}: {ch} (GT {want})")
            # organism Q-KIND
            d = org.get(str(k)) or {}
            ids = {h for h, (L, e) in labels.items() if L == "verbatimIdentification" and "GT species" in e}
            for h, a in (d.get("kinds") or {}).items():
                if a.get("choice") == "part" or h not in lab:
                    continue
                add("organism column Q-KIND", (a.get("probs") or {}).get(a.get("choice")),
                    (a.get("choice") == "species") == (h in ids), f"{p} t{k} '{h}': {a.get('choice')}")
            # relevance Q-COL on the columns the GT draws on
            for ck, a in (relev.get("columns") or {}).items():
                kk, h = ck.split("|", 1)
                if kk != str(k) or lab.get(h) not in TRAITS:
                    continue
                ch, pr = a.get("choice"), a.get("probs") or {}
                add("relevance Q-COL, a GT trait column", pr.get(ch), ch not in DROP, f"{p} t{k} '{h}': {ch}")
                if "count2" in a:
                    asked = a["count2"]["asked"][0]
                    add("relevance Q-COUNT, a GT trait column", (asked.get("probs") or {}).get(asked.get("choice")),
                        not a["count2"]["site"], f"{p} t{k} '{h}': site={a['count2']['site']}")
            # units: each question asked of a column, against the GT unit of its rows
            idc = next(iter(ids), None)
            for ck, u in (units.get("columns") or {}).items():
                kk, h = ck.split("|", 1)
                if kk != str(k) or lab.get(h) not in TRAITS:
                    continue
                got = collections.Counter()
                for r in t.records:
                    rid = gt.match_id(r.get(idc)) if idc else (gt.ids[0] if len(gt.ids) == 1 else None)
                    if rid:
                        got.update(units_of.get((rid, crb.norm(r.get(h))), {}))
                if not got:
                    continue
                want = got.most_common(1)[0][0]
                for a in u.get("asked") or []:
                    pr = a.get("probs") or {}
                    q = f"units: {a.get('source')} candidate"
                    right = bool(a.get("unit")) == same_unit(a.get("part"), want)
                    add(q, pr.get(a.get("choice")), right, f"{p} t{k} '{h}': '{a.get('part')}' -> {a.get('choice')} (GT '{want}')")
        # decoder: every coded cell of the key that the run decoded
        for trait, e in (key.get(p) or {}).items():
            r = dec.get(f"{e['table']}:{e['col']}") or {}
            for cell, want in (e.get("coded") or {}).items():
                c = (r.get("cells") or {}).get(cell)
                if not c:
                    continue
                ps = [max(v.values()) for v in (c.get("probs") or {}).values() if isinstance(v, dict) and v]
                if not ps:
                    continue
                term = c.get("term") or cell
                add("decoder (weakest of QK / QV / QB)", min(ps), words(term) == words(want),
                    f"{p} '{trait}': '{cell}' -> '{term}' (key '{want}')")

    L = [f"Calibration audit, full_run_v24 answers on {n_papers} tuning papers (dev + held_a). Bins by the probability of "
         f"the answer given; 'right' = agrees with a key that does not come from the model.", ""]
    js = {}
    for q in sorted(rec):
        xs = rec[q]
        L.append(f"{q}: {len(xs)} answers")
        L.append(f"    {'p':>11s} {'n':>6s} {'right':>7s}")
        js[q] = []
        for lo, hi in BINS:
            b = [r for pp, r, _e in xs if lo <= pp < hi]
            if b:
                L.append(f"    {lo:.2f}-{min(hi, 1):.2f} {len(b):6d} {sum(b) / len(b):7.1%}")
                js[q].append({"lo": lo, "hi": min(hi, 1), "n": len(b), "right": sum(b)})
        sure = [(pp, r, e) for pp, r, e in xs if pp >= 0.8]
        wrong = [x for x in sure if not x[1]]
        if sure:
            L.append(f"    sure (p >= 0.8): {len(sure)}, of them wrong {len(wrong)} ({len(wrong) / len(sure):.1%})")
        for pp, _r, e in sorted(wrong, reverse=True)[:5]:
            L.append(f"      wrong at {pp:.3f}: {e[:150]}")
        L.append("")
    (OUT / "eval_split/CALIBRATION.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    (OUT / "eval_split/CALIBRATION.json").write_text(json.dumps(js, indent=1), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
