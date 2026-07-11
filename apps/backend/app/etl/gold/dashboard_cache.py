"""Precomputed dashboard snapshot table (GOLD layer extension)."""

from __future__ import annotations

import json

import duckdb

from app.core.logging import get_logger
from app.etl.gold._helpers import table_exists

logger = get_logger(__name__)

AGG_DASHBOARD_CACHE_DDL = """
CREATE TABLE agg_dashboard_cache (
    cache_key         VARCHAR PRIMARY KEY,
    cache_type        VARCHAR NOT NULL,
    metric_date       DATE,
    metric_hour       INTEGER,
    total_streams     BIGINT,
    active_users      INTEGER,
    total_tracks      INTEGER,
    top_genre         VARCHAR,
    avg_session_min   DOUBLE,
    skip_rate         DOUBLE,
    streams_60m       INTEGER,
    users_60m         INTEGER,
    growth_pct_weekly DOUBLE,
    payload_json      VARCHAR,
    computed_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""


def build_agg_dashboard_cache(conn: duckdb.DuckDBPyConnection) -> int:
    """Rebuild dashboard cache from GOLD aggregates (no fact full scans)."""
    logger.info("[GOLD] Building dashboard cache...")
    conn.execute("DROP TABLE IF EXISTS agg_dashboard_cache")
    conn.execute(AGG_DASHBOARD_CACHE_DDL)

    _insert_overview(conn)
    _insert_hourly(conn)
    _insert_engagement(conn)
    _insert_growth(conn)

    total = int(conn.execute("SELECT COUNT(*) FROM agg_dashboard_cache").fetchone()[0])
    logger.info("[GOLD] agg_dashboard_cache → %s rows", f"{total:,}")
    return total


def _daily_skip_rate_expr(conn: duckdb.DuckDBPyConnection) -> str:
    cols = {str(r[0]).lower() for r in conn.execute("DESCRIBE agg_daily_streams").fetchall()}
    if "skip_rate" in cols:
        return "skip_rate"
    if "skip_count" in cols:
        return "ROUND(COALESCE(skip_count, 0) * 1.0 / NULLIF(total_streams, 0), 4)"
    return "0.0"


def _insert_overview(conn: duckdb.DuckDBPyConnection) -> None:
    if not table_exists(conn, "agg_daily_streams"):
        return

    skip_expr = _daily_skip_rate_expr(conn)

    total_tracks = 0
    if table_exists(conn, "dim_track"):
        total_tracks = int(conn.execute("SELECT COUNT(*) FROM dim_track").fetchone()[0])

    top_genre = None
    if table_exists(conn, "agg_genero_popularidad"):
        row = conn.execute(
            """
            SELECT nombre_genero FROM agg_genero_popularidad
            ORDER BY popularidad_promedio DESC, total_tracks DESC LIMIT 1
            """
        ).fetchone()
        top_genre = row[0] if row else None

    avg_session = 0.0
    if table_exists(conn, "agg_user_engagement"):
        row = conn.execute(
            "SELECT ROUND(AVG(avg_session_min), 1) FROM agg_user_engagement"
        ).fetchone()
        avg_session = float(row[0] or 0)

    conn.execute(
        """
        INSERT INTO agg_dashboard_cache (
            cache_key, cache_type, metric_date,
            total_streams, active_users, total_tracks,
            top_genre, avg_session_min, skip_rate, computed_at
        )
        SELECT
            'overview:latest',
            'overview',
            d.fecha,
            d.total_streams,
            d.unique_users,
            ?,
            ?,
            ?,
            ROUND(COALESCE(d.skip_rate, 0) / CASE WHEN d.skip_rate > 1 THEN 100.0 ELSE 1.0 END, 4),
            CURRENT_TIMESTAMP
        FROM (
            SELECT fecha, total_streams, unique_users, {skip_expr} AS skip_rate
            FROM agg_daily_streams
            ORDER BY fecha DESC
            LIMIT 1
        ) d
        """.format(skip_expr=skip_expr),
        [total_tracks, top_genre, avg_session],
    )


def _insert_hourly(conn: duckdb.DuckDBPyConnection) -> None:
    if not table_exists(conn, "agg_daily_streams"):
        return
    conn.execute(
        """
        INSERT INTO agg_dashboard_cache (
            cache_key, cache_type, metric_date, metric_hour,
            total_streams, streams_60m, computed_at
        )
        SELECT
            'hourly:' || CAST(fecha AS VARCHAR),
            'hourly',
            fecha,
            EXTRACT(HOUR FROM CURRENT_TIMESTAMP)::INTEGER,
            total_streams,
            GREATEST(1, CAST(total_streams / 24.0 AS INTEGER)),
            CURRENT_TIMESTAMP
        FROM (
            SELECT fecha, total_streams
            FROM agg_daily_streams
            ORDER BY fecha DESC
            LIMIT 24
        ) sub
        """
    )


def _insert_engagement(conn: duckdb.DuckDBPyConnection) -> None:
    if not table_exists(conn, "agg_user_engagement"):
        return
    rows = conn.execute(
        """
        SELECT segment, user_count, avg_plays, avg_session_min, retention_pct
        FROM agg_user_engagement
        """
    ).fetchall()
    payload = json.dumps(
        [
            {
                "segment": r[0],
                "user_count": r[1],
                "avg_plays": r[2],
                "avg_session_min": r[3],
                "retention_pct": r[4],
            }
            for r in rows
        ]
    )
    total_users = sum(int(r[1] or 0) for r in rows) or 1
    avg_sess = conn.execute(
        "SELECT ROUND(AVG(avg_session_min), 1) FROM agg_user_engagement"
    ).fetchone()[0]

    conn.execute(
        """
        INSERT INTO agg_dashboard_cache (
            cache_key, cache_type, payload_json, active_users, avg_session_min, computed_at
        ) VALUES ('engagement:latest', 'engagement', ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        [payload, total_users, avg_sess],
    )


def _insert_growth(conn: duckdb.DuckDBPyConnection) -> None:
    if not table_exists(conn, "agg_daily_streams"):
        return

    growth_row = conn.execute(
        """
        WITH bounds AS (
            SELECT MAX(fecha) AS max_d FROM agg_daily_streams
        ),
        w AS (
            SELECT
                SUM(CASE WHEN d.fecha > b.max_d - INTERVAL 7 DAY THEN d.total_streams ELSE 0 END) AS s7,
                SUM(CASE WHEN d.fecha <= b.max_d - INTERVAL 7 DAY
                          AND d.fecha > b.max_d - INTERVAL 14 DAY THEN d.total_streams ELSE 0 END) AS sp7
            FROM agg_daily_streams d
            CROSS JOIN bounds b
        )
        SELECT CASE WHEN sp7 = 0 THEN 0 ELSE ROUND((s7 - sp7) * 100.0 / sp7, 1) END FROM w
        """
    ).fetchone()
    growth_pct = float(growth_row[0] or 0) if growth_row else 0.0

    artists: list[dict] = []
    if table_exists(conn, "agg_artist_growth"):
        for r in conn.execute(
            """
            SELECT id_artista, nombre_artista, streams_7d, growth_pct
            FROM agg_artist_growth
            ORDER BY growth_pct DESC, streams_7d DESC
            LIMIT 10
            """
        ).fetchall():
            artists.append(
                {
                    "id_artista": r[0],
                    "nombre": r[1],
                    "streams_7d": r[2],
                    "growth_pct": r[3],
                }
            )

    conn.execute(
        """
        INSERT INTO agg_dashboard_cache (
            cache_key, cache_type, growth_pct_weekly, payload_json, computed_at
        ) VALUES ('growth:latest', 'growth', ?, ?, CURRENT_TIMESTAMP)
        """,
        [growth_pct, json.dumps({"top_artists": artists})],
    )
