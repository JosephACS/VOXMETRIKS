"""COMPATIBILITY_ADAPTER — Spec 014 D2. Prefer catalog + engagement route packages."""

from app.packages.catalog.routes import artists_router, genres_router, tracks_router
from app.packages.engagement.routes import dashboard_router, favorites_router, playlists_router

__all__ = [
    "artists_router",
    "genres_router",
    "tracks_router",
    "playlists_router",
    "favorites_router",
    "dashboard_router",
]
