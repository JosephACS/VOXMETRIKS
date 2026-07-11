from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import StreamServiceDep, get_stream_service
from app.api.handlers import dispatch_service
from app.schemas.common import DaysQuery

router = APIRouter(prefix="/streams", tags=["Streams"])


@router.get(
    "/daily",
    summary="Daily stream aggregates",
    description="Returns daily streaming KPIs from agg_daily_streams.",
)
def streams_daily(
    query: DaysQuery = Depends(),
    service: StreamServiceDep = Depends(get_stream_service),
):
    return dispatch_service(lambda: service.get_daily(query.days))


@router.get(
    "/engagement",
    summary="Stream engagement analysis",
    description="Cross-analysis of fact_streaming and agg_daily_streams.",
)
def streams_engagement(service: StreamServiceDep = Depends(get_stream_service)):
    return dispatch_service(service.get_engagement)
