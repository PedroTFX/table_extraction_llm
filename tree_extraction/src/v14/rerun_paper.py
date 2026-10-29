"""rerun_paper.py — redo some papers of the grit run from scratch, every stage head -> v14, when
their sources changed (a supplement added: new tables shift the table numbers every saved
answer is keyed by). The other papers are not touched.

  1. markdown   (--md) rebuild <paper>_full.md from the per-file markdown already there
                (mineru_extract.combine_paper_to_markdown; MinerU runs only for a source
                with no .md yet)
  2. purge      every saved answer of the paper in the run: per-paper files of every stage
                and version, its head-reader entries, its legend inventory, its v14 CSV folder
                (the earlier versions' CSVs and reports stay: the 'before' score compares with)
  3. stages     the head reader (body check on every table, as grit_run), then every stage
                of full_run_v14 on these papers only; before each version's stages its answers
                are copied forward from the version before, as that version's setup does for
                the whole run
  4. assemble + score (v14; compared with v13's saved CSV of the paper)

    python rerun_paper.py [--md] <paper ...>        (TREE_PAPERS / TREE_OUTPUT as grit_run)
"""
import json
import shutil
import sys

import grit_run                                   # noqa: F401  (grit roots, inputs without a GT)
import _paths
import full_run_v14 as r14
import header_tree_bench as hb
import legend_inventory as li

# what each version's setup copies from the version before it
FORWARD = [("V3", "FULL", ("tags", "meaning")),
           ("V4", "V3", ("tags", "meaning", "decode", "species")),
           ("V6", "V4", ("tags", "meaning", "decode", "species", "organism")),
           ("V7", "V6", ("tags", "meaning", "decode", "species", "organism", "structure")),
           ("V8", "V7", ("tags", "meaning", "decode", "species", "organism", "structure", "kind")),
           ("V9", "V8", ("tags", "meaning", "decode", "species", "organism", "structure", "kind", "sections")),
           ("V11", "V9", ("tags", "meaning", "decode", "species", "organism", "structure", "kind", "sections",
                          "legend_names")),
           ("V12", "V11", ("tags", "meaning", "decode", "species", "organism", "structure", "kind", "sections",
                          "legend_names", "name_parts")),
           ("V13", "V12", ("tags", "meaning", "decode", "species", "organism", "structure", "kind", "sections",
                          "legend_names", "name_parts")),
           ("V14", "V13", ("tags", "meaning", "decode", "species", "organism", "structure", "kind", "sections",
                          "legend_names", "name_parts", "one_species"))]
STAGES_OF = {"FULL": ["base:tag", "base:meaning", "base:inventory", "base:decode"],
             "V3": ["v3:decode", "v3:endings", "v3:species"],
             "V4": ["v4:organism", "v4:species"],
             "V6": ["v6:structure"],
             "V7": ["v7:kind", "v7:decode", "v7:meaning"],
             "V8": ["v8:sections"],
             "V9": ["v9:names"],
             "V11": ["v11:names", "v11:species"],
             "V12": ["v12:decode"],
             "V13": ["v13:subject"],
             "V14": ["v14:tags"]}


def rebuild_md(paper):
    sys.path.insert(0, str(_paths.REPO / "source"))
    from mineru_extract import combine_paper_to_markdown
    combine_paper_to_markdown(_paths.PAPERS / paper)


def purge(paper):
    """Every saved answer of the paper; its CSV / report folders only in v14 (the one remade):
    the earlier versions' results stay as the 'before' that score compares with."""
    n = 0
    for root in sorted(_paths.OUTPUT.glob("full_run*")):
        for f in root.glob(f"*/{paper}.json"):
            f.unlink()
            n += 1
        if root == r14.V14 and (root / paper).is_dir():
            shutil.rmtree(root / paper)
            n += 1
    for f in (li.OUT / f"{paper}.json", _paths.OUTPUT / "decode_key" / "chain" / "tags_extra" / f"{paper}.json"):
        if f.exists():
            f.unlink()
            n += 1
    exp = hb.OUT / "experiments"
    for name in ("reader2_more.json", "reader2_all.json"):
        f = exp / name
        if f.exists():
            d = json.loads(f.read_text(encoding="utf-8"))
            if d.pop(paper, None) is not None:
                f.write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")
                n += 1
    print(f"  [purge] {paper}: {n} saved files / entries removed", flush=True)


def forward(paper, dst, src, dirs):
    for d in dirs:
        a, b = getattr(r14, src) / d / f"{paper}.json", getattr(r14, dst) / d / f"{paper}.json"
        if a.exists():
            b.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(a, b)


def main(argv):
    md = "--md" in argv
    papers = [a for a in argv if not a.startswith("--")]
    for p in papers:
        if md:
            rebuild_md(p)
        purge(p)
    grit_run.stage_head(papers)
    for name in STAGES_OF["FULL"]:
        print(f"\n===== {name}", flush=True)
        r14.STAGES[name](papers)
    for dst, src, dirs in FORWARD:
        for p in papers:
            forward(p, dst, src, dirs)
        for name in STAGES_OF[dst]:
            print(f"\n===== {name}", flush=True)
            r14.STAGES[name](papers)
    print("\n===== assemble (v14)", flush=True)
    r14.stage_assemble(papers)
    print("\n===== score (v14 vs v13's saved CSV)", flush=True)
    r14.stage_score(papers)


if __name__ == "__main__":
    main(sys.argv[1:])
