"""Personal checkout orchestrator — Spec 052.

Creates invoice + processing subscription without canceling the active plan.
Confirmation activates only after a successful simulated payment result.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Optional

import duckdb

from app.core.database import transactional
from app.core.time_util import utc_now
from app.packages.personal_subscriptions.application.catalog import (
    OWNER_TYPE_USER,
    ensure_personal_catalog,
)
from app.packages.personal_subscriptions.application import use_cases as uc
from app.packages.personal_subscriptions.domain.errors import (
    HouseholdMembershipError,
    PersonalNotFoundError,
    PersonalSubscriptionError,
)
from app.packages.personal_subscriptions.infrastructure.schema import (
    ensure_personal_subscription_tables,
)

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


class CheckoutError(PersonalSubscriptionError):
    pass


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


def _next_id(conn: duckdb.DuckDBPyConnection, table: str) -> int:
    return int(conn.execute(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table}").fetchone()[0])


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


def _expire_if_needed(conn: duckdb.DuckDBPyConnection, row: dict[str, Any]) -> dict[str, Any]:
    if row["status"] in ("succeeded", "canceled", "expired"):
        return row
    expires = row.get("expires_at")
    if expires is None:
        return row
    now = utc_now()
    # Compare using original datetime if still present.
    if hasattr(expires, "isoformat") and expires <= now:
        conn.execute(
            """
            UPDATE personal_checkout_session
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


def _iso(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _map_session(conn: duckdb.DuckDBPyConnection, row: tuple) -> dict[str, Any]:
    (
        sid,
        user_id,
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
        "scope_type": "personal",
        "scope_id": int(user_id),
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
            FROM personal_payment_method_reference WHERE id = ?
            """,
            [out["payment_method_id"]],
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


def _get_row(conn: duckdb.DuckDBPyConnection, checkout_id: int, user_id: int) -> tuple:
    row = conn.execute(
        """
        SELECT id, user_id, actor_user_id, plan_code, plan_id, plan_price_id, billing_period,
               amount, currency, status, subscription_id, invoice_id, payment_attempt_id,
               payment_method_id, idempotency_key, failure_code, created_at, updated_at,
               expires_at, completed_at
        FROM personal_checkout_session WHERE id = ? AND user_id = ?
        """,
        [checkout_id, user_id],
    ).fetchone()
    if not row:
        raise CheckoutError("Checkout not found", code="checkout_not_found")
    return row


def get_checkout(conn: duckdb.DuckDBPyConnection, user_id: int, checkout_id: int) -> dict[str, Any]:
    ensure_personal_subscription_tables(conn)
    return _map_session(conn, _get_row(conn, checkout_id, user_id))


def create_checkout(
    conn: duckdb.DuckDBPyConnection,
    user_id: int,
    *,
    plan_code: str,
    billing_period: str,
    idempotency_key: str,
    plan_price_id: Optional[int] = None,
) -> dict[str, Any]:
    ensure_personal_subscription_tables(conn)
    ensure_personal_catalog(conn)
    if not idempotency_key or not idempotency_key.strip():
        raise CheckoutError("idempotency_key is required", code="validation_error")
    key = idempotency_key.strip()

    existing = conn.execute(
        """
        SELECT id FROM personal_checkout_session
        WHERE user_id = ? AND idempotency_key = ?
        """,
        [user_id, key],
    ).fetchone()
    if existing:
        return get_checkout(conn, user_id, int(existing[0]))

    if plan_code == "personal_free":
        raise CheckoutError("Free does not require checkout", code="invalid_plan")
    if billing_period not in ("monthly", "annual"):
        raise CheckoutError("Invalid billing period", code="invalid_period")

    member = conn.execute(
        """
        SELECT hm.role FROM household_member hm
        JOIN household h ON h.id = hm.household_id
        WHERE hm.user_id = ? AND hm.status = 'active' AND h.status = 'active'
        """,
        [user_id],
    ).fetchone()
    if member and member[0] == "member":
        raise HouseholdMembershipError(
            "Ya perteneces a un household. Abandónalo antes de contratar otro plan."
        )

    plan = conn.execute(
        "SELECT id, display_name, is_free FROM personal_plan WHERE code = ? AND status = 'active'",
        [plan_code],
    ).fetchone()
    if not plan or bool(plan[2]):
        raise PersonalNotFoundError("Plan no encontrado")
    plan_id = int(plan[0])

    if plan_price_id is not None:
        price = conn.execute(
            """
            SELECT id, amount, currency, billing_period FROM personal_plan_price
            WHERE id = ? AND plan_id = ? AND status = 'active'
            """,
            [plan_price_id, plan_id],
        ).fetchone()
        if not price:
            raise CheckoutError("Plan price mismatch", code="plan_price_mismatch")
        if str(price[3]) != billing_period:
            raise CheckoutError("Plan price mismatch", code="plan_price_mismatch")
    else:
        price = conn.execute(
            """
            SELECT id, amount, currency, billing_period FROM personal_plan_price
            WHERE plan_id = ? AND billing_period = ? AND status = 'active'
            """,
            [plan_id, billing_period],
        ).fetchone()
        if not price:
            raise PersonalNotFoundError("Precio no disponible")

    amount = _quantize(price[1])
    currency = str(price[2] or "USD").strip().upper()
    now = utc_now()
    expires = now + timedelta(hours=SESSION_TTL_HOURS)
    period_days = 30 if billing_period == "monthly" else 365
    period_start = date.today()
    period_end = period_start + timedelta(days=period_days)

    with transactional(conn):
        # Resume an abandoned open checkout for the same price instead of blocking re-entry.
        open_row = conn.execute(
            """
            SELECT id, idempotency_key FROM personal_checkout_session
            WHERE user_id = ? AND plan_price_id = ?
              AND status IN ('draft', 'awaiting_method', 'ready', 'failed', 'processing')
            LIMIT 1
            """,
            [user_id, int(price[0])],
        ).fetchone()
        if open_row:
            existing = get_checkout(conn, user_id, int(open_row[0]))
            if existing.get("status") not in ("canceled", "expired", "succeeded"):
                return existing

        inv_id = _next_id(conn, "personal_invoice")
        inv_number = f"PINV-{user_id}-{inv_id}"
        conn.execute(
            """
            INSERT INTO personal_invoice (
                id, user_id, personal_subscription_id, invoice_number, currency, status,
                subtotal, total, amount_paid, amount_due, period_start, period_end,
                due_date, issued_at, created_at, updated_at
            ) VALUES (?, ?, NULL, ?, ?, 'issued', ?, ?, 0, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                inv_id,
                user_id,
                inv_number,
                currency,
                amount,
                amount,
                amount,
                period_start,
                period_end,
                period_start + timedelta(days=7),
                now,
                now,
                now,
            ],
        )
        conn.execute(
            """
            INSERT INTO personal_invoice_item (
                id, invoice_id, description, quantity, unit_price, amount, created_at
            ) VALUES (?, ?, ?, 1, ?, ?, ?)
            """,
            [
                _next_id(conn, "personal_invoice_item"),
                inv_id,
                f"{plan[1]} ({billing_period})",
                amount,
                amount,
                now,
            ],
        )

        # Processing placeholder — do NOT cancel the active subscription.
        sub_id = _next_id(conn, "personal_subscription")
        conn.execute(
            """
            INSERT INTO personal_subscription (
                id, user_id, plan_id, plan_price_id, household_id, owner_type,
                status, billing_currency, current_period_start, current_period_end,
                cancel_at_period_end, access_state, created_at, updated_at
            ) VALUES (?, ?, ?, ?, NULL, ?, 'processing', ?, ?, ?, FALSE, 'limited', ?, ?)
            """,
            [
                sub_id,
                user_id,
                plan_id,
                int(price[0]),
                OWNER_TYPE_USER,
                currency,
                period_start,
                period_end,
                now,
                now,
            ],
        )
        conn.execute(
            "UPDATE personal_invoice SET personal_subscription_id = ?, updated_at = ? WHERE id = ?",
            [sub_id, now, inv_id],
        )

        cid = _next_id(conn, "personal_checkout_session")
        conn.execute(
            """
            INSERT INTO personal_checkout_session (
                id, user_id, actor_user_id, plan_code, plan_id, plan_price_id, billing_period,
                amount, currency, status, subscription_id, invoice_id, payment_attempt_id,
                payment_method_id, idempotency_key, failure_code, created_at, updated_at,
                expires_at, completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'awaiting_method', ?, ?, NULL, NULL, ?, NULL, ?, ?, ?, NULL)
            """,
            [
                cid,
                user_id,
                user_id,
                plan_code,
                plan_id,
                int(price[0]),
                billing_period,
                amount,
                currency,
                sub_id,
                inv_id,
                key,
                now,
                now,
                expires,
            ],
        )
        uc._emit_event(  # noqa: SLF001 — shared event trail
            conn,
            user_id=user_id,
            event_type="checkout_started",
            subscription_id=sub_id,
            payload={"checkout_id": cid, "plan_code": plan_code, "invoice_id": inv_id},
        )

    return get_checkout(conn, user_id, cid)


def attach_payment_method(
    conn: duckdb.DuckDBPyConnection,
    user_id: int,
    checkout_id: int,
    *,
    brand: str,
    last4: str,
    exp_month: int,
    exp_year: int,
    display_label: str,
    simulation_token: str,
    is_default: bool = True,
) -> dict[str, Any]:
    ensure_personal_subscription_tables(conn)
    if not re.fullmatch(r"\d{4}", str(last4 or "")):
        raise CheckoutError("last4 must be exactly four digits", code="validation_error")
    if not simulation_token or simulation_token not in SIM_TOKEN_SCENARIO:
        raise CheckoutError("Unknown simulation token", code="validation_error")
    now = utc_now()
    if exp_year < now.year or (exp_year == now.year and exp_month < now.month):
        raise CheckoutError("Card expiry is in the past", code="validation_error")

    with transactional(conn):
        session = _map_session(conn, _get_row(conn, checkout_id, user_id))
        if session["status"] not in ("awaiting_method", "ready", "failed", "draft"):
            raise CheckoutError("Checkout cannot accept a method", code="checkout_state_conflict")

        if is_default:
            conn.execute(
                """
                UPDATE personal_payment_method_reference
                SET is_default = FALSE, updated_at = ?
                WHERE user_id = ? AND status = 'active'
                """,
                [now, user_id],
            )
        mid = _next_id(conn, "personal_payment_method_reference")
        conn.execute(
            """
            INSERT INTO personal_payment_method_reference (
                id, user_id, provider_code, brand, last4, exp_month, exp_year,
                display_label, token_ref, simulation_token, is_default, status,
                created_at, updated_at
            ) VALUES (?, ?, 'mock', ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
            """,
            [
                mid,
                user_id,
                brand.strip().lower(),
                last4,
                int(exp_month),
                int(exp_year),
                display_label.strip() or f"{brand} ····{last4}",
                f"pm_ref_{mid}",
                simulation_token,
                bool(is_default),
                now,
                now,
            ],
        )
        conn.execute(
            """
            UPDATE personal_checkout_session
            SET payment_method_id = ?, status = 'ready', failure_code = NULL, updated_at = ?
            WHERE id = ?
            """,
            [mid, now, checkout_id],
        )
        uc._emit_event(
            conn,
            user_id=user_id,
            event_type="checkout_method_attached",
            subscription_id=session.get("subscription_id"),
            payload={"checkout_id": checkout_id, "payment_method_id": mid, "last4": last4},
        )
    return get_checkout(conn, user_id, checkout_id)


def confirm_checkout(
    conn: duckdb.DuckDBPyConnection,
    user_id: int,
    checkout_id: int,
    *,
    idempotency_key: str,
) -> dict[str, Any]:
    ensure_personal_subscription_tables(conn)
    if not idempotency_key or not idempotency_key.strip():
        raise CheckoutError("idempotency_key is required", code="validation_error")
    confirm_key = idempotency_key.strip()

    with transactional(conn):
        session = _map_session(conn, _get_row(conn, checkout_id, user_id))
        if session["status"] == "succeeded":
            return session
        if session["status"] == "processing":
            return session
        if session["status"] not in ("ready", "failed"):
            raise CheckoutError("Checkout is not confirmable", code="checkout_state_conflict")
        if not session.get("payment_method_id"):
            raise CheckoutError("Payment method required", code="payment_method_required")

        # Replay same confirm key
        prior = conn.execute(
            """
            SELECT id, status FROM personal_payment_attempt
            WHERE user_id = ? AND idempotency_key = ?
            """,
            [user_id, confirm_key],
        ).fetchone()
        if prior:
            return get_checkout(conn, user_id, checkout_id)

        pm = conn.execute(
            """
            SELECT simulation_token, brand, last4 FROM personal_payment_method_reference
            WHERE id = ? AND user_id = ? AND status = 'active'
            """,
            [session["payment_method_id"], user_id],
        ).fetchone()
        if not pm:
            raise CheckoutError("Payment method required", code="payment_method_required")
        scenario = SIM_TOKEN_SCENARIO.get(str(pm[0]), "declined")

        now = utc_now()
        conn.execute(
            """
            UPDATE personal_checkout_session
            SET status = 'processing', updated_at = ?, failure_code = NULL
            WHERE id = ?
            """,
            [now, checkout_id],
        )
        uc._emit_event(
            conn,
            user_id=user_id,
            event_type="checkout_processing",
            subscription_id=session.get("subscription_id"),
            payload={"checkout_id": checkout_id},
        )

        attempt_id = _next_id(conn, "personal_payment_attempt")
        conn.execute(
            """
            INSERT INTO personal_payment_attempt (
                id, invoice_id, user_id, amount, currency, status, provider_code,
                is_mock, idempotency_key, scenario, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, 'created', 'mock', TRUE, ?, ?, ?, ?)
            """,
            [
                attempt_id,
                session["invoice_id"],
                user_id,
                _quantize(session["amount"]),
                str(session["currency"]),
                confirm_key,
                scenario,
                now,
                now,
            ],
        )
        conn.execute(
            """
            UPDATE personal_checkout_session
            SET payment_attempt_id = ?, updated_at = ?
            WHERE id = ?
            """,
            [attempt_id, now, checkout_id],
        )

        if scenario == "processing":
            conn.execute(
                """
                UPDATE personal_payment_attempt
                SET status = 'processing', updated_at = ? WHERE id = ?
                """,
                [now, attempt_id],
            )
            return get_checkout(conn, user_id, checkout_id)

        if scenario in ("declined", "failed", "insufficient_funds"):
            conn.execute(
                """
                UPDATE personal_payment_attempt
                SET status = 'failed', error_code = ?, updated_at = ? WHERE id = ?
                """,
                [scenario, now, attempt_id],
            )
            # Fail checkout only — keep active subscription untouched.
            conn.execute(
                """
                UPDATE personal_subscription
                SET status = 'canceled', canceled_at = ?, updated_at = ?
                WHERE id = ? AND status = 'processing'
                """,
                [now, now, session["subscription_id"]],
            )
            conn.execute(
                """
                UPDATE personal_checkout_session
                SET status = 'failed', failure_code = ?, updated_at = ?
                WHERE id = ?
                """,
                [scenario, now, checkout_id],
            )
            uc._emit_event(
                conn,
                user_id=user_id,
                event_type="checkout_failed",
                subscription_id=session.get("subscription_id"),
                payload={"checkout_id": checkout_id, "scenario": scenario},
            )
            return get_checkout(conn, user_id, checkout_id)

        # Success path — activate selected, supersede prior paid.
        try:
            conn.execute(
                """
                UPDATE personal_payment_attempt
                SET status = 'succeeded', scenario = 'succeeded', updated_at = ?
                WHERE id = ?
                """,
                [now, attempt_id],
            )
            amount = _quantize(session["amount"])
            conn.execute(
                """
                UPDATE personal_invoice
                SET status = 'paid', amount_paid = ?, amount_due = 0, paid_at = ?, updated_at = ?
                WHERE id = ?
                """,
                [amount, now, now, session["invoice_id"]],
            )
            # Supersede prior paid (non-free active/past_due) only now — never the target.
            conn.execute(
                """
                UPDATE personal_subscription
                SET status = 'canceled', canceled_at = ?, updated_at = ?
                WHERE id IN (
                    SELECT s.id FROM personal_subscription s
                    JOIN personal_plan p ON p.id = s.plan_id
                    WHERE s.user_id = ? AND p.is_free = FALSE
                      AND s.status IN ('active', 'past_due')
                      AND s.id <> ?
                )
                """,
                [now, now, user_id, session["subscription_id"]],
            )
            conn.execute(
                """
                UPDATE personal_subscription
                SET status = 'active', access_state = 'full', canceled_at = NULL, updated_at = ?
                WHERE id = ?
                """,
                [now, session["subscription_id"]],
            )
            free_plan = conn.execute(
                "SELECT id FROM personal_plan WHERE code = 'personal_free'"
            ).fetchone()
            if free_plan:
                conn.execute(
                    """
                    UPDATE personal_subscription
                    SET status = 'canceled', canceled_at = ?, updated_at = ?
                    WHERE user_id = ? AND plan_id = ? AND status = 'active' AND id <> ?
                    """,
                    [now, now, user_id, int(free_plan[0]), session["subscription_id"]],
                )
            plan_id = int(session["plan_id"])
            sub_id = int(session["subscription_id"])
            uc._materialize_entitlements(conn, sub_id, user_id, plan_id)  # noqa: SLF001
            plan_meta = conn.execute(
                "SELECT code, max_members FROM personal_plan WHERE id = ?", [plan_id]
            ).fetchone()
            if plan_meta:
                uc._ensure_household_for_plan(  # noqa: SLF001
                    conn,
                    user_id=user_id,
                    subscription_id=sub_id,
                    plan_code=str(plan_meta[0]),
                    max_members=int(plan_meta[1]),
                )
            conn.execute(
                """
                UPDATE personal_checkout_session
                SET status = 'succeeded', completed_at = ?, updated_at = ?, failure_code = NULL
                WHERE id = ?
                """,
                [now, now, checkout_id],
            )
            uc._emit_event(
                conn,
                user_id=user_id,
                event_type="checkout_succeeded",
                subscription_id=session.get("subscription_id"),
                payload={"checkout_id": checkout_id, "invoice_id": session["invoice_id"]},
            )
        except CheckoutError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise CheckoutError(
                "Payment confirmation failed",
                code="payment_confirmation_failed",
            ) from exc

    return get_checkout(conn, user_id, checkout_id)


def cancel_checkout(
    conn: duckdb.DuckDBPyConnection,
    user_id: int,
    checkout_id: int,
) -> dict[str, Any]:
    ensure_personal_subscription_tables(conn)
    with transactional(conn):
        session = _map_session(conn, _get_row(conn, checkout_id, user_id))
        if session["status"] in ("succeeded", "canceled", "expired"):
            raise CheckoutError("Checkout cannot be canceled", code="checkout_state_conflict")
        now = utc_now()
        conn.execute(
            """
            UPDATE personal_checkout_session
            SET status = 'canceled', updated_at = ?, completed_at = ?
            WHERE id = ?
            """,
            [now, now, checkout_id],
        )
        if session.get("subscription_id"):
            conn.execute(
                """
                UPDATE personal_subscription
                SET status = 'canceled', canceled_at = ?, updated_at = ?
                WHERE id = ? AND status = 'processing'
                """,
                [now, now, session["subscription_id"]],
            )
        uc._emit_event(
            conn,
            user_id=user_id,
            event_type="checkout_canceled",
            subscription_id=session.get("subscription_id"),
            payload={"checkout_id": checkout_id},
        )
    return get_checkout(conn, user_id, checkout_id)
