"""
SmartCity API — FastAPI server
ضعي هذا الملف في نفس مجلد SmartCity_Model_v2.ipynb
"""

import pickle
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

# ── تحميل الموديل ──
with open("smartcity_model.pkl", "rb") as f:
    bundle = pickle.load(f)

clf        = bundle["classifier"]
reg        = bundle["regressor"]
le_tier    = bundle["le_tier"]
le_cat     = bundle["le_category"]
FEATURES   = bundle["features"]
AREAS      = bundle["areas"]
BTYPES     = bundle["business_types"]

app = FastAPI(
    title="SmartCity Business Classifier",
    description="تصنيف ملاءمة العقارات للأنشطة التجارية",
    version="1.0"
)

# ── Schemas ──
class PropertyInput(BaseModel):
    area_sqm:  float
    rent_egp:  float
    category:  str
    area_id:   Optional[int] = None
    comp_500m: Optional[int] = 0
    comp_1km:  Optional[int] = 0

class RecommendInput(BaseModel):
    category: str
    max_rent: float
    area_sqm: float
    top_n:    Optional[int] = 10

# ── Helper ──
def build_features(area_sqm, rent_egp, category, area_id, comp_500m, comp_1km):
    population   = AREAS.get(area_id, (None, 10000))[1] if area_id else 10000
    rent_per_sqm = rent_egp / area_sqm
    affordability = max(0.2, min(2.0, 1 - (rent_per_sqm / 450 - 1) * 0.5))
    try:
        cat_enc = int(le_cat.transform([category])[0])
    except Exception:
        raise HTTPException(400, f"category غير معروف: {category}")
    return np.array([[area_sqm, rent_per_sqm, affordability,
                      comp_500m, comp_1km, population, cat_enc]])

# ── Endpoints ──
@app.get("/")
def root():
    return {"message": "SmartCity API is running ✅"}

@app.get("/categories")
def get_categories():
    return {"categories": list(le_cat.classes_)}

@app.get("/areas")
def get_areas():
    return {"areas": {str(k): v[0] for k, v in AREAS.items()}}

@app.post("/predict")
def predict(data: PropertyInput):
    x          = build_features(data.area_sqm, data.rent_egp, data.category,
                                data.area_id, data.comp_500m, data.comp_1km)
    score      = round(float(min(10.0, max(1.0, reg.predict(x)[0]))), 2)
    tier       = le_tier.inverse_transform([clf.predict(x)[0]])[0]
    area_name  = AREAS.get(data.area_id, ("غير محدد", 0))[0] if data.area_id else "غير محدد"

    return {
        "area_name":    area_name,
        "category":     data.category,
        "score":        score,
        "tier":         tier,
        "recommended":  score >= 6,
        "rent_per_sqm": round(data.rent_egp / data.area_sqm, 1)
    }

@app.post("/recommend")
def recommend(data: RecommendInput):
    try:
        cat_enc = int(le_cat.transform([data.category])[0])
    except Exception:
        raise HTTPException(400, f"category غير معروف: {data.category}")

    results = []
    for area_id, (area_name, population) in AREAS.items():
        avg_rps  = min(1200, max(80, 450 * (population / 12000)))
        est_rent = avg_rps * data.area_sqm
        if est_rent > data.max_rent:
            continue

        afford = max(0.2, min(2.0, 1 - (avg_rps / 450 - 1) * 0.5))
        x      = np.array([[data.area_sqm, avg_rps, afford, 2, 5, population, cat_enc]])
        score  = round(float(min(10.0, max(1.0, reg.predict(x)[0]))), 2)
        tier   = le_tier.inverse_transform([clf.predict(x)[0]])[0]

        results.append({
            "area_id":       area_id,
            "area_name":     area_name,
            "score":         score,
            "tier":          tier,
            "est_rent_egp":  int(est_rent),
            "population":    population,
        })

    results = sorted(results, key=lambda r: -r["score"])[:data.top_n]
    return {"category": data.category, "results": results}
