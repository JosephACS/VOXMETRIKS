"""Test O1: Campaigns schema — Spec 022."""

from __future__ import annotations

import duckdb
import pytest


@pytest.fixture(scope="module")
def db_conn(tmp_path_factory):
    from app.core import schema_bootstrap

    previous = schema_bootstrap._schema_ready
    schema_bootstrap._schema_ready = False

    db_path = tmp_path_factory.mktemp("campaigns_schema") / "test.duckdb"
    conn = duckdb.connect(str(db_path))

    from app.packages.identity.services.user_storage import ensure_user_tables
    from app.packages.organizations.infrastructure.schema import ensure_organization_tables
    from app.packages.platform_rbac.infrastructure.schema import ensure_platform_rbac_tables
    from app.packages.crm.infrastructure.schema import ensure_crm_tables
    from app.packages.contracts.infrastructure.schema import ensure_commercial_contract_tables
    from app.packages.subscriptions.infrastructure.schema import ensure_subscription_tables
    from app.packages.billing.infrastructure.schema import ensure_billing_tables
    from app.packages.artists.infrastructure.schema import ensure_artist_tables
    from app.packages.catalog_rights.infrastructure.schema import ensure_catalog_rights_tables
    from app.packages.campaigns.infrastructure.schema import ensure_campaign_tables

    ensure_user_tables(conn)
    ensure_organization_tables(conn)
    ensure_platform_rbac_tables(conn)
    ensure_crm_tables(conn)
    ensure_commercial_contract_tables(conn)
    ensure_subscription_tables(conn)
    ensure_billing_tables(conn)
    ensure_artist_tables(conn)
    ensure_catalog_rights_tables(conn)
    ensure_campaign_tables(conn)

    schema_bootstrap._schema_ready = previous
    yield conn
    conn.close()


@pytest.mark.parametrize(
    "table",
    [
        "app_campaign",
        "app_campaign_objective",
        "app_campaign_target",
        "app_campaign_budget",
        "app_campaign_approval",
        "app_campaign_expense",
        "app_campaign_result",
        "app_attribution_definition",
        "app_attributable_revenue_record",
        "app_campaign_roi_snapshot",
        "app_campaign_status_history",
    ],
)
def test_campaign_table_exists(db_conn, table):
    db_conn.execute(f"SELECT id FROM {table} LIMIT 0")


def test_ensure_campaign_tables_idempotent(db_conn):
    from app.packages.campaigns.infrastructure.schema import CAMPAIGNS_TABLES, ensure_campaign_tables

    ensure_campaign_tables(db_conn)
    for table in CAMPAIGNS_TABLES:
        count = db_conn.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
            [table],
        ).fetchone()[0]
        assert int(count) == 1


def test_campaign_status_check(db_conn):
    from app.core.time_util import utc_now

    now = utc_now()
    with pytest.raises(Exception):
        db_conn.execute(
            """
            INSERT INTO app_campaign
                (id, organization_id, name, status, created_at, updated_at)
            VALUES (9001, 1, 'Bad', 'invalid_status', ?, ?)
            """,
            [now, now],
        )


@pytest.mark.parametrize(
    "code",
    [
        "campaign.view",
        "campaign.create",
        "campaign.update",
        "campaign.approve",
        "campaign.expense",
        "campaign.close",
    ],
)
def test_campaign_permission_seeded(db_conn, code):
    row = db_conn.execute("SELECT id FROM app_permission WHERE code = ?", [code]).fetchone()
    assert row is not None, f"{code} not seeded"


def test_owner_has_all_campaign_permissions(db_conn):
    rows = db_conn.execute(
        """
        SELECT p.code
        FROM app_business_role br
        JOIN app_role_permission rp ON rp.role_id = br.id
        JOIN app_permission p ON p.id = rp.permission_id
        WHERE br.code = 'owner' AND p.code LIKE 'campaign.%'
        """
    ).fetchall()
    codes = {r[0] for r in rows}
    assert codes == {
        "campaign.view", "campaign.create", "campaign.update",
        "campaign.approve", "campaign.expense", "campaign.close",
    }


def test_marketing_manager_campaign_permissions(db_conn):
    rows = db_conn.execute(
        """
        SELECT p.code
        FROM app_business_role br
        JOIN app_role_permission rp ON rp.role_id = br.id
        JOIN app_permission p ON p.id = rp.permission_id
        WHERE br.code = 'marketing_manager' AND p.code LIKE 'campaign.%'
        """
    ).fetchall()
    codes = {r[0] for r in rows}
    assert codes == {"campaign.view", "campaign.create", "campaign.update", "campaign.expense"}


def test_finance_campaign_permissions(db_conn):
    rows = db_conn.execute(
        """
        SELECT p.code
        FROM app_business_role br
        JOIN app_role_permission rp ON rp.role_id = br.id
        JOIN app_permission p ON p.id = rp.permission_id
        WHERE br.code = 'finance' AND p.code LIKE 'campaign.%'
        """
    ).fetchall()
    codes = {r[0] for r in rows}
    assert codes == {"campaign.view", "campaign.approve"}
