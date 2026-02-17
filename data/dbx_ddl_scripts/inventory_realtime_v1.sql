-- DDL for retail_consumer_goods.supply_chain_control_tower.inventory_realtime_v1
-- Generated on 2026-02-03 22:32:33

CREATE TABLE retail_consumer_goods.supply_chain_control_tower.inventory_realtime_v1 (
  record_id INT COMMENT 'A unique identifier for each shipment record, allowing for easy tracking and reference.',
  reference_number STRING COMMENT 'An alphanumeric code used to reference the shipment, facilitating communication and tracking across systems.',
  product_id STRING COMMENT 'The identifier for the product being shipped, which links to product details in the inventory system.',
  product_name STRING COMMENT 'The name of the product being shipped, providing clarity on what is being transported.',
  status STRING COMMENT 'Indicates the current status of the shipment, such as in transit, delivered, or delayed, which is crucial for monitoring progress.',
  qty INT COMMENT 'The quantity of the product being shipped, essential for inventory management and order fulfillment.',
  unit_price DOUBLE COMMENT 'The price per unit of the product, useful for calculating total shipment value and financial analysis.',
  current_location STRING COMMENT 'The current geographical location of the shipment, which helps in tracking its movement.',
  latitude DOUBLE COMMENT 'The latitude coordinate of the current location, providing precise geographical positioning for logistics.',
  longitude DOUBLE COMMENT 'The longitude coordinate of the current location, complementing the latitude for accurate geographical tracking.',
  destination STRING COMMENT 'The intended delivery location for the shipment, important for route planning and logistics management.',
  time_remaining_to_destination_hours DOUBLE COMMENT 'Estimates the remaining time in hours until the shipment reaches its destination, aiding in delivery planning.',
  last_updated STRING,
  last_updated_cst STRING,
  expected_arrival_time STRING,
  batch_id STRING COMMENT 'An identifier for the batch of shipments, useful for grouping and managing multiple shipments together.',
  transit_status STRING COMMENT 'Represents the movement progress of the shipment within its transit phase, indicating stages such as Delayed , ontime.')
USING delta
COMMENT 'The table contains real-time data on shipments within the supply chain. It includes details such as product identifiers, shipment status, quantities, and current locations. This data can be used for tracking shipments, managing inventory levels, and optimizing logistics operations. Use cases include monitoring delivery progress, analyzing shipment delays, and planning for inventory replenishment.'
TBLPROPERTIES (
  'delta.minReaderVersion' = '1',
  'delta.minWriterVersion' = '2',
  'delta.parquet.compression.codec' = 'zstd')
;
