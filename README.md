# 🏙️ SmartCity Analyzer

> End-to-end data engineering pipeline for **Alexandria, Egypt** — collecting, streaming, transforming, and warehousing urban data to score commercial property suitability.

---

## 📐 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      DATA SOURCES                               │
│  Aqarmap · OpenStreetMap · Egyfinder · CAPMAS · WorldPop · GEE  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1 — Ingestion (Kafka + PostgreSQL)                       │
│                                                                 │
│  5 Kafka Pipelines (producers → consumers)                      │
│  → output_all/  (Excel / CSV files)                             │
│  → Bronze Loader → PostgreSQL  schema: bronze                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 2 — Transformation (PySpark)                             │
│                                                                 │
│  PostgreSQL (bronze) → Apache Spark 3.5.3                       │
│  → Haversine distances · Suitability scoring · Star schema      │
│  → gold_output/  (Dim + Fact Excel files)                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 3 — Data Warehouse (SQL Server)                          │
│                                                                 │
│  Gold files → SQL Server  db: SmartCity                         │
│  Star Schema: 3 Dims + 2 Facts · PKs · FKs · Indexes           │
└─────────────────────────────────────────────────────────────────┘
                           ▲
                           │  orchestrates all phases
┌─────────────────────────────────────────────────────────────────┐
│  AIRFLOW — Orchestration  (smartcity_full_pipeline DAG)         │
│                                                                 │
│  Schedule: every 6 months  ·  UI: localhost:8085                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Warehouse — Final Row Counts

| Table | Type | Rows |
|---|---|---|
| `Dim_Business_Type` | Dimension | 12 |
| `Dim_Area` | Dimension | 51 |
| `Dim_Property` | Dimension | 221 |
| `Fact_Area_Business_Score` | Fact | 612 |
| `Fact_Property_Suitability` | Fact | 2,652 |

**Total: 3,548 rows**

---

## 🛠️ Tools & Technologies

| Layer | Tools |
|---|---|
| **Orchestration** | Apache Airflow 2.9 |
| **Processing** | Apache Spark (PySpark) 3.5.3 + NumPy / Pandas |
| **Streaming** | Apache Kafka + Zookeeper + Kafka UI |
| **Databases** | PostgreSQL 16 (Bronze) · SQL Server (Data Warehouse) |
| **Containers** | Docker + Docker Compose |
| **Python Stack** | Pandas, NumPy, kafka-python |
| **Scraping** | Requests, BeautifulSoup4 |
| **Data Sources** | Aqarmap · OpenStreetMap (Overpass) · Egyfinder · CAPMAS · WorldPop · Google Earth Engine |

---

## 📁 Project Structure

```
SmartCityAnalyzer-main/
│
├── README.md                              ← You are here
├── setup.sh                               ← One-time environment setup
├── run.sh                                 ← Start / Stop / Status
├── Dockerfile.airflow
│
├── phase1_scraping/                       ← Kafka + PostgreSQL (Bronze)
│   ├── README.md
│   ├── docker-compose.master.yml          ← All Phase 1 services
│   ├── output_all/                        ← All pipeline outputs
│   ├── pipeline_01_rental/                ← Aqarmap scraping
│   ├── pipeline_02_business/              ← OSM + Egyfinder
│   ├── pipeline_03_education/             ← OSM Education
│   ├── pipeline_04_population/            ← CAPMAS + WorldPop + GEE
│   ├── pipeline_05_traffic/               ← OSMnx + SQLite
│   └── pipeline_bronze_postgres/          ← Auto-loader → PostgreSQL
│
├── phase2_transform/                      ← PySpark ETL
│   ├── README.md
│   ├── SmartCity_Phase1_Fixed.ipynb       ← Main Spark notebook
│   ├── run_phase2.py                      ← CLI runner
│   └── gold_output/                       ← Dim + Fact Excel files
│       ├── Dim_Area.xlsx
│       ├── Dim_Business_Type.xlsx
│       ├── Dim_Property.xlsx
│       ├── Fact_Area_Business_Score.xlsx
│       └── Fact_Property_Suitability.xlsx
│
├── phase3_dwh/                            ← SQL Server Data Warehouse
│   ├── README.md
│   ├── load_to_sqlserver.ipynb
│   ├── run_load.py
│   └── dwh/
│       ├── 01_create_schema.sql
│       ├── 02_create_tables.sql
│       ├── 03_constraints.sql
│       └── 04_indexes.sql
│
└── smartcity-airflow/                     ← Airflow Orchestrator
    ├── README.md
    ├── docker-compose.yml
    ├── .env.example                       ← Copy to .env and edit
    └── dags/
        └── smartcity_pipeline.py          ← Full pipeline DAG
```

---

## ⚡ Quick Start

```bash
# 1. One-time setup (check Docker, pull images, create dirs)
bash setup.sh

# 2. Run everything via Airflow (recommended)
bash run.sh airflow

# 3. Or run phases manually
bash run.sh phase1        # Start Kafka + PostgreSQL pipelines
bash run.sh phase2        # Run PySpark transform
bash run.sh phase3        # Load to SQL Server

# 4. Check status
bash run.sh status

# 5. Stop everything
bash run.sh stop
```

---

## 🔗 Service Endpoints

| Service | URL / Port | Credentials |
|---|---|---|
| Airflow UI | http://localhost:8085 | `admin / admin` |
| Kafka UI | http://localhost:8080 | — |
| Kafka Broker | `localhost:9092` | — |
| PostgreSQL (Bronze) | `localhost:5432` | `smartcity / smartcity123` |
| PostgreSQL (Airflow) | `localhost:5433` | `airflow / airflow` |
| SQL Server (DWH) | `localhost:1433` | `sa / YourPassword` |

---

## 📋 Phase Details

| Phase | README | Key Tech |
|---|---|---|
| Phase 1 — Ingestion | [phase1_scraping/README.md](phase1_scraping/README.md) | Kafka · PostgreSQL · Docker |
| Phase 2 — Transform | [phase2_transform/README.md](phase2_transform/README.md) | PySpark · Haversine · Medallion |
| Phase 3 — DWH | [phase3_dwh/README.md](phase3_dwh/README.md) | SQL Server · Star Schema |
| Airflow — Orchestration | [smartcity-airflow/README.md](smartcity-airflow/README.md) | Airflow DAG · LocalExecutor |

---

## 🔄 Airflow DAG Flow

```
start_infrastructure → wait_kafka_healthy
                              │
           ┌──────────────────┼──────────────────────┐
           ▼                  ▼                      ▼
     p01_rental          p02_business  ...  p05_traffic   (parallel)
           │                  │                      │
     p01_consumer       p02_consumer          p05_consumer
           └──────────────────┴──────────────────────┘
                              │
                       bronze_loader  ←─── cleanup_kafka
                              │
                  phase2_spark_transform
                              │
                   phase3_create_dwh_schema
                              │
                  phase3_load_gold_to_sqlserver
                              │
                phase3_apply_constraints_indexes
```

**Schedule:** `0 2 1 */6 *` — 2:00 AM on the 1st of every 6 months

---

*SmartCity Analyzer · Alexandria, Egypt · Data Engineering Pipeline*
