from __future__ import annotations

from app.services.analytics_service import AnalyticsService
from app.services.dashboard_service import DashboardService
from app.services.health_service import HealthService
from app.services.recommendation_service import RecommendationService
from app.services.search_service import SearchService
from app.services.streaming_service import StreamingService
from app.services.user_service import UserService


def get_analytics_service() -> AnalyticsService:
    return AnalyticsService()


def get_user_service() -> UserService:
    return UserService()


def get_streaming_service() -> StreamingService:
    return StreamingService()


def get_search_service() -> SearchService:
    return SearchService()


def get_recommendation_service() -> RecommendationService:
    return RecommendationService()


def get_dashboard_service() -> DashboardService:
    return DashboardService()


def get_health_service() -> HealthService:
    return HealthService()
