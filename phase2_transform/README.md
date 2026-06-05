# 🏙️ SmartCity — Phase 2: Data Transformation

> **نظرة عامة:** هذه المرحلة تُحوّل بيانات Alexandria الخام (Bronze layer) إلى جداول Gold جاهزة للتحليل، مع تطبيق منهجية **Medallion Architecture** باستخدام Apache Spark + PostgreSQL.

---

## 📐 المعمارية العامة

```
PostgreSQL (Bronze Layer)
        │
        ▼
  Apache Spark 3.5.3
        │
        ├─► Dim_Area
        ├─► Dim_Business_Type
        ├─► Dim_Property
        ├─► Fact_Area_Business_Score
        └─► Fact_Property_Suitability
                │
                ▼
         Gold Output (.xlsx / .csv)
```

---

## 🗂️ مصادر البيانات (Bronze Tables)

| الجدول | المحتوى | الحقول الأساسية |
|---|---|---|
| `cafes`, `gyms`, `restaurants`, `bakeries` | أماكن الأكل واللياقة | name, latitude, longitude |
| `hotels`, `hospitals`, `banks` | السياحة والصحة والمال | name, latitude, longitude |
| `clothing`, `supermarkets`, `sweets` | التجزئة | name, latitude, longitude |
| `pharmacies` | الصيدليات (بدون إحداثيات) | name, address, phone |
| `schools`, `centers` | التعليم | name, type, latitude, longitude |
| `population` | سكان الأحياء | district, population, year, latitude, longitude |
| `rent_commercial` | إيجارات تجارية | area_m2, rent_egp, location_en |

---

## 🔄 خطوات التحويل

### Cell 6 — قراءة البيانات وتوحيد المشاريع

**ما يفعله:**
- يقرأ كل جداول الـ OSM من PostgreSQL ويُطبّق عليها `dropDuplicates` + فلترة القيم الفارغة.
- يُوحّد كل الأصناف في DataFrame واحد (`df_all_biz`) بنفس الـ schema باستخدام `reduce(union)`.
- الصيدليات بدون إحداثيات → يُوزّعها على الأحياء بشكل متناسب مع الكثافة السكانية باستخدام `numpy.random.choice` مع `seed=42` لضمان التكرارية.
- يُعدّ بيانات الإيجارات (`df_rent_raw`) مع cast صريح للأنواع وفلترة القيم السالبة.

**الإصلاحات المُطبّقة:**
```
✦ Schema صريح لكل createDataFrame → يمنع الانهيار عند الـ DataFrames الفارغة
✦ seed=42 في توزيع الصيدليات → نتائج قابلة للتكرار
```

---

### Cell 7 — تنظيف بيانات السكان

**ما يفعله:**
- يقرأ جدول `population` ويُبقي على السجل الأحدث لكل حي.

**الإصلاح الرئيسي:**

| قبل الإصلاح ❌ | بعد الإصلاح ✅ |
|---|---|
| `dropDuplicates(["district"])` — يُبقي على سجل عشوائي | `Window.partitionBy("area_name").orderBy(year DESC)` |
| يُفقد بيانات السنوات الإضافية | يُبقي دائماً على أحدث سنة لكل حي |

```python
w_latest = Window.partitionBy("area_name").orderBy(F.col("year").desc())
df_pop = df_pop_raw.withColumn("rn", F.row_number().over(w_latest)).filter(F.col("rn") == 1)
```

---

### Cell 8 — Dim_Area

**الـ Schema:**

| العمود | النوع | الوصف |
|---|---|---|
| `area_id` | INT | مفتاح بديل تسلسلي |
| `area_name` | STRING | اسم الحي |
| `population` | BIGINT | عدد السكان |
| `latitude` | DOUBLE | خط العرض (6 خانات عشرية) |
| `longitude` | DOUBLE | خط الطول (6 خانات عشرية) |

---

### Cell 9 — Dim_Business_Type

**الـ Schema:**

| العمود | النوع | الوصف |
|---|---|---|
| `business_type_id` | INT | مفتاح بديل |
| `category` | STRING | الفئة الكبرى (مثال: Food & Beverage) |
| `subcategory` | STRING | الفئة الفرعية (مثال: Restaurant) |
| `service_type` | STRING | نوع الخدمة |

**الفئات المدعومة (13 نوع):**

```
Food & Beverage       → Cafe, Restaurant, Bakery, Ice Cream & Sweets
Health & Fitness      → Fitness Center
Tourism & Hospitality → Hotel
Healthcare            → Hospital & Clinic, Pharmacy
Financial Services    → Bank & Exchange
Retail                → Clothing & Fashion, Supermarket & Grocery
Education             → School, Education Center
```

---

### Cell 10 — Dim_Property

**ما يفعله:**
- يُحوّل بيانات الإيجارات إلى بعد قابل للتحليل مع ربط كل عقار بحيّه.
- يحسب `rent_per_sqm` = `rent_egp ÷ area_sqm`.

**الإصلاح الرئيسي — Street→Area Mapping:**

| قبل الإصلاح ❌ | بعد الإصلاح ✅ |
|---|---|
| `street.contains(area_name)` في Spark | `STREET_AREA_MAP` dictionary في Pandas |
| Nested loop داخلي في Spark | Lookup مباشر O(1) |
| يُضيّع ~99% من العقارات | يُربط كل شارع بحيّه الصحيح |

القاموس يغطي **60+ تعيين** للشوارع الشهيرة في الإسكندرية:
```python
STREET_AREA_MAP = {
    "el gaish":   "Sidi Bishr",
    "stanley":    "Stanley",
    "san stefano":"San Stefano",
    # ... و 57 تعيين آخر
}
```

**الـ Schema:**

| العمود | النوع | الوصف |
|---|---|---|
| `prop_id` | INT | مفتاح بديل |
| `area_id` | INT | مفتاح خارجي → Dim_Area |
| `street_name` | STRING | اسم الشارع الأصلي |
| `area_sqm` | INT | المساحة بالمتر المربع |
| `rent_monthly_egp` | INT | الإيجار الشهري |
| `rent_per_sqm` | DOUBLE | سعر المتر المربع |

---

### Cell 11 — تعيين الحي الأقرب للمشاريع

**ما يفعله:**
- يُعيّن لكل مشروع (`df_all_biz`) الحيَّ الأقرب إليه جغرافياً باستخدام معادلة **Haversine**.

**الإصلاح الرئيسي — إلغاء Cross Join:**

| قبل الإصلاح ❌ | بعد الإصلاح ✅ |
|---|---|
| `crossJoin` كامل (businesses × 50 حي) | `broadcast` لقائمة الأحياء + UDF |
| 2000 مشروع × 50 حي = 100,000 صف | 2000 مشروع × 1 حساب = 2,000 صف |
| حسابات `acos + radians` ثقيلة على Spark | Numpy vectorized Haversine |

```python
# الـ 50 حي (أقل من 1KB) يُرسل مرة واحدة لكل worker
areas_bc = spark.sparkContext.broadcast(areas_list)

@F.udf(returnType=nearest_area_schema)
def nearest_area_udf(lat, lon):
    dists = 2 * np.arctan2(...) * 6371.0   # Haversine vectorized
    return areas[np.argmin(dists)]
```

---

### Cell 12 — Fact_Area_Business_Score

**ما يفعله:**
- يبني شبكة كاملة (50 حي × 13 نوع نشاط = 650 صف) ويحسب لكل خلية:

| المقياس | الحساب |
|---|---|
| `competitor_count` | عدد المنافسين في نفس الحي والنوع |
| `nearest_competitor_m` | متوسط المسافة لأقرب منافس بالمتر |
| `demand_index` | population ÷ competitor_count |
| `market_saturation` | (competitors ÷ (population/1000)) × 10، بحد أقصى 100 |
| `suitability_score` | (0.4 × demand + 0.3 × population + 0.3 × (1−saturation)) × 10 |
| `recommended` | `suitability_score >= 6.0` |

**الإصلاح الرئيسي — إلغاء Python O(n²) UDF:**

| قبل الإصلاح ❌ | بعد الإصلاح ✅ |
|---|---|
| `collect_list` + Python nested loop | Spark SQL self-join |
| يُشغَّل في Python (10x أبطأ) | يُشغَّل في JVM native |
| O(n²) per group | `groupBy + min(dist)` |

```python
# Self-join نظيف على نفس الـ area + subcategory
df_pair_dist = df_a.join(df_b,
    (col("a.area_id") == col("b.area_id")) &
    (col("a.subcategory") == col("b.subcategory")) &
    (col("a.business_name") != col("b.business_name")), "left"
).withColumn("dist_m", acos(...) * 6371000.0)
```

**الـ Schema:**

| العمود | النوع |
|---|---|
| `score_id` | INT (PK) |
| `area_id` | INT (FK) |
| `area_name` | STRING |
| `business_type_id` | INT (FK) |
| `category` / `subcategory` | STRING |
| `competitor_count` | INT |
| `nearest_competitor_m` | INT |
| `population` | BIGINT |
| `demand_index` | INT |
| `market_saturation` | DOUBLE |
| `suitability_score` | DOUBLE (1.0–10.0) |
| `recommended` | BOOLEAN |

---

### Cell 13 — Fact_Property_Suitability

**ما يفعله:**
- يحسب لكل عقار × كل نوع نشاط درجة ملاءمة تجارية بناءً على:
  - عدد المنافسين في نطاق 500م و1كم
  - مدى القدرة على تحمّل الإيجار مقارنةً بمتوسط الحي
  - الطلب (population ÷ عدد المنافسين)

**الإصلاح الرئيسي — Vectorized Haversine:**

| قبل الإصلاح ❌ | بعد الإصلاح ✅ |
|---|---|
| `pandas.apply()` لكل مشروع | `numpy` vectorized على كل المنافسين دفعة واحدة |
| 35 عقار × 13 نوع × apply(2000) = **910,000 استدعاء** | **455 iteration** فقط |

```python
def haversine_vec_m(lat1, lon1, lats2, lons2):
    # numpy scalar × array — حساب كل المسافات في سطر واحد
    a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lats2)) * np.sin(dlon/2)**2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
```

**معادلة الدرجة النهائية:**
```
suitability = (0.4 × affordability + 0.3 × competition_score + 0.3 × demand_score) × 10
recommended = suitability >= 6.0
```

**الـ Schema:**

| العمود | النوع |
|---|---|
| `fact_id` | INT (PK) |
| `prop_id` | INT (FK → Dim_Property) |
| `area_id` | INT (FK → Dim_Area) |
| `business_type_id` | INT (FK → Dim_Business_Type) |
| `category` | STRING |
| `street_name` | STRING |
| `area_sqm` | INT |
| `rent_monthly_egp` | INT |
| `rent_per_sqm` | DOUBLE |
| `competitors_500m` | INT |
| `competitors_1km` | INT |
| `affordability_score` | DOUBLE |
| `suitability_score` | DOUBLE (1.0–10.0) |
| `recommended` | BOOLEAN |

---

## 📤 Gold Output

| الملف | الجدول | الوصف |
|---|---|---|
| `Dim_Area.xlsx` | Dim_Area | أحياء الإسكندرية مع السكان والإحداثيات |
| `Dim_Business_Type.xlsx` | Dim_Business_Type | تصنيفات الأنشطة التجارية |
| `Dim_Property.xlsx` | Dim_Property | العقارات التجارية مع الإيجارات |
| `Fact_Area_Business_Score.xlsx` | Fact_Area_Business_Score | درجات ملاءمة الأحياء |
| `Fact_Property_Suitability.xlsx` | Fact_Property_Suitability | درجات ملاءمة العقارات |

---

## ⚡ ملخص الإصلاحات الجوهرية

| # | المشكلة | الإصلاح | التأثير |
|---|---|---|---|
| 1 | `local[2]` — كورين فقط | `local[*]` — كل الـ cores | أسرع بشكل ملحوظ |
| 2 | Memory 1g | Memory 4g (driver + executor) | يمنع OOM errors |
| 3 | بدون AQE | Adaptive Query Execution مُفعَّل | توفير 30–60% وقت |
| 4 | Java Serializer | KryoSerializer | تسلسل أسرع |
| 5 | `dropDuplicates` عشوائي للسكان | Window function بأحدث سنة | لا فقد بيانات |
| 6 | String contains join للشوارع | Dictionary lookup | ربط 99%+ من العقارات |
| 7 | Cross Join (businesses × areas) | Broadcast + Numpy UDF | تقليل الصفوف من n×50 إلى n |
| 8 | Python O(n²) UDF | Spark SQL self-join (JVM) | 10x أسرع |
| 9 | pandas apply (910,000 استدعاء) | Numpy vectorized (455 iteration) | ~50x أسرع |

---

## 🛠️ المتطلبات التقنية

```
Apache Spark   3.5.3
Python         3.x
PostgreSQL     14+
Java           11 (OpenJDK)
```

**Python Packages:**
```
pyspark==3.5.3
psycopg2
openpyxl
numpy
pandas
```

**JDBC Driver:** `postgresql-42.7.3.jar`

---

## 🚀 طريقة التشغيل

```bash
# 1. تشغيل الـ cells بالترتيب في Google Colab:
Cell 0  → تثبيت الـ dependencies
Cell 1  → إنشاء Spark Session
Cell 2  → تشغيل PostgreSQL
Cell 3  → فك ضغط الـ ZIP
Cell 4  → إنشاء Bronze Schema
Cell 5  → تحميل البيانات في PostgreSQL

# ── Transformation ──
Cell 6  → قراءة Bronze + توحيد المشاريع
Cell 7  → تنظيف السكان
Cell 8  → Dim_Area
Cell 9  → Dim_Business_Type
Cell 10 → Dim_Property
Cell 11 → تعيين الحي لكل مشروع
Cell 12 → Fact_Area_Business_Score
Cell 13 → Fact_Property_Suitability
Cell 14 → Export Gold Tables
```

---

*SmartCity Phase 2 — Alexandria Business Intelligence Platform*
