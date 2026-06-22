# Phase 1 — Data Ingestion

> **Kafka streaming + PostgreSQL Bronze Layer** — 5 pipelines collecting urban data across Alexandria.

---

## Architecture

```
Data Sources → Kafka Producers → Topics → Consumers → output_all/
                                                            │
                                                     Bronze Loader
                                                            │
                                                     PostgreSQL (bronze)
```

---

## Pipelines

| # | Pipeline | Data Source | Kafka Topic(s) | Output |
|---|---|---|---|---|
| 01 | Rental | aqarmap.com.eg (scraping) | `rent-commercial-alexandria` | `rent_commercial_alexandria_YYYYMMDD.xlsx` |
| 02 | Business | OSM Overpass API + egyfinder.net | `osm-cafes-alexandria`, `osm-gyms-alexandria`, `pharmacy-alexandria` | Multiple xlsx/csv |
| 03 | Education | OSM Overpass API | `schools-alexandria`, `centers-alexandria` | `schools_YYYYMMDD.xlsx`, `centers_YYYYMMDD.xlsx` |
| 04 | Population | CAPMAS (local) + WorldPop API + GEE VIIRS | `population-alexandria` | `population_alexandria_YYYYMMDD.xlsx` |
| 05 | Traffic | SQLite DB + OSMnx API | `traffic-nodes-alexandria`, `traffic-edges-alexandria` | Nodes + Edges xlsx |

---

## Infrastructure Services

| Service | Image | Port | Purpose |
|---|---|---|---|
| Zookeeper | `confluentinc/cp-zookeeper:7.6.0` | 2181 | Kafka coordination |
| Kafka | `confluentinc/cp-kafka:7.6.0` | 9092 | Message broker |
| Kafka UI | `provectuslabs/kafka-ui:latest` | 8080 | Topic monitoring |
| PostgreSQL | `postgres:16-alpine` | 5432 | Bronze layer storage |
| Bronze Loader | custom | — | Watches output_all/ → loads to PostgreSQL |

---

## Bronze Layer — PostgreSQL

**Connection:** `smartcity / smartcity123` · DB: `smartcity` · Schema: `bronze`

| Table | Source | Key Columns |
|---|---|---|
| `bronze.rent_commercial` | Pipeline 01 | area_m2, rent_egp, location_en |
| `bronze.cafes` | Pipeline 02 | name, latitude, longitude |
| `bronze.gyms` | Pipeline 02 | name, latitude, longitude |
| `bronze.restaurants` | Pipeline 02 | name, latitude, longitude |
| `bronze.bakeries` | Pipeline 02 | name, latitude, longitude |
| `bronze.hotels` | Pipeline 02 | name, latitude, longitude |
| `bronze.hospitals` | Pipeline 02 | name, latitude, longitude |
| `bronze.banks` | Pipeline 02 | name, latitude, longitude |
| `bronze.clothing` | Pipeline 02 | name, latitude, longitude |
| `bronze.supermarkets` | Pipeline 02 | name, latitude, longitude |
| `bronze.sweets` | Pipeline 02 | name, latitude, longitude |
| `bronze.pharmacies` | Pipeline 02 | name, address, phone |
| `bronze.schools` | Pipeline 03 | name, type, latitude, longitude |
| `bronze.centers` | Pipeline 03 | name, type, latitude, longitude |
| `bronze.population` | Pipeline 04 | data (JSONB) |
| `bronze.traffic_nodes` | Pipeline 05 | osmid, x, y, street_count |
| `bronze.traffic_edges` | Pipeline 05 | u, v, length, data (JSONB) |
| `bronze.ingestion_log` | Bronze Loader | filename, row_count, status |

Every row also has: `_source_file`, `_ingested_at`

---

## Local Data Required

Pipelines 04 and 05 need local files mounted under `data/`:

```
data/
├── population__data/raw/
│   ├── alex_population.xlsx
│   └── Alexandria_Nightlights_2023.csv
└── Trafic_Data/
    ├── egypt_smart_city (1).db
    ├── Alexandria_Intersections_Nodes.csv
    └── Alexandria_Streets_Edges.csv
```

---

## Run

```bash
# All pipelines (master)
cd Phase1_Scraping
docker compose -f docker-compose.master.yml up --build

# Single pipeline (standalone)
cd Phase1_Scraping/pipeline_01_rental
docker compose up --build
```

---

## Useful Queries

```sql
-- Check ingestion log
SELECT filename, dataset, row_count, status, ingested_at
FROM bronze.ingestion_log
ORDER BY ingested_at DESC LIMIT 20;

-- Count per table
SELECT 'cafes' AS tbl, COUNT(*) FROM bronze.cafes
UNION ALL
SELECT 'pharmacies', COUNT(*) FROM bronze.pharmacies
UNION ALL
SELECT 'schools', COUNT(*) FROM bronze.schools;
```

---

## Python Dependencies (per pipeline)

```
kafka-python==2.0.2    requests==2.31.0
beautifulsoup4==4.12.3  lxml==5.2.1
pandas==2.2.2           openpyxl==3.1.2
APScheduler==3.10.4

# Bronze Loader only:
psycopg2-binary==2.9.9
```
