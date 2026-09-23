"""
run_pipeline.py — extract structured trait records from a paper *and its
complementary files* into the team's output CSV.

A "document set" is the main paper plus any supplementary files that carry
extra tables (xlsx/csv/extra md). Pass them all to ``run_pipeline``; tables are
collected from every file (with provenance), mapped, grouped into one
species-keyed structure, enriched, decoded, and written out.

Stages
  1. collect + map tables from all sources, group by species   (table_to_data)
  2. build the prose chunks used by the tag agents             (text_manager)
  3. measurement-level tags per column                         (fill_template)
  4. paper-level tags per species                              (fill_template)
  4b value-legend decoding (footnote-first, LLM fallback)      (fill_template)
  5. emit output.csv                                           (to_output)
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from text_manager import get_text
from table_to_data import map_and_group, table_id, _identifier_column
from fill_template import (get_measurement_level_tags, route_tags, apply_plan,
                           decode_grouped_values)
from to_output import write_output_csv

# Fields the volunteers fill with constants; override empties at output time.
# Pull associatedReferences from your per-paper metadata rather than hardcoding.
DEFAULTS = {
    "measurementStatistic": "mode",
    "sex": "both",
    "lifeStage": "adult",
    # PreservedSpecimen is the overwhelmingly dominant basisOfRecord in the GT
    # (morphology off specimens). Used only when the tag step left it empty or
    # returned a non-DwC description (cleared by to_output.normalize_basis_out).
    "basisOfRecord": "PreservedSpecimen",
}


def prose_chunks(sources, chunk_size=None):
    """Concatenate the prose (tables stripped) of all md/html/txt sources into
    chunks for the tag agents. xlsx/csv carry no prose and are ignored here.

    ``chunk_size=None`` => one big chunk (fine for a single small paper; switch
    to a real size, e.g. 6000, once papers + supplements get long — the agents
    already judge across multiple chunks)."""
    texts = []
    for src in sources:
        p = Path(src)
        if p.suffix.lower() in {".md", ".html", ".htm", ".txt"}:
            texts.append(p.read_text(encoding="utf-8", errors="replace"))
    full = "\n\n".join(texts)
    size = chunk_size or max(len(full), 1)
    pieces = get_text(full, size)
    if chunk_size is None:
        return [{"content": "\n\n".join(c["content"] for c in pieces)}]
    return pieces


def run_pipeline(paper_filename, complementary_files=(), output_path="output.csv",
                 out_dir=".", citation=None, chunk_size=None):
    sources = [paper_filename, *complementary_files]
    print("=" * 60)
    print(f"Document set: {[Path(s).name for s in sources]}")
    print("=" * 60)
    t0 = time.time()

    # 1) tables -> mappings -> grouped
    print("\n[1/5] Collecting + mapping tables, grouping by species...")
    paper_text = "\n\n".join(
        Path(s).read_text(encoding="utf-8", errors="replace")
        for s in sources if Path(s).suffix.lower() in {".md", ".html", ".htm", ".txt"})
    grouped, tables, mappings = map_and_group(sources, paper_text, out_dir=out_dir)
    grouped_path = str(Path(out_dir) / "grouped_by_species.json")
    Path(grouped_path).write_text(json.dumps(grouped, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  grouped {len(grouped)} species from {len(tables)} table(s)")

    # 2) prose chunks
    print("\n[2/5] Building prose chunks...")
    chunks = prose_chunks(sources, chunk_size=chunk_size)
    print(f"  {len(chunks)} chunk(s)")

    # Tag routing plan — decide each tag's LEVEL once instead of hardcoding which
    # tags are measurement-level vs paper-level. Column tags are column-level by
    # nature; the cross-record tags (sex/lifeStage/caste) are classified by one
    # LLM pass, with 'derived' resolved from a curated rule (e.g. caste -> sex).
    print("\n[plan] Routing tags to levels...")
    COLUMN_TAGS = ["basisOfRecord", "measurementMethod", "measurementUnit", "measurementStatistic"]
    CROSS_TAGS = ["sex", "lifeStage", "caste"]
    plan = {t: {"level": "column"} for t in COLUMN_TAGS}
    plan.update(route_tags(CROSS_TAGS, list(grouped.keys()), chunks))
    for tag, spec in plan.items():
        extra = {k: spec[k] for k in ("value", "from") if k in spec}
        print(f"  {tag}: {spec['level']}" + (f" {extra}" if extra else ""))
    column_tags = {t for t, s in plan.items() if s["level"] == "column"}

    # 3) measurement-level (column) tags — only those the plan routed to 'column'
    print("\n[3/5] Measurement-level tags...")
    # Page-fragments of one table share a schema and a mapping, so tag ONCE per
    # distinct header set and copy the result to its fragments (see map_and_group).
    import copy as _copy
    tag_cache: dict = {}
    for table in tables:
        tid = table_id(table)
        if tid not in mappings:
            continue
        # Only tag tables that actually produced specimen rows. A table with no
        # identifier column (e.g. a GLMM/stats table) was dropped at grouping, so
        # tagging its columns just wastes LLM calls.
        if _identifier_column(table, mappings[tid]) is None:
            print(f"  skip tags for {tid} — no identifier column (not specimen data)")
            continue
        sig = tuple(table.header_names)
        if sig in tag_cache:
            mappings[tid] = _copy.deepcopy(tag_cache[sig])
            print(f"  reuse tags for {tid} — same schema as an earlier table")
        else:
            mappings[tid] = get_measurement_level_tags(
                mappings[tid], chunks, allowed_tags=column_tags)
            tag_cache[sig] = mappings[tid]
        (Path(out_dir) / f"{tid}_mapping.json").write_text(
            json.dumps(mappings[tid], indent=2, ensure_ascii=False), encoding="utf-8")

    # 4) apply paper / species / derived tags onto grouped per the plan
    print("\n[4/5] Applying paper/species/derived tags...")
    apply_plan(plan, grouped_path)

    # 4b) decode legends
    print("\n[4b] Decoding value legends...")
    decode_grouped_values(grouped_path, tables, paper_text, chunks, mappings)

    # 5) output csv
    print("\n[5/5] Writing output CSV...")
    defaults = dict(DEFAULTS)
    if citation:
        defaults["associatedReferences "] = citation
    write_output_csv(
        grouped_path=grouped_path,
        mapping_paths=[str(Path(out_dir) / f"{table_id(t)}_mapping.json") for t in tables],
        output_path=output_path,
        decode=False,            # values already decoded in 4b
        keep_protocol=False,
        defaults=defaults,
    )

    print(f"\nDONE in {time.time() - t0:.1f}s -> {output_path}")


if __name__ == "__main__":
    run_pipeline(
        "Abensperg-Traun M. (1991).md",
        complementary_files=[],     # e.g. ["Abensperg-Traun M. (1991)_S1.xlsx"]
        citation=("Abensperg-Traun M. 1991. Seasonal changes in activity of "
                  "subterranean termite species (Isoptera) in Western Australian "
                  "wheatbelt habitats. Australian Journal of Ecology 16, 331-336."),
    )