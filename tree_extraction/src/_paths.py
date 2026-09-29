"""
Paths shared by the tree_extraction subproject, and access to the pipeline.

tree_extraction/ is an experiment beside the main extraction code: it READS the
pipeline (source/: table parsing, GT loading, the gemma mapper used as a
baseline) but never changes it. Importing this module puts source/ on the import
path, so `import tables`, `from evaluate import load_xlsx` work from here.
"""

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent             # tree_extraction/src
SUB = SRC.parent                                  # tree_extraction/
REPO = SUB.parent                                 # the main project
PIPELINE = REPO / "source"                        # the main extraction code
PAPERS = REPO / "data" / "un_processed_papers"    # <paper>/<paper>_full.md + GT xlsx
OUTPUT = SUB / "output"                           # every result of this subproject

if str(PIPELINE) not in sys.path:
    sys.path.insert(0, str(PIPELINE))
