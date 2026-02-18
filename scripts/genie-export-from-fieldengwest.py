import requests
import json
from datetime import datetime

# Configuration
WORKSPACE_URL = "https://e2-demo-west.cloud.databricks.com"
API_ENDPOINT = "/api/2.0/genie/spaces"

# Get authentication token
token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()

# Space IDs to export
spaces = {
    "DC_Shipment_plan": "01f0d174f47318d48c31b839b49d633b",
    "DC_inventory": "01f0d176d7ee1179bb7b0c87b9ff37d0",
    "Link_Customer": "01f0d17658c11f7bbfc81e874ac0baff",
    "Incoming_Supply_to_DC": "01f0d174335910cab56ec05d2d249acd",
    "Supplier_Orders": "01f0d173982c1226871f2426ee232ebe"
}

print(f"Ready to export {len(spaces)} Genie spaces")

# COMMAND ----------
def export_genie_space(space_name, space_id):
    url = f"{WORKSPACE_URL}{API_ENDPOINT}/{space_id}"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"include_serialized_space": "true"}
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

# COMMAND ----------
# Export all spaces
exported_spaces = {}

for space_name, space_id in spaces.items():
    print(f"Exporting {space_name}...")
    exported_spaces[space_name] = export_genie_space(space_name, space_id)
    print(f"✓ {space_name} exported")

print(f"\nExported {len(exported_spaces)} spaces successfully")

# COMMAND ----------
# Display results
for name, data in exported_spaces.items():
    print(f"\n{name}:")
    print(f"  Title: {data.get('title')}")
    print(f"  Description: {data.get('description')}")
    print(f"  Serialized config length: {len(data.get('serialized_space', ''))} chars")