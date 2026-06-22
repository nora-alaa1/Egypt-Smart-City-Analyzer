"""
Bronze Layer Loader — PostgreSQL
==================================
يراقب مجلد output_all ويلود كل ملف جديد لـ PostgreSQL.

Tables في schema bronze:
    rent_commercial, cafes, gyms, restaurants, bakeries,
    hotels, hospitals, banks, clothing, supermarkets, sweets,
    pharmacies, schools, centers, population,
    traffic_nodes, traffic_edges
"""

import json
import logging
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# ─── Logging ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [BRONZE-PG] %(levelname)s — %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)

# ─── Config ────────────────────────────────────────────────────
PG_HOST     = os.environ.get("PG_HOST",     "postgres")
PG_PORT     = int(os.environ.get("PG_PORT", "5432"))
PG_DB       = os.environ.get("PG_DB",       "smartcity")
PG_USER     = os.environ.get("PG_USER",     "smartcity")
PG_PASSWORD = os.environ.get("PG_PASSWORD", "smartcity123")

OUTPUT_DIR    = Path(os.environ.get("OUTPUT_DIR", "/app/output"))
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL_SEC", "30"))
ONE_SHOT = os.environ.get("ONE_SHOT", "false").lower() == "true"

FILE_PATTERN = re.compile(r"^([a-z0-9_]+?)_(\d{8})(\.[a-z]+)$")


# ─── Dataset name cleanup ───────────────────────────────────────
def get_dataset(raw_name: str) -> str:
    name = re.sub(r"_cycle\d+", "", raw_name)
    name = re.sub(r"_alexandria$", "", name)
    name = re.sub(r"_full$",       "", name)
    return name


# ─── DB Connection ─────────────────────────────────────────────
def get_conn():
    return psycopg2.connect(
        host=PG_HOST, port=PG_PORT,
        dbname=PG_DB, user=PG_USER, password=PG_PASSWORD
    )

def wait_for_postgres(retries=30, delay=5):
    for i in range(1, retries + 1):
        try:
            conn = get_conn()
            conn.close()
            log.info("Connected to PostgreSQL ✓")
            return
        except Exception as e:
            log.warning(f"PostgreSQL not ready ({i}/{retries}): {e}")
            time.sleep(delay)
    log.error("Could not connect to PostgreSQL — exiting.")
    sys.exit(1)


# ─── File Reading ──────────────────────────────────────────────
def read_file(filepath: Path, dataset: str) -> pd.DataFrame | None:
    suffix = filepath.suffix.lower()
    try:
        if suffix == ".xlsx":
            df = pd.read_excel(filepath, engine="openpyxl")

            # ── Detect title-row pattern (education files) ──────────
            # If most header columns are NaN-like and first cell looks
            # like a title string, re-read with header=1
            col_names = [str(c) for c in df.columns]
            nan_cols = sum(1 for c in col_names if c.startswith("Unnamed"))
            if nan_cols >= len(col_names) // 2 and len(col_names) > 2:
                log.info(f"  Title-row detected in {filepath.name} — re-reading with header=1")
                df = pd.read_excel(filepath, engine="openpyxl", header=1)

            summary_labels = {
                "total records", "avg latitude", "avg rent (egp)",
                "avg area (m²)", "scraped at", "avg longitude",
                "source", "scraped at",
            }
            mask = df.iloc[:, 0].astype(str).str.strip().str.lower().isin(summary_labels)
            df = df[~mask].dropna(how="all").reset_index(drop=True)
        elif suffix == ".csv":
            df = pd.read_csv(filepath, encoding="utf-8-sig")
        else:
            return None

        log.info(f"Read {len(df)} rows ← {filepath.name}")
        return df
    except Exception as e:
        log.error(f"Failed to read {filepath.name}: {e}")
        return None


# ─── Loaders per dataset ───────────────────────────────────────

def load_osm_places(conn, table: str, df: pd.DataFrame, source: str):
    """cafes, gyms, restaurants, bakeries, hotels, hospitals, banks, clothing, supermarkets, sweets"""
    rows = []
    for _, r in df.iterrows():
        name = r.get("name") if pd.notna(r.get("name", None)) else None
        try:
            lat = float(r.get("latitude",  0))
            lon = float(r.get("longitude", 0))
        except (ValueError, TypeError):
            continue
        rows.append((name, lat, lon, source))

    sql = f"""
        INSERT INTO bronze.{table} (name, latitude, longitude, _source_file)
        VALUES %s
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, rows)
    conn.commit()
    return len(rows)


def load_rent(conn, df: pd.DataFrame, source: str):
    rows = []
    for _, r in df.iterrows():
        try:
            area = int(r.get("area(m²)", 0))
            rent = int(r.get("rent(EGP)", 0))
            loc  = str(r.get("location_en", "")).strip() or None
        except (ValueError, TypeError):
            continue
        rows.append((area, rent, loc, source))

    sql = """
        INSERT INTO bronze.rent_commercial (area_m2, rent_egp, location_en, _source_file)
        VALUES %s
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, rows)
    conn.commit()
    return len(rows)


def load_pharmacies(conn, df: pd.DataFrame, source: str):
    rows = []
    for _, r in df.iterrows():
        name    = str(r.get("name",    "")).strip() or None
        address = str(r.get("address", "")).strip() or None
        phone   = str(r.get("phone",   "")).strip() if pd.notna(r.get("phone", None)) else None
        src     = str(r.get("source_file", "")).strip() or None
        url     = str(r.get("web_scraper_start_url", "")).strip() or None
        rows.append((name, address, phone, src, url, source))

    sql = """
        INSERT INTO bronze.pharmacies
            (name, address, phone, source_file, web_scraper_start_url, _source_file)
        VALUES %s
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, rows)
    conn.commit()
    return len(rows)


def load_education(conn, table: str, df: pd.DataFrame, source: str):
    """schools, centers"""
    rows = []
    for _, r in df.iterrows():
        name = str(r.get("name", "")).strip() or None
        typ  = str(r.get("type", "")).strip() if "type" in df.columns else None
        try:
            lat = float(r.get("latitude",  0))
            lon = float(r.get("longitude", 0))
        except (ValueError, TypeError):
            lat, lon = None, None
        rows.append((name, typ, lat, lon, source))

    sql = f"""
        INSERT INTO bronze.{table} (name, type, latitude, longitude, _source_file)
        VALUES %s
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, rows)
    conn.commit()
    return len(rows)


def load_population(conn, df: pd.DataFrame, source: str):
    rows = []
    for _, r in df.iterrows():
        data = json.dumps(r.dropna().to_dict(), ensure_ascii=False, default=str)
        rows.append((data, source))

    sql = """
        INSERT INTO bronze.population (data, _source_file)
        VALUES %s
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, rows)
    conn.commit()
    return len(rows)


def load_traffic_nodes(conn, df: pd.DataFrame, source: str):
    rows = []
    for _, r in df.iterrows():
        try:
            osmid = int(r.get("osmid", 0)) if pd.notna(r.get("osmid", None)) else None
            y     = float(r.get("y", 0))   if pd.notna(r.get("y",    None)) else None
            x     = float(r.get("x", 0))   if pd.notna(r.get("x",    None)) else None
            sc    = int(r.get("street_count", 0)) if pd.notna(r.get("street_count", None)) else None
        except (ValueError, TypeError):
            osmid = y = x = sc = None

        extra = {k: v for k, v in r.items()
                 if k not in ("osmid", "y", "x", "street_count") and pd.notna(v)}
        data = json.dumps(extra, ensure_ascii=False, default=str)
        rows.append((osmid, y, x, sc, data, source))

    sql = """
        INSERT INTO bronze.traffic_nodes (osmid, y, x, street_count, data, _source_file)
        VALUES %s
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, rows)
    conn.commit()
    return len(rows)


def load_traffic_edges(conn, df: pd.DataFrame, source: str):
    # drop unnamed columns
    df = df.loc[:, ~df.columns.str.match(r"^Unnamed")]

    rows = []
    for _, r in df.iterrows():
        try:
            u   = int(r.get("u",   0)) if pd.notna(r.get("u",   None)) else None
            v   = int(r.get("v",   0)) if pd.notna(r.get("v",   None)) else None
            key = int(r.get("key", 0)) if pd.notna(r.get("key", None)) else None
            lng = float(r.get("length", 0)) if pd.notna(r.get("length", None)) else None
        except (ValueError, TypeError):
            u = v = key = lng = None

        extra = {k: val for k, val in r.items()
                 if k not in ("u", "v", "key", "length") and pd.notna(val)}
        data = json.dumps(extra, ensure_ascii=False, default=str)
        rows.append((u, v, key, lng, data, source))

    sql = """
        INSERT INTO bronze.traffic_edges (u, v, key_col, length, data, _source_file)
        VALUES %s
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, rows)
    conn.commit()
    return len(rows)


# ─── Dispatch ──────────────────────────────────────────────────
OSM_PLACES = {
    "cafes", "gyms", "restaurants", "bakeries",
    "hotels", "hospitals", "banks", "clothing",
    "supermarkets", "sweets"
}


def log_ingestion(conn, filename, dataset, row_count, status, error_msg=None):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO bronze.ingestion_log (filename, dataset, row_count, status, error_msg)
            VALUES (%s, %s, %s, %s, %s)
        """, (filename, dataset, row_count, status, error_msg))
    conn.commit()


def process_file(filepath: Path) -> bool:
    match = FILE_PATTERN.match(filepath.name)
    if not match:
        return False

    raw_name = match.group(1)
    dataset  = get_dataset(raw_name)
    source   = filepath.name

    log.info(f"Processing: {filepath.name} → dataset='{dataset}'")

    df = read_file(filepath, dataset)
    if df is None or df.empty:
        log.warning(f"Empty: {filepath.name}")
        return False

    conn = get_conn()
    try:
        if dataset in OSM_PLACES:
            count = load_osm_places(conn, dataset, df, source)
        elif dataset == "rent_commercial":
            count = load_rent(conn, df, source)
        elif dataset == "pharmacies":
            count = load_pharmacies(conn, df, source)
        elif dataset in ("schools", "centers"):
            count = load_education(conn, dataset, df, source)
        elif dataset == "population":
            count = load_population(conn, df, source)
        elif dataset == "traffic_nodes":
            count = load_traffic_nodes(conn, df, source)
        elif dataset == "traffic_edges":
            count = load_traffic_edges(conn, df, source)
        else:
            log.warning(f"Unknown dataset '{dataset}' — skipping")
            conn.close()
            return False

        log_ingestion(conn, source, dataset, count, "success")
        log.info(f"✓ Loaded {count} rows → bronze.{dataset}")
        conn.close()
        return True

    except Exception as e:
        log.error(f"✗ Failed {filepath.name}: {e}")
        try:
            conn.rollback()
            log_ingestion(conn, source, dataset, 0, "error", str(e))
        except Exception:
            pass
        conn.close()
        return False


# ─── Main Loop ─────────────────────────────────────────────────
def scan_and_load(processed: set[str]):
    if not OUTPUT_DIR.exists():
        log.warning(f"OUTPUT_DIR not found: {OUTPUT_DIR}")
        return

    # استعلم من الـ DB عشان تاخد أحدث state دايمًا
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT filename FROM bronze.ingestion_log WHERE status='success'"
            )
            for row in cur.fetchall():
                processed.add(row[0])
        conn.close()
    except Exception as e:
        log.warning(f"Could not restore processed list from DB: {e}")
        return  # وقف — متلودش حاجة لو الـ DB مش شغال

    supported = {".xlsx", ".csv"}
    files = [
        f for f in OUTPUT_DIR.iterdir()
        if f.suffix.lower() in supported and f.name not in processed
    ]

    if not files:
        log.debug("No new files.")
        return

    log.info(f"Found {len(files)} new file(s)...")
    for filepath in sorted(files):
        success = process_file(filepath)
        if success:
            processed.add(filepath.name)


def main():
    log.info("=" * 55)
    log.info("  SmartCity Bronze Loader — PostgreSQL")
    log.info(f"  DB   : {PG_HOST}:{PG_PORT}/{PG_DB}")
    log.info(f"  Watch: {OUTPUT_DIR}")
    log.info(f"  Poll : every {POLL_INTERVAL}s")
    log.info("=" * 55)

    wait_for_postgres()

    processed: set[str] = set()
    while True:
        scan_and_load(processed)
        if ONE_SHOT:
            log.info("ONE_SHOT done.")
            break
        log.info(f"Sleeping {POLL_INTERVAL}s ... (loaded: {len(processed)} files)")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
