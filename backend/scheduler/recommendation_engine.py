import logging
from datetime import datetime
from sqlalchemy import text

from db import get_engine, init_db

logger = logging.getLogger("scheduler.recommendations")

TOP_N = 5

def compute_recommendations():
    logger.info("=== RECOMMENDATIONS START ===")
    engine = get_engine()
    init_db()

    with engine.connect() as conn:
        conn.execute(
            text("DELETE FROM precomputed_recommendations")
        )
        conn.commit()
        logger.info("Cleared old precomputed_recommendations")

        rows = conn.execute(
            text("""
                SELECT DISTINCT business_type_id
                FROM area_business_scores
                WHERE business_type_id IS NOT NULL
            """)
        ).fetchall()

        total_inserted = 0
        for (bt_id,) in rows:
            top_areas = conn.execute(
                text("""
                    SELECT area_id, suitability_score
                    FROM area_business_scores
                    WHERE business_type_id = :bt
                    ORDER BY suitability_score DESC
                    LIMIT :limit
                """),
                {"bt": bt_id, "limit": TOP_N}
            ).fetchall()

            for rank, row in enumerate(top_areas, 1):
                conn.execute(
                    text("""
                        INSERT INTO precomputed_recommendations
                            (business_type_id, area_id, suitability_score, rank, created_at)
                        VALUES (:bt, :aid, :score, :rank, :ts)
                    """),
                    {
                        "bt": bt_id,
                        "aid": row.area_id,
                        "score": row.suitability_score,
                        "rank": rank,
                        "ts": datetime.utcnow(),
                    }
                )
                total_inserted += 1

        conn.commit()

    logger.info("Computed %d recommendations (%d business types)", total_inserted, len(rows))
    logger.info("=== RECOMMENDATIONS COMPLETE ===")
    return True
