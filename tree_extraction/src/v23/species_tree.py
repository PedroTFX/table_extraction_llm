"""Which organism a table is about when it has no species column (single-species papers:
Orr2024, Brant2021, Kovacs2008, Franzen2025, Tsai2020 …).

One paper at a time, start to finish: its rounds over its own sections, in reading
order (title + abstract, introduction, methods, results, discussion), stopping when its
tables are settled; then the next paper. In each round:
  gemma   reads the section: the species this paper's own study is about, each copied as
          printed at its fullest mention, and a one-or-two sentence summary of the study.
          Code keeps only names printed in that section (the legend inventory's boundary
          check). A section whose summary is empty does not describe the study: read on.
  nimble  answers from the sections read so far (below). gemma is unloaded before nimble
          loads, and nimble before gemma reads the next section.
First a gate per paper: from the summaries and names read so far, did the study measure
one species or several ('several' closes the paper: its tables get no paper-level name;
Beyer and Wallon's tables otherwise got 'Vicia faba L', 'arthropods'). Only 'one'-species
papers go on to the per-table question, with the names known when the gate said
'one' (later sections add species from cited studies: Luo's lizard). If their tables are matched to different
names, the gate is asked again with those names (once); unless it still says 'one',
the names are withdrawn.
A table is settled when nimble picks a name, 'several' or 'none' with p >= SURE; 'unsaid'
or a lower p sends it to the next section. Only a picked name changes the output: the
table's rows get that species. Nothing runs in parallel and nothing is shared between
papers: each paper's state lives in its own species/<paper>.json, every prompt holds only
that paper's text, and the decision client keeps no state between questions.
"""
import json
import re
import time
import urllib.request

import column_tree as ct
import decoder as v1
import decoder_v3 as v3
import full_run as fr
import _paths

SURE = 0.8
CHUNK = 3000            # characters per gemma call
MAX_CHARS = 9000        # per section
MAX_NAMES = 10

ROUNDS = ["title and abstract", "introduction", "methods", "results", "discussion"]
KIND = [("title and abstract", re.compile(r"abstract|summary", re.I)),
        ("introduction", re.compile(r"introduc|background", re.I)),
        ("methods", re.compile(r"method|material|study (species|organism|area|site)|sampl", re.I)),
        ("results", re.compile(r"result", re.I)),
        ("discussion", re.compile(r"discussion|conclusion", re.I)),
        ("end", re.compile(r"reference|literature cited|acknowledg|bibliograph|supplement|"
                           r"appendix|author contrib|data availab|funding", re.I))]

READ = """Below is the {kind} of a scientific paper.

List every species whose traits or measurements this paper's own study is about (not species from the studies it cites), named at species level. Write each one as its scientific name exactly as printed at its fullest mention: genus and species (and subspecies if printed), not an abbreviation such as 'V. maculifrons' when the full name is printed, and without the common name or the author. Leave out group names (such as 'beetles', 'wild bees', 'Bombus spp.', a family or an order). Then summarise in one or two sentences what the whole study measured: which organism or organisms, and whether its measurements cover one species or many. Describe this paper's own study, not a single passing mention and not the studies it cites. If this text does not say what the study measured, leave the summary empty.

Text:
{text}"""
READ_SCHEMA = {"type": "object", "required": ["organisms", "summary"],
               "properties": {"organisms": {"type": "array", "items": {"type": "string"}},
                              "summary": {"type": "string"}}}


def _flat(s):
    return " ".join(str(s or "").split())


def _clean_md(text):
    text = re.sub(r"<table.*?</table>", " ", text, flags=re.S)
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return text


def sections(paper):
    """{round name: text} split at the markdown headings by their words. Text before the
    first introduction / methods / results heading is the title and abstract; with an
    'Abstract' heading, only the title and the text under it (no authors, affiliations)."""
    f = _paths.PAPERS / paper / f"{paper}_full.md"
    if not f.exists():
        return {}
    out, kind, title = {}, "title and abstract", ""
    for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.lstrip()
        if s.startswith("# ") and not title:
            title = line
        if s.startswith("#"):
            for name, rx in KIND:
                if rx.search(line):
                    if name == "title and abstract":     # front matter before it is dropped
                        out["title and abstract"] = [title] if title and title != line else []
                    kind = name
                    break
        if kind != "end":
            out.setdefault(kind, []).append(line)
    return {k: _flat(_clean_md("\n".join(v)))[:MAX_CHARS] for k, v in out.items() if k in ROUNDS}


def _gemma(prompt):
    body = {"model": v1.GEMMA, "stream": False, "format": READ_SCHEMA, "think": False,
            "messages": [{"role": "user", "content": prompt}],
            "options": {"temperature": 0, "num_ctx": 16384}}
    for attempt in range(3):
        try:
            req = urllib.request.Request("http://127.0.0.1:11434/api/chat", data=json.dumps(body).encode(),
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=900) as r:
                got = json.loads(json.loads(r.read()).get("message", {}).get("content", "") or "{}")
            return got if isinstance(got, dict) else {}
        except json.JSONDecodeError:
            return {}
        except Exception:
            if attempt == 2:
                raise
            time.sleep(10 * (attempt + 1))


def read_section(kind, text):
    """gemma over the section in CHUNK pieces -> {"organisms": [printed names], "summary"}."""
    names, summaries = [], []
    for i in range(0, len(text), CHUNK):
        piece = text[i:i + CHUNK]
        got = _gemma(READ.format(kind=kind, text=piece))
        low = piece.lower()
        for n in got.get("organisms") or []:
            n = _flat(n).strip(" .,;")
            if n and n.lower() in low and n not in names:          # printed in this section
                names.append(n)
        if _flat(got.get("summary")):
            summaries.append(_flat(got.get("summary")))
    return {"organisms": names, "summary": " ".join(summaries)[:600]}


def caption_above(table, flat, spans):
    """The text printed directly above the table (after the previous table), at most 300
    characters: layout, from the markdown."""
    i = v3.locate_table(table, spans)
    if i is None:
        return ""
    start = spans[i - 1][1] if i > 0 else 0
    above = _flat(re.sub(r"<[^>]+>|<!--.*?-->", " ", flat[start:spans[i][0]]))
    return above[-300:]


def table_state(table, caption, reads, names):
    """What the per-table question shows: the table's columns and first cells, the text above
    it, the summaries read so far and the organism names printed there (v11's duels show the
    same)."""
    heads = [c.name for c in table.columns][:12]
    first = []
    for r in table.records[:6]:
        v = _flat(r.get(table.columns[0].name)) if table.columns else ""
        if v:
            first.append(v)
    state = (f"A table in a scientific paper has the columns {heads}. Its first cells read "
             f"{first}. The text printed directly above the table: '{caption}'.")
    for kind, rd in reads:
        if rd.get("summary"):
            state += f" The paper's {kind}, summarised: '{rd['summary']}'"
    if names:
        state += " Organism names printed there: " + ", ".join(f"'{n}'" for n in names) + "."
    return state


QUESTION = "Which organism were the measurements in this table taken on?"
NAMED = "'{}': every row of the table is about this organism"
SEVERAL = ("several organisms: the rows are about different species or groups, so each row needs "
           "its own name")
NONE = "no organism's measurements: the table lists trait definitions, statistics, sites, dates or methods"


def ask_table(client, table, caption, reads, names):
    crit = {f"o{i}": NAMED.format(n) for i, n in enumerate(names)}
    crit["several"] = SEVERAL
    crit["none"] = NONE
    crit["unsaid"] = "the text quoted does not say which organism the table is about"
    return v1.ask(client, table_state(table, caption, reads, names), QUESTION, crit)


def ask_paper(client, reads, names, clash=None):
    """The gate: one species or several, from the sections read so far. `clash`: the
    different names this paper's tables were matched to (asked again with that fact)."""
    state = "A scientific paper."
    for kind, rd in reads:
        if rd.get("summary"):
            state += f" Its {kind}, summarised: '{rd['summary']}'"
    if names:
        state += " Species names printed there: " + ", ".join(f"'{n}'" for n in names) + "."
    if clash:
        state += (" Its tables were matched to different organisms: "
                  + ", ".join(f"'{n}'" for n in clash) + ".")
    return v1.ask(client, state, "How many species did this study take its measurements on?", {
        "one": ("one species: all of the study's measurements are of a single species (perhaps "
                "of different castes, sexes, populations or sites)"),
        "several": "several species: the study measures or compares more than one species",
        "unsaid": "the text quoted does not say"})


def open_tables(paper, head):
    """Reader tables with trait columns, records, and no species in any record."""
    out = []
    for t, fields, org, _x in fr.plan(paper, head):
        if not t.records or not any(fields.get(c.name) in fr.TRAITS for c in t.columns):
            continue
        if not any(fr.species_of(t, fields, org, r) for r in t.records):
            out.append(t)
    return out


def run(papers, out_dir):
    """One paper at a time, start to finish (resumable: out_dir/<paper>.json keeps the reads
    and every answer). A batch is only this loop over papers."""
    out_dir.mkdir(parents=True, exist_ok=True)
    head = fr.head_runs()
    for p in papers:
        if p in head:
            run_paper(p, head, out_dir)


def _names(reads):
    out = []
    for _k, rd in reads:
        for n in rd.get("organisms") or []:
            if n not in out:
                out.append(n)
    return out[:MAX_NAMES]


def run_paper(p, head, out_dir):
    """The rounds for one paper. Each round: gemma reads the section, unload; nimble answers
    (gate, then tables), unload. Never two models loaded, never two papers in flight."""
    f = out_dir / f"{p}.json"
    st = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {"reads": {}, "tables": {}}
    st.setdefault("paper", {"rounds": [], "answer": None})
    tables = {str(t.table_index): t for t in open_tables(p, head)}
    for k in tables:
        st["tables"].setdefault(k, {"rounds": [], "species": None, "settled": None})
    if not st["tables"]:
        return
    text_of = sections(p)
    flat, spans = v3.md_tables(p)
    for kind in ROUNDS:
        if all(x["settled"] for x in st["tables"].values()):
            break
        if kind not in st["reads"]:
            text = text_of.get(kind, "")
            st["reads"][kind] = read_section(kind, text) if text else {"organisms": [], "summary": ""}
            v1.unload(v1.GEMMA)
            _save(out_dir, p, st)
        if not st["reads"][kind].get("summary"):
            continue                    # the section does not describe the study: read on
        reads = [(k, st["reads"][k]) for k in ROUNDS[:ROUNDS.index(kind) + 1] if k in st["reads"]]
        names = _names(reads)
        client = ct.DecisionClient(v1.NIMBLE, 1)
        gate = st["paper"]
        if not gate["answer"] and kind not in [r["round"] for r in gate["rounds"]]:
            ch, probs = ask_paper(client, reads, names)
            gate["rounds"].append({"round": kind, "choice": ch, "probs": probs, "names": names})
            if ch in ("one", "several") and probs.get(ch, 0) >= SURE:
                gate["answer"] = ch
                gate["names"] = names           # the names known when nimble said 'one'
        if gate["answer"] == "several":                # many species: no paper-level name
            for x in st["tables"].values():
                if not x["settled"]:
                    x["settled"], x["answer"] = kind, "several (paper)"
        if gate["answer"] == "one":
            options = gate.get("names") or names
            for k, x in st["tables"].items():
                if x["settled"] or k not in tables or kind in [r["round"] for r in x["rounds"]]:
                    continue
                ch, probs = ask_table(client, tables[k], caption_above(tables[k], flat, spans),
                                      reads, options)
                x["rounds"].append({"round": kind, "choice": ch, "probs": probs, "names": options})
                if ch and ch != "unsaid" and probs.get(ch, 0) >= SURE:
                    named = re.fullmatch(r"o(\d+)", ch)
                    x["settled"] = kind
                    x["species"] = options[int(named.group(1))] if named else None
                    x["answer"] = "name" if named else ch
            named = sorted({x["species"] for x in st["tables"].values() if x.get("species")})
            if len(named) > 1 and not gate.get("clash"):    # 'one species' but tables differ
                ch, probs = ask_paper(client, reads, names, clash=named)
                gate["clash"] = {"names": named, "choice": ch, "probs": probs}
                if not (ch == "one" and probs.get(ch, 0) >= SURE):
                    gate["answer"] = ("several" if ch == "several" and probs.get(ch, 0) >= SURE
                                      else "undecided")
                    for x in st["tables"].values():         # the names are withdrawn
                        x["species"], x["settled"] = None, kind
                        x["answer"] = f"{gate['answer']} (paper)"
        v1.unload(v1.NIMBLE)
        _save(out_dir, p, st)
    _save(out_dir, p, st)
    print(f"  [species] {p:22s} paper: {st['paper']['answer'] or 'open'} | " + "; ".join(
        f"t{k}: {x.get('species') or x.get('answer') or 'open'}" for k, x in st["tables"].items()),
        flush=True)


def _save(out_dir, p, st):
    (out_dir / f"{p}.json").write_text(json.dumps(st, indent=1, ensure_ascii=False), encoding="utf-8")


def species_of_tables(out_dir, paper):
    f = out_dir / f"{paper}.json"
    if not f.exists():
        return {}
    st = json.loads(f.read_text(encoding="utf-8"))
    return {int(k): x["species"] for k, x in st["tables"].items() if x.get("species")}
