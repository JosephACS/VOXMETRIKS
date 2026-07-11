"""Trending modules — today, week, genre, fast-growing, most saved."""

from __future__ import annotations

from typing import Any, Dict, List

import duckdb

from ._helpers import table_exists_conn


def build_trending_modules(conn: duckdb.DuckDBPyConnection, *, limit: int = 12) -> Dict[str, Any]:
    return {
        "trending_today": _trending_today(conn, limit),
        "trending_week": _trending_week(conn, limit),
        "trending_by_genre": _trending_by_genre(conn, limit=8),
        "fast_growing_artists": _fast_growing_artists(conn, limit=8),
        "most_saved_tracks": _most_saved(conn, limit),
    }


def _trending_today(conn: duckdb.DuckDBPyConnection, limit: int) -> List[Dict[str, Any]]:
    if not table_exists_conn(conn, "agg_daily_streams"):
        return _fallback_popular(conn, limit)
    return _fallback_popular(conn, limit)


def _trending_week(conn: duckdb.DuckDBPyConnection, limit: int) -> List[Dict[str, Any]]:
    if table_exists_conn(conn, "agg_recommendation_scores"):
        rows = conn.execute(
            """
            SELECT id_track, nombre_track, popularity, recommendation_score
            FROM agg_recommendation_scores
            ORDER BY recommendation_score DESC
            LIMIT ?
            """,
            [limit],
        ).fetchall()
        return [
            {
                "id_track": int(r[0]),
                "nombre_track": r[1],
                "popularity": r[2],
                "score": r[3],
            }
            for r in rows
        ]
    return _fallback_popular(conn, limit)


def _trending_by_genre(conn: duckdb.DuckDBPyConnection, limit: int) -> List[Dict[str, Any]]:
    if not table_exists_conn(conn, "agg_genre_trends"):
        return []
    rows = conn.execute(
        """
        SELECT id_genero, nombre_genero, streams_7d, trend_pct
        FROM agg_genre_trends
        ORDER BY trend_pct DESC NULLS LAST
        LIMIT ?
        """,
        [limit],
    ).fetchall()
    return [
        {
            "id_genero": int(r[0]),
            "nombre_genero": r[1],
            "streams_7d": int(r[2] or 0),
            "trend_pct": float(r[3] or 0),
        }
        for r in rows
    ]


def _fast_growing_artists(conn: duckdb.DuckDBPyConnection, limit: int) -> List[Dict[str, Any]]:
    if not table_exists_conn(conn, "agg_artist_growth"):
        return []
    rows = conn.execute(
        """
        SELECT id_artista, nombre_artista, growth_pct, streams_7d
        FROM agg_artist_growth
        ORDER BY growth_pct DESC NULLS LAST
        LIMIT ?
        """,
        [limit],
    ).fetchall()
    return [
        {
            "id_artista": int(r[0]),
            "nombre_artista": r[1],
            "growth_pct": float(r[2] or 0),
            "streams_7d": int(r[3] or 0),
        }
        for r in rows
    ]


def _most_saved(conn: duckdb.DuckDBPyConnection, limit: int) -> List[Dict[str, Any]]:
    try:
        rows = conn.execute(
            """
            SELECT dt.id_track, dt.nombre_track, da.nombre_artista, COUNT(*) AS saves
            FROM app_favorite f
            INNER JOIN dim_track dt ON dt.id_track = f.track_id
            LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
            GROUP BY dt.id_track, dt.nombre_track, da.nombre_artista
            ORDER BY saves DESC
            LIMIT ?
            """,
            [limit],
        ).fetchall()
        return [
            {
                "id_track": int(r[0]),
                "nombre_track": r[1],
                "nombre_artista": r[2],
                "saves": int(r[3]),
            }
            for r in rows
        ]
    except Exception:
        return []


def _fallback_popular(conn: duckdb.DuckDBPyConnection, limit: int) -> List[Dict[str, Any]]:
    if not table_exists_conn(conn, "agg_tracks_populares"):
        return []
    rows = conn.execute(
        """
        SELECT id_track, nombre_track, nombre_artista, popularity
        FROM agg_tracks_populares
        ORDER BY popularity DESC NULLS LAST
        LIMIT ?
        """,
        [limit],
    ).fetchall()
    return [
        {
            "id_track": int(r[0]),
            "nombre_track": r[1],
            "nombre_artista": r[2],
            "popularity": r[3],
        }
        for r in rows
    ]
