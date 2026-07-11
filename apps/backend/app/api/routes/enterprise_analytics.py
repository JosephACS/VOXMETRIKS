from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query

from app.api.deps_enterprise import get_analytics_service
from app.core.query_params import ListFilters, get_list_filters
from app.schemas.common import success_response
from app.services.enterprise_analytics_service import EnterpriseAnalyticsService
from app.utils.time_utils import utc_today

router = APIRouter(prefix="/analytics", tags=["Enterprise Analytics"])


@router.get(
    "/streams",
    summary="Streaming analytics for a date range",
    response_description="Daily series, peak hours, trending artists and genres",
)
def streams_analytics(
    start_date: date | None = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: date | None = Query(None, description="End date (YYYY-MM-DD)"),
    filters: ListFilters = Depends(get_list_filters),
    service: EnterpriseAnalyticsService = Depends(get_analytics_service),
):
    end = end_date or utc_today()
    start = start_date or (end - timedelta(days=30))
    if filters.date_from:
        start = filters.date_from
    if filters.date_to:
        end = filters.date_to
    data = service.get_streams_analytics(start, end)
    return success_response(data.model_dump(), count=len(data.series))
