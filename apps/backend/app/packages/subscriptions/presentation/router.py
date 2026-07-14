"""Subscriptions HTTP routers — Spec 018.

plans_router:        /plans   (platform catalog; platform RBAC)
subscriptions_router: /subscriptions  (org-scoped; org RBAC via X-Organization-Id)
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

import duckdb
from fastapi import APIRouter, Depends, Query

from app.core.database import get_write_conn
from app.packages.subscriptions.application.use_cases import (
    AddonUseCases,
    PlanFeatureUseCases,
    PlanPriceUseCases,
    PlanUseCases,
    SubscriptionAddonUseCases,
    SubscriptionUseCases,
    UsageUseCases,
)
from app.packages.subscriptions.presentation.dependencies import (
    get_authenticated_user,
    require_org_permission,
    require_platform_permission,
)
from app.packages.subscriptions.presentation.error_mapping import raise_sub_http
from app.packages.subscriptions.presentation.schemas import (
    AccessStateOut,
    AddonCreateRequest,
    AddonOut,
    ApplyChangeRequest,
    EntitlementOut,
    PaginatedAddons,
    PaginatedPlans,
    PaginatedSubscriptionChanges,
    PaginatedSubscriptions,
    PaginatedUsage,
    PlanCreateRequest,
    PlanFeatureConfigRequest,
    PlanFeatureOut,
    PlanOut,
    PlanPriceOut,
    PlanPriceSetRequest,
    PlanUpdateRequest,
    RenewRequest,
    SubscriptionActivateRequest,
    SubscriptionAddonAddRequest,
    SubscriptionAddonOut,
    SubscriptionCancelRequest,
    SubscriptionChangeOut,
    SubscriptionChangeRequest,
    SubscriptionCreateRequest,
    SubscriptionOut,
    SubscriptionReactivateRequest,
    TrialStartRequest,
    UpdateAccessStateRequest,
    UsageRecordOut,
    UsageRecordRequest,
)

plans_router = APIRouter(prefix="/plans", tags=["Plans"])
subscriptions_router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


def _page_bounds(page: int, limit: int, max_limit: int = 100) -> tuple[int, int, int]:
    page = max(1, page)
    lim = min(max(1, limit), max_limit)
    offset = (page - 1) * lim
    return page, lim, offset


def _plan_out(p) -> PlanOut:
    return PlanOut(
        id=p.id, code=p.code, display_name=p.display_name, description=p.description,
        status=p.status, trial_days_default=p.trial_days_default,
        sort_order=p.sort_order, created_at=p.created_at, updated_at=p.updated_at,
    )


def _price_out(p) -> PlanPriceOut:
    return PlanPriceOut(
        id=p.id, plan_id=p.plan_id, currency=p.currency,
        billing_period=p.billing_period, amount=p.amount,
        status=p.status, created_at=p.created_at, updated_at=p.updated_at,
    )


def _feature_out(f) -> PlanFeatureOut:
    return PlanFeatureOut(
        id=f.id, plan_id=f.plan_id, feature_code=f.feature_code,
        limit_value=f.limit_value, enabled=f.enabled,
        created_at=f.created_at, updated_at=f.updated_at,
    )


def _addon_out(a) -> AddonOut:
    return AddonOut(
        id=a.id, code=a.code, display_name=a.display_name, description=a.description,
        feature_code=a.feature_code, amount=a.amount, currency=a.currency,
        billing_period=a.billing_period, status=a.status,
        created_at=a.created_at, updated_at=a.updated_at,
    )


def _sub_out(s) -> SubscriptionOut:
    return SubscriptionOut(
        id=s.id, organization_id=s.organization_id, plan_id=s.plan_id,
        plan_price_id=s.plan_price_id, status=s.status,
        billing_currency=s.billing_currency, trial_ends_at=s.trial_ends_at,
        current_period_start=s.current_period_start,
        current_period_end=s.current_period_end,
        cancel_at_period_end=s.cancel_at_period_end, canceled_at=s.canceled_at,
        activation_source=s.activation_source, access_state=s.access_state,
        created_at=s.created_at, updated_at=s.updated_at,
    )


def _change_out(c) -> SubscriptionChangeOut:
    return SubscriptionChangeOut(
        id=c.id, subscription_id=c.subscription_id, change_type=c.change_type,
        from_plan_id=c.from_plan_id, to_plan_id=c.to_plan_id,
        from_price_id=c.from_price_id, to_price_id=c.to_price_id,
        scheduled_for=c.scheduled_for, applied_at=c.applied_at,
        status=c.status, actor_user_id=c.actor_user_id,
        reason=c.reason, created_at=c.created_at, updated_at=c.updated_at,
    )


def _entitlement_out(e, current_usage: int | None = None, remaining: int | None = None) -> EntitlementOut:
    return EntitlementOut(
        id=e.id, subscription_id=e.subscription_id, feature_code=e.feature_code,
        source=e.source, limit_value=e.limit_value, enabled=e.enabled,
        created_at=e.created_at, updated_at=e.updated_at,
        current_usage=current_usage, remaining=remaining,
    )


def _sub_addon_out(a) -> SubscriptionAddonOut:
    return SubscriptionAddonOut(
        id=a.id, subscription_id=a.subscription_id, addon_id=a.addon_id,
        status=a.status, added_at=a.added_at, removed_at=a.removed_at,
    )


def _usage_out(u) -> UsageRecordOut:
    return UsageRecordOut(
        id=u.id, subscription_id=u.subscription_id, organization_id=u.organization_id,
        feature_code=u.feature_code, quantity=u.quantity,
        period_start=u.period_start, period_end=u.period_end,
        idempotency_key=u.idempotency_key, recorded_at=u.recorded_at,
    )


# ── Plan catalog endpoints ─────────────────────────────────────────────────────

@plans_router.get("", response_model=PaginatedPlans)
def list_plans(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    status: Optional[str] = Query(None),
    actor: dict = Depends(get_authenticated_user),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    """List plans. Authenticated users see active plans; platform_admin sees all."""
    try:
        page, lim, offset = _page_bounds(page, limit)
        effective_status = status
        if effective_status is None:
            from app.packages.platform_rbac.infrastructure import repository as rbac_repo
            if not rbac_repo.has_permission(conn, actor["user_id"], "plan.view"):
                effective_status = "active"
        items, total = PlanUseCases(conn).list(status=effective_status, limit=lim, offset=offset)
        return PaginatedPlans(items=[_plan_out(p) for p in items], page=page, limit=lim, total=total)
    except Exception as exc:
        raise_sub_http(exc)


@plans_router.get("/{plan_id}", response_model=PlanOut)
def get_plan(
    plan_id: int,
    actor: dict = Depends(get_authenticated_user),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        return _plan_out(PlanUseCases(conn).get(plan_id))
    except Exception as exc:
        raise_sub_http(exc)


@plans_router.post("", status_code=201, response_model=PlanOut)
def create_plan(
    body: PlanCreateRequest,
    actor: dict = Depends(require_platform_permission("plan.create")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        p = PlanUseCases(conn).create(
            actor_user_id=actor["user_id"],
            code=body.code,
            display_name=body.display_name,
            description=body.description,
            trial_days_default=body.trial_days_default,
            sort_order=body.sort_order,
            request_id=actor["request_id"],
        )
        return _plan_out(p)
    except Exception as exc:
        raise_sub_http(exc)


@plans_router.patch("/{plan_id}", response_model=PlanOut)
def update_plan(
    plan_id: int,
    body: PlanUpdateRequest,
    actor: dict = Depends(require_platform_permission("plan.create")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        p = PlanUseCases(conn).update(
            plan_id,
            actor_user_id=actor["user_id"],
            display_name=body.display_name,
            description=body.description,
            trial_days_default=body.trial_days_default,
            sort_order=body.sort_order,
            request_id=actor["request_id"],
        )
        return _plan_out(p)
    except Exception as exc:
        raise_sub_http(exc)


@plans_router.post("/{plan_id}/activate", response_model=PlanOut)
def activate_plan(
    plan_id: int,
    actor: dict = Depends(require_platform_permission("plan.activate")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        p = PlanUseCases(conn).activate(
            plan_id,
            actor_user_id=actor["user_id"],
            request_id=actor["request_id"],
        )
        return _plan_out(p)
    except Exception as exc:
        raise_sub_http(exc)


@plans_router.post("/{plan_id}/archive", response_model=PlanOut)
def archive_plan(
    plan_id: int,
    actor: dict = Depends(require_platform_permission("plan.archive")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        p = PlanUseCases(conn).archive(
            plan_id,
            actor_user_id=actor["user_id"],
            request_id=actor["request_id"],
        )
        return _plan_out(p)
    except Exception as exc:
        raise_sub_http(exc)


@plans_router.get("/{plan_id}/prices", response_model=list[PlanPriceOut])
def list_plan_prices(
    plan_id: int,
    active_only: bool = Query(default=True),
    actor: dict = Depends(get_authenticated_user),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        prices = PlanPriceUseCases(conn).list_for_plan(plan_id, active_only=active_only)
        return [_price_out(p) for p in prices]
    except Exception as exc:
        raise_sub_http(exc)


@plans_router.post("/{plan_id}/prices", status_code=201, response_model=PlanPriceOut)
def set_plan_price(
    plan_id: int,
    body: PlanPriceSetRequest,
    actor: dict = Depends(require_platform_permission("plan_price.manage")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        price = PlanPriceUseCases(conn).set_price(
            plan_id,
            actor_user_id=actor["user_id"],
            currency=body.currency,
            billing_period=body.billing_period,
            amount=body.amount,
            request_id=actor["request_id"],
        )
        return _price_out(price)
    except Exception as exc:
        raise_sub_http(exc)


@plans_router.get("/{plan_id}/features", response_model=list[PlanFeatureOut])
def list_plan_features(
    plan_id: int,
    actor: dict = Depends(get_authenticated_user),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        features = PlanFeatureUseCases(conn).list_for_plan(plan_id)
        return [_feature_out(f) for f in features]
    except Exception as exc:
        raise_sub_http(exc)


@plans_router.post("/{plan_id}/features", status_code=201, response_model=PlanFeatureOut)
def configure_plan_feature(
    plan_id: int,
    body: PlanFeatureConfigRequest,
    actor: dict = Depends(require_platform_permission("plan_feature.manage")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        feature = PlanFeatureUseCases(conn).configure(
            plan_id,
            actor_user_id=actor["user_id"],
            feature_code=body.feature_code,
            limit_value=body.limit_value,
            enabled=body.enabled,
            request_id=actor["request_id"],
        )
        return _feature_out(feature)
    except Exception as exc:
        raise_sub_http(exc)


# ── Addon endpoints (under /plans router for simplicity) ──────────────────────

addons_router = APIRouter(prefix="/addons", tags=["Addons"])


@addons_router.get("", response_model=PaginatedAddons)
def list_addons(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    status: Optional[str] = Query(None),
    actor: dict = Depends(get_authenticated_user),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        page, lim, offset = _page_bounds(page, limit)
        items, total = AddonUseCases(conn).list(status=status, limit=lim, offset=offset)
        return PaginatedAddons(items=[_addon_out(a) for a in items], page=page, limit=lim, total=total)
    except Exception as exc:
        raise_sub_http(exc)


@addons_router.post("", status_code=201, response_model=AddonOut)
def create_addon(
    body: AddonCreateRequest,
    actor: dict = Depends(require_platform_permission("addon.manage")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        a = AddonUseCases(conn).create(
            actor_user_id=actor["user_id"],
            code=body.code,
            display_name=body.display_name,
            description=body.description,
            feature_code=body.feature_code,
            amount=body.amount,
            currency=body.currency,
            billing_period=body.billing_period,
            request_id=actor["request_id"],
        )
        return _addon_out(a)
    except Exception as exc:
        raise_sub_http(exc)


@addons_router.get("/{addon_id}", response_model=AddonOut)
def get_addon(
    addon_id: int,
    actor: dict = Depends(get_authenticated_user),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        return _addon_out(AddonUseCases(conn).get(addon_id))
    except Exception as exc:
        raise_sub_http(exc)


# ── Subscription endpoints ─────────────────────────────────────────────────────

@subscriptions_router.get("", response_model=PaginatedSubscriptions)
def list_subscriptions(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    status: Optional[str] = Query(None),
    actor: dict = Depends(require_org_permission("subscription.view")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        page, lim, offset = _page_bounds(page, limit)
        items, total = SubscriptionUseCases(conn).list(
            organization_id=actor["organization_id"], status=status,
            limit=lim, offset=offset,
        )
        return PaginatedSubscriptions(
            items=[_sub_out(s) for s in items], page=page, limit=lim, total=total
        )
    except Exception as exc:
        raise_sub_http(exc)


@subscriptions_router.post("", status_code=201, response_model=SubscriptionOut)
def create_subscription(
    body: SubscriptionCreateRequest,
    actor: dict = Depends(require_org_permission("subscription.create")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        s = SubscriptionUseCases(conn).create(
            actor_user_id=actor["user_id"],
            organization_id=actor["organization_id"],
            plan_id=body.plan_id,
            plan_price_id=body.plan_price_id,
            billing_currency=body.billing_currency,
            period_start=body.period_start,
            period_end=body.period_end,
            activation_source=body.activation_source,
            request_id=actor["request_id"],
        )
        return _sub_out(s)
    except Exception as exc:
        raise_sub_http(exc)


@subscriptions_router.post("/trial", status_code=201, response_model=SubscriptionOut)
def start_trial(
    body: TrialStartRequest,
    actor: dict = Depends(require_org_permission("subscription.create")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        s = SubscriptionUseCases(conn).start_trial(
            actor_user_id=actor["user_id"],
            organization_id=actor["organization_id"],
            plan_id=body.plan_id,
            plan_price_id=body.plan_price_id,
            billing_currency=body.billing_currency,
            trial_days=body.trial_days,
            activation_source=body.activation_source,
            request_id=actor["request_id"],
        )
        return _sub_out(s)
    except Exception as exc:
        raise_sub_http(exc)


@subscriptions_router.get("/{subscription_id}", response_model=SubscriptionOut)
def get_subscription(
    subscription_id: int,
    actor: dict = Depends(require_org_permission("subscription.view")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        s = SubscriptionUseCases(conn).get(subscription_id)
        if s.organization_id != actor["organization_id"]:
            from app.packages.subscriptions.presentation.error_mapping import http_error
            raise http_error(403, "Subscription not in your organization", code="permission_denied")
        return _sub_out(s)
    except Exception as exc:
        raise_sub_http(exc)


@subscriptions_router.post("/{subscription_id}/activate", response_model=SubscriptionOut)
def activate_subscription(
    subscription_id: int,
    body: SubscriptionActivateRequest,
    actor: dict = Depends(require_org_permission("subscription.change")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        s = SubscriptionUseCases(conn).activate(
            subscription_id,
            actor_user_id=actor["user_id"],
            plan_price_id=body.plan_price_id,
            period_start=body.period_start,
            period_end=body.period_end,
            request_id=actor["request_id"],
        )
        return _sub_out(s)
    except Exception as exc:
        raise_sub_http(exc)


@subscriptions_router.post("/{subscription_id}/change", response_model=SubscriptionChangeOut)
def schedule_change(
    subscription_id: int,
    body: SubscriptionChangeRequest,
    actor: dict = Depends(require_org_permission("subscription.change")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        change = SubscriptionUseCases(conn).schedule_plan_change(
            subscription_id,
            actor_user_id=actor["user_id"],
            to_plan_id=body.to_plan_id,
            to_price_id=body.to_price_id,
            scheduled_for=body.scheduled_for,
            reason=body.reason,
            request_id=actor["request_id"],
        )
        return _change_out(change)
    except Exception as exc:
        raise_sub_http(exc)


@subscriptions_router.post("/{subscription_id}/apply-change", response_model=SubscriptionOut)
def apply_change(
    subscription_id: int,
    body: ApplyChangeRequest,
    actor: dict = Depends(require_org_permission("subscription.change")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        s = SubscriptionUseCases(conn).apply_plan_change(
            body.change_id,
            actor_user_id=actor["user_id"],
            request_id=actor["request_id"],
        )
        return _sub_out(s)
    except Exception as exc:
        raise_sub_http(exc)


@subscriptions_router.post("/{subscription_id}/cancel", response_model=SubscriptionOut)
def cancel_subscription(
    subscription_id: int,
    body: SubscriptionCancelRequest,
    actor: dict = Depends(require_org_permission("subscription.cancel")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        s = SubscriptionUseCases(conn).cancel(
            subscription_id,
            actor_user_id=actor["user_id"],
            mode=body.mode,
            reason=body.reason,
            request_id=actor["request_id"],
        )
        return _sub_out(s)
    except Exception as exc:
        raise_sub_http(exc)


@subscriptions_router.post("/{subscription_id}/reactivate", response_model=SubscriptionOut)
def reactivate_subscription(
    subscription_id: int,
    body: SubscriptionReactivateRequest,
    actor: dict = Depends(require_org_permission("subscription.reactivate")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        s = SubscriptionUseCases(conn).reactivate(
            subscription_id,
            actor_user_id=actor["user_id"],
            reason=body.reason,
            request_id=actor["request_id"],
        )
        return _sub_out(s)
    except Exception as exc:
        raise_sub_http(exc)


@subscriptions_router.post("/{subscription_id}/renew", response_model=SubscriptionOut)
def renew_subscription(
    subscription_id: int,
    body: RenewRequest,
    actor: dict = Depends(require_platform_permission("plan.activate")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    """Renew subscription period (orchestration/platform action)."""
    try:
        s = SubscriptionUseCases(conn).renew(
            subscription_id,
            actor_user_id=actor["user_id"],
            new_period_start=body.new_period_start,
            new_period_end=body.new_period_end,
            request_id=actor["request_id"],
        )
        return _sub_out(s)
    except Exception as exc:
        raise_sub_http(exc)


@subscriptions_router.post("/{subscription_id}/access-state", response_model=SubscriptionOut)
def update_access_state(
    subscription_id: int,
    body: UpdateAccessStateRequest,
    actor: dict = Depends(require_platform_permission("plan.activate")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    """Update access state (orchestration hook stub for 019)."""
    try:
        s = SubscriptionUseCases(conn).update_access_state(
            subscription_id,
            actor_user_id=actor["user_id"],
            access_state=body.access_state,
            reason=body.reason,
            also_set_past_due=body.also_set_past_due,
            request_id=actor["request_id"],
        )
        return _sub_out(s)
    except Exception as exc:
        raise_sub_http(exc)


@subscriptions_router.get("/{subscription_id}/changes", response_model=PaginatedSubscriptionChanges)
def list_subscription_changes(
    subscription_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    actor: dict = Depends(require_org_permission("subscription.view")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        page, lim, offset = _page_bounds(page, limit)
        changes, total = SubscriptionUseCases(conn).list_changes(subscription_id, limit=lim, offset=offset)
        return PaginatedSubscriptionChanges(
            items=[_change_out(c) for c in changes], page=page, limit=lim, total=total
        )
    except Exception as exc:
        raise_sub_http(exc)


@subscriptions_router.get("/{subscription_id}/entitlements", response_model=list[EntitlementOut])
def list_entitlements(
    subscription_id: int,
    actor: dict = Depends(require_org_permission("subscription.view")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        snap = UsageUseCases(conn).entitlement_usage_snapshot(subscription_id)
        return [
            _entitlement_out(s["entitlement"], s["current_usage"], s["remaining"])
            for s in snap
        ]
    except Exception as exc:
        raise_sub_http(exc)


@subscriptions_router.get("/{subscription_id}/usage", response_model=PaginatedUsage)
def list_usage(
    subscription_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    feature_code: Optional[str] = Query(None),
    actor: dict = Depends(require_org_permission("usage.view")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        page, lim, offset = _page_bounds(page, limit, max_limit=200)
        records, total = UsageUseCases(conn).list(
            subscription_id, feature_code=feature_code, limit=lim, offset=offset
        )
        return PaginatedUsage(
            items=[_usage_out(r) for r in records], page=page, limit=lim, total=total
        )
    except Exception as exc:
        raise_sub_http(exc)


@subscriptions_router.post("/{subscription_id}/usage", status_code=201, response_model=UsageRecordOut)
def record_usage(
    subscription_id: int,
    body: UsageRecordRequest,
    actor: dict = Depends(require_org_permission("usage.view")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        sub = SubscriptionUseCases(conn).get(subscription_id)
        record = UsageUseCases(conn).record(
            actor_user_id=actor["user_id"],
            subscription_id=subscription_id,
            organization_id=sub.organization_id,
            feature_code=body.feature_code,
            quantity=body.quantity,
            period_start=body.period_start,
            period_end=body.period_end,
            idempotency_key=body.idempotency_key,
            request_id=actor["request_id"],
        )
        return _usage_out(record)
    except Exception as exc:
        raise_sub_http(exc)


@subscriptions_router.get("/{subscription_id}/addons", response_model=list[SubscriptionAddonOut])
def list_subscription_addons(
    subscription_id: int,
    actor: dict = Depends(require_org_permission("subscription.view")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        addons = SubscriptionAddonUseCases(conn).list(subscription_id)
        return [_sub_addon_out(a) for a in addons]
    except Exception as exc:
        raise_sub_http(exc)


@subscriptions_router.post("/{subscription_id}/addons", status_code=201, response_model=SubscriptionAddonOut)
def add_subscription_addon(
    subscription_id: int,
    body: SubscriptionAddonAddRequest,
    actor: dict = Depends(require_org_permission("subscription.change")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        sa = SubscriptionAddonUseCases(conn).add(
            subscription_id,
            actor_user_id=actor["user_id"],
            addon_id=body.addon_id,
            request_id=actor["request_id"],
        )
        return _sub_addon_out(sa)
    except Exception as exc:
        raise_sub_http(exc)


@subscriptions_router.delete("/{subscription_id}/addons/{addon_id}", response_model=SubscriptionAddonOut)
def remove_subscription_addon(
    subscription_id: int,
    addon_id: int,
    actor: dict = Depends(require_org_permission("subscription.change")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        sa = SubscriptionAddonUseCases(conn).remove(
            subscription_id,
            actor_user_id=actor["user_id"],
            addon_id=addon_id,
            request_id=actor["request_id"],
        )
        return _sub_addon_out(sa)
    except Exception as exc:
        raise_sub_http(exc)


@subscriptions_router.get("/{subscription_id}/access-state", response_model=AccessStateOut)
def get_access_state(
    subscription_id: int,
    actor: dict = Depends(require_org_permission("subscription.view")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        state = SubscriptionUseCases(conn).get_access_state(subscription_id)
        return AccessStateOut(
            subscription_id=state.subscription_id,
            access_state=state.access_state,
            reason=state.reason,
            updated_at=state.updated_at,
        )
    except Exception as exc:
        raise_sub_http(exc)
