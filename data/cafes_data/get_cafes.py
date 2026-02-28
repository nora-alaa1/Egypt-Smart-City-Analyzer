import osmnx as ox
import pandas as pd
import warnings

warnings.filterwarnings("ignore")

print("Starting Cafes Script...")

# -----------------------------
# 1️⃣ تحديد المدينة
# -----------------------------
place = "Alexandria, Egypt"

# -----------------------------
# 2️⃣ تعريف التاجز الخاصة بالكافيهات
# -----------------------------
cafe_tags = {
    "amenity": "cafe"
}

print("Downloading cafes data from OpenStreetMap...")

# -----------------------------
# 3️⃣ جلب البيانات
# -----------------------------
gdf = ox.features_from_place(place, cafe_tags)

print("Data downloaded.")

# -----------------------------
# 4️⃣ التأكد من وجود عمود الاسم
# -----------------------------
if "name" not in gdf.columns:
    print("No cafes found.")
    exit()

# حذف القيم الفاضية
gdf = gdf.dropna(subset=["name"])

# -----------------------------
# 5️⃣ استخراج الإحداثيات
# -----------------------------
gdf["latitude"] = gdf.geometry.centroid.y
gdf["longitude"] = gdf.geometry.centroid.x

# اختيار الأعمدة المهمة
cafes = gdf[["name", "latitude", "longitude"]].copy()

# حذف التكرار
cafes = cafes.drop_duplicates()

# -----------------------------
# 6️⃣ حفظ CSV
# -----------------------------
cafes.to_csv("cafes_alexandria.csv", index=False, encoding="utf-8-sig")

print("✅ Cafes file created successfully!")
print("📊 Total Cafes:", len(cafes))