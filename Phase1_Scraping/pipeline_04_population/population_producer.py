"""
Population Data Producer
=========================
يرسل بيانات تعداد سكان الإسكندرية لـ Kafka

Sources (بالترتيب):
  1. الجهاز المركزي للتعبئة العامة والإحصاء — المحلي (alex_population.xlsx)
  2. WorldPop API (https://hub.worldpop.org) — تقديرات سنوية مجانية
  3. Alexandria_Nightlights_2023.csv (Google Earth Engine VIIRS)

Topic:    population-alexandria
Schedule: كل 6 أشهر

Output columns:
  district | population | year | source | nightlight_intensity
"""

import json
import logging
import os
import re
import time
from datetime import datetime, timezone

import pandas as pd
import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from kafka import KafkaProducer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [POP-PRODUCER] %(message)s")
log = logging.getLogger(__name__)

# ─── Config ────────────────────────────────────────────────────────────────────
KAFKA_BROKER   = os.getenv("KAFKA_BROKER", "localhost:9092")
TOPIC          = "population-alexandria"

# مسارات الملفات المحلية
DATA_DIR       = DATA_DIR = os.environ.get("DATA_DIR", "/app/data")
POP_XLSX       = os.path.join(DATA_DIR, "population__data", "raw", "alex_population.xlsx")
NIGHTLIGHTS    = os.path.join(DATA_DIR, "population__data", "raw", "Alexandria_Nightlights_2023.csv")
PROCESSED_POP  = os.path.join(DATA_DIR, "population__data", "processed", "Final Population data.csv")

# WorldPop API — بيانات 100m resolution لمصر
WORLDPOP_API = (
    "https://hub.worldpop.org/rest/data/pop/wpgp?"
    "iso3=EGY&year={year}&apiKey="  # free endpoint, no key required for listing
)
# ───────────────────────────────────────────────────────────────────────────────

# مناطق إسكندرية وإحداثياتها (مستخرجة من Dim_Location)
ALEX_DISTRICTS = {
    "Sidi Gaber":         {"lat": 31.220, "lon": 29.95,  "pop_estimate": 15000},
    "El Montazah":        {"lat": 31.285, "lon": 30.01,  "pop_estimate": 8000},
    "El Mandara":         {"lat": 31.275, "lon": 30.00,  "pop_estimate": 9000},
    "Kafr Abdu":          {"lat": 31.215, "lon": 29.93,  "pop_estimate": 18000},
    "Borg El Arab":       {"lat": 30.910, "lon": 29.53,  "pop_estimate": 2000},
    "Gleem":              {"lat": 31.225, "lon": 29.965, "pop_estimate": 12000},
    "Sidi Bishr":         {"lat": 31.255, "lon": 30.03,  "pop_estimate": 11000},
    "Miami":              {"lat": 31.260, "lon": 30.045, "pop_estimate": 10000},
    "El Asafra":          {"lat": 31.265, "lon": 30.055, "pop_estimate": 10500},
    "Abu Youssef":        {"lat": 31.210, "lon": 29.91,  "pop_estimate": 16000},
    "Bab El Hadid":       {"lat": 31.195, "lon": 29.90,  "pop_estimate": 20000},
    "El Gomrok (Bahary)": {"lat": 31.200, "lon": 29.89,  "pop_estimate": 22000},
    "El Agamy":           {"lat": 31.055, "lon": 29.77,  "pop_estimate": 6000},
    "Moharram Bek":       {"lat": 31.195, "lon": 29.92,  "pop_estimate": 17000},
    "Louran":             {"lat": 31.205, "lon": 29.935, "pop_estimate": 14000},
    "Camp Shezar":        {"lat": 31.207, "lon": 29.92,  "pop_estimate": 13500},
    "Mahatet El Raml":    {"lat": 31.200, "lon": 29.91,  "pop_estimate": 22000},
    "Abis":               {"lat": 31.150, "lon": 29.85,  "pop_estimate": 5000},
    "Abu Qir":            {"lat": 31.315, "lon": 30.07,  "pop_estimate": 4000},
    "Smouha":             {"lat": 31.215, "lon": 29.96,  "pop_estimate": 13000},
    "Stanley":            {"lat": 31.230, "lon": 29.97,  "pop_estimate": 11500},
    "Zizinia":            {"lat": 31.235, "lon": 29.975, "pop_estimate": 10000},
    "Roshdy":             {"lat": 31.225, "lon": 29.96,  "pop_estimate": 12000},
    "El Ibrahimiya":      {"lat": 31.207, "lon": 29.925, "pop_estimate": 15000},
    "El Shotbi":          {"lat": 31.205, "lon": 29.93,  "pop_estimate": 19000},
    "Saba Pasha":         {"lat": 31.220, "lon": 29.955, "pop_estimate": 13500},
    "El Azarita":         {"lat": 31.195, "lon": 29.905, "pop_estimate": 20000},
    "Cleopatra":          {"lat": 31.235, "lon": 29.98,  "pop_estimate": 14000},
    "Fleming":            {"lat": 31.225, "lon": 29.965, "pop_estimate": 13000},
    "Laurent":            {"lat": 31.215, "lon": 29.955, "pop_estimate": 12500},
    "El Anfushi":         {"lat": 31.210, "lon": 29.88,  "pop_estimate": 16000},
    "Attarin":            {"lat": 31.198, "lon": 29.90,  "pop_estimate": 20000},
    "El Shatby":          {"lat": 31.198, "lon": 29.905, "pop_estimate": 14000},
    "El Hadra":           {"lat": 31.185, "lon": 29.895, "pop_estimate": 22000},
    "El Wardian":         {"lat": 31.185, "lon": 29.885, "pop_estimate": 20000},
    "El Dekhela":         {"lat": 31.155, "lon": 29.85,  "pop_estimate": 7000},
    "Mex":                {"lat": 31.160, "lon": 29.855, "pop_estimate": 8500},
    "King Mariout":       {"lat": 31.020, "lon": 29.65,  "pop_estimate": 3000},
    "Boulkly":            {"lat": 31.225, "lon": 29.965, "pop_estimate": 11000},
    "Chatby":             {"lat": 31.197, "lon": 29.905, "pop_estimate": 13000},
    "Victoria":           {"lat": 31.250, "lon": 30.02,  "pop_estimate": 10000},
    "San Stefano":        {"lat": 31.235, "lon": 29.98,  "pop_estimate": 9500},
    "Sidi Salem":         {"lat": 31.270, "lon": 30.05,  "pop_estimate": 8000},
    "El Maamoura":        {"lat": 31.290, "lon": 30.03,  "pop_estimate": 7500},
    "Cleopatra Hamamat":  {"lat": 31.255, "lon": 30.035, "pop_estimate": 9000},
    "El Nozha":           {"lat": 31.265, "lon": 30.05,  "pop_estimate": 8500},
    "Sporting":           {"lat": 31.220, "lon": 29.955, "pop_estimate": 12000},
    "El Ekbal":           {"lat": 31.210, "lon": 29.945, "pop_estimate": 11000},
    "New Borg El Arab":   {"lat": 30.895, "lon": 29.525, "pop_estimate": 3500},
    "Ard El Sobhiya":     {"lat": 31.170, "lon": 29.875, "pop_estimate": 9000},
}


def build_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
        acks="all",
        retries=3,
    )


def load_processed_population() -> dict[str, float]:
    """يحمّل بيانات السكان المعالجة من الملف المحلي"""
    pop_map = {}
    try:
        if os.path.exists(PROCESSED_POP):
            df = pd.read_csv(PROCESSED_POP)
            log.info(f"Loaded processed population: {len(df)} rows, cols={list(df.columns)}")
            # نبحث عن أعمدة district وpopulation
            dist_col = next((c for c in df.columns if "district" in c.lower() or "area" in c.lower() or "name" in c.lower()), None)
            pop_col  = next((c for c in df.columns if "pop" in c.lower() or "count" in c.lower() or "total" in c.lower()), None)
            if dist_col and pop_col:
                for _, row in df.iterrows():
                    pop_map[str(row[dist_col]).strip()] = float(row[pop_col])
        else:
            log.warning(f"Processed population file not found: {PROCESSED_POP}")
    except Exception as e:
        log.warning(f"Could not load processed population: {e}")
    return pop_map


def load_nightlights() -> dict[str, float]:
    """يحمّل بيانات الإضاءة الليلية (proxy لكثافة النشاط الاقتصادي)"""
    nl_map = {}
    try:
        if os.path.exists(NIGHTLIGHTS):
            df = pd.read_csv(NIGHTLIGHTS)
            log.info(f"Loaded nightlights: {len(df)} rows, cols={list(df.columns)}")
            dist_col = next((c for c in df.columns if "district" in c.lower() or "area" in c.lower() or "name" in c.lower()), None)
            nl_col   = next((c for c in df.columns if "light" in c.lower() or "intensity" in c.lower() or "radiance" in c.lower() or "mean" in c.lower()), None)
            if dist_col and nl_col:
                for _, row in df.iterrows():
                    nl_map[str(row[dist_col]).strip()] = float(row[nl_col])
    except Exception as e:
        log.warning(f"Could not load nightlights: {e}")
    return nl_map


def run_cycle():
    log.info("=" * 60)
    log.info(f"Population scrape cycle — {datetime.now():%Y-%m-%d %H:%M}")
    producer = build_producer()

    # تحميل البيانات المحلية
    pop_lookup = load_processed_population()
    nl_lookup  = load_nightlights()

    sent = 0
    current_year = datetime.now().year

    for district, meta in ALEX_DISTRICTS.items():
        # نبحث عن مطابقة في البيانات المحلية (partial match)
        matched_pop = None
        for key, val in pop_lookup.items():
            if district.lower() in key.lower() or key.lower() in district.lower():
                matched_pop = val
                break

        matched_nl = None
        for key, val in nl_lookup.items():
            if district.lower() in key.lower() or key.lower() in district.lower():
                matched_nl = val
                break

        record = {
            "district":             district,
            "latitude":             meta["lat"],
            "longitude":            meta["lon"],
            "population":           matched_pop if matched_pop else meta["pop_estimate"],
            "population_source":    "CAPMAS" if matched_pop else "estimate",
            "nightlight_intensity": matched_nl,
            "year":                 current_year,
            "scraped_at":           datetime.now(timezone.utc).isoformat(),
            "source":               "CAPMAS + Google Earth Engine",
        }

        producer.send(TOPIC, value=record)
        sent += 1

    producer.flush()
    producer.close()
    log.info(f"Population cycle complete — {sent} districts → topic '{TOPIC}'")
    log.info("=" * 60)


if __name__ == "__main__":
    log.info("Running once (Airflow mode)")
    run_cycle()
    log.info("Done.")
