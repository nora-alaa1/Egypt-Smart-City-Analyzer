# 🤖 Phase 5 — SmartCity AI Model & API

> **تصنيف ملاءمة العقارات للأنشطة التجارية باستخدام Machine Learning**

---

## 📌 نظرة عامة

هذه المرحلة تُضيف طبقة الذكاء الاصطناعي على البيانات المُعالَجة في مراحل سابقة من المشروع.
الموديل يتصل مباشرةً بـ **SQL Server DWH** ويُدرِّب نموذجَين مستقلَّين، ثم يُكشَف عنهما عبر **FastAPI REST API** يمكن لأي Frontend أو تطبيق خارجي استهلاكه.

---

## 🗂️ هيكل الملفات

```
Phase_5_ML_Model/
├── SmartCity_Model_v2.ipynb   ← Notebook التدريب الكامل (11 Cell)
├── smartcity_api.py           ← FastAPI server
├── smartcity_meta.json        ← Metadata (يُنتَج بعد التدريب)
├── requirements.txt           ← Python dependencies
└── README.md                  ← هذا الملف
```

> ⚠️ **ملاحظة:** ملف `smartcity_model.pkl` **لا يُرفع على GitHub** — حجمه كبير وبيُتعمل من الـ Notebook تلقائياً.
> أضيفي هذا السطر في `.gitignore`:
> ```
> smartcity_model.pkl
> ```

---

## ⚙️ المتطلبات

### 1. Python Libraries

```bash
pip install -r requirements.txt
```

**المكتبات الأساسية:**

| Library | الاستخدام |
|---|---|
| `scikit-learn` | تدريب الـ Models وتقييمها |
| `pandas` / `numpy` | معالجة البيانات |
| `pyodbc` + `sqlalchemy` | الاتصال بـ SQL Server |
| `fastapi` + `uvicorn` | تشغيل الـ REST API |
| `pydantic` | التحقق من صحة البيانات في الـ API |

### 2. SQL Server

يجب أن يكون الـ DWH جاهزاً وفيه الجداول:
- `Dim_Area`
- `Dim_Business_Type`
- `Fact_Property_Suitability`

> اسم الـ Database الافتراضي: `SmartCity`

---

## 🚀 خطوات التشغيل

### الخطوة 1 — تعديل إعدادات الاتصال (Cell 2 في الـ Notebook)

```python
DB_SERVER = r"YOUR_PC\MSSQLSERVER01"  # ← غيّري لاسم السيرفر عندك
DB_NAME   = "SmartCity"
DB_DRIVER = "ODBC Driver 17 for SQL Server"
```

### الخطوة 2 — تشغيل الـ Notebook

شغّلي الـ Cells بالترتيب من 1 إلى 8:

| Cell | المحتوى |
|---|---|
| 1 | تثبيت المكتبات |
| 2 | إعدادات الاتصال |
| 3 | تحميل البيانات من SQL Server |
| 4 | استكشاف البيانات (EDA) |
| 5 | تجهيز البيانات للتدريب |
| 6 | تدريب **Model A** — Tier Classifier |
| 7 | تدريب **Model B** — Score Regressor |
| 8 | حفظ `smartcity_model.pkl` و `smartcity_meta.json` |

بعد Cell 8، يمكنك استخدام Cells 9 و 10 للاختبار اليدوي.

### الخطوة 3 — تشغيل الـ API

افتحي Terminal جديد وشغّلي:

```bash
uvicorn smartcity_api:app --reload --port 8000
```

ثم افتحي المتصفح على:

```
http://localhost:8000/docs
```

---

## 🧠 المودلين المُدرَّبَين

### Model A — Tier Classifier (RandomForestClassifier)

يُصنّف درجة الملاءمة إلى ثلاثة مستويات:

| التصنيف | نطاق الدرجة |
|---|---|
| `High` | 7.5 — 10 |
| `Medium` | 5.0 — 7.4 |
| `Low` | أقل من 5.0 |

**الإعدادات:**
```python
RandomForestClassifier(
    n_estimators  = 200,
    max_depth     = 8,
    class_weight  = "balanced",
    random_state  = 42
)
```

**التقييم:** 5-Fold Stratified Cross-Validation

---

### Model B — Score Regressor (GradientBoostingRegressor)

يُقدِّر درجة الملاءمة كرقم مستمر من **1.0 إلى 10.0**.

**الإعدادات:**
```python
GradientBoostingRegressor(
    n_estimators  = 300,
    learning_rate = 0.05,
    max_depth     = 4,
    subsample     = 0.8,
    random_state  = 42
)
```

**مقاييس التقييم:** MAE و R² عبر Cross-Validation

---

### 📊 Features المُستخدَمة في التدريب

| Feature | الوصف |
|---|---|
| `area_sqm` | مساحة العقار بالمتر المربع |
| `rent_per_sqm` | الإيجار لكل متر مربع |
| `affordability` | مؤشر مُحسوب لتناسب الإيجار مع السوق |
| `comp_500m` | عدد المنافسين في نطاق 500 متر |
| `comp_1km` | عدد المنافسين في نطاق 1 كيلومتر |
| `population` | عدد سكان المنطقة |
| `category_enc` | نوع النشاط التجاري (مُرمَّز بـ LabelEncoder) |

---

## 🌐 API Endpoints

### `GET /`
Health check — التحقق من أن الـ API يعمل.

---

### `GET /categories`
يُرجع قائمة بأنواع الأنشطة التجارية المتاحة في الموديل.

**Response:**
```json
{
  "categories": ["Food & Beverage", "Healthcare", "Retail", ...]
}
```

---

### `GET /areas`
يُرجع قائمة بالمناطق وأرقام تعريفها.

**Response:**
```json
{
  "areas": { "1": "Agami", "2": "Al-Anfushi", ... }
}
```

---

### `POST /predict`
يُنبّئ بدرجة ملاءمة عقار واحد.

**Request Body:**
```json
{
  "area_sqm":  120,
  "rent_egp":  30000,
  "category":  "Food & Beverage",
  "area_id":   5,
  "comp_500m": 1,
  "comp_1km":  3
}
```

**Response:**
```json
{
  "area_name":    "Attarin",
  "category":     "Food & Beverage",
  "score":        7.84,
  "tier":         "High",
  "recommended":  true,
  "rent_per_sqm": 250.0
}
```

---

### `POST /recommend`
يُرجع أفضل المناطق لنشاط معين وميزانية محددة.

**Request Body:**
```json
{
  "category": "Retail",
  "max_rent": 80000,
  "area_sqm": 150,
  "top_n":    10
}
```

**Response:**
```json
{
  "category": "Retail",
  "results": [
    {
      "area_id":      12,
      "area_name":    "Smouha",
      "score":        8.21,
      "tier":         "High",
      "est_rent_egp": 67500,
      "population":   95000
    },
    ...
  ]
}
```

---

## 📦 Artifacts المُنتَجة

| الملف | الوصف |
|---|---|
| `smartcity_model.pkl` | الموديل الكامل (Classifier + Regressor + Encoders + Training Data) |
| `smartcity_meta.json` | Metadata خفيف للـ Frontend (المناطق، الأنواع، مقاييس الأداء) |

---

## 🔗 الارتباط بمراحل المشروع

```
Phase 1 — Ingestion (Kafka)
      ↓
Phase 2 — Processing (PySpark)
      ↓
Phase 3 — DWH (SQL Server Star Schema)
      ↓
Phase 4 — Orchestration (Airflow)
      ↓
Phase 5 — AI Model & API  ← أنتِ هنا
```

---

*SmartCity Analyzer — Alexandria Urban Intelligence Pipeline*
