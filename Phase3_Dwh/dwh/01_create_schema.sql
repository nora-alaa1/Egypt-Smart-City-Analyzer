-- ============================================================
-- SmartCity DWH — 01_create_schema.sql
-- ============================================================

USE master;
GO

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'SmartCity')
BEGIN
    CREATE DATABASE SmartCity;
    PRINT '✅ Database SmartCity created.';
END
ELSE
    PRINT '✅ Database SmartCity already exists.';
GO

USE SmartCity;
GO

IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'dbo')
    EXEC('CREATE SCHEMA dbo');
GO

PRINT '✅ Schema ready.';
GO
