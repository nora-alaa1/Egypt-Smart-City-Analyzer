"""
Aqarmap Rental Data — Kafka Producer
=====================================
يسحب بيانات الإيجارات التجارية من Aqarmap كل 6 أشهر

البنية الفعلية (مرصودة مباشرة من HTML الموقع):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<ul class="search-result-grid ...">
  <li>
    <a href="/en/listing/...">
      <img alt="Commercial For rent in STREET, NEIGHBORHOOD, 600 sqm">
    </a>
    ... 300,000 EGP/month ...
    <a href="/en/for-rent/commercial/alexandria/sidi-bishr/">Sidi Bishr</a>
    /
    <a href="/en/for-rent/commercial/alexandria/sidi-bishr/gamal-st/">Gamal Abd El Nasir St</a>
    <a href="/en/listing/...">+ 600 m²</a>
  </li>
</ul>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ملاحظة: __NEXT_DATA__ غير موجود (تأكد 0/0 في المتصفح)
الموقع يعمل بـ Server-Side Rendering عادي.

Topic:    rent-commercial-alexandria
Schedule: كل 6 أشهر (26 أسبوع)
"""
import os
import json
import re
import time
import logging
import requests
from bs4 import BeautifulSoup
from kafka import KafkaProducer
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s [PRODUCER] %(message)s")
log = logging.getLogger(__name__)

# ─── Config ────────────────────────────────────────────────────────────────────
KAFKA_BROKER  = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC         = "rent-commercial-alexandria"
BASE_URL      = "https://aqarmap.com.eg/en/for-rent/commercial/alexandria/"
HEADERS       = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
MAX_PAGES     = 62           # 1,472 listings / ~24 per page
DELAY_BETWEEN = 2            # ثانيتين بين requests (polite crawling)
# ───────────────────────────────────────────────────────────────────────────────

RE_PRICE = re.compile(r"([\d,]+)\s*EGP/month", re.IGNORECASE)
RE_AREA  = re.compile(r"\+\s*([\d,]+)\s*m[²2]", re.IGNORECASE)


def build_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
        acks="all",
        retries=5,
        max_block_ms=300000,
        request_timeout_ms=300000,
        retry_backoff_ms=1000,
    )


def parse_card(card) -> dict | None:
    """
    يستخرج (rent, area, location) من كل <li> card.

    3 مصادر للداتا — مرتبة من الأكثر دقة للأقل:
    1. نص الـ card → price
    2. رابط "+ 600 m²" → area  |  fallback: img alt "600 sqm"
    3. location links (href /alexandria/HOOD/) → location
    """
    try:
        card_text = card.get_text(" ", strip=True)

        # ── 1. Price ─────────────────────────────────────────────────────────────
        price_m = RE_PRICE.search(card_text)
        if not price_m:
            return None
        rent = int(price_m.group(1).replace(",", ""))

        # ── 2. Area ──────────────────────────────────────────────────────────────
        # المصدر الأول: نص "+ 600 m²" الصريح في الـ card
        area_m = RE_AREA.search(card_text)
        if area_m:
            area = int(area_m.group(1).replace(",", ""))
        else:
            # fallback: img alt="Commercial For rent in ..., 600 sqm"
            img = card.select_one("img[alt]")
            sqm_m = re.search(r"(\d+)\s*sqm", img["alt"], re.IGNORECASE) if img else None
            area  = int(sqm_m.group(1)) if sqm_m else None

        if not area:
            return None

        # ── 3. Location ───────────────────────────────────────────────────────────
        # روابط الحي والشارع: href="/en/for-rent/commercial/alexandria/HOOD/"
        # نستبعد الرابط العام /alexandria/ نفسه
        loc_links = [
            a for a in card.select('a[href*="/for-rent/commercial/alexandria/"]')
            if a["href"].rstrip("/") != "/en/for-rent/commercial/alexandria"
        ]
        if not loc_links:
            return None

        # أول link = الحي (Neighborhood)، ثاني link = الشارع (لو موجود)
        parts    = ["Alexandria"] + [a.get_text(strip=True) for a in loc_links[:2]]
        location = " / ".join(p for p in parts if p)

        return {
            "location_en": location,
            "area(m²)":    area,
            "rent(EGP)":   rent,
            "scraped_at":  datetime.now(timezone.utc).isoformat(),
            "source":      "aqarmap",
        }

    except Exception as e:
        log.debug(f"Card parse error: {e}")
        return None


def scrape_page(page: int) -> list[dict]:
    url  = f"{BASE_URL}?page={page}" if page > 1 else BASE_URL
    resp = requests.get(url, headers=HEADERS, timeout=20)

    if resp.status_code != 200:
        log.warning(f"Page {page} → HTTP {resp.status_code}")
        return []

    soup  = BeautifulSoup(resp.text, "lxml")

    # الـ listings في <ul class="search-result-grid ..."> → <li>
    grid  = soup.select_one("ul[class*='search-result-grid']")
    cards = grid.select("li") if grid else []

    if not cards:
        log.debug(f"Page {page}: grid not found, trying fallback li selector")
        cards = soup.select("li")

    records = [r for card in cards if (r := parse_card(card))]
    log.info(f"Page {page:>3} → {len(records):>3} records  ({len(cards)} cards found)")
    return records


def run_scrape_and_publish():
    log.info("=" * 55)
    log.info(f"Aqarmap scrape cycle started — {datetime.now():%Y-%m-%d %H:%M}")
    producer = build_producer()
    total    = 0

    for page in range(1, MAX_PAGES + 1):
        records = scrape_page(page)
        if not records:
            log.info(f"Empty page {page} — stopping.")
            break
        for rec in records:
            producer.send(TOPIC, value=rec)
            total += 1
        time.sleep(DELAY_BETWEEN)

    producer.flush()
    producer.close()
    log.info(f"Cycle complete — {total} records → topic '{TOPIC}'")
    log.info("=" * 55)


# ─── Scheduler: كل 6 أشهر ──────────────────────────────────────────────────────
if __name__ == "__main__":
    log.info("Running once (Airflow mode)")
    run_scrape_and_publish()
    log.info("Done.")
