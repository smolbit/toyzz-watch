import re, requests, json
H={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36","Accept-Language":"tr-TR,tr;q=0.9","Origin":"https://www.toyzzshop.com","Referer":"https://www.toyzzshop.com/"}
B="https://www.toyzzshop.com"
html=requests.get(B+"/karakter/hot-wheels/38",headers=H,timeout=30).text
p=re.findall(r'(/assets/index-[\w\-]+\.js)',html)[0]
js=requests.get(B+p,headers=H,timeout=30).text
out=[]
calls=set()
for m in re.finditer(r'\.(get|post|put)\(\s*([`"\'])([^`"\']{2,160})\2',js):
    calls.add(f"{m.group(1).upper()} {m.group(3)}")
out.append("=== AXIOS CALLS ===")
out+=sorted(calls)
out.append("=== CONTEXTS ===")
for kw in ["core.toyzzshop.com","characterId","CharacterId","getCharacter","characters/","Character/","listing","Listing","productList","ProductList","filterTypes.CHARACTERS"]:
    for i,mm in enumerate(re.finditer(re.escape(kw),js)):
        if i>=3: break
        out.append(f"[{kw}] "+js[max(0,mm.start()-300):mm.end()+300].replace("\n"," "))
open("probe.txt","w").write("\n".join(out)+"\n")
