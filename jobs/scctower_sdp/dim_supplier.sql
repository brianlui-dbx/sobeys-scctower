CREATE OR REFRESH MATERIALIZED VIEW dim_supplier (
  supplier_id,
  name COMMENT 'The name of the specific entity involved in the event, providing clarity on which organization or individual was part of the interaction.',
  location COMMENT 'Describes the geographical location of the entity involved in the event, which is important for understanding the context of the supply chain.',
  latitude COMMENT 'Provides the latitude coordinate of the entity location, enabling precise geographical analysis of events.',
  longitude COMMENT 'Provides the longitude coordinate of the entity location, complementing the latitude for accurate mapping and geographical insights.'
)
COMMENT 'The table contains information about suppliers within the supply chain. It includes details such as the supplier name, geographical location, and coordinates. This data can be used for analyzing supplier distribution, understanding regional supply chain dynamics, and mapping supplier locations for logistical planning.'
TBLPROPERTIES ('delta.feature.timestampNtz' = 'supported')
AS SELECT * FROM snowflake_retail_consumer_goods.supply_chain_control_tower.dim_supplier;
