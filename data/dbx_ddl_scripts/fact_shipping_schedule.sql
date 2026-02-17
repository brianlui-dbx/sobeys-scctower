-- DDL for retail_consumer_goods.supply_chain_control_tower.fact_shipping_schedule
-- Generated on 2026-02-03 22:32:32

CREATE TABLE retail_consumer_goods.supply_chain_control_tower.fact_shipping_schedule (
  schedule_id STRING COMMENT 'A unique identifier for each shipping schedule entry, allowing for easy tracking and reference of specific schedules.',
  product_id STRING COMMENT 'Represents the unique identifier for the product involved in the event, facilitating product-specific analysis.',
  location_id STRING COMMENT 'Identifies the location associated with the shipping schedule, which is essential for logistics and distribution planning.Shows the DC location',
  customer_id STRING COMMENT 'Denotes the unique identifier for the customer receiving the shipment, enabling customer-specific tracking and order management.',
  schedule_date DATE COMMENT 'Specifies the exact date when the shipment is scheduled to occur, crucial for planning and operational efficiency.',
  qty INT COMMENT 'Represents the quantity of products scheduled for shipping, providing insight into order sizes and inventory management.',
  snapshot_date DATE COMMENT 'Captures the date on which the shipping schedule data was recorded, essential for historical analysis and data versioning.')
USING delta
COMMENT 'The table contains shipping schedule data related to product deliveries. It includes details such as the unique identifiers for schedules, products, locations, and customers, as well as the scheduled shipping date and quantity of products. This data can be used for logistics planning, tracking shipments, analyzing order sizes, and managing inventory effectively.'
TBLPROPERTIES (
  'delta.minReaderVersion' = '1',
  'delta.minWriterVersion' = '2',
  'delta.parquet.compression.codec' = 'zstd')
;
