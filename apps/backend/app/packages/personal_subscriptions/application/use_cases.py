"""Personal subscription use cases — Spec 029.

owner_type is always ``user`` here. Organization B2B subscriptions stay in Spec 018.
"""

from __future__ import annotations

import hashlib
import json
import secrets
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

import duckdb

from app.core.time_util import utc_now
from app.packages.personal_subscriptions.application.catalog import (
    OWNER_TYPE_USER,
    ensure_personal_catalog,
)
from app.packages.personal_subscriptions.domain.errors import (
    HouseholdCapacityError,
    HouseholdMembershipError,
    InvitationError,
    PersonalForbiddenError,
    PersonalNotFoundError,
    PersonalPaymentError,
    PersonalSubscriptionError,
)
from app.packages.personal_subscriptions.infrastructure.schema import (
    ensure_personal_subscription_tables,
)

GRACE_DAYS = 3
INVITE_TTL_HOURS = 72
INVITE_RATE_LIMIT_PER_HOUR = 10


def _next_id(conn: duckdb.DuckDBPyConnection, table: str) -> int:
    return int(conn.execute(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table}").fetchone()[0])


def _quantize(amount: object) -> Decimal:
    return Decimal(str(amount)).quantize(Decimal("0.01"))


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _emit_event(
    conn: duckdb.DuckDBPyConnection,
    *,
    user_id: int,
    event_type: str,
    subscription_id: Optional[int] = None,
    actor_user_id: Optional[int] = None,
    payload: Optional[dict] = None,
) -> None:
    conn.execute(
        """
        INSERT INTO personal_subscription_event (
            id, personal_subscription_id, user_id, event_type,
            payload_json, actor_user_id, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            _next_id(conn, "personal_subscription_event"),
            subscription_id,
            user_id,
            event_type,
            json.dumps(payload or {}, default=str),
            actor_user_id or user_id,
            utc_now(),
        ],
    )


def _materialize_entitlements(
    conn: duckdb.DuckDBPyConnection, subscription_id: int, user_id: int, plan_id: int
) -> None:
    now = utc_now()
    conn.execute(
        "DELETE FROM personal_entitlement WHERE personal_subscription_id = ?",
        [subscription_id],
    )
    feats = conn.execute(
        """
        SELECT feature_code, limit_value, enabled
        FROM personal_plan_feature WHERE plan_id = ?
        """,
        [plan_id],
    ).fetchall()
    for f in feats:
        conn.execute(
            """
            INSERT INTO personal_entitlement (
                id, personal_subscription_id, user_id, feature_code,
                limit_value, enabled, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                _next_id(conn, "personal_entitlement"),
                subscription_id,
                user_id,
                f[0],
                f[1],
                f[2],
                now,
                now,
            ],
        )


def ensure_free_subscription(conn: duckdb.DuckDBPyConnection, user_id: int) -> Dict[str, Any]:
    """Idempotent Free assignment for a personal user (no invoice)."""
    ensure_personal_subscription_tables(conn)
    ensure_personal_catalog(conn)

    existing = conn.execute(
        """
        SELECT s.id FROM personal_subscription s
        JOIN personal_plan p ON p.id = s.plan_id
        WHERE s.user_id = ? AND p.code = 'personal_free'
          AND s.status IN ('active', 'past_due', 'processing')
        LIMIT 1
        """,
        [user_id],
    ).fetchone()
    if existing:
        return get_subscription(conn, user_id)

    # If user already has premium active, leave Free absent as active primary
    premium = conn.execute(
        """
        SELECT s.id FROM personal_subscription s
        JOIN personal_plan p ON p.id = s.plan_id
        WHERE s.user_id = ? AND p.is_free = FALSE
          AND s.status IN ('active', 'past_due', 'processing')
        LIMIT 1
        """,
        [user_id],
    ).fetchone()
    if premium:
        return get_subscription(conn, user_id)

    plan = conn.execute(
        "SELECT id FROM personal_plan WHERE code = 'personal_free'"
    ).fetchone()
    if not plan:
        raise PersonalSubscriptionError("Free plan missing from catalog")
    plan_id = int(plan[0])
    now = utc_now()
    sub_id = _next_id(conn, "personal_subscription")
    conn.execute(
        """
        INSERT INTO personal_subscription (
            id, user_id, plan_id, plan_price_id, household_id, owner_type,
            status, billing_currency, current_period_start, current_period_end,
            cancel_at_period_end, access_state, created_at, updated_at
        ) VALUES (?, ?, ?, NULL, NULL, ?, 'active', 'USD', ?, ?, FALSE, 'full', ?, ?)
        """,
        [
            sub_id,
            user_id,
            plan_id,
            OWNER_TYPE_USER,
            date.today(),
            date.today() + timedelta(days=3650),
            now,
            now,
        ],
    )
    _materialize_entitlements(conn, sub_id, user_id, plan_id)
    _emit_event(
        conn,
        user_id=user_id,
        event_type="free_assigned",
        subscription_id=sub_id,
        payload={"plan": "personal_free"},
    )
    return get_subscription(conn, user_id)


def get_subscription(conn: duckdb.DuckDBPyConnection, user_id: int) -> Dict[str, Any]:
    ensure_personal_subscription_tables(conn)
    ensure_personal_catalog(conn)
    row = conn.execute(
        """
        SELECT s.id, s.user_id, s.plan_id, s.plan_price_id, s.household_id,
               s.status, s.billing_currency, s.current_period_start, s.current_period_end,
               s.cancel_at_period_end, s.canceled_at, s.grace_until, s.access_state,
               p.code, p.display_name, p.is_free, p.max_members,
               pr.billing_period, pr.amount
        FROM personal_subscription s
        JOIN personal_plan p ON p.id = s.plan_id
        LEFT JOIN personal_plan_price pr ON pr.id = s.plan_price_id
        WHERE s.user_id = ? AND s.status IN ('active', 'past_due', 'processing')
        ORDER BY CASE WHEN p.is_free THEN 1 ELSE 0 END, s.id DESC
        LIMIT 1
        """,
        [user_id],
    ).fetchone()
    if not row:
        return ensure_free_subscription(conn, user_id)

    # Household membership context
    hh = conn.execute(
        """
        SELECT h.id, h.plan_code, h.max_members, hm.role
        FROM household_member hm
        JOIN household h ON h.id = hm.household_id
        WHERE hm.user_id = ? AND hm.status = 'active' AND h.status = 'active'
        LIMIT 1
        """,
        [user_id],
    ).fetchone()

    return {
        "id": int(row[0]),
        "user_id": int(row[1]),
        "owner_type": OWNER_TYPE_USER,
        "plan_id": int(row[2]),
        "plan_price_id": int(row[3]) if row[3] is not None else None,
        "household_id": int(row[4]) if row[4] is not None else (int(hh[0]) if hh else None),
        "status": row[5],
        "billing_currency": row[6],
        "current_period_start": str(row[7]) if row[7] else None,
        "current_period_end": str(row[8]) if row[8] else None,
        "cancel_at_period_end": bool(row[9]),
        "canceled_at": str(row[10]) if row[10] else None,
        "grace_until": str(row[11]) if row[11] else None,
        "access_state": row[12],
        "plan_code": row[13],
        "plan_name": row[14],
        "is_free": bool(row[15]),
        "max_members": int(row[16]),
        "billing_period": row[17],
        "amount": float(row[18]) if row[18] is not None else 0.0,
        "household_role": hh[3] if hh else ("owner" if not bool(row[15]) and row[4] else None),
    }


def list_personal_plans(conn: duckdb.DuckDBPyConnection) -> List[Dict[str, Any]]:
    ensure_personal_subscription_tables(conn)
    ensure_personal_catalog(conn)
    plans = conn.execute(
        """
        SELECT id, code, display_name, description, max_members, is_free, sort_order
        FROM personal_plan WHERE status = 'active'
        ORDER BY sort_order
        """
    ).fetchall()
    out: List[Dict[str, Any]] = []
    for p in plans:
        prices = conn.execute(
            """
            SELECT id, billing_period, amount, currency, status
            FROM personal_plan_price
            WHERE plan_id = ? AND status = 'active'
            ORDER BY billing_period
            """,
            [p[0]],
        ).fetchall()
        features = conn.execute(
            """
            SELECT feature_code, limit_value, enabled
            FROM personal_plan_feature WHERE plan_id = ?
            """,
            [p[0]],
        ).fetchall()
        out.append(
            {
                "id": int(p[0]),
                "code": p[1],
                "display_name": p[2],
                "description": p[3],
                "max_members": int(p[4]),
                "is_free": bool(p[5]),
                "sort_order": int(p[6]),
                "prices": [
                    {
                        "id": int(r[0]),
                        "billing_period": r[1],
                        "amount": float(_quantize(r[2])),
                        "currency": r[3],
                        "status": r[4],
                    }
                    for r in prices
                ],
                "features": [
                    {
                        "feature_code": f[0],
                        "limit_value": int(f[1]) if f[1] is not None else None,
                        "enabled": bool(f[2]),
                    }
                    for f in features
                ],
            }
        )
    return out


def _cancel_active_non_free(conn: duckdb.DuckDBPyConnection, user_id: int) -> None:
    now = utc_now()
    rows = conn.execute(
        """
        SELECT s.id FROM personal_subscription s
        JOIN personal_plan p ON p.id = s.plan_id
        WHERE s.user_id = ? AND p.is_free = FALSE
          AND s.status IN ('active', 'past_due', 'processing')
        """,
        [user_id],
    ).fetchall()
    for r in rows:
        conn.execute(
            """
            UPDATE personal_subscription
            SET status = 'canceled', canceled_at = ?, updated_at = ?
            WHERE id = ?
            """,
            [now, now, int(r[0])],
        )


def start_checkout(
    conn: duckdb.DuckDBPyConnection,
    user_id: int,
    *,
    plan_code: str,
    billing_period: str,
) -> Dict[str, Any]:
    """Create personal invoice + mock payment attempt for a premium plan."""
    ensure_personal_subscription_tables(conn)
    ensure_personal_catalog(conn)
    if plan_code == "personal_free":
        raise PersonalSubscriptionError("Free no requiere checkout", code="invalid_plan")
    if billing_period not in ("monthly", "annual"):
        raise PersonalSubscriptionError("Periodo inválido", code="invalid_period")

    # Members of another household cannot buy a conflicting household plan as second home
    member = conn.execute(
        """
        SELECT hm.household_id, hm.role FROM household_member hm
        JOIN household h ON h.id = hm.household_id
        WHERE hm.user_id = ? AND hm.status = 'active' AND h.status = 'active'
        """,
        [user_id],
    ).fetchone()
    if member and member[1] == "member":
        raise HouseholdMembershipError(
            "Ya perteneces a un household. Abandónalo antes de contratar otro plan."
        )

    plan = conn.execute(
        "SELECT id, display_name, max_members, is_free FROM personal_plan WHERE code = ? AND status = 'active'",
        [plan_code],
    ).fetchone()
    if not plan or bool(plan[3]):
        raise PersonalNotFoundError("Plan no encontrado")
    plan_id = int(plan[0])
    price = conn.execute(
        """
        SELECT id, amount, currency FROM personal_plan_price
        WHERE plan_id = ? AND billing_period = ? AND status = 'active'
        """,
        [plan_id, billing_period],
    ).fetchone()
    if not price:
        raise PersonalNotFoundError("Precio no disponible")

    amount = _quantize(price[1])
    now = utc_now()
    period_days = 30 if billing_period == "monthly" else 365
    period_start = date.today()
    period_end = period_start + timedelta(days=period_days)

    inv_id = _next_id(conn, "personal_invoice")
    inv_number = f"PINV-{user_id}-{inv_id}"
    conn.execute(
        """
        INSERT INTO personal_invoice (
            id, user_id, personal_subscription_id, invoice_number, currency, status,
            subtotal, total, amount_paid, amount_due, period_start, period_end,
            due_date, issued_at, created_at, updated_at
        ) VALUES (?, ?, NULL, ?, 'USD', 'issued', ?, ?, 0, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            inv_id,
            user_id,
            inv_number,
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

    # Placeholder subscription in processing until payment succeeds
    _cancel_active_non_free(conn, user_id)
    sub_id = _next_id(conn, "personal_subscription")
    conn.execute(
        """
        INSERT INTO personal_subscription (
            id, user_id, plan_id, plan_price_id, household_id, owner_type,
            status, billing_currency, current_period_start, current_period_end,
            cancel_at_period_end, access_state, created_at, updated_at
        ) VALUES (?, ?, ?, ?, NULL, ?, 'processing', 'USD', ?, ?, FALSE, 'limited', ?, ?)
        """,
        [
            sub_id,
            user_id,
            plan_id,
            int(price[0]),
            OWNER_TYPE_USER,
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

    attempt_id = _next_id(conn, "personal_payment_attempt")
    idem = f"ppay-{user_id}-{inv_id}-checkout"
    conn.execute(
        """
        INSERT INTO personal_payment_attempt (
            id, invoice_id, user_id, amount, currency, status, provider_code,
            is_mock, idempotency_key, scenario, created_at, updated_at
        ) VALUES (?, ?, ?, ?, 'USD', 'created', 'mock', TRUE, ?, NULL, ?, ?)
        """,
        [attempt_id, inv_id, user_id, amount, idem, now, now],
    )
    _emit_event(
        conn,
        user_id=user_id,
        event_type="checkout_started",
        subscription_id=sub_id,
        payload={"plan_code": plan_code, "invoice_id": inv_id},
    )
    return {
        "subscription_id": sub_id,
        "invoice_id": inv_id,
        "invoice_number": inv_number,
        "attempt_id": attempt_id,
        "amount": float(amount),
        "currency": "USD",
        "plan_code": plan_code,
        "billing_period": billing_period,
        "status": "processing",
    }


def simulate_payment(
    conn: duckdb.DuckDBPyConnection,
    user_id: int,
    *,
    attempt_id: int,
    scenario: str = "succeeded",
) -> Dict[str, Any]:
    """Mock payment outcomes: succeeded | declined | processing."""
    ensure_personal_subscription_tables(conn)
    att = conn.execute(
        """
        SELECT id, invoice_id, amount, status, idempotency_key
        FROM personal_payment_attempt WHERE id = ? AND user_id = ?
        """,
        [attempt_id, user_id],
    ).fetchone()
    if not att:
        raise PersonalNotFoundError("Intento de pago no encontrado")
    if att[3] == "succeeded":
        return {"attempt_id": attempt_id, "status": "succeeded", "idempotent": True}

    now = utc_now()
    scenario = (scenario or "succeeded").strip().lower()
    if scenario == "processing":
        conn.execute(
            """
            UPDATE personal_payment_attempt
            SET status = 'processing', scenario = ?, updated_at = ?
            WHERE id = ?
            """,
            [scenario, now, attempt_id],
        )
        return {"attempt_id": attempt_id, "status": "processing"}

    if scenario in ("declined", "failed", "insufficient_funds"):
        conn.execute(
            """
            UPDATE personal_payment_attempt
            SET status = 'failed', scenario = ?, error_code = ?, updated_at = ?
            WHERE id = ?
            """,
            [scenario, scenario, now, attempt_id],
        )
        inv_id = int(att[1])
        sub = conn.execute(
            "SELECT personal_subscription_id FROM personal_invoice WHERE id = ? AND user_id = ?",
            [inv_id, user_id],
        ).fetchone()
        if sub and sub[0]:
            grace = now + timedelta(days=GRACE_DAYS)
            conn.execute(
                """
                UPDATE personal_subscription
                SET status = 'past_due', access_state = 'limited',
                    grace_until = ?, updated_at = ?
                WHERE id = ?
                """,
                [grace, now, int(sub[0])],
            )
            # Ensure Free remains available
            free_plan = conn.execute(
                "SELECT id FROM personal_plan WHERE code = 'personal_free'"
            ).fetchone()
            free_active = conn.execute(
                """
                SELECT s.id FROM personal_subscription s
                WHERE s.user_id = ? AND s.plan_id = ? AND s.status = 'active'
                """,
                [user_id, int(free_plan[0])],
            ).fetchone()
            if not free_active and free_plan:
                # Soft: activate Free access by leaving free entitlements via ensure
                pass
            ensure_free_subscription(conn, user_id)
            _emit_event(
                conn,
                user_id=user_id,
                event_type="payment_declined",
                subscription_id=int(sub[0]),
                payload={"scenario": scenario},
            )
        conn.execute(
            "UPDATE personal_invoice SET status = 'past_due', updated_at = ? WHERE id = ?",
            [now, inv_id],
        )
        return {"attempt_id": attempt_id, "status": "failed", "scenario": scenario}

    # succeeded
    conn.execute(
        """
        UPDATE personal_payment_attempt
        SET status = 'succeeded', scenario = 'succeeded', updated_at = ?
        WHERE id = ?
        """,
        [now, attempt_id],
    )
    inv_id = int(att[1])
    amount = _quantize(att[2])
    conn.execute(
        """
        UPDATE personal_invoice
        SET status = 'paid', amount_paid = ?, amount_due = 0, paid_at = ?, updated_at = ?
        WHERE id = ?
        """,
        [amount, now, now, inv_id],
    )
    inv = conn.execute(
        "SELECT personal_subscription_id FROM personal_invoice WHERE id = ?",
        [inv_id],
    ).fetchone()
    sub_id = int(inv[0]) if inv and inv[0] else None
    if sub_id:
        # Cancel Free while premium active
        conn.execute(
            """
            UPDATE personal_subscription
            SET status = 'canceled', canceled_at = ?, updated_at = ?
            WHERE user_id = ? AND id != ? AND status = 'active'
              AND plan_id = (SELECT id FROM personal_plan WHERE code = 'personal_free')
            """,
            [now, now, user_id, sub_id],
        )
        conn.execute(
            """
            UPDATE personal_subscription
            SET status = 'active', access_state = 'full', grace_until = NULL, updated_at = ?
            WHERE id = ?
            """,
            [now, sub_id],
        )
        plan_row = conn.execute(
            "SELECT plan_id FROM personal_subscription WHERE id = ?", [sub_id]
        ).fetchone()
        plan_id = int(plan_row[0])
        _materialize_entitlements(conn, sub_id, user_id, plan_id)
        plan_meta = conn.execute(
            "SELECT code, max_members FROM personal_plan WHERE id = ?", [plan_id]
        ).fetchone()
        _ensure_household_for_plan(
            conn, user_id=user_id, subscription_id=sub_id,
            plan_code=str(plan_meta[0]), max_members=int(plan_meta[1]),
        )
        _emit_event(
            conn,
            user_id=user_id,
            event_type="payment_succeeded",
            subscription_id=sub_id,
            payload={"invoice_id": inv_id},
        )
        _send_confirmation_email(conn, user_id, plan_code=str(plan_meta[0]))
    return {"attempt_id": attempt_id, "status": "succeeded", "invoice_id": inv_id}


def _send_confirmation_email(
    conn: duckdb.DuckDBPyConnection, user_id: int, *, plan_code: str
) -> None:
    """Console-only email path during tests / default config."""
    try:
        from app.packages.platform_ops.application.email_service import send_rendered_email
        from app.packages.platform_ops.application.email_templates import RenderedEmail

        user = conn.execute(
            "SELECT email, username FROM app_user WHERE id = ?", [user_id]
        ).fetchone()
        if not user:
            return
        rendered = RenderedEmail(
            subject=f"VOXMETRIKS — Confirmación {plan_code}",
            body_text=(
                f"Hola {user[1]}, tu suscripción personal {plan_code} "
                "está activa. Este correo es de confirmación."
            ),
            body_html=(
                f"<p>Hola {_esc(user[1])}, tu suscripción personal "
                f"<strong>{_esc(plan_code)}</strong> está activa.</p>"
            ),
            template_code="personal_subscription_confirmation",
        )
        send_rendered_email(
            to_address=str(user[0]),
            rendered=rendered,
            conn=conn,
            related_type="personal_subscription",
            related_id=str(user_id),
            idempotency_key=f"personal-confirm-{user_id}-{plan_code}-{date.today().isoformat()}",
        )
    except Exception:  # noqa: BLE001 — never fail checkout on email
        pass


def _esc(value: object) -> str:
    import html

    return html.escape(str(value if value is not None else ""), quote=True)


def _ensure_household_for_plan(
    conn: duckdb.DuckDBPyConnection,
    *,
    user_id: int,
    subscription_id: int,
    plan_code: str,
    max_members: int,
) -> Optional[int]:
    if max_members <= 1:
        return None
    now = utc_now()
    existing = conn.execute(
        """
        SELECT id FROM household
        WHERE owner_user_id = ? AND status = 'active'
        """,
        [user_id],
    ).fetchone()
    if existing:
        hh_id = int(existing[0])
        conn.execute(
            """
            UPDATE household SET plan_code = ?, max_members = ?, updated_at = ?
            WHERE id = ?
            """,
            [plan_code, max_members, now, hh_id],
        )
    else:
        hh_id = _next_id(conn, "household")
        conn.execute(
            """
            INSERT INTO household (
                id, owner_user_id, plan_code, max_members, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 'active', ?, ?)
            """,
            [hh_id, user_id, plan_code, max_members, now, now],
        )
        conn.execute(
            """
            INSERT INTO household_member (
                id, household_id, user_id, role, status, joined_at, created_at, updated_at
            ) VALUES (?, ?, ?, 'owner', 'active', ?, ?, ?)
            """,
            [_next_id(conn, "household_member"), hh_id, user_id, now, now, now],
        )
    conn.execute(
        "UPDATE personal_subscription SET household_id = ?, updated_at = ? WHERE id = ?",
        [hh_id, now, subscription_id],
    )
    return hh_id


def apply_grace_expiry(conn: duckdb.DuckDBPyConnection, user_id: int) -> Dict[str, Any]:
    """Downgrade past_due after grace without deleting playlists/favorites/history."""
    ensure_personal_subscription_tables(conn)
    now = utc_now()
    rows = conn.execute(
        """
        SELECT s.id, s.household_id FROM personal_subscription s
        JOIN personal_plan p ON p.id = s.plan_id
        WHERE s.user_id = ? AND s.status = 'past_due'
          AND (s.grace_until IS NULL OR s.grace_until <= ?)
          AND p.is_free = FALSE
        """,
        [user_id, now],
    ).fetchall()
    for r in rows:
        conn.execute(
            """
            UPDATE personal_subscription
            SET status = 'expired', access_state = 'blocked', updated_at = ?
            WHERE id = ?
            """,
            [now, int(r[0])],
        )
        if r[1]:
            _close_household(conn, int(r[1]), actor_user_id=user_id)
        _emit_event(
            conn,
            user_id=user_id,
            event_type="downgraded_to_free",
            subscription_id=int(r[0]),
        )
    return ensure_free_subscription(conn, user_id)


def cancel_subscription(
    conn: duckdb.DuckDBPyConnection, user_id: int, *, at_period_end: bool = True
) -> Dict[str, Any]:
    ensure_personal_subscription_tables(conn)
    sub = conn.execute(
        """
        SELECT s.id, s.household_id, s.current_period_end FROM personal_subscription s
        JOIN personal_plan p ON p.id = s.plan_id
        WHERE s.user_id = ? AND p.is_free = FALSE
          AND s.status IN ('active', 'past_due', 'processing')
        ORDER BY s.id DESC LIMIT 1
        """,
        [user_id],
    ).fetchone()
    if not sub:
        raise PersonalNotFoundError("No hay suscripción premium activa")
    now = utc_now()
    if at_period_end:
        conn.execute(
            """
            UPDATE personal_subscription
            SET cancel_at_period_end = TRUE, updated_at = ?
            WHERE id = ?
            """,
            [now, int(sub[0])],
        )
        _emit_event(
            conn,
            user_id=user_id,
            event_type="cancel_scheduled",
            subscription_id=int(sub[0]),
        )
    else:
        conn.execute(
            """
            UPDATE personal_subscription
            SET status = 'canceled', cancel_at_period_end = FALSE,
                canceled_at = ?, updated_at = ?
            WHERE id = ?
            """,
            [now, now, int(sub[0])],
        )
        if sub[1]:
            _close_household(conn, int(sub[1]), actor_user_id=user_id)
        ensure_free_subscription(conn, user_id)
        _emit_event(
            conn,
            user_id=user_id,
            event_type="canceled_immediate",
            subscription_id=int(sub[0]),
        )
    return get_subscription(conn, user_id)


def finalize_period_end_cancellations(conn: duckdb.DuckDBPyConnection, user_id: int) -> Dict[str, Any]:
    """When paid period ends, return owner + members to Free."""
    now = utc_now()
    rows = conn.execute(
        """
        SELECT s.id, s.household_id FROM personal_subscription s
        JOIN personal_plan p ON p.id = s.plan_id
        WHERE s.user_id = ? AND s.cancel_at_period_end = TRUE
          AND s.status = 'active' AND p.is_free = FALSE
          AND (s.current_period_end IS NULL OR s.current_period_end <= ?)
        """,
        [user_id, date.today()],
    ).fetchall()
    for r in rows:
        conn.execute(
            """
            UPDATE personal_subscription
            SET status = 'canceled', canceled_at = ?, updated_at = ?
            WHERE id = ?
            """,
            [now, now, int(r[0])],
        )
        if r[1]:
            _close_household(conn, int(r[1]), actor_user_id=user_id)
    return ensure_free_subscription(conn, user_id)


def _close_household(
    conn: duckdb.DuckDBPyConnection, household_id: int, *, actor_user_id: int
) -> None:
    now = utc_now()
    members = conn.execute(
        """
        SELECT user_id FROM household_member
        WHERE household_id = ? AND status = 'active' AND role = 'member'
        """,
        [household_id],
    ).fetchall()
    conn.execute(
        """
        UPDATE household_member SET status = 'removed', left_at = ?, updated_at = ?
        WHERE household_id = ? AND status = 'active'
        """,
        [now, now, household_id],
    )
    conn.execute(
        "UPDATE household SET status = 'closed', updated_at = ? WHERE id = ?",
        [now, household_id],
    )
    for m in members:
        ensure_free_subscription(conn, int(m[0]))
        _emit_event(
            conn,
            user_id=int(m[0]),
            event_type="returned_to_free_after_household_close",
            actor_user_id=actor_user_id,
            payload={"household_id": household_id},
        )


def change_billing_period(
    conn: duckdb.DuckDBPyConnection,
    user_id: int,
    *,
    billing_period: str,
) -> Dict[str, Any]:
    """Switch monthly/annual on active premium (issues new invoice + attempt)."""
    sub = get_subscription(conn, user_id)
    if sub.get("is_free"):
        raise PersonalSubscriptionError("Contrata un plan premium primero")
    return start_checkout(
        conn, user_id, plan_code=sub["plan_code"], billing_period=billing_period
    )


def refund_latest_paid(
    conn: duckdb.DuckDBPyConnection, user_id: int
) -> Dict[str, Any]:
    ensure_personal_subscription_tables(conn)
    inv = conn.execute(
        """
        SELECT id, personal_subscription_id, total FROM personal_invoice
        WHERE user_id = ? AND status = 'paid'
        ORDER BY id DESC LIMIT 1
        """,
        [user_id],
    ).fetchone()
    if not inv:
        raise PersonalNotFoundError("No hay factura pagada para reembolsar")
    now = utc_now()
    conn.execute(
        "UPDATE personal_invoice SET status = 'refunded', updated_at = ? WHERE id = ?",
        [now, int(inv[0])],
    )
    if inv[1]:
        conn.execute(
            """
            UPDATE personal_subscription
            SET status = 'canceled', canceled_at = ?, updated_at = ?
            WHERE id = ?
            """,
            [now, now, int(inv[1])],
        )
        hh = conn.execute(
            "SELECT household_id FROM personal_subscription WHERE id = ?",
            [int(inv[1])],
        ).fetchone()
        if hh and hh[0]:
            _close_household(conn, int(hh[0]), actor_user_id=user_id)
    ensure_free_subscription(conn, user_id)
    _emit_event(
        conn,
        user_id=user_id,
        event_type="refunded",
        subscription_id=int(inv[1]) if inv[1] else None,
        payload={"invoice_id": int(inv[0])},
    )
    return {"invoice_id": int(inv[0]), "status": "refunded"}


# ── Household ──────────────────────────────────────────────────────────────


def get_household(conn: duckdb.DuckDBPyConnection, user_id: int) -> Optional[Dict[str, Any]]:
    ensure_personal_subscription_tables(conn)
    row = conn.execute(
        """
        SELECT h.id, h.owner_user_id, h.plan_code, h.max_members, h.status, hm.role
        FROM household_member hm
        JOIN household h ON h.id = hm.household_id
        WHERE hm.user_id = ? AND hm.status = 'active' AND h.status = 'active'
        LIMIT 1
        """,
        [user_id],
    ).fetchone()
    if not row:
        return None
    members = conn.execute(
        """
        SELECT hm.user_id, hm.role, hm.status, hm.joined_at, u.username, u.email
        FROM household_member hm
        LEFT JOIN app_user u ON u.id = hm.user_id
        WHERE hm.household_id = ? AND hm.status = 'active'
        ORDER BY CASE WHEN hm.role = 'owner' THEN 0 ELSE 1 END, hm.id
        """,
        [int(row[0])],
    ).fetchall()
    invites = conn.execute(
        """
        SELECT id, email_normalized, status, expires_at, created_at
        FROM household_invitation
        WHERE household_id = ? AND status = 'pending'
        ORDER BY id DESC
        """,
        [int(row[0])],
    ).fetchall()
    active_count = len(members)
    return {
        "id": int(row[0]),
        "owner_user_id": int(row[1]),
        "plan_code": row[2],
        "max_members": int(row[3]),
        "status": row[4],
        "my_role": row[5],
        "seats_used": active_count,
        "seats_available": max(0, int(row[3]) - active_count),
        "members": [
            {
                "user_id": int(m[0]),
                "role": m[1],
                "status": m[2],
                "joined_at": str(m[3]) if m[3] else None,
                "username": m[4],
                "email": m[5],
            }
            for m in members
        ],
        "pending_invitations": [
            {
                "id": int(i[0]),
                "email": i[1],
                "status": i[2],
                "expires_at": str(i[3]) if i[3] else None,
                "created_at": str(i[4]) if i[4] else None,
            }
            for i in invites
        ],
    }


def invite_member(
    conn: duckdb.DuckDBPyConnection, owner_user_id: int, email: str
) -> Dict[str, Any]:
    ensure_personal_subscription_tables(conn)
    hh = get_household(conn, owner_user_id)
    if not hh or hh["my_role"] != "owner":
        raise PersonalForbiddenError("Solo el titular gestiona invitaciones")
    if hh["seats_available"] <= 0:
        raise HouseholdCapacityError(
            f"Capacidad máxima ({hh['max_members']}) alcanzada"
        )

    email_n = email.strip().lower()
    recent = conn.execute(
        """
        SELECT COUNT(*) FROM household_invitation
        WHERE invited_by_user_id = ?
          AND created_at >= ?
        """,
        [owner_user_id, utc_now() - timedelta(hours=1)],
    ).fetchone()
    if recent and int(recent[0]) >= INVITE_RATE_LIMIT_PER_HOUR:
        raise InvitationError("Límite de invitaciones por hora alcanzado", code="rate_limited")

    # Target user must not be in another active household
    target = conn.execute(
        "SELECT id FROM app_user WHERE LOWER(email) = ?", [email_n]
    ).fetchone()
    if target:
        other = conn.execute(
            """
            SELECT 1 FROM household_member hm
            JOIN household h ON h.id = hm.household_id
            WHERE hm.user_id = ? AND hm.status = 'active' AND h.status = 'active'
            """,
            [int(target[0])],
        ).fetchone()
        if other:
            raise HouseholdMembershipError(
                "El usuario ya pertenece a un household activo"
            )

    raw = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw)
    now = utc_now()
    inv_id = _next_id(conn, "household_invitation")
    conn.execute(
        """
        INSERT INTO household_invitation (
            id, household_id, email_normalized, invited_by_user_id, token_hash,
            status, expires_at, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?)
        """,
        [
            inv_id,
            hh["id"],
            email_n,
            owner_user_id,
            token_hash,
            now + timedelta(hours=INVITE_TTL_HOURS),
            now,
            now,
        ],
    )
    _emit_event(
        conn,
        user_id=owner_user_id,
        event_type="household_invite_sent",
        payload={"invitation_id": inv_id, "email": email_n},
    )
    # Dev/console token for tests (never store raw token in DB)
    return {
        "invitation_id": inv_id,
        "email": email_n,
        "expires_at": (now + timedelta(hours=INVITE_TTL_HOURS)).isoformat(),
        "token": raw,
        "status": "pending",
    }


def cancel_invitation(
    conn: duckdb.DuckDBPyConnection, owner_user_id: int, invitation_id: int
) -> None:
    hh = get_household(conn, owner_user_id)
    if not hh or hh["my_role"] != "owner":
        raise PersonalForbiddenError("Solo el titular cancela invitaciones")
    now = utc_now()
    conn.execute(
        """
        UPDATE household_invitation
        SET status = 'canceled', updated_at = ?
        WHERE id = ? AND household_id = ? AND status = 'pending'
        """,
        [now, invitation_id, hh["id"]],
    )


def accept_invitation(
    conn: duckdb.DuckDBPyConnection, user_id: int, token: str
) -> Dict[str, Any]:
    ensure_personal_subscription_tables(conn)
    token_hash = _hash_token(token)
    now = utc_now()
    inv = conn.execute(
        """
        SELECT id, household_id, email_normalized, status, expires_at
        FROM household_invitation WHERE token_hash = ?
        """,
        [token_hash],
    ).fetchone()
    if not inv:
        raise InvitationError("Invitación inválida")
    if inv[3] != "pending":
        raise InvitationError("Invitación ya utilizada o cancelada")
    if inv[4] and inv[4] < now:
        conn.execute(
            "UPDATE household_invitation SET status = 'expired', updated_at = ? WHERE id = ?",
            [now, int(inv[0])],
        )
        raise InvitationError("Invitación expirada")

    user = conn.execute(
        "SELECT email FROM app_user WHERE id = ?", [user_id]
    ).fetchone()
    if not user or str(user[0]).strip().lower() != str(inv[2]):
        raise PersonalForbiddenError("La invitación no corresponde a tu correo")

    existing = conn.execute(
        """
        SELECT 1 FROM household_member hm
        JOIN household h ON h.id = hm.household_id
        WHERE hm.user_id = ? AND hm.status = 'active' AND h.status = 'active'
        """,
        [user_id],
    ).fetchone()
    if existing:
        raise HouseholdMembershipError("Ya perteneces a un household activo")

    hh = conn.execute(
        "SELECT max_members, status FROM household WHERE id = ?", [int(inv[1])]
    ).fetchone()
    if not hh or hh[1] != "active":
        raise HouseholdCapacityError("Household no disponible")
    count = int(
        conn.execute(
            "SELECT COUNT(*) FROM household_member WHERE household_id = ? AND status = 'active'",
            [int(inv[1])],
        ).fetchone()[0]
    )
    if count >= int(hh[0]):
        raise HouseholdCapacityError("Capacidad máxima alcanzada")

    conn.execute(
        """
        INSERT INTO household_member (
            id, household_id, user_id, role, status, joined_at, created_at, updated_at
        ) VALUES (?, ?, ?, 'member', 'active', ?, ?, ?)
        """,
        [_next_id(conn, "household_member"), int(inv[1]), user_id, now, now, now],
    )
    conn.execute(
        """
        UPDATE household_invitation
        SET status = 'accepted', accepted_at = ?, accepted_by_user_id = ?, updated_at = ?
        WHERE id = ?
        """,
        [now, user_id, now, int(inv[0])],
    )
    # Cancel member's own conflicting premium (keep library; inherit household)
    _cancel_active_non_free(conn, user_id)
    _emit_event(
        conn,
        user_id=user_id,
        event_type="household_joined",
        payload={"household_id": int(inv[1])},
    )
    return get_household(conn, user_id) or {}


def remove_member(
    conn: duckdb.DuckDBPyConnection, owner_user_id: int, member_user_id: int
) -> Dict[str, Any]:
    hh = get_household(conn, owner_user_id)
    if not hh or hh["my_role"] != "owner":
        raise PersonalForbiddenError("Solo el titular elimina miembros")
    if member_user_id == owner_user_id:
        raise HouseholdMembershipError("El titular no puede eliminarse a sí mismo")
    now = utc_now()
    conn.execute(
        """
        UPDATE household_member
        SET status = 'removed', left_at = ?, updated_at = ?
        WHERE household_id = ? AND user_id = ? AND status = 'active'
        """,
        [now, now, hh["id"], member_user_id],
    )
    ensure_free_subscription(conn, member_user_id)
    _emit_event(
        conn,
        user_id=member_user_id,
        event_type="removed_from_household",
        actor_user_id=owner_user_id,
    )
    return get_household(conn, owner_user_id) or {}


def list_invoices(conn: duckdb.DuckDBPyConnection, user_id: int) -> List[Dict[str, Any]]:
    ensure_personal_subscription_tables(conn)
    rows = conn.execute(
        """
        SELECT id, invoice_number, currency, status, total, amount_paid, amount_due,
               period_start, period_end, issued_at, paid_at
        FROM personal_invoice WHERE user_id = ?
        ORDER BY id DESC
        """,
        [user_id],
    ).fetchall()
    return [
        {
            "id": int(r[0]),
            "invoice_number": r[1],
            "currency": r[2],
            "status": r[3],
            "total": float(r[4]),
            "amount_paid": float(r[5]),
            "amount_due": float(r[6]),
            "period_start": str(r[7]) if r[7] else None,
            "period_end": str(r[8]) if r[8] else None,
            "issued_at": str(r[9]) if r[9] else None,
            "paid_at": str(r[10]) if r[10] else None,
        }
        for r in rows
    ]


def personal_metrics(conn: duckdb.DuckDBPyConnection) -> Dict[str, Any]:
    """B2C metrics — never mix with B2B without explicit labels."""
    ensure_personal_subscription_tables(conn)
    ensure_personal_catalog(conn)

    def _count(code: str) -> int:
        return int(
            conn.execute(
                """
                SELECT COUNT(*) FROM personal_subscription s
                JOIN personal_plan p ON p.id = s.plan_id
                WHERE p.code = ? AND s.status = 'active'
                """,
                [code],
            ).fetchone()[0]
        )

    free_users = _count("personal_free")
    individual = _count("premium_individual")
    duo = _count("premium_duo")
    family = _count("premium_family")

    mrr_rows = conn.execute(
        """
        SELECT COALESCE(SUM(
            CASE WHEN pr.billing_period = 'annual' THEN pr.amount / 12 ELSE pr.amount END
        ), 0)
        FROM personal_subscription s
        JOIN personal_plan p ON p.id = s.plan_id
        JOIN personal_plan_price pr ON pr.id = s.plan_price_id
        WHERE s.status = 'active' AND p.is_free = FALSE AND s.billing_currency = 'USD'
        """
    ).fetchone()
    past_due_mrr = conn.execute(
        """
        SELECT COALESCE(SUM(
            CASE WHEN pr.billing_period = 'annual' THEN pr.amount / 12 ELSE pr.amount END
        ), 0)
        FROM personal_subscription s
        JOIN personal_plan p ON p.id = s.plan_id
        JOIN personal_plan_price pr ON pr.id = s.plan_price_id
        WHERE s.status = 'past_due' AND p.is_free = FALSE AND s.billing_currency = 'USD'
        """
    ).fetchone()
    conversions = int(
        conn.execute(
            """
            SELECT COUNT(*) FROM personal_subscription_event
            WHERE event_type = 'payment_succeeded'
            """
        ).fetchone()[0]
    )
    hh_members = int(
        conn.execute(
            """
            SELECT COUNT(*) FROM household_member hm
            JOIN household h ON h.id = hm.household_id
            WHERE hm.status = 'active' AND h.status = 'active' AND hm.role = 'member'
            """
        ).fetchone()[0]
    )
    return {
        "segment": "B2C",
        "currency": "USD",
        "free_users": free_users,
        "individual_subscribers": individual,
        "duo_subscribers": duo,
        "family_subscribers": family,
        "personal_mrr": float(_quantize(mrr_rows[0])),
        "personal_past_due_mrr": float(_quantize(past_due_mrr[0])),
        "free_to_premium_conversions": conversions,
        "active_household_members": hh_members,
    }
