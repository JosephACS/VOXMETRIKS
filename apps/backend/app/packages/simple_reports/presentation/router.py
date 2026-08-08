# -*- coding: utf-8 -*-
"""Simple reports HTTP API — Tarea 11."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.packages.identity.services.auth_deps import require_staff_identity
from app.packages.simple_reports.presentation.dependencies import (
    get_current_role,
    require_simple_report_access,
)
from app.packages.simple_reports.presentation.schemas import (
    ReportColumnOut,
    ReportFilterOut,
    SimpleReportCatalogItem,
    SimpleReportCatalogResponse,
    SimpleReportDataResponse,
)
from app.packages.simple_reports.queries import run_report
from app.packages.simple_reports.registry import ACCESS_ROLES, all_reports, get_report
from app.packages.identity.services.data_classification import report_data_classification
from app.packages.simple_reports.ownership import (
    MODULE_LABELS,
    get_simple_ownership,
)

simple_reports_router = APIRouter(prefix="/reports/simple", tags=["Simple Reports"])


def _to_catalog_item(r) -> SimpleReportCatalogItem:
    own = get_simple_ownership(r.id)
    return SimpleReportCatalogItem(
        id=r.id,
        area=r.area,
        title=r.title,
        description=r.description,
        objective=r.objective,
        access=r.access,
        org_scoped=r.org_scoped,
        implementation=r.implementation,
        pending_reason=r.pending_reason,
        columns=[ReportColumnOut(key=c.key, label=c.label) for c in r.columns],
        filters=[
            ReportFilterOut(key=f.key, label=f.label, kind=f.kind, options=list(f.options))
            for f in r.filters
        ],
        business_module=own.business_module if own else "",
        business_module_label=MODULE_LABELS.get(own.business_module, "") if own else "",
        business_process=own.business_process if own else "",
        category=own.category if own else "",
        decision=own.decision if own else r.objective,
        data_classification=own.data_classification if own else "unknown",
        monetary_classification=own.monetary_classification if own else None,
        route=own.route if own else f"/simple-reports?report={r.id}",
        demo_backend_dependency=own.demo_backend_dependency if own else "",
        report_type="simple",
    )


@simple_reports_router.get("/catalog", response_model=SimpleReportCatalogResponse)
def catalog(
    area: Optional[str] = Query(default=None),
    module: Optional[str] = Query(default=None, description="business_module filter"),
    category: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None, description="search title/description"),
    user_id: int = Depends(require_staff_identity),
    role: str = Depends(get_current_role),
) -> SimpleReportCatalogResponse:
    items = []
    for r in all_reports():
        if role not in ACCESS_ROLES.get(r.access, {"admin"}):
            continue
        if area and r.area.lower() != area.lower():
            continue
        item = _to_catalog_item(r)
        if module and item.business_module != module:
            continue
        if category and item.category.lower() != category.lower():
            continue
        if q:
            blob = f"{item.title} {item.description} {item.objective} {item.category}".lower()
            if q.lower() not in blob:
                continue
        items.append(item)
    modules = [
        {"id": mid, "label": label}
        for mid, label in MODULE_LABELS.items()
        if any(i.business_module == mid for i in items)
    ]
    categories = sorted({i.category for i in items if i.category})
    return SimpleReportCatalogResponse(
        items=items,
        total=len(items),
        modules=modules,
        categories=categories,
    )

@simple_reports_router.get("")
def list_alias(
    area: Optional[str] = Query(default=None),
    module: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
    user_id: int = Depends(require_staff_identity),
    role: str = Depends(get_current_role),
) -> SimpleReportCatalogResponse:
    return catalog(
        area=area,
        module=module,
        category=category,
        q=q,
        user_id=user_id,
        role=role,
    )

@simple_reports_router.get("/{report_id}", response_model=SimpleReportCatalogItem)
def get_definition(
    report_id: str,
    role: str = Depends(get_current_role),
    user_id: int = Depends(require_staff_identity),
) -> SimpleReportCatalogItem:
    r = get_report(report_id)
    if r is None:
        raise HTTPException(status_code=404, detail="Informe no encontrado")
    if role not in ACCESS_ROLES.get(r.access, {"admin"}):
        raise HTTPException(status_code=403, detail="No autorizado para este informe")
    return _to_catalog_item(r)


@simple_reports_router.get("/{report_id}/data", response_model=SimpleReportDataResponse)
def get_data(
    report_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    search: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    severity: Optional[str] = Query(default=None),
    stage: Optional[str] = Query(default=None),
    priority: Optional[str] = Query(default=None),
    within_days: Optional[str] = Query(default=None),
    ctx: dict = Depends(require_simple_report_access),
) -> SimpleReportDataResponse:
    report = ctx["report"]
    # Re-bind dependency with path id consistency
    if report.id != report_id:
        raise HTTPException(status_code=404, detail="Informe no encontrado")

    filters = {}
    if status:
        filters["status"] = status
    if severity:
        filters["severity"] = severity
    if stage:
        filters["stage"] = stage
    if priority:
        filters["priority"] = priority
    if within_days:
        filters["within_days"] = within_days

    page_size = min(max(page_size, 1), 100)
    offset = (page - 1) * page_size
    items, total = run_report(
        ctx["conn"],
        report_id,
        organization_id=ctx.get("organization_id"),
        filters=filters,
        search=search,
        limit=page_size,
        offset=offset,
    )
    monetary = False
    own = get_simple_ownership(report.id)
    if own and own.monetary_classification == "simulated":
        monetary = True
    elif report.area.lower() in {
        "finanzas",
        "facturación",
        "facturacion",
        "cobros",
        "pagos",
    } or "invoice" in report.id or "payment" in report.id or "refund" in report.id:
        monetary = True
    meta = report_data_classification(includes_synthetic_events=False, monetary=monetary)
    # Prefer ownership classification hint when more specific than generic unknown.
    data_cls = meta["data_classification"]
    if own and own.data_classification in {"synthetic", "demo", "mixed", "operational", "real"}:
        if own.data_classification == "operational":
            data_cls = meta["data_classification"]
        elif own.data_classification == "demo":
            data_cls = "demo"
        else:
            data_cls = own.data_classification
    return SimpleReportDataResponse(
        report_id=report.id,
        title=report.title,
        description=report.description,
        columns=[ReportColumnOut(key=c.key, label=c.label) for c in report.columns],
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        implementation=report.implementation,
        data_classification=data_cls,
        monetary_classification=meta.get("monetary_classification")
        or (own.monetary_classification if own else None),
        classification_note=meta.get("classification_note"),
    )
