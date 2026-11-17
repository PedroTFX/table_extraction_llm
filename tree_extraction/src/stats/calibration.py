"""Calibration audit (REVIEW 2026-11-16, experiment 1): is a 'sure' answer (p >= 0.8) a right answer? Files only, no
model. For each question type with a key that does not come from the model, the saved answers of full_run_v24 are
binned by the probability of the answer given and checked against the key. Tuning papers only (dev + held_a of
split_v15.json); totals only, no paper named except in the examples, which are tuning papers.

  question                key (independent of the model)
  head reader (QF + QC)   your verdict per table, header review round 2 (answers_r2): right / wrong
  column tag              column_role_bench.derive_labels, a trait label kept only when the column is one GT trait
  Q-KIND                  a table with a column the GT draws on should be 'traits'
  Q-ROW (structure)       structure_key.py (GT long -> 'record', GT wide -> 'wide'), tables of several species
  organism Q-KIND         every column whose cells are >= 50% GT species names organisms; any other -> not 'species'
  relevance Q-COL         a column the GT draws on is a trait: any of identifier / genetic / count / statistic is wrong
  decoder (QK / QV / QB)  the decoding key (decode_key/all/key.json): the term a coded cell stands for
  units (Q-PART, Q-TEXT)  the GT unit of the GT trait the column (or a long table's name cell) is

'The GT draws on a column' (revised 2026-11-17, after Noriega2023): its cells, with each row's species, match GT
rows for 40% or more, AND one GT trait holds half of those matches or more. Matching on species and value alone
mixes GT traits: Noriega2023 records the same biomass values as 'Biomass' in g and as 'Body Mass' in mm, and the first
version of this key gave the column the majority unit of both (mm). A column of 0 / 1 or small numbers matches many
GT traits by coincidence and is not counted. A long table's value column counts when structure_key.py calls the
table long; a header that names a GT trait counts too. When the GT traits of a column disagree on the unit, the trait
named like the column decides; if none is, the key is left out (counted at the end).

The keys are noisy (a GT convention is not always the paper's), so 'wrong' here means 'disagrees with the GT'.
What matters is the shape: does accuracy rise with p, and how often is an answer at 0.8 or more wrong?
Every sure-and-wrong case is listed with its key's evidence in CALIBRATION_WRONG.txt, for checking by hand.

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
    def k(s):
        s = str(s or "").lower().replace("μ", "µ").replace("²", "2").replace("³", "3")
        s = re.sub(r"[\s.]", "", s)
        s = re.sub(r"(?<=[a-z]{3})s$", "", s)                  # 'days' = 'day'
        return "/".join(UNIT_SYN.get(x, x) for x in s.split("/"))
    return bool(a) and k(a) == k(b)


DROPPED = collections.Counter()           # keys left out, by reason
SKEY = {}                                 # (paper, table) -> 'GT long' | 'GT wide' | 'no GT rows' (structure_key.py)
for _e in json.loads((OUT / "eval_split/structure_key.json").read_text(encoding="utf-8")):
    SKEY[(_e["paper"], int(_e["table"]))] = _e.get("gt")
# spelled units and their symbols, so a printed 'grams' agrees with a GT 'g'
UNIT_SYN = {"gram": "g", "milligram": "mg", "kilogram": "kg", "microgram": "µg", "millimetre": "mm", "millimeter": "mm",
            "centimetre": "cm", "centimeter": "cm", "micrometre": "µm", "micrometer": "µm", "micron": "µm", "um": "µm",
            "metre": "m", "meter": "m", "second": "s", "sec": "s", "minute": "min", "hour": "h", "hr": "h", "d": "day"}


def _flat(s):
    return " ".join(str(s or "").split())


def gt_index(rows):
    """(species, value) -> [(GT trait, GT unit)] for every GT row."""
    by = collections.defaultdict(list)
    for r in rows:
        by[(r["verbatimIdentification"].strip(), crb.norm(r["measurementValue"]))].append(
            (r["measurementType"].strip(), (r.get("measurementUnit") or "").strip()))
    return by


def id_columns(t, gt):
    """{column: share of its cells that are GT species} for every column where it is half or more."""
    out = {}
    for c in t.columns:
        cells = [_flat(r.get(c.name)) for r in t.records if _flat(r.get(c.name))]
        if cells:
            f = sum(1 for x in cells if gt.match_id(x)) / len(cells)
            if f >= 0.5:
                out[c.name] = f
    return out


def row_ids_of(t, gt, ids):
    if ids:
        best = max(ids, key=ids.get)
        return [gt.match_id(r.get(best)) for r in t.records]
    return [gt.ids[0] if len(gt.ids) == 1 else None] * len(t.records)


def column_evidence_rows(pairs, cols, by):
    """(cells with a species, cells matching a GT row, {GT trait: cells}, {GT trait: Counter(units)})."""
    n = m = 0
    traits, units = collections.Counter(), collections.defaultdict(collections.Counter)
    for rid, r in pairs:
        for h in cols:
            v = crb.norm(r.get(h))
            if not rid or not v:
                continue
            n += 1
            hits = by.get((rid, v))
            if not hits:
                continue
            m += 1
            for tr in {x for x, _u in hits}:
                traits[tr] += 1
            for tr, u in hits:
                units[tr][u] += 1
    return n, m, traits, units


def column_evidence(t, h, row_ids, by):
    return column_evidence_rows(list(zip(row_ids, t.records)), [h], by)


def gt_traits(n, m, traits):
    """The GT traits a column is: its cells match GT rows for 40% or more, and one GT trait holds half the matches or
    more (a 0 / 1 or small-number column matches many GT traits by coincidence). [] when not."""
    if not n or m < 0.4 * n or not traits:
        return []
    return [tr for tr, c in traits.items() if c >= 0.5 * m]


def unit_key(traits, units, names):
    """The GT unit of the column: the units of its GT traits when they agree; else the traits whose name shares a word
    with the column's names; None when that does not settle it (Noriega2023 records the same biomass values as
    'Biomass' in g and as 'Body Mass' in mm)."""
    unit_of = {tr: units[tr].most_common(1)[0][0] for tr in traits if units.get(tr)}
    if not unit_of:
        return None, ""
    if len(set(unit_of.values())) == 1:
        return next(iter(unit_of.values())), f"GT {sorted(unit_of)}"
    w = set(words(" ".join(names)).split())
    named = {tr: u for tr, u in unit_of.items() if set(words(tr).split()) & w}
    if len(set(named.values())) == 1:
        return next(iter(named.values())), (f"GT {sorted(named)}, named like the column; "
                                            f"not {sorted(set(unit_of) - set(named))}")
    return None, ""


def unit_answers(u, want, where, why):
    for a in u.get("asked") or []:
        pr = a.get("probs") or {}
        q = f"units: {a.get('source')} candidate, " + ("said: the unit" if a.get("unit") else "said: not the unit")
        right = bool(a.get("unit")) == same_unit(a.get("part"), want)
        add(q, pr.get(a.get("choice")), right,
            f"{where}: '{a.get('part')}' -> {a.get('choice')} (GT unit '{want}', {why})")


def same_term(a, b):
    """The decoded term against the key's: equal words, one inside the other, or close (the key keeps the GT's
    typos: 'highly eussocial')."""
    import difflib
    x, y = words(a), words(b)
    return bool(x) and (x == y or (len(y) > 3 and (x in y or y in x))
                        or difflib.SequenceMatcher(None, x, y).ratio() >= 0.85)


def chosen(probs):
    """The probability of the answer given, for each question in a (possibly nested) {question: {option: p}}."""
    for v in probs.values():
        if isinstance(v, dict) and v:
            nums = [x for x in v.values() if isinstance(x, (int, float))]
            if nums:
                yield max(nums)
            else:
                yield from chosen(v)


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
        meaning = load(V24 / "meaning" / f"{p}.json")
        by = gt_index(rows)
        for t, _ctx in f24.tables_of(p, head):
            k = t.table_index
            labels = crb.derive_labels(t, gt)
            if not labels:
                continue
            lab = {h: L for h, (L, _e) in labels.items()}
            ids = id_columns(t, gt)
            row_ids = row_ids_of(t, gt, ids)
            skey = SKEY.get((p, k))
            ev_of = {c.name: column_evidence(t, c.name, row_ids, by) for c in t.columns}

            def gt_col(h):
                """The GT traits the column is (a list), [] for a long table's value column or a header naming a GT
                trait, None when the GT does not draw on it (or only by coincidence)."""
                if lab.get(h) == "measurementValue" and skey == "GT long":
                    return []
                got = gt_traits(*ev_of[h][:3])
                if got:
                    return got
                if lab.get(h) == "measurementType" and crb.header_names_trait(h, gt):
                    return []
                return None
            gt_table = any(gt_col(c.name) is not None for c in t.columns)
            # column tags
            for h, v in ((known.get(k) or {}).get("fields") or {}).items():
                L = lab.get(h)
                if not v or L in (None, "unsure") or len(v) < 2 or h not in ev_of:
                    continue
                if L in TRAITS and gt_col(h) is None:
                    DROPPED["column tag: a GT trait label by coincidence (no one GT trait)"] += 1
                    continue
                tag = v[0] or "none"
                right = (tag in TRAITS and L in TRAITS) or tag == L
                q = "column tag, a column the GT draws on" if L != "none" else "column tag, a column the GT does not use"
                add(q, v[1], right, f"{p} t{k} '{h}': {tag} (GT {L}; {labels[h][1]})")
            # Q-KIND
            d = kind.get(str(k))
            if gt_table and d and (d.get("kind") or {}).get("choice") in ("traits", "figure", "model", "sampling", "other"):
                ch, pr = d["kind"]["choice"], d["kind"]["probs"]
                why = "; ".join(f"'{c.name}' = GT {gt_col(c.name) or 'values'}" for c in t.columns
                                if gt_col(c.name) is not None)[:200]
                add("Q-KIND (table kind)", pr.get(ch), ch == "traits", f"{p} t{k}: {ch} (GT columns: {why})")
            # Q-ROW: the structure key (structure_key.py), tables of several species
            d = struct.get(str(k))
            several = len(set(row_ids) - {None}) >= 2
            if skey in ("GT long", "GT wide") and several and d and d.get("row"):
                want = "record" if skey == "GT long" else "wide"
                ch, pr = d["row"]["choice"], d["row"]["probs"]
                add("Q-ROW (structure)", pr.get(ch), ch == want, f"{p} t{k}: {ch} ({skey})")
            # organism Q-KIND: every column naming GT species counts
            d = org.get(str(k)) or {}
            for h, a in (d.get("kinds") or {}).items():
                if a.get("choice") == "part" or h not in lab:
                    continue
                names = a.get("choice") in ("species", "higher") if h in ids else a.get("choice") == "species"
                add("organism column Q-KIND", (a.get("probs") or {}).get(a.get("choice")),
                    names == (h in ids), f"{p} t{k} '{h}': {a.get('choice')} (GT species in {ids.get(h, 0):.0%} of cells)")
            # relevance Q-COL on the columns the GT draws on
            for ck, a in (relev.get("columns") or {}).items():
                kk, h = ck.split("|", 1)
                if kk != str(k) or h not in ev_of:
                    continue
                g = gt_col(h)
                if g is None:
                    continue
                ch, pr = a.get("choice"), a.get("probs") or {}
                add("relevance Q-COL, a GT trait column", pr.get(ch), ch not in DROP,
                    f"{p} t{k} '{h}': {ch} (GT {g or lab.get(h)})")
                if "count2" in a:
                    asked = a["count2"]["asked"][0]
                    add("relevance Q-COUNT, a GT trait column", (asked.get("probs") or {}).get(asked.get("choice")),
                        not a["count2"]["site"], f"{p} t{k} '{h}': site={a['count2']['site']} (GT {g or lab.get(h)})")
            # units, wide columns: the GT unit of the GT trait the column is
            for ck, u in (units.get("columns") or {}).items():
                kk, h = ck.split("|", 1)
                if kk != str(k) or h not in ev_of:
                    continue
                g = gt_col(h)
                if not g:
                    continue
                want, why = unit_key(g, ev_of[h][3], [h, meaning.get(h, "")])
                if want is None:
                    DROPPED["units: GT traits with different units, none named like the column"] += 1
                    continue
                unit_answers(u, want, f"{p} t{k} '{h}'", why)
            # units, a long table's name cells: the rows printing that name, their value columns
            vcols = [h for h, L in lab.items() if L == "measurementValue"] if skey == "GT long" else []
            for cell, u in ((units.get("cells") or {}).items() if vcols else ()):
                tcol = next((c.name for c in t.columns if c.name not in vcols
                             and any(_flat(r.get(c.name)) == cell for r in t.records)), None)
                if not tcol:
                    continue
                sub = [(rid, r) for rid, r in zip(row_ids, t.records) if _flat(r.get(tcol)) == cell]
                ev = column_evidence_rows(sub, vcols, by)
                g = gt_traits(*ev[:3])
                if not g:
                    continue
                want, why = unit_key(g, ev[3], [cell])
                if want is None:
                    DROPPED["units: GT traits with different units, none named like the cell"] += 1
                    continue
                unit_answers(u, want, f"{p} t{k} cell '{cell}'", why)
        # decoder: every coded cell of the key that the run decoded
        for trait, e in (key.get(p) or {}).items():
            r = dec.get(f"{e['table']}:{e['col']}") or {}
            for cell, want in (e.get("coded") or {}).items():
                if "binary convention" in str((e.get("where") or {}).get(cell, "")):
                    continue                                   # 0 / 1 -> No / Yes is the GT's, not printed
                c = (r.get("cells") or {}).get(cell)
                if not c:
                    continue
                ps = list(chosen(c.get("probs") or {}))
                if not ps:
                    continue
                term = c.get("term") or cell
                add("decoder (weakest of QK / QV / QB)", min(ps), same_term(term, want),
                    f"{p} '{trait}': '{cell}' -> '{term}' (key '{want}')")

    L = [f"Calibration audit, full_run_v24 answers on {n_papers} tuning papers (dev + held_a). Bins by the probability of "
         f"the answer given; 'right' = agrees with a key that does not come from the model.", ""]
    js = {}
    W = ["Every sure (p >= 0.8) answer that disagrees with its key, with the key's evidence. Tuning papers only.", ""]
    for q in sorted(rec):
        xs = rec[q]
        L.append(f"{q}: {len(xs)} answers")
        if "does not use" in q:
            L.append("    (no key: the GT may simply not annotate these columns; listed for scale, not calibration)")
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
        W.append(f"## {q}: {len(wrong)} sure and wrong")
        W += [f"  {pp:.3f}  {e}" for pp, _r, e in sorted(wrong, reverse=True)]
        W.append("")
    L += ["Keys left out (the key could not settle the answer):"] + [f"    {n:5d}  {r}" for r, n in DROPPED.most_common()]
    (OUT / "eval_split/CALIBRATION.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    (OUT / "eval_split/CALIBRATION_WRONG.txt").write_text("\n".join(W) + "\n", encoding="utf-8")
    (OUT / "eval_split/CALIBRATION.json").write_text(json.dumps(js, indent=1), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
