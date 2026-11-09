#!/bin/bash
# One prose variant on the papers given, in the root TREE_OUTPUT points at (default: the main output), the prose
# stages as two_step runs them: -> <root>/prose_<variant>/{prose,combined}/<paper>. Nothing of two_step is changed.
# Logs: <root>/prose_<variant>/logs/<paper>.log (they name the paper: for held_b papers, read only totals).
#     bash run_variant_papers.sh <variant> <paper> [<paper> ...]
V=$1; shift
R=$HOME/table_extraction_llm
PY=$R/.venv/bin/python
OUT=${TREE_OUTPUT:-$R/tree_extraction/output}
export PROSE_VARIANT=$V
cd $R/tree_extraction/src/prose
mkdir -p $OUT/prose_$V/logs
n=0; bad=0
for p in "$@"; do
  for st in "prose_reader.py abbrev" "prose_reader.py shape" "prose_reader.py nm" "prose_reader.py heads" \
            "prose_reader.py walk" "prose_reader.py field" "sentence_test.py" "prose_tree_t2.py treeread" \
            "prose_reader.py names" "prose_reader.py places" "prose_reader.py facts" "prose_tree_t2.py treefinal" \
            "prose_reader.py assemble"; do
    $PY -u $st $p >> $OUT/prose_$V/logs/$p.log 2>&1 || { bad=$((bad + 1)); break; }
  done
  n=$((n + 1))
done
echo "prose $V: $n papers, $bad failed $(date +%T)"
