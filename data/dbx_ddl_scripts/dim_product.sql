-- DDL for retail_consumer_goods.supply_chain_control_tower.dim_product
-- Generated on 2026-02-03 22:32:31

CREATE TABLE retail_consumer_goods.supply_chain_control_tower.dim_product (
  product_id STRING COMMENT 'Represents the unique identifier for the product involved in the event, facilitating product-specific analysis.',
  name STRING COMMENT 'The name of the product associated with the event, providing a more descriptive context for analysis and reporting.',
  cost_per_unit DOUBLE COMMENT 'The price per unit of the product, useful for calculating total shipment value and financial analysis.')
USING delta
COMMENT 'The table contains detailed information about products within the supply chain. It includes unique identifiers, product names, and cost per unit. This data can be used for product-specific analysis, financial assessments, and reporting on shipment values.'
TBLPROPERTIES (
  'delta.minReaderVersion' = '1',
  'delta.minWriterVersion' = '2',
  'delta.parquet.compression.codec' = 'zstd')
;
