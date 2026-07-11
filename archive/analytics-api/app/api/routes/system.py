from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import SystemServiceDep, get_system_service
from app.api.handlers import dispatch_service

router = APIRouter(prefix="/system", tags=["System"])


@router.get(
    "/health/full",
    summary="Full system health probe",
    description=(
        "Enterprise health check: database, pipeline, data quality, "
        "query latency benchmarks, and warehouse table summary."
    ),
)
def system_health_full(service: SystemServiceDep = Depends(get_system_service)):
    return dispatch_service(service.get_full_health)
