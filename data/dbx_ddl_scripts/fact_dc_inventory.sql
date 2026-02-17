-- DDL for retail_consumer_goods.supply_chain_control_tower.fact_dc_inventory
-- Generated on 2026-02-03 22:32:32

CREATE TABLE retail_consumer_goods.supply_chain_control_tower.fact_dc_inventory (
  product_id STRING COMMENT 'Represents the unique identifier for the product involved in the event, facilitating product-specific analysis.',
  dc_id STRING COMMENT 'Identifies the location associated with the shipping schedule, which is essential for logistics and distribution planning.Shows the DC location',
  allocated_qty BIGINT COMMENT 'Indicates the quantity of products that have been allocated for specific orders or purposes, helping in inventory management.',
  safety_stock INT COMMENT 'Represents the minimum quantity of a product that must be kept on hand to prevent stockouts, ensuring availability during demand fluctuations.',
  excess_qty INT COMMENT 'Shows the quantity of products that exceed the desired inventory level, which can indicate overstock situations that may need addressing.',
  total_qty BIGINT COMMENT 'Reflects the total quantity of products available, combining allocated, safety stock, and excess quantities for a comprehensive view of inventory levels.',
  snapshot_date DATE COMMENT 'Denotes the date on which the inventory data was captured, providing a temporal context for the quantities reported.')
USING delta
COMMENT 'The table contains inventory data related to products in distribution centers. It includes information on product allocation, safety stock levels, excess inventory, and total quantities available. This data can be used for inventory management, logistics planning, and analyzing stock levels over time, helping to ensure that products are available to meet demand while minimizing overstock situations.'
TBLPROPERTIES (
  'delta.minReaderVersion' = '1',
  'delta.minWriterVersion' = '2',
  'delta.parquet.compression.codec' = 'zstd')
;
