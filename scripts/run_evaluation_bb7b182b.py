"""
run_evaluation_bb7b182b.py

Runs mlflow.genai.evaluate() against the MAS serving endpoint
(mas-bb7b182b-endpoint) using the 20-question supply chain evaluation
dataset and the 6 registered scorers from the experiment.

Results are logged as an MLflow run inside:
  /Users/brian.lui@databricks.com/mas-bb7b182b-dev-experiment

USAGE
=====
    python scripts/run_evaluation_bb7b182b.py
    python scripts/run_evaluation_bb7b182b.py --profile sobeysagentsdbw
"""

import argparse
import json
import os
import sys
from pathlib import Path

# ─── Configuration ────────────────────────────────────────────────────────────

EXPERIMENT_NAME = "/Users/brian.lui@databricks.com/mas-bb7b182b-dev-experiment"
EXPERIMENT_ID   = "71289383921652"
DATASET_NAME    = "retail_consumer_goods.supply_chain_control_tower.scc_tower_eval_v2"
MAS_ENDPOINT    = "mas-bb7b182b-endpoint"
JUDGE_MODEL     = "databricks:/databricks-claude-sonnet-4-6"
RESULTS_CSV     = "run_evaluation_bb7b182b_results.csv"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get_ws_credentials(profile: str | None) -> tuple[str, str]:
    import subprocess
    cmd_base = ["databricks"]
    if profile:
        cmd_base.extend(["--profile", profile])
    host = json.loads(
        subprocess.check_output(cmd_base + ["auth", "env"], stderr=subprocess.DEVNULL)
    ).get("env", {}).get("DATABRICKS_HOST", "")
    token = json.loads(
        subprocess.check_output(cmd_base + ["auth", "token"], stderr=subprocess.DEVNULL)
    ).get("access_token", "")
    return host, token


def _extract_text_from_sse(resp_text: str) -> str:
    """Parse SSE stream and extract the final assistant text."""
    answer = ""
    for line in resp_text.splitlines():
        if not line.startswith("data: "):
            continue
        raw = line[6:]
        if raw == "[DONE]":
            break
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "response.output_text.delta":
            answer += event.get("delta", "")
    return answer


def _extract_response_text(data: dict) -> str:
    """Extract the assistant's response from any MAS endpoint response format."""
    # Format 1: OpenAI-compatible chat completion
    choices = data.get("choices", [])
    if choices:
        content = choices[0].get("message", {}).get("content", "")
        if content:
            return str(content)

    # Format 2: Databricks agent output list
    output = data.get("output", [])
    if isinstance(output, list):
        for item in reversed(output):
            if item.get("type") == "message":
                content_list = item.get("content", [])
                if isinstance(content_list, list):
                    for c in content_list:
                        if c.get("type") in ("output_text", "text") and c.get("text", "").strip():
                            return c["text"]
                elif isinstance(content_list, str) and content_list.strip():
                    return content_list
    elif isinstance(output, dict):
        content = output.get("content", "")
        if content:
            return str(content)

    # Format 3: single "content" field
    if "content" in data and isinstance(data["content"], str):
        return data["content"]

    return json.dumps(data)


def _call_mas(question: str, endpoint_url: str, headers: dict) -> str:
    """Call the MAS endpoint (non-streaming) and return the assistant's text."""
    import requests

    payload = {
        "input": [{"role": "user", "content": question}],
        "stream": False,
    }
    resp = requests.post(endpoint_url, json=payload, headers=headers, timeout=300)
    resp.raise_for_status()

    content_type = resp.headers.get("content-type", "")
    if "text/event-stream" in content_type:
        return _extract_text_from_sse(resp.text)

    return _extract_response_text(resp.json())


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Run MAS evaluation with MLflow.")
    parser.add_argument("--profile", default=None, help="Databricks CLI profile.")
    args = parser.parse_args()

    print("=" * 60)
    print("  Supply Chain Control Tower — Evaluation Run (v2)")
    print(f"  Endpoint: {MAS_ENDPOINT}")
    print(f"  Dataset:  {DATASET_NAME}")
    print("=" * 60)

    host, token = _get_ws_credentials(args.profile)
    if not host or not token:
        print("ERROR: Could not retrieve Databricks credentials.")
        sys.exit(1)

    os.environ["MLFLOW_TRACKING_URI"] = "databricks"
    os.environ["DATABRICKS_HOST"]     = host
    os.environ["DATABRICKS_TOKEN"]    = token

    import mlflow
    import pandas as pd
    from mlflow.genai.judges import make_judge
    from mlflow.genai.scorers import Completeness, Correctness, RelevanceToQuery

    mlflow.set_tracking_uri("databricks")
    mlflow.set_experiment(experiment_id=EXPERIMENT_ID)

    # ── Load evaluation records ───────────────────────────────────────────────
    sys.path.insert(0, str(Path(__file__).parent))
    from create_evaluation_bb7b182b import EVAL_RECORDS  # noqa: E402

    # ── Build predict_fn ───────────────────────────────────────────────────────
    endpoint_url = f"{host.rstrip('/')}/serving-endpoints/{MAS_ENDPOINT}/invocations"
    req_headers  = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    total        = len(EVAL_RECORDS)

    call_counter = [0]

    def predict_fn(question: str) -> str:
        call_counter[0] += 1
        n = call_counter[0]
        short_q = question[:65] + ("..." if len(question) > 65 else "")
        print(f"  [{n}/{total}] {short_q}")
        try:
            text = _call_mas(question, endpoint_url, req_headers)
            print(f"         -> {len(text)} chars")
            return text
        except Exception as e:
            print(f"         -> ERROR: {e}")
            return f"[ERROR: {e}]"

    # ── Scorers ────────────────────────────────────────────────────────────────
    print("\n── Scorers ─────────────────────────────────────────────────")
    scorers = [
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
    for s in scorers:
        print(f"  {s.name}")

    # ── Run evaluation ─────────────────────────────────────────────────────────
    print(f"\n── Calling MAS ({total} questions — ~90 s each) ─────────────────")
    print("  Results will appear in the MLflow experiment UI after completion.\n")

    df = pd.DataFrame(EVAL_RECORDS)

    results = mlflow.genai.evaluate(
        data=df,
        predict_fn=predict_fn,
        scorers=scorers,
    )

    # ── Save & summarise results ───────────────────────────────────────────────
    print("\n── Results ─────────────────────────────────────────────────")

    if hasattr(results, "metrics") and results.metrics:
        for k, v in sorted(results.metrics.items()):
            print(f"  {k}: {v}")

    if hasattr(results, "tables") and results.tables:
        for table_name, tdf in results.tables.items():
            if hasattr(tdf, "to_csv"):
                out_path = RESULTS_CSV if table_name == "eval_results" else f"run_evaluation_bb7b182b_{table_name}.csv"
                tdf.to_csv(out_path, index=False)
                print(f"  Saved {table_name} -> {out_path} ({len(tdf)} rows)")

    print("\n" + "=" * 60)
    print("  Evaluation complete.")
    print(f"  Experiment: {EXPERIMENT_NAME}")
    print("=" * 60)


if __name__ == "__main__":
    main()
