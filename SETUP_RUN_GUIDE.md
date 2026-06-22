# دليل التشغيل — SmartCity Analyzer
# Setup & Run Guide

> يتضمّن هذا الدليل شرحاً تفصيلياً لخطوات إعداد البيئة وتشغيل المشروع باستخدام ملفَّي `setup.sh` و `run.sh`.
> متوافق مع: **Linux · macOS · Git Bash (Windows)**

---

## المتطلبات الأساسية (Prerequisites)

قبل البدء، يجب التأكد من تثبيت المتطلبات التالية:

| الأداة | الإصدار | رابط التحميل |
|---|---|---|
| Docker Desktop | latest | https://docs.docker.com/get-docker/ |
| Git Bash (لمستخدمي Windows) | latest | https://git-scm.com/downloads |

> **ملاحظة:** يجب التأكد من أن Docker Desktop يعمل بشكل كامل قبل تنفيذ أي خطوة.

---

## المرحلة الأولى — إعداد البيئة (`setup.sh`)

يُنفَّذ هذا الملف **مرةً واحدةً فقط** عند الإعداد الأولي للمشروع. يقوم بالتحقق من المتطلبات وتجهيز البيئة تلقائياً.

```bash
bash setup.sh
```

### الخطوات التي ينفذها الملف

| # | الخطوة | الوصف |
|---|---|---|
| 1 | التحقق من Docker | يتأكد من وجود Docker وتثبيته |
| 2 | التحقق من Docker Compose | يتأكد من توافر الإصدار v2 أو أحدث |
| 3 | التحقق من تشغيل الـ Daemon | يتأكد من أن Docker daemon يعمل فعلياً |
| 4 | فحص المنافذ المطلوبة | يتحقق من أن المنافذ التالية غير محجوزة |
| 5 | إنشاء المجلدات اللازمة | `output_all/` · `gold_output/` · `airflow/logs/` |
| 6 | إعداد ملف البيئة | نسخ `.env.example` إلى `.env` تلقائياً |
| 7 | تنزيل Docker Images | تحميل جميع الصور المطلوبة لتشغيل الخدمات |

### المنافذ المطلوبة (Required Ports)

يجب أن تكون المنافذ التالية متاحةً قبل التشغيل:

| Port | الخدمة |
|---|---|
| 2181 | Zookeeper |
| 9092 | Kafka Broker |
| 8080 | Kafka UI |
| 5432 | PostgreSQL — Bronze Layer |
| 5433 | PostgreSQL — Airflow Metadata |
| 8085 | Airflow Web UI |

### إعداد ملف البيئة بعد `setup.sh`

بعد اكتمال تنفيذ الملف، يجب تعديل المتغيرات التالية في `SmartCity-Airflow/.env`:

```bash
# المسار المطلق لمجلد المشروع على الجهاز
SMARTCITY_PROJECT_PATH=C:/Users/YourName/Downloads/SmartCityAnalyzer-main
SMARTCITY_HOST_PATH=C:/Users/YourName/Downloads/SmartCityAnalyzer-main

# كلمة مرور SQL Server
SQLSERVER_PASSWORD=YourStrong@Passw0rd
```

---

## المرحلة الثانية — تشغيل المشروع (`run.sh`)

يوفّر هذا الملف واجهةً موحّدةً للتحكم في جميع خدمات المشروع عبر أوامر بسيطة.

```bash
bash run.sh <command>
```

### الأوامر المتاحة

| الأمر | الوظيفة |
|---|---|
| `bash run.sh airflow` | تشغيل Airflow الذي يُشغّل جميع المراحل تلقائياً بالترتيب |
| `bash run.sh phase1` | تشغيل المرحلة الأولى فقط — Kafka و PostgreSQL |
| `bash run.sh phase2` | تشغيل المرحلة الثانية فقط — PySpark Transform |
| `bash run.sh phase3` | تشغيل المرحلة الثالثة فقط — تحميل البيانات إلى SQL Server |
| `bash run.sh stop` | إيقاف جميع الخدمات الجارية |
| `bash run.sh status` | عرض قائمة بالـ containers العاملة حالياً |
| `bash run.sh logs` | متابعة سجلات جميع الخدمات |
| `bash run.sh logs <service>` | متابعة سجلات خدمة محددة |
| `bash run.sh clean` | إيقاف الخدمات وحذف جميع البيانات والـ volumes |

---

## طرق التشغيل

### الطريقة الأولى — التشغيل الكامل عبر Airflow *(الموصى بها)*

تُعدّ هذه الطريقة الأنسب لتشغيل المشروع بالكامل، إذ يتولى Airflow جدولة المراحل وتنفيذها بالترتيب الصحيح تلقائياً.

```bash
# عند الإعداد الأول فقط
bash setup.sh

# تشغيل Airflow
bash run.sh airflow
```

بعد التشغيل، يمكن الوصول إلى واجهة Airflow من خلال:

```
URL      : http://localhost:8085
Username : admin
Password : admin
```

للبدء يدوياً: ابحث عن DAG باسم `smartcity_full_pipeline` ← اضغط **Trigger DAG**

---

### الطريقة الثانية — التشغيل اليدوي مرحلةً بمرحلة

تُستخدم هذه الطريقة عند الحاجة إلى تشغيل مرحلة بعينها أو اختبار جزء محدد من المشروع.

```bash
# المرحلة الأولى: جمع البيانات وتخزينها في PostgreSQL
bash run.sh phase1

# المرحلة الثانية: التحويل بـ PySpark (بعد اكتمال Phase 1)
bash run.sh phase2

# المرحلة الثالثة: تحميل البيانات إلى SQL Server (بعد اكتمال Phase 2)
bash run.sh phase3
```

---

## عناوين الخدمات (Service Endpoints)

| الخدمة | العنوان | بيانات الدخول |
|---|---|---|
| Airflow UI | http://localhost:8085 | admin / admin |
| Kafka UI | http://localhost:8080 | — |
| PostgreSQL (Bronze) | localhost:5432 | smartcity / smartcity123 |
| PostgreSQL (Airflow) | localhost:5433 | airflow / airflow |
| SQL Server (DWH) | localhost:1433 | sa / كلمة المرور المحددة |

---

## استعلامات مفيدة بعد التشغيل

```bash
# عرض حالة جميع الخدمات
bash run.sh status

# متابعة سجلات Airflow Scheduler
bash run.sh logs airflow-scheduler

# متابعة سجلات Kafka
bash run.sh logs kafka

# إيقاف جميع الخدمات
bash run.sh stop
```

---

## حل المشكلات الشائعة (Troubleshooting)

**المشكلة: منفذ مُستخدم مسبقاً (Port already in use)**

```bash
# Windows
netstat -ano | findstr :9092

# Linux / macOS
lsof -i :9092
```

يجب إيقاف الخدمة التي تشغل هذا المنفذ قبل المتابعة.

---

**المشكلة: Docker daemon غير مُشغَّل**

يجب تشغيل Docker Desktop والانتظار حتى تظهر علامة التشغيل الكاملة في شريط المهام قبل إعادة المحاولة.

---

**المشكلة: الملف لا يعمل على Windows**

يجب تشغيل الملف عبر **Git Bash** وليس CMD أو PowerShell.

---

**المشكلة: Phase 3 لا يستطيع الاتصال بـ SQL Server**

في ملف `SmartCity-Airflow/.env`، قم بتعديل المتغير التالي:

```bash
SQLSERVER_HOST=host.docker.internal
```
