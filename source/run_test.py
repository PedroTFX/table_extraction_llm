"""run_test.py — run the extraction pipeline over the OTHER team's test papers
(data/test/{imagePDF,newPDF,ocrPDF}/) and score against their ground truth,
writing everything to a separate output tree so our real results stay untouched.

Layout of the test set (flat, one paper = three files):
    data/test/<cat>/<name>.pdf          the paper (raw PDF — needs MinerU)
    data/test/<cat>/<name>.xlsx         their GT spreadsheet (their schema)
    data/test/<cat>/<name>_gt.json      their GT (their schema) — what we score on

For each <name>.pdf we:
  1. build <name>.pdf.md via MinerU (cached next to the PDF)      [mineru_extract]
  2. run the extraction pipeline -> output_test/<cat>/<name>/<name>.csv [run_pipeline]
  3. adapt <name>_gt.json into template columns and evaluate       [gt_from_test + evaluate]
A summary.csv with per-paper precision/recall/F1 is written at the end.

IMPORTANT: we feed the pipeline ONLY the PDF-derived markdown. The paper's .xlsx
is GROUND TRUTH, never a source — passing it would leak the answers.

Run from source/:
    python run_test.py                    # all categories, all papers
    python run_test.py --cat newPDF       # one category
    python run_test.py --only n20-en      # one paper (any category)
    python run_test.py --limit 3          # first 3 papers overall (smoke test)
    python run_test.py --no-eval          # extract only
    python run_test.py --resume           # skip papers with a non-empty CSV
"""

from __future__ import annotations

import base64
import contextlib
import csv
import io
import json
import os
import sys
import time
import traceback
from pathlib import Path

from run_pipeline import run_pipeline
from evaluate import evaluate, DEFAULT_KEY
from mineru_extract import doc_to_markdown
from gt_from_test import write_template_xlsx

# The pipeline prints Unicode (e.g. "✓ Wrote ...") that the default Windows
# console codepage (cp1252) can't encode, which raises UnicodeEncodeError at the
# very last step and aborts an otherwise-finished paper. Force UTF-8 on our
# streams so those prints never crash the batch.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# A fresh MinerU token can be dropped in source/.mineru_token.txt (gitignored)
# instead of re-exporting MINERU_TOKEN and restarting the app. If present, it
# overrides the (often-expired) inherited env var for this process.
TOKEN_FILE = Path(__file__).with_name(".mineru_token.txt")


def _load_mineru_token():
    if not TOKEN_FILE.exists():
        return
    tok = TOKEN_FILE.read_text(encoding="utf-8").strip()
    if not tok:
        return
    os.environ["MINERU_TOKEN"] = tok
    # Best-effort expiry check so a stale token fails loudly, up front.
    try:
        payload = tok.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        exp = json.loads(base64.urlsafe_b64decode(payload)).get("exp")
        if exp and exp < time.time():
            hrs = (time.time() - exp) / 3600
            print(f"  [token] WARNING: {TOKEN_FILE.name} expired {hrs:.1f}h ago — "
                  "MinerU calls will 401. Get a fresh token at "
                  "https://mineru.net/apiManage/token")
        else:
            print(f"  [token] using {TOKEN_FILE.name} (valid)")
    except Exception:
        print(f"  [token] using {TOKEN_FILE.name}")

# --- paths -----------------------------------------------------------------
BASE = Path("../data/test")
CATEGORIES = ["imagePDF", "newPDF", "ocrPDF"]
OUTPUT_DIR = Path("../output_test")

# --- eval knobs ------------------------------------------------------------
DECODE_EVAL = False      # values are already decoded by the pipeline
SEMANTIC_EVAL = True     # remap predicted measurementType names onto GT wording
USE_LLM_EVAL = False     # keep the test run deterministic + fast (no Ollama confirm)

# MinerU language hint from the <name>-<lang> suffix. VLM is largely
# language-agnostic, so anything unmapped falls back to "en".
_LANG = {"en": "en", "fr": "fr", "de": "de", "ru": "ru", "chi": "ch",
         "ko": "ko", "es": "es", "it": "it", "tu": "tr", "lat": "en"}


def _lang_of(name: str) -> str:
    suffix = name.rsplit("-", 1)[-1].lower() if "-" in name else "en"
    return _LANG.get(suffix, "en")


def _iter_papers(only=None, cat=None, limit=None):
    """Yield (category, pdf_path) for the test papers to process."""
    cats = [cat] if cat else CATEGORIES
    count = 0
    for c in cats:
        folder = BASE / c
        if not folder.is_dir():
            print(f"  [warn] no such category folder: {folder}")
            continue
        for pdf in sorted(folder.glob("*.pdf")):
            if only and pdf.stem != only:
                continue
            yield c, pdf
            count += 1
            if limit and count >= limit:
                return


def main(only=None, cat=None, limit=None, evaluate_results=True, resume=False):
    _load_mineru_token()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    papers = list(_iter_papers(only=only, cat=cat, limit=limit))
    if not papers:
        raise SystemExit("No matching test papers found.")
    print(f"Processing {len(papers)} test paper(s)\n")

    summary = []
    for category, pdf in papers:
        name = pdf.stem
        paper_out = OUTPUT_DIR / category / name
        paper_out.mkdir(parents=True, exist_ok=True)
        out_csv = paper_out / f"{name}.csv"
        report = paper_out / f"{name}_report.txt"
        gt_json = pdf.with_name(f"{name}_gt.json")

        print("=" * 70)
        print(f"PAPER: {category}/{name}")
        print("=" * 70)

        if resume and out_csv.exists() and out_csv.stat().st_size > 0:
            print(f"  [skip] {out_csv.name} already exists — resuming past it")
            summary.append({"category": category, "paper": name, "precision": "",
                            "recall": "", "f1": "", "gt_rows": "",
                            "status": "skipped_resume"})
            continue

        try:
            # 1) PDF -> markdown via MinerU (cached as <name>.pdf.md next to the PDF)
            md_path = doc_to_markdown(pdf, backend="vlm", lang=_lang_of(name))

            # 2) extraction pipeline -> output_test/<cat>/<name>/<name>.csv
            run_pipeline(
                str(md_path),
                output_path=str(out_csv),
                out_dir=str(paper_out),
                chunk_size=None,
            )

            # 3) adapt their GT and evaluate
            if not evaluate_results:
                print("  (evaluation disabled via --no-eval)")
                summary.append({"category": category, "paper": name, "precision": "",
                                "recall": "", "f1": "", "gt_rows": "",
                                "status": "extracted_only"})
            elif gt_json.exists():
                gt_xlsx = paper_out / f"{name}_gt_template.xlsx"
                n_gt = write_template_xlsx(gt_json, gt_xlsx)
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    metrics = evaluate(str(out_csv), str(gt_xlsx), DEFAULT_KEY,
                                       DECODE_EVAL, semantic=SEMANTIC_EVAL,
                                       use_llm=USE_LLM_EVAL)
                report.write_text(buf.getvalue(), encoding="utf-8")
                p, r, f = metrics["row"]
                print(buf.getvalue())
                print(f"  -> P/R/F1 = {p:.3f}/{r:.3f}/{f:.3f}  (GT rows: {n_gt})"
                      f"   report: {report.name}")
                summary.append({"category": category, "paper": name,
                                "precision": round(p, 3), "recall": round(r, 3),
                                "f1": round(f, 3), "gt_rows": n_gt, "status": "ok"})
            else:
                print(f"  (no {gt_json.name} — skipped evaluation)")
                summary.append({"category": category, "paper": name, "precision": "",
                                "recall": "", "f1": "", "gt_rows": "",
                                "status": "no_ground_truth"})

        except Exception as e:
            print(f"  FAIL {name}: {e}")
            traceback.print_exc()
            summary.append({"category": category, "paper": name, "precision": "",
                            "recall": "", "f1": "", "gt_rows": "",
                            "status": f"FAIL: {e}"})

    # --- summary table ------------------------------------------------------
    tag = only or cat or "all"
    summary_path = OUTPUT_DIR / f"summary_{tag}.csv"
    with open(summary_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["category", "paper", "precision",
                                           "recall", "f1", "gt_rows", "status"])
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
    argv = sys.argv[1:]

    def _opt(flag):
        return argv[argv.index(flag) + 1] if flag in argv and argv.index(flag) + 1 < len(argv) else None

    only = _opt("--only")
    cat = _opt("--cat")
    limit = _opt("--limit")
    limit = int(limit) if limit else None
    no_eval = "--no-eval" in argv
    resume = "--resume" in argv
    main(only=only, cat=cat, limit=limit, evaluate_results=not no_eval, resume=resume)
