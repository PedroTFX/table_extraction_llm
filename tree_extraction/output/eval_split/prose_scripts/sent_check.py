import json,re,sys,collections,random,openpyxl
W=sys.argv[1]
norm=lambda s:" "+" ".join(re.findall(r"[a-z0-9]+(?:[.,][0-9]+)?",str(s or "").lower()))+" "
def key(name):
    w=re.findall(r"[A-Za-z]+",str(name or ""))
    return f"{w[0][0].lower()}. {w[1].lower()}" if len(w)>=2 and w[1][0].islower() else " ".join(w[:2]).lower()
def gt(p):
    ws=openpyxl.load_workbook(f"data/un_processed_papers/{p}/{p}.xlsx",read_only=True,data_only=True).worksheets[0]
    it=ws.iter_rows(values_only=True);h=[str(x or "").strip() for x in next(it)]
    return [(str(r[h.index("verbatimIdentification")] or ""),str(r[h.index("measurementType")] or ""),r[h.index("measurementValue")]) for r in it if r[h.index("measurementValue")] is not None]
random.seed(5)
for p in ["Xia2022","Xu2024","Ustjuzhanin2024"]:
    d=json.load(open(f"{W}/sent/{p}.json",encoding="utf-8")); U=d["units"]
    for r in U: r["n"]=norm(r["text"])
    by=collections.defaultdict(list)
    for r in U: by[key(r["account"])].append(r)
    dropped=[r for r in U if not r["kept"]]
    risk=[];only=0
    for sp,t,v in gt(p):
        n=norm(v).strip()
        if not n or (len(n)<2 and n.isdigit()): continue
        f=" "+" ".join(n.split()[:8])+" "
        hits=[r for r in by.get(key(sp),[]) if f in r["n"]]
        dh=[r for r in hits if not r["kept"]]
        if dh: risk.append((t,str(v)[:50],dh[0]["text"][:110],len(hits)-len(dh)))
    print(f"\n===== {p}: dropped {len(dropped)}; GT rows whose value is ALSO in a dropped sentence: {len(risk)}")
    for t,v,s,k in random.sample(risk,min(8,len(risk))): print(f"   risk: {t[:26]!r}={v!r} (in {k} kept) | dropped: {s!r}")
    print("  dropped by label:",collections.Counter(r["label"] or "(no label)" for r in dropped).most_common(8))
    for r in random.sample(dropped,min(9,len(dropped))): print("   DROP:",repr(r["text"][:150]))
    kept_rem=[r for r in U if r["kept"] and re.match(r"(remark|note|etymolog)",(r["label"] or "").lower())]
    print(f"  kept with a Remarks / Note / Etymology label: {len(kept_rem)}")
    for r in random.sample(kept_rem,min(5,len(kept_rem))): print(f"   KEPT {r.get('cat')}:",repr(r["text"][:150]))
    print("  trait -> category (top):")
    for t,c in sorted(d["cross"].items(),key=lambda x:-sum(x[1].values()))[:9]: print(f"     {t[:28]:28s} {dict(sorted(c.items(),key=lambda x:-x[1]))}")
    if p=="Xia2022":
        for r in U:
            if "not mentioned in Yang" in r["text"] or "miyakei" in r["account"] and r["label"].lower().startswith("remark"):
                print("  MIYAKEI:",r["kept"],r.get("cat"),r.get("about"),repr(r["text"][:170]))
