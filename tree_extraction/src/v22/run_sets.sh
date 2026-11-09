#!/bin/bash
# v22 on the 109 set, then grit: the account step (Q-KIND + Q-ACCOUNT), assemble, then score_v22.py against v18.
# Logs name papers (held_b, grit-only): read only <root>/V22_TOTALS.txt.
#     bash run_sets.sh
R=$HOME/table_extraction_llm
PY=$R/.venv/bin/python
cd $R/tree_extraction/src/v22
for spec in "109:$R/data/un_processed_papers:$R/tree_extraction/output" "grit:$R/data/grit_testing:$R/tree_extraction/output_grit"; do
  IFS=: read -r name P O <<< "$spec"
  export TREE_PAPERS=$P TREE_OUTPUT=$O
  echo "=== $name account $(date +%T)"
  $PY -u full_run_v22.py v22:account all > $O/v22_account.log 2>&1 || echo "  account step failed (see $O/v22_account.log)"
  echo "=== $name assemble $(date +%T)"
  $PY -u full_run_v22.py assemble all > $O/v22_assemble.log 2>&1 || echo "  assemble failed"
  echo "=== $name score $(date +%T)"
  $PY -u score_v22.py > $O/v22_score.log 2>&1 || echo "  score failed"
  echo "=== $name done $(date +%T)"
done
