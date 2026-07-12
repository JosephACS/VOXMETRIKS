"""Customer Success & Support routers — Spec 025."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.packages.customer_success.application.use_cases import (
    ExpansionUseCases,
    HealthUseCases,
    InterventionUseCases,
    OnboardingUseCases,
    RenewalUseCases,
    RiskUseCases,
    SupportUseCases,
)
from app.packages.customer_success.domain.errors import CustomerSuccessError
from app.packages.customer_success.presentation.dependencies import require_org_cs_permission
from app.packages.customer_success.presentation.error_mapping import raise_cs_http
from app.packages.customer_success.presentation.schemas import (
    AssignRequest,
    BlockStepRequest,
    ExpansionCreateRequest,
    ExpansionOut,
    HealthSnapshotOut,
    InterventionCreateRequest,
    InterventionOut,
    MessageCreateRequest,
    MessageOut,
    OnboardingOut,
    OnboardingStepOut,
    RenewalOut,
    RiskCreateRequest,
    RiskOut,
    SatisfactionOut,
    SatisfactionRequest,
    SlaEventOut,
    SupportCaseCreateRequest,
    SupportCaseOut,
)

customer_success_router = APIRouter(prefix="/customer-success", tags=["Customer Success"])
support_router = APIRouter(prefix="/support", tags=["Support"])


@customer_success_router.get("/dashboard")
def cs_dashboard(ctx: dict = Depends(require_org_cs_permission("customer_success.view"))) -> dict:
    health = HealthUseCases(ctx["conn"]).latest(ctx["organization_id"])
    risks = RiskUseCases(ctx["conn"]).list(ctx["organization_id"])
    expansions = ExpansionUseCases(ctx["conn"]).list(ctx["organization_id"])
    return {
        "health": HealthSnapshotOut(**health.__dict__).model_dump() if health else None,
        "open_risks": len([r for r in risks if r.status in ("open", "intervention_required")]),
        "expansions": len(expansions),
        "label": "Customer Success academic dashboard",
    }


@customer_success_router.post("/onboarding", response_model=OnboardingOut, status_code=201)
def create_onboarding(ctx: dict = Depends(require_org_cs_permission("customer_success.manage"))) -> OnboardingOut:
    try:
        o = OnboardingUseCases(ctx["conn"]).create(
            organization_id=ctx["organization_id"], actor_user_id=ctx["user_id"], request_id=ctx["request_id"],
        )
    except CustomerSuccessError as e:
        raise_cs_http(e)
    return OnboardingOut(**o.__dict__)


@customer_success_router.get("/onboarding/{onboarding_id}/steps", response_model=list[OnboardingStepOut])
def list_steps(onboarding_id: int, ctx: dict = Depends(require_org_cs_permission("customer_success.view"))) -> list[OnboardingStepOut]:
    try:
        steps = OnboardingUseCases(ctx["conn"]).list_steps(ctx["organization_id"], onboarding_id)
    except CustomerSuccessError as e:
        raise_cs_http(e)
    return [OnboardingStepOut(**s.__dict__) for s in steps]


@customer_success_router.post("/onboarding/{onboarding_id}/steps/{step_id}/complete", response_model=OnboardingStepOut)
def complete_step(onboarding_id: int, step_id: int, ctx: dict = Depends(require_org_cs_permission("customer_success.manage"))) -> OnboardingStepOut:
    try:
        s = OnboardingUseCases(ctx["conn"]).complete_step(
            organization_id=ctx["organization_id"], onboarding_id=onboarding_id, step_id=step_id,
            actor_user_id=ctx["user_id"], request_id=ctx["request_id"],
        )
    except CustomerSuccessError as e:
        raise_cs_http(e)
    return OnboardingStepOut(**s.__dict__)


@customer_success_router.post("/onboarding/{onboarding_id}/steps/{step_id}/block", response_model=OnboardingStepOut)
def block_step(onboarding_id: int, step_id: int, body: BlockStepRequest, ctx: dict = Depends(require_org_cs_permission("customer_success.manage"))) -> OnboardingStepOut:
    try:
        s = OnboardingUseCases(ctx["conn"]).block_step(
            organization_id=ctx["organization_id"], onboarding_id=onboarding_id, step_id=step_id,
            reason=body.reason, actor_user_id=ctx["user_id"], request_id=ctx["request_id"],
        )
    except CustomerSuccessError as e:
        raise_cs_http(e)
    return OnboardingStepOut(**s.__dict__)


@customer_success_router.post("/health/calculate", response_model=HealthSnapshotOut)
def calculate_health(ctx: dict = Depends(require_org_cs_permission("customer_health.calculate"))) -> HealthSnapshotOut:
    try:
        h = HealthUseCases(ctx["conn"]).calculate(
            organization_id=ctx["organization_id"], actor_user_id=ctx["user_id"], request_id=ctx["request_id"],
        )
    except CustomerSuccessError as e:
        raise_cs_http(e)
    return HealthSnapshotOut(**h.__dict__)


@customer_success_router.get("/health/latest", response_model=HealthSnapshotOut | None)
def latest_health(ctx: dict = Depends(require_org_cs_permission("customer_health.view"))) -> HealthSnapshotOut | None:
    h = HealthUseCases(ctx["conn"]).latest(ctx["organization_id"])
    return HealthSnapshotOut(**h.__dict__) if h else None


@customer_success_router.post("/risks", response_model=RiskOut, status_code=201)
def create_risk(body: RiskCreateRequest, ctx: dict = Depends(require_org_cs_permission("customer_risk.manage"))) -> RiskOut:
    try:
        r = RiskUseCases(ctx["conn"]).create(
            organization_id=ctx["organization_id"], title=body.title, description=body.description,
            severity=body.severity, actor_user_id=ctx["user_id"], request_id=ctx["request_id"],
        )
    except CustomerSuccessError as e:
        raise_cs_http(e)
    return RiskOut(**r.__dict__)


@customer_success_router.get("/risks", response_model=list[RiskOut])
def list_risks(ctx: dict = Depends(require_org_cs_permission("customer_success.view"))) -> list[RiskOut]:
    return [RiskOut(**r.__dict__) for r in RiskUseCases(ctx["conn"]).list(ctx["organization_id"])]


@customer_success_router.post("/interventions", response_model=InterventionOut, status_code=201)
def assign_intervention(body: InterventionCreateRequest, ctx: dict = Depends(require_org_cs_permission("customer_intervention.manage"))) -> InterventionOut:
    try:
        i = InterventionUseCases(ctx["conn"]).assign(
            organization_id=ctx["organization_id"], title=body.title, risk_id=body.risk_id,
            assignee_user_id=body.assignee_user_id, actor_user_id=ctx["user_id"], request_id=ctx["request_id"],
        )
    except CustomerSuccessError as e:
        raise_cs_http(e)
    return InterventionOut(**i.__dict__)


@customer_success_router.post("/interventions/{intervention_id}/complete", response_model=InterventionOut)
def complete_intervention(intervention_id: int, ctx: dict = Depends(require_org_cs_permission("customer_intervention.manage"))) -> InterventionOut:
    try:
        i = InterventionUseCases(ctx["conn"]).complete(
            organization_id=ctx["organization_id"], intervention_id=intervention_id,
            actor_user_id=ctx["user_id"], request_id=ctx["request_id"],
        )
    except CustomerSuccessError as e:
        raise_cs_http(e)
    return InterventionOut(**i.__dict__)


@customer_success_router.post("/renewal/evaluate", response_model=RenewalOut)
def evaluate_renewal(ctx: dict = Depends(require_org_cs_permission("renewal_readiness.view"))) -> RenewalOut:
    try:
        r = RenewalUseCases(ctx["conn"]).evaluate(
            organization_id=ctx["organization_id"], actor_user_id=ctx["user_id"], request_id=ctx["request_id"],
        )
    except CustomerSuccessError as e:
        raise_cs_http(e)
    return RenewalOut(**r.__dict__)


@customer_success_router.post("/expansions", response_model=ExpansionOut, status_code=201)
def create_expansion(body: ExpansionCreateRequest, ctx: dict = Depends(require_org_cs_permission("expansion.manage"))) -> ExpansionOut:
    try:
        e = ExpansionUseCases(ctx["conn"]).create(
            organization_id=ctx["organization_id"], title=body.title, estimated_value=body.estimated_value,
            notes=body.notes, actor_user_id=ctx["user_id"], request_id=ctx["request_id"],
        )
    except CustomerSuccessError as e:
        raise_cs_http(e)
    return ExpansionOut(**e.__dict__)


@customer_success_router.get("/expansions", response_model=list[ExpansionOut])
def list_expansions(ctx: dict = Depends(require_org_cs_permission("customer_success.view"))) -> list[ExpansionOut]:
    return [ExpansionOut(**e.__dict__) for e in ExpansionUseCases(ctx["conn"]).list(ctx["organization_id"])]


# ── Support ───────────────────────────────────────────────────────────────────

@support_router.get("/cases", response_model=list[SupportCaseOut])
def list_cases(ctx: dict = Depends(require_org_cs_permission("support.view"))) -> list[SupportCaseOut]:
    return [SupportCaseOut(**c.__dict__) for c in SupportUseCases(ctx["conn"]).list_cases(ctx["organization_id"])]


@support_router.post("/cases", response_model=SupportCaseOut, status_code=201)
def create_case(body: SupportCaseCreateRequest, ctx: dict = Depends(require_org_cs_permission("support.create"))) -> SupportCaseOut:
    try:
        c = SupportUseCases(ctx["conn"]).create(
            organization_id=ctx["organization_id"], subject=body.subject, category=body.category,
            priority=body.priority, actor_user_id=ctx["user_id"], request_id=ctx["request_id"],
        )
    except CustomerSuccessError as e:
        raise_cs_http(e)
    return SupportCaseOut(**c.__dict__)


@support_router.get("/cases/{case_id}", response_model=SupportCaseOut)
def get_case(case_id: int, ctx: dict = Depends(require_org_cs_permission("support.view"))) -> SupportCaseOut:
    try:
        c = SupportUseCases(ctx["conn"])._get_case(ctx["organization_id"], case_id)
    except CustomerSuccessError as e:
        raise_cs_http(e)
    return SupportCaseOut(**c.__dict__)


@support_router.post("/cases/{case_id}/triage", response_model=SupportCaseOut)
def triage_case(case_id: int, ctx: dict = Depends(require_org_cs_permission("support.assign"))) -> SupportCaseOut:
    try:
        c = SupportUseCases(ctx["conn"]).triage(organization_id=ctx["organization_id"], case_id=case_id, actor_user_id=ctx["user_id"], request_id=ctx["request_id"])
    except CustomerSuccessError as e:
        raise_cs_http(e)
    return SupportCaseOut(**c.__dict__)


@support_router.post("/cases/{case_id}/assign", response_model=SupportCaseOut)
def assign_case(case_id: int, body: AssignRequest, ctx: dict = Depends(require_org_cs_permission("support.assign"))) -> SupportCaseOut:
    try:
        c = SupportUseCases(ctx["conn"]).assign(
            organization_id=ctx["organization_id"], case_id=case_id, assignee_user_id=body.assignee_user_id,
            actor_user_id=ctx["user_id"], request_id=ctx["request_id"],
        )
    except CustomerSuccessError as e:
        raise_cs_http(e)
    return SupportCaseOut(**c.__dict__)


@support_router.post("/cases/{case_id}/messages", response_model=MessageOut, status_code=201)
def add_message(case_id: int, body: MessageCreateRequest, ctx: dict = Depends(require_org_cs_permission("support.respond"))) -> MessageOut:
    try:
        m = SupportUseCases(ctx["conn"]).add_message(
            organization_id=ctx["organization_id"], case_id=case_id, body=body.body, is_internal=False,
            actor_user_id=ctx["user_id"], request_id=ctx["request_id"],
        )
    except CustomerSuccessError as e:
        raise_cs_http(e)
    return MessageOut(**m.__dict__)


@support_router.post("/cases/{case_id}/internal-notes", response_model=MessageOut, status_code=201)
def add_internal_note(case_id: int, body: MessageCreateRequest, ctx: dict = Depends(require_org_cs_permission("support.internal_note"))) -> MessageOut:
    try:
        m = SupportUseCases(ctx["conn"]).add_message(
            organization_id=ctx["organization_id"], case_id=case_id, body=body.body, is_internal=True,
            actor_user_id=ctx["user_id"], request_id=ctx["request_id"],
        )
    except CustomerSuccessError as e:
        raise_cs_http(e)
    return MessageOut(**m.__dict__)


@support_router.get("/cases/{case_id}/messages", response_model=list[MessageOut])
def list_messages(
    case_id: int,
    include_internal: bool = Query(default=False),
    ctx: dict = Depends(require_org_cs_permission("support.view")),
) -> list[MessageOut]:
    # Internal notes require support.internal_note
    if include_internal:
        # re-check permission
        from app.packages.customer_success.presentation.dependencies import require_org_cs_permission as _req
        # Already have support.view; gate internal via separate check
        perm = ctx["conn"].execute(
            """
            SELECT 1 FROM app_organization_member m
            JOIN app_member_role mr ON mr.member_id = m.id AND mr.status = 'active'
            JOIN app_role_permission rp ON rp.role_id = mr.role_id
            JOIN app_permission p ON p.id = rp.permission_id AND p.code = 'support.internal_note'
            WHERE m.organization_id = ? AND m.user_id = ? AND m.status = 'active' LIMIT 1
            """,
            [ctx["organization_id"], ctx["user_id"]],
        ).fetchone()
        if not perm:
            include_internal = False
    try:
        items = SupportUseCases(ctx["conn"]).list_messages(
            ctx["organization_id"], case_id, include_internal=include_internal,
        )
    except CustomerSuccessError as e:
        raise_cs_http(e)
    return [MessageOut(**m.__dict__) for m in items]


@support_router.post("/cases/{case_id}/escalate", response_model=SupportCaseOut)
def escalate_case(case_id: int, ctx: dict = Depends(require_org_cs_permission("support.escalate"))) -> SupportCaseOut:
    try:
        c = SupportUseCases(ctx["conn"]).escalate(organization_id=ctx["organization_id"], case_id=case_id, actor_user_id=ctx["user_id"], request_id=ctx["request_id"])
    except CustomerSuccessError as e:
        raise_cs_http(e)
    return SupportCaseOut(**c.__dict__)


@support_router.post("/cases/{case_id}/resolve", response_model=SupportCaseOut)
def resolve_case(case_id: int, ctx: dict = Depends(require_org_cs_permission("support.resolve"))) -> SupportCaseOut:
    try:
        c = SupportUseCases(ctx["conn"]).resolve(organization_id=ctx["organization_id"], case_id=case_id, actor_user_id=ctx["user_id"], request_id=ctx["request_id"])
    except CustomerSuccessError as e:
        raise_cs_http(e)
    return SupportCaseOut(**c.__dict__)


@support_router.post("/cases/{case_id}/close", response_model=SupportCaseOut)
def close_case(case_id: int, ctx: dict = Depends(require_org_cs_permission("support.close"))) -> SupportCaseOut:
    try:
        c = SupportUseCases(ctx["conn"]).close(organization_id=ctx["organization_id"], case_id=case_id, actor_user_id=ctx["user_id"], request_id=ctx["request_id"])
    except CustomerSuccessError as e:
        raise_cs_http(e)
    return SupportCaseOut(**c.__dict__)


@support_router.post("/cases/{case_id}/reopen", response_model=SupportCaseOut)
def reopen_case(case_id: int, ctx: dict = Depends(require_org_cs_permission("support.close"))) -> SupportCaseOut:
    try:
        c = SupportUseCases(ctx["conn"]).reopen(organization_id=ctx["organization_id"], case_id=case_id, actor_user_id=ctx["user_id"], request_id=ctx["request_id"])
    except CustomerSuccessError as e:
        raise_cs_http(e)
    return SupportCaseOut(**c.__dict__)


@support_router.post("/cases/{case_id}/satisfaction", response_model=SatisfactionOut, status_code=201)
def record_satisfaction(case_id: int, body: SatisfactionRequest, ctx: dict = Depends(require_org_cs_permission("support.create"))) -> SatisfactionOut:
    try:
        s = SupportUseCases(ctx["conn"]).record_satisfaction(
            organization_id=ctx["organization_id"], case_id=case_id, score=body.score, comment=body.comment,
            actor_user_id=ctx["user_id"], request_id=ctx["request_id"],
        )
    except CustomerSuccessError as e:
        raise_cs_http(e)
    return SatisfactionOut(**s.__dict__)


@support_router.get("/cases/{case_id}/sla-events", response_model=list[SlaEventOut])
def list_sla(case_id: int, ctx: dict = Depends(require_org_cs_permission("support.audit.view"))) -> list[SlaEventOut]:
    try:
        items = SupportUseCases(ctx["conn"]).list_sla_events(ctx["organization_id"], case_id)
    except CustomerSuccessError as e:
        raise_cs_http(e)
    return [SlaEventOut(**e.__dict__) for e in items]
