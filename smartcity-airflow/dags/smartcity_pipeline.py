from __future__ import annotations
import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.trigger_rule import TriggerRule

PROJECT = "/opt/airflow/smartcity"
PHASE1  = f"{PROJECT}/phase1_scraping"
PHASE2  = f"{PROJECT}/phase2_transform"
PHASE3  = f"{PROJECT}/phase3_dwh"
COMPOSE = f"{PHASE1}/docker-compose.master.yml"
HOST_PROJECT = os.getenv("SMARTCITY_HOST_PATH", "C:/Users/mohamed/Downloads/SmartCityAnalyzer")
HOST_PHASE2  = f"{HOST_PROJECT}/phase2_transform"
HOST_PHASE3  = f"{HOST_PROJECT}/phase3_dwh"
# ✅ بعد
DC = f"docker-compose -p smartcity -f {COMPOSE}"
NETWORK = "smartcity_default"

default_args = {
    "owner":             "smartcity",
    "retries":           1,
    "retry_delay":       timedelta(minutes=2),
    "execution_timeout": timedelta(hours=3),
    "email_on_failure":  False,
}

with DAG(
    dag_id="smartcity_full_pipeline",
    default_args=default_args,
    description="SmartCity Alexandria — Kafka → Bronze → Gold → DWH",
    schedule_interval="0 2 1 */6 *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["smartcity", "kafka", "postgres", "spark", "dwh"],
) as dag:

    start_infrastructure = BashOperator(
    task_id="start_infrastructure",
    bash_command=f"""
        set -e  # ← الأهم: أي command يفشل = الـ task بيفشل فوراً

        echo "Cleaning up old run containers..."
        docker ps -a --filter "name=smartcity" -q | xargs -r docker rm -f || true

        echo "Stopping old infrastructure..."
        timeout 60 {DC} down --remove-orphans --timeout 10 || true
        docker rm -f zookeeper kafka postgres kafka_ui || true

        echo "Starting SmartCity infrastructure..."
        {DC} up -d zookeeper kafka postgres
        echo "✅ Infrastructure containers started"
    """,
)
    wait_kafka_healthy = BashOperator(
        task_id="wait_kafka_healthy",
        bash_command="""
            for i in $(seq 1 30); do
                if timeout 15 docker exec kafka kafka-topics --bootstrap-server kafka:9092 --list > /dev/null 2>&1; then
                    echo "✅ Kafka ready after ${i} attempts"
                    exit 0
                fi
                sleep 10
            done
            echo "❌ Kafka timeout" && exit 1
        """,
        retries=3,
        retry_delay=timedelta(minutes=2),
    )

    # ── Pipeline 01 ──────────────────────────────
    p01_producer = BashOperator(
        task_id="p01_rental_producer",
        bash_command=f"""
            set -e
            echo "🏠 P01 Producer — Rental"
            {DC} run --no-deps --rm rental-producer
            echo "✅ P01 producer done"
        """,
        retries=1,
    )
    p01_consumer = BashOperator(
        task_id="p01_rental_consumer",
        bash_command=f"""
            set -e
            echo "🏠 P01 Consumer — Rental"
            {DC} run --no-deps --rm rental-consumer
            echo "✅ P01 consumer done"
        """,
        retries=2,
    )

    # ── Pipeline 02 ──────────────────────────────
    p02_producer = BashOperator(
        task_id="p02_business_producer",
        bash_command=f"""
            set -e
            echo "🏪 P02 Producer — Business"
            {DC} run --no-deps --rm osm-producer
            echo "⏳ Waiting 30s to avoid API rate-limit..."
            sleep 30
            {DC} run --no-deps --rm pharmacy-producer
            echo "⏳ Waiting 30s to avoid API rate-limit..."
            sleep 30
            {DC} run --no-deps --rm osm-missing-producer
            echo "✅ P02 producer done"
        """,
        retries=3,
        retry_delay=timedelta(minutes=5),
    )
    p02_consumer = BashOperator(
        task_id="p02_business_consumer",
        bash_command=f"""
            set -e
            echo "🏪 P02 Consumer — Business"
            {DC} run --no-deps --rm business-consumer
            echo "✅ P02 consumer done"
        """,
        retries=2,
    )

    # ── Pipeline 03 ──────────────────────────────
    p03_producer = BashOperator(
        task_id="p03_education_producer",
        bash_command=f"""
            set -e
            echo "🏫 P03 Producer — Education"
            {DC} run --no-deps --rm education-producer
            echo "✅ P03 producer done"
        """,
        retries=1,
    )
    p03_consumer = BashOperator(
        task_id="p03_education_consumer",
        bash_command=f"""
            set -e
            echo "🏫 P03 Consumer — Education"
            {DC} run --no-deps --rm education-consumer
            echo "✅ P03 consumer done"
        """,
        retries=2,
    )

    # ── Pipeline 04 ──────────────────────────────
    p04_producer = BashOperator(
        task_id="p04_population_producer",
        bash_command=f"""
            set -e
            echo "👥 P04 Producer — Population"
            {DC} run --no-deps --rm population-producer
            echo "✅ P04 producer done"
        """,
        retries=1,
    )
    p04_consumer = BashOperator(
        task_id="p04_population_consumer",
        bash_command=f"""
            set -e
            echo "👥 P04 Consumer — Population"
            {DC} run --no-deps --rm population-consumer
            echo "✅ P04 consumer done"
        """,
        retries=2,
    )

    # ── Pipeline 05 ──────────────────────────────
    p05_producer = BashOperator(
        task_id="p05_traffic_producer",
        bash_command=f"""
            set -e
            echo "🚗 P05 Producer — Traffic"
            {DC} run --no-deps --rm traffic-producer
            echo "✅ P05 producer done"
        """,
        retries=1,
        execution_timeout=timedelta(hours=2),
    )
    p05_consumer = BashOperator(
        task_id="p05_traffic_consumer",
        bash_command=f"""
            set -e
            echo "🚗 P05 Consumer — Traffic"
            {DC} run --no-deps --rm traffic-consumer
            echo "✅ P05 consumer done"
        """,
        retries=2,
        execution_timeout=timedelta(hours=2),
    )

    bronze_loader = BashOperator(
        task_id="bronze_loader",
        bash_command=f"""
            set -e
            echo "🗄️ Bronze Loader"
            {DC} run --no-deps --rm \
                -e POLL_INTERVAL_SEC=5 \
                -e ONE_SHOT=true \
                bronze-loader
            echo "✅ Bronze layer loaded"
        """,
        trigger_rule=TriggerRule.ALL_DONE,
    )

    phase2_spark_transform = BashOperator(
        task_id="phase2_spark_transform",
        bash_command=f"""
            set -e
            echo "⚡ Phase 2 — Spark Transformation"
            docker run --rm \
                --network {NETWORK} \
                -e PG_HOST=postgres -e PG_PORT=5432 \
                -e PG_DB=smartcity -e PG_USER=smartcity \
                -e PG_PASSWORD=smartcity123 \
                -v {HOST_PHASE2}:/home/jovyan/work \
                -w /home/jovyan/work \
                jupyter/pyspark-notebook:spark-3.5.0 \
                jupyter nbconvert --to notebook --execute \
                    --ExecutePreprocessor.timeout=3600 \
                    --output SmartCity_Phase1_Fixed_executed.ipynb \
                    SmartCity_Phase1_Fixed.ipynb
            echo "✅ Phase 2 done"
        """,
        execution_timeout=timedelta(hours=2),
    )

    phase3_create_schema = BashOperator(
        task_id="phase3_create_dwh_schema",
        bash_command=f"""
            set -e
            echo "🏗️ Phase 3 — Create Schema"
            docker run --rm \
                --add-host=host.docker.internal:host-gateway \
                -v {HOST_PHASE3}/dwh:/dwh \
                mcr.microsoft.com/mssql-tools \
                /opt/mssql-tools/bin/sqlcmd \
                    -S "${{SQLSERVER_HOST}},${{SQLSERVER_PORT}}" \
                    -U "${{SQLSERVER_USER}}" \
                    -P "${{SQLSERVER_PASSWORD}}" \
                    -d "${{SQLSERVER_DB}}" \
                    -i /dwh/01_create_schema.sql
            echo "✅ Schema created"
        """,
    )

    phase3_load_data = BashOperator(
        task_id="phase3_load_gold_to_sqlserver",
        bash_command=f"""
            set -e
            echo "📦 Phase 3 — Load Gold to SQL Server"
            docker run --rm \
                --add-host=host.docker.internal:host-gateway \
                -e SQLSERVER_HOST=host.docker.internal \
                -e SQLSERVER_PORT=1433 \
                -e SQLSERVER_DB=SmartCity \
                -e SQLSERVER_USER=sa \
                -e SQLSERVER_PASSWORD=SmartCity@123 \
                -v {HOST_PHASE3}:/home/jovyan/work \
                -v {HOST_PHASE2}:/home/jovyan/gold_output \
                -w /home/jovyan/work \
                jupyter/datascience-notebook:latest \
                bash -c "pip install --quiet sqlalchemy pymssql openpyxl && jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=1800 --output load_to_sqlserver_executed.ipynb load_to_sqlserver.ipynb"
            echo "✅ Gold loaded to SQL Server"
        """,
        execution_timeout=timedelta(hours=1),
    )

    phase3_apply_constraints = BashOperator(
        task_id="phase3_apply_constraints_indexes",
        bash_command=f"""
            set -e
            echo "🔑 Phase 3 — Constraints & Indexes"
            for sql_file in 02_create_tables.sql 03_constraints.sql 04_indexes.sql; do
                docker run --rm \
                    --add-host=host.docker.internal:host-gateway \
                    -v {HOST_PHASE3}/dwh:/dwh \
                    mcr.microsoft.com/mssql-tools \
                    /opt/mssql-tools/bin/sqlcmd \
                        -S "${{SQLSERVER_HOST}},${{SQLSERVER_PORT}}" \
                        -U "${{SQLSERVER_USER}}" \
                        -P "${{SQLSERVER_PASSWORD}}" \
                        -d "${{SQLSERVER_DB}}" \
                        -i /dwh/$sql_file
            done
            echo "✅ Constraints applied"
        """,
    )

    cleanup_kafka = BashOperator(
        task_id="cleanup_kafka_containers",
        bash_command=f"""
            set -e
            echo "🧹 Cleanup Kafka"
            {DC} stop zookeeper kafka kafka-ui
            echo "✅ Kafka stopped"
        """,
        trigger_rule=TriggerRule.ALL_DONE,
    )

    # ── Dependencies ─────────────────────────────
    start_infrastructure >> wait_kafka_healthy

    wait_kafka_healthy >> [p01_producer, p02_producer, p03_producer, p04_producer, p05_producer]

    p01_producer >> p01_consumer
    p02_producer >> p02_consumer
    p03_producer >> p03_consumer
    p04_producer >> p04_consumer
    p05_producer >> p05_consumer

    [p01_consumer, p02_consumer, p03_consumer, p04_consumer, p05_consumer] >> bronze_loader
    [p01_consumer, p02_consumer, p03_consumer, p04_consumer, p05_consumer] >> cleanup_kafka

    bronze_loader >> phase2_spark_transform
    phase2_spark_transform >> phase3_create_schema
    phase3_create_schema   >> phase3_load_data
    phase3_load_data       >> phase3_apply_constraints
