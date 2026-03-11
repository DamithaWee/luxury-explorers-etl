-- ==========================================
-- 1. SCHEMA DEFINITIONS (Medallion Architecture)
-- ==========================================
-- We use 'transformation' for staging/cleaning and 'presentation' for the final Star Schema.
CREATE SCHEMA IF NOT EXISTS transformation;
CREATE SCHEMA IF NOT EXISTS presentation;

-- ==========================================
-- 2. TRANSFORMATION LAYER (Silver Zone)
-- ==========================================
-- This table accepts the raw data pulled down from S3.
-- Data types are intentionally permissive (VARCHAR) to prevent database crashes when loading dirty data.
CREATE TABLE transformation.nyc_inspections_staging (
    restaurant_id VARCHAR(50),
    name VARCHAR(255),
    borough VARCHAR(100),
    zipcode VARCHAR(20),
    category VARCHAR(255),
    inspection_date VARCHAR(50),
    score VARCHAR(20),
    grade VARCHAR(10),
    violation_description TEXT,
    critical_flag VARCHAR(50)
);

-- ==========================================
-- 3. PRESENTATION LAYER (Gold Zone / Star Schema)
-- ==========================================

-- Dimension Table 1: Restaurant Details
CREATE TABLE presentation.dim_restaurant (
    restaurant_id VARCHAR(50) PRIMARY KEY, -- Using the NYC CAMIS ID as the PK
    name VARCHAR(255) NOT NULL,
    category VARCHAR(255)
);

-- Dimension Table 2: Location Details
-- Surrogate key (SERIAL) because zip/boro combinations repeat across thousands of records.
CREATE TABLE presentation.dim_location (
    location_id SERIAL PRIMARY KEY,
    borough VARCHAR(100) NOT NULL,
    zipcode VARCHAR(20),
    CONSTRAINT unique_location UNIQUE (borough, zipcode)
);

-- Fact Table: Inspection Events
CREATE TABLE presentation.fact_inspection (
    inspection_id SERIAL PRIMARY KEY,
    restaurant_id VARCHAR(50) NOT NULL,
    location_id INT NOT NULL,
    inspection_date DATE NOT NULL,
    score INT,
    grade VARCHAR(10),
    violation_description TEXT,
    critical_flag VARCHAR(50),
    
    -- Foreign Key Constraints linking back to the dimensions
    CONSTRAINT fk_restaurant 
        FOREIGN KEY (restaurant_id) 
        REFERENCES presentation.dim_restaurant(restaurant_id)
        ON DELETE CASCADE,
        
    CONSTRAINT fk_location 
        FOREIGN KEY (location_id) 
        REFERENCES presentation.dim_location(location_id)
        ON DELETE CASCADE,

    -- Data Quality Check
    CONSTRAINT chk_score_positive CHECK (score >= 0)
);

-- ==========================================
-- 4. PERFORMANCE INDEXING
-- ==========================================

-- Index for category-based aggregations 
CREATE INDEX idx_dim_restaurant_category ON presentation.dim_restaurant(category);

-- Index for time-series analytics 
CREATE INDEX idx_fact_inspection_date ON presentation.fact_inspection(inspection_date);

-- Index for geographic aggregations
CREATE INDEX idx_dim_location_boro ON presentation.dim_location(borough);

-- Foreign key indexes to speed up JOIN operations between Facts and Dimensions
CREATE INDEX idx_fact_inspection_restaurant_id ON presentation.fact_inspection(restaurant_id);
CREATE INDEX idx_fact_inspection_location_id ON presentation.fact_inspection(location_id);