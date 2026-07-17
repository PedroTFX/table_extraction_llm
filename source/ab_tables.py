"""
ab_tables.py — isolated A/B comparison of table-extraction variants.

Purpose: you are about to change something in the extraction stack (upgrade
MinerU, swap a backend, tweak detection) and you want to know WHICH PAPERS
CHANGED, so you only hand-check those instead of re-reading all of them.

It never touches run_pipeline; it only reads papers and writes snapshots.

Workflow
--------
    # 1. record the current behaviour
    python ab_tables.py snapshot baseline

    # 2. change something (pip install -U mineru, edit a backend, ...)

    # 3. record the new behaviour
    python ab_tables.py snapshot mineru34

    # 4. see ONLY what differs
    python ab_tables.py diff baseline mineru34

Snapshots live in ab_snapshots/<label>/<paper>.json and are plain JSON, so they
diff, commit, and archive cleanly.

Useful flags
------------
    --papers DIR        papers root (default: ../data/un_processed_papers)
    --only NAME[,NAME]  restrict to certain paper folders
    --enable a,b,c      restrict backends (e.g. --enable geometry to isolate one)
    --full              in `diff`, print every changed cell, not just a summary

Isolating one backend is the sharpest test: to attribute a change to MinerU
alone, snapshot twice with `--enable mineru`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import traceback
from pathlib import Path

from read_tables import extract_all, source_files
from reconcile import reconcile

SNAP_ROOT = Path("ab_snapshots")
DEFAULT_PAPERS = Path("../data/un_processed_papers")


# ---------------------------------------------------------------------------
# fingerprinting
# ---------------------------------------------------------------------------

def _cell_hash(records, header) -> str:
    """Stable hash of a table's *content*, order-sensitive, so any changed cell
    changes the digest."""
    blob = json.dumps([[str(r.get(h, "")) for h in header] for r in records],
                      ensure_ascii=False, sort_keys=False)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:12]


def table_fingerprint(rt) -> dict:
    """What we compare between variants. Records are kept in full so `diff` can
    show the exact cells that moved; the hash lets us skip unchanged tables fast."""
    return {
        "backends": sorted(rt.backends),
        "primary": rt.primary_backend,
        "confidence": rt.confidence,
        "header": rt.header,
        "n_records": len(rt.records),
        "n_conflicts": rt.n_conflicts,
        "digest": _cell_hash(rt.records, rt.header),
        "records": [[str(r.get(h, "")) for h in rt.header] for r in rt.records],
    }


def snapshot_paper(folder: Path, enable=None) -> dict:
    out = {"paper": folder.name, "sources": {}, "tables": [], "error": None}
    try:
        for src in source_files(folder):
            raws, counts = extract_all(str(src), enable)
            out["sources"][src.name] = {k: str(v) for k, v in counts.items()}
            for rt in reconcile(raws):
                fp = table_fingerprint(rt)
                fp["source"] = src.name
                out["tables"].append(fp)
    except Exception as e:                       # a bad paper must not stop the run
        out["error"] = f"{type(e).__name__}: {e}"
        out["trace"] = traceback.format_exc(limit=3)
    return out


# ---------------------------------------------------------------------------
# commands
# ---------------------------------------------------------------------------

def cmd_snapshot(args):
    root = Path(args.papers)
    if not root.is_dir():
        sys.exit(f"papers dir not found: {root}")
    only = set(args.only.split(",")) if args.only else None
    enable = set(args.enable.split(",")) if args.enable else None

    folders = sorted(p for p in root.iterdir() if p.is_dir())
    if only:
        folders = [f for f in folders if f.name in only]

    out_dir = SNAP_ROOT / args.label
    out_dir.mkdir(parents=True, exist_ok=True)
    meta = {"label": args.label, "enable": sorted(enable) if enable else "all",
            "mineru_version": _pkg_version("mineru"),
            "docling_version": _pkg_version("docling"),
            "pdfplumber_version": _pkg_version("pdfplumber")}
    (out_dir / "_meta.json").write_text(json.dumps(meta, indent=2))

    print(f"snapshot '{args.label}'  backends={meta['enable']}  "
          f"mineru={meta['mineru_version']}\n")
    for f in folders:
        snap = snapshot_paper(f, enable)
        (out_dir / f"{f.name}.json").write_text(
            json.dumps(snap, indent=2, ensure_ascii=False), encoding="utf-8")
        if snap["error"]:
            print(f"  {f.name:<28} ERROR {snap['error']}")
        else:
            nt = len(snap["tables"])
            nr = sum(t["n_records"] for t in snap["tables"])
            print(f"  {f.name:<28} {nt:>3} table(s)  {nr:>5} record(s)")
    print(f"\nwritten to {out_dir}")


def _pkg_version(name):
    try:
        from importlib.metadata import version
        return version(name)
    except Exception:
        return "not installed"


def _load(label):
    d = SNAP_ROOT / label
    if not d.is_dir():
        sys.exit(f"no snapshot '{label}' (looked in {d})")
    snaps = {}
    for f in sorted(d.glob("*.json")):
        if f.name == "_meta.json":
            continue
        snaps[f.stem] = json.loads(f.read_text(encoding="utf-8"))
    meta = json.loads((d / "_meta.json").read_text()) if (d / "_meta.json").exists() else {}
    return snaps, meta


def _match_tables(a_tables, b_tables):
    """Pair tables across variants. Same source + same ordinal within it — the
    only stable identity when the content itself is what changed."""
    def key(t, seen):
        i = seen.get(t["source"], 0)
        seen[t["source"]] = i + 1
        return (t["source"], i)

    sa, sb = {}, {}
    A = {key(t, sa): t for t in a_tables}
    B = {key(t, sb): t for t in b_tables}
    return A, B


def _diff_records(ra, rb, limit):
    """Cell-level differences between two record matrices."""
    out = []
    for i in range(max(len(ra), len(rb))):
        if i >= len(ra):
            out.append(f"      + row {i}: {rb[i][:4]}")
            continue
        if i >= len(rb):
            out.append(f"      - row {i}: {ra[i][:4]}")
            continue
        for j in range(max(len(ra[i]), len(rb[i]))):
            va = ra[i][j] if j < len(ra[i]) else ""
            vb = rb[i][j] if j < len(rb[i]) else ""
            if va != vb:
                out.append(f"      ~ row {i} col {j}: {va!r} -> {vb!r}")
        if len(out) > limit:
            break
    return out[:limit]


def cmd_diff(args):
    A, ameta = _load(args.a)
    B, bmeta = _load(args.b)
    print(f"A = {args.a}  (mineru {ameta.get('mineru_version','?')})")
    print(f"B = {args.b}  (mineru {bmeta.get('mineru_version','?')})\n")

    papers = sorted(set(A) | set(B))
    changed, identical = [], []

    for p in papers:
        a, b = A.get(p), B.get(p)
        if a is None or b is None:
            changed.append((p, [f"  only in {args.b if a is None else args.a}"]))
            continue
        if a.get("error") or b.get("error"):
            changed.append((p, [f"  ERROR A={a.get('error')} B={b.get('error')}"]))
            continue

        notes = []
        if len(a["tables"]) != len(b["tables"]):
            notes.append(f"  table count {len(a['tables'])} -> {len(b['tables'])}")

        TA, TB = _match_tables(a["tables"], b["tables"])
        for k in sorted(set(TA) | set(TB), key=lambda x: (x[0], x[1])):
            ta, tb = TA.get(k), TB.get(k)
            tag = f"  [{k[0]} #{k[1]}]"
            if ta is None or tb is None:
                notes.append(f"{tag} only in {args.b if ta is None else args.a}")
                continue
            if ta["digest"] == tb["digest"] and ta["header"] == tb["header"]:
                continue
            bits = []
            if ta["n_records"] != tb["n_records"]:
                bits.append(f"rows {ta['n_records']}->{tb['n_records']}")
            if ta["header"] != tb["header"]:
                bits.append("header changed")
            if ta["n_conflicts"] != tb["n_conflicts"]:
                bits.append(f"conflicts {ta['n_conflicts']}->{tb['n_conflicts']}")
            if ta["backends"] != tb["backends"]:
                bits.append(f"backends {ta['backends']}->{tb['backends']}")
            if not bits:
                bits.append("cells changed")
            notes.append(f"{tag} " + ", ".join(bits))
            if ta["header"] != tb["header"]:
                notes.append(f"      A hdr: {ta['header']}")
                notes.append(f"      B hdr: {tb['header']}")
            notes += _diff_records(ta["records"], tb["records"],
                                   200 if args.full else 6)

        (changed if notes else identical).append((p, notes))

    for p, notes in changed:
        print(f"\n### {p}")
        for n in notes:
            print(n)

    print("\n" + "=" * 60)
    print(f"CHANGED : {len(changed)} paper(s)  <- hand-check these")
    for p, _ in changed:
        print(f"   {p}")
    print(f"IDENTICAL: {len(identical)} paper(s)")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("snapshot", help="record extraction results under a label")
    s.add_argument("label")
    s.add_argument("--papers", default=str(DEFAULT_PAPERS))
    s.add_argument("--only", default=None)
    s.add_argument("--enable", default=None)
    s.set_defaults(func=cmd_snapshot)

    d = sub.add_parser("diff", help="show only what changed between two snapshots")
    d.add_argument("a")
    d.add_argument("b")
    d.add_argument("--full", action="store_true")
    d.set_defaults(func=cmd_diff)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
