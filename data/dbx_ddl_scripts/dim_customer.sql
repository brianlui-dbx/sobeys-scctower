-- DDL for retail_consumer_goods.supply_chain_control_tower.dim_customer
-- Generated on 2026-02-03 22:32:31

CREATE TABLE retail_consumer_goods.supply_chain_control_tower.dim_customer (
  customer_id STRING,
  name STRING COMMENT 'The name of the specific entity involved in the event, providing clarity on which organization or individual was part of the interaction.',
  location STRING COMMENT 'Describes the geographical location of the entity involved in the event, which is important for understanding the context of the supply chain.',
  latitude DOUBLE COMMENT 'Provides the latitude coordinate of the entity\'s location, enabling precise geographical analysis of events.',
  longitude DOUBLE COMMENT 'Provides the longitude coordinate of the entity\'s location, complementing the latitude for accurate mapping and geographical insights.')
USING delta
COMMENT 'The table contains data related to entities involved in supply chain events. It includes information such as customer identification, names of the entities, and their geographical locations. This data can be used for analyzing supply chain interactions, understanding regional dynamics, and mapping events geographically.'
TBLPROPERTIES (
  'delta.minReaderVersion' = '1',
  'delta.minWriterVersion' = '2',
  'delta.parquet.compression.codec' = 'zstd')
;
