from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import dashboards, enterprise_analytics, enterprise_users, health, tracks
from app.core.config import get_settings

settings = get_settings()

enterprise_v1_router = APIRouter(prefix=settings.api_prefix)

enterprise_v1_router.include_router(dashboards.router)
enterprise_v1_router.include_router(enterprise_analytics.router)
enterprise_v1_router.include_router(tracks.router)
enterprise_v1_router.include_router(enterprise_users.router)
enterprise_v1_router.include_router(health.router)

__all__ = ["enterprise_v1_router", "health"]
