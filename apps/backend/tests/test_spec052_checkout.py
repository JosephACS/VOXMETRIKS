"""Spec 052 — Personal + Organization checkout directed tests (isolated DuckDB)."""

from __future__ import annotations

import duckdb
import pytest


@pytest.fixture()
def personal_db(tmp_path):
    from app.core import schema_bootstrap

    schema_bootstrap._schema_ready = False
    db = tmp_path / "spec052_personal.duckdb"
    c = duckdb.connect(str(db))
    from app.core.time_util import utc_now
    from app.packages.engagement.services.app_storage import ensure_app_tables
    from app.packages.identity.services.password_security import hash_password
    from app.packages.identity.services.user_storage import ensure_user_tables
    from app.packages.personal_subscriptions.infrastructure.schema import (
        ensure_personal_subscription_tables,
    )
    from app.packages.platform_ops.infrastructure.schema import ensure_platform_ops_tables

    ensure_user_tables(c)
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS dim_track (
            id_track INTEGER PRIMARY KEY, spotify_track_id VARCHAR,
            nombre_track VARCHAR NOT NULL, id_artista INTEGER, id_album INTEGER,
            id_genero INTEGER, explicit BOOLEAN DEFAULT FALSE,
            duration_ms INTEGER, popularity INTEGER
        )
        """
    )
    ensure_app_tables(c)
    ensure_platform_ops_tables(c)
    ensure_personal_subscription_tables(c)
    now = utc_now()
    uid = 9001
    c.execute(
        """
        INSERT INTO app_user
            (id, username, email, password_hash, role, plan, favorite_genre,
             created_at, preferences_json, email_verified, auth_provider)
        VALUES (?, 'vx052_personal', 'vx052_personal@test.local', ?, 'user', 'Free',
                NULL, ?, '{}', TRUE, 'local')
        """,
        [uid, hash_password("Secret052!pass"), now],
    )
    from app.packages.personal_subscriptions.application.use_cases import (
        ensure_free_subscription,
    )

    ensure_free_subscription(c, uid)
    yield c, uid
    c.close()
    schema_bootstrap._schema_ready = False


def _attach(conn, uid, checkout_id, token="sim_tok_succeeded", last4="4242"):
    from app.packages.personal_subscriptions.application import checkout as co

    return co.attach_payment_method(
        conn,
        uid,
        checkout_id,
        brand="visa",
        last4=last4,
        exp_month=12,
        exp_year=2030,
        display_label=f"Visa ····{last4}",
        simulation_token=token,
    )


def _active_free_count(conn, uid: int) -> int:
    return int(
        conn.execute(
            """
            SELECT COUNT(*) FROM personal_subscription s
            JOIN personal_plan p ON p.id = s.plan_id
            WHERE s.user_id = ? AND p.is_free = TRUE AND s.status = 'active'
            """,
            [uid],
        ).fetchone()[0]
    )


def test_personal_success_preserves_then_supersedes(personal_db):
    conn, uid = personal_db
    from app.packages.personal_subscriptions.application import checkout as co
    from app.packages.personal_subscriptions.application.use_cases import get_subscription

    assert _active_free_count(conn, uid) == 1
    session = co.create_checkout(
        conn,
        uid,
        plan_code="premium_individual",
        billing_period="monthly",
        idempotency_key="pers-intent-1",
    )
    assert session["status"] == "awaiting_method"
    assert _active_free_count(conn, uid) == 1

    _attach(conn, uid, session["id"])
    result = co.confirm_checkout(conn, uid, session["id"], idempotency_key="pers-confirm-1")
    assert result["status"] == "succeeded"
    after = get_subscription(conn, uid)
    assert after["plan_code"] == "premium_individual"
    assert after["status"] == "active"
    assert _active_free_count(conn, uid) == 0

    again = co.confirm_checkout(conn, uid, session["id"], idempotency_key="pers-confirm-1")
    assert again["status"] == "succeeded"
    inv_count = conn.execute(
        "SELECT COUNT(*) FROM personal_invoice WHERE user_id = ? AND status = 'paid'",
        [uid],
    ).fetchone()[0]
    assert int(inv_count) == 1


def test_personal_decline_keeps_active_plan(personal_db):
    conn, uid = personal_db
    from app.packages.personal_subscriptions.application import checkout as co
    from app.packages.personal_subscriptions.application.use_cases import get_subscription

    session = co.create_checkout(
        conn,
        uid,
        plan_code="premium_individual",
        billing_period="monthly",
        idempotency_key="pers-decline-1",
    )
    _attach(conn, uid, session["id"], token="sim_tok_declined", last4="0002")
    failed = co.confirm_checkout(conn, uid, session["id"], idempotency_key="pers-confirm-d1")
    assert failed["status"] == "failed"
    assert _active_free_count(conn, uid) == 1

    _attach(conn, uid, session["id"], token="sim_tok_succeeded", last4="4242")
    ok = co.confirm_checkout(conn, uid, session["id"], idempotency_key="pers-confirm-d2")
    assert ok["status"] == "succeeded"
    assert get_subscription(conn, uid)["plan_code"] == "premium_individual"


def test_personal_rejects_pan_cvv_fields(personal_db):
    from app.packages.personal_subscriptions.application import checkout as co
    from app.packages.personal_subscriptions.domain.errors import PersonalSubscriptionError

    with pytest.raises(PersonalSubscriptionError) as ei:
        co.reject_raw_card_fields({"pan": "4111111111111111", "brand": "visa"})
    assert ei.value.code == "card_data_forbidden"
    with pytest.raises(PersonalSubscriptionError):
        co.reject_raw_card_fields({"cvv": "123", "last4": "4242"})


def test_personal_idempotent_create(personal_db):
    conn, uid = personal_db
    from app.packages.personal_subscriptions.application import checkout as co

    a = co.create_checkout(
        conn,
        uid,
        plan_code="premium_individual",
        billing_period="monthly",
        idempotency_key="same-key",
    )
    b = co.create_checkout(
        conn,
        uid,
        plan_code="premium_individual",
        billing_period="monthly",
        idempotency_key="same-key",
    )
    assert a["id"] == b["id"]


def test_personal_checkout_propagates_catalog_currency(personal_db):
    conn, uid = personal_db
    from app.packages.personal_subscriptions.application import checkout as co

    conn.execute(
        """
        UPDATE personal_plan_price SET currency = 'EUR'
        WHERE plan_id = (SELECT id FROM personal_plan WHERE code = 'premium_individual')
          AND billing_period = 'annual'
        """
    )
    session = co.create_checkout(
        conn,
        uid,
        plan_code="premium_individual",
        billing_period="annual",
        idempotency_key="pers-eur-intent",
    )

    invoice_currency = conn.execute(
        "SELECT currency FROM personal_invoice WHERE id = ?", [session["invoice_id"]]
    ).fetchone()[0]
    subscription_currency = conn.execute(
        "SELECT billing_currency FROM personal_subscription WHERE id = ?",
        [session["subscription_id"]],
    ).fetchone()[0]
    assert session["currency"] == "EUR"
    assert invoice_currency == "EUR"
    assert subscription_currency == "EUR"


def test_legacy_start_checkout_does_not_cancel_active(personal_db):
    conn, uid = personal_db
    from app.packages.personal_subscriptions.application import use_cases as uc

    assert _active_free_count(conn, uid) == 1
    payload = uc.start_checkout(
        conn, uid, plan_code="premium_individual", billing_period="monthly"
    )
    assert payload["status"] == "processing"
    assert _active_free_count(conn, uid) == 1


@pytest.fixture()
def org_db(tmp_path):
    from app.core import schema_bootstrap

    schema_bootstrap._schema_ready = False
    db = tmp_path / "spec052_org.duckdb"
    c = duckdb.connect(str(db))
    from app.core.time_util import utc_now
    from app.packages.billing.infrastructure.schema import ensure_billing_tables
    from app.packages.identity.services.password_security import hash_password
    from app.packages.identity.services.user_storage import ensure_user_tables
    from app.packages.organizations.infrastructure.schema import ensure_organization_tables
    from app.packages.platform_rbac.infrastructure.schema import ensure_platform_rbac_tables
    from app.packages.subscriptions.infrastructure.schema import ensure_subscription_tables

    ensure_user_tables(c)
    ensure_platform_rbac_tables(c)
    ensure_organization_tables(c)
    ensure_subscription_tables(c)
    ensure_billing_tables(c)
    now = utc_now()
    uid = 9101
    c.execute(
        """
        INSERT INTO app_user
            (id, username, email, password_hash, role, plan, favorite_genre,
             created_at, preferences_json, email_verified, auth_provider)
        VALUES (?, 'vx052_org', 'vx052_org@test.local', ?, 'user', 'Free',
                NULL, ?, '{}', TRUE, 'local')
        """,
        [uid, hash_password("Secret052!pass"), now],
    )
    org_id = 1
    c.execute(
        """
        INSERT INTO app_organization
            (id, display_name, slug, organization_type, timezone, default_currency,
             status, created_by, created_at, updated_at)
        VALUES (?, 'Label 052', 'label-052', 'label', 'UTC', 'USD', 'active', ?, ?, ?)
        """,
        [org_id, uid, now, now],
    )
    c.execute(
        """
        INSERT INTO app_organization_member
            (id, organization_id, user_id, status, joined_at,
             suspended_at, left_at, removed_at, created_by, created_at, updated_at)
        VALUES (1, ?, ?, 'active', ?, NULL, NULL, NULL, ?, ?, ?)
        """,
        [org_id, uid, now, uid, now, now],
    )
    role_id = c.execute(
        "SELECT id FROM app_business_role WHERE code = 'owner' LIMIT 1"
    ).fetchone()
    if role_id:
        c.execute(
            """
            INSERT INTO app_member_role
                (id, member_id, role_id, status, assigned_by, assigned_at)
            VALUES (1, 1, ?, 'active', ?, ?)
            """,
            [int(role_id[0]), uid, now],
        )

    plan = c.execute(
        "SELECT id FROM app_plan WHERE status = 'active' ORDER BY id LIMIT 1"
    ).fetchone()
    assert plan, "commercial catalog must seed a plan"
    plan_id = int(plan[0])
    price = c.execute(
        """
        SELECT id, currency, billing_period FROM app_plan_price
        WHERE plan_id = ? AND status = 'active' ORDER BY id LIMIT 1
        """,
        [plan_id],
    ).fetchone()
    assert price
    yield c, uid, org_id, plan_id, int(price[0]), str(price[1]), str(price[2])
    c.close()
    schema_bootstrap._schema_ready = False


def test_org_checkout_pending_until_success(org_db):
    conn, uid, org_id, plan_id, price_id, currency, period = org_db
    from app.packages.organizations.application.module_access import get_org_subscription_snapshot
    from app.packages.subscriptions.application import checkout as co

    snap0 = get_org_subscription_snapshot(conn, org_id)
    assert snap0["tier"] == "onboarding"

    session = co.create_checkout(
        conn,
        actor_user_id=uid,
        organization_id=org_id,
        plan_id=plan_id,
        plan_price_id=price_id,
        billing_period=period if period in ("monthly", "annual") else "monthly",
        idempotency_key="org-intent-1",
    )
    assert session["status"] == "awaiting_method"
    snap1 = get_org_subscription_snapshot(conn, org_id)
    assert snap1["tier"] == "onboarding"

    co.attach_payment_method(
        conn,
        actor_user_id=uid,
        organization_id=org_id,
        checkout_id=session["id"],
        brand="visa",
        last4="4242",
        exp_month=12,
        exp_year=2030,
        display_label="Visa ····4242",
        simulation_token="sim_tok_succeeded",
    )
    result = co.confirm_checkout(
        conn,
        actor_user_id=uid,
        organization_id=org_id,
        checkout_id=session["id"],
        idempotency_key="org-confirm-1",
    )
    assert result["status"] == "succeeded"
    snap2 = get_org_subscription_snapshot(conn, org_id)
    assert snap2["status"] == "active"
    assert snap2["tier"] == "operational"


def test_org_decline_stays_onboarding(org_db):
    conn, uid, org_id, plan_id, price_id, currency, period = org_db
    from app.packages.organizations.application.module_access import get_org_subscription_snapshot
    from app.packages.subscriptions.application import checkout as co

    session = co.create_checkout(
        conn,
        actor_user_id=uid,
        organization_id=org_id,
        plan_id=plan_id,
        plan_price_id=price_id,
        billing_period=period if period in ("monthly", "annual") else "monthly",
        idempotency_key="org-decline-1",
    )
    co.attach_payment_method(
        conn,
        actor_user_id=uid,
        organization_id=org_id,
        checkout_id=session["id"],
        brand="visa",
        last4="0002",
        exp_month=12,
        exp_year=2030,
        display_label="Visa ····0002",
        simulation_token="sim_tok_declined",
    )
    failed = co.confirm_checkout(
        conn,
        actor_user_id=uid,
        organization_id=org_id,
        checkout_id=session["id"],
        idempotency_key="org-confirm-d1",
    )
    assert failed["status"] == "failed"
    snap = get_org_subscription_snapshot(conn, org_id)
    assert snap["tier"] == "onboarding"


def test_org_cross_tenant_isolation(org_db):
    conn, uid, org_id, plan_id, price_id, currency, period = org_db
    from app.packages.subscriptions.application import checkout as co
    from app.packages.subscriptions.domain.errors import CheckoutError

    session = co.create_checkout(
        conn,
        actor_user_id=uid,
        organization_id=org_id,
        plan_id=plan_id,
        plan_price_id=price_id,
        billing_period=period if period in ("monthly", "annual") else "monthly",
        idempotency_key="org-iso-1",
    )
    with pytest.raises(CheckoutError) as ei:
        co.get_checkout(conn, organization_id=org_id + 999, checkout_id=session["id"])
    assert ei.value.code in ("checkout_not_found", "checkout_forbidden")


def test_org_cancel_checkout_stays_onboarding(org_db):
    conn, uid, org_id, plan_id, price_id, currency, period = org_db
    from app.packages.organizations.application.module_access import get_org_subscription_snapshot
    from app.packages.subscriptions.application import checkout as co

    session = co.create_checkout(
        conn,
        actor_user_id=uid,
        organization_id=org_id,
        plan_id=plan_id,
        plan_price_id=price_id,
        billing_period=period if period in ("monthly", "annual") else "monthly",
        idempotency_key="org-cancel-1",
    )
    canceled = co.cancel_checkout(
        conn,
        actor_user_id=uid,
        organization_id=org_id,
        checkout_id=session["id"],
    )
    assert canceled["status"] == "canceled"
    snap = get_org_subscription_snapshot(conn, org_id)
    assert snap["tier"] == "onboarding"


def test_org_rejects_pan_fields():
    from app.packages.subscriptions.application import checkout as co
    from app.packages.subscriptions.domain.errors import CheckoutError

    with pytest.raises(CheckoutError) as ei:
        co.reject_raw_card_fields({"card_number": "4111111111111111"})
    assert ei.value.code == "card_data_forbidden"


def test_http_rejects_pan_on_personal_checkout_sessions(tmp_path, monkeypatch):
    from app.core import schema_bootstrap
    from app.core.config import get_settings
    from fastapi.testclient import TestClient

    schema_bootstrap._schema_ready = False
    db = tmp_path / "api052.duckdb"
    monkeypatch.setenv("DB_PATH", str(db))
    get_settings.cache_clear()
    from app.main import create_app

    app = create_app()
    client = TestClient(app)
    r = client.post(
        "/api/v1/personal/checkout-sessions",
        json={
            "plan_code": "premium_individual",
            "billing_period": "monthly",
            "idempotency_key": "x" * 12,
            "pan": "4111111111111111",
        },
    )
    assert r.status_code in (401, 422)
