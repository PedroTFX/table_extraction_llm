"""
Paths shared by the tree_extraction subproject, and access to the pipeline.

tree_extraction/ is an experiment beside the main extraction code: it READS the
pipeline (source/: table parsing, GT loading, the gemma mapper used as a
baseline) but never changes it. Importing this module puts source/ on the import
path, so `import tables`, `from evaluate import load_xlsx` work from here.
"""

import os
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent             # tree_extraction/src/<version folder>
SUB = next(p for p in SRC.parents if p.name == "tree_extraction")   # tree_extraction/
REPO = SUB.parent                                 # the main project
PIPELINE = REPO / "source"                        # the main extraction code
# TREE_PAPERS / TREE_OUTPUT run the whole subproject on another paper set (grit_run.py):
# every stage caches by paper name, so another set needs its own output root
PAPERS = Path(os.environ.get("TREE_PAPERS") or REPO / "data" / "un_processed_papers")
OUTPUT = Path(os.environ.get("TREE_OUTPUT") or SUB / "output")

if str(PIPELINE) not in sys.path:
    sys.path.insert(0, str(PIPELINE))
