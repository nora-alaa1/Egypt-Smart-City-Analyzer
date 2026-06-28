import os
import json
import logging
from datetime import datetime
from sqlalchemy import text

from db import get_engine, init_db

logger = logging.getLogger("scheduler.alerts")

_STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_previous_state.json")

SUITABILITY_INCREASE_THRESHOLD = 0.5
RENT_DROP_THRESHOLD = 200

def _load_previous_state():
    if os.path.exists(_STATE_FILE):
        with open(_STATE_FILE) as f:
            return json.load(f)
    return {}

def _save_state(state: dict):
    with open(_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def _ensure_alert_type(raw: str) -> str:
    valid = {"competition", "rent", "demand"}
    return raw if raw in valid else "demand"

def _insert_alert(conn, message: str, alert_type: str, area_id, business_type_id):
    conn.execute(
        text("""
            INSERT INTO alerts (message, type, area_id, business_type_id, created_at)
            VALUES (:msg, :typ, :aid, :bt, :ts)
        """),
        {
            "msg": message,
            "typ": _ensure_alert_type(alert_type),
            "aid": area_id,
            "bt": business_type_id,
            "ts": datetime.utcnow(),
        }
    )

def _is_duplicate(conn, message: str) -> bool:
    result = conn.execute(
        text("SELECT COUNT(*) FROM alerts WHERE message = :msg AND created_at >= datetime('now', '-1 hour')"),
        {"msg": message}
    ).scalar()
    return result > 0

def generate_alerts():
    logger.info("=== ALERTS START ===")
    engine = get_engine()
    init_db()

    previous = _load_previous_state()
    current = {}

    with engine.connect() as conn:
        # Current top-area per business_type
        top_rows = conn.execute(
            text("""
                SELECT pr.business_type_id, pr.area_id, pr.suitability_score, pr.rank,
                       abs.competitor_count, abs.market_saturation
                FROM precomputed_recommendations pr
                LEFT JOIN area_business_scores abs
                    ON abs.business_type_id = pr.business_type_id
                    AND abs.area_id = pr.area_id
                WHERE pr.rank = 1
            """)
        ).fetchall()

        # Get business type names
        bt_map = {}
        bt_rows = conn.execute(
            text("SELECT business_type_id, category, subcategory FROM business_types")
        ).fetchall()
        for r in bt_rows:
            bt_map[r.business_type_id] = f"{r.category} / {r.subcategory}"

        # Get area names
        area_map = {}
        area_rows = conn.execute(
            text("SELECT area_id, area_name FROM areas")
        ).fetchall()
        for r in area_rows:
            area_map[r.area_id] = r.area_name

        alert_count = 0

        for row in top_rows:
            bt_id = row.business_type_id
            area_id = row.area_id
            score = row.suitability_score
            competitors = row.competitor_count or 0
            saturation = row.market_saturation or 0.0

            bt_name = bt_map.get(bt_id, f"type-{bt_id}")
            area_name = area_map.get(area_id, f"area-{area_id}")

            current[str(bt_id)] = {
                "area_id": area_id,
                "area_name": area_name,
                "score": score,
                "competitors": competitors,
                "saturation": saturation,
            }

            prev = previous.get(str(bt_id))

            # (a) New top area detected
            if prev and prev.get("area_id") != area_id:
                msg = f"New top area detected for {bt_name}: {area_name}"
                if not _is_duplicate(conn, msg):
                    _insert_alert(conn, msg, "competition", area_id, bt_id)
                    logger.info("ALERT: %s", msg)
                    alert_count += 1

            # (b) Competitor count dropped significantly
            if prev:
                prev_comp = prev.get("competitors", competitors)
                if prev_comp > 3 and competitors < prev_comp - 2:
                    msg = f"Competitor count dropped in {area_name} ({bt_name}): {prev_comp} → {competitors}"
                    if not _is_duplicate(conn, msg):
                        _insert_alert(conn, msg, "competition", area_id, bt_id)
                        logger.info("ALERT: %s", msg)
                        alert_count += 1

            # (c) Suitability score increased above threshold
            if prev:
                prev_score = prev.get("score", score)
                if score > prev_score + SUITABILITY_INCREASE_THRESHOLD:
                    msg = f"Score jump for {area_name} ({bt_name}): {prev_score:.1f} → {score:.1f}"
                    if not _is_duplicate(conn, msg):
                        _insert_alert(conn, msg, "demand", area_id, bt_id)
                        logger.info("ALERT: %s", msg)
                        alert_count += 1

            # (d) Market saturation / rent signal
            if prev:
                prev_sat = prev.get("saturation", saturation)
                if saturation < prev_sat - 10:
                    msg = f"Market saturation dropped in {area_name} ({bt_name}): {prev_sat:.0f}% → {saturation:.0f}%"
                    if not _is_duplicate(conn, msg):
                        _insert_alert(conn, msg, "rent", area_id, bt_id)
                        logger.info("ALERT: %s", msg)
                        alert_count += 1

        conn.commit()

    _save_state(current)
    logger.info("Generated %d alerts", alert_count)
    logger.info("=== ALERTS COMPLETE ===")
    return True
