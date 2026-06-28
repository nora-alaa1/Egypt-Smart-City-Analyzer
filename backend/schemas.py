"""
SmartCity AI — Pydantic schemas for DB-backed endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional


# ── DB-backed response schemas ──

class AreaOut(BaseModel):
    id: int
    name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    population: Optional[int] = None
    avg_rent: Optional[float] = None

    class Config:
        from_attributes = True


class PlaceOut(BaseModel):
    id: int
    name: str
    category: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    area_id: Optional[int] = None
    area_name: Optional[str] = None

    class Config:
        from_attributes = True


class AreaMetricOut(BaseModel):
    area_id: int
    area_name: str
    population: int
    avg_rent: float
    competitor_count: int
    traffic_score: float
    accessibility_score: float

    class Config:
        from_attributes = True


# ── Analysis request / response ──

class AnalysisRunRequest(BaseModel):
    category: str = Field(..., description="Business category e.g. 'Food & Beverage'")
    max_rent: Optional[float] = Field(None, description="Max monthly rent budget (EGP)")
    min_population: Optional[int] = Field(0, description="Minimum population filter")
    top_n: int = Field(12, ge=1, le=50, description="Number of top areas to return")


class AreaScore(BaseModel):
    area_id: int
    name: str
    population: int
    avg_rent: float
    competitor_count: int
    traffic_score: float
    accessibility_score: float
    suitability_score: float
    tier: str
    recommended: bool
    reason: str


class AnalysisRunResponse(BaseModel):
    category: str
    total_areas_evaluated: int
    best_area: Optional[AreaScore] = None
    top_areas: list[AreaScore]


# ── PowerBI-friendly export ──

class PowerBIExportRequest(BaseModel):
    category: Optional[str] = None
    format: str = "json"   # json | csv
