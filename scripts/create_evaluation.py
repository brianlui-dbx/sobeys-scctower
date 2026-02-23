"""
create_evaluation.py

Adds evaluation datasets and scorers to the mas-db1b25a7-dev-experiment MLflow
experiment in the target Databricks workspace.

Creates:
  - Dataset: scc_tower_supply_chain_questions_v1
      13 supply chain questions covering all MAS agents and routing scenarios
  - Scorers (registered to the experiment):
      relevance_to_query     — built-in: is the response relevant?
      correctness            — built-in: are expected_facts present?
      completeness           — built-in: is the question fully addressed?
      supply_chain_routing   — custom:   did the agent route to the right sub-agent?

USAGE
=====
    python scripts/create_evaluation.py
    python scripts/create_evaluation.py --profile sobeysagentsdbw
"""

import argparse
import json
import os
import subprocess
import sys

# ─── Configuration ────────────────────────────────────────────────────────────

EXPERIMENT_NAME = "/Users/brian.lui@databricks.com/mas-db1b25a7-dev-experiment"
EXPERIMENT_ID   = "3708509851031113"
DATASET_NAME    = "retail_consumer_goods.supply_chain_control_tower.scc_tower_supply_chain_questions_v1"
JUDGE_MODEL     = "databricks:/databricks-claude-sonnet-4-6"

# ─── Evaluation records ───────────────────────────────────────────────────────
# Each record:
#   inputs.question      — what the user asks the MAS
#   expectations:
#     expected_facts     — key data points the response MUST mention (for Correctness scorer)
#     guidelines         — routing + quality requirements (for custom routing scorer)

EVAL_RECORDS = [
    # ── DC Inventory ──────────────────────────────────────────────────────────
    {
        "inputs": {"question": "Which DC has the highest excess inventory right now, and which product is it for?"},
        "expectations": {
            "expected_facts": [
                "A specific DC name or ID is identified as having the highest excess",
                "A specific product name is provided",
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
        "inputs": {"question": "Are there any products at risk of stockout at DC003?"},
        "expectations": {
            "expected_facts": [
                "DC003 or its location name is referenced in the response",
                "Safety stock levels or days-of-supply are mentioned",
                "At least one specific product is mentioned with its stock level",
            ],
            "guidelines": (
                "The agent must query dc_inventory for DC003. "
                "Response must assess stockout risk and compare current stock against safety stock thresholds."
            ),
        },
        "tags": {"target_agent": "dc_inventory", "scenario": "stockout_risk"},
    },

    # ── DC Shipment Plan ──────────────────────────────────────────────────────
    {
        "inputs": {"question": "What are the top 3 products scheduled to ship from DC001 in the next 5 days?"},
        "expectations": {
            "expected_facts": [
                "DC001 or its location name is referenced",
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
        "inputs": {"question": "Which customer has the highest demand across all DCs in the next 5 days?"},
        "expectations": {
            "expected_facts": [
                "A specific customer name is identified",
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

    # ── Incoming Supply ───────────────────────────────────────────────────────
    {
        "inputs": {"question": "What supply is arriving at DC002 in the next 3 days?"},
        "expectations": {
            "expected_facts": [
                "DC002 or its location name is referenced",
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
        "inputs": {"question": "What is the total value of supply in transit across all DCs?"},
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

    # ── Link Customer ──────────────────────────────────────────────────────────
    {
        "inputs": {"question": "Which DC is responsible for serving FreshWay Supermarket?"},
        "expectations": {
            "expected_facts": [
                "FreshWay Supermarket is referenced",
                "A specific DC or distribution center is identified by name or ID",
            ],
            "guidelines": (
                "The agent must query the link_customer Genie space. "
                "Response must identify the specific DC that serves FreshWay Supermarket."
            ),
        },
        "tags": {"target_agent": "link_customer", "scenario": "customer_dc_mapping"},
    },

    # ── Supplier Orders ────────────────────────────────────────────────────────
    {
        "inputs": {"question": "Which supplier orders are overdue or at risk of late delivery?"},
        "expectations": {
            "expected_facts": [
                "At least one supplier name is mentioned",
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

    # ── Demand Forecasting ─────────────────────────────────────────────────────
    {
        "inputs": {"question": (
            "Predict demand for Compliments Organic Whole Milk 2L for FreshWay Supermarket "
            "for March 1, 2026."
        )},
        "expectations": {
            "expected_facts": [
                "FreshWay Supermarket is referenced",
                "Compliments Organic Whole Milk 2L is referenced",
                "A numeric demand prediction (number of units) is provided",
                "Weather forecast information was retrieved and incorporated into the prediction",
            ],
            "guidelines": (
                "The agent must first call Tavily to get a weather forecast for the date and location, "
                "then call the demand_forecast UC function passing the weather result. "
                "Response must include a specific unit count and acknowledge the weather condition used."
            ),
        },
        "tags": {"target_agent": "demand_forecast", "scenario": "demand_planning"},
    },

    # ── Supplier Order Actions ──────────────────────────────────────────────────
    {
        "inputs": {"question": "Place an order for 300 units of Compliments Balance Chicken Breast 600g."},
        "expectations": {
            "expected_facts": [
                "A purchase order confirmation number (PO-XXXXXXXX) is provided",
                "Compliments Balance Chicken Breast 600g is referenced",
                "300 units is confirmed in the response",
                "A supplier name is mentioned",
            ],
            "guidelines": (
                "The agent must call the place_supplier_order UC function with the correct product name "
                "and unit amount. Response must confirm placement with a PO number and supplier name."
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
                "The agent must call expedite_supplier_order with PO-12345678. "
                "Response must confirm the expedite request was sent to the supplier."
            ),
        },
        "tags": {"target_agent": "expedite_supplier_order", "scenario": "order_action"},
    },

    # ── System Integration ──────────────────────────────────────────────────────
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
                "The agent must call get_order_from_AWR. "
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
                "The agent must call send_order_to_SAP. "
                "Response must confirm successful submission to SAP with a reference number."
            ),
        },
        "tags": {"target_agent": "send_order_to_SAP", "scenario": "system_integration"},
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
        description="Create evaluation datasets and scorers for mas-db1b25a7-dev-experiment."
    )
    parser.add_argument("--profile", default=None, help="Databricks CLI profile.")
    args = parser.parse_args()

    # ── Set up tracking URI & auth ───────────────────────────────────────────
    print("=" * 60)
    print("  Supply Chain Control Tower — Evaluation Setup")
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
            instructions="""
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
        dataset.merge_records(EVAL_RECORDS)
        print(f"  Merged {len(EVAL_RECORDS)} records. Digest: {dataset.digest}")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  Setup complete.")
    print(f"  Experiment: {EXPERIMENT_NAME}")
    print(f"  Dataset:    {DATASET_NAME}  ({len(EVAL_RECORDS)} records)")
    print(f"  Scorers:    {', '.join(registered_names)}")
    print("=" * 60)
    print()
    print("Next step — run evaluation against the MAS endpoint:")
    print("  python scripts/run_evaluation.py [--profile PROFILE]")


if __name__ == "__main__":
    main()
