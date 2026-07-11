from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_dashboard_service
from app.models.schemas import (
    DashboardEngagementResponse,
    DashboardGrowthResponse,
    DashboardOverviewResponse,
    DashboardRealtimeResponse,
)
from app.packages.identity.services.auth_deps import require_user_id
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/overview", response_model=DashboardOverviewResponse, summary="Dashboard KPI overview")
def dashboard_overview(
    _user: int = Depends(require_user_id),
    service: DashboardService = Depends(get_dashboard_service),
):
    return service.get_overview()


@router.get("/realtime", response_model=DashboardRealtimeResponse, summary="Realtime streaming metrics")
def dashboard_realtime(
    _user: int = Depends(require_user_id),
    service: DashboardService = Depends(get_dashboard_service),
):
    return service.get_realtime()


@router.get("/growth", response_model=DashboardGrowthResponse, summary="Weekly growth metrics")
def dashboard_growth(
    _user: int = Depends(require_user_id),
    service: DashboardService = Depends(get_dashboard_service),
):
    return service.get_growth()


@router.get("/engagement", response_model=DashboardEngagementResponse, summary="User engagement segments")
def dashboard_engagement(
    _user: int = Depends(require_user_id),
    service: DashboardService = Depends(get_dashboard_service),
):
    return service.get_engagement()
