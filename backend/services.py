"""
SmartCity AI — Data-fetching service layer.

All DB queries are isolated here so the API layer stays clean.
"""

import numpy as np
from sqlalchemy.orm import Session
from typing import Optional

from db import Area, Place, AreaMetric

# ── Model bundle (loaded once at import) ──
import pickle, os

_MODEL_PATH = os.path.join(os.path.dirname(__file__), "smartcity_model.pkl")

with open(_MODEL_PATH, "rb") as f:
    _bundle = pickle.load(f)

_clf = _bundle["classifier"]
_reg = _bundle["regressor"]
_le_tier = _bundle["le_tier"]
_le_cat = _bundle["le_category"]
_FEATURES = _bundle["features"]
_CATEGORIES: list[str] = _bundle["categories"]
_METRICS = _bundle["metrics"]


# ════════════════════════════════════════════════════════════
#  Queries
# ════════════════════════════════════════════════════════════

def get_all_areas(db: Session) -> list[dict]:
    """Return all areas with their latest metric row."""
    rows = (
        db.query(Area, AreaMetric)
        .outerjoin(AreaMetric, Area.id == AreaMetric.area_id)
        .order_by(Area.name)
        .all()
    )
    result = []
    for area, metric in rows:
        result.append({
            "id":          area.id,
            "name":        area.name,
            "latitude":    area.latitude,
            "longitude":   area.longitude,
            "population":  metric.population if metric else 0,
            "avg_rent":    metric.avg_rent if metric else 0.0,
            "traffic_score":       metric.traffic_score if metric else 0.0,
            "accessibility_score": metric.accessibility_score if metric else 0.0,
            "competitor_count":    metric.competitor_count if metric else 0,
        })
    return result


def get_area_by_id(db: Session, area_id: int) -> Optional[dict]:
    """Fetch a single area + metrics."""
    row = (
        db.query(Area, AreaMetric)
        .outerjoin(AreaMetric, Area.id == AreaMetric.area_id)
        .filter(Area.id == area_id)
        .first()
    )
    if not row:
        return None
    area, metric = row
    return {
        "id":          area.id,
        "name":        area.name,
        "latitude":    area.latitude,
        "longitude":   area.longitude,
        "population":  metric.population if metric else 0,
        "avg_rent":    metric.avg_rent if metric else 0.0,
        "traffic_score":       metric.traffic_score if metric else 0.0,
        "accessibility_score": metric.accessibility_score if metric else 0.0,
        "competitor_count":    metric.competitor_count if metric else 0,
    }


def count_competitors(db: Session, area_id: int, category: str) -> int:
    """Count places in a given area that match the business category."""
    return (
        db.query(Place)
        .filter(Place.area_id == area_id, Place.category == category)
        .count()
    )


def get_places_by_area(db: Session, area_id: int) -> list[dict]:
    """Get all places for a given area."""
    rows = (
        db.query(Place)
        .filter(Place.area_id == area_id)
        .all()
    )
    return [
        {
            "id": p.id,
            "name": p.name,
            "category": p.category,
            "latitude": p.latitude,
            "longitude": p.longitude,
        }
        for p in rows
    ]


def get_categories_from_db(db: Session) -> list[str]:
    """Return distinct place categories from the DB."""
    rows = db.query(Place.category).distinct().all()
    cats = [r[0] for r in rows if r[0]]
    return sorted(set(cats)) if cats else _CATEGORIES


# ════════════════════════════════════════════════════════════
#  Feature assembly + AI prediction
# ════════════════════════════════════════════════════════════

def assemble_features(
    area_sqm: float,
    rent_egp: float,
    population: int,
    competitor_count: int,
    traffic_score: float,
    accessibility_score: float,
    category: str,
) -> np.ndarray:
    """
    Build the 7-feature vector the model expects:
      [area_sqm, rent_per_sqm, affordability, comp_500m, comp_1km,
       population, category_enc]

    The model was trained with approximate competitor radii from
    synthetic data; we map total competitor_count → comp_500m estimate
    and use traffic/accessibility as additional signals.
    """
    if category not in _CATEGORIES:
        raise ValueError(
            f"Unknown category '{category}'. Available: {_CATEGORIES}"
        )

    rent_per_sqm = rent_egp / area_sqm if area_sqm > 0 else 500
    affordability = max(0.2, min(2.0, 1 - (rent_per_sqm / 450 - 1) * 0.5))

    # Distribute competitor count into rough radii bins
    comp_500m = int(round(competitor_count * 0.35))
    comp_1km  = int(round(competitor_count * 0.65))

    cat_enc = _le_cat.transform([category])[0]

    return np.array([[area_sqm, rent_per_sqm, affordability,
                      comp_500m, comp_1km, population, cat_enc]])


def predict_suitability(features: np.ndarray) -> tuple[float, str, bool]:
    """
    Run the model on a feature vector.
    Returns (suitability_score, tier_label, recommended).
    """
    score = float(_reg.predict(features)[0])
    score = round(min(10.0, max(1.0, score)), 2)
    tier_label = _le_tier.inverse_transform([_clf.predict(features)[0]])[0]
    return score, tier_label, score >= 6.0


def generate_reason(
    score: float,
    population: int,
    avg_rent: float,
    competitor_count: int,
    traffic_score: float,
    accessibility_score: float,
) -> str:
    """Human-readable explanation of the score."""
    parts = []
    if population > 30000:
        parts.append("high population")
    elif population > 20000:
        parts.append("moderate population")
    else:
        parts.append("lower population")

    if avg_rent < 200:
        parts.append("low rent")
    elif avg_rent < 350:
        parts.append("moderate rent")
    else:
        parts.append("higher rent")

    if competitor_count < 3:
        parts.append("low competition")
    elif competitor_count < 6:
        parts.append("moderate competition")
    else:
        parts.append("high competition")

    if traffic_score >= 7:
        parts.append("good traffic flow")
    if accessibility_score >= 7:
        parts.append("high accessibility")

    return ", ".join(parts)


def run_full_analysis(
    db: Session,
    category: str,
    max_rent: Optional[float] = None,
    min_population: int = 0,
    area_sqm_default: float = 120.0,
) -> list[dict]:
    """
    Full pipeline:
      1. Fetch all areas + metrics from DB
      2. Count competitors per area (filtered by category)
      3. Assemble feature vectors
      4. Run AI predictions
      5. Return ranked results
    """
    areas = get_all_areas(db)
    results = []

    for area in areas:
        if area["population"] < min_population:
            continue

        comp_count = count_competitors(db, area["id"], category)
        rent = area["avg_rent"] if area["avg_rent"] > 0 else 300.0

        if max_rent is not None and rent > max_rent:
            continue

        features = assemble_features(
            area_sqm=area_sqm_default,
            rent_egp=rent * area_sqm_default,
            population=area["population"],
            competitor_count=comp_count,
            traffic_score=area["traffic_score"],
            accessibility_score=area["accessibility_score"],
            category=category,
        )

        score, tier_label, recommended = predict_suitability(features)

        reason = generate_reason(
            score, area["population"], rent, comp_count,
            area["traffic_score"], area["accessibility_score"],
        )

        results.append({
            "area_id":           area["id"],
            "name":              area["name"],
            "population":        area["population"],
            "avg_rent":          round(rent, 1),
            "competitor_count":  comp_count,
            "traffic_score":     area["traffic_score"],
            "accessibility_score": area["accessibility_score"],
            "suitability_score": score,
            "tier":              tier_label,
            "recommended":       recommended,
            "reason":            reason,
        })

    results.sort(key=lambda r: -r["suitability_score"])
    return results


# ── Expose model info ──

def get_model_categories() -> list[str]:
    return _CATEGORIES

def get_model_metrics() -> dict:
    return _METRICS
