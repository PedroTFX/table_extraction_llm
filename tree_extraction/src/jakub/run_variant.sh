#!/bin/bash
# A prose variant on one group of Jakub's papers (split_jakub.json), beside two_step's t2 rows (nothing of t2 changed):
# the papers two_step routed to prose, the prose stages as two_step runs them, with PROSE_VARIANT=<variant>,
# -> output_jakub_<set>/prose_<variant>/combined; then jakub_judge.py: t2 (two_step) and the variant, same papers.
#     bash run_variant.sh <variant> tune|test [newPDF imagePDF ocrPDF]
set -e
V=$1; G=$2; shift 2
SETS=${@:-newPDF imagePDF ocrPDF}
R=$HOME/table_extraction_llm
PY=$R/.venv/bin/python
SRC=$R/tree_extraction/src
for S in $SETS; do
  export TREE_PAPERS=$R/data/Jakub_papers/$S TREE_OUTPUT=$R/tree_extraction/output_jakub_$S PROSE_VARIANT=$V
  PAPERS=$($PY - <<PY
import json
a = json.load(open("$R/tree_extraction/output/eval_split/split_jakub.json"))["assign"]
st = json.load(open("$TREE_OUTPUT/two_step/status.json"))
print(" ".join(p for p, v in sorted(st.items()) if v.get("route") == "prose" and a.get(p) == "$G"))
PY
)
  echo "=== $S $V $G: $(echo $PAPERS | wc -w) prose papers $(date +%T)"
  cd $SRC/prose
  TREE=$(ls prose_tree_t2.py prose_tree_t1.py 2>/dev/null | head -1)
  mkdir -p $TREE_OUTPUT/prose_$V/logs
  for p in $PAPERS; do
    for st in "prose_reader.py abbrev" "prose_reader.py shape" "prose_reader.py nm" "prose_reader.py heads" \
              "prose_reader.py walk" "prose_reader.py field" "sentence_test.py" "$TREE treeread" \
              "prose_reader.py names" "prose_reader.py places" "prose_reader.py facts" "$TREE treefinal" \
              "prose_reader.py assemble"; do
      $PY -u $st $p >> $TREE_OUTPUT/prose_$V/logs/$p.log 2>&1 || { echo "  $p failed at $st"; break; }
    done
  done
  echo "=== $S $V $G done $(date +%T)"
done
unset TREE_PAPERS TREE_OUTPUT PROSE_VARIANT
cd $SRC/jakub
$PY -u jakub_judge.py $SETS --group $G
$PY -u jakub_judge.py $SETS --group $G --rows prose_$V/combined
