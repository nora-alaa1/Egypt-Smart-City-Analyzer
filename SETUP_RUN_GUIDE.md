# 🚀 Setup & Run — SmartCity Analyzer

> دليل تشغيل المشروع خطوة بخطوة باستخدام ملفين بس: `setup.sh` و `run.sh`
> Works on: **Linux · macOS · Git Bash (Windows)**

---

## قبل ما تبدأي (Prerequisites)

| الأداة | الإصدار | رابط التحميل |
|---|---|---|
| Docker Desktop | latest | https://docs.docker.com/get-docker/ |
| Git Bash (Windows فقط) | latest | https://git-scm.com/downloads |

> تأكدي إن Docker Desktop شغّال قبل أي خطوة.

---

## الخطوة الأولى — `setup.sh`

ملف بيتشغل **مرة واحدة بس** عند أول إعداد للمشروع.

```bash
bash setup.sh
```

### اللي بيعمله

| # | الخطوة | التفاصيل |
|---|---|---|
| 1 | فحص Docker | بيتأكد إن Docker مثبّت |
| 2 | فحص Docker Compose | بيتأكد إن الإصدار v2+ موجود |
| 3 | فحص الـ Daemon | بيتأكد إن Docker شغّال فعلاً |
| 4 | فحص الـ Ports | بيتأكد إن المنافذ المطلوبة مش محجوزة |
| 5 | إنشاء المجلدات | `output_all/` · `gold_output/` · `airflow/logs` |
| 6 | إعداد `.env` | بينسخ `.env.example` → `.env` تلقائياً |
| 7 | Pull Docker Images | بينزّل كل الـ images المطلوبة |

### المنافذ المطلوبة (Ports)

| Port | Service |
|---|---|
| 2181 | Zookeeper |
| 9092 | Kafka |
| 8080 | Kafka UI |
| 5432 | PostgreSQL (Bronze) |
| 5433 | PostgreSQL (Airflow) |
| 8085 | Airflow UI |

### بعد `setup.sh` — خطوة مهمة ⚠️

افتحي ملف `smartcity-airflow/.env` وعدّلي هذه القيم:

```bash
# مسار مجلد المشروع على جهازك
SMARTCITY_PROJECT_PATH=C:/Users/YourName/Downloads/SmartCityAnalyzer-main
SMARTCITY_HOST_PATH=C:/Users/YourName/Downloads/SmartCityAnalyzer-main

# باسورد SQL Server
SQLSERVER_PASSWORD=YourStrong@Passw0rd
```

---

## الخطوة التانية — `run.sh`

ملف للتحكم في تشغيل وإيقاف المشروع.

```bash
bash run.sh <command>
```

### الأوامر المتاحة

| Command | الوظيفة |
|---|---|
| `bash run.sh airflow` | تشغيل Airflow — بيشغّل كل المراحل تلقائياً |
| `bash run.sh phase1` | تشغيل Phase 1 فقط (Kafka + PostgreSQL) |
| `bash run.sh phase2` | تشغيل Phase 2 فقط (PySpark Transform) |
| `bash run.sh phase3` | تشغيل Phase 3 فقط (تحميل SQL Server) |
| `bash run.sh stop` | إيقاف كل الـ services |
| `bash run.sh status` | عرض الـ containers الشغّالة |
| `bash run.sh logs` | متابعة كل الـ logs |
| `bash run.sh logs <service>` | متابعة logs service معين |
| `bash run.sh clean` | حذف كل الـ containers والـ volumes (⚠️ بيمسح الداتا) |

---

## التشغيل الكامل (Full Pipeline)

### الطريقة 1 — عن طريق Airflow (الموصى بيها)

```bash
# المرة الأولى بس
bash setup.sh

# تشغيل Airflow
bash run.sh airflow
```

بعد كده افتحي: **http://localhost:8085**
- Username: `admin`
- Password: `admin`

دوّري على DAG اسمه `smartcity_full_pipeline` ← اضغطي **Trigger DAG**

---

### الطريقة 2 — تشغيل كل مرحلة لوحدها (يدوي)

```bash
# المرحلة الأولى: جمع البيانات
bash run.sh phase1

# بعد ما Phase 1 يخلص
bash run.sh phase2

# بعد ما Phase 2 يخلص
bash run.sh phase3
```

---

## أوامر مفيدة

```bash
# شوفي إيه الشغّال
bash run.sh status

# تابعي logs الـ Airflow
bash run.sh logs airflow-scheduler

# تابعي logs الـ Kafka
bash run.sh logs kafka

# وقّفي كل حاجة
bash run.sh stop

# امسحي كل حاجة (⚠️ بيمسح الداتا)
bash run.sh clean
```

---

## Service Endpoints

| Service | URL / Port | Login |
|---|---|---|
| Airflow UI | http://localhost:8085 | admin / admin |
| Kafka UI | http://localhost:8080 | — |
| PostgreSQL (Bronze) | localhost:5432 | smartcity / smartcity123 |
| PostgreSQL (Airflow) | localhost:5433 | airflow / airflow |
| SQL Server (DWH) | localhost:1433 | sa / (باسوردك) |

---

## مشاكل شائعة (Troubleshooting)

**❌ Port already in use**
```bash
# شوفي مين بيستخدم البورت (مثال 9092)
netstat -ano | findstr :9092    # Windows
lsof -i :9092                  # Linux/Mac
```

**❌ Docker daemon is not running**
> شغّلي Docker Desktop وانتظري لحد ما تظهر علامة ✓ في الـ taskbar

**❌ setup.sh مش شغّال على Windows**
> استخدمي Git Bash مش CMD أو PowerShell

**❌ Phase 3 مش واصل لـ SQL Server**
> في `smartcity-airflow/.env` غيّري:
> `SQLSERVER_HOST=host.docker.internal`
