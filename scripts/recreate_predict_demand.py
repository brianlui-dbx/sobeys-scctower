"""
recreate_predict_demand.py

Recreates the predict_demand UC function in a target Databricks workspace.
This is the full end-to-end script: trains the model, deploys the serving
endpoint, and registers the UC SQL function with the 2x safety factor.

PREREQUISITES
=============
The target workspace must have:

1. CATALOG & SCHEMA — the target catalog/schema must exist in Unity Catalog.
   Default: retail_consumer_goods.supply_chain_control_tower

2. TRAINING DATA — the demand_training_data table must exist in the target schema:
     retail_consumer_goods.supply_chain_control_tower.demand_training_data

3. DATABRICKS CLI — configured with a profile for the target workspace.

USAGE
=====
    # Using default profile and catalog/schema:
    python scripts/recreate_predict_demand.py

    # Using a specific CLI profile:
    python scripts/recreate_predict_demand.py --profile my-workspace

    # Using a different catalog/schema:
    python scripts/recreate_predict_demand.py --catalog my_catalog --schema my_schema

    # Skip model training/deploy (only recreate the UC function):
    python scripts/recreate_predict_demand.py --function-only

    # Skip function creation (only train and deploy the model):
    python scripts/recreate_predict_demand.py --model-only
"""

import argparse
import json
import subprocess
import sys
import textwrap


def get_warehouse_id(profile: str | None) -> str:
    """Return the first available SQL warehouse ID."""
    cmd = ["databricks", "api", "get", "/api/2.0/sql/warehouses"]
    if profile:
        cmd.extend(["--profile", profile])
    result = subprocess.run(cmd, capture_output=True, text=True)
    warehouses = json.loads(result.stdout).get("warehouses", [])
    for w in warehouses:
        if w.get("state") == "RUNNING":
            return w["id"]
    if warehouses:
        return warehouses[0]["id"]
    raise RuntimeError("No SQL warehouse found in workspace.")


def run_sql(sql: str, profile: str | None = None, warehouse_id: str | None = None) -> None:
    """Execute a SQL statement via the Databricks SQL Statements API."""
    if warehouse_id is None:
        warehouse_id = get_warehouse_id(profile)
    payload = json.dumps({
        "statement": sql,
        "warehouse_id": warehouse_id,
        "wait_timeout": "50s",
        "disposition": "INLINE",
        "format": "JSON_ARRAY",
    })
    cmd = ["databricks", "api", "post", "/api/2.0/sql/statements", "--json", payload]
    if profile:
        cmd.extend(["--profile", profile])
    print("  Executing SQL...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr.strip()}")
        sys.exit(1)
    response = json.loads(result.stdout)
    state = response.get("status", {}).get("state", "UNKNOWN")
    if state != "SUCCEEDED":
        error = response.get("status", {}).get("error", {})
        print(f"  ERROR ({state}): {error.get('message', result.stdout[:200])}")
        sys.exit(1)
    print("  OK")


def deploy_model(catalog: str, schema: str, profile: str | None = None) -> None:
    """Train the demand forecast model, deploy to a serving endpoint."""
    model_name = f"{catalog}.{schema}.demand_forecast_model"
    endpoint_name = "demand-forecast-endpoint"

    print("\n--- Step 1/3: Training demand forecast model ---")
    print(f"  Model: {model_name}")
    print("  This step must be run on a Databricks cluster (notebook or job).")
    print("  Run: scripts/demand_forecast_train.py")
    print("  The training script will register the model in Unity Catalog.")

    print(f"\n--- Step 2/3: Deploying model to serving endpoint ---")
    print(f"  Endpoint: {endpoint_name}")
    print("  Run: scripts/demand_forecast_deploy.py")
    print("  The deploy script will create/update the model serving endpoint.")


def create_uc_function(catalog: str, schema: str, profile: str | None = None, warehouse_id: str | None = None) -> None:
    """Create the predict_demand UC function with 2x safety factor."""
    endpoint_name = "demand-forecast-endpoint"
    full_name = f"{catalog}.{schema}.predict_demand"

    print(f"\n--- Step 3/3: Creating UC function ---")
    print(f"  Function: {full_name}")
    print(f"  Endpoint: {endpoint_name}")
    print(f"  Safety factor: 2x (doubles raw model prediction)")

    sql = textwrap.dedent(f"""\
        CREATE OR REPLACE FUNCTION {catalog}.{schema}.predict_demand(
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
        COMMENT 'Predicts demand (number of units) for a given customer, product, date, and weather forecast using the demand forecasting ML model. A 2x safety factor is applied to the raw model prediction to ensure supply buffer. Use this for demand planning and supply chain optimization. Always search for the weather forecast first using Tavily before calling this function.'
        RETURN
            SELECT
                customer_name AS customer,
                product_name AS product,
                forecast_date AS date,
                weather_forecast AS weather,
                CAST(
                    ai_query(
                        '{endpoint_name}',
                        named_struct(
                            'customer_name', customer_name,
                            'product_name', product_name,
                            'date', forecast_date,
                            'weather_forecast', weather_forecast
                        )
                    ).predicted_demand * 2 AS BIGINT
                ) AS predicted_demand
    """)

    run_sql(sql, profile, warehouse_id)
    print(f"\n  Function {full_name} created successfully.")


def verify_function(catalog: str, schema: str, profile: str | None = None, warehouse_id: str | None = None) -> None:
    """Verify the function exists by describing it."""
    full_name = f"{catalog}.{schema}.predict_demand"
    print(f"\n--- Verifying function ---")
    sql = f"DESCRIBE FUNCTION {full_name}"
    run_sql(sql, profile, warehouse_id)
    print(f"  Function {full_name} verified.")


def main():
    parser = argparse.ArgumentParser(
        description="Recreate the predict_demand UC function in a Databricks workspace."
    )
    parser.add_argument(
        "--profile",
        default=None,
        help="Databricks CLI profile for the target workspace.",
    )
    parser.add_argument(
        "--catalog",
        default="retail_consumer_goods",
        help="Target Unity Catalog name (default: retail_consumer_goods).",
    )
    parser.add_argument(
        "--schema",
        default="supply_chain_control_tower",
        help="Target schema name (default: supply_chain_control_tower).",
    )
    parser.add_argument(
        "--function-only",
        action="store_true",
        help="Only create the UC function (skip model training/deploy instructions).",
    )
    parser.add_argument(
        "--model-only",
        action="store_true",
        help="Only show model training/deploy instructions (skip UC function creation).",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  Recreate predict_demand UC Function")
    print(f"  Target: {args.catalog}.{args.schema}")
    if args.profile:
        print(f"  Profile: {args.profile}")
    print("=" * 60)

    warehouse_id = get_warehouse_id(args.profile) if not args.model_only else None

    if not args.function_only:
        deploy_model(args.catalog, args.schema, args.profile)

    if not args.model_only:
        create_uc_function(args.catalog, args.schema, args.profile, warehouse_id)
        verify_function(args.catalog, args.schema, args.profile, warehouse_id)

    print("\n" + "=" * 60)
    print("  Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
