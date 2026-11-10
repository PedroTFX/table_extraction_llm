#!/bin/bash
# The fix plans of 2026-11-10 on one paper set, on the remote: the four model stages once (answers in
# <root>/full_run_v24), then the rows and the score per layer set against v18 (code + the scorer).
# TREE_PAPERS / TREE_OUTPUT pick another set's root (grit), as for the other runs. One model at a time.
#     bash run_v24.sh smoke  <paper> [<paper> ...]     stages + score on a few tuning papers, per-paper lines on screen
#     bash run_v24.sh stages <group>                   v23:units, v22:account, v24:relevance, v24:rowlabel
#     bash run_v24.sh score  <group>                   assemble + score_v24.py for each layer set below
# <group>: tuning (dev + held_a of split_v15.json) | held_b | all (every paper of the root's split.json) | paper names.
# Nothing but counts and totals goes to the screen for a group (held_b and grit-only names stay in the logs).
# Layer sets scored: units | account+rowlabel | relevance | all four.
set -e
MODE=$1; shift
R=$HOME/table_extraction_llm
PY=$R/.venv/bin/python
OUT=${TREE_OUTPUT:-$R/tree_extraction/output}
cd $R/tree_extraction/src/v24
LOG=$OUT/full_run_v24_logs
mkdir -p $LOG
SETS="units account,rowlabel relevance units,account,relevance,rowlabel"

PAPERS=$($PY - "$OUT" "$R" "$@" <<'PY'
import json, sys
out, repo, args = sys.argv[1], sys.argv[2], sys.argv[3:]
load = lambda f: json.load(open(f, encoding="utf-8"))["assign"]
if args[:1] == ["tuning"]:
    print(" ".join(p for p, g in load(repo + "/tree_extraction/output/eval_split/split_v15.json").items() if g in ("dev", "held_a")))
elif args[:1] == ["held_b"]:
    print(" ".join(p for p, g in load(repo + "/tree_extraction/output/eval_split/split_v15.json").items() if g == "held_b"))
elif args[:1] == ["all"]:
    print(" ".join(load(out + "/eval_split/split.json")))
else:
    print(" ".join(args))
PY
)
N=$(echo $PAPERS | wc -w)
[ "$N" -gt 0 ] || { echo "no papers"; exit 1; }
SHOW='^\s+\[|Traceback|Error'
[ "$MODE" = smoke ] || SHOW='Traceback|Error'

stages() {
  for st in v23:units v22:account v24:relevance v24:rowlabel; do
    echo "=== $st on $N papers $(date +%T)"
    $PY -u full_run_v24.py $st $PAPERS > $LOG/${st//:/_}.log 2>&1 || echo "    FAILED: tail $LOG/${st//:/_}.log"
    grep -E "$SHOW" $LOG/${st//:/_}.log | cut -c1-220 || true
    echo "    papers answered: $(grep -cE '^\s+\[' $LOG/${st//:/_}.log || true)"
  done
  $PY -u full_run_v24.py v24:relevance:report $PAPERS > $LOG/relevance_report.txt 2>&1 || true
  echo "what relevance takes out: $LOG/relevance_report.txt (tuning papers by name)"
}

score() {
  for L in $SETS; do
    echo "=== layers $L $(date +%T)"
    V24_LAYERS=$L $PY -u full_run_v24.py assemble $PAPERS > $LOG/assemble_${L//,/+}.log 2>&1 || echo "    FAILED: tail $LOG/assemble_${L//,/+}.log"
    tail -2 $LOG/assemble_${L//,/+}.log | cut -c1-200
    V24_LAYERS=$L $PY -u score_v24.py $PAPERS > $LOG/score_${L//,/+}.log 2>&1 || echo "    FAILED: tail $LOG/score_${L//,/+}.log"
    grep -E "^v24|^  (dev|held_a|held_b|grit) |^      " $LOG/score_${L//,/+}.log || true
  done
}

case $MODE in
  stages) stages ;;
  score) score ;;
  smoke) stages; score ;;
  *) echo "smoke | stages | score"; exit 1 ;;
esac
echo "=== done $(date +%T)"
