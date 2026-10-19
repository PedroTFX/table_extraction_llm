"""
meaning_report.py — a self-contained HTML report of the meaning / synonym benchmark
(meaning_bench_v3): totals, every column with its evidence, every decoy, and the
lists to review by eye. One file, no server: the data is embedded as JSON and the
sorting and filtering are plain JavaScript.
"""

from __future__ import annotations

import html
import json

STATUS = [  # status, css class, what it means
    ("direct match", "ok", "the head reader's name (or a group label) matches the GT trait"),
    ("direct match via meaning", "ok", "matches once its abbreviations are written out from the paper"),
    ("synonym only", "syn", "credited only because the judge said 'same trait'"),
    ("rejected synonym", "rej", "the judge said 'different traits'"),
    ("value, not name", "val", "the judge said one of them is a value of a trait"),
    ("unresolved", "unr", "an abbreviation the paper does not define: not judged"),
    ("no name", "unr", "the head reader gave the column no name"),
]

CSS = """
:root{--bg:#fbfbfa;--fg:#1d1d1f;--muted:#6b6b70;--line:#dcdcd7;--card:#fff;--head:#f2f2ef;
--ok:#1e7a3c;--ok-bg:#e3f4e8;--syn:#7a5a00;--syn-bg:#fdf1cc;--rej:#5b5b60;--rej-bg:#ececec;
--val:#a3271b;--val-bg:#fbe2df;--unr:#3b4a8a;--unr-bg:#e3e8fb;--accent:#2f5bd3}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#161617;--fg:#ececee;
--muted:#9a9aa0;--line:#38383c;--card:#1e1e20;--head:#232326;--ok:#7fd69a;--ok-bg:#183524;
--syn:#f0cc6a;--syn-bg:#3d3215;--rej:#b5b5ba;--rej-bg:#2b2b2e;--val:#ff9b8f;--val-bg:#47201c;
--unr:#a9b8ff;--unr-bg:#232a4a;--accent:#8fa9ff}}
:root[data-theme="dark"]{--bg:#161617;--fg:#ececee;--muted:#9a9aa0;--line:#38383c;--card:#1e1e20;
--head:#232326;--ok:#7fd69a;--ok-bg:#183524;--syn:#f0cc6a;--syn-bg:#3d3215;--rej:#b5b5ba;
--rej-bg:#2b2b2e;--val:#ff9b8f;--val-bg:#47201c;--unr:#a9b8ff;--unr-bg:#232a4a;--accent:#8fa9ff}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1280px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:22px;margin:0 0 4px}h2{font-size:18px;margin:36px 0 8px}h3{font-size:15px;margin:18px 0 6px}
.sub{color:var(--muted);margin:0 0 12px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.wrap{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:var(--card)}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
th{background:var(--head);font-weight:600;white-space:nowrap}
th.sort{cursor:pointer;user-select:none}th.sort:after{content:" ↕";color:var(--muted)}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
.chip{display:inline-block;border-radius:999px;padding:1px 9px;font-size:12px;font-weight:600;white-space:nowrap}
.ok{color:var(--ok);background:var(--ok-bg)}.syn{color:var(--syn);background:var(--syn-bg)}
.rej{color:var(--rej);background:var(--rej-bg)}.val{color:var(--val);background:var(--val-bg)}
.unr{color:var(--unr);background:var(--unr-bg)}
.legend{display:flex;flex-wrap:wrap;gap:8px 16px;margin:8px 0}
.legend span{display:inline-flex;gap:6px;align-items:center;color:var(--muted);font-size:13px}
.controls{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0}
input,select{background:var(--card);color:var(--fg);border:1px solid var(--line);border-radius:6px;padding:5px 8px;font:inherit}
tr.row{cursor:pointer}tr.row:hover td{background:var(--head)}
tr.detail td{background:var(--head)}
.ev{display:grid;gap:10px}.ev div{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:8px 10px}
.q{font-style:italic}.mut{color:var(--muted)}.mono{font-family:ui-monospace,Consolas,monospace;font-size:12px}
ul.rev{margin:4px 0 0 18px;padding:0}ul.rev li{margin:3px 0}
.fp{color:var(--val);font-weight:600}
"""

JS = r"""
const D = JSON.parse(document.getElementById('data').textContent);
const STATUS = Object.fromEntries(D.status.map(s => [s[0], s[1]]));
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const chip = (s, cls) => `<span class="chip ${cls || STATUS[s] || 'rej'}">${esc(s)}</span>`;
const ans = a => a ? chip(a, {same:'syn', different:'rej', value:'val'}[a]) : '<span class="mut">–</span>';
const probs = p => Object.entries(p || {}).map(([k, v]) => `${esc(k)} ${(+v).toFixed(2)}`).join(' · ');

function evidence(r) {
  const defs = (r.definitions || []).map(d => `<div><b>${esc(d.token)}</b> → ${d.chosen ? '<b>' + esc(d.chosen) + '</b>' : '<span class="mut">no meaning accepted</span>'}
    <span class="mut">(${probs(d.probs)})</span>${(d.candidates || []).map(c =>
    `<div class="mut">candidate <b>${esc(c.term)}</b> <span class="mono">[${esc(c.shape)}]</span><br>“${esc(c.quote)}”</div>`).join('')}</div>`).join('');
  const judge = Object.entries(r.judge || {}).map(([who, j]) => `<div><b>judge (${who})</b>:
    <span class="q">${esc(j.question)}</span><br>3-way ${ans(j.answer)} <span class="mut">${probs(j.probs)}</span>
    · 2-way (v2) ${esc(j.v2 || '–')}</div>`).join('');
  const dec = (r.decoys || []).map(d => `<div><b>decoy ${esc(d.kind)} (${d.who})</b>: '${esc(d.label)}' ~ '${esc(d.trait)}'
    · expected ${esc(d.expected)} · got ${ans(d.answer)} ${d.false_positive ? '<span class="fp">false positive</span>' : ''}
    <span class="mut">${probs(d.probs)} · v2 ${esc(d.v2 || '–')}</span></div>`).join('');
  return `<div class="ev">
    <div><b>original header</b> '${esc(r.label)}' · <b>written out</b> '${esc(r.expanded || '–')}' · <b>GT trait</b> '${esc(r.trait)}'
      ${r.unresolved && r.unresolved.length ? '<br><b>undefined in the paper:</b> ' + esc(r.unresolved.join(', ')) : ''}
      ${r.head_gate ? '<br><b>judged?</b> ' + esc(r.head_gate) : ''}${r.gemma_gate ? '<br><b>gemma judged?</b> ' + esc(r.gemma_gate) : ''}
      <br><b>gemma's name</b> '${esc(r.gemma_name || '–')}'${r.gemma_said ? ' (' + esc(r.gemma_said) + ')' : ''}
      → ${r.gemma_meaning ? chip('direct match', 'ok') : (r.judge.gemma ? ans(r.judge.gemma.answer) : '<span class="mut">not judged</span>')}</div>
    ${defs || '<div class="mut">no definitions found in the paper for this header</div>'}${judge}${dec}</div>`;
}

function makeSortable(tbl, rowsOf, render) {
  let key = null, dir = 1;
  tbl.querySelectorAll('th.sort').forEach(th => th.addEventListener('click', () => {
    const k = th.dataset.k; dir = key === k ? -dir : 1; key = k;
    rowsOf().sort((a, b) => (a[k] > b[k] ? 1 : a[k] < b[k] ? -1 : 0) * dir); render();
  }));
}

// --- columns
let cols = D.rows.map((r, i) => ({...r, i, set: r.dev ? 'development' : 'held-out',
  judge3: (r.judge.head || {}).answer || '', credit: r.head_syn ? 'yes' : 'no'}));
const ctb = document.querySelector('#cols tbody');
function renderCols() {
  const q = document.getElementById('q').value.toLowerCase(), st = document.getElementById('st').value,
        set = document.getElementById('set').value;
  const vis = cols.filter(r => (!st || r.status === st) && (!set || r.set === set) &&
    (!q || [r.paper, r.label, r.expanded, r.trait, r.gemma_name].join(' ').toLowerCase().includes(q)));
  document.getElementById('count').textContent = `${vis.length} of ${cols.length} columns`;
  ctb.innerHTML = vis.map(r => `<tr class="row" data-i="${r.i}"><td>${esc(r.paper)}</td><td class="num">${r.table}</td>
    <td class="num">${r.col}</td><td>${esc(r.label || '–')}</td><td>${esc(r.expanded && r.expanded !== r.name ? r.expanded : '')}</td>
    <td>${esc(r.trait)}</td><td>${ans(r.judge3)}</td><td>${r.credit}</td><td>${chip(r.status)}</td><td>${esc(r.set)}</td></tr>
    <tr class="detail" data-d="${r.i}" hidden><td colspan="10">${evidence(r)}</td></tr>`).join('');
}
ctb.addEventListener('click', e => {
  const tr = e.target.closest('tr.row'); if (!tr) return;
  const d = ctb.querySelector(`tr[data-d="${tr.dataset.i}"]`); d.hidden = !d.hidden;
});
['q', 'st', 'set'].forEach(id => document.getElementById(id).addEventListener('input', renderCols));
makeSortable(document.getElementById('cols'), () => cols, renderCols);
renderCols();

// --- decoys
let decs = D.rows.flatMap(r => (r.decoys || []).map(d => ({...d, paper: r.paper, table: r.table,
  set: r.dev ? 'development' : 'held-out', fp: d.false_positive ? 'yes' : 'no'})));
const dtb = document.querySelector('#decoys tbody');
function renderDecoys() {
  const k = document.getElementById('dk').value, fp = document.getElementById('dfp').value;
  const vis = decs.filter(d => (!k || d.kind === k) && (!fp || d.fp === fp));
  dtb.innerHTML = vis.map(d => `<tr><td>${esc(d.set)}</td><td>${esc(d.paper)} t${d.table}</td><td>${esc(d.who)}</td>
    <td>${esc(d.kind)}</td><td>${esc(d.label)}</td><td>${esc(d.trait)}</td><td>${esc(d.expected)}</td>
    <td>${ans(d.answer)}</td><td>${esc(d.v2 || '–')}</td><td>${d.false_positive ? '<span class="fp">yes</span>' : 'no'}</td></tr>`).join('');
}
['dk', 'dfp'].forEach(id => document.getElementById(id).addEventListener('input', renderDecoys));
makeSortable(document.getElementById('decoys'), () => decs, renderDecoys);
renderDecoys();
"""


def _pct(a, b):
    return f"{a}/{b} ({a / b:.0%})" if b else "–"


def _overview(name, t):
    n = t["n"]
    rows = [("gemma names", t["gemma"]), ("head reader names", t["head"]),
            ("gemma + meaning v2", t["gemma_meaning"]),
            ("<b>head + meaning v2 — the score</b>", t["head_meaning"]),
            ("gemma, 2-way judge (v2) · provisional", t["gemma_syn2"]),
            ("gemma, 3-way judge (v3) · provisional", t["gemma_syn3"]),
            ("head, 2-way judge (v2) · provisional", t["head_syn2"]),
            ("head, 3-way judge (v3) · provisional", t["head_syn3"])]
    body = "".join(f"<tr><td>{label}</td><td class='num'>{_pct(v, n)}</td></tr>" for label, v in rows)
    dec = "".join(
        f"<tr><td>{who}</td><td>{kind}</td><td class='num'>{_pct(t[f'{who}_{kind}'][0], t[f'{who}_{kind}'][2])}</td>"
        f"<td class='num'>{_pct(t[f'{who}_{kind}'][1], t[f'{who}_{kind}'][2])}</td></tr>"
        for who in ("head", "gemma") for kind in ("unrelated", "value", "initials"))
    return (f"<div class='card'><h3>{name} · {n} GT-trait columns</h3><table><tr><th>names matching the GT trait"
            f"</th><th class='num'>score</th></tr>{body}</table><h3>decoys judged 'same trait' (false positives)</h3>"
            f"<table><tr><th>names</th><th>decoy</th><th class='num'>3-way</th><th class='num'>2-way (v2)</th></tr>"
            f"{dec}</table></div>")


def _review(rows):
    e = html.escape
    judge_only = [f"<li>{e(w)} · {e(r['paper'])} t{r['table']}: '{e(j['label'])}' ~ '{e(r['trait'])}' "
                  f"<span class='mut'>({e(j.get('said') or 'no definition used')})</span></li>"
                  for r in rows for w, j in r["judge"].items() if j["answer"] == "same"]
    values = [f"<li>{e(d['who'])} · {e(r['paper'])} t{r['table']}: '{e(d['label'])}' ~ '{e(d['trait'])}'</li>"
              for r in rows for d in r["decoys"] if d["kind"] == "value" and d["answer"] == "same"]
    fps = [f"<li>{e(d['who'])} · {e(d['kind'])} · {e(r['paper'])} t{r['table']}: '{e(d['label'])}' ~ '{e(d['trait'])}'</li>"
           for r in rows for d in r["decoys"] if d["kind"] != "value" and d["answer"] == "same"]
    changed = [f"<li>{e(d['who'])} · {e(d['kind'])} · {e(r['paper'])} t{r['table']}: '{e(d['label'])}' ~ "
               f"'{e(d['trait'])}': 2-way {e(d['v2'])} → 3-way {e(d['answer'])}</li>"
               for r in rows for d in [*[{"kind": "main", "who": w, **j} for w, j in r["judge"].items()],
                                       *r["decoys"]]
               if d.get("v2") and (d["v2"] == "yes") != (d["answer"] == "same")]
    unres = [f"<li>{e(r['paper'])} t{r['table']}: '{e(r['label'] or '(no name)')}' vs '{e(r['trait'])}' — "
             f"{e(r['status'])}{(': ' + e(', '.join(r['unresolved']))) if r['unresolved'] else ''}</li>"
             for r in rows if r["status"] in ("unresolved", "no name", "rejected synonym", "value, not name")]
    block = lambda title, items: (f"<div class='card'><h3>{title} ({len(items)})</h3>"
                                  + (f"<ul class='rev'>{''.join(items)}</ul>" if items else
                                     "<p class='mut'>none</p>") + "</div>")
    return ("<div class='grid'>" + block("Credited only by the judge", judge_only)
            + block("Body values judged 'same trait'", values)
            + block("Other decoys judged 'same trait'", fps)
            + block("Judge answers that changed from v2 to v3", changed)
            + block("Not credited: unresolved, unnamed, rejected or value", unres) + "</div>")


def write(rows, totals, path):
    legend = "".join(f"<span><span class='chip {c}'>{html.escape(s)}</span>{html.escape(d)}</span>"
                     for s, c, d in STATUS)
    data = json.dumps({"rows": rows, "status": STATUS}, ensure_ascii=False).replace("</", "<\\/")
    opts = "".join(f"<option>{html.escape(s)}</option>" for s, _c, _d in STATUS)
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Meaning benchmark</title>
<style>{CSS}</style></head><body><main>
<h1>Meaning and synonym benchmark</h1>
<p class="sub">Head reader (frozen) + meaning v2 (frozen: one question per abbreviation, from the
paper's own definitions) + the synonym judge with three outcomes (same trait / different traits /
value, not name). The direct match is the score; synonym-adjusted figures stay provisional until the
judge passes the decoy tests. Click a column row for its evidence.</p>
<h2>Overview</h2><div class="grid">{''.join(_overview(k, v) for k, v in totals.items())}</div>
<h2>Columns</h2><div class="legend">{legend}</div>
<div class="controls"><input id="q" placeholder="filter: paper, name, trait…" size="32">
<select id="st"><option value="">every status</option>{opts}</select>
<select id="set"><option value="">held-out + development</option><option>held-out</option><option>development</option></select>
<span id="count" class="mut"></span></div>
<div class="wrap"><table id="cols"><thead><tr><th class="sort" data-k="paper">paper</th><th class="sort num" data-k="table">table</th>
<th class="sort num" data-k="col">col</th><th class="sort" data-k="label">original name</th><th class="sort" data-k="expanded">written out</th>
<th class="sort" data-k="trait">GT trait</th><th class="sort" data-k="judge3">judge (3-way)</th><th class="sort" data-k="credit">synonym credit</th>
<th class="sort" data-k="status">status</th><th class="sort" data-k="set">set</th></tr></thead><tbody></tbody></table></div>
<h2>Decoys</h2><p class="sub">Questions whose right answer is known: an unrelated trait of the same table
(expected: different), one of the column's own body values (expected: value), a trait with the same
initials (expected: different). A 'same trait' answer is a false positive.</p>
<div class="controls"><select id="dk"><option value="">every kind</option><option>unrelated</option><option>value</option><option>initials</option></select>
<select id="dfp"><option value="">all answers</option><option value="yes">false positives</option><option value="no">correct</option></select></div>
<div class="wrap"><table id="decoys"><thead><tr><th class="sort" data-k="set">set</th><th class="sort" data-k="paper">table</th>
<th class="sort" data-k="who">names</th><th class="sort" data-k="kind">decoy</th><th class="sort" data-k="label">candidate text</th>
<th class="sort" data-k="trait">GT trait</th><th class="sort" data-k="expected">expected</th><th class="sort" data-k="answer">3-way</th>
<th class="sort" data-k="v2">2-way (v2)</th><th class="sort" data-k="fp">false positive</th></tr></thead><tbody></tbody></table></div>
<h2>Review lists</h2>{_review(rows)}
<script type="application/json" id="data">{data}</script><script>{JS}</script>
</main></body></html>"""
    path.write_text(page, encoding="utf-8")
