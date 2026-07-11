from __future__ import annotations

import duckdb

from app.etl.gold._helpers import rebuild_table, stream_events_all_table

AGG_DAILY_STREAMS_DDL = """
CREATE TABLE agg_daily_streams (
    fecha            DATE PRIMARY KEY,
    total_streams    INTEGER,
    unique_users     INTEGER,
    unique_tracks    INTEGER,
    avg_duration_ms  DOUBLE,
    skip_rate        DOUBLE
)
"""

AGG_PLATFORM_USAGE_DDL = """
CREATE TABLE agg_platform_usage (
    platform         VARCHAR,
    device_type      VARCHAR,
    session_count    INTEGER,
    total_streams    INTEGER,
    avg_session_min  DOUBLE,
    share_pct        DOUBLE,
    PRIMARY KEY (platform, device_type)
)
"""


def build_agg_daily_streams(conn: duckdb.DuckDBPyConnection) -> int:
    events = stream_events_all_table(conn)
    has_skipped = "skipped" in {
        r[0] for r in conn.execute(f"DESCRIBE {events}").fetchall()
    }
    duration_col = "duracion_ms" if events == "fact_streaming" else "duracion_ms"
    skip_expr = (
        "ROUND(SUM(CASE WHEN COALESCE(skipped, FALSE) THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2)"
        if has_skipped
        else "0.0"
    )
    insert_sql = f"""
        INSERT INTO agg_daily_streams (
            fecha, total_streams, unique_users, unique_tracks, avg_duration_ms, skip_rate
        )
        SELECT
            CAST(fecha_evento AS DATE) AS fecha,
            COUNT(*) AS total_streams,
            COUNT(DISTINCT id_usuario) AS unique_users,
            COUNT(DISTINCT id_track) AS unique_tracks,
            ROUND(AVG(COALESCE({duration_col}, 0)), 0) AS avg_duration_ms,
            {skip_expr} AS skip_rate
        FROM {events}
        WHERE fecha_evento IS NOT NULL
          AND id_track IS NOT NULL
        GROUP BY 1
        ORDER BY 1
    """
    return rebuild_table(
        conn,
        "agg_daily_streams",
        AGG_DAILY_STREAMS_DDL,
        insert_sql,
        label="daily metrics",
    )


def build_agg_platform_usage(conn: duckdb.DuckDBPyConnection) -> int:
    events = stream_events_all_table(conn)
    insert_sql = f"""
        INSERT INTO agg_platform_usage (
            platform, device_type, session_count, total_streams, avg_session_min, share_pct
        )
        WITH base AS (
            SELECT
                COALESCE(platform, 'unknown') AS platform,
                COALESCE(device_type, 'unknown') AS device_type,
                COUNT(DISTINCT COALESCE(session_id, id_streaming)) AS session_count,
                COUNT(*) AS total_streams
            FROM {events}
            GROUP BY 1, 2
        ),
        tot AS (SELECT SUM(total_streams) AS t FROM base)
        SELECT
            b.platform,
            b.device_type,
            b.session_count,
            b.total_streams,
            ROUND(b.total_streams * 3.5 / NULLIF(b.session_count, 0), 1) AS avg_session_min,
            ROUND(b.total_streams * 100.0 / NULLIF(t.t, 0), 2) AS share_pct
        FROM base b
        CROSS JOIN tot t
        ORDER BY b.total_streams DESC
    """
    return rebuild_table(
        conn,
        "agg_platform_usage",
        AGG_PLATFORM_USAGE_DDL,
        insert_sql,
        label="platform usage",
    )
