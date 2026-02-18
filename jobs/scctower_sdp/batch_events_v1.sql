CREATE OR REFRESH MATERIALIZED VIEW batch_events_v1 (
  record_id COMMENT 'A unique identifier for each event record, allowing for easy reference and tracking of individual entries.',
  batch_id COMMENT 'Identifies the specific batch associated with the event, which is crucial for understanding the context of the product journey.',
  product_id COMMENT 'Represents the unique identifier for the product involved in the event, facilitating product-specific analysis.',
  product_name COMMENT 'The name of the product associated with the event, providing a more descriptive context for analysis and reporting.',
  event COMMENT 'Describes the type of event that occurred during the product journey, which is essential for tracking and analyzing supply chain activities.',
  event_time_cst COMMENT 'Records the timestamp of when the event occurred, allowing for chronological tracking and analysis of events over time.',
  entity_involved COMMENT 'Indicates the type of entity that was involved in the event, which can include suppliers, distributors, or other stakeholders in the supply chain.',
  entity_name COMMENT 'The name of the specific entity involved in the event, providing clarity on which organization or individual was part of the interaction.',
  entity_location COMMENT 'Describes the geographical location of the entity involved in the event, which is important for understanding the context of the supply chain.',
  entity_latitude COMMENT 'Provides the latitude coordinate of the entity location, enabling precise geographical analysis of events.',
  entity_longitude COMMENT 'Provides the longitude coordinate of the entity location, complementing the latitude for accurate mapping and geographical insights.',
  event_time_cst_readable COMMENT 'Human-readable format of the event timestamp, simplifying interpretation and analysis of chronological data.'
)
COMMENT 'The table captures events related to products within the supply chain. It includes details such as the product involved, the type of event, and the entities participating in these events. This data can be used for tracking product journeys, analyzing supply chain activities, and understanding the interactions between different stakeholders. Use cases include identifying trends in product movement, assessing the performance of suppliers or distributors, and conducting geographical analyses of supply chain events.'
TBLPROPERTIES ('delta.feature.timestampNtz' = 'supported')
AS SELECT * FROM snowflake_retail_consumer_goods.supply_chain_control_tower.batch_events_v1;
