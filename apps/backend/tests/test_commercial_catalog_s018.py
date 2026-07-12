"""Commercial catalog normalization — plans, prices, features."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import duckdb
import pytest

from app.core import schema_bootstrap
from app.packages.identity.services.user_storage import ensure_user_tables
from app.packages.subscriptions.application.commercial_catalog import (
    COMMERCIAL_ACTIVE_AMOUNTS,
    COMMERCIAL_CATALOG,
    COMMERCIAL_PLAN_CODES,
    ensure_commercial_catalog,
    get_active_price_id,
    subscription_line_description,
)
from app.packages.subscriptions.infrastructure.schema import ensure_subscription_tables
from app.packages.business_analytics.application.recurring_revenue import compute_recurring_revenue
from app.packages.organizations.infrastructure.schema import ensure_organization_tables
from app.core.time_util import utc_now


@pytest.fixture()
def conn(tmp_path: Path):
    previous = schema_bootstrap.schema_ready()
    schema_bootstrap._schema_ready = False
    db = duckdb.connect(str(tmp_path / "catalog.duckdb"))
    ensure_user_tables(db)
    ensure_organization_tables(db)
    ensure_subscription_tables(db)
    yield db
    db.close()
    schema_bootstrap._schema_ready = previous


def test_catalog_active_prices(conn):
    ensure_commercial_catalog(conn)
    codes = {
        r[0]
        for r in conn.execute(
            "SELECT code FROM app_plan WHERE status = 'active'"
        ).fetchall()
    }
    assert COMMERCIAL_PLAN_CODES.issubset(codes)

    rows = conn.execute(
        """
        SELECT p.code, pp.billing_period, pp.amount, pp.status
        FROM app_plan_price pp
        JOIN app_plan p ON p.id = pp.plan_id
        WHERE p.code IN ('starter','professional','business','enterprise')
          AND pp.status = 'active' AND pp.currency = 'USD'
        ORDER BY p.code, pp.billing_period
        """
    ).fetchall()
    got = {(str(c), str(b), Decimal(str(a)).quantize(Decimal("0.01"))) for c, b, a, s in rows}
    expected = set()
    for plan in COMMERCIAL_CATALOG:
        for price in plan.prices:
            expected.add((plan.code, price.billing_period, price.amount.quantize(Decimal("0.01"))))
    assert got == expected
    assert all(a in COMMERCIAL_ACTIVE_AMOUNTS for _, _, a in got)


def test_legacy_demo_prices_retired_not_deleted(conn):
    now = utc_now()
    pid = int(conn.execute("SELECT COALESCE(MAX(id),0)+1 FROM app_plan").fetchone()[0])
    conn.execute(
        """
        INSERT INTO app_plan
            (id, code, display_name, description, status, trial_days_default, sort_order, created_at, updated_at)
        VALUES (?, 'demo-legacy', 'Legacy Demo', 'old', 'active', 0, 99, ?, ?)
        """,
        [pid, now, now],
    )
    price_id = int(conn.execute("SELECT COALESCE(MAX(id),0)+1 FROM app_plan_price").fetchone()[0])
    conn.execute(
        """
        INSERT INTO app_plan_price
            (id, plan_id, currency, billing_period, amount, status, created_at, updated_at)
        VALUES (?, ?, 'USD', 'monthly', 75.00, 'active', ?, ?)
        """,
        [price_id, pid, now, now],
    )
    ensure_commercial_catalog(conn)
    status = conn.execute(
        "SELECT status FROM app_plan_price WHERE id = ?", [price_id]
    ).fetchone()[0]
    assert status == "retired"
    # Row still exists
    assert conn.execute(
        "SELECT COUNT(*) FROM app_plan_price WHERE id = ?", [price_id]
    ).fetchone()[0] == 1


def test_professional_monthly_price_id(conn):
    ensure_commercial_catalog(conn)
    price_id = get_active_price_id(conn, plan_code="professional", billing_period="monthly")
    assert price_id is not None
    amount = conn.execute(
        "SELECT amount FROM app_plan_price WHERE id = ?", [price_id]
    ).fetchone()[0]
    assert Decimal(str(amount)).quantize(Decimal("0.01")) == Decimal("99.00")


def test_invoice_line_includes_plan_and_period(conn):
    ensure_commercial_catalog(conn)
    now = utc_now()
    org_id = int(conn.execute("SELECT COALESCE(MAX(id),0)+1 FROM app_organization").fetchone()[0])
    conn.execute(
        """
        INSERT INTO app_organization
            (id, display_name, legal_name, slug, organization_type, country_code,
             timezone, default_currency, status, created_by, created_at, updated_at, is_demo)
        VALUES (?, 'Cat Org', NULL, 'cat-org', 'label', NULL,
                'UTC', 'USD', 'active', 1, ?, ?, TRUE)
        """,
        [org_id, now, now],
    )
    plan_id = conn.execute("SELECT id FROM app_plan WHERE code='professional'").fetchone()[0]
    price_id = get_active_price_id(conn, plan_code="professional", billing_period="monthly")
    sub_id = int(conn.execute("SELECT COALESCE(MAX(id),0)+1 FROM app_subscription").fetchone()[0])
    conn.execute(
        """
        INSERT INTO app_subscription
            (id, organization_id, plan_id, plan_price_id, status, billing_currency,
             activation_source, access_state, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'active', 'USD', 'test', 'full', ?, ?)
        """,
        [sub_id, org_id, plan_id, price_id, now, now],
    )
    line = subscription_line_description(conn, subscription_id=sub_id)
    assert line is not None
    desc, amount, currency = line
    assert "Professional" in desc
    assert "monthly" in desc
    assert "$99.00 USD" in desc
    assert amount == Decimal("99.00")
    assert currency == "USD"


def test_mrr_uses_subscription_price(conn):
    ensure_commercial_catalog(conn)
    now = utc_now()
    org_id = int(conn.execute("SELECT COALESCE(MAX(id),0)+1 FROM app_organization").fetchone()[0])
    conn.execute(
        """
        INSERT INTO app_organization
            (id, display_name, legal_name, slug, organization_type, country_code,
             timezone, default_currency, status, created_by, created_at, updated_at, is_demo)
        VALUES (?, 'MRR Org', NULL, 'mrr-org', 'label', NULL,
                'UTC', 'USD', 'active', 1, ?, ?, TRUE)
        """,
        [org_id, now, now],
    )
    plan_id = conn.execute("SELECT id FROM app_plan WHERE code='starter'").fetchone()[0]
    price_id = get_active_price_id(conn, plan_code="starter", billing_period="monthly")
    sub_id = int(conn.execute("SELECT COALESCE(MAX(id),0)+1 FROM app_subscription").fetchone()[0])
    conn.execute(
        """
        INSERT INTO app_subscription
            (id, organization_id, plan_id, plan_price_id, status, billing_currency,
             activation_source, access_state, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'active', 'USD', 'test', 'full', ?, ?)
        """,
        [sub_id, org_id, plan_id, price_id, now, now],
    )
    metrics = compute_recurring_revenue(conn, organization_id=org_id)
    assert metrics.get("active_mrr") == 49.0
