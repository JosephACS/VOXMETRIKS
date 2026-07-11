from .dashboard import router as dashboard_router
from .favorites import router as favorites_router
from .playlists import router as playlists_router

__all__ = ["playlists_router", "favorites_router", "dashboard_router"]
