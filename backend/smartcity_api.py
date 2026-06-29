"""
SmartCity AI — FastAPI Server (CSV + DB backed)

Reads real Alexandria data from CSV files → assembles features →
runs AI model. Falls back to synthetic data when CSVs are missing.
Also supports PostgreSQL via SQLAlchemy when DATABASE_URL is set.
"""

import os
import csv
import io
import pickle
import numpy as np
import pandas as pd
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# ── CSV data loader (primary source) ──
from csv_loader import get_csv_data, reload_csv_data

# ── Database (optional, for PostgreSQL) ──
_DB_AVAILABLE = False
try:
    from db import get_db, init_db, get_engine, Area, Place, AreaMetric, PrecomputedRecommendation, Alert
    from sqlalchemy.orm import Session
    from sqlalchemy import text
    _DB_AVAILABLE = True
except Exception:
    get_db = None
    init_db = lambda: None

# ══════════════════════════════════════════════════════════════
#  Load AI model bundle
# ══════════════════════════════════════════════════════════════

_MODEL_PATH = os.path.join(os.path.dirname(__file__), "smartcity_model.pkl")
try:
    with open(_MODEL_PATH, "rb") as f:
        _bundle = pickle.load(f)
except FileNotFoundError:
    raise RuntimeError("smartcity_model.pkl not found. Run train_model.py first.")

_clf = _bundle["classifier"]
_reg = _bundle["regressor"]
_le_tier = _bundle["le_tier"]
_le_cat = _bundle["le_category"]
_FEATURES: list[str] = _bundle["features"]
_CATEGORIES: list[str] = _bundle["categories"]
_METRICS: dict = _bundle["metrics"]

# ── Fallback synthetic data ──
_FALLBACK_AREAS: dict[int, tuple[str, int]] = _bundle["areas"]
_TRAINING_DATA: pd.DataFrame = _bundle.get("training_data", pd.DataFrame())
_CATEGORY_AREA_LOOKUP: dict[str, dict] = {}
if not _TRAINING_DATA.empty:
    for cat in _CATEGORIES:
        subset = _TRAINING_DATA[_TRAINING_DATA["category"] == cat]
        if not subset.empty:
            _CATEGORY_AREA_LOOKUP[cat] = subset.groupby("area_id").agg({
                "rent_per_sqm": "mean", "comp_500m": "mean", "comp_1km": "mean",
            }).to_dict("index")

# ── Frontend 1-12 ID → CSV area_id mapping ──
_FRONTEND_TO_CSV: dict[int, int] = {
    1: 46, 2: 44, 3: 49, 4: 34, 5: 11,
    6: 48, 7: 40, 8: 26, 9: 21, 10: 38,
    11: 31, 12: 5,
}

_BUSINESS_TYPES: dict = _bundle["business_types"]

# ── CSV categories override ──
csv_data = get_csv_data()
if csv_data.loaded:
    _CATEGORIES = csv_data.get_categories()

# ══════════════════════════════════════════════════════════════
#  App setup
# ══════════════════════════════════════════════════════════════

app = FastAPI(
    title="Egypt Smart City Analyzer — AI API",
    description="AI-powered urban analysis for Alexandria. Reads real CSV data → AI model → ranked insights.",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_start():
    try:
        csv_data = get_csv_data()
        if csv_data.loaded:
            print(f"[startup] CSV loaded: {len(csv_data.get_areas())} areas, "
                  f"{len(csv_data.get_categories())} categories, "
                  f"{len(csv_data.scores)} scores, "
                  f"{len(csv_data.suitability)} properties")
        else:
            print(f"[startup] CSV not loaded ({csv_data.error}) — using fallback data.")
    except Exception as e:
        print(f"[startup] CSV load skipped ({e}).")


# ══════════════════════════════════════════════════════════════
#  Request schemas
# ══════════════════════════════════════════════════════════════

class PredictRequest(BaseModel):
    area_sqm: float = Field(..., gt=0)
    rent_egp: float = Field(..., gt=0)
    category: str = Field(...)
    area_id: Optional[int] = None
    comp_500m: int = Field(0, ge=0)
    comp_1km: int = Field(0, ge=0)


class RecommendRequest(BaseModel):
    category: str = Field(...)
    max_rent: float = Field(..., gt=0)
    area_sqm: float = Field(..., gt=0)
    top_n: int = Field(10, ge=1, le=50)


class AnalyzeRequest(BaseModel):
    area_id: int = Field(...)
    category: str = Field(...)
    rent_budget: float = Field(..., gt=0)
    area_sqm: float = Field(..., gt=0)
    min_population: Optional[int] = Field(0)


class AnalysisRunRequest(BaseModel):
    category: str = Field(..., description="Business category")
    max_rent: Optional[float] = Field(None, description="Max monthly rent (EGP)")
    min_population: int = Field(0, description="Minimum population filter")
    top_n: int = Field(12, ge=1, le=50)


# ══════════════════════════════════════════════════════════════
#  Prediction helpers
# ══════════════════════════════════════════════════════════════

def _predict_single(area_sqm, rent_egp, category, area_id=None,
                    comp_500m=0, comp_1km=0, population_override=None):
    if category not in _CATEGORIES:
        raise HTTPException(400, f"Unknown category '{category}'. Available: {_CATEGORIES}")

    population = population_override or 10000
    area_name_val = "Unknown"
    if area_id and area_id in _FALLBACK_AREAS:
        population = _FALLBACK_AREAS[area_id][1]
        area_name_val = _FALLBACK_AREAS[area_id][0]
    # Try CSV data for real name/pop
    csv_data = get_csv_data()
    if csv_data.loaded:
        area_info = csv_data.get_area(area_id) if area_id else None
        if area_info:
            population = int(area_info.get("population", population))
            area_name_val = area_info.get("area_name", area_name_val)

    rent_per_sqm = rent_egp / area_sqm if area_sqm > 0 else 500
    affordability = max(0.2, min(2.0, 1 - (rent_per_sqm / 450 - 1) * 0.5))
    try:
        cat_enc = _le_cat.transform([category])[0]
    except ValueError:
        cat_enc = 0
    x = np.array([[area_sqm, rent_per_sqm, affordability,
                   comp_500m, comp_1km, population, cat_enc]])

    score = float(_reg.predict(x)[0])
    score = round(min(10.0, max(1.0, score)), 2)
    tier_label = _le_tier.inverse_transform([_clf.predict(x)[0]])[0]

    return {
        "area_sqm": area_sqm, "rent_egp": rent_egp,
        "rent_per_sqm": round(rent_per_sqm, 1),
        "category": category, "area_name": area_name_val,
        "population": population,
        "competitors_500m": comp_500m, "competitors_1km": comp_1km,
        "suitability_score": score, "tier": tier_label,
        "recommended": score >= 6.0,
    }


def _generate_reason(score, pop, rent, comp_count, traffic, access):
    parts = []
    if pop > 30000: parts.append("high population")
    elif pop > 20000: parts.append("moderate population")
    else: parts.append("lower population")
    if rent < 200: parts.append("low rent")
    elif rent < 350: parts.append("moderate rent")
    else: parts.append("higher rent")
    if comp_count < 3: parts.append("low competition")
    elif comp_count < 6: parts.append("moderate competition")
    else: parts.append("high competition")
    if traffic >= 7: parts.append("good traffic")
    if access >= 7: parts.append("high accessibility")
    return ", ".join(parts)


# ── Profit / ROI estimation ──

_CATEGORY_PARAMS = {
    "Food & Beverage":       {"penetration_pct": 3.5, "avg_transaction": 180,  "fit_out_per_sqm": 8000,  "labor_pct": 0.32},
    "Retail":                {"penetration_pct": 2.0, "avg_transaction": 350,  "fit_out_per_sqm": 5000,  "labor_pct": 0.25},
    "Healthcare":            {"penetration_pct": 1.5, "avg_transaction": 250,  "fit_out_per_sqm": 12000, "labor_pct": 0.35},
    "Education":             {"penetration_pct": 2.0, "avg_transaction": 400,  "fit_out_per_sqm": 6000,  "labor_pct": 0.30},
    "Fitness":               {"penetration_pct": 1.2, "avg_transaction": 500,  "fit_out_per_sqm": 10000, "labor_pct": 0.28},
    "Entertainment":         {"penetration_pct": 1.8, "avg_transaction": 200,  "fit_out_per_sqm": 7500,  "labor_pct": 0.30},
    "Health & Fitness":      {"penetration_pct": 1.2, "avg_transaction": 500,  "fit_out_per_sqm": 10000, "labor_pct": 0.28},
    "Financial Services":    {"penetration_pct": 0.8, "avg_transaction": 600,  "fit_out_per_sqm": 15000, "labor_pct": 0.30},
    "Tourism & Hospitality": {"penetration_pct": 2.5, "avg_transaction": 350,  "fit_out_per_sqm": 12000, "labor_pct": 0.35},
}


def _estimate_profit(population: int, avg_rent: float, competitor_count: int,
                     category: str, area_sqm: float = 120.0) -> dict:
    """Estimate monthly revenue, costs, profit and payback period."""
    params = _CATEGORY_PARAMS.get(category, _CATEGORY_PARAMS["Retail"])

    penetration = params["penetration_pct"]
    # Reduce penetration for high-competition areas
    if competitor_count > 8:
        penetration *= 0.7
    elif competitor_count > 4:
        penetration *= 0.85

    avg_transaction = params["avg_transaction"]
    est_monthly_customers = int(population * penetration / 100)
    monthly_revenue = est_monthly_customers * avg_transaction

    monthly_rent = avg_rent * area_sqm
    monthly_labor = monthly_revenue * params["labor_pct"]
    monthly_utilities = monthly_revenue * 0.08
    monthly_marketing = monthly_revenue * 0.05
    monthly_other = monthly_revenue * 0.03
    monthly_costs = monthly_rent + monthly_labor + monthly_utilities + monthly_marketing + monthly_other

    monthly_profit = monthly_revenue - monthly_costs
    profit_margin_pct = round((monthly_profit / monthly_revenue) * 100, 1) if monthly_revenue > 0 else 0

    fit_out_cost = params["fit_out_per_sqm"] * area_sqm
    initial_investment = int(fit_out_cost + monthly_rent * 6)

    payback_months = round(initial_investment / monthly_profit, 1) if monthly_profit > 0 else 999

    return {
        "estimated_monthly_customers": est_monthly_customers,
        "avg_transaction_egp": avg_transaction,
        "estimated_monthly_revenue": int(monthly_revenue),
        "monthly_rent": int(monthly_rent),
        "monthly_labor": int(monthly_labor),
        "monthly_utilities": int(monthly_utilities),
        "monthly_marketing": int(monthly_marketing),
        "total_monthly_costs": int(monthly_costs),
        "estimated_monthly_profit": int(monthly_profit),
        "profit_margin_pct": profit_margin_pct,
        "initial_investment_egp": initial_investment,
        "estimated_payback_months": payback_months,
        "penetration_rate_pct": round(penetration, 1),
    }


# ══════════════════════════════════════════════════════════════
#  CSV-based pipeline (primary)
# ══════════════════════════════════════════════════════════════

def _run_csv_pipeline(category: str, min_pop: int = 0,
                       max_rent: Optional[float] = None,
                       area_sqm_default: float = 120.0) -> list[dict]:
    """Full analysis using real CSV data."""
    csv_data = get_csv_data()
    if not csv_data.loaded:
        raise HTTPException(503, "CSV data not loaded")

    # Get area metrics for this category from the pre-scored data
    area_metrics = csv_data.get_area_metrics_for_category(category)
    results = []

    for am in area_metrics:
        if min_pop and am["population"] < min_pop:
            continue
        if max_rent and am.get("avg_rent", 0) > max_rent:
            continue

        # Use the pre-computed suitability score directly as a baseline
        base_score = am["suitability_score"]

        # Count competitors from suitability table
        comp_count = csv_data.count_competitors(am["area_id"], category)

        traffic = 6.0
        demand = am.get("demand_index", 5000)
        if demand > 6000: traffic = 8.0
        elif demand > 4000: traffic = 6.5
        elif demand > 2000: traffic = 5.0
        else: traffic = 4.0

        accessibility = 6.0
        market_sat = am.get("market_saturation", 0)
        if market_sat < 10: accessibility = 8.0
        elif market_sat < 30: accessibility = 6.5
        else: accessibility = 5.0

        # Enhance with AI model prediction
        rent_est = am.get("avg_rent", 300) or 300
        rent_egp = rent_est * area_sqm_default
        rent_per_sqm = rent_est
        affordability = max(0.2, min(2.0, 1 - (rent_per_sqm / 450 - 1) * 0.5))
        try:
            cat_enc = _le_cat.transform([category])[0]
        except ValueError:
            cat_enc = 0
        comp_500m = int(round(comp_count * 0.35))
        comp_1km = int(round(comp_count * 0.65))

        x = np.array([[area_sqm_default, rent_per_sqm, affordability,
                       comp_500m, comp_1km, am["population"], cat_enc]])
        ai_score = float(_reg.predict(x)[0])
        ai_score = round(min(10.0, max(1.0, ai_score)), 2)

        # Blend CSV score + AI score
        final_score = round((base_score * 0.4 + ai_score * 0.6), 2)
        tier_label = _le_tier.inverse_transform([_clf.predict(x)[0]])[0]
        recommended = final_score >= 6.0

        reason = _generate_reason(final_score, am["population"], rent_est,
                                   comp_count, traffic, accessibility)

        profit = _estimate_profit(am["population"], rent_est, comp_count, category, area_sqm_default)

        results.append({
            "area_id": am["area_id"],
            "name": am["name"],
            "population": am["population"],
            "avg_rent": round(rent_est, 1),
            "competitor_count": comp_count,
            "traffic_score": round(traffic, 1),
            "accessibility_score": round(accessibility, 1),
            "suitability_score": final_score,
            "tier": tier_label,
            "recommended": recommended,
            "reason": reason,
            "latitude": am.get("latitude"),
            "longitude": am.get("longitude"),
            "profit_analysis": profit,
        })

    results.sort(key=lambda r: -r["suitability_score"])
    return results


# ══════════════════════════════════════════════════════════════
#  Endpoints
# ══════════════════════════════════════════════════════════════

@app.get("/")
def root():
    csv_data = get_csv_data()
    return {
        "service": "Egypt Smart City Analyzer",
        "version": "3.0.0",
        "csv_loaded": csv_data.loaded,
        "db_available": _DB_AVAILABLE,
        "model_loaded": True,
        "metrics": _METRICS,
    }


@app.get("/health")
def health():
    csv_data = get_csv_data()
    return {
        "status": "healthy",
        "csv_loaded": csv_data.loaded,
        "db_available": _DB_AVAILABLE,
        "model_loaded": True,
    }


@app.get("/areas")
def get_areas():
    """List areas from CSV data."""
    csv_data = get_csv_data()
    if csv_data.loaded:
        result = csv_data.get_areas()
        return {"areas": result, "count": len(result), "source": "csv"}
    # Fallback
    result = [{"area_id": k, "area_name": v[0], "population": v[1],
               "latitude": None, "longitude": None}
              for k, v in sorted(_FALLBACK_AREAS.items())]
    return {"areas": result, "count": len(result), "source": "fallback"}


@app.get("/categories")
def get_categories():
    csv_data = get_csv_data()
    if csv_data.loaded:
        cats = csv_data.get_categories()
        return {"categories": cats, "count": len(cats), "source": "csv"}
    return {"categories": _CATEGORIES, "count": len(_CATEGORIES), "source": "model"}


@app.get("/places")
def get_places(area_id: Optional[int] = None, category: Optional[str] = None):
    """Query places from CSV data."""
    csv_data = get_csv_data()
    if not csv_data.loaded:
        return {"places": [], "count": 0, "source": "unavailable"}
    rows = csv_data.suitability.to_dict("records")
    result = []
    for r in rows:
        if area_id and r.get("area_id") != area_id:
            continue
        if category and r.get("category") != category:
            continue
        result.append({
            "id": r.get("fact_id", r.get("prop_id", 0)),
            "area_id": r.get("area_id"),
            "category": r.get("category"),
            "street_name": r.get("street_name", ""),
            "area_sqm": r.get("area_sqm", 0),
            "rent_monthly_egp": r.get("rent_monthly_egp", 0),
        })
    return {"places": result, "count": len(result), "source": "csv"}


@app.get("/metrics/{area_id}")
def get_metrics(area_id: int):
    """Metrics for a single area from CSV."""
    csv_data = get_csv_data()
    if csv_data.loaded:
        area = csv_data.get_area(area_id)
        if area:
            scores = csv_data.get_scores_for_category(csv_data.get_categories()[0]) if csv_data.get_categories() else []
            comp_count = csv_data.count_competitors(area_id, csv_data.get_categories()[0]) if csv_data.get_categories() else 0
            return {
                "area_id": area_id,
                "area_name": area["area_name"],
                "population": int(area.get("population", 0)),
                "avg_rent": 300.0,
                "competitor_count": comp_count,
                "traffic_score": 6.0,
                "accessibility_score": 6.0,
            }
    if area_id in _FALLBACK_AREAS:
        name, pop = _FALLBACK_AREAS[area_id]
        return {"area_id": area_id, "area_name": name, "population": pop,
                "avg_rent": 300.0, "competitor_count": 5,
                "traffic_score": 6.0, "accessibility_score": 6.0}
    raise HTTPException(404, "Area not found")


@app.post("/predict")
def predict_endpoint(req: PredictRequest):
    return _predict_single(
        area_sqm=req.area_sqm, rent_egp=req.rent_egp,
        category=req.category, area_id=req.area_id,
        comp_500m=req.comp_500m, comp_1km=req.comp_1km,
    )


@app.post("/recommend")
def recommend_endpoint(req: RecommendRequest):
    """Find best locations (uses CSV pipeline when available)."""
    try:
        results = _run_csv_pipeline(req.category, max_rent=req.max_rent)
        if results:
            top = results[:req.top_n]
            return {
                "query": {"category": req.category, "max_rent": req.max_rent, "area_sqm": req.area_sqm},
                "total_areas_evaluated": len(results),
                "recommendations": top,
                "best": top[0] if top else None,
                "source": "csv",
            }
    except Exception:
        pass

    # Fallback: synthetic
    if req.category not in _CATEGORIES:
        raise HTTPException(400, f"Unknown category. Available: {_CATEGORIES}")
    try:
        cat_enc = _le_cat.transform([req.category])[0]
    except ValueError:
        cat_enc = 0
    results = []
    for area_id, (area_name, population) in _FALLBACK_AREAS.items():
        lookup = _CATEGORY_AREA_LOOKUP.get(req.category, {}).get(area_id, {})
        avg_rps = lookup.get("rent_per_sqm", min(1200, max(80, 450 * (population / 12000))))
        avg_c500 = int(round(lookup.get("comp_500m", 2)))
        avg_c1km = int(round(lookup.get("comp_1km", 5)))
        est_rent = avg_rps * req.area_sqm
        if est_rent > req.max_rent:
            continue
        affordability = max(0.2, min(2.0, 1 - (avg_rps / 450 - 1) * 0.5))
        x = np.array([[req.area_sqm, avg_rps, affordability, avg_c500, avg_c1km, population, cat_enc]])
        score = round(min(10.0, max(1.0, float(_reg.predict(x)[0]))), 2)
        tier_label = _le_tier.inverse_transform([_clf.predict(x)[0]])[0]
        results.append({
            "area_id": area_id, "area_name": area_name,
            "population": population, "suitability_score": score,
            "tier": tier_label, "estimated_rent": int(est_rent),
            "avg_rent_per_sqm": round(avg_rps, 1),
            "competitors_500m": avg_c500, "competitors_1km": avg_c1km,
            "recommended": score >= 6.0,
        })
    results.sort(key=lambda r: -r["suitability_score"])
    top = results[:req.top_n]
    return {
        "query": {"category": req.category, "max_rent": req.max_rent, "area_sqm": req.area_sqm},
        "total_areas_evaluated": len(results), "recommendations": top,
        "best": top[0] if top else None, "source": "fallback",
    }


def _map_to_analysis_shape(item: dict, area_sqm: float = 120.0) -> dict:
    """Map CSV pipeline result fields to the TypeScript-expected shape."""
    rent_est = item.get("avg_rent", 300)
    return {
        "area_id": item["area_id"],
        "area_name": item.get("name", item.get("area_name", "Unknown")),
        "population": item["population"],
        "suitability_score": item["suitability_score"],
        "tier": item["tier"],
        "recommended": item.get("recommended", item["suitability_score"] >= 6.0),
        "rent_per_sqm": round(rent_est, 1),
        "affordability": round(max(0.2, min(2.0, 1 - (rent_est / 450 - 1) * 0.5)), 3),
        "competitors_500m": int(round(item.get("competitor_count", 0) * 0.35)),
        "competitors_1km": int(round(item.get("competitor_count", 0) * 0.65)),
        "estimated_rent": int(rent_est * area_sqm),
        "traffic_score": item.get("traffic_score", 5.0),
        "accessibility_score": item.get("accessibility_score", 5.0),
        "reason": item.get("reason", ""),
        "profit_analysis": item.get("profit_analysis"),
    }


def _remap_to_frontend_ids(items: list[dict]) -> list[dict]:
    """Map CSV area_ids back to frontend 1-12 IDs. Skips unmapped areas."""
    csv_to_fe = {v: k for k, v in _FRONTEND_TO_CSV.items()}
    csv_ids = set(_FRONTEND_TO_CSV.values())
    out = []
    for item in items:
        if item["area_id"] not in csv_ids:
            continue
        item["area_id"] = csv_to_fe[item["area_id"]]
        out.append(item)
    return out


@app.get("/recommend/areas")
def get_precomputed_recommendations(
    business_type_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Return precomputed recommendations (refreshed every 5 min by scheduler)."""
    if not _DB_AVAILABLE:
        raise HTTPException(503, "Database not available")
    query = db.query(PrecomputedRecommendation)
    if business_type_id:
        query = query.filter(PrecomputedRecommendation.business_type_id == business_type_id)
    results = query.order_by(
        PrecomputedRecommendation.business_type_id,
        PrecomputedRecommendation.rank
    ).all()
    return {
        "recommendations": [
            {
                "id": r.id,
                "business_type_id": r.business_type_id,
                "area_id": r.area_id,
                "suitability_score": r.suitability_score,
                "rank": r.rank,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in results
        ],
        "count": len(results),
    }


@app.get("/alerts")
def get_alerts(
    limit: int = Query(50, ge=1, le=200),
    alert_type: Optional[str] = Query(None, alias="type"),
    db: Session = Depends(get_db),
):
    """Return latest alerts."""
    if not _DB_AVAILABLE:
        raise HTTPException(503, "Database not available")
    query = db.query(Alert)
    if alert_type:
        query = query.filter(Alert.type == alert_type)
    results = query.order_by(Alert.created_at.desc()).limit(limit).all()
    return {
        "alerts": [
            {
                "id": a.id,
                "message": a.message,
                "type": a.type,
                "area_id": a.area_id,
                "business_type_id": a.business_type_id,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in results
        ],
        "count": len(results),
    }


@app.post("/analyze")
def analyze_endpoint(req: AnalyzeRequest):
    """Full analysis for a specific area (backward compat)."""
    # Try CSV pipeline — always include requested area regardless of filter
    try:
        raw_results = _run_csv_pipeline(req.category, min_pop=0)
        if raw_results:
            results = _remap_to_frontend_ids([_map_to_analysis_shape(r, req.area_sqm) for r in raw_results])
            frontend_id = req.area_id
            current = next((r for r in results if r["area_id"] == frontend_id), None)
            if current:
                filtered = [
                    r for r in results
                    if r["area_id"] != frontend_id
                    and r["population"] >= (req.min_population or 0)
                ]
                all_sorted = sorted(filtered + [current], key=lambda x: -x["suitability_score"])
                return {
                    "current_area": current,
                    "rankings": all_sorted,
                    "best": all_sorted[0] if all_sorted else None,
                }
    except Exception:
        pass

    # Fallback synthetic
    if req.category not in _CATEGORIES:
        raise HTTPException(400, f"Unknown category. Available: {_CATEGORIES}")
    if req.area_id not in _FALLBACK_AREAS:
        raise HTTPException(400, f"Unknown area_id. Valid: {list(_FALLBACK_AREAS.keys())}")
    area_name = _FALLBACK_AREAS[req.area_id][0]
    population = _FALLBACK_AREAS[req.area_id][1]
    lookup = _CATEGORY_AREA_LOOKUP.get(req.category, {}).get(req.area_id, {})
    avg_rps = lookup.get("rent_per_sqm", min(1200, max(80, 450 * (population / 12000))))
    avg_c500 = int(round(lookup.get("comp_500m", 2)))
    avg_c1km = int(round(lookup.get("comp_1km", 5)))
    rent_per_sqm = req.rent_budget / req.area_sqm
    affordability = max(0.2, min(2.0, 1 - (rent_per_sqm / 450 - 1) * 0.5))
    try:
        cat_enc = _le_cat.transform([req.category])[0]
    except ValueError:
        cat_enc = 0
    x = np.array([[req.area_sqm, rent_per_sqm, affordability, avg_c500, avg_c1km, population, cat_enc]])
    score = round(min(10.0, max(1.0, float(_reg.predict(x)[0]))), 2)
    tier_label = _le_tier.inverse_transform([_clf.predict(x)[0]])[0]
    all_recs = []
    for aid, (aname, apop) in _FALLBACK_AREAS.items():
        if req.min_population and apop < req.min_population: continue
        lc = _CATEGORY_AREA_LOOKUP.get(req.category, {}).get(aid, {})
        rps_a = lc.get("rent_per_sqm", min(1200, max(80, 450 * (apop / 12000))))
        c5 = int(round(lc.get("comp_500m", 2)))
        c1 = int(round(lc.get("comp_1km", 5)))
        est = rps_a * req.area_sqm
        if est > req.rent_budget * 1.2: continue
        aff = max(0.2, min(2.0, 1 - (rps_a / 450 - 1) * 0.5))
        xe = np.array([[req.area_sqm, rps_a, aff, c5, c1, apop, cat_enc]])
        sc = round(min(10.0, max(1.0, float(_reg.predict(xe)[0]))), 2)
        tl = _le_tier.inverse_transform([_clf.predict(xe)[0]])[0]
        all_recs.append({"area_id": aid, "area_name": aname, "population": apop,
                         "suitability_score": sc, "tier": tl,
                         "estimated_rent": int(est), "competitors_500m": c5})
    all_recs.sort(key=lambda r: -r["suitability_score"])
    return {
        "current_area": {"area_id": req.area_id, "area_name": area_name,
                         "population": population, "suitability_score": score,
                         "tier": tier_label, "recommended": score >= 6.0,
                         "rent_per_sqm": round(rent_per_sqm, 1),
                         "affordability": round(affordability, 3),
                         "competitors_500m": avg_c500, "competitors_1km": avg_c1km},
        "rankings": all_recs, "best": all_recs[0] if all_recs else None,
    }


@app.post("/analysis/run")
def run_analysis(req: AnalysisRunRequest):
    """
    Full analysis pipeline — uses real CSV data as primary source.

    1. Reads area-business scores from CSV (611 records)
    2. Blends with AI model predictions
    3. Returns ranked results with human-readable reasons
    """
    if req.category not in _CATEGORIES:
        raise HTTPException(400, f"Unknown category. Available: {_CATEGORIES}")

    try:
        results = _run_csv_pipeline(req.category, min_pop=req.min_population,
                                     max_rent=req.max_rent)
    except HTTPException:
        results = []
        # Fallback to synthetic
        for area_id, (area_name, population) in _FALLBACK_AREAS.items():
            if req.min_population and population < req.min_population: continue
            results.append({
                "area_id": area_id, "name": area_name, "population": population,
                "avg_rent": 300.0, "competitor_count": 3,
                "traffic_score": 6.0, "accessibility_score": 6.0,
                "suitability_score": 5.0, "tier": "Medium",
                "recommended": False,
                "reason": "fallback data — limited analysis",
                "latitude": None, "longitude": None,
            })

    results.sort(key=lambda r: -r["suitability_score"])
    top = results[:req.top_n]
    source = "csv" if get_csv_data().loaded else "fallback"

    return {
        "category": req.category,
        "total_areas_evaluated": len(results),
        "source": source,
        "best_area": top[0] if top else None,
        "top_areas": top,
    }

# ══════════════════════════════════════════════════════════════
#  CSV Data reload
# ══════════════════════════════════════════════════════════════

@app.post("/admin/reload-csv")
def admin_reload_csv():
    """Force reload CSV data from disk."""
    try:
        cd = reload_csv_data()
        return {"status": "reloaded", "loaded": cd.loaded,
                "areas": len(cd.get_areas()), "categories": cd.get_categories()}
    except Exception as e:
        raise HTTPException(500, str(e))


# ══════════════════════════════════════════════════════════════
#  PowerBI Export Endpoints
# ══════════════════════════════════════════════════════════════

@app.get("/export/areas")
def export_areas_csv():
    """Export all areas + metrics as CSV for PowerBI."""
    csv_data = get_csv_data()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["area_id", "area_name", "population", "latitude", "longitude",
                      "competitor_count", "traffic_score", "accessibility_score"])

    if csv_data.loaded:
        for a in csv_data.get_areas():
            writer.writerow([
                a["area_id"], a["area_name"], a.get("population", 0),
                a.get("latitude", 0), a.get("longitude", 0),
                0, 6.0, 6.0,
            ])
    else:
        for aid, (name, pop) in _FALLBACK_AREAS.items():
            writer.writerow([aid, name, pop, 0, 0, 0, 6.0, 6.0])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=smartcity_areas.csv"},
    )


@app.get("/export/area-scores")
def export_area_scores_csv(category: str = Query("Food & Beverage")):
    """Full area-business scores as CSV for PowerBI."""
    csv_data = get_csv_data()
    output = io.StringIO()
    writer = csv.writer(output)

    if csv_data.loaded:
        metrics = csv_data.get_area_metrics_for_category(category)
        if not metrics:
            # Fallback: use scores directly
            scores = csv_data.get_scores_for_category(category)
            if scores:
                writer.writerow(scores[0].keys())
                for s in scores:
                    writer.writerow(s.values())
            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=smartcity_scores_{category.replace('& ','')}.csv"},
            )

        writer.writerow(metrics[0].keys())
        for m in metrics:
            writer.writerow(m.values())
    else:
        writer.writerow(["area_id", "name", "suitability_score", "tier"])
        for aid, (name, pop) in _FALLBACK_AREAS.items():
            writer.writerow([aid, name, 5.0, "Medium"])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=smartcity_scores_{category.replace('& ','')}.csv"},
    )


@app.get("/export/predictions")
def export_predictions_csv(category: str = Query("Food & Beverage")):
    """Run analysis and export ranked predictions as CSV for PowerBI."""
    req = AnalysisRunRequest(category=category, top_n=50)
    result = run_analysis(req)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "rank", "area_name", "population", "avg_rent",
        "competitor_count", "traffic_score", "accessibility_score",
        "suitability_score", "tier", "recommended", "reason",
    ])
    for i, area in enumerate(result.get("top_areas", []), 1):
        writer.writerow([
            i, area["name"], area["population"], area["avg_rent"],
            area["competitor_count"], area["traffic_score"],
            area["accessibility_score"], area["suitability_score"],
            area["tier"], area["recommended"], area["reason"],
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition":
                f"attachment; filename=smartcity_predictions_{category.replace('& ','')}.csv"
        },
    )


@app.get("/export/metadata")
def export_metadata_json():
    """Model metadata for PowerBI integration."""
    csv_data = get_csv_data()
    return {
        "model_metrics": _METRICS,
        "categories": _CATEGORIES,
        "csv_loaded": csv_data.loaded,
        "csv_areas": len(csv_data.get_areas()) if csv_data.loaded else 0,
        "csv_categories": csv_data.get_categories() if csv_data.loaded else [],
    }


# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("smartcity_api:app", host="0.0.0.0", port=port, reload=True)
