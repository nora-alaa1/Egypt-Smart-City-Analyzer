"""
SmartCity AI — CSV Data Loader

Loads the 5 real CSV files into memory for fast access by the API.
Mirrors the SQL Server tables from the original notebook.
"""

import os
import pandas as pd
from typing import Optional

_CSV_DIR = os.path.dirname(os.path.abspath(__file__))

# ── File paths ──
_AREA_CSV = os.path.join(_CSV_DIR, "Dim_Area(Area).csv")
_BTYPE_CSV = os.path.join(_CSV_DIR, "Dim_Business_Type 2(Business_Type).csv")
_PROP_CSV = os.path.join(_CSV_DIR, "Dim_Property(Property).csv")
_SCORE_CSV = os.path.join(_CSV_DIR, "Fact_Area_Business_Score(Area_Business_Score).csv")
_SUIT_CSV = os.path.join(_CSV_DIR, "Fact_Property_Suitability(Property_Suitability).csv")


class CSVData:
    """In-memory store for all CSV data."""

    def __init__(self):
        self.areas: pd.DataFrame = pd.DataFrame()
        self.business_types: pd.DataFrame = pd.DataFrame()
        self.properties: pd.DataFrame = pd.DataFrame()
        self.scores: pd.DataFrame = pd.DataFrame()
        self.suitability: pd.DataFrame = pd.DataFrame()

        self._loaded = False
        self._error: Optional[str] = None

    def load(self, reload: bool = False):
        if self._loaded and not reload:
            return
        try:
            self.areas = pd.read_csv(_AREA_CSV)
            self.business_types = pd.read_csv(_BTYPE_CSV)
            self.properties = pd.read_csv(_PROP_CSV)
            self.scores = pd.read_csv(_SCORE_CSV)
            self.suitability = pd.read_csv(_SUIT_CSV)

            # Clean / normalize
            for col in ["latitude", "longitude", "population"]:
                if col in self.areas.columns:
                    self.areas[col] = pd.to_numeric(self.areas[col], errors="coerce").fillna(0)

            self._loaded = True
            self._error = None
        except Exception as e:
            self._loaded = False
            self._error = str(e)

    @property
    def loaded(self) -> bool:
        return self._loaded

    @property
    def error(self) -> Optional[str]:
        return self._error

    # ── Helpers ──

    def get_areas(self) -> list[dict]:
        """Return all areas with clean dicts."""
        if not self._loaded:
            return []
        rows = self.areas.to_dict("records")
        for r in rows:
            r["area_id"] = int(r["area_id"])
            r["population"] = int(r.get("population", 0))
        return rows

    def get_area(self, area_id: int) -> Optional[dict]:
        for a in self.get_areas():
            if a["area_id"] == area_id:
                return a
        return None

    def get_categories(self) -> list[str]:
        if not self._loaded:
            return []
        return sorted(self.scores["category"].dropna().unique().tolist())

    def get_business_types(self) -> list[dict]:
        if not self._loaded:
            return []
        return self.business_types.to_dict("records")

    def get_scores_for_category(self, category: str) -> list[dict]:
        """Return area-business scores filtered by category."""
        if not self._loaded:
            return []
        subset = self.scores[self.scores["category"] == category]
        return subset.to_dict("records")

    def get_suitability_for_area(self, area_id: int) -> list[dict]:
        """Return property suitability records for a given area."""
        if not self._loaded:
            return []
        subset = self.suitability[self.suitability["area_id"] == area_id]
        return subset.to_dict("records")

    def get_properties_for_area(self, area_id: int) -> list[dict]:
        if not self._loaded:
            return []
        subset = self.properties[self.properties["area_id"] == area_id]
        return subset.to_dict("records")

    def count_competitors(self, area_id: int, category: str) -> int:
        """Count competitor properties in area for category."""
        if not self._loaded:
            return 0
        mask = (
            (self.suitability["area_id"] == area_id)
            & (self.suitability["category"] == category)
        )
        subset = self.suitability[mask]
        if subset.empty:
            return 0
        return int(subset["competitors_500m"].sum() // max(len(subset), 1))

    def get_area_metrics_for_category(self, category: str) -> list[dict]:
        """
        Return all areas with their suitability metrics for a given category.
        This is the primary pipeline data source.
        """
        if not self._loaded:
            return []

        scores = self.scores[self.scores["category"] == category].copy()
        if scores.empty:
            return []

        merged = scores.merge(
            self.areas[["area_id", "area_name", "population", "latitude", "longitude"]],
            on="area_id", how="left", suffixes=("", "_area")
        )
        
        # Prevent "cannot convert float NaN to integer"
        merged.fillna({
            "population": 0,
            "latitude": 0,
            "longitude": 0,
            "competitor_count": 0,
            "nearest_competitor_m": 0,
            "demand_index": 0,
            "market_saturation": 0,
            "suitability_score": 5.0,
            "recommended": False
        }, inplace=True)

        results = []
        for _, row in merged.iterrows():
            results.append({
                "area_id": int(row["area_id"]),
                "name": row.get("area_name_y") or row.get("area_name_x", ""),
                "population": int(row["population"]),
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "competitor_count": int(row["competitor_count"]),
                "nearest_competitor_m": float(row["nearest_competitor_m"]),
                "demand_index": float(row["demand_index"]),
                "market_saturation": float(row["market_saturation"]),
                "suitability_score": float(row["suitability_score"]),
                "recommended": bool(row["recommended"]),
            })

        return results


# ── Singleton ──
_csv_data = CSVData()


def get_csv_data() -> CSVData:
    """Get the singleton CSV data store (loads on first call)."""
    if not _csv_data.loaded:
        _csv_data.load()
    return _csv_data


def reload_csv_data():
    """Force reload from disk."""
    _csv_data.load(reload=True)
    return _csv_data
