"""High-level warehouse summary counts and averages."""

from __future__ import annotations

import logging
from typing import Any, Dict

import duckdb

from app.core.database import table_exists
from app.core.query_helpers import count_rows
from app.core.response_cache import cached_response

from .constants import ACTIVITY_FACT_TABLES

logger = logging.getLogger(__name__)


def _safe_count(conn: duckdb.DuckDBPyConnection, table: str) -> int:
    if not table_exists(conn, table):
        return 0
    return count_rows(conn, table)


@cached_response(ttl_seconds=30.0)
def get_summary(conn: duckdb.DuckDBPyConnection) -> Dict[str, Any]:
    """High-level counts + averages across all warehouse tables."""
    result: Dict[str, Any] = {
        "total_tracks": _safe_count(conn, "dim_track"),
        "total_artistas": _safe_count(conn, "dim_artista"),
        "total_generos": _safe_count(conn, "dim_genero"),
        "total_albumes": _safe_count(conn, "dim_album"),
        "total_streams": _safe_count(conn, "fact_streaming"),
        "active_users": _safe_count(conn, "dim_usuario"),
        "total_playlists": _safe_count(conn, "dim_playlist"),
    }
    result["total_events"] = sum(_safe_count(conn, table) for table in ACTIVITY_FACT_TABLES)

    try:
        row = conn.execute("""
            SELECT
                ROUND(SUM(CASE WHEN skipped THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 2),
                ROUND(SUM(CASE WHEN completado THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 2),
                ROUND(AVG(engagement_score), 2)
            FROM fact_streaming fs
            LEFT JOIN agg_user_activity ua ON ua.id_usuario = fs.id_usuario
        """).fetchone()
        if row:
            result["skip_rate"] = float(row[0] or 0)
            result["completion_rate"] = float(row[1] or 0)
            result["engagement_score"] = float(row[2] or 0)
    except Exception:
        logger.exception("get_summary: engagement metrics query failed")

    try:
        row = conn.execute("""
            SELECT
                AVG(popularity)    AS promedio_popularidad,
                AVG(energy)        AS promedio_energy,
                AVG(danceability)  AS promedio_danceability,
                AVG(valence)       AS promedio_valence,
                AVG(tempo)         AS promedio_tempo
            FROM dim_track
            WHERE popularity IS NOT NULL
        """).fetchone()
        if row:
            result["promedio_popularidad"] = round(float(row[0] or 0), 1)
            result["promedio_energy"] = round(float(row[1] or 0), 4)
            result["promedio_danceability"] = round(float(row[2] or 0), 4)
            result["promedio_valence"] = round(float(row[3] or 0), 4)
            result["promedio_tempo"] = round(float(row[4] or 0), 1)
    except Exception:
        logger.exception("get_summary: dim_track audio averages query failed")
        result["promedio_popularidad"] = 0.0
        result["promedio_energy"] = 0.0
        result["promedio_danceability"] = 0.0
        result["promedio_valence"] = 0.0
        result["promedio_tempo"] = 0.0

    return result
