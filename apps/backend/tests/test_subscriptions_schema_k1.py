"""Test K1: Subscriptions schema — Spec 018.

Verifies:
- All 10 subscription tables created.
- Status CHECK constraints enforced.
- NO invoice/payment/billing_profile tables created.
- Platform RBAC seeded with plan.* permissions.
- Org catalogs seeded with subscription.* permissions.
"""

from __future__ import annotations

import pytest
import duckdb


@pytest.fixture(scope="module")
def db_conn(tmp_path_factory):
    from app.core import schema_bootstrap

    previous = schema_bootstrap.schema_ready()
    schema_bootstrap._schema_ready = False

    db_path = tmp_path_factory.mktemp("sub_schema") / "test.duckdb"
    conn = duckdb.connect(str(db_path))

    from app.packages.identity.services.user_storage import ensure_user_tables
    from app.packages.organizations.infrastructure.schema import ensure_organization_tables
    from app.packages.platform_rbac.infrastructure.schema import ensure_platform_rbac_tables
    from app.packages.crm.infrastructure.schema import ensure_crm_tables
    from app.packages.contracts.infrastructure.schema import ensure_commercial_contract_tables
    from app.packages.subscriptions.infrastructure.schema import ensure_subscription_tables

    ensure_user_tables(conn)
    ensure_organization_tables(conn)
    ensure_platform_rbac_tables(conn)
    ensure_crm_tables(conn)
    ensure_commercial_contract_tables(conn)
    ensure_subscription_tables(conn)

    yield conn
    conn.close()
    schema_bootstrap._schema_ready = previous


# ── Table existence ────────────────────────────────────────────────────────────

def test_app_plan_table_exists(db_conn):
    db_conn.execute("SELECT id FROM app_plan LIMIT 0")


def test_app_plan_price_table_exists(db_conn):
    db_conn.execute("SELECT id FROM app_plan_price LIMIT 0")


def test_app_plan_feature_table_exists(db_conn):
    db_conn.execute("SELECT id FROM app_plan_feature LIMIT 0")


def test_app_addon_table_exists(db_conn):
    db_conn.execute("SELECT id FROM app_addon LIMIT 0")


def test_app_subscription_table_exists(db_conn):
    db_conn.execute("SELECT id FROM app_subscription LIMIT 0")


def test_app_subscription_change_table_exists(db_conn):
    db_conn.execute("SELECT id FROM app_subscription_change LIMIT 0")


def test_app_subscription_entitlement_table_exists(db_conn):
    db_conn.execute("SELECT id FROM app_subscription_entitlement LIMIT 0")


def test_app_subscription_addon_table_exists(db_conn):
    db_conn.execute("SELECT id FROM app_subscription_addon LIMIT 0")


def test_app_usage_record_table_exists(db_conn):
    db_conn.execute("SELECT id FROM app_usage_record LIMIT 0")


def test_app_subscription_access_state_table_exists(db_conn):
    db_conn.execute("SELECT id FROM app_subscription_access_state LIMIT 0")


# ── No forbidden tables ────────────────────────────────────────────────────────

def test_no_invoice_table(db_conn):
    tables = {r[0] for r in db_conn.execute("SHOW TABLES").fetchall()}
    assert "app_invoice" not in tables
    assert "invoice" not in tables


def test_no_payment_table(db_conn):
    tables = {r[0] for r in db_conn.execute("SHOW TABLES").fetchall()}
    assert "app_payment" not in tables
    assert "payment" not in tables


def test_no_billing_profile_table(db_conn):
    tables = {r[0] for r in db_conn.execute("SHOW TABLES").fetchall()}
    assert "app_billing_profile" not in tables


# ── Status constraints ─────────────────────────────────────────────────────────

def test_plan_status_constraint(db_conn):
    from app.core.time_util import utc_now
    now = utc_now()
    with pytest.raises(Exception):
        db_conn.execute(
            "INSERT INTO app_plan (id, code, display_name, status, trial_days_default, sort_order, created_at, updated_at) "
            "VALUES (9999, 'bad', 'bad', 'invalid_status', 0, 0, ?, ?)",
            [now, now],
        )


def test_subscription_status_constraint(db_conn):
    from app.core.time_util import utc_now
    now = utc_now()
    with pytest.raises(Exception):
        db_conn.execute(
            "INSERT INTO app_subscription (id, organization_id, plan_id, status, billing_currency, "
            "cancel_at_period_end, access_state, created_at, updated_at) "
            "VALUES (9999, 1, 1, 'paid', 'USD', FALSE, 'full', ?, ?)",
            [now, now],
        )


def test_subscription_access_state_constraint(db_conn):
    from app.core.time_util import utc_now
    now = utc_now()
    with pytest.raises(Exception):
        db_conn.execute(
            "INSERT INTO app_subscription (id, organization_id, plan_id, status, billing_currency, "
            "cancel_at_period_end, access_state, created_at, updated_at) "
            "VALUES (9998, 1, 1, 'active', 'USD', FALSE, 'unknown', ?, ?)",
            [now, now],
        )


# ── Platform permissions seeded ────────────────────────────────────────────────

def test_plan_permissions_seeded_in_platform_rbac(db_conn):
    rows = db_conn.execute("SELECT code FROM app_platform_permission").fetchall()
    codes = {r[0] for r in rows}
    assert "plan.view" in codes
    assert "plan.create" in codes
    assert "plan.activate" in codes
    assert "plan.archive" in codes
    assert "plan_price.manage" in codes
    assert "plan_feature.manage" in codes
    assert "addon.manage" in codes


def test_platform_admin_has_plan_permissions(db_conn):
    rows = db_conn.execute("""
        SELECT pp.code
        FROM app_platform_role pr
        JOIN app_platform_role_permission rp ON rp.role_id = pr.id
        JOIN app_platform_permission pp ON pp.id = rp.permission_id
        WHERE pr.code = 'platform_admin' AND pp.code LIKE 'plan%'
    """).fetchall()
    codes = {r[0] for r in rows}
    assert "plan.create" in codes
    assert "plan.activate" in codes


def test_auditor_has_plan_view_permission(db_conn):
    rows = db_conn.execute("""
        SELECT pp.code
        FROM app_platform_role pr
        JOIN app_platform_role_permission rp ON rp.role_id = pr.id
        JOIN app_platform_permission pp ON pp.id = rp.permission_id
        WHERE pr.code = 'auditor'
    """).fetchall()
    codes = {r[0] for r in rows}
    assert "plan.view" in codes


# ── Org permissions seeded ─────────────────────────────────────────────────────

def test_subscription_permissions_seeded_in_org_catalog(db_conn):
    rows = db_conn.execute("SELECT code FROM app_permission").fetchall()
    codes = {r[0] for r in rows}
    assert "subscription.view" in codes
    assert "subscription.create" in codes
    assert "subscription.change" in codes
    assert "subscription.cancel" in codes
    assert "subscription.reactivate" in codes
    assert "usage.view" in codes


def test_owner_role_has_subscription_permissions(db_conn):
    rows = db_conn.execute("""
        SELECT p.code
        FROM app_business_role br
        JOIN app_role_permission rp ON rp.role_id = br.id
        JOIN app_permission p ON p.id = rp.permission_id
        WHERE br.code = 'owner' AND p.code LIKE 'subscription%'
    """).fetchall()
    codes = {r[0] for r in rows}
    assert "subscription.view" in codes
    assert "subscription.create" in codes
    assert "subscription.cancel" in codes


def test_billing_manager_has_subscription_permissions(db_conn):
    rows = db_conn.execute("""
        SELECT p.code
        FROM app_business_role br
        JOIN app_role_permission rp ON rp.role_id = br.id
        JOIN app_permission p ON p.id = rp.permission_id
        WHERE br.code = 'billing_manager'
    """).fetchall()
    codes = {r[0] for r in rows}
    assert "subscription.view" in codes
    assert "subscription.create" in codes


# ── Idempotency ────────────────────────────────────────────────────────────────

def test_ensure_subscription_tables_is_idempotent(db_conn):
    from app.core import schema_bootstrap
    schema_bootstrap._schema_ready = False
    from app.packages.subscriptions.infrastructure.schema import ensure_subscription_tables
    # Should not raise
    ensure_subscription_tables(db_conn)
    ensure_subscription_tables(db_conn)
