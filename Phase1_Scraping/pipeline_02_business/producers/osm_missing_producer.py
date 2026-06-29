"""
OSM Missing Categories Producer — Overpass API
================================================
يسحب البيانات المفقودة من OpenStreetMap لمدينة الإسكندرية
كل 6 أشهر ويرسلها لـ Kafka

الـ categories المستهدفة (مطابقة لـ Dim_Business_Type.xlsx):
  ┌─────────────────────────────────────────────────────────┐
  │ Category              │ Subcategory       │ Topic        │
  ├─────────────────────────────────────────────────────────┤
  │ Food & Beverage       │ Restaurant        │ restaurants  │
  │ Food & Beverage       │ Bakery            │ bakeries     │
  │ Food & Beverage       │ Ice Cream & Sweets│ sweets       │
  │ Food & Beverage       │ Juice Bar         │ juice-bars   │
  │ Tourism & Hospitality │ Hotel             │ hotels       │
  │ Healthcare            │ Hospital & Clinic │ hospitals    │
  │ Financial Services    │ Bank & Financial  │ banks        │
  │ Retail                │ Supermarket       │ supermarkets │
  │ Retail                │ Clothing & Fashion│ clothing     │
  └─────────────────────────────────────────────────────────┘

Output format (مطابق للـ producers الموجودة):
  name, latitude, longitude, osm_id,
  category, subcategory, scraped_at, source

Topic naming: <subcategory-slug>-alexandria
Schedule: كل 6 أشهر
"""

import os
import json
import time
import logging
import requests
from kafka import KafkaProducer
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s [OSM-MISSING] %(message)s")
log = logging.getLogger(__name__)

# ─── Config ────────────────────────────────────────────────────────────────────
KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "kafka:9092")
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
TIMEOUT      = 90

# Bounding box: إسكندرية مصر (south, west, north, east)
ALEX_BBOX = "30.9,29.5,31.4,30.2"

HEADERS = {
    "User-Agent": "SmartCityAnalyzer/1.0 (Alexandria, Egypt; academic project)",
    "Accept":     "application/json",
}
# ───────────────────────────────────────────────────────────────────────────────


def q(tags_block: str) -> str:
    """Helper — يبني Overpass query بشكل موحد."""
    return f"""
[out:json][timeout:{TIMEOUT}];
(
{tags_block}
);
out center;
""".strip()


def bbox(tag: str) -> str:
    """يبني سطر واحد من الـ query لـ node + way بنفس الـ tag."""
    return (
        f'  node{tag}({ALEX_BBOX});\n'
        f'  way{tag}({ALEX_BBOX});\n'
        f'  relation{tag}({ALEX_BBOX});'
    )


# ─── Category Definitions ──────────────────────────────────────────────────────
# كل entry: (category, subcategory, kafka_topic, overpass_query)
CATEGORIES = [
    (
        "Food & Beverage",
        "Restaurant",
        "restaurants-alexandria",
        q(
            bbox('["amenity"="restaurant"]') + "\n" +
            bbox('["amenity"="fast_food"]')
        ),
    ),
    (
        "Food & Beverage",
        "Bakery",
        "bakeries-alexandria",
        q(
            bbox('["shop"="bakery"]') + "\n" +
            bbox('["amenity"="bakery"]')
        ),
    ),
    (
        "Food & Beverage",
        "Ice Cream & Sweets",
        "sweets-alexandria",
        q(
            bbox('["amenity"="ice_cream"]') + "\n" +
            bbox('["shop"="confectionery"]') + "\n" +
            bbox('["shop"="pastry"]') + "\n" +
            bbox('["shop"="chocolate"]')
        ),
    ),
    (
        "Food & Beverage",
        "Juice Bar",
        "juice-bars-alexandria",
        q(
            bbox('["amenity"="juice_bar"]') + "\n" +
            bbox('["shop"="juice"]') + "\n" +
            bbox('["amenity"="beverages"]')
        ),
    ),
    (
        "Tourism & Hospitality",
        "Hotel",
        "hotels-alexandria",
        q(
            bbox('["tourism"="hotel"]') + "\n" +
            bbox('["tourism"="guest_house"]') + "\n" +
            bbox('["tourism"="hostel"]') + "\n" +
            bbox('["tourism"="apartment"]')
        ),
    ),
    (
        "Healthcare",
        "Hospital & Clinic",
        "hospitals-alexandria",
        q(
            bbox('["amenity"="hospital"]') + "\n" +
            bbox('["amenity"="clinic"]') + "\n" +
            bbox('["amenity"="doctors"]') + "\n" +
            bbox('["amenity"="dentist"]') + "\n" +
            bbox('["amenity"="pharmacy"]')   # دعم إضافي لو الـ topic الأصلي ناقص
        ),
    ),
    (
        "Financial Services",
        "Bank & Financial",
        "banks-alexandria",
        q(
            bbox('["amenity"="bank"]') + "\n" +
            bbox('["amenity"="atm"]') + "\n" +
            bbox('["amenity"="bureau_de_change"]')
        ),
    ),
    (
        "Retail",
        "Supermarket",
        "supermarkets-alexandria",
        q(
            bbox('["shop"="supermarket"]') + "\n" +
            bbox('["shop"="convenience"]') + "\n" +
            bbox('["shop"="grocery"]') + "\n" +
            bbox('["shop"="department_store"]')
        ),
    ),
    (
        "Retail",
        "Clothing & Fashion",
        "clothing-alexandria",
        q(
            bbox('["shop"="clothes"]') + "\n" +
            bbox('["shop"="shoes"]') + "\n" +
            bbox('["shop"="boutique"]') + "\n" +
            bbox('["shop"="fashion"]') + "\n" +
            bbox('["shop"="accessories"]')
        ),
    ),
]
# ───────────────────────────────────────────────────────────────────────────────


def build_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
        acks="all",
        retries=5,
        max_block_ms=300_000,        # 5 دقائق بدل 60 ثانية الافتراضية
        request_timeout_ms=60_000,
        metadata_max_age_ms=30_000,
    )


def fetch_overpass(query: str, label: str) -> list[dict]:
    """يرسل Overpass query ويرجع list of elements."""
    log.info(f"  Fetching [{label}] from Overpass...")
    try:
        resp = requests.post(
            OVERPASS_URL,
            data={"data": query},
            headers=HEADERS,
            timeout=TIMEOUT + 15,
        )
        resp.raise_for_status()
        elements = resp.json().get("elements", [])
        log.info(f"  → {len(elements)} raw elements")
        return elements
    except requests.exceptions.Timeout:
        log.error(f"  Overpass timeout for [{label}]")
        return []
    except Exception as e:
        log.error(f"  Overpass error for [{label}]: {e}")
        return []


def extract_coords(el: dict) -> tuple:
    """يستخرج (lat, lon) من node أو way/relation."""
    if el["type"] == "node":
        return el.get("lat"), el.get("lon")
    center = el.get("center", {})
    return center.get("lat"), center.get("lon")


def parse_element(el: dict, category: str, subcategory: str) -> dict | None:
    """
    يحول OSM element لـ record مطابق لشكل الـ Dim_Business_Type:
      name, latitude, longitude, osm_id,
      category, subcategory, scraped_at, source
    """
    tags = el.get("tags", {})

    name = (
        tags.get("name")
        or tags.get("name:ar")
        or tags.get("name:en")
        or tags.get("brand")
        or None
    )

    # تجاهل العناصر اللي مش ليها إحداثيات
    lat, lon = extract_coords(el)
    if lat is None or lon is None:
        return None

    # تنظيف الـ name
    if name and str(name).strip() in ("nan", "NaN", ""):
        name = None

    return {
        "name":        name,
        "latitude":    round(float(lat), 6),
        "longitude":   round(float(lon), 6),
        "osm_id":      el.get("id"),
        "osm_type":    el.get("type"),        # node / way / relation
        "category":    category,
        "subcategory": subcategory,
        # حقول إضافية من الـ tags لو موجودة
        "phone":       tags.get("phone") or tags.get("contact:phone"),
        "website":     tags.get("website") or tags.get("contact:website"),
        "opening_hours": tags.get("opening_hours"),
        "brand":       tags.get("brand"),
        "scraped_at":  datetime.now(timezone.utc).isoformat(),
        "source":      "openstreetmap",
    }


def run_cycle():
    log.info("=" * 60)
    log.info(f"OSM Missing Categories cycle — {datetime.now():%Y-%m-%d %H:%M}")
    grand_total = 0

    for (category, subcategory, topic, query) in CATEGORIES:
        label = f"{category} / {subcategory}"
        log.info(f"\n── {label} ──")

        # نجيب الداتا الأول قبل ما نفتح الـ producer
        elements = fetch_overpass(query, label)

        if not elements:
            log.info(f"  0 records → topic '{topic}'")
            time.sleep(3)
            continue

        # نبني producer جديد لكل category عشان نتجنب metadata timeout
        producer = build_producer()
        sent = 0
        seen_ids = set()

        for el in elements:
            rec = parse_element(el, category, subcategory)
            if rec is None:
                continue
            uid = (el["type"], el.get("id"))
            if uid in seen_ids:
                continue
            seen_ids.add(uid)
            producer.send(topic, value=rec)
            sent += 1

        producer.flush()
        producer.close()

        log.info(f"  ✓ {sent} records → topic '{topic}'")
        grand_total += sent

        # Polite delay بين الـ queries
        time.sleep(3)

    log.info(f"\nCycle complete — {grand_total} total records sent")
    log.info("=" * 60)


if __name__ == "__main__":
    log.info("Running once (Airflow mode)")
    run_cycle()
    log.info("Done.")
