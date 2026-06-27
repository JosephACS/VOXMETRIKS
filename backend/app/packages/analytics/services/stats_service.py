"""backend/services/stats_service.py"""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any, Dict, List

import duckdb

from .base_service import count_rows, fetch_rows

# Límites validados — el catálogo musical queda real; lo sintético son eventos/facts.
MAX_TARGET_TOTAL = 2_000_000       # tope práctico para actividad sintética
MAX_CREATE_PER_RUN = 2_000_000     # máx. filas nuevas por ejecución
WARN_CREATE_ABOVE = 500_000        # aviso UI / respuesta
SYNTHETIC_BATCH_SIZE = 100_000     # insert por lotes para no saturar memoria
ACTIVITY_FACT_TABLES = [
    "fact_streaming",
    "fact_user_activity",
    "fact_playlist_activity",
    "fact_favorites",
    "fact_searches",
    "fact_stream_sessions",
]


def get_summary(conn: duckdb.DuckDBPyConnection) -> Dict[str, Any]:
    """High-level counts + averages across all warehouse tables."""
    result: Dict[str, Any] = {
        "total_tracks":   count_rows(conn, "dim_track"),
        "total_artistas": count_rows(conn, "dim_artista"),
        "total_generos":  count_rows(conn, "dim_genero"),
        "total_albumes":  count_rows(conn, "dim_album"),
        "total_streams":  count_rows(conn, "fact_streaming"),
        "active_users":   count_rows(conn, "dim_usuario"),
        "total_playlists": count_rows(conn, "dim_playlist"),
    }
    result["total_events"] = sum(count_rows(conn, table) for table in ACTIVITY_FACT_TABLES)

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
        pass

    # Averages from dim_track (audio features live there now)
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
            result["promedio_popularidad"]  = round(float(row[0] or 0), 1)
            result["promedio_energy"]       = round(float(row[1] or 0), 4)
            result["promedio_danceability"] = round(float(row[2] or 0), 4)
            result["promedio_valence"]      = round(float(row[3] or 0), 4)
            result["promedio_tempo"]        = round(float(row[4] or 0), 1)
    except Exception:
        result["promedio_popularidad"]  = 0.0
        result["promedio_energy"]       = 0.0
        result["promedio_danceability"] = 0.0
        result["promedio_valence"]      = 0.0
        result["promedio_tempo"]        = 0.0

    return result


def get_energia_distribution(conn: duckdb.DuckDBPyConnection) -> List[Dict[str, Any]]:
    rows, _ = fetch_rows(
        conn, "agg_distribucion_energia",
        columns=[
            "rango_energia", "cantidad_tracks",
            "popularidad_promedio", "danceability_promedio",
        ],
        order_by="rango_energia",
    )
    return rows


def get_top_tracks_by_popularity(
    conn: duckdb.DuckDBPyConnection, limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Top tracks by popularity using dim_track (audio features are stored there)
    joined with dim_artista for the artist name.
    """
    rows = conn.execute(f"""
        SELECT
            dt.id_track,
            dt.nombre_track,
            COALESCE(da.nombre_artista, '—') AS nombre_artista,
            dt.id_artista,
            dt.id_genero,
            dt.popularity,
            dt.energy,
            dt.danceability,
            dt.valence
        FROM dim_track dt
        LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
        WHERE dt.popularity IS NOT NULL
        ORDER BY dt.popularity DESC
        LIMIT {int(limit)}
    """).fetchall()

    cols = [
        "id_track", "nombre_track", "nombre_artista", "id_artista",
        "id_genero", "popularity", "energy", "danceability", "valence",
    ]
    return [dict(zip(cols, row)) for row in rows]


def get_last_loads(
    conn: duckdb.DuckDBPyConnection, limit: int = 5
) -> List[Dict[str, Any]]:
    rows, _ = fetch_rows(
        conn, "ctl_carga_dataset",
        columns=["id_carga", "fecha_carga", "modo", "registros_nuevos", "total_raw", "estado"],
        order_by="id_carga DESC",
        limit=limit,
    )
    result = []
    for r in rows:
        result.append({
            "id_carga":         r.get("id_carga"),
            "fecha_carga":      str(r["fecha_carga"]) if r.get("fecha_carga") else None,
            "modo":             r.get("modo", "—"),
            "registros_nuevos": r.get("registros_nuevos", 0),
            "total_raw":        r.get("total_raw", 0),
            "estado":           r.get("estado", "—"),
        })
    return result


def get_catalog_growth(
    conn: duckdb.DuckDBPyConnection,
    months: int = 12,
) -> List[Dict[str, Any]]:
    """
    Catalog growth series from ctl_carga_dataset (real warehouse loads).
    Falls back to current dim_track count if no load history exists.
    """
    months = max(3, min(int(months), 24))
    current = count_rows(conn, "dim_track")

    try:
        rows = conn.execute("""
            SELECT
                fecha_carga,
                COALESCE(total_raw, 0) AS total_raw,
                COALESCE(registros_nuevos, 0) AS registros_nuevos
            FROM ctl_carga_dataset
            ORDER BY fecha_carga ASC
        """).fetchall()
    except Exception:
        rows = []

    points: List[Dict[str, Any]] = []
    if rows:
        for r in rows:
            fecha = str(r[0]) if r[0] else ""
            label = fecha[:7] if len(fecha) >= 7 else fecha
            points.append({
                "label": label,
                "total": int(r[1] or 0),
                "added": int(r[2] or 0),
            })
        if points and points[-1]["total"] < current:
            points.append({
                "label": "actual",
                "total": current,
                "added": max(0, current - points[-1]["total"]),
            })
    else:
        # No load history — single real snapshot
        points.append({"label": "actual", "total": current, "added": 0})

    # Normalize to requested length (pad or trim)
    if len(points) > months:
        points = points[-months:]
    while len(points) < months and len(points) >= 1:
        first = points[0]
        prev_total = max(0, first["total"] - first.get("added", 0))
        points.insert(0, {
            "label": "…",
            "total": prev_total,
            "added": 0,
        })

    values = [p["total"] for p in points]
    max_v = max(values) if values else 1
    return [
        {**p, "normalized": round((p["total"] / max_v) * 100, 1) if max_v else 0}
        for p in points
    ]


def get_synthetic_limits() -> Dict[str, Any]:
    """Límites expuestos al frontend para validación antes de generar."""
    return {
        "max_target_total": MAX_TARGET_TOTAL,
        "max_create_per_run": MAX_CREATE_PER_RUN,
        "warn_create_above": WARN_CREATE_ABOVE,
        "batch_size": SYNTHETIC_BATCH_SIZE,
        "duckdb_note": (
            "DuckDB soporta millones de eventos. El catálogo musical se mantiene real; "
            "lo sintético se genera en streams, búsquedas, favoritos, playlists y sesiones."
        ),
    }


def _activity_total(conn: duckdb.DuckDBPyConnection) -> int:
    return sum(count_rows(conn, table) for table in ACTIVITY_FACT_TABLES)


def _purge_synthetic_catalog(conn: duckdb.DuckDBPyConnection) -> int:
    """Remove old syn_% track clones so the visible catalog stays real."""
    if count_rows(conn, "dim_track") == 0:
        return 0
    before = count_rows(conn, "dim_track")
    conn.execute("DELETE FROM dim_track WHERE spotify_track_id LIKE 'syn_%'")
    return before - count_rows(conn, "dim_track")


def _ensure_activity_dimensions(conn: duckdb.DuckDBPyConnection, target_total: int) -> Dict[str, int]:
    """Generate synthetic users/playlists only; musical dimensions remain real."""
    user_count = max(5_000, min(50_000, target_total // 80))
    playlist_count = max(800, min(20_000, target_total // 250))

    conn.execute("DELETE FROM dim_usuario WHERE id_usuario > 1")
    conn.execute(f"""
        INSERT INTO dim_usuario (id_usuario, nombre, email, pais, plan)
        SELECT 1 + i,
               'User_' || LPAD(CAST(i AS VARCHAR), 5, '0'),
               'user' || i || '@voxmetrik.io',
               (ARRAY['EC','US','MX','CO','AR','ES','CL','PE'])[1 + (i % 8)],
               (ARRAY['free','premium','family','student'])[1 + (i % 4)]
        FROM generate_series(1, {user_count - 1}) AS t(i)
    """)

    conn.execute("DELETE FROM dim_playlist WHERE id_playlist > 1")
    conn.execute(f"""
        INSERT INTO dim_playlist (id_playlist, nombre, id_usuario, descripcion, publica)
        SELECT 1 + i,
               (ARRAY['Daily Mix','Discover Weekly','Release Radar','Chill Vibes',
                      'Workout Hits','Focus Flow','Top 50','Road Trip'])[1 + (i % 8)] || ' ' || i,
               1 + (i % {user_count}),
               'Synthetic behavior playlist over real catalog',
               (i % 3) <> 0
        FROM generate_series(1, {playlist_count - 1}) AS t(i)
    """)
    return {"users": user_count, "playlists": playlist_count}


def _split_activity_counts(target_total: int) -> Dict[str, int]:
    counts = {
        "fact_streaming": int(target_total * 0.65),
        "fact_user_activity": int(target_total * 0.12),
        "fact_playlist_activity": int(target_total * 0.08),
        "fact_favorites": int(target_total * 0.06),
        "fact_searches": int(target_total * 0.05),
    }
    counts["fact_stream_sessions"] = target_total - sum(counts.values())
    return counts


def _real_track_count(conn: duckdb.DuckDBPyConnection) -> int:
    return int(conn.execute("""
        SELECT COUNT(*) FROM dim_track
        WHERE spotify_track_id IS NULL OR spotify_track_id NOT LIKE 'syn_%'
    """).fetchone()[0])


def _replace_fact_streaming(conn: duckdb.DuckDBPyConnection, n: int) -> None:
    conn.execute("DELETE FROM fact_streaming")
    if n <= 0:
        return
    track_count = _real_track_count(conn)
    user_count = max(count_rows(conn, "dim_usuario"), 1)
    playlist_count = max(count_rows(conn, "dim_playlist"), 1)
    conn.execute(f"""
        INSERT INTO fact_streaming (
            id_streaming, id_track, id_usuario, id_tiempo, id_playlist,
            streams, duracion_ms, completado, skipped, device_type, platform,
            session_id, hour_of_day, fecha_evento
        )
        WITH tracks AS (
            SELECT id_track, duration_ms, popularity,
                   ROW_NUMBER() OVER (ORDER BY id_track) rn, COUNT(*) OVER () total
            FROM dim_track
            WHERE spotify_track_id IS NULL OR spotify_track_id NOT LIKE 'syn_%'
        ),
        tiempo AS (
            SELECT id_tiempo, fecha, ROW_NUMBER() OVER (ORDER BY fecha DESC) rn
            FROM dim_tiempo WHERE fecha <= CURRENT_DATE
        )
        SELECT g.i, t.id_track, 1 + (g.i % {user_count}), ti.id_tiempo,
               1 + (g.i % {playlist_count}),
               1 + (COALESCE(t.popularity, 0) / 20), COALESCE(t.duration_ms, 180000),
               (g.i % 100) >= 18, (g.i % 100) < 22,
               (ARRAY['mobile','desktop','tablet','smart_tv','web'])[1 + (g.i % 5)],
               (ARRAY['ios','android','web','desktop','car'])[1 + (g.i % 5)],
               1 + (g.i % GREATEST(1, CAST({n} / 20 AS INTEGER))), g.i % 24,
               CAST(ti.fecha AS TIMESTAMP) + (g.i % 86400) * INTERVAL '1' SECOND
        FROM generate_series(1, {n}) g(i)
        JOIN tracks t ON t.rn = ((g.i - 1) % {track_count}) + 1
        JOIN tiempo ti ON ti.rn = 1 + (g.i % 90)
    """)


def _replace_fact_user_activity(conn: duckdb.DuckDBPyConnection, n: int) -> None:
    conn.execute("DELETE FROM fact_user_activity")
    if n <= 0:
        return
    track_count = _real_track_count(conn)
    user_count = max(count_rows(conn, "dim_usuario"), 1)
    conn.execute(f"""
        INSERT INTO fact_user_activity (
            id_activity, id_usuario, id_track, id_tiempo, action_type,
            device_type, duration_ms, fecha_evento
        )
        WITH tracks AS (
            SELECT id_track, ROW_NUMBER() OVER (ORDER BY id_track) rn
            FROM dim_track
            WHERE spotify_track_id IS NULL OR spotify_track_id NOT LIKE 'syn_%'
        ),
        tiempo AS (
            SELECT id_tiempo, ROW_NUMBER() OVER (ORDER BY fecha DESC) rn
            FROM dim_tiempo WHERE fecha <= CURRENT_DATE
        )
        SELECT i, 1 + (i % {user_count}), t.id_track, ti.id_tiempo,
               (ARRAY['play','pause','skip','like','share','add_playlist'])[1 + (i % 6)],
               (ARRAY['mobile','desktop','web'])[1 + (i % 3)],
               30000 + (i % 240000),
               CURRENT_TIMESTAMP - (i % 604800) * INTERVAL '1' SECOND
        FROM generate_series(1, {n}) g(i)
        JOIN tracks t ON t.rn = ((i - 1) % {track_count}) + 1
        JOIN tiempo ti ON ti.rn = 1 + (i % 90)
    """)


def _replace_fact_playlist_activity(conn: duckdb.DuckDBPyConnection, n: int) -> None:
    conn.execute("DELETE FROM fact_playlist_activity")
    if n <= 0:
        return
    track_count = _real_track_count(conn)
    user_count = max(count_rows(conn, "dim_usuario"), 1)
    playlist_count = max(count_rows(conn, "dim_playlist"), 1)
    conn.execute(f"""
        INSERT INTO fact_playlist_activity (
            id_activity, id_playlist, id_usuario, id_track, action_type, fecha_evento
        )
        WITH tracks AS (
            SELECT id_track, ROW_NUMBER() OVER (ORDER BY id_track) rn
            FROM dim_track
            WHERE spotify_track_id IS NULL OR spotify_track_id NOT LIKE 'syn_%'
        )
        SELECT i, 1 + (i % {playlist_count}), 1 + (i % {user_count}), t.id_track,
               (ARRAY['add','remove','play','follow','share'])[1 + (i % 5)],
               CURRENT_TIMESTAMP - (i % 2592000) * INTERVAL '1' SECOND
        FROM generate_series(1, {n}) g(i)
        JOIN tracks t ON t.rn = ((i - 1) % {track_count}) + 1
    """)


def _replace_fact_favorites(conn: duckdb.DuckDBPyConnection, n: int) -> None:
    conn.execute("DELETE FROM fact_favorites")
    if n <= 0:
        return
    track_count = _real_track_count(conn)
    user_count = max(count_rows(conn, "dim_usuario"), 1)
    conn.execute(f"""
        INSERT INTO fact_favorites (id_favorite, id_usuario, id_track, id_tiempo, fecha_evento)
        WITH tracks AS (
            SELECT id_track, ROW_NUMBER() OVER (ORDER BY id_track) rn
            FROM dim_track
            WHERE spotify_track_id IS NULL OR spotify_track_id NOT LIKE 'syn_%'
        ),
        tiempo AS (
            SELECT id_tiempo, ROW_NUMBER() OVER (ORDER BY fecha DESC) rn
            FROM dim_tiempo WHERE fecha <= CURRENT_DATE
        )
        SELECT i, 1 + (i % {user_count}), t.id_track, ti.id_tiempo,
               CURRENT_TIMESTAMP - (i % 7776000) * INTERVAL '1' SECOND
        FROM generate_series(1, {n}) g(i)
        JOIN tracks t ON t.rn = ((i - 1) % {track_count}) + 1
        JOIN tiempo ti ON ti.rn = 1 + (i % 60)
    """)


def _replace_fact_searches(conn: duckdb.DuckDBPyConnection, n: int) -> None:
    conn.execute("DELETE FROM fact_searches")
    if n <= 0:
        return
    user_count = max(count_rows(conn, "dim_usuario"), 1)
    conn.execute(f"""
        INSERT INTO fact_searches (id_search, id_usuario, query_text, results_count, id_tiempo, fecha_evento)
        WITH tiempo AS (
            SELECT id_tiempo, ROW_NUMBER() OVER (ORDER BY fecha DESC) rn
            FROM dim_tiempo WHERE fecha <= CURRENT_DATE
        )
        SELECT i, 1 + (i % {user_count}),
               (ARRAY['bad bunny','taylor swift','drake','reggaeton','rock','pop','chill',
                      'workout','latin hits','indie','focus','party','electronic','jazz',
                      'kpop','metal','hip hop','oldies','discover weekly','sad songs'])[1 + (i % 20)],
               5 + (i % 95), ti.id_tiempo,
               CURRENT_TIMESTAMP - (i % 1209600) * INTERVAL '1' SECOND
        FROM generate_series(1, {n}) g(i)
        JOIN tiempo ti ON ti.rn = 1 + (i % 30)
    """)


def _replace_fact_stream_sessions(conn: duckdb.DuckDBPyConnection, n: int) -> None:
    conn.execute("DELETE FROM fact_stream_sessions")
    if n <= 0:
        return
    user_count = max(count_rows(conn, "dim_usuario"), 1)
    conn.execute(f"""
        INSERT INTO fact_stream_sessions (
            id_session, id_usuario, device_type, platform,
            session_start, session_end, tracks_played, total_ms, skips
        )
        SELECT i, 1 + (i % {user_count}),
               (ARRAY['mobile','desktop','tablet','web','smart_tv'])[1 + (i % 5)],
               (ARRAY['ios','android','web','desktop','car'])[1 + (i % 5)],
               CURRENT_TIMESTAMP - (i % 604800) * INTERVAL '1' SECOND,
               CURRENT_TIMESTAMP - (i % 604800) * INTERVAL '1' SECOND + (1800 + i % 5400) * INTERVAL '1' SECOND,
               3 + (i % 25), 180000 + (i % 3600000), i % 8
        FROM generate_series(1, {n}) g(i)
    """)


def _refresh_enterprise_aggregates(conn: duckdb.DuckDBPyConnection) -> None:
    """Rebuild derived agg_* tables after regenerating synthetic activity."""
    root = Path(__file__).resolve().parents[5]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from elt.transform.enterprise_analytics import (  # local project module
        apply_enterprise_schema,
        _build_agg_daily_streams,
        _build_agg_user_activity,
        _build_agg_genre_trends,
        _build_agg_artist_growth,
        _build_agg_platform_usage,
        _build_agg_top_playlists,
        _build_agg_recommendation_scores,
        _build_agg_user_engagement,
        _build_agg_streaming_devices,
        _build_agg_recent_activity,
        _build_agg_top_searches,
        _build_agg_user_retention,
    )

    apply_enterprise_schema(conn)
    _build_agg_daily_streams(conn)
    _build_agg_user_activity(conn)
    _build_agg_genre_trends(conn)
    _build_agg_artist_growth(conn)
    _build_agg_platform_usage(conn)
    _build_agg_top_playlists(conn)
    _build_agg_recommendation_scores(conn)
    _build_agg_user_engagement(conn)
    _build_agg_streaming_devices(conn)
    _build_agg_recent_activity(conn)
    _build_agg_top_searches(conn)
    _build_agg_user_retention(conn)


def generate_synthetic_activity(
    conn: duckdb.DuckDBPyConnection,
    *,
    target_total: int | None = None,
    multiplier: int | None = None,
) -> Dict[str, Any]:
    """
    Generate high-volume behavioral activity over real catalog rows.

    Musical catalog tables (dim_track, dim_artista, dim_album, dim_genero) stay real.
    Synthetic data is limited to users/playlists and activity facts.
    """
    if target_total is None and multiplier is None:
        raise ValueError("provide target_total or multiplier")

    purged_tracks = _purge_synthetic_catalog(conn)
    real_tracks = _real_track_count(conn)
    if real_tracks == 0:
        raise ValueError(
            "No hay tracks reales en el warehouse. Importa primero desde PocketBase "
            "(POST /api/v1/stats/import o python scripts/import_from_pocketbase.py)."
        )

    before = _activity_total(conn)
    if target_total is None:
        if multiplier is None or multiplier < 1:
            raise ValueError("multiplier must be >= 1")
        target_total = before * multiplier

    if target_total < 1:
        raise ValueError("target_total must be >= 1")
    if target_total > MAX_TARGET_TOTAL:
        raise ValueError(
            f"target_total cannot exceed {MAX_TARGET_TOTAL:,} "
            f"(DuckDB límite del proyecto; pediste {target_total:,})"
        )

    created = max(0, target_total - before)
    if created == 0:
        return {
            "before": before,
            "after": before,
            "created": 0,
            "target_total": target_total,
            "source_rows": real_tracks,
            "track_total": real_tracks,
            "purged_synthetic_tracks": purged_tracks,
            "batches": 0,
            "warning": None,
        }

    if created > MAX_CREATE_PER_RUN:
        raise ValueError(
            f"cannot create more than {MAX_CREATE_PER_RUN:,} rows in one run "
            f"(requested {created:,}). Usa varias ejecuciones (+100K) o baja el objetivo."
        )

    dimensions = _ensure_activity_dimensions(conn, target_total)
    activity_counts = _split_activity_counts(target_total)
    _replace_fact_streaming(conn, activity_counts["fact_streaming"])
    _replace_fact_user_activity(conn, activity_counts["fact_user_activity"])
    _replace_fact_playlist_activity(conn, activity_counts["fact_playlist_activity"])
    _replace_fact_favorites(conn, activity_counts["fact_favorites"])
    _replace_fact_searches(conn, activity_counts["fact_searches"])
    _replace_fact_stream_sessions(conn, activity_counts["fact_stream_sessions"])
    _refresh_enterprise_aggregates(conn)

    after = _activity_total(conn)
    created = max(0, after - before)
    warning = "large" if created >= WARN_CREATE_ABOVE else None

    try:
        id_carga = conn.execute(
            "SELECT COALESCE(MAX(id_carga), 0) + 1 FROM ctl_carga_dataset"
        ).fetchone()[0]
        conn.execute(
            """
            INSERT INTO ctl_carga_dataset
                (id_carga, fecha_carga, modo, registros_nuevos, total_raw, estado)
            VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, 'OK')
            """,
            [id_carga, f"synthetic_activity_target_{target_total}", created, after],
        )
    except Exception:
        pass

    return {
        "before": before,
        "after": after,
        "created": created,
        "target_total": target_total,
        "source_rows": real_tracks,
        "track_total": real_tracks,
        "purged_synthetic_tracks": purged_tracks,
        "dimensions": dimensions,
        "activity_counts": activity_counts,
        "batches": max(1, (target_total + SYNTHETIC_BATCH_SIZE - 1) // SYNTHETIC_BATCH_SIZE),
        "warning": warning,
    }


# Backwards-compatible name for existing route/client code.
generate_synthetic_tracks = generate_synthetic_activity