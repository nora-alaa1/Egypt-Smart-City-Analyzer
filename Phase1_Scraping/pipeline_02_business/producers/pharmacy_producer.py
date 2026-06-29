"""
Pharmacy Producer — egyfinder.net
===================================
يسحب بيانات الصيدليات من egyfinder.net كل 6 أشهر

البنية الحقيقية لصفحة egyfinder (مرصودة مباشرة):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
كل listing يحتوي على:
  <h3><a href="/company/en/...">Pharmacy Name</a></h3>
  <p>4.3</p>                    ← rating
  <p>alexandria, semouha</p>    ← location
  <p>address text - ...</p>    ← address (يحتوي st. أو rd. أو " - ")
  <p>035301103</p>              ← phone(s)
  <a href="#">Phone</a>...      ← action links

Pagination: ?p=1, ?p=2, ...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Output مطابق لـ pharmacies_NORMALIZED___1_.csv:
  name, address, phone, source_file, web_scraper_start_url

Topic:    pharmacy-alexandria
Schedule: كل 6 أشهر
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [PHARMA] %(message)s")
log = logging.getLogger(__name__)

# ─── Config ────────────────────────────────────────────────────────────────────
# BUG FIX #3: كان "KAFKA_BOOTSTRAP_SERVERS" بس الـ docker-compose بيبعت "KAFKA_BROKER"
KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "kafka:9092")
TOPIC        = "pharmacy-alexandria"
BASE_URL     = "https://egyfinder.net/categories/en/pharmacies/alexandria"
MAX_PAGES    = 10
DELAY        = 2
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://egyfinder.net/",
}

# كلمات دالة على العنوان — مرصودة من الداتا الأصلية
ADDR_KEYWORDS = ["st.", "rd.", "sq.", "ave", " - ", "bldg", "floor",
                 "shop", "mall", "tower", "inside", "beside", "near",
                 "behind", "opposite", "off ", "intersection"]
# ───────────────────────────────────────────────────────────────────────────────


def build_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
        acks="all",
        retries=3,
    )


def find_address(paragraphs: list[str]) -> str:
    """
    من قائمة نصوص الـ paragraphs، يلاقي العنوان.
    العنوان هو أول paragraph يحتوي على كلمة دالة على عنوان.
    """
    for txt in paragraphs:
        txt_lower = txt.lower()
        if any(kw in txt_lower for kw in ADDR_KEYWORDS) and len(txt) > 10:
            return txt
    return ""


def find_phone(paragraphs: list[str]) -> str | None:
    """
    يلاقي أول رقم تليفون صالح من النصوص.
    يشمل formats: 035301103, 01282048564, +20.12.2377.1659
    """
    for txt in paragraphs:
        nums = re.findall(r"[\d\+][\d\s\.\-\(\)]{6,18}[\d]", txt)
        for num in nums:
            digits = re.sub(r"[^\d]", "", num)
            if 7 <= len(digits) <= 12:
                return txt.strip()
    return None


def parse_listing_block(h3, all_siblings: list) -> dict | None:
    """
    يحول h3 + siblings التاليين لـ record.
    البنية: h3(name) → p(rating) → p(location) → p(address) → p(phone) → links
    """
    try:
        # ── Name ─────────────────────────────────────────────────────────────
        name_el = h3.select_one("a") or h3
        name    = name_el.get_text(strip=True)
        if not name:
            return None

        # نجمع النصوص من الـ siblings حتى الـ h3 التالية
        texts = []
        for sib in all_siblings:
            if sib.name == "h3":
                break
            txt = sib.get_text(strip=True) if hasattr(sib, "get_text") else str(sib).strip()
            if txt and len(txt) > 2:
                texts.append(txt)

        # ── Address ───────────────────────────────────────────────────────────
        address = find_address(texts)
        if not address:
            return None

        # ── Phone ─────────────────────────────────────────────────────────────
        phone = find_phone(texts)

        return {"name": name, "address": address, "phone": phone}

    except Exception as e:
        log.debug(f"Block parse error: {e}")
        return None


def parse_cards(cards) -> list[dict]:
    """
    يحول list of _itemBox cards لـ records.
    الهيكل الحقيقي لـ egyfinder (مرصود):
      div._itemBox
        h3 > a > span[itemprop=name]   ← الاسم
        div._address                    ← العنوان
        div._phone                      ← التليفون
    """
    records = []
    for card in cards:
        try:
            # ── Name ──────────────────────────────────────────────────────────
            name_el = card.select_one("h3 span[itemprop='name'], h3 a, h3")
            if not name_el:
                continue
            name = name_el.get_text(strip=True)
            if not name:
                continue

            # ── Address ───────────────────────────────────────────────────────
            addr_el = card.select_one("div._address")
            address = addr_el.get_text(strip=True) if addr_el else ""

            # لو مفيش div._address، جرب أي نص طويل
            if not address:
                all_texts = [
                    el.get_text(strip=True)
                    for el in card.select("p, span, div")
                    if el.get_text(strip=True)
                ]
                address = find_address(all_texts)
                if not address:
                    for txt in all_texts:
                        if len(txt) > 15 and txt not in name:
                            address = txt
                            break

            if not address:
                continue

            # ── Phone ──────────────────────────────────────────────────────────
            phone_el = card.select_one("div._phone")
            phone = phone_el.get_text(strip=True) if phone_el else None
            if not phone:
                all_texts = [
                    el.get_text(strip=True)
                    for el in card.select("p, span, div")
                    if el.get_text(strip=True)
                ]
                phone = find_phone(all_texts)

            records.append({"name": name, "address": address, "phone": phone})

        except Exception as e:
            log.debug(f"Card error: {e}")
            continue

    return records


def scrape_page(page: int) -> list[dict]:
    url = BASE_URL if page == 1 else f"{BASE_URL}?p={page}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        if resp.status_code != 200:
            log.warning(f"Page {page} → HTTP {resp.status_code}")
            return []

        soup = BeautifulSoup(resp.text, "lxml")

        # ── Strategy 1: div._itemBox (الهيكل الحقيقي المرصود من egyfinder) ──
        cards = soup.select("div._itemBox")
        if cards:
            records = parse_cards(cards)
            if records:
                log.info(f"Page {page}: {len(records)} pharmacies [_itemBox strategy]")
                return records

        # ── Strategy 2: h3-based traversal كـ fallback ───────────────────────
        h3_tags = soup.select("h3")
        if not h3_tags:
            log.info(f"Page {page}: no h3 tags — end of pages")
            return []

        records = []
        for h3 in h3_tags:
            siblings = []
            for sib in h3.find_next_siblings():
                if sib.name == "h3":
                    break
                siblings.append(sib)

            r = parse_listing_block(h3, siblings)
            if r:
                records.append(r)

        log.info(f"Page {page}: {len(records)} pharmacies [h3-traversal strategy]")
        return records

    except Exception as e:
        log.error(f"Page {page} error: {e}")
        return []


def run_cycle():
    log.info("=" * 60)
    log.info(f"Pharmacy scrape cycle — {datetime.now():%Y-%m-%d %H:%M}")
    producer = build_producer()
    total    = 0

    for page in range(1, MAX_PAGES + 1):
        records = scrape_page(page)
        if not records:
            log.info(f"Empty page {page} — stopping")
            break
        for r in records:
            producer.send(TOPIC, value={
                **r,
                "web_scraper_start_url": BASE_URL if page == 1 else f"{BASE_URL}?p={page}",
                "source_file":           f"egyfinder page {page}",
                "scraped_at":            datetime.now(timezone.utc).isoformat(),
                "source":                "egyfinder",
            })
            total += 1
        time.sleep(DELAY)

    producer.flush()
    producer.close()
    log.info(f"Pharmacy cycle complete — {total} records → topic '{TOPIC}'")
    log.info("=" * 60)


if __name__ == "__main__":
    log.info("Running once (Airflow mode)")
    run_cycle()
    log.info("Done.")
