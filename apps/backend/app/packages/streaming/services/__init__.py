"""COMPATIBILITY_ADAPTER — Spec 014 D2. Prefer catalog / engagement services.

Audio modules remain under ``app.packages.streaming.services.audio``.
"""

from app.packages.catalog.services.artist_service import (  # noqa: F401
    create_artist,
    delete_artist,
    get_artist_by_id,
    get_artist_stats,
    get_artists,
    get_top_artists,
    update_artist,
)
from app.packages.catalog.services.genre_service import (  # noqa: F401
    create_genre,
    delete_genre,
    get_genre_by_id,
    get_genre_stats,
    get_genres,
    update_genre,
)
from app.packages.catalog.services.track_service import (  # noqa: F401
    create_track,
    delete_track,
    get_track_by_id,
    get_track_detail,
    get_track_features,
    get_tracks,
    get_tracks_cursor,
    search_tracks,
    update_track,
)

__all__ = [
    "get_artists",
    "get_artist_by_id",
    "get_artist_stats",
    "get_top_artists",
    "create_artist",
    "update_artist",
    "delete_artist",
    "get_genres",
    "get_genre_by_id",
    "get_genre_stats",
    "create_genre",
    "update_genre",
    "delete_genre",
    "get_tracks",
    "get_tracks_cursor",
    "get_track_by_id",
    "get_track_detail",
    "get_track_features",
    "search_tracks",
    "create_track",
    "update_track",
    "delete_track",
]
