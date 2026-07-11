from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import AuditServiceDep, get_audit_service
from app.api.handlers import dispatch_service

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get(
    "/pipeline",
    summary="Pipeline health audit",
    description="Returns ELT pipeline stages and load history from ctl_* tables.",
)
def audit_pipeline(service: AuditServiceDep = Depends(get_audit_service)):
    return dispatch_service(service.get_pipeline)


@router.get(
    "/data-quality",
    summary="Data quality reconciliation",
    description="Cross-checks facts vs aggregates for warehouse integrity.",
)
def audit_data_quality(service: AuditServiceDep = Depends(get_audit_service)):
    return dispatch_service(service.get_data_quality)
