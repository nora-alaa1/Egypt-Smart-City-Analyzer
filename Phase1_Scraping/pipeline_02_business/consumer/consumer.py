"""
Business Data Consumer
========================
يستقبل من كل الـ topics:
  osm-cafes-alexandria       → cafes.csv
  osm-gyms-alexandria        → gyms.csv
  pharmacy-alexandria        → pharmacies.csv
  restaurants-alexandria     → restaurants.csv
  bakeries-alexandria        → bakeries.csv
  hotels-alexandria          → hotels.csv
  hospitals-alexandria       → hospitals.csv
  banks-alexandria           → banks.csv
  clothing-alexandria        → clothing.csv
  supermarkets-alexandria    → supermarkets.csv
  sweets-alexandria          → sweets.csv
"""

import json
import logging
import os
import re
from datetime import datetime, timezone

import pandas as pd
from kafka import KafkaConsumer
# openpyxl removed — all output is now CSV

logging.basicConfig(level=logging.INFO, format="%(asctime)s [CONSUMER] %(message)s")
log = logging.getLogger(__name__)

# ─── Config ────────────────────────────────────────────────────────────────────
KAFKA_BROKER = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPICS = [
    "osm-cafes-alexandria",
    "osm-gyms-alexandria",
    "pharmacy-alexandria",
    "restaurants-alexandria",
    "bakeries-alexandria",
    "hotels-alexandria",
    "hospitals-alexandria",
    "banks-alexandria",
    "clothing-alexandria",
    "supermarkets-alexandria",
    "sweets-alexandria",
]
GROUP_ID   = "business-cleaner-group-v3"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")
TIMEOUT_MS = 60_000

# إسكندرية مصر bounding box
ALEX_LAT = (30.9, 31.4)
ALEX_LON = (29.5, 30.2)
# ───────────────────────────────────────────────────────────────────────────────


# ═══════════════════════════════════════════════════════════════════════════════
# CLEANING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def clean_osm_record(raw: dict) -> dict | None:
    """
    ينظف OSM record (كافيه، جيم، مطعم، فندق، إلخ).
    - latitude/longitude لازم يكونوا جوا bounding box إسكندرية
    - name ممكن يكون None
    - بنحذف duplicates بـ (lat, lon)
    """
    try:
        lat = float(raw.get("latitude", 0))
        lon = float(raw.get("longitude", 0))
        name = raw.get("name")

        if not (ALEX_LAT[0] <= lat <= ALEX_LAT[1]):
            return None
        if not (ALEX_LON[0] <= lon <= ALEX_LON[1]):
            return None

        return {
            "name":      name,
            "latitude":  round(lat, 6),
            "longitude": round(lon, 6),
        }
    except Exception:
        return None


def clean_pharmacy_record(raw: dict) -> dict | None:
    """
    ينظف pharmacy record.
    - name و address لازم موجودين
    - phone ممكن يكون None
    """
    try:
        name    = str(raw.get("name", "")).strip()
        address = str(raw.get("address", "")).strip()
        phone   = raw.get("phone")
        url     = str(raw.get("web_scraper_start_url", "")).strip()
        src     = str(raw.get("source_file", "")).strip()

        if not name:
            return None
        if not address:
            return None

        if phone:
            phone_str = str(phone).strip()
            phone_digits = re.sub(r"[^\d]", "", phone_str)
            if len(phone_digits) < 5:
                phone = None
            else:
                try:
                    phone = float(phone_str.replace(",", ""))
                except ValueError:
                    phone = None
        else:
            phone = None

        return {
            "name":                  name,
            "address":               address,
            "phone":                 phone,
            "source_file":           src,
            "web_scraper_start_url": url,
        }
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# CSV OUTPUT
# ═══════════════════════════════════════════════════════════════════════════════


def write_csv(df: pd.DataFrame, path: str):
    df.to_csv(path, index=False, encoding="utf-8-sig")
    log.info(f"Saved {len(df)} rows → {path}")


def save_osm_topic(records: list, name: str, date_tag: str, drop_null_name: bool = False):
    """حفظ أي topic من نوع OSM كـ CSV."""
    if not records:
        return
    df = pd.DataFrame(records).drop_duplicates(subset=["latitude", "longitude"])
    if drop_null_name:
        df = df.dropna(subset=["name"])
    df = df.reset_index(drop=True)
    path = os.path.join(OUTPUT_DIR, f"{name}_{date_tag}.csv")
    write_csv(df[["name", "latitude", "longitude"]], path)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN CONSUMER
# ═══════════════════════════════════════════════════════════════════════════════

def run():
    consumer = KafkaConsumer(
        *TOPICS,
        bootstrap_servers=KAFKA_BROKER,
        group_id=GROUP_ID,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        consumer_timeout_ms=TIMEOUT_MS,
    )

    log.info(f"Listening on topics: {TOPICS}")

    buffers = {
        "cafes":        [],
        "gyms":         [],
        "pharmacies":   [],
        "restaurants":  [],
        "bakeries":     [],
        "hotels":       [],
        "hospitals":    [],
        "banks":        [],
        "clothing":     [],
        "supermarkets": [],
        "sweets":       [],
    }

    topic_map = {
        "osm-cafes-alexandria":     "cafes",
        "osm-gyms-alexandria":      "gyms",
        "restaurants-alexandria":   "restaurants",
        "bakeries-alexandria":      "bakeries",
        "hotels-alexandria":        "hotels",
        "hospitals-alexandria":     "hospitals",
        "banks-alexandria":         "banks",
        "clothing-alexandria":      "clothing",
        "supermarkets-alexandria":  "supermarkets",
        "sweets-alexandria":        "sweets",
    }

    try:
        for msg in consumer:
            topic = msg.topic
            raw   = msg.value

            if topic == "pharmacy-alexandria":
                r = clean_pharmacy_record(raw)
                if r:
                    buffers["pharmacies"].append(r)

            elif topic in topic_map:
                r = clean_osm_record(raw)
                if r:
                    buffers[topic_map[topic]].append(r)

    except StopIteration:
        pass
    finally:
        consumer.close()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    date_tag = datetime.now().strftime("%Y%m%d")

    # ── OSM Topics → Excel ─────────────────────────────────────────────────────
    save_osm_topic(buffers["cafes"],        "cafes",        date_tag)
    save_osm_topic(buffers["gyms"],         "gyms",         date_tag, drop_null_name=True)
    save_osm_topic(buffers["restaurants"],  "restaurants",  date_tag)
    save_osm_topic(buffers["bakeries"],     "bakeries",     date_tag)
    save_osm_topic(buffers["hotels"],       "hotels",       date_tag)
    save_osm_topic(buffers["hospitals"],    "hospitals",    date_tag)
    save_osm_topic(buffers["banks"],        "banks",        date_tag)
    save_osm_topic(buffers["clothing"],     "clothing",     date_tag)
    save_osm_topic(buffers["supermarkets"], "supermarkets", date_tag)
    save_osm_topic(buffers["sweets"],       "sweets",       date_tag)

    # ── Pharmacies → CSV ───────────────────────────────────────────────────────
    if buffers["pharmacies"]:
        df = (pd.DataFrame(buffers["pharmacies"])
              .drop_duplicates(subset=["name", "address"])
              .reset_index(drop=True))
        path = os.path.join(OUTPUT_DIR, f"pharmacies_{date_tag}.csv")
        write_csv(
            df[["name", "address", "phone", "source_file", "web_scraper_start_url"]],
            path,
        )

    log.info(
        f"Done — "
        + " | ".join(f"{k}:{len(v)}" for k, v in buffers.items())
    )


if __name__ == "__main__":
    run()
