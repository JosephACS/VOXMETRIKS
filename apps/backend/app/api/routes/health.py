from __future__ import annotations

from fastapi import APIRouter

from app.models.schemas import SystemHealthResponse
from app.schemas.common import success_response
from app.services.health_service import HealthService

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=SystemHealthResponse, summary="System health (legacy shape)")
def health_legacy():
    return HealthService().get_system_health()


@router.get("/health/enterprise", summary="Enterprise health wrapper")
def health_enterprise():
    system = HealthService().get_system_health()
    return success_response(system.model_dump())
