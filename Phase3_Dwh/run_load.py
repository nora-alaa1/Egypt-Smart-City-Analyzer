import sys, subprocess

subprocess.run([sys.executable, "-m", "pip", "install", "--quiet",
                "sqlalchemy", "pymssql", "openpyxl"])

print("✅ كل المتطلبات جاهزة")

import os

DB_SERVER   = os.getenv("SQLSERVER_HOST", "host.docker.internal")
DB_PORT     = int(os.getenv("SQLSERVER_PORT", "1433"))
DB_NAME     = os.getenv("SQLSERVER_DB", "SmartCity")
DB_USER     = os.getenv("SQLSERVER_USER", "sa")
DB_PASSWORD = os.getenv("SQLSERVER_PASSWORD", "SmartCity@123")
FILES_DIR = "/data/Phase2_Transform/gold_output"

print(f"✅ Server: {DB_SERVER}:{DB_PORT} | DB: {DB_NAME} | User: {DB_USER}")

import pymssql
from sqlalchemy import create_engine, text, event
engine = create_engine(
    "mssql+pymssql://",
    creator=lambda: pymssql.connect(
        server=DB_SERVER,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
        autocommit=True
    )
)
with engine.connect() as conn:
    conn.execute(text("SELECT 1"))

print("✅ اتصال ناجح بـ SQL Server")

# Drop FK constraints before reload
drop_fks = """
DECLARE @sql NVARCHAR(MAX) = ''
SELECT @sql += 'ALTER TABLE ' + QUOTENAME(OBJECT_SCHEMA_NAME(parent_object_id))
             + '.' + QUOTENAME(OBJECT_NAME(parent_object_id))
             + ' DROP CONSTRAINT ' + QUOTENAME(name) + ';'
FROM sys.foreign_keys
EXEC sp_executesql @sql
"""
with engine.connect() as conn:
    conn.execute(text(drop_fks))
    conn.commit()
print("✅ FK constraints dropped")

# Cell 4 — رفع الجداول
import os
import pandas as pd

TABLES = [
    {"name": "Dim_Area",                  "file": "Dim_Area.csv"},
    {"name": "Dim_Business_Type",         "file": "Dim_Business_Type.csv"},
    {"name": "Dim_Property",              "file": "Dim_Property.csv"},
    {"name": "Fact_Area_Business_Score",  "file": "Fact_Area_Business_Score.csv"},
    {"name": "Fact_Property_Suitability", "file": "Fact_Property_Suitability.csv"},
]

success, failed = [], []

for table in TABLES:
    name = table["name"]
    path = os.path.join(FILES_DIR, table["file"])

    if not os.path.exists(path):
        print(f"⚠️  مش لاقي: {table['file']} — تم التخطي")
        failed.append(name)
        continue

    # قراءة الملف
    ext = os.path.splitext(path)[1].lower()
    df  = pd.read_csv(path, encoding="utf-8-sig") if ext == ".csv" else pd.read_excel(path)

    # رفع لـ SQL Server
    df.to_sql(name, engine, if_exists="replace", index=False, chunksize=500)
    print(f"✅ {name:<35} {len(df):>5} rows")
    success.append(name)

print(f"\n{'='*50}")
print(f"  تم رفع : {len(success)} جدول")
if failed:
    print(f"  فشل    : {failed}")
if len(success) == len(TABLES):
    print("\n🎉 كل الجداول اتنقلت لـ SQL Server بنجاح!")
    print("   افتحي SSMS وتأكدي إن الجداول موجودة ✅")
