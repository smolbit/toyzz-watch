import traceback, requests, json
import toyzz_watch as w
out=[]
try:
    r=requests.get(w.API,headers=w.HEADERS,params={"limit":48,"order":"ocd","page":1},timeout=30)
    out.append(f"status={r.status_code} ct={r.headers.get('content-type')} len={len(r.text)}")
    out.append(r.text[:1500])
except Exception:
    out.append(traceback.format_exc())
try:
    p=w.fetch_products(); out.append(f"fetch_products OK n={len(p)}")
except Exception:
    out.append("fetch_products HATA:\n"+traceback.format_exc())
open("diag.txt","w").write("\n".join(out)+"\n")
