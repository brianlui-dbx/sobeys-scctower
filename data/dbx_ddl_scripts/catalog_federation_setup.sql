-- =============================================================================
-- Databricks Catalog Federation: Snowflake Connection Setup
-- Federates Snowflake database `retail_consumer_goods` into Unity Catalog
-- Target schema: supply_chain_control_tower
-- =============================================================================

-- 1. Create a connection to Snowflake
--    Replace placeholder values (<...>) with your Snowflake account details.
--    The connection object is stored in Unity Catalog and can be shared across
--    workspaces within the same metastore.
CREATE CONNECTION IF NOT EXISTS snowflake_scctower
  TYPE snowflake
  OPTIONS (
    host        'NTNEFLN-QG31461.snowflakecomputing.com',
    port        '443',
    sfWarehouse '<your_warehouse>',
    user        secret('scctower-secrets', 'snowflake-federation-user'),
    password    secret('scctower-secrets', 'snowflake-federation-password')
  );

-- 2. Create a foreign catalog that mirrors the Snowflake database
--    This maps Snowflake database → Databricks catalog.
--    All schemas and tables within the database are accessible through the catalog.
--    AUTHORIZED PATH enables direct Iceberg reads from Azure storage
--    (bypasses the Snowflake query engine) using a path under an existing external location.
CREATE FOREIGN CATALOG IF NOT EXISTS snowflake_retail_consumer_goods
  USING CONNECTION snowflake_scctower
  OPTIONS (database 'RETAIL_CONSUMER_GOODS')
  WITH EXTERNAL LOCATION PATH 'abfss://datalake@stbrianl2slko0183juc.dfs.core.windows.net/scctower';
  WITH AUTHORIZED PATH 'abfss://datalake@stbrianl2slko0183juc.dfs.core.windows.net/scctower/iceberg/';

-- 3. Verify the connection and explore federated objects
--    After creating the catalog, the schema and tables should be visible:
SHOW SCHEMAS IN snowflake_retail_consumer_goods;

SHOW TABLES IN snowflake_retail_consumer_goods.supply_chain_control_tower;

-- 4. Test query — validate data is accessible through federation
SELECT * FROM snowflake_retail_consumer_goods.supply_chain_control_tower.dim_product LIMIT 5;

-- 5. (Optional) Grant access to other users or groups
--    Uncomment and modify as needed for your environment.
-- GRANT USE CATALOG ON CATALOG retail_consumer_goods TO `data-engineers`;
-- GRANT USE SCHEMA ON SCHEMA retail_consumer_goods.supply_chain_control_tower TO `data-engineers`;
-- GRANT SELECT ON SCHEMA retail_consumer_goods.supply_chain_control_tower TO `data-engineers`;
