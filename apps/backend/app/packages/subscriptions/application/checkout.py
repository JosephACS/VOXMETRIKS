"""Organization checkout orchestrator — Spec 052.

Composes Billing + Subscription use cases. Creates issued invoice and a pending
subscription without activating modules; confirmation activates only after a
successful simulated payment result.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Optional

import duckdb

from app.core.database import transactional
from app.core.time_util import utc_now
from app.packages.billing.application.use_cases import (
    BillingProfileUseCases,
    InvoiceUseCases,
    PaymentAttemptUseCases,
    PaymentUseCases,
)
from app.packages.billing.domain import errors as billing_errors
from app.packages.billing.infrastructure.schema import ensure_billing_tables
from app.packages.subscriptions.application.use_cases import (
    _assert_org_active,
    _has_active_subscription,
    _materialize_entitlements,
    _next_id,
    _upsert_access_state,
)
from app.packages.subscriptions.domain.errors import (
    ActiveSubscriptionExists,
    CheckoutError,
    NotFoundError,
    PlanRetiredError,
    ValidationError,
)
from app.packages.subscriptions.infrastructure.schema import ensure_subscription_tables

CHECKOUT_STATUSES = frozenset(
    {
        "draft",
        "awaiting_method",
        "ready",
        "processing",
        "succeeded",
        "failed",
        "canceled",
        "expired",
    }
)
MUTABLE = frozenset({"draft", "awaiting_method", "ready", "failed", "processing"})
SESSION_TTL_HOURS = 24

# Opaque simulation tokens → provider scenario (never raw PAN).
SIM_TOKEN_SCENARIO = {
    "sim_tok_succeeded": "succeeded",
    "sim_tok_declined": "declined",
    "sim_tok_insufficient_funds": "insufficient_funds",
    "sim_tok_processing": "processing",
}

_PAN_FIELD = re.compile(r"(?i)^(pan|card_number|cardNumber|cvv|cvc|security_code)$")


def reject_raw_card_fields(payload: dict[str, Any] | None) -> None:
    if not payload:
        return
    for key in payload.keys():
        if _PAN_FIELD.match(str(key)) or str(key).lower() in {
            "pan",
            "cvv",
            "cvc",
            "card_number",
            "cardnumber",
        }:
            raise CheckoutError(
                "Raw card data is not accepted",
                code="card_data_forbidden",
            )


def _quantize(amount: object) -> Decimal:
    return Decimal(str(amount)).quantize(Decimal("0.01"))


def _next_action(status: str) -> str:
    return {
        "draft": "attach_payment_method",
        "awaiting_method": "attach_payment_method",
        "ready": "confirm",
        "processing": "wait_or_resume",
        "failed": "retry_or_change_method",
        "succeeded": "view_result",
        "canceled": "start_new",
        "expired": "start_new",
    }.get(status, "none")


def _iso(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _expire_if_needed(conn: duckdb.DuckDBPyConnection, row: dict[str, Any]) -> dict[str, Any]:
    if row["status"] in ("succeeded", "canceled", "expired"):
        return row
    expires = row.get("expires_at")
    if expires is None:
        return row
    now = utc_now()
    if hasattr(expires, "isoformat") and expires <= now:
        conn.execute(
            """
            UPDATE app_subscription_checkout_session
            SET status = 'expired', updated_at = ?, failure_code = 'checkout_expired'
            WHERE id = ? AND status NOT IN ('succeeded', 'canceled', 'expired')
            """,
            [now, row["id"]],
        )
        row = dict(row)
        row["status"] = "expired"
        row["failure_code"] = "checkout_expired"
        row["next_action"] = _next_action("expired")
    return row


def _map_session(conn: duckdb.DuckDBPyConnection, row: tuple) -> dict[str, Any]:
    (
        sid,
        organization_id,
        actor_user_id,
        plan_code,
        plan_id,
        plan_price_id,
        billing_period,
        amount,
        currency,
        status,
        subscription_id,
        invoice_id,
        payment_attempt_id,
        payment_method_id,
        idempotency_key,
        failure_code,
        created_at,
        updated_at,
        expires_at,
        completed_at,
    ) = row
    out = {
        "id": int(sid),
        "scope_type": "organization",
        "scope_id": int(organization_id),
        "organization_id": int(organization_id),
        "actor_user_id": int(actor_user_id),
        "plan_code": str(plan_code),
        "plan_id": int(plan_id),
        "plan_price_id": int(plan_price_id),
        "billing_period": str(billing_period),
        "amount": float(_quantize(amount)),
        "currency": str(currency),
        "status": str(status),
        "next_action": _next_action(str(status)),
        "subscription_id": int(subscription_id) if subscription_id is not None else None,
        "invoice_id": int(invoice_id) if invoice_id is not None else None,
        "payment_attempt_id": int(payment_attempt_id) if payment_attempt_id is not None else None,
        "payment_method_id": int(payment_method_id) if payment_method_id is not None else None,
        "idempotency_key": str(idempotency_key),
        "failure_code": failure_code,
        "created_at": created_at,
        "updated_at": updated_at,
        "expires_at": expires_at,
        "completed_at": completed_at,
        "is_simulated": True,
        "payment_method": None,
    }
    if out["payment_method_id"]:
        pm = conn.execute(
            """
            SELECT brand, last4, exp_month, exp_year, display_label, status
            FROM app_payment_method_reference
            WHERE id = ? AND organization_id = ?
            """,
            [out["payment_method_id"], out["organization_id"]],
        ).fetchone()
        if pm:
            out["payment_method"] = {
                "brand": pm[0],
                "last4": pm[1],
                "exp_month": int(pm[2]) if pm[2] is not None else None,
                "exp_year": int(pm[3]) if pm[3] is not None else None,
                "display_label": pm[4],
                "status": pm[5],
            }
    mapped = _expire_if_needed(conn, out)
    for key in ("created_at", "updated_at", "expires_at", "completed_at"):
        mapped[key] = _iso(mapped.get(key))
    return mapped


def _get_row(
    conn: duckdb.DuckDBPyConnection, checkout_id: int, organization_id: int
) -> tuple:
    row = conn.execute(
        """
        SELECT id, organization_id, actor_user_id, plan_code, plan_id, plan_price_id,
               billing_period, amount, currency, status, subscription_id, invoice_id,
               payment_attempt_id, payment_method_id, idempotency_key, failure_code,
               created_at, updated_at, expires_at, completed_at
        FROM app_subscription_checkout_session
        WHERE id = ? AND organization_id = ?
        """,
        [checkout_id, organization_id],
    ).fetchone()
    if not row:
        raise CheckoutError("Checkout not found", code="checkout_not_found")
    return row


def get_checkout(
    conn: duckdb.DuckDBPyConnection, organization_id: int, checkout_id: int
) -> dict[str, Any]:
    ensure_subscription_tables(conn)
    ensure_billing_tables(conn)
    return _map_session(conn, _get_row(conn, checkout_id, organization_id))


def _ensure_billing_profile(
    conn: duckdb.DuckDBPyConnection,
    *,
    actor_user_id: int,
    organization_id: int,
    currency: str,
    request_id: Optional[str] = None,
):
    profiles = BillingProfileUseCases(conn)
    try:
        return profiles.get_by_org(organization_id)
    except billing_errors.NotFoundError:
        return profiles.create(
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            default_currency=currency,
            request_id=request_id,
        )


def create_checkout(
    conn: duckdb.DuckDBPyConnection,
    *,
    actor_user_id: int,
    organization_id: int,
    plan_id: int,
    plan_price_id: int,
    idempotency_key: str,
    billing_period: Optional[str] = None,
    request_id: Optional[str] = None,
) -> dict[str, Any]:
    ensure_subscription_tables(conn)
    ensure_billing_tables(conn)
    if not idempotency_key or not idempotency_key.strip():
        raise CheckoutError("idempotency_key is required", code="validation_error")
    key = idempotency_key.strip()

    existing = conn.execute(
        """
        SELECT id FROM app_subscription_checkout_session
        WHERE organization_id = ? AND idempotency_key = ?
        """,
        [organization_id, key],
    ).fetchone()
    if existing:
        return get_checkout(conn, organization_id, int(existing[0]))

    _assert_org_active(conn, organization_id)
    if _has_active_subscription(conn, organization_id):
        raise ActiveSubscriptionExists(
            f"Organization {organization_id} already has an active/trialing subscription"
        )

    plan = conn.execute(
        "SELECT id, code, display_name, status FROM app_plan WHERE id = ?",
        [plan_id],
    ).fetchone()
    if not plan:
        raise NotFoundError(f"plan id={plan_id}")
    if str(plan[3]) == "archived":
        raise PlanRetiredError(f"Plan {plan[1]!r} is archived")
    if str(plan[3]) != "active":
        raise ValidationError(f"Plan {plan[1]!r} is not active")

    price = conn.execute(
        """
        SELECT id, amount, currency, billing_period, status
        FROM app_plan_price WHERE id = ? AND plan_id = ?
        """,
        [plan_price_id, plan_id],
    ).fetchone()
    if not price:
        raise CheckoutError("Plan price mismatch", code="plan_price_mismatch")
    if str(price[4]) == "retired":
        raise PlanRetiredError(f"plan_price id={plan_price_id} is retired")
    period = str(price[3])
    if period not in ("monthly", "annual"):
        raise CheckoutError("Invalid billing period", code="invalid_period")
    if billing_period is not None and str(billing_period) != period:
        raise CheckoutError("Plan price mismatch", code="plan_price_mismatch")

    amount = _quantize(price[1])
    currency = str(price[2] or "USD").strip().upper()
    now = utc_now()
    expires = now + timedelta(hours=SESSION_TTL_HOURS)
    period_days = 30 if period == "monthly" else 365
    period_start = date.today()
    period_end = period_start + timedelta(days=period_days)
    plan_code = str(plan[1])

    with transactional(conn):
        # Resume an abandoned open checkout for the same price instead of blocking re-entry.
        open_row = conn.execute(
            """
            SELECT id, idempotency_key FROM app_subscription_checkout_session
            WHERE organization_id = ? AND plan_price_id = ?
              AND status IN ('draft', 'awaiting_method', 'ready', 'failed', 'processing')
            LIMIT 1
            """,
            [organization_id, plan_price_id],
        ).fetchone()
        if open_row:
            existing = get_checkout(conn, organization_id, int(open_row[0]))
            if existing.get("status") not in ("canceled", "expired", "succeeded"):
                return existing

        # Pending subscription — do NOT call SubscriptionUseCases.create (activates).
        sub_id = _next_id(conn, "app_subscription")
        conn.execute(
            """
            INSERT INTO app_subscription (
                id, organization_id, plan_id, plan_price_id, status, billing_currency,
                trial_ends_at, current_period_start, current_period_end,
                cancel_at_period_end, canceled_at, activation_source, access_state,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, 'pending', ?, NULL, ?, ?, FALSE, NULL, 'checkout',
                      'blocked', ?, ?)
            """,
            [
                sub_id,
                organization_id,
                plan_id,
                plan_price_id,
                currency,
                period_start,
                period_end,
                now,
                now,
            ],
        )
        # No entitlements / access_state materialization while pending.

        profile = _ensure_billing_profile(
            conn,
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            currency=currency,
            request_id=request_id,
        )
        invoices = InvoiceUseCases(conn)
        inv = invoices.create(
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            billing_profile_id=profile.id,
            subscription_id=sub_id,
            period_start=period_start,
            period_end=period_end,
            due_date=period_start + timedelta(days=7),
            notes=f"Checkout {plan_code} ({period})",
            request_id=request_id,
        )
        # Ensure a line item exists even if catalog helper returned nothing.
        item_count = int(
            conn.execute(
                "SELECT COUNT(*) FROM app_invoice_item WHERE invoice_id = ?",
                [inv.id],
            ).fetchone()[0]
        )
        if item_count == 0:
            invoices.add_item(
                inv.id,
                actor_user_id=actor_user_id,
                organization_id=organization_id,
                description=f"{plan[2]} ({period})",
                quantity=Decimal("1"),
                unit_price=amount,
                period_start=period_start,
                period_end=period_end,
            )
        invoices.issue(
            inv.id,
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            request_id=request_id,
        )

        cid = _next_id(conn, "app_subscription_checkout_session")
        conn.execute(
            """
            INSERT INTO app_subscription_checkout_session (
                id, organization_id, actor_user_id, plan_code, plan_id, plan_price_id,
                billing_period, amount, currency, status, subscription_id, invoice_id,
                payment_attempt_id, payment_method_id, idempotency_key, failure_code,
                created_at, updated_at, expires_at, completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'awaiting_method', ?, ?, NULL, NULL,
                      ?, NULL, ?, ?, ?, NULL)
            """,
            [
                cid,
                organization_id,
                actor_user_id,
                plan_code,
                plan_id,
                plan_price_id,
                period,
                amount,
                currency,
                sub_id,
                inv.id,
                key,
                now,
                now,
                expires,
            ],
        )

    return get_checkout(conn, organization_id, cid)


def attach_payment_method(
    conn: duckdb.DuckDBPyConnection,
    *,
    actor_user_id: int,
    organization_id: int,
    checkout_id: int,
    brand: str,
    last4: str,
    exp_month: int,
    exp_year: int,
    display_label: str,
    simulation_token: str,
    is_default: bool = True,
) -> dict[str, Any]:
    ensure_subscription_tables(conn)
    ensure_billing_tables(conn)
    if not re.fullmatch(r"\d{4}", str(last4 or "")):
        raise CheckoutError("last4 must be exactly four digits", code="validation_error")
    if not simulation_token or simulation_token not in SIM_TOKEN_SCENARIO:
        raise CheckoutError("Unknown simulation token", code="validation_error")
    now = utc_now()
    if exp_year < now.year or (exp_year == now.year and exp_month < now.month):
        raise CheckoutError("Card expiry is in the past", code="validation_error")

    with transactional(conn):
        session = _map_session(conn, _get_row(conn, checkout_id, organization_id))
        if session["status"] not in ("awaiting_method", "ready", "failed", "draft"):
            raise CheckoutError("Checkout cannot accept a method", code="checkout_state_conflict")

        if is_default:
            conn.execute(
                """
                UPDATE app_payment_method_reference
                SET is_default = FALSE, updated_at = ?
                WHERE organization_id = ? AND status = 'active'
                """,
                [now, organization_id],
            )
        mid = _next_id(conn, "app_payment_method_reference")
        label = (display_label or "").strip() or f"{brand} ····{last4}"
        conn.execute(
            """
            INSERT INTO app_payment_method_reference (
                id, organization_id, provider_code, display_label, token_ref,
                method_type, is_default, status, created_at, updated_at,
                brand, last4, exp_month, exp_year, simulation_token
            ) VALUES (?, ?, 'academic_mock', ?, ?, 'mock', ?, 'active', ?, ?,
                      ?, ?, ?, ?, ?)
            """,
            [
                mid,
                organization_id,
                label,
                f"pm_ref_{mid}",
                bool(is_default),
                now,
                now,
                brand.strip().lower(),
                last4,
                int(exp_month),
                int(exp_year),
                simulation_token,
            ],
        )
        conn.execute(
            """
            UPDATE app_subscription_checkout_session
            SET payment_method_id = ?, status = 'ready', failure_code = NULL, updated_at = ?
            WHERE id = ? AND organization_id = ?
            """,
            [mid, now, checkout_id, organization_id],
        )
    return get_checkout(conn, organization_id, checkout_id)


def confirm_checkout(
    conn: duckdb.DuckDBPyConnection,
    *,
    actor_user_id: int,
    organization_id: int,
    checkout_id: int,
    idempotency_key: str,
    request_id: Optional[str] = None,
) -> dict[str, Any]:
    ensure_subscription_tables(conn)
    ensure_billing_tables(conn)
    if not idempotency_key or not idempotency_key.strip():
        raise CheckoutError("idempotency_key is required", code="validation_error")
    confirm_key = idempotency_key.strip()

    with transactional(conn):
        session = _map_session(conn, _get_row(conn, checkout_id, organization_id))
        if session["status"] == "succeeded":
            return session
        if session["status"] == "processing":
            return session
        if session["status"] not in ("ready", "failed"):
            raise CheckoutError("Checkout is not confirmable", code="checkout_state_conflict")
        if not session.get("payment_method_id"):
            raise CheckoutError("Payment method required", code="payment_method_required")

        prior = conn.execute(
            """
            SELECT id, status FROM app_payment_attempt
            WHERE organization_id = ? AND idempotency_key = ?
            """,
            [organization_id, confirm_key],
        ).fetchone()
        if prior:
            return _map_session(conn, _get_row(conn, checkout_id, organization_id))

        pm = conn.execute(
            """
            SELECT simulation_token, brand, last4 FROM app_payment_method_reference
            WHERE id = ? AND organization_id = ? AND status = 'active'
            """,
            [session["payment_method_id"], organization_id],
        ).fetchone()
        if not pm:
            raise CheckoutError("Payment method required", code="payment_method_required")
        scenario = SIM_TOKEN_SCENARIO.get(str(pm[0]), "declined")

        now = utc_now()
        conn.execute(
            """
            UPDATE app_subscription_checkout_session
            SET status = 'processing', updated_at = ?, failure_code = NULL
            WHERE id = ? AND organization_id = ?
            """,
            [now, checkout_id, organization_id],
        )

        attempts = PaymentAttemptUseCases(conn)
        attempt = attempts.create(
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            invoice_id=int(session["invoice_id"]),
            provider_code=PaymentAttemptUseCases.MOCK_PROVIDER,
            idempotency_key=confirm_key,
            amount=_quantize(session["amount"]),
            currency=str(session["currency"]),
            payment_method_ref_id=int(session["payment_method_id"]),
            request_id=request_id,
        )
        conn.execute(
            """
            UPDATE app_subscription_checkout_session
            SET payment_attempt_id = ?, updated_at = ?
            WHERE id = ? AND organization_id = ?
            """,
            [attempt.id, now, checkout_id, organization_id],
        )

        try:
            sim = attempts.simulate_mock(
                attempt.id,
                scenario=scenario,
                actor_user_id=actor_user_id,
                organization_id=organization_id,
                request_id=request_id,
            )
        except Exception as exc:  # noqa: BLE001
            raise CheckoutError(
                "Payment confirmation failed",
                code="payment_confirmation_failed",
            ) from exc

        scenario_n = str(sim.get("scenario") or scenario).lower()
        updated_attempt = sim.get("attempt")
        attempt_status = getattr(updated_attempt, "status", None) or scenario_n

        if scenario_n == "processing" or attempt_status == "processing":
            return _map_session(conn, _get_row(conn, checkout_id, organization_id))

        if scenario_n in ("declined", "failed", "insufficient_funds", "invalid_method", "timeout") or (
            attempt_status == "failed"
        ):
            # Keep subscription pending so module access stays onboarding (not recovery).
            # Operational entitlements are never materialized on failure.
            conn.execute(
                """
                UPDATE app_subscription_checkout_session
                SET status = 'failed', failure_code = ?, updated_at = ?
                WHERE id = ? AND organization_id = ?
                """,
                [scenario_n, now, checkout_id, organization_id],
            )
            return _map_session(conn, _get_row(conn, checkout_id, organization_id))

        # Success path — payment record already created by confirm_mock inside simulate_mock.
        try:
            pay_row = conn.execute(
                """
                SELECT id, amount FROM app_payment
                WHERE payment_attempt_id = ? AND organization_id = ?
                ORDER BY id DESC LIMIT 1
                """,
                [attempt.id, organization_id],
            ).fetchone()
            if not pay_row:
                raise CheckoutError(
                    "Payment confirmation failed",
                    code="payment_confirmation_failed",
                )
            PaymentUseCases(conn).allocate(
                int(pay_row[0]),
                actor_user_id=actor_user_id,
                organization_id=organization_id,
                invoice_id=int(session["invoice_id"]),
                amount=_quantize(pay_row[1]),
                request_id=request_id,
            )
            # Ensure invoice paid_at when fully paid.
            conn.execute(
                """
                UPDATE app_invoice
                SET paid_at = COALESCE(paid_at, ?), updated_at = ?
                WHERE id = ? AND organization_id = ? AND status = 'paid'
                """,
                [now, now, session["invoice_id"], organization_id],
            )
            sub_id = int(session["subscription_id"])
            plan_id = int(session["plan_id"])
            conn.execute(
                """
                UPDATE app_subscription
                SET status = 'active', access_state = 'full', canceled_at = NULL,
                    activation_source = 'checkout', updated_at = ?
                WHERE id = ? AND organization_id = ?
                """,
                [now, sub_id, organization_id],
            )
            _materialize_entitlements(conn, sub_id, plan_id)
            _upsert_access_state(conn, sub_id, "full", "checkout_succeeded")
            conn.execute(
                """
                UPDATE app_subscription_checkout_session
                SET status = 'succeeded', completed_at = ?, updated_at = ?, failure_code = NULL
                WHERE id = ? AND organization_id = ?
                """,
                [now, now, checkout_id, organization_id],
            )
        except CheckoutError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise CheckoutError(
                "Payment confirmation failed",
                code="payment_confirmation_failed",
            ) from exc

    return get_checkout(conn, organization_id, checkout_id)


def cancel_checkout(
    conn: duckdb.DuckDBPyConnection,
    *,
    actor_user_id: int,
    organization_id: int,
    checkout_id: int,
) -> dict[str, Any]:
    del actor_user_id  # reserved for audit trail parity with other mutations
    ensure_subscription_tables(conn)
    ensure_billing_tables(conn)
    with transactional(conn):
        session = _map_session(conn, _get_row(conn, checkout_id, organization_id))
        if session["status"] in ("succeeded", "canceled", "expired"):
            raise CheckoutError("Checkout cannot be canceled", code="checkout_state_conflict")
        now = utc_now()
        conn.execute(
            """
            UPDATE app_subscription_checkout_session
            SET status = 'canceled', updated_at = ?, completed_at = ?
            WHERE id = ? AND organization_id = ?
            """,
            [now, now, checkout_id, organization_id],
        )
        if session.get("subscription_id"):
            conn.execute(
                """
                UPDATE app_subscription
                SET status = 'canceled', canceled_at = ?, updated_at = ?, access_state = 'blocked'
                WHERE id = ? AND organization_id = ? AND status = 'pending'
                """,
                [now, now, session["subscription_id"], organization_id],
            )
    return get_checkout(conn, organization_id, checkout_id)
