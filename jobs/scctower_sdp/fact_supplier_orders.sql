CREATE OR REFRESH MATERIALIZED VIEW fact_supplier_orders (
  order_id COMMENT 'Represents the unique identifier for each purchase order, allowing for easy tracking and reference of specific orders.',
  supplier_id COMMENT 'Identifies the supplier from whom the products are being ordered, which is essential for managing supplier relationships and performance.',
  product_id COMMENT 'Denotes the unique identifier for each product being ordered, facilitating inventory management and product tracking.',
  qty COMMENT 'Indicates the quantity of products ordered in the purchase order, which is crucial for inventory planning and supply chain management.',
  expected_arrival_days COMMENT 'Specifies the number of days expected until the order arrives, helping in planning and managing inventory levels.',
  snapshot_date COMMENT 'Records the date when the data was captured, providing context for the order information and aiding in historical analysis.',
  expected_arrival_date
)
COMMENT 'The table contains data related to supplier orders within the supply chain. It includes details such as order identifiers, supplier and product information, quantities ordered, and expected arrival times. This data can be used for tracking orders, managing supplier relationships, and optimizing inventory levels.'
TBLPROPERTIES ('delta.feature.timestampNtz' = 'supported')
AS SELECT * FROM snowflake_retail_consumer_goods.supply_chain_control_tower.fact_supplier_orders;
