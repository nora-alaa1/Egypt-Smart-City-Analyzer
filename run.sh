#!/bin/bash
# ================================================================
#  SmartCity Analyzer — run.sh
#  Start / Stop / Status for all phases
#  Works on: Linux · macOS · Git Bash (Windows)
#
#  Usage: bash run.sh <command>
#
#  Commands:
#    airflow          Start Airflow (orchestrates everything)
#    phase1           Start Phase 1 only (Kafka + PostgreSQL)
#    phase2           Run Phase 2 only (PySpark transform)
#    phase3           Run Phase 3 only (load to SQL Server)
#    stop             Stop all running services
#    status           Show all running containers
#    logs [service]   Follow logs (all or specific service)
#    clean            Remove all containers and volumes
#    help             Show this help message
# ================================================================

# ── Paths ────────────────────────────────────────────────────────
PHASE1_COMPOSE="Phase1_Scraping/docker-compose.master.yml"
AIRFLOW_COMPOSE="SmartCity-Airflow/docker-compose.yml"

# ── Colors ───────────────────────────────────────────────────────
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

ok()     { echo -e "  ${GREEN}✓${NC} $1"; }
fail()   { echo -e "  ${RED}✗${NC} $1"; }
warn()   { echo -e "  ${YELLOW}!${NC} $1"; }
info()   { echo -e "  ${CYAN}→${NC} $1"; }
header() { echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; echo -e "  $1"; echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; }

# ── Helpers ──────────────────────────────────────────────────────
check_compose_file() {
    if [ ! -f "$1" ]; then
        fail "Compose file not found: $1"
        echo "  Make sure you're running this from the SmartCityAnalyzer-main folder."
        exit 1
    fi
}

check_env_file() {
    if [ ! -f "SmartCity-Airflow/.env" ]; then
        fail "SmartCity-Airflow/.env not found"
        warn "Run 'bash setup.sh' first, then edit the .env file."
        exit 1
    fi
}

# ================================================================
#  COMMANDS
# ================================================================

CMD="${1:-help}"

case "$CMD" in

# ── airflow ──────────────────────────────────────────────────────
airflow)
    header "🚀 Starting Airflow Orchestrator"
    check_compose_file "$AIRFLOW_COMPOSE"
    check_env_file

    # Check if init is needed (first time)
    if ! docker ps -a --format '{{.Names}}' | grep -q "airflow_postgres"; then
        echo ""
        info "First run detected — initializing Airflow (this takes ~2 minutes)..."
        docker compose -f "$AIRFLOW_COMPOSE" up airflow-init
    fi

    docker compose -f "$AIRFLOW_COMPOSE" up -d

    echo ""
    ok "Airflow is starting..."
    echo ""
    echo "  ┌─────────────────────────────────────────┐"
    echo "  │  Airflow UI    → http://localhost:8085  │"
    echo "  │  Login         → admin / admin          │"
    echo "  │                                         │"
    echo "  │  DAG           → smartcity_full_pipeline│"
    echo "  │  Schedule      → every 6 months         │"
    echo "  │                                         │"
    echo "  │  To trigger:   click 'Trigger DAG'      │"
    echo "  └─────────────────────────────────────────┘"
    echo ""
    info "Waiting ~30 seconds for Airflow to be ready..."
    sleep 30
    info "Follow logs: bash run.sh logs airflow-webserver"
    ;;

# ── phase1 ───────────────────────────────────────────────────────
phase1)
    header "🚀 Starting Phase 1 — Kafka + PostgreSQL"
    check_compose_file "$PHASE1_COMPOSE"

    docker compose -f "$PHASE1_COMPOSE" up --build -d

    echo ""
    ok "Phase 1 services started"
    echo ""
    echo "  ┌──────────────────────────────────────────────┐"
    echo "  │  Kafka UI     → http://localhost:8080        │"
    echo "  │  PostgreSQL   → localhost:5432               │"
    echo "  │                  smartcity / smartcity123     │"
    echo "  └──────────────────────────────────────────────┘"
    echo ""
    info "Follow logs: bash run.sh logs"
    info "Stop:        bash run.sh stop"
    ;;

# ── phase2 ───────────────────────────────────────────────────────
phase2)
    header "⚡ Running Phase 2 — PySpark Transformation"

    if [ ! -f "Phase2_Transform/run_phase2.py" ]; then
        fail "Phase2_Transform/run_phase2.py not found"
        exit 1
    fi

    echo ""
    info "Running PySpark notebook..."
    echo ""

    docker run --rm \
        --network smartcity_default \
        -e PG_HOST=postgres \
        -e PG_PORT=5432 \
        -e PG_DB=smartcity \
        -e PG_USER=smartcity \
        -e PG_PASSWORD=smartcity123 \
        -v "$(pwd)/Phase2_Transform:/home/jovyan/work" \
        -w /home/jovyan/work \
        jupyter/pyspark-notebook:spark-3.5.0 \
        jupyter nbconvert --to notebook --execute \
            --ExecutePreprocessor.timeout=3600 \
            --output SmartCity_Phase1_Fixed_executed.ipynb \
            SmartCity_Phase1_Fixed.ipynb

    echo ""
    ok "Phase 2 complete — Gold files saved to Phase2_Transform/gold_output/"
    ;;

# ── phase3 ───────────────────────────────────────────────────────
phase3)
    header "🏗️ Running Phase 3 — Load to SQL Server"

    if [ ! -f "Phase3_Dwh/run_load.py" ]; then
        fail "Phase3_Dwh/run_load.py not found"
        exit 1
    fi

    echo ""
    warn "Make sure SQL Server is running and accessible."
    warn "Edit Phase3_Dwh/load_to_sqlserver.ipynb (Cell 2) with your connection settings."
    echo ""
    read -p "  Continue? (y/n): " CONFIRM
    if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
        echo "  Cancelled."
        exit 0
    fi

    docker run --rm \
        --add-host=host.docker.internal:host-gateway \
        -v "$(pwd)/Phase3_Dwh:/home/jovyan/work" \
        -v "$(pwd)/Phase2_Transform/gold_output:/home/jovyan/gold_output" \
        -w /home/jovyan/work \
        jupyter/datascience-notebook:latest \
        bash -c "pip install --quiet sqlalchemy pymssql openpyxl && \
                 jupyter nbconvert --to notebook --execute \
                 --ExecutePreprocessor.timeout=1800 \
                 --output load_to_sqlserver_executed.ipynb \
                 load_to_sqlserver.ipynb"

    echo ""
    ok "Phase 3 complete — Data loaded to SQL Server"
    echo ""
    info "Apply constraints: run dwh/02_create_tables.sql, 03_constraints.sql, 04_indexes.sql in SSMS"
    ;;

# ── stop ─────────────────────────────────────────────────────────
stop)
    header "⏹️  Stopping All Services"

    echo ""
    info "Stopping Phase 1 (Kafka + PostgreSQL)..."
    if [ -f "$PHASE1_COMPOSE" ]; then
        docker compose -f "$PHASE1_COMPOSE" down 2>/dev/null || true
        ok "Phase 1 stopped"
    fi

    info "Stopping Airflow..."
    if [ -f "$AIRFLOW_COMPOSE" ]; then
        docker compose -f "$AIRFLOW_COMPOSE" down 2>/dev/null || true
        ok "Airflow stopped"
    fi

    echo ""
    ok "All services stopped"
    ;;

# ── status ───────────────────────────────────────────────────────
status)
    header "📊 Running Containers"
    echo ""
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | \
        grep -E "(NAME|smartcity|airflow|kafka|zookeeper|postgres|bronze)" || \
        echo "  No SmartCity containers running."
    echo ""
    ;;

# ── logs ─────────────────────────────────────────────────────────
logs)
    SERVICE="$2"

    if [ -n "$SERVICE" ]; then
        # Try to find the service in Phase 1 or Airflow
        if docker compose -f "$PHASE1_COMPOSE" ps --services 2>/dev/null | grep -q "^${SERVICE}$"; then
            docker compose -f "$PHASE1_COMPOSE" logs -f "$SERVICE"
        elif docker compose -f "$AIRFLOW_COMPOSE" ps --services 2>/dev/null | grep -q "^${SERVICE}$"; then
            docker compose -f "$AIRFLOW_COMPOSE" logs -f "$SERVICE"
        else
            # Try by container name directly
            docker logs -f "$SERVICE" 2>/dev/null || {
                fail "Service not found: $SERVICE"
                echo ""
                echo "  Available Phase 1 services:"
                docker compose -f "$PHASE1_COMPOSE" ps --services 2>/dev/null | sed 's/^/    /'
                echo ""
                echo "  Available Airflow services:"
                docker compose -f "$AIRFLOW_COMPOSE" ps --services 2>/dev/null | sed 's/^/    /'
            }
        fi
    else
        echo ""
        info "Showing all Phase 1 logs (Ctrl+C to stop)..."
        docker compose -f "$PHASE1_COMPOSE" logs -f 2>/dev/null || \
            fail "Phase 1 is not running"
    fi
    ;;

# ── clean ────────────────────────────────────────────────────────
clean)
    header "🗑️  Clean — Remove All Data"
    echo ""
    warn "This will delete ALL containers, networks, and volumes."
    warn "PostgreSQL data, Kafka data, and Airflow metadata will be lost."
    echo ""
    read -p "  Type 'yes' to confirm: " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        echo "  Cancelled."
        exit 0
    fi

    echo ""
    info "Removing Phase 1..."
    docker compose -f "$PHASE1_COMPOSE" down -v --remove-orphans 2>/dev/null || true

    info "Removing Airflow..."
    docker compose -f "$AIRFLOW_COMPOSE" down -v --remove-orphans 2>/dev/null || true

    info "Removing any remaining SmartCity containers..."
    docker ps -a --filter "name=smartcity" -q | xargs -r docker rm -f 2>/dev/null || true
    docker ps -a --filter "name=airflow" -q | xargs -r docker rm -f 2>/dev/null || true

    echo ""
    ok "All containers and volumes removed"
    warn "output_all/ and gold_output/ files were NOT deleted (delete manually if needed)"
    ;;

# ── help ─────────────────────────────────────────────────────────
help|--help|-h|*)
    echo ""
    echo "  SmartCity Analyzer — run.sh"
    echo ""
    echo "  Usage: bash run.sh <command>"
    echo ""
    echo "  ┌──────────────────────────────────────────────────────────────┐"
    echo "  │  Command          Description                                │"
    echo "  ├──────────────────────────────────────────────────────────────┤"
    echo "  │  airflow          Start Airflow (orchestrates all phases)    │"
    echo "  │  phase1           Start Phase 1 only (Kafka + PostgreSQL)    │"
    echo "  │  phase2           Run Phase 2 only (PySpark transform)       │"
    echo "  │  phase3           Run Phase 3 only (load to SQL Server)      │"
    echo "  │  stop             Stop all running services                  │"
    echo "  │  status           Show all running containers                │"
    echo "  │  logs             Follow all Phase 1 logs                    │"
    echo "  │  logs <service>   Follow logs for one service                │"
    echo "  │  clean            Remove all containers + volumes            │"
    echo "  │  help             Show this message                          │"
    echo "  └──────────────────────────────────────────────────────────────┘"
    echo ""
    echo "  Examples:"
    echo "    bash run.sh airflow                 # Full pipeline via Airflow"
    echo "    bash run.sh phase1                  # Phase 1 only"
    echo "    bash run.sh logs kafka              # Kafka logs"
    echo "    bash run.sh logs airflow-scheduler  # Airflow scheduler logs"
    echo "    bash run.sh stop                    # Stop everything"
    echo "    bash run.sh status                  # What's running?"
    echo ""
    echo "  First time? Run setup first:"
    echo "    bash setup.sh"
    echo ""
    ;;

esac
