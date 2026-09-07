"""
check_sync.py — verify the modules in source/ are a consistent set BEFORE a run.

Two ImportErrors in a row came from the same cause: one file updated, another not,
or a file saved incompletely. The tracebacks were misleading — a missing symbol in
tables.py reports as an error in table_to_data.py, and a truncated file reports as
a missing function rather than as a short file. This checks directly.

    python check_sync.py

Exit code 0 = consistent, 1 = something is missing. Prints every problem, not
just the first, so one run tells you everything to fix.
"""

from __future__ import annotations

import importlib
import sys
import traceback
from pathlib import Path

# Symbols each module must expose for the others to work. Keep in step with the
# imports at the top of each file.
REQUIRED = {
    "tables": [
        "Table", "parse_table", "clean_text", "find_abbreviation_definitions",
        "find_binomial_candidates", "is_headerless_continuation",
        "looks_multivalue_column", "split_multivalue",
        "detect_transposed", "transpose_table", "looks_like_taxon",
    ],
    "table_to_data": [
        "map_and_group", "table_id", "_identifier_column",
        "maybe_transpose", "strip_identifier_parentheticals",
        "resolve_paper_species", "agent_resolve_paper_species",
        "PAPER_SPECIES_KEY",
        "agent_find_header", "_header_plan_for",
    ],
    "column_relevance": [
        "agent_define_columns_relevance", "make_llm", "invoke_sized",
        "loads_salvaging", "column_relevance_msg_builder_all",
    ],
    "text_manager": ["get_text", "get_tables", "xlsx_to_table", "csv_to_table"],
    "mineru_extract": [
        "classify_folder", "combine_paper_to_markdown", "docx_to_markdown",
        "_docx_table_to_html",
    ],
    "evaluate": [
        "evaluate", "evaluate_all", "DEFAULT_KEY", "KEY_SETS",
        "ACTIVE_KEY_SETS", "species_match", "species_tokens",
        "remap_pred_species", "score_key_set",
        "assess_miss_severity", "ASSESS_MISS_SEVERITY",
    ],
    "trait_name_matcher": [
        "build_type_map", "containment_match", "deterministic_match", "llm_match",
    ],
    "to_output": ["write_output_csv", "build_column_lookup"],
    "fill_template": [
        "get_measurement_level_tags", "route_tags", "apply_plan",
        "decode_grouped_values",
    ],
    "run_pipeline": ["run_pipeline"],
}

# Rough expected sizes — a file far shorter than this is probably a partial save.
MIN_LINES = {
    "tables": 1000, "table_to_data": 1300, "evaluate": 900,
    "column_relevance": 300, "mineru_extract": 380, "trait_name_matcher": 200,
    "to_output": 195,
}

# Cross-module wiring that a symbol check alone cannot see: a module can expose
# every name it is asked for and still be an old copy that never calls the newer
# helper. Each entry is (module, attribute-or-import that must be present).
REQUIRED_WIRING = [
    ("to_output", "split_multivalue",
     "to_output.py is the pre-multivalue copy: it splits on every comma and will "
     "shred names like 'Coras montanus (Emerton, 1890a)' into two rows"),
]


def main() -> int:
    problems = []
    here = Path(__file__).resolve().parent

    print(f"checking modules in {here}\n")
    for name, symbols in REQUIRED.items():
        path = here / f"{name}.py"
        if not path.exists():
            problems.append(f"{name}.py — FILE MISSING")
            print(f"  {name:<20} MISSING FILE")
            continue

        n_lines = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
        short = ""
        if name in MIN_LINES and n_lines < MIN_LINES[name]:
            short = f"  <-- only {n_lines} lines, expected >{MIN_LINES[name]}: likely a partial save"
            problems.append(f"{name}.py is short ({n_lines} lines)")

        try:
            mod = importlib.import_module(name)
        except Exception as e:
            problems.append(f"{name}.py — import failed: {type(e).__name__}: {e}")
            print(f"  {name:<20} IMPORT FAILED  {type(e).__name__}: {e}")
            if not isinstance(e, ImportError):
                traceback.print_exc(limit=2)
            continue

        missing = [s for s in symbols if not hasattr(mod, s)]
        if missing:
            problems.append(f"{name}.py — missing: {', '.join(missing)}")
            print(f"  {name:<20} {n_lines:>5} lines   MISSING: {', '.join(missing)}{short}")
        else:
            print(f"  {name:<20} {n_lines:>5} lines   ok{short}")

    for mod_name, attr, why in REQUIRED_WIRING:
        mod = sys.modules.get(mod_name)
        if mod is not None and not hasattr(mod, attr):
            problems.append(f"{mod_name}.py — not wired to {attr}: {why}")
            print(f"  {mod_name:<20} STALE — missing {attr}: {why}")

    print()
    if problems:
        print(f"{len(problems)} problem(s) — these files are out of sync:")
        for p in problems:
            print(f"  - {p}")
        print("\nRe-copy the affected file(s) in full. A missing symbol in one "
              "module usually surfaces as an error in whichever module imports it.")
        return 1
    print("all modules present and consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())