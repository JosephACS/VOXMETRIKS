"""Billing dunning / mora use cases — academic mock/manual only.

Flow:
  payment attempt failed → invoice past_due → dunning open (grace)
  → retry scheduled → access limited → grace expires → access blocked
  → mock payment settled + allocation → recovered → access full
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

import duckdb

from app.core.time_util import utc_now
from app.packages.billing.domain.errors import InvalidTransitionError, NotFoundError, ValidationError


def _now():
    return utc_now()


def _next_id(conn: duckdb.DuckDBPyConnection, table: str) -> int:
    return int(conn.execute(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table}").fetchone()[0])


def _audit(conn, *, action: str, target_type: str, target_id: str, actor_user_id=None,
           organization_id=None, previous_values=None, new_values=None, request_id=None) -> None:
    try:
        from app.packages.billing.application.use_cases import _audit as billing_audit
        billing_audit(
            conn, action=action, target_type=target_type, target_id=target_id,
            actor_user_id=actor_user_id, organization_id=organization_id,
            previous_values=previous_values, new_values=new_values, request_id=request_id,
        )
    except Exception:
        pass


@dataclass
class BillingDunning:
    id: int
    organization_id: int
    invoice_id: int
    subscription_id: Optional[int]
    status: str
    retry_count: int
    next_retry_at: Optional[object]
    grace_until: Optional[object]
    last_error_sanitized: Optional[str]
    last_attempt_id: Optional[int]
    retry_lock_token: Optional[str]
    created_at: object
    updated_at: object


_COLS = (
    "id, organization_id, invoice_id, subscription_id, status, retry_count, "
    "next_retry_at, grace_until, last_error_sanitized, last_attempt_id, "
    "retry_lock_token, created_at, updated_at"
)


def _map(row: tuple) -> BillingDunning:
    return BillingDunning(*row)


class DunningUseCases:
    """Minimal academic dunning engine (no real payment gateway)."""

    GRACE_DAYS = 7
    RETRY_HOURS = 24

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def _get(self, dunning_id: int, organization_id: int) -> BillingDunning:
        row = self._conn.execute(
            f"SELECT {_COLS} FROM app_billing_dunning WHERE id = ? AND organization_id = ?",
            [dunning_id, organization_id],
        ).fetchone()
        if not row:
            raise NotFoundError("Dunning record not found")
        return _map(row)

    def get_by_invoice(self, organization_id: int, invoice_id: int) -> Optional[BillingDunning]:
        row = self._conn.execute(
            f"SELECT {_COLS} FROM app_billing_dunning WHERE organization_id = ? AND invoice_id = ? "
            "ORDER BY id DESC LIMIT 1",
            [organization_id, invoice_id],
        ).fetchone()
        return _map(row) if row else None

    def list(self, organization_id: int, *, status: Optional[str] = None) -> list[BillingDunning]:
        if status:
            rows = self._conn.execute(
                f"SELECT {_COLS} FROM app_billing_dunning WHERE organization_id = ? AND status = ? ORDER BY id DESC",
                [organization_id, status],
            ).fetchall()
        else:
            rows = self._conn.execute(
                f"SELECT {_COLS} FROM app_billing_dunning WHERE organization_id = ? ORDER BY id DESC",
                [organization_id],
            ).fetchall()
        return [_map(r) for r in rows]

    def open_from_failed_attempt(
        self,
        *,
        organization_id: int,
        invoice_id: int,
        attempt_id: int,
        actor_user_id: int,
        failure_reason: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> BillingDunning:
        """Create/update dunning after a failed mock attempt; mark invoice past_due."""
        from app.packages.billing.application.use_cases import InvoiceUseCases

        inv = InvoiceUseCases(self._conn)._get_or_raise_for_org(invoice_id, organization_id)
        existing = self.get_by_invoice(organization_id, invoice_id)
        if existing and existing.status in ("recovered", "canceled"):
            existing = None
        if existing and existing.status == "retry_in_progress":
            raise InvalidTransitionError("Dunning retry already in progress")

        now = _now()
        grace_until = now + timedelta(days=self.GRACE_DAYS)
        next_retry = now + timedelta(hours=self.RETRY_HOURS)
        sanitized = (failure_reason or "payment_failed")[:200]

        if inv.status not in ("past_due", "paid", "void", "credited"):
            try:
                InvoiceUseCases(self._conn).mark_past_due(
                    invoice_id,
                    actor_user_id=actor_user_id,
                    organization_id=organization_id,
                    request_id=request_id,
                )
            except Exception:
                # invoice may already be past_due from concurrent path
                pass

        if existing:
            self._conn.execute(
                """
                UPDATE app_billing_dunning SET
                    status='grace', last_error_sanitized=?, last_attempt_id=?,
                    next_retry_at=?, grace_until=COALESCE(grace_until, ?),
                    updated_at=?
                WHERE id=?
                """,
                [sanitized, attempt_id, next_retry, grace_until, now, existing.id],
            )
            d = self._get(existing.id, organization_id)
        else:
            did = _next_id(self._conn, "app_billing_dunning")
            self._conn.execute(
                f"""
                INSERT INTO app_billing_dunning ({_COLS})
                VALUES (?, ?, ?, ?, 'grace', 0, ?, ?, ?, ?, NULL, ?, ?)
                """,
                [
                    did, organization_id, invoice_id, inv.subscription_id,
                    next_retry, grace_until, sanitized, attempt_id, now, now,
                ],
            )
            d = self._get(did, organization_id)

        _audit(
            self._conn, action="dunning.opened", target_type="billing_dunning",
            target_id=str(d.id), actor_user_id=actor_user_id, organization_id=organization_id,
            new_values={"status": d.status, "invoice_id": invoice_id},
            request_id=request_id,
        )
        return d

    def begin_retry(
        self,
        dunning_id: int,
        *,
        organization_id: int,
        actor_user_id: int,
        request_id: Optional[str] = None,
    ) -> BillingDunning:
        """Acquire exclusive retry lock (prevents concurrent double retry)."""
        d = self._get(dunning_id, organization_id)
        if d.status in ("recovered", "canceled", "blocked"):
            raise InvalidTransitionError(f"Cannot retry dunning in status={d.status}")
        if d.status == "retry_in_progress" and d.retry_lock_token:
            raise InvalidTransitionError("Concurrent retry already in progress")

        now = _now()
        token = uuid.uuid4().hex
        self._conn.execute(
            """
            UPDATE app_billing_dunning SET
                status='retry_in_progress', retry_lock_token=?,
                retry_count=retry_count+1, updated_at=?
            WHERE id=? AND organization_id=? AND status != 'retry_in_progress'
            """,
            [token, now, dunning_id, organization_id],
        )
        updated = self._get(dunning_id, organization_id)
        if updated.retry_lock_token != token:
            raise InvalidTransitionError("Concurrent retry already in progress")
        _audit(
            self._conn, action="dunning.retry_started", target_type="billing_dunning",
            target_id=str(dunning_id), actor_user_id=actor_user_id, organization_id=organization_id,
            new_values={"retry_count": updated.retry_count},
            request_id=request_id,
        )
        return updated

    def complete_retry_started(
        self,
        dunning_id: int,
        *,
        organization_id: int,
        attempt_id: int,
        request_id: Optional[str] = None,
    ) -> BillingDunning:
        """Release retry lock after a new attempt was created (awaiting confirm/fail)."""
        d = self._get(dunning_id, organization_id)
        now = _now()
        status = "grace"
        if d.grace_until and now >= d.grace_until:
            status = "limited"
        self._conn.execute(
            """
            UPDATE app_billing_dunning SET
                status=?, retry_lock_token=NULL, last_attempt_id=?, updated_at=?
            WHERE id=?
            """,
            [status, attempt_id, now, dunning_id],
        )
        return self._get(dunning_id, organization_id)

    def complete_retry_failed(
        self,
        dunning_id: int,
        *,
        organization_id: int,
        attempt_id: int,
        failure_reason: Optional[str] = None,
        actor_user_id: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> BillingDunning:
        d = self._get(dunning_id, organization_id)
        now = _now()
        next_retry = now + timedelta(hours=self.RETRY_HOURS)
        sanitized = (failure_reason or "retry_failed")[:200]
        status = "grace"
        if d.grace_until and now >= d.grace_until:
            status = "limited"
        self._conn.execute(
            """
            UPDATE app_billing_dunning SET
                status=?, retry_lock_token=NULL, last_attempt_id=?,
                last_error_sanitized=?, next_retry_at=?, updated_at=?
            WHERE id=?
            """,
            [status, attempt_id, sanitized, next_retry, now, dunning_id],
        )
        return self._get(dunning_id, organization_id)

    def mark_recovered(
        self,
        *,
        organization_id: int,
        invoice_id: int,
        actor_user_id: int,
        request_id: Optional[str] = None,
    ) -> Optional[BillingDunning]:
        d = self.get_by_invoice(organization_id, invoice_id)
        if not d or d.status == "recovered":
            return d
        now = _now()
        self._conn.execute(
            """
            UPDATE app_billing_dunning SET
                status='recovered', retry_lock_token=NULL, updated_at=?
            WHERE id=?
            """,
            [now, d.id],
        )
        updated = self._get(d.id, organization_id)
        _audit(
            self._conn, action="dunning.recovered", target_type="billing_dunning",
            target_id=str(d.id), actor_user_id=actor_user_id, organization_id=organization_id,
            request_id=request_id,
        )
        return updated

    def apply_grace_expiry(
        self,
        dunning_id: int,
        *,
        organization_id: int,
        actor_user_id: int,
        request_id: Optional[str] = None,
    ) -> BillingDunning:
        """If grace elapsed → block access (academic manual/job trigger)."""
        d = self._get(dunning_id, organization_id)
        now = _now()
        if d.status in ("recovered", "canceled", "blocked"):
            return d
        if d.grace_until and now < d.grace_until:
            raise ValidationError("Grace period has not elapsed")

        self._conn.execute(
            "UPDATE app_billing_dunning SET status='blocked', retry_lock_token=NULL, updated_at=? WHERE id=?",
            [now, dunning_id],
        )
        if d.subscription_id:
            from app.packages.subscriptions.application.use_cases import SubscriptionUseCases
            try:
                SubscriptionUseCases(self._conn).update_access_state(
                    d.subscription_id,
                    actor_user_id=actor_user_id,
                    access_state="blocked",
                    reason="dunning_grace_expired",
                    request_id=request_id,
                )
            except Exception:
                pass
        _audit(
            self._conn, action="dunning.blocked", target_type="billing_dunning",
            target_id=str(dunning_id), actor_user_id=actor_user_id, organization_id=organization_id,
            request_id=request_id,
        )
        return self._get(dunning_id, organization_id)
