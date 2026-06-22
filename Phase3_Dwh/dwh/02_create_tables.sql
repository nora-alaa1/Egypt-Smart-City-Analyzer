-- ============================================================
-- SmartCity DWH — 02_create_tables.sql
-- ============================================================
-- الترتيب مهم: الـ Dims الأول، بعدين الـ Facts
-- ============================================================

USE SmartCity;
GO

-- ──────────────────────────────────────────────────────────
-- Dim_Business_Type
-- ──────────────────────────────────────────────────────────
IF OBJECT_ID('dbo.Dim_Business_Type', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Dim_Business_Type (
        business_type_id INT            NOT NULL,
        category         NVARCHAR(100)  NOT NULL,
        subcategory      NVARCHAR(100)  NOT NULL,
        service_type     NVARCHAR(100)  NULL
    );
    PRINT '✅ Dim_Business_Type created.';
END
ELSE
    PRINT '⚠️  Dim_Business_Type already exists — skipped.';
GO

-- ──────────────────────────────────────────────────────────
-- Dim_Area
-- ──────────────────────────────────────────────────────────
IF OBJECT_ID('dbo.Dim_Area', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Dim_Area (
        area_id    INT            NOT NULL,
        area_name  NVARCHAR(200)  NOT NULL,
        population BIGINT         NULL,
        latitude   FLOAT          NULL,
        longitude  FLOAT          NULL
    );
    PRINT '✅ Dim_Area created.';
END
ELSE
    PRINT '⚠️  Dim_Area already exists — skipped.';
GO

-- ──────────────────────────────────────────────────────────
-- Dim_Property
-- ──────────────────────────────────────────────────────────
IF OBJECT_ID('dbo.Dim_Property', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Dim_Property (
        prop_id          INT            NOT NULL,
        area_id          INT            NULL,
        street_name      NVARCHAR(300)  NULL,
        area_sqm         INT            NULL,
        rent_monthly_egp INT            NULL,
        rent_per_sqm     FLOAT          NULL
    );
    PRINT '✅ Dim_Property created.';
END
ELSE
    PRINT '⚠️  Dim_Property already exists — skipped.';
GO

-- ──────────────────────────────────────────────────────────
-- Fact_Area_Business_Score
-- ──────────────────────────────────────────────────────────
IF OBJECT_ID('dbo.Fact_Area_Business_Score', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Fact_Area_Business_Score (
        score_id             INT            NOT NULL,
        area_id              INT            NULL,
        area_name            NVARCHAR(200)  NULL,
        business_type_id     INT            NULL,
        category             NVARCHAR(100)  NULL,
        subcategory          NVARCHAR(100)  NULL,
        competitor_count     INT            NULL,
        nearest_competitor_m INT            NULL,
        population           BIGINT         NULL,
        demand_index         INT            NULL,
        market_saturation    FLOAT          NULL,
        suitability_score    FLOAT          NULL,
        recommended          BIT            NULL
    );
    PRINT '✅ Fact_Area_Business_Score created.';
END
ELSE
    PRINT '⚠️  Fact_Area_Business_Score already exists — skipped.';
GO

-- ──────────────────────────────────────────────────────────
-- Fact_Property_Suitability
-- ──────────────────────────────────────────────────────────
IF OBJECT_ID('dbo.Fact_Property_Suitability', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Fact_Property_Suitability (
        fact_id              INT            NOT NULL,
        prop_id              INT            NULL,
        area_id              INT            NULL,
        business_type_id     INT            NULL,
        category             NVARCHAR(100)  NULL,
        street_name          NVARCHAR(300)  NULL,
        area_sqm             INT            NULL,
        rent_monthly_egp     INT            NULL,
        rent_per_sqm         FLOAT          NULL,
        competitors_500m     INT            NULL,
        competitors_1km      INT            NULL,
        affordability_score  FLOAT          NULL,
        suitability_score    FLOAT          NULL,
        recommended          BIT            NULL
    );
    PRINT '✅ Fact_Property_Suitability created.';
END
ELSE
    PRINT '⚠️  Fact_Property_Suitability already exists — skipped.';
GO

PRINT '✅ All tables created successfully.';
GO
