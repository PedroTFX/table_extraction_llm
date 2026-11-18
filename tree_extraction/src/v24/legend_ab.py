"""legend_ab.py — the decoder's legend prompts, old examples against new (legend_variants.py), one prompt at a time.

  papers    the tuning papers (dev + held_a of split_v15.json) with coded columns in the decoding key
  inventory legend_inventory.build, as the full run builds it (fixed units and batches, passes A, C, B), once with
            the current prompts ('old') and once per variant, in one session. gemma runs at temperature 0 and a
            prompt asked before is answered from the cache, so a variant costs only the calls its prompt changes
  key       the decoding key (decoder.load_key): the code -> term pairs the curators decoded, weighted by the
            rows that carry the code; pairs whose legend the paper does not print, and GT errors, left out
  score     captured  the inventory holds an entry for the cell whose term or name is the GT value
                      (decode_inv.captured: what pass A and C must find)
            name      of those, an entry whose NAME is exactly the GT value (what pass B must cut)
            entries   the inventory's size, entries dropped by the boundary check
            'stored': the inventories of the last full run, built in an earlier session: a rough drift reference

    python legend_ab.py run [variant ...]     resumable: output/legend_ab/<variant>/<paper>.json
    python legend_ab.py score                 -> output/legend_ab/SCORE.txt
"""
import collections
import contextlib
import json
import sys
import time

import _paths
import decode_inv as dinv
import decoder as v1
import decoder_v2 as v2
import legend_inventory as li
import legend_variants as lv

OUT = _paths.OUTPUT / "legend_ab"
SPLIT = json.loads((_paths.SUB / "output/eval_split/split_v15.json").read_text(encoding="utf-8"))["assign"]
TUNING = ("dev", "held_a")
ORDER = ["old", "organise", "labels", "uncoded", "all"]
MODULE = {"ORGANISE": v1, "LABELS": v2, "UNCODED": v2}


class Memo:
    """v1.gemma and v2._chat answered once per identical prompt in this session."""

    def __init__(self):
        self.cache, self.asked, self.reused = {}, 0, 0
        self.gemma, self.chat = v1.gemma, v2._chat

    def _get(self, key, fn):
        if key in self.cache:
            self.reused += 1
        else:
            self.cache[key] = fn()
            self.asked += 1
        return json.loads(json.dumps(self.cache[key]))

    def install(self):
        v1.gemma = lambda prompt, timeout=900: self._get(("A", prompt), lambda: self.gemma(prompt, timeout))
        v2._chat = lambda prompt, schema, field, timeout=900: self._get(
            (field, prompt), lambda: self.chat(prompt, schema, field, timeout))


@contextlib.contextmanager
def applied(variant):
    saved = {name: getattr(mod, name) for name, mod in MODULE.items()}
    try:
        for name, text in lv.VARIANTS.get(variant, {}).items():
            setattr(MODULE[name], name, text)
        yield
    finally:
        for name, text in saved.items():
            setattr(MODULE[name], name, text)


def papers():
    key = v1.load_key()
    return [p for p in li.coded_papers() if SPLIT.get(p) in TUNING and p in key]


def run(variants):
    memo = Memo()
    memo.install()
    for p in papers():
        t0 = time.time()
        for v in ["old"] + [x for x in variants if x != "old"]:
            f = OUT / v / f"{p}.json"
            if f.exists():
                continue
            with applied(v):
                inv = li.build(p)
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(json.dumps({k: inv[k] for k in ("paper", "calls", "categories", "dropped")}, indent=1,
                                    ensure_ascii=False), encoding="utf-8")
        print(f"  [legend_ab] {p:22s} {memo.asked} calls asked, {memo.reused} reused ({time.time() - t0:.0f}s)",
              flush=True)
    v1.unload(v1.GEMMA)


def cats_of(variant, paper):
    f = (li.OUT if variant == "stored" else OUT / variant) / f"{paper}.json"
    if not f.exists():
        return None, None
    d = json.loads(f.read_text(encoding="utf-8"))
    return [v2.strip_own_code(dict(e)) for e in d["categories"]], d


def named(cats, cell, want, header=""):
    """An entry offered for the cell whose name is exactly the GT value."""
    _ev, es = v2.candidates(cats, cell, header)
    return any(v1._flat(e.get("label") or "") == v1._flat(want) for e in es)


def score():
    key = v1.load_key()
    variants = ["stored"] + [v for v in ORDER if (OUT / v).exists()]
    rows = {}                                       # paper -> [(cell, want, weight, header)]
    for p in papers():
        rr = []
        for r in v2.score_dir_from(p, key[p], lambda e: None):
            if r["kind"] != "coded" or r["out"] == "no legend printed" or (p, r["cell"]) in v1.GT_ERRORS \
                    or ((p, "*") in v1.GT_ERRORS):
                continue
            rr.append((r["cell"], r["want"], r["w"], r.get("header", "")))
        rows[p] = rr
    res = {}
    for v in variants:
        c = collections.Counter()
        per = {}
        for p, rr in rows.items():
            cats, d = cats_of(v, p)
            if cats is None:
                continue
            got = {}
            for cell, want, w, _h in rr:
                cap = dinv.captured(cats, cell, want)
                nam = named(cats, cell, want)
                for g in ("all", SPLIT[p]):
                    c[(g, "rows")] += w
                    c[(g, "pairs")] += 1
                    c[(g, "cap rows")] += w * cap
                    c[(g, "cap pairs")] += cap
                    c[(g, "name rows")] += w * nam
                got[cell] = (cap, nam)
            for g in ("all", SPLIT[p]):
                c[(g, "papers")] += 1
                c[(g, "entries")] += len(cats)
                c[(g, "dropped")] += len(d.get("dropped", []))
            per[p] = got
        res[v] = (c, per)
    L = ["Decoder legend prompts: old examples against new, one prompt at a time. Key: decoder.load_key (coded pairs",
         "whose legend the paper prints), weighted by rows. 'captured': the inventory holds an entry for the code whose",
         "term or name is the GT value; 'name': an entry whose name is exactly the GT value. 'stored' is the last full",
         "run's inventory (an earlier session): a rough drift reference for 'old'.", ""]
    for v in variants:
        c, _per = res[v]
        L.append(f"== {v}")
        for g in ("all",) + TUNING:
            if not c[(g, "papers")]:
                continue
            r, n = c[(g, "rows")], c[(g, "pairs")]
            L.append(f"  {g:6s} {c[(g, 'papers')]:3d} papers  captured {c[(g, 'cap rows')]}/{r} rows "
                     f"({c[(g, 'cap rows')] / max(r, 1):.1%}), {c[(g, 'cap pairs')]}/{n} pairs   name "
                     f"{c[(g, 'name rows')]}/{r} rows ({c[(g, 'name rows')] / max(r, 1):.1%})   entries "
                     f"{c[(g, 'entries')]}, dropped {c[(g, 'dropped')]}")
        L.append("")
    L.append("Pairs that changed against 'old' (cell: old -> new, captured / name):")
    base = res.get("old", (None, {}))[1]
    for v in variants:
        if v == "old":
            continue
        for p, got in res[v][1].items():
            for cell, now in got.items():
                was = base.get(p, {}).get(cell)
                if was is not None and was != now:
                    L.append(f"  {v:9s} {p:22s} '{cell}': captured {was[0]}->{now[0]}, name {was[1]}->{now[1]}")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "SCORE.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


def main(argv):
    if argv[:1] == ["score"]:
        return score()
    variants = argv[1:] or ORDER[1:]
    bad = [v for v in variants if v not in lv.VARIANTS and v != "old"]
    assert not bad, f"unknown variants {bad}"
    run(variants)


if __name__ == "__main__":
    main(sys.argv[1:])
