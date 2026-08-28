# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Optional

import duckdb
from fastapi import APIRouter, Depends, Header, HTTPException, Path, Query
from pydantic import BaseModel, Field

from app.core.database import get_write_conn
from app.packages.complex_reports.queries import run_complex_report
from app.packages.complex_reports.registry import ACCESS_ROLES, all_reports, get_report
from app.packages.identity.services.auth_deps import require_user_id
from app.packages.identity.services.data_classification import report_data_classification
from app.packages.reporting.presentation.dependencies import resolve_report_access_context

complex_reports_router = APIRouter(prefix="/reports/complex", tags=["Complex Reports"])


def _role(user_id: int, conn) -> str:
    """Compatibility helper retained for older integrations and tests."""

    from app.packages.identity.services.user_service import _fetch_user

    user = _fetch_user(conn, user_id)
    return str((user or {}).get("role") or "user").lower()


def resolve_complex_report_access(
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
    x_organization_id: Optional[str] = Header(default=None, alias="X-Organization-Id"),
) -> dict:
    return resolve_report_access_context(
        user_id=user_id,
        conn=conn,
        identity_role=_role(user_id, conn),
        x_organization_id=x_organization_id,
    )


from app.packages.complex_reports.ownership import MODULE_LABELS, get_complex_ownership


class CatalogItem(BaseModel):
    id: str
    area: str
    title: str
    question: str
    description: str
    calculation: str
    chart_type: str
    access: str
    available: bool
    unavailable_reason: str = ""
    business_module: str = ""
    business_module_label: str = ""
    business_process: str = ""
    category: str = ""
    decision: str = ""
    data_classification: str = "unknown"
    monetary_classification: Optional[str] = None
    route: str = ""
    demo_backend_dependency: str = ""
    report_type: str = "complex"


class CatalogResponse(BaseModel):
    items: list[CatalogItem]
    total: int
    modules: list[dict[str, str]] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)


class SeriesPoint(BaseModel):
    label: str
    value: Optional[float] = None


class ColumnOut(BaseModel):
    key: str
    label: str


class ComplexDataOut(BaseModel):
    report_id: str
    title: str
    question: str
    calculation: str
    chart_type: str
    available: bool
    unavailable_reason: str = ""
    period_start: str
    period_end_exclusive: str
    updated_at: str
    includes_synthetic_events: bool = False
    data_classification: str = "unknown"
    monetary_classification: Optional[str] = None
    classification_note: Optional[str] = None
    summary: dict[str, Any] = Field(default_factory=dict)
    series: list[SeriesPoint] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    columns: list[ColumnOut] = Field(default_factory=list)


def _to_complex_item(r) -> CatalogItem:
    own = get_complex_ownership(r.id)
    return CatalogItem(
        id=r.id,
        area=r.area,
        title=r.title,
        question=r.question,
        description=r.description,
        calculation=r.calculation,
        chart_type=r.chart_type,
        access=r.access,
        available=r.available,
        unavailable_reason=r.unavailable_reason,
        business_module=own.business_module if own else "",
        business_module_label=MODULE_LABELS.get(own.business_module, "") if own else "",
        business_process=own.business_process if own else "",
        category=own.category if own else "",
        decision=own.decision if own else r.question,
        data_classification=own.data_classification if own else "unknown",
        monetary_classification=own.monetary_classification if own else None,
        route=own.route if own else f"/complex-reports?report={r.id}",
        demo_backend_dependency=own.demo_backend_dependency if own else "",
        report_type="complex",
    )


@complex_reports_router.get("/catalog", response_model=CatalogResponse)
def catalog(
    module: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
    access: dict = Depends(resolve_complex_report_access),
) -> CatalogResponse:
    role = str(access["access_role"])
    items = []
    for r in all_reports():
        if role not in ACCESS_ROLES.get(r.access, {"admin"}):
            continue
        item = _to_complex_item(r)
        if module and item.business_module != module:
            continue
        if category and item.category.lower() != category.lower():
            continue
        if q:
            blob = f"{item.title} {item.description} {item.question} {item.category}".lower()
            if q.lower() not in blob:
                continue
        items.append(item)
    modules = [
        {"id": mid, "label": label}
        for mid, label in MODULE_LABELS.items()
        if any(i.business_module == mid for i in items)
    ]
    categories = sorted({i.category for i in items if i.category})
    return CatalogResponse(
        items=items, total=len(items), modules=modules, categories=categories
    )


@complex_reports_router.get("/{report_id}", response_model=CatalogItem)
def definition(
    report_id: str,
    access: dict = Depends(resolve_complex_report_access),
) -> CatalogItem:
    r = get_report(report_id)
    if r is None:
        raise HTTPException(status_code=404, detail="Informe no encontrado")
    role = str(access["access_role"])
    if role not in ACCESS_ROLES.get(r.access, {"admin"}):
        raise HTTPException(status_code=403, detail="No autorizado")
    return _to_complex_item(r)

@complex_reports_router.get("/{report_id}/data", response_model=ComplexDataOut)
def data(
    report_id: str = Path(...),
    date_from: Optional[str] = Query(default=None, alias="from"),
    date_to: Optional[str] = Query(default=None, alias="to"),
    limit: int = Query(default=20, ge=1, le=100),
    access: dict = Depends(resolve_complex_report_access),
) -> ComplexDataOut:
    r = get_report(report_id)
    if r is None:
        raise HTTPException(status_code=404, detail="Informe no encontrado")
    role = str(access["access_role"])
    if role not in ACCESS_ROLES.get(r.access, {"admin"}):
        raise HTTPException(status_code=403, detail="No autorizado")
    conn = access["conn"]
    org_id = access.get("organization_id")
    try:
        payload = run_complex_report(
            conn,
            report_id,
            date_from=date_from,
            date_to=date_to,
            organization_id=org_id,
            limit=limit,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Informe no encontrado")
    monetary = r.id in {"income-by-month", "campaign-roi"} or r.area.lower() in {
        "finanzas",
        "marketing",
    }
    meta = report_data_classification(
        includes_synthetic_events=bool(payload.get("includes_synthetic_events")),
        monetary=monetary,
    )
    payload.update(meta)
    return ComplexDataOut(**payload)
