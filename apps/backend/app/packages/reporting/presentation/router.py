"""Reporting HTTP routers — Spec 024."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, Response

from app.packages.reporting.application.use_cases import (
    BusinessDecisionUseCases,
    ExecutiveReportUseCases,
    ReportDefinitionUseCases,
    ReportGenerationUseCases,
)
from app.packages.reporting.domain.errors import ReportingError
from app.packages.reporting.presentation.dependencies import require_org_reporting_permission
from app.packages.reporting.presentation.error_mapping import raise_reporting_http
from app.packages.reporting.presentation.schemas import (
    ApproveReportRequest,
    BusinessDecisionCreateRequest,
    BusinessDecisionOut,
    CancelDecisionRequest,
    DecisionActionCreateRequest,
    DecisionActionOut,
    DecisionActionUpdateRequest,
    DecisionFollowUpCreateRequest,
    DecisionFollowUpOut,
    ExecutiveReportOut,
    GenerateResultOut,
    PaginatedDecisions,
    PaginatedDefinitions,
    PaginatedExecutiveReports,
    ReportDefinitionCreateRequest,
    ReportDefinitionOut,
    ReportGenerationOut,
    ReportGenerationRequest,
    ReportSnapshotOut,
)

reports_router = APIRouter(prefix="/reports", tags=["Executive Reporting"])
business_decisions_router = APIRouter(prefix="/business-decisions", tags=["Business Decisions"])


def _page(page: int, page_size: int, max_size: int = 100) -> tuple[int, int, int]:
    page = max(1, page)
    ps = min(max(1, page_size), max_size)
    return page, ps, (page - 1) * ps


@reports_router.get("/definitions", response_model=PaginatedDefinitions)
def list_definitions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    ctx: dict = Depends(require_org_reporting_permission("report.view")),
) -> PaginatedDefinitions:
    p, ps, offset = _page(page, page_size)
    items, total = ReportDefinitionUseCases(ctx["conn"]).list(
        ctx["organization_id"], limit=ps, offset=offset,
    )
    return PaginatedDefinitions(
        items=[ReportDefinitionOut(**i.__dict__) for i in items],
        total=total, page=p, page_size=ps,
    )


@reports_router.post("/definitions", response_model=ReportDefinitionOut, status_code=201)
def create_definition(
    body: ReportDefinitionCreateRequest,
    ctx: dict = Depends(require_org_reporting_permission("report.generate")),
) -> ReportDefinitionOut:
    try:
        d = ReportDefinitionUseCases(ctx["conn"]).create(
            organization_id=ctx["organization_id"],
            code=body.code,
            title=body.title,
            description=body.description,
            default_period=body.default_period,
            actor_user_id=ctx["user_id"],
            request_id=ctx["request_id"],
        )
    except ReportingError as e:
        raise_reporting_http(e)
    return ReportDefinitionOut(**d.__dict__)


@reports_router.post("/generations", response_model=ReportGenerationOut, status_code=201)
def request_generation(
    body: ReportGenerationRequest,
    ctx: dict = Depends(require_org_reporting_permission("report.generate")),
) -> ReportGenerationOut:
    try:
        g = ReportGenerationUseCases(ctx["conn"]).request(
            organization_id=ctx["organization_id"],
            definition_id=body.definition_id,
            period_start=body.period_start,
            period_end=body.period_end,
            filters=body.filters,
            actor_user_id=ctx["user_id"],
            request_id=ctx["request_id"],
        )
    except ReportingError as e:
        raise_reporting_http(e)
    return ReportGenerationOut(**g.__dict__)


@reports_router.post("/generations/{generation_id}/generate", response_model=GenerateResultOut)
def generate_snapshot(
    generation_id: int,
    ctx: dict = Depends(require_org_reporting_permission("report.generate")),
) -> GenerateResultOut:
    try:
        gen, snap, exe = ReportGenerationUseCases(ctx["conn"]).generate_snapshot(
            organization_id=ctx["organization_id"],
            generation_id=generation_id,
            actor_user_id=ctx["user_id"],
            request_id=ctx["request_id"],
        )
    except ReportingError as e:
        raise_reporting_http(e)
    return GenerateResultOut(
        generation=ReportGenerationOut(**gen.__dict__),
        snapshot=ReportSnapshotOut(**snap.__dict__),
        executive_report=ExecutiveReportOut(**exe.__dict__),
    )


@reports_router.get("/executive", response_model=PaginatedExecutiveReports)
def list_executive(
    status: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    ctx: dict = Depends(require_org_reporting_permission("report.view")),
) -> PaginatedExecutiveReports:
    p, ps, offset = _page(page, page_size)
    items, total = ExecutiveReportUseCases(ctx["conn"]).list(
        ctx["organization_id"], status=status, limit=ps, offset=offset,
    )
    return PaginatedExecutiveReports(
        items=[ExecutiveReportOut(**i.__dict__) for i in items],
        total=total, page=p, page_size=ps,
    )


@reports_router.get("/executive/{report_id}", response_model=ExecutiveReportOut)
def get_executive(
    report_id: int,
    ctx: dict = Depends(require_org_reporting_permission("report.view")),
) -> ExecutiveReportOut:
    try:
        r = ExecutiveReportUseCases(ctx["conn"]).get(ctx["organization_id"], report_id)
    except ReportingError as e:
        raise_reporting_http(e)
    return ExecutiveReportOut(**r.__dict__)


@reports_router.post("/executive/{report_id}/submit", response_model=ExecutiveReportOut)
def submit_executive(
    report_id: int,
    ctx: dict = Depends(require_org_reporting_permission("report.generate")),
) -> ExecutiveReportOut:
    try:
        r = ExecutiveReportUseCases(ctx["conn"]).submit_for_approval(
            organization_id=ctx["organization_id"], report_id=report_id,
            actor_user_id=ctx["user_id"], request_id=ctx["request_id"],
        )
    except ReportingError as e:
        raise_reporting_http(e)
    return ExecutiveReportOut(**r.__dict__)


@reports_router.post("/executive/{report_id}/approve", response_model=ExecutiveReportOut)
def approve_executive(
    report_id: int,
    body: ApproveReportRequest | None = None,
    ctx: dict = Depends(require_org_reporting_permission("report.approve")),
) -> ExecutiveReportOut:
    try:
        r = ExecutiveReportUseCases(ctx["conn"]).approve(
            organization_id=ctx["organization_id"], report_id=report_id,
            comment=(body.comment if body else None),
            actor_user_id=ctx["user_id"], request_id=ctx["request_id"],
        )
    except ReportingError as e:
        raise_reporting_http(e)
    return ExecutiveReportOut(**r.__dict__)


@reports_router.post("/executive/{report_id}/publish", response_model=ExecutiveReportOut)
def publish_executive(
    report_id: int,
    ctx: dict = Depends(require_org_reporting_permission("report.publish")),
) -> ExecutiveReportOut:
    try:
        r = ExecutiveReportUseCases(ctx["conn"]).publish(
            organization_id=ctx["organization_id"], report_id=report_id,
            actor_user_id=ctx["user_id"], request_id=ctx["request_id"],
        )
    except ReportingError as e:
        raise_reporting_http(e)
    return ExecutiveReportOut(**r.__dict__)


@reports_router.post("/executive/{report_id}/archive", response_model=ExecutiveReportOut)
def archive_executive(
    report_id: int,
    ctx: dict = Depends(require_org_reporting_permission("report.publish")),
) -> ExecutiveReportOut:
    try:
        r = ExecutiveReportUseCases(ctx["conn"]).archive(
            organization_id=ctx["organization_id"], report_id=report_id,
            actor_user_id=ctx["user_id"], request_id=ctx["request_id"],
        )
    except ReportingError as e:
        raise_reporting_http(e)
    return ExecutiveReportOut(**r.__dict__)


@reports_router.get("/executive/{report_id}/export")
def export_executive(
    report_id: int,
    ctx: dict = Depends(require_org_reporting_permission("report.export")),
) -> Response:
    try:
        csv_text = ExecutiveReportUseCases(ctx["conn"]).export_csv(
            organization_id=ctx["organization_id"], report_id=report_id,
        )
    except ReportingError as e:
        raise_reporting_http(e)
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="executive-report-{report_id}.csv"'},
    )


@reports_router.get("/executive/{report_id}/snapshot", response_model=ReportSnapshotOut)
def get_snapshot(
    report_id: int,
    ctx: dict = Depends(require_org_reporting_permission("report.view")),
) -> ReportSnapshotOut:
    from app.packages.reporting.application.use_cases import ReportSnapshotUseCases

    try:
        report = ExecutiveReportUseCases(ctx["conn"]).get(ctx["organization_id"], report_id)
        snap = ReportSnapshotUseCases(ctx["conn"]).get(ctx["organization_id"], report.snapshot_id)
    except ReportingError as e:
        raise_reporting_http(e)
    return ReportSnapshotOut(**snap.__dict__)


# ── Business decisions ────────────────────────────────────────────────────────

@business_decisions_router.get("", response_model=PaginatedDecisions)
def list_decisions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    ctx: dict = Depends(require_org_reporting_permission("decision.view")),
) -> PaginatedDecisions:
    p, ps, offset = _page(page, page_size)
    items, total = BusinessDecisionUseCases(ctx["conn"]).list(
        ctx["organization_id"], limit=ps, offset=offset,
    )
    return PaginatedDecisions(
        items=[BusinessDecisionOut(**i.__dict__) for i in items],
        total=total, page=p, page_size=ps,
    )


@business_decisions_router.post("", response_model=BusinessDecisionOut, status_code=201)
def create_decision(
    body: BusinessDecisionCreateRequest,
    ctx: dict = Depends(require_org_reporting_permission("decision.create")),
) -> BusinessDecisionOut:
    try:
        d = BusinessDecisionUseCases(ctx["conn"]).create(
            organization_id=ctx["organization_id"],
            title=body.title,
            proposal=body.proposal,
            executive_report_id=body.executive_report_id,
            evidence_refs=body.evidence_refs,
            actor_user_id=ctx["user_id"],
            request_id=ctx["request_id"],
        )
    except ReportingError as e:
        raise_reporting_http(e)
    return BusinessDecisionOut(**d.__dict__)


@business_decisions_router.get("/{decision_id}", response_model=BusinessDecisionOut)
def get_decision(
    decision_id: int,
    ctx: dict = Depends(require_org_reporting_permission("decision.view")),
) -> BusinessDecisionOut:
    try:
        d = BusinessDecisionUseCases(ctx["conn"]).get(ctx["organization_id"], decision_id)
    except ReportingError as e:
        raise_reporting_http(e)
    return BusinessDecisionOut(**d.__dict__)


@business_decisions_router.post("/{decision_id}/approve", response_model=BusinessDecisionOut)
def approve_decision(
    decision_id: int,
    ctx: dict = Depends(require_org_reporting_permission("decision.approve")),
) -> BusinessDecisionOut:
    try:
        d = BusinessDecisionUseCases(ctx["conn"]).approve(
            organization_id=ctx["organization_id"], decision_id=decision_id,
            actor_user_id=ctx["user_id"], request_id=ctx["request_id"],
        )
    except ReportingError as e:
        raise_reporting_http(e)
    return BusinessDecisionOut(**d.__dict__)


@business_decisions_router.post("/{decision_id}/cancel", response_model=BusinessDecisionOut)
def cancel_decision(
    decision_id: int,
    body: CancelDecisionRequest,
    ctx: dict = Depends(require_org_reporting_permission("decision.complete")),
) -> BusinessDecisionOut:
    try:
        d = BusinessDecisionUseCases(ctx["conn"]).cancel(
            organization_id=ctx["organization_id"],
            decision_id=decision_id,
            reason=body.reason,
            actor_user_id=ctx["user_id"],
            request_id=ctx["request_id"],
        )
    except ReportingError as e:
        raise_reporting_http(e)
    return BusinessDecisionOut(**d.__dict__)


@business_decisions_router.post("/{decision_id}/actions", response_model=DecisionActionOut, status_code=201)
def add_action(
    decision_id: int,
    body: DecisionActionCreateRequest,
    ctx: dict = Depends(require_org_reporting_permission("decision.update")),
) -> DecisionActionOut:
    try:
        a = BusinessDecisionUseCases(ctx["conn"]).add_action(
            organization_id=ctx["organization_id"], decision_id=decision_id,
            title=body.title, assignee_user_id=body.assignee_user_id,
            actor_user_id=ctx["user_id"], request_id=ctx["request_id"],
        )
    except ReportingError as e:
        raise_reporting_http(e)
    return DecisionActionOut(**a.__dict__)


@business_decisions_router.get("/{decision_id}/actions", response_model=list[DecisionActionOut])
def list_actions(
    decision_id: int,
    ctx: dict = Depends(require_org_reporting_permission("decision.view")),
) -> list[DecisionActionOut]:
    try:
        items = BusinessDecisionUseCases(ctx["conn"]).list_actions(ctx["organization_id"], decision_id)
    except ReportingError as e:
        raise_reporting_http(e)
    return [DecisionActionOut(**a.__dict__) for a in items]


@business_decisions_router.patch("/{decision_id}/actions/{action_id}", response_model=DecisionActionOut)
def update_action(
    decision_id: int,
    action_id: int,
    body: DecisionActionUpdateRequest,
    ctx: dict = Depends(require_org_reporting_permission("decision.update")),
) -> DecisionActionOut:
    try:
        a = BusinessDecisionUseCases(ctx["conn"]).update_action(
            organization_id=ctx["organization_id"], decision_id=decision_id, action_id=action_id,
            status=body.status, title=body.title,
            actor_user_id=ctx["user_id"], request_id=ctx["request_id"],
        )
    except ReportingError as e:
        raise_reporting_http(e)
    return DecisionActionOut(**a.__dict__)


@business_decisions_router.post("/{decision_id}/complete", response_model=BusinessDecisionOut)
def complete_decision(
    decision_id: int,
    ctx: dict = Depends(require_org_reporting_permission("decision.complete")),
) -> BusinessDecisionOut:
    try:
        d = BusinessDecisionUseCases(ctx["conn"]).complete(
            organization_id=ctx["organization_id"], decision_id=decision_id,
            actor_user_id=ctx["user_id"], request_id=ctx["request_id"],
        )
    except ReportingError as e:
        raise_reporting_http(e)
    return BusinessDecisionOut(**d.__dict__)


@business_decisions_router.get("/{decision_id}/follow-ups", response_model=list[DecisionFollowUpOut])
def list_follow_ups(
    decision_id: int,
    ctx: dict = Depends(require_org_reporting_permission("decision.view")),
) -> list[DecisionFollowUpOut]:
    try:
        items = BusinessDecisionUseCases(ctx["conn"]).list_follow_ups(ctx["organization_id"], decision_id)
    except ReportingError as e:
        raise_reporting_http(e)
    return [DecisionFollowUpOut(**f.__dict__) for f in items]


@business_decisions_router.post("/{decision_id}/follow-ups", response_model=DecisionFollowUpOut, status_code=201)
def add_follow_up(
    decision_id: int,
    body: DecisionFollowUpCreateRequest,
    ctx: dict = Depends(require_org_reporting_permission("decision.update")),
) -> DecisionFollowUpOut:
    try:
        f = BusinessDecisionUseCases(ctx["conn"]).add_follow_up(
            organization_id=ctx["organization_id"], decision_id=decision_id, note=body.note,
            actor_user_id=ctx["user_id"], request_id=ctx["request_id"],
        )
    except ReportingError as e:
        raise_reporting_http(e)
    return DecisionFollowUpOut(**f.__dict__)
