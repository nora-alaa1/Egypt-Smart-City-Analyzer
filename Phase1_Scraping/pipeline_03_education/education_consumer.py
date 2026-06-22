"""
Education Data Consumer
========================
يستقبل من topic-ين:
  schools-alexandria  → Schools_Alexandria.csv
  centers-alexandria  → Centers_Alexandria.csv

Output columns:
  name | type | edu_level | latitude | longitude | operator | capacity
"""

import json
import logging
import os
from datetime import datetime

import pandas as pd
from kafka import KafkaConsumer
# openpyxl removed — all output is now CSV

logging.basicConfig(level=logging.INFO, format="%(asctime)s [EDU-CONSUMER] %(message)s")
log = logging.getLogger(__name__)

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
TOPICS       = ["schools-alexandria", "centers-alexandria"]
GROUP_ID     = "education-cleaner-group"
OUTPUT_DIR   = os.path.join(os.path.dirname(__file__), "output")
TIMEOUT_MS   = 60_000

ALEX_LAT = (30.9, 31.4)
ALEX_LON = (29.5, 30.2)



def clean_record(raw: dict) -> dict | None:
    try:
        lat = float(raw.get("latitude", 0))
        lon = float(raw.get("longitude", 0))
        if not (ALEX_LAT[0] <= lat <= ALEX_LAT[1]):
            return None
        if not (ALEX_LON[0] <= lon <= ALEX_LON[1]):
            return None
        return {
            "name":      raw.get("name"),
            "type":      raw.get("type", "Educational"),
            "edu_level": raw.get("edu_level"),
            "latitude":  round(lat, 6),
            "longitude": round(lon, 6),
            "operator":  raw.get("operator"),
            "capacity":  raw.get("capacity"),
        }
    except Exception:
        return None


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
    buffers = {"schools": [], "centers": []}

    try:
        for msg in consumer:
            raw = msg.value
            r   = clean_record(raw)
            if r:
                key = "schools" if msg.topic == "schools-alexandria" else "centers"
                buffers[key].append(r)
    except StopIteration:
        pass
    finally:
        consumer.close()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    date_tag = datetime.now().strftime("%Y%m%d")
    cols = ["name", "type", "edu_level", "latitude", "longitude", "operator", "capacity"]

    for key, title, sheet in [
        ("schools", "Alexandria Schools — SmartCityAnalyzer", "Schools"),
        ("centers", "Alexandria Education Centers — SmartCityAnalyzer", "Centers"),
    ]:
        if buffers[key]:
            df = (
                pd.DataFrame(buffers[key])
                .drop_duplicates(subset=["latitude", "longitude"])
                .reset_index(drop=True)
            )
            path = os.path.join(OUTPUT_DIR, f"{key}_alexandria_{date_tag}.csv")
            df[cols].to_csv(path, index=False, encoding="utf-8-sig")
            log.info(f"Saved {len(df)} rows → {path}")

    log.info(f"Done — schools:{len(buffers['schools'])} centers:{len(buffers['centers'])}")


if __name__ == "__main__":
    run()
