"""
Education Data Producer — Schools & Centers (Overpass API)
===========================================================
يسحب بيانات المدارس والمراكز التعليمية من OpenStreetMap
كل 6 أشهر ويرسلها لـ Kafka

Sources:
  - OpenStreetMap via Overpass API (مجاني، بدون API key)
  - https://overpass-api.de/api/interpreter

Bounding Box إسكندرية مصر:
  lat: 30.9 → 31.4
  lon: 29.5 → 30.2

Topics:
  schools-alexandria    → المدارس (ابتدائي، إعدادي، ثانوي)
  centers-alexandria    → المراكز التعليمية والمعاهد

Output columns (مطابق لـ SQLQuery1.sql):
  name, type, latitude, longitude, operator, capacity

Schedule: كل 6 أشهر
"""

import json
import time
import logging
import requests
from kafka import KafkaProducer
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, timezone
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s [EDU-PRODUCER] %(message)s")
log = logging.getLogger(__name__)

# ─── Config ────────────────────────────────────────────────────────────────────
KAFKA_BROKER  = os.getenv("KAFKA_BROKER", "localhost:9092")
OVERPASS_URL  = "https://overpass-api.de/api/interpreter"
TIMEOUT       = 60
ALEX_BBOX     = "30.9,29.5,31.4,30.2"

TOPICS = {
    "schools": "schools-alexandria",
    "centers": "centers-alexandria",
}

HEADERS = {
    "User-Agent": "SmartCityAnalyzer/1.0 (Alexandria Education; academic)",
    "Accept":     "application/json",
}
# ───────────────────────────────────────────────────────────────────────────────

# ─── Overpass Queries ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    delay = int(os.environ.get("STARTUP_DELAY_SEC", "0"))
    if delay:
        time.sleep(delay)
    scheduler = BlockingScheduler()

SCHOOL_QUERY = f"""
[out:json][timeout:{TIMEOUT}];
(
  node["amenity"="school"]({ALEX_BBOX});
  way["amenity"="school"]({ALEX_BBOX});
  node["amenity"="kindergarten"]({ALEX_BBOX});
  way["amenity"="kindergarten"]({ALEX_BBOX});
  node["isced:level"~"1|2|3"]({ALEX_BBOX});
  way["isced:level"~"1|2|3"]({ALEX_BBOX});
);
out center tags;
"""

CENTER_QUERY = f"""
[out:json][timeout:{TIMEOUT}];
(
  node["amenity"="college"]({ALEX_BBOX});
  way["amenity"="college"]({ALEX_BBOX});
  node["amenity"="university"]({ALEX_BBOX});
  way["amenity"="university"]({ALEX_BBOX});
  node["amenity"="training"]({ALEX_BBOX});
  way["amenity"="training"]({ALEX_BBOX});
  node["amenity"="language_school"]({ALEX_BBOX});
  way["amenity"="language_school"]({ALEX_BBOX});
  node["amenity"="tutoring_centre"]({ALEX_BBOX});
  way["amenity"="tutoring_centre"]({ALEX_BBOX});
  node["office"="educational_institution"]({ALEX_BBOX});
  way["office"="educational_institution"]({ALEX_BBOX});
);
out center tags;
"""
# ───────────────────────────────────────────────────────────────────────────────

SCHOOL_TYPE_MAP = {
    "school":       "School",
    "kindergarten": "Kindergarten",
    "college":      "College",
    "university":   "University",
    "training":     "Training Center",
    "language_school": "Language School",
    "tutoring_centre": "Tutoring Center",
    "educational_institution": "Educational Institution",
}


def build_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
        acks="all",
        retries=3,
    )


def fetch_overpass(query: str, label: str) -> list[dict]:
    log.info(f"Fetching {label} from Overpass API...")
    try:
        resp = requests.post(
            OVERPASS_URL,
            data={"data": query},
            headers=HEADERS,
            timeout=TIMEOUT + 10,
        )
        resp.raise_for_status()
        elements = resp.json().get("elements", [])
        log.info(f"  → {len(elements)} raw elements")
        return elements
    except Exception as e:
        log.error(f"Overpass error for {label}: {e}")
        return []


def extract_coords(el: dict) -> tuple[float, float] | tuple[None, None]:
    if el["type"] == "node":
        return el.get("lat"), el.get("lon")
    center = el.get("center", {})
    return center.get("lat"), center.get("lon")


def parse_element(el: dict, category: str) -> dict | None:
    tags = el.get("tags", {})
    lat, lon = extract_coords(el)
    if lat is None or lon is None:
        return None

    # اسم المكان
    name = (
        tags.get("name")
        or tags.get("name:ar")
        or tags.get("name:en")
        or tags.get("official_name")
        or None
    )

    # نوع المنشأة
    amenity = tags.get("amenity") or tags.get("office", "")
    edu_type = SCHOOL_TYPE_MAP.get(amenity, "Educational")

    # مستوى التعليم
    isced = tags.get("isced:level", "")
    if isced:
        level_map = {"0": "Pre-Primary", "1": "Primary", "2": "Lower Secondary",
                     "3": "Upper Secondary", "4": "Post-Secondary", "5": "Higher"}
        edu_level = level_map.get(isced.split(";")[0], isced)
    else:
        edu_level = None

    return {
        "name":        name,
        "type":        edu_type,
        "edu_level":   edu_level,
        "latitude":    round(float(lat), 6),
        "longitude":   round(float(lon), 6),
        "operator":    tags.get("operator"),
        "capacity":    tags.get("capacity"),
        "osm_id":      el.get("id"),
        "category":    category,
        "scraped_at":  datetime.now(timezone.utc).isoformat(),
        "source":      "openstreetmap",
    }


def run_cycle():
    log.info("=" * 60)
    log.info(f"Education scrape cycle — {datetime.now():%Y-%m-%d %H:%M}")
    producer = build_producer()

    jobs = [
        ("Schools",  SCHOOL_QUERY,  "schools", TOPICS["schools"]),
        ("Centers",  CENTER_QUERY,  "centers", TOPICS["centers"]),
    ]

    for label, query, category, topic in jobs:
        elements = fetch_overpass(query, label)
        sent = 0
        seen = set()

        for el in elements:
            rec = parse_element(el, category)
            if rec is None:
                continue
            oid = rec["osm_id"]
            if oid in seen:
                continue
            seen.add(oid)
            producer.send(topic, value=rec)
            sent += 1

        log.info(f"  {label}: {sent} records → topic '{topic}'")
        time.sleep(2)

    producer.flush()
    producer.close()
    log.info("Education cycle complete")
    log.info("=" * 60)


if __name__ == "__main__":
    log.info("Running once (Airflow mode)")
    run_cycle()
    log.info("Done.")
