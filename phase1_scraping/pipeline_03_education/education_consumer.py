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

HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
HEADER_FONT = Font(name="Arial", bold=True, color="FFFFFF", size=11)
DATA_FONT   = Font(name="Arial", size=10)
EVEN_FILL   = PatternFill("solid", fgColor="D9E1F2")
THIN        = Border(
    left=Side(style="thin"), right=Side(style="thin"),
    top=Side(style="thin"),  bottom=Side(style="thin"),
)

COL_WIDTHS = {
    "name": 40, "type": 22, "edu_level": 18,
    "latitude": 13, "longitude": 13, "operator": 30, "capacity": 12,
}


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


def write_excel(df: pd.DataFrame, path: str, sheet_name: str, title: str):
    headers = df.columns.tolist()
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name

    # Title row
    ws.merge_cells(f"A1:{chr(64+len(headers))}1")
    title_cell = ws["A1"]
    title_cell.value = title
    title_cell.font  = Font(name="Arial", bold=True, color="FFFFFF", size=13)
    title_cell.fill  = PatternFill("solid", fgColor="0D3349")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 28

    # Header row
    for ci, h in enumerate(headers, 1):
        c = ws.cell(row=2, column=ci, value=h)
        c.font, c.fill = HEADER_FONT, HEADER_FILL
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = THIN
        col_letter = ws.cell(row=2, column=ci).column_letter
        ws.column_dimensions[col_letter].width = COL_WIDTHS.get(h, 18)
    ws.row_dimensions[2].height = 20

    # Data rows
    for ri, row in df.iterrows():
        er   = ri + 3
        fill = EVEN_FILL if ri % 2 == 0 else PatternFill()
        for ci, col in enumerate(headers, 1):
            val = row[col]
            if pd.isna(val):
                val = None
            c = ws.cell(row=er, column=ci, value=val)
            c.font, c.fill, c.border = DATA_FONT, fill, THIN
            c.alignment = Alignment(
                horizontal="left" if ci == 1 else "center",
                vertical="center",
            )

    # Summary
    last = len(df) + 2
    sr   = last + 2
    for label, val in [
        ("Total Records", f"=COUNTA(A3:A{last})"),
        ("Scraped At",    datetime.now().strftime("%Y-%m-%d")),
        ("Source",        "OpenStreetMap / Overpass API"),
    ]:
        r = sr
        sr += 1
        ws.cell(row=r, column=1, value=label).font = Font(name="Arial", bold=True, size=10)
        ws.cell(row=r, column=2, value=val)

    wb.save(path)
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
