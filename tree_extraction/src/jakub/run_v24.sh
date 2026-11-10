#!/bin/bash
# full_run_v24 (the fix plans of 2026-11-10) on one group of Jakub's papers. Nothing of the baseline (two_step, prose_t2)
# or of v22's rows is replaced.
#   1. the four model stages on the group's papers (v22's account answers are taken over where they exist)
#   2. rows per layer set: v24_<layers> = v24's table rows + the prose rows of the papers two_step routed to prose
#   3. jakub_judge.py: two_step (baseline), v22_tables (if run_v22.sh made it), and each layer set, on the same papers
#     bash run_v24.sh tune|test [newPDF imagePDF ocrPDF]
set -e
G=$1; shift
SETS=${@:-newPDF imagePDF ocrPDF}
R=$HOME/table_extraction_llm
PY=$R/.venv/bin/python
SRC=$R/tree_extraction/src
LAYERSETS="account account,rowlabel units,account,relevance,rowlabel"
for S in $SETS; do
  export TREE_PAPERS=$R/data/Jakub_papers/$S TREE_OUTPUT=$R/tree_extraction/output_jakub_$S
  ALL=$($PY - <<PY
import json
a = json.load(open("$R/tree_extraction/output/eval_split/split_jakub.json", encoding="utf-8"))["assign"]
st = json.load(open("$TREE_OUTPUT/two_step/status.json", encoding="utf-8"))
print(" ".join(p for p in sorted(st) if a.get(p) == "$G"))
PY
)
  echo "=== $S $G: $(echo $ALL | wc -w) papers $(date +%T)"
  cd $SRC/v24
  mkdir -p $TREE_OUTPUT/full_run_v24_logs
  for st in v23:units v22:account v24:relevance v24:rowlabel; do
    $PY -u full_run_v24.py $st $ALL > $TREE_OUTPUT/full_run_v24_logs/${st//:/_}_$G.log 2>&1 || echo "  FAILED $st: see full_run_v24_logs"
    echo "  $st: $(grep -cE '^\s+\[' $TREE_OUTPUT/full_run_v24_logs/${st//:/_}_$G.log || true) papers answered $(date +%T)"
  done
  for L in $LAYERSETS; do
    T=${L//,/+}
    V24_LAYERS=$L $PY -u full_run_v24.py assemble $ALL | tail -2 | cut -c1-160
    V24_LAYERS=$L $PY - <<PY
import csv, json
from pathlib import Path
O = Path("$TREE_OUTPUT")
tag = "$T"
src = O / ("full_run_v24" if tag == "units+account+relevance+rowlabel" else "full_run_v24_" + tag)
st = json.load(open(O / "two_step/status.json", encoding="utf-8"))
def rows(f):
    return list(csv.DictReader(open(f, encoding="utf-8", newline=""))) if f.exists() else []
n = 0
for p in "$ALL".split():
    tab = rows(src / p / f"{p}.csv")
    prose = rows(O / "prose_t2" / "prose" / p / f"{p}.csv") if st[p].get("route") == "prose" else []
    out = tab + prose
    d = O / ("v24_" + tag) / p
    d.mkdir(parents=True, exist_ok=True)
    fields = list(tab[0] if tab else prose[0] if prose else {"verbatimIdentification": ""})
    for r in out:
        fields += [k for k in r if k not in fields]
    with open(d / f"{p}.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(out)
    n += len(out)
print("rows written for v24_" + tag + ":", n)
PY
  done
done
unset TREE_PAPERS TREE_OUTPUT
cd $SRC/jakub
ROWS="two_step"
[ -d $R/tree_extraction/output_jakub_${SETS%% *}/v22_tables ] && ROWS="$ROWS v22_tables"
for L in $LAYERSETS; do ROWS="$ROWS v24_${L//,/+}"; done
for rows in $ROWS; do
  $PY -u jakub_judge.py $SETS --group $G --rows $rows | grep -E "^####|exact names|exact \+ vague|TP exact"
done
