"""Trending tracks, genres, and daily stream series."""

from __future__ import annotations

import logging
from typing import Any, Dict

import duckdb

from app.core.query_helpers import fetch_rows

from ..stats.catalog import get_top_tracks_by_popularity

logger = logging.getLogger(__name__)


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
        logger.exception("get_trending_analytics: agg_recommendation_scores unavailable; using popularity fallback")
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
        logger.exception("get_trending_analytics: agg_genre_trends unavailable")

    daily = []
    try:
        rows, _ = fetch_rows(
            conn, "agg_daily_streams",
            columns=["fecha", "total_streams", "unique_users", "skip_count"],
            order_by="fecha ASC", limit=30,
        )
        daily = [{**r, "fecha": str(r.get("fecha", ""))} for r in rows]
    except Exception:
        logger.exception("get_trending_analytics: agg_daily_streams unavailable")

    avg_score = 0.0
    if top_tracks:
        avg_score = round(sum(t.get("recommendation_score", 0) or 0 for t in top_tracks) / len(top_tracks), 2)

    return {
        "top_tracks": top_tracks,
        "top_genres": genre_trends,
        "daily_streams": daily,
        "trending_score_avg": avg_score,
    }
