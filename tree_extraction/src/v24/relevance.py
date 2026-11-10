"""Keep out what is not a trait (v24; tree_extraction/plans/06_relevance.md, 2026-11-10). Of the rows we write
beyond the GT, 24% are copied right but are no trait (alleles, colony and specimen IDs, scores of an analysis, counts
per site and date, higher taxa) and 16.5% are wrong (a table of the hosts read with the hosts as the organisms; a
species-level category written again for every specimen record). nimble decides; code picks the questions and applies
the sure answers.

  Q-ALSO2   a table the kind step dropped as sampling data (sure), asked again with the wider wording: does it give
            the organism of each row something of its own (what it lives on, eats, hosts or carries included)? Sure
            'yes' in both option orders: the table is read again; its count columns then meet Q-COL
  Q-ORG     a table with an organism in each row (three names or more), with the paper's title and abstract: are the
            rows the organisms the paper studies, or something they use, live on or are compared with? Sure 'other'
            in both orders: the table gives no rows
  Q-COL     every trait column of a wide table, with its header, the paper's legend for it and five values: a
            characteristic of the organism / an identifier or label / a genetic marker / a count or presence at a
            site, date or sample / a statistic of an analysis / something else. Only a sure answer other than the
            first takes the column out, and 'something else' never does. Asked once per header and values per paper.
  Q-LEVEL   a table where a species takes several rows, a trait column that never differs inside a species while
            another trait column does: is it a characteristic of the species printed again on each row, or a value
            of each row's own specimen? Sure 'species' in both orders: one row per species, trait and value
  apply     dropped tables and columns lose their trait tags; t.once_cols names the columns written once per species

    python full_run_v24.py v24:relevance <papers>     writes <run>/relevance/<paper>.json
"""
import collections
import json
import re
import time

import _paths
import decoder_v3 as v3
import duels
import full_run as fr
import kind_tree as kt
import legend_names as ln
import species_tree as sp

MAX_COLS = 150           # trait columns asked per table
Q_ALSO = "Besides any counts or site data, does the table give the organism of each row something of its own?"
ALSO = {"yes": "yes: at least one column gives the row's organism a characteristic of its own: a group or category it "
               "belongs to, a measurement of it, its behaviour, or what it lives on, eats, hosts or carries",
        "no": "no: every column is counts, abundances, occurrences, sampling effort, or data of the site or sample"}
Q_ORG = "Are the names in the rows of this table the organisms that this paper studies?"
ORG = {"studied": "yes: the rows are the organisms (species, groups or specimens) whose characteristics the paper "
                  "reports",
       "other": "no: the rows are something the studied organisms use, live on, feed on, carry or are compared with, "
                "and the table describes those rows, not the studied organisms"}
Q_COL = "What does the column '{col}' give for each row?"
COL = {"trait": "a characteristic of the organism: of its body, life history, behaviour or ecology, or what it lives "
                "on, eats, hosts or carries",
       "identifier": "an identifier or a label: a specimen, colony, sample or record code, a name, or a higher taxon "
                     "the organism belongs to",
       "genetic": "a genetic marker or a sequence reference: alleles, loci, haplotypes or accession numbers",
       "count": "a count, an abundance or a presence at a site, on a date or in a sample",
       "statistic": "a statistic of an analysis: a score, a loading, a test value or a p-value",
       "other": "something else"}
# the answers that take a column out ('other' does not: on Noriega2023 a behaviour category was 'other' at 0.91)
DROP = ("identifier", "genetic", "count", "statistic")
Q_LEVEL = ("In this table one species takes several rows, and the column '{col}' has the same value on every row of a "
           "species. What does the column give?")
LEVEL = {"species": "a characteristic of the species as a whole, printed again on each of its rows",
         "row": "a value recorded for each row's own specimen, sample or group, which happens to be equal inside a "
                "species"}


def _flat(s):
    return " ".join(str(s or "").split())


def _reversed(crit):
    return dict(reversed(list(crit.items())))


def both(ask, state, q, crit, key):
    """The answer `key` sure in both option orders -> (True / False, [the two answers])."""
    log = []
    for c in (crit, _reversed(crit)):
        ch, probs = ask(state, q, c)
        log.append({"choice": ch, "probs": probs})
        if duels.sure(ch, probs, key) != key:
            return False, log
    return True, log


def paper_view(p):
    """The paper's title and abstract: layout only (the first long heading; the text under 'Abstract')."""
    f = _paths.PAPERS / p / f"{p}_full.md"
    if not f.exists():
        return ""
    t = f.read_text(encoding="utf-8", errors="ignore")
    heads = [x.lstrip("#").strip() for x in t.split("\n") if x.startswith("#")]
    title = next((h for h in heads if len(h) > 25), heads[0] if heads else "")
    m = re.search(r"(?ims)^#+\s*abstract\s*$(.*?)^#", t)
    abstract = _flat(re.sub(r"<[^>]+>", " ", m.group(1) if m else t[:1500]))[:900]
    return f"A scientific paper is titled '{title[:200]}'. Its abstract reads: '{abstract}'."


def table_state(t, above="", n=3):
    s = f"A table in a scientific paper has the columns {[c.name for c in t.columns][:14]}."
    if above:
        s += f" The text printed directly above it: '{above}'."
    return s + f" Its first rows read: {kt._shown(t, n)}."


def wide_traits(t, fields):
    """The trait columns of a wide reading (a long reading names its traits in cells: not asked)."""
    names = [c for c in t.columns if fields.get(c.name) == "measurementType"]
    values = [c for c in t.columns if fields.get(c.name) == "measurementValue"]
    return [] if names and values else names + values


def distinct(t, col, k=5):
    out = []
    for r in t.records:
        v = _flat(r.get(col.name))
        if v and v not in out:
            out.append(v)
        if len(out) == k:
            break
    return out


def sampling_dropped(kind):
    """The tables the kind step dropped as sampling data, sure."""
    return [k for k, d in (kind or {}).items()
            if isinstance(d, dict) and d.get("action") == "no rows" and (d.get("kind") or {}).get("choice") == "sampling"
            and (d["kind"].get("probs") or {}).get("sampling", 0) >= duels.SURE]


def level_columns(t, fields, org, cols):
    """Trait columns that never differ inside a species, in a table where species take several rows and another trait
    column does differ inside one (the rows are specimens or samples, not the same record printed again)."""
    by = collections.defaultdict(list)
    for r in t.records:
        s = _flat(fr.species_of(t, fields, org, r))
        if s:
            by[s].append(r)
    many = [rs for rs in by.values() if len(rs) >= 2]
    if len(by) < 2 or len(many) < 2:
        return []
    const, varies = [], False
    for c in cols:
        per = [{_flat(r.get(c.name)) for r in rs if _flat(r.get(c.name))} for rs in many]
        if any(len(v) > 1 for v in per):
            varies = True
        elif sum(bool(v) for v in per) >= 2 and len(set().union(*per)) >= 2:
            const.append(c)
    return const if varies else []


def run(run_dir, papers, plan_lifted, skip=lambda p: set()):
    """One paper at a time; resumable (run_dir/relevance/<paper>.json). plan_lifted(paper, head, tables) -> the plan
    with those tables' sampling drop lifted. skip(paper): tables another step reads row by row (v13)."""
    out = run_dir / "relevance"
    out.mkdir(parents=True, exist_ok=True)
    head = fr.head_runs()
    ask = duels.Nimble()
    for p in papers:
        f = out / f"{p}.json"
        if f.exists() or p not in head:
            continue
        t0, n_q = time.time(), 0
        res = {"also": {}, "organism": {}, "columns": {}, "level": {}}
        flat, spans = v3.md_tables(p)
        kf = run_dir / "kind" / f"{p}.json"
        kind = json.loads(kf.read_text(encoding="utf-8")) if kf.exists() else {}
        tables = {str(t.table_index): t for t, _f, _o, _x in fr.plan(p, head)}
        for k in sampling_dropped(kind):                                   # Q-ALSO2
            t = tables.get(k)
            if t is None or not t.records:
                continue
            st = table_state(t, sp.caption_above(t, flat, spans))
            below = kt.caption_below(t, flat, spans)
            ok, log = both(ask, st + (f" The text printed directly below it: '{below}'." if below else ""), Q_ALSO, ALSO, "yes")
            n_q += len(log)
            res["also"][k] = {"lift": ok, "asked": log}
        lifts = {int(k) for k, d in res["also"].items() if d["lift"]}
        view = None
        left = skip(p)
        cats = ln.entries(p)
        cache, done_org = {}, set()
        for t, fields, org, _x in plan_lifted(p, head, lifts):
            k = str(t.table_index)
            cols = wide_traits(t, fields)[:MAX_COLS]
            if not t.records or t.table_index in left or not (cols or any(v in fr.TRAITS for v in fields.values())):
                continue
            species = [_flat(fr.species_of(t, fields, org, r)) for r in t.records]
            names = list(dict.fromkeys(s for s in species if s))
            if not names:
                continue
            above = sp.caption_above(t, flat, spans)
            own = len(names) >= 3 and not getattr(t, "account_species", "") and not getattr(t, "paper_species", "")
            if own and k not in done_org:                                  # Q-ORG
                done_org.add(k)
                view = view or paper_view(p)
                st = (view + " One of its tables" + table_state(t, above)[len("A table in a scientific paper"):]
                      + " The rows are named " + ", ".join(f"'{s}'" for s in names[:6]) + ".")
                ok, log = both(ask, st, Q_ORG, ORG, "other")
                n_q += len(log)
                res["organism"][k] = {"drop": ok, "asked": log}
            if (res["organism"].get(k) or {}).get("drop"):
                continue
            state = table_state(t, above)
            kept = []
            for c in cols:                                                 # Q-COL
                key = f"{k}|{c.name}"
                if key in res["columns"]:
                    if res["columns"][key].get("keep"):
                        kept.append(c)
                    continue
                vals = distinct(t, c)
                if not vals:
                    continue
                ck = (re.sub(r" #\d+$", "", c.name), tuple(vals))
                if ck not in cache:
                    legend = [x for x in ln.candidates(c.name, cats)][:2]
                    st = state + f" The column '{c.name}' holds values such as {', '.join(repr(v) for v in vals)}."
                    if legend:
                        st += " The paper's legend gives for it: " + "; ".join(f"'{x['term']}' ({x['entry'][:120]})" for x in legend) + "."
                    ch, probs = ask(st, Q_COL.format(col=c.name), dict(COL))
                    n_q += 1
                    cache[ck] = {"choice": ch, "probs": probs,
                                 "keep": duels.sure(ch, probs, *DROP) is None}
                res["columns"][key] = dict(cache[ck], values=vals)
                if cache[ck]["keep"]:
                    kept.append(c)
            for c in level_columns(t, fields, org, kept):                  # Q-LEVEL
                key = f"{k}|{c.name}"
                if key in res["level"]:
                    continue
                st = (state + f" The column '{c.name}' holds values such as "
                      f"{', '.join(repr(v) for v in distinct(t, c))}. The table has {len(t.records)} rows for {len(names)} species.")
                ok, log = both(ask, st, Q_LEVEL.format(col=c.name), LEVEL, "species")
                n_q += len(log)
                res["level"][key] = {"once": ok, "asked": log}
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  [relevance] {p:22s} sampling tables read again {sum(d['lift'] for d in res['also'].values())} of "
              f"{len(res['also'])}; tables of other organisms {sum(d['drop'] for d in res['organism'].values())} of "
              f"{len(res['organism'])}; columns taken out {sum(not d['keep'] for d in res['columns'].values())} of "
              f"{len(res['columns'])}; written once per species {sum(d['once'] for d in res['level'].values())} "
              f"({n_q} questions, {time.time() - t0:.0f}s)", flush=True)
    ask.unload()


Q_COUNT = "The column '{col}' gives a number for each row. What is that number?"
COUNT = {"site": "a count of the organism at a site, on a date or in a sample: how many were caught, seen or present there",
         "own": "a number belonging to the organism itself: of its members, parts, broods, generations or offspring, or "
                "the months, days or places of its life"}


def recheck_counts(run_dir, papers):
    """Q-COUNT on a column Q-COL took out as 'count' (Khayati2024 'Number of queens', Scalercio2020 'Flight_Months'):
    a count at a site, date or sample, or a number of the organism's own? The column stays out only with 'site'
    sure in both orders. Asked on the saved records; resumable (rec['count2'])."""
    head = fr.head_runs()
    ask = duels.Nimble()
    for p in papers:
        f = run_dir / "relevance" / f"{p}.json"
        if not f.exists() or p not in head:
            continue
        res = json.loads(f.read_text(encoding="utf-8"))
        todo = {k: d for k, d in res["columns"].items()
                if not d.get("keep") and d.get("choice") == "count" and "count2" not in d}
        if not todo:
            continue
        flat, spans = v3.md_tables(p)
        tables = {str(t.table_index): t for t, _f, _o, _x in fr.plan(p, head)}
        back = 0
        for key, d in todo.items():
            k, col = key.split("|", 1)
            t = tables.get(k)
            if t is None:
                continue
            st = (table_state(t, sp.caption_above(t, flat, spans))
                  + f" The column '{col}' holds values such as {', '.join(repr(v) for v in d.get('values', []))}.")
            ok, log = both(ask, st, Q_COUNT.format(col=col), COUNT, "site")
            d["count2"] = {"site": ok, "asked": log}
            if not ok:
                d["keep"] = True
                back += 1
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  [relevance counts] {p:22s} {back} of {len(todo)} count columns kept as a number of the organism's own",
              flush=True)
    ask.unload()


def lifts(dec):
    """The tables whose sampling drop Q-ALSO2 lifted."""
    return {int(k) for k, d in ((dec or {}).get("also") or {}).items() if d.get("lift")}


def apply(dec, out):
    """plan()'s list with the tables of other organisms and the columns that are no trait left without trait tags,
    and t.once_cols: the columns written once per species, trait and value."""
    if not dec:
        return out
    res = []
    for t, fields, org, x in out:
        k = str(t.table_index)
        if ((dec.get("organism") or {}).get(k) or {}).get("drop"):
            fields = {c: ("none" if v in fr.TRAITS else v) for c, v in fields.items()}
        else:
            names = [c for c, v in fields.items() if v == "measurementType"]
            values = [c for c, v in fields.items() if v == "measurementValue"]
            if not (names and values):                                     # a wide reading only
                out_cols = {key.split("|", 1)[1] for key, d in (dec.get("columns") or {}).items()
                            if key.split("|", 1)[0] == k and not d.get("keep")}
                if out_cols:
                    fields = {c: ("none" if c in out_cols and v in fr.TRAITS else v) for c, v in fields.items()}
                once = {key.split("|", 1)[1] for key, d in (dec.get("level") or {}).items()
                        if key.split("|", 1)[0] == k and d.get("once")}
                if once:
                    t.once_cols = once
        res.append((t, fields, org, x))
    return res


def report(run_dir, papers, named):
    """What the layer takes out, per paper for the papers in `named` (the tuning groups), totals for the rest: the
    list to check against the GT before adoption (a column the GT uses must not be taken out)."""
    L, rest = [], collections.Counter()
    for p in papers:
        f = run_dir / "relevance" / f"{p}.json"
        if not f.exists():
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        cols = [(k, v) for k, v in d["columns"].items() if not v.get("keep")]
        orgs = [k for k, v in d["organism"].items() if v.get("drop")]
        also = [k for k, v in d["also"].items() if v.get("lift")]
        once = [k for k, v in d["level"].items() if v.get("once")]
        if p not in named:
            rest.update({"papers": 1, "columns out": len(cols), "tables out": len(orgs), "tables back": len(also),
                         "once columns": len(once)})
            continue
        if cols or orgs or also or once:
            L.append(p)
            L += [f"    table {k}: the rows are not the studied organisms: no rows" for k in orgs]
            L += [f"    table {k}: sampling table read again" for k in also]
            L += [f"    column {k}: {v['choice']} ({v['probs'].get(v['choice'], 0):.2f}) values {v['values'][:3]}" for k, v in cols]
            L += [f"    column {k}: once per species" for k in once]
    L.append(f"other papers (totals only): {dict(rest)}")
    (run_dir / "relevance" / "REPORT.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
