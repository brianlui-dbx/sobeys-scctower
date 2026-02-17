-- Snowflake Iceberg DDL for fact_supplier_orders
-- Converted from: retail_consumer_goods.supply_chain_control_tower.fact_supplier_orders

USE DATABASE retail_consumer_goods;
USE SCHEMA supply_chain_control_tower;

CREATE OR REPLACE ICEBERG TABLE fact_supplier_orders (
  order_id VARCHAR
    COMMENT 'Represents the unique identifier for each purchase order, allowing for easy tracking and reference of specific orders.',
  supplier_id VARCHAR
    COMMENT 'Identifies the supplier from whom the products are being ordered, which is essential for managing supplier relationships and performance.',
  product_id VARCHAR
    COMMENT 'Denotes the unique identifier for each product being ordered, facilitating inventory management and product tracking.',
  qty INT
    COMMENT 'Indicates the quantity of products ordered in the purchase order, which is crucial for inventory planning and supply chain management.',
  expected_arrival_days INT
    COMMENT 'Specifies the number of days expected until the order arrives, helping in planning and managing inventory levels.',
  snapshot_date DATE
    COMMENT 'Records the date when the data was captured, providing context for the order information and aiding in historical analysis.',
  expected_arrival_date DATE
    COMMENT 'The date on which the order is expected to arrive.'
)
  CATALOG         = 'SNOWFLAKE'
  EXTERNAL_VOLUME = 'scctower_iceberg_vol'
  BASE_LOCATION   = 'fact_supplier_orders/'
  COMMENT = 'The table contains data related to supplier orders within the supply chain. It includes details such as order identifiers, supplier and product information, quantities ordered, and expected arrival times. This data can be used for tracking orders, managing supplier relationships, and optimizing inventory levels.';
