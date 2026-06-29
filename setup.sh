#!/bin/bash
# ================================================================
#  SmartCity Analyzer — setup.sh
#  One-time environment setup
#  Works on: Linux · macOS · Git Bash (Windows)
# ================================================================

set -e

# ── Colors ───────────────────────────────────────────────────────
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { echo -e "  ${GREEN}✓${NC} $1"; }
fail() { echo -e "  ${RED}✗${NC} $1"; }
warn() { echo -e "  ${YELLOW}!${NC} $1"; }
step() { echo -e "\n[${1}/${TOTAL}] $2"; }

TOTAL=7

echo ""
echo "================================================================"
echo "  SmartCity Analyzer — Environment Setup"
echo "================================================================"

# ── 1. Docker ────────────────────────────────────────────────────
step 1 "Checking Docker..."
if ! command -v docker &>/dev/null; then
    fail "Docker not found. Install Docker Desktop:"
    echo "      https://docs.docker.com/get-docker/"
    exit 1
fi
DOCKER_VER=$(docker --version)
ok "$DOCKER_VER"

# ── 2. Docker Compose ────────────────────────────────────────────
step 2 "Checking Docker Compose..."
if ! docker compose version &>/dev/null; then
    fail "Docker Compose v2 not found. Update Docker Desktop."
    exit 1
fi
COMPOSE_VER=$(docker compose version)
ok "$COMPOSE_VER"

# ── 3. Docker running ────────────────────────────────────────────
step 3 "Checking Docker daemon..."
if ! docker info &>/dev/null; then
    fail "Docker daemon is not running. Start Docker Desktop first."
    exit 1
fi
ok "Docker daemon is running"

# ── 4. Required ports ────────────────────────────────────────────
step 4 "Checking required ports..."
PORTS=(2181 9092 8080 5432 5433 8085)
LABELS=("Zookeeper" "Kafka" "Kafka UI" "PostgreSQL (Bronze)" "PostgreSQL (Airflow)" "Airflow UI")
PORT_OK=true

for i in "${!PORTS[@]}"; do
    PORT="${PORTS[$i]}"
    LABEL="${LABELS[$i]}"
    # Use ss if available, fall back to netstat
    if command -v ss &>/dev/null; then
        IN_USE=$(ss -tlnp 2>/dev/null | grep ":${PORT} " || true)
    elif command -v netstat &>/dev/null; then
        IN_USE=$(netstat -tlnp 2>/dev/null | grep ":${PORT} " || true)
    else
        IN_USE=""
    fi

    if [ -n "$IN_USE" ]; then
        warn "Port ${PORT} (${LABEL}) is already in use"
        PORT_OK=false
    else
        ok "Port ${PORT} (${LABEL}) is free"
    fi
done

if [ "$PORT_OK" = false ]; then
    warn "Some ports are in use — free them or edit docker-compose files before running"
fi

# ── 5. Create directories ────────────────────────────────────────
step 5 "Creating required directories..."

mkdir -p Phase1_Scraping/output_all
ok "Phase1_Scraping/output_all/"

mkdir -p Phase2_Transform/gold_output
ok "Phase2_Transform/gold_output/"

mkdir -p SmartCity-Airflow/logs
mkdir -p SmartCity-Airflow/plugins
mkdir -p SmartCity-Airflow/config
ok "SmartCity-Airflow/logs|plugins|config/"

# ── 6. Airflow .env ──────────────────────────────────────────────
step 6 "Setting up Airflow environment file..."

ENV_FILE="SmartCity-Airflow/.env"
ENV_EXAMPLE="SmartCity-Airflow/.env.example"

if [ -f "$ENV_FILE" ]; then
    ok ".env already exists — skipping (edit it manually if needed)"
else
    if [ -f "$ENV_EXAMPLE" ]; then
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        ok ".env created from .env.example"
        echo ""
        warn "IMPORTANT: Edit SmartCity-Airflow/.env before running Airflow:"
        echo "      → Set SMARTCITY_PROJECT_PATH to this folder's absolute path"
        echo "      → Set SMARTCITY_HOST_PATH to the same path"
        echo "      → Set SQLSERVER_PASSWORD to your SQL Server password"
    else
        warn ".env.example not found — create SmartCity-Airflow/.env manually"
    fi
fi

# ── 7. Pull Docker images ────────────────────────────────────────
step 7 "Pulling Docker images (may take a few minutes)..."

IMAGES=(
    "confluentinc/cp-zookeeper:7.6.0"
    "confluentinc/cp-kafka:7.6.0"
    "provectuslabs/kafka-ui:latest"
    "postgres:16-alpine"
    "postgres:15-alpine"
    "jupyter/pyspark-notebook:spark-3.5.0"
)

for IMG in "${IMAGES[@]}"; do
    echo "  Pulling $IMG ..."
    docker pull "$IMG" -q
    ok "$IMG"
done

# ── Done ─────────────────────────────────────────────────────────
echo ""
echo "================================================================"
echo -e "  ${GREEN}Setup complete!${NC}"
echo ""
echo "  Next steps:"
echo "    1. Edit SmartCity-Airflow/.env  (set your project path)"
echo "    2. bash run.sh airflow           (start orchestrator)"
echo "    OR"
echo "    2. bash run.sh phase1            (run Phase 1 only)"
echo ""
echo "  For help:"
echo "    bash run.sh help"
echo "================================================================"
echo ""
