"""Business analytics HTTP router — Spec 023."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.packages.business_analytics.application.use_cases import (
    AnalyticsDashboardUseCases,
    BusinessAlertUseCases,
    DataQualityUseCases,
    KpiCatalogUseCases,
    KpiSnapshotUseCases,
    MetricSourceUseCases,
    RecommendationUseCases,
)
from app.packages.business_analytics.domain.errors import BusinessAnalyticsError
from app.packages.business_analytics.presentation.dependencies import require_org_biz_analytics_permission
from app.packages.business_analytics.presentation.error_mapping import raise_biz_analytics_http
from app.packages.business_analytics.presentation.schemas import (
    BusinessAlertCreateRequest,
    BusinessAlertOut,
    CaptureSnapshotRequest,
    DashboardOverviewOut,
    DataQualityResultOut,
    DrillDownOut,
    KpiDefinitionOut,
    KpiSnapshotOut,
    MetricSourceOut,
    RecommendationOut,
    StrategicOverviewOut,
    StrategicRefreshOut,
)

business_analytics_router = APIRouter(prefix="/business-analytics", tags=["Business Analytics"])


@business_analytics_router.get("/dashboard", response_model=DashboardOverviewOut)
def dashboard_overview(ctx: dict = Depends(require_org_biz_analytics_permission("biz_analytics.view"))):
    data = AnalyticsDashboardUseCases(ctx["conn"]).overview(ctx["organization_id"])
    return DashboardOverviewOut(**data)


@business_analytics_router.get("/kpis", response_model=list[KpiDefinitionOut])
def list_kpis(ctx: dict = Depends(require_org_biz_analytics_permission("biz_analytics.view"))):
    items = KpiCatalogUseCases(ctx["conn"]).list(status="active")
    return [KpiDefinitionOut(**k.__dict__) for k in items]


@business_analytics_router.get("/kpis/{code}", response_model=KpiDefinitionOut)
def get_kpi(code: str, ctx: dict = Depends(require_org_biz_analytics_permission("biz_analytics.view"))):
    try:
        kpi = KpiCatalogUseCases(ctx["conn"]).get_by_code(code)
    except BusinessAnalyticsError as e:
        raise_biz_analytics_http(e)
    return KpiDefinitionOut(**kpi.__dict__)


@business_analytics_router.get("/snapshots", response_model=list[KpiSnapshotOut])
def list_snapshots(
    kpi_code: Optional[str] = Query(default=None),
    ctx: dict = Depends(require_org_biz_analytics_permission("biz_analytics.view")),
):
    items = KpiSnapshotUseCases(ctx["conn"]).list(
        organization_id=ctx["organization_id"], kpi_code=kpi_code,
    )
    return [KpiSnapshotOut(**s.__dict__) for s in items]


@business_analytics_router.post("/snapshots", response_model=KpiSnapshotOut, status_code=201)
def capture_snapshot(
    body: CaptureSnapshotRequest,
    ctx: dict = Depends(require_org_biz_analytics_permission("biz_analytics.manage")),
):
    try:
        snap = KpiSnapshotUseCases(ctx["conn"]).capture(
            body.kpi_code, organization_id=ctx["organization_id"], period=body.period,
            is_synthetic=body.is_synthetic, actor_user_id=ctx["user_id"],
        )
    except BusinessAnalyticsError as e:
        raise_biz_analytics_http(e)
    return KpiSnapshotOut(**snap.__dict__)


@business_analytics_router.get("/sources", response_model=list[MetricSourceOut])
def list_sources(ctx: dict = Depends(require_org_biz_analytics_permission("biz_analytics.view"))):
    items = MetricSourceUseCases(ctx["conn"]).list()
    return [MetricSourceOut(**s.__dict__) for s in items]


@business_analytics_router.get("/quality", response_model=list[DataQualityResultOut])
def list_quality(ctx: dict = Depends(require_org_biz_analytics_permission("biz_analytics.view"))):
    items = DataQualityUseCases(ctx["conn"]).list(organization_id=ctx["organization_id"])
    return [DataQualityResultOut(**q.__dict__) for q in items]


@business_analytics_router.post("/quality/run/{check_code}", response_model=DataQualityResultOut)
def run_quality_check(
    check_code: str,
    ctx: dict = Depends(require_org_biz_analytics_permission("biz_analytics.manage")),
):
    result = DataQualityUseCases(ctx["conn"]).run_check(
        check_code, organization_id=ctx["organization_id"], actor_user_id=ctx["user_id"],
    )
    return DataQualityResultOut(**result.__dict__)


@business_analytics_router.get("/alerts", response_model=list[BusinessAlertOut])
def list_alerts(
    status: Optional[str] = Query(default=None),
    ctx: dict = Depends(require_org_biz_analytics_permission("biz_analytics.view")),
):
    items = BusinessAlertUseCases(ctx["conn"]).list(ctx["organization_id"], status=status)
    return [BusinessAlertOut(**a.__dict__) for a in items]


@business_analytics_router.post("/alerts", response_model=BusinessAlertOut, status_code=201)
def create_alert(
    body: BusinessAlertCreateRequest,
    ctx: dict = Depends(require_org_biz_analytics_permission("biz_analytics.alert")),
):
    alert = BusinessAlertUseCases(ctx["conn"]).create(
        ctx["organization_id"], severity=body.severity, title=body.title, body=body.body,
        kpi_code=body.kpi_code, actor_user_id=ctx["user_id"],
    )
    return BusinessAlertOut(**alert.__dict__)


@business_analytics_router.post("/alerts/{alert_id}/ack", response_model=BusinessAlertOut)
def ack_alert(
    alert_id: int,
    ctx: dict = Depends(require_org_biz_analytics_permission("biz_analytics.alert")),
):
    try:
        alert = BusinessAlertUseCases(ctx["conn"]).ack(
            alert_id, ctx["organization_id"], actor_user_id=ctx["user_id"],
        )
    except BusinessAnalyticsError as e:
        raise_biz_analytics_http(e)
    return BusinessAlertOut(**alert.__dict__)


@business_analytics_router.get("/recommendations", response_model=list[RecommendationOut])
def list_recommendations(ctx: dict = Depends(require_org_biz_analytics_permission("biz_analytics.view"))):
    items = RecommendationUseCases(ctx["conn"]).list(ctx["organization_id"])
    return [RecommendationOut(**r.__dict__) for r in items]


@business_analytics_router.post("/recommendations/generate", response_model=list[RecommendationOut])
def generate_recommendations(ctx: dict = Depends(require_org_biz_analytics_permission("biz_analytics.view"))):
    items = RecommendationUseCases(ctx["conn"]).generate_rule_based(ctx["organization_id"])
    return [RecommendationOut(**r.__dict__) for r in items]


@business_analytics_router.get("/drill-down/{dimension}", response_model=DrillDownOut)
def drill_down(
    dimension: str,
    value: Optional[str] = Query(default=None),
    ctx: dict = Depends(require_org_biz_analytics_permission("biz_analytics.view")),
):
    data = AnalyticsDashboardUseCases(ctx["conn"]).drill_down(
        ctx["organization_id"], dimension=dimension, value=value,
    )
    return DrillDownOut(**data)


@business_analytics_router.post("/strategic/refresh", response_model=StrategicRefreshOut)
def refresh_strategic_overview(
    include_global: bool = Query(default=False),
    ctx: dict = Depends(require_org_biz_analytics_permission("biz_analytics.manage")),
):
    from app.packages.business_analytics.application.strategic_agg import (
        default_period,
        refresh_strategic_kpi_period,
    )

    allow_global = bool(include_global and ctx.get("is_platform_admin"))
    period_start, period_end = default_period()
    rows = refresh_strategic_kpi_period(
        ctx["conn"],
        organization_id=ctx["organization_id"],
        period_start=period_start,
        period_end=period_end,
        include_global=allow_global,
    )
    return StrategicRefreshOut(
        organization_id=ctx["organization_id"],
        period_start=period_start.isoformat(),
        period_end=period_end.isoformat(),
        include_global=allow_global,
        rows_written=len(rows),
    )


@business_analytics_router.get("/strategic/overview", response_model=StrategicOverviewOut)
def strategic_overview_endpoint(
    include_global: bool = Query(default=False),
    ctx: dict = Depends(require_org_biz_analytics_permission("biz_analytics.view")),
):
    from app.packages.business_analytics.application.strategic_agg import strategic_overview

    allow_global = bool(include_global and ctx.get("is_platform_admin"))
    data = strategic_overview(
        ctx["conn"],
        organization_id=ctx["organization_id"],
        include_global=allow_global,
        can_create_decision=bool(ctx.get("can_create_decision")),
        can_draft_report=bool(ctx.get("can_draft_report")),
        can_refresh_strategic=bool(ctx.get("can_refresh_strategic")),
        auto_refresh=False,
    )
    return StrategicOverviewOut(**data)
