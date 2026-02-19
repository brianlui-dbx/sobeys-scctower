-- UC Function: Demand Forecast
-- Wraps the demand-forecast-endpoint model serving endpoint.
-- Takes customer name, product name, date, and weather forecast as input.
-- Returns predicted demand (number of units).

CREATE OR REPLACE FUNCTION retail_consumer_goods.supply_chain_control_tower.predict_demand(
    customer_name STRING COMMENT 'Name of the customer (e.g., FreshWay Supermarket)',
    product_name STRING COMMENT 'Name of the product (e.g., Organic Tomatoes)',
    forecast_date STRING COMMENT 'Date for the demand forecast in YYYY-MM-DD format (e.g., 2026-02-19)',
    weather_forecast STRING COMMENT 'Weather forecast description from Tavily search (e.g., sunny and warm, heavy rain expected, snow storm)'
)
RETURNS TABLE (
    customer STRING,
    product STRING,
    date STRING,
    weather STRING,
    predicted_demand BIGINT
)
COMMENT 'Predicts demand (number of units) for a given customer, product, date, and weather forecast using the demand forecasting ML model. Use this for demand planning and supply chain optimization. Always search for the weather forecast first using Tavily before calling this function.'
RETURN
    SELECT
        customer_name AS customer,
        product_name AS product,
        forecast_date AS date,
        weather_forecast AS weather,
        CAST(
            ai_query(
                'demand-forecast-endpoint',
                named_struct(
                    'customer_name', customer_name,
                    'product_name', product_name,
                    'date', forecast_date,
                    'weather_forecast', weather_forecast
                )
            ).predicted_demand AS BIGINT
        ) AS predicted_demand;
