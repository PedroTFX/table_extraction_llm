"""Tables printed inside a species' account (v22). A taxonomic revision prints each species' measurements in a small
table inside its account (oc36-en: 142 tables, rows I-IV x F P T Mt t Tot under '## Diores annetteae new species').
The table has no organism column, and the species step's paper gate ('How many species did this study take its
measurements on?') rightly says 'several', which closed every such table with no species: no rows, and Q-KIND was
never asked (it skips tables without species). The paper-level count stays as information; here each table is asked
on its own.

  candidates  code: a table with records and trait columns that gives no species (no organism column, the species
              step named none), or whose organism column holds no name of an organism ('Carapace:', 'Tibia-patella:')
  account     code, geometry only: the nearest heading line above the table that prints a genus and an epithet
              (a markdown heading, a bold line, or a short line with a new-species mark, an author's bracket or a
              year); the genus must never be printed in lower case in the paper ('Leg measurements' is no name).
              No such heading: nothing is asked.
  Q-KIND      the table step's own question, asked here for these tables (it is independent of the species gate)
  Q-ACCOUNT   the table, its account's heading and the text before it: which statement describes the organisms
              measured? (the reviewer's wording, 2026-11-09). A sure '{s}' gives every row the account's species.
  apply       the plan's table gets t.account_species; species_fn returns it before any column. A sure Q-KIND other
              than 'traits' leaves the table without rows.

    python full_run_v22.py v22:account <papers>        writes <run>/account/<paper>.json
"""
import json
import re
import time

import _paths
import column_tree as ct
import decoder as v1
import duels
import full_run as fr
import kind_tree as kt

SURE = 0.8
HEAD_LINE = re.compile(r"^\s*(#{1,6}\s*|\*\*)?\**\s*([A-Z][a-z]{2,})\s+(?:\([A-Z][a-z]+\)\s+)?([a-z][a-z-]{2,})\b(.*)$")
# what follows the name in an account heading (layout of nomenclature, no paper's words): a new-taxon mark, an author
# (a capital, an initial), a year or a bracket; a colon right after the name is a citation line, not a heading
MARK = re.compile(r"^\W{0,3}?(\(|sp\.?\s*n|sp\.?\s*nov|n\.\s*sp|nov\.|new\b|spec\.|comb\.|[A-Z][\w'’-]+|[A-Z]\.|1[6-9]\d\d|20\d\d|\*\*)")
RANK_WORDS = {"species", "subspecies", "genus", "group", "spp", "sp", "family", "and", "the", "van", "von", "der", "den", "del"}
NAMED = re.compile(r"\b[A-Z][a-z]*\.?\s+(\([A-Z][a-z]+\)\s+)?[a-z]{3,}")

Q_ACCOUNT = ("Considering its heading, columns, first rows and the surrounding text, which statement best describes "
             "the organisms measured in this table?")


def options(s):
    return {"this": f"{s}: all measurements in this table are of {s}. Rows may distinguish its specimens, sexes, "
                    f"castes, body parts or populations",
            "another": "another organism: the measurements are all of a different, identifiable organism",
            "several": "several: the table contains measurements of different organisms, with their identity "
                       "determined by its rows or columns",
            "unassigned": "several, not individually identified: different organisms are covered, but the "
                          "measurements cannot be assigned individually from the table",
            "none": "none: the table does not contain organism measurements; it contains definitions, statistics, "
                    "sites, dates or methods",
            "uncertain": "uncertain: the table and its surrounding text do not establish the subject"}


def _flat(s):
    return " ".join(re.sub(r"<[^>]+>|<!--.*?-->", " ", str(s or "")).split())


def looks_named(v):
    v = _flat(v)
    return bool(NAMED.search(v) or re.fullmatch(r"[a-z]{3,}", v))


def account_of(raw, start):
    """(species as printed in the heading, the heading line, its offset) of the account heading above, or Nones.
    Layout only: a line that starts with a genus and an epithet followed by a nomenclature mark. A markdown or bold
    heading within NEAR characters above wins over a plain line (a synonymy citation printed inside the account)."""
    lo, pos = max(0, start - 40000), start
    plain = heading = None
    for ln in reversed(raw[lo:start].split("\n")):
        pos -= len(ln) + 1
        m = HEAD_LINE.match(ln)
        rest = m.group(4) or "" if m else ""
        if not m or m.group(3) in RANK_WORDS or len(ln.strip()) > 160 or rest.lstrip().startswith(":") \
                or not MARK.match(rest):
            continue
        genus = m.group(2)
        if re.search(r"(?<![^\W\d_])" + re.escape(genus.lower()) + r"(?![^\W\d_])", raw):
            continue                                  # printed in lower case too: a word, not a genus
        hit = (f"{genus} {m.group(3)}", _flat(ln)[:200], max(lo, pos))
        if m.group(1):
            heading = hit
            break
        plain = plain or hit
        if start - pos > NEAR and plain:
            break
    if heading and (not plain or start - heading[2] <= NEAR):
        return heading
    return plain or heading or (None, None, None)


NEAR = 4000


def needs_account(t, fields, org, step_named):
    """A table with records and trait columns whose rows give no organism: no species from the species step, and
    no record's organism cell printing a name (none, or labels such as 'Carapace:')."""
    if not t.records or not kt.candidate(t, fields) or step_named(t):
        return False
    return not any(n and looks_named(n) for n in (fr.species_of(t, fields, org, r) for r in t.records))


def ask_account(client, t, s, heading, before):
    state = (f"A table in a scientific paper has the columns {[c.name for c in t.columns][:14]}. Its first rows read: "
             f"{kt._shown(t)}. This table has no column identifying the organism. It appears within the account of "
             f"{s}: the account's heading reads '{heading}', and the text printed directly before the table reads "
             f"'{before}'.")
    return v1.ask(client, state, Q_ACCOUNT, options(s))


def run(run_dir, papers, dry=False, named_elsewhere=lambda p: set()):
    """dry: code only (candidates and accounts found, no question asked, nothing written).
    named_elsewhere(paper): tables another step gives a species (v13's one-species subject): never asked."""
    import decoder_v3 as v3
    import species_tree as sp
    step_named = lambda t: (bool(sp.species_of_tables(run_dir / "species", getattr(t, "paper", "")).get(t.table_index))
                            or t.table_index in named_elsewhere(getattr(t, "paper", "")))
    out = run_dir / "account"
    out.mkdir(parents=True, exist_ok=True)
    head = fr.head_runs()
    client = None
    for p in papers:
        f = out / f"{p}.json"
        if (f.exists() and not dry) or p not in head:
            continue
        t0 = time.time()
        flat, spans = v3.md_tables(p)
        mdf = _paths.PAPERS / p / f"{p}_full.md"
        raw = mdf.read_text(encoding="utf-8", errors="replace") if mdf.exists() else ""
        raw_at = [m.start() for m in re.finditer(r"<table.*?</table>", raw, re.S)]   # the same tables, in order, with
        if len(raw_at) != len(spans):                                                # the lines kept (md_tables flattens)
            print(f"  [account] {p}: {len(raw_at)} tables in the markdown, {len(spans)} flattened: skipped", flush=True)
            continue
        res = {}
        for t, fields, org, _x in fr.plan(p, head):
            if not needs_account(t, fields, org, step_named):
                continue
            i = v3.locate_table(t, spans)
            if i is None:
                continue
            s, heading, hpos = account_of(raw, raw_at[i])
            rec = {"account": s, "heading": heading}
            if dry:
                res[str(t.table_index)] = rec
                continue
            if s:
                client = client or ct.DecisionClient(v1.NIMBLE, 1)
                above = sp.caption_above(t, flat, spans)
                ch, probs = kt.ask_kind(client, t, above)
                rec["kind"] = {"choice": ch, "probs": probs}
                if duels.sure(ch, probs, *kt.KIND_OPTIONS) not in (None, "traits"):
                    rec["species"] = None
                else:
                    before = _flat(raw[hpos:raw_at[i]])[-400:]
                    c2, p2 = ask_account(client, t, s, heading, before)
                    rec["q_account"] = {"choice": c2, "probs": p2}
                    rec["species"] = s if duels.sure(c2, p2, "this") == "this" else None
            res[str(t.table_index)] = rec
        if dry:
            acc = [r for r in res.values() if r["account"]]
            print(f"  [account dry] {p:12s} {len(res)} candidate tables, {len(acc)} inside an account: "
                  + "; ".join(f"t{k} -> {r['account']} ({r['heading'][:60]})" for k, r in list(res.items()) if r["account"])[:600],
                  flush=True)
            continue
        f.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        got = sum(1 for r in res.values() if r.get("species"))
        print(f"  [account] {p:22s} {len(res)} tables without a species; {sum(1 for r in res.values() if r['account'])} "
              f"inside an account; {got} given its species ({time.time() - t0:.0f}s)", flush=True)
    if client:
        v1.unload(v1.NIMBLE)


def apply(dec, out):
    """plan()'s list with each table Q-ACCOUNT gave a species marked t.account_species; a sure non-traits Q-KIND
    answer leaves the table without rows."""
    if not dec:
        return out
    res = []
    for t, fields, org, x in out:
        d = dec.get(str(t.table_index))
        if d and d.get("kind") and duels.sure(d["kind"]["choice"], d["kind"]["probs"], *kt.KIND_OPTIONS) not in (None, "traits"):
            fields = {k: ("none" if v in fr.TRAITS else v) for k, v in fields.items()}
        elif d and d.get("species"):
            t.account_species = d["species"]
        res.append((t, fields, org, x))
    return res
