CREATE OR REFRESH MATERIALIZED VIEW inventory_realtime_v1 (
  record_id COMMENT 'A unique identifier for each shipment record, allowing for easy tracking and reference.',
  reference_number COMMENT 'An alphanumeric code used to reference the shipment, facilitating communication and tracking across systems.',
  product_id COMMENT 'The identifier for the product being shipped, which links to product details in the inventory system.',
  product_name COMMENT 'The name of the product being shipped, providing clarity on what is being transported.',
  status COMMENT 'Indicates the current status of the shipment, such as in transit, delivered, or delayed, which is crucial for monitoring progress.',
  qty COMMENT 'The quantity of the product being shipped, essential for inventory management and order fulfillment.',
  unit_price COMMENT 'The price per unit of the product, useful for calculating total shipment value and financial analysis.',
  current_location COMMENT 'The current geographical location of the shipment, which helps in tracking its movement.',
  latitude COMMENT 'The latitude coordinate of the current location, providing precise geographical positioning for logistics.',
  longitude COMMENT 'The longitude coordinate of the current location, complementing the latitude for accurate geographical tracking.',
  destination COMMENT 'The intended delivery location for the shipment, important for route planning and logistics management.',
  time_remaining_to_destination_hours COMMENT 'Estimates the remaining time in hours until the shipment reaches its destination, aiding in delivery planning.',
  last_updated,
  last_updated_cst,
  expected_arrival_time,
  batch_id COMMENT 'An identifier for the batch of shipments, useful for grouping and managing multiple shipments together.',
  transit_status COMMENT 'Represents the movement progress of the shipment within its transit phase, indicating stages such as Delayed , ontime.'
)
COMMENT 'The table contains real-time data on shipments within the supply chain. It includes details such as product identifiers, shipment status, quantities, and current locations. This data can be used for tracking shipments, managing inventory levels, and optimizing logistics operations. Use cases include monitoring delivery progress, analyzing shipment delays, and planning for inventory replenishment.'
TBLPROPERTIES ('delta.feature.timestampNtz' = 'supported')
AS SELECT * FROM snowflake_retail_consumer_goods.supply_chain_control_tower.inventory_realtime_v1;
