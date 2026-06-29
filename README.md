# 🏙️ Egypt Smart City Analyzer

> *Helping entrepreneurs find their perfect spot in Alexandria — one data point at a time.*

🔗 **Live App:** [egypt-smart-city-analyzer.vercel.app](https://egypt-smart-city-analyzer.vercel.app)

---

## 📌 Overview

Every city has a story hidden in its data — population flows, rental trends, competitor patterns, and foot traffic. But that story is rarely told in a way entrepreneurs and investors can actually use.

**Egypt Smart City Analyzer** is a full end-to-end data engineering platform that transforms raw urban data into actionable business intelligence. It collects, streams, processes, warehouses, and models city data — then presents the results through an AI-powered web dashboard that helps anyone make smarter location decisions.

The platform is built to scale across any Egyptian city. **Alexandria** is our starting point — a pilot that proves the concept and sets the foundation for a national urban intelligence system.

**No guesswork. Just data.**

---

## ⚙️ Pipeline

```
  [ Data Sources ]
  OpenStreetMap · Aqarmap · CAPMAS · WorldPop · Google Earth Engine
         │
         ▼
  [ Phase 1 — Ingestion ]
  Kafka Producers & Consumers  ──►  PostgreSQL  (Bronze Layer)
  5 pipelines: Rental · Business · Education · Population · Traffic
         │
         ▼
  [ Phase 2 — Transformation ]
  PySpark ETL  ──►  Gold Layer  (Dim + Fact CSV files)
  Haversine distances · Suitability scoring · Medallion Architecture
         │
         ▼
  [ Phase 3 — Data Warehouse ]
  SQL Server  ──►  Star Schema  (3 Dimensions · 2 Facts · 3,548 rows)
         │
         ▼
  [ Phase 4 — Orchestration ]
  Apache Airflow  ──►  Full pipeline DAG  (runs every 6 months)
         │
         ▼
  [ Phase 5 — AI & API ]
  scikit-learn Models  +  FastAPI  ──►  Tier + Score predictions
         │
         ▼
  [ Frontend ]
  Next.js Dashboard  ──►  Live on Vercel  🌐
```

---

## 🛠️ Tools & Technologies

| Layer | Tool | What it does |
|---|---|---|
| **Streaming** | Apache Kafka + Zookeeper | Streams scraped data in real time |
| **Bronze DB** | PostgreSQL 16 | Stores raw ingested data |
| **Processing** | PySpark 3.5 + Pandas | Cleans, transforms, and scores data |
| **Warehouse** | SQL Server + Star Schema | Powers analytical queries |
| **Orchestration** | Apache Airflow 2.9 | Schedules and monitors the pipeline |
| **ML** | scikit-learn (RF + GBR) | Predicts suitability tier and score |
| **API** | FastAPI + Uvicorn | Serves predictions to the frontend |
| **Frontend** | Next.js + TypeScript + Tailwind | Interactive web dashboard |
| **Deployment** | Vercel + Render | Hosts the live app |
| **Containers** | Docker + Docker Compose | Reproducible environments |
| **Scraping** | BeautifulSoup4 + Requests | Extracts data from the web |
| **Data Sources** | OSM · Aqarmap · CAPMAS · WorldPop · GEE | Real urban data inputs |

---

## 📊 Data Warehouse — Snapshot

| Table | Type | Rows |
|---|---|---|
| `Dim_Business_Type` | Dimension | 12 |
| `Dim_Area` | Dimension | 51 |
| `Dim_Property` | Dimension | 221 |
| `Fact_Area_Business_Score` | Fact | 612 |
| `Fact_Property_Suitability` | Fact | **2,652** |

**Total: 3,548 rows** across 5 tables.

---

## 🤖 AI Models

Two models trained on `Fact_Property_Suitability` (2,652 records):

| Model | Algorithm | Output |
|---|---|---|
| **Tier Classifier** | RandomForestClassifier — 200 trees | `High` / `Medium` / `Low` |
| **Score Regressor** | GradientBoostingRegressor — 300 estimators | Score from **1.0 → 10.0** |

**Features:** property size · rent per m² · affordability index · competitor density (500m & 1km) · population · business category.

**API Endpoints:**

| Endpoint | Method | What it returns |
|---|---|---|
| `/predict` | POST | Suitability score + tier for a single property |
| `/recommend` | POST | Top N areas for a business type & budget |
| `/areas` | GET | All area names and IDs |
| `/categories` | GET | All supported business types |

---

## 🌐 The Web App

A live dashboard at **[egypt-smart-city-analyzer.vercel.app](https://egypt-smart-city-analyzer.vercel.app)** where users can:

- Choose a **district** (Smouha, Sidi Gaber, Stanley, Rushdy, and 8 more)
- Select a **business type** (Food & Beverage, Retail, Healthcare, Education, Fitness, Entertainment)
- Set a **rent budget** and **space** in m²
- Get an **AI suitability score** with a `High / Medium / Low` tier
- View a live **OpenStreetMap** with color-coded grid overlays
- Compare **competitor density**, **population distribution**, and **rental prices** across districts
- Export results as **CSV** for use in Power BI or Excel

---

## 📁 Project Structure

```
Egypt-Smart-City-Analyzer/
│
├── Phase1_Scraping/        ← Kafka + PostgreSQL (Bronze Layer)
├── Phase2_Transform/       ← PySpark ETL + Gold CSV outputs
├── Phase3_Dwh/             ← SQL Server DWH + Star Schema SQL
├── SmartCity-Airflow/      ← Airflow DAG + Docker Compose
├── Phase_5_ML_Model/       ← ML training notebook + FastAPI server
├── backend/                ← Production API (deployed on Render)
├── src/                    ← Next.js frontend source
├── setup.sh                ← One-time environment setup
└── run.sh                  ← Start / Stop / Status commands
```

---

## 🚀 Quick Start

```bash
# 1. One-time setup
bash setup.sh

# 2. Run everything via Airflow (recommended)
bash run.sh airflow

# 3. Or run phases manually
bash run.sh phase1    # Kafka + PostgreSQL scraping
bash run.sh phase2    # PySpark transformation
bash run.sh phase3    # Load to SQL Server DWH

# 4. Start the ML API
cd Phase_5_ML_Model
uvicorn smartcity_api:app --reload --port 8000
# Docs: http://localhost:8000/docs
```

---

## 🔗 Service Endpoints

| Service | URL | Credentials |
|---|---|---|
| Airflow UI | http://localhost:8085 | `admin / admin` |
| Kafka UI | http://localhost:8080 | — |
| PostgreSQL (Bronze) | `localhost:5432` | `smartcity / smartcity123` |
| SQL Server (DWH) | `localhost:1433` | `sa / YourPassword` |
| ML API Docs | http://localhost:8000/docs | — |

---

*Built with ❤️ by the SmartCity Team · Faculty of Engineering · Menofia University · Alexandria, Egypt*
