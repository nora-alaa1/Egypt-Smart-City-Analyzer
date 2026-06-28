import os
import pandas as pd
import logging
from datetime import datetime
from sqlalchemy import inspect

from db import get_engine, get_db, init_db

logger = logging.getLogger("scheduler.data_updater")

_CSV_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CSV_FILES = {
    "areas":                 "Dim_Area(Area).csv",
    "business_types":        "Dim_Business_Type 2(Business_Type).csv",
    "properties":            "Dim_Property(Property).csv",
    "area_business_scores":  "Fact_Area_Business_Score(Area_Business_Score).csv",
    "property_suitability":  "Fact_Property_Suitability(Property_Suitability).csv",
}

TABLE_TARGETS = {
    "areas":                 "areas",
    "business_types":        "business_types",
    "properties":            "properties",
    "area_business_scores":  "area_business_scores",
    "property_suitability":  "property_suitability",
}

def load_csv(filename: str) -> pd.DataFrame:
    path = os.path.join(_CSV_DIR, filename)
    if not os.path.exists(path):
        logger.warning("CSV not found: %s", path)
        return pd.DataFrame()
    df = pd.read_csv(path)
    logger.info("Loaded %s — %d rows, %d cols", filename, len(df), len(df.columns))
    return df

def _clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df

def _sanitize_cols(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    if table_name == "areas":
        for col in ["latitude", "longitude", "population"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df

def update_data_pipeline():
    logger.info("=== DATA UPDATE START ===")
    engine = get_engine()
    init_db()

    for key, filename in CSV_FILES.items():
        target = TABLE_TARGETS[key]
        df = load_csv(filename)
        if df.empty:
            logger.warning("Skipping %s — no data", target)
            continue
        df = _clean_column_names(df)
        df = _sanitize_cols(df, target)
        try:
            df.to_sql(target, engine, if_exists="replace", index=False)
            logger.info("Replaced table '%s' — %d rows", target, len(df))
        except Exception as e:
            logger.error("Failed to write '%s': %s", target, e)

    logger.info("=== DATA UPDATE COMPLETE ===")
    return True
