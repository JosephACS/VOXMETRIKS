"""CRM HTTP router — Spec 017 · /api/v1/crm."""

from __future__ import annotations

import json
from typing import Any, Optional

import duckdb
from fastapi import APIRouter, Depends, Query

from app.core.config import get_settings
from app.core.database import get_write_conn
from app.packages.crm.application.use_cases import (
    ActivityUseCases,
    ApprovalUseCases,
    ContactUseCases,
    ConversionUseCases,
    OpportunityUseCases,
    ProspectUseCases,
    QuotationUseCases,
)
from app.packages.crm.domain.entities import (
    ApprovalRequest,
    Contact,
    CustomerConversion,
    Opportunity,
    OpportunityStageHistory,
    Prospect,
    ProspectContact,
    QuotationItem,
    QuotationVersion,
    Quotation,
    SalesActivity,
)
from app.packages.crm.presentation.dependencies import (
    require_crm_permission,
    require_org_owner,
    request_id_header,
)
from app.packages.crm.presentation.error_mapping import raise_crm_http
from app.packages.crm.presentation.schemas import (
    ActivityCreateRequest,
    ActivityOut,
    ActivityUpdateRequest,
    ApprovalOut,
    ApprovalReviewRequest,
    AuditEntryOut,
    ClaimConversionRequest,
    ConfirmLinkRequest,
    ContactCreateRequest,
    ContactOut,
    ContactUpdateRequest,
    ConversionOut,
    ConversionPrepareRequest,
    ConversionPrepareResponse,
    DiscountApprovalRequest,
    LinkContactRequest,
    OpportunityCloseRequest,
    OpportunityCreateRequest,
    OpportunityOut,
    OpportunityStageRequest,
    OpportunityUpdateRequest,
    PaginatedActivities,
    PaginatedApprovals,
    PaginatedAudit,
    PaginatedContacts,
    PaginatedConversions,
    PaginatedOpportunities,
    PaginatedProspects,
    PaginatedQuotations,
    ProspectContactOut,
    ProspectCreateRequest,
    ProspectOut,
    ProspectStatusRequest,
    ProspectUpdateRequest,
    QuotationCreateRequest,
    QuotationItemCreateRequest,
    QuotationItemOut,
    QuotationOut,
    QuotationVersionCreateRequest,
    QuotationVersionOut,
    SendVersionRequest,
    StageHistoryOut,
)
from app.packages.identity.services.auth_deps import require_user_id

router = APIRouter(prefix="/crm", tags=["CRM"])


def _page_bounds(page: int, limit: int, max_limit: int = 100) -> tuple[int, int, int]:
    page = max(1, page)
    lim = min(max(1, limit), max_limit)
    offset = (page - 1) * lim
    return page, lim, offset


# ── Permissions discovery ─────────────────────────────────────────────────────

@router.get("/permissions")
def get_my_crm_permissions(
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    """Return CRM-relevant permissions and roles for the current user.

    Requires authentication only; returns empty lists if no CRM roles are assigned.
    Used by the Angular frontend to determine UI access without exposing
    all platform permissions.
    """
    from app.packages.platform_rbac.infrastructure.repository import (
        list_permissions,
        list_user_platform_roles,
    )

    all_perms = list_permissions(conn, user_id)
    all_roles = list_user_platform_roles(conn, user_id)
    crm_domains = ("crm.", "quotation.", "contract.", "customer.")
    crm_perms = [p for p in all_perms if any(p.startswith(d) for d in crm_domains)]
    crm_roles = [r for r in all_roles if r in ("sales_agent", "sales_manager", "platform_admin", "auditor")]
    return {"permissions": crm_perms, "roles": crm_roles}


# ── Prospect serialization ────────────────────────────────────────────────────

def _prospect_out(p: Prospect) -> ProspectOut:
    return ProspectOut(
        id=p.id,
        display_name=p.display_name,
        company_name=p.company_name,
        email=p.email,
        phone=p.phone,
        source=p.source,
        status=p.status,
        owner_user_id=p.owner_user_id,
        organization_id=p.organization_id,
        notes=p.notes,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


def _contact_out(c: Contact) -> ContactOut:
    return ContactOut(
        id=c.id,
        full_name=c.full_name,
        email=c.email,
        phone=c.phone,
        company_name=c.company_name,
        linked_user_id=c.linked_user_id,
        created_by=c.created_by,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


def _opp_out(o: Opportunity) -> OpportunityOut:
    return OpportunityOut(
        id=o.id,
        prospect_id=o.prospect_id,
        name=o.name,
        description=o.description,
        stage=o.stage,
        probability=o.probability,
        expected_value=o.expected_value,
        currency=o.currency,
        expected_close_date=o.expected_close_date,
        actual_close_date=o.actual_close_date,
        outcome=o.outcome,
        owner_user_id=o.owner_user_id,
        organization_id=o.organization_id,
        created_at=o.created_at,
        updated_at=o.updated_at,
    )


def _activity_out(a: SalesActivity) -> ActivityOut:
    return ActivityOut(
        id=a.id,
        activity_type=a.activity_type,
        subject=a.subject,
        body=a.body,
        outcome=a.outcome,
        prospect_id=a.prospect_id,
        contact_id=a.contact_id,
        opportunity_id=a.opportunity_id,
        actor_user_id=a.actor_user_id,
        scheduled_at=a.scheduled_at,
        completed_at=a.completed_at,
        status=a.status,
        created_at=a.created_at,
        updated_at=a.updated_at,
    )


def _quotation_out(q: Quotation) -> QuotationOut:
    return QuotationOut(
        id=q.id,
        opportunity_id=q.opportunity_id,
        status=q.status,
        currency=q.currency,
        notes=q.notes,
        row_version=q.row_version,
        current_version_no=q.current_version_no,
        created_by=q.created_by,
        created_at=q.created_at,
        updated_at=q.updated_at,
    )


def _version_out(v: QuotationVersion) -> QuotationVersionOut:
    return QuotationVersionOut(
        id=v.id,
        quotation_id=v.quotation_id,
        version_no=v.version_no,
        status=v.status,
        subtotal=v.subtotal,
        discount_pct=v.discount_pct,
        discount_requires_approval=v.discount_requires_approval,
        total=v.total,
        notes=v.notes,
        sent_at=v.sent_at,
        accepted_at=v.accepted_at,
        rejected_at=v.rejected_at,
        is_immutable=v.is_immutable,
        created_by=v.created_by,
        created_at=v.created_at,
    )


def _item_out(i: QuotationItem) -> QuotationItemOut:
    return QuotationItemOut(
        id=i.id,
        quotation_version_id=i.quotation_version_id,
        description=i.description,
        quantity=i.quantity,
        unit_price=i.unit_price,
        discount_pct=i.discount_pct,
        line_total=i.line_total,
        plan_code=i.plan_code,
        sort_order=i.sort_order,
        created_at=i.created_at,
    )


def _approval_out(a: ApprovalRequest) -> ApprovalOut:
    return ApprovalOut(
        id=a.id,
        object_type=a.object_type,
        object_id=a.object_id,
        reason=a.reason,
        threshold_ref=a.threshold_ref,
        status=a.status,
        requested_by=a.requested_by,
        reviewed_by=a.reviewed_by,
        review_note=a.review_note,
        requested_at=a.requested_at,
        reviewed_at=a.reviewed_at,
        created_at=a.created_at,
        updated_at=a.updated_at,
    )


def _conversion_out(c: CustomerConversion) -> ConversionOut:
    return ConversionOut(
        id=c.id,
        opportunity_id=c.opportunity_id,
        mode=c.mode,
        status=c.status,
        organization_id=c.organization_id,
        contact_id=c.contact_id,
        signatory_user_id=c.signatory_user_id,
        claim_token_expires_at=c.claim_token_expires_at,
        claim_consumed_at=c.claim_consumed_at,
        idempotency_key=c.idempotency_key,
        requested_by=c.requested_by,
        completed_at=c.completed_at,
        failure_reason=c.failure_reason,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


# ── Prospects ─────────────────────────────────────────────────────────────────

@router.post("/prospects", status_code=201, response_model=ProspectOut)
def create_prospect(
    body: ProspectCreateRequest,
    actor: dict = Depends(require_crm_permission("crm.prospect.create")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        p = ProspectUseCases(conn).create(
            actor_user_id=actor["user_id"],
            display_name=body.display_name,
            company_name=body.company_name,
            email=body.email,
            phone=body.phone,
            source=body.source,
            notes=body.notes,
            request_id=actor["request_id"],
        )
        return _prospect_out(p)
    except Exception as exc:
        raise_crm_http(exc)


@router.get("/prospects", response_model=PaginatedProspects)
def list_prospects(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    status: Optional[str] = Query(None),
    actor: dict = Depends(require_crm_permission("crm.prospect.view")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        page, lim, offset = _page_bounds(page, limit)
        items, total = ProspectUseCases(conn).list(status=status, limit=lim, offset=offset)
        return PaginatedProspects(items=[_prospect_out(p) for p in items], page=page, limit=lim, total=total)
    except Exception as exc:
        raise_crm_http(exc)


@router.get("/prospects/{prospect_id}", response_model=ProspectOut)
def get_prospect(
    prospect_id: int,
    actor: dict = Depends(require_crm_permission("crm.prospect.view")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        return _prospect_out(ProspectUseCases(conn).get(prospect_id))
    except Exception as exc:
        raise_crm_http(exc)


@router.patch("/prospects/{prospect_id}", response_model=ProspectOut)
def update_prospect(
    prospect_id: int,
    body: ProspectUpdateRequest,
    actor: dict = Depends(require_crm_permission("crm.prospect.update")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        p = ProspectUseCases(conn).update(
            prospect_id,
            actor_user_id=actor["user_id"],
            display_name=body.display_name,
            company_name=body.company_name,
            email=body.email,
            phone=body.phone,
            source=body.source,
            notes=body.notes,
            request_id=actor["request_id"],
        )
        return _prospect_out(p)
    except Exception as exc:
        raise_crm_http(exc)


@router.post("/prospects/{prospect_id}/status", response_model=ProspectOut)
def transition_prospect_status(
    prospect_id: int,
    body: ProspectStatusRequest,
    actor: dict = Depends(require_crm_permission("crm.prospect.update")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        p = ProspectUseCases(conn).transition_status(
            prospect_id,
            actor_user_id=actor["user_id"],
            new_status=body.status,
            request_id=actor["request_id"],
        )
        return _prospect_out(p)
    except Exception as exc:
        raise_crm_http(exc)


@router.post("/prospects/{prospect_id}/contacts", response_model=ProspectContactOut)
def link_contact_to_prospect(
    prospect_id: int,
    body: LinkContactRequest,
    actor: dict = Depends(require_crm_permission("crm.prospect.update")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        pc = ContactUseCases(conn).link_to_prospect(
            prospect_id=prospect_id,
            contact_id=body.contact_id,
            actor_user_id=actor["user_id"],
            is_primary=body.is_primary,
            is_decision_maker=body.is_decision_maker,
            is_signatory=body.is_signatory,
        )
        return ProspectContactOut(
            prospect_id=pc.prospect_id,
            contact_id=pc.contact_id,
            is_primary=pc.is_primary,
            is_decision_maker=pc.is_decision_maker,
            is_signatory=pc.is_signatory,
            added_at=pc.added_at,
        )
    except Exception as exc:
        raise_crm_http(exc)


# ── Contacts ──────────────────────────────────────────────────────────────────

@router.post("/contacts", status_code=201, response_model=ContactOut)
def create_contact(
    body: ContactCreateRequest,
    actor: dict = Depends(require_crm_permission("crm.prospect.create")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        c = ContactUseCases(conn).create(
            actor_user_id=actor["user_id"],
            full_name=body.full_name,
            email=body.email,
            phone=body.phone,
            company_name=body.company_name,
            request_id=actor["request_id"],
        )
        return _contact_out(c)
    except Exception as exc:
        raise_crm_http(exc)


@router.get("/contacts", response_model=PaginatedContacts)
def list_contacts(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    actor: dict = Depends(require_crm_permission("crm.prospect.view")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        page, lim, offset = _page_bounds(page, limit)
        items, total = ContactUseCases(conn).list(limit=lim, offset=offset)
        return PaginatedContacts(items=[_contact_out(c) for c in items], page=page, limit=lim, total=total)
    except Exception as exc:
        raise_crm_http(exc)


@router.get("/contacts/{contact_id}", response_model=ContactOut)
def get_contact(
    contact_id: int,
    actor: dict = Depends(require_crm_permission("crm.prospect.view")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        return _contact_out(ContactUseCases(conn).get(contact_id))
    except Exception as exc:
        raise_crm_http(exc)


@router.patch("/contacts/{contact_id}", response_model=ContactOut)
def update_contact(
    contact_id: int,
    body: ContactUpdateRequest,
    actor: dict = Depends(require_crm_permission("crm.prospect.update")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        c = ContactUseCases(conn).update(
            contact_id,
            actor_user_id=actor["user_id"],
            full_name=body.full_name,
            email=body.email,
            phone=body.phone,
            company_name=body.company_name,
            request_id=actor["request_id"],
        )
        return _contact_out(c)
    except Exception as exc:
        raise_crm_http(exc)


# ── Opportunities ─────────────────────────────────────────────────────────────

@router.post("/opportunities", status_code=201, response_model=OpportunityOut)
def create_opportunity(
    body: OpportunityCreateRequest,
    actor: dict = Depends(require_crm_permission("crm.opportunity.create")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        o = OpportunityUseCases(conn).create(
            actor_user_id=actor["user_id"],
            prospect_id=body.prospect_id,
            name=body.name,
            description=body.description,
            expected_value=body.expected_value,
            currency=body.currency,
            probability=body.probability,
            expected_close_date=body.expected_close_date,
            request_id=actor["request_id"],
        )
        return _opp_out(o)
    except Exception as exc:
        raise_crm_http(exc)


@router.get("/opportunities", response_model=PaginatedOpportunities)
def list_opportunities(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    stage: Optional[str] = Query(None),
    prospect_id: Optional[int] = Query(None),
    actor: dict = Depends(require_crm_permission("crm.opportunity.view")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        page, lim, offset = _page_bounds(page, limit)
        items, total = OpportunityUseCases(conn).list(stage=stage, prospect_id=prospect_id, limit=lim, offset=offset)
        return PaginatedOpportunities(items=[_opp_out(o) for o in items], page=page, limit=lim, total=total)
    except Exception as exc:
        raise_crm_http(exc)


@router.get("/opportunities/{opportunity_id}", response_model=OpportunityOut)
def get_opportunity(
    opportunity_id: int,
    actor: dict = Depends(require_crm_permission("crm.opportunity.view")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        return _opp_out(OpportunityUseCases(conn).get(opportunity_id))
    except Exception as exc:
        raise_crm_http(exc)


@router.patch("/opportunities/{opportunity_id}", response_model=OpportunityOut)
def update_opportunity(
    opportunity_id: int,
    body: OpportunityUpdateRequest,
    actor: dict = Depends(require_crm_permission("crm.opportunity.update")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        o = OpportunityUseCases(conn).update(
            opportunity_id,
            actor_user_id=actor["user_id"],
            name=body.name,
            description=body.description,
            expected_value=body.expected_value,
            currency=body.currency,
            probability=body.probability,
            expected_close_date=body.expected_close_date,
            request_id=actor["request_id"],
        )
        return _opp_out(o)
    except Exception as exc:
        raise_crm_http(exc)


@router.post("/opportunities/{opportunity_id}/stage", response_model=OpportunityOut)
def advance_opportunity_stage(
    opportunity_id: int,
    body: OpportunityStageRequest,
    actor: dict = Depends(require_crm_permission("crm.opportunity.update")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        o = OpportunityUseCases(conn).advance_stage(
            opportunity_id,
            actor_user_id=actor["user_id"],
            new_stage=body.stage,
            reason=body.reason,
            request_id=actor["request_id"],
        )
        return _opp_out(o)
    except Exception as exc:
        raise_crm_http(exc)


@router.post("/opportunities/{opportunity_id}/close", response_model=OpportunityOut)
def close_opportunity(
    opportunity_id: int,
    body: OpportunityCloseRequest,
    actor: dict = Depends(require_crm_permission("crm.opportunity.close")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        o = OpportunityUseCases(conn).close(
            opportunity_id,
            actor_user_id=actor["user_id"],
            outcome=body.outcome,
            new_stage=body.stage,
            reason=body.reason,
            request_id=actor["request_id"],
        )
        return _opp_out(o)
    except Exception as exc:
        raise_crm_http(exc)


@router.get("/opportunities/{opportunity_id}/stage-history", response_model=list[StageHistoryOut])
def get_stage_history(
    opportunity_id: int,
    actor: dict = Depends(require_crm_permission("crm.opportunity.view")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        history = OpportunityUseCases(conn).stage_history(opportunity_id)
        return [
            StageHistoryOut(
                id=h.id,
                opportunity_id=h.opportunity_id,
                from_stage=h.from_stage,
                to_stage=h.to_stage,
                actor_user_id=h.actor_user_id,
                reason=h.reason,
                occurred_at=h.occurred_at,
            )
            for h in history
        ]
    except Exception as exc:
        raise_crm_http(exc)


# ── Activities ────────────────────────────────────────────────────────────────

@router.post("/activities", status_code=201, response_model=ActivityOut)
def create_activity(
    body: ActivityCreateRequest,
    actor: dict = Depends(require_crm_permission("crm.activity.manage")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        a = ActivityUseCases(conn).create(
            actor_user_id=actor["user_id"],
            activity_type=body.activity_type,
            subject=body.subject,
            body=body.body,
            prospect_id=body.prospect_id,
            contact_id=body.contact_id,
            opportunity_id=body.opportunity_id,
            scheduled_at=body.scheduled_at,
            request_id=actor["request_id"],
        )
        return _activity_out(a)
    except Exception as exc:
        raise_crm_http(exc)


@router.get("/activities", response_model=PaginatedActivities)
def list_activities(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    opportunity_id: Optional[int] = Query(None),
    prospect_id: Optional[int] = Query(None),
    actor: dict = Depends(require_crm_permission("crm.activity.manage")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        page, lim, offset = _page_bounds(page, limit)
        items, total = ActivityUseCases(conn).list(
            opportunity_id=opportunity_id, prospect_id=prospect_id, limit=lim, offset=offset
        )
        return PaginatedActivities(items=[_activity_out(a) for a in items], page=page, limit=lim, total=total)
    except Exception as exc:
        raise_crm_http(exc)


@router.get("/activities/{activity_id}", response_model=ActivityOut)
def get_activity(
    activity_id: int,
    actor: dict = Depends(require_crm_permission("crm.activity.manage")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        return _activity_out(ActivityUseCases(conn).get(activity_id))
    except Exception as exc:
        raise_crm_http(exc)


@router.patch("/activities/{activity_id}", response_model=ActivityOut)
def update_activity(
    activity_id: int,
    body: ActivityUpdateRequest,
    actor: dict = Depends(require_crm_permission("crm.activity.manage")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        a = ActivityUseCases(conn).update(
            activity_id,
            actor_user_id=actor["user_id"],
            subject=body.subject,
            body=body.body,
            outcome=body.outcome,
            status=body.status,
            completed_at=body.completed_at,
            request_id=actor["request_id"],
        )
        return _activity_out(a)
    except Exception as exc:
        raise_crm_http(exc)


# ── Quotations ────────────────────────────────────────────────────────────────

@router.post("/quotations", status_code=201, response_model=QuotationOut)
def create_quotation(
    body: QuotationCreateRequest,
    actor: dict = Depends(require_crm_permission("quotation.create")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        q = QuotationUseCases(conn).create(
            actor_user_id=actor["user_id"],
            opportunity_id=body.opportunity_id,
            currency=body.currency,
            notes=body.notes,
            request_id=actor["request_id"],
        )
        return _quotation_out(q)
    except Exception as exc:
        raise_crm_http(exc)


@router.get("/quotations", response_model=PaginatedQuotations)
def list_quotations(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    opportunity_id: Optional[int] = Query(None),
    actor: dict = Depends(require_crm_permission("quotation.create")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        page, lim, offset = _page_bounds(page, limit)
        items, total = QuotationUseCases(conn).list(opportunity_id=opportunity_id, limit=lim, offset=offset)
        return PaginatedQuotations(items=[_quotation_out(q) for q in items], page=page, limit=lim, total=total)
    except Exception as exc:
        raise_crm_http(exc)


@router.get("/quotations/{quotation_id}", response_model=QuotationOut)
def get_quotation(
    quotation_id: int,
    actor: dict = Depends(require_crm_permission("quotation.create")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        return _quotation_out(QuotationUseCases(conn).get(quotation_id))
    except Exception as exc:
        raise_crm_http(exc)


@router.post("/quotations/{quotation_id}/versions", status_code=201, response_model=QuotationVersionOut)
def create_quotation_version(
    quotation_id: int,
    body: QuotationVersionCreateRequest,
    actor: dict = Depends(require_crm_permission("quotation.create")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        v = QuotationUseCases(conn).create_version(
            quotation_id,
            actor_user_id=actor["user_id"],
            notes=body.notes,
            request_id=actor["request_id"],
        )
        return _version_out(v)
    except Exception as exc:
        raise_crm_http(exc)


@router.get("/quotations/{quotation_id}/versions", response_model=list[QuotationVersionOut])
def list_quotation_versions(
    quotation_id: int,
    actor: dict = Depends(require_crm_permission("quotation.create")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        versions = QuotationUseCases(conn).list_versions(quotation_id)
        return [_version_out(v) for v in versions]
    except Exception as exc:
        raise_crm_http(exc)


@router.get("/quotation-versions/{version_id}", response_model=QuotationVersionOut)
def get_quotation_version(
    version_id: int,
    actor: dict = Depends(require_crm_permission("quotation.create")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        return _version_out(QuotationUseCases(conn).get_version(version_id))
    except Exception as exc:
        raise_crm_http(exc)


@router.post("/quotation-versions/{version_id}/items", status_code=201, response_model=QuotationItemOut)
def add_quotation_item(
    version_id: int,
    body: QuotationItemCreateRequest,
    actor: dict = Depends(require_crm_permission("quotation.update")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        item = QuotationUseCases(conn).add_item(
            version_id,
            actor_user_id=actor["user_id"],
            description=body.description,
            quantity=body.quantity,
            unit_price=body.unit_price,
            discount_pct=body.discount_pct,
            plan_code=body.plan_code,
            sort_order=body.sort_order,
            request_id=actor["request_id"],
        )
        return _item_out(item)
    except Exception as exc:
        raise_crm_http(exc)


@router.get("/quotation-versions/{version_id}/items", response_model=list[QuotationItemOut])
def list_quotation_items(
    version_id: int,
    actor: dict = Depends(require_crm_permission("quotation.create")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        items = QuotationUseCases(conn).list_items(version_id)
        return [_item_out(i) for i in items]
    except Exception as exc:
        raise_crm_http(exc)


@router.post("/quotation-versions/{version_id}/send", response_model=QuotationVersionOut)
def send_quotation_version(
    version_id: int,
    body: SendVersionRequest,
    actor: dict = Depends(require_crm_permission("quotation.send")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        settings = get_settings()
        threshold = settings.crm_discount_approval_threshold
        v = QuotationUseCases(conn).send_version(
            version_id,
            actor_user_id=actor["user_id"],
            discount_approval_threshold=threshold,
            request_id=actor["request_id"],
        )
        return _version_out(v)
    except Exception as exc:
        raise_crm_http(exc)


@router.post("/quotation-versions/{version_id}/accept", response_model=QuotationVersionOut)
def accept_quotation_version(
    version_id: int,
    actor: dict = Depends(require_crm_permission("quotation.send")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        v = QuotationUseCases(conn).accept_version(
            version_id,
            actor_user_id=actor["user_id"],
            request_id=actor["request_id"],
        )
        return _version_out(v)
    except Exception as exc:
        raise_crm_http(exc)


@router.post("/quotation-versions/{version_id}/request-approval", status_code=201, response_model=ApprovalOut)
def request_discount_approval(
    version_id: int,
    body: DiscountApprovalRequest,
    actor: dict = Depends(require_crm_permission("quotation.create")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        ar = QuotationUseCases(conn).request_discount_approval(
            version_id,
            actor_user_id=actor["user_id"],
            reason=body.reason,
            request_id=actor["request_id"],
        )
        return _approval_out(ar)
    except Exception as exc:
        raise_crm_http(exc)


# ── Approvals ─────────────────────────────────────────────────────────────────

@router.get("/approvals", response_model=PaginatedApprovals)
def list_approvals(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    actor: dict = Depends(require_crm_permission("quotation.approve")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        page, lim, offset = _page_bounds(page, limit)
        items, total = ApprovalUseCases(conn).list_pending(limit=lim, offset=offset)
        return PaginatedApprovals(items=[_approval_out(a) for a in items], page=page, limit=lim, total=total)
    except Exception as exc:
        raise_crm_http(exc)


@router.get("/approvals/{approval_id}", response_model=ApprovalOut)
def get_approval(
    approval_id: int,
    actor: dict = Depends(require_crm_permission("quotation.approve")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        return _approval_out(ApprovalUseCases(conn).get(approval_id))
    except Exception as exc:
        raise_crm_http(exc)


@router.post("/approvals/{approval_id}/approve", response_model=ApprovalOut)
def approve_request(
    approval_id: int,
    body: ApprovalReviewRequest,
    actor: dict = Depends(require_crm_permission("quotation.approve")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        ar = ApprovalUseCases(conn).approve(
            approval_id,
            actor_user_id=actor["user_id"],
            review_note=body.review_note,
            request_id=actor["request_id"],
        )
        return _approval_out(ar)
    except Exception as exc:
        raise_crm_http(exc)


@router.post("/approvals/{approval_id}/reject", response_model=ApprovalOut)
def reject_request(
    approval_id: int,
    body: ApprovalReviewRequest,
    actor: dict = Depends(require_crm_permission("quotation.approve")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        ar = ApprovalUseCases(conn).reject(
            approval_id,
            actor_user_id=actor["user_id"],
            review_note=body.review_note,
            request_id=actor["request_id"],
        )
        return _approval_out(ar)
    except Exception as exc:
        raise_crm_http(exc)


# ── Conversions ───────────────────────────────────────────────────────────────

@router.post("/conversions", status_code=201, response_model=ConversionPrepareResponse)
def prepare_conversion(
    body: ConversionPrepareRequest,
    actor: dict = Depends(require_crm_permission("customer.convert")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        conv, raw_token = ConversionUseCases(conn).prepare(
            actor_user_id=actor["user_id"],
            opportunity_id=body.opportunity_id,
            mode=body.mode,
            contact_id=body.contact_id,
            idempotency_key=body.idempotency_key,
            request_id=actor["request_id"],
        )
        note = "Token returned once. Store securely and provide to signatory." if raw_token else None
        return ConversionPrepareResponse(
            conversion=_conversion_out(conv),
            claim_token=raw_token,
            claim_token_note=note,
        )
    except Exception as exc:
        raise_crm_http(exc)


@router.get("/conversions", response_model=PaginatedConversions)
def list_conversions(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    opportunity_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    actor: dict = Depends(require_crm_permission("customer.convert")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        page, lim, offset = _page_bounds(page, limit)
        items, total = ConversionUseCases(conn).list(
            opportunity_id=opportunity_id, status=status, limit=lim, offset=offset
        )
        return PaginatedConversions(items=[_conversion_out(c) for c in items], page=page, limit=lim, total=total)
    except Exception as exc:
        raise_crm_http(exc)


@router.get("/conversions/{conversion_id}", response_model=ConversionOut)
def get_conversion(
    conversion_id: int,
    actor: dict = Depends(require_crm_permission("customer.convert")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        return _conversion_out(ConversionUseCases(conn).get(conversion_id))
    except Exception as exc:
        raise_crm_http(exc)


@router.post("/conversions/{conversion_id}/confirm-link", response_model=ConversionOut)
def confirm_link_conversion(
    conversion_id: int,
    body: ConfirmLinkRequest,
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
    request_id: str = Depends(request_id_header),
):
    """Path A: authenticated OWNER of organization confirms the link.

    No CRM platform role required — requires being an active org owner.
    """
    try:
        # Verify org ownership
        row = conn.execute(
            """
            SELECT 1
            FROM app_organization_member m
            JOIN app_member_role mr ON mr.member_id = m.id AND mr.status = 'active'
            JOIN app_business_role br ON br.id = mr.role_id AND br.code = 'owner'
            WHERE m.organization_id = ? AND m.user_id = ? AND m.status = 'active'
            LIMIT 1
            """,
            [body.organization_id, user_id],
        ).fetchone()
        if not row:
            from app.packages.crm.presentation.error_mapping import http_error
            raise http_error(403, "Must be an active owner of the organization", code="not_org_owner")

        conv = ConversionUseCases(conn).confirm_link(
            conversion_id,
            actor_user_id=user_id,
            organization_id=body.organization_id,
            request_id=request_id,
        )
        return _conversion_out(conv)
    except Exception as exc:
        raise_crm_http(exc)


@router.post("/conversions/{conversion_id}/claim", response_model=ConversionOut)
def claim_conversion(
    conversion_id: int,
    body: ClaimConversionRequest,
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
    request_id: str = Depends(request_id_header),
):
    """Path B: authenticated signatory claims the token and becomes org owner.

    No CRM platform role required — any authenticated user can claim if they hold the token.
    The signatory is NOT assigned a CRM role automatically.
    """
    try:
        conv = ConversionUseCases(conn).claim(
            conversion_id,
            raw_token=body.token,
            actor_user_id=user_id,
            org_display_name=body.org_display_name,
            org_slug=body.org_slug,
            org_type=body.org_type,
            timezone=body.timezone,
            default_currency=body.default_currency,
            country_code=body.country_code,
            request_id=request_id,
        )
        return _conversion_out(conv)
    except Exception as exc:
        raise_crm_http(exc)


# ── CRM Audit ─────────────────────────────────────────────────────────────────

@router.get("/audit", response_model=PaginatedAudit)
def list_crm_audit(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    actor: dict = Depends(require_crm_permission("crm.audit.view")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        page, lim, offset = _page_bounds(page, limit, max_limit=200)
        total = int(
            conn.execute(
                "SELECT COUNT(*) FROM app_audit_log WHERE source LIKE 'crm.%' OR source LIKE 'contracts.%'"
            ).fetchone()[0]
        )
        rows = conn.execute(
            """
            SELECT id, organization_id, actor_user_id, actor_platform_role,
                   action, target_type, target_id, previous_values_json, new_values_json,
                   reason, request_id, source, result, occurred_at
            FROM app_audit_log
            WHERE source LIKE 'crm.%' OR source LIKE 'contracts.%'
            ORDER BY occurred_at DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            [lim, offset],
        ).fetchall()
        items = []
        for r in rows:
            prev = json.loads(r[7]) if r[7] else None
            new = json.loads(r[8]) if r[8] else None
            items.append(AuditEntryOut(
                id=int(r[0]),
                organization_id=int(r[1]) if r[1] is not None else None,
                actor_user_id=int(r[2]) if r[2] is not None else None,
                action=str(r[4]),
                target_type=str(r[5]),
                target_id=str(r[6]) if r[6] is not None else None,
                source=str(r[11]),
                result=str(r[12]),
                reason=r[9],
                occurred_at=r[13],
                previous_values=prev,
                new_values=new,
            ))
        return PaginatedAudit(items=items, page=page, limit=lim, total=total)
    except Exception as exc:
        raise_crm_http(exc)
