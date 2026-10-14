"""
Toyzz Shop Hot Wheels izleyici (GitHub Actions)
- Toyzz'un kendi API'sinden Hot Wheels urunlerini ceker (en yeniler sirali)
- Yeni eklenen VEYA tukendikten sonra tekrar stoga giren, isminde anahtar
  kelime gecen ve MAX_PRICE altindaki urunleri Telegram'a yollar.
"""
import json
import re
import os
import sys
from datetime import datetime, timedelta, timezone

import requests

API = "https://core.toyzzshop.com/api/characters/38/products"  # 38 = Hot Wheels
PAGE_SIZE = 48
MAX_PAGES = 25
KEYWORDS = ["premium", "car culture", "boulevard", "pop culture", "team transport",
            "rlc", "red line", "1:64 premium", "fast & furious premium"]
MAX_PRICE = 500.0  # TL
STATE_FILE = "seen.json"
CATALOG_FILE = "catalog.txt"

TG_TOKEN = "".join((os.getenv("TG_TOKEN") or "").split()).removeprefix("bot")
TG_CHAT = "".join((os.getenv("TG_CHAT") or "").split())
TG_FAILED = False

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/128.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "tr-TR,tr;q=0.9",
    "Origin": "https://www.toyzzshop.com",
    "Referer": "https://www.toyzzshop.com/",
}


def fetch_products() -> dict:
    products = {}
    for page in range(1, MAX_PAGES + 1):
        r = requests.get(API, headers=HEADERS, timeout=30,
                         params={"limit": PAGE_SIZE, "order": "ocd", "page": page})
        r.raise_for_status()
        items = r.json().get("payload", {}).get("products", [])
        for p in items:
            sid = str(p["serial_id"])
            products[sid] = {
                "title": p.get("title") or p.get("product_name") or "-",
                "price": float(p["price"]["original"]),
                "old_price": float((p.get("old_price") or p["price"])["original"]),
                "in_stock": int(p.get("quantity") or 0) > 0,
                "qty": int(p.get("quantity") or 0),
                "created": (p.get("created_at") or "")[:16],
                "url": f"https://www.toyzzshop.com/{p['slug']}?serial={sid}",
                "image": p.get("image_url"),
            }
        if len(items) < PAGE_SIZE:
            break
    return products


# Premium olmasa da takip edilen markalar/modeller (regular dahil)
BRAND_RE = re.compile(r"\b(bmw|mercedes|benz|amg|ferrari|gt-?r|skyline)\b", re.I)


def match_reason(p: dict) -> str | None:
    if p["price"] >= MAX_PRICE:
        return None
    t = p["title"].lower()
    if any(k in t for k in KEYWORDS):
        return "PREMIUM"
    if BRAND_RE.search(t):
        return "MARKA"
    return None


def is_match(p: dict) -> bool:
    return match_reason(p) is not None


def notify(text: str, image: str | None = None, silent: bool = False):
    global TG_FAILED
    print(text)
    if not (TG_TOKEN and TG_CHAT):
        TG_FAILED = True
        log_tg(f"SECRET EKSIK: TG_TOKEN={'var' if TG_TOKEN else 'YOK'} TG_CHAT={'var' if TG_CHAT else 'YOK'}")
        return
    base = f"https://api.telegram.org/bot{TG_TOKEN}"
    if image:
        r = requests.post(f"{base}/sendPhoto", data={"chat_id": TG_CHAT, "photo": image, "caption": text, "disable_notification": silent}, timeout=20)
        if r.ok:
            return
    r = requests.post(f"{base}/sendMessage", data={"chat_id": TG_CHAT, "text": text, "disable_notification": silent}, timeout=20)
    if not r.ok:
        TG_FAILED = True
        log_tg(f"TELEGRAM HATASI {r.status_code}: {r.text[:300]} | chat_len={len(TG_CHAT)} token_len={len(TG_TOKEN)}")
    else:
        log_tg("OK - mesaj gitti")


def now_tr() -> datetime:
    return datetime.now(timezone(timedelta(hours=3)))


def log_tg(msg: str):
    print(msg)
    with open("tg_status.txt", "w", encoding="utf-8") as f:
        f.write(f"{now_tr():%Y-%m-%d %H:%M} {msg}\n")


def fmt(p: dict, header: str) -> str:
    price = f"{p['price']:.2f} TL"
    if p["old_price"] > p["price"]:
        price += f" (eski {p['old_price']:.2f})"
    return f"{header}\n{p['title']}\n💰 {price} · stok {p['qty']}\n{p['url']}"


def main():
    try:
        with open(STATE_FILE) as f:
            state = json.load(f)  # serial -> 1 (stokta) / 0 (tukendi)
    except (FileNotFoundError, json.JSONDecodeError):
        state = {}
    first_run = not state

    products = fetch_products()
    print(f"{len(products)} urun tarandi")
    if not products:
        print("Hic urun gelmedi - API degismis olabilir")
        sys.exit(1)

    alerts, new_any, sold_out, back_any = 0, 0, [], 0
    for sid, p in products.items():
        prev = state.get(sid)
        now = 1 if p["in_stock"] else 0
        if not first_run:
            if prev is None:
                new_any += 1
            elif prev == 1 and now == 0:
                if is_match(p):
                    sold_out.append(p["title"])
            elif prev == 0 and now == 1:
                back_any += 1
        if not first_run and is_match(p) and now == 1:
            if prev is None:
                notify(fmt(p, f"🚗 YENİ ÜRÜN ({match_reason(p)})"), p["image"])
                alerts += 1
            elif prev == 0:
                notify(fmt(p, f"🔁 TEKRAR STOKTA ({match_reason(p)})"), p["image"])
                alerts += 1
        state[sid] = now

    with open(STATE_FILE, "w") as f:
        json.dump(dict(sorted(state.items())), f, indent=0)

    lines = [f"{p['created']}  {'✔' if p['in_stock'] else '✘'}  {p['price']:>9.2f}  "
             f"{'*' if is_match(p) else ' '} {p['title']}" for p in products.values()]
    with open(CATALOG_FILE, "w", encoding="utf-8") as f:
        f.write("# tarih  stok  fiyat  *=filtreye uyuyor  isim\n" + "\n".join(lines) + "\n")

    matches = [p for p in products.values() if is_match(p) and p["in_stock"]]
    in_stock_total = sum(1 for p in products.values() if p["in_stock"])
    if not first_run:
        r = [f"📋 Tarama raporu · {now_tr():%H:%M}",
             f"Taranan: {len(products)} ürün ({in_stock_total} stokta)",
             f"Yeni ürün: {new_any} · Tekrar stoğa giren: {back_any}",
             f"Filtrene uyan bildirim: {alerts}"]
        if sold_out:
            r.append("Tükenen (filtrendeki): " + ", ".join(t[-40:] for t in sold_out[:5]))
        r.append(f"\nŞu an stokta, filtrene uyan {len(matches)} ürün:")
        for p in sorted(matches, key=lambda x: x["price"])[:10]:
            r.append(f"• {p['price']:.0f}₺ {p['title'].split(' - ')[-1][:45]}")
        if len(matches) > 10:
            r.append(f"… +{len(matches) - 10} ürün daha")
        notify("\n".join(r), silent=True)

    if first_run:
        m = sum(1 for p in products.values() if is_match(p))
        notify(f"✅ Toyzz izleyici kuruldu. {len(products)} Hot Wheels ürünü tarandı, "
               f"{m} tanesi filtrene uyuyor. Bundan sonra yeni gelen ve tekrar stoğa giren "
               f"500₺ altı premium'ları buraya atacağım.")

    if TG_FAILED:
        sys.exit("Telegram bildirimi gonderilemedi - secret'lari kontrol et")


if __name__ == "__main__":
    main()
