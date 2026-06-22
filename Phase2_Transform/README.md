# Phase 2 — Data Transformation (PySpark)

> **Medallion Architecture** — Bronze (PostgreSQL) → Gold (Excel) using Apache Spark 3.5.3

---

## Architecture

```
PostgreSQL · schema: bronze
        │
        ▼
Apache Spark 3.5.3 (local[*] · 4g memory · AQE enabled)
        │
        ├── Dim_Area                ← 51 rows
        ├── Dim_Business_Type       ← 12 rows
        ├── Dim_Property            ← 221 rows
        ├── Fact_Area_Business_Score    ← 612 rows
        └── Fact_Property_Suitability   ← 2,652 rows
                │
                ▼
        gold_output/  (.csv files)
```

---

## What Gets Built

### Dim_Area
Districts of Alexandria with population and GPS coordinates. Uses a **Window function** to always keep the latest census year per district.

### Dim_Business_Type
13 business subcategories across 7 categories:

| Category | Subcategories |
|---|---|
| Food & Beverage | Cafe, Restaurant, Bakery, Ice Cream & Sweets |
| Health & Fitness | Fitness Center |
| Tourism & Hospitality | Hotel |
| Healthcare | Hospital & Clinic, Pharmacy |
| Financial Services | Bank & Exchange |
| Retail | Clothing & Fashion, Supermarket & Grocery |
| Education | School, Education Center |

### Dim_Property
Commercial rental properties from Aqarmap, each mapped to a district using a `STREET_AREA_MAP` dictionary (60+ Alexandria street → district mappings). Includes `rent_per_sqm` calculation.

### Fact_Area_Business_Score
For every combination of district × business type (51 × 13 = 663 grid):

| Metric | Formula |
|---|---|
| `competitor_count` | Count of businesses of same type in same district |
| `nearest_competitor_m` | Avg distance to nearest competitor (Spark SQL self-join) |
| `demand_index` | population ÷ competitor_count |
| `market_saturation` | (competitors ÷ population/1000) × 10, capped at 100 |
| `suitability_score` | (0.4 × demand + 0.3 × population + 0.3 × (1 − saturation)) × 10 |
| `recommended` | suitability_score ≥ 6.0 |

### Fact_Property_Suitability
For every property × business type combination, scores each property based on:
- Competitor density within 500m and 1km (vectorized Haversine)
- Affordability vs. district average rent
- Demand index

`suitability = (0.4 × affordability + 0.3 × competition_score + 0.3 × demand_score) × 10`

---

## Key Technical Optimizations

| Issue | Fix | Impact |
|---|---|---|
| `local[2]` (2 cores only) | `local[*]` (all cores) | Faster processing |
| 1g memory | 4g driver + executor | Prevents OOM errors |
| No AQE | Adaptive Query Execution enabled | 30–60% time saving |
| Java serializer | KryoSerializer | Faster serialization |
| `dropDuplicates` on population (random) | `Window.partitionBy` (latest year) | Correct results |
| `string.contains` street→district join | `STREET_AREA_MAP` dict (O(1) lookup) | 99%+ match rate |
| Cross join (businesses × all areas) | Broadcast + NumPy UDF | n×50 rows → n rows |
| Python O(n²) UDF for distances | Spark SQL self-join (JVM native) | ~10x faster |
| `pandas.apply` (910K calls) | NumPy vectorized Haversine (455 iterations) | ~50x faster |

---

## Files

| File | Description |
|---|---|
| `SmartCity_Phase1_Fixed.ipynb` | Main notebook — run cells in order |
| `SmartCity_Phase1_Fixed_executed.ipynb` | Last executed version with outputs |
| `run_phase2.py` | Script to run the notebook non-interactively |
| `gold_output/` | Output Excel files (Dim + Fact tables) |

---

## Notebook Cell Order

```
Cell 0  → Install dependencies
Cell 1  → Create Spark Session (local[*], 4g, AQE, Kryo)
Cell 2  → Start PostgreSQL tunnel
Cell 3  → Unzip project data
Cell 4  → Create bronze schema
Cell 5  → Load files to PostgreSQL
─── Transformation ───
Cell 6  → Read bronze tables · unify businesses · distribute pharmacies
Cell 7  → Clean population (latest year per district)
Cell 8  → Build Dim_Area
Cell 9  → Build Dim_Business_Type
Cell 10 → Build Dim_Property (street→district mapping)
Cell 11 → Assign nearest district to each business (broadcast + UDF)
Cell 12 → Build Fact_Area_Business_Score (Spark SQL self-join)
Cell 13 → Build Fact_Property_Suitability (vectorized Haversine)
Cell 14 → Export all Gold tables to gold_output/
```

---

## Requirements

```
Apache Spark  3.5.3
Python        3.x
JDBC Driver   postgresql-42.7.3.jar

pyspark==3.5.3
psycopg2
openpyxl
numpy
pandas
```

---

## Run

```bash
# Non-interactive (via runner script)
python run_phase2.py

# Or via Airflow (runs automatically after Phase 1)
# → phase2_spark_transform task in smartcity_full_pipeline DAG
```
