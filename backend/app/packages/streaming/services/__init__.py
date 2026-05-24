"""
Streaming services - Business logic for Artists, Genres, and Tracks
"""

from .artist_service import (
    get_artists, get_artist_by_id, get_artist_stats, get_top_artists,
    create_artist, update_artist, delete_artist,
)
from .genre_service import (
    get_genres, get_genre_by_id, get_genre_stats,
    create_genre, update_genre, delete_genre,
)
from .track_service import (
    get_tracks, get_track_by_id, get_track_features,
    create_track, update_track, delete_track,
)

__all__ = [
    # Artists
    "get_artists", "get_artist_by_id", "get_artist_stats", "get_top_artists",
    "create_artist", "update_artist", "delete_artist",
    # Genres
    "get_genres", "get_genre_by_id", "get_genre_stats",
    "create_genre", "update_genre", "delete_genre",
    # Tracks
    "get_tracks", "get_track_by_id", "get_track_features",
    "create_track", "update_track", "delete_track",
]
