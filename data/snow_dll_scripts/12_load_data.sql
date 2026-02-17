-- =============================================================================
-- Data Loading Script: Load CSV files into Snowflake Iceberg tables
-- =============================================================================
--
-- Prerequisites:
--   1. Run 00_setup_external_volume.sql (creates DB, schema, stage, file format)
--   2. Run 01–11 DDL scripts (creates all Iceberg tables)
--   3. Upload CSV files to the stage using SnowSQL:
--
--      snowsql -a <account> -u <user> -d retail_consumer_goods -s supply_chain_control_tower -q "
--        PUT file://data/dim_customer.csv          @scctower_csv_stage/dim_customer          AUTO_COMPRESS=TRUE;
--        PUT file://data/dim_product.csv           @scctower_csv_stage/dim_product           AUTO_COMPRESS=TRUE;
--        PUT file://data/dim_supplier.csv          @scctower_csv_stage/dim_supplier          AUTO_COMPRESS=TRUE;
--        PUT file://data/dim_storage_location.csv  @scctower_csv_stage/dim_storage_location  AUTO_COMPRESS=TRUE;
--        PUT file://data/fact_dc_inventory.csv     @scctower_csv_stage/fact_dc_inventory     AUTO_COMPRESS=TRUE;
--        PUT file://data/fact_incoming_supply.csv  @scctower_csv_stage/fact_incoming_supply  AUTO_COMPRESS=TRUE;
--        PUT file://data/fact_shipping_schedule.csv @scctower_csv_stage/fact_shipping_schedule AUTO_COMPRESS=TRUE;
--        PUT file://data/fact_supplier_orders.csv  @scctower_csv_stage/fact_supplier_orders  AUTO_COMPRESS=TRUE;
--        PUT file://data/inventory_realtime_v1.csv @scctower_csv_stage/inventory_realtime_v1 AUTO_COMPRESS=TRUE;
--        PUT file://data/link_dc_customer.csv      @scctower_csv_stage/link_dc_customer      AUTO_COMPRESS=TRUE;
--        PUT file://data/batch_events_v1.csv       @scctower_csv_stage/batch_events_v1       AUTO_COMPRESS=TRUE;
--      "
--
-- =============================================================================

USE DATABASE retail_consumer_goods;
USE SCHEMA supply_chain_control_tower;

-- ─────────────────────────────────────────────────────────────────────────────
-- dim_customer
-- ─────────────────────────────────────────────────────────────────────────────
COPY INTO dim_customer (customer_id, name, location, latitude, longitude)
  FROM @scctower_csv_stage/dim_customer
  FILE_FORMAT = scctower_csv_format
  ON_ERROR = 'ABORT_STATEMENT';

-- ─────────────────────────────────────────────────────────────────────────────
-- dim_product
-- ─────────────────────────────────────────────────────────────────────────────
COPY INTO dim_product (product_id, name, cost_per_unit)
  FROM @scctower_csv_stage/dim_product
  FILE_FORMAT = scctower_csv_format
  ON_ERROR = 'ABORT_STATEMENT';

-- ─────────────────────────────────────────────────────────────────────────────
-- dim_supplier
-- ─────────────────────────────────────────────────────────────────────────────
COPY INTO dim_supplier (supplier_id, name, location, latitude, longitude)
  FROM @scctower_csv_stage/dim_supplier
  FILE_FORMAT = scctower_csv_format
  ON_ERROR = 'ABORT_STATEMENT';

-- ─────────────────────────────────────────────────────────────────────────────
-- dim_storage_location
-- ─────────────────────────────────────────────────────────────────────────────
COPY INTO dim_storage_location (location_id, location_name, type, location, latitude, longitude)
  FROM @scctower_csv_stage/dim_storage_location
  FILE_FORMAT = scctower_csv_format
  ON_ERROR = 'ABORT_STATEMENT';

-- ─────────────────────────────────────────────────────────────────────────────
-- fact_dc_inventory
-- ─────────────────────────────────────────────────────────────────────────────
COPY INTO fact_dc_inventory (product_id, dc_id, allocated_qty, safety_stock, excess_qty, total_qty, snapshot_date)
  FROM @scctower_csv_stage/fact_dc_inventory
  FILE_FORMAT = scctower_csv_format
  ON_ERROR = 'ABORT_STATEMENT';

-- ─────────────────────────────────────────────────────────────────────────────
-- fact_incoming_supply
-- ─────────────────────────────────────────────────────────────────────────────
COPY INTO fact_incoming_supply (shipment_id, source_location_id, product_id, destination_dc_id, qty, expected_arrival_days, snapshot_date, expected_arrival_date)
  FROM @scctower_csv_stage/fact_incoming_supply
  FILE_FORMAT = scctower_csv_format
  ON_ERROR = 'ABORT_STATEMENT';

-- ─────────────────────────────────────────────────────────────────────────────
-- fact_shipping_schedule
-- ─────────────────────────────────────────────────────────────────────────────
COPY INTO fact_shipping_schedule (schedule_id, product_id, location_id, customer_id, schedule_date, qty, snapshot_date)
  FROM @scctower_csv_stage/fact_shipping_schedule
  FILE_FORMAT = scctower_csv_format
  ON_ERROR = 'ABORT_STATEMENT';

-- ─────────────────────────────────────────────────────────────────────────────
-- fact_supplier_orders
-- ─────────────────────────────────────────────────────────────────────────────
COPY INTO fact_supplier_orders (order_id, supplier_id, product_id, qty, expected_arrival_days, snapshot_date, expected_arrival_date)
  FROM @scctower_csv_stage/fact_supplier_orders
  FILE_FORMAT = scctower_csv_format
  ON_ERROR = 'ABORT_STATEMENT';

-- ─────────────────────────────────────────────────────────────────────────────
-- inventory_realtime_v1
-- ─────────────────────────────────────────────────────────────────────────────
COPY INTO inventory_realtime_v1 (
    record_id, reference_number, product_id, product_name, status,
    qty, unit_price, current_location, latitude, longitude,
    destination, time_remaining_to_destination_hours,
    last_updated, last_updated_cst, expected_arrival_time,
    batch_id, transit_status
)
  FROM @scctower_csv_stage/inventory_realtime_v1
  FILE_FORMAT = scctower_csv_format
  ON_ERROR = 'ABORT_STATEMENT';

-- ─────────────────────────────────────────────────────────────────────────────
-- link_dc_customer
-- ─────────────────────────────────────────────────────────────────────────────
COPY INTO link_dc_customer (link_id, location_id, customer_id, is_active, created_timestamp)
  FROM @scctower_csv_stage/link_dc_customer
  FILE_FORMAT = (
    TYPE = 'CSV'
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    SKIP_HEADER = 1
    NULL_IF = ('null', 'NULL', '')
    EMPTY_FIELD_AS_NULL = TRUE
    TRIM_SPACE = TRUE
  )
  ON_ERROR = 'ABORT_STATEMENT';

-- ─────────────────────────────────────────────────────────────────────────────
-- batch_events_v1
-- ─────────────────────────────────────────────────────────────────────────────
COPY INTO batch_events_v1 (
    record_id, batch_id, product_id, product_name, event,
    event_time_cst, entity_involved, entity_name, entity_location,
    entity_latitude, entity_longitude, event_time_cst_readable
)
  FROM @scctower_csv_stage/batch_events_v1
  FILE_FORMAT = scctower_csv_format
  ON_ERROR = 'ABORT_STATEMENT';

-- ─────────────────────────────────────────────────────────────────────────────
-- Verify row counts
-- ─────────────────────────────────────────────────────────────────────────────
SELECT 'dim_customer'          AS table_name, COUNT(*) AS row_count FROM dim_customer
UNION ALL SELECT 'dim_product',           COUNT(*) FROM dim_product
UNION ALL SELECT 'dim_supplier',          COUNT(*) FROM dim_supplier
UNION ALL SELECT 'dim_storage_location',  COUNT(*) FROM dim_storage_location
UNION ALL SELECT 'fact_dc_inventory',     COUNT(*) FROM fact_dc_inventory
UNION ALL SELECT 'fact_incoming_supply',  COUNT(*) FROM fact_incoming_supply
UNION ALL SELECT 'fact_shipping_schedule',COUNT(*) FROM fact_shipping_schedule
UNION ALL SELECT 'fact_supplier_orders',  COUNT(*) FROM fact_supplier_orders
UNION ALL SELECT 'inventory_realtime_v1', COUNT(*) FROM inventory_realtime_v1
UNION ALL SELECT 'link_dc_customer',      COUNT(*) FROM link_dc_customer
UNION ALL SELECT 'batch_events_v1',       COUNT(*) FROM batch_events_v1
ORDER BY table_name;
