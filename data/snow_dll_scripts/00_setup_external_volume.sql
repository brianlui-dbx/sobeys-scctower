-- =============================================================================
-- Snowflake Setup: External Volume, Database, Schema, File Format
-- For Iceberg Tables (Snowflake as Iceberg Catalog)
-- =============================================================================

-- 1. Create the database and schema (equivalent to Databricks catalog.schema)
CREATE DATABASE IF NOT EXISTS retail_consumer_goods;
USE DATABASE retail_consumer_goods;

CREATE SCHEMA IF NOT EXISTS supply_chain_control_tower;
USE SCHEMA supply_chain_control_tower;

-- 2. Create the external volume
--    AZURE_TENANT_ID must be the tenant that owns the storage account.
--    Snowflake uses its own managed service principal (not your client credentials).
--    Cross-tenant access is configured via the consent flow in step 3.
CREATE OR REPLACE EXTERNAL VOLUME scctower_iceberg_vol
  STORAGE_LOCATIONS = (
    (
      NAME               = 'scctower-azure'
      STORAGE_BASE_URL   = 'azure://stbrianl2slko0183juc.blob.core.windows.net/datalake/scctower/iceberg/'
      STORAGE_PROVIDER   = 'AZURE'
      AZURE_TENANT_ID    = 'bf465dc7-3bc8-4944-b018-092572b5c20d'
    )
  );

-- 3. Retrieve Snowflake's service principal details for cross-tenant consent
--    Record these values from the output:
--      AZURE_CONSENT_URL          - Open this URL in a browser to grant consent in the storage tenant
--      AZURE_MULTI_TENANT_APP_NAME - The Snowflake service principal to grant storage access to
DESC EXTERNAL VOLUME scctower_iceberg_vol;

-- 4. Cross-tenant setup (manual steps in Azure Portal):
--    a) Open the AZURE_CONSENT_URL in a browser. Log in as an admin of tenant bf465dc7-...
--       and click "Accept" to register Snowflake's multi-tenant app in that tenant.
--    b) In Azure Portal > Storage Accounts > stbrianl2slko0183juc > Access Control (IAM):
--       - Add role assignment: "Storage Blob Data Contributor"
--       - Assign to the Snowflake service principal (search for AZURE_MULTI_TENANT_APP_NAME,
--         using only the portion before the underscore)
--       - Note: It can take up to 1 hour for the service principal to appear after consent.
--    c) Verify access:
SELECT SYSTEM$VERIFY_EXTERNAL_VOLUME('scctower_iceberg_vol');

-- 5. Create a file format for CSV data loading
CREATE OR REPLACE FILE FORMAT scctower_csv_format
  TYPE = 'CSV'
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  SKIP_HEADER = 1
  NULL_IF = ('null', 'NULL', '')
  EMPTY_FIELD_AS_NULL = TRUE
  TRIM_SPACE = TRUE;

-- 6. Create a stage for uploading CSV files
CREATE OR REPLACE STAGE scctower_csv_stage
  FILE_FORMAT = scctower_csv_format;
