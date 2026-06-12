# Airflow Orchestrator

> Automates the full SmartCity pipeline: **Kafka → Bronze → PySpark → SQL Server DWH**
> DAG: `smartcity_full_pipeline` · Schedule: every 6 months · UI: http://localhost:8085

---

## DAG Flow

```
start_infrastructure
        │
  wait_kafka_healthy
        │
        ├── p01_rental_producer  → p01_rental_consumer  ─┐
        ├── p02_business_producer → p02_business_consumer │
        ├── p03_education_producer → p03_education_consumer│  all parallel
        ├── p04_population_producer → p04_population_consumer│
        └── p05_traffic_producer → p05_traffic_consumer  ─┤
                                                           │
                          ┌────────────────────────────────┘
                          │
                    bronze_loader ←── cleanup_kafka
                          │
               phase2_spark_transform
                          │
              phase3_create_dwh_schema
                          │
             phase3_load_gold_to_sqlserver
                          │
           phase3_apply_constraints_indexes
```

---

## Task Summary

| Task | Timeout | Retries | Description |
|---|---|---|---|
| `start_infrastructure` | 10 min | 0 | Starts Zookeeper, Kafka, PostgreSQL |
| `wait_kafka_healthy` | 5 min | 3 | Polls Kafka every 10s (max 30 attempts) |
| `p01_rental_producer` | 3 hrs | 1 | Scrapes Aqarmap |
| `p02_business_producer` | 3 hrs | 3 | OSM + Pharmacy + Missing (30s delay between each) |
| `p03_education_producer` | 3 hrs | 1 | OSM Education |
| `p04_population_producer` | 3 hrs | 1 | CAPMAS + WorldPop + GEE |
| `p05_traffic_producer` | **2 hrs** | 1 | OSMnx road network (81k records) |
| `p0*_consumer` | 3 hrs | 2 | Consume and save to output_all/ |
| `bronze_loader` | 3 hrs | — | Loads all output_all/ → PostgreSQL |
| `cleanup_kafka` | 5 min | — | Stops Kafka after consumers finish |
| `phase2_spark_transform` | 2 hrs | 0 | PySpark notebook (Bronze → Gold) |
| `phase3_create_dwh_schema` | 10 min | 0 | Runs 01_create_schema.sql |
| `phase3_load_gold_to_sqlserver` | 1 hr | 0 | Runs load_to_sqlserver.ipynb |
| `phase3_apply_constraints_indexes` | 10 min | 0 | Runs 02–04 SQL scripts |

---

## Setup

### 1. Configure Environment

```bash
cd smartcity-airflow
cp .env.example .env
```

Edit `.env` — two things to change:

```bash
# Path to SmartCityAnalyzer-main on your machine
SMARTCITY_PROJECT_PATH=C:/Users/YourName/Downloads/SmartCityAnalyzer-main
SMARTCITY_HOST_PATH=C:/Users/YourName/Downloads/SmartCityAnalyzer-main

# SQL Server credentials
SQLSERVER_PASSWORD=YourStrong@Passw0rd
```

### 2. Initialize Airflow (first time only)

```bash
docker compose up airflow-init
```

### 3. Start Airflow

```bash
docker compose up -d
docker compose ps   # verify all services are healthy
```

### 4. Open UI & Run

```
http://localhost:8085
Username: admin
Password: admin
```

- Find DAG: `smartcity_full_pipeline`
- Enable the toggle
- Click **Trigger DAG** to run now, or wait for the schedule

---

## Services

| Service | Port | Credentials |
|---|---|---|
| Airflow Webserver | 8085 | admin / admin |
| Airflow PostgreSQL (metadata) | 5433 | airflow / airflow |

---

## Change Schedule

In `dags/smartcity_pipeline.py`:

```python
schedule_interval="0 2 1 */6 *"   # every 6 months (default)
schedule_interval="@monthly"       # every month
schedule_interval="@once"          # run once then stop
schedule_interval=None             # manual trigger only
```

---

## Troubleshooting

**Kafka not ready:**
```bash
docker logs kafka
docker network ls | grep smartcity
```

**Phase 2 fails (Spark):**
```bash
# Test notebook manually
docker run --rm --network smartcity_default \
  -v /path/to/phase2_transform:/home/jovyan/work \
  jupyter/pyspark-notebook:spark-3.5.0 \
  jupyter nbconvert --to notebook --execute SmartCity_Phase1_Fixed.ipynb
```

**Phase 3 can't reach SQL Server:**
```bash
# For SQL Server on same machine, use:
SQLSERVER_HOST=host.docker.internal

# For SQL Server on a different machine:
SQLSERVER_HOST=192.168.1.X
```

**Docker socket permission error:**
```bash
docker exec airflow_scheduler docker ps
# If error → restart with user: "0:0" (already set in docker-compose.yml)
```

---

## Monitoring

| Tool | URL |
|---|---|
| Airflow DAG runs | http://localhost:8085/dags/smartcity_full_pipeline |
| Airflow Graph view | http://localhost:8085 → Graph |
| Kafka UI (while Phase 1 running) | http://localhost:8080 |

```bash
# Follow logs for specific Airflow task
docker compose logs -f airflow-scheduler
docker compose logs -f airflow-webserver
```
