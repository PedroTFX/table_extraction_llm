"""The table model's answers (v24/table_model.py) against keys that do not come from the model and against today's
answers (main root full_run_v24), tuning papers only (dev + held_a). Files only, no model.

  N1 purpose   key: a table the GT draws on (calibration.py's test: its cells match GT rows for 40% or more and one GT
               trait holds half of them) is about organisms. Beside it, today's effective reading of the same tables:
               dropped by Q-KIND (not lifted by Q-ALSO, Q-ALSO2 or the one-species clash) or by structure 'no rows'.
               Tables the GT does not draw on have no key (the GT may simply not annotate them): counted, and every
               table that one reading would read and the other drop is listed, to be judged by hand.
  N2 row       key: structure_key.py (GT long -> 'measurement', GT wide -> 'organism' or 'part'), tables of several GT
               species, beside today's Q-ROW on the same tables.
  agreement    N1 x Q-KIND, N2 x Q-ROW, N2b x one_species rows, N2 'part' x row_label 'parts', on the tables both asked.

    python table_model_check.py     -> output/eval_split/TABLE_MODEL.txt, TABLE_MODEL_CASES.txt
"""
import collections
import json

import calibration as cal                 # puts src/v24 on the path; its keys and GT helpers
import _paths  # noqa: E402
import one_species as subj  # noqa: E402
import relevance as rv  # noqa: E402
import table_model as tm  # noqa: E402

SURE = 0.8
DROP_PURPOSE = tm.CLOSES                  # key, methods, figure
DROP_ROW = {"other"}


def old_reading(k, kind, struct, own, relev):
    """Today's effective reading of table k: 'read', or the reason it gives no rows."""
    lifted = subj.lifted(own).get(k, set())
    d = kind.get(str(k))
    if d and d.get("action") == "no rows" and k not in rv.lifts(relev) and "kind" not in lifted:
        return f"dropped by Q-KIND '{(d.get('kind') or {}).get('choice')}'"
    s = struct.get(str(k))
    if s and s.get("action") == "no rows" and "structure" not in lifted:
        return f"dropped by Q-ROW '{(s.get('row') or {}).get('choice')}'"
    return "read"


def new_reading(d, old):
    """The table model's reading; a node that is not sure leaves today's decision of that kind standing."""
    pu, ro = d["purpose"]["choice"], d["rows"]["choice"]
    if pu in DROP_PURPOSE:
        return f"dropped by N1 '{pu}'"
    if pu is None and old.startswith("dropped by Q-KIND"):
        return old + " (N1 not sure)"
    if ro in DROP_ROW:
        return f"dropped by N2 '{ro}'"
    if ro is None and old.startswith("dropped by Q-ROW"):
        return old + " (N2 not sure)"
    return "read"


def sure_choice(a):
    if not a or not a.get("probs"):
        return None
    ch = a.get("choice")
    return ch if a["probs"].get(ch, 0) >= SURE else f"{ch}?"


def main():
    head = cal.f24.head_runs()
    V = cal.V24
    T = collections.Counter()                         # tallies
    X = collections.defaultdict(collections.Counter)  # crosstabs
    C = collections.defaultdict(list)                 # cases
    n_papers = 0
    for p in cal.TUNING:
        res = tm.load(p)
        if not res or p not in head:
            continue
        inp = cal.crb.paper_inputs(_paths.PAPERS / p)
        if not inp:
            continue
        n_papers += 1
        rows = cal.ev.load_xlsx(str(inp[1]))
        gt = cal.crb.GroundTruth(rows)
        by = cal.gt_index(rows)
        kind, struct = cal.load(V / "kind" / f"{p}.json"), cal.load(V / "structure" / f"{p}.json")
        own, relev = cal.load(V / "one_species" / f"{p}.json"), cal.load(V / "relevance" / f"{p}.json")
        rlab = cal.load(V / "row_label" / f"{p}.json")
        for t, _ctx in cal.f24.tables_of(p, head):
            k = t.table_index
            d = res.get(str(k))
            if not d:
                continue
            T["tables asked"] += 1
            labels = cal.crb.derive_labels(t, gt) or {}
            lab = {h: L for h, (L, _e) in labels.items()}
            ids = cal.id_columns(t, gt)
            row_ids = cal.row_ids_of(t, gt, ids)
            skey, sinfo = cal.SKEY.get((p, k)), cal.SKINFO.get((p, k)) or {}
            long_vals = set(sinfo.get("values") or []) if skey == "GT long" else set()

            def gt_col(h):
                if h in long_vals or (lab.get(h) == "measurementValue" and skey == "GT long"):
                    return []
                got = cal.gt_traits(*cal.column_evidence(t, h, row_ids, by))
                if got:
                    return got
                if lab.get(h) == "measurementType" and cal.crb.header_names_trait(h, gt):
                    return []
                return None
            gt_table = bool(labels) and any(gt_col(c.name) is not None for c in t.columns)
            pu = d["purpose"]["choice"] or "not sure"
            ro = tm.leaf(d)
            top = d["rows"]["choice"] or "not sure"
            old = old_reading(k, kind, struct, own, relev)
            new = new_reading(d, old)
            where = f"{p} t{k} ({len(t.records)} rows; columns {[c.name for c in t.columns][:6]})"

            # N1 against the GT key
            grp = "GT draws on it" if gt_table else "GT does not draw on it"
            T[f"{grp}: tables"] += 1
            T[f"{grp}: N1 {pu}"] += 1
            T[f"{grp}: N2 {ro}"] += 1
            T[f"{grp}: today {old.split(' ')[0]}"] += 1
            T[f"{grp}: table model {new.split(' ')[0]}"] += 1
            if gt_table and (old != "read" or new != "read"):
                C["GT table dropped by a reading (the GT draws on it: should be read)"].append(
                    f"{where}: today {old}; table model {new}")
            if not gt_table and (old == "read") != (new == "read"):
                C["no key: one reading reads, the other drops (judge by hand)"].append(
                    f"{where}: today {old}; table model {new}")

            # N2 against the structure key, tables of several GT species
            several = len(set(row_ids) - {None}) >= 2
            if skey in ("GT long", "GT wide") and several:
                right = ro == "measurement" if skey == "GT long" else (top in ("organisms", "parts") and ro != "measurement")
                T[f"structure key {skey}: tables"] += 1
                T[f"structure key {skey}: N2 " + ("right" if right else ro)] += 1
                s = struct.get(str(k))
                if s and s.get("row"):
                    w_old = "record" if skey == "GT long" else "wide"
                    o = sure_choice(s["row"])
                    T[f"structure key {skey}: Q-ROW asked"] += 1
                    T[f"structure key {skey}: Q-ROW " + ("right" if o == w_old else str(o))] += 1
                if not right:
                    C["N2 against the structure key"].append(f"{where}: N2 {ro} ({skey}); Q-ROW "
                                                             f"{sure_choice((struct.get(str(k)) or {}).get('row'))}")

            # agreement with today's answers
            kd = kind.get(str(k))
            if kd and kd.get("kind"):
                X["N1 x Q-KIND"][(pu, sure_choice(kd["kind"]))] += 1
            sd = struct.get(str(k))
            if sd and sd.get("row"):
                X["N2 x Q-ROW"][(ro, sure_choice(sd["row"]))] += 1
            od = subj.table(own, k)
            if od and od.get("rows") and "how" in d:
                X["N2b x one_species rows"][((d["how"]["choice"] or "not sure"), od["rows"].get("choice") or "not sure")] += 1
            rd = (rlab.get(str(k)) or {}).get("labels") or {}
            if rd.get("whole"):
                X["N2 x row_label (first labels column)"][(top, sure_choice(rd["whole"]))] += 1

    L = [f"Table model phase 1, version 2 (N2 rows first, N1 purpose; both option orders) on {n_papers} tuning papers, {T['tables asked']} tables, against "
         "keys that do not come from the model and against today's answers (full_run_v24, main root).", ""]
    for grp in ("GT draws on it", "GT does not draw on it"):
        L.append(f"{grp}: {T[f'{grp}: tables']} tables")
        L.append("  N1: " + ", ".join(f"{k.split(': N1 ')[1]} {v}" for k, v in sorted(T.items())
                                       if k.startswith(f"{grp}: N1 ")))
        L.append("  N2: " + ", ".join(f"{k.split(': N2 ')[1]} {v}" for k, v in sorted(T.items())
                                       if k.startswith(f"{grp}: N2 ")))
        L.append(f"  read: today {T[f'{grp}: today read']}, table model {T[f'{grp}: table model read']}; "
                 f"dropped: today {T[f'{grp}: today dropped']}, table model {T[f'{grp}: table model dropped']}")
        L.append("")
    for sk in ("GT long", "GT wide"):
        if T[f"structure key {sk}: tables"]:
            L.append(f"structure key {sk}, several species: {T[f'structure key {sk}: tables']} tables")
            L.append("  N2: " + ", ".join(f"{k.split(': N2 ')[1]} {v}" for k, v in sorted(T.items())
                                           if k.startswith(f"structure key {sk}: N2 ")))
            L.append(f"  Q-ROW (asked on {T[f'structure key {sk}: Q-ROW asked']}): "
                     + ", ".join(f"{k.split(': Q-ROW ')[1]} {v}" for k, v in sorted(T.items())
                                 if k.startswith(f"structure key {sk}: Q-ROW ") and not k.endswith("asked")))
            L.append("")
    for name, tab in X.items():
        L.append(f"{name} (table model, today; '?' = not sure):")
        for (a, b), n in sorted(tab.items(), key=lambda x: -x[1]):
            L.append(f"  {n:4d}  {a:16s} {b}")
        L.append("")
    W = ["Tables where the readings differ or a key disagrees, tuning papers only.", ""]
    for name, xs in C.items():
        W.append(f"## {name}: {len(xs)}")
        W += [f"  {x}" for x in xs]
        W.append("")
    out = _paths.SUB / "output" / "eval_split"
    (out / "TABLE_MODEL.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    (out / "TABLE_MODEL_CASES.txt").write_text("\n".join(W) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
