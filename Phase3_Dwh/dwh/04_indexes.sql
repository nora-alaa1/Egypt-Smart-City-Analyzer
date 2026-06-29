-- ============================================================
-- SmartCity DWH — 04_indexes.sql
-- ============================================================
-- شغّل الملف ده بعد 03_constraints.sql
-- ============================================================

USE SmartCity;
GO

-- ──────────────────────────────────────────────────────────
-- Fact_Area_Business_Score
-- ──────────────────────────────────────────────────────────

-- أكتر استعلام شائع: فلترة بالـ recommended + ترتيب بالـ score
CREATE NONCLUSTERED INDEX IX_FactArea_Recommended
ON dbo.Fact_Area_Business_Score (recommended, suitability_score DESC)
INCLUDE (area_id, area_name, category, subcategory, competitor_count, demand_index);
PRINT '✅ IX_FactArea_Recommended';
GO

-- بحث بالحي والنوع
CREATE NONCLUSTERED INDEX IX_FactArea_Area_Category
ON dbo.Fact_Area_Business_Score (area_id, category)
INCLUDE (subcategory, suitability_score, recommended);
PRINT '✅ IX_FactArea_Area_Category';
GO

-- بحث بالـ business_type_id
CREATE NONCLUSTERED INDEX IX_FactArea_BusinessType
ON dbo.Fact_Area_Business_Score (business_type_id)
INCLUDE (suitability_score, recommended);
PRINT '✅ IX_FactArea_BusinessType';
GO

-- ──────────────────────────────────────────────────────────
-- Fact_Property_Suitability
-- ──────────────────────────────────────────────────────────

-- العقارات الموصى بيها مرتبة بالـ score
CREATE NONCLUSTERED INDEX IX_FactProp_Recommended
ON dbo.Fact_Property_Suitability (recommended, suitability_score DESC)
INCLUDE (prop_id, area_id, category, rent_monthly_egp, competitors_500m);
PRINT '✅ IX_FactProp_Recommended';
GO

-- بحث بالحي والنوع
CREATE NONCLUSTERED INDEX IX_FactProp_Area_Category
ON dbo.Fact_Property_Suitability (area_id, category)
INCLUDE (suitability_score, recommended, rent_per_sqm);
PRINT '✅ IX_FactProp_Area_Category';
GO

-- بحث بالعقار
CREATE NONCLUSTERED INDEX IX_FactProp_PropId
ON dbo.Fact_Property_Suitability (prop_id)
INCLUDE (suitability_score, recommended);
PRINT '✅ IX_FactProp_PropId';
GO

-- ──────────────────────────────────────────────────────────
-- Dim_Property
-- ──────────────────────────────────────────────────────────

-- بحث بالحي (join مع Fact)
CREATE NONCLUSTERED INDEX IX_DimProp_AreaId
ON dbo.Dim_Property (area_id)
INCLUDE (street_name, area_sqm, rent_monthly_egp, rent_per_sqm);
PRINT '✅ IX_DimProp_AreaId';
GO

-- ──────────────────────────────────────────────────────────
-- Dim_Area
-- ──────────────────────────────────────────────────────────

-- بحث بالاسم (للـ dashboards)
CREATE NONCLUSTERED INDEX IX_DimArea_Name
ON dbo.Dim_Area (area_name)
INCLUDE (population, latitude, longitude);
PRINT '✅ IX_DimArea_Name';
GO

PRINT '✅ All indexes created successfully.';
GO
