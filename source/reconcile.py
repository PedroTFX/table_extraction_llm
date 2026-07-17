"""
reconcile.py — cross-check the same table read by different backends and surface
the cells that are likely READING ERRORS.

The premise: independent extractors rarely make the *same* mistake. So where two
or more backends agree on a value, trust it; where they disagree, flag it for
review. This is what turns "we extracted the table" into "we know which cells to
double-check."

Pipeline:
  1. group RawTables that describe the same underlying table (content overlap);
  2. within a group, parse each backend's grid to records (via table_parser),
     align records by identifier and columns by position;
  3. emit a ReconciledTable: the chosen "primary" reading, a per-field agreement
     map, and a list of concrete disagreements (missing rows, conflicting cells,
     shape mismatches).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from table_ir import RawTable, content_overlap, _norm
from table_parser import parse


# Which backend to believe when they disagree and no majority exists.
# Order is empirical, not theoretical: on the hardest real table tested (a
# 3-page borderless species×trait table with a 3-line wrapped name), MinerU was
# the only backend to reconstruct it perfectly — correct header, all 56 rows,
# wrapped name merged, and the one cell every other tool got wrong. Native
# structured sources (docx/xlsx) are exact and rank above any PDF reconstruction.
DEFAULT_PRIORITY = ["docx", "xlsx", "mineru", "docling", "pdfplumber-lines",
                    "geometry"]


@dataclass
class Disagreement:
    kind: str                       # "cell" | "missing_row" | "shape"
    identifier: str
    column: Optional[str]
    values: Dict[str, str]          # backend -> value
    note: str = ""


@dataclass
class ReconciledTable:
    primary_backend: str
    header: List[str]
    records: List[dict]
    backends: List[str]
    disagreements: List[Disagreement] = field(default_factory=list)
    confidence: str = "single"      # "agree" | "conflict" | "single"

    @property
    def n_conflicts(self) -> int:
        return sum(1 for d in self.disagreements if d.kind == "cell")


# ---------------------------------------------------------------------------
# grouping
# ---------------------------------------------------------------------------

def _ordinal_index(tables):
    """Position of each table within its own (source, backend) stream — i.e. its
    document order. The k-th table a backend reports from a file is the k-th
    table in that file."""
    seen, out = {}, {}
    for t in tables:
        key = (t.source, t.backend)
        seen[key] = seen.get(key, -1) + 1
        out[id(t)] = seen[key]
    return out


def group_tables(tables: List[RawTable], min_overlap=0.30) -> List[List[RawTable]]:
    """Cluster tables that describe the same underlying table.

    Two passes, because neither signal alone is sufficient:
      1. CONTENT OVERLAP within the same source file. Reliable when backends
         render cells similarly.
      2. DOCUMENT ORDER for whatever is left over. Layout-model backends (MinerU)
         report no page number and render cells very differently (`$\\chi^2$` vs
         `v2`), so a stats table read by two backends can score near-zero overlap
         and stay split. But the k-th table in a file is the k-th table in that
         file for every backend, so leftover singletons from different backends
         at the same ordinal are the same table.
    """
    ordinal = _ordinal_index(tables)
    groups: List[List[RawTable]] = []

    for t in tables:
        placed = False
        for g in groups:
            if g[0].source != t.source:
                continue
            if any(u.backend == t.backend for u in g):
                continue                      # a backend can't see one table twice
            if any(content_overlap(t, u) >= min_overlap for u in g):
                g.append(t)
                placed = True
                break
        if not placed:
            groups.append([t])

    # pass 2: pair singletons of different backends sitting at the same ordinal
    singles = [g for g in groups if len(g) == 1]
    merged = set()
    for i, g in enumerate(singles):
        if id(g[0]) in merged:
            continue
        for h in singles[i + 1:]:
            a, b = g[0], h[0]
            if id(b) in merged or a.source != b.source or a.backend == b.backend:
                continue
            if ordinal[id(a)] == ordinal[id(b)] and abs(a.ncols - b.ncols) <= 2:
                g.append(b)
                merged.add(id(b))
                break
    return [g for g in groups if not (len(g) == 1 and id(g[0]) in merged)]


# ---------------------------------------------------------------------------
# per-group reconciliation
# ---------------------------------------------------------------------------

def _records_of(rt: RawTable):
    """Parse one backend's grid into (header, {norm_id: record}). Identifier is
    the first header column's value; falls back to row index if empty."""
    pt = parse(rt.grid)
    header = pt.sections[0].header if pt.sections else []
    by_id = {}
    for i, r in enumerate(pt.records):
        idv = r.get(header[0], "") if header else ""
        key = _norm(idv) or f"__row{i}"
        by_id[key] = r
    return header, by_id


def reconcile_group(group: List[RawTable], priority=DEFAULT_PRIORITY) -> ReconciledTable:
    parsed = []
    for rt in group:
        try:
            header, by_id = _records_of(rt)
            parsed.append((rt, header, by_id))
        except Exception:
            continue
    if not parsed:
        return ReconciledTable("none", [], [], [rt.backend for rt in group])

    order = sorted(parsed, key=lambda p: (priority.index(p[0].backend)
                                          if p[0].backend in priority else 99))
    primary_rt, primary_header, primary_by_id = order[0]
    backends = [rt.backend for rt, _, _ in parsed]

    recon = ReconciledTable(primary_rt.backend, primary_header,
                            list(primary_by_id.values()), backends)

    if len(parsed) == 1:
        recon.confidence = "single"
        return recon

    all_ids = set()
    for _, _, by_id in parsed:
        all_ids |= set(by_id.keys())

    conflict = False
    for idv in sorted(all_ids):
        # positional (__row) identifiers can't be reliably aligned across
        # backends that fragmented pages differently — skip them to avoid noise.
        if idv.startswith("__row"):
            continue
        present = [(rt.backend, hdr, by_id[idv]) for rt, hdr, by_id in parsed if idv in by_id]
        if len(present) < 2:
            # a real identifier seen by only one backend is worth noting once
            if len(present) < len(parsed):
                recon.disagreements.append(Disagreement(
                    "missing_row", idv, None,
                    {rt.backend: ("yes" if any(rt.backend == b for b, _, _ in present)
                                  else "\u2014") for rt, _, _ in parsed},
                    note="row found by some backends only"))
                conflict = True
            continue
        # cell disagreements, aligned by column position
        ncols = min(len(hdr) for _, hdr, _ in present)
        for c in range(1, ncols):                # skip identifier column
            col_name = primary_header[c] if c < len(primary_header) else f"col{c}"
            vals = {}
            for backend, hdr, rec in present:
                vals[backend] = rec.get(hdr[c], "") if c < len(hdr) else ""
            norms = {_norm(v) for v in vals.values() if _norm(v)}
            if len(norms) > 1:
                recon.disagreements.append(Disagreement("cell", idv, col_name, vals))
                conflict = True

    recon.confidence = "conflict" if conflict else "agree"
    return recon


def reconcile(tables: List[RawTable], priority=DEFAULT_PRIORITY,
              min_overlap=0.30) -> List[ReconciledTable]:
    return [reconcile_group(g, priority) for g in group_tables(tables, min_overlap)]
