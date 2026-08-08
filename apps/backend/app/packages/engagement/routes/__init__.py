from .dashboard import router as dashboard_router
from .favorites import router as favorites_router
from .listening_activity import router as listening_activity_router
from .listening_history import router as listening_history_router
from .playlists import router as playlists_router

__all__ = [
    "playlists_router",
    "favorites_router",
    "listening_history_router",
    "listening_activity_router",
    "dashboard_router",
]
