from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import analytics, dashboard, recommendations, search, streaming, users

api_router = APIRouter(prefix="/api/v2")

api_router.include_router(dashboard.router)
api_router.include_router(users.router)
api_router.include_router(streaming.router)
api_router.include_router(analytics.router)
api_router.include_router(search.router)
api_router.include_router(recommendations.router)
