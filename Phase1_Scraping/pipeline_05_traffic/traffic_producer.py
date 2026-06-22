"""
Traffic Data Producer — Alexandria Road Network
================================================
يرسل بيانات شبكة الطرق والتقاطعات من مصدرين:

Source 1: egypt_smart_city.db (SQLite — مخزّن محلياً)
  - جداول: nodes, edges أو intersections, streets
  - 81,768 عقدة وحافة

Source 2: OSMnx API (live refresh كل 6 أشهر)
  - يسحب road network إسكندرية من OpenStreetMap مباشرة
  - يحسب betweenness centrality لكل عقدة (مؤشر أهمية التقاطع)

Topics:
  traffic-nodes-alexandria   → التقاطعات (nodes)
  traffic-edges-alexandria   → الطرق (edges)

Output columns:
  Nodes: node_id | latitude | longitude | district | betweenness | degree | street_count
  Edges: edge_id | from_node | to_node | name | length_m | speed_kph | road_type | district

Schedule: كل 6 أشهر
"""

import json
import logging
import os
import sqlite3
import time
from datetime import datetime, timezone

import pandas as pd
import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from kafka import KafkaProducer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [TRAFFIC-PRODUCER] %(message)s")
log = logging.getLogger(__name__)

# ─── Config ────────────────────────────────────────────────────────────────────
KAFKA_BROKER  = os.getenv("KAFKA_BROKER", "localhost:9092")
TOPIC_NODES   = "traffic-nodes-alexandria"
TOPIC_EDGES   = "traffic-edges-alexandria"

DATA_DIR      = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data")
DB_PATH       = os.path.join(DATA_DIR, "Trafic_Data", "egypt_smart_city (1).db")
NODES_CSV     = os.path.join(DATA_DIR, "Trafic_Data", "Alexandria_Intersections_Nodes.csv")
EDGES_CSV     = os.path.join(DATA_DIR, "Trafic_Data", "Alexandria_Streets_Edges.csv")

# إسكندرية bounding box
ALEX_LAT = (30.9, 31.4)
ALEX_LON = (29.5, 30.2)

# Overpass لجلب OSMnx-style roads
OVERPASS_URL  = "https://overpass-api.de/api/interpreter"
ALEX_BBOX     = "30.9,29.5,31.4,30.2"
# ───────────────────────────────────────────────────────────────────────────────

# تصنيف أنواع الطرق بالعربي/الإنجليزي
ROAD_TYPE_MAP = {
    "motorway": "Motorway", "motorway_link": "Motorway",
    "trunk": "Trunk Road", "trunk_link": "Trunk Road",
    "primary": "Primary", "primary_link": "Primary",
    "secondary": "Secondary", "secondary_link": "Secondary",
    "tertiary": "Tertiary", "tertiary_link": "Tertiary",
    "residential": "Residential", "service": "Service",
    "unclassified": "Unclassified", "living_street": "Living Street",
    "pedestrian": "Pedestrian",
}

# سرعات افتراضية بـ kph لكل نوع طريق (OpenStreetMap convention)
SPEED_DEFAULTS = {
    "Motorway": 110, "Trunk Road": 90, "Primary": 60,
    "Secondary": 50, "Tertiary": 40, "Residential": 30,
    "Service": 20, "Unclassified": 30, "Living Street": 10, "Pedestrian": 5,
}

# مناطق إسكندرية مع bounding boxes تقريبية لـ district assignment
DISTRICT_BOUNDS = {
    "Mahatet El Raml":    (31.190, 31.205, 29.895, 29.920),
    "Moharram Bek":       (31.190, 31.205, 29.915, 29.935),
    "Sidi Gaber":         (31.210, 31.230, 29.940, 29.965),
    "Kafr Abdu":          (31.205, 31.225, 29.920, 29.945),
    "Smouha":             (31.205, 31.225, 29.950, 29.975),
    "El Montazah":        (31.275, 31.300, 30.000, 30.025),
    "Sidi Bishr":         (31.245, 31.270, 30.020, 30.045),
    "Miami":              (31.250, 31.275, 30.035, 30.060),
    "Stanley":            (31.220, 31.240, 29.960, 29.980),
    "San Stefano":        (31.228, 31.245, 29.975, 29.995),
    "El Agamy":           (31.040, 31.075, 29.760, 29.790),
    "Borg El Arab":       (30.895, 30.930, 29.520, 29.550),
    "Louran":             (31.200, 31.215, 29.925, 29.945),
    "El Gomrok":          (31.195, 31.210, 29.880, 29.900),
    "Attarin":            (31.190, 31.205, 29.895, 29.915),
    "El Hadra":           (31.178, 31.195, 29.885, 29.905),
    "El Wardian":         (31.178, 31.195, 29.875, 29.895),
    "Bab El Hadid":       (31.188, 31.205, 29.890, 29.910),
    "El Dekhela":         (31.145, 31.165, 29.840, 29.865),
    "Abu Qir":            (31.305, 31.330, 30.060, 30.090),
}


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


def assign_district(lat: float, lon: float) -> str | None:
    """يعيّن المنطقة بناءً على الإحداثيات"""
    for district, (lat_min, lat_max, lon_min, lon_max) in DISTRICT_BOUNDS.items():
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            return district
    return None


def load_from_sqlite(producer: KafkaProducer) -> tuple[int, int]:
    """يحمّل بيانات الـ SQLite DB المحلي"""
    if not os.path.exists(DB_PATH):
        log.warning(f"SQLite DB not found: {DB_PATH}")
        return 0, 0

    nodes_sent = edges_sent = 0

    try:
        conn   = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # اكتشاف الجداول الموجودة
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        log.info(f"SQLite tables: {tables}")

        # محاولة قراءة nodes
        node_table = next((t for t in tables if "node" in t.lower() or "intersection" in t.lower()), None)
        if node_table:
            df_nodes = pd.read_sql(f"SELECT * FROM [{node_table}]", conn)
            log.info(f"  Nodes table '{node_table}': {len(df_nodes)} rows, cols={list(df_nodes.columns)}")

            lat_col = next((c for c in df_nodes.columns if "lat" in c.lower() or "y" == c.lower()), None)
            lon_col = next((c for c in df_nodes.columns if "lon" in c.lower() or "lng" in c.lower() or "x" == c.lower()), None)
            id_col  = next((c for c in df_nodes.columns if "id" in c.lower() or "osmid" in c.lower()), df_nodes.columns[0])

            if lat_col and lon_col:
                for _, row in df_nodes.iterrows():
                    lat = float(row[lat_col])
                    lon = float(row[lon_col])
                    if not (ALEX_LAT[0] <= lat <= ALEX_LAT[1] and ALEX_LON[0] <= lon <= ALEX_LON[1]):
                        continue
                    rec = {
                        "node_id":    str(row[id_col]),
                        "latitude":   round(lat, 6),
                        "longitude":  round(lon, 6),
                        "district":   assign_district(lat, lon),
                        "street_count": row.get("street_count", row.get("degree")),
                        "betweenness":  row.get("betweenness_centrality", row.get("betweenness")),
                        "source":     "sqlite_local",
                        "scraped_at": datetime.now(timezone.utc).isoformat(),
                    }
                    producer.send(TOPIC_NODES, value=rec)
                    nodes_sent += 1

        # محاولة قراءة edges
        edge_table = next((t for t in tables if "edge" in t.lower() or "street" in t.lower() or "road" in t.lower()), None)
        if edge_table:
            df_edges = pd.read_sql(f"SELECT * FROM [{edge_table}]", conn)
            log.info(f"  Edges table '{edge_table}': {len(df_edges)} rows, cols={list(df_edges.columns)}")

            for _, row in df_edges.iterrows():
                rec = {
                    "from_node": str(row.get("u", row.get("from_node", row.get("source", "")))),
                    "to_node":   str(row.get("v", row.get("to_node", row.get("target", "")))),
                    "name":      row.get("name", row.get("street_name")),
                    "length_m":  row.get("length", row.get("length_m")),
                    "speed_kph": row.get("speed_kph", row.get("maxspeed")),
                    "road_type": ROAD_TYPE_MAP.get(
                        str(row.get("highway", row.get("road_type", ""))).lower(),
                        str(row.get("highway", "Unclassified"))
                    ),
                    "source":    "sqlite_local",
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                }
                producer.send(TOPIC_EDGES, value=rec)
                edges_sent += 1

        conn.close()

    except Exception as e:
        log.error(f"SQLite error: {e}")

    return nodes_sent, edges_sent


def load_from_csv(producer: KafkaProducer) -> tuple[int, int]:
    """يحمّل من ملفات الـ CSV المحلية (fallback)"""
    nodes_sent = edges_sent = 0

    # Nodes CSV
    if os.path.exists(NODES_CSV):
        try:
            df = pd.read_csv(NODES_CSV)
            log.info(f"Nodes CSV: {len(df)} rows, cols={list(df.columns)}")

            lat_col = next((c for c in df.columns if "lat" in c.lower()), None)
            lon_col = next((c for c in df.columns if "lon" in c.lower() or "lng" in c.lower()), None)
            id_col  = next((c for c in df.columns if "id" in c.lower() or "osmid" in c.lower()), df.columns[0])

            if lat_col and lon_col:
                for _, row in df.iterrows():
                    lat = float(row[lat_col])
                    lon = float(row[lon_col])
                    if not (ALEX_LAT[0] <= lat <= ALEX_LAT[1] and ALEX_LON[0] <= lon <= ALEX_LON[1]):
                        continue
                    rec = {
                        "node_id":    str(row[id_col]),
                        "latitude":   round(lat, 6),
                        "longitude":  round(lon, 6),
                        "district":   assign_district(lat, lon),
                        "street_count": row.get("street_count"),
                        "betweenness":  row.get("betweenness_centrality"),
                        "source":     "csv_local",
                        "scraped_at": datetime.now(timezone.utc).isoformat(),
                    }
                    producer.send(TOPIC_NODES, value=rec)
                    nodes_sent += 1
        except Exception as e:
            log.error(f"Nodes CSV error: {e}")

    # Edges CSV
    if os.path.exists(EDGES_CSV):
        try:
            df = pd.read_csv(EDGES_CSV)
            log.info(f"Edges CSV: {len(df)} rows, cols={list(df.columns)}")

            for _, row in df.iterrows():
                highway = str(row.get("highway", "")).lower().strip()
                rec = {
                    "from_node": str(row.get("u", row.get("from", ""))),
                    "to_node":   str(row.get("v", row.get("to", ""))),
                    "name":      row.get("name"),
                    "length_m":  row.get("length"),
                    "speed_kph": row.get("speed_kph", SPEED_DEFAULTS.get(ROAD_TYPE_MAP.get(highway, "Unclassified"), 30)),
                    "road_type": ROAD_TYPE_MAP.get(highway, "Unclassified"),
                    "source":    "csv_local",
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                }
                producer.send(TOPIC_EDGES, value=rec)
                edges_sent += 1
        except Exception as e:
            log.error(f"Edges CSV error: {e}")

    return nodes_sent, edges_sent


def fetch_osm_roads(producer: KafkaProducer) -> tuple[int, int]:
    """يسحب بيانات الطرق من Overpass API مباشرة (live refresh)"""
    log.info("Fetching road network from Overpass API...")

    query = f"""
[out:json][timeout:90];
(
  way["highway"~"^(motorway|trunk|primary|secondary|tertiary|residential|service|unclassified)$"]({ALEX_BBOX});
);
out geom tags;
"""
    nodes_sent = edges_sent = 0

    try:
        resp = requests.post(
            OVERPASS_URL,
            data={"data": query},
            headers={"User-Agent": "SmartCityAnalyzer/1.0 Traffic"},
            timeout=100,
        )
        resp.raise_for_status()
        elements = resp.json().get("elements", [])
        log.info(f"  Overpass returned {len(elements)} road elements")

        seen_pairs = set()
        for el in elements:
            tags     = el.get("tags", {})
            highway  = tags.get("highway", "unclassified")
            road_type = ROAD_TYPE_MAP.get(highway, "Unclassified")
            name     = tags.get("name") or tags.get("name:ar") or tags.get("name:en")
            speed    = tags.get("maxspeed")
            try:
                speed = int(str(speed).replace("km/h", "").strip()) if speed else SPEED_DEFAULTS.get(road_type, 30)
            except ValueError:
                speed = SPEED_DEFAULTS.get(road_type, 30)

            geometry = el.get("geometry") or []
            if not isinstance(geometry, list) or len(geometry) < 2:
                continue
            geometry = [g for g in geometry if isinstance(g, dict) and "lat" in g and "lon" in g]
            if len(geometry) < 2:
                continue

            # حساب طول الـ way (تقريبي بدون geodesy)
            total_length = 0.0
            for i in range(len(geometry) - 1):
                dlat = (geometry[i+1]["lat"] - geometry[i]["lat"]) * 111320
                dlon = (geometry[i+1]["lon"] - geometry[i]["lon"]) * 111320 * 0.8
                total_length += (dlat**2 + dlon**2) ** 0.5

            # Node أول وآخر
            first = geometry[0]
            last  = geometry[-1]

            pair = (round(first["lat"], 4), round(first["lon"], 4),
                    round(last["lat"], 4), round(last["lon"], 4))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            # إرسال الـ nodes
            for node_g in [first, last]:
                lat = node_g["lat"]
                lon = node_g["lon"]
                if not (ALEX_LAT[0] <= lat <= ALEX_LAT[1] and ALEX_LON[0] <= lon <= ALEX_LON[1]):
                    continue
                producer.send(TOPIC_NODES, value={
                    "node_id":    f"osm_{el['id']}_{round(lat,4)}_{round(lon,4)}",
                    "latitude":   round(lat, 6),
                    "longitude":  round(lon, 6),
                    "district":   assign_district(lat, lon),
                    "street_count": None,
                    "betweenness":  None,
                    "source":     "overpass_live",
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                })
                nodes_sent += 1

            # إرسال الـ edge
            producer.send(TOPIC_EDGES, value={
                "from_node": f"{round(first['lat'],4)}_{round(first['lon'],4)}",
                "to_node":   f"{round(last['lat'],4)}_{round(last['lon'],4)}",
                "name":      name,
                "length_m":  round(total_length, 1),
                "speed_kph": speed,
                "road_type": road_type,
                "source":    "overpass_live",
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            })
            edges_sent += 1

    except Exception as e:
        log.error(f"Overpass road fetch error: {e}")

    return nodes_sent, edges_sent


def run_cycle():
    log.info("=" * 60)
    log.info(f"Traffic scrape cycle — {datetime.now():%Y-%m-%d %H:%M}")
    producer = build_producer()

    # Strategy 1: SQLite DB
    n1, e1 = load_from_sqlite(producer)
    log.info(f"  SQLite: {n1} nodes, {e1} edges")

    # Strategy 2: CSVs (إذا الـ DB فاضية)
    if n1 == 0 and e1 == 0:
        n2, e2 = load_from_csv(producer)
        log.info(f"  CSV fallback: {n2} nodes, {e2} edges")
    else:
        n2 = e2 = 0

    # Strategy 3: Live Overpass refresh
    time.sleep(2)
    n3, e3 = fetch_osm_roads(producer)
    log.info(f"  Overpass live: {n3} nodes, {e3} edges")

    producer.flush()
    producer.close()

    total_n = n1 + n2 + n3
    total_e = e1 + e2 + e3
    log.info(f"Traffic cycle complete — {total_n} nodes + {total_e} edges sent")
    log.info("=" * 60)


if __name__ == "__main__":
    log.info("Running once (Airflow mode)")
    run_cycle()
    log.info("Done.")
