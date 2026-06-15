"""
Population Data Consumer
=========================
يستقبل من topic:
  population-alexandria  → Population_Alexandria.csv

Output columns:
  district | population | population_source | nightlight_intensity | year | latitude | longitude
"""

import json
import logging
import os
from datetime import datetime

import pandas as pd
from kafka import KafkaConsumer
# openpyxl removed — all output is now CSV

logging.basicConfig(level=logging.INFO, format="%(asctime)s [POP-CONSUMER] %(message)s")
log = logging.getLogger(__name__)

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
TOPIC        = "population-alexandria"
GROUP_ID     = "population-cleaner-group"
OUTPUT_DIR   = os.path.join(os.path.dirname(__file__), "output")
TIMEOUT_MS   = 60_000

# ─── Formatting constants removed (openpyxl not needed) ───────────────────────


def write_csv(df: pd.DataFrame, path: str):
    df.to_csv(path, index=False, encoding="utf-8-sig")
    log.info(f"Saved {len(df)} rows → {path}")


def run():
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        group_id=GROUP_ID,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        consumer_timeout_ms=TIMEOUT_MS,
    )

    log.info(f"Listening on topic '{TOPIC}' ...")
    buffer = []

    try:
        for msg in consumer:
            r = clean_record(msg.value)
            if r:
                buffer.append(r)
    except StopIteration:
        pass
    finally:
        consumer.close()

    if buffer:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        date_tag = datetime.now().strftime("%Y%m%d")
        df = (
            pd.DataFrame(buffer)
            .drop_duplicates(subset=["district", "year"])
            .sort_values("district")
            .reset_index(drop=True)
        )
        cols = ["district", "population", "population_source",
                "nightlight_intensity", "year", "latitude", "longitude"]
        path = os.path.join(OUTPUT_DIR, f"population_alexandria_{date_tag}.csv")
        write_csv(df[cols], path)
        log.info(f"Done — {len(df)} districts saved.")
    else:
        log.warning("No records received.")


if __name__ == "__main__":
    run()
