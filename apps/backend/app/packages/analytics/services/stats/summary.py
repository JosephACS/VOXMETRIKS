"""High-level warehouse summary counts and averages."""

from __future__ import annotations

import logging
from typing import Any, Dict

import duckdb

from app.core.database import table_exists
from app.core.query_helpers import count_rows
from app.core.response_cache import cached_response

from .constants import ACTIVITY_FACT_TABLES
from .events_inventory import classify_activity_facts, _latest_activity_load

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
        # Scope labels — warehouse global catalog (unique rows), not personal.
        "tracks_scope": "warehouse_catalog",
        "artists_scope": "warehouse_catalog",
        "albums_scope": "warehouse_catalog",
        "playlists_scope": "warehouse_catalog",
        "streams_scope": "warehouse_fact_streaming",
        "events_scope": "warehouse_activity_facts",
    }
    # Analytical events KPI: sum of activity fact tables (see get_events_breakdown).
    events_total = sum(_safe_count(conn, table) for table in ACTIVITY_FACT_TABLES)
    result["total_events"] = events_total
    try:
        classification = classify_activity_facts(conn)
        class_totals = {c: 0 for c in ("real", "imported", "demo", "synthetic", "unknown")}
        class_totals[classification] = events_total
        result["events_classification_totals"] = class_totals
        load = _latest_activity_load(conn)
        if load and load.get("fecha_carga") is not None:
            fc = load["fecha_carga"]
            result["events_updated_at"] = fc.isoformat() if hasattr(fc, "isoformat") else str(fc)
        else:
            result["events_updated_at"] = None
    except Exception:
        logger.exception("get_summary: events classification enrichment failed")
        result["events_updated_at"] = None
        result["events_classification_totals"] = None

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
