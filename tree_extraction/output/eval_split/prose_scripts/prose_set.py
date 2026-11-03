"""Prose papers: where each GT row is printed (table / text / nowhere), how much text a reader
would have to read with simple cuts (references, back matter, running heads), and what shape
the text holding the GT has (species accounts, labelled fields, key couplets, narrative).
Reads only (markdown + GT xlsx); no pipeline code, no model.
    python prose_set.py <papers dir> <split_v15.json> <out.json>
Prints per-paper lines for dev + held_a only; held_b and grit-only as totals."""
import collections, html, json, os, re, sys

import openpyxl

sys.stdout.reconfigure(encoding="utf-8")
papers_dir, split_f, out_f = sys.argv[1:4]
assign = json.load(open(split_f, encoding="utf-8"))["assign"]
group = lambda p: assign.get(p, "grit-only")
SEE = {"dev", "held_a"}

norm = lambda s: " ".join(re.findall(r"[a-z0-9]+(?:[.,][0-9]+)?", html.unescape(str(s or "")).lower()))

REF_H = re.compile(r"^(references?( cited)?|literature( cited)?|bibliography|works cited|cited literature)\b", re.I)
BACK_H = re.compile(r"^(acknowledge?ments?|funding|author('s|s')? contributions?|contributions|competing interests?|"
                    r"conflicts? of interest|declaration|ethic|data availability|availability of data|"
                    r"author orcids?|orcid|additional information|consent|disclosure|open access|"
                    r"publisher'?s note|supplementary information|electronic supplementary)", re.I)
KEY_H = re.compile(r"\bkey\b", re.I)
CITE = re.compile(r"(\(\d{4}[a-z]?\)|\b\d{4}[a-z]?\.)")          # (2001) or 2001.
CITE2 = re.compile(r"(doi|https?://|\b\d+\s*[:(]\s*\d+|\d+\s*[–-]\s*\d+)", re.I)
LABEL = re.compile(r"^\s*(\*\*[^*]{1,60}\*\*|[A-Z][A-Za-z ,()/-]{1,40}[.:])\s")
COUPLET = re.compile(r"(\.{4,}|…{2,}|\s[–—-]\s*\d+[a-z]?\s*$|^\s*\d+[a-z]?[.(’']?\s*\(?\d*\)?\s*[A-Z])")


def gt_rows(p):
    f = f"{papers_dir}/{p}/{p}.xlsx"
    if not os.path.exists(f):
        return []
    ws = openpyxl.load_workbook(f, read_only=True, data_only=True).worksheets[0]
    it = ws.iter_rows(values_only=True)
    head = [str(h or "").replace("\xa0", " ").strip() for h in next(it)]
    ix = {h: i for i, h in enumerate(head)}
    out = []
    for r in it:
        get = lambda k: r[ix[k]] if k in ix and ix[k] < len(r) else None
        sp, ty, v = get("verbatimIdentification"), get("measurementType"), get("measurementValue")
        if sp is None and ty is None and v is None:
            continue
        out.append((str(sp or "").strip(), str(ty or "").strip(), v))
    return out


def val_forms(v):
    if isinstance(v, float):
        forms = {repr(v), f"{v:g}"} | ({str(int(v))} if v.is_integer() else set())
        forms |= {f"{v:.{d}f}" for d in (1, 2, 3)}
        return {norm(x) for x in forms}
    if isinstance(v, int):
        return {str(v)}
    if hasattr(v, "year"):
        return {f"{v.day}.{v.month}", f"{v.month}.{v.day}"}
    s = norm(v)
    if len(s) > 60:                       # a sentence: its first words are enough
        s = " ".join(s.split()[:8])
    return {s} if s else set()


def sp_forms(s):
    w = norm(re.sub(r"\(.*?\)", " ", s)).split()
    if len(w) < 2:
        return {" ".join(w)} if w else set()
    return {f"{w[0]} {w[1]}", f"{w[0][0]} {w[1]}"}


def blocks(raw):
    """[(kind, heading path text, text)] kind: heading / table / para; page markers, images and
    running heads marked so they can be cut."""
    raw = re.sub(r"<table.*?</table>", lambda m: "\n\n@@TABLE@@" + m.group(0).replace("\n", " ") + "\n\n", raw, flags=re.S)
    lines = raw.split("\n")
    count = collections.Counter(l.strip() for l in lines if l.strip())
    out, para, heading = [], [], ""

    def flush():
        if para:
            t = "\n".join(para)
            out.append(("para", heading, t))
            para.clear()

    for l in lines:
        s = l.strip()
        if not s:
            flush(); continue
        if s.startswith("@@TABLE@@"):
            flush(); out.append(("table", heading, s[9:])); continue
        if s.startswith("|"):
            flush(); out.append(("table", heading, s)); continue
        if s.startswith("#"):
            flush(); heading = s.lstrip("#").strip(); out.append(("heading", heading, s)); continue
        if s.startswith("<!--") or s.startswith("![") or re.fullmatch(r"\d{1,4}", s) or \
                (count[s] >= 3 and len(s) < 150):
            flush(); out.append(("noise", heading, s)); continue
        para.append(s)
    flush()
    return out


def zones(bl):
    """zone per block: refs / back / keep (a heading opens a zone; the next heading closes it)."""
    z, cur = [], "keep"
    for kind, h, t in bl:
        if kind == "heading":
            hh = re.sub(r"[*_\d.\s]+", " ", h).strip()
            cur = "refs" if REF_H.match(hh) else "back" if BACK_H.match(hh) else "keep"
        z.append(cur)
    return z


def ref_like(t):
    return len(t) < 700 and bool(CITE.search(t)) and bool(CITE2.search(t)) and \
        bool(re.match(r"^[A-ZÀ-Ž][\w'’-]+,?\s+([A-Z]\.|[A-Z][a-z]+)", t))


stats, tot = {}, collections.defaultdict(collections.Counter)
for p in sorted(os.listdir(papers_dir)):
    md = f"{papers_dir}/{p}/{p}_full.md"
    if not os.path.exists(md):
        continue
    rows = gt_rows(p)
    if not rows:
        continue
    raw = open(md, encoding="utf-8", errors="ignore").read()
    bl = blocks(raw)
    zn = zones(bl)
    size = collections.Counter()
    nb = [None] * len(bl)                    # normalized text per block
    for i, (kind, h, t) in enumerate(bl):
        z = zn[i]
        if kind == "table":
            k = "table"
        elif kind == "noise":
            k = "noise"
        elif z == "refs":
            k = "refs"
        elif z == "back":
            k = "back"
        elif kind == "para" and ref_like(t):
            k = "refs_loose"                 # a reference entry outside a references heading
        else:
            k = "text"
        size[k] += len(t)
        nb[i] = (k, " " + norm(t) + " ", " " + norm(h) + " ")
    gtsp = {sp for sp, _t, _v in rows}
    spf = {sp: sp_forms(sp) for sp in gtsp}
    # species scope per block: species in the block, in its heading, or in the last paragraph that
    # began with a species name under the same heading
    scope, last_h, last_sp = [], None, set()
    for i, (kind, h, t) in enumerate(bl):
        k, bt, ht = nb[i]
        in_h = {sp for sp, fs in spf.items() if any(f" {x} " in ht for x in fs)}
        in_b = {sp for sp, fs in spf.items() if any(f" {x} " in bt for x in fs)}
        if h != last_h:
            last_h, last_sp = h, set()
        start = " " + " ".join(bt.split()[:6]) + " "
        starts = {sp for sp in in_b if any(f" {x} " in start for x in spf[sp])}
        if starts:
            last_sp = starts
        scope.append(in_h | in_b | last_sp)
    # shape of each block holding text
    shape = []
    for i, (kind, h, t) in enumerate(bl):
        if kind != "para":
            shape.append(kind); continue
        sp_head = bool({sp for sp, fs in spf.items() if any(f" {x} " in nb[i][2] for x in fs)})
        if KEY_H.search(h) or sum(bool(COUPLET.search(l)) for l in t.split("\n")) >= 2:
            s = "key couplets"
        elif t.startswith("Fig") or t.startswith("Table") and len(t) < 600:
            s = "caption"
        elif LABEL.match(t):
            s = "labelled field (species account)" if sp_head else "labelled field"
        elif sp_head:
            s = "species account, running text"
        else:
            s = "narrative paragraph"
        shape.append(s)
    where = collections.Counter()
    hits_shape = collections.Counter()
    lost = 0
    fcache = {}
    live = [i for i in range(len(bl)) if bl[i][0] not in ("heading", "noise")]
    for sp, ty, v in rows:
        vf = val_forms(v)
        if not vf:
            where["empty value"] += 1; continue
        key = repr(v)
        if key not in fcache:
            fcache[key] = [i for i in live if any(f" {x} " in nb[i][1] for x in vf if len(x) >= 2 or not x.isdigit())]
        found = fcache[key]
        if not found:
            where["value not printed"] += 1; continue
        in_tab = [i for i in found if nb[i][0] == "table"]
        txt = [i for i in found if nb[i][0] != "table"]
        txt_sp = [i for i in txt if sp in scope[i]]
        tab_sp = [i for i in in_tab if sp in scope[i]]
        if tab_sp or (in_tab and not txt_sp):
            where["table"] += 1
        elif txt_sp:
            kept = [i for i in txt_sp if nb[i][0] == "text"]
            if kept:
                where["text, with its species"] += 1
                hits_shape[shape[kept[0]]] += 1
            else:
                where["text, only in a cut part"] += 1
                lost += 1
        else:
            where["text, species not near"] += 1
    n = len(rows)
    txt_rows = where["text, with its species"] + where["text, only in a cut part"]
    st = {"group": group(p), "gt": n, "where": dict(where), "shape": dict(hits_shape), "size": dict(size),
          "text_share": round(txt_rows / n, 3), "table_share": round(where["table"] / n, 3),
          "species_headings": sum(1 for i, b in enumerate(bl) if b[0] == "heading" and
                                  any(f" {x} " in nb[i][2] for fs in spf.values() for x in fs)),
          "n_species": len(gtsp)}
    stats[p] = st

json.dump(stats, open(out_f, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
PROSE = 0.5
print(f"{papers_dir}: {len(stats)} papers with GT; prose = at least {PROSE:.0%} of GT rows found in the text with their species")
for g in ("dev", "held_a", "held_b", "grit-only"):
    ps = [p for p, s in stats.items() if s["group"] == g]
    if not ps:
        continue
    pr = [p for p in ps if stats[p]["text_share"] >= PROSE]
    some = [p for p in ps if 0.1 <= stats[p]["text_share"] < PROSE]
    print(f"  {g:9s} {len(ps):3d} papers: prose {len(pr):2d}, some prose (10-50%) {len(some):2d}; "
          f"GT rows in prose papers {sum(stats[p]['gt'] for p in pr)}")
print("\nper paper (dev + held_a only), text share >= 10%:")
for p, s in sorted(stats.items(), key=lambda x: -x[1]["text_share"]):
    if s["group"] not in SEE or s["text_share"] < 0.1:
        continue
    z = s["size"]
    allc = sum(z.values())
    cut = z.get("refs", 0) + z.get("refs_loose", 0) + z.get("back", 0) + z.get("noise", 0)
    print(f"  {p:22s} {s['group']:6s} GT {s['gt']:5d} sp {s['n_species']:4d} sp-headings {s['species_headings']:3d}  "
          f"text {s['text_share']:4.0%} table {s['table_share']:4.0%}  chars {allc:8d} "
          f"(tables {z.get('table', 0) / allc:4.0%}, refs {(z.get('refs', 0) + z.get('refs_loose', 0)) / allc:4.0%}, "
          f"back {z.get('back', 0) / allc:4.0%}, noise {z.get('noise', 0) / allc:4.0%}) -> text kept {z.get('text', 0):7d}")
    print(f"  {'':22s} where: {s['where']}")
    print(f"  {'':22s} shape of the text rows: {s['shape']}")
