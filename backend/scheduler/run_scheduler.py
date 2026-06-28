import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import schedule
import time
from datetime import datetime

from scheduler.data_updater import update_data_pipeline
from scheduler.recommendation_engine import compute_recommendations
from scheduler.alert_system import generate_alerts

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("scheduler.runner")


def run_full_pipeline():
    logger.info("=" * 50)
    logger.info("PIPELINE RUN STARTED at %s", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("=" * 50)
    try:
        update_data_pipeline()
    except Exception as e:
        logger.error("Data update failed: %s", e)
    try:
        compute_recommendations()
    except Exception as e:
        logger.error("Recommendations failed: %s", e)
    try:
        generate_alerts()
    except Exception as e:
        logger.error("Alert generation failed: %s", e)
    logger.info("=" * 50)
    logger.info("PIPELINE RUN COMPLETED")
    logger.info("=" * 50)


if __name__ == "__main__":
    interval_minutes = int(os.getenv("SCHEDULER_INTERVAL", "5"))
    logger.info("Starting scheduler — interval=%d minutes", interval_minutes)

    run_full_pipeline()

    schedule.every(interval_minutes).minutes.do(run_full_pipeline)

    while True:
        schedule.run_pending()
        time.sleep(10)
