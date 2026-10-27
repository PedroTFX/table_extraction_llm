"""
decode_misses.py — AUDIT (no model): where each remaining decodable miss of decoder v2
fails, stage by stage, weighted by species rows.

Stages, first failing one wins:
  1 gather      the GT term is not in the passages gemma saw
  2 gemma       the term is in the passages, but no verified entry/category has it
  3 offered     an entry has it, but it was not offered for the cell (code forms /
                initials did not match)
  4 QK word     offered, nimble called the value a word
  5 QV keep     nimble kept the code
  6 QV other    nimble chose another entry
  7 QB wording  the right entry, but another wording was recorded
Only rows whose legend is printed (decode_key.where) are counted.

    python decode_misses.py   -> output/decode_key/decoder_v2/MISSES.txt
"""

from __future__ import annotations

import collections
import json

import decoder as v1
import decoder_v2 as v2


def stage(r, org, cell_rec):
    want = v1._flat(r["want"])
    if want not in v1._flat(" ".join(org["passages"])):
        return "1 gather"
    cats = org["categories"]
    holding = [e for e in cats if want in v1._flat(e.get("term") or e["label"])]
    if not holding:
        return "2 gemma"
    offered = (cell_rec or {}).get("options", {})
    labels = [l for o in offered.values() for l in o.get("labels", [])]
    if not any(want in v1._flat(l) or v1._flat(l) in want
               for l in labels + [e.get("term", "") for e in holding if e["label"] in labels]):
        return "3 not offered"
    probs = (cell_rec or {}).get("probs", {})
    qk = [v for k, v in probs.items() if k.endswith("| QK")]
    if qk and all(max(p, key=p.get) == "word" for p in qk if p):
        return "4 QK word"
    if not cell_rec or cell_rec.get("term") is None:
        return "5 QV keep"
    if any(k.endswith("| QB") for k in probs) and r["out"] == "right, longer wording":
        return "7 QB wording"
    if r["out"] in ("right, longer wording", "right, shorter wording"):
        return "7 QB wording"
    return "6 QV other"


def main():
    rows = v2.score_dir(v2.OUT, v1.dev_papers())
    key = v1.load_key()
    tally, examples = collections.Counter(), collections.defaultdict(list)
    for r in rows:
        if r["kind"] != "coded" or r["out"] in ("right", "right, unit inside",
                                                "no legend printed", "GT error"):
            continue
        org = json.loads((v2.OUT / "organise" / f"{r['paper']}.json").read_text(encoding="utf-8"))
        m = json.loads((v2.OUT / "match" / f"{r['paper']}.json").read_text(encoding="utf-8"))
        e = key[r["paper"]][r["trait"]]                 # the key's own table:column
        cell_rec = m.get(f"{e['table']}:{e['col']}", {}).get("cells", {}).get(r["cell"])
        s = stage(r, org, cell_rec)
        tally[s] += r["w"]
        examples[s].append(f"{r['paper']} '{r['trait'][:24]}' '{r['cell']}' -> want "
                           f"'{r['want'][:40]}', have '{r['have'][:50]}' (rows {r['w']})")
    L = ["decoder v2: remaining decodable misses by stage (species rows)", ""]
    L += [f"  {s:16s}{v:6d}" for s, v in sorted(tally.items())]
    for s in sorted(examples):
        L += ["", f"{s}:"] + [f"  {x}" for x in examples[s]]
    out = v2.OUT / "MISSES.txt"
    out.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
