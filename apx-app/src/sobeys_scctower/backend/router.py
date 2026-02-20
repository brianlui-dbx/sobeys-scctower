from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import yaml
from databricks.sdk.service.iam import User as UserOut
from fastapi import Query, Response

from .core import Dependency, create_router, execute_sql, logger
from .models import (
    ChatRequestIn,
    ChatStepOut,
    ChatTaskOut,
    CustomerLocationOut,
    DcInventoryOut,
    ExecutiveDashboardOut,
    IncomingSupplyOut,
    ShippingScheduleOut,
    StockoutRiskOut,
    StorageLocationOut,
    SupplierOrderOut,
    VersionOut,
)

router = create_router()


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _schema(config: Any) -> str:
    return f"{config.catalog}.{config.schema_name}"


def _load_metrics() -> dict[str, Any]:
    metrics_path = Path(__file__).parent / "metrics.yaml"
    with open(metrics_path) as f:
        return yaml.safe_load(f)


# ─── Version (SP auth — no user needed) ─────────────────────────────────────

@router.get("/version", response_model=VersionOut, operation_id="version")
async def version():
    return VersionOut.from_metadata()


@router.get("/current-user", response_model=UserOut, operation_id="currentUser")
def me(user_ws: Dependency.UserClient):
    return user_ws.current_user.me()


# ─── Executive Dashboard (SP auth for SQL) ──────────────────────────────────

@router.get(
    "/dashboard/executive",
    response_model=ExecutiveDashboardOut,
    operation_id="getExecutiveDashboard",
)
def get_executive_dashboard(ws: Dependency.Client, config: Dependency.Config):
    metrics = _load_metrics()
    dashboard = metrics.get("executive_dashboard", {})

    s = _schema(config)
    try:
        rows = execute_sql(ws, config, f"""
            SELECT SUM(CAST(qty AS DOUBLE) * CAST(unit_price AS DOUBLE)) as total_value
            FROM {s}.inventory_realtime_v1
        """)
        if rows and rows[0].get("total_value"):
            total_millions = round(float(rows[0]["total_value"]) / 1_000_000, 1)
            for card in dashboard.get("kpi_cards", []):
                if card.get("id") == "total_inventory_value":
                    card["value"] = total_millions
    except Exception as e:
        logger.warning(f"Could not enrich dashboard with live data: {e}")

    # Enrich inventory levels from SQL
    try:
        rows = execute_sql(ws, config, f"""
            SELECT status, SUM(CAST(qty AS DOUBLE) * CAST(unit_price AS DOUBLE)) as value
            FROM {s}.inventory_realtime_v1
            GROUP BY status
        """)
        if rows:
            locations = [{"name": str(r["status"]), "value": round(float(r["value"]) / 1_000_000, 1)} for r in rows if r.get("value")]
            total = sum(loc["value"] for loc in locations)
            if "inventory_levels" in dashboard:
                dashboard["inventory_levels"]["locations"] = locations
                dashboard["inventory_levels"]["total_value"] = round(total, 1)
    except Exception as e:
        logger.warning(f"Could not enrich inventory levels: {e}")

    fill_rate = None
    for card in dashboard.get("kpi_cards", []):
        if card.get("id") == "fill_rate":
            fill_rate = card.get("value", 95)
    if fill_rate is not None:
        for card in dashboard.get("kpi_cards", []):
            if card.get("id") == "otif":
                card["value"] = fill_rate - 3

    # Enrich supplier performance with real names from dim_supplier
    try:
        rows = execute_sql(ws, config, f"""
            SELECT name FROM {s}.dim_supplier ORDER BY name LIMIT 10
        """)
        if rows:
            import hashlib
            fake_metrics = [
                (98, 95, "7 days", "Low"),
                (92, 88, "10 days", "Medium"),
                (95, 92, "8 days", "Low"),
                (85, 80, "14 days", "High"),
                (90, 85, "12 days", "Medium"),
                (97, 93, "6 days", "Low"),
                (88, 82, "11 days", "Medium"),
                (94, 90, "9 days", "Low"),
                (82, 78, "15 days", "High"),
                (91, 87, "10 days", "Medium"),
            ]
            suppliers = []
            for i, r in enumerate(rows):
                name = str(r.get("name", ""))
                idx = int(hashlib.md5(name.encode()).hexdigest(), 16) % len(fake_metrics)
                otd, qs, lt, rs = fake_metrics[idx]
                suppliers.append({
                    "name": name,
                    "on_time_delivery": otd,
                    "quality_score": qs,
                    "lead_time": lt,
                    "risk_score": rs,
                })
            if "supplier_performance" in dashboard:
                dashboard["supplier_performance"]["suppliers"] = suppliers
    except Exception as e:
        logger.warning(f"Could not enrich supplier performance: {e}")

    return ExecutiveDashboardOut(**dashboard)


# ─── DC Inventory (SP auth) ──────────────────────────────────────────────────

@router.get(
    "/dc-inventory",
    response_model=list[DcInventoryOut],
    operation_id="listDcInventory",
)
def list_dc_inventory(
    ws: Dependency.Client,
    config: Dependency.Config,
    dc_id: Optional[str] = Query(None),
):
    s = _schema(config)
    where = f"AND i.dc_id = '{dc_id}'" if dc_id else ""
    rows = execute_sql(ws, config, f"""
        SELECT i.product_id, p.name as product_name,
               i.dc_id, s.location_name as dc_name,
               i.allocated_qty, i.safety_stock, i.excess_qty, i.total_qty,
               CAST(i.snapshot_date AS STRING) as snapshot_date
        FROM {s}.fact_dc_inventory i
        JOIN {s}.dim_product p ON i.product_id = p.product_id
        JOIN {s}.dim_storage_location s ON i.dc_id = s.location_id
        WHERE i.snapshot_date = (SELECT MAX(snapshot_date) FROM {s}.fact_dc_inventory)
        {where}
        ORDER BY i.total_qty DESC
        LIMIT 10
    """)
    return [DcInventoryOut(
        product_id=str(r.get("product_id", "")),
        product_name=str(r.get("product_name", "")),
        dc_id=str(r.get("dc_id", "")),
        dc_name=str(r.get("dc_name", "")),
        allocated_qty=int(r.get("allocated_qty", 0)),
        safety_stock=int(r.get("safety_stock", 0)),
        excess_qty=int(r.get("excess_qty", 0)),
        total_qty=int(r.get("total_qty", 0)),
        snapshot_date=str(r.get("snapshot_date", "")),
    ) for r in rows]


# ─── Incoming Supply (SP auth) ───────────────────────────────────────────────

@router.get(
    "/incoming-supply",
    response_model=list[IncomingSupplyOut],
    operation_id="listIncomingSupply",
)
def list_incoming_supply(ws: Dependency.Client, config: Dependency.Config):
    s = _schema(config)
    rows = execute_sql(ws, config, f"""
        SELECT i.shipment_id,
               src.location_name as source_location,
               p.name as product_name,
               dst.location_name as destination_dc,
               i.qty, i.expected_arrival_days,
               CAST(i.expected_arrival_date AS STRING) as expected_arrival_date
        FROM {s}.fact_incoming_supply i
        JOIN {s}.dim_product p ON i.product_id = p.product_id
        JOIN {s}.dim_storage_location src ON i.source_location_id = src.location_id
        JOIN {s}.dim_storage_location dst ON i.destination_dc_id = dst.location_id
        WHERE i.snapshot_date = (SELECT MAX(snapshot_date) FROM {s}.fact_incoming_supply)
        ORDER BY i.expected_arrival_days ASC
        LIMIT 10
    """)
    return [IncomingSupplyOut(
        shipment_id=str(r.get("shipment_id", "")),
        source_location=str(r.get("source_location", "")),
        product_name=str(r.get("product_name", "")),
        destination_dc=str(r.get("destination_dc", "")),
        qty=int(r.get("qty", 0)),
        expected_arrival_days=int(r.get("expected_arrival_days", 0)),
        expected_arrival_date=str(r.get("expected_arrival_date", "")),
    ) for r in rows]


# ─── Shipping Schedule (SP auth) ─────────────────────────────────────────────

@router.get(
    "/shipping-schedule",
    response_model=list[ShippingScheduleOut],
    operation_id="listShippingSchedule",
)
def list_shipping_schedule(ws: Dependency.Client, config: Dependency.Config):
    s = _schema(config)
    rows = execute_sql(ws, config, f"""
        SELECT ss.schedule_id, p.name as product_name,
               sl.location_name as dc_name, c.name as customer_name,
               CAST(ss.schedule_date AS STRING) as schedule_date, ss.qty
        FROM {s}.fact_shipping_schedule ss
        JOIN {s}.dim_product p ON ss.product_id = p.product_id
        JOIN {s}.dim_storage_location sl ON ss.location_id = sl.location_id
        JOIN {s}.dim_customer c ON ss.customer_id = c.customer_id
        WHERE ss.snapshot_date = (SELECT MAX(snapshot_date) FROM {s}.fact_shipping_schedule)
        ORDER BY ss.schedule_date ASC
        LIMIT 10
    """)
    return [ShippingScheduleOut(
        schedule_id=str(r.get("schedule_id", "")),
        product_name=str(r.get("product_name", "")),
        dc_name=str(r.get("dc_name", "")),
        customer_name=str(r.get("customer_name", "")),
        schedule_date=str(r.get("schedule_date", "")),
        qty=int(r.get("qty", 0)),
    ) for r in rows]


# ─── Supplier Orders (SP auth) ───────────────────────────────────────────────

@router.get(
    "/supplier-orders",
    response_model=list[SupplierOrderOut],
    operation_id="listSupplierOrders",
)
def list_supplier_orders(ws: Dependency.Client, config: Dependency.Config):
    s = _schema(config)
    rows = execute_sql(ws, config, f"""
        SELECT so.order_id, sup.name as supplier_name,
               p.name as product_name, so.qty,
               so.expected_arrival_days,
               CAST(so.expected_arrival_date AS STRING) as expected_arrival_date
        FROM {s}.fact_supplier_orders so
        JOIN {s}.dim_supplier sup ON so.supplier_id = sup.supplier_id
        JOIN {s}.dim_product p ON so.product_id = p.product_id
        WHERE so.snapshot_date = (SELECT MAX(snapshot_date) FROM {s}.fact_supplier_orders)
        ORDER BY so.expected_arrival_days ASC
        LIMIT 10
    """)
    return [SupplierOrderOut(
        order_id=str(r.get("order_id", "")),
        supplier_name=str(r.get("supplier_name", "")),
        product_name=str(r.get("product_name", "")),
        qty=int(r.get("qty", 0)),
        expected_arrival_days=int(r.get("expected_arrival_days", 0)),
        expected_arrival_date=str(r.get("expected_arrival_date", "")),
    ) for r in rows]


# ─── Stockout Risk (SP auth) ─────────────────────────────────────────────────

@router.get(
    "/stockout-risk",
    response_model=list[StockoutRiskOut],
    operation_id="listStockoutRisk",
)
def list_stockout_risk(ws: Dependency.Client, config: Dependency.Config):
    s = _schema(config)
    rows = execute_sql(ws, config, f"""
        WITH daily_demand AS (
            SELECT product_id, location_id, AVG(CAST(qty AS DOUBLE)) as avg_daily
            FROM {s}.fact_shipping_schedule
            GROUP BY product_id, location_id
        )
        SELECT p.name as product_name, sl.location_name as dc_name,
               i.total_qty as current_qty, i.safety_stock,
               CASE WHEN COALESCE(d.avg_daily, 0) > 0
                    THEN ROUND(CAST(i.total_qty AS DOUBLE) / d.avg_daily, 1)
                    ELSE 999 END as days_of_supply,
               CASE
                    WHEN COALESCE(d.avg_daily, 0) > 0 AND CAST(i.total_qty AS DOUBLE) / d.avg_daily < 3 THEN 'Critical'
                    WHEN COALESCE(d.avg_daily, 0) > 0 AND CAST(i.total_qty AS DOUBLE) / d.avg_daily < 7 THEN 'High'
                    WHEN COALESCE(d.avg_daily, 0) > 0 AND CAST(i.total_qty AS DOUBLE) / d.avg_daily < 14 THEN 'Medium'
                    ELSE 'Low'
               END as risk_level
        FROM {s}.fact_dc_inventory i
        JOIN {s}.dim_product p ON i.product_id = p.product_id
        JOIN {s}.dim_storage_location sl ON i.dc_id = sl.location_id
        LEFT JOIN daily_demand d ON i.product_id = d.product_id AND i.dc_id = d.location_id
        WHERE i.snapshot_date = (SELECT MAX(snapshot_date) FROM {s}.fact_dc_inventory)
        ORDER BY days_of_supply ASC
        LIMIT 10
    """)
    return [StockoutRiskOut(
        product_name=str(r.get("product_name", "")),
        dc_name=str(r.get("dc_name", "")),
        current_qty=int(r.get("current_qty", 0)),
        safety_stock=int(r.get("safety_stock", 0)),
        days_of_supply=float(r.get("days_of_supply", 999)),
        risk_level=str(r.get("risk_level", "Low")),
    ) for r in rows]


# ─── Storage Locations (SP auth) ─────────────────────────────────────────────

@router.get(
    "/storage-locations",
    response_model=list[StorageLocationOut],
    operation_id="listStorageLocations",
)
def list_storage_locations(ws: Dependency.Client, config: Dependency.Config):
    s = _schema(config)
    rows = execute_sql(ws, config, f"""
        SELECT location_id, location_name, type, location, latitude, longitude
        FROM {s}.dim_storage_location
    """)
    return [StorageLocationOut(
        location_id=str(r.get("location_id", "")),
        location_name=str(r.get("location_name", "")),
        type=str(r.get("type", "")),
        location=str(r.get("location", "")),
        latitude=float(r.get("latitude", 0)),
        longitude=float(r.get("longitude", 0)),
    ) for r in rows]


# ─── Customer Locations (SP auth) ────────────────────────────────────────────

@router.get(
    "/customer-locations",
    response_model=list[CustomerLocationOut],
    operation_id="listCustomerLocations",
)
def list_customer_locations(ws: Dependency.Client, config: Dependency.Config):
    s = _schema(config)
    rows = execute_sql(ws, config, f"""
        SELECT customer_id, name, location, latitude, longitude
        FROM {s}.dim_customer
    """)
    return [CustomerLocationOut(
        customer_id=str(r.get("customer_id", "")),
        name=str(r.get("name", "")),
        location=str(r.get("location", "")),
        latitude=float(r.get("latitude", 0)),
        longitude=float(r.get("longitude", 0)),
    ) for r in rows]


# ─── Chat: Streaming SSE ─────────────────────────────────────────────────────

import re as _re

_AGENT_LABEL_RE = _re.compile(r"^\s*<name>.+</name>\s*$", _re.DOTALL)


def _prettify_agent_name(raw: str) -> str:
    """Turn 'agent-dc-inventory' into 'DC Inventory'."""
    name = raw.removeprefix("agent-").removeprefix("mcp-")
    return name.replace("-", " ").replace("_", " ").title()


def _extract_message_text(item: dict) -> str:
    """Extract text from a message output item."""
    content_list = item.get("content", [])
    if isinstance(content_list, list):
        for c in content_list:
            if c.get("type") == "output_text" and c.get("text", "").strip():
                return c["text"]
    return ""


def _sse(event: str, data: Any) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


import time as _time
import threading as _threading

_chat_tasks: dict[str, dict[str, Any]] = {}


def _cleanup_old_tasks() -> None:
    now = _time.time()
    stale = [k for k, v in _chat_tasks.items() if now - v.get("created_at", 0) > 300]
    for k in stale:
        _chat_tasks.pop(k, None)


def _process_sse_event(event_json: dict, task: dict, phase: str, text_buffer: str, answer_buffer: str) -> tuple[str, str, str]:
    """Process a single SSE event and update task state in-place.

    Returns updated (phase, text_buffer, answer_buffer).
    """
    event_type = event_json.get("type", "")

    if event_type == "response.output_text.delta":
        delta = event_json.get("delta", "")
        if phase == "streaming":
            answer_buffer += delta
            task["response"] = answer_buffer
        else:
            text_buffer += delta

    elif event_type == "response.output_item.done":
        item = event_json.get("item", {})
        item_type = item.get("type", "")

        if item_type == "function_call":
            if text_buffer.strip():
                task["steps"].append({
                    "type": "thinking",
                    "title": "Reasoning",
                    "content": text_buffer.strip(),
                })
                text_buffer = ""

            if phase == "streaming" and answer_buffer.strip():
                task["steps"].append({
                    "type": "thinking",
                    "title": "Reasoning",
                    "content": answer_buffer.strip(),
                })
                answer_buffer = ""
                task["response"] = ""

            agent_name = item.get("name", "unknown")
            try:
                args = json.loads(item.get("arguments", "{}"))
                query = args.get("genie_query", args.get("query", json.dumps(args)))
            except (json.JSONDecodeError, TypeError):
                query = item.get("arguments", "")

            task["steps"].append({
                "type": "tool_call",
                "title": _prettify_agent_name(agent_name),
                "content": query,
            })
            phase = "waiting"

        elif item_type == "message":
            text = _extract_message_text(item)
            if text and _AGENT_LABEL_RE.match(text):
                if "SCC_Tower" in text or "Supervisor" in text:
                    phase = "streaming"
                    answer_buffer = ""

    return phase, text_buffer, answer_buffer


def _run_mas_task(
    task_id: str, messages: list[dict], host: str, model: str, auth_headers: dict,
) -> None:
    """Background thread: stream from MAS using requests for real-time updates."""
    import requests

    task = _chat_tasks[task_id]
    task["status"] = "running"

    url = f"{host}/serving-endpoints/{model}/invocations"
    payload = {"input": messages, "stream": True}

    phase = "init"
    text_buffer = ""
    answer_buffer = ""

    import sys
    t0 = _time.time()

    def _log(msg: str) -> None:
        print(f"[TIMING +{_time.time()-t0:.1f}s] {msg}", flush=True, file=sys.stderr)

    try:
        _log(f"Starting POST to {url[:60]}...")
        resp = requests.post(
            url, json=payload,
            headers={**auth_headers, "Content-Type": "application/json"},
            timeout=300,
            stream=True,
        )
        _log(f"HTTP {resp.status_code}")
        if resp.status_code != 200:
            task["status"] = "error"
            task["response"] = f"MAS returned {resp.status_code}: {resp.text[:200]}"
            return

        line_count = 0
        for line in resp.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            raw = line[6:]
            if raw == "[DONE]":
                _log(f"[DONE] lines={line_count} steps={len(task['steps'])}")
                break

            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                continue

            line_count += 1
            event_type = event.get("type", "")
            if event_type == "response.output_item.done":
                item = event.get("item", {})
                it = item.get("type", "")
                name = item.get("name", "")
                _log(f"item_done({it} {name}) steps={len(task['steps'])}")

            phase, text_buffer, answer_buffer = _process_sse_event(
                event, task, phase, text_buffer, answer_buffer,
            )

        # Handle no-tool-call case (direct answer without sub-agents)
        if text_buffer.strip() and phase == "init":
            task["response"] = text_buffer

        task["status"] = "done"
        _log(f"COMPLETE {len(task.get('response', ''))} chars, {len(task['steps'])} steps")

    except Exception as e:
        logger.error(f"Chat task {task_id} error: {e}")
        task["status"] = "error"
        task["response"] = str(e)


@router.post("/chat/start", response_model=ChatTaskOut, operation_id="startChat")
def start_chat(
    body: ChatRequestIn,
    ws: Dependency.Client,
    config: Dependency.Config,
):
    import uuid
    task_id = str(uuid.uuid4())
    auth_headers = ws.config.authenticate()
    messages = [{"role": m.role, "content": m.content} for m in body.messages]

    _cleanup_old_tasks()
    _chat_tasks[task_id] = {
        "status": "pending", "response": "", "steps": [],
        "created_at": _time.time(),
    }

    thread = _threading.Thread(
        target=_run_mas_task,
        args=(task_id, messages, str(ws.config.host), config.chat_model, auth_headers),
        daemon=True,
    )
    thread.start()

    return ChatTaskOut(task_id=task_id, status="pending")


@router.get("/chat/poll/{task_id}", response_model=ChatTaskOut, operation_id="pollChat")
async def poll_chat(task_id: str):
    """Async handler — runs directly in the event loop, never blocked by thread pool."""
    task = _chat_tasks.get(task_id)
    if not task:
        return ChatTaskOut(task_id=task_id, status="error", response="Task not found")

    steps = [ChatStepOut(**s) for s in task.get("steps", [])]
    return ChatTaskOut(task_id=task_id, status=task["status"], response=task.get("response", ""), steps=steps)
