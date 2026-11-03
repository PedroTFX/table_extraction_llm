"""Prose set (>= 50% of GT rows found in the text with their species, < 20% in tables) and the
text a reader keeps under simple cuts, each cut on top of the one before:
  full        the whole markdown (tables included)
  -refs       references (heading zone + reference-like entries elsewhere)
  -back       acknowledgements, funding, contributions, conflicts, ethics, data availability, ORCIDs
  -noise      page markers, running heads, page numbers, image placeholders
  -tables     tables (in prose papers they hold vouchers / statistics)
  -frame      abstract, introduction, discussion, conclusion
  -key        identification keys
  accounts    only the blocks under a species heading, plus materials and methods (the abbreviations)
Per cut: characters kept and GT rows still found in kept text with their species. Reads only.
    python prose_tactics.py <papers dir> <split_v15.json> <prose_*.json> <out set json>
Per paper for dev + held_a; held_b and grit-only as totals."""
import collections, json, os, re, sys

here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, "prose_set.py"), encoding="utf-8").read()
papers_dir, split_f, stats_f, set_f = sys.argv[1:]
sys.argv = [sys.argv[0], papers_dir, split_f, os.devnull]
exec(src.split("stats, tot =")[0])

stats = json.load(open(stats_f, encoding="utf-8"))
prose = sorted(p for p, s in stats.items() if s["text_share"] >= 0.5 and s["table_share"] < 0.2)
FRAME = re.compile(r"^(abstract|summary|introduction|background|discussion|conclusions?|general discussion|"
                   r"keywords?|key words|highlights|graphical abstract|resumen|résumé|zusammenfassung)\b", re.I)
METH = re.compile(r"(material|method|abbreviation|terminology|measurement)", re.I)
CUTS = ["full", "-refs", "-back", "-noise", "-tables", "-frame", "-key", "accounts"]

tot = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
json.dump({g: [p for p in prose if stats[p]["group"] == g] for g in ("dev", "held_a", "held_b", "grit-only")},
          open(set_f, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
for p in prose:
    g = stats[p]["group"]
    rows = gt_rows(p)
    raw = open(f"{papers_dir}/{p}/{p}_full.md", encoding="utf-8", errors="ignore").read()
    bl = blocks(raw)
    zn = zones(bl)
    gtsp = {sp for sp, _t, _v in rows}
    spf = {sp: sp_forms(sp) for sp in gtsp}
    nb = [" " + norm(t) + " " for _k, _h, t in bl]
    nh = [" " + norm(h) + " " for _k, h, _t in bl]
    # top section per block (the last heading that is not a species name or a label), species heading flag
    scope, last_h, last_sp, sec, sp_under = [], None, set(), [], []
    top, under_sp = "", False
    for i, (kind, h, t) in enumerate(bl):
        sp_head = {sp for sp, fs in spf.items() if any(f" {x} " in nh[i] for x in fs)}
        if kind == "heading":
            under_sp = bool(sp_head)
            if not sp_head:
                top = re.sub(r"[*_\d.\s]+", " ", h).strip()
        in_b = {sp for sp, fs in spf.items() if any(f" {x} " in nb[i] for x in fs)}
        if h != last_h:
            last_h, last_sp = h, set()
        start = " " + " ".join(nb[i].split()[:6]) + " "
        st = {sp for sp in in_b if any(f" {x} " in start for x in spf[sp])}
        if st:
            last_sp = st
        scope.append(sp_head | in_b | last_sp)
        sec.append(top); sp_under.append(under_sp)

    def keep(i, cut):
        kind, h, t = bl[i]
        if kind == "heading":
            return False
        c = CUTS.index(cut)
        if c >= 1 and (zn[i] == "refs" or (kind == "para" and ref_like(t))):
            return False
        if c >= 2 and zn[i] == "back":
            return False
        if c >= 3 and kind == "noise":
            return False
        if c >= 4 and kind == "table":
            return False
        if c >= 5 and FRAME.match(sec[i]) and not sp_under[i]:
            return False
        if c >= 6 and KEY_H.search(sec[i]) and not sp_under[i]:
            return False
        if c >= 7 and not sp_under[i] and not METH.search(sec[i]):
            return False
        return True

    fc = {}
    hits = {}
    for sp, ty, v in rows:
        vf = val_forms(v)
        k = repr(v)
        if k not in fc:
            fc[k] = [i for i in range(len(bl)) if bl[i][0] not in ("heading", "noise") and
                     any(f" {x} " in nb[i] for x in vf if len(x) >= 2 or not x.isdigit())]
        hits.setdefault((sp, k), [i for i in fc[k] if sp in scope[i]])
    line = []
    for cut in CUTS:
        ks = [keep(i, cut) for i in range(len(bl))]
        ch = sum(len(bl[i][2]) for i in range(len(bl)) if ks[i])
        found = sum(1 for sp, ty, v in rows if any(ks[i] for i in hits[(sp, repr(v))]))
        tot[g][cut]["chars"] += ch; tot[g][cut]["found"] += found
        line.append((cut, ch, found))
    tot[g]["full"]["gt"] += len(rows); tot[g]["full"]["papers"] += 1
    if g in SEE:
        print(f"\n{p} ({g}), {len(rows)} GT rows")
        for cut, ch, found in line:
            print(f"  {cut:9s} chars {ch:8d} ({ch / line[0][1]:4.0%}) ~tokens {ch // 4:6d}  GT rows found {found:4d}")

print("\ntotals per group (prose papers only)")
for g in ("dev", "held_a", "held_b", "grit-only"):
    if g not in tot:
        continue
    t = tot[g]
    print(f"  {g}: {t['full']['papers']} papers, {t['full']['gt']} GT rows")
    for cut in CUTS:
        print(f"    {cut:9s} chars {t[cut]['chars']:8d} ({t[cut]['chars'] / t['full']['chars']:4.0%})  "
              f"GT rows found {t[cut]['found']:5d} ({t[cut]['found'] / max(1, t['full']['found']):4.0%} of those found in full)")
