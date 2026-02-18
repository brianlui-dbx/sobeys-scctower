CREATE OR REFRESH MATERIALIZED VIEW dim_storage_location (
  location_id,
  location_name COMMENT 'The name of the specific entity involved in the event, providing clarity on which organization or individual was part of the interaction.',
  type,
  location COMMENT 'Describes the geographical location of the entity involved in the event, which is important for understanding the context of the supply chain.',
  latitude COMMENT 'Provides the latitude coordinate of the entity location, enabling precise geographical analysis of events.',
  longitude COMMENT 'Provides the longitude coordinate of the entity location, complementing the latitude for accurate mapping and geographical insights.'
)
COMMENT 'The table contains information about various storage locations within the supply chain. It includes details such as the location name, type, and geographical coordinates (latitude and longitude). This data can be used for analyzing supply chain logistics, optimizing storage strategies, and understanding the geographical distribution of storage facilities.'
TBLPROPERTIES ('delta.feature.timestampNtz' = 'supported')
AS SELECT * FROM snowflake_retail_consumer_goods.supply_chain_control_tower.dim_storage_location;
