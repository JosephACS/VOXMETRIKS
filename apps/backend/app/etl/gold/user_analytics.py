from __future__ import annotations

import duckdb

from app.etl.gold._helpers import rebuild_table, stream_events_table

AGG_USER_ENGAGEMENT_DDL = """
CREATE TABLE agg_user_engagement (
    segment          VARCHAR PRIMARY KEY,
    user_count       INTEGER,
    avg_plays        DOUBLE,
    avg_session_min  DOUBLE,
    retention_pct    DOUBLE
)
"""


def build_agg_user_engagement(conn: duckdb.DuckDBPyConnection) -> int:
    events = stream_events_table(conn)
    insert_sql = f"""
        INSERT INTO agg_user_engagement (
            segment, user_count, avg_plays, avg_session_min, retention_pct
        )
        WITH user_stats AS (
            SELECT
                fs.id_usuario,
                COUNT(*) AS total_plays,
                ROUND(AVG(COALESCE(fs.engagement_score, 0)), 2) AS avg_engagement,
                COUNT(DISTINCT COALESCE(
                    fs.fecha_limpia,
                    CAST(fs.fecha_evento AS DATE)
                )) AS active_days,
                MIN(COALESCE(fs.fecha_limpia, CAST(fs.fecha_evento AS DATE))) AS first_day,
                MAX(COALESCE(fs.fecha_limpia, CAST(fs.fecha_evento AS DATE))) AS last_day
            FROM {events} fs
            WHERE fs.id_usuario IS NOT NULL
            GROUP BY 1
        ),
        thresholds AS (
            SELECT
                quantile_cont(total_plays, 0.75) AS p75_plays,
                quantile_cont(total_plays, 0.25) AS p25_plays,
                quantile_cont(avg_engagement, 0.75) AS p75_eng
            FROM user_stats
        ),
        classified AS (
            SELECT
                us.*,
                CASE
                    WHEN us.total_plays >= t.p75_plays OR us.avg_engagement >= t.p75_eng
                        THEN 'power_users'
                    WHEN us.total_plays >= t.p25_plays
                        THEN 'regular_users'
                    ELSE 'casual_users'
                END AS segment,
                ROUND(us.total_plays * 3.2 / NULLIF(us.active_days, 0), 1) AS avg_session_min,
                CASE
                    WHEN us.active_days <= 1 THEN 25.0
                    WHEN us.active_days >= 14 THEN 75.0
                    ELSE ROUND(25.0 + us.active_days * 3.5, 1)
                END AS retention_pct
            FROM user_stats us
            CROSS JOIN thresholds t
        )
        SELECT
            segment,
            COUNT(*) AS user_count,
            ROUND(AVG(total_plays), 1) AS avg_plays,
            ROUND(AVG(avg_session_min), 1) AS avg_session_min,
            ROUND(AVG(retention_pct), 1) AS retention_pct
        FROM classified
        GROUP BY segment
        ORDER BY avg_plays DESC
    """
    return rebuild_table(
        conn,
        "agg_user_engagement",
        AGG_USER_ENGAGEMENT_DDL,
        insert_sql,
        label="user engagement segments",
    )
