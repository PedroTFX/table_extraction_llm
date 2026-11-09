#!/bin/bash
# Iterations 1 + 2 on one group of Jakub's papers (2026-11-09): tables inside a species' account (full_run_v22,
# Q-KIND + Q-ACCOUNT) and both readers on every paper. Nothing of the baseline (two_step, prose_t2) is replaced.
#   1. full_run_v22 account:dry (code only: which tables, which account heading), then v22:account and assemble
#   2. prose t2 on the group's papers two_step had routed to tables (TREE_TABLES=v22)
#   3. rows:  v22_tables = v22 table rows + prose rows where two_step ran prose (iteration 2 alone)
#             v22_both   = v22 table rows + prose rows of every paper            (iterations 1 + 2)
#   4. jakub_judge.py: two_step (baseline), v22_tables, v22_both on the same papers
#     bash run_v22.sh tune|test [newPDF imagePDF ocrPDF]
set -e
G=$1; shift
SETS=${@:-newPDF imagePDF ocrPDF}
R=$HOME/table_extraction_llm
PY=$R/.venv/bin/python
SRC=$R/tree_extraction/src
for S in $SETS; do
  export TREE_PAPERS=$R/data/Jakub_papers/$S TREE_OUTPUT=$R/tree_extraction/output_jakub_$S TREE_TABLES=v22
  read ALL TOTAB < <($PY - <<PY
import json
a = json.load(open("$R/tree_extraction/output/eval_split/split_jakub.json"))["assign"]
st = json.load(open("$TREE_OUTPUT/two_step/status.json"))
g = [p for p in sorted(st) if a.get(p) == "$G"]
print(",".join(g), ",".join(p for p in g if st[p].get("route") != "prose"))
PY
)
  ALL=${ALL//,/ }; TOTAB=${TOTAB//,/ }
  echo "=== $S $G: $(echo $ALL | wc -w) papers, $(echo $TOTAB | wc -w) routed to tables $(date +%T)"
  cd $SRC/v22
  $PY -u full_run_v22.py account:dry $ALL | grep "account dry" || true
  $PY -u full_run_v22.py v22:account $ALL | grep "\[account\]" || true
  $PY -u full_run_v22.py assemble $ALL | tail -2
  echo "=== $S prose on the papers routed to tables $(date +%T)"
  cd $SRC/prose
  export PROSE_VARIANT=t2
  mkdir -p $TREE_OUTPUT/prose_t2/logs
  for p in $TOTAB; do
    for st in "prose_reader.py abbrev" "prose_reader.py shape" "prose_reader.py nm" "prose_reader.py heads" \
              "prose_reader.py walk" "prose_reader.py field" "sentence_test.py" "prose_tree_t2.py treeread" \
              "prose_reader.py names" "prose_reader.py places" "prose_reader.py facts" "prose_tree_t2.py treefinal" \
              "prose_reader.py assemble"; do
      $PY -u $st $p >> $TREE_OUTPUT/prose_t2/logs/$p.log 2>&1 || { echo "  $p failed at $st"; break; }
    done
  done
  unset PROSE_VARIANT
  $PY - <<PY
import csv, json
from pathlib import Path
O = Path("$TREE_OUTPUT")
st = json.load(open(O / "two_step/status.json"))
def rows(f):
    return list(csv.DictReader(open(f, encoding="utf-8", newline=""))) if f.exists() else []
n = {"v22_tables": 0, "v22_both": 0}
for p in "$ALL".split():
    tab = rows(O / "full_run_v22" / p / f"{p}.csv")
    prose = rows(O / "prose_t2" / "prose" / p / f"{p}.csv")
    for name, keep in (("v22_tables", st[p].get("route") == "prose"), ("v22_both", True)):
        out = tab + (prose if keep else [])
        d = O / name / p
        d.mkdir(parents=True, exist_ok=True)
        fields = list(tab[0] if tab else prose[0] if prose else {"verbatimIdentification": ""})
        for r in out:
            fields += [k for k in r if k not in fields]
        with open(d / f"{p}.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(out)
        n[name] += len(out)
print("rows written:", n)
PY
done
unset TREE_PAPERS TREE_OUTPUT TREE_TABLES
cd $SRC/jakub
for rows in two_step v22_tables v22_both; do
  $PY -u jakub_judge.py $SETS --group $G --rows $rows | grep -E "^####|exact names|exact \+ vague|TP exact"
done
