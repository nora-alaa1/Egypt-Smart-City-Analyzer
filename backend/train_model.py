"""
SmartCity AI — Training Script
Generates synthetic Alexandria urban data, trains models, and saves the bundle.
"""

import pickle
import json
import warnings
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import cross_val_score, StratifiedKFold, cross_val_predict
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline

warnings.filterwarnings("ignore")
np.random.seed(42)

# ── Alexandria districts with realistic attributes ──
AREAS = {
    1:  {"name": "Smouha",       "population": 45000, "lat": 31.2100, "lng": 29.9400},
    2:  {"name": "Sidi Gaber",   "population": 38000, "lat": 31.2200, "lng": 29.9500},
    3:  {"name": "Stanley",      "population": 25000, "lat": 31.2300, "lng": 29.9600},
    4:  {"name": "Louran",       "population": 32000, "lat": 31.2150, "lng": 29.9300},
    5:  {"name": "Cleopatra",    "population": 35000, "lat": 31.2250, "lng": 29.9450},
    6:  {"name": "Sports City",  "population": 22000, "lat": 31.2050, "lng": 29.9200},
    7:  {"name": "Rushdy",       "population": 29000, "lat": 31.2350, "lng": 29.9650},
    8:  {"name": "Shatby",       "population": 18000, "lat": 31.2400, "lng": 29.9700},
    9:  {"name": "Ibrahimia",    "population": 26000, "lat": 31.2170, "lng": 29.9350},
    10: {"name": "Moharam Bek",  "population": 31000, "lat": 31.2070, "lng": 29.9150},
    11: {"name": "Kafr Abdu",    "population": 27000, "lat": 31.2120, "lng": 29.9250},
    12: {"name": "El-Attarin",   "population": 15000, "lat": 31.2000, "lng": 29.9000},
}

# ── Business categories ──
BUSINESS_TYPES = {
    1:  {"category": "Food & Beverage",  "subcategory": "Cafe"},
    2:  {"category": "Food & Beverage",  "subcategory": "Restaurant"},
    3:  {"category": "Food & Beverage",  "subcategory": "Bakery"},
    4:  {"category": "Retail",           "subcategory": "Clothing Store"},
    5:  {"category": "Retail",           "subcategory": "Electronics"},
    6:  {"category": "Retail",           "subcategory": "Supermarket"},
    7:  {"category": "Healthcare",       "subcategory": "Pharmacy"},
    8:  {"category": "Healthcare",       "subcategory": "Clinic"},
    9:  {"category": "Education",        "subcategory": "Tutoring Center"},
    10: {"category": "Education",        "subcategory": "Language School"},
    11: {"category": "Fitness",          "subcategory": "Gym"},
    12: {"category": "Fitness",          "subcategory": "Yoga Studio"},
    13: {"category": "Entertainment",     "subcategory": "Game Zone"},
    14: {"category": "Entertainment",     "subcategory": "Cinema"},
}

# ── Generate synthetic property data ──
def generate_training_data(areas, btypes, n_per_area=30):
    rows = []
    for area_id, area in areas.items():
        for _ in range(n_per_area):
            btype_id = np.random.choice(list(btypes.keys()))
            btype = btypes[btype_id]
            area_sqm = np.random.uniform(30, 500)
            base_rent_per_sqm = np.random.uniform(80, 500)
            rent_egp = area_sqm * base_rent_per_sqm

            pop_factor = area["population"] / 45000
            comp_500m = max(0, int(np.random.poisson(3 * pop_factor)))
            comp_1km = max(0, int(np.random.poisson(8 * pop_factor)))

            affordability = max(0.2, min(2.0, 1 - (base_rent_per_sqm / 400 - 1) * 0.4))
            noise = np.random.normal(0, 0.5)
            suitability = min(10, max(1, 3.5 + pop_factor * 3 - comp_500m * 0.15 + affordability * 1.5 + noise))

            category_enc = list(btypes.keys()).index(btype_id)
            recommended = suitability >= 6.0

            rows.append({
                "prop_id": len(rows) + 1,
                "area_id": area_id,
                "area_name": area["name"],
                "population": area["population"],
                "business_type_id": btype_id,
                "category": btype["category"],
                "subcategory": btype["subcategory"],
                "street_name": f"Street {np.random.randint(1, 100)}",
                "area_sqm": round(area_sqm, 1),
                "rent_egp": round(rent_egp, 0),
                "rent_per_sqm": round(base_rent_per_sqm, 1),
                "comp_500m": comp_500m,
                "comp_1km": comp_1km,
                "affordability": round(affordability, 3),
                "suitability": round(suitability, 2),
                "recommended": bool(recommended),
            })
    return pd.DataFrame(rows)

print("Generating synthetic training data...")
df = generate_training_data(AREAS, BUSINESS_TYPES, n_per_area=40)
print(f"  Rows generated: {len(df)}")

# ── Prepare features ──
def tier(score):
    if score >= 7.5:
        return "High"
    if score >= 5.0:
        return "Medium"
    return "Low"

df["tier"] = df["suitability"].apply(tier)

le_cat = LabelEncoder()
df["category_enc"] = le_cat.fit_transform(df["category"])

FEATURES = [
    "area_sqm", "rent_per_sqm", "affordability",
    "comp_500m", "comp_1km", "population", "category_enc"
]

X = df[FEATURES].values
y_tier = df["tier"].values
y_score = df["suitability"].values

print(f"\nFeatures: {FEATURES}")
print(f"Samples : {len(X)}")
print(f"\nTier distribution:\n{df['tier'].value_counts()}")

# ── Model A: Tier Classifier (RandomForest) ──
le_tier = LabelEncoder()
y_tier_enc = le_tier.fit_transform(y_tier)

clf = Pipeline([
    ("scaler", StandardScaler()),
    ("rf", RandomForestClassifier(
        n_estimators=200, max_depth=8,
        min_samples_leaf=2, class_weight="balanced", random_state=42
    ))
])

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(clf, X, y_tier_enc, cv=cv, scoring="accuracy")
clf.fit(X, y_tier_enc)

print(f"\n{'='*45}")
print(f"Model A — Tier Classifier")
print(f"  CV Accuracy: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

rf = clf.named_steps["rf"]
print("\nFeature Importance:")
for feat, imp in sorted(zip(FEATURES, rf.feature_importances_), key=lambda x: -x[1]):
    bar = "#" * int(imp * 40)
    print(f"  {feat:<20} {imp:.3f}  {bar}")

# ── Model B: Score Regressor (GradientBoosting) ──
reg = Pipeline([
    ("scaler", StandardScaler()),
    ("gbr", GradientBoostingRegressor(
        n_estimators=300, learning_rate=0.05,
        max_depth=4, subsample=0.8, random_state=42
    ))
])

y_pred_cv = cross_val_predict(reg, X, y_score, cv=5)
mae = mean_absolute_error(y_score, y_pred_cv)
r2 = r2_score(y_score, y_pred_cv)
reg.fit(X, y_score)

print(f"\nModel B — Suitability Score Regressor")
print(f"  CV MAE: {mae:.3f}")
print(f"  CV R² : {r2:.3f}")

# ── Save model bundle ──
areas_out = {int(k): (v["name"], int(v["population"])) for k, v in AREAS.items()}
btypes_out = {int(k): (v["category"], v["subcategory"]) for k, v in BUSINESS_TYPES.items()}

model_bundle = {
    "classifier":     clf,
    "regressor":      reg,
    "le_tier":        le_tier,
    "le_category":    le_cat,
    "features":       FEATURES,
    "areas":          areas_out,
    "business_types": btypes_out,
    "tier_labels":    list(le_tier.classes_),
    "categories":     list(le_cat.classes_),
    "training_data":  df,
    "metrics": {
        "classifier_cv_accuracy": float(cv_scores.mean()),
        "regressor_cv_mae":       float(mae),
        "regressor_cv_r2":        float(r2),
    }
}

with open("smartcity_model.pkl", "wb") as f:
    pickle.dump(model_bundle, f)

meta = {
    "areas":          {str(k): {"name": v[0], "population": v[1]} for k, v in areas_out.items()},
    "business_types": {str(k): {"category": v[0], "subcategory": v[1]} for k, v in btypes_out.items()},
    "categories":     list(le_cat.classes_),
    "tier_labels":    list(le_tier.classes_),
    "metrics":        model_bundle["metrics"],
}
with open("smartcity_meta.json", "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)

print(f"\n{'='*45}")
print("[OK] smartcity_model.pkl saved")
print("[OK] smartcity_meta.json saved")
print(f"\nFinal metrics:")
print(f"  Classifier Accuracy : {cv_scores.mean():.1%}")
print(f"  Regressor MAE       : {mae:.3f}")
print(f"  Regressor R²        : {r2:.3f}")
print(f"\nTo start the API server:")
print(f"  cd backend")
print(f"  uvicorn smartcity_api:app --reload --port 8000")
