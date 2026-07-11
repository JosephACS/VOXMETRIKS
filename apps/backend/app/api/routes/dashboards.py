from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps_enterprise import get_analytics_service
from app.packages.identity.services.auth_deps import require_user_id
from app.schemas.common import success_response
from app.services.enterprise_analytics_service import EnterpriseAnalyticsService

router = APIRouter(prefix="/dashboard", tags=["Enterprise Dashboard"])


@router.get(
    "/overview",
    summary="Main analytics dashboard overview",
    response_description="KPIs, genre trends, device usage, and growth series",
)
def dashboard_overview(
    _user: int = Depends(require_user_id),
    service: EnterpriseAnalyticsService = Depends(get_analytics_service),
):
    data = service.get_dashboard_overview()
    return success_response(data.model_dump(), count=len(data.growth_trends))
