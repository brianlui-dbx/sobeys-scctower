"""
create_evaluation_bb7b182b.py

Adds evaluation datasets and scorers to the mas-bb7b182b-dev-experiment MLflow
experiment in the target Databricks workspace.

Creates:
  - Dataset: scc_tower_eval_v2
      20 supply chain questions covering all MAS agents, routing scenarios,
      multi-step workflows, and edge cases — using real entity names from the data.
  - Scorers (registered to the experiment):
      relevance_to_query     — built-in: is the response relevant?
      correctness            — built-in: are expected_facts present?
      completeness           — built-in: is the question fully addressed?
      supply_chain_routing   — custom:   did the agent route to the right sub-agent?
      tool_execution         — custom:   did the agent actually invoke the required tool?
      safety_stock_protocol  — custom:   does the agent follow the safety stock approval rule?

USAGE
=====
    python scripts/create_evaluation_bb7b182b.py
    python scripts/create_evaluation_bb7b182b.py --profile sobeysagentsdbw
"""

import argparse
import json
import os
import subprocess
import sys

# ─── Configuration ────────────────────────────────────────────────────────────

EXPERIMENT_NAME = "/Users/brian.lui@databricks.com/mas-bb7b182b-dev-experiment"
EXPERIMENT_ID   = "71289383921652"
DATASET_NAME    = "retail_consumer_goods.supply_chain_control_tower.scc_tower_eval_v2"
JUDGE_MODEL     = "databricks:/databricks-claude-sonnet-4-6"

# ─── Evaluation records ───────────────────────────────────────────────────────
# Each record:
#   inputs.question      — what the user asks the MAS
#   expectations:
#     expected_facts     — key data points the response MUST mention (for Correctness scorer)
#     guidelines         — routing + quality requirements (for custom routing scorer)

EVAL_RECORDS = [
    # ── DC Inventory (3 questions) ─────────────────────────────────────────────
    {
        "inputs": {"question": "Which DC has the highest excess inventory right now, and which product is it for?"},
        "expectations": {
            "expected_facts": [
                "A specific DC name or ID (e.g. DC001-DC005) is identified as having the highest excess",
                "A specific product name is provided (e.g. Organic Bananas, Organic Avocados, etc.)",
                "An excess quantity value is mentioned",
            ],
            "guidelines": (
                "The agent must route to the dc_inventory Genie space. "
                "The response must identify the DC with the highest excess and the specific product with a quantity."
            ),
        },
        "tags": {"target_agent": "dc_inventory", "scenario": "inventory_analysis"},
    },
    {
        "inputs": {"question": "Are there any products at risk of stockout at DC003 (Calgary)?"},
        "expectations": {
            "expected_facts": [
                "DC003 or Calgary is referenced in the response",
                "Safety stock levels or comparison of current stock to safety thresholds",
                "At least one specific product is mentioned with its stock level",
            ],
            "guidelines": (
                "The agent must query dc_inventory for DC003. "
                "Response must assess stockout risk by comparing current stock against safety stock thresholds."
            ),
        },
        "tags": {"target_agent": "dc_inventory", "scenario": "stockout_risk"},
    },
    {
        "inputs": {"question": "What is the total inventory value at DC002 (Mississauga) across all products?"},
        "expectations": {
            "expected_facts": [
                "DC002 or Mississauga is referenced",
                "A total monetary value or aggregated quantity is provided",
                "Multiple products are covered in the calculation",
            ],
            "guidelines": (
                "The agent must route to dc_inventory and aggregate across all products for DC002. "
                "Response must provide a total inventory value or quantity breakdown."
            ),
        },
        "tags": {"target_agent": "dc_inventory", "scenario": "inventory_value"},
    },

    # ── DC Shipment Plan (2 questions) ────────────────────────────────────────
    {
        "inputs": {"question": "What are the top 3 products scheduled to ship from DC001 (Dartmouth) in the next 5 days?"},
        "expectations": {
            "expected_facts": [
                "DC001 or Dartmouth is referenced",
                "At least 2 product names are listed with scheduled ship dates within 5 days",
                "Shipment quantities are included",
            ],
            "guidelines": (
                "The agent must route to the dc_shipment_plan Genie space and filter by DC001. "
                "Response must list top products by outbound volume with dates and quantities."
            ),
        },
        "tags": {"target_agent": "dc_shipment_plan", "scenario": "shipment_planning"},
    },
    {
        "inputs": {"question": "Which customer has the highest total demand across all DCs in the next 5 days?"},
        "expectations": {
            "expected_facts": [
                "A specific customer name is identified (e.g. Sobeys Markham, Farm Boy Ottawa, etc.)",
                "A demand quantity or order volume is stated",
                "A DC or shipment date context is given",
            ],
            "guidelines": (
                "The agent must query dc_shipment_plan for upcoming customer demand. "
                "Response must name a specific customer and provide their demand volume."
            ),
        },
        "tags": {"target_agent": "dc_shipment_plan", "scenario": "customer_demand"},
    },

    # ── Incoming Supply (2 questions) ─────────────────────────────────────────
    {
        "inputs": {"question": "What supply is arriving at DC002 (Mississauga) in the next 3 days?"},
        "expectations": {
            "expected_facts": [
                "DC002 or Mississauga is referenced",
                "Expected arrival dates within 3 days are mentioned",
                "At least one product and its incoming quantity are stated",
            ],
            "guidelines": (
                "The agent must query the incoming_supply Genie space filtering for DC002. "
                "Response must list inbound shipments with arrival dates and quantities."
            ),
        },
        "tags": {"target_agent": "incoming_supply", "scenario": "inbound_planning"},
    },
    {
        "inputs": {"question": "What is the total value of supply currently in transit across all DCs?"},
        "expectations": {
            "expected_facts": [
                "A total monetary value of in-transit supply is provided",
                "Multiple DCs are covered in the aggregation",
            ],
            "guidelines": (
                "The agent must query incoming_supply and aggregate across all DCs. "
                "Response must provide a total supply value figure."
            ),
        },
        "tags": {"target_agent": "incoming_supply", "scenario": "supply_value"},
    },

    # ── Link Customer (2 questions) ───────────────────────────────────────────
    {
        "inputs": {"question": "Which DC is responsible for serving Sobeys Markham?"},
        "expectations": {
            "expected_facts": [
                "Sobeys Markham is referenced",
                "A specific DC or distribution center is identified by name or ID",
            ],
            "guidelines": (
                "The agent must query the link_customer Genie space. "
                "Response must identify the specific DC that serves Sobeys Markham."
            ),
        },
        "tags": {"target_agent": "link_customer", "scenario": "customer_dc_mapping"},
    },
    {
        "inputs": {"question": "How many active customers does DC004 (Laval) serve?"},
        "expectations": {
            "expected_facts": [
                "DC004 or Laval is referenced",
                "A count of active customers is provided",
            ],
            "guidelines": (
                "The agent must query the link_customer Genie space for DC004. "
                "Response must provide the number of active customers."
            ),
        },
        "tags": {"target_agent": "link_customer", "scenario": "customer_count"},
    },

    # ── Supplier Orders (2 questions) ─────────────────────────────────────────
    {
        "inputs": {"question": "Which supplier orders are overdue or at risk of late delivery?"},
        "expectations": {
            "expected_facts": [
                "At least one supplier name is mentioned (e.g. Green Valley Produce Co., FreshHarvest Farms)",
                "Order expected arrival information (dates or days overdue) is provided",
                "Specific product names are included in the at-risk orders",
            ],
            "guidelines": (
                "The agent must query the supplier_orders Genie space. "
                "Response must identify overdue or at-risk orders with supplier, product, and timing details."
            ),
        },
        "tags": {"target_agent": "supplier_orders", "scenario": "supplier_risk"},
    },
    {
        "inputs": {"question": "What is the total order value from Sunrise Organic Growers?"},
        "expectations": {
            "expected_facts": [
                "Sunrise Organic Growers is referenced",
                "A total order value or quantity is provided",
                "At least one product ordered from this supplier is mentioned",
            ],
            "guidelines": (
                "The agent must query the supplier_orders Genie space filtering by Sunrise Organic Growers. "
                "Response must provide order value or quantity details for this supplier."
            ),
        },
        "tags": {"target_agent": "supplier_orders", "scenario": "supplier_detail"},
    },

    # ── Demand Forecasting (1 question) ───────────────────────────────────────
    {
        "inputs": {"question": (
            "Predict demand for Organic Bananas for Sobeys Markham "
            "for March 1, 2026."
        )},
        "expectations": {
            "expected_facts": [
                "Sobeys Markham is referenced",
                "Organic Bananas is referenced",
                "A numeric demand prediction (number of units) is provided",
                "Weather forecast information was retrieved and incorporated into the prediction",
            ],
            "guidelines": (
                "The agent must first call Tavily (mcp-tavily-mcp) to get a weather forecast, "
                "then call the demand_forecast UC function passing the weather result. "
                "Response must include a specific unit count and acknowledge the weather condition used."
            ),
        },
        "tags": {"target_agent": "demand_forecast", "scenario": "demand_planning"},
    },

    # ── Supplier Order Actions (2 questions) ──────────────────────────────────
    {
        "inputs": {"question": "Place an order for 500 units of Organic Strawberries."},
        "expectations": {
            "expected_facts": [
                "A purchase order confirmation number (PO-XXXXXXXX) is provided",
                "Organic Strawberries is referenced",
                "500 units is confirmed in the response",
                "A supplier name is mentioned",
            ],
            "guidelines": (
                "The agent must call the place_supplier_order UC function with product_name='Organic Strawberries' "
                "and unit_amount=500. Response must confirm placement with a PO number and supplier name."
            ),
        },
        "tags": {"target_agent": "place_supplier_order", "scenario": "order_action"},
    },
    {
        "inputs": {"question": "Expedite purchase order PO-12345678 — we need it faster."},
        "expectations": {
            "expected_facts": [
                "PO-12345678 is explicitly referenced",
                "An expedite confirmation is provided",
                "Reduced lead time or faster delivery is mentioned",
            ],
            "guidelines": (
                "The agent must call expedite_supplier_order UC function with po_number='PO-12345678'. "
                "Response must confirm the expedite request was actually sent to the supplier. "
                "The agent must NOT fabricate a successful response without calling the tool."
            ),
        },
        "tags": {"target_agent": "expedite_supplier_order", "scenario": "order_action"},
    },

    # ── System Integration (3 questions) ──────────────────────────────────────
    {
        "inputs": {"question": "What order does the AWR system currently have on record?"},
        "expectations": {
            "expected_facts": [
                "AWR (Automated Warehouse Replenishment) system is referenced",
                "A PO number is provided",
                "Product name and quantity from AWR are mentioned",
                "Order status and expected delivery are included",
            ],
            "guidelines": (
                "The agent must call get_order_from_AWR UC function. "
                "Response must display the full order record from AWR including PO number, product, quantity, and status."
            ),
        },
        "tags": {"target_agent": "get_order_from_AWR", "scenario": "system_integration"},
    },
    {
        "inputs": {"question": "Send the pending order to SAP for processing."},
        "expectations": {
            "expected_facts": [
                "SAP system is referenced",
                "A confirmation that the order was successfully sent is provided",
                "A SAP reference ID or document number is mentioned",
            ],
            "guidelines": (
                "The agent must call send_order_to_SAP UC function. "
                "Response must confirm successful submission to SAP with a reference number. "
                "The agent must NOT claim the tool is unavailable — it IS registered."
            ),
        },
        "tags": {"target_agent": "send_order_to_SAP", "scenario": "system_integration"},
    },
    {
        "inputs": {"question": "Retrieve the current order from CAO and then send it to SAP."},
        "expectations": {
            "expected_facts": [
                "CAO (Computer Assisted Ordering) is referenced",
                "SAP system is referenced",
                "Order details from CAO are shown (PO number, product, quantity)",
                "A SAP submission confirmation is provided",
            ],
            "guidelines": (
                "The agent must call get_order_from_CAO first, then call send_order_to_SAP. "
                "Both tool calls must be made in sequence. Response must show the CAO order "
                "details and confirm SAP submission."
            ),
        },
        "tags": {"target_agent": "multi_tool", "scenario": "system_integration_chain"},
    },

    # ── Multi-Domain / Cross-Agent (2 questions) ──────────────────────────────
    {
        "inputs": {"question": (
            "DC005 (Surrey) needs to ship 200 units of Organic Avocados to FreshCo Brampton "
            "tomorrow. Do we have enough stock? If not, what supply is arriving soon?"
        )},
        "expectations": {
            "expected_facts": [
                "DC005 or Surrey is referenced",
                "Organic Avocados is referenced",
                "Current inventory or excess quantity at DC005 is stated",
                "A comparison of stock vs. the 200-unit requirement is made",
                "Incoming supply data is included if stock is insufficient",
            ],
            "guidelines": (
                "The agent must query dc_inventory for DC005 stock of Organic Avocados, "
                "then check dc_shipment_plan for existing planned shipments, "
                "then query incoming_supply if there is a shortfall. "
                "The agent should follow the routing flow: inventory -> demand -> incoming supply. "
                "Response must end by asking about safety stock allocation approval."
            ),
        },
        "tags": {"target_agent": "multi_agent", "scenario": "cross_domain_planning"},
    },
    {
        "inputs": {"question": (
            "Compare the total excess inventory at DC001 (Dartmouth) vs DC002 (Mississauga). "
            "Which DC has more idle stock?"
        )},
        "expectations": {
            "expected_facts": [
                "DC001 or Dartmouth excess inventory is stated",
                "DC002 or Mississauga excess inventory is stated",
                "A comparison or ranking is provided",
                "Specific product-level detail is included",
            ],
            "guidelines": (
                "The agent must query dc_inventory for both DC001 and DC002. "
                "Response must provide excess quantities for both DCs and identify which has more."
            ),
        },
        "tags": {"target_agent": "dc_inventory", "scenario": "dc_comparison"},
    },

    # ── Safety Stock Protocol (1 question) ────────────────────────────────────
    {
        "inputs": {"question": (
            "I need to ship 1000 units of Organic Spinach from DC004 (Laval) to Farm Boy Ottawa. "
            "Can we fulfil this?"
        )},
        "expectations": {
            "expected_facts": [
                "DC004 or Laval is referenced",
                "Organic Spinach is referenced",
                "Farm Boy Ottawa is referenced",
                "Current excess inventory at DC004 is stated",
                "The response asks about safety stock allocation approval",
            ],
            "guidelines": (
                "The agent must check dc_inventory for DC004 Organic Spinach stock. "
                "If excess is insufficient, the agent MUST ask 'Do you approve of Safety stock allocation?' "
                "before including safety stock in the plan. "
                "The agent must NOT automatically include safety stock without asking."
            ),
        },
        "tags": {"target_agent": "dc_inventory", "scenario": "safety_stock_protocol"},
    },
]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get_ws_credentials(profile: str | None) -> tuple[str, str]:
    """Return (host, token) from the Databricks CLI."""
    cmd_base = ["databricks"]
    if profile:
        cmd_base.extend(["--profile", profile])

    host = subprocess.check_output(
        cmd_base + ["auth", "env"],
        stderr=subprocess.DEVNULL,
    )
    host_str = json.loads(host).get("env", {}).get("DATABRICKS_HOST", "")

    token = subprocess.check_output(
        cmd_base + ["auth", "token"],
        stderr=subprocess.DEVNULL,
    )
    token_str = json.loads(token).get("access_token", "")

    return host_str, token_str


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create evaluation datasets and scorers for mas-bb7b182b-dev-experiment."
    )
    parser.add_argument("--profile", default=None, help="Databricks CLI profile.")
    args = parser.parse_args()

    # ── Set up tracking URI & auth ───────────────────────────────────────────
    print("=" * 60)
    print("  Supply Chain Control Tower — Evaluation Setup (v2)")
    print(f"  Experiment: {EXPERIMENT_NAME}")
    print("=" * 60)

    host, token = _get_ws_credentials(args.profile)
    if not host or not token:
        print("ERROR: Could not retrieve Databricks credentials.")
        sys.exit(1)

    os.environ["MLFLOW_TRACKING_URI"] = "databricks"
    os.environ["DATABRICKS_HOST"]     = host
    os.environ["DATABRICKS_TOKEN"]    = token

    import mlflow
    from mlflow.genai.datasets import create_dataset, search_datasets
    from mlflow.genai.judges import make_judge
    from mlflow.genai.scorers import Completeness, Correctness, RelevanceToQuery

    mlflow.set_tracking_uri("databricks")

    # ── Step 1: Register scorers ──────────────────────────────────────────────
    print("\n── Step 1: Registering scorers ─────────────────────────────")

    scorers_to_register = [
        RelevanceToQuery(model=JUDGE_MODEL),
        Correctness(model=JUDGE_MODEL),
        Completeness(model=JUDGE_MODEL),
        make_judge(
            name="supply_chain_routing",
            model=JUDGE_MODEL,
            instructions="""\
Evaluate whether the Supply Chain Control Tower correctly routed the query
to the appropriate specialized agent(s) and used the right data source.

User inputs: {{ inputs }}

Assistant response: {{ outputs }}

Routing requirements from expectations: {{ expectations }}

Score YES if the assistant:
1. Called the correct specialized agent(s) described in the routing requirements (guidelines field)
2. Retrieved data that is consistent with having used the right data source
   (e.g., Genie space for inventory/shipment/supply data, UC function for actions/forecasting,
   Tavily for weather data before demand forecasting)
3. Included concrete data from the queried system (not just generic statements)

Score NO if the assistant:
1. Gave a generic answer without querying any tools or agents
2. Clearly queried the wrong data source (e.g., used inventory data for a supplier order question)
3. Skipped a required tool call (e.g., omitted Tavily weather lookup before demand forecast)
""",
            feedback_value_type=bool,
        ),
        make_judge(
            name="tool_execution",
            model=JUDGE_MODEL,
            instructions="""\
Evaluate whether the agent actually executed the required tool/function call
rather than fabricating a response without tool invocation.

User inputs: {{ inputs }}

Assistant response: {{ outputs }}

Expected behavior from expectations: {{ expectations }}

Score YES if:
1. The response contains specific data that could only come from an actual tool call
   (e.g., real PO numbers, specific quantities from database queries, SAP document numbers,
   system-generated confirmation IDs)
2. For action-oriented requests (place order, expedite, send to SAP/AWR/CAO), the response
   shows evidence of having invoked the function (specific confirmation details, not generic text)
3. The agent did NOT claim a tool was unavailable when the guidelines state it should exist

Score NO if:
1. The response appears to fabricate plausible-sounding results without having called the tool
   (e.g., generic "Successfully processed!" without system-specific confirmation details)
2. The agent says "I'll do that for you" or "Let me check" but then provides no actual result
3. The agent claims a tool is not available when the guidelines indicate it IS registered
4. The response is truncated mid-execution without completing the required tool call
""",
            feedback_value_type=bool,
        ),
        make_judge(
            name="safety_stock_protocol",
            model=JUDGE_MODEL,
            instructions="""\
Evaluate whether the agent follows the safety stock approval protocol correctly
in scenarios involving inventory allocation decisions.

User inputs: {{ inputs }}

Assistant response: {{ outputs }}

Expected behavior from expectations: {{ expectations }}

This scorer applies when the question involves fulfilling a shipment request
or allocating inventory where excess stock alone may not be sufficient.

Score YES if ANY of these conditions are met:
1. The question does NOT involve inventory allocation decisions — scorer is not applicable,
   so score YES by default
2. The agent uses ONLY excess inventory (not safety stock) in its initial plan
3. If excess is insufficient, the agent explicitly asks for safety stock allocation approval
   before including safety stock in the plan
4. The agent clearly separates what can be fulfilled from excess vs. what would require
   dipping into safety stock

Score NO if:
1. The agent includes safety stock in its plan without asking for approval first
2. The agent treats safety stock as freely available inventory without any mention of
   the approval requirement
3. The agent combines excess and safety stock totals without distinguishing between them
""",
            feedback_value_type=bool,
        ),
    ]

    registered_names = []
    for scorer in scorers_to_register:
        try:
            registered = scorer.register(experiment_id=EXPERIMENT_ID)
            print(f"  OK (registered):  {registered.name}")
            registered_names.append(registered.name)
        except Exception as e:
            err_str = str(e)
            if "already" in err_str.lower() or "ALREADY_EXISTS" in err_str:
                print(f"  OK (exists):      {scorer.name}")
                registered_names.append(scorer.name)
            else:
                print(f"  WARN: {scorer.name} — {e}")

    # ── Step 2: Create evaluation dataset ─────────────────────────────────────
    print("\n── Step 2: Creating evaluation dataset ─────────────────────")
    print(f"  Name:    {DATASET_NAME}")
    print(f"  Records: {len(EVAL_RECORDS)}")

    dataset = None
    try:
        dataset = create_dataset(
            name=DATASET_NAME,
            experiment_id=EXPERIMENT_ID,
        )
        print(f"  Created dataset: {dataset.dataset_id}")
    except Exception as e:
        if "already exists" in str(e).lower() or "ALREADY_EXISTS" in str(e) or "already" in str(e).lower():
            print(f"  Dataset '{DATASET_NAME}' already exists — finding it...")
            results = search_datasets(experiment_ids=[EXPERIMENT_ID])
            for ds in results:
                if ds.name == DATASET_NAME:
                    dataset = ds
                    print(f"  Found dataset:   {dataset.dataset_id}")
                    break
            if dataset is None:
                print(f"  WARN: Could not find existing dataset '{DATASET_NAME}'.")
        else:
            print(f"  ERROR creating dataset: {e}")
            raise

    if dataset is not None:
        try:
            dataset.merge_records(EVAL_RECORDS)
            print(f"  Merged {len(EVAL_RECORDS)} records. Digest: {dataset.digest}")
        except Exception as e:
            # Fallback: use databricks.agents directly if mlflow routing fails
            print(f"  merge_records via mlflow failed ({type(e).__name__}), trying databricks.agents...")
            try:
                from databricks.agents.datasets import get_dataset as db_get_dataset
                db_ds = db_get_dataset(DATASET_NAME)
                db_ds.merge_records(EVAL_RECORDS)
                print(f"  Merged {len(EVAL_RECORDS)} records via databricks.agents.")
            except Exception as e2:
                print(f"  WARN: Could not merge records: {e2}")
                print(f"  Dataset was created (ID: {dataset.dataset_id}) but records need to be added manually.")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  Setup complete.")
    print(f"  Experiment: {EXPERIMENT_NAME}")
    print(f"  Dataset:    {DATASET_NAME}  ({len(EVAL_RECORDS)} records)")
    print(f"  Scorers:    {', '.join(registered_names)}")
    print("=" * 60)
    print()
    print("Next step — run evaluation against the MAS endpoint:")
    print("  python scripts/run_evaluation_bb7b182b.py [--profile PROFILE]")


if __name__ == "__main__":
    main()
