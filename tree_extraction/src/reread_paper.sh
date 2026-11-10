#!/bin/bash
# A paper read again in a root of its own (plans/08_evaluation.md D). Every stage caches by paper name, so a paper whose
# markdown changed (Figueroa2021), or that got a table the head reader had skipped (head_wide.py, Chichorro2022), keeps
# its old answers in the main root. Here nothing of the main root is touched: -> tree_extraction/output_reread.
#   head    blind: the head reader reads every table again (a changed markdown)
#           keep:  the main root's head readings of the paper are copied, then head_wide.py reads its too-wide tables
#   then    full_run_v18 run, full_run_v24 stages + assemble, and the scorer on both
#     bash reread_paper.sh blind|keep <paper> [<paper> ...]        (TREE_PAPERS picks another paper folder)
set -e
HEADMODE=$1; shift
R=$HOME/table_extraction_llm
PY=$R/.venv/bin/python
MAIN=${REREAD_FROM:-$R/tree_extraction/output}
NEW=$R/tree_extraction/output_reread
export TREE_OUTPUT=$NEW
mkdir -p $NEW/eval_split $NEW/header_tree_bench/experiments
$PY - "$NEW" "$MAIN" "$HEADMODE" "$@" <<'PY'
import json, sys
from pathlib import Path
new, main, mode, papers = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], sys.argv[4:]
f = new / "eval_split" / "split.json"
assign = json.loads(f.read_text(encoding="utf-8"))["assign"] if f.exists() else {}
assign.update({p: "reread" for p in papers})
f.write_text(json.dumps({"assign": assign}, indent=1), encoding="utf-8")
exp = new / "header_tree_bench" / "experiments"
for name in ("round2.json", "reader2_all.json"):
    if not (exp / name).exists():
        (exp / name).write_text("{}", encoding="utf-8")
if mode == "keep":
    src = json.loads((main / "header_tree_bench" / "experiments" / "reader2_all.json").read_text(encoding="utf-8"))
    dst = json.loads((exp / "reader2_all.json").read_text(encoding="utf-8"))
    for p in papers:
        dst.setdefault(p, src.get(p, []))
    (exp / "reader2_all.json").write_text(json.dumps(dst, indent=1, ensure_ascii=False), encoding="utf-8")
PY

cd $R/tree_extraction/src/v24
if [ "$HEADMODE" = blind ]; then
  echo "=== head reader, every table $(date +%T)"
  $PY -u - "$@" <<'PY'
import sys
import head_more as hm, header_tree_bench as hb
hb.keyed_tables = lambda p: set(range(len(hb.html_tables(p))))
hm.main(sys.argv[1:])
PY
fi
echo "=== head_wide $(date +%T)"
$PY -u head_wide.py "$@" | tail -5

echo "=== full_run_v18 $(date +%T)"
cd $R/tree_extraction/src/v18
$PY -u full_run_v18.py run "$@" > $NEW/reread_v18.log 2>&1 || { echo "v18 FAILED: tail $NEW/reread_v18.log"; exit 1; }
grep "assembled" $NEW/reread_v18.log || true
echo "=== full_run_v24 $(date +%T)"
cd $R/tree_extraction/src/v24
for st in v23:units v22:account v24:relevance v24:rowlabel assemble; do
  $PY -u full_run_v24.py $st "$@" >> $NEW/reread_v24.log 2>&1 || { echo "v24 FAILED at $st: tail $NEW/reread_v24.log"; exit 1; }
done
grep "assembled" $NEW/reread_v24.log || true
echo "=== score $(date +%T)"
$PY -u - <<'PY'
import _paths
import evaluate as ev
ev.ASSESS_MISS_SEVERITY = False
for v in ("full_run_v18", "full_run_v24"):
    ev.evaluate_all(_paths.PAPERS, _paths.OUTPUT / v, ev.DEFAULT_KEY, False, semantic=True, use_llm=True, skip_existing=True)
    for d in sorted((_paths.OUTPUT / v).iterdir()):
        rep = d / f"{d.name}_report.txt"
        m = ev._metrics_from_report(rep) if rep.exists() else None
        if m:
            print(f"  {v}  {d.name:22s} P {float(m[0]):.3f}  R {float(m[1]):.3f}  F1 {float(m[2]):.3f}")
PY
echo "=== done $(date +%T): rows in $NEW/full_run_v18 and $NEW/full_run_v24"
