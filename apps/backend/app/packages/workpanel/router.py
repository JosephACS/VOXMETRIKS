# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field

import duckdb

from app.core.database import get_conn
from app.packages.identity.services.auth_deps import (
    require_staff_identity,
    resolve_optional_org_membership,
)
from app.packages.identity.services.data_classification import workpanel_classifications
from app.packages.identity.services.user_service import _fetch_user
from app.packages.workpanel.service import build_workpanel

workpanel_router = APIRouter(prefix="/workpanel", tags=["Workpanel"])


class WorkpanelMetricOut(BaseModel):
    id: str
    label: str
    value: Optional[float] = None
    unit: str
    period: str
    previous_value: Optional[float] = None
    variation_pct: Optional[float] = None
    explanation: str
    detail_path: str
    available: bool
    status: str = "ok"
    scope: str = "organization"
    display_caption: Optional[str] = None


class WorkpanelPendingOut(BaseModel):
    id: str
    label: str
    value: float
    detail_path: str
    severity: str = "medium"


class WorkpanelLinkOut(BaseModel):
    label: str
    path: str


class WorkpanelSectionOut(BaseModel):
    id: str
    title: str
    description: str
    badge: str
    scope: str
    metric_ids: list[str] = Field(default_factory=list)
    quick_links: list[WorkpanelLinkOut] = Field(default_factory=list)


class WorkpanelOut(BaseModel):
    title: str
    subtitle: str
    period: str
    period_start: str
    period_end_exclusive: str
    updated_at: str
    analytics_updated_at: Optional[str] = None
    organization_id: Optional[int] = None
    includes_synthetic_events: bool = False
    data_classification: str = "unknown"
    monetary_classification: str = "simulated"
    classification_note: Optional[str] = None
    available_periods: list[str] = Field(default_factory=list)
    default_period: Optional[str] = None
    period_sources: dict[str, list[str]] = Field(default_factory=dict)
    sections: list[WorkpanelSectionOut] = Field(default_factory=list)
    metrics: list[WorkpanelMetricOut] = Field(default_factory=list)
    pendings: list[WorkpanelPendingOut] = Field(default_factory=list)
    links: list[WorkpanelLinkOut] = Field(default_factory=list)


def _role(user_id: int, conn: duckdb.DuckDBPyConnection) -> str:
    user = _fetch_user(conn, user_id)
    return (user.get("role") or "user").lower() if user else "user"


@workpanel_router.get("", response_model=WorkpanelOut)
def get_workpanel(
    period: Optional[str] = Query(default=None, description="Periodo YYYY-MM"),
    user_id: int = Depends(require_staff_identity),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-Id"),
) -> WorkpanelOut:
    """Enterprise Workpanel — staff only (admin|engineer). Listeners → 403."""
    org_id: Optional[int] = None
    if x_organization_id is not None and str(x_organization_id).strip() != "":
        try:
            raw = int(str(x_organization_id).strip())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid X-Organization-Id")
        org_id = resolve_optional_org_membership(
            user_id=user_id, organization_id=raw, conn=conn
        )
    try:
        data = build_workpanel(
            conn,
            period=period,
            organization_id=org_id,
            role=_role(user_id, conn),
        )
    except ValueError as exc:
        code = str(exc)
        if code == "future_period":
            raise HTTPException(status_code=400, detail="No se permiten periodos futuros") from exc
        if code == "unknown_period":
            raise HTTPException(
                status_code=400,
                detail="Periodo no disponible. Elija un mes con datos.",
            ) from exc
        if code == "invalid_period_format":
            raise HTTPException(status_code=400, detail="Formato de periodo inválido (YYYY-MM)") from exc
        raise HTTPException(status_code=400, detail="Periodo inválido") from exc
    meta = workpanel_classifications(
        conn,
        includes_synthetic_events=bool(data.get("includes_synthetic_events")),
    )
    data.update(meta)
    return WorkpanelOut(**data)
