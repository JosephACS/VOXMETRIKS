from .artists import router as artists_router
from .genres  import router as genres_router
from .tracks  import router as tracks_router
from .stats   import router as stats_router

__all__ = ["artists_router", "genres_router", "tracks_router", "stats_router"]
