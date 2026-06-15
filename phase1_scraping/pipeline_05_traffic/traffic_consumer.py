"""
Traffic Data Consumer
======================
يستقبل من topic-ين:
  traffic-nodes-alexandria  → Nodes_Alexandria.csv
  traffic-edges-alexandria  → Edges_Alexandria.csv

Output:
  Nodes: node_id | latitude | longitude | district | betweenness | street_count | source
  Edges: from_node | to_node | name | length_m | speed_kph | road_type | source
"""

import json
import logging
import os
from datetime import datetime

import pandas as pd
from kafka import KafkaConsumer
# openpyxl removed — all output is now CSV

logging.basicConfig(level=logging.INFO, format="%(asctime)s [TRAFFIC-CONSUMER] %(message)s")
log = logging.getLogger(__name__)

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
TOPICS       = ["traffic-nodes-alexandria", "traffic-edges-alexandria"]
GROUP_ID     = "traffic-cleaner-group"
OUTPUT_DIR   = os.path.join(os.path.dirname(__file__), "output")
TIMEOUT_MS   = 90_000   # أكبر لأن الداتا كبيرة

# ─── Formatting constants removed (openpyxl not needed) ───────────────────────


def write_csv(df: pd.DataFrame, path: str):
    df.to_csv(path, index=False, encoding="utf-8-sig")
    log.info(f"Saved {len(df)} rows → {path}")


def run():
    consumer = KafkaConsumer(
        *TOPICS,
        bootstrap_servers=KAFKA_BROKER,
        group_id=GROUP_ID,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        consumer_timeout_ms=TIMEOUT_MS,
        session_timeout_ms=120_000,
        heartbeat_interval_ms=40_000,
        max_poll_interval_ms=600_000,
        max_poll_records=1000,
        fetch_max_bytes=52428800,
    )

    log.info(f"Listening on topics: {TOPICS}")
    buffers = {"nodes": [], "edges": []}

    try:
        for msg in consumer:
            raw = msg.value
            if msg.topic == "traffic-nodes-alexandria":
                r = clean_node(raw)
                if r:
                    buffers["nodes"].append(r)
            elif msg.topic == "traffic-edges-alexandria":
                r = clean_edge(raw)
                if r:
                    buffers["edges"].append(r)
    except StopIteration:
        pass
    finally:
        consumer.close()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    date_tag = datetime.now().strftime("%Y%m%d")

    # Nodes CSV
    if buffers["nodes"]:
        df_nodes = (
            pd.DataFrame(buffers["nodes"])
            .drop_duplicates(subset=["latitude", "longitude"])
            .sort_values(["district", "latitude"])
            .reset_index(drop=True)
        )
        path = os.path.join(OUTPUT_DIR, f"traffic_nodes_alexandria_{date_tag}.csv")
        write_csv(
            df_nodes[["node_id", "latitude", "longitude", "district", "street_count", "betweenness", "source"]],
            path,
        )

    # Edges CSV
    if buffers["edges"]:
        df_edges = (
            pd.DataFrame(buffers["edges"])
            .drop_duplicates(subset=["from_node", "to_node"])
            .sort_values(["road_type", "name"])
            .reset_index(drop=True)
        )
        path = os.path.join(OUTPUT_DIR, f"traffic_edges_alexandria_{date_tag}.csv")
        write_csv(
            df_edges[["from_node", "to_node", "name", "length_m", "speed_kph", "road_type", "source"]],
            path,
        )

    log.info(
        f"Done — nodes:{len(buffers['nodes'])} edges:{len(buffers['edges'])}"
    )


if __name__ == "__main__":
    run()
