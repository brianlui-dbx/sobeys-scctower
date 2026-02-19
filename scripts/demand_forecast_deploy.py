"""
Deploy the demand forecast model to a Model Serving endpoint.
Uses MLflow Deployments SDK for serverless serving with scale-to-zero.
"""

import mlflow
from mlflow.deployments import get_deploy_client

MODEL_NAME = "retail_consumer_goods.supply_chain_control_tower.demand_forecast_model"
MODEL_VERSION = "2"
ENDPOINT_NAME = "demand-forecast-endpoint"

mlflow.set_registry_uri("databricks-uc")
client = get_deploy_client("databricks")

print(f"Deploying {MODEL_NAME} v{MODEL_VERSION} to endpoint '{ENDPOINT_NAME}'...")

try:
    # Check if endpoint already exists
    existing = client.get_endpoint(ENDPOINT_NAME)
    print(f"Endpoint '{ENDPOINT_NAME}' already exists. Updating...")
    client.update_endpoint(
        endpoint=ENDPOINT_NAME,
        config={
            "served_entities": [
                {
                    "entity_name": MODEL_NAME,
                    "entity_version": MODEL_VERSION,
                    "workload_size": "Small",
                    "scale_to_zero_enabled": True,
                }
            ],
            "traffic_config": {
                "routes": [
                    {
                        "served_model_name": f"demand_forecast_model-{MODEL_VERSION}",
                        "traffic_percentage": 100,
                    }
                ]
            },
        },
    )
except Exception:
    print(f"Creating new endpoint '{ENDPOINT_NAME}'...")
    client.create_endpoint(
        name=ENDPOINT_NAME,
        config={
            "served_entities": [
                {
                    "entity_name": MODEL_NAME,
                    "entity_version": MODEL_VERSION,
                    "workload_size": "Small",
                    "scale_to_zero_enabled": True,
                }
            ]
        },
    )

print(f"Endpoint '{ENDPOINT_NAME}' deployment initiated!")
print("It may take several minutes for the endpoint to become READY.")
