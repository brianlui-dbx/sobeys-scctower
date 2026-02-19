"""
recreate_mas_supervisor.py

Recreates the SCC_Tower_Supply_Chain_Supervisor Supervisor Agent (MAS)
in a target Databricks workspace.

Captured from source workspace on 2026-02-19.
Source tile_id: 5fba20e2-a75d-478e-a25c-deb9a9fb92ae

PREREQUISITES
=============
The target workspace must have the following resources before running:

1. GENIE SPACES — recreate using genie-export-from-fieldengwest.py, then update
   GENIE_SPACE_IDS below with the IDs from the target workspace:
     - DC Inventory Genie Space
     - DC Shipment Plan Genie Space
     - Incoming Supply to DC Genie Space
     - Link Customer (DC-to-Customer) Genie Space
     - Supplier Orders Genie Space

2. UC FUNCTION — deploy the demand forecasting ML model and register the UC function:
     - Run: scripts/demand_forecast_train.py   (trains and logs the model)
     - Run: scripts/demand_forecast_deploy.py  (deploys the model serving endpoint)
     - Run: scripts/demand_forecast_uc_function.sql  (creates the UC function)
   Expected path: retail_consumer_goods.supply_chain_control_tower.predict_demand
   Update UC_FUNCTION_CATALOG / UC_FUNCTION_SCHEMA below if using a different catalog/schema.

3. MCP CONNECTION (Tavily) — create a UC HTTP Connection for real-time weather/distance data:
     CREATE CONNECTION tavily_mcp TYPE HTTP
     OPTIONS (
       host 'https://api.tavily.com',
       port '443',
       is_mcp_connection 'true'
     );
   Grant access to the agent service principal:
     GRANT USE CONNECTION ON CONNECTION tavily_mcp TO `<agent_service_principal>`;

USAGE
=====
Option A — Run in a Databricks notebook (uses dbutils for auth automatically):
  1. Upload this file to your workspace
  2. Update GENIE_SPACE_IDS with target workspace values
  3. Run all cells

Option B — Run locally with Databricks CLI configured:
  1. Set env vars: DATABRICKS_HOST, DATABRICKS_TOKEN
  2. Update GENIE_SPACE_IDS with target workspace values
  3. pip install requests databricks-sdk
  4. python scripts/recreate_mas_supervisor.py
"""

import os
import json
import requests
import time

# =============================================================================
# CONFIGURATION — UPDATE THESE FOR THE TARGET WORKSPACE
# =============================================================================

TARGET_WORKSPACE_URL = os.getenv(
    "DATABRICKS_HOST",
    "https://your-workspace.cloud.databricks.com"  # ← update or set DATABRICKS_HOST
)

# Leave blank to use DATABRICKS_TOKEN env var or notebook dbutils auth
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN", "")

# Genie Space IDs in the TARGET workspace.
# These are workspace-scoped IDs and differ from the source workspace.
# To find them: use the Genie UI URL (the ID is in the path) or the Genie API.
GENIE_SPACE_IDS = {
    "dc_inventory":    "REPLACE_WITH_TARGET_DC_INVENTORY_GENIE_ID",
    "dc_shipment_plan":"REPLACE_WITH_TARGET_DC_SHIPMENT_PLAN_GENIE_ID",
    "incoming_supply": "REPLACE_WITH_TARGET_INCOMING_SUPPLY_GENIE_ID",
    "link_customer":   "REPLACE_WITH_TARGET_LINK_CUSTOMER_GENIE_ID",
    "supplier_orders": "REPLACE_WITH_TARGET_SUPPLIER_ORDERS_GENIE_ID",
}

# UC Function location — update if using a different catalog/schema
UC_FUNCTION_CATALOG = "retail_consumer_goods"
UC_FUNCTION_SCHEMA  = "supply_chain_control_tower"
UC_FUNCTION_NAME    = "predict_demand"

# MCP Connection name registered in UC
MCP_CONNECTION_NAME = "tavily_mcp"

# Supervisor Agent name in the target workspace
MAS_NAME = "SCC_Tower_Supply_Chain_Supervisor"

# =============================================================================
# MAS CONFIGURATION — captured from source workspace, do not modify
# =============================================================================

MAS_DESCRIPTION = (
    '''
    This agent is an expert at planning supply chain scenarios. Looks at demand and supply and helps to make effective decisions. Routes queries to specialized Genie spaces covering DC inventory, shipment planning, incoming supply, customer-DC relationships, and supplier orders. Also includes demand forecasting powered by ML and real-time weather data from Tavily. 
    '''
)

MAS_INSTRUCTIONS = '''
You are the Supply Chain Control Tower supervisor. Route user queries to the most appropriate specialized agent or tool:

1. **dc_inventory** — Questions about current stock levels at Distribution Centers, excess inventory, stockout risks, safety stock, or inventory value by DC or product.

2. **dc_shipment_plan** — Questions about outbound shipments, customer demand, scheduled shipments in the next 5 days, shipment volume by DC or product, or which customers have the highest demand.

3. **incoming_supply** — Questions about inbound shipments to DCs, expected arrival dates and lead times, supply in transit, upcoming arrivals within the next N days, or supply value by product.

4. **link_customer** — Questions about which customers are served by which DC, the DC-to-customer mapping, active customer counts per DC, or customer assignments.

5. **supplier_orders** — Questions about purchase orders placed with suppliers, supplier lead times, overdue orders, total order value by supplier, or products currently on order.

6. **mcp-tavily-mcp** — Retrieval of weather information required for demand forecasting model inference.

7. **demand_forecast** — Predicts product demand (number of units) for a given customer, product, date, and weather forecast 

If a query spans multiple domains (e.g., comparing inventory at a DC against incoming supply to identify risks), call the relevant agents in sequence and synthesize their responses.

Additional rules:
Pass only the id of the entity to the sub agent , not both. Example: to check the current shipment plan pass the Storage location id like DC001 the the genie room DC_Shipment_plan
Always use the flow as Identify the DC-> Look for the product demand in the demand forecasting model -> Look for the excess in inventory--> Look for supply coming into the DC-> Look for the Closest DC Excess Qty-->Finally, review the supplier order and recommend expediting
When you look at DC inventory, don't consider allocated inventory. Consider only the excess for allocation
Always assume that the quantity asked for is the total, unless otherwise specified as "additional" in the question. Example: if asked "I want to ship x qty tomorrow to customer Y, then consider the qty which is already planned to ship tomorrow, compare that with the ask in question to identify additional requirements
You should Fist check  the planned shipment/Demand  for the respective day for the specified customer
When you are looking for additional inventory at DC always look for Excess quantity. Do not consider Safety stock as part of the plan unless it has been approved.
You should always end the first response by asking a question:" Do you approve of Safety stock allocation?". If approved, you should provide a revised plan; else stick with the current plan.
When the Safety Stock is approved use the Safety stock from the current DC only. Do not account other DC safety stocks
'''  

# Agent routing descriptions (critical for the supervisor's routing decisions)
AGENT_CONFIGS = [
    {
        "name": "dc_inventory",
        "type": "genie_space",
        "description": (
            "Provides visibility into current inventory status at each Distribution Center (DC) "
            "by product. Answers questions about stock levels, excess inventory, stockout risk, "
            "safety stock thresholds, and total inventory value. "
            "Use for questions about what is currently on hand at any DC."
        ),
    },
    {
        "name": "dc_shipment_plan",
        "type": "genie_space",
        "description": (
            "Provides details on the outbound shipment schedule from each DC to customers, "
            "covering orders due to ship within the next 5 days. "
            "Answers questions about customer demand, scheduled shipment quantities, "
            "shipment value, and top products by outbound volume. "
            "Use for questions about what needs to be shipped out."
        ),
    },
    {
        "name": "incoming_supply",
        "type": "genie_space",
        "description": (
            "Provides information on inbound supply shipments arriving at each DC, "
            "including expected arrival dates and days-to-arrival. "
            "Answers questions about what supply is in transit, which shipments arrive soonest, "
            "total incoming quantities by DC or product, and supply shipment value. "
            "Use for questions about what is coming in."
        ),
    },
    {
        "name": "link_customer",
        "type": "genie_space",
        "description": (
            "Provides information about the DC-to-customer relationship — "
            "which DC each customer is assigned to, active customer counts per DC, "
            "and customer locations. "
            "Answers questions about customer assignments, which DC serves a given customer, "
            "and how many customers each DC handles. "
            "Use for questions about customer-DC mappings."
        ),
    },
    {
        "name": "supplier_orders",
        "type": "genie_space",
        "description": (
            "Provides purchase order details for supplier replenishment, including order quantities, "
            "expected arrival dates, supplier lead times, and overdue orders. "
            "Answers questions about what is on order from suppliers, supplier performance, "
            "order value by supplier or product, and which orders are overdue. "
            "Use for questions about upstream procurement."
        ),
    },
    {
        "name": "demand_forecast",
        "type": "uc_function",
        "description": (
            "Predicts demand (number of units) for a given customer, product, date, "
            "and weather forecast using the demand forecasting ML model. "
            "Use this tool when asked about demand forecasting, demand planning, "
            "or predicted demand for a specific customer and product. "
            "IMPORTANT: Always search for the weather forecast first using the Tavily tool "
            "before calling this function, then pass the weather information as the "
            "weather_forecast parameter."
        ),
    },
    {
        "name": "mcp-tavily-mcp",
        "type": "mcp_connection",
        "description": (
            "MCP connection for Tavily MCP Server-Searcher Weather, distance, "
            "Transportation rates and all the real time data for the agent"
        ),
    },
]

# Example questions from source (used for routing evaluation)
MAS_EXAMPLES = [
    # Fetched count was 6; add them below if you export them separately.
    # Format: {"question": "...", "guideline": "Should route to <agent_name>"}
]

# =============================================================================
# HELPER: AUTHENTICATION
# =============================================================================

def _get_token():
    if DATABRICKS_TOKEN:
        return DATABRICKS_TOKEN
    try:
        # Running inside a Databricks notebook
        return (
            dbutils.notebook.entry_point  # noqa: F821
            .getDbutils().notebook().getContext()
            .apiToken().get()
        )
    except NameError:
        raise RuntimeError(
            "No token found. Set the DATABRICKS_TOKEN environment variable "
            "or run this script inside a Databricks notebook."
        )


def _headers():
    return {
        "Authorization": f"Bearer {_get_token()}",
        "Content-Type": "application/json",
    }

# =============================================================================
# STEP 1: VALIDATE PREREQUISITES
# =============================================================================

def validate_prerequisites():
    """Check that all required resources exist before attempting MAS creation."""
    errors = []

    # Check Genie space IDs have been filled in
    for key, gid in GENIE_SPACE_IDS.items():
        if gid.startswith("REPLACE_WITH"):
            errors.append(f"  GENIE_SPACE_IDS['{key}'] has not been set.")

    if errors:
        print("VALIDATION FAILED — missing configuration:")
        for e in errors:
            print(e)
        print(
            "\nUpdate GENIE_SPACE_IDS at the top of this script with the "
            "Genie space IDs from the target workspace, then re-run."
        )
        return False

    print("Configuration looks complete. Proceeding...")
    return True

# =============================================================================
# STEP 2: BUILD AGENT LIST
# =============================================================================

def build_agent_list():
    """Convert AGENT_CONFIGS into the format expected by the Agent Bricks API."""
    agents = []
    uc_fn = f"{UC_FUNCTION_CATALOG}.{UC_FUNCTION_SCHEMA}.{UC_FUNCTION_NAME}"

    for cfg in AGENT_CONFIGS:
        agent = {"name": cfg["name"], "description": cfg["description"]}

        if cfg["type"] == "genie_space":
            agent["genie_space_id"] = GENIE_SPACE_IDS[cfg["name"]]
        elif cfg["type"] == "uc_function":
            agent["uc_function_name"] = uc_fn
        elif cfg["type"] == "mcp_connection":
            agent["connection_name"] = MCP_CONNECTION_NAME
        else:
            raise ValueError(f"Unknown agent type: {cfg['type']}")

        agents.append(agent)

    return agents

# =============================================================================
# STEP 3: CREATE THE SUPERVISOR AGENT VIA THE AGENT BRICKS SDK
# =============================================================================

def create_supervisor_agent():
    """
    Create the Supervisor Agent using the Databricks Agent Bricks (AI Tiles) REST API.

    If you prefer using the databricks-sdk Python library instead of direct REST calls,
    replace the requests calls below with:
        from databricks.sdk import WorkspaceClient
        w = WorkspaceClient(host=TARGET_WORKSPACE_URL, token=_get_token())
        result = w.api_client.do("POST", "/api/2.0/agent-evaluation/tile-resources",
                                 body=payload)
    """
    agents = build_agent_list()
    payload = {
        "type": "SUPERVISOR",
        "name": MAS_NAME,
        "description": MAS_DESCRIPTION,
        "instructions": MAS_INSTRUCTIONS,
        "agents": agents,
    }
    if MAS_EXAMPLES:
        payload["examples"] = MAS_EXAMPLES

    url = f"{TARGET_WORKSPACE_URL}/api/2.0/agent-evaluation/tile-resources"

    print(f"Creating Supervisor Agent '{MAS_NAME}'...")
    print(f"  Agents ({len(agents)}):")
    for a in agents:
        agent_ref = next(
            (f"{k}={v}" for k, v in a.items()
             if k in ("genie_space_id", "uc_function_name", "connection_name", "endpoint_name", "ka_tile_id")),
            "(unknown)"
        )
        print(f"    - {a['name']:20s}  {agent_ref}")

    response = requests.post(url, headers=_headers(), json=payload)

    if response.status_code not in (200, 201):
        print(f"\nERROR {response.status_code}: {response.text}")
        response.raise_for_status()

    result = response.json()
    return result

# =============================================================================
# STEP 4: WAIT FOR ONLINE STATUS
# =============================================================================

def wait_for_online(tile_id, timeout_seconds=300, poll_interval=20):
    """Poll the tile until it reaches ONLINE status or times out."""
    url = f"{TARGET_WORKSPACE_URL}/api/2.0/agent-evaluation/tile-resources/{tile_id}"
    deadline = time.time() + timeout_seconds

    print(f"\nWaiting for endpoint to come ONLINE (timeout: {timeout_seconds}s)...")
    while time.time() < deadline:
        resp = requests.get(url, headers=_headers())
        resp.raise_for_status()
        status = resp.json().get("endpoint_status", "UNKNOWN")
        print(f"  Status: {status}")
        if status == "ONLINE":
            return True
        if status == "FAILED":
            print("  Endpoint reached FAILED state.")
            return False
        time.sleep(poll_interval)

    print("  Timed out waiting for ONLINE status. Check manually.")
    return False

# =============================================================================
# MAIN
# =============================================================================

def recreate():
    print("=" * 60)
    print(f"Recreating: {MAS_NAME}")
    print(f"Target workspace: {TARGET_WORKSPACE_URL}")
    print("=" * 60)

    if not validate_prerequisites():
        return

    result = create_supervisor_agent()

    tile_id = result.get("tile_id")
    status  = result.get("endpoint_status", "PROVISIONING")
    print(f"\nCreated successfully!")
    print(f"  tile_id:        {tile_id}")
    print(f"  endpoint_status: {status}")

    if status != "ONLINE":
        online = wait_for_online(tile_id)
        if online:
            print("\nSupervisor Agent is ONLINE and ready.")
        else:
            print(f"\nCheck status manually:")
            print(f"  GET {TARGET_WORKSPACE_URL}/api/2.0/agent-evaluation/tile-resources/{tile_id}")
    else:
        print("\nSupervisor Agent is ONLINE and ready.")

    print(f"\nDone. Save this tile_id for future updates: {tile_id}")
    return tile_id


if __name__ == "__main__":
    recreate()
