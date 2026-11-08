#!/bin/bash
# One of Jakub's sets through the tree extraction, on the remote, in a root of its own (nothing shared is touched).
#   1. wst_gt.py translate: the folders' GT in our template (group first for a set still flat)
#   2. MinerU on every folder without a _full.md, then its server stopped (one model on the GPU at a time)
#   3. the head reader blind (every table read, no GT), then two_step.py (tables; prose where routed)
#   4. jakub_score.py: tables, combined, totals -> <root>/jakub_scores.csv
#     bash run_set.sh newPDF|imagePDF|ocrPDF
set -e
SET=$1
R=$HOME/table_extraction_llm
PY=$R/.venv/bin/python
P=$R/data/Jakub_papers/$SET
NEW=$R/tree_extraction/output_jakub_$SET
export MINERU_EXE=$R/.mineru_venv/bin/mineru
echo "=== $SET start $(date)"
cd $R && git log --oneline -1 | cut -c1-80

echo "=== GT $(date +%T)"
cd $R/tree_extraction/src/jakub
$PY -u wst_gt.py translate $P

echo "=== MinerU $(date +%T)"
cd $R/source
$PY -u mineru_extract.py $P | grep -E "OK|FAIL|SKIP|Found" || true
$MINERU_EXE server stop >/dev/null 2>&1 || true
PAPERS=$(cd $P && for d in */; do d=${d%/}; [ -f "$d/${d}_full.md" ] && printf "%s " "$d"; done)
echo "papers with markdown: $(echo $PAPERS | wc -w)"

mkdir -p $NEW/eval_split
$PY - <<PY
import json
json.dump({"assign": {p: "jakub" for p in "$PAPERS".split()}}, open("$NEW/eval_split/split.json", "w"), indent=1)
PY
export TREE_PAPERS=$P TREE_OUTPUT=$NEW

echo "=== head reader (blind) $(date +%T)"
cd $R/tree_extraction/src/v18
$PY -u - <<PY
import head_more as hm, header_tree_bench as hb
hm.he.EXP.mkdir(parents=True, exist_ok=True)
if not hm.BENCH.exists():
    hm.BENCH.write_text("{}", encoding="utf-8")
hb.keyed_tables = lambda p: set(range(len(hb.html_tables(p))))
hm.main("$PAPERS".split())
PY

echo "=== two_step $(date +%T)"
cd $R/tree_extraction/src/prose
$PY -u two_step.py $PAPERS | grep -E "^step|routes" | cut -c1-200 || true

echo "=== score $(date +%T)"
cd $R/tree_extraction/src/jakub
$PY -u jakub_score.py tables combined > $NEW/jakub_score.log 2>&1
$PY -u jakub_score.py totals | tee $NEW/jakub_totals.txt
echo "=== $SET end $(date)"
