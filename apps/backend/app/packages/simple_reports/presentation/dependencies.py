# -*- coding: utf-8 -*-
"""Auth helpers for simple reports (spec 037 — staff enterprise gate)."""

from __future__ import annotations

from typing import Optional

import duckdb
from fastapi import Depends, Header, HTTPException, Path

from app.core.database import get_conn
from app.packages.identity.services.auth_deps import (
    require_staff_identity,
    require_user_id,
    resolve_optional_org_membership,
)
from app.packages.identity.services.user_service import _fetch_user
from app.packages.simple_reports.registry import ACCESS_ROLES, get_report


def get_current_role(
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
) -> str:
    user = _fetch_user(conn, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return (user.get("role") or "user").lower()


def require_simple_report_access(
    report_id: str = Path(...),
    user_id: int = Depends(require_staff_identity),
    role: str = Depends(get_current_role),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-Id"),
) -> dict:
    report = get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Informe no encontrado")
    allowed = ACCESS_ROLES.get(report.access, {"admin"})
    if role not in allowed:
        raise HTTPException(status_code=403, detail="No autorizado para este informe")
    org_id = None
    if x_organization_id is not None and str(x_organization_id).strip() != "":
        try:
            raw = int(str(x_organization_id).strip())
        except ValueError:
            raise HTTPException(status_code=400, detail="X-Organization-Id inválido")
        # Always verify membership when header is present (no ID hopping / spoof).
        org_id = resolve_optional_org_membership(
            user_id=user_id, organization_id=raw, conn=conn
        )
    elif report.org_scoped:
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
