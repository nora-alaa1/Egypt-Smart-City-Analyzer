import osmnx as ox
import pandas as pd
import warnings

warnings.filterwarnings("ignore")

print("Starting script...")

# -----------------------------
# 1️⃣ تحديد المدينة
# -----------------------------
place = "Alexandria, Egypt"

# -----------------------------
# 2️⃣ تعريف التاجز الخاصة بالجيمات
# -----------------------------
gym_tags = {
    "leisure": ["fitness_centre", "sports_centre"],
    "sport": "fitness"
}

print("Downloading data from OpenStreetMap...")

# -----------------------------
# 3️⃣ جلب البيانات من OSM
# -----------------------------
gdf = ox.features_from_place(place, gym_tags)

print("Data downloaded.")

# -----------------------------
# 4️⃣ التأكد إن فيه عمود name
# -----------------------------
if "name" not in gdf.columns:
    print("No gyms found.")
    exit()

# حذف القيم الفاضية
gdf = gdf.dropna(subset=["name"])

# -----------------------------
# 5️⃣ استخراج الإحداثيات
# -----------------------------
gdf["latitude"] = gdf.geometry.centroid.y
gdf["longitude"] = gdf.geometry.centroid.x

# اختيار الأعمدة المهمة فقط
gyms = gdf[["name", "latitude", "longitude"]].copy()

# حذف التكرار
gyms = gyms.drop_duplicates()

# -----------------------------
# 6️⃣ حفظ الملف
# -----------------------------
gyms.to_csv("gyms_alexandria.csv", index=False, encoding="utf-8-sig")

print("✅ Gyms file created successfully!")
print("📊 Total Gyms:", len(gyms))