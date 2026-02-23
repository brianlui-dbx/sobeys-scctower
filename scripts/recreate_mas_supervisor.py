"""
recreate_mas_supervisor.py

Recreates the SCC_Tower_Supply_Chain_Supervisor Supervisor Agent (MAS)
in a target Databricks workspace.

Captured from source workspace on 2026-02-19.
Source tile_id: 5fba20e2-a75d-478e-a25c-deb9a9fb92ae

Last deployed to sobeysagentsdbw on 2026-02-23.
Current tile_id: db1b25a7-b412-43be-929f-e430e1b42235
Current endpoint: mas-db1b25a7-endpoint

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
    "dc_inventory":    "01f10d0ff1901eb193810415e62b6c99",
    "dc_shipment_plan":"01f10d0ff41a1f1bad465c9884729e7e",
    "incoming_supply": "01f10d0ff2f119a5b62015b6d842e697",
    "link_customer":   "01f10d0ff5771c2e807536dd10bff876",
    "supplier_orders": "01f10d0ff6ae1729b72b938a9c294daf",
}

# UC Function location — update if using a different catalog/schema
UC_FUNCTION_CATALOG = "retail_consumer_goods"
UC_FUNCTION_SCHEMA  = "supply_chain_control_tower"
UC_FUNCTION_NAME    = "predict_demand"  # legacy name used as default

# Additional UC Functions for supplier order actions and operational system integrations
# All located at UC_FUNCTION_CATALOG.UC_FUNCTION_SCHEMA.<name>
UC_SUPPLY_CHAIN_FUNCTIONS = [
    "place_supplier_order",
    "expedite_supplier_order",
    "get_order_from_AWR",
    "send_order_to_AWR",
    "get_order_from_CAO",
    "send_order_to_CAO",
    "get_order_from_SAP",
    "send_order_to_SAP",
]

# MCP Connection name registered in UC
MCP_CONNECTION_NAME = "tavily_mcp"

# Supervisor Agent name in the target workspace
MAS_NAME = "SCC_Tower_Supply_Chain_Supervisor"

# =============================================================================
# MAS CONFIGURATION — captured from source workspace, do not modify
# =============================================================================

MAS_DESCRIPTION = (
    '''
    This agent is an expert at planning supply chain scenarios. Looks at demand and supply and helps to make effective decisions. Routes queries to specialized Genie spaces covering DC inventory, shipment planning, incoming supply, customer-DC relationships, and supplier orders. Also includes demand forecasting powered by ML and real-time weather data from Tavily. Can take action by placing and expediting supplier orders, and by retrieving and sending orders to operational systems (AWR, CAO, SAP).
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

8. **place_supplier_order** — Places a new purchase order with a supplier for a given product and quantity. Use when the user wants to create or submit a new supplier order.

9. **expedite_supplier_order** — Expedites an existing supplier order by PO number. Use when the user wants to rush or prioritize an existing order.

10. **get_order_from_AWR** — Retrieves the current order from the AWR (Automated Warehouse Replenishment) system. Use when the user asks about the order in AWR or wants to review what AWR has on record.

11. **send_order_to_AWR** — Sends a pending order to the AWR (Automated Warehouse Replenishment) system. Use when the user wants to push or submit an order to AWR.

12. **get_order_from_CAO** — Retrieves the current order from the CAO (Computer Assisted Ordering) system. Use when the user asks about the order in CAO or wants to review what CAO has on record.

13. **send_order_to_CAO** — Sends a pending order to the CAO (Computer Assisted Ordering) system. Use when the user wants to push or submit an order to CAO.

14. **get_order_from_SAP** — Retrieves the current order from the SAP system. Use when the user asks about the order in SAP or wants to review what SAP has on record.

15. **send_order_to_SAP** — Sends a pending order to the SAP system. Use when the user wants to push or submit an order to SAP.

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
    {
        "name": "place_supplier_order",
        "type": "uc_function",
        "uc_fn": "place_supplier_order",
        "description": (
            "Places a new purchase order with a supplier for a given product name and unit amount. "
            "Returns an order confirmation number and the supplier name. "
            "Use this when the user wants to create or submit a new supplier order."
        ),
    },
    {
        "name": "expedite_supplier_order",
        "type": "uc_function",
        "uc_fn": "expedite_supplier_order",
        "description": (
            "Expedites an existing supplier order by providing a PO number. "
            "Sends a priority request to the supplier to reduce lead time. "
            "Use this when the user wants to rush or accelerate an existing order."
        ),
    },
    {
        "name": "get_order_from_AWR",
        "type": "uc_function",
        "uc_fn": "get_order_from_AWR",
        "description": (
            "Retrieves the current order from the AWR (Automated Warehouse Replenishment) system. "
            "Returns order details including PO number, product, quantity, status, supplier, and expected delivery. "
            "Use when the user asks about what AWR has on record or wants to review the AWR order."
        ),
    },
    {
        "name": "send_order_to_AWR",
        "type": "uc_function",
        "uc_fn": "send_order_to_AWR",
        "description": (
            "Sends a pending order to the AWR (Automated Warehouse Replenishment) system. "
            "Returns a confirmation that the order was successfully submitted to AWR. "
            "Use when the user wants to push or submit an order into AWR."
        ),
    },
    {
        "name": "get_order_from_CAO",
        "type": "uc_function",
        "uc_fn": "get_order_from_CAO",
        "description": (
            "Retrieves the current order from the CAO (Computer Assisted Ordering) system. "
            "Returns order details including PO number, product, quantity, status, supplier, and expected delivery. "
            "Use when the user asks about what CAO has on record or wants to review the CAO order."
        ),
    },
    {
        "name": "send_order_to_CAO",
        "type": "uc_function",
        "uc_fn": "send_order_to_CAO",
        "description": (
            "Sends a pending order to the CAO (Computer Assisted Ordering) system. "
            "Returns a confirmation that the order was successfully submitted to CAO. "
            "Use when the user wants to push or submit an order into CAO."
        ),
    },
    {
        "name": "get_order_from_SAP",
        "type": "uc_function",
        "uc_fn": "get_order_from_SAP",
        "description": (
            "Retrieves the current order from the SAP system. "
            "Returns order details including SAP document number, product, quantity, status, supplier, and expected delivery. "
            "Use when the user asks about what SAP has on record or wants to review the SAP order."
        ),
    },
    {
        "name": "send_order_to_SAP",
        "type": "uc_function",
        "uc_fn": "send_order_to_SAP",
        "description": (
            "Sends a pending order to the SAP system. "
            "Returns a confirmation including the SAP document number created. "
            "Use when the user wants to push or submit an order into SAP."
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
    """Convert AGENT_CONFIGS into the format expected by the Agent Bricks REST API.

    The API uses agent_type as a discriminator with nested payload objects:
      - genie-space           → genie_space: {id: "..."}
      - unity-catalog-function→ unity_catalog_function: {uc_path: {catalog, schema, name}}
      - external-mcp-server   → external_mcp_server: {connection_name: "..."}
    """
    agents = []
    default_fn_name = UC_FUNCTION_NAME

    for cfg in AGENT_CONFIGS:
        agent = {"name": cfg["name"], "description": cfg["description"]}

        if cfg["type"] == "genie_space":
            agent["agent_type"] = "genie-space"
            agent["genie_space"] = {"id": GENIE_SPACE_IDS[cfg["name"]]}
        elif cfg["type"] == "uc_function":
            fn_name = cfg.get("uc_fn", default_fn_name)
            agent["agent_type"] = "unity-catalog-function"
            agent["unity_catalog_function"] = {
                "uc_path": {
                    "catalog": UC_FUNCTION_CATALOG,
                    "schema":  UC_FUNCTION_SCHEMA,
                    "name":    fn_name,
                }
            }
        elif cfg["type"] == "mcp_connection":
            agent["agent_type"] = "external-mcp-server"
            agent["external_mcp_server"] = {"connection_name": MCP_CONNECTION_NAME}
        else:
            raise ValueError(f"Unknown agent type: {cfg['type']}")

        agents.append(agent)

    return agents

# =============================================================================
# STEP 3: CREATE THE SUPERVISOR AGENT VIA THE AGENT BRICKS SDK
# =============================================================================

def _find_existing_tile_id(name: str) -> str | None:
    """Search for an existing Supervisor Agent by name; return tile_id or None.

    Uses GET /api/2.0/tiles which lists all Agent Bricks tiles (KA, Genie, MAS).
    """
    url = f"{TARGET_WORKSPACE_URL}/api/2.0/tiles"
    resp = requests.get(url, headers=_headers())
    if resp.status_code != 200:
        return None
    items = resp.json().get("tiles", [])
    sanitized = name.replace(" ", "_")
    for item in items:
        if item.get("name") in (name, sanitized) and item.get("tile_type") == "MAS":
            return item.get("tile_id")
    return None


def create_supervisor_agent():
    """
    Create (or update if already exists) the Supervisor Agent via the Agent Bricks REST API.

    POST /api/2.0/multi-agent-supervisors  — create
    PUT  /api/2.0/multi-agent-supervisors/{tile_id} — update (if name already exists)
    """
    agents = build_agent_list()
    payload = {
        "name": MAS_NAME,
        "description": MAS_DESCRIPTION,
        "instructions": MAS_INSTRUCTIONS,
        "agents": agents,
    }
    if MAS_EXAMPLES:
        payload["examples"] = MAS_EXAMPLES

    base_url = f"{TARGET_WORKSPACE_URL}/api/2.0/multi-agent-supervisors"

    print(f"Creating Supervisor Agent '{MAS_NAME}'...")
    print(f"  Agents ({len(agents)}):")
    for a in agents:
        atype = a.get("agent_type", "?")
        if atype == "genie-space":
            ref = f"genie_space_id={a.get('genie_space', {}).get('id', '?')}"
        elif atype == "unity-catalog-function":
            uc = a.get("unity_catalog_function", {}).get("uc_path", {})
            ref = f"uc_function={uc.get('catalog','')}.{uc.get('schema','')}.{uc.get('name','')}"
        elif atype == "external-mcp-server":
            ref = f"connection_name={a.get('external_mcp_server', {}).get('connection_name', '?')}"
        else:
            ref = "(unknown)"
        print(f"    - {a['name']:26s}  [{atype}]  {ref}")

    response = requests.post(base_url, headers=_headers(), json=payload)

    if response.status_code == 409:
        # Already exists — find the tile_id and update instead
        print(f"\n  409 Conflict: '{MAS_NAME}' already exists. Looking up existing tile_id...")
        existing_tile_id = _find_existing_tile_id(MAS_NAME)
        if existing_tile_id:
            print(f"  Found tile_id: {existing_tile_id}. Updating via PATCH...")
            patch_url = f"{base_url}/{existing_tile_id}"
            response = requests.patch(patch_url, headers=_headers(), json=payload)
        else:
            print(f"  Could not find existing tile_id. Cannot update.")
            response.raise_for_status()

    if response.status_code not in (200, 201):
        print(f"\nERROR {response.status_code}: {response.text}")
        response.raise_for_status()

    raw = response.json()

    # Normalise the response: both POST and PATCH may wrap the result
    # under {"multi_agent_supervisor": {"tile": {...}}}.
    if "multi_agent_supervisor" in raw:
        tile = raw["multi_agent_supervisor"].get("tile", {})
        normalized = {
            "tile_id": tile.get("tile_id"),
            "endpoint_status": "PROVISIONING",  # check endpoint separately
            "endpoint_name": tile.get("serving_endpoint_name", ""),
        }
    else:
        normalized = raw

    return normalized

# =============================================================================
# STEP 4: WAIT FOR ONLINE STATUS
# =============================================================================

def wait_for_online(tile_id, timeout_seconds=300, poll_interval=20):
    """Poll the serving endpoint until it reaches READY status or times out."""
    if not tile_id:
        print("  No tile_id available — skipping endpoint wait.")
        return None
    endpoint_name = f"mas-{tile_id[:8]}-endpoint"
    url = f"{TARGET_WORKSPACE_URL}/api/2.0/serving-endpoints/{endpoint_name}"
    deadline = time.time() + timeout_seconds

    print(f"\nWaiting for endpoint '{endpoint_name}' to come READY (timeout: {timeout_seconds}s)...")
    while time.time() < deadline:
        resp = requests.get(url, headers=_headers())
        if resp.status_code == 404:
            print("  Endpoint not yet created, waiting...")
            time.sleep(poll_interval)
            continue
        resp.raise_for_status()
        state = resp.json().get("state", {}).get("ready", "NOT_READY")
        print(f"  Status: {state}")
        if state == "READY":
            return True
        if state == "FAILED":
            print("  Endpoint reached FAILED state.")
            return False
        time.sleep(poll_interval)

    print("  Timed out waiting for READY status. Check manually.")
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

    tile_id      = result.get("tile_id")
    status       = result.get("endpoint_status", "PROVISIONING")
    endpoint_name = result.get("endpoint_name") or (f"mas-{tile_id[:8]}-endpoint" if tile_id else "")
    print(f"\nCreated/Updated successfully!")
    print(f"  tile_id:         {tile_id}")
    print(f"  endpoint:        {endpoint_name}")
    print(f"  endpoint_status: {status}")

    if status != "ONLINE":
        online = wait_for_online(tile_id)
        if online is None:
            print("\nSupervisor Agent update complete (endpoint already running).")
        elif online:
            print("\nSupervisor Agent is ONLINE and ready.")
        else:
            print(f"\nCheck status manually:")
            print(f"  GET {TARGET_WORKSPACE_URL}/api/2.0/serving-endpoints/{endpoint_name}")
    else:
        print("\nSupervisor Agent is ONLINE and ready.")

    print(f"\nDone. Save this tile_id for future updates: {tile_id}")
    return tile_id


if __name__ == "__main__":
    recreate()
