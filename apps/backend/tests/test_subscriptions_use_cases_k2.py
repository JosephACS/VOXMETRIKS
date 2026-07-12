"""Test K2: Subscriptions use cases — Spec 018.

Covers:
- Plan lifecycle (create, activate, archive)
- Plan price set
- Plan features configure
- Subscription trial start (org isolation)
- Subscription direct create
- Trial → activate transition
- Schedule + apply plan change
- Cancel (period_end and immediate)
- Reactivate
- Renew
- Entitlements materialized from plan
- Addon add / remove
- Usage recording (idempotency)
- EvaluateEntitlements
- UpdateAccessState (stub for 019) → does NOT mark "paid"
- ActiveSubscriptionExists enforced (one per org)
- Past_due only via UpdateAccessState, not via subscription create
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import duckdb
import pytest


@pytest.fixture(scope="module")
def conn(tmp_path_factory):
    from app.core import schema_bootstrap

    previous = schema_bootstrap.schema_ready()
    schema_bootstrap._schema_ready = False

    db_path = tmp_path_factory.mktemp("sub_uc") / "test.duckdb"
    c = duckdb.connect(str(db_path))

    from app.packages.identity.services.user_storage import ensure_user_tables
    from app.packages.organizations.infrastructure.schema import ensure_organization_tables
    from app.packages.platform_rbac.infrastructure.schema import ensure_platform_rbac_tables
    from app.packages.crm.infrastructure.schema import ensure_crm_tables
    from app.packages.contracts.infrastructure.schema import ensure_commercial_contract_tables
    from app.packages.subscriptions.infrastructure.schema import ensure_subscription_tables
    from app.packages.identity.services.password_security import hash_password
    from app.core.time_util import utc_now

    ensure_user_tables(c)
    ensure_organization_tables(c)
    ensure_platform_rbac_tables(c)
    ensure_crm_tables(c)
    ensure_commercial_contract_tables(c)
    ensure_subscription_tables(c)

    now = utc_now()
    # Create admin user
    c.execute(
        "INSERT INTO app_user (id, username, email, password_hash, role, plan, created_at, preferences_json)"
        " VALUES (?, ?, ?, ?, 'admin', 'Free', ?, '{}')",
        [200, "sub_admin", "sub_admin@test.io", hash_password("x"), now],
    )
    # Create owner user
    c.execute(
        "INSERT INTO app_user (id, username, email, password_hash, role, plan, created_at, preferences_json)"
        " VALUES (?, ?, ?, ?, 'user', 'Free', ?, '{}')",
        [201, "sub_owner", "sub_owner@test.io", hash_password("x"), now],
    )

    # Assign platform_admin role to user 200
    from app.packages.platform_rbac.infrastructure.repository import assign_role
    assign_role(c, user_id=200, role_code="platform_admin", assigned_by=None)

    # Create organization A (active)
    c.execute(
        "INSERT INTO app_organization (id, slug, display_name, organization_type, status, "
        "timezone, default_currency, created_by, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, 'active', 'UTC', 'USD', ?, ?, ?)",
        [300, "org-a", "Org A", "customer", 200, now, now],
    )
    # Create organization B (active)
    c.execute(
        "INSERT INTO app_organization (id, slug, display_name, organization_type, status, "
        "timezone, default_currency, created_by, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, 'active', 'UTC', 'USD', ?, ?, ?)",
        [301, "org-b", "Org B", "customer", 200, now, now],
    )
    # Create organization C (closed — for blocked-mutation tests)
    c.execute(
        "INSERT INTO app_organization (id, slug, display_name, organization_type, status, "
        "timezone, default_currency, created_by, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, 'closed', 'UTC', 'USD', ?, ?, ?)",
        [302, "org-c", "Org C", "customer", 200, now, now],
    )

    yield c
    c.close()
    schema_bootstrap._schema_ready = previous


# ── Plan lifecycle ─────────────────────────────────────────────────────────────

def test_create_plan_draft(conn):
    from app.packages.subscriptions.application.use_cases import PlanUseCases
    p = PlanUseCases(conn).create(
        actor_user_id=200,
        code="starter",
        display_name="Starter",
        trial_days_default=14,
    )
    assert p.id > 0
    assert p.status == "draft"
    assert p.trial_days_default == 14


def test_plan_code_unique(conn):
    from app.packages.subscriptions.application.use_cases import PlanUseCases
    from app.packages.subscriptions.domain.errors import ConflictError
    with pytest.raises(ConflictError):
        PlanUseCases(conn).create(actor_user_id=200, code="starter", display_name="Dup")


def test_activate_plan(conn):
    from app.packages.subscriptions.application.use_cases import PlanUseCases
    plan = PlanUseCases(conn).get_by_code("starter")
    p = PlanUseCases(conn).activate(plan.id, actor_user_id=200)
    assert p.status == "active"


def test_archive_plan(conn):
    from app.packages.subscriptions.application.use_cases import PlanUseCases
    # Create a new plan to archive
    p = PlanUseCases(conn).create(actor_user_id=200, code="to-archive", display_name="ToArchive")
    a = PlanUseCases(conn).archive(p.id, actor_user_id=200)
    assert a.status == "archived"


def test_archived_plan_cannot_be_subscribed(conn):
    from app.packages.subscriptions.application.use_cases import PlanUseCases, SubscriptionUseCases
    from app.packages.subscriptions.domain.errors import PlanRetiredError
    p = PlanUseCases(conn).create(actor_user_id=200, code="old-plan", display_name="Old")
    PlanUseCases(conn).archive(p.id, actor_user_id=200)
    with pytest.raises(PlanRetiredError):
        SubscriptionUseCases(conn).start_trial(
            actor_user_id=200,
            organization_id=300,
            plan_id=p.id,
            billing_currency="USD",
        )


# ── Plan prices ────────────────────────────────────────────────────────────────

def test_set_plan_price(conn):
    from app.packages.subscriptions.application.use_cases import PlanUseCases, PlanPriceUseCases
    plan = PlanUseCases(conn).get_by_code("starter")
    price = PlanPriceUseCases(conn).set_price(
        plan.id,
        actor_user_id=200,
        currency="USD",
        billing_period="monthly",
        amount=Decimal("49.00"),
    )
    assert price.amount == Decimal("49.00")
    assert price.status == "active"
    assert price.currency == "USD"


def test_set_plan_price_retires_previous(conn):
    from app.packages.subscriptions.application.use_cases import PlanUseCases, PlanPriceUseCases
    plan = PlanUseCases(conn).get_by_code("starter")
    p1 = PlanPriceUseCases(conn).set_price(
        plan.id, actor_user_id=200, currency="EUR", billing_period="monthly", amount=Decimal("45.00"),
    )
    p2 = PlanPriceUseCases(conn).set_price(
        plan.id, actor_user_id=200, currency="EUR", billing_period="monthly", amount=Decimal("50.00"),
    )
    prices = PlanPriceUseCases(conn).list_for_plan(plan.id, active_only=True)
    eur_monthly = [p for p in prices if p.currency == "EUR" and p.billing_period == "monthly"]
    assert len(eur_monthly) == 1
    assert eur_monthly[0].amount == Decimal("50.00")


# ── Plan features ──────────────────────────────────────────────────────────────

def test_configure_plan_feature(conn):
    from app.packages.subscriptions.application.use_cases import PlanUseCases, PlanFeatureUseCases
    plan = PlanUseCases(conn).get_by_code("starter")
    f = PlanFeatureUseCases(conn).configure(
        plan.id,
        actor_user_id=200,
        feature_code="max_users",
        limit_value=10,
        enabled=True,
    )
    assert f.feature_code == "max_users"
    assert f.limit_value == 10
    assert f.enabled is True


def test_configure_plan_feature_upsert(conn):
    from app.packages.subscriptions.application.use_cases import PlanUseCases, PlanFeatureUseCases
    plan = PlanUseCases(conn).get_by_code("starter")
    PlanFeatureUseCases(conn).configure(
        plan.id, actor_user_id=200, feature_code="api_calls", limit_value=1000,
    )
    updated = PlanFeatureUseCases(conn).configure(
        plan.id, actor_user_id=200, feature_code="api_calls", limit_value=5000,
    )
    assert updated.limit_value == 5000


# ── Subscription trial ─────────────────────────────────────────────────────────

def test_start_trial(conn):
    from app.packages.subscriptions.application.use_cases import PlanUseCases, SubscriptionUseCases
    plan = PlanUseCases(conn).get_by_code("starter")
    s = SubscriptionUseCases(conn).start_trial(
        actor_user_id=200,
        organization_id=300,
        plan_id=plan.id,
        billing_currency="USD",
        trial_days=7,
    )
    assert s.status == "trialing"
    assert s.trial_ends_at is not None
    assert s.organization_id == 300
    assert s.access_state == "full"


def test_trial_entitlements_materialized(conn):
    from app.packages.subscriptions.application.use_cases import SubscriptionUseCases, UsageUseCases
    subs, _ = SubscriptionUseCases(conn).list(organization_id=300, status="trialing")
    assert len(subs) > 0
    sub = subs[0]
    ents = UsageUseCases(conn).evaluate_entitlements(sub.id)
    feature_codes = {e.feature_code for e in ents}
    assert "max_users" in feature_codes
    assert "api_calls" in feature_codes


def test_one_active_subscription_per_org(conn):
    from app.packages.subscriptions.application.use_cases import PlanUseCases, SubscriptionUseCases
    from app.packages.subscriptions.domain.errors import ActiveSubscriptionExists
    plan = PlanUseCases(conn).get_by_code("starter")
    with pytest.raises(ActiveSubscriptionExists):
        SubscriptionUseCases(conn).start_trial(
            actor_user_id=200,
            organization_id=300,
            plan_id=plan.id,
            billing_currency="USD",
        )


def test_org_isolation_different_org_can_subscribe(conn):
    from app.packages.subscriptions.application.use_cases import PlanUseCases, SubscriptionUseCases
    plan = PlanUseCases(conn).get_by_code("starter")
    s = SubscriptionUseCases(conn).start_trial(
        actor_user_id=200,
        organization_id=301,
        plan_id=plan.id,
        billing_currency="USD",
    )
    assert s.organization_id == 301


def test_closed_org_cannot_subscribe(conn):
    from app.packages.subscriptions.application.use_cases import PlanUseCases, SubscriptionUseCases
    from app.packages.subscriptions.domain.errors import OrgNotActiveError
    plan = PlanUseCases(conn).get_by_code("starter")
    with pytest.raises(OrgNotActiveError):
        SubscriptionUseCases(conn).start_trial(
            actor_user_id=200,
            organization_id=302,
            plan_id=plan.id,
            billing_currency="USD",
        )


# ── Activate trial → active ────────────────────────────────────────────────────

def test_activate_trialing_subscription(conn):
    from app.packages.subscriptions.application.use_cases import SubscriptionUseCases
    subs, _ = SubscriptionUseCases(conn).list(organization_id=300, status="trialing")
    assert subs, "Expected a trialing subscription for org 300"
    s = SubscriptionUseCases(conn).activate(
        subs[0].id,
        actor_user_id=200,
        period_start=date.today(),
    )
    assert s.status == "active"
    assert s.trial_ends_at is None


# ── Plan change ────────────────────────────────────────────────────────────────

def test_schedule_and_apply_plan_change(conn):
    from app.packages.subscriptions.application.use_cases import PlanUseCases, SubscriptionUseCases
    from app.packages.subscriptions.domain.errors import InvalidTransitionError

    # Create a pro plan
    pro = PlanUseCases(conn).create(actor_user_id=200, code="pro", display_name="Pro")
    PlanUseCases(conn).activate(pro.id, actor_user_id=200)

    subs, _ = SubscriptionUseCases(conn).list(organization_id=300, status="active")
    assert subs, "Expected active subscription for org 300"
    sub = subs[0]

    # Immediate schedule applies in one step (status=applied)
    change = SubscriptionUseCases(conn).schedule_plan_change(
        sub.id,
        actor_user_id=200,
        to_plan_id=pro.id,
    )
    assert change.status == "applied"
    assert change.to_plan_id == pro.id
    updated = SubscriptionUseCases(conn).get(sub.id)
    assert updated.plan_id == pro.id

    # Re-applying an already-applied change must fail
    with pytest.raises(InvalidTransitionError):
        SubscriptionUseCases(conn).apply_plan_change(change.id, actor_user_id=200)


def test_cancel_period_end(conn):
    from app.packages.subscriptions.application.use_cases import SubscriptionUseCases
    subs, _ = SubscriptionUseCases(conn).list(organization_id=301, status="trialing")
    if not subs:
        subs, _ = SubscriptionUseCases(conn).list(organization_id=301, status="active")
    assert subs
    s = SubscriptionUseCases(conn).cancel(subs[0].id, actor_user_id=200, mode="period_end")
    assert s.cancel_at_period_end is True
    assert s.status in ("trialing", "active")


def test_cancel_immediate(conn):
    from app.packages.subscriptions.application.use_cases import PlanUseCases, SubscriptionUseCases
    from app.core.time_util import utc_now

    plan = PlanUseCases(conn).get_by_code("starter")
    now = utc_now()
    conn.execute(
        "INSERT INTO app_organization (id, slug, display_name, organization_type, status, "
        "timezone, default_currency, created_by, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, 'active', 'UTC', 'USD', ?, ?, ?)",
        [305, "org-305", "Org 305", "customer", 200, now, now],
    )
    sub = SubscriptionUseCases(conn).start_trial(
        actor_user_id=200,
        organization_id=305,
        plan_id=plan.id,
        billing_currency="USD",
        trial_days=7,
    )
    s = SubscriptionUseCases(conn).cancel(sub.id, actor_user_id=200, mode="immediate")
    assert s.status == "canceled"


# ── Reactivate ─────────────────────────────────────────────────────────────────

def test_reactivate_canceled_subscription(conn):
    from app.packages.subscriptions.application.use_cases import SubscriptionUseCases
    subs, _ = SubscriptionUseCases(conn).list(organization_id=305, status="canceled")
    assert subs
    s = SubscriptionUseCases(conn).reactivate(subs[0].id, actor_user_id=200)
    assert s.status == "active"
    assert s.access_state == "full"


# ── Renew ──────────────────────────────────────────────────────────────────────

def test_renew_subscription(conn):
    from app.packages.subscriptions.application.use_cases import SubscriptionUseCases
    subs, _ = SubscriptionUseCases(conn).list(organization_id=305, status="active")
    assert subs
    new_start = date.today() + timedelta(days=30)
    s = SubscriptionUseCases(conn).renew(
        subs[0].id,
        actor_user_id=200,
        new_period_start=new_start,
    )
    assert s.status == "active"
    assert s.current_period_start == new_start


# ── Access state / past_due ────────────────────────────────────────────────────

def test_update_access_state_to_limited(conn):
    from app.packages.subscriptions.application.use_cases import SubscriptionUseCases
    subs, _ = SubscriptionUseCases(conn).list(organization_id=305, status="active")
    assert subs
    s = SubscriptionUseCases(conn).update_access_state(
        subs[0].id,
        actor_user_id=200,
        access_state="limited",
        reason="usage_exceeded",
    )
    assert s.access_state == "limited"
    assert s.status == "active"  # status unchanged without also_set_past_due


def test_past_due_only_via_orchestration_hook(conn):
    from app.packages.subscriptions.application.use_cases import SubscriptionUseCases
    subs, _ = SubscriptionUseCases(conn).list(organization_id=305, status="active")
    assert subs
    # past_due requires also_set_past_due=True (orchestration hook)
    s = SubscriptionUseCases(conn).update_access_state(
        subs[0].id,
        actor_user_id=200,
        access_state="blocked",
        also_set_past_due=True,
        reason="payment_failed",
    )
    assert s.status == "past_due"
    assert s.access_state == "blocked"


def test_subscription_never_marked_paid(conn):
    """Subscription has no 'paid' status — prove constraint."""
    from app.core.time_util import utc_now
    now = utc_now()
    with pytest.raises(Exception):
        conn.execute(
            "INSERT INTO app_subscription (id, organization_id, plan_id, status, billing_currency, "
            "cancel_at_period_end, access_state, created_at, updated_at) "
            "VALUES (9997, 1, 1, 'paid', 'USD', FALSE, 'full', ?, ?)",
            [now, now],
        )


# ── Usage ──────────────────────────────────────────────────────────────────────

def test_record_usage(conn):
    from app.packages.subscriptions.application.use_cases import SubscriptionUseCases, UsageUseCases
    subs, _ = SubscriptionUseCases(conn).list(organization_id=300, status="active")
    assert subs
    sub = subs[0]
    r = UsageUseCases(conn).record(
        actor_user_id=200,
        subscription_id=sub.id,
        organization_id=300,
        feature_code="api_calls",
        quantity=Decimal("100"),
        period_start=date.today().replace(day=1),
        period_end=date.today(),
        idempotency_key="test-usage-001",
    )
    assert r.feature_code == "api_calls"
    assert r.quantity == Decimal("100")


def test_usage_idempotency(conn):
    from app.packages.subscriptions.application.use_cases import SubscriptionUseCases, UsageUseCases
    subs, _ = SubscriptionUseCases(conn).list(organization_id=300, status="active")
    sub = subs[0]
    r1 = UsageUseCases(conn).record(
        actor_user_id=200,
        subscription_id=sub.id,
        organization_id=300,
        feature_code="api_calls",
        quantity=Decimal("50"),
        period_start=date.today().replace(day=1),
        period_end=date.today(),
        idempotency_key="test-usage-001",  # same key
    )
    # Returns existing record, quantity unchanged
    assert r1.quantity == Decimal("100")


# ── Check feature entitlement ──────────────────────────────────────────────────

def test_check_feature_entitled(conn):
    from app.packages.subscriptions.application.use_cases import (
        PlanFeatureUseCases,
        PlanUseCases,
        PlanPriceUseCases,
        SubscriptionUseCases,
        UsageUseCases,
        _materialize_entitlements,
    )
    from decimal import Decimal

    plan = PlanUseCases(conn).create(
        actor_user_id=200, code="feat-check", display_name="FeatCheck", trial_days_default=0
    )
    PlanUseCases(conn).activate(plan.id, actor_user_id=200)
    price = PlanPriceUseCases(conn).set_price(
        plan.id, actor_user_id=200, currency="USD", billing_period="monthly", amount=Decimal("1.00")
    )
    PlanFeatureUseCases(conn).configure(
        plan_id=plan.id,
        actor_user_id=200,
        feature_code="max_users",
        limit_value=10,
        enabled=True,
    )
    from app.core.time_util import utc_now

    now = utc_now()
    conn.execute(
        "INSERT INTO app_organization (id, slug, display_name, organization_type, status, "
        "timezone, default_currency, created_by, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, 'active', 'UTC', 'USD', ?, ?, ?)",
        [310, "org-feat", "Org Feat", "customer", 200, now, now],
    )
    sub = SubscriptionUseCases(conn).create(
        actor_user_id=200,
        organization_id=310,
        plan_id=plan.id,
        plan_price_id=price.id,
        billing_currency="USD",
    )
    enabled, limit = UsageUseCases(conn).check_feature(sub.id, "max_users")
    assert enabled is True
    assert limit == 10


def test_check_feature_not_entitled(conn):
    from app.packages.subscriptions.application.use_cases import SubscriptionUseCases, UsageUseCases
    subs, _ = SubscriptionUseCases(conn).list(organization_id=300, status="active")
    sub = subs[0]
    enabled, limit = UsageUseCases(conn).check_feature(sub.id, "nonexistent_feature")
    assert enabled is False
    assert limit is None


# ── Addon ──────────────────────────────────────────────────────────────────────

def test_addon_add_and_remove(conn):
    from app.packages.subscriptions.application.use_cases import AddonUseCases, SubscriptionUseCases, SubscriptionAddonUseCases
    addon = AddonUseCases(conn).create(
        actor_user_id=200,
        code="extra-storage",
        display_name="Extra Storage",
        feature_code="storage_gb",
        amount=Decimal("9.99"),
        currency="USD",
        billing_period="monthly",
    )

    subs, _ = SubscriptionUseCases(conn).list(organization_id=300, status="active")
    sub = subs[0]

    sa = SubscriptionAddonUseCases(conn).add(sub.id, actor_user_id=200, addon_id=addon.id)
    assert sa.status == "active"

    # Feature should now be entitled
    from app.packages.subscriptions.application.use_cases import UsageUseCases
    enabled, _ = UsageUseCases(conn).check_feature(sub.id, "storage_gb")
    assert enabled is True

    removed = SubscriptionAddonUseCases(conn).remove(sub.id, actor_user_id=200, addon_id=addon.id)
    assert removed.status == "removed"

    # Feature no longer entitled
    enabled2, _ = UsageUseCases(conn).check_feature(sub.id, "storage_gb")
    assert enabled2 is False
