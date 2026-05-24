"""
Streaming routes - API endpoints for Artists, Genres, and Tracks
"""

from .artists import router as artists_router
from .genres import router as genres_router
from .tracks import router as tracks_router

__all__ = ["artists_router", "genres_router", "tracks_router"]
