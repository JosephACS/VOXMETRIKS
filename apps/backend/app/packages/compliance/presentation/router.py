"""Compliance HTTP router — Spec 026."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.packages.compliance.application.use_cases import (
    AuditSearchUseCases,
    ConsentDefinitionUseCases,
    ConsentRecordUseCases,
    DataRequestUseCases,
    LegalHoldUseCases,
    RetentionPolicyUseCases,
    SecurityIncidentUseCases,
    SensitiveAccessUseCases,
    TermsAcceptanceUseCases,
    TermsVersionUseCases,
)
from app.packages.compliance.domain.errors import ComplianceError
from app.packages.compliance.presentation.dependencies import (
    require_authenticated_user,
    require_org_compliance_permission,
    require_platform_audit_permission,
)
from app.packages.compliance.presentation.error_mapping import raise_compliance_http
from app.packages.compliance.presentation.schemas import (
    AuditSearchOut,
    ConsentDefinitionCreateRequest,
    ConsentDefinitionOut,
    ConsentGrantRequest,
    ConsentRecordOut,
    DataRequestActionOut,
    DataRequestOut,
    DataRequestSubmitRequest,
    IncidentActionCreateRequest,
    IncidentActionOut,
    LegalHoldCreateRequest,
    LegalHoldOut,
    PaginatedAuditSearch,
    PaginatedConsentDefinitions,
    PaginatedDataRequests,
    PaginatedSecurityIncidents,
    PaginatedTermsVersions,
    RetentionExecutionOut,
    RetentionPolicyCreateRequest,
    RetentionPolicyOut,
    SecurityIncidentCreateRequest,
    SecurityIncidentOut,
    SensitiveAccessOut,
    SensitiveAccessRequest,
    TermsAcceptRequest,
    TermsAcceptanceOut,
    TermsVersionCreateRequest,
    TermsVersionOut,
)

compliance_router = APIRouter(prefix="/compliance", tags=["Compliance"])


def _page(page: int, page_size: int, max_size: int = 100) -> tuple[int, int, int]:
    page = max(1, page)
    ps = min(max(1, page_size), max_size)
    return page, ps, (page - 1) * ps


# ── Terms ─────────────────────────────────────────────────────────────────────

@compliance_router.get("/terms", response_model=PaginatedTermsVersions)
def list_terms(
    status: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    ctx: dict = Depends(require_org_compliance_permission("compliance.view")),
) -> PaginatedTermsVersions:
    p, ps, offset = _page(page, page_size)
    items, total = TermsVersionUseCases(ctx["conn"]).list(status=status, limit=ps, offset=offset)
    return PaginatedTermsVersions(
        items=[TermsVersionOut(**t.__dict__) for t in items],
        total=total, page=p, page_size=ps,
    )


@compliance_router.post("/terms", response_model=TermsVersionOut, status_code=201)
def create_terms(
    body: TermsVersionCreateRequest,
    ctx: dict = Depends(require_org_compliance_permission("compliance.manage")),
) -> TermsVersionOut:
    try:
        tv = TermsVersionUseCases(ctx["conn"]).create(
            actor_user_id=ctx["user_id"],
            version_code=body.version_code,
            title=body.title,
            content_summary=body.content_summary,
            effective_at=body.effective_at,
            request_id=ctx["request_id"],
        )
    except ComplianceError as e:
        raise_compliance_http(e)
    return TermsVersionOut(**tv.__dict__)


@compliance_router.post("/terms/{version_id}/publish", response_model=TermsVersionOut)
def publish_terms(
    version_id: int,
    ctx: dict = Depends(require_org_compliance_permission("compliance.manage")),
) -> TermsVersionOut:
    try:
        tv = TermsVersionUseCases(ctx["conn"]).publish(
            version_id, actor_user_id=ctx["user_id"], request_id=ctx["request_id"],
        )
    except ComplianceError as e:
        raise_compliance_http(e)
    return TermsVersionOut(**tv.__dict__)


@compliance_router.post("/terms/accept", response_model=TermsAcceptanceOut, status_code=201)
def accept_terms(
    body: TermsAcceptRequest,
    ctx: dict = Depends(require_authenticated_user()),
) -> TermsAcceptanceOut:
    try:
        acc = TermsAcceptanceUseCases(ctx["conn"]).accept(
            user_id=ctx["user_id"],
            terms_version_id=body.terms_version_id,
            organization_id=ctx.get("organization_id"),
            ip_address=body.ip_address,
            request_id=ctx["request_id"],
        )
    except ComplianceError as e:
        raise_compliance_http(e)
    return TermsAcceptanceOut(**acc.__dict__)


@compliance_router.get("/terms/acceptances/me", response_model=list[TermsAcceptanceOut])
def my_terms_acceptances(
    ctx: dict = Depends(require_authenticated_user()),
) -> list[TermsAcceptanceOut]:
    items = TermsAcceptanceUseCases(ctx["conn"]).list_for_user(
        ctx["user_id"], organization_id=ctx.get("organization_id"),
    )
    return [TermsAcceptanceOut(**a.__dict__) for a in items]


# ── Consent ───────────────────────────────────────────────────────────────────

@compliance_router.get("/consent/definitions", response_model=PaginatedConsentDefinitions)
def list_consent_definitions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    ctx: dict = Depends(require_org_compliance_permission("compliance.view")),
) -> PaginatedConsentDefinitions:
    p, ps, offset = _page(page, page_size)
    items, total = ConsentDefinitionUseCases(ctx["conn"]).list(
        organization_id=ctx["organization_id"], limit=ps, offset=offset,
    )
    return PaginatedConsentDefinitions(
        items=[ConsentDefinitionOut(**d.__dict__) for d in items],
        total=total, page=p, page_size=ps,
    )


@compliance_router.post("/consent/definitions", response_model=ConsentDefinitionOut, status_code=201)
def create_consent_definition(
    body: ConsentDefinitionCreateRequest,
    ctx: dict = Depends(require_org_compliance_permission("compliance.manage")),
) -> ConsentDefinitionOut:
    try:
        d = ConsentDefinitionUseCases(ctx["conn"]).create(
            actor_user_id=ctx["user_id"],
            code=body.code,
            title=body.title,
            description=body.description,
            organization_id=ctx["organization_id"],
            is_required=body.is_required,
            request_id=ctx["request_id"],
        )
    except ComplianceError as e:
        raise_compliance_http(e)
    return ConsentDefinitionOut(**d.__dict__)


@compliance_router.post("/consent/grant", response_model=ConsentRecordOut, status_code=201)
def grant_consent(
    body: ConsentGrantRequest,
    ctx: dict = Depends(require_authenticated_user()),
) -> ConsentRecordOut:
    try:
        rec = ConsentRecordUseCases(ctx["conn"]).grant(
            user_id=ctx["user_id"],
            consent_definition_id=body.consent_definition_id,
            organization_id=ctx.get("organization_id"),
            request_id=ctx["request_id"],
        )
    except ComplianceError as e:
        raise_compliance_http(e)
    return ConsentRecordOut(**rec.__dict__)


@compliance_router.post("/consent/{record_id}/withdraw", response_model=ConsentRecordOut)
def withdraw_consent(
    record_id: int,
    ctx: dict = Depends(require_authenticated_user()),
) -> ConsentRecordOut:
    try:
        rec = ConsentRecordUseCases(ctx["conn"]).withdraw(
            record_id,
            user_id=ctx["user_id"],
            organization_id=ctx.get("organization_id"),
            request_id=ctx["request_id"],
        )
    except ComplianceError as e:
        raise_compliance_http(e)
    return ConsentRecordOut(**rec.__dict__)


@compliance_router.get("/consent/records/me", response_model=list[ConsentRecordOut])
def my_consent_records(
    ctx: dict = Depends(require_authenticated_user()),
) -> list[ConsentRecordOut]:
    items = ConsentRecordUseCases(ctx["conn"]).list_for_user(
        ctx["user_id"], organization_id=ctx.get("organization_id"),
    )
    return [ConsentRecordOut(**r.__dict__) for r in items]


# ── DSR (Data Subject Requests) ───────────────────────────────────────────────

@compliance_router.post("/dsr", response_model=DataRequestOut, status_code=201)
def submit_dsr(
    body: DataRequestSubmitRequest,
    ctx: dict = Depends(require_org_compliance_permission("privacy.request")),
) -> DataRequestOut:
    try:
        dr = DataRequestUseCases(ctx["conn"]).submit(
            requester_user_id=ctx["user_id"],
            organization_id=ctx["organization_id"],
            request_type=body.request_type,
            subject_user_id=body.subject_user_id,
            reason=body.reason,
            request_id=ctx["request_id"],
        )
    except ComplianceError as e:
        raise_compliance_http(e)
    return DataRequestOut(**dr.__dict__)


@compliance_router.get("/dsr", response_model=PaginatedDataRequests)
def list_dsr(
    status: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    ctx: dict = Depends(require_org_compliance_permission("compliance.view")),
) -> PaginatedDataRequests:
    p, ps, offset = _page(page, page_size)
    items, total = DataRequestUseCases(ctx["conn"]).list(
        ctx["organization_id"], status=status, limit=ps, offset=offset,
    )
    return PaginatedDataRequests(
        items=[DataRequestOut(**d.__dict__) for d in items],
        total=total, page=p, page_size=ps,
    )


@compliance_router.post("/dsr/{request_id}/export", response_model=DataRequestActionOut)
def export_dsr(
    request_id: int,
    ctx: dict = Depends(require_org_compliance_permission("privacy.export")),
) -> DataRequestActionOut:
    try:
        action = DataRequestUseCases(ctx["conn"]).export_data(
            request_id, ctx["organization_id"],
            actor_user_id=ctx["user_id"], request_id=ctx["request_id"],
        )
    except ComplianceError as e:
        raise_compliance_http(e)
    return DataRequestActionOut(**action.__dict__)


@compliance_router.post("/dsr/{request_id}/delete", response_model=DataRequestActionOut)
def process_deletion_dsr(
    request_id: int,
    ctx: dict = Depends(require_org_compliance_permission("compliance.manage")),
) -> DataRequestActionOut:
    try:
        action = DataRequestUseCases(ctx["conn"]).process_deletion(
            request_id, ctx["organization_id"],
            actor_user_id=ctx["user_id"], request_id=ctx["request_id"],
        )
    except ComplianceError as e:
        raise_compliance_http(e)
    return DataRequestActionOut(**action.__dict__)


# ── Retention ─────────────────────────────────────────────────────────────────

@compliance_router.get("/retention/policies", response_model=list[RetentionPolicyOut])
def list_retention_policies(
    ctx: dict = Depends(require_org_compliance_permission("compliance.view")),
) -> list[RetentionPolicyOut]:
    items = RetentionPolicyUseCases(ctx["conn"]).list(ctx["organization_id"])
    return [RetentionPolicyOut(**p.__dict__) for p in items]


@compliance_router.post("/retention/policies", response_model=RetentionPolicyOut, status_code=201)
def create_retention_policy(
    body: RetentionPolicyCreateRequest,
    ctx: dict = Depends(require_org_compliance_permission("compliance.manage")),
) -> RetentionPolicyOut:
    try:
        p = RetentionPolicyUseCases(ctx["conn"]).create(
            actor_user_id=ctx["user_id"],
            organization_id=ctx["organization_id"],
            data_category=body.data_category,
            retention_days=body.retention_days,
            description=body.description,
            request_id=ctx["request_id"],
        )
    except ComplianceError as e:
        raise_compliance_http(e)
    return RetentionPolicyOut(**p.__dict__)


@compliance_router.post("/retention/policies/{policy_id}/execute", response_model=RetentionExecutionOut)
def execute_retention(
    policy_id: int,
    ctx: dict = Depends(require_org_compliance_permission("compliance.manage")),
) -> RetentionExecutionOut:
    try:
        ex = RetentionPolicyUseCases(ctx["conn"]).execute(
            policy_id, ctx["organization_id"],
            actor_user_id=ctx["user_id"], request_id=ctx["request_id"],
        )
    except ComplianceError as e:
        raise_compliance_http(e)
    return RetentionExecutionOut(**ex.__dict__)


# ── Legal Hold ────────────────────────────────────────────────────────────────

@compliance_router.get("/legal-holds", response_model=list[LegalHoldOut])
def list_legal_holds(
    status: Optional[str] = Query(default=None),
    ctx: dict = Depends(require_org_compliance_permission("compliance.view")),
) -> list[LegalHoldOut]:
    items = LegalHoldUseCases(ctx["conn"]).list(ctx["organization_id"], status=status)
    return [LegalHoldOut(**h.__dict__) for h in items]


@compliance_router.post("/legal-holds", response_model=LegalHoldOut, status_code=201)
def place_legal_hold(
    body: LegalHoldCreateRequest,
    ctx: dict = Depends(require_org_compliance_permission("compliance.manage")),
) -> LegalHoldOut:
    try:
        h = LegalHoldUseCases(ctx["conn"]).place(
            actor_user_id=ctx["user_id"],
            organization_id=ctx["organization_id"],
            subject_type=body.subject_type,
            subject_id=body.subject_id,
            reason=body.reason,
            request_id=ctx["request_id"],
        )
    except ComplianceError as e:
        raise_compliance_http(e)
    return LegalHoldOut(**h.__dict__)


@compliance_router.post("/legal-holds/{hold_id}/release", response_model=LegalHoldOut)
def release_legal_hold(
    hold_id: int,
    ctx: dict = Depends(require_org_compliance_permission("compliance.manage")),
) -> LegalHoldOut:
    try:
        h = LegalHoldUseCases(ctx["conn"]).release(
            hold_id, ctx["organization_id"],
            actor_user_id=ctx["user_id"], request_id=ctx["request_id"],
        )
    except ComplianceError as e:
        raise_compliance_http(e)
    return LegalHoldOut(**h.__dict__)


# ── Security Incidents ────────────────────────────────────────────────────────

@compliance_router.get("/incidents", response_model=PaginatedSecurityIncidents)
def list_incidents(
    status: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    ctx: dict = Depends(require_org_compliance_permission("incident.manage")),
) -> PaginatedSecurityIncidents:
    p, ps, offset = _page(page, page_size)
    items, total = SecurityIncidentUseCases(ctx["conn"]).list(
        organization_id=ctx["organization_id"], status=status, limit=ps, offset=offset,
    )
    return PaginatedSecurityIncidents(
        items=[SecurityIncidentOut(**i.__dict__) for i in items],
        total=total, page=p, page_size=ps,
    )


@compliance_router.post("/incidents", response_model=SecurityIncidentOut, status_code=201)
def create_incident(
    body: SecurityIncidentCreateRequest,
    ctx: dict = Depends(require_org_compliance_permission("incident.manage")),
) -> SecurityIncidentOut:
    try:
        inc = SecurityIncidentUseCases(ctx["conn"]).create(
            actor_user_id=ctx["user_id"],
            title=body.title,
            severity=body.severity,
            description=body.description,
            organization_id=ctx["organization_id"],
            request_id=ctx["request_id"],
        )
    except ComplianceError as e:
        raise_compliance_http(e)
    return SecurityIncidentOut(**inc.__dict__)


@compliance_router.post("/incidents/{incident_id}/actions", response_model=IncidentActionOut, status_code=201)
def add_incident_action(
    incident_id: int,
    body: IncidentActionCreateRequest,
    ctx: dict = Depends(require_org_compliance_permission("incident.manage")),
) -> IncidentActionOut:
    try:
        action = SecurityIncidentUseCases(ctx["conn"]).add_action(
            incident_id,
            actor_user_id=ctx["user_id"],
            action_type=body.action_type,
            description=body.description,
            organization_id=ctx["organization_id"],
            request_id=ctx["request_id"],
        )
    except ComplianceError as e:
        raise_compliance_http(e)
    return IncidentActionOut(**action.__dict__)


# ── Sensitive Access ──────────────────────────────────────────────────────────

@compliance_router.post("/sensitive-access", response_model=SensitiveAccessOut, status_code=201)
def record_sensitive_access(
    body: SensitiveAccessRequest,
    ctx: dict = Depends(require_org_compliance_permission("compliance.manage")),
) -> SensitiveAccessOut:
    try:
        rec = SensitiveAccessUseCases(ctx["conn"]).record(
            accessor_user_id=ctx["user_id"],
            resource_type=body.resource_type,
            resource_id=body.resource_id,
            reason=body.reason,
            organization_id=ctx["organization_id"],
            request_id=ctx["request_id"],
        )
    except ComplianceError as e:
        raise_compliance_http(e)
    return SensitiveAccessOut(**rec.__dict__)


# ── Audit Search ──────────────────────────────────────────────────────────────

@compliance_router.get("/audit/search", response_model=PaginatedAuditSearch)
def search_org_audit(
    action: Optional[str] = Query(default=None),
    source: Optional[str] = Query(default=None),
    actor_user_id: Optional[int] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    ctx: dict = Depends(require_org_compliance_permission("audit.search")),
) -> PaginatedAuditSearch:
    p, ps, offset = _page(page, page_size)
    items, total = AuditSearchUseCases(ctx["conn"]).search(
        organization_id=ctx["organization_id"],
        action=action, source=source, actor_user_id=actor_user_id,
        limit=ps, offset=offset,
    )
    return PaginatedAuditSearch(
        items=[AuditSearchOut(**e.__dict__) for e in items],
        total=total, page=p, page_size=ps,
    )


@compliance_router.get("/audit/search/platform", response_model=PaginatedAuditSearch)
def search_platform_audit(
    action: Optional[str] = Query(default=None),
    source: Optional[str] = Query(default=None),
    organization_id: Optional[int] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    ctx: dict = Depends(require_platform_audit_permission("audit.search")),
) -> PaginatedAuditSearch:
    p, ps, offset = _page(page, page_size)
    items, total = AuditSearchUseCases(ctx["conn"]).search(
        organization_id=organization_id,
        action=action, source=source,
        limit=ps, offset=offset, platform_scope=True,
    )
    return PaginatedAuditSearch(
        items=[AuditSearchOut(**e.__dict__) for e in items],
        total=total, page=p, page_size=ps,
    )
