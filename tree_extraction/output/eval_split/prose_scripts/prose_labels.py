"""For the tuning prose papers: which parts of the text hold the GT rows. Per paper, every
paragraph is put under its label ('**Diagnosis.**' -> Diagnosis) or, unlabelled, under its
section heading (species headings -> '(species heading)'); per part: paragraphs, characters,
GT rows found there with their species. Reads only.
    python prose_labels.py <papers dir> <split_v15.json> <paper> [<paper> ...]"""
import collections, os, re, sys

here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, "prose_set.py"), encoding="utf-8").read()
papers_dir, split_f, *papers = sys.argv[1:]
sys.argv = [sys.argv[0], papers_dir, split_f, os.devnull]
exec(src.split("stats, tot =")[0])          # the helpers only

for p in papers:
    if group(p) not in SEE:
        print(f"{p}: not a tuning paper, skipped"); continue
    rows = gt_rows(p)
    raw = open(f"{papers_dir}/{p}/{p}_full.md", encoding="utf-8", errors="ignore").read()
    bl = blocks(raw)
    zn = zones(bl)
    gtsp = {sp for sp, _t, _v in rows}
    spf = {sp: sp_forms(sp) for sp in gtsp}
    nb = [" " + norm(t) + " " for _k, _h, t in bl]
    nh = [" " + norm(h) + " " for _k, h, _t in bl]
    part, scope, last_h, last_sp = [], [], None, set()
    for i, (kind, h, t) in enumerate(bl):
        sp_head = {sp for sp, fs in spf.items() if any(f" {x} " in nh[i] for x in fs)}
        in_b = {sp for sp, fs in spf.items() if any(f" {x} " in nb[i] for x in fs)}
        if h != last_h:
            last_h, last_sp = h, set()
        start = " " + " ".join(nb[i].split()[:6]) + " "
        st = {sp for sp in in_b if any(f" {x} " in start for x in spf[sp])}
        if st:
            last_sp = st
        scope.append(sp_head | in_b | last_sp)
        if kind in ("heading", "noise"):
            part.append(None); continue
        if kind == "table":
            part.append("[table]"); continue
        if zn[i] != "keep" or ref_like(t):
            part.append(f"[cut: {zn[i] if zn[i] != 'keep' else 'reference entry'}]"); continue
        m = LABEL.match(t)
        where = "(species heading)" if sp_head else re.sub(r"\s+", " ", h)[:40]
        if m:
            lab = re.split(r"[.:]", m.group(1).strip("* "))[0].strip()[:30]
            part.append(f"{where} / {lab}" if not sp_head else lab)
        else:
            part.append(f"{where} / (running text)" if not sp_head else "(running text under a species heading)")
    size, nblk, hits = collections.Counter(), collections.Counter(), collections.Counter()
    for i, k in enumerate(part):
        if k:
            size[k] += len(bl[i][2]); nblk[k] += 1
    fcache = {}
    live = [i for i, k in enumerate(part) if k and not k.startswith("[cut") and k != "[table]"]
    for sp, ty, v in rows:
        vf = val_forms(v)
        key = repr(v)
        if key not in fcache:
            fcache[key] = [i for i in live if any(f" {x} " in nb[i] for x in vf if len(x) >= 2 or not x.isdigit())]
        f = [i for i in fcache[key] if sp in scope[i]]
        hits[part[f[0]] if f else "(not found in kept text with its species)"] += 1
    tot = sum(size.values())
    print(f"\n=== {p}: {len(rows)} GT rows, {len(gtsp)} species, {tot} characters outside headings")
    keys = sorted(set(size) | set(hits), key=lambda k: (-hits[k], -size[k]))
    for k in keys:
        if hits[k] or size[k] >= 0.01 * tot:
            print(f"  {k[:62]:62s} paras {nblk[k]:4d}  chars {size[k]:7d} ({size[k] / tot:4.0%})  GT rows {hits[k]:4d}")
    small = [k for k in keys if not hits[k] and size[k] < 0.01 * tot]
    print(f"  ({len(small)} more parts, each < 1% of the text and no GT row: {sum(size[k] for k in small)} chars)")
