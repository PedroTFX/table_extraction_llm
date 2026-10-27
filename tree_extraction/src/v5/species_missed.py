"""Tables with trait columns but no species, checked against the GT: are GT species printed
in them, and where (a column the tagger did not call verbatimIdentification, the headers
of a turned table, the text above it)? Reads saved files only, no model.

    python species_missed.py [paper ...]      default: every GT paper with such tables
"""
import collections
import contextlib
import io
import re
import sys

import _paths
import decoder_v3 as v3
import full_run as fr
import species_tree as sp

sys.path.insert(0, str(_paths.REPO / "source"))


def _key(s):
    """'Andrena flavipes Panzer, 1799' -> ('andrena', 'flavipes'); 'A. flavipes' -> ('a', 'flavipes')."""
    w = re.findall(r"[A-Za-z][a-z-]*\.?", str(s or ""))
    if not w:
        return None
    if len(w) == 1 or w[1].rstrip(".").lower() in ("sp", "spp"):
        return (w[0].rstrip(".").lower(),)        # identified to genus: 'Zelusia', 'Gyrinus sp.'
    return (w[0].rstrip(".").lower(), w[1].rstrip(".").lower())


def gt_keys(paper):
    import evaluate as ev
    from mineru_extract import classify_folder
    with contextlib.redirect_stdout(io.StringIO()):
        _, gt, _ = classify_folder(_paths.PAPERS / paper)
        rows = ev.load_xlsx(gt)
    full, short = set(), set()
    for r in rows:
        k = _key(r.get("verbatimIdentification"))
        if k:
            full.add(k)
            if len(k) == 2:
                short.add((k[0][:1], k[1]))
    return full, short


def hit(text, full, short):
    """Same genus and epithet; an abbreviated genus ('D. sibiricus') on either side is
    compared by its initial only (full keeps the GT's own abbreviated names as printed)."""
    k = _key(text)
    if not k:
        return False
    if len(k) == 1:
        return k in full
    return k in full or (len(k[0]) == 1 and k in short) or (k[0][:1], k[1]) in full


def main(papers):
    head = fr.head_runs()
    papers = papers or fr.gt_papers()
    where = collections.Counter()
    for p in papers:
        if p not in head:
            continue
        tables = sp.open_tables(p, head)
        if not tables:
            continue
        try:
            full, short = gt_keys(p)
        except Exception:
            continue
        if len(full) < 2:
            continue                                   # single-species papers: species step
        tags = fr.known_tags(p)
        flat, spans = v3.md_tables(p)
        lines = []
        for t in tables:
            fields = {h: (v or ["none"])[0] for h, v in (tags.get(t.table_index, {}).get("fields") or {}).items()}
            found = []
            for col in t.columns:
                n = sum(hit(r.get(col.name), full, short) for r in t.records)
                if n:
                    found.append(f"column '{col.name[:30]}' tagged {fields.get(col.name, 'untagged')}: "
                                 f"{n}/{len(t.records)} cells")
            nh = sum(hit(c.name, full, short) for c in t.columns)
            if nh:
                found.append(f"headers: {nh}/{len(t.columns)} are GT species (table turned)")
            above = sp.caption_above(t, flat, spans)
            if hit(above.split("##")[-1], full, short):
                found.append(f"text above: '{above[-60:]}'")
            kind = ("tagger missed a species column" if any("column" in x for x in found) else
                    "species in headers" if nh else "species above the table" if found else "no GT species")
            where[kind] += 1
            if found:
                lines.append(f"   t{t.table_index} ({len(t.records)} rec): " + "; ".join(found))
        if lines:
            print(f"== {p}  ({len(tables)} tables without species)")
            print("\n".join(lines))
    print("\nTABLES:", dict(where.most_common()))


if __name__ == "__main__":
    main(sys.argv[1:])
