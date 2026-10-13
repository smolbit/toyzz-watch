import re, requests
H={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36","Accept-Language":"tr-TR,tr;q=0.9"}
B="https://www.toyzzshop.com"
out=[]
html=requests.get(B+"/karakter/hot-wheels/38",headers=H,timeout=30).text
queue=re.findall(r'(/assets/[\w\-.]+\.js)',html); seen=set(); n=0
pat=re.compile(r'''["'`]((?:https?://[^"'`\s]{3,200})|(?:/[\w\-./{}$:?=&]*(?:api|product|urun|category|kategori|karakter|search|list|catalog|brand|marka)[\w\-./{}$:?=&]*))["'`]''',re.I)
found={}
while queue and n<60:
    p=queue.pop(0)
    if p in seen: continue
    seen.add(p); n+=1
    try: js=requests.get(B+p,headers=H,timeout=30).text
    except Exception as e: out.append(f"ERR {p} {e}"); continue
    out.append(f"JS {p} len={len(js)}")
    for m in re.findall(r'(?:assets/)?([\w\-.]+\.js)',js):
        if re.match(r'^[\w\-]+-[\w\-]{6,}\.js$',m): queue.append("/assets/"+m)
    for m in pat.findall(js):
        found.setdefault(m,p)
    for kw in ["baseURL","baseUrl","apiUrl","API_URL","karakter"]:
        for mm in re.finditer(kw,js):
            out.append(f"CTX[{kw}] {p}: "+js[max(0,mm.start()-150):mm.end()+250].replace("\n"," "))
            break
out.append("=== URL/PATH STRINGS ===")
for k,v in sorted(found.items()): out.append(f"{k}    <- {v}")
open("probe.txt","w").write("\n".join(out)+"\n")
print("\n".join(out[:50]))
