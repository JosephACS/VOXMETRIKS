"""HTTP presentation — Spec 029 personal music subscriptions."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.database import get_write_conn
from app.packages.personal_subscriptions.application import checkout as checkout_uc
from app.packages.personal_subscriptions.application import entitlements as ent
from app.packages.personal_subscriptions.application import use_cases as uc
from app.packages.personal_subscriptions.domain.errors import PersonalSubscriptionError
from app.packages.subscriptions.presentation.dependencies import (
    get_authenticated_user,
    require_platform_permission,
)

personal_router = APIRouter(prefix="/personal", tags=["Personal Subscriptions"])


class CheckoutRequest(BaseModel):
    """Deprecated one-shot checkout — prefer /checkout-sessions."""

    plan_code: str
    billing_period: str = Field(pattern="^(monthly|annual)$")


class SimulatePaymentRequest(BaseModel):
    scenario: str = "succeeded"


class CheckoutSessionCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan_code: str
    billing_period: str = Field(pattern="^(monthly|annual)$")
    plan_id: Optional[int] = None
    plan_price_id: Optional[int] = None
    idempotency_key: str = Field(min_length=8, max_length=128)

    @model_validator(mode="before")
    @classmethod
    def _reject_card(cls, data: Any) -> Any:
        if isinstance(data, dict):
            checkout_uc.reject_raw_card_fields(data)
        return data


class CheckoutPaymentMethodRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    brand: str = Field(min_length=2, max_length=32)
    last4: str = Field(pattern=r"^\d{4}$")
    exp_month: int = Field(ge=1, le=12)
    exp_year: int = Field(ge=2024, le=2100)
    display_label: str = Field(default="", max_length=120)
    simulation_token: str = Field(min_length=8, max_length=64)
    is_default: bool = True

    @model_validator(mode="before")
    @classmethod
    def _reject_card(cls, data: Any) -> Any:
        if isinstance(data, dict):
            checkout_uc.reject_raw_card_fields(data)
        return data


class CheckoutConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    idempotency_key: str = Field(min_length=8, max_length=128)

    @model_validator(mode="before")
    @classmethod
    def _reject_card(cls, data: Any) -> Any:
        if isinstance(data, dict):
            checkout_uc.reject_raw_card_fields(data)
        return data


class InviteRequest(BaseModel):
    email: str


class AcceptInviteRequest(BaseModel):
    token: str


class RejectInviteRequest(BaseModel):
    token: str


class CancelRequest(BaseModel):
    at_period_end: bool = True


class ChangePeriodRequest(BaseModel):
    billing_period: str = Field(pattern="^(monthly|annual)$")


def _raise(exc: PersonalSubscriptionError):
    from fastapi import HTTPException

    status = 400
    if exc.code in ("not_found", "checkout_not_found"):
        status = 404
    elif exc.code in ("forbidden", "checkout_forbidden"):
        status = 403
    elif exc.code == "rate_limited":
        status = 429
    elif exc.code in ("entitlement_limit", "payment_declined"):
        status = 402
    elif exc.code in (
        "checkout_state_conflict",
        "checkout_idempotency_conflict",
        "payment_confirmation_failed",
    ):
        status = 409
    elif exc.code == "card_data_forbidden":
        status = 422
    raise HTTPException(
        status_code=status,
        detail={"code": exc.code, "message": str(exc)},
    )


@personal_router.get("/plans")
def list_plans(conn=Depends(get_write_conn)):
    return {"items": uc.list_personal_plans(conn), "owner_type": "user"}


@personal_router.get("/subscription")
def my_subscription(
    user: dict = Depends(get_authenticated_user),
    conn=Depends(get_write_conn),
):
    uc.apply_grace_expiry(conn, int(user["user_id"]))
    uc.finalize_period_end_cancellations(conn, int(user["user_id"]))
    return uc.get_subscription(conn, int(user["user_id"]))


@personal_router.get("/entitlements")
def my_entitlements(
    user: dict = Depends(get_authenticated_user),
    conn=Depends(get_write_conn),
):
    return ent.effective_limits(conn, int(user["user_id"]))


@personal_router.post(
    "/checkout",
    deprecated=True,
    summary="Deprecated one-shot checkout — use /checkout-sessions",
)
def checkout(
    body: CheckoutRequest,
    user: dict = Depends(get_authenticated_user),
    conn=Depends(get_write_conn),
):
    try:
        return uc.start_checkout(
            conn,
            int(user["user_id"]),
            plan_code=body.plan_code,
            billing_period=body.billing_period,
        )
    except PersonalSubscriptionError as e:
        _raise(e)


@personal_router.post(
    "/payment-attempts/{attempt_id}/simulate",
    deprecated=True,
    summary="Deprecated simulate — use checkout-sessions confirm",
)
def simulate_payment(
    attempt_id: int,
    body: SimulatePaymentRequest,
    user: dict = Depends(get_authenticated_user),
    conn=Depends(get_write_conn),
):
    try:
        return uc.simulate_payment(
            conn, int(user["user_id"]), attempt_id=attempt_id, scenario=body.scenario
        )
    except PersonalSubscriptionError as e:
        _raise(e)


@personal_router.post("/checkout-sessions", status_code=201)
def create_checkout_session(
    body: CheckoutSessionCreateRequest,
    user: dict = Depends(get_authenticated_user),
    conn=Depends(get_write_conn),
):
    try:
        return checkout_uc.create_checkout(
            conn,
            int(user["user_id"]),
            plan_code=body.plan_code,
            billing_period=body.billing_period,
            plan_price_id=body.plan_price_id,
            idempotency_key=body.idempotency_key,
        )
    except PersonalSubscriptionError as e:
        _raise(e)


@personal_router.get("/checkout-sessions/{checkout_id}")
def get_checkout_session(
    checkout_id: int,
    user: dict = Depends(get_authenticated_user),
    conn=Depends(get_write_conn),
):
    try:
        return checkout_uc.get_checkout(conn, int(user["user_id"]), checkout_id)
    except PersonalSubscriptionError as e:
        _raise(e)


@personal_router.post("/checkout-sessions/{checkout_id}/payment-method")
def attach_checkout_payment_method(
    checkout_id: int,
    body: CheckoutPaymentMethodRequest,
    user: dict = Depends(get_authenticated_user),
    conn=Depends(get_write_conn),
):
    try:
        return checkout_uc.attach_payment_method(
            conn,
            int(user["user_id"]),
            checkout_id,
            brand=body.brand,
            last4=body.last4,
            exp_month=body.exp_month,
            exp_year=body.exp_year,
            display_label=body.display_label,
            simulation_token=body.simulation_token,
            is_default=body.is_default,
        )
    except PersonalSubscriptionError as e:
        _raise(e)


@personal_router.post("/checkout-sessions/{checkout_id}/confirm")
def confirm_checkout_session(
    checkout_id: int,
    body: CheckoutConfirmRequest,
    user: dict = Depends(get_authenticated_user),
    conn=Depends(get_write_conn),
):
    try:
        session = checkout_uc.confirm_checkout(
            conn,
            int(user["user_id"]),
            checkout_id,
            idempotency_key=body.idempotency_key,
        )
        if session.get("status") == "failed":
            from fastapi import HTTPException

            raise HTTPException(
                status_code=402,
                detail={
                    "code": "payment_declined",
                    "message": "Payment declined",
                    "checkout": session,
                },
            )
        if session.get("status") == "processing":
            from fastapi import Response

            # 200 with processing state (contract: payment_processing is a state)
            return session
        return session
    except PersonalSubscriptionError as e:
        _raise(e)


@personal_router.post("/checkout-sessions/{checkout_id}/cancel")
def cancel_checkout_session(
    checkout_id: int,
    user: dict = Depends(get_authenticated_user),
    conn=Depends(get_write_conn),
):
    try:
        return checkout_uc.cancel_checkout(conn, int(user["user_id"]), checkout_id)
    except PersonalSubscriptionError as e:
        _raise(e)


@personal_router.post("/subscription/cancel")
def cancel_sub(
    body: CancelRequest,
    user: dict = Depends(get_authenticated_user),
    conn=Depends(get_write_conn),
):
    try:
        return uc.cancel_subscription(
            conn, int(user["user_id"]), at_period_end=body.at_period_end
        )
    except PersonalSubscriptionError as e:
        _raise(e)


@personal_router.post("/subscription/change-period")
def change_period(
    body: ChangePeriodRequest,
    user: dict = Depends(get_authenticated_user),
    conn=Depends(get_write_conn),
):
    try:
        return uc.change_billing_period(
            conn, int(user["user_id"]), billing_period=body.billing_period
        )
    except PersonalSubscriptionError as e:
        _raise(e)


@personal_router.post("/subscription/refund")
def refund(
    user: dict = Depends(get_authenticated_user),
    conn=Depends(get_write_conn),
):
    try:
        return uc.refund_latest_paid(conn, int(user["user_id"]))
    except PersonalSubscriptionError as e:
        _raise(e)


@personal_router.get("/invoices")
def invoices(
    user: dict = Depends(get_authenticated_user),
    conn=Depends(get_write_conn),
):
    return {"items": uc.list_invoices(conn, int(user["user_id"]))}


@personal_router.get("/household")
def household(
    user: dict = Depends(get_authenticated_user),
    conn=Depends(get_write_conn),
):
    data = uc.get_household(conn, int(user["user_id"]))
    return data or {"household": None}


@personal_router.get("/household/profiles")
def household_profiles(
    user: dict = Depends(get_authenticated_user),
    conn=Depends(get_write_conn),
):
    return uc.list_household_profiles(conn, int(user["user_id"]))


@personal_router.post("/household/profiles/{target_user_id}/prepare-switch")
def prepare_profile_switch(
    target_user_id: int,
    user: dict = Depends(get_authenticated_user),
    conn=Depends(get_write_conn),
):
    try:
        return uc.prepare_profile_switch(conn, int(user["user_id"]), int(target_user_id))
    except PersonalSubscriptionError as e:
        _raise(e)


@personal_router.post("/household/invitations")
def invite(
    body: InviteRequest,
    user: dict = Depends(get_authenticated_user),
    conn=Depends(get_write_conn),
):
    try:
        return uc.invite_member(conn, int(user["user_id"]), body.email)
    except PersonalSubscriptionError as e:
        _raise(e)


@personal_router.post("/household/invitations/{invitation_id}/cancel")
def cancel_invite(
    invitation_id: int,
    user: dict = Depends(get_authenticated_user),
    conn=Depends(get_write_conn),
):
    try:
        uc.cancel_invitation(conn, int(user["user_id"]), invitation_id)
        return {"ok": True}
    except PersonalSubscriptionError as e:
        _raise(e)


@personal_router.post("/household/invitations/{invitation_id}/resend")
def resend_invite(
    invitation_id: int,
    user: dict = Depends(get_authenticated_user),
    conn=Depends(get_write_conn),
):
    try:
        return uc.resend_invitation(conn, int(user["user_id"]), invitation_id)
    except PersonalSubscriptionError as e:
        _raise(e)


@personal_router.post("/household/accept")
def accept_invite(
    body: AcceptInviteRequest,
    user: dict = Depends(get_authenticated_user),
    conn=Depends(get_write_conn),
):
    try:
        return uc.accept_invitation(conn, int(user["user_id"]), body.token)
    except PersonalSubscriptionError as e:
        _raise(e)


@personal_router.post("/household/reject")
def reject_invite(
    body: RejectInviteRequest,
    user: dict = Depends(get_authenticated_user),
    conn=Depends(get_write_conn),
):
    try:
        return uc.reject_invitation(conn, int(user["user_id"]), body.token)
    except PersonalSubscriptionError as e:
        _raise(e)


@personal_router.post("/household/leave")
def leave_household(
    user: dict = Depends(get_authenticated_user),
    conn=Depends(get_write_conn),
):
    try:
        return uc.leave_household(conn, int(user["user_id"]))
    except PersonalSubscriptionError as e:
        _raise(e)


@personal_router.post("/household/members/{member_user_id}/remove")
def remove_member(
    member_user_id: int,
    user: dict = Depends(get_authenticated_user),
    conn=Depends(get_write_conn),
):
    try:
        return uc.remove_member(conn, int(user["user_id"]), member_user_id)
    except PersonalSubscriptionError as e:
        _raise(e)


@personal_router.get("/admin/metrics")
def admin_metrics(
    _admin=Depends(require_platform_permission("ops.view")),
    conn=Depends(get_write_conn),
):
    """Platform admin B2C metrics (separate from B2B)."""
    b2c = uc.personal_metrics(conn)
    # Optional B2B peek labeled clearly
    try:
        b2b_active = conn.execute(
            """
            SELECT COUNT(*) FROM app_subscription WHERE status = 'active'
            """
        ).fetchone()
        b2b_count = int(b2b_active[0]) if b2b_active else 0
    except Exception:  # noqa: BLE001
        b2b_count = 0
    return {
        "b2c": b2c,
        "b2b": {
            "segment": "B2B",
            "active_organization_subscriptions": b2b_count,
            "note": "Valores B2B no mezclados en MRR personal. Moneda B2C: USD.",
        },
        "total_labeled": {
            "description": "Suma solo de conteos de suscripciones activas (no MRR cruzado).",
            "active_subscriptions_b2c_plus_b2b": (
                b2c["individual_subscribers"]
                + b2c["duo_subscribers"]
                + b2c["family_subscribers"]
                + b2b_count
            ),
        },
    }


@personal_router.post("/admin/demo-seed")
def admin_demo_seed(
    _admin=Depends(require_platform_permission("ops.manage")),
    conn=Depends(get_write_conn),
):
    from app.packages.personal_subscriptions.application.seed_demo import seed_personal_demo

    return seed_personal_demo(conn)


@personal_router.get("/admin/subscriptions")
def admin_list_subscriptions(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    _admin=Depends(require_platform_permission("ops.view")),
    conn=Depends(get_write_conn),
):
    offset = (page - 1) * limit
    rows = conn.execute(
        """
        SELECT s.id, s.user_id, p.code, s.status, s.billing_currency,
               s.current_period_end, s.created_at
        FROM personal_subscription s
        JOIN personal_plan p ON p.id = s.plan_id
        ORDER BY s.id DESC
        LIMIT ? OFFSET ?
        """,
        [limit, offset],
    ).fetchall()
    total = int(conn.execute("SELECT COUNT(*) FROM personal_subscription").fetchone()[0])
    return {
        "items": [
            {
                "id": int(r[0]),
                "user_id": int(r[1]),
                "plan_code": r[2],
                "status": r[3],
                "currency": r[4],
                "period_end": str(r[5]) if r[5] else None,
                "created_at": str(r[6]) if r[6] else None,
                "owner_type": "user",
            }
            for r in rows
        ],
        "page": page,
        "limit": limit,
        "total": total,
    }
