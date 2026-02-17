-- Snowflake Iceberg DDL for link_dc_customer
-- Converted from: retail_consumer_goods.supply_chain_control_tower.link_dc_customer

USE DATABASE retail_consumer_goods;
USE SCHEMA supply_chain_control_tower;

CREATE OR REPLACE ICEBERG TABLE link_dc_customer (
  link_id VARCHAR
    COMMENT 'Unique identifier for the DC-to-customer mapping.',
  location_id VARCHAR
    COMMENT 'Shows the DC location.',
  customer_id VARCHAR
    COMMENT 'Denotes the unique identifier for the customer.',
  is_active BOOLEAN
    COMMENT 'Indicates whether the DC-customer relationship is currently active.',
  created_timestamp TIMESTAMP
    COMMENT 'Timestamp when the DC-customer link was created.'
)
  CATALOG         = 'SNOWFLAKE'
  EXTERNAL_VOLUME = 'scctower_iceberg_vol'
  BASE_LOCATION   = 'link_dc_customer/'
  COMMENT = 'The table contains information about customer and their corresponding DC. Each DC supports a unique list of customers.';
