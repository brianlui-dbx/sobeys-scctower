-- Snowflake Iceberg DDL for fact_shipping_schedule
-- Converted from: retail_consumer_goods.supply_chain_control_tower.fact_shipping_schedule

USE DATABASE retail_consumer_goods;
USE SCHEMA supply_chain_control_tower;

CREATE OR REPLACE ICEBERG TABLE fact_shipping_schedule (
  schedule_id VARCHAR
    COMMENT 'A unique identifier for each shipping schedule entry, allowing for easy tracking and reference of specific schedules.',
  product_id VARCHAR
    COMMENT 'Represents the unique identifier for the product involved in the event, facilitating product-specific analysis.',
  location_id VARCHAR
    COMMENT 'Identifies the location associated with the shipping schedule, which is essential for logistics and distribution planning. Shows the DC location.',
  customer_id VARCHAR
    COMMENT 'Denotes the unique identifier for the customer receiving the shipment, enabling customer-specific tracking and order management.',
  schedule_date DATE
    COMMENT 'Specifies the exact date when the shipment is scheduled to occur, crucial for planning and operational efficiency.',
  qty INT
    COMMENT 'Represents the quantity of products scheduled for shipping, providing insight into order sizes and inventory management.',
  snapshot_date DATE
    COMMENT 'Captures the date on which the shipping schedule data was recorded, essential for historical analysis and data versioning.'
)
  CATALOG         = 'SNOWFLAKE'
  EXTERNAL_VOLUME = 'scctower_iceberg_vol'
  BASE_LOCATION   = 'fact_shipping_schedule/'
  COMMENT = 'The table contains shipping schedule data related to product deliveries. It includes details such as the unique identifiers for schedules, products, locations, and customers, as well as the scheduled shipping date and quantity of products. This data can be used for logistics planning, tracking shipments, analyzing order sizes, and managing inventory effectively.';
