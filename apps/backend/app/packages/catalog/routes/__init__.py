from .artists import router as artists_router
from .genres import router as genres_router
from .playlists import router as catalog_playlists_router
from .tracks import router as tracks_router

__all__ = ["artists_router", "genres_router", "tracks_router", "catalog_playlists_router"]
