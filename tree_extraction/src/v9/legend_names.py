"""Trait names from the paper's own legends (v9). The meaning step finds a column name's
definition only through text shapes ('term (ABBR)', 'ABBR = term') and only for tokens that look
abbreviated, so a column the paper defines in a legend table stays as printed (Noriega2023 'HW',
'PH' -> GT 'head width', 'pronotum height'). The legend inventory (legend_inventory.py) already
holds those definitions: entries whose code is the column's name and whose variable names it.

  code     candidates: for each trait column whose name the meaning step left as printed, the
           inventory variables whose code is that name (units in brackets ignored, case
           ignored), each with the entry it comes from. Code never makes a name up.
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


def candidates(name, cats):
    """[{"term", "entry"}]: the variables the legends give the code `name`."""
    base, out, seen = _base(name), [], set()
    if not base:
        return out
    for e in cats:
        code, var = str(e.get("code") or "").strip(), str(e.get("variable") or "").strip()
        if not code or not var or code.lower() != base or _base(var) == base or _base(var) in seen:
            continue
        seen.add(_base(var))
        what = "; ".join(x for x in (e.get("label"), e.get("explanation")) if x)[:120]
        out.append({"term": var, "entry": f"code '{code}' under '{var}'" + (f" ({what})" if what else "")})
    return out


def ask_name(client, name, header_ctx, cands):
    crit = {f"c{i}": f"'{c['term']}' — the paper's legend lists {c['entry']}" for i, c in enumerate(cands)}
    crit["none"] = (f"none of these is the full name of '{name}' (one may be the trait it is a "
                    f"category of, or an unrelated entry)")
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
