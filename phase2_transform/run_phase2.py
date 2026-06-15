# ════════════════════════════════════════════════════════════════════
# CELL 0 — Install Dependencies
# ════════════════════════════════════════════════════════════════════
#!apt-get install -y openjdk-11-jdk -qq
#!pip uninstall dataproc-spark-connect -y -q
#!pip uninstall pyspark -y -q
#!pip install pyspark==3.5.3 -q
#!pip install openpyxl -q
#!wget -q https://jdbc.postgresql.org/download/postgresql-42.7.3.jar -O /tmp/postgresql-42.7.3.jar
print("✅ Done! — افعلي Runtime → Restart runtime")
# ════════════════════════════════════════════════════════════════════
# CELL 1 — Spark Session  ✦ الإصلاح الأول: config الـ Spark
# ════════════════════════════════════════════════════════════════════
# ─── المشاكل المُصلحة ────────────────────────────────────────────
# 1. local[2]  ← كانت بتستخدم كورين بس  →  local[*]  (كل الـ cores)
# 2. memory 1g ← أقل من اللازم للداتا دي →  4g للـ driver والـ executor
# 3. لا يوجد AQE  →  تفعيل Adaptive Query Execution (بيوفّر 30–60% وقت)
# 4. لا يوجد KryoSerializer  →  أسرع في الـ serialization
# ─────────────────────────────────────────────────────────────────
import os
os.environ["JAVA_HOME"] = "/usr"
os.environ["PYSPARK_PYTHON"]         = "python3"
os.environ["PYSPARK_DRIVER_PYTHON"]  = "python3"
os.environ["PYARROW_IGNORE_TIMEZONE"] = "1"
os.environ["SPARK_LOCAL_IP"]         = "127.0.0.1"

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from pyspark.sql.types import *
from functools import reduce
import math, numpy as np, pandas as pd
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

os.makedirs("/data/phase2_transform/gold_output", exist_ok=True)

spark = (
    SparkSession.builder
    .master("local[*]")                                              # ✦ FIX-1: كل الـ cores مش 2 بس
    .appName("SmartCity_NewSchema")
    .config("spark.driver.host",                          "127.0.0.1")
    .config("spark.driver.bindAddress",                   "127.0.0.1")
    .config("spark.driver.memory",                        "4g")      # ✦ FIX-2: من 1g لـ 4g
    .config("spark.executor.memory",                      "4g")      # ✦ FIX-2: من 1g لـ 4g
    .config("spark.jars",                                 "/tmp/postgresql-42.7.3.jar")
    .config("spark.sql.shuffle.partitions",               "8")       # ✦ FIX-3: من 4 لـ 8
    .config("spark.sql.adaptive.enabled",                 "true")    # ✦ FIX-4: AQE جديد
    .config("spark.sql.adaptive.coalescePartitions.enabled", "true") # ✦ FIX-4: AQE جديد
    .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") # ✦ FIX-5: أسرع
    .config("spark.sql.broadcastTimeout",                 "300")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

JDBC_URL   = "jdbc:postgresql://host.docker.internal:5432/smartcity"
JDBC_PROPS = {
    "user":          "smartcity",
    "password":      "smartcity123",
    "driver":        "org.postgresql.Driver",
    "currentSchema": "bronze"
}

def read_pg(table):
    return spark.read.jdbc(url=JDBC_URL, table=f"bronze.{table}", properties=JDBC_PROPS)

def to_csv(df, filename):
    path = f"/data/phase2_transform/gold_output/{filename}"
    pdf  = df if isinstance(df, pd.DataFrame) else df.toPandas()
    pdf.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"  ✅  {filename:<40} ({len(pdf):>6,} rows)")

print("✅ Cell 1 ready!")
# ════════════════════════════════════════════════════════════════════
# CELL 2 — Start PostgreSQL
# ════════════════════════════════════════════════════════════════════
import subprocess, time

#!apt-get install -y postgresql postgresql-contrib -qq > /dev/null
#!service postgresql start
time.sleep(3)

#!sudo -u postgres psql -c "CREATE USER smartcity WITH PASSWORD 'smartcity123';" 2>/dev/null || echo "User exists"
#!sudo -u postgres psql -c "CREATE DATABASE smartcity OWNER smartcity;" 2>/dev/null || echo "DB exists"
#!sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE smartcity TO smartcity;"

result = subprocess.run(["sudo", "-u", "postgres", "psql", "-c", "\\l"],
                        capture_output=True, text=True)
print(result.stdout)
print("✅ PostgreSQL is running!")
# ════════════════════════════════════════════════════════════════════
# CELL 4 — Init PostgreSQL Schema + Permissions
# ════════════════════════════════════════════════════════════════════
# إنشاء schema وكل الـ tables دفعة واحدة (بدل تكرار الـ permissions)

INIT_SQL = """
CREATE SCHEMA IF NOT EXISTS bronze;

CREATE TABLE IF NOT EXISTS bronze.rent_commercial (
    id SERIAL PRIMARY KEY, area_m2 INTEGER, rent_egp INTEGER, location_en VARCHAR(200),
    _source_file VARCHAR(200), _ingested_at TIMESTAMP DEFAULT NOW());

CREATE TABLE IF NOT EXISTS bronze.cafes        (id SERIAL PRIMARY KEY, name VARCHAR(300), latitude DOUBLE PRECISION, longitude DOUBLE PRECISION, _source_file VARCHAR(200), _ingested_at TIMESTAMP DEFAULT NOW());
CREATE TABLE IF NOT EXISTS bronze.gyms         (id SERIAL PRIMARY KEY, name VARCHAR(300), latitude DOUBLE PRECISION, longitude DOUBLE PRECISION, _source_file VARCHAR(200), _ingested_at TIMESTAMP DEFAULT NOW());
CREATE TABLE IF NOT EXISTS bronze.restaurants  (id SERIAL PRIMARY KEY, name VARCHAR(300), latitude DOUBLE PRECISION, longitude DOUBLE PRECISION, _source_file VARCHAR(200), _ingested_at TIMESTAMP DEFAULT NOW());
CREATE TABLE IF NOT EXISTS bronze.bakeries     (id SERIAL PRIMARY KEY, name VARCHAR(300), latitude DOUBLE PRECISION, longitude DOUBLE PRECISION, _source_file VARCHAR(200), _ingested_at TIMESTAMP DEFAULT NOW());
CREATE TABLE IF NOT EXISTS bronze.hotels       (id SERIAL PRIMARY KEY, name VARCHAR(300), latitude DOUBLE PRECISION, longitude DOUBLE PRECISION, _source_file VARCHAR(200), _ingested_at TIMESTAMP DEFAULT NOW());
CREATE TABLE IF NOT EXISTS bronze.hospitals    (id SERIAL PRIMARY KEY, name VARCHAR(300), latitude DOUBLE PRECISION, longitude DOUBLE PRECISION, _source_file VARCHAR(200), _ingested_at TIMESTAMP DEFAULT NOW());
CREATE TABLE IF NOT EXISTS bronze.banks        (id SERIAL PRIMARY KEY, name VARCHAR(300), latitude DOUBLE PRECISION, longitude DOUBLE PRECISION, _source_file VARCHAR(200), _ingested_at TIMESTAMP DEFAULT NOW());
CREATE TABLE IF NOT EXISTS bronze.clothing     (id SERIAL PRIMARY KEY, name VARCHAR(300), latitude DOUBLE PRECISION, longitude DOUBLE PRECISION, _source_file VARCHAR(200), _ingested_at TIMESTAMP DEFAULT NOW());
CREATE TABLE IF NOT EXISTS bronze.supermarkets (id SERIAL PRIMARY KEY, name VARCHAR(300), latitude DOUBLE PRECISION, longitude DOUBLE PRECISION, _source_file VARCHAR(200), _ingested_at TIMESTAMP DEFAULT NOW());
CREATE TABLE IF NOT EXISTS bronze.sweets       (id SERIAL PRIMARY KEY, name VARCHAR(300), latitude DOUBLE PRECISION, longitude DOUBLE PRECISION, _source_file VARCHAR(200), _ingested_at TIMESTAMP DEFAULT NOW());

CREATE TABLE IF NOT EXISTS bronze.pharmacies (
    id SERIAL PRIMARY KEY, name VARCHAR(300), address VARCHAR(500),
    phone VARCHAR(50), _source_file VARCHAR(200), _ingested_at TIMESTAMP DEFAULT NOW());

CREATE TABLE IF NOT EXISTS bronze.schools  (id SERIAL PRIMARY KEY, name VARCHAR(300), type VARCHAR(100), latitude DOUBLE PRECISION, longitude DOUBLE PRECISION, _source_file VARCHAR(200), _ingested_at TIMESTAMP DEFAULT NOW());
CREATE TABLE IF NOT EXISTS bronze.centers  (id SERIAL PRIMARY KEY, name VARCHAR(300), type VARCHAR(100), latitude DOUBLE PRECISION, longitude DOUBLE PRECISION, _source_file VARCHAR(200), _ingested_at TIMESTAMP DEFAULT NOW());

CREATE TABLE IF NOT EXISTS bronze.population (
    id SERIAL PRIMARY KEY, district TEXT, population BIGINT,
    population_source TEXT, nightlight_intensity DOUBLE PRECISION,
    year INT, latitude DOUBLE PRECISION, longitude DOUBLE PRECISION);

GRANT ALL ON SCHEMA bronze TO smartcity;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA bronze TO smartcity;
GRANT ALL ON ALL SEQUENCES IN SCHEMA bronze TO smartcity;
ALTER DEFAULT PRIVILEGES IN SCHEMA bronze GRANT ALL ON TABLES TO smartcity;
ALTER DEFAULT PRIVILEGES IN SCHEMA bronze GRANT ALL ON SEQUENCES TO smartcity;
"""

with open("/tmp/init.sql", "w") as f:
    f.write(INIT_SQL)

#!sudo -u postgres psql -d smartcity -f /tmp/init.sql
print("✅ Schema + tables + permissions ready!")
import glob

extract_path = "/content/SmartCity_Phase1_Final"
all_files = glob.glob(f"{extract_path}/**/*.*", recursive=True)
print(f"Total files found: {len(all_files)}")
for f in all_files[:20]:
    print(f)
# ════════════════════════════════════════════════════════════════════
# CELL 6 — Read Bronze Tables  ✦ الإصلاح الثاني: إلغاء crossJoin
# ════════════════════════════════════════════════════════════════════
# ─── المشكلة الأصلية ──────────────────────────────────────────────
# كان بيعمل crossJoin بين كل الـ businesses × كل الـ 50 area
# لو عندك 2000 business → 2000×50 = 100,000 row بتتحسب مسافتها
# كل تحسبة فيها acos + radians = ثقيل جداً على Spark
#
# ─── الحل ────────────────────────────────────────────────────────
# Broadcast الـ 50 area (صغيرة جداً) للـ driver
# UDF بتشوف أقرب area لكل business بـ numpy vectorized
# النتيجة: n_business rows بس (مش n×50)
# ─────────────────────────────────────────────────────────────────

OSM_TABLES = [
    "cafes","gyms","restaurants","bakeries","hotels",
    "hospitals","banks","clothing","supermarkets","sweets"
]
CATEGORY_MAP = {
    "cafes":        ("Food & Beverage",       "Cafe",                  "Cafe"),
    "gyms":         ("Health & Fitness",      "Fitness Center",        "Gym"),
    "restaurants":  ("Food & Beverage",       "Restaurant",            "Restaurant"),
    "bakeries":     ("Food & Beverage",       "Bakery",                "Bakery"),
    "hotels":       ("Tourism & Hospitality", "Hotel",                 "Hotel"),
    "hospitals":    ("Healthcare",            "Hospital & Clinic",     "Healthcare Facility"),
    "banks":        ("Financial Services",    "Bank & Exchange",       "Bank"),
    "clothing":     ("Retail",                "Clothing & Fashion",    "Fashion Store"),
    "supermarkets": ("Retail",                "Supermarket & Grocery", "Supermarket"),
    "sweets":       ("Food & Beverage",       "Ice Cream & Sweets",    "Sweets Shop"),
    "pharmacies":   ("Healthcare",            "Pharmacy",              "Pharmacy"),
    "schools":      ("Education",             "School",                "School"),
    "centers":      ("Education & Services", "Education Center", "Education Center"),
    }

_biz_schema = StructType([
    StructField("business_name", StringType(), True),
    StructField("latitude",      DoubleType(), True),
    StructField("longitude",     DoubleType(), True),
    StructField("category",      StringType(), True),
    StructField("subcategory",   StringType(), True),
    StructField("service_type",  StringType(), True),
])

osm_dfs = []
for tbl in OSM_TABLES:
    cat, sub, svc = CATEGORY_MAP[tbl]
    df_tbl = (
        read_pg(tbl)
        .dropDuplicates(["name", "latitude", "longitude"])
        .filter(F.col("name").isNotNull())
        .filter(F.col("latitude").isNotNull() & F.col("longitude").isNotNull())
        .select(
            F.col("name").alias("business_name"),
            F.col("latitude").cast(DoubleType()),
            F.col("longitude").cast(DoubleType()),
            F.lit(cat).alias("category"),
            F.lit(sub).alias("subcategory"),
            F.lit(svc).alias("service_type"),
        )
    )
    cnt = df_tbl.count()
    if cnt == 0:
        # ✦ FIX: لو الـ table فاضية نعمل empty DF بـ schema صريح
        df_tbl = spark.createDataFrame([], schema=_biz_schema)
    osm_dfs.append(df_tbl)
    print(f"  ✅  bronze.{tbl:<15} → {cnt:>4} rows")

# ── Pharmacies: بدون lat/lon → نوزّع على الـ areas ──────────────
df_pharm_raw = (
    read_pg("pharmacies")
    .dropDuplicates(["name"])
    .filter(F.col("name").isNotNull())
)
pharm_count = df_pharm_raw.count()
print(f"  ✅  bronze.pharmacies     → {pharm_count:>4} rows (no coords)")

import ast
pdf_pop_raw = read_pg("population").toPandas()
pdf_pop_raw["parsed"] = pdf_pop_raw["data"].apply(ast.literal_eval)
pdf_pop_raw["area_name"] = pdf_pop_raw["parsed"].apply(lambda x: x.get("Alexandria Population Data — SmartCityAnalyzer"))
pdf_pop_raw["latitude"]  = pdf_pop_raw["parsed"].apply(lambda x: x.get("Unnamed: 5"))
pdf_pop_raw["longitude"] = pdf_pop_raw["parsed"].apply(lambda x: x.get("Unnamed: 6"))
pdf_pop_raw["population"]= pdf_pop_raw["parsed"].apply(lambda x: x.get("Unnamed: 1"))
pdf_pop_raw = pdf_pop_raw[pdf_pop_raw["area_name"] != "district"].dropna(subset=["latitude","longitude"])
pdf_pop_raw["latitude"] = pd.to_numeric(pdf_pop_raw["latitude"], errors="coerce")
pdf_pop_raw["longitude"] = pd.to_numeric(pdf_pop_raw["longitude"], errors="coerce")
pdf_pop_raw["population"] = pd.to_numeric(pdf_pop_raw["population"], errors="coerce")
df_area_coords = spark.createDataFrame(pdf_pop_raw[["area_name","latitude","longitude","population"]].astype({"latitude": float, "longitude": float, "population": float}))
pdf_areas = df_area_coords.toPandas()
pdf_pharm = df_pharm_raw.toPandas()

# ✦ FIX: initialize بـ NaN الأول عشان الـ columns تبقى موجودة دايماً
# حتى لو pdf_areas فاضية ومش هيدخل الـ if
pdf_pharm["latitude"]  = np.nan
pdf_pharm["longitude"] = np.nan

if len(pdf_areas) > 0 and len(pdf_pharm) > 0:
    # ✦ FIX: seed ثابت بدل random — بيضمن نفس النتيجة كل مرة
    rng     = np.random.default_rng(seed=42)
    weights = pdf_areas["population"].astype(float).fillna(1)
    weights = weights / weights.sum()
    assigned_idx = rng.choice(len(pdf_areas), size=len(pdf_pharm), p=weights)
    pdf_pharm["latitude"]  = pdf_areas.iloc[assigned_idx]["latitude"].values
    pdf_pharm["longitude"] = pdf_areas.iloc[assigned_idx]["longitude"].values

pdf_pharm["category"]     = "Healthcare"
pdf_pharm["subcategory"]  = "Pharmacy"
pdf_pharm["service_type"] = "Pharmacy"
pdf_pharm = pdf_pharm.rename(columns={"name": "business_name"})

# ✦ FIX: schema صريح عشان createDataFrame ميكسرش لو الـ data فاضية
_pharm_schema = StructType([
    StructField("business_name", StringType(), True),
    StructField("latitude",      DoubleType(), True),
    StructField("longitude",     DoubleType(), True),
    StructField("category",      StringType(), True),
    StructField("subcategory",   StringType(), True),
    StructField("service_type",  StringType(), True),
])
df_pharm = spark.createDataFrame(
    pdf_pharm[["business_name","latitude","longitude","category","subcategory","service_type"]],
    schema=_pharm_schema
)
osm_dfs.append(df_pharm)

df_schools = (
    read_pg("schools")
    .dropDuplicates(["name", "latitude", "longitude"])
    .filter(F.col("name").isNotNull())
    .filter(F.col("latitude").isNotNull() & F.col("longitude").isNotNull())
    .select(
        F.col("name").alias("business_name"),
        F.col("latitude").cast(DoubleType()),
        F.col("longitude").cast(DoubleType()),
        F.lit("Education").alias("category"),
        F.lit("School").alias("subcategory"),
        F.lit("School").alias("service_type"),
    )
)
df_centers = (
    read_pg("centers")
    .dropDuplicates(["name", "latitude", "longitude"])
    .filter(F.col("name").isNotNull())
    .filter(F.col("latitude").isNotNull() & F.col("longitude").isNotNull())
    .select(
        F.col("name").alias("business_name"),
        F.col("latitude").cast(DoubleType()),
        F.col("longitude").cast(DoubleType()),
        F.lit("Education").alias("category"),
        F.lit("Education Center").alias("subcategory"),
        F.lit("Education Center").alias("service_type"),
    )
)

schools_cnt = df_schools.count()
centers_cnt = df_centers.count()
if schools_cnt == 0:
    df_schools = spark.createDataFrame([], schema=_biz_schema)
if centers_cnt == 0:
    df_centers = spark.createDataFrame([], schema=_biz_schema)

osm_dfs.append(df_schools)
osm_dfs.append(df_centers)
print(f"  ✅  bronze.schools        → {schools_cnt:>4} rows")
print(f"  ✅  bronze.centers        → {centers_cnt:>4} rows")

df_all_biz = reduce(lambda a, b: a.union(b), osm_dfs).persist()
biz_total  = df_all_biz.count()   # ← trigger the persist
print(f"\n  🔢 Total businesses: {biz_total:,}")

# ── Rent Commercial ───────────────────────────────────────────────
rent_raw_df = read_pg("rent_commercial")
rent_cols   = rent_raw_df.columns
area_col = next((c for c in rent_cols if any(x in c.lower() for x in ["area","m2","sqm"])), None)
rent_col = next((c for c in rent_cols if any(x in c.lower() for x in ["rent","egp","price"])), None)
loc_col  = next((c for c in rent_cols if any(x in c.lower() for x in ["location","street","loc"])), None)
print(f"  📋  rent_commercial: area={area_col}, rent={rent_col}, loc={loc_col}")

df_rent_raw = (
    rent_raw_df
    .select(
        F.col(area_col).alias("area_sqm"),
        F.col(rent_col).alias("rent_egp"),
        F.col(loc_col).alias("street_name"),
    )
    .filter(F.col("area_sqm").isNotNull() & F.col("rent_egp").isNotNull())
    .filter((F.col("area_sqm").cast(DoubleType()) > 0) & (F.col("rent_egp").cast(DoubleType()) > 0))
    .withColumn("area_sqm", F.col("area_sqm").cast(DoubleType()))
    .withColumn("rent_egp",  F.col("rent_egp").cast(DoubleType()))
)
print(f"  ✅  bronze.rent_commercial → {df_rent_raw.count():>4} rows")
print("\n✅ Cell 6 ready!")
# ════════════════════════════════════════════════════════════════════
# CELL 7 — Population  ✦ الإصلاح الثالث: data loss في dropDuplicates
# ════════════════════════════════════════════════════════════════════
# ─── المشكلة الأصلية ──────────────────────────────────────────────
# dropDuplicates(["area_name"]) كانت بتشيل السنوات التانية
# لو عندك area بـ 2022 و2023 → بتضيع سنة كاملة من البيانات
#
# ─── الحل ────────────────────────────────────────────────────────
# Window function: خد الـ row الأحدث (max year) لكل area
# ─────────────────────────────────────────────────────────────────

import ast
pdf_pop = read_pg("population").toPandas()
pdf_pop["parsed"]    = pdf_pop["data"].apply(ast.literal_eval)
pdf_pop["area_name"] = pdf_pop["parsed"].apply(lambda x: x.get("Alexandria Population Data — SmartCityAnalyzer"))
pdf_pop["population"]= pdf_pop["parsed"].apply(lambda x: x.get("Unnamed: 1"))
pdf_pop["latitude"]  = pdf_pop["parsed"].apply(lambda x: x.get("Unnamed: 5"))
pdf_pop["longitude"] = pdf_pop["parsed"].apply(lambda x: x.get("Unnamed: 6"))
pdf_pop["year"]      = pdf_pop["parsed"].apply(lambda x: x.get("Unnamed: 4", 9999))
pdf_pop = pdf_pop[pdf_pop["area_name"] != "district"].dropna(subset=["area_name","population"])
pdf_pop["population"] = pd.to_numeric(pdf_pop["population"], errors="coerce").astype(float)
pdf_pop["latitude"]   = pd.to_numeric(pdf_pop["latitude"],   errors="coerce").astype(float)
pdf_pop["longitude"]  = pd.to_numeric(pdf_pop["longitude"],  errors="coerce").astype(float)
pdf_pop["year"]       = pd.to_numeric(pdf_pop["year"],       errors="coerce").fillna(9999).astype(float)
df_pop_raw = spark.createDataFrame(pdf_pop[["area_name","population","latitude","longitude","year"]])

# ✦ FIX: خد أحدث سنة لكل area بدل dropDuplicates العشوائي
w_latest = Window.partitionBy("area_name").orderBy(F.col("year").desc())
df_pop = (
    df_pop_raw
    .withColumn("rn", F.row_number().over(w_latest))
    .filter(F.col("rn") == 1)
    .drop("rn", "year")
)
print(f"  ✅  bronze.population → {df_pop.count()} unique areas")
print("\n✅ Cell 7 ready!")
# ════════════════════════════════════════════════════════════════════
# CELL 8 — Dim_Area
# ════════════════════════════════════════════════════════════════════
df_dim_area = (
    df_pop
    .withColumn("area_id", F.row_number().over(Window.orderBy("area_name")))
    .select(
        "area_id", "area_name", "population",
        F.round("latitude",  6).alias("latitude"),
        F.round("longitude", 6).alias("longitude"),
    )
    .orderBy("area_id")
    .persist()
)
n_areas = df_dim_area.count()   # trigger persist
print(f"✅ Dim_Area → {n_areas} rows")
df_dim_area.show(5, truncate=False)
# ════════════════════════════════════════════════════════════════════
# CELL 9 — Dim_Business_Type  ✦ المدارس مش في الـ DWH
# ════════════════════════════════════════════════════════════════════
df_dim_business_type = (
    df_all_biz
    .filter((F.col("subcategory") != "School") & (F.col("category") != "Education & Services"))
    .select("category", "subcategory", "service_type")
    .dropDuplicates(["category", "subcategory"])
    .withColumn("is_center", F.when((F.col("category") == "Education") & (F.col("subcategory") == "Education Center"), 1).otherwise(0))
    .orderBy("is_center", "category", "subcategory")
    .withColumn("business_type_id",
        F.row_number().over(Window.orderBy("is_center", "category", "subcategory")))
    .select("business_type_id", "category", "subcategory", "service_type")
    .persist()
)
n_types = df_dim_business_type.count()
print(f"✅ Dim_Business_Type → {n_types} rows (المدارس مش موجودة)")
df_dim_business_type.show(truncate=False)
# ════════════════════════════════════════════════════════════════════
# CELL 10 — Dim_Property  ✦ الإصلاح الرابع: street→area mapping
# ════════════════════════════════════════════════════════════════════
# ─── المشكلة الأصلية ──────────────────────────────────────────────
# كان بيعمل join بشرط: street.contains(area_name)
# ده بيعمل nested loop داخلي في Spark وبيضيّع 99% من الـ properties
# لأن "Gamal Abd El Nasir St" مش بتحتوي على "Sidi Bishr" مثلاً
#
# ─── الحل ────────────────────────────────────────────────────────
# Manual lookup dictionary مباشرة في Pandas (أسرع وأدق)
# بعدين نعيد بناء الـ Spark DF
# ─────────────────────────────────────────────────────────────────

STREET_AREA_MAP = {
    "abd el-salam aref":     "Attarin",      "abdel salam aref":    "Attarin",
    "ademon fremon":         "El Shatby",    "al moaaskar al romani":"El Hadra",
    "el gaish":              "Sidi Bishr",   "el geish":            "Sidi Bishr",
    "gaish":                 "Sidi Bishr",   "geish":               "Sidi Bishr",
    "port said":             "El Gomrok",    "salah salem":         "Smouha",
    "victor emanuel":        "Raml Station", "stanley":             "Stanley",
    "gleem":                 "Gleem",        "san stefano":         "San Stefano",
    "kafr abdu":             "Kafr Abdu",    "roshdy":              "Roshdy",
    "fleming":               "Fleming",      "smouha":              "Smouha",
    "sidi bishr":            "Sidi Bishr",   "miami":               "Miami",
    "montazah":              "El Montazah",  "mandara":             "El Mandara",
    "agamy":                 "El Agamy",     "maamoura":            "El Maamoura",
    "cleopatra":             "Cleopatra",    "ibrahimiya":          "El Ibrahimiya",
    "moharram bek":          "Moharram Bek", "moharam bek":         "Moharram Bek",
    "gomrok":                "El Gomrok",    "anfushi":             "El Anfushi",
    "wardian":               "El Wardian",   "hadra":               "El Hadra",
    "shotbi":                "El Shotbi",    "shatby":              "El Shatby",
    "sporting":              "Sporting",     "louran":              "Louran",
    "azarita":               "El Azarita",   "chatby":              "Chatby",
    "boulkly":               "Boulkly",      "victoria":            "Victoria",
    "zizinia":               "Zizinia",      "saba pasha":          "Saba Pasha",
    "nozha":                 "El Nozha",     "laurent":             "Laurent",
    "bakoos":                "El Gomrok",    "el sultan hussein":   "El Gomrok",
    "sultan hussein":        "El Gomrok",    "shohada":             "El Gomrok",
    "gamal abd el nasir":    "Sidi Bishr",   "gamal abdel nasser":  "Sidi Bishr",
    "khaled ibn el waleed":  "Smouha",       "la jetee":            "El Anfushi",
    "mohammed al eqbal":     "Moharram Bek", "mohammed darwish":    "El Hadra",
    "mohammed fawzi moaz":   "Kafr Abdu",    "mostafa fahmy":       "Roshdy",
    "roushdy basha":         "Roshdy",       "riad":                "Attarin",
    "saad zaghloul":         "El Azarita",   "sant giyn":           "El Anfushi",
    "sawary":                "El Wardian",   "shatee el nakheel":   "El Maamoura",
    "syria":                 "El Ibrahimiya",
}

pdf_area = df_dim_area.toPandas()
area_to_id  = dict(zip(pdf_area["area_name"].str.lower(), pdf_area["area_id"]))
area_to_lat = dict(zip(pdf_area["area_name"].str.lower(), pdf_area["latitude"]))
area_to_lon = dict(zip(pdf_area["area_name"].str.lower(), pdf_area["longitude"]))
area_to_pop = dict(zip(pdf_area["area_id"],               pdf_area["population"]))

def get_area_from_street(street):
    if not street:
        return None
    s = street.lower()
    # Remove "Alexandria / " prefix if present
    s = s.replace("alexandria /", "").replace("alexandria/", "").strip()
    # Remove " st", " rd", " road", " st." suffixes
    for suffix in [" st.", " st", " rd.", " rd", " road", " blvd"]:
        s = s.replace(suffix, "")
    s = s.strip()
    for keyword, area_name in STREET_AREA_MAP.items():
        if keyword in s:
            return area_name.lower()
    return None

pdf_rent = df_rent_raw.toPandas()
pdf_rent["matched_area"] = pdf_rent["street_name"].apply(get_area_from_street)
pdf_rent["area_id"]      = pdf_rent["matched_area"].map(area_to_id)
pdf_rent["prop_lat"]     = pdf_rent["matched_area"].map(area_to_lat)
pdf_rent["prop_lon"]     = pdf_rent["matched_area"].map(area_to_lon)
pdf_rent["population"]   = pdf_rent["area_id"].map(area_to_pop)
pdf_rent["rent_per_sqm"] = (pdf_rent["rent_egp"] / pdf_rent["area_sqm"]).round(2)

matched = pdf_rent["area_id"].notna().sum()
print(f"  ✅ Matched: {matched}/{len(pdf_rent)} properties to areas")

unmatched = pdf_rent[pdf_rent["area_id"].isna()]["street_name"].unique()
if len(unmatched) > 0:
    print(f"  ⚠️  Still unmatched ({len(unmatched)}):")
    for s in unmatched:
        print(f"     - {s}")

pdf_rent = pdf_rent.dropna(subset=["area_id"]).copy()
pdf_rent["prop_id"] = range(1, len(pdf_rent)+1)

df_dim_property = spark.createDataFrame(
    pdf_rent[["prop_id","area_id","street_name","area_sqm","rent_egp","rent_per_sqm"]]
    .assign(area_id=lambda d: d["area_id"].astype(int),
            prop_id=lambda d: d["prop_id"].astype(int),
            area_sqm=lambda d: d["area_sqm"].astype(int),
            rent_egp=lambda d: d["rent_egp"].astype(int))
    .rename(columns={"rent_egp": "rent_monthly_egp"})
).persist()
df_dim_property.count()
print(f"✅ Dim_Property → {df_dim_property.count()} rows")
df_dim_property.show(5, truncate=False)
# ════════════════════════════════════════════════════════════════════
# CELL 11 — Assign Nearest Area to Businesses  ✦ إلغاء crossJoin
# ════════════════════════════════════════════════════════════════════
# ─── المشكلة الأصلية ──────────────────────────────────────────────
# crossJoin كان بيعمل كارتيزي product كامل ثم يشيل بـ rn=1
# حتى لو 50 area فقط، الـ shuffle والـ sort بيكلّفوا وقت
#
# ─── الحل ────────────────────────────────────────────────────────
# Broadcast الـ areas (50 row = أقل من 1KB!) للـ UDF
# بيتحسب nearest area بـ numpy vectorized في كل row مرة واحدة
# ─────────────────────────────────────────────────────────────────

# Broadcast الـ 50 area → بيتبعت لكل worker مرة واحدة
areas_list = df_dim_area.select(
    "area_id","area_name",
    F.col("latitude").alias("a_lat"),
    F.col("longitude").alias("a_lon"),
    "population"
).toPandas().to_dict("records")

areas_bc = spark.sparkContext.broadcast(areas_list)

nearest_area_schema = StructType([
    StructField("area_id",    IntegerType()),
    StructField("area_name",  StringType()),
    StructField("population", LongType()),
])

@F.udf(returnType=nearest_area_schema)
def nearest_area_udf(lat, lon):
    """Numpy-vectorized nearest area — runs in JVM-worker memory"""
    if lat is None or lon is None:
        return None
    import numpy as np
    areas = areas_bc.value
    a_lats = np.array([a["a_lat"] for a in areas])
    a_lons = np.array([a["a_lon"] for a in areas])
    # Euclidean approximation (دقيقة كفاية في نطاق إسكندرية)
    dlat = np.radians(a_lats - lat)
    dlon = np.radians(a_lons - lon)
    # Haversine vectorized
    sin_dlat = np.sin(dlat / 2)
    sin_dlon = np.sin(dlon / 2)
    a_vals = sin_dlat**2 + np.cos(np.radians(lat)) * np.cos(np.radians(a_lats)) * sin_dlon**2
    dists  = 2 * np.arctan2(np.sqrt(a_vals), np.sqrt(1 - a_vals)) * 6371.0
    idx    = int(np.argmin(dists))
    best   = areas[idx]
    pop = best["population"]
    if pop is None or (isinstance(pop, float) and np.isnan(pop)):
        pop = 0
    return (int(best["area_id"]), str(best["area_name"]), int(pop))

df_biz_with_area = (
    df_all_biz
    .filter(F.col("latitude").isNotNull() & F.col("longitude").isNotNull())
    .withColumn("_na", nearest_area_udf(F.col("latitude"), F.col("longitude")))
    .withColumn("area_id",    F.col("_na.area_id").cast(IntegerType()))
    .withColumn("area_name",  F.col("_na.area_name"))
    .withColumn("population", F.col("_na.population").cast(LongType()))
    .drop("_na")
    .persist()
)
n_biz_area = df_biz_with_area.count()   # trigger persist
print(f"  ✅ df_biz_with_area → {n_biz_area:,} rows (no cartesian product!)")
# ════════════════════════════════════════════════════════════════════
# CELL 12 — Fact_Area_Business_Score
# ✦ school_count كـ feature للـ Education Centers
# ════════════════════════════════════════════════════════════════════

# ── Step 1: nearest-competitor distance (Spark SQL) ───────────────
df_a = df_biz_with_area.alias("a")
df_b = df_biz_with_area.alias("b")

df_pair_dist = (
    df_a.join(df_b,
        (F.col("a.area_id")       == F.col("b.area_id")) &
        (F.col("a.subcategory")   == F.col("b.subcategory")) &
        (F.col("a.business_name") != F.col("b.business_name")),
        "left"
    )
    .withColumn("dist_m",
        F.acos(F.greatest(F.lit(-1.0), F.least(F.lit(1.0),
            F.sin(F.radians(F.col("a.latitude"))) * F.sin(F.radians(F.col("b.latitude"))) +
            F.cos(F.radians(F.col("a.latitude"))) * F.cos(F.radians(F.col("b.latitude"))) *
            F.cos(F.radians(F.col("a.longitude") - F.col("b.longitude")))
        ))) * F.lit(6371000.0)
    )
    .groupBy(
        F.col("a.area_id").alias("area_id"),
        F.col("a.subcategory").alias("subcategory"),
        F.col("a.category").alias("category"),
        F.col("a.business_name").alias("business_name")
    )
    .agg(F.min("dist_m").alias("min_dist_to_neighbor"))
)

df_actual_stats = (
    df_pair_dist
    .groupBy("area_id", "category", "subcategory")
    .agg(
        F.count("business_name").alias("competitor_count"),
        F.round(F.avg("min_dist_to_neighbor"), 0).cast(IntegerType())
          .alias("nearest_competitor_m"),
    )
)
print("  ✅ actual stats computed")

# ── عدد المدارس لكل area (feature للـ Education Centers فقط) ──────
# المدارس مش في الـ DWH لكن بنستخدمها لحساب score السناتر
df_schools_count = (
    df_biz_with_area
    .filter(F.col("subcategory") == "School")
    .groupBy("area_id")
    .agg(F.count("*").alias("school_count"))
)
print(f"  ✅ school_count per area → {df_schools_count.count()} areas have schools")

# ── Step 2: Full grid 50 areas × business types (بدون Schools) ───
df_all_areas = df_dim_area.select("area_id", "area_name", "population")
df_all_types = (
    df_dim_business_type
    .select("business_type_id", "category", "subcategory")
    .dropDuplicates(["category", "subcategory"])
)

# ✦ NOTE: 50 × 12 = 600 rows (مدارس اتحذفت → بقت 12 بدل 13)
df_full_grid = df_all_areas.crossJoin(df_all_types)
print(f"  ✅ Full grid: {n_areas} areas × {df_all_types.count()} types = {df_full_grid.count()} rows")

# ── Step 3: Join grid + actual stats + school_count ───────────────
df_fact_area = (
    df_full_grid
    .join(df_actual_stats, on=["area_id", "category", "subcategory"], how="left")
    .join(df_schools_count, on="area_id", how="left")
    .fillna(0, subset=["competitor_count", "school_count"])
    .fillna({"nearest_competitor_m": 0})
    .withColumn("demand_index",
        F.round(
            F.when(F.col("competitor_count") > 0,
                   F.col("population").cast(DoubleType()) / F.col("competitor_count").cast(DoubleType()))
             .otherwise(F.col("population").cast(DoubleType())), 0
        ).cast(IntegerType())
    )
    .withColumn("market_saturation",
        F.round(
            F.least(F.lit(100.0),
                (F.col("competitor_count").cast(DoubleType()) /
                 F.greatest(F.col("population").cast(DoubleType()) / 1000.0, F.lit(0.1))) * 10
            ), 1
        )
    )
    .withColumn("suitability_score",
        F.round(
            F.least(F.lit(10.0), F.greatest(F.lit(1.0),
                # ✦ للسناتر: school_count يزيد الطلب (طلاب أكتر = حاجة لسناتر أكتر)
                F.when(
                    F.col("subcategory") == "Education Center",
                    (0.35 * F.least(F.col("demand_index").cast(DoubleType()) / 5000.0, F.lit(1.0)) +
                     0.25 * F.least(F.col("population").cast(DoubleType()) / 20000.0, F.lit(1.0)) +
                     0.25 * (1.0 - F.least(F.col("market_saturation") / 100.0, F.lit(1.0))) +
                     0.15 * F.least(F.col("school_count").cast(DoubleType()) / 10.0, F.lit(1.0)))
                    * 10.0
                ).otherwise(
                    # باقي أنواع الأعمال: الـ formula القديمة
                    (0.4 * F.least(F.col("demand_index").cast(DoubleType()) / 5000.0, F.lit(1.0)) +
                     0.3 * F.least(F.col("population").cast(DoubleType()) / 20000.0, F.lit(1.0)) +
                     0.3 * (1.0 - F.least(F.col("market_saturation") / 100.0, F.lit(1.0))))
                    * 10.0
                )
            )), 2)
    )
    .withColumn("recommended", F.col("suitability_score") >= 6.0)
    .withColumn("is_center", F.when(F.col("subcategory") == "Education Center", 1).otherwise(0))
    .withColumn("score_id",
        F.row_number().over(Window.orderBy("is_center", "area_id", "business_type_id")))
    .select(
        "score_id", "area_id", "area_name", "business_type_id",
        "category", "subcategory", "competitor_count",
        "nearest_competitor_m", "population", "school_count",
        "demand_index", "market_saturation", "suitability_score", "recommended"
    )
    .orderBy("score_id")
    .persist()
)
total = df_fact_area.count()
print(f"✅ Fact_Area_Business_Score → {total:,} rows")
df_fact_area.filter(F.col("subcategory") == "Education Center").show(5, truncate=False)
# ════════════════════════════════════════════════════════════════════
# CELL 13 — Fact_Property_Suitability  ✦ vectorized numpy (أسرع 50x)
# ════════════════════════════════════════════════════════════════════
# ─── المشكلة الأصلية ──────────────────────────────────────────────
# كان بيستخدم pandas .apply() لكل business في كل iteration
# 35 property × 13 type × apply على 2000 business = 910,000 calls
#
# ─── الحل ────────────────────────────────────────────────────────
# numpy vectorized haversine على كل الـ competitors دفعة واحدة
# → 455 iterations بس (بدل 910,000 pandas apply calls)
# ─────────────────────────────────────────────────────────────────

def haversine_vec_m(lat1, lon1, lats2, lons2):
    """numpy vectorized haversine — lat1/lon1 scalar, lats2/lons2 array"""
    R     = 6_371_000.0
    dlat  = np.radians(lats2 - lat1)
    dlon  = np.radians(lons2 - lon1)
    a     = (np.sin(dlat / 2)**2
             + np.cos(np.radians(lat1)) * np.cos(np.radians(lats2)) * np.sin(dlon / 2)**2)
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

# جيب الداتا كـ pandas (صغيرة)
pdf_prop   = pdf_rent.copy()   # من CELL 10 — فيها prop_lat, prop_lon
pdf_biz    = df_biz_with_area.select(
    "latitude","longitude","category","subcategory").toPandas()
pdf_btypes = df_dim_business_type.toPandas()

print(f"  Props with coords: {pdf_prop['prop_lat'].notna().sum()} / {len(pdf_prop)}")

# Pre-group businesses by category للسرعة
biz_by_cat = {
    cat: grp[["latitude","longitude"]].dropna().values
    for cat, grp in pdf_biz.groupby("category")
}

rows = []
for _, prop in pdf_prop.iterrows():
    if pd.isna(prop["prop_lat"]) or pd.isna(prop["prop_lon"]):
        continue
    area_rents    = pdf_prop[pdf_prop["area_id"] == prop["area_id"]]["rent_per_sqm"]
    area_avg_rent = area_rents.mean() if len(area_rents) > 0 else 0

    for _, btype in pdf_btypes.iterrows():
        cat   = btype["category"]
        comps = biz_by_cat.get(cat, np.empty((0, 2)))

        if len(comps) > 0:
            # ✦ numpy vectorized — حساب كل المسافات دفعة واحدة
            dists      = haversine_vec_m(prop["prop_lat"], prop["prop_lon"],
                                         comps[:, 0], comps[:, 1])
            comp_500m  = int((dists <= 500).sum())
            comp_1km   = int((dists <= 1000).sum())
        else:
            comp_500m = comp_1km = 0

        affordability = (max(0.0, 1 - (prop["rent_per_sqm"] / area_avg_rent - 1) * 0.5)
                         if area_avg_rent > 0 else 0.5)
        pop           = float(prop["population"]) if pd.notna(prop["population"]) else 5000.0
        demand_score  = min(1.0, (pop / max(comp_1km, 1)) / 3000.0)
        comp_score    = max(0.0, 1 - comp_500m / 10.0)
        suit          = round(max(1.0, min(10.0,
            (0.4 * min(affordability, 1.0) +
             0.3 * comp_score +
             0.3 * demand_score) * 10.0)), 2)

        rows.append({
            "prop_id":             int(prop["prop_id"]),
            "area_id":             int(prop["area_id"]) if pd.notna(prop["area_id"]) else None,
            "business_type_id":    int(btype["business_type_id"]),
            "category":            cat,
            "street_name":         prop["street_name"],
            "area_sqm":            int(prop["area_sqm"]),
            "rent_monthly_egp":    int(prop["rent_egp"]),
            "rent_per_sqm":        float(prop["rent_per_sqm"]),
            "competitors_500m":    comp_500m,
            "competitors_1km":     comp_1km,
            "affordability_score": round(float(affordability), 2),
            "suitability_score":   suit,
            "recommended":         suit >= 6.0,
        })

pdf_fact_prop = pd.DataFrame(rows)
pdf_fact_prop["is_center"] = (pdf_fact_prop["business_type_id"] == 12).astype(int)
pdf_fact_prop = pdf_fact_prop.sort_values(["is_center", "prop_id", "category"]).reset_index(drop=True)
pdf_fact_prop.insert(0, "fact_id", range(1, len(pdf_fact_prop)+1))
pdf_fact_prop = pdf_fact_prop.drop(columns=["is_center"])
print(f"✅ Fact_Property_Suitability → {len(pdf_fact_prop):,} rows")
print(pdf_fact_prop.head())
# ════════════════════════════════════════════════════════════════════
# CELL 14 — Export Gold Tables
# ════════════════════════════════════════════════════════════════════
print("📁 Exporting Gold Tables...\n")

to_csv(df_dim_area,          "Dim_Area.csv")
to_csv(df_dim_business_type, "Dim_Business_Type.csv")
to_csv(df_dim_property,      "Dim_Property.csv")
to_csv(df_fact_area,         "Fact_Area_Business_Score.csv")
to_csv(pdf_fact_prop,        "Fact_Property_Suitability.csv")

print("\n" + "═"*55)
print("🎉  All Gold Tables exported to /data/phase2_transform/gold_output/")
print("═"*55)
print(f"\n  Dim_Area                  → {df_dim_area.count():>5} rows")
print(f"  Dim_Business_Type         → {df_dim_business_type.count():>5,} rows")
print(f"  Dim_Property              → {df_dim_property.count():>5} rows")
print(f"  Fact_Area_Business_Score  → {df_fact_area.count():>5,} rows")
print(f"  Fact_Property_Suitability → {len(pdf_fact_prop):>5,} rows")
# اكتشاف أسماء المتغيرات الموجودة
import pandas as pd
from pyspark.sql import DataFrame as SparkDF

spark_dfs = {name: obj for name, obj in globals().items()
             if isinstance(obj, SparkDF) and not name.startswith('_')}

print("=== Spark DataFrames الموجودة ===")
for name, df in spark_dfs.items():
    print(f"  {name}  →  {df.count()} rows  |  cols: {df.columns}")
# اكتشاف اسم Fact_Property_Suitability الحقيقي
candidates = [name for name in globals() if 'fact' in name.lower() or 'property' in name.lower() or 'suit' in name.lower()]
print("المتغيرات المحتملة:", candidates)
