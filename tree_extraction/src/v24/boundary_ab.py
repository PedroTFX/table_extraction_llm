"""
boundary_ab.py — experiment A (2026-11-24, after the review of inventory_audit.py): the inventory's boundary check
(legend_inventory.grounded -> decoder_v2.verify_a) finds a code only as a separate word within decoder.NEAR of the
term. A numbered legend that the PDF reader glued together ('1. herbivorous2. primary predators3. hyper predators',
Uemori2022) therefore loses entries gemma listed right: '3' follows the 's' of 'predators'.

The rescue, nothing else changed: a NUMERIC code printed as an enumeration mark directly before the term
('3. hyper predators', '3) …', '3: …'), with no digit, point or comma before it, counts as printed. Gemma is not
run: the entries the check dropped are in each inventory's 'dropped' list and are checked again against the paper's
units (an entry's batch is not recorded, so every unit of the paper is tried; only the enumeration rule can pass
an entry here, so nothing the old check would reach in another batch is added). A rescued entry gets the fields a
kept one has, its label the whole term (decoder_v2.label_of without gemma's pass B).

  inventory  (code only) on the tuning papers (dev + held_a): every entry the rescue adds, with the unit text, and
             the decoding key's printed pairs it recovers  -> output/boundary_ab/INVENTORY.txt, added.json
  decode     (nimble) the key columns (legend_scope.columns) of the papers with added entries, decoded with the
             inventory as it is and with the added entries, in one session (identical questions answered once):
             coded rows right gained / lost, plain cells changed  -> output/boundary_ab/DECODE.txt, <paper>.json

    python boundary_ab.py inventory | decode | report
TREE_OUTPUT picks the root whose inventory is used (output_frozen_109: the frozen run's).
"""
from __future__ import annotations

import collections
import json
import re
import sys
import time

import _paths
import column_tree as ct
import decode_chain as dc
import decode_inv as di
import decode_units as du
import decoder as v1
import decoder_v2 as v2
import full_run_v24 as fr
import legend_inventory as li
import legend_scope as ls

OUT = _paths.OUTPUT / "boundary_ab"
WINDOW = 90


def enumerated(code, term, text):
    """The start of 'N. term' / 'N) term' / 'N: term' for a numeric code N, or None."""
    words = re.findall(r"[^\W_]+", term)
    if not words:
        return None
    t = r"[\W_]+".join(map(re.escape, words))
    for f in v2.forms(code):
        if not re.fullmatch(r"\d{1,2}", f):
            continue
        m = re.search(rf"(?<![\d.,]){re.escape(f)}\s*[.):]\s*{t}", text, flags=re.I)
        if m:
            return m.start()
    return None


def rescued(paper):
    """[(entry as the inventory keeps it, unit, snippet)] for the dropped entries the enumeration rule grounds."""
    inv = json.loads((li.OUT / f"{paper}.json").read_text(encoding="utf-8"))
    have = {(e.get("variable", "").lower(), e.get("code"), (e.get("term") or "").lower()) for e in inv["categories"]}
    out, seen = [], set()
    for d in inv.get("dropped", []):
        code, term = d.get("code") or "", d.get("term") or ""
        if not code or not term or li.MARKER.search(term):
            continue
        k = (d.get("variable", "").lower(), code, term.lower())
        if k in have or k in seen:
            continue
        for u in inv["units"]:
            i = enumerated(code, term, u["text"])
            if i is not None:
                label, expl = v2.label_of(term, None)
                e = {"variable": d.get("variable", ""), "code": code, "term": term, "unit": u["id"],
                     "label": label, "explanation": expl, "rescued": "enumeration"}
                a = max(0, i - WINDOW)
                out.append((e, u, " ".join(u["text"][a:i + WINDOW].split())))
                seen.add(k)
                break
    return out


def inventory():
    OUT.mkdir(parents=True, exist_ok=True)
    added, L = {}, []
    tot = collections.Counter()
    for p in ls.tuning_papers():
        if not (li.OUT / f"{p}.json").exists():
            continue
        got = rescued(p)
        if not got:
            continue
        added[p] = [e for e, _u, _s in got]
        cats = di.inventory(p) or []
        more = cats + [v2.strip_own_code(dict(e)) for e in added[p]]
        found = ls.key_of(p)
        weight = {(r["trait"], r["cell"]): r["w"] for r in v2.score_dir_from(p, found, lambda e: None)}
        rec = []
        for T, e in found.items():
            if e["kind"] != "coded":
                continue
            for code, term in e["coded"].items():
                if e["where"][code] in v1.NO_LEGEND:
                    continue
                if not di.captured(cats, code, term) and di.captured(more, code, term):
                    rec.append(f"'{code}' -> '{term}' ({T}, x{weight.get((T, code), 1)})")
                    tot["pairs"] += 1
                    tot["rows"] += weight.get((T, code), 1)
        tot["entries"] += len(got)
        L.append(f"{p} [{ls.SPLIT[p]}]: {len(got)} entries added; key pairs recovered: {', '.join(rec) or 'none'}")
        for e, u, s in got:
            L.append(f"    '{e['code']}' = '{e['term']}'  (variable '{e['variable']}'; {u['id']} {u['kind']})")
            L.append(f"        {s}")
    head = [f"experiment A, the enumeration rescue: {tot['entries']} entries added in {len(added)} tuning papers; "
            f"key pairs recovered {tot['pairs']} ({tot['rows']} species rows)", ""]
    (OUT / "added.json").write_text(json.dumps(added, indent=1, ensure_ascii=False), encoding="utf-8")
    (OUT / "INVENTORY.txt").write_text("\n".join(head + L) + "\n", encoding="utf-8")
    print("\n".join(head + L))


def decode():
    added = json.loads((OUT / "added.json").read_text(encoding="utf-8"))
    head = fr.head_runs()
    client = None
    for p, extra in added.items():
        f = OUT / f"{p}.json"
        if f.exists() or p not in head:
            continue
        found = ls.key_of(p)
        if not any(e["kind"] == "coded" for e in found.values()):
            continue
        cats = di.inventory(p) or []
        more = cats + [v2.strip_own_code(dict(e)) for e in extra]
        cols = ls.columns(p, head, found)
        units = du.unit_texts(p)
        client = client or ls.Memo(ct.DecisionClient(v1.NIMBLE, 1))
        res, t0 = {"_columns": {k: list(v) for k, v in cols.items()}}, time.time()
        for name, pool in (("control", cats), ("rescued", more)):
            res[name] = {k: fr._retry(lambda: ls.decode_column(client, h, vals, pool, units, set()))
                         for k, (h, vals) in cols.items()}
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  {p:22s} {len(cols)} columns ({time.time() - t0:.0f}s)", flush=True)
    if client:
        v1.unload(v1.NIMBLE)
    report()


def report():
    rows = {"control": [], "rescued": []}
    for f in sorted(OUT.glob("*.json")):
        if f.stem == "added":
            continue
        res = json.loads(f.read_text(encoding="utf-8"))
        found = ls.key_of(f.stem)
        for n in rows:
            dec = res[n]
            rows[n] += v2.score_dir_from(f.stem, found, lambda e: dc.lookup(dec, e["table"], e["col"]))
    ok = ls.RIGHT + ls.WORDING
    L = [f"experiment A, decode: {len({r['paper'] for r in rows['control']})} papers with added entries, "
         f"the inventory as it is (control) and with the rescued entries", ""]
    for n, rs in rows.items():
        coded = [r for r in rs if r["kind"] == "coded" and r["out"] not in ("no legend printed", "GT error")]
        kept = [r for r in rs if r["kind"] == "kept"]
        L.append(f"  {n:8s} coded right {sum(r['w'] for r in coded if r['out'] in ls.RIGHT)} "
                 f"(+{sum(r['w'] for r in coded if r['out'] in ls.WORDING)} wording) of {sum(r['w'] for r in coded)};  "
                 f"plain kept {sum(r['w'] for r in kept if r['out'] == 'right')} of {sum(r['w'] for r in kept)};  "
                 f"not-printed pairs decoded anyway "
                 f"{sum(r['w'] for r in rs if r['out'] == 'no legend printed' and r['have'] != r['cell'])}")
    base = {(r["paper"], r["trait"], r["cell"]): r for r in rows["control"]}
    gains, losses, moved = [], [], []
    for r in rows["rescued"]:
        b = base.get((r["paper"], r["trait"], r["cell"]))
        if not b or b["have"] == r["have"]:
            continue
        line = (f"    {r['paper']:16s} {r['trait'][:26]!r:28s} '{r['cell']}' -> want '{r['want'][:24]}': "
                f"'{b['have'][:28]}' -> '{r['have'][:28]}'  (x{r['w']}, {b['out']} -> {r['out']})")
        a, z = b["out"] in ok, r["out"] in ok
        (gains if z and not a else losses if a and not z else moved).append((r["w"], line))
    L += ["", f"rescued against control: right gained {sum(w for w, _ in gains)} rows, lost {sum(w for w, _ in losses)}, "
              f"other changes {sum(w for w, _ in moved)}"]
    for title, xs in (("gained", gains), ("lost", losses), ("changed, neither right", moved)):
        if xs:
            L.append(f"  {title}:")
            L += [x for _w, x in sorted(xs, key=lambda t: -t[0])]
    (OUT / "DECODE.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    {"inventory": inventory, "decode": decode, "report": report}[sys.argv[1]]()
