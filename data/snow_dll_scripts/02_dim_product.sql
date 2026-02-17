-- Snowflake Iceberg DDL for dim_product
-- Converted from: retail_consumer_goods.supply_chain_control_tower.dim_product

USE DATABASE retail_consumer_goods;
USE SCHEMA supply_chain_control_tower;

CREATE OR REPLACE ICEBERG TABLE dim_product (
  product_id VARCHAR
    COMMENT 'Represents the unique identifier for the product involved in the event, facilitating product-specific analysis.',
  name VARCHAR
    COMMENT 'The name of the product associated with the event, providing a more descriptive context for analysis and reporting.',
  cost_per_unit DOUBLE
    COMMENT 'The price per unit of the product, useful for calculating total shipment value and financial analysis.'
)
  CATALOG         = 'SNOWFLAKE'
  EXTERNAL_VOLUME = 'scctower_iceberg_vol'
  BASE_LOCATION   = 'dim_product/'
  COMMENT = 'The table contains detailed information about products within the supply chain. It includes unique identifiers, product names, and cost per unit. This data can be used for product-specific analysis, financial assessments, and reporting on shipment values.';
