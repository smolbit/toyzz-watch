"""
Toyzz Shop Hot Wheels izleyici - GitHub Actions versiyonu
Her calismada bir kez tarar, yeni + eslesen urun varsa Telegram'a yollar.
Gorulen urunler seen.json'a yazilir (workflow bunu repoya commit'ler).
"""
import json
import os
import re
import sys
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

URLS = [
    "https://www.toyzzshop.com/karakter/hot-wheels/38",          # En Yeniler, sayfa 1
    "https://www.toyzzshop.com/karakter/hot-wheels/38?q=page/2",  # yedek: sayfa 2
]
KEYWORDS = ["premium", "car culture", "boulevard", "pop culture", "team transport", "rlc"]
MAX_PRICE = 500.0  # TL
SEEN_FILE = "seen.json"

TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT = os.getenv("TG_CHAT")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/128.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9",
}
PRICE_RE = re.compile(r"(\d{1,3}(?:\.\d{3})*,\d{2})\s*TL")


def parse_price(s: str) -> float:
    return float(s.replace(".", "").replace(",", "."))


def fetch_products() -> dict:
    products = {}
    debug = []
    for i, url in enumerate(URLS):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
        except Exception as e:
            debug.append(f"{url}\n  ISTEK HATASI: {e!r}")
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        title = soup.title.get_text(strip=True) if soup.title else "-"
        debug.append(
            f"{url}\n  status={r.status_code} len={len(r.text)} title={title!r}\n"
            f"  serial= sayisi={r.text.count('serial=')} TL sayisi={r.text.count(' TL')}"
        )
        if i == 0:
            with open("debug.html", "w", encoding="utf-8") as f:
                f.write(r.text)
        if not r.ok:
            continue
        for a in soup.select('a[href*="serial="]'):
            m = re.search(r"serial=(\d+)", a["href"])
            if not m:
                continue
            text = a.get_text(" ", strip=True)
            prices = [parse_price(p) for p in PRICE_RE.findall(text)]
            if not prices:
                continue
            products[m.group(1)] = {
                "name": text,
                "price": min(prices),
                "url": urljoin("https://www.toyzzshop.com", a["href"]),
            }
    debug.append(f"Toplam urun: {len(products)}")
    with open("debug.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(debug) + "\n")
    print("\n".join(debug))
    return products


def is_match(p: dict) -> bool:
    name = p["name"].lower()
    return p["price"] < MAX_PRICE and any(k in name for k in KEYWORDS)


def notify(msg: str):
    print(msg)
    if not (TG_TOKEN and TG_CHAT):
        print("UYARI: TG_TOKEN / TG_CHAT tanimli degil")
        return
    r = requests.post(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        data={"chat_id": TG_CHAT, "text": msg},
        timeout=15,
    )
    if not r.ok:
        print("Telegram hatasi:", r.status_code, r.text)


def main():
    try:
        with open(SEEN_FILE) as f:
            seen = set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        seen = set()
    first_run = not seen

    products = fetch_products()
    print(f"{len(products)} urun tarandi")
    if not products:
        print("Hic urun bulunamadi - site yapisi degismis ya da erisim engellenmis olabilir")
        sys.exit(1)

    for serial, p in products.items():
        if serial in seen:
            continue
        seen.add(serial)
        if not first_run and is_match(p):
            notify(f"🚗 YENİ: {p['name']}\n💰 {p['price']:.2f} TL\n{p['url']}")

    with open(SEEN_FILE, "w") as f:
        json.dump(sorted(seen), f)

    if first_run:
        notify(f"✅ Toyzz izleyici kuruldu, {len(products)} ürün tarandı. Artık yeni gelenleri bildireceğim.")


if __name__ == "__main__":
    main()
