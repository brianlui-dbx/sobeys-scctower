-- Snowflake Iceberg DDL for dim_customer
-- Converted from: retail_consumer_goods.supply_chain_control_tower.dim_customer

USE DATABASE retail_consumer_goods;
USE SCHEMA supply_chain_control_tower;

CREATE OR REPLACE ICEBERG TABLE dim_customer (
  customer_id VARCHAR
    COMMENT 'Unique identifier for each customer entity in the supply chain.',
  name VARCHAR
    COMMENT 'The name of the specific entity involved in the event, providing clarity on which organization or individual was part of the interaction.',
  location VARCHAR
    COMMENT 'Describes the geographical location of the entity involved in the event, which is important for understanding the context of the supply chain.',
  latitude DOUBLE
    COMMENT 'Provides the latitude coordinate of the entity''s location, enabling precise geographical analysis of events.',
  longitude DOUBLE
    COMMENT 'Provides the longitude coordinate of the entity''s location, complementing the latitude for accurate mapping and geographical insights.'
)
  CATALOG         = 'SNOWFLAKE'
  EXTERNAL_VOLUME = 'scctower_iceberg_vol'
  BASE_LOCATION   = 'dim_customer/'
  COMMENT = 'The table contains data related to entities involved in supply chain events. It includes information such as customer identification, names of the entities, and their geographical locations. This data can be used for analyzing supply chain interactions, understanding regional dynamics, and mapping events geographically.';
