from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.routes._status import module_status
from app.api.deps import get_analytics_service
from app.models.schemas import (
    DailyStreamsResponse,
    GenresAnalyticsResponse,
    PlatformUsageResponse,
    TopArtistsResponse,
    TopTracksResponse,
)
from app.packages.identity.services.auth_deps import require_user_id
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/status", summary="Analytics module status")
def analytics_status():
    return module_status("analytics")


@router.get(
    "/daily-streams",
    response_model=DailyStreamsResponse,
    summary="Latest daily streaming KPIs",
)
def daily_streams(
    _user: int = Depends(require_user_id),
    service: AnalyticsService = Depends(get_analytics_service),
):
    return service.get_daily_streams()


@router.get(
    "/top-artists",
    response_model=TopArtistsResponse,
    summary="Top artists by 7-day streams",
)
def top_artists(
    limit: int = Query(20, ge=1, le=100),
    _user: int = Depends(require_user_id),
    service: AnalyticsService = Depends(get_analytics_service),
):
    return service.get_top_artists(limit=limit)


@router.get(
    "/top-tracks",
    response_model=TopTracksResponse,
    summary="Top tracks by streams and engagement",
)
def top_tracks(
    limit: int = Query(20, ge=1, le=100),
    _user: int = Depends(require_user_id),
    service: AnalyticsService = Depends(get_analytics_service),
):
    return service.get_top_tracks(limit=limit)


@router.get(
    "/genres",
    response_model=GenresAnalyticsResponse,
    summary="Genre popularity and energy aggregates",
)
def genres(
    limit: int = Query(50, ge=1, le=200),
    _user: int = Depends(require_user_id),
    service: AnalyticsService = Depends(get_analytics_service),
):
    return service.get_genres(limit=limit)


@router.get(
    "/platform-usage",
    response_model=PlatformUsageResponse,
    summary="Platform and device usage share",
)
def platform_usage(
    limit: int = Query(20, ge=1, le=100),
    _user: int = Depends(require_user_id),
    service: AnalyticsService = Depends(get_analytics_service),
):
    return service.get_platform_usage(limit=limit)
