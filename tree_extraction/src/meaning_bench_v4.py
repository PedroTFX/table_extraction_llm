"""
meaning_bench_v4.py — v3 (three-way judge, meaning v2 frozen) with ONE change: who
may be judged at all. A label is judged only when every part of it says something:

  whole label   every component that builds the assembled label is checked — the
                group cells, the leaf name and the details ('Traits', 'CL', 'M' in
                'Traits CL M'), not just the leaf. An abbreviation-like token with no
                definition the paper supplied (an accepted meaning-v2 answer for
                this paper) makes the label unresolved: 'M = mean' does not say what
                'CL' is.
  specific name a label with no column-specific name is unresolved: gemma's
                'Traits (8)' — the ' (8)' is the pipeline's duplicate suffix
                (tables._build_columns adds ' (n)' only when the bare name came
                earlier in the same table, so it is checked that way, not assumed)
                — and a base or a head label that several columns share names a
                group, not a column.

Plain words are NOT required to be defined ('Dry tolerant', 'Body Size'): an
understandable name in other words is still judged. An unresolved label gets no
synonym question and no credit, and stays apart from 'different trait'.

    python meaning_bench_v4.py
-> tree_extraction/output/meaning_bench_v4/{rows.json, summary.txt, report.html}
"""

from __future__ import annotations

import collections
import json
import re
import shutil
import sys

import _paths
import meaning as mn
import meaning_bench_v2 as mb2
import meaning_bench_v3 as m3

OUT = _paths.OUTPUT / "meaning_bench_v4"
SUFFIX = re.compile(r"(.+) \((\d+)\)")


def defined_tokens(paper):
    """Tokens of this paper the frozen meaning step gave an accepted meaning."""
    out = set()
    for key, rec in mb2.TOKENS.items():
        if key.split("|", 1)[0] == paper:
            out |= {t for t, v in (rec.get("tokens") or {}).items() if v}
    return out


def _abbrev(component):
    return [t for t in re.findall(r"[A-Za-z][A-Za-z0-9]*\.?", component) if mn.looks_abbreviated(t)]


def gate(who, ctx):
    lab = ctx["label"]
    if not lab:
        return False, "no name"
    if who == "head":
        components = [*ctx["groups"], ctx["name"], *ctx["details"]]
        shared = sum(1 for x in ctx["head_labels"] if x == lab)
        if shared > 1:
            return False, f"no column-specific name: '{lab}' heads {shared} columns"
    else:
        names = ctx["gemma_names"]
        mt = SUFFIX.fullmatch(lab)
        base = mt.group(1) if mt and mt.group(1) in names else lab   # a generated suffix?
        bases = [(SUFFIX.fullmatch(n).group(1) if SUFFIX.fullmatch(n)
                  and SUFFIX.fullmatch(n).group(1) in names else n) for n in names]
        shared = bases.count(base)
        if shared > 1:
            return False, (f"no column-specific name: '{base}' heads {shared} columns"
                           + (f" ('{lab}' is the pipeline's duplicate suffix)" if base != lab else ""))
        components = [base]
    known = defined_tokens(ctx["paper"])
    for comp in components:
        for tok in _abbrev(comp):
            if tok not in known and tok.rstrip(".") not in known:
                return False, f"undefined in the paper: '{tok}' (in '{comp}')"
    return True, "every part of the label is understood"


def regression(rows):
    """The checks named for this run."""
    L = ["regression checks:"]
    for r in rows:
        if r["paper"] == "Oliveira2022":
            for who in ("head", "gemma"):
                lab = r["label"] if who == "head" else r["gemma_name"]
                L.append(f"  {who:5s} Oliveira '{lab}' ~ '{r['trait']}': "
                         f"{'JUDGED' if r[f'{who}_eligible'] else 'unresolved'} — {r.get(f'{who}_gate', '')}")
    verified = [("Braschler2021", "Dry tolerant"), ("Ibarra2021", "Mean length (mm) ± SD"),
                ("Rebrina2022", "Body Size (mm)")]
    for r in rows:
        if (r["paper"], r["label"]) in verified:
            j = r["judge"].get("head", {})
            L.append(f"  verified credit {r['paper']} t{r['table']} '{r['label']}' ~ '{r['trait']}': "
                     f"{'judged, ' + j.get('answer', '?') if r['head_eligible'] else 'BLOCKED — ' + r.get('head_gate', '')}")
    return L


def main(argv):
    OUT.mkdir(parents=True, exist_ok=True)
    src = m3.OUT / "judge3.json"
    if src.exists() and not (OUT / "judge3.json").exists():
        shutil.copy(src, OUT / "judge3.json")             # v3's answers: only new questions are asked
    m3.OUT, m3.GATE = OUT, gate
    rows = m3.run()
    s = m3.summary(rows)
    blocked = collections.Counter(r.get(f"{w}_gate", "").split(":")[0] for r in rows for w in ("head", "gemma")
                                  if not r[f"{w}_eligible"] and not r[f"{w}_meaning"] and r.get(f"{w}_gate"))
    s += "\n" + "\n".join(regression(rows)) + "\n\nnot judged, by reason (head + gemma):\n" + "\n".join(
        f"  {k:40s}{v}" for k, v in blocked.most_common())
    (OUT / "summary.txt").write_text(s, encoding="utf-8")
    import meaning_report
    meaning_report.write(rows, {"held-out": m3.tallies([r for r in rows if not r["dev"]]),
                                "development": m3.tallies([r for r in rows if r["dev"]])},
                         OUT / "report.html")
    print(s)


if __name__ == "__main__":
    main(sys.argv[1:])
