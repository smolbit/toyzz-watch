import re, requests, json
H={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36","Accept":"application/json","Accept-Language":"tr-TR,tr;q=0.9","Origin":"https://www.toyzzshop.com","Referer":"https://www.toyzzshop.com/"}
B="https://www.toyzzshop.com"; A="https://core.toyzzshop.com/api/"
out=[]
html=requests.get(B+"/karakter/hot-wheels/38",headers=H,timeout=30).text
js=requests.get(B+re.findall(r'(/assets/index-[\w\-]+\.js)',html)[0],headers=H,timeout=30).text
for kw in ['getCharacterProducts(','serial=','order_by','orderBy','sort_by','"sort"','per_page','perPage','limit:']:
    for k,mm in enumerate(re.finditer(re.escape(kw),js)):
        if k>=2: break
        out.append(f"[{kw}] "+js[max(0,mm.start()-300):mm.end()+300])
def summ(name,params):
    r=requests.get(A+"characters/38/products",headers=H,params=params,timeout=30)
    try:
        d=r.json()["payload"]
        prods=d.get("products",[])
        other={k:v for k,v in d.items() if k!="products"}
        out.append(f"--- {name} {params}: {r.status_code} n={len(prods)} other_keys={list(other)}\n"+json.dumps(other,ensure_ascii=False)[:1500])
        for p in prods[:6]: out.append(f"   {p['created_at'][:10]} q={p['quantity']} {p['price']['original']} {p['title'][:60]} | {p['slug']} sid={p['serial_id']}")
        return prods
    except Exception as e:
        out.append(f"--- {name}: {r.status_code} ERR {e} {r.text[:300]}")
all1=summ("default",{})
summ("page2",{"page":2})
for s in ["new","newest","en-yeniler","created_at","-created_at","price_asc","price"]:
    summ("sort",{"sort":s})
summ("q premium",{"q":"premium"})
summ("search api",{})
r=requests.get(A+"search/products",headers=H,params={"q":"hot wheels premium"},timeout=30)
out.append(f"--- search/products: {r.status_code} {r.text[:1500]}")
open("probe.txt","w").write("\n\n".join(out)+"\n")
