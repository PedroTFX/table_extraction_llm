"""Trait names from the paper's own legends (v9). The meaning step finds a column name's
definition only through text shapes ('term (ABBR)', 'ABBR = term') and only for tokens that look
abbreviated, so a column the paper defines in a legend table stays as printed (Noriega2023 'HW',
'PH' -> GT 'head width', 'pronotum height'). The legend inventory (legend_inventory.py) already
holds those definitions: entries whose code is the column's name.

  code     candidates: for each trait column whose name the meaning step left as printed, every
           inventory entry whose code is that name (units in brackets ignored, case ignored)
           offers both its variable and its term — which one names the column differs by legend
           ('HW' under 'Head width (mm)'; 'HL' under 'Morphological trait', term 'Head length') —
           each saying where it comes from and which other codes share it. Code never makes a
           name up. (Iteration 2, 2026-10-28: iteration 1 offered the variable only, and nimble
           took lone group headings: Yates 'HL' -> 'Morphological trait', mean F1 0.518 -> 0.515.)
  Q-NAME   one question per column with candidates: which one is the full name of the column
           in this paper, or none ('Sprawler' under 'Locomotion' is a category, not a name).
           Sure (p >= SURE) -> the column's name; else it stays as printed.

    python full_run_v9.py v9:names <papers>     writes <run>/legend_names/<paper>.json and
                                                updates <run>/meaning/<paper>.json
"""
import json
import re

import column_tree as ct
import decoder as v1
import full_run as fr
import legend_inventory as li

SURE = 0.8


def _base(name):
    """The name without bracketed units, lower case: 'HW (mm)' -> 'hw'."""
    return re.sub(r"\s*[\(\[][^)\]]*[\)\]]", "", str(name or "")).strip().lower()


def entries(paper):
    f = li.OUT / f"{paper}.json"
    return json.loads(f.read_text(encoding="utf-8")).get("categories") or [] if f.exists() else []


def _parsed(term):
    """Objective parse checks on an inventory field (they drop artefacts such as the joined
    'S5, S6 | TRAITS'; they judge nothing about meaning): a letter first, three letters, no '|'."""
    t = str(term or "").strip()
    return bool(t) and t[0].isalpha() and sum(ch.isalpha() for ch in t) >= 3 and "|" not in t


def candidates(name, cats):
    """[{"term", "entry"}]: for each inventory entry whose code is `name`, both the variable it
    is listed under and the term it gives the code — which one is the column's name differs by
    legend ('HW' under 'Head width (mm)'; 'HL' under 'Morphological trait' with term 'Head
    length'). Each candidate says where it comes from and which other codes share it."""
    base, out, seen = _base(name), [], set()
    if not base:
        return out
    codes_of = {}                                   # a variable or term -> the codes it is given
    for e in cats:
        code = str(e.get("code") or "").strip()
        for k in ("variable", "term"):
            if code and _parsed(e.get(k)):
                codes_of.setdefault(_base(e[k]), set()).add(code)
    for e in cats:
        code = str(e.get("code") or "").strip()
        if not code or code.lower() != base:
            continue
        var, term = str(e.get("variable") or "").strip(), str(e.get("term") or "").strip()
        for kind, x in (("term", term), ("variable", var)):
            if not _parsed(x) or _base(x) in (base, *seen):
                continue
            seen.add(_base(x))
            others = sorted(codes_of.get(_base(x), set()) - {code})
            where = (f"the term the legend gives code '{code}' (listed under '{var}')" if kind == "term"
                     else f"the heading code '{code}' is listed under")
            if others:
                where += (f"; the legend gives this same name to {len(others)} other code(s): "
                          + ", ".join(f"'{o}'" for o in others[:6]))
            out.append({"term": x, "entry": where})
    return out


def ask_name(client, name, header_ctx, cands):
    crit = {f"c{i}": f"'{c['term']}' — {c['entry']}" for i, c in enumerate(cands)}
    crit["none"] = (f"none of these is the full name of '{name}': a heading shared by several "
                    f"columns (a group of traits, or the trait whose categories the columns are), "
                    f"or an unrelated entry")
    state = (f"A table in a scientific paper has a trait column named '{name}'"
             + (f"; its other columns are {header_ctx}" if header_ctx else "") + ". The options quote "
             "the paper's legends that list the code '" + name + "'.")
    ch, probs = v1.ask(client, state, f"What is the full name of the column '{name}' in this paper?", crit)
    term = cands[int(ch[1:])]["term"] if ch and ch.startswith("c") and probs.get(ch, 0) >= SURE else None
    return term, ch, probs


def run(run_dir, papers):
    """One paper at a time; resumable (run_dir/legend_names/<paper>.json). The trait columns are the
    ones full_run.plan gives (the caller installs its layers)."""
    out = run_dir / "legend_names"
    out.mkdir(parents=True, exist_ok=True)
    head = fr.head_runs()
    client = None
    for p in papers:
        f = out / f"{p}.json"
        if f.exists() or p not in head:
            continue
        mf = run_dir / "meaning" / f"{p}.json"
        names = json.loads(mf.read_text(encoding="utf-8")) if mf.exists() else {}
        cats = entries(p)
        res = {}
        for t, fields, _o, _x in fr.plan(p, head):
            heads = [c.name for c in t.columns]
            for c in t.columns:
                if fields.get(c.name) != "measurementType" or c.name in res:
                    continue
                if _base(names.get(c.name) or c.name) != _base(c.name):
                    continue                        # the meaning step already spelled it out
                cands = candidates(c.name, cats)
                if not cands:
                    continue
                client = client or ct.DecisionClient(v1.NIMBLE, 1)
                ctx = ", ".join(f"'{h}'" for h in heads[:10] if h != c.name)
                term, ch, probs = ask_name(client, c.name, ctx, cands)
                res[c.name] = {"candidates": cands, "choice": ch, "probs": probs, "term": term}
                if term:
                    names[c.name] = term
        if res:
            mf.write_text(json.dumps(names, indent=1, ensure_ascii=False), encoding="utf-8")
            print(f"  [names] {p:22s} " + "; ".join(f"{k} -> {v['term'] or '(kept)'}" for k, v in res.items())[:300],
                  flush=True)
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    if client:
        v1.unload(v1.NIMBLE)
