"""
run_all.py — run the full extraction pipeline over every paper folder and collect
all outputs in the project-root output/ folder.

For each folder under un_processed_papers/:
  1. build the single combined markdown (main + complementary)   [mineru_extract]
  2. run the extraction pipeline -> output/<paper>.csv            [run_pipeline]
  3. evaluate output/<paper>.csv vs the results xlsx, save a report
A summary.csv with per-paper precision/recall/F1 is written at the end.

Run from the source/ folder (where the modules live):
    python run_all.py
"""

from __future__ import annotations

import contextlib
import csv
import io
import sys
import traceback
from pathlib import Path

# The pipeline prints Unicode (e.g. "✓ Wrote ...") that the default Windows
# console codepage (cp1252) can't encode, which raises UnicodeEncodeError at the
# very last step and marks an otherwise-finished paper FAILed. Force UTF-8 on our
# streams so those prints never crash the run.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from run_pipeline import run_pipeline
from evaluate import evaluate, DEFAULT_KEY
from mineru_extract import classify_folder

# --- paths -----------------------------------------------------------------
BASE = Path("../data/un_processed_papers")
OUTPUT_DIR = Path("../output")

DECODE_EVAL = False     # values are already decoded by the pipeline
SEMANTIC_EVAL = True    # remap predicted measurementType names onto GT wording
USE_LLM_EVAL = True     # allow the LLM confirm pass (needs Ollama); False = det. only


def main(only_paper=None, evaluate_results=True, resume=False):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if only_paper:
        target = BASE / only_paper
        if not target.is_dir():
            raise SystemExit(f"No paper folder named '{only_paper}' under {BASE}")
        folders = [target]
        print(f"Running single paper: {only_paper}\n")
    else:
        folders = sorted(p for p in BASE.iterdir() if p.is_dir())
        print(f"Found {len(folders)} paper folder(s)\n")

    summary = []
    for folder in folders:
        paper = folder.name
        # one folder per paper inside output/, holding the CSV, the report, and
        # all intermediate JSONs (mappings, grouped_by_species, ...)
        paper_out = OUTPUT_DIR / paper
        paper_out.mkdir(parents=True, exist_ok=True)
        out_csv = paper_out / f"{paper}.csv"
        report = paper_out / f"{paper}_report.txt"
        print("=" * 70)
        print(f"PAPER: {paper}")
        print("=" * 70)

        # --resume: a non-empty output CSV means run_pipeline finished this paper
        # (write_output_csv is its last step), so skip past it. NOTE: this treats
        # ANY existing CSV as done, so only use it to continue an interrupted run —
        # not to re-do papers whose CSVs are stale from an earlier run.
        if resume and out_csv.exists() and out_csv.stat().st_size > 0:
            print(f"  [skip] {out_csv.name} already exists — resuming past it")
            summary.append({"paper": paper, "precision": "", "recall": "",
                            "f1": "", "status": "skipped_resume"})
            continue

        try:
            # 1) use the ALREADY-BUILT combined markdown (do NOT re-run mineru)
            full_md = folder / f"{paper}_full.md"
            if not full_md.exists():
                raise FileNotFoundError(
                    f"{full_md.name} not found — run mineru_extract.py first")

            # the results xlsx is needed for evaluation; find it via classify_folder.
            # NOTE: mineru_extract already folds every complementary source (incl.
            # xlsx/csv supplements, embedded as HTML tables) into <paper>_full.md,
            # so the md IS the complete source — do NOT also pass the supplements
            # here or their tables get counted twice.
            try:
                _, results_path, _ = classify_folder(folder)
                results_xlsx = str(results_path) if results_path else None
            except Exception:
                results_xlsx = None

            # 2) extraction pipeline -> output/<paper>/<paper>.csv
            #    intermediates (grouped json, mapping json) also go in output/<paper>/
            run_pipeline(
                str(full_md),
                output_path=str(out_csv),
                out_dir=str(paper_out),
                chunk_size=None,     # one chunk: feed the whole paper, no 6000 split
            )

            # 3) evaluate against the results xlsx (if present), capturing the
            #    printed report to a file and the metrics to the summary
            if not evaluate_results:
                print("  (evaluation disabled via --no-eval)")
                summary.append({"paper": paper, "precision": "", "recall": "",
                                "f1": "", "status": "extracted_only"})
            elif results_xlsx and Path(results_xlsx).exists():
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    metrics = evaluate(str(out_csv), results_xlsx, DEFAULT_KEY,
                                       DECODE_EVAL, semantic=SEMANTIC_EVAL,
                                       use_llm=USE_LLM_EVAL)
                report.write_text(buf.getvalue(), encoding="utf-8")
                p, r, f = metrics["row"]
                print(buf.getvalue())
                print(f"  -> P/R/F1 = {p:.3f}/{r:.3f}/{f:.3f}   report: {report.name}")
                summary.append({"paper": paper, "precision": round(p, 3),
                                "recall": round(r, 3), "f1": round(f, 3),
                                "status": "ok"})
            else:
                print("  (no results xlsx — skipped evaluation)")
                summary.append({"paper": paper, "precision": "", "recall": "",
                                "f1": "", "status": "no_ground_truth"})

        except Exception as e:
            print(f"  FAIL {paper}: {e}")
            traceback.print_exc()
            summary.append({"paper": paper, "precision": "", "recall": "",
                            "f1": "", "status": f"FAIL: {e}"})

    # --- summary table ------------------------------------------------------
    summary_path = OUTPUT_DIR / (f"summary_{only_paper}.csv" if only_paper else "summary.csv")
    with open(summary_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["paper", "precision", "recall", "f1", "status"])
        w.writeheader()
        w.writerows(summary)

    print("\n" + "=" * 70)
    print(f"DONE. {len(summary)} paper(s). Summary -> {summary_path}")
    ok = [s for s in summary if s["status"] == "ok"]
    if ok:
        avg = sum(s["f1"] for s in ok) / len(ok)
        print(f"Evaluated {len(ok)} paper(s); mean F1 = {avg:.3f}")
    print("=" * 70)


if __name__ == "__main__":
    import sys
    # Optional args (any order):
    #   a single paper (folder) name to process, e.g.  python run_all.py Araujo2021
    #   --no-eval  extract only; skip scoring against the results xlsx
    #   --resume   skip papers that already have a non-empty output CSV
    argv = sys.argv[1:]
    no_eval = "--no-eval" in argv
    resume = "--resume" in argv
    positional = [a for a in argv if not a.startswith("-")]
    only = positional[0] if positional else None
    main(only_paper=only, evaluate_results=not no_eval, resume=resume)