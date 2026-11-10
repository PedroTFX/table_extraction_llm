"""
bench_report.py — short reports for column_tree_bench results.

    summary.txt   one table per test set: accuracy, identifiers, traits, new tags,
                  exact identifier sets, seconds per column
    report.html   the same table, a per-paper grid, and ONLY the columns some model
                  got wrong (click a row for the tree paths); GT-unused columns are
                  collapsed, since their answer key is weak

column_tree_bench writes both after every run. To combine several runs (e.g.
the held-out baselines in new20/ with a later tree run in v5_q4/):

    python bench_report.py --out combined \\
        --set "Held-out (19 papers)=new20,v5_q4,v5_tev1" \\
        --set "Tuning (10 papers)=.,v5_q4,v5_tev1" \\
        --models gemma,tev1,tree_nimble,tree5_tev1,tree5_q4

A set's papers are those of its FIRST directory; the other directories add the
models they ran on the same tables.
"""

from __future__ import annotations

import html
import json
import pickle
import sys
import time
from pathlib import Path

import _paths
import column_role_bench as crb
import column_tree as ct

BASE = _paths.OUTPUT / "column_tree_bench"
NINE = {"verbatimIdentification", "measurementType", "measurementValue", *crb.ROW_FIELDS}
NAMES = {
    "gemma": "gemma (pipeline)",
    "tev1": "tev1 flat",
    "nimble": "nimble flat",
    "nimble_full": "nimble flat + full .md",
    "tree_tev1": "tree v3 · tev1",
    "tree_tev1_noctx": "tree v3 · tev1 no table level",
    "tree_nimble": "tree v3 · nimble Q8",
    "tree_nimble_q4": "tree v3 · nimble Q4",
    "tree_nimble_q4_4k": "tree v3 · nimble Q4 4k",
    "tree5_tev1": "tree v5 · tev1",
    "tree5_q4": "tree v5 · nimble Q4",
}


def name(m):
    return NAMES.get(m, m)


# --- loading -------------------------------------------------------------------------

def merge(dirs) -> dict:
    """Results of dirs[0], with the models of the other dirs added per table."""
    load = lambda d: json.loads((BASE / d / "results.json").read_text(encoding="utf-8"))
    res = load(dirs[0])
    for d in dirs[1:]:
        if not (BASE / d / "results.json").exists():
            continue
        other = load(d)
        for paper, entries in res.items():
            by = {e["table"]: e for e in other.get(paper, [])}
            for e in entries:
                o = by.get(e["table"])
                if not o:
                    continue
                for m, p in o["pred"].items():
                    e["pred"][m] = p
                    e.setdefault("secs", {})[m] = o.get("secs", {}).get(m, 0)
                for m, t in (o.get("tree") or {}).items():
                    e.setdefault("tree", {})[m] = t
    return res


# --- scoring -------------------------------------------------------------------------

def _gold(e, h):
    return e["labels"].get(h, ("none", ""))[0]


def _guess(e, m, h):
    p = e["pred"].get(m, {}).get(h)
    return p[0] if p else None


def stats(res, m, models):
    """Counts over the columns EVERY shown model answered (same denominators)."""
    c = {k: [0, 0] for k in ("used", "id", "trait", "new", "exact")}
    secs = cols = 0
    for es in res.values():
        for e in es:
            if m not in e["pred"]:
                continue
            secs += e.get("secs", {}).get(m, 0)
            cols += len(e["headers"])
            hs = [h for h in e["headers"] if all(_guess(e, x, h) is not None for x in models)]
            for h in hs:
                g, q = _gold(e, h), _guess(e, m, h)
                for k, ok in (("used", g in NINE),
                              ("id", g == "verbatimIdentification"),
                              ("trait", g in ("measurementType", "measurementValue")),
                              ("new", g not in NINE and g not in ("none", "unsure"))):
                    if ok:
                        c[k][0] += q == g
                        c[k][1] += 1
            gold = {h for h in hs if _gold(e, h) == "verbatimIdentification"}
            if gold:
                c["exact"][1] += 1
                c["exact"][0] += gold == {h for h in hs if _guess(e, m, h) == "verbatimIdentification"}
    c["spc"] = secs / cols if cols else 0.0
    return c


COLS = [("used", "Accuracy (GT-used, 9 fields)"), ("id", "Identifier columns"),
        ("trait", "Trait columns"), ("new", "New tags"),
        ("exact", "Tables: identifier exact"), ("spc", "Seconds / column")]


SHORT = ["accuracy", "identifiers", "traits", "new tags", "id exact", "s/column"]


def _pct(x):
    return f"{x[0] / x[1]:.0%}" if x[1] else "–"


def summary_text(sets, models) -> str:
    L = []
    for title, res in sets:
        n_t = sum(len(v) for v in res.values())
        L.append(f"{title}: {len(res)} papers, {n_t} tables")
        w = max(len(name(m)) for m in models) + 2
        L.append(f"  {'model':{w}s}" + "".join(f"{lab:>16s}" for lab in SHORT))
        for m in models:
            s = stats(res, m, models)
            row = f"  {name(m):{w}s}"
            for k, _ in COLS:
                row += (f"{s[k]:>15.2f}s" if k == "spc"
                        else f"{f'{s[k][0]}/{s[k][1]} {_pct(s[k])}':>16s}")
            L.append(row)
        wrong = sum(1 for _, e, h in _columns(res, models)
                    if _gold(e, h) != "none" and any(_guess(e, m, h) != _gold(e, h) for m in models))
        L.append(f"  {wrong} GT-used column(s) with at least one wrong answer -> report.html")
        L.append("")
    return "\n".join(L)


def _columns(res, models):
    for paper, es in res.items():
        for e in es:
            for h in e["headers"]:
                if _gold(e, h) == "unsure":
                    continue
                if all(_guess(e, m, h) is not None for m in models):
                    yield paper, e, h


# --- html ----------------------------------------------------------------------------

CSS = """
:root{--bg:#fbfbfa;--fg:#1d1d1f;--muted:#6b6b70;--line:#e3e3e0;--card:#ffffff;
--ok:#1f7a44;--okbg:#e6f4ea;--bad:#b3261e;--badbg:#fbe9e7;--best:#0b57d0;--head:#f2f2ef}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#161617;--fg:#ececee;
--muted:#9a9aa0;--line:#2e2e31;--card:#1e1e20;--ok:#7fd49a;--okbg:#17301f;--bad:#ff9b8f;
--badbg:#3a1d1a;--best:#8ab4f8;--head:#232326}}
:root[data-theme="dark"]{--bg:#161617;--fg:#ececee;--muted:#9a9aa0;--line:#2e2e31;--card:#1e1e20;
--ok:#7fd49a;--okbg:#17301f;--bad:#ff9b8f;--badbg:#3a1d1a;--best:#8ab4f8;--head:#232326}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1200px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:22px;margin:0 0 4px}h2{font-size:17px;margin:32px 0 8px}
.sub{color:var(--muted);margin:0 0 16px}
.wrap{overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:var(--card)}
table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}
th,td{padding:6px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:var(--head);font-weight:600;white-space:nowrap;position:sticky;top:0}
td.n{text-align:right;white-space:nowrap}
.best{color:var(--best);font-weight:700}
.ok{color:var(--ok)}.bad{background:var(--badbg);color:var(--bad);font-weight:600}
.okc{background:var(--okbg);color:var(--ok)}
.vals{color:var(--muted);font-size:12px;max-width:260px}
tr.err{cursor:pointer}tr.err:hover td{filter:brightness(0.97)}
tr.path td{background:var(--head);font:12px/1.5 ui-monospace,Consolas,monospace;color:var(--muted)}
tr.path{display:none}tr.path.open{display:table-row}
details{margin-top:12px}summary{cursor:pointer;color:var(--muted)}
input{padding:6px 10px;border:1px solid var(--line);border-radius:6px;background:var(--card);
color:var(--fg);width:min(320px,100%);margin:4px 0 8px}
.note{color:var(--muted);font-size:12px;margin:6px 0 0}
"""

JS = """
document.querySelectorAll('tr.err').forEach(r=>r.addEventListener('click',()=>{
  const n=r.nextElementSibling; if(n&&n.classList.contains('path')) n.classList.toggle('open');}));
document.querySelectorAll('input[data-filter]').forEach(inp=>inp.addEventListener('input',()=>{
  const q=inp.value.toLowerCase(); const t=document.getElementById(inp.dataset.filter);
  t.querySelectorAll('tr.err').forEach(r=>{const show=r.textContent.toLowerCase().includes(q);
    r.style.display=show?'':'none'; const n=r.nextElementSibling;
    if(n&&n.classList.contains('path')&&!show) n.classList.remove('open');});}));
"""


def _e(x):
    return html.escape(str(x))


def _tables_of(paper, cache={}):
    if paper not in cache:
        p = crb.OUT / f"tables_{paper}.pkl"
        cache[paper] = ({f"{t.source}#{t.table_index}": t
                         for t in pickle.loads(p.read_bytes())} if p.exists() else {})
    return cache[paper]


def _values(paper, e, h):
    t = _tables_of(paper).get(e["table"])
    return ct.sample_values(t, h, k=4, width=24) if t else ""


def _summary_html(res, models):
    st = {m: stats(res, m, models) for m in models}
    best = {}
    for k, _ in COLS:
        vals = [(st[m][k] if k == "spc" else (st[m][k][0] / st[m][k][1] if st[m][k][1] else -1))
                for m in models]
        best[k] = min(v for v in vals if v > 0) if k == "spc" else max(vals)
    rows = []
    for m in models:
        cells = [f"<td>{_e(name(m))}</td>"]
        for k, _ in COLS:
            s = st[m][k]
            if k == "spc":
                cls = " best" if s == best[k] else ""
                cells.append(f'<td class="n{cls}">{s:.2f}</td>')
            else:
                v = s[0] / s[1] if s[1] else -1
                cls = " best" if s[1] and v == best[k] else ""
                cells.append(f'<td class="n{cls}">{_pct(s)} <span style="color:var(--muted)">'
                             f'{s[0]}/{s[1]}</span></td>')
        rows.append("<tr>" + "".join(cells) + "</tr>")
    head = "<tr><th>Model</th>" + "".join(f"<th>{_e(lab)}</th>" for _, lab in COLS) + "</tr>"
    return f'<div class="wrap"><table>{head}{"".join(rows)}</table></div>'


def _paper_grid(res, models):
    head = "<tr><th>Paper</th>" + "".join(f"<th>{_e(name(m))}</th>" for m in models) + "</tr>"
    rows = []
    for paper, es in res.items():
        cells = [f"<td>{_e(paper)}</td>"]
        for m in models:
            ok = n = 0
            for e in es:
                for h in e["headers"]:
                    g = _gold(e, h)
                    if g in ("none", "unsure") or _guess(e, m, h) is None:
                        continue
                    n += 1
                    ok += _guess(e, m, h) == g
            cls = "okc" if n and ok == n else ("bad" if n else "")
            cells.append(f'<td class="n {cls}">{ok}/{n}</td>' if n else '<td class="n">–</td>')
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return f'<div class="wrap"><table>{head}{"".join(rows)}</table></div>'


def _error_table(res, models, trees, used, tid):
    head = ("<tr><th>Paper</th><th>Column</th><th>Values</th><th>GT</th>"
            + "".join(f"<th>{_e(name(m))}</th>" for m in models) + "</tr>")
    rows = []
    for paper, e, h in _columns(res, models):
        g = _gold(e, h)
        if (g != "none") != used:
            continue
        guesses = {m: _guess(e, m, h) for m in models}
        if all(q == g for q in guesses.values()):
            continue
        cells = [f"<td>{_e(paper)}<br><span class='vals'>{_e(e['table'].split('#')[-1])}</span></td>",
                 f"<td>{_e(h[:48])}</td>", f"<td class='vals'>{_e(_values(paper, e, h))}</td>",
                 f"<td>{_e(g)}</td>"]
        for m in models:
            q = guesses[m]
            tag = ((e.get("tree", {}).get(m) or {}).get("tags") or {}).get(h)
            extra = f"<br><span class='vals'>{_e('; '.join(f'{k}: {v}' for k, v in tag.items()))}</span>" if tag else ""
            cells.append(f'<td class="ok">✓{extra}</td>' if q == g
                         else f'<td class="bad">{_e(q)}{extra}</td>')
        rows.append('<tr class="err">' + "".join(cells) + "</tr>")
        paths = []
        for m in trees:
            p = ((e.get("tree", {}).get(m) or {}).get("paths") or {}).get(h)
            if p:
                paths.append(f"{_e(name(m))}: {_e(p)}")
        rows.append(f'<tr class="path"><td colspan="{4 + len(models)}">'
                    + ("<br>".join(paths) or "no tree path") + "</td></tr>")
    if not rows:
        return "<p class='note'>None.</p>"
    return (f'<input data-filter="{tid}" placeholder="Filter (paper, column, tag…)">'
            f'<div class="wrap"><table id="{tid}">{head}{"".join(rows)}</table></div>'
            f'<p class="note">{len(rows) // 2} column(s). Click a row for the tree paths.</p>')


def write(out_dir, sets, models, trees) -> str:
    """Write summary.txt and report.html into out_dir; returns the summary text."""
    out_dir = Path(out_dir)
    trees = [t for t in trees if t in models]
    text = summary_text(sets, models)
    (out_dir / "summary.txt").write_text(text, encoding="utf-8")
    body = [f"<h1>Column tagging benchmark</h1>",
            f"<p class='sub'>{_e(time.strftime('%Y-%m-%d %H:%M'))} · answer key derived from "
            f"the GT xlsx · tree v3 = frozen copy (column_tree_v3.py), tree v5 = current "
            f"column_tree.py</p>"]
    for i, (title, res) in enumerate(sets):
        n_t = sum(len(v) for v in res.values())
        body += [f"<h2>{_e(title)}</h2>",
                 f"<p class='sub'>{len(res)} papers · {n_t} tables. Best value per "
                 f"column in blue. Timings depend on what else used the GPU.</p>",
                 _summary_html(res, models),
                 "<h2 style='font-size:15px'>Columns the GT uses, where a model is wrong</h2>",
                 _error_table(res, models, trees, True, f"err{i}"),
                 "<details><summary>Per paper (GT-used columns right / total)</summary>",
                 _paper_grid(res, models), "</details>",
                 "<details><summary>Columns the GT does not use, where a model disagrees "
                 "(weak answer key: the volunteers may just have skipped them)</summary>",
                 _error_table(res, models, trees, False, f"unused{i}"), "</details>"]
    page = (f"<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>Column tagging benchmark</title><style>{CSS}</style></head>"
            f"<body><main>{''.join(body)}</main><script>{JS}</script></body></html>")
    (out_dir / "report.html").write_text(page, encoding="utf-8")
    return text


def main(argv):
    out = BASE / (argv[argv.index("--out") + 1] if "--out" in argv else "combined")
    out.mkdir(parents=True, exist_ok=True)
    sets = []
    for i, a in enumerate(argv):
        if a == "--set":
            title, dirs = argv[i + 1].split("=", 1)
            sets.append((title, merge(dirs.split(","))))
    models = (argv[argv.index("--models") + 1].split(",") if "--models" in argv
              else ["gemma", "tev1", "tree_nimble", "tree5_tev1", "tree5_q4"])
    trees = [m for m in models if m.startswith("tree")]
    print(write(out, sets, models, trees))
    print(f"-> {out / 'report.html'}")


if __name__ == "__main__":
    main(sys.argv[1:])
