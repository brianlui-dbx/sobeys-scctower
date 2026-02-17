-- Snowflake Iceberg DDL for dim_supplier
-- Converted from: retail_consumer_goods.supply_chain_control_tower.dim_supplier

USE DATABASE retail_consumer_goods;
USE SCHEMA supply_chain_control_tower;

CREATE OR REPLACE ICEBERG TABLE dim_supplier (
  supplier_id VARCHAR
    COMMENT 'Unique identifier for each supplier in the supply chain.',
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
  BASE_LOCATION   = 'dim_supplier/'
  COMMENT = 'The table contains information about suppliers within the supply chain. It includes details such as the supplier''s name, geographical location, and coordinates. This data can be used for analyzing supplier distribution, understanding regional supply chain dynamics, and mapping supplier locations for logistical planning.';
