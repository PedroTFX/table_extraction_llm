"""What a table holds, and what its doubtful columns are (output/column_review: the person's
table-by-table review of 2026-10-20, five papers of the 'trait columns mis-tagged' group).
The same questions for every table the run would take rows from; nimble decides from printed
headers, cells and the text above and below the table; code applies the answers to the tags.

  Q-KIND   traits / figure / model / sampling / other        (rules 1-3 of the review)
           anything but 'traits' (>= SURE) -> the table gives no rows
  Q-COL    (a table read long without the structure step's confirmation) per value column:
           statistic / trait / label                           (rule 4: 'Mean' / 'Range' rows)
  Q-ROLE   per column tagged caste / sex / lifeStage: context / trait   (rule 6: Melo 'FG')

    python full_run_v7.py kind <papers>      writes <run>/kind/<paper>.json
"""
import json
import re

import column_tree as ct
import decoder as v1
import full_run as fr
import structure_tree as st

SURE = 0.8
CONTEXT_TAGS = {"caste", "sex", "lifeStage"}
N_IN_LABEL = re.compile(r"^(.*?\S)\s*\(\s*n\s*=\s*(\d+)\s*\)\s*$", re.I)


def _flat(s):
    return " ".join(str(s or "").split())


def caption_below(table, flat, spans):
    """The text printed directly below the table (up to the next table), at most 300
    characters: figure captions follow the numbers read off the figure."""
    import decoder_v3 as v3
    i = v3.locate_table(table, spans)
    if i is None:
        return ""
    end = spans[i + 1][0] if i + 1 < len(spans) else len(flat)
    below = _flat(re.sub(r"<[^>]+>|<!--.*?-->", " ", flat[spans[i][1]:end]))
    return below[:300]


def _shown(t, n=3, cols=10):
    return " | ".join("row %d: " % (i + 1) + "; ".join(
        f"'{c.name}' = '{_flat(r.get(c.name))}'" for c in t.columns[:cols] if _flat(r.get(c.name)))
        for i, r in enumerate(t.records[:n]))


def _distinct(t, col, k=8):
    out = []
    for r in t.records:
        v = _flat(r.get(col.name))
        if v and v not in out:
            out.append(v)
    return out[:k]


KIND_OPTIONS = {          # Q-KIND's options (v13's subject step quotes them in its clash duel)
    "traits": ("organisms (species, genera, families or specimens) with their traits or "
               "measured characteristics, printed as data"),
    "figure": ("numbers read off a figure: a plot, boxplot, scatter or bar chart (often "
               "approximate values marked '~'), not a table printed in the paper"),
    "model": ("results of statistical tests or models: estimates, t, p, F, R², AIC, "
              "contrasts or correlations"),
    "sampling": ("sampling data: counts, abundances or occurrences per site, sampling "
                 "effort, pollen or prey collected, environmental or site measurements"),
    "other": "methods, protocols, definitions, or lists of names without values"}


def ask_kind(client, t, above="", below=""):
    state = f"A table in a scientific paper has the columns {[c.name for c in t.columns][:14]}."
    if above:
        state += f" The text printed directly above it: '{above}'."
    if below:
        state += f" The text printed directly below it: '{below}'."
    state += f" Its first rows read: {_shown(t)}."
    return v1.ask(client, state, "What does this table hold?", dict(KIND_OPTIONS))


def ask_also(client, t, above="", below=""):
    """Q-ALSO, after a sure 'sampling': species lists often print each species' guild, diet or
    nesting beside its counts per site (Pereira, Nunes, McCune)."""
    state = f"A table in a scientific paper has the columns {[c.name for c in t.columns][:14]}."
    if above:
        state += f" The text printed directly above it: '{above}'."
    if below:
        state += f" The text printed directly below it: '{below}'."
    state += f" Its first rows read: {_shown(t)}."
    return v1.ask(client, state, "Besides any counts or site data, does the table give each "
                  "organism a characteristic of its own?", {
        "yes": ("yes: at least one column gives each organism a trait of its own, such as its "
                "functional group, guild, diet, nesting, habitat, body size or biomass"),
        "no": "no: every column is counts, abundances, occurrences, effort or site data"})


def ask_col(client, t, col, above=""):
    vals = ", ".join(f"'{v}'" for v in _distinct(t, col))
    state = (f"A table in a scientific paper has the columns {[c.name for c in t.columns][:14]}."
             + (f" The text printed directly above it: '{above}'." if above else "")
             + f" Its first rows read: {_shown(t)}. The column '{col.name}' holds: {vals}.")
    return v1.ask(client, state, f"What does the column '{col.name}' say about each row?", {
        "statistic": ("which statistic the row's values are: mean, SD, range, minimum, "
                      "maximum, median"),
        "trait": "a trait of the organism: its measured value or its category",
        "label": "a number or label identifying the row, a group, cluster, site or sample"})


def ask_role(client, t, col, above=""):
    vals = ", ".join(f"'{v}'" for v in _distinct(t, col))
    state = (f"A table in a scientific paper has the columns {[c.name for c in t.columns][:14]}."
             + (f" The text printed directly above it: '{above}'." if above else "")
             + f" The column '{col.name}' holds: {vals}.")
    return v1.ask(client, state, f"What do the values of the column '{col.name}' say?", {
        "context": ("which caste, sex or life stage the row is about (worker, queen, male, "
                    "female, larva, adult)"),
        "trait": ("a trait of the organism: its group, behaviour, diet, habitat, size or "
                  "another characteristic, possibly as a code explained in a legend")})


def unconfirmed_long(fields, dec):
    """Read long only because tags say so: the structure step did not confirm a names column."""
    return st.reads_long(fields) and (not dec or dec.get("action") == "v4")


def decide_table(client, t, fields, dec, above, below, org_col=None):
    res = {"cols": {}}
    if org_col:
        res["organism"] = org_col
    ch, probs = ask_kind(client, t, above, below)
    res["kind"] = {"choice": ch, "probs": probs}
    if ch != "traits" and probs.get(ch, 0) >= SURE:
        res["action"] = "no rows"
        recheck_sampling(client, t, res, above, below)
        if res["action"] == "no rows":
            return res
    res["action"] = "keep"
    return ask_columns(client, t, fields, dec, above, res)


def ask_columns(client, t, fields, dec, above, res):
    if unconfirmed_long(fields, dec):
        for c in t.columns:
            if fields.get(c.name) == "measurementValue":
                c2, p2 = ask_col(client, t, c, above)
                res["cols"][c.name] = {"q": "col", "choice": c2, "probs": p2}
    for c in t.columns:
        if fields.get(c.name) in CONTEXT_TAGS:
            c2, p2 = ask_role(client, t, c, above)
            res["cols"][c.name] = {"q": "role", "choice": c2, "probs": p2}
    return res


def recheck_sampling(client, t, res, above, below):
    """A sure 'sampling' table is kept when Q-ALSO says (sure) its organisms carry traits too."""
    if res.get("action") != "no rows" or res["kind"]["choice"] != "sampling" or "also" in res:
        return False
    ch, probs = ask_also(client, t, above, below)
    res["also"] = {"choice": ch, "probs": probs}
    if ch == "yes" and probs.get(ch, 0) >= SURE:
        res["action"] = "keep"
    return True


NEW_TAG = {("col", "statistic"): "measurementStatistic", ("col", "trait"): "measurementType",
           ("col", "label"): "none", ("role", "trait"): "measurementType"}


def apply(fields, res):
    """The tags with the answers applied. Q-COL answers count only when every value column
    of the table was answered sure, so a table is never half re-read."""
    out = dict(fields)
    if not res:
        return out
    if res.get("action") == "no rows":
        return {k: ("none" if v in fr.TRAITS else v) for k, v in out.items()}
    cols = res.get("cols") or {}
    col_q = {k: a for k, a in cols.items() if a["q"] == "col"}
    if col_q and all(a["probs"].get(a["choice"], 0) >= SURE for a in col_q.values()):
        for k, a in col_q.items():
            out[k] = NEW_TAG[("col", a["choice"])]
    for k, a in cols.items():
        if a["q"] == "oracle":                       # the person's tag (full_run_v7 oracle)
            out[k] = a["tag"]
        elif a["q"] == "role" and a["probs"].get(a["choice"], 0) >= SURE and ("role", a["choice"]) in NEW_TAG:
            out[k] = NEW_TAG[("role", a["choice"])]
    return out


def candidate(t, fields):
    return bool(t.records) and any(v in fr.TRAITS or v in CONTEXT_TAGS for v in fields.values())


def groups_column(org_dec):
    """The higher-rank column the organism step (organism_tree Q-UNITS) turned down only
    because its rows summarise a group ('groups'): the GT records such summaries at that
    rank (Attiwilli's families, mean ± SD and range). None otherwise."""
    if not org_dec or org_dec.get("organism") or (org_dec.get("units") or {}).get("choice") != "groups":
        return None
    higher = [c for c, k in (org_dec.get("kinds") or {}).items() if k.get("choice") == "higher"]
    return higher[0] if len(higher) == 1 else None


def organism_column(res):
    """The organism column a kept 'traits' table takes back (see groups_column), or None."""
    if not res or res.get("action") != "keep":
        return None
    k = res.get("kind") or {}
    sure = k.get("choice") == "review" or (k.get("choice") == "traits" and k.get("probs", {}).get("traits", 0) >= SURE)
    return res.get("organism") if sure else None


def organism_decisions(run_dir, paper):
    f = run_dir / "organism" / f"{paper}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def run(run_dir, papers, has_species, structure_of):
    """One paper at a time; resumable (run_dir/kind/<paper>.json). `structure_of(paper)` gives
    the structure step's decisions {table: dec}. Tables without species are asked too when
    the organism step turned their higher-rank column down as 'groups'."""
    import decoder_v3 as v3
    import species_tree as sp
    out = run_dir / "kind"
    out.mkdir(parents=True, exist_ok=True)
    head = fr.head_runs()
    client = None
    for p in papers:
        f = out / f"{p}.json"
        if p not in head:
            continue
        old = json.loads(f.read_text(encoding="utf-8")) if f.exists() else None
        if old is not None and not any(d["action"] == "no rows" and d["kind"]["choice"] == "sampling"
                                       and "also" not in d for d in old.values()):
            continue                                 # done, Q-ALSO included
        res, seen = old or {}, set()
        flat, spans = v3.md_tables(p)
        decs, orgs = structure_of(p), organism_decisions(run_dir, p)
        for t, fields, org, _x in fr.plan(p, head):
            k = str(t.table_index)
            if t.table_index in seen or not candidate(t, fields):
                continue
            gcol = groups_column(orgs.get(k))
            if not gcol and not has_species(t, fields, org):
                continue
            seen.add(t.table_index)
            client = client or ct.DecisionClient(v1.NIMBLE, 1)
            above, below = sp.caption_above(t, flat, spans), caption_below(t, flat, spans)
            if old is None:
                res[k] = decide_table(client, t, fields, decs.get(k), above, below, gcol)
            elif k in res and recheck_sampling(client, t, res[k], above, below) and res[k]["action"] == "keep":
                ask_columns(client, t, fields, decs.get(k), above, res[k])   # older runs: Q-ALSO only
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        acts = [f"t{k}:{d['kind']['choice']}" for k, d in res.items() if d["action"] == "no rows"]
        print(f"  [kind] {p:22s} {len(res)} tables; no rows: " + (", ".join(acts) or "none"), flush=True)
    if client:
        v1.unload(v1.NIMBLE)


def split_n(rows):
    """'Hesperiidae(n=45)' -> organism 'Hesperiidae', sampleSizeValue '45' (a printing
    convention; code). Rows that already carry a sample size keep it."""
    n = 0
    for r in rows:
        m = N_IN_LABEL.match(r.get("verbatimIdentification") or "")
        if m:
            r["verbatimIdentification"] = m.group(1)
            r["sampleSizeValue"] = r.get("sampleSizeValue") or m.group(2)
            n += 1
    return n
