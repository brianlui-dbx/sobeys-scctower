-- DDL for retail_consumer_goods.supply_chain_control_tower.link_dc_customer
-- Generated on 2026-02-03 22:32:33

CREATE TABLE retail_consumer_goods.supply_chain_control_tower.link_dc_customer (
  link_id STRING,
  location_id STRING COMMENT 'Shows the DC location',
  customer_id STRING COMMENT 'Denotes the unique identifier for the customer',
  is_active BOOLEAN,
  created_timestamp TIMESTAMP)
USING delta
COMMENT 'The table contains information about customer  and their corresponding DC.Each DC  supports Unique list of customers'
TBLPROPERTIES (
  'delta.minReaderVersion' = '1',
  'delta.minWriterVersion' = '2',
  'delta.parquet.compression.codec' = 'zstd')
;
