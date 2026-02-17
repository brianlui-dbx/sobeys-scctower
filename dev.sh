#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$APP_DIR/.venv"
REQUIREMENTS="$APP_DIR/backend/requirements.txt"
ENV_FILE="$APP_DIR/.env"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[dev]${NC} $*"; }
warn() { echo -e "${YELLOW}[dev]${NC} $*"; }
err()  { echo -e "${RED}[dev]${NC} $*" >&2; }

# --- Check Python ---
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        PYTHON="$cmd"
        break
    fi
done

if [[ -z "$PYTHON" ]]; then
    err "Python 3 is required but not found. Please install Python 3.9+."
    exit 1
fi

PY_VERSION=$("$PYTHON" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
log "Using $PYTHON ($PY_VERSION)"

# --- Create / activate virtual environment ---
if [[ ! -d "$VENV_DIR" ]]; then
    log "Creating virtual environment in $VENV_DIR ..."
    "$PYTHON" -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
log "Virtual environment activated"

# --- Install / update dependencies ---
log "Installing dependencies from $REQUIREMENTS ..."
pip install --quiet --upgrade pip
pip install --quiet -r "$REQUIREMENTS"

# --- Check .env file ---
if [[ ! -f "$ENV_FILE" ]]; then
    warn ".env file not found. Copying from backend/.env.example ..."
    cp "$APP_DIR/backend/.env.example" "$ENV_FILE"
    warn "Please edit $ENV_FILE with your Databricks credentials, then re-run this script."
    exit 1
fi

# --- Validate required env vars ---
set -a
source "$ENV_FILE"
set +a

MISSING=()
for VAR in DATABRICKS_HOST DATABRICKS_TOKEN DATABRICKS_HTTP_PATH DATABRICKS_CATALOG DATABRICKS_SCHEMA; do
    val="${!VAR:-}"
    if [[ -z "$val" || "$val" == your_* ]]; then
        MISSING+=("$VAR")
    fi
done

if [[ ${#MISSING[@]} -gt 0 ]]; then
    warn "The following required env vars are missing or still have placeholder values in $ENV_FILE:"
    for v in "${MISSING[@]}"; do
        warn "  - $v"
    done
    warn "The app will start but Databricks-dependent features will fail."
fi

# --- Start the server ---
log "Starting Supply Chain Control Tower on http://$HOST:$PORT ..."
log "  API docs: http://localhost:$PORT/docs"
log "  Frontend: http://localhost:$PORT/"
log "  Press Ctrl+C to stop"
echo ""

exec uvicorn backend.main:app \
    --host "$HOST" \
    --port "$PORT" \
    --reload \
    --reload-dir "$APP_DIR/backend" \
    --timeout-keep-alive 75 \
    --app-dir "$APP_DIR"
