-- =============================================================================
-- Snowflake Setup: External Volume, Database, Schema, File Format
-- For Iceberg Tables (Snowflake as Iceberg Catalog)
-- =============================================================================

-- 1. Create the database and schema (equivalent to Databricks catalog.schema)
CREATE DATABASE IF NOT EXISTS retail_consumer_goods;
USE DATABASE retail_consumer_goods;

CREATE SCHEMA IF NOT EXISTS supply_chain_control_tower;
USE SCHEMA supply_chain_control_tower;

CREATE OR REPLACE EXTERNAL VOLUME scctower_iceberg_vol
  STORAGE_LOCATIONS = (
    (
      NAME               = 'scctower-azure'
      STORAGE_BASE_URL   = 'azure://stbrianl2slko0183juc.blob.core.windows.net/datalake/scctower/iceberg/'
      STORAGE_PROVIDER   = 'AZURE'
      AZURE_TENANT_ID    = 'bf465dc7-3bc8-4944-b018-092572b5c20d'
    )
  );

-- 3. Verify the external volume was created
DESC EXTERNAL VOLUME scctower_iceberg_vol;

-- 4. Create a file format for CSV data loading
CREATE OR REPLACE FILE FORMAT scctower_csv_format
  TYPE = 'CSV'
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  SKIP_HEADER = 1
  NULL_IF = ('null', 'NULL', '')
  EMPTY_FIELD_AS_NULL = TRUE
  TRIM_SPACE = TRUE;

-- 5. Create a stage for uploading CSV files
CREATE OR REPLACE STAGE scctower_csv_stage
  FILE_FORMAT = scctower_csv_format;
