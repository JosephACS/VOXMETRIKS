"""Enterprise analytics service — warehouse, trending, platform, engagement."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

import duckdb

from .base_service import count_rows, fetch_rows

PROJECT_ROOT = Path(__file__).resolve().parents[5]
BRONZE_PARQUET = PROJECT_ROOT / "data" / "bronze" / "raw_spotify.parquet"
SILVER_PARQUET = PROJECT_ROOT / "data" / "silver" / "silver_spotify.parquet"
GOLD_DIR = PROJECT_ROOT / "data" / "gold"


def _file_mb(path: Path) -> float:
    try:
        return round(path.stat().st_size / (1024 * 1024), 2) if path.exists() else 0.0
    except OSError:
        return 0.0


def _table_counts(conn: duckdb.DuckDBPyConnection, prefix: str) -> Dict[str, int]:
    tables = conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='main'"
    ).fetchall()
    out: Dict[str, int] = {}
    for (name,) in tables:
        if name.startswith(prefix):
            out[name] = count_rows(conn, name)
    return out


def get_warehouse_status(conn: duckdb.DuckDBPyConnection) -> Dict[str, Any]:
    db_path = os.environ.get("DB_PATH", str(PROJECT_ROOT / "data" / "warehouse" / "voxmetrik.duckdb"))
    db_size_mb = _file_mb(Path(db_path))

    dim_counts = _table_counts(conn, "dim_")
    fact_counts = _table_counts(conn, "fact_")
    agg_counts = _table_counts(conn, "agg_")

    stages: List[Dict[str, Any]] = []
    try:
        rows, _ = fetch_rows(
            conn, "ctl_pipeline_stages",
            columns=["stage", "layer", "duration_ms", "rows_in", "rows_out", "status", "started_at"],
            order_by="id_stage DESC", limit=8,
        )
        stages = rows
    except Exception:
        pass

    loads = []
    try:
        from .stats_service import get_last_loads
        loads = get_last_loads(conn, limit=5)
    except Exception:
        pass

    last_load = loads[0] if loads else None
    pipeline_status = "healthy" if count_rows(conn, "fact_streaming") >= 100_000 else "degraded"

    return {
        "pipeline_status": pipeline_status,
        "db_size_mb": db_size_mb,
        "layers": {
            "bronze": {"file": str(BRONZE_PARQUET.name), "size_mb": _file_mb(BRONZE_PARQUET)},
            "silver": {"file": str(SILVER_PARQUET.name), "size_mb": _file_mb(SILVER_PARQUET)},
            "gold": {
                "parquet_dir": str(GOLD_DIR),
                "parquet_files": len(list(GOLD_DIR.glob("*.parquet"))) if GOLD_DIR.exists() else 0,
                "dimensions": dim_counts,
                "facts": fact_counts,
                "aggregates": agg_counts,
                "total_rows": sum(dim_counts.values()) + sum(fact_counts.values()) + sum(agg_counts.values()),
            },
        },
        "kpis": {
            "total_tracks": count_rows(conn, "dim_track"),
            "total_streams": count_rows(conn, "fact_streaming"),
            "active_users": count_rows(conn, "dim_usuario"),
            "total_playlists": count_rows(conn, "dim_playlist"),
            "fact_tables_rows": sum(fact_counts.values()),
        },
        "last_load": last_load,
        "recent_stages": stages,
    }


def get_trending_analytics(conn: duckdb.DuckDBPyConnection, limit: int = 25) -> Dict[str, Any]:
    top_tracks = []
    try:
        rows, _ = fetch_rows(
            conn, "agg_recommendation_scores",
            columns=["id_track", "nombre_track", "recommendation_score", "engagement_score", "popularity"],
            order_by="recommendation_score DESC", limit=limit,
        )
        top_tracks = rows
    except Exception:
        from .stats_service import get_top_tracks_by_popularity
        top_tracks = get_top_tracks_by_popularity(conn, limit=limit)

    genre_trends = []
    try:
        rows, _ = fetch_rows(
            conn, "agg_genre_trends",
            columns=["id_genero", "nombre_genero", "streams_7d", "trend_pct", "avg_popularity"],
            order_by="streams_7d DESC", limit=15,
        )
        genre_trends = rows
    except Exception:
        pass

    daily = []
    try:
        rows, _ = fetch_rows(
            conn, "agg_daily_streams",
            columns=["fecha", "total_streams", "unique_users", "skip_count"],
            order_by="fecha ASC", limit=30,
        )
        daily = [{**r, "fecha": str(r.get("fecha", ""))} for r in rows]
    except Exception:
        pass

    avg_score = 0.0
    if top_tracks:
        avg_score = round(sum(t.get("recommendation_score", 0) or 0 for t in top_tracks) / len(top_tracks), 2)

    return {
        "top_tracks": top_tracks,
        "top_genres": genre_trends,
        "daily_streams": daily,
        "trending_score_avg": avg_score,
    }


def get_platform_analytics(conn: duckdb.DuckDBPyConnection) -> Dict[str, Any]:
    devices = []
    platform = []
    try:
        rows, _ = fetch_rows(
            conn, "agg_streaming_devices",
            columns=["device_type", "stream_count", "unique_users", "share_pct"],
            order_by="stream_count DESC",
        )
        devices = rows
    except Exception:
        pass

    try:
        rows, _ = fetch_rows(
            conn, "agg_platform_usage",
            columns=["platform", "device_type", "session_count", "total_streams", "avg_session_min", "share_pct"],
            order_by="total_streams DESC",
        )
        platform = rows
    except Exception:
        pass

    active_users = count_rows(conn, "dim_usuario")
    sessions = count_rows(conn, "fact_stream_sessions")

    return {
        "devices": devices,
        "platform_usage": platform,
        "active_users": active_users,
        "sessions": sessions,
        "total_streams": count_rows(conn, "fact_streaming"),
    }


def get_engagement_analytics(conn: duckdb.DuckDBPyConnection) -> Dict[str, Any]:
    skip_rate = 0.0
    completion_rate = 0.0
    avg_session_min = 0.0
    try:
        row = conn.execute("""
            SELECT
                ROUND(SUM(CASE WHEN skipped THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2),
                ROUND(SUM(CASE WHEN completado THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2)
            FROM fact_streaming
        """).fetchone()
        if row:
            skip_rate = float(row[0] or 0)
            completion_rate = float(row[1] or 0)
    except Exception:
        pass

    try:
        row = conn.execute("""
            SELECT ROUND(AVG(total_ms) / 60000.0, 2) FROM fact_stream_sessions
        """).fetchone()
        if row and row[0]:
            avg_session_min = float(row[0])
    except Exception:
        pass

    segments = []
    retention = []
    top_searches = []
    try:
        rows, _ = fetch_rows(
            conn, "agg_user_engagement",
            columns=["segment", "user_count", "avg_plays", "avg_session_min", "retention_pct"],
        )
        segments = rows
    except Exception:
        pass

    try:
        rows, _ = fetch_rows(conn, "agg_user_retention",
                             columns=["cohort_week", "users_cohort", "week_1_pct", "week_2_pct", "week_4_pct"],
                             order_by="cohort_week")
        retention = rows
    except Exception:
        pass

    try:
        rows, _ = fetch_rows(conn, "agg_top_searches",
                             columns=["query_text", "search_count", "avg_results"],
                             order_by="search_count DESC", limit=10)
        top_searches = rows
    except Exception:
        pass

    engagement_score = 0.0
    try:
        row = conn.execute("SELECT ROUND(AVG(engagement_score), 2) FROM agg_user_activity").fetchone()
        if row and row[0]:
            engagement_score = float(row[0])
    except Exception:
        engagement_score = round(completion_rate * 0.6 + (100 - skip_rate) * 0.4, 2)

    return {
        "skip_rate": skip_rate,
        "completion_rate": completion_rate,
        "avg_session_time_min": avg_session_min,
        "engagement_score": engagement_score,
        "user_segments": segments,
        "user_retention": retention,
        "top_searches": top_searches,
        "recommendation_avg": engagement_score,
    }
