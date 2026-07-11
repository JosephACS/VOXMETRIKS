"""
Streaming routes - API endpoints for Artists, Genres, and Tracks
"""

from .artists import router as artists_router
from .dashboard import router as dashboard_router
from .favorites import router as favorites_router
from .genres import router as genres_router
from .playlists import router as playlists_router
from .tracks import router as tracks_router

__all__ = [
    "artists_router", "genres_router", "tracks_router",
    "playlists_router", "favorites_router", "dashboard_router",
]
