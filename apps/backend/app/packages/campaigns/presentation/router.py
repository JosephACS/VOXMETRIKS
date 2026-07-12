"""Campaigns HTTP router — Spec 022."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.packages.campaigns.application.use_cases import (
    AttributionDefinitionUseCases,
    AttributableRevenueUseCases,
    CampaignApprovalUseCases,
    CampaignBudgetUseCases,
    CampaignExpenseUseCases,
    CampaignHistoryUseCases,
    CampaignObjectiveUseCases,
    CampaignResultUseCases,
    CampaignRoiUseCases,
    CampaignTargetUseCases,
    CampaignUseCases,
)
from app.packages.campaigns.domain.errors import CampaignsError
from app.packages.campaigns.presentation.dependencies import require_org_campaign_permission
from app.packages.campaigns.presentation.error_mapping import raise_campaigns_http
from app.packages.campaigns.presentation.schemas import (
    AttributionDefinitionCreateRequest,
    AttributionDefinitionOut,
    AttributableRevenueCreateRequest,
    AttributableRevenueOut,
    CampaignApprovalDecideRequest,
    CampaignApprovalOut,
    CampaignApprovalSubmitRequest,
    CampaignBudgetOut,
    CampaignBudgetSetRequest,
    CampaignCreateRequest,
    CampaignExpenseCreateRequest,
    CampaignExpenseOut,
    CampaignObjectiveCreateRequest,
    CampaignObjectiveOut,
    CampaignOut,
    CampaignResultCreateRequest,
    CampaignResultOut,
    CampaignRoiSnapshotOut,
    CampaignStatusHistoryOut,
    CampaignTargetOut,
    CampaignTargetSetRequest,
    CampaignTransitionRequest,
    CampaignUpdateRequest,
    PaginatedCampaigns,
)

campaigns_router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


def _page(page: int, page_size: int, max_size: int = 100) -> tuple[int, int, int]:
    page = max(1, page)
    ps = min(max(1, page_size), max_size)
    return page, ps, (page - 1) * ps


@campaigns_router.get("", response_model=PaginatedCampaigns)
def list_campaigns(
    status: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    ctx: dict = Depends(require_org_campaign_permission("campaign.view")),
) -> PaginatedCampaigns:
    p, ps, offset = _page(page, page_size)
    items, total = CampaignUseCases(ctx["conn"]).list(
        ctx["organization_id"], status=status, limit=ps, offset=offset,
    )
    return PaginatedCampaigns(
        items=[CampaignOut(**c.__dict__) for c in items],
        total=total, page=p, page_size=ps,
    )


@campaigns_router.post("", response_model=CampaignOut, status_code=201)
def create_campaign(
    body: CampaignCreateRequest,
    ctx: dict = Depends(require_org_campaign_permission("campaign.create")),
) -> CampaignOut:
    try:
        campaign = CampaignUseCases(ctx["conn"]).create(
            actor_user_id=ctx["user_id"],
            organization_id=ctx["organization_id"],
            name=body.name,
            market=body.market,
            segment=body.segment,
            start_date=body.start_date,
            end_date=body.end_date,
            artist_profile_id=body.artist_profile_id,
            catalog_release_id=body.catalog_release_id,
            request_id=ctx["request_id"],
        )
    except CampaignsError as e:
        raise_campaigns_http(e)
    return CampaignOut(**campaign.__dict__)


@campaigns_router.get("/{campaign_id}", response_model=CampaignOut)
def get_campaign(
    campaign_id: int,
    ctx: dict = Depends(require_org_campaign_permission("campaign.view")),
) -> CampaignOut:
    try:
        campaign = CampaignUseCases(ctx["conn"]).get(campaign_id, ctx["organization_id"])
    except CampaignsError as e:
        raise_campaigns_http(e)
    return CampaignOut(**campaign.__dict__)


@campaigns_router.patch("/{campaign_id}", response_model=CampaignOut)
def update_campaign(
    campaign_id: int,
    body: CampaignUpdateRequest,
    ctx: dict = Depends(require_org_campaign_permission("campaign.update")),
) -> CampaignOut:
    try:
        campaign = CampaignUseCases(ctx["conn"]).update(
            campaign_id, ctx["organization_id"],
            actor_user_id=ctx["user_id"],
            name=body.name,
            market=body.market,
            segment=body.segment,
            start_date=body.start_date,
            end_date=body.end_date,
            artist_profile_id=body.artist_profile_id,
            catalog_release_id=body.catalog_release_id,
            request_id=ctx["request_id"],
        )
    except CampaignsError as e:
        raise_campaigns_http(e)
    return CampaignOut(**campaign.__dict__)


@campaigns_router.post("/{campaign_id}/submit-for-approval", response_model=CampaignOut)
def submit_campaign_for_approval(
    campaign_id: int,
    ctx: dict = Depends(require_org_campaign_permission("campaign.update")),
) -> CampaignOut:
    try:
        campaign = CampaignUseCases(ctx["conn"]).submit_for_approval(
            campaign_id, ctx["organization_id"],
            actor_user_id=ctx["user_id"], request_id=ctx["request_id"],
        )
    except CampaignsError as e:
        raise_campaigns_http(e)
    return CampaignOut(**campaign.__dict__)


@campaigns_router.post("/{campaign_id}/activate", response_model=CampaignOut)
def activate_campaign(
    campaign_id: int,
    ctx: dict = Depends(require_org_campaign_permission("campaign.update")),
) -> CampaignOut:
    try:
        campaign = CampaignUseCases(ctx["conn"]).activate(
            campaign_id, ctx["organization_id"],
            actor_user_id=ctx["user_id"], request_id=ctx["request_id"],
        )
    except CampaignsError as e:
        raise_campaigns_http(e)
    return CampaignOut(**campaign.__dict__)


@campaigns_router.post("/{campaign_id}/pause", response_model=CampaignOut)
def pause_campaign(
    campaign_id: int,
    ctx: dict = Depends(require_org_campaign_permission("campaign.update")),
) -> CampaignOut:
    try:
        campaign = CampaignUseCases(ctx["conn"]).pause(
            campaign_id, ctx["organization_id"],
            actor_user_id=ctx["user_id"], request_id=ctx["request_id"],
        )
    except CampaignsError as e:
        raise_campaigns_http(e)
    return CampaignOut(**campaign.__dict__)


@campaigns_router.post("/{campaign_id}/complete", response_model=CampaignOut)
def complete_campaign(
    campaign_id: int,
    ctx: dict = Depends(require_org_campaign_permission("campaign.close")),
) -> CampaignOut:
    try:
        campaign = CampaignUseCases(ctx["conn"]).complete(
            campaign_id, ctx["organization_id"],
            actor_user_id=ctx["user_id"], request_id=ctx["request_id"],
        )
    except CampaignsError as e:
        raise_campaigns_http(e)
    return CampaignOut(**campaign.__dict__)


@campaigns_router.post("/{campaign_id}/cancel", response_model=CampaignOut)
def cancel_campaign(
    campaign_id: int,
    body: CampaignTransitionRequest,
    ctx: dict = Depends(require_org_campaign_permission("campaign.update")),
) -> CampaignOut:
    try:
        campaign = CampaignUseCases(ctx["conn"]).cancel(
            campaign_id, ctx["organization_id"],
            actor_user_id=ctx["user_id"], reason=body.reason,
            request_id=ctx["request_id"],
        )
    except CampaignsError as e:
        raise_campaigns_http(e)
    return CampaignOut(**campaign.__dict__)


@campaigns_router.post("/{campaign_id}/close", response_model=CampaignOut)
def close_campaign(
    campaign_id: int,
    ctx: dict = Depends(require_org_campaign_permission("campaign.close")),
) -> CampaignOut:
    try:
        campaign = CampaignUseCases(ctx["conn"]).close(
            campaign_id, ctx["organization_id"],
            actor_user_id=ctx["user_id"], request_id=ctx["request_id"],
        )
    except CampaignsError as e:
        raise_campaigns_http(e)
    return CampaignOut(**campaign.__dict__)


@campaigns_router.get("/{campaign_id}/history", response_model=list[CampaignStatusHistoryOut])
def get_campaign_history(
    campaign_id: int,
    ctx: dict = Depends(require_org_campaign_permission("campaign.view")),
) -> list[CampaignStatusHistoryOut]:
    try:
        entries = CampaignHistoryUseCases(ctx["conn"]).get(campaign_id, ctx["organization_id"])
    except CampaignsError as e:
        raise_campaigns_http(e)
    return [CampaignStatusHistoryOut(**e.__dict__) for e in entries]


# ── Objectives ────────────────────────────────────────────────────────────────

@campaigns_router.get("/{campaign_id}/objectives", response_model=list[CampaignObjectiveOut])
def list_objectives(
    campaign_id: int,
    ctx: dict = Depends(require_org_campaign_permission("campaign.view")),
) -> list[CampaignObjectiveOut]:
    try:
        items = CampaignObjectiveUseCases(ctx["conn"]).list(campaign_id, ctx["organization_id"])
    except CampaignsError as e:
        raise_campaigns_http(e)
    return [CampaignObjectiveOut(**o.__dict__) for o in items]


@campaigns_router.post("/{campaign_id}/objectives", response_model=CampaignObjectiveOut, status_code=201)
def add_objective(
    campaign_id: int,
    body: CampaignObjectiveCreateRequest,
    ctx: dict = Depends(require_org_campaign_permission("campaign.update")),
) -> CampaignObjectiveOut:
    try:
        obj = CampaignObjectiveUseCases(ctx["conn"]).add(
            campaign_id, ctx["organization_id"],
            objective_type=body.objective_type,
            description=body.description,
            priority=body.priority,
            actor_user_id=ctx["user_id"],
            request_id=ctx["request_id"],
        )
    except CampaignsError as e:
        raise_campaigns_http(e)
    return CampaignObjectiveOut(**obj.__dict__)


# ── Targets ───────────────────────────────────────────────────────────────────

@campaigns_router.get("/{campaign_id}/targets", response_model=list[CampaignTargetOut])
def list_targets(
    campaign_id: int,
    ctx: dict = Depends(require_org_campaign_permission("campaign.view")),
) -> list[CampaignTargetOut]:
    try:
        items = CampaignTargetUseCases(ctx["conn"]).list(campaign_id, ctx["organization_id"])
    except CampaignsError as e:
        raise_campaigns_http(e)
    return [CampaignTargetOut(**t.__dict__) for t in items]


@campaigns_router.post("/{campaign_id}/targets", response_model=CampaignTargetOut)
def set_target(
    campaign_id: int,
    body: CampaignTargetSetRequest,
    ctx: dict = Depends(require_org_campaign_permission("campaign.update")),
) -> CampaignTargetOut:
    try:
        target = CampaignTargetUseCases(ctx["conn"]).set(
            campaign_id, ctx["organization_id"],
            metric_code=body.metric_code,
            target_value=body.target_value,
            unit=body.unit,
            actor_user_id=ctx["user_id"],
            request_id=ctx["request_id"],
        )
    except CampaignsError as e:
        raise_campaigns_http(e)
    return CampaignTargetOut(**target.__dict__)


# ── Budget ────────────────────────────────────────────────────────────────────

@campaigns_router.get("/{campaign_id}/budget", response_model=Optional[CampaignBudgetOut])
def get_budget(
    campaign_id: int,
    ctx: dict = Depends(require_org_campaign_permission("campaign.view")),
) -> Optional[CampaignBudgetOut]:
    try:
        budget = CampaignBudgetUseCases(ctx["conn"]).get(campaign_id, ctx["organization_id"])
    except CampaignsError as e:
        raise_campaigns_http(e)
    return CampaignBudgetOut(**budget.__dict__) if budget else None


@campaigns_router.post("/{campaign_id}/budget", response_model=CampaignBudgetOut)
def set_budget(
    campaign_id: int,
    body: CampaignBudgetSetRequest,
    ctx: dict = Depends(require_org_campaign_permission("campaign.update")),
) -> CampaignBudgetOut:
    try:
        budget = CampaignBudgetUseCases(ctx["conn"]).set(
            campaign_id, ctx["organization_id"],
            amount=body.amount,
            currency=body.currency,
            approval_threshold=body.approval_threshold,
            actor_user_id=ctx["user_id"],
            request_id=ctx["request_id"],
        )
    except CampaignsError as e:
        raise_campaigns_http(e)
    return CampaignBudgetOut(**budget.__dict__)


# ── Approvals ─────────────────────────────────────────────────────────────────

@campaigns_router.get("/{campaign_id}/approvals", response_model=list[CampaignApprovalOut])
def list_approvals(
    campaign_id: int,
    ctx: dict = Depends(require_org_campaign_permission("campaign.view")),
) -> list[CampaignApprovalOut]:
    try:
        items = CampaignApprovalUseCases(ctx["conn"]).list(campaign_id, ctx["organization_id"])
    except CampaignsError as e:
        raise_campaigns_http(e)
    return [CampaignApprovalOut(**a.__dict__) for a in items]


@campaigns_router.post("/{campaign_id}/approvals", response_model=CampaignApprovalOut, status_code=201)
def submit_approval(
    campaign_id: int,
    body: CampaignApprovalSubmitRequest,
    ctx: dict = Depends(require_org_campaign_permission("campaign.update")),
) -> CampaignApprovalOut:
    try:
        approval = CampaignApprovalUseCases(ctx["conn"]).submit(
            campaign_id, ctx["organization_id"],
            approval_type=body.approval_type,
            actor_user_id=ctx["user_id"],
            request_id=ctx["request_id"],
        )
    except CampaignsError as e:
        raise_campaigns_http(e)
    return CampaignApprovalOut(**approval.__dict__)


@campaigns_router.post("/approvals/{approval_id}/decide", response_model=CampaignApprovalOut)
def decide_approval(
    approval_id: int,
    body: CampaignApprovalDecideRequest,
    ctx: dict = Depends(require_org_campaign_permission("campaign.approve")),
) -> CampaignApprovalOut:
    try:
        approval = CampaignApprovalUseCases(ctx["conn"]).decide(
            approval_id, ctx["organization_id"],
            approved=body.approved,
            actor_user_id=ctx["user_id"],
            reason=body.reason,
            request_id=ctx["request_id"],
        )
    except CampaignsError as e:
        raise_campaigns_http(e)
    return CampaignApprovalOut(**approval.__dict__)


# ── Expenses ──────────────────────────────────────────────────────────────────

@campaigns_router.get("/{campaign_id}/expenses", response_model=list[CampaignExpenseOut])
def list_expenses(
    campaign_id: int,
    ctx: dict = Depends(require_org_campaign_permission("campaign.view")),
) -> list[CampaignExpenseOut]:
    try:
        items = CampaignExpenseUseCases(ctx["conn"]).list(campaign_id, ctx["organization_id"])
    except CampaignsError as e:
        raise_campaigns_http(e)
    return [CampaignExpenseOut(**e.__dict__) for e in items]


@campaigns_router.post("/{campaign_id}/expenses", response_model=CampaignExpenseOut, status_code=201)
def add_expense(
    campaign_id: int,
    body: CampaignExpenseCreateRequest,
    ctx: dict = Depends(require_org_campaign_permission("campaign.expense")),
) -> CampaignExpenseOut:
    try:
        expense = CampaignExpenseUseCases(ctx["conn"]).add(
            campaign_id, ctx["organization_id"],
            amount=body.amount,
            currency=body.currency,
            category=body.category,
            expense_date=body.expense_date,
            description=body.description,
            actor_user_id=ctx["user_id"],
            override_id=body.override_id,
            request_id=ctx["request_id"],
        )
    except CampaignsError as e:
        raise_campaigns_http(e)
    return CampaignExpenseOut(**expense.__dict__)


# ── Results ───────────────────────────────────────────────────────────────────

@campaigns_router.get("/{campaign_id}/results", response_model=list[CampaignResultOut])
def list_results(
    campaign_id: int,
    ctx: dict = Depends(require_org_campaign_permission("campaign.view")),
) -> list[CampaignResultOut]:
    try:
        items = CampaignResultUseCases(ctx["conn"]).list(campaign_id, ctx["organization_id"])
    except CampaignsError as e:
        raise_campaigns_http(e)
    return [CampaignResultOut(**r.__dict__) for r in items]


@campaigns_router.post("/{campaign_id}/results", response_model=CampaignResultOut, status_code=201)
def record_result(
    campaign_id: int,
    body: CampaignResultCreateRequest,
    ctx: dict = Depends(require_org_campaign_permission("campaign.update")),
) -> CampaignResultOut:
    try:
        result = CampaignResultUseCases(ctx["conn"]).record(
            campaign_id, ctx["organization_id"],
            metric_code=body.metric_code,
            value=body.value,
            unit=body.unit,
            is_monetary=body.is_monetary,
            period_start=body.period_start,
            period_end=body.period_end,
            source_label=body.source_label,
            actor_user_id=ctx["user_id"],
            request_id=ctx["request_id"],
        )
    except CampaignsError as e:
        raise_campaigns_http(e)
    return CampaignResultOut(**result.__dict__)


# ── Attribution & Revenue ─────────────────────────────────────────────────────

@campaigns_router.post(
    "/{campaign_id}/attribution-definitions",
    response_model=AttributionDefinitionOut,
    status_code=201,
)
def create_attribution_definition(
    campaign_id: int,
    body: AttributionDefinitionCreateRequest,
    ctx: dict = Depends(require_org_campaign_permission("campaign.update")),
) -> AttributionDefinitionOut:
    try:
        definition = AttributionDefinitionUseCases(ctx["conn"]).create(
            campaign_id, ctx["organization_id"],
            model_code=body.model_code,
            confidence=body.confidence,
            responsible=body.responsible,
            description=body.description,
            actor_user_id=ctx["user_id"],
            request_id=ctx["request_id"],
        )
    except CampaignsError as e:
        raise_campaigns_http(e)
    return AttributionDefinitionOut(**definition.__dict__)


@campaigns_router.post(
    "/attribution-definitions/{definition_id}/approve",
    response_model=AttributionDefinitionOut,
)
def approve_attribution_definition(
    definition_id: int,
    ctx: dict = Depends(require_org_campaign_permission("campaign.approve")),
) -> AttributionDefinitionOut:
    try:
        definition = AttributionDefinitionUseCases(ctx["conn"]).approve(
            definition_id, ctx["organization_id"],
            actor_user_id=ctx["user_id"],
            request_id=ctx["request_id"],
        )
    except CampaignsError as e:
        raise_campaigns_http(e)
    return AttributionDefinitionOut(**definition.__dict__)


@campaigns_router.post(
    "/{campaign_id}/attributable-revenue",
    response_model=AttributableRevenueOut,
    status_code=201,
)
def record_attributable_revenue(
    campaign_id: int,
    body: AttributableRevenueCreateRequest,
    ctx: dict = Depends(require_org_campaign_permission("campaign.update")),
) -> AttributableRevenueOut:
    try:
        record = AttributableRevenueUseCases(ctx["conn"]).record(
            campaign_id, ctx["organization_id"],
            attribution_definition_id=body.attribution_definition_id,
            amount=body.amount,
            currency=body.currency,
            period_start=body.period_start,
            period_end=body.period_end,
            actor_user_id=ctx["user_id"],
            request_id=ctx["request_id"],
        )
    except CampaignsError as e:
        raise_campaigns_http(e)
    return AttributableRevenueOut(**record.__dict__)


@campaigns_router.post(
    "/attributable-revenue/{record_id}/approve",
    response_model=AttributableRevenueOut,
)
def approve_attributable_revenue(
    record_id: int,
    ctx: dict = Depends(require_org_campaign_permission("campaign.approve")),
) -> AttributableRevenueOut:
    try:
        record = AttributableRevenueUseCases(ctx["conn"]).approve(
            record_id, ctx["organization_id"],
            actor_user_id=ctx["user_id"],
            request_id=ctx["request_id"],
        )
    except CampaignsError as e:
        raise_campaigns_http(e)
    return AttributableRevenueOut(**record.__dict__)


# ── ROI ───────────────────────────────────────────────────────────────────────

@campaigns_router.get("/{campaign_id}/roi", response_model=Optional[CampaignRoiSnapshotOut])
def get_roi(
    campaign_id: int,
    ctx: dict = Depends(require_org_campaign_permission("campaign.view")),
) -> Optional[CampaignRoiSnapshotOut]:
    try:
        snapshot = CampaignRoiUseCases(ctx["conn"]).get_latest(campaign_id, ctx["organization_id"])
    except CampaignsError as e:
        raise_campaigns_http(e)
    return CampaignRoiSnapshotOut(**snapshot.__dict__) if snapshot else None


@campaigns_router.post("/{campaign_id}/roi/compute", response_model=CampaignRoiSnapshotOut)
def compute_roi(
    campaign_id: int,
    ctx: dict = Depends(require_org_campaign_permission("campaign.view")),
) -> CampaignRoiSnapshotOut:
    try:
        snapshot = CampaignRoiUseCases(ctx["conn"]).compute_snapshot(
            campaign_id, ctx["organization_id"],
            actor_user_id=ctx["user_id"],
            request_id=ctx["request_id"],
        )
    except CampaignsError as e:
        raise_campaigns_http(e)
    return CampaignRoiSnapshotOut(**snapshot.__dict__)
