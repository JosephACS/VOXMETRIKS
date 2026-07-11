from __future__ import annotations

from app.services.enterprise_analytics_service import EnterpriseAnalyticsService
from app.services.enterprise_user_service import EnterpriseUserService
from app.services.track_service import TrackService


def get_analytics_service() -> EnterpriseAnalyticsService:
    return EnterpriseAnalyticsService()


def get_user_service() -> EnterpriseUserService:
    return EnterpriseUserService()


def get_track_service() -> TrackService:
    return TrackService()
