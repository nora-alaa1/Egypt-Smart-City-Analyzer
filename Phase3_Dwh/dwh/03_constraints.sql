-- ============================================================
-- SmartCity DWH — 03_constraints.sql
-- ============================================================
-- شغّل الملف ده بعد 02_create_tables.sql
-- ============================================================

USE SmartCity;
GO

-- ── Fix nullable PK columns ──────────────────────────────

ALTER TABLE dbo.Dim_Business_Type
    ALTER COLUMN business_type_id BIGINT NOT NULL;
GO

ALTER TABLE dbo.Dim_Area
    ALTER COLUMN area_id BIGINT NOT NULL;
GO

ALTER TABLE dbo.Dim_Property
    ALTER COLUMN prop_id BIGINT NOT NULL;
GO

ALTER TABLE dbo.Fact_Area_Business_Score
    ALTER COLUMN score_id BIGINT NOT NULL;
GO

ALTER TABLE dbo.Fact_Property_Suitability
    ALTER COLUMN fact_id BIGINT NOT NULL;
GO

PRINT '✅ All PK columns set to NOT NULL — safe to run 03_constraints.sql now';
GO

-- ──────────────────────────────────────────────────────────
-- Primary Keys
-- ──────────────────────────────────────────────────────────

ALTER TABLE dbo.Dim_Business_Type
    ADD CONSTRAINT PK_Dim_Business_Type
    PRIMARY KEY (business_type_id);
PRINT '✅ PK — Dim_Business_Type';
GO

ALTER TABLE dbo.Dim_Area
    ADD CONSTRAINT PK_Dim_Area
    PRIMARY KEY (area_id);
PRINT '✅ PK — Dim_Area';
GO

ALTER TABLE dbo.Dim_Property
    ADD CONSTRAINT PK_Dim_Property
    PRIMARY KEY (prop_id);
PRINT '✅ PK — Dim_Property';
GO

ALTER TABLE dbo.Fact_Area_Business_Score
    ADD CONSTRAINT PK_Fact_Area_Business_Score
    PRIMARY KEY (score_id);
PRINT '✅ PK — Fact_Area_Business_Score';
GO

ALTER TABLE dbo.Fact_Property_Suitability
    ADD CONSTRAINT PK_Fact_Property_Suitability
    PRIMARY KEY (fact_id);
PRINT '✅ PK — Fact_Property_Suitability';
GO

-- ──────────────────────────────────────────────────────────
-- Foreign Keys
-- ──────────────────────────────────────────────────────────

-- Dim_Property → Dim_Area
ALTER TABLE dbo.Dim_Property
    ADD CONSTRAINT FK_DimProperty_Area
    FOREIGN KEY (area_id) REFERENCES dbo.Dim_Area(area_id);
PRINT '✅ FK — Dim_Property → Dim_Area';
GO

-- Fact_Area_Business_Score → Dim_Area
ALTER TABLE dbo.Fact_Area_Business_Score
    ADD CONSTRAINT FK_FactArea_Area
    FOREIGN KEY (area_id) REFERENCES dbo.Dim_Area(area_id);
PRINT '✅ FK — Fact_Area_Business_Score → Dim_Area';
GO

-- Fact_Area_Business_Score → Dim_Business_Type
ALTER TABLE dbo.Fact_Area_Business_Score
    ADD CONSTRAINT FK_FactArea_BusinessType
    FOREIGN KEY (business_type_id) REFERENCES dbo.Dim_Business_Type(business_type_id);
PRINT '✅ FK — Fact_Area_Business_Score → Dim_Business_Type';
GO

-- Fact_Property_Suitability → Dim_Property
ALTER TABLE dbo.Fact_Property_Suitability
    ADD CONSTRAINT FK_FactProp_Property
    FOREIGN KEY (prop_id) REFERENCES dbo.Dim_Property(prop_id);
PRINT '✅ FK — Fact_Property_Suitability → Dim_Property';
GO

-- Fact_Property_Suitability → Dim_Area
ALTER TABLE dbo.Fact_Property_Suitability
    ADD CONSTRAINT FK_FactProp_Area
    FOREIGN KEY (area_id) REFERENCES dbo.Dim_Area(area_id);
PRINT '✅ FK — Fact_Property_Suitability → Dim_Area';
GO

-- Fact_Property_Suitability → Dim_Business_Type
ALTER TABLE dbo.Fact_Property_Suitability
    ADD CONSTRAINT FK_FactProp_BusinessType
    FOREIGN KEY (business_type_id) REFERENCES dbo.Dim_Business_Type(business_type_id);
PRINT '✅ FK — Fact_Property_Suitability → Dim_Business_Type';
GO

PRINT '✅ All constraints applied successfully.';
GO


USE SmartCity;
GO

SELECT 
    fk.name        AS FK_Name,
    tp.name        AS Parent_Table,
    tr.name        AS Referenced_Table
FROM sys.foreign_keys fk
JOIN sys.tables tp ON fk.parent_object_id = tp.object_id
JOIN sys.tables tr ON fk.referenced_object_id = tr.object_id
ORDER BY tp.name;

SELECT 
    t.name  AS Table_Name,
    i.name  AS PK_Name
FROM sys.indexes i
JOIN sys.tables t ON i.object_id = t.object_id
WHERE i.is_primary_key = 1
ORDER BY t.name;