# -*- coding: utf-8 -*-
"""Auth helpers for simple reports (staff or organization reporting access)."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Path

from app.packages.reporting.presentation.dependencies import (
    get_current_report_role as get_current_role,
    resolve_staff_or_org_report_access,
)
from app.packages.simple_reports.registry import ACCESS_ROLES, get_report

def require_simple_report_access(
    report_id: str = Path(...),
    access: dict = Depends(resolve_staff_or_org_report_access),
) -> dict:
    report = get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Informe no encontrado")
    user_id = int(access["user_id"])
    role = str(access["access_role"])
    conn = access["conn"]
    allowed = ACCESS_ROLES.get(report.access, {"admin"})
    if role not in allowed:
        raise HTTPException(status_code=403, detail="No autorizado para este informe")
    org_id = access.get("organization_id")
    if access.get("organization_access") and not report.org_scoped:
        raise HTTPException(status_code=403, detail="Informe disponible solo para administración de plataforma")
    if org_id is None and report.org_scoped:
        # Spec 044 P0: org-scoped reports require active organization context.
        # No silent global fallback.
        raise HTTPException(
            status_code=400,
            detail="Se requiere organización activa (X-Organization-Id) para este informe",
        )
    return {
        "user_id": user_id,
        "role": role,
        "conn": conn,
        "organization_id": org_id,
        "report": report,
    }
