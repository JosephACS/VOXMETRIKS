"""Subscriptions consolidated use cases — Spec 018.

Covers: Plan catalog, PlanPrice, PlanFeature, Addon,
        Subscription lifecycle (trial, activate, change, cancel, reactivate, renew),
        SubscriptionAddon, UsageRecord, Entitlements, AccessState.

NO invoice/payment tables. Subscription is NEVER marked "paid" by itself.
past_due only via UpdateAccessState / orchestration hooks (stub callable for 019).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Optional

import duckdb

from app.core.time_util import utc_now
from app.packages.subscriptions.domain.entities import (
    Addon,
    Plan,
    PlanFeature,
    PlanPrice,
    Subscription,
    SubscriptionAccessState,
    SubscriptionAddon,
    SubscriptionChange,
    SubscriptionEntitlement,
    UsageRecord,
)
from app.packages.subscriptions.domain.errors import (
    ActiveSubscriptionExists,
    ConflictError,
    InvalidTransitionError,
    NotFoundError,
    OrgNotActiveError,
    PersistenceError,
    PlanRetiredError,
    ValidationError,
)


# ── Helpers ────────────────────────────────────────────────────────────────────


def _next_id(conn: duckdb.DuckDBPyConnection, table: str) -> int:
    row = conn.execute(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table}").fetchone()
    return int(row[0])


def _now() -> datetime:
    return utc_now()


def _audit(
    conn: duckdb.DuckDBPyConnection,
    *,
    action: str,
    target_type: str,
    target_id: str,
    actor_user_id: int,
    organization_id: Optional[int] = None,
    previous_values: Optional[dict[str, Any]] = None,
    new_values: Optional[dict[str, Any]] = None,
    reason: Optional[str] = None,
    request_id: Optional[str] = None,
    result: str = "success",
) -> None:
    from app.packages.organizations.infrastructure.repositories.audit_repository import (
        AuditRepository,
    )

    AuditRepository(conn).append(
        action=action,
        target_type=target_type,
        target_id=target_id,
        source="subscriptions.use_case",
        result=result,
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        previous_values=previous_values,
        new_values=new_values,
        reason=reason,
        request_id=request_id,
    )


# ── Plan mappers ───────────────────────────────────────────────────────────────

_PLAN_COLS = (
    "id, code, display_name, description, status, "
    "trial_days_default, sort_order, created_at, updated_at"
)


def _map_plan(row: tuple) -> Plan:
    return Plan(
        id=int(row[0]),
        code=str(row[1]),
        display_name=str(row[2]),
        description=row[3],
        status=str(row[4]),
        trial_days_default=int(row[5]) if row[5] is not None else 0,
        sort_order=int(row[6]) if row[6] is not None else 0,
        created_at=row[7],
        updated_at=row[8],
    )


_PRICE_COLS = (
    "id, plan_id, currency, billing_period, amount, status, created_at, updated_at"
)


def _map_price(row: tuple) -> PlanPrice:
    return PlanPrice(
        id=int(row[0]),
        plan_id=int(row[1]),
        currency=str(row[2]),
        billing_period=str(row[3]),
        amount=Decimal(str(row[4])),
        status=str(row[5]),
        created_at=row[6],
        updated_at=row[7],
    )


_FEATURE_COLS = (
    "id, plan_id, feature_code, limit_value, enabled, created_at, updated_at"
)


def _map_feature(row: tuple) -> PlanFeature:
    return PlanFeature(
        id=int(row[0]),
        plan_id=int(row[1]),
        feature_code=str(row[2]),
        limit_value=int(row[3]) if row[3] is not None else None,
        enabled=bool(row[4]),
        created_at=row[5],
        updated_at=row[6],
    )


_ADDON_COLS = (
    "id, code, display_name, description, feature_code, "
    "amount, currency, billing_period, status, created_at, updated_at"
)


def _map_addon(row: tuple) -> Addon:
    return Addon(
        id=int(row[0]),
        code=str(row[1]),
        display_name=str(row[2]),
        description=row[3],
        feature_code=row[4],
        amount=Decimal(str(row[5])) if row[5] is not None else None,
        currency=row[6],
        billing_period=row[7],
        status=str(row[8]),
        created_at=row[9],
        updated_at=row[10],
    )


_SUB_COLS = (
    "id, organization_id, plan_id, plan_price_id, status, billing_currency, "
    "trial_ends_at, current_period_start, current_period_end, cancel_at_period_end, "
    "canceled_at, activation_source, access_state, created_at, updated_at"
)


def _map_subscription(row: tuple) -> Subscription:
    return Subscription(
        id=int(row[0]),
        organization_id=int(row[1]),
        plan_id=int(row[2]),
        plan_price_id=int(row[3]) if row[3] is not None else None,
        status=str(row[4]),
        billing_currency=str(row[5]),
        trial_ends_at=row[6],
        current_period_start=row[7],
        current_period_end=row[8],
        cancel_at_period_end=bool(row[9]),
        canceled_at=row[10],
        activation_source=row[11],
        access_state=str(row[12]),
        created_at=row[13],
        updated_at=row[14],
    )


_CHANGE_COLS = (
    "id, subscription_id, change_type, from_plan_id, to_plan_id, "
    "from_price_id, to_price_id, scheduled_for, applied_at, status, "
    "actor_user_id, reason, created_at, updated_at"
)


def _map_change(row: tuple) -> SubscriptionChange:
    return SubscriptionChange(
        id=int(row[0]),
        subscription_id=int(row[1]),
        change_type=str(row[2]),
        from_plan_id=int(row[3]) if row[3] is not None else None,
        to_plan_id=int(row[4]) if row[4] is not None else None,
        from_price_id=int(row[5]) if row[5] is not None else None,
        to_price_id=int(row[6]) if row[6] is not None else None,
        scheduled_for=row[7],
        applied_at=row[8],
        status=str(row[9]),
        actor_user_id=int(row[10]),
        reason=row[11],
        created_at=row[12],
        updated_at=row[13],
    )


_ENTITLEMENT_COLS = (
    "id, subscription_id, feature_code, source, limit_value, enabled, created_at, updated_at"
)


def _map_entitlement(row: tuple) -> SubscriptionEntitlement:
    return SubscriptionEntitlement(
        id=int(row[0]),
        subscription_id=int(row[1]),
        feature_code=str(row[2]),
        source=str(row[3]),
        limit_value=int(row[4]) if row[4] is not None else None,
        enabled=bool(row[5]),
        created_at=row[6],
        updated_at=row[7],
    )


_ADDON_SUB_COLS = "id, subscription_id, addon_id, status, added_at, removed_at"


def _map_sub_addon(row: tuple) -> SubscriptionAddon:
    return SubscriptionAddon(
        id=int(row[0]),
        subscription_id=int(row[1]),
        addon_id=int(row[2]),
        status=str(row[3]),
        added_at=row[4],
        removed_at=row[5],
    )


_USAGE_COLS = (
    "id, subscription_id, organization_id, feature_code, quantity, "
    "period_start, period_end, idempotency_key, recorded_at"
)


def _map_usage(row: tuple) -> UsageRecord:
    return UsageRecord(
        id=int(row[0]),
        subscription_id=int(row[1]),
        organization_id=int(row[2]),
        feature_code=str(row[3]),
        quantity=Decimal(str(row[4])),
        period_start=row[5],
        period_end=row[6],
        idempotency_key=row[7],
        recorded_at=row[8],
    )


_ACCESS_COLS = "id, subscription_id, access_state, reason, updated_at"


def _map_access_state(row: tuple) -> SubscriptionAccessState:
    return SubscriptionAccessState(
        id=int(row[0]),
        subscription_id=int(row[1]),
        access_state=str(row[2]),
        reason=row[3],
        updated_at=row[4],
    )


# ── Plan Use Cases ─────────────────────────────────────────────────────────────


class PlanUseCases:
    """Catalog management: CreatePlan, ActivatePlan, ArchivePlan."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def create(
        self,
        *,
        actor_user_id: int,
        code: str,
        display_name: str,
        description: Optional[str] = None,
        trial_days_default: int = 0,
        sort_order: int = 0,
        request_id: Optional[str] = None,
    ) -> Plan:
        if not code or not code.strip():
            raise ValidationError("code is required")
        if not display_name or not display_name.strip():
            raise ValidationError("display_name is required")
        if trial_days_default < 0:
            raise ValidationError("trial_days_default must be >= 0")

        existing = self._conn.execute(
            "SELECT 1 FROM app_plan WHERE code = ?", [code.strip()]
        ).fetchone()
        if existing:
            raise ConflictError(f"Plan code={code!r} already exists")

        now = _now()
        pid = _next_id(self._conn, "app_plan")
        self._conn.execute(
            f"""
            INSERT INTO app_plan ({_PLAN_COLS})
            VALUES (?, ?, ?, ?, 'draft', ?, ?, ?, ?)
            """,
            [pid, code.strip(), display_name.strip(), description,
             trial_days_default, sort_order, now, now],
        )
        plan = self._get_or_raise(pid)
        _audit(
            self._conn,
            action="plan.created",
            target_type="plan",
            target_id=str(pid),
            actor_user_id=actor_user_id,
            new_values={"code": plan.code, "status": plan.status},
            request_id=request_id,
        )
        return plan

    def update(
        self,
        plan_id: int,
        *,
        actor_user_id: int,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        trial_days_default: Optional[int] = None,
        sort_order: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> Plan:
        existing = self._get_or_raise(plan_id)
        if existing.status == "archived":
            raise InvalidTransitionError("Cannot update an archived plan")
        now = _now()
        self._conn.execute(
            """
            UPDATE app_plan SET
                display_name = COALESCE(?, display_name),
                description = COALESCE(?, description),
                trial_days_default = COALESCE(?, trial_days_default),
                sort_order = COALESCE(?, sort_order),
                updated_at = ?
            WHERE id = ?
            """,
            [display_name, description, trial_days_default, sort_order, now, plan_id],
        )
        updated = self._get_or_raise(plan_id)
        _audit(
            self._conn,
            action="plan.updated",
            target_type="plan",
            target_id=str(plan_id),
            actor_user_id=actor_user_id,
            previous_values={"display_name": existing.display_name},
            new_values={"display_name": updated.display_name},
            request_id=request_id,
        )
        return updated

    def activate(
        self,
        plan_id: int,
        *,
        actor_user_id: int,
        request_id: Optional[str] = None,
    ) -> Plan:
        existing = self._get_or_raise(plan_id)
        if existing.status not in ("draft",):
            raise InvalidTransitionError(
                f"Cannot activate plan from status={existing.status}"
            )
        now = _now()
        self._conn.execute(
            "UPDATE app_plan SET status = 'active', updated_at = ? WHERE id = ?",
            [now, plan_id],
        )
        updated = self._get_or_raise(plan_id)
        _audit(
            self._conn,
            action="plan.activated",
            target_type="plan",
            target_id=str(plan_id),
            actor_user_id=actor_user_id,
            previous_values={"status": existing.status},
            new_values={"status": "active"},
            request_id=request_id,
        )
        return updated

    def archive(
        self,
        plan_id: int,
        *,
        actor_user_id: int,
        request_id: Optional[str] = None,
    ) -> Plan:
        existing = self._get_or_raise(plan_id)
        if existing.status == "archived":
            raise InvalidTransitionError("Plan is already archived")
        now = _now()
        self._conn.execute(
            "UPDATE app_plan SET status = 'archived', updated_at = ? WHERE id = ?",
            [now, plan_id],
        )
        updated = self._get_or_raise(plan_id)
        _audit(
            self._conn,
            action="plan.archived",
            target_type="plan",
            target_id=str(plan_id),
            actor_user_id=actor_user_id,
            previous_values={"status": existing.status},
            new_values={"status": "archived"},
            request_id=request_id,
        )
        return updated

    def get(self, plan_id: int) -> Plan:
        return self._get_or_raise(plan_id)

    def get_by_code(self, code: str) -> Plan:
        row = self._conn.execute(
            f"SELECT {_PLAN_COLS} FROM app_plan WHERE code = ?", [code]
        ).fetchone()
        if not row:
            raise NotFoundError(f"plan code={code!r}")
        return _map_plan(row)

    def list(
        self,
        *,
        status: Optional[str] = None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[Plan], int]:
        conditions: list[str] = []
        params: list[Any] = []
        if status is not None:
            conditions.append("status = ?")
            params.append(status)
        where = " AND ".join(conditions) if conditions else "1=1"

        total = int(
            self._conn.execute(
                f"SELECT COUNT(*) FROM app_plan WHERE {where}", params
            ).fetchone()[0]
        )
        rows = self._conn.execute(
            f"SELECT {_PLAN_COLS} FROM app_plan WHERE {where} "
            f"ORDER BY sort_order ASC, id ASC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
        return [_map_plan(r) for r in rows], total

    def _get_or_raise(self, plan_id: int) -> Plan:
        row = self._conn.execute(
            f"SELECT {_PLAN_COLS} FROM app_plan WHERE id = ?", [plan_id]
        ).fetchone()
        if not row:
            raise NotFoundError(f"plan id={plan_id}")
        return _map_plan(row)


# ── PlanPrice Use Cases ────────────────────────────────────────────────────────


class PlanPriceUseCases:
    """SetPlanPrice: add / retire prices for a plan."""

    VALID_PERIODS = frozenset({"monthly", "annual", "one_time"})

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def set_price(
        self,
        plan_id: int,
        *,
        actor_user_id: int,
        currency: str,
        billing_period: str,
        amount: Decimal,
        request_id: Optional[str] = None,
    ) -> PlanPrice:
        if not currency or len(currency.strip()) != 3:
            raise ValidationError("currency must be a 3-char ISO code")
        if billing_period not in self.VALID_PERIODS:
            raise ValidationError(f"billing_period must be one of {self.VALID_PERIODS}")
        if amount < 0:
            raise ValidationError("amount must be >= 0")

        currency = currency.strip().upper()
        now = _now()
        # Retire any existing active price for same plan/currency/period
        self._conn.execute(
            """
            UPDATE app_plan_price SET status = 'retired', updated_at = ?
            WHERE plan_id = ? AND currency = ? AND billing_period = ? AND status = 'active'
            """,
            [now, plan_id, currency, billing_period],
        )
        pid = _next_id(self._conn, "app_plan_price")
        self._conn.execute(
            f"""
            INSERT INTO app_plan_price ({_PRICE_COLS})
            VALUES (?, ?, ?, ?, ?, 'active', ?, ?)
            """,
            [pid, plan_id, currency, billing_period, str(amount), now, now],
        )
        price = self._get_or_raise(pid)
        _audit(
            self._conn,
            action="plan_price.set",
            target_type="plan_price",
            target_id=str(pid),
            actor_user_id=actor_user_id,
            new_values={"plan_id": plan_id, "currency": currency,
                        "billing_period": billing_period, "amount": str(amount)},
            request_id=request_id,
        )
        return price

    def list_for_plan(self, plan_id: int, *, active_only: bool = True) -> list[PlanPrice]:
        if active_only:
            rows = self._conn.execute(
                f"SELECT {_PRICE_COLS} FROM app_plan_price WHERE plan_id = ? AND status = 'active' "
                "ORDER BY billing_period ASC, currency ASC",
                [plan_id],
            ).fetchall()
        else:
            rows = self._conn.execute(
                f"SELECT {_PRICE_COLS} FROM app_plan_price WHERE plan_id = ? "
                "ORDER BY billing_period ASC, currency ASC",
                [plan_id],
            ).fetchall()
        return [_map_price(r) for r in rows]

    def get(self, price_id: int) -> PlanPrice:
        return self._get_or_raise(price_id)

    def _get_or_raise(self, price_id: int) -> PlanPrice:
        row = self._conn.execute(
            f"SELECT {_PRICE_COLS} FROM app_plan_price WHERE id = ?", [price_id]
        ).fetchone()
        if not row:
            raise NotFoundError(f"plan_price id={price_id}")
        return _map_price(row)


# ── PlanFeature Use Cases ──────────────────────────────────────────────────────


class PlanFeatureUseCases:
    """ConfigurePlanFeature: upsert feature on a plan."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def configure(
        self,
        plan_id: int,
        *,
        actor_user_id: int,
        feature_code: str,
        limit_value: Optional[int] = None,
        enabled: bool = True,
        request_id: Optional[str] = None,
    ) -> PlanFeature:
        if not feature_code or not feature_code.strip():
            raise ValidationError("feature_code is required")

        feature_code = feature_code.strip()
        now = _now()
        existing_row = self._conn.execute(
            f"SELECT {_FEATURE_COLS} FROM app_plan_feature WHERE plan_id = ? AND feature_code = ?",
            [plan_id, feature_code],
        ).fetchone()

        if existing_row:
            fid = int(existing_row[0])
            self._conn.execute(
                "UPDATE app_plan_feature SET limit_value = ?, enabled = ?, updated_at = ? WHERE id = ?",
                [limit_value, enabled, now, fid],
            )
        else:
            fid = _next_id(self._conn, "app_plan_feature")
            self._conn.execute(
                f"INSERT INTO app_plan_feature ({_FEATURE_COLS}) VALUES (?, ?, ?, ?, ?, ?, ?)",
                [fid, plan_id, feature_code, limit_value, enabled, now, now],
            )

        feature = self._get_or_raise(fid)
        _audit(
            self._conn,
            action="plan_feature.configured",
            target_type="plan_feature",
            target_id=str(fid),
            actor_user_id=actor_user_id,
            new_values={"plan_id": plan_id, "feature_code": feature_code,
                        "limit_value": limit_value, "enabled": enabled},
            request_id=request_id,
        )
        return feature

    def list_for_plan(self, plan_id: int) -> list[PlanFeature]:
        rows = self._conn.execute(
            f"SELECT {_FEATURE_COLS} FROM app_plan_feature WHERE plan_id = ? ORDER BY feature_code ASC",
            [plan_id],
        ).fetchall()
        return [_map_feature(r) for r in rows]

    def _get_or_raise(self, feature_id: int) -> PlanFeature:
        row = self._conn.execute(
            f"SELECT {_FEATURE_COLS} FROM app_plan_feature WHERE id = ?", [feature_id]
        ).fetchone()
        if not row:
            raise NotFoundError(f"plan_feature id={feature_id}")
        return _map_feature(row)


# ── Addon Use Cases ────────────────────────────────────────────────────────────


class AddonUseCases:
    """Addon catalog management."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def create(
        self,
        *,
        actor_user_id: int,
        code: str,
        display_name: str,
        description: Optional[str] = None,
        feature_code: Optional[str] = None,
        amount: Optional[Decimal] = None,
        currency: Optional[str] = None,
        billing_period: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Addon:
        if not code or not code.strip():
            raise ValidationError("code is required")
        if not display_name or not display_name.strip():
            raise ValidationError("display_name is required")

        existing = self._conn.execute(
            "SELECT 1 FROM app_addon WHERE code = ?", [code.strip()]
        ).fetchone()
        if existing:
            raise ConflictError(f"Addon code={code!r} already exists")

        now = _now()
        aid = _next_id(self._conn, "app_addon")
        self._conn.execute(
            f"""
            INSERT INTO app_addon ({_ADDON_COLS})
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
            """,
            [aid, code.strip(), display_name.strip(), description, feature_code,
             str(amount) if amount is not None else None,
             currency.strip().upper() if currency else None,
             billing_period, now, now],
        )
        addon = self._get_or_raise(aid)
        _audit(
            self._conn,
            action="addon.created",
            target_type="addon",
            target_id=str(aid),
            actor_user_id=actor_user_id,
            new_values={"code": addon.code},
            request_id=request_id,
        )
        return addon

    def get(self, addon_id: int) -> Addon:
        return self._get_or_raise(addon_id)

    def list(
        self,
        *,
        status: Optional[str] = None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[Addon], int]:
        conditions: list[str] = []
        params: list[Any] = []
        if status is not None:
            conditions.append("status = ?")
            params.append(status)
        where = " AND ".join(conditions) if conditions else "1=1"
        total = int(
            self._conn.execute(
                f"SELECT COUNT(*) FROM app_addon WHERE {where}", params
            ).fetchone()[0]
        )
        rows = self._conn.execute(
            f"SELECT {_ADDON_COLS} FROM app_addon WHERE {where} ORDER BY code ASC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
        return [_map_addon(r) for r in rows], total

    def _get_or_raise(self, addon_id: int) -> Addon:
        row = self._conn.execute(
            f"SELECT {_ADDON_COLS} FROM app_addon WHERE id = ?", [addon_id]
        ).fetchone()
        if not row:
            raise NotFoundError(f"addon id={addon_id}")
        return _map_addon(row)


# ── Subscription Use Cases ─────────────────────────────────────────────────────

_ACTIVE_STATUSES = frozenset({"trialing", "active", "past_due"})


def _assert_org_active(conn: duckdb.DuckDBPyConnection, organization_id: int) -> None:
    row = conn.execute(
        "SELECT status FROM app_organization WHERE id = ?", [organization_id]
    ).fetchone()
    if row is None:
        raise NotFoundError(f"organization id={organization_id}")
    if str(row[0]) not in ("active", "provisioning"):
        raise OrgNotActiveError(
            f"Organization status={row[0]!r}; must be active to create subscriptions"
        )


def _has_active_subscription(conn: duckdb.DuckDBPyConnection, organization_id: int) -> bool:
    row = conn.execute(
        "SELECT 1 FROM app_subscription WHERE organization_id = ? AND status IN ('trialing', 'active', 'past_due') LIMIT 1",
        [organization_id],
    ).fetchone()
    return row is not None


def _materialize_entitlements(
    conn: duckdb.DuckDBPyConnection,
    subscription_id: int,
    plan_id: int,
) -> None:
    """Delete and recreate entitlements from plan features. Idempotent."""
    conn.execute(
        "DELETE FROM app_subscription_entitlement WHERE subscription_id = ? AND source = 'plan'",
        [subscription_id],
    )
    features = conn.execute(
        f"SELECT {_FEATURE_COLS} FROM app_plan_feature WHERE plan_id = ?", [plan_id]
    ).fetchall()
    now = _now()
    for f in features:
        eid = _next_id(conn, "app_subscription_entitlement")
        feature_code = str(f[2])
        limit_value = f[3]
        enabled = bool(f[4])
        conn.execute(
            f"""
            INSERT INTO app_subscription_entitlement ({_ENTITLEMENT_COLS})
            VALUES (?, ?, ?, 'plan', ?, ?, ?, ?)
            """,
            [eid, subscription_id, feature_code, limit_value, enabled, now, now],
        )


def _upsert_access_state(
    conn: duckdb.DuckDBPyConnection,
    subscription_id: int,
    access_state: str,
    reason: Optional[str] = None,
) -> None:
    now = _now()
    existing = conn.execute(
        f"SELECT {_ACCESS_COLS} FROM app_subscription_access_state WHERE subscription_id = ?",
        [subscription_id],
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE app_subscription_access_state SET access_state = ?, reason = ?, updated_at = ? WHERE subscription_id = ?",
            [access_state, reason, now, subscription_id],
        )
    else:
        aid = _next_id(conn, "app_subscription_access_state")
        conn.execute(
            f"INSERT INTO app_subscription_access_state ({_ACCESS_COLS}) VALUES (?, ?, ?, ?, ?)",
            [aid, subscription_id, access_state, reason, now],
        )


class SubscriptionUseCases:
    """Core subscription lifecycle."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    # ── StartTrial ────────────────────────────────────────────────────────────

    def start_trial(
        self,
        *,
        actor_user_id: int,
        organization_id: int,
        plan_id: int,
        plan_price_id: Optional[int] = None,
        billing_currency: str,
        trial_days: Optional[int] = None,
        activation_source: Optional[str] = "trial",
        request_id: Optional[str] = None,
    ) -> Subscription:
        _assert_org_active(self._conn, organization_id)
        if _has_active_subscription(self._conn, organization_id):
            raise ActiveSubscriptionExists(
                f"Organization {organization_id} already has an active/trialing subscription"
            )

        plan = self._get_plan_or_raise(plan_id)
        if plan.status == "archived":
            raise PlanRetiredError(f"Plan {plan.code!r} is archived")

        effective_trial_days = trial_days if trial_days is not None else plan.trial_days_default
        now = _now()
        trial_ends_at = now + timedelta(days=effective_trial_days) if effective_trial_days > 0 else None

        sid = _next_id(self._conn, "app_subscription")
        self._conn.execute(
            f"""
            INSERT INTO app_subscription ({_SUB_COLS})
            VALUES (?, ?, ?, ?, 'trialing', ?, ?, NULL, NULL, FALSE, NULL, ?, 'full', ?, ?)
            """,
            [sid, organization_id, plan_id, plan_price_id,
             billing_currency.strip().upper(),
             trial_ends_at, activation_source or "trial", now, now],
        )
        sub = self._get_or_raise(sid)
        _materialize_entitlements(self._conn, sid, plan_id)
        _upsert_access_state(self._conn, sid, "full")
        self._append_change(
            subscription_id=sid,
            change_type="trial_start",
            to_plan_id=plan_id,
            to_price_id=plan_price_id,
            actor_user_id=actor_user_id,
            reason=f"trial_days={effective_trial_days}",
        )
        _audit(
            self._conn,
            action="subscription.trial_started",
            target_type="subscription",
            target_id=str(sid),
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            new_values={"plan_id": plan_id, "status": "trialing",
                        "trial_days": effective_trial_days},
            request_id=request_id,
        )
        return sub

    # ── CreateSubscription (direct active) ────────────────────────────────────

    def create(
        self,
        *,
        actor_user_id: int,
        organization_id: int,
        plan_id: int,
        plan_price_id: int,
        billing_currency: str,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None,
        activation_source: Optional[str] = "manual",
        request_id: Optional[str] = None,
    ) -> Subscription:
        _assert_org_active(self._conn, organization_id)
        if _has_active_subscription(self._conn, organization_id):
            raise ActiveSubscriptionExists(
                f"Organization {organization_id} already has an active subscription"
            )

        plan = self._get_plan_or_raise(plan_id)
        if plan.status == "archived":
            raise PlanRetiredError(f"Plan {plan.code!r} is archived")

        price_row = self._conn.execute(
            "SELECT id, status FROM app_plan_price WHERE id = ? AND plan_id = ?",
            [plan_price_id, plan_id],
        ).fetchone()
        if not price_row:
            raise NotFoundError(f"plan_price id={plan_price_id} for plan id={plan_id}")
        if str(price_row[1]) == "retired":
            raise PlanRetiredError(f"plan_price id={plan_price_id} is retired")

        now = _now()
        ps = period_start or now.date()
        sid = _next_id(self._conn, "app_subscription")
        self._conn.execute(
            f"""
            INSERT INTO app_subscription ({_SUB_COLS})
            VALUES (?, ?, ?, ?, 'active', ?, NULL, ?, ?, FALSE, NULL, ?, 'full', ?, ?)
            """,
            [sid, organization_id, plan_id, plan_price_id,
             billing_currency.strip().upper(),
             ps, period_end,
             activation_source or "manual", now, now],
        )
        sub = self._get_or_raise(sid)
        _materialize_entitlements(self._conn, sid, plan_id)
        _upsert_access_state(self._conn, sid, "full")
        self._append_change(
            subscription_id=sid,
            change_type="activate",
            to_plan_id=plan_id,
            to_price_id=plan_price_id,
            actor_user_id=actor_user_id,
        )
        _audit(
            self._conn,
            action="subscription.created",
            target_type="subscription",
            target_id=str(sid),
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            new_values={"plan_id": plan_id, "status": "active",
                        "billing_currency": billing_currency},
            request_id=request_id,
        )
        return sub

    # ── ActivateSubscription (trial → active) ─────────────────────────────────

    def activate(
        self,
        subscription_id: int,
        *,
        actor_user_id: int,
        plan_price_id: Optional[int] = None,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None,
        request_id: Optional[str] = None,
    ) -> Subscription:
        sub = self._get_or_raise(subscription_id)
        if sub.status != "trialing":
            raise InvalidTransitionError(
                f"Can only activate a trialing subscription (status={sub.status})"
            )
        now = _now()
        ps = period_start or now.date()
        new_price_id = plan_price_id or sub.plan_price_id
        self._conn.execute(
            """
            UPDATE app_subscription SET
                status = 'active', plan_price_id = COALESCE(?, plan_price_id),
                trial_ends_at = NULL,
                current_period_start = COALESCE(?, current_period_start),
                current_period_end = COALESCE(?, current_period_end),
                updated_at = ?
            WHERE id = ?
            """,
            [new_price_id, ps, period_end, now, subscription_id],
        )
        updated = self._get_or_raise(subscription_id)
        self._append_change(
            subscription_id=subscription_id,
            change_type="activate",
            from_plan_id=sub.plan_id,
            to_plan_id=sub.plan_id,
            from_price_id=sub.plan_price_id,
            to_price_id=new_price_id,
            actor_user_id=actor_user_id,
        )
        _audit(
            self._conn,
            action="subscription.activated",
            target_type="subscription",
            target_id=str(subscription_id),
            actor_user_id=actor_user_id,
            organization_id=sub.organization_id,
            previous_values={"status": sub.status},
            new_values={"status": "active"},
            request_id=request_id,
        )
        return updated

    # ── SchedulePlanChange ────────────────────────────────────────────────────

    def schedule_plan_change(
        self,
        subscription_id: int,
        *,
        actor_user_id: int,
        to_plan_id: int,
        to_price_id: Optional[int] = None,
        scheduled_for: Optional[date] = None,
        reason: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> SubscriptionChange:
        sub = self._get_or_raise(subscription_id)
        if sub.status not in ("active", "trialing"):
            raise InvalidTransitionError(
                f"Can only schedule change for active/trialing subscription (status={sub.status})"
            )

        new_plan = self._get_plan_or_raise(to_plan_id)
        if new_plan.status == "archived":
            raise PlanRetiredError(f"Target plan {new_plan.code!r} is archived")

        change_type = "upgrade" if to_plan_id != sub.plan_id else "downgrade"
        status = "pending" if scheduled_for is not None else "applied"
        cid = self._append_change(
            subscription_id=subscription_id,
            change_type=change_type,
            from_plan_id=sub.plan_id,
            to_plan_id=to_plan_id,
            from_price_id=sub.plan_price_id,
            to_price_id=to_price_id,
            scheduled_for=scheduled_for,
            actor_user_id=actor_user_id,
            reason=reason,
            status=status,
        )
        if status == "applied":
            now = _now()
            self._conn.execute(
                """
                UPDATE app_subscription SET
                    plan_id = ?,
                    plan_price_id = COALESCE(?, plan_price_id),
                    updated_at = ?
                WHERE id = ?
                """,
                [to_plan_id, to_price_id, now, subscription_id],
            )
            self._conn.execute(
                "UPDATE app_subscription_change SET applied_at = ? WHERE id = ?",
                [now, cid],
            )
            _materialize_entitlements(self._conn, subscription_id, to_plan_id)
        _audit(
            self._conn,
            action="subscription.change_scheduled",
            target_type="subscription_change",
            target_id=str(cid),
            actor_user_id=actor_user_id,
            organization_id=sub.organization_id,
            new_values={"from_plan_id": sub.plan_id, "to_plan_id": to_plan_id,
                        "scheduled_for": str(scheduled_for) if scheduled_for else None,
                        "status": status},
            reason=reason,
            request_id=request_id,
        )
        return self._get_change_or_raise(cid)

    # ── ApplyPlanChange ───────────────────────────────────────────────────────

    def apply_plan_change(
        self,
        change_id: int,
        *,
        actor_user_id: int,
        request_id: Optional[str] = None,
    ) -> Subscription:
        change = self._get_change_or_raise(change_id)
        if change.status != "pending":
            raise InvalidTransitionError(
                f"Change is not pending (status={change.status})"
            )
        sub = self._get_or_raise(change.subscription_id)
        now = _now()
        self._conn.execute(
            """
            UPDATE app_subscription SET
                plan_id = COALESCE(?, plan_id),
                plan_price_id = COALESCE(?, plan_price_id),
                updated_at = ?
            WHERE id = ?
            """,
            [change.to_plan_id, change.to_price_id, now, change.subscription_id],
        )
        self._conn.execute(
            "UPDATE app_subscription_change SET status = 'applied', applied_at = ?, updated_at = ? WHERE id = ?",
            [now, now, change_id],
        )
        if change.to_plan_id and change.to_plan_id != sub.plan_id:
            _materialize_entitlements(self._conn, change.subscription_id, change.to_plan_id)
        updated = self._get_or_raise(change.subscription_id)
        _audit(
            self._conn,
            action="subscription.change_applied",
            target_type="subscription",
            target_id=str(change.subscription_id),
            actor_user_id=actor_user_id,
            organization_id=updated.organization_id,
            previous_values={"plan_id": sub.plan_id},
            new_values={"plan_id": updated.plan_id},
            request_id=request_id,
        )
        return updated

    # ── CancelSubscription ────────────────────────────────────────────────────

    def cancel(
        self,
        subscription_id: int,
        *,
        actor_user_id: int,
        mode: str = "period_end",
        reason: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Subscription:
        if mode not in ("period_end", "immediate"):
            raise ValidationError("mode must be 'period_end' or 'immediate'")
        sub = self._get_or_raise(subscription_id)
        if sub.status not in ("active", "trialing", "past_due"):
            raise InvalidTransitionError(
                f"Cannot cancel subscription in status={sub.status}"
            )

        now = _now()
        if mode == "immediate":
            self._conn.execute(
                """
                UPDATE app_subscription SET
                    status = 'canceled', canceled_at = ?, cancel_at_period_end = FALSE, updated_at = ?
                WHERE id = ?
                """,
                [now, now, subscription_id],
            )
            _upsert_access_state(self._conn, subscription_id, "blocked", "subscription_canceled")
        else:
            self._conn.execute(
                "UPDATE app_subscription SET cancel_at_period_end = TRUE, updated_at = ? WHERE id = ?",
                [now, subscription_id],
            )
        self._append_change(
            subscription_id=subscription_id,
            change_type="cancel",
            from_plan_id=sub.plan_id,
            actor_user_id=actor_user_id,
            reason=reason,
        )
        updated = self._get_or_raise(subscription_id)
        _audit(
            self._conn,
            action="subscription.canceled",
            target_type="subscription",
            target_id=str(subscription_id),
            actor_user_id=actor_user_id,
            organization_id=sub.organization_id,
            previous_values={"status": sub.status},
            new_values={"status": updated.status, "mode": mode},
            reason=reason,
            request_id=request_id,
        )
        return updated

    # ── ReactivateSubscription ────────────────────────────────────────────────

    def reactivate(
        self,
        subscription_id: int,
        *,
        actor_user_id: int,
        reason: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Subscription:
        sub = self._get_or_raise(subscription_id)
        if sub.status not in ("canceled", "expired"):
            raise InvalidTransitionError(
                f"Cannot reactivate subscription in status={sub.status}"
            )
        org_id = sub.organization_id
        if _has_active_subscription(self._conn, org_id):
            raise ActiveSubscriptionExists(
                f"Organization {org_id} already has an active subscription"
            )

        now = _now()
        self._conn.execute(
            """
            UPDATE app_subscription SET
                status = 'active', cancel_at_period_end = FALSE,
                canceled_at = NULL, updated_at = ?
            WHERE id = ?
            """,
            [now, subscription_id],
        )
        _upsert_access_state(self._conn, subscription_id, "full", "reactivated")
        self._append_change(
            subscription_id=subscription_id,
            change_type="reactivate",
            from_plan_id=sub.plan_id,
            to_plan_id=sub.plan_id,
            actor_user_id=actor_user_id,
            reason=reason,
        )
        updated = self._get_or_raise(subscription_id)
        _audit(
            self._conn,
            action="subscription.reactivated",
            target_type="subscription",
            target_id=str(subscription_id),
            actor_user_id=actor_user_id,
            organization_id=sub.organization_id,
            previous_values={"status": sub.status},
            new_values={"status": "active"},
            reason=reason,
            request_id=request_id,
        )
        return updated

    # ── RenewSubscription ─────────────────────────────────────────────────────

    def renew(
        self,
        subscription_id: int,
        *,
        actor_user_id: int,
        new_period_start: date,
        new_period_end: Optional[date] = None,
        request_id: Optional[str] = None,
    ) -> Subscription:
        sub = self._get_or_raise(subscription_id)
        if sub.status not in ("active", "past_due"):
            raise InvalidTransitionError(
                f"Cannot renew subscription in status={sub.status}"
            )
        if sub.cancel_at_period_end:
            raise InvalidTransitionError(
                "Subscription is marked for cancellation at period end"
            )

        now = _now()
        self._conn.execute(
            """
            UPDATE app_subscription SET
                status = 'active', current_period_start = ?, current_period_end = ?,
                updated_at = ?
            WHERE id = ?
            """,
            [new_period_start, new_period_end, now, subscription_id],
        )
        _upsert_access_state(self._conn, subscription_id, "full", "renewed")
        self._append_change(
            subscription_id=subscription_id,
            change_type="renew",
            from_plan_id=sub.plan_id,
            to_plan_id=sub.plan_id,
            actor_user_id=actor_user_id,
        )
        updated = self._get_or_raise(subscription_id)
        _audit(
            self._conn,
            action="subscription.renewed",
            target_type="subscription",
            target_id=str(subscription_id),
            actor_user_id=actor_user_id,
            organization_id=sub.organization_id,
            previous_values={"status": sub.status,
                             "period_start": str(sub.current_period_start)},
            new_values={"status": "active",
                        "period_start": str(new_period_start)},
            request_id=request_id,
        )
        return updated

    # ── UpdateAccessState (stub callable for 019) ─────────────────────────────

    def update_access_state(
        self,
        subscription_id: int,
        *,
        actor_user_id: int,
        access_state: str,
        reason: Optional[str] = None,
        also_set_past_due: bool = False,
        request_id: Optional[str] = None,
    ) -> Subscription:
        """Update access state. also_set_past_due=True marks subscription past_due
        (only callable from orchestration hooks / Billing events, stub for 019).
        """
        if access_state not in ("full", "limited", "blocked"):
            raise ValidationError("access_state must be full|limited|blocked")
        sub = self._get_or_raise(subscription_id)

        now = _now()
        new_status = sub.status
        if also_set_past_due and sub.status == "active":
            new_status = "past_due"
            self._conn.execute(
                "UPDATE app_subscription SET status = 'past_due', updated_at = ? WHERE id = ?",
                [now, subscription_id],
            )

        self._conn.execute(
            "UPDATE app_subscription SET access_state = ?, updated_at = ? WHERE id = ?",
            [access_state, now, subscription_id],
        )
        _upsert_access_state(self._conn, subscription_id, access_state, reason)

        updated = self._get_or_raise(subscription_id)
        _audit(
            self._conn,
            action="subscription.access_state_updated",
            target_type="subscription",
            target_id=str(subscription_id),
            actor_user_id=actor_user_id,
            organization_id=sub.organization_id,
            previous_values={"access_state": sub.access_state, "status": sub.status},
            new_values={"access_state": access_state, "status": new_status},
            reason=reason,
            request_id=request_id,
        )
        return updated

    # ── Getters ───────────────────────────────────────────────────────────────

    def get(self, subscription_id: int) -> Subscription:
        return self._get_or_raise(subscription_id)

    def list(
        self,
        *,
        organization_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[Subscription], int]:
        conditions: list[str] = []
        params: list[Any] = []
        if organization_id is not None:
            conditions.append("organization_id = ?")
            params.append(organization_id)
        if status is not None:
            conditions.append("status = ?")
            params.append(status)
        where = " AND ".join(conditions) if conditions else "1=1"
        total = int(
            self._conn.execute(
                f"SELECT COUNT(*) FROM app_subscription WHERE {where}", params
            ).fetchone()[0]
        )
        rows = self._conn.execute(
            f"SELECT {_SUB_COLS} FROM app_subscription WHERE {where} "
            f"ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
        return [_map_subscription(r) for r in rows], total

    def get_access_state(self, subscription_id: int) -> SubscriptionAccessState:
        row = self._conn.execute(
            f"SELECT {_ACCESS_COLS} FROM app_subscription_access_state WHERE subscription_id = ?",
            [subscription_id],
        ).fetchone()
        if not row:
            return SubscriptionAccessState(
                id=0, subscription_id=subscription_id,
                access_state="full", reason=None, updated_at=_now(),
            )
        return _map_access_state(row)

    def list_changes(
        self,
        subscription_id: int,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[SubscriptionChange], int]:
        total = int(
            self._conn.execute(
                "SELECT COUNT(*) FROM app_subscription_change WHERE subscription_id = ?",
                [subscription_id],
            ).fetchone()[0]
        )
        rows = self._conn.execute(
            f"SELECT {_CHANGE_COLS} FROM app_subscription_change WHERE subscription_id = ? "
            "ORDER BY created_at DESC LIMIT ? OFFSET ?",
            [subscription_id, limit, offset],
        ).fetchall()
        return [_map_change(r) for r in rows], total

    # ── Private helpers ───────────────────────────────────────────────────────

    def _get_or_raise(self, subscription_id: int) -> Subscription:
        row = self._conn.execute(
            f"SELECT {_SUB_COLS} FROM app_subscription WHERE id = ?", [subscription_id]
        ).fetchone()
        if not row:
            raise NotFoundError(f"subscription id={subscription_id}")
        return _map_subscription(row)

    def _get_plan_or_raise(self, plan_id: int) -> Plan:
        row = self._conn.execute(
            f"SELECT {_PLAN_COLS} FROM app_plan WHERE id = ?", [plan_id]
        ).fetchone()
        if not row:
            raise NotFoundError(f"plan id={plan_id}")
        return _map_plan(row)

    def _get_change_or_raise(self, change_id: int) -> SubscriptionChange:
        row = self._conn.execute(
            f"SELECT {_CHANGE_COLS} FROM app_subscription_change WHERE id = ?",
            [change_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"subscription_change id={change_id}")
        return _map_change(row)

    def _append_change(
        self,
        *,
        subscription_id: int,
        change_type: str,
        from_plan_id: Optional[int] = None,
        to_plan_id: Optional[int] = None,
        from_price_id: Optional[int] = None,
        to_price_id: Optional[int] = None,
        scheduled_for: Optional[date] = None,
        actor_user_id: int,
        reason: Optional[str] = None,
        status: str = "applied",
    ) -> int:
        now = _now()
        cid = _next_id(self._conn, "app_subscription_change")
        self._conn.execute(
            f"""
            INSERT INTO app_subscription_change ({_CHANGE_COLS})
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [cid, subscription_id, change_type,
             from_plan_id, to_plan_id, from_price_id, to_price_id,
             scheduled_for, now, status, actor_user_id, reason, now, now],
        )
        return cid


# ── SubscriptionAddon Use Cases ────────────────────────────────────────────────


class SubscriptionAddonUseCases:
    """AddSubscriptionAddon, RemoveSubscriptionAddon."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def add(
        self,
        subscription_id: int,
        *,
        actor_user_id: int,
        addon_id: int,
        request_id: Optional[str] = None,
    ) -> SubscriptionAddon:
        sub = self._get_sub_or_raise(subscription_id)
        if sub.status not in ("active", "trialing"):
            raise InvalidTransitionError(
                f"Cannot add addon to subscription in status={sub.status}"
            )
        addon_row = self._conn.execute(
            f"SELECT {_ADDON_COLS} FROM app_addon WHERE id = ? AND status = 'active'",
            [addon_id],
        ).fetchone()
        if not addon_row:
            raise NotFoundError(f"active addon id={addon_id}")

        existing = self._conn.execute(
            "SELECT id FROM app_subscription_addon WHERE subscription_id = ? AND addon_id = ? AND status = 'active'",
            [subscription_id, addon_id],
        ).fetchone()
        if existing:
            raise ConflictError(f"Addon {addon_id} already active on subscription {subscription_id}")

        now = _now()
        said = _next_id(self._conn, "app_subscription_addon")
        self._conn.execute(
            f"INSERT INTO app_subscription_addon ({_ADDON_SUB_COLS}) VALUES (?, ?, ?, 'active', ?, NULL)",
            [said, subscription_id, addon_id, now],
        )
        addon = _map_addon(addon_row)
        if addon.feature_code:
            self._upsert_addon_entitlement(subscription_id, addon, now)
        _audit(
            self._conn,
            action="subscription.addon_added",
            target_type="subscription_addon",
            target_id=str(said),
            actor_user_id=actor_user_id,
            organization_id=sub.organization_id,
            new_values={"addon_id": addon_id, "feature_code": addon.feature_code},
            request_id=request_id,
        )
        row = self._conn.execute(
            f"SELECT {_ADDON_SUB_COLS} FROM app_subscription_addon WHERE id = ?", [said]
        ).fetchone()
        return _map_sub_addon(row)

    def remove(
        self,
        subscription_id: int,
        *,
        actor_user_id: int,
        addon_id: int,
        request_id: Optional[str] = None,
    ) -> SubscriptionAddon:
        sub = self._get_sub_or_raise(subscription_id)
        row = self._conn.execute(
            "SELECT id FROM app_subscription_addon WHERE subscription_id = ? AND addon_id = ? AND status = 'active'",
            [subscription_id, addon_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"active addon {addon_id} on subscription {subscription_id}")

        said = int(row[0])
        now = _now()
        self._conn.execute(
            "UPDATE app_subscription_addon SET status = 'removed', removed_at = ? WHERE id = ?",
            [now, said],
        )
        addon_row = self._conn.execute(
            f"SELECT {_ADDON_COLS} FROM app_addon WHERE id = ?", [addon_id]
        ).fetchone()
        if addon_row:
            addon = _map_addon(addon_row)
            if addon.feature_code:
                self._conn.execute(
                    "DELETE FROM app_subscription_entitlement WHERE subscription_id = ? AND feature_code = ? AND source = 'addon'",
                    [subscription_id, addon.feature_code],
                )
        _audit(
            self._conn,
            action="subscription.addon_removed",
            target_type="subscription_addon",
            target_id=str(said),
            actor_user_id=actor_user_id,
            organization_id=sub.organization_id,
            new_values={"addon_id": addon_id, "status": "removed"},
            request_id=request_id,
        )
        result_row = self._conn.execute(
            f"SELECT {_ADDON_SUB_COLS} FROM app_subscription_addon WHERE id = ?", [said]
        ).fetchone()
        return _map_sub_addon(result_row)

    def list(self, subscription_id: int) -> list[SubscriptionAddon]:
        rows = self._conn.execute(
            f"SELECT {_ADDON_SUB_COLS} FROM app_subscription_addon WHERE subscription_id = ? ORDER BY added_at DESC",
            [subscription_id],
        ).fetchall()
        return [_map_sub_addon(r) for r in rows]

    def _upsert_addon_entitlement(
        self,
        subscription_id: int,
        addon: Addon,
        now: datetime,
    ) -> None:
        existing = self._conn.execute(
            "SELECT id FROM app_subscription_entitlement WHERE subscription_id = ? AND feature_code = ? AND source = 'addon'",
            [subscription_id, addon.feature_code],
        ).fetchone()
        if existing:
            self._conn.execute(
                "UPDATE app_subscription_entitlement SET enabled = TRUE, updated_at = ? WHERE id = ?",
                [now, int(existing[0])],
            )
        else:
            eid = _next_id(self._conn, "app_subscription_entitlement")
            self._conn.execute(
                f"INSERT INTO app_subscription_entitlement ({_ENTITLEMENT_COLS}) VALUES (?, ?, ?, 'addon', NULL, TRUE, ?, ?)",
                [eid, subscription_id, addon.feature_code, now, now],
            )

    def _get_sub_or_raise(self, subscription_id: int) -> Subscription:
        row = self._conn.execute(
            f"SELECT {_SUB_COLS} FROM app_subscription WHERE id = ?", [subscription_id]
        ).fetchone()
        if not row:
            raise NotFoundError(f"subscription id={subscription_id}")
        return _map_subscription(row)


# ── Usage & Entitlement Use Cases ──────────────────────────────────────────────


class UsageUseCases:
    """RecordUsage, EvaluateEntitlements."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def record(
        self,
        *,
        actor_user_id: int,
        subscription_id: int,
        organization_id: int,
        feature_code: str,
        quantity: Decimal,
        period_start: date,
        period_end: date,
        idempotency_key: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> UsageRecord:
        if quantity <= 0:
            raise ValidationError("quantity must be > 0")
        if not feature_code or not feature_code.strip():
            raise ValidationError("feature_code is required")

        if idempotency_key:
            existing = self._conn.execute(
                f"SELECT {_USAGE_COLS} FROM app_usage_record WHERE idempotency_key = ?",
                [idempotency_key],
            ).fetchone()
            if existing:
                return _map_usage(existing)

        now = _now()
        uid = _next_id(self._conn, "app_usage_record")
        self._conn.execute(
            f"""
            INSERT INTO app_usage_record ({_USAGE_COLS})
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [uid, subscription_id, organization_id, feature_code.strip(),
             str(quantity), period_start, period_end, idempotency_key, now],
        )
        record = self._get_or_raise(uid)
        _audit(
            self._conn,
            action="usage.recorded",
            target_type="usage_record",
            target_id=str(uid),
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            new_values={"feature_code": feature_code, "quantity": str(quantity)},
            request_id=request_id,
        )
        return record

    def list(
        self,
        subscription_id: int,
        *,
        feature_code: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[UsageRecord], int]:
        conditions = ["subscription_id = ?"]
        params: list[Any] = [subscription_id]
        if feature_code:
            conditions.append("feature_code = ?")
            params.append(feature_code)
        where = " AND ".join(conditions)
        total = int(
            self._conn.execute(
                f"SELECT COUNT(*) FROM app_usage_record WHERE {where}", params
            ).fetchone()[0]
        )
        rows = self._conn.execute(
            f"SELECT {_USAGE_COLS} FROM app_usage_record WHERE {where} "
            "ORDER BY recorded_at DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
        return [_map_usage(r) for r in rows], total

    def evaluate_entitlements(
        self,
        subscription_id: int,
    ) -> list[SubscriptionEntitlement]:
        """Return all active entitlements for a subscription."""
        rows = self._conn.execute(
            f"SELECT {_ENTITLEMENT_COLS} FROM app_subscription_entitlement "
            "WHERE subscription_id = ? AND enabled = TRUE ORDER BY feature_code ASC",
            [subscription_id],
        ).fetchall()
        return [_map_entitlement(r) for r in rows]

    def check_feature(
        self,
        subscription_id: int,
        feature_code: str,
    ) -> tuple[bool, Optional[int]]:
        """Check if feature is enabled and return (enabled, limit_value).

        Returns (False, None) if not entitled.
        """
        row = self._conn.execute(
            "SELECT enabled, limit_value FROM app_subscription_entitlement "
            "WHERE subscription_id = ? AND feature_code = ? AND enabled = TRUE LIMIT 1",
            [subscription_id, feature_code],
        ).fetchone()
        if not row:
            return False, None
        return bool(row[0]), int(row[1]) if row[1] is not None else None

    def _get_or_raise(self, usage_id: int) -> UsageRecord:
        row = self._conn.execute(
            f"SELECT {_USAGE_COLS} FROM app_usage_record WHERE id = ?", [usage_id]
        ).fetchone()
        if not row:
            raise NotFoundError(f"usage_record id={usage_id}")
        return _map_usage(row)
