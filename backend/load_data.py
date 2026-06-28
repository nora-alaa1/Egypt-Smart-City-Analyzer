import pandas as pd
from db import get_engine

engine = get_engine()

# Load dimension tables
areas = pd.read_csv("Dim_Area(Area).csv")
business_types = pd.read_csv("Dim_Business_Type 2(Business_Type).csv")
properties = pd.read_csv("Dim_Property(Property).csv")

# Load fact tables
area_scores = pd.read_csv("Fact_Area_Business_Score(Area_Business_Score).csv")
property_scores = pd.read_csv("Fact_Property_Suitability(Property_Suitability).csv")

# Insert into DB
areas.to_sql("areas", engine, if_exists="replace", index=False)
business_types.to_sql("business_types", engine, if_exists="replace", index=False)
properties.to_sql("properties", engine, if_exists="replace", index=False)

area_scores.to_sql("area_business_scores", engine, if_exists="replace", index=False)
property_scores.to_sql("property_suitability", engine, if_exists="replace", index=False)

print("✅ ALL DATA LOADED SUCCESSFULLY")
