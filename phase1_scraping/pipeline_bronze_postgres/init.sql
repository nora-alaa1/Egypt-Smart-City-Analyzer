-- ============================================================
--  SmartCity Bronze Layer — PostgreSQL Schema
--  كل الداتا الخام من الـ Kafka consumers
-- ============================================================

CREATE SCHEMA IF NOT EXISTS bronze;

-- ── Metadata columns مشتركة في كل table ──────────────────────
-- _source_file : اسم الملف الأصلي
-- _ingested_at : وقت الـ insert

-- ── Pipeline 01 — Rental ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS bronze.rent_commercial (
    id            SERIAL PRIMARY KEY,
    area_m2       INTEGER,
    rent_egp      INTEGER,
    location_en   VARCHAR(200),
    _source_file  VARCHAR(200),
    _ingested_at  TIMESTAMP DEFAULT NOW()
);

-- ── Pipeline 02 — Business (OSM) ─────────────────────────────
CREATE TABLE IF NOT EXISTS bronze.cafes (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(300),
    latitude      DOUBLE PRECISION,
    longitude     DOUBLE PRECISION,
    _source_file  VARCHAR(200),
    _ingested_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bronze.gyms (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(300),
    latitude      DOUBLE PRECISION,
    longitude     DOUBLE PRECISION,
    _source_file  VARCHAR(200),
    _ingested_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bronze.restaurants (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(300),
    latitude      DOUBLE PRECISION,
    longitude     DOUBLE PRECISION,
    _source_file  VARCHAR(200),
    _ingested_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bronze.bakeries (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(300),
    latitude      DOUBLE PRECISION,
    longitude     DOUBLE PRECISION,
    _source_file  VARCHAR(200),
    _ingested_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bronze.hotels (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(300),
    latitude      DOUBLE PRECISION,
    longitude     DOUBLE PRECISION,
    _source_file  VARCHAR(200),
    _ingested_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bronze.hospitals (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(300),
    latitude      DOUBLE PRECISION,
    longitude     DOUBLE PRECISION,
    _source_file  VARCHAR(200),
    _ingested_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bronze.banks (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(300),
    latitude      DOUBLE PRECISION,
    longitude     DOUBLE PRECISION,
    _source_file  VARCHAR(200),
    _ingested_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bronze.clothing (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(300),
    latitude      DOUBLE PRECISION,
    longitude     DOUBLE PRECISION,
    _source_file  VARCHAR(200),
    _ingested_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bronze.supermarkets (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(300),
    latitude      DOUBLE PRECISION,
    longitude     DOUBLE PRECISION,
    _source_file  VARCHAR(200),
    _ingested_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bronze.sweets (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(300),
    latitude      DOUBLE PRECISION,
    longitude     DOUBLE PRECISION,
    _source_file  VARCHAR(200),
    _ingested_at  TIMESTAMP DEFAULT NOW()
);

-- ── Pipeline 02 — Pharmacies (Egyfinder) ─────────────────────
CREATE TABLE IF NOT EXISTS bronze.pharmacies (
    id                      SERIAL PRIMARY KEY,
    name                    VARCHAR(300),
    address                 VARCHAR(500),
    phone                   VARCHAR(50),
    source_file             VARCHAR(300),
    web_scraper_start_url   VARCHAR(500),
    _source_file            VARCHAR(200),
    _ingested_at            TIMESTAMP DEFAULT NOW()
);

-- ── Pipeline 03 — Education ───────────────────────────────────
CREATE TABLE IF NOT EXISTS bronze.schools (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(300),
    type          VARCHAR(100),
    latitude      DOUBLE PRECISION,
    longitude     DOUBLE PRECISION,
    _source_file  VARCHAR(200),
    _ingested_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bronze.centers (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(300),
    type          VARCHAR(100),
    latitude      DOUBLE PRECISION,
    longitude     DOUBLE PRECISION,
    _source_file  VARCHAR(200),
    _ingested_at  TIMESTAMP DEFAULT NOW()
);

-- ── Pipeline 04 — Population ──────────────────────────────────
CREATE TABLE IF NOT EXISTS bronze.population (
    id            SERIAL PRIMARY KEY,
    data          JSONB,          -- flexible لأن columns CAPMAS بتتغير
    _source_file  VARCHAR(200),
    _ingested_at  TIMESTAMP DEFAULT NOW()
);

-- ── Pipeline 05 — Traffic Nodes ───────────────────────────────
CREATE TABLE IF NOT EXISTS bronze.traffic_nodes (
    id            SERIAL PRIMARY KEY,
    osmid         BIGINT,
    y             DOUBLE PRECISION,   -- latitude
    x             DOUBLE PRECISION,   -- longitude
    street_count  INTEGER,
    data          JSONB,              -- باقي الـ columns
    _source_file  VARCHAR(200),
    _ingested_at  TIMESTAMP DEFAULT NOW()
);

-- ── Pipeline 05 — Traffic Edges ───────────────────────────────
CREATE TABLE IF NOT EXISTS bronze.traffic_edges (
    id            SERIAL PRIMARY KEY,
    u             BIGINT,
    v             BIGINT,
    key_col       INTEGER,
    length        DOUBLE PRECISION,
    data          JSONB,              -- باقي الـ columns
    _source_file  VARCHAR(200),
    _ingested_at  TIMESTAMP DEFAULT NOW()
);

-- ── Ingestion Log ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bronze.ingestion_log (
    id            SERIAL PRIMARY KEY,
    filename      VARCHAR(200),
    dataset       VARCHAR(100),
    row_count     INTEGER,
    status        VARCHAR(20),    -- 'success' | 'error'
    error_msg     TEXT,
    ingested_at   TIMESTAMP DEFAULT NOW()
);
