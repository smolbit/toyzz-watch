import re, requests, json
H={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36","Accept":"application/json","Accept-Language":"tr-TR,tr;q=0.9","Origin":"https://www.toyzzshop.com","Referer":"https://www.toyzzshop.com/"}
B="https://www.toyzzshop.com"; A="https://core.toyzzshop.com/api/"
out=[]
html=requests.get(B+"/karakter/hot-wheels/38",headers=H,timeout=30).text
js=requests.get(B+re.findall(r'(/assets/index-[\w\-]+\.js)',html)[0],headers=H,timeout=30).text
i=js.find('const kt="https://core.toyzzshop.com/api"')
out.append("HEADERS CODE: "+js[max(0,i-1500):i])
for kw in ['"users/init"','_guestToken']:
    for k,mm in enumerate(re.finditer(re.escape(kw),js)):
        if k>=4: break
        out.append(f"[{kw}] "+js[max(0,mm.start()-250):mm.end()+350])
def show(name,r):
    out.append(f"--- {name}: {r.status_code} {r.headers.get('content-type')}\n{r.text[:2500]}")
r=requests.get(A+"users/init",headers=H,timeout=30); show("users/init",r)
tok=None
try:
    d=r.json(); s=json.dumps(d)
    m=re.search(r'"(?:token|accessToken|guestToken|access_token)"\s*:\s*"([^"]+)"',s); tok=m.group(1) if m else None
except Exception: pass
out.append(f"TOKEN={tok[:20] if tok else None}")
show("characters/38/products noauth",requests.get(A+"characters/38/products",headers=H,timeout=30))
if tok:
    for hn,hv in [("Authorization","Bearer "+tok),("Authorization",tok),("guest-token",tok)]:
        h=dict(H); h[hn]=hv
        show(f"characters/38/products {hn}={hv[:12]}",requests.get(A+"characters/38/products",headers=h,timeout=30))
open("probe.txt","w").write("\n\n".join(out)+"\n")
