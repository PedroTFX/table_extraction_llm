"""Does the '-ptera' cell fact decide the taxon question? (2026-11-21, Viza2023 Suborder t7: the fact said 'the Latin
order ending' under a 'Suborder' header.) Every tuning table with a column the fact is printed for (30% or more of its
cells end in -ptera) is read twice through the B0.4 tree (column_variants: the names part of B), in one session: with
the old fact ('ptera' -> order) and with the neutral one (the ending, no rank, as column_tree.py now has it). Every
column of those tables is reported, so side effects show too. Tuning papers only (dev + held_a).

    python ptera_test.py       -> output/prompt_ab/PTERA_TEST.txt
"""
import json

import _paths
import column_tree as ct
import column_variants as cv
import decoder as v1
import prompt_ab as pa

OLD = [(e, "order" if e == "ptera" else r) for e, r in ct._RANK_ENDINGS]
NEW = list(ct._RANK_ENDINGS)
assert dict(NEW)["ptera"] is None, "column_tree.py should carry the neutral -ptera fact"


def ptera_columns(t):
    out = []
    for h in t.header_names:
        f = ct.cell_facts(t, h)
        c = f["endings"].get(("ptera", None), 0)
        if f["n"] and c / f["n"] >= 0.3:
            out.append(h)
    return out


def main():
    head = json.loads(pa.HEAD.read_text(encoding="utf-8"))
    papers = sorted(p for p, g in pa.SPLIT.items() if g in ("dev", "held_a"))
    client = ct.DecisionClient(*pa.MODEL)
    saved_nodes, saved_end = ct.NODES, ct._RANK_ENDINGS
    L = ["The -ptera fact, old ('the Latin order ending') against neutral (the ending alone), both on the B0.4 tree, "
         "one session. Tuning tables with a -ptera column; every column shown, changed ones marked '*'.", ""]
    n_tab = n_col = changed = 0
    try:
        ct.NODES = cv.build({"Bn"})
        for p in papers:
            _gt, text, tabs = pa.tables_of(p, head)
            for t, ctx, labels in tabs:
                cols = ptera_columns(t)
                if not cols:
                    continue
                n_tab += 1
                tid = f"{p}#{t.table_index}"
                got = {}
                for name, ends in (("old", OLD), ("neutral", NEW)):
                    ct._RANK_ENDINGS = ends
                    got[name] = ct.classify_table(t, text, client, table_context=True, seed=tid, extra_context=ctx)
                L.append(f"== {tid}  (-ptera columns: {cols})")
                for h in t.header_names:
                    a, b = got["old"]["greedy"].get(h), got["neutral"]["greedy"].get(h)
                    if a is None and b is None:
                        continue
                    n_col += 1
                    mark = "*" if a != b or got["old"]["paths"].get(h) != got["neutral"]["paths"].get(h) else " "
                    changed += mark == "*"
                    lab = (labels.get(h) or ["?"])[0]
                    L.append(f" {mark} '{h[:40]}'  key {lab}{'   (-ptera column)' if h in cols else ''}")
                    L.append(f"      old      {a}: {got['old']['paths'].get(h, '')}")
                    L.append(f"      neutral  {b}: {got['neutral']['paths'].get(h, '')}")
                L.append("")
    finally:
        ct.NODES, ct._RANK_ENDINGS = saved_nodes, saved_end
        v1.unload(pa.MODEL[0])
    L.insert(1, f"{n_tab} tables, {n_col} columns, {changed} with a different answer or path.")
    (_paths.OUTPUT / "prompt_ab" / "PTERA_TEST.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
