-- DDL for retail_consumer_goods.supply_chain_control_tower.fact_incoming_supply
-- Generated on 2026-02-03 22:32:32

CREATE TABLE retail_consumer_goods.supply_chain_control_tower.fact_incoming_supply (
  shipment_id STRING COMMENT 'Identifies the unique shipment being tracked, allowing for easy reference and monitoring of specific deliveries.',
  source_location_id STRING COMMENT 'Represents the origin location from where the shipment is dispatched, which is crucial for understanding supply chain logistics.',
  product_id STRING COMMENT 'Denotes the specific product being shipped, enabling tracking of inventory and product availability.',
  destination_dc_id STRING COMMENT 'Indicates the distribution center where the shipment is intended to arrive, essential for planning and resource allocation.',
  qty INT COMMENT 'Specifies the quantity of the product included in the shipment, which is important for inventory management and demand forecasting.',
  expected_arrival_days INT COMMENT 'Estimates the number of days until the shipment is expected to arrive, aiding in delivery planning and customer communication.',
  snapshot_date DATE COMMENT 'Records the date when the shipment data was captured, allowing for historical analysis and tracking of shipment timelines.',
  expected_arrival_date DATE COMMENT 'Indicates the exact date when the shipment is expected to arrive, which is crucial for scheduling and inventory planning.')
USING delta
COMMENT 'The table contains data related to incoming shipments within the supply chain. It includes details such as shipment identification, source and destination locations, product information, quantities, and expected arrival dates. This data can be used for tracking shipments, managing inventory levels, and improving delivery planning and logistics operations.'
TBLPROPERTIES (
  'delta.minReaderVersion' = '1',
  'delta.minWriterVersion' = '2',
  'delta.parquet.compression.codec' = 'zstd')
;
