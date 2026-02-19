#!/usr/bin/env bash
set -eo pipefail

###############################################################################
# deploy.sh — End-to-end deployment of the Supply Chain Control Tower
#
# Deploys the full stack into a Databricks workspace:
#   1. CSV seed data → Unity Catalog Volume
#   2. Applies column-level comments for Genie
#   3. Creates the demand-forecast UC function
#   4. Creates Genie spaces from exported JSON
#   5. Creates the MAS Supervisor Agent
#
# Usage:
#   ./deploy.sh                          # full deploy with defaults
#   ./deploy.sh --profile myprofile      # use a specific CLI profile
#   ./deploy.sh --skip-data              # skip data upload
#   ./deploy.sh --from-phase N           # resume from a specific phase
#   ./deploy.sh --help
###############################################################################

# ─── Configuration ───────────────────────────────────────────────────────────
PROFILE="${DATABRICKS_PROFILE:-}"
CATALOG="retail_consumer_goods"
SCHEMA="supply_chain_control_tower"
VOLUME_NAME="raw_data"

DEMAND_ENDPOINT="demand-forecast-endpoint"
MAS_NAME="SCC_Tower_Supply_Chain_Supervisor"

# Genie spaces — parallel arrays (bash 3 compatible)
GENIE_NAMES=(  "DC_inventory" "DC_Shipment_plan" "Incoming_Supply_to_DC" "Link_Customer" "Supplier_Orders")
GENIE_FILES=(  "genie-spaces/DC_inventory.json" "genie-spaces/DC_Shipment_plan.json" "genie-spaces/Incoming_Supply_to_DC.json" "genie-spaces/Link_Customer.json" "genie-spaces/Supplier_Orders.json")
# MAS agent key that maps to each Genie name (same order as above)
GENIE_MAS_KEYS=("dc_inventory" "dc_shipment_plan" "incoming_supply" "link_customer" "supplier_orders")

# Populated during Phase 4 (same index order)
GENIE_IDS=("" "" "" "" "")

# Temp file for passing Genie IDs between phases
GENIE_ID_FILE="$(mktemp -t deploy_genie_ids.XXXXXX)"
trap 'rm -f "$GENIE_ID_FILE"' EXIT

# ─── Flags ───────────────────────────────────────────────────────────────────
SKIP_DATA=false
FROM_PHASE=1
DRY_RUN=false

# ─── Colours ─────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

phase() { echo -e "\n${CYAN}${BOLD}════════ Phase $1: $2 ════════${NC}"; }
log()   { echo -e "${GREEN}[deploy]${NC} $*"; }
warn()  { echo -e "${YELLOW}[deploy]${NC} $*"; }
err()   { echo -e "${RED}[deploy]${NC} $*" >&2; }
skip()  { echo -e "${YELLOW}[deploy]${NC} Skipping — $*"; }

# ─── Helpers ─────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

dbcli() {
  local args=("$@")
  if [[ -n "$PROFILE" ]]; then
    args+=(--profile "$PROFILE")
  fi
  databricks "${args[@]}"
}

run_sql() {
  local stmt="$1"
  dbcli sql execute --statement "$stmt" 2>&1
}

run_sql_file() {
  local file="$1"
  local current=""
  local count=0
  local total
  total="$(grep -c ';' "$file" 2>/dev/null || echo 0)"

  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -z "${line// /}" ]] && continue
    [[ "$line" =~ ^--.*$ ]] && continue
    current+="$line "
    if [[ "$line" == *";" ]]; then
      current="${current%;}"
      current="$(echo "$current" | xargs)"
      if [[ -n "$current" ]]; then
        count=$((count + 1))
        local preview="${current:0:80}"
        log "  ($count/$total) ${preview}..."
        if ! run_sql "$current" >/dev/null 2>&1; then
          warn "  Statement $count may have failed — continuing"
        fi
      fi
      current=""
    fi
  done < "$file"
}

# ─── Parse Arguments ─────────────────────────────────────────────────────────
usage() {
  cat <<EOF
Usage: $0 [OPTIONS]

Options:
  --profile NAME      Databricks CLI profile (default: \$DATABRICKS_PROFILE or none)
  --catalog NAME      Unity Catalog name (default: $CATALOG)
  --schema  NAME      Schema name (default: $SCHEMA)
  --skip-data         Skip CSV data upload (Phase 1)
  --from-phase N      Start from phase N (1-5), skipping earlier phases
  --dry-run           Print what would happen without executing
  -h, --help          Show this help message
EOF
  exit 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)       PROFILE="$2"; shift 2 ;;
    --catalog)       CATALOG="$2"; shift 2 ;;
    --schema)        SCHEMA="$2"; shift 2 ;;
    --skip-data)     SKIP_DATA=true; shift ;;
    --from-phase)    FROM_PHASE="$2"; shift 2 ;;
    --dry-run)       DRY_RUN=true; shift ;;
    -h|--help)       usage ;;
    *) err "Unknown option: $1"; usage ;;
  esac
done

VOLUME_PATH="/Volumes/${CATALOG}/${SCHEMA}/${VOLUME_NAME}"
FULL_SCHEMA="${CATALOG}.${SCHEMA}"

# ─── Pre-flight Checks ──────────────────────────────────────────────────────
log "Supply Chain Control Tower — Deployment"
log "  Catalog:  $CATALOG"
log "  Schema:   $SCHEMA"
log "  Profile:  ${PROFILE:-<default>}"
echo ""

if ! command -v databricks &>/dev/null; then
  err "Databricks CLI not found. Install: https://docs.databricks.com/dev-tools/cli/install.html"
  exit 1
fi

if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
  err "Python 3 is required but not found."
  exit 1
fi
PYTHON="$(command -v python3 || command -v python)"

if [[ "$DRY_RUN" == true ]]; then
  warn "Dry-run mode — no changes will be made"
fi

###############################################################################
# Phase 1: Upload CSV Seed Data to Volume
###############################################################################
if [[ "$FROM_PHASE" -le 1 ]]; then
  phase 1 "Upload CSV Seed Data"

  if [[ "$SKIP_DATA" == true ]]; then
    skip "data upload (--skip-data)"
  else
    log "Ensuring volume ${VOLUME_PATH} exists..."
    if [[ "$DRY_RUN" == false ]]; then
      run_sql "CREATE VOLUME IF NOT EXISTS ${FULL_SCHEMA}.${VOLUME_NAME}" >/dev/null 2>&1 || true
    fi

    for csv in data/*.csv; do
      local_name="$(basename "$csv")"
      log "  Uploading $local_name ..."
      if [[ "$DRY_RUN" == false ]]; then
        dbcli fs cp "$csv" "${VOLUME_PATH}/${local_name}" --overwrite 2>/dev/null || \
          warn "  Failed to upload $local_name — continuing"
      fi
    done
    log "Data upload complete."
  fi
fi

###############################################################################
# Phase 2: Apply Column Comments
###############################################################################
if [[ "$FROM_PHASE" -le 2 ]]; then
  phase 2 "Apply Column Comments"
  log "Applying column-level comments for Genie curation..."
  if [[ "$DRY_RUN" == false ]]; then
    run_sql_file "scripts/apply_column_comments.sql"
  fi
  log "Column comments applied."
fi

###############################################################################
# Phase 3: Create Demand Forecast UC Function
###############################################################################
if [[ "$FROM_PHASE" -le 3 ]]; then
  phase 3 "Demand Forecast — Model + UC Function"

  log "This phase has two parts:"
  log ""
  log "  Part A: Train & deploy the ML model (requires a Databricks cluster)"
  log "    1. Upload scripts/demand_forecast_train.py as a notebook"
  log "    2. Run it on a cluster with ML Runtime"
  log "    3. Upload scripts/demand_forecast_deploy.py as a notebook"
  log "    4. Run it to create the '${DEMAND_ENDPOINT}' serving endpoint"
  log ""
  log "    Or use the helper:"
  log "      python scripts/recreate_predict_demand.py --model-only${PROFILE:+ --profile $PROFILE}"
  log ""
  log "  Part B: Creating the predict_demand UC function..."

  if [[ "$DRY_RUN" == false ]]; then
    "$PYTHON" scripts/recreate_predict_demand.py \
      --function-only \
      --catalog "$CATALOG" \
      --schema "$SCHEMA" \
      ${PROFILE:+--profile "$PROFILE"} || {
      warn "UC function creation failed — you may need to deploy the model endpoint first."
      warn "Run: python scripts/recreate_predict_demand.py${PROFILE:+ --profile $PROFILE}"
    }
  fi
fi

###############################################################################
# Phase 4: Create Genie Spaces
###############################################################################
if [[ "$FROM_PHASE" -le 4 ]]; then
  phase 4 "Create Genie Spaces"

  log "Creating ${#GENIE_NAMES[@]} Genie spaces from exported JSON..."

  WS_HOST=""
  WS_TOKEN=""
  if [[ "$DRY_RUN" == false ]]; then
    WS_HOST="$(dbcli auth env 2>/dev/null | grep DATABRICKS_HOST | head -1 | cut -d= -f2- || true)"
    WS_TOKEN="$(dbcli auth token 2>/dev/null | tr -d '[:space:]' || true)"

    if [[ -z "$WS_HOST" || -z "$WS_TOKEN" ]]; then
      warn "Could not resolve workspace host/token from CLI profile."
      warn "Genie spaces must be created manually."
      warn "JSON exports are in genie-spaces/*.json"
    fi
  fi

  for i in "${!GENIE_NAMES[@]}"; do
    name="${GENIE_NAMES[$i]}"
    json_file="${GENIE_FILES[$i]}"

    if [[ ! -f "$json_file" ]]; then
      warn "  $json_file not found — skipping"
      continue
    fi

    log "  Creating Genie space: $name"

    if [[ "$DRY_RUN" == false && -n "$WS_HOST" && -n "$WS_TOKEN" ]]; then
      # Build the create payload from exported JSON
      payload="$("$PYTHON" -c "
import json
d = json.load(open('$json_file'))
body = {
    'title': d.get('title', '$name'),
    'description': d.get('description', ''),
    'warehouse_id': d.get('warehouse_id', ''),
    'serialized_space': d.get('serialized_space', '')
}
print(json.dumps(body))
")"

      # Create via REST API
      response="$(curl -s -X POST \
        "${WS_HOST}/api/2.0/genie/spaces" \
        -H "Authorization: Bearer ${WS_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$payload" 2>/dev/null || true)"

      space_id="$(echo "$response" | "$PYTHON" -c "import json,sys; d=json.load(sys.stdin); print(d.get('space_id',''))" 2>/dev/null || true)"

      if [[ -n "$space_id" ]]; then
        log "    Created: $name → $space_id"
        GENIE_IDS[$i]="$space_id"
      else
        warn "    Could not create $name. Response: ${response:0:200}"
        # Fall back to source workspace space_id
        fallback_id="$("$PYTHON" -c "import json; d=json.load(open('$json_file')); print(d.get('space_id',''))" 2>/dev/null || true)"
        if [[ -n "$fallback_id" ]]; then
          warn "    Using source space_id as fallback: $fallback_id"
          GENIE_IDS[$i]="$fallback_id"
        fi
      fi
    else
      # Dry run or no credentials — use source IDs
      fallback_id="$("$PYTHON" -c "import json; d=json.load(open('$json_file')); print(d.get('space_id',''))" 2>/dev/null || true)"
      GENIE_IDS[$i]="${fallback_id:-}"
    fi
  done

  # Save IDs for Phase 5
  for i in "${!GENIE_NAMES[@]}"; do
    echo "${GENIE_MAS_KEYS[$i]}=${GENIE_IDS[$i]}" >> "$GENIE_ID_FILE"
  done

  log "Genie space IDs:"
  for i in "${!GENIE_NAMES[@]}"; do
    log "  ${GENIE_NAMES[$i]} → ${GENIE_IDS[$i]:-<not set>}"
  done
fi

###############################################################################
# Phase 5: Create MAS Supervisor Agent
###############################################################################
if [[ "$FROM_PHASE" -le 5 ]]; then
  phase 5 "Create MAS Supervisor Agent"

  # Load Genie IDs from file (in case phases ran separately)
  if [[ -f "$GENIE_ID_FILE" ]]; then
    while IFS='=' read -r key val; do
      case "$key" in
        dc_inventory)    DC_INV="$val" ;;
        dc_shipment_plan) DC_SHIP="$val" ;;
        incoming_supply) INC_SUP="$val" ;;
        link_customer)   LINK_CU="$val" ;;
        supplier_orders) SUPP_OR="$val" ;;
      esac
    done < "$GENIE_ID_FILE"
  fi

  # Fall back to array values
  DC_INV="${DC_INV:-${GENIE_IDS[0]:-}}"
  DC_SHIP="${DC_SHIP:-${GENIE_IDS[1]:-}}"
  INC_SUP="${INC_SUP:-${GENIE_IDS[2]:-}}"
  LINK_CU="${LINK_CU:-${GENIE_IDS[3]:-}}"
  SUPP_OR="${SUPP_OR:-${GENIE_IDS[4]:-}}"

  # If still empty, try source JSON files
  if [[ -z "$DC_INV" ]]; then
    log "Loading Genie IDs from source JSON files..."
    for i in "${!GENIE_NAMES[@]}"; do
      json_file="${GENIE_FILES[$i]}"
      mas_key="${GENIE_MAS_KEYS[$i]}"
      if [[ -f "$json_file" ]]; then
        sid="$("$PYTHON" -c "import json; d=json.load(open('$json_file')); print(d.get('space_id',''))" 2>/dev/null || true)"
        case "$mas_key" in
          dc_inventory)     DC_INV="$sid" ;;
          dc_shipment_plan) DC_SHIP="$sid" ;;
          incoming_supply)  INC_SUP="$sid" ;;
          link_customer)    LINK_CU="$sid" ;;
          supplier_orders)  SUPP_OR="$sid" ;;
        esac
      fi
    done
  fi

  log "Creating MAS: $MAS_NAME"
  log "  Genie IDs:"
  log "    dc_inventory    = ${DC_INV:-<missing>}"
  log "    dc_shipment_plan= ${DC_SHIP:-<missing>}"
  log "    incoming_supply = ${INC_SUP:-<missing>}"
  log "    link_customer   = ${LINK_CU:-<missing>}"
  log "    supplier_orders = ${SUPP_OR:-<missing>}"

  if [[ "$DRY_RUN" == false ]]; then
    WS_HOST="${WS_HOST:-$(dbcli auth env 2>/dev/null | grep DATABRICKS_HOST | head -1 | cut -d= -f2- || true)}"
    WS_TOKEN="${WS_TOKEN:-$(dbcli auth token 2>/dev/null | tr -d '[:space:]' || true)}"

    if [[ -n "$WS_HOST" && -n "$WS_TOKEN" ]]; then
      DATABRICKS_HOST="$WS_HOST" DATABRICKS_TOKEN="$WS_TOKEN" \
        "$PYTHON" -c "
import sys, os
sys.path.insert(0, '.')
import scripts.recreate_mas_supervisor as mas

mas.TARGET_WORKSPACE_URL = os.environ['DATABRICKS_HOST']
mas.DATABRICKS_TOKEN     = os.environ['DATABRICKS_TOKEN']
mas.GENIE_SPACE_IDS = {
    'dc_inventory':    '${DC_INV}',
    'dc_shipment_plan':'${DC_SHIP}',
    'incoming_supply': '${INC_SUP}',
    'link_customer':   '${LINK_CU}',
    'supplier_orders': '${SUPP_OR}',
}
mas.UC_FUNCTION_CATALOG = '${CATALOG}'
mas.UC_FUNCTION_SCHEMA  = '${SCHEMA}'
mas.recreate()
" || {
        warn "MAS creation returned an error."
        warn "You can retry manually:"
        warn "  python scripts/recreate_mas_supervisor.py"
      }
    else
      warn "Could not resolve workspace credentials. Create the MAS manually:"
      warn "  python scripts/recreate_mas_supervisor.py"
    fi
  fi
fi

###############################################################################
# Done
###############################################################################
echo ""
log "${BOLD}Deployment complete.${NC}"
echo ""
log "Summary of deployed resources:"
log "  Catalog:    $CATALOG"
log "  Schema:     $SCHEMA"
log "  UC Func:    ${FULL_SCHEMA}.predict_demand"
log "  MAS:        $MAS_NAME"
echo ""
log "Remaining manual steps (if not already done):"
log "  1. Train the demand forecast model on a cluster:"
log "       Upload scripts/demand_forecast_train.py as a notebook and run"
log "  2. Deploy the model serving endpoint:"
log "       Upload scripts/demand_forecast_deploy.py as a notebook and run"
