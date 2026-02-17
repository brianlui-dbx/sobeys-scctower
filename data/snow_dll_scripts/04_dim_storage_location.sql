-- Snowflake Iceberg DDL for dim_storage_location
-- Converted from: retail_consumer_goods.supply_chain_control_tower.dim_storage_location

USE DATABASE retail_consumer_goods;
USE SCHEMA supply_chain_control_tower;

CREATE OR REPLACE ICEBERG TABLE dim_storage_location (
  location_id VARCHAR
    COMMENT 'Unique identifier for each storage location.',
  location_name VARCHAR
    COMMENT 'The name of the specific entity involved in the event, providing clarity on which organization or individual was part of the interaction.',
  type VARCHAR
    COMMENT 'The type of storage location (e.g., DC, Dock, Warehouse).',
  location VARCHAR
    COMMENT 'Describes the geographical location of the entity involved in the event, which is important for understanding the context of the supply chain.',
  latitude DOUBLE
    COMMENT 'Provides the latitude coordinate of the entity''s location, enabling precise geographical analysis of events.',
  longitude DOUBLE
    COMMENT 'Provides the longitude coordinate of the entity''s location, complementing the latitude for accurate mapping and geographical insights.'
)
  CATALOG         = 'SNOWFLAKE'
  EXTERNAL_VOLUME = 'scctower_iceberg_vol'
  BASE_LOCATION   = 'dim_storage_location/'
  COMMENT = 'The table contains information about various storage locations within the supply chain. It includes details such as the location''s name, type, and geographical coordinates (latitude and longitude). This data can be used for analyzing supply chain logistics, optimizing storage strategies, and understanding the geographical distribution of storage facilities.';
