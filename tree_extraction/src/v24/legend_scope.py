"""
legend_scope.py — the column's legend scope, tested apart (2026-11-23, after the review of decode_trace.py's trace):
the inventory as it is (gemma not run), QK / QV / QB as they are; only the passage choice before them changes.

Today (full_run_v24.decode_column): QL, nimble's "which passage says what the values in the column stand for?"
(decode_units.choose_unit), is asked only when >= 2 passages hold an entry printed like one of the column's codes.
With one such passage its entries are used without asking; 'none of these' or 'several' -> the paper's whole
inventory (decode_units.match_column, 2026-10-14, kept the values on 'none').

Variants, one change each, then all four; each against the control in the same session (identical questions are
answered once, so a difference comes from the change, not from the model's wobble):
  control  full_run_v24.decode_column as it is
  ask      QL also when one passage holds such an entry (options: that passage, 'none of these'; 'none' keeps the
           column's values as printed, else the question would change nothing)
  none     'none of these' (two or more passages) -> the column's values kept as printed
  several  'several' -> the entries of the passages offered, not the whole inventory
  var      each passage option names the variables its entries were listed for (the inventory's 'variable')
  all      the four together

Columns: the full run's base trait columns (base_plan, first 25 values) that a column of the decoding answer key
falls on (decode_key.build_key on the GT; a continuation table counts under the table it continues, as
decode_chain.lookup does). Scored with decoder_v2.score_dir_from, weighted by species rows: coded cells right / in
another wording / left as printed / another term / not reached; pairs the paper does not print are counted apart
('no legend printed'); plain cells kept or changed. Tuning papers only (dev + held_a of split_v15).

    python legend_scope.py run [papers]     -> output/legend_scope/<paper>.json (resumable)
    python legend_scope.py report           -> output/legend_scope/REPORT.txt
TREE_OUTPUT picks the root (the inventory and the tags of that run: output_frozen_109 for the frozen tree).
"""
from __future__ import annotations

import collections
import contextlib
import copy
import io
import json
import sys
import time

import _paths
import column_tree as ct
import decode_chain as dc
import decode_inv as di
import decode_key as dk
import decode_units as du
import decoder as v1
import decoder_v2 as v2
import full_run_v24 as fr

OUT = _paths.OUTPUT / "legend_scope"
SPLIT = json.loads((_paths.SUB / "output/eval_split/split_v15.json").read_text(encoding="utf-8"))["assign"]
TUNING = ("dev", "held_a")
VARIANTS = {"control": set(), "ask": {"ask"}, "none": {"none"}, "several": {"several"},
            "var": {"var"}, "all": {"ask", "none", "several", "var"}}
EXAMPLES = {"Uemori2022": {3}, "Wallon2024": {24, 28}, "Tonelli2021": {7}}   # the review's cases, shown cell by cell


class Memo:
    """prompt_ab.Memo: client.ask with identical questions (same state, same question set) answered once."""

    def __init__(self, client):
        self.client, self.cache, self.asked, self.reused, self.requests = client, {}, 0, 0, 0

    @property
    def calls(self):
        return self.client.calls

    def ask(self, state_at, questions):
        self.requests += 1                 # what the variant would ask alone (its cost)
        key = json.dumps([state_at(0), questions], sort_keys=True, ensure_ascii=False)
        if key in self.cache:
            self.reused += 1
        else:
            self.cache[key] = self.client.ask(state_at, questions)
            self.asked += 1
        return copy.deepcopy(self.cache[key])


# --- the passage choice ---------------------------------------------------------------------------------------

def unit_variables(cats, u, codes):
    """The variables the inventory lists for the entries of unit u printed like one of the column's codes."""
    vs = []
    for e in cats:
        if e.get("unit") == u and e.get("code") and e.get("variable") \
                and any(v2.same_form(c, e["code"]) for c in codes):
            v = " ".join(str(e["variable"]).split())
            if v not in vs:
                vs.append(v)
    return vs


def choose_unit(client, header, values, units, by, cats, opts):
    """decode_units.choose_unit's question, word for word, except: one passage -> no 'several' option (ask); each
    passage option names its variables (var). -> (chosen unit ids | 'none', record)"""
    if len(by) >= 2 and "var" not in opts:
        return du.choose_unit(client, header, values, units, by)
    ranked = sorted(by, key=lambda u: (-len(by[u]), int(u[1:])))[:du.MAX_UNITS]
    shown = ", ".join(f"'{v}'" for v in values[:25])
    crit = {}
    for i, u in enumerate(ranked):
        vs = unit_variables(cats, u, by[u]) if "var" in opts else []
        about = f"; it defines codes for {', '.join(repr(v) for v in vs[:3])}" if vs else ""
        crit[f"p{i}"] = f"the passage ({units[u]['kind']}{about}): \"{du.quote(units[u]['text'], by[u])}\""
    if len(ranked) > 1:
        crit["several"] = "more than one of these passages: the column's codes are defined in several of them"
    crit["none"] = ("none of these: no passage here says what this column's values stand for; they "
                    "are written out as they are, or the passages are about something else")
    state = (f"A table in a scientific paper has a column named '{header}'. Its cells hold these "
             f"values: {shown}. The paper prints these passages that define some of the same codes.")
    ch, probs = v1.ask(client, state, f"Which passage says what the values in the column '{header}' "
                       f"stand for?", crit)
    rec = {"offered": ranked, "choice": ch, "probs": probs}
    if not ch or ch == "none":
        return "none", rec
    if ch == "several":
        return set(ranked), rec
    return {ranked[int(ch[1:])]}, rec


def decode_column(client, header, values, cats, units, opts):
    """full_run_v24.decode_column with the variant's changes; no change -> the same questions, the same result."""
    by = du.column_units(cats, header, values)
    allowed, rec = cats, {"offered": sorted(by), "choice": None}
    single = len(by) == 1 and "ask" in opts          # the new question: its 'none' keeps the values
    if len(by) >= 2 or single:
        chosen, rec = choose_unit(client, header, values, units, by, cats, opts)
        if chosen == "none":
            if "none" in opts or single:
                allowed = []
        elif len(chosen) == 1 or "several" in opts:
            allowed = [e for e in cats if e.get("unit") in chosen]
            rec["chosen"] = sorted(chosen)
    r = v2.match_column(client, header, values, allowed)
    r["units"] = rec
    return r


# --- the columns and the key ----------------------------------------------------------------------------------

def tuning_papers():
    return sorted(p for p, s in SPLIT.items() if s in TUNING)


def target(keys, k, c):
    """decode_chain.lookup's choice, as the key of the column decoded: (k, c), else the nearest earlier table at c."""
    if f"{k}:{c}" in keys:
        return f"{k}:{c}"
    earlier = sorted((int(x.split(":")[0]) for x in keys if x.split(":")[1] == str(c) and int(x.split(":")[0]) < k),
                     reverse=True)
    return f"{earlier[0]}:{c}" if earlier else None


def key_of(paper):
    """decode_key.build_key's columns, each coded cell with where the paper prints its pair (every printed form of
    the code tried: '1.0' is printed '1')."""
    found, grids = dk.build_key(paper)
    raw = (_paths.PAPERS / paper / f"{paper}_full.md").read_text(encoding="utf-8", errors="replace")
    text, spans = dk.clean(raw), dk.table_spans(raw)
    for e in found.values():
        for code, term in e.get("coded", {}).items():
            ws = [dk.where(f, term, text, raw, grids, e["table"], spans)[0] for f in v2.forms(code)]
            e.setdefault("where", {})[code] = next((w for w in ws if w not in v1.NO_LEGEND), ws[0])
    return found


def columns(paper, head, found):
    with contextlib.redirect_stdout(io.StringIO()):
        cols = {f"{k}:{c}": (h, vals) for t, fields, _o, _x in fr.base_plan(paper, head)
                for k, c, h, vals in fr.trait_columns(t, fields)}
    want = {target(cols, e["table"], e["col"]) for e in found.values()} - {None}
    return {k: cols[k] for k in sorted(want, key=lambda x: tuple(map(int, x.split(":"))))}


def run(papers):
    OUT.mkdir(parents=True, exist_ok=True)
    head = fr.head_runs()
    client = None
    for p in papers:
        f = OUT / f"{p}.json"
        if f.exists() or p not in head or SPLIT.get(p) not in TUNING:
            continue
        cats = di.inventory(p)
        found = key_of(p)
        if not cats or not any(e["kind"] == "coded" for e in found.values()):
            continue
        cols = columns(p, head, found)
        units = du.unit_texts(p)
        client = client or Memo(ct.DecisionClient(v1.NIMBLE, 1))
        res, t0 = {"_columns": {k: list(v) for k, v in cols.items()}, "_questions": {}}, time.time()
        for name, opts in VARIANTS.items():
            a0, q0 = client.asked, client.requests
            res[name] = {k: fr._retry(lambda: decode_column(client, h, vals, cats, units, opts))
                         for k, (h, vals) in cols.items()}
            res["_questions"][name] = {"new": client.asked - a0, "questions": client.requests - q0}
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  {p:22s} {len(cols)} columns, " + ", ".join(f"{n} {q['new']}" for n, q in res["_questions"].items())
              + f" new questions ({time.time() - t0:.0f}s)", flush=True)
    if client:
        v1.unload(v1.NIMBLE)


# --- the report -----------------------------------------------------------------------------------------------

RIGHT = ("right", "right, unit inside")
WORDING = ("right, longer wording", "right, shorter wording")


def report():
    rows = {n: [] for n in VARIANTS}
    ql = {n: collections.Counter() for n in VARIANTS}
    cost = collections.Counter()
    n_cols = 0
    for f in sorted(OUT.glob("*.json")):
        p = f.stem
        res = json.loads(f.read_text(encoding="utf-8"))
        found = key_of(p)
        n_cols += len(res["_columns"])
        for n in VARIANTS:
            dec = res[n]
            for r in v2.score_dir_from(p, found, lambda e: dc.lookup(dec, e["table"], e["col"])):
                r["table"] = found[r["trait"]]["table"]
                rows[n].append(r)
            for rec in dec.values():
                ch = (rec.get("units") or {}).get("choice")
                if ch is not None:
                    ql[n]["asked"] += 1
                    ql[n]["one passage" if ch.startswith("p") else ch] += 1
            cost[n] += res["_questions"][n]["questions"]
    L = [f"legend scope: the column's passage choice before QK / QV / QB (inventory unchanged), "
         f"{len(list(OUT.glob('*.json')))} tuning papers, {n_cols} columns", ""]

    def tally(rs):
        c = collections.Counter()
        for r in rs:
            if r["kind"] == "kept":
                c["kept_n"] += r["w"]
                c["kept_ok"] += r["w"] * (r["out"] == "right")
                continue
            if r["out"] in ("no legend printed", "GT error"):
                c[r["out"]] += r["w"]
                continue
            c["coded_n"] += r["w"]
            c["right"] += r["w"] * (r["out"] in RIGHT)
            c["wording"] += r["w"] * (r["out"] in WORDING)
            c["left as printed"] += r["w"] * (r["out"] == "left as printed")
            c["other term"] += r["w"] * (r["out"] == "other term")
            c["not reached"] += r["w"] * (r["out"] == "not reached")
        for r in rs:                       # pairs the paper does not print: decoded anyway?
            if r["out"] == "no legend printed":
                c["nlp_changed"] += r["w"] * (r["have"] != r["cell"])
        return c

    L.append("coded cells (species rows; the pair printed in the paper):")
    L.append(f"  {'variant':9s} {'right':>12s} {'wording':>8s} {'left':>6s} {'other':>6s} {'unreached':>9s}   "
             f"plain kept      not printed (decoded anyway)   QL asked   questions")
    for n in VARIANTS:
        c = tally(rows[n])
        pct = lambda a, b: f"{a}/{b} {a / b:.0%}" if b else "-"
        L.append(f"  {n:9s} {pct(c['right'], c['coded_n']):>12s} {c['wording']:>8d} {c['left as printed']:>6d} "
                 f"{c['other term']:>6d} {c['not reached']:>9d}   {pct(c['kept_ok'], c['kept_n']):>14s}  "
                 f"{c['no legend printed']:>6d} ({c['nlp_changed']})                 {ql[n]['asked']:>4d}      "
                 f"{cost[n]}")
    L.append("")
    L.append("QL answers per variant: " + "; ".join(f"{n}: " + ", ".join(f"{k} {v}" for k, v in sorted(ql[n].items())
                                                                         if k != "asked") for n in VARIANTS))
    base = {(r["paper"], r["trait"], r["cell"]): r for r in rows["control"]}
    for n in VARIANTS:
        if n == "control":
            continue
        gains, losses, moved = [], [], []
        for r in rows[n]:
            b = base.get((r["paper"], r["trait"], r["cell"]))
            if not b or b["have"] == r["have"]:
                continue
            ok_b, ok_r = b["out"] in RIGHT + WORDING, r["out"] in RIGHT + WORDING
            line = (f"    {r['paper']:16s} {r['trait'][:26]!r:28s} '{r['cell']}' -> want '{r['want'][:24]}': "
                    f"'{b['have'][:28]}' -> '{r['have'][:28]}'  (x{r['w']}, {b['out']} -> {r['out']})")
            (gains if ok_r and not ok_b else losses if ok_b and not ok_r else moved).append((r["w"], line))
        L += ["", f"{n} against control: right gained {sum(w for w, _ in gains)} rows, lost {sum(w for w, _ in losses)}, "
                  f"other changes {sum(w for w, _ in moved)}"]
        for title, xs in (("gained", gains), ("lost", losses), ("changed, neither right", moved)):
            if xs:
                L.append(f"  {title}:")
                L += [x for _w, x in sorted(xs, key=lambda t: -t[0])]
    L += ["", "the review's cases, cell by cell (control -> all):"]
    for r in rows["all"]:
        if r["table"] in EXAMPLES.get(r["paper"], ()):
            b = base.get((r["paper"], r["trait"], r["cell"]))
            L.append(f"  {r['paper']:12s} {r['trait'][:26]!r:28s} '{r['cell']}' want '{r['want'][:24]}': "
                     f"'{(b or {}).get('have', '?')[:28]}' -> '{r['have'][:28]}' ({r['out']})")
    L += ["", "per paper, coded rows right (control / ask / none / several / var / all):"]
    for p in sorted({r["paper"] for r in rows["control"]}):
        cs = [tally([r for r in rows[n] if r["paper"] == p]) for n in VARIANTS]
        L.append(f"  {p:22s} [{SPLIT.get(p)}] " + " / ".join(f"{c['right']}" for c in cs) + f"  of {cs[0]['coded_n']}")
    (OUT / "REPORT.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    if sys.argv[1:2] == ["run"]:
        run(sys.argv[2:] or tuning_papers())
    else:
        report()
