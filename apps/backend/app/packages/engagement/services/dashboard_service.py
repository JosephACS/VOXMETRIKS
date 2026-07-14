"""BFF payload for the streaming home dashboard (single round-trip)."""

from __future__ import annotations

from typing import Any, Dict, Optional

import duckdb

from app.packages.analytics.services.stats_service import (
    get_catalog_growth,
    get_summary,
    get_top_tracks_by_popularity,
)
from app.packages.catalog.services.artist_service import get_artists
from app.packages.catalog.services.genre_service import get_genre_stats
from app.packages.catalog.services.playlist_catalog_service import (
    list_popular_catalog_playlists,
)
from app.packages.catalog.services.track_service import get_tracks
from app.packages.engagement.services.playlist_service import list_playlists


def get_home_feed(
    conn: duckdb.DuckDBPyConnection,
    *,
    user_id: Optional[int] = None,
    discover_page: int = 1,
    discover_limit: int = 24,
    top_limit: int = 24,
    growth_months: int = 12,
    genre_limit: int = 8,
    artist_limit: int = 8,
    playlist_limit: int = 6,
) -> Dict[str, Any]:
    """Aggregate home rails in one DuckDB connection."""
    page = max(1, min(int(discover_page), 200))
    discover_rows, discover_total = get_tracks(conn, page=page, limit=discover_limit)
    genre_rows, _ = get_genre_stats(conn, page=1, limit=genre_limit)
    artist_rows, _ = get_artists(conn, page=1, limit=artist_limit)
    # Home rail = popular warehouse playlists (not the user's personal lists).
    playlists = list_popular_catalog_playlists(conn, limit=playlist_limit)
    my_playlist_count = 0
    if user_id is not None:
        my_playlist_count = len(list_playlists(conn, user_id))

    return {
        "summary": get_summary(conn),
        "top_tracks": get_top_tracks_by_popularity(conn, limit=top_limit),
        "catalog_growth": get_catalog_growth(conn, months=growth_months),
        "discover": {
            "page": page,
            "limit": discover_limit,
            "total": discover_total,
            "items": discover_rows,
        },
        "genres": genre_rows,
        "artists": artist_rows,
        "playlists": playlists,
        "my_playlist_count": my_playlist_count,
    }
