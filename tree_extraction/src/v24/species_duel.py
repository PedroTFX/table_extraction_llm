"""Species duels (v11, output/eval_split/DESIGN_names_v11.md). The per-table question of
species_tree.py offers every name, 'several', 'none' and 'unsaid' at once; with four options
the right one can stay below SURE in every round (Luo2023 t4: 0.58-0.69 for the species,
0.26-0.29 for 'several'), so the table stays open. Here the same table meets the options two
at a time (duels.py):

  which     papers whose gate said 'one', tables still open after every round, and no duel yet
  options   the names known when the gate said 'one', in that order, then 'several organisms'
  duels     the first two, then the one kept against the next; not sure: the table stays open
  final     the one left against 'none: no organism's measurements'; sure -> settled ('duel')
  clash     tables now matched to different names: the gate is asked again with those names,
            and they are withdrawn unless it still says 'one' (the per-table question's rule)

Only nimble: the reads (gemma's names and summaries) are the ones species_tree saved.

    python full_run_v11.py v11:species <papers>   updates <run>/species/<paper>.json
"""
import json

import decoder_v3 as v3
import duels
import full_run as fr
import species_tree as sp


def run(run_dir, papers):
    """One paper at a time; a table with a 'duel' record is not asked again."""
    out_dir = run_dir / "species"
    head = fr.head_runs()
    ask = duels.Nimble()
    for p in papers:
        f = out_dir / f"{p}.json"
        if p not in head or not f.exists():
            continue
        st = json.loads(f.read_text(encoding="utf-8"))
        gate = st.get("paper") or {}
        todo = [k for k, x in st["tables"].items() if not x.get("settled") and "duel" not in x]
        if gate.get("answer") != "one" or not todo:
            continue
        reads = [(k, st["reads"][k]) for k in sp.ROUNDS if k in st["reads"]]
        names = gate.get("names") or sp._names(reads)
        tables = {str(t.table_index): t for t in sp.open_tables(p, head)}
        if not names or not tables:
            continue
        flat, spans = v3.md_tables(p)
        options = [(n, sp.NAMED.format(n)) for n in names] + [("several", sp.SEVERAL)]
        for k in todo:
            if k not in tables:
                continue
            state = sp.table_state(tables[k], sp.caption_above(tables[k], flat, spans), reads, names)
            held, log = duels.duel(ask, state, sp.QUESTION, options)
            x = st["tables"][k]
            x["duel"] = {"options": [o[0] for o in options], "duels": log}
            if held is None:
                continue                            # not sure: the table stays open
            ch, probs = ask(state, sp.QUESTION, {"pick": options[held][1], "none": sp.NONE})
            x["duel"]["final"] = {"choice": ch, "probs": probs}
            got = duels.sure(ch, probs, "pick", "none")
            if not got:
                continue
            x["settled"] = "duel"
            if got == "none":
                x["answer"] = "none"
            elif held < len(names):
                x["species"], x["answer"] = names[held], "name"
            else:
                x["answer"] = "several"
        named = sorted({x["species"] for x in st["tables"].values() if x.get("species")})
        if len(named) > 1 and not gate.get("clash"):        # 'one species' but tables differ
            ch, probs = sp.ask_paper(ask.get(), reads, names, clash=named)
            gate["clash"] = {"names": named, "choice": ch, "probs": probs}
            if not duels.sure(ch, probs, "one"):
                gate["answer"] = "several" if duels.sure(ch, probs, "several") else "undecided"
                for x in st["tables"].values():             # the names are withdrawn
                    x["species"], x["settled"] = None, "duel"
                    x["answer"] = f"{gate['answer']} (paper)"
        sp._save(out_dir, p, st)
        print(f"  [species duel] {p:22s} " + "; ".join(
            f"t{k}: {st['tables'][k].get('species') or st['tables'][k].get('answer') or 'open'}"
            for k in todo), flush=True)
    ask.unload()
