# 🏙️ SmartCity Analyzer — Apache Airflow Orchestrator

> يوركستريت الـ 3 phases كاملة: Kafka Pipelines → Spark Transform → SQL Server DWH

---

## 🗺️ الـ Pipeline Flow

```
start_infrastructure
        ↓
  wait_kafka_healthy
        ↓
┌──────────────────────────────────────────────────────────┐
│  pipeline_01_rental      (Aqarmap → XLSX)                │
│  pipeline_02_business    (OSM + Egyfinder → XLSX/CSV)    │  ← parallel
│  pipeline_03_education   (OSM → XLSX)                    │
│  pipeline_04_population  (CAPMAS + WorldPop → XLSX)      │
│  pipeline_05_traffic     (OSMnx → XLSX, ~81k records)    │
└──────────────────────────────────────────────────────────┘
        ↓                                      ↓
   bronze_loader                      cleanup_kafka_containers
   (XLSX/CSV → PostgreSQL bronze)
        ↓
  phase2_spark_transform
  (Bronze → Gold: Dim + Fact tables)
        ↓
  phase3_create_dwh_schema
        ↓
  phase3_load_gold_to_sqlserver
        ↓
  phase3_apply_constraints_indexes
```

---

## 🚀 Quick Start

### 1. المتطلبات

- Docker Desktop (مع Docker Compose v2)
- المشروع SmartCityAnalyzer-main محمّل على جهازك
- SQL Server شغّال (للـ Phase 3)

### 2. إعداد الـ Environment

```bash
# 1. انسخ ملف الـ .env
cp .env .env.local

# 2. عدّل المسار ده بمسار المشروع على جهازك
SMARTCITY_PROJECT_PATH=/path/to/SmartCityAnalyzer-main

# 3. عدّل بيانات SQL Server لو اختلفت
SQLSERVER_HOST=localhost
SQLSERVER_USER=sa
SQLSERVER_PASSWORD=YourPassword
```

### 3. تشغيل Airflow

```bash
# أول مرة فقط — بيعمل الـ DB ويعمل admin user
docker compose up airflow-init

# تشغيل كل الـ services
docker compose up -d

# تحقق إن كل حاجة شغّالة
docker compose ps
```

### 4. افتح الـ Airflow UI

```
http://localhost:8085
Username: admin
Password: admin
```

### 5. شغّل الـ DAG

- ابحث عن DAG اسمه **`smartcity_full_pipeline`**
- فعّله (Toggle من الـ UI)
- اضغط **Trigger DAG** لو عايز تشغّله دلوقتي
- أو هيشتغل أوتوماتيكي كل 6 شهور

---

## 🗂️ Project Structure

```
smartcity-airflow/
├── docker-compose.yml          ← Airflow services (webserver + scheduler + postgres)
├── .env                        ← Environment variables (عدّل SMARTCITY_PROJECT_PATH)
├── dags/
│   └── smartcity_pipeline.py   ← الـ DAG الرئيسي
├── logs/                       ← Airflow logs (بتتعمل تلقائياً)
├── plugins/                    ← Custom Airflow plugins (فاضي)
└── config/                     ← Airflow config (فاضي)
```

---

## ⚙️ Task Details

| Task | Description | Timeout |
|------|-------------|---------|
| `start_infrastructure` | يشغّل Zookeeper + Kafka + Postgres | 10 دقايق |
| `wait_kafka_healthy` | يستنّى Kafka (30 محاولة × 10 ثوانٍ) | 5 دقايق |
| `pipeline_01_rental` | Aqarmap producer + consumer | 3 ساعات |
| `pipeline_02_business` | OSM + Pharmacy + Missing producers + consumer | 3 ساعات |
| `pipeline_03_education` | Education producer + consumer | 3 ساعات |
| `pipeline_04_population` | Population producer + consumer | 3 ساعات |
| `pipeline_05_traffic` | Traffic producer + consumer (81k records) | **2 ساعات** |
| `bronze_loader` | يلود كل output_all/ → PostgreSQL | 3 ساعات |
| `cleanup_kafka_containers` | يوقف Kafka بعد التحميل | 5 دقايق |
| `phase2_spark_transform` | PySpark notebook (Bronze → Gold) | 2 ساعات |
| `phase3_create_dwh_schema` | ينفّذ 01_create_schema.sql | 10 دقايق |
| `phase3_load_gold_to_sqlserver` | ينفّذ load_to_sqlserver.ipynb | ساعة |
| `phase3_apply_constraints_indexes` | ينفّذ 02-04 SQL scripts | 10 دقايق |

---

## 🔧 Troubleshooting

### Kafka ما بتجاوبش
```bash
# شوف logs الـ kafka container
docker logs kafka

# تأكد إن الـ SmartCity network موجود
docker network ls | grep smartcity
```

### Phase 2 بتفشل
```bash
# تأكد إن الـ notebook يشتغل manually أول
docker run --rm \
  --network smartcity_default \
  -v /path/to/phase2_transform:/home/jovyan/work \
  jupyter/pyspark-notebook:spark-3.5.0 \
  jupyter nbconvert --to notebook --execute SmartCity_Phase1_Fixed.ipynb
```

### Phase 3 مش بتوصل لـ SQL Server
```bash
# تأكد من الـ connection string
SQLSERVER_HOST=host.docker.internal  # لو SQL Server على نفس الجهاز
SQLSERVER_HOST=192.168.1.X           # لو على جهاز تاني على الشبكة
```

### مشكلة في Docker socket
```bash
# تأكد إن Airflow container عنده صلاحية على Docker socket
docker exec airflow_scheduler docker ps
```

---

## 📊 Monitoring

**Airflow UI** → http://localhost:8085
- **DAGs**: شوف حالة كل run
- **Graph View**: شوف dependencies بصريًا
- **Logs**: شوف output كل task

**Kafka UI** → http://localhost:8080 (لو SmartCity containers شغّالة)

---

## 🔄 Customizing the Schedule

في ملف `dags/smartcity_pipeline.py`:

```python
# كل 6 شهور (default)
schedule_interval="0 2 1 */6 *"

# كل شهر
schedule_interval="@monthly"

# مرة واحدة بس
schedule_interval="@once"

# يدوي فقط
schedule_interval=None
```

---

*SmartCity Analyzer — Phase 1-3 Orchestrated with Apache Airflow 🇪🇬*
