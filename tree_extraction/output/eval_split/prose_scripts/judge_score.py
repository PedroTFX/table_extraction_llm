import json,re,difflib,sys,collections,os
N=sys.argv[1]; sys.argv=[sys.argv[0], N, "."]
exec(open(f"{N}/judge_match.py",encoding="utf-8").read().split("res = {}")[0])
r=json.load(open(f"{N}/judge_res_{os.environ.get('OURS','ours3')}.json",encoding="utf-8"))
num=lambda s: bool(re.fullmatch(r"[\d.,\s\-–~<>]+",nv(s))) and any(c.isdigit() for c in s)
for p,d in r.items():
    eq=len(d["exact"]); typo=part=bad=0
    for g,u,s in d["near"]:
        a,b=nv(g["v"]),nv(u["v"])
        if num(g["v"]) and num(u["v"]):
            if difflib.SequenceMatcher(None,a,b).ratio()>=0.85: typo+=1
            else: bad+=1
        elif a==b or difflib.SequenceMatcher(None,a,b).ratio()>=0.9: typo+=1
        else: part+=1
    gt_types={g["t"] for g,_ in d["exact"]}|{g["t"] for g,_,_ in d["near"]}|{g["t"] for g in d["missed"]}
    in_scope=sum(1 for u in d["extra"] if any(same_trait(p,t,u["t"]) for t in gt_types if t))
    ngt=eq+len(d["near"])+len(d["missed"])
    def f(tp,fp,fn):
        P=tp/(tp+fp) if tp+fp else 0; R=tp/(tp+fn) if tp+fn else 0
        return R,P,(2*P*R/(P+R) if P+R else 0)
    R,P,F=f(eq+typo,in_scope+part+bad,ngt-eq-typo); R2,P2,F2=f(eq+typo+part,in_scope+bad,ngt-eq-typo-part)
    miss=collections.Counter(g["t"] for g in d["missed"]).most_common(5)
    print(f"{p:16s} judged R {R:.3f} P {P:.3f} F1 {F:.3f} | lenient R {R2:.3f} P {P2:.3f} F1 {F2:.3f} | GT unmatched {len(d['missed'])}: {miss}")
