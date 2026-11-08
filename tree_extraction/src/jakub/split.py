"""Jakub's papers split for tuning and testing, all three sets mixed (the user, 2026-11-08: "a mix of all on the
tuning and test"): each set shuffled with one seed and cut in half, so both groups hold new, image and OCR PDFs.
-> tree_extraction/output/eval_split/split_jakub.json {"assign": {paper: "tune" | "test"}, "set": {paper: set}}

    python split.py
"""
import json
import random
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SEED = 20261108
out = {"seed": SEED, "rule": "per set, sorted then shuffled with the seed; the first half (rounded up) tunes",
       "assign": {}, "set": {}}
rng = random.Random(SEED)
for s in ("newPDF", "imagePDF", "ocrPDF"):
    papers = sorted(d.name for d in (REPO / "data" / "Jakub_papers" / s).iterdir() if d.is_dir() and list(d.glob("*.pdf")))
    rng.shuffle(papers)
    cut = (len(papers) + 1) // 2
    for i, p in enumerate(papers):
        out["assign"][p] = "tune" if i < cut else "test"
        out["set"][p] = s
f = REPO / "tree_extraction" / "output" / "eval_split" / "split_jakub.json"
f.write_text(json.dumps(out, indent=1), encoding="utf-8")
c = {}
for p, g in out["assign"].items():
    c[(out["set"][p], g)] = c.get((out["set"][p], g), 0) + 1
print(f"{len(out['assign'])} papers -> {f}: {c}")
