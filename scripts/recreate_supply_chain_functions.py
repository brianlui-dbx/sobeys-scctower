"""
recreate_supply_chain_functions.py

Creates the 8 supply chain action UC functions in Unity Catalog.
These are demo functions with mocked return values for:
  - place_supplier_order       — place a new PO with a supplier
  - expedite_supplier_order    — expedite an existing PO
  - get_order_from_AWR / send_order_to_AWR
  - get_order_from_CAO / send_order_to_CAO
  - get_order_from_SAP / send_order_to_SAP

USAGE
=====
    python scripts/recreate_supply_chain_functions.py
    python scripts/recreate_supply_chain_functions.py --profile my-workspace
    python scripts/recreate_supply_chain_functions.py --catalog my_catalog --schema my_schema
"""

import argparse
import json
import subprocess
import sys


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


def run_sql(sql: str, profile: str | None, warehouse_id: str, name: str) -> None:
    """Execute a SQL statement via the Databricks SQL Statements API."""
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
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR creating {name}: {result.stderr.strip()[:300]}")
        sys.exit(1)
    response = json.loads(result.stdout)
    state = response.get("status", {}).get("state", "UNKNOWN")
    if state != "SUCCEEDED":
        error = response.get("status", {}).get("error", {})
        print(f"  ERROR ({state}) creating {name}: {error.get('message', result.stdout[:200])}")
        sys.exit(1)
    print(f"  OK: {name}")


def build_functions(catalog: str, schema: str) -> list[tuple[str, str]]:
    """Return list of (name, ddl) for all 8 supply chain action functions."""
    p = f"{catalog}.{schema}"
    fns = []

    # 1. place_supplier_order
    fns.append(("place_supplier_order", f"""\
CREATE OR REPLACE FUNCTION {p}.place_supplier_order(
  product_name STRING COMMENT 'Name of the product to order',
  unit_amount INT COMMENT 'Number of units to order'
)
RETURNS STRUCT<order_confirmation STRING, supplier_name STRING>
LANGUAGE PYTHON
COMMENT 'Places a supplier order for a given product. Demo function with mocked return values.'
AS $$
# Logic for integrating with operational systems should be added here
import random, string
po_number = 'PO-' + ''.join(random.choices(string.digits, k=8))
suppliers = ['Sysco Foods Ltd.', 'GFS Canada', 'Collaboration Commerce Inc.', 'Performance Food Group', 'US Foods']
supplier = random.choice(suppliers)
return {{
  'order_confirmation': 'Order confirmed. PO# ' + po_number + ' placed for ' + str(unit_amount) + ' units of ' + product_name + '.',
  'supplier_name': supplier,
}}
$$"""))

    # 2. expedite_supplier_order
    fns.append(("expedite_supplier_order", f"""\
CREATE OR REPLACE FUNCTION {p}.expedite_supplier_order(
  po_number STRING COMMENT 'Existing purchase order number to expedite'
)
RETURNS STRING
LANGUAGE PYTHON
COMMENT 'Expedites an existing supplier order. Demo function with mocked return values.'
AS $$
# Logic for integrating with operational systems should be added here
return 'Expedite request sent successfully for PO# ' + po_number + '. Supplier has been notified to prioritize this order. Expected lead time reduced by 2-3 business days.'
$$"""))

    # Helper for get_order_from_* functions
    def _get_order(system: str, system_full: str, po_prefix: str,
                   supplier: str, product: str, qty: int, status: str, days: int) -> str:
        return f"""\
CREATE OR REPLACE FUNCTION {p}.get_order_from_{system}()
RETURNS STRUCT<po_number STRING, product_name STRING, quantity INT, status STRING, supplier STRING, expected_delivery DATE>
LANGUAGE PYTHON
COMMENT 'Retrieves the current order from the {system_full} system. Demo function with mocked return values.'
AS $$
# Logic for integrating with operational systems should be added here
from datetime import date, timedelta
return {{
  'po_number': '{po_prefix}-PO-20240315',
  'product_name': '{product}',
  'quantity': {qty},
  'status': '{status}',
  'supplier': '{supplier}',
  'expected_delivery': str(date.today() + timedelta(days={days})),
}}
$$"""

    # Helper for send_order_to_* functions
    def _send_order(system: str, system_full: str, ref_id: str, msg: str) -> str:
        return f"""\
CREATE OR REPLACE FUNCTION {p}.send_order_to_{system}()
RETURNS STRING
LANGUAGE PYTHON
COMMENT 'Sends a pending order to the {system_full} system. Demo function with mocked return values.'
AS $$
# Logic for integrating with operational systems should be added here
return 'Order successfully sent to {system_full}. Reference ID: {ref_id}. {msg}'
$$"""

    # 3 & 4. AWR
    fns.append(("get_order_from_AWR", _get_order(
        "AWR", "AWR (Automated Warehouse Replenishment)", "AWR",
        "Agropur Cooperative", "Compliments Organic Whole Milk 2L",
        500, "In Transit", 3,
    )))
    fns.append(("send_order_to_AWR", _send_order(
        "AWR", "AWR (Automated Warehouse Replenishment)",
        "AWR-REF-78234", "Order queued for warehouse processing.",
    )))

    # 5 & 6. CAO
    fns.append(("get_order_from_CAO", _get_order(
        "CAO", "CAO (Computer Assisted Ordering)", "CAO",
        "PepsiCo Canada", "Sensations by Compliments BBQ Chips 200g",
        1200, "Pending Confirmation", 5,
    )))
    fns.append(("send_order_to_CAO", _send_order(
        "CAO", "CAO (Computer Assisted Ordering)",
        "CAO-REF-45891", "Order submitted for automated replenishment processing.",
    )))

    # 7 & 8. SAP
    fns.append(("get_order_from_SAP", _get_order(
        "SAP", "SAP", "SAP",
        "Maple Leaf Foods Inc.", "Compliments Balance Chicken Breast 600g",
        800, "Confirmed", 2,
    )))
    fns.append(("send_order_to_SAP", _send_order(
        "SAP", "SAP",
        "4500098765", "Purchase order created and posted to SAP MM module. Vendor notification triggered.",
    )))

    return fns


def main():
    parser = argparse.ArgumentParser(
        description="Create supply chain action UC functions in a Databricks workspace."
    )
    parser.add_argument("--profile", default=None, help="Databricks CLI profile.")
    parser.add_argument("--catalog", default="retail_consumer_goods", help="Unity Catalog name.")
    parser.add_argument("--schema", default="supply_chain_control_tower", help="Schema name.")
    args = parser.parse_args()

    print("=" * 60)
    print("  Creating Supply Chain Action UC Functions")
    print(f"  Target: {args.catalog}.{args.schema}")
    if args.profile:
        print(f"  Profile: {args.profile}")
    print("=" * 60)

    warehouse_id = get_warehouse_id(args.profile)
    functions = build_functions(args.catalog, args.schema)
    for name, ddl in functions:
        print(f"\nCreating {name}...")
        run_sql(ddl, args.profile, warehouse_id, name)

    print("\n" + "=" * 60)
    print(f"  Created {len(functions)} supply chain UC functions.")
    print("=" * 60)


if __name__ == "__main__":
    main()
