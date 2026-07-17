"""
table_ir.py — the shared representation every extraction backend emits.

The whole architecture hinges on this: no matter which tool read the table
(pdfplumber, Docling, MinerU, python-docx, openpyxl), it produces the SAME thing
— a RawTable: an aligned grid of cell strings plus provenance. Everything
downstream (the semantic parser, the reconciler, the reporter) works on RawTable
and never needs to know which tool produced it.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class RawTable:
    grid: List[List[str]]                       # aligned cell strings
    backend: str                                # e.g. "pdfplumber-lines"
    source: str                                 # file path it came from
    page: Optional[int] = None                  # page index (pdf) or None
    bbox: Optional[Tuple[float, float, float, float]] = None  # x0,top,x1,bottom
    meta: dict = field(default_factory=dict)

    def __post_init__(self):
        self.grid = normalize_grid(self.grid)

    @property
    def nrows(self) -> int:
        return len(self.grid)

    @property
    def ncols(self) -> int:
        return len(self.grid[0]) if self.grid else 0

    def cells(self) -> List[str]:
        return [c for row in self.grid for c in row if c.strip()]

    def signature(self) -> Counter:
        """Multiset of normalized non-empty cell values — used to tell whether two
        backends extracted the same underlying table (content overlap), which is
        robust to differing page coordinates across tools."""
        return Counter(_norm(c) for c in self.cells())


def normalize_grid(grid) -> List[List[str]]:
    """Strip cells, coerce to str, pad ragged rows to the widest width, and drop
    fully-empty trailing/leading rows."""
    g = [[("" if c is None else str(c).strip()) for c in row] for row in (grid or [])]
    g = [row for row in g if any(c for c in row)]        # drop all-blank rows
    width = max((len(r) for r in g), default=0)
    return [r + [""] * (width - len(r)) for r in g]


_LATEX_CMD = re.compile(r"\\([a-zA-Z]+)\s*")
_MATH_DELIM = re.compile(r"\$+")
_MD_EMPH = re.compile(r"[*_`]{1,3}")

# Different backends spell the same glyph differently. MinerU emits `$\chi^2$`
# where the geometry reader sees the ligature `v2`; unless these fold together,
# two readings of the SAME table look unrelated and never group.
_SYMBOL_ALIASES = {
    "chi^2": "x2", "chi2": "x2", "χ2": "x2", "χ²": "x2", "v2": "x2",
    "\u00b1": "+/-", "\u2013": "-", "\u2014": "-", "\u2212": "-",
}


def _norm(s: str) -> str:
    """Aggressive normalization for cross-backend value comparison: strip math
    delimiters, LaTeX commands and markdown emphasis, fold symbol spellings,
    lowercase and collapse whitespace."""
    s = re.sub(r"[\u2020\u2021\u00a7\u00b6\uFFFD]", "", str(s))
    s = s.replace("\xa0", " ")
    s = _MATH_DELIM.sub(" ", s)
    s = _LATEX_CMD.sub(r"\1", s)                  # \chi -> chi (no added space)
    s = re.sub(r"[\^_{}]", "", s)                 # chi^2 -> chi2
    s = _MD_EMPH.sub("", s)
    s = re.sub(r"\s+", " ", s).strip().lower()
    for a, b in _SYMBOL_ALIASES.items():
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()


def content_overlap(a: RawTable, b: RawTable) -> float:
    """Jaccard-like overlap of two tables' cell multisets (0..1). High overlap =>
    same underlying table read by two backends."""
    sa, sb = a.signature(), b.signature()
    if not sa or not sb:
        return 0.0
    inter = sum((sa & sb).values())
    union = sum((sa | sb).values())
    return inter / union if union else 0.0
