"""Synthetic dimension helpers and aggregate refresh."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict

import duckdb

from app.core.query_helpers import count_rows


def purge_synthetic_catalog(conn: duckdb.DuckDBPyConnection) -> int:
    """Remove old syn_% track clones so the visible catalog stays real."""
    if count_rows(conn, "dim_track") == 0:
        return 0
    before = count_rows(conn, "dim_track")
    conn.execute("DELETE FROM dim_track WHERE spotify_track_id LIKE 'syn_%'")
    return before - count_rows(conn, "dim_track")


def ensure_activity_dimensions(conn: duckdb.DuckDBPyConnection, target_total: int) -> Dict[str, int]:
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


def split_activity_counts(target_total: int) -> Dict[str, int]:
    counts = {
        "fact_streaming": int(target_total * 0.65),
        "fact_user_activity": int(target_total * 0.12),
        "fact_playlist_activity": int(target_total * 0.08),
        "fact_favorites": int(target_total * 0.06),
        "fact_searches": int(target_total * 0.05),
    }
    counts["fact_stream_sessions"] = target_total - sum(counts.values())
    return counts


def refresh_enterprise_aggregates(conn: duckdb.DuckDBPyConnection) -> None:
    """Rebuild derived agg_* tables after regenerating synthetic activity."""
    root = Path(__file__).resolve().parents[6]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from elt.transform.enterprise_analytics import (
        _build_agg_artist_growth,
        _build_agg_daily_streams,
        _build_agg_genre_trends,
        _build_agg_platform_usage,
        _build_agg_recent_activity,
        _build_agg_recommendation_scores,
        _build_agg_streaming_devices,
        _build_agg_top_playlists,
        _build_agg_top_searches,
        _build_agg_user_activity,
        _build_agg_user_engagement,
        _build_agg_user_retention,
        apply_enterprise_schema,
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
