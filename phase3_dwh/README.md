# Phase 3 — Data Warehouse (SQL Server)

> Loads Gold tables from Phase 2 into **SQL Server** and builds a complete Star Schema with constraints and indexes.

---

## Architecture

```
gold_output/  (Phase 2 CSV files)
        │
        ▼
load_to_sqlserver.ipynb
(SQLAlchemy + pyodbc · fast_executemany)
        │
        ▼
SQL Server · DB: SmartCity
        │
        ├── Dim_Area               (51 rows)
        ├── Dim_Business_Type      (12 rows)
        ├── Dim_Property           (221 rows)
        ├── Fact_Area_Business_Score   (612 rows)
        └── Fact_Property_Suitability  (2,652 rows)
        │
        ▼
dwh/*.sql  → PKs · FKs · Indexes
```

---

## Star Schema

```
           Dim_Area (area_id PK)
               │
               │ FK                    FK
               ▼                       ▼
Dim_Business_Type ──► Fact_Area_Business_Score
(business_type_id PK)

Dim_Property ──► Fact_Property_Suitability
(prop_id PK)    FK: area_id → Dim_Area
                FK: business_type_id → Dim_Business_Type
```

---

## Tables

### Dim_Area
| Column | Type |
|---|---|
| area_id (PK) | INT |
| area_name | NVARCHAR(200) |
| population | BIGINT |
| latitude | FLOAT |
| longitude | FLOAT |

### Dim_Business_Type
| Column | Type |
|---|---|
| business_type_id (PK) | INT |
| category | NVARCHAR(100) |
| subcategory | NVARCHAR(100) |
| service_type | NVARCHAR(100) |

### Dim_Property
| Column | Type |
|---|---|
| prop_id (PK) | INT |
| area_id (FK) | INT |
| street_name | NVARCHAR(300) |
| area_sqm | INT |
| rent_monthly_egp | INT |
| rent_per_sqm | FLOAT |

### Fact_Area_Business_Score
| Column | Type |
|---|---|
| score_id (PK) | INT |
| area_id (FK) | INT |
| business_type_id (FK) | INT |
| competitor_count | INT |
| nearest_competitor_m | INT |
| population | BIGINT |
| demand_index | INT |
| market_saturation | FLOAT |
| suitability_score | FLOAT |
| recommended | BIT |

### Fact_Property_Suitability
| Column | Type |
|---|---|
| fact_id (PK) | INT |
| prop_id (FK) | INT |
| area_id (FK) | INT |
| business_type_id (FK) | INT |
| competitors_500m | INT |
| competitors_1km | INT |
| affordability_score | FLOAT |
| suitability_score | FLOAT |
| recommended | BIT |

---

## SQL Scripts Execution Order

```
dwh/01_create_schema.sql    → CREATE SCHEMA SmartCity
dwh/02_create_tables.sql    → CREATE TABLE (all 5 tables)
dwh/03_constraints.sql      → PRIMARY KEY + FOREIGN KEY
dwh/04_indexes.sql          → Query optimization indexes
```

---

## Connection Setup

Edit `load_to_sqlserver.ipynb` Cell 2:

| Variable | Value |
|---|---|
| `DB_SERVER` | Your SQL Server instance name (e.g. `LAPTOP\MSSQLSERVER01`) |
| `DB_NAME` | `SmartCity` |
| `DB_DRIVER` | `ODBC Driver 17 for SQL Server` |
| `FILES_DIR` | Path to `gold_output/` folder |

```python
engine = create_engine(
    f"mssql+pyodbc://{DB_SERVER}/{DB_NAME}"
    f"?driver={DB_DRIVER}&trusted_connection=yes&TrustServerCertificate=yes",
    fast_executemany=True
)
```

> `trusted_connection=yes` → Windows Authentication (no password needed)

---

## Requirements

```
SQL Server 2019/2022 (or Express)


pandas
```

---

## Run

```bash
# Run the load notebook
python run_load.py

# Or manually in Jupyter:
# 1. Open load_to_sqlserver.ipynb
# 2. Edit connection settings in Cell 2
# 3. Run all cells in order

# Then apply constraints and indexes in SSMS:
# Run dwh/02_create_tables.sql
# Run dwh/03_constraints.sql
# Run dwh/04_indexes.sql
```

---

## Post-Load Verification

```sql
-- Check row counts
SELECT 'Dim_Area'                AS tbl, COUNT(*) AS rows FROM Dim_Area
UNION ALL SELECT 'Dim_Business_Type',       COUNT(*) FROM Dim_Business_Type
UNION ALL SELECT 'Dim_Property',            COUNT(*) FROM Dim_Property
UNION ALL SELECT 'Fact_Area_Business_Score',COUNT(*) FROM Fact_Area_Business_Score
UNION ALL SELECT 'Fact_Property_Suitability',COUNT(*) FROM Fact_Property_Suitability;

-- Top recommended areas for cafes
SELECT area_name, suitability_score
FROM Fact_Area_Business_Score
WHERE subcategory = 'Cafe' AND recommended = 1
ORDER BY suitability_score DESC;

-- Best properties for any business
SELECT street_name, category, suitability_score
FROM Fact_Property_Suitability
WHERE recommended = 1
ORDER BY suitability_score DESC;
```

---

## Indexes Applied

```sql
CREATE INDEX IX_FactArea_recommended  ON Fact_Area_Business_Score (recommended, suitability_score DESC);
CREATE INDEX IX_FactArea_area         ON Fact_Area_Business_Score (area_id, category);
CREATE INDEX IX_FactProp_recommended  ON Fact_Property_Suitability (recommended, suitability_score DESC);
CREATE INDEX IX_FactProp_area         ON Fact_Property_Suitability (area_id, category);
CREATE INDEX IX_DimProp_area          ON Dim_Property (area_id);
```
