-- Post-pipeline script to apply column-level comments to materialized views
-- Run this after the scctower_sdp pipeline completes successfully.
-- SDP silently ignores inline COMMENT clauses in CREATE OR REFRESH MATERIALIZED VIEW
-- column definitions, so comments must be applied separately.
-- ALTER TABLE does not work on views; use COMMENT ON COLUMN instead.

USE CATALOG retail_consumer_goods;
USE SCHEMA supply_chain_control_tower;

-- batch_events_v1
COMMENT ON COLUMN batch_events_v1.record_id IS 'A unique identifier for each event record, allowing for easy reference and tracking of individual entries.';
COMMENT ON COLUMN batch_events_v1.batch_id IS 'Identifies the specific batch associated with the event, which is crucial for understanding the context of the product journey.';
COMMENT ON COLUMN batch_events_v1.product_id IS 'Represents the unique identifier for the product involved in the event, facilitating product-specific analysis.';
COMMENT ON COLUMN batch_events_v1.product_name IS 'The name of the product associated with the event, providing a more descriptive context for analysis and reporting.';
COMMENT ON COLUMN batch_events_v1.event IS 'Describes the type of event that occurred during the product journey, which is essential for tracking and analyzing supply chain activities.';
COMMENT ON COLUMN batch_events_v1.event_time_cst IS 'Records the timestamp of when the event occurred, allowing for chronological tracking and analysis of events over time.';
COMMENT ON COLUMN batch_events_v1.entity_involved IS 'Indicates the type of entity that was involved in the event, which can include suppliers, distributors, or other stakeholders in the supply chain.';
COMMENT ON COLUMN batch_events_v1.entity_name IS 'The name of the specific entity involved in the event, providing clarity on which organization or individual was part of the interaction.';
COMMENT ON COLUMN batch_events_v1.entity_location IS 'Describes the geographical location of the entity involved in the event, which is important for understanding the context of the supply chain.';
COMMENT ON COLUMN batch_events_v1.entity_latitude IS 'Provides the latitude coordinate of the entity location, enabling precise geographical analysis of events.';
COMMENT ON COLUMN batch_events_v1.entity_longitude IS 'Provides the longitude coordinate of the entity location, complementing the latitude for accurate mapping and geographical insights.';
COMMENT ON COLUMN batch_events_v1.event_time_cst_readable IS 'Human-readable format of the event timestamp, simplifying interpretation and analysis of chronological data.';

-- dim_customer
COMMENT ON COLUMN dim_customer.name IS 'The name of the specific entity involved in the event, providing clarity on which organization or individual was part of the interaction.';
COMMENT ON COLUMN dim_customer.location IS 'Describes the geographical location of the entity involved in the event, which is important for understanding the context of the supply chain.';
COMMENT ON COLUMN dim_customer.latitude IS 'Provides the latitude coordinate of the entity location, enabling precise geographical analysis of events.';
COMMENT ON COLUMN dim_customer.longitude IS 'Provides the longitude coordinate of the entity location, complementing the latitude for accurate mapping and geographical insights.';

-- dim_product
COMMENT ON COLUMN dim_product.product_id IS 'Represents the unique identifier for the product involved in the event, facilitating product-specific analysis.';
COMMENT ON COLUMN dim_product.name IS 'The name of the product associated with the event, providing a more descriptive context for analysis and reporting.';
COMMENT ON COLUMN dim_product.cost_per_unit IS 'The price per unit of the product, useful for calculating total shipment value and financial analysis.';

-- dim_storage_location
COMMENT ON COLUMN dim_storage_location.location_name IS 'The name of the specific entity involved in the event, providing clarity on which organization or individual was part of the interaction.';
COMMENT ON COLUMN dim_storage_location.location IS 'Describes the geographical location of the entity involved in the event, which is important for understanding the context of the supply chain.';
COMMENT ON COLUMN dim_storage_location.latitude IS 'Provides the latitude coordinate of the entity location, enabling precise geographical analysis of events.';
COMMENT ON COLUMN dim_storage_location.longitude IS 'Provides the longitude coordinate of the entity location, complementing the latitude for accurate mapping and geographical insights.';

-- dim_supplier
COMMENT ON COLUMN dim_supplier.name IS 'The name of the specific entity involved in the event, providing clarity on which organization or individual was part of the interaction.';
COMMENT ON COLUMN dim_supplier.location IS 'Describes the geographical location of the entity involved in the event, which is important for understanding the context of the supply chain.';
COMMENT ON COLUMN dim_supplier.latitude IS 'Provides the latitude coordinate of the entity location, enabling precise geographical analysis of events.';
COMMENT ON COLUMN dim_supplier.longitude IS 'Provides the longitude coordinate of the entity location, complementing the latitude for accurate mapping and geographical insights.';

-- fact_dc_inventory
COMMENT ON COLUMN fact_dc_inventory.product_id IS 'Represents the unique identifier for the product involved in the event, facilitating product-specific analysis.';
COMMENT ON COLUMN fact_dc_inventory.dc_id IS 'Identifies the location associated with the shipping schedule, which is essential for logistics and distribution planning. Shows the DC location.';
COMMENT ON COLUMN fact_dc_inventory.allocated_qty IS 'Indicates the quantity of products that have been allocated for specific orders or purposes, helping in inventory management.';
COMMENT ON COLUMN fact_dc_inventory.safety_stock IS 'Represents the minimum quantity of a product that must be kept on hand to prevent stockouts, ensuring availability during demand fluctuations.';
COMMENT ON COLUMN fact_dc_inventory.excess_qty IS 'Shows the quantity of products that exceed the desired inventory level, which can indicate overstock situations that may need addressing.';
COMMENT ON COLUMN fact_dc_inventory.total_qty IS 'Reflects the total quantity of products available, combining allocated, safety stock, and excess quantities for a comprehensive view of inventory levels.';
COMMENT ON COLUMN fact_dc_inventory.snapshot_date IS 'Denotes the date on which the inventory data was captured, providing a temporal context for the quantities reported.';

-- fact_incoming_supply
COMMENT ON COLUMN fact_incoming_supply.shipment_id IS 'Identifies the unique shipment being tracked, allowing for easy reference and monitoring of specific deliveries.';
COMMENT ON COLUMN fact_incoming_supply.source_location_id IS 'Represents the origin location from where the shipment is dispatched, which is crucial for understanding supply chain logistics.';
COMMENT ON COLUMN fact_incoming_supply.product_id IS 'Denotes the specific product being shipped, enabling tracking of inventory and product availability.';
COMMENT ON COLUMN fact_incoming_supply.destination_dc_id IS 'Indicates the distribution center where the shipment is intended to arrive, essential for planning and resource allocation.';
COMMENT ON COLUMN fact_incoming_supply.qty IS 'Specifies the quantity of the product included in the shipment, which is important for inventory management and demand forecasting.';
COMMENT ON COLUMN fact_incoming_supply.expected_arrival_days IS 'Estimates the number of days until the shipment is expected to arrive, aiding in delivery planning and customer communication.';
COMMENT ON COLUMN fact_incoming_supply.snapshot_date IS 'Records the date when the shipment data was captured, allowing for historical analysis and tracking of shipment timelines.';
COMMENT ON COLUMN fact_incoming_supply.expected_arrival_date IS 'Indicates the exact date when the shipment is expected to arrive, which is crucial for scheduling and inventory planning.';

-- fact_shipping_schedule
COMMENT ON COLUMN fact_shipping_schedule.schedule_id IS 'A unique identifier for each shipping schedule entry, allowing for easy tracking and reference of specific schedules.';
COMMENT ON COLUMN fact_shipping_schedule.product_id IS 'Represents the unique identifier for the product involved in the event, facilitating product-specific analysis.';
COMMENT ON COLUMN fact_shipping_schedule.location_id IS 'Identifies the location associated with the shipping schedule, which is essential for logistics and distribution planning. Shows the DC location.';
COMMENT ON COLUMN fact_shipping_schedule.customer_id IS 'Denotes the unique identifier for the customer receiving the shipment, enabling customer-specific tracking and order management.';
COMMENT ON COLUMN fact_shipping_schedule.schedule_date IS 'Specifies the exact date when the shipment is scheduled to occur, crucial for planning and operational efficiency.';
COMMENT ON COLUMN fact_shipping_schedule.qty IS 'Represents the quantity of products scheduled for shipping, providing insight into order sizes and inventory management.';
COMMENT ON COLUMN fact_shipping_schedule.snapshot_date IS 'Captures the date on which the shipping schedule data was recorded, essential for historical analysis and data versioning.';

-- fact_supplier_orders
COMMENT ON COLUMN fact_supplier_orders.order_id IS 'Represents the unique identifier for each purchase order, allowing for easy tracking and reference of specific orders.';
COMMENT ON COLUMN fact_supplier_orders.supplier_id IS 'Identifies the supplier from whom the products are being ordered, which is essential for managing supplier relationships and performance.';
COMMENT ON COLUMN fact_supplier_orders.product_id IS 'Denotes the unique identifier for each product being ordered, facilitating inventory management and product tracking.';
COMMENT ON COLUMN fact_supplier_orders.qty IS 'Indicates the quantity of products ordered in the purchase order, which is crucial for inventory planning and supply chain management.';
COMMENT ON COLUMN fact_supplier_orders.expected_arrival_days IS 'Specifies the number of days expected until the order arrives, helping in planning and managing inventory levels.';
COMMENT ON COLUMN fact_supplier_orders.snapshot_date IS 'Records the date when the data was captured, providing context for the order information and aiding in historical analysis.';

-- inventory_realtime_v1
COMMENT ON COLUMN inventory_realtime_v1.record_id IS 'A unique identifier for each shipment record, allowing for easy tracking and reference.';
COMMENT ON COLUMN inventory_realtime_v1.reference_number IS 'An alphanumeric code used to reference the shipment, facilitating communication and tracking across systems.';
COMMENT ON COLUMN inventory_realtime_v1.product_id IS 'The identifier for the product being shipped, which links to product details in the inventory system.';
COMMENT ON COLUMN inventory_realtime_v1.product_name IS 'The name of the product being shipped, providing clarity on what is being transported.';
COMMENT ON COLUMN inventory_realtime_v1.status IS 'Indicates the current status of the shipment, such as in transit, delivered, or delayed, which is crucial for monitoring progress.';
COMMENT ON COLUMN inventory_realtime_v1.qty IS 'The quantity of the product being shipped, essential for inventory management and order fulfillment.';
COMMENT ON COLUMN inventory_realtime_v1.unit_price IS 'The price per unit of the product, useful for calculating total shipment value and financial analysis.';
COMMENT ON COLUMN inventory_realtime_v1.current_location IS 'The current geographical location of the shipment, which helps in tracking its movement.';
COMMENT ON COLUMN inventory_realtime_v1.latitude IS 'The latitude coordinate of the current location, providing precise geographical positioning for logistics.';
COMMENT ON COLUMN inventory_realtime_v1.longitude IS 'The longitude coordinate of the current location, complementing the latitude for accurate geographical tracking.';
COMMENT ON COLUMN inventory_realtime_v1.destination IS 'The intended delivery location for the shipment, important for route planning and logistics management.';
COMMENT ON COLUMN inventory_realtime_v1.time_remaining_to_destination_hours IS 'Estimates the remaining time in hours until the shipment reaches its destination, aiding in delivery planning.';
COMMENT ON COLUMN inventory_realtime_v1.batch_id IS 'An identifier for the batch of shipments, useful for grouping and managing multiple shipments together.';
COMMENT ON COLUMN inventory_realtime_v1.transit_status IS 'Represents the movement progress of the shipment within its transit phase, indicating stages such as Delayed or ontime.';

-- link_dc_customer
COMMENT ON COLUMN link_dc_customer.location_id IS 'Shows the DC location.';
COMMENT ON COLUMN link_dc_customer.customer_id IS 'Denotes the unique identifier for the customer.';
