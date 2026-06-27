"""Enterprise analytics service — warehouse, trending, platform, engagement."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import duckdb

from .base_service import count_rows, fetch_rows
from app.packages.streaming.services.display_text import sanitize_display_text

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


# Tables never exposed via Data Explorer (auth/session data).
EXPLORER_BLOCKED_TABLES: frozenset[str] = frozenset({
    "app_user",
    "app_session",
})

# Column names redacted in preview rows (defense in depth).
SENSITIVE_COLUMN_NAMES: frozenset[str] = frozenset({
    "password_hash",
    "password",
    "token",
    "session_token",
})


def _table_kind(name: str) -> str:
    if name.startswith("dim_"):
        return "dimension"
    if name.startswith("fact_"):
        return "fact"
    if name.startswith("agg_"):
        return "aggregation"
    if name.startswith("ctl_") or name == "raw_spotify":
        return "control"
    if name.startswith("app_"):
        return "application"
    return "other"


def _explorer_visible_tables(conn: duckdb.DuckDBPyConnection) -> List[str]:
    return [n for n in _allowed_tables(conn) if n not in EXPLORER_BLOCKED_TABLES]


def _redact_cell(column: str, value: Any) -> Any:
    if column.lower() in SENSITIVE_COLUMN_NAMES:
        return "***"
    return value


def _allowed_tables(conn: duckdb.DuckDBPyConnection) -> List[str]:
    rows = conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' ORDER BY table_name"
    ).fetchall()
    return [r[0] for r in rows]


def get_warehouse_tables(conn: duckdb.DuckDBPyConnection) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    for name in _explorer_visible_tables(conn):
        kind = _table_kind(name)
        row_count = count_rows(conn, name)
        columns: List[Dict[str, str]] = []
        try:
            desc = conn.execute(f'DESCRIBE "{name}"').fetchall()
            columns = [{"name": r[0], "type": str(r[1])} for r in desc]
        except Exception:
            pass
        result.append({
            "name": name,
            "kind": kind,
            "layer": "gold" if kind in ("dimension", "fact", "aggregation") else "warehouse",
            "row_count": row_count,
            "columns": columns,
        })
    return result


def get_table_preview(
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    page: int = 1,
    limit: int = 8,
) -> Dict[str, Any]:
    allowed = set(_explorer_visible_tables(conn))
    if table_name not in allowed:
        if table_name in EXPLORER_BLOCKED_TABLES:
            raise ValueError(f"Table '{table_name}' is not accessible")
        raise ValueError(f"Table '{table_name}' not found")

    offset = max(0, (page - 1) * limit)
    total = count_rows(conn, table_name)

    rows_raw = conn.execute(
        f'SELECT * FROM "{table_name}" LIMIT ? OFFSET ?',
        [limit, offset],
    ).fetchall()
    cols = [d[0] for d in conn.description]
    safe_cols = [c for c in cols if c.lower() not in SENSITIVE_COLUMN_NAMES]
    if not safe_cols:
        safe_cols = cols
    rows = []
    for r in rows_raw:
        item: Dict[str, Any] = {}
        for col, val in zip(cols, r):
            if col.lower() in SENSITIVE_COLUMN_NAMES:
                continue
            if val is None:
                item[col] = None
            elif hasattr(val, "isoformat"):
                item[col] = val.isoformat()
            else:
                item[col] = _redact_cell(col, val)
        rows.append(item)

    col_list = ", ".join(safe_cols[:8]) if safe_cols else "*"
    query = f"SELECT {col_list}\nFROM {table_name}\nLIMIT {limit}\nOFFSET {offset};"

    return {
        "table": table_name,
        "total": total,
        "page": page,
        "limit": limit,
        "columns": safe_cols if safe_cols else cols,
        "rows": rows,
        "query": query,
    }


MOOD_ENERGY_RANGES: Dict[str, Tuple[float, float]] = {
    "1_muy_baja": (0.0, 0.2),
    "2_baja": (0.2, 0.4),
    "3_media": (0.4, 0.6),
    "4_alta": (0.6, 0.8),
    "5_muy_alta": (0.8, 1.001),
}

MOOD_LABELS: Dict[str, Tuple[str, str]] = {
    "1_muy_baja": ("Chill", "Muy baja energía · ambiente relajado"),
    "2_baja": ("Focus", "Baja energía · concentración moderada"),
    "3_media": ("Balance", "Energía media equilibrada"),
    "4_alta": ("Workout", "Alta energía · actividad física"),
    "5_muy_alta": ("Party", "Máxima intensidad · fiesta"),
}


def _parse_energy_range(mood_key: str) -> Optional[Tuple[float, float]]:
    """Convierte id warehouse o rango numérico a (low, high)."""
    if mood_key in MOOD_ENERGY_RANGES:
        return MOOD_ENERGY_RANGES[mood_key]
    normalized = mood_key.replace("_", ".")
    if "-" not in normalized:
        return None
    parts = normalized.split("-", 1)
    try:
        return float(parts[0]), float(parts[1])
    except ValueError:
        return None


def get_mood_tracks(
    conn: duckdb.DuckDBPyConnection,
    mood_key: str,
    limit: int = 12,
) -> List[Dict[str, Any]]:
    parsed = _parse_energy_range(mood_key)
    if not parsed:
        return []
    low, high = parsed
    rows = conn.execute(
        """
        SELECT
            dt.id_track,
            dt.nombre_track,
            da.nombre_artista,
            dg.nombre_genero,
            dt.popularity,
            dt.energy,
            ROUND(dt.popularity * 0.6 + dt.energy * 100 * 0.4, 1) AS recommendation_score
        FROM dim_track dt
        LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
        LEFT JOIN dim_genero dg ON dg.id_genero = dt.id_genero
        WHERE dt.energy >= ? AND dt.energy < ?
        ORDER BY dt.popularity DESC NULLS LAST
        LIMIT ?
        """,
        [low, high if high < 1.0 else 1.001, limit],
    ).fetchall()
    result = []
    for r in rows:
        artist_raw = r[2] or ""
        primary = artist_raw.split(";")[0].strip() if artist_raw else None
        result.append({
            "id_track": r[0],
            "nombre_track": r[1],
            "nombre_artista": primary,
            "nombre_artista_full": artist_raw,
            "nombre_genero": r[3],
            "popularity": r[4],
            "energy": r[5],
            "recommendation_score": float(r[6] or 0),
        })
    return result


def _clean_track_labels(track: Dict[str, Any]) -> Dict[str, Any]:
    cleaned = dict(track)
    if "nombre_track" in cleaned:
        cleaned["nombre_track"] = sanitize_display_text(cleaned.get("nombre_track"))
    if "nombre_artista" in cleaned:
        cleaned["nombre_artista"] = sanitize_display_text(cleaned.get("nombre_artista"))
    return cleaned


def get_recommendations(
    conn: duckdb.DuckDBPyConnection,
    favorite_genre: Optional[str] = None,
    limit: int = 12,
    mood: Optional[str] = None,
) -> Dict[str, Any]:
    tracks: List[Dict[str, Any]] = []
    try:
        rows, _ = fetch_rows(
            conn, "agg_recommendation_scores",
            columns=[
                "id_track", "nombre_track", "nombre_artista", "nombre_genero",
                "recommendation_score", "engagement_score", "popularity",
            ],
            order_by="recommendation_score DESC",
            limit=limit,
        )
        tracks = rows
    except Exception:
        from .stats_service import get_top_tracks_by_popularity
        raw = get_top_tracks_by_popularity(conn, limit=limit)
        tracks = [
            {
                "id_track": t.get("id_track"),
                "nombre_track": t.get("nombre_track"),
                "nombre_artista": t.get("nombre_artista"),
                "nombre_genero": t.get("nombre_genero"),
                "recommendation_score": t.get("popularity"),
                "popularity": t.get("popularity"),
            }
            for t in raw
        ]

    if favorite_genre and tracks:
        genre_lower = favorite_genre.lower()
        preferred = [t for t in tracks if (t.get("nombre_genero") or "").lower() == genre_lower]
        others = [t for t in tracks if (t.get("nombre_genero") or "").lower() != genre_lower]
        tracks = preferred + others

    artists: List[Dict[str, Any]] = []
    try:
        rows, _ = fetch_rows(
            conn, "agg_top_artistas",
            columns=["id_artista", "nombre_artista", "promedio_popularidad", "total_tracks"],
            order_by="promedio_popularidad DESC",
            limit=8,
        )
        artists = [
            {
                **r,
                "affinity": round((r.get("promedio_popularidad") or 0), 1),
            }
            for r in rows
        ]
    except Exception:
        pass

    genres: List[Dict[str, Any]] = []
    try:
        rows, _ = fetch_rows(
            conn, "agg_genero_popularidad",
            columns=["id_genero", "nombre_genero", "popularidad_promedio", "total_tracks"],
            order_by="popularidad_promedio DESC",
            limit=10,
        )
        max_pop = max((r.get("popularidad_promedio") or 0) for r in rows) if rows else 1
        genres = [
            {
                "genre": r.get("nombre_genero"),
                "score": round(((r.get("popularidad_promedio") or 0) / max_pop) * 100, 1),
                "total_tracks": r.get("total_tracks"),
            }
            for r in rows
        ]
    except Exception:
        pass

    moods: List[Dict[str, Any]] = []
    try:
        rows, _ = fetch_rows(
            conn, "agg_distribucion_energia",
            columns=["rango_energia", "cantidad_tracks", "popularidad_promedio"],
            order_by="rango_energia",
        )
        for r in rows:
            key = r.get("rango_energia", "")
            meta = MOOD_LABELS.get(key, (key.replace("_", " ").title(), "Colección por energía"))
            moods.append({
                "id": key,
                "name": meta[0],
                "description": meta[1],
                "tracks": int(r.get("cantidad_tracks") or 0),
            })
    except Exception:
        pass

    mood_tracks: List[Dict[str, Any]] = []
    mood_label = None
    if mood:
        mood_tracks = get_mood_tracks(conn, mood, limit=limit)
        for m in moods:
            if m.get("id") == mood:
                mood_label = m.get("name")
                break
        if not mood_label:
            meta = MOOD_LABELS.get(mood)
            mood_label = meta[0] if meta else mood.replace("_", " ")

    return {
        "for_you": [_clean_track_labels(t) for t in tracks],
        "artists": artists,
        "genres": genres,
        "moods": moods,
        "mood_filter": mood,
        "mood_label": mood_label,
        "mood_tracks": [_clean_track_labels(t) for t in mood_tracks],
        "mood_count": len(mood_tracks),
    }
