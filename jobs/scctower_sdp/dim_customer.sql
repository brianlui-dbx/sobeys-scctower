CREATE OR REFRESH MATERIALIZED VIEW dim_customer (
  customer_id,
  name COMMENT 'The name of the specific entity involved in the event, providing clarity on which organization or individual was part of the interaction.',
  location COMMENT 'Describes the geographical location of the entity involved in the event, which is important for understanding the context of the supply chain.',
  latitude COMMENT 'Provides the latitude coordinate of the entity location, enabling precise geographical analysis of events.',
  longitude COMMENT 'Provides the longitude coordinate of the entity location, complementing the latitude for accurate mapping and geographical insights.'
)
COMMENT 'The table contains data related to entities involved in supply chain events. It includes information such as customer identification, names of the entities, and their geographical locations. This data can be used for analyzing supply chain interactions, understanding regional dynamics, and mapping events geographically.'
TBLPROPERTIES ('delta.feature.timestampNtz' = 'supported')
AS SELECT * FROM snowflake_retail_consumer_goods.supply_chain_control_tower.dim_customer;
