"""
OSM Producer — Cafes & Gyms (Overpass API)
============================================
يسحب بيانات الكافيهات والجيمات من OpenStreetMap
كل 6 أشهر ويرسلها لـ Kafka

Target output format (مطابق للملفات الأصلية):
  cafes.xlsx / gyms.xlsx:
    name       | str
    latitude   | float64
    longitude  | float64

المصدر: Overpass API (مجاني، بدون API key)
  https://overpass-api.de/api/interpreter

الـ bounding box لإسكندرية مصر:
  lat: 30.9 → 31.4
  lon: 29.5 → 30.2

Topics:
  osm-cafes-alexandria
  osm-gyms-alexandria

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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [OSM-PRODUCER] %(message)s")
log = logging.getLogger(__name__)

# ─── Config ────────────────────────────────────────────────────────────────────
KAFKA_BROKER   = os.environ.get("KAFKA_BROKER", "kafka:9092")
OVERPASS_URL   = "https://overpass-api.de/api/interpreter"
TIMEOUT        = 60

# Bounding box: إسكندرية مصر فقط (south, west, north, east)
ALEX_BBOX = "30.9,29.5,31.4,30.2"

if __name__ == "__main__":
    delay = int(os.environ.get("STARTUP_DELAY_SEC", "0"))
    if delay:
        time.sleep(delay)
    scheduler = BlockingScheduler()

HEADERS = {
    "User-Agent": "SmartCityAnalyzer/1.0 (Alexandria, Egypt; academic project)",
    "Accept": "application/json",
}

TOPICS = {
    "cafes": "osm-cafes-alexandria",
    "gyms":  "osm-gyms-alexandria",
}

# ─── Overpass Queries ───────────────────────────────────────────────────────────
# كل query محددة بـ bounding box إسكندرية مصر بدقة

CAFE_QUERY = f"""
[out:json][timeout:{TIMEOUT}];
(
  node["amenity"="cafe"]({ALEX_BBOX});
  way["amenity"="cafe"]({ALEX_BBOX});
  relation["amenity"="cafe"]({ALEX_BBOX});
);
out center;
"""

GYM_QUERY = f"""
[out:json][timeout:{TIMEOUT}];
(
  node["leisure"="fitness_centre"]({ALEX_BBOX});
  way["leisure"="fitness_centre"]({ALEX_BBOX});
  node["leisure"="sports_centre"]({ALEX_BBOX});
  way["leisure"="sports_centre"]({ALEX_BBOX});
  node["sport"="fitness"]({ALEX_BBOX});
  way["sport"="fitness"]({ALEX_BBOX});
);
out center;
"""
# ───────────────────────────────────────────────────────────────────────────────


def build_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
        acks="all",
        retries=3,
        max_block_ms=300000,   # 30s ??? 60s ??????????
        request_timeout_ms=25000,
    )


def fetch_overpass(query: str, label: str) -> list[dict]:
    """يرسل Overpass query ويرجع list of elements"""
    log.info(f"Fetching {label} from Overpass API...")
    try:
        resp = requests.post(
            OVERPASS_URL,
            data={"data": query},
            headers=HEADERS,
            timeout=TIMEOUT + 10,
        )
        resp.raise_for_status()
        data = resp.json()
        elements = data.get("elements", [])
        log.info(f"  → {len(elements)} raw elements returned")
        return elements
    except requests.exceptions.Timeout:
        log.error(f"Overpass timeout for {label}")
        return []
    except Exception as e:
        log.error(f"Overpass error for {label}: {e}")
        return []


def extract_coords(el: dict) -> tuple[float, float] | tuple[None, None]:
    """
    يستخرج (lat, lon) من element.
    - Node: el["lat"], el["lon"]
    - Way/Relation: el["center"]["lat"], el["center"]["lon"]
    """
    if el["type"] == "node":
        return el.get("lat"), el.get("lon")
    center = el.get("center", {})
    return center.get("lat"), center.get("lon")


def parse_element(el: dict, category: str) -> dict | None:
    """
    يحول OSM element لـ record بنفس شكل cafes.xlsx / gyms.xlsx:
      name, latitude, longitude
    """
    tags = el.get("tags", {})

    # اسم المكان — بنفس أولوية الـ get_cafes.py الأصلي
    name = (
        tags.get("name")
        or tags.get("name:ar")
        or tags.get("name:en")
        or tags.get("brand")
        or None
    )

    lat, lon = extract_coords(el)

    if lat is None or lon is None:
        return None

    return {
        "name":       None if (name is not None and str(name) in ('nan','NaN','')) else name,
        "latitude":   round(float(lat), 6),
        "longitude":  round(float(lon), 6),
        "osm_id":     el.get("id"),
        "category":   category,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "source":     "openstreetmap",
    }


def run_cycle():
    log.info("=" * 60)
    log.info(f"OSM scrape cycle — {datetime.now():%Y-%m-%d %H:%M}")
    producer = build_producer()

    for category, (label, query, topic) in {
        "cafes": ("Cafes",  CAFE_QUERY, TOPICS["cafes"]),
        "gyms":  ("Gyms",   GYM_QUERY,  TOPICS["gyms"]),
    }.items():
        elements = fetch_overpass(query, label)
        sent = 0
        seen_ids = set()

        for el in elements:
            rec = parse_element(el, category)
            if rec is None:
                continue
            osm_id = rec["osm_id"]
            if osm_id in seen_ids:
                continue
            seen_ids.add(osm_id)
            producer.send(topic, value=rec)
            sent += 1

        log.info(f"  {label}: sent {sent} records → topic '{topic}'")
        time.sleep(2)   # polite delay between queries

    producer.flush()
    producer.close()
    log.info("OSM cycle complete")
    log.info("=" * 60)


if __name__ == "__main__":
    log.info("Running once (Airflow mode)")
    run_cycle()
    log.info("Done.")
