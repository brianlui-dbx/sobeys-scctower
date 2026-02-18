CREATE OR REFRESH MATERIALIZED VIEW link_dc_customer (
  link_id,
  location_id COMMENT 'Shows the DC location',
  customer_id COMMENT 'Denotes the unique identifier for the customer',
  is_active,
  created_timestamp
)
COMMENT 'The table contains information about customer  and their corresponding DC.Each DC  supports Unique list of customers'
TBLPROPERTIES ('delta.feature.timestampNtz' = 'supported')
AS SELECT * FROM snowflake_retail_consumer_goods.supply_chain_control_tower.link_dc_customer;
