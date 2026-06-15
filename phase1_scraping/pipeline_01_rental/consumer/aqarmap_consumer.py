"""
Aqarmap Rental Data — Kafka Consumer + Cleaner
================================================
يستقبل events من الـ Producer
→ ينظف الداتا
→ يحفظها في CSV

Output columns:
    area(m²)     | int
    rent(EGP)    | int
    location_en  | str  →  "Alexandria / Neighborhood"
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
KAFKA_BROKER   = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC          = "rent-commercial-alexandria"
GROUP_ID       = "rent-cleaner-group"
OUTPUT_DIR     = os.path.join(os.path.dirname(__file__), "..", "output")
BATCH_TIMEOUT  = 60_000      # ms — flush batch لو مفيش messages جديدة
# ───────────────────────────────────────────────────────────────────────────────


# ─── Cleaning Rules (تطابق clean_data_rent.ipynb) ──────────────────────────────

AREA_MIN, AREA_MAX   = 50, 5000      # م² — نفس range الداتا الأصلية
RENT_MIN, RENT_MAX   = 1100, 700_000  # ج.م — نفس range الداتا الأصلية

LOCATION_FIXES = {               # تصحيح أخطاء إملائية شائعة من الـ scraper
    "Moharam Bek":   "Moharram Bek",
    "Moharam Bey":   "Moharram Bek",
    "El Asafra":     "Asafra Bahary",
    "Kafr Abdu":     "Kafr Abdo",
    "San Stefanus":  "San Stefano",
}


def clean_location(raw: str) -> str | None:
    """
    'Alexandria / smouha'  →  'Alexandria / Smouha'
    يتأكد من البداية بـ 'Alexandria'، ويعمل Title Case
    """
    if not raw or "/" not in raw:
        return None
    parts = [p.strip().title() for p in raw.split("/")]
    if parts[0].lower() not in ("alexandria", "al iskandariya"):
        return None
    neighborhood = parts[-1]
    neighborhood = LOCATION_FIXES.get(neighborhood, neighborhood)
    return f"Alexandria / {neighborhood}"


def clean_record(raw: dict) -> dict | None:
    """ينظف record واحد — بيرجع None لو فيه مشكلة"""
    try:
        area = int(raw.get("area(m²)", 0))
        rent = int(raw.get("rent(EGP)", 0))
        loc  = clean_location(str(raw.get("location_en", "")))

        if not loc:
            return None
        if not (AREA_MIN <= area <= AREA_MAX):
            return None
        if not (RENT_MIN <= rent <= RENT_MAX):
            return None

        return {
            "area(m²)":    area,
            "rent(EGP)":   rent,
            "location_en": loc,
        }
    except Exception as e:
        log.debug(f"Clean error: {e} | raw={raw}")
        return None


# ─── CSV Export ────────────────────────────────────────────────────────────────


def save_to_csv(records: list[dict], cycle: int):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    date_tag  = datetime.now().strftime("%Y%m%d")
    filename  = f"rent_commercial_alexandria_cycle{cycle}_{date_tag}.csv"
    filepath  = os.path.join(OUTPUT_DIR, filename)

    df = (
        pd.DataFrame(records)
        .drop_duplicates(subset=["location_en", "area(m²)", "rent(EGP)"])
        .sort_values("location_en")
        .reset_index(drop=True)
    )

    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    log.info(f"Saved {len(df)} records → {filepath}")
    return filepath


# ─── Main Consumer Loop ─────────────────────────────────────────────────────────

def run():
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        group_id=GROUP_ID,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        consumer_timeout_ms=BATCH_TIMEOUT,
    )

    log.info(f"Listening on topic '{TOPIC}' ...")
    cycle      = 1
    buffer     = []

    try:
        for msg in consumer:
            raw     = msg.value
            cleaned = clean_record(raw)
            if cleaned:
                buffer.append(cleaned)

    except StopIteration:
        # consumer_timeout_ms انتهى → البيانات خلصت
        pass
    finally:
        consumer.close()

    if buffer:
        path = save_to_csv(buffer, cycle)
        log.info(f"Cycle {cycle}: {len(buffer)} clean records saved → {path}")
    else:
        log.warning("No valid records received in this cycle.")


if __name__ == "__main__":
    # كل مرة بيتشغل المستهلك (بعد ما الـ Scheduler يشغل الـ Producer)
    # بيستهلك كل الـ events الجديدة ويحفظهم في CSV
    run()
