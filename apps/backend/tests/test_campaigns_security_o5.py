"""Test O5: Campaigns security — Spec 022."""

from __future__ import annotations

import duckdb
import pytest
from fastapi.testclient import TestClient

from app.packages.campaigns.application.use_cases import CampaignUseCases
from app.packages.campaigns.domain.errors import NotFoundError


@pytest.fixture(scope="module")
def db_conn(tmp_path_factory):
    from app.core import schema_bootstrap

    previous = schema_bootstrap._schema_ready
    schema_bootstrap._schema_ready = False

    db_path = tmp_path_factory.mktemp("campaigns_sec") / "test.duckdb"
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
    from app.core.time_util import utc_now

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

    now = utc_now()
    for oid, slug in [(60, "campaigns-sec-a"), (61, "campaigns-sec-b")]:
        conn.execute(
            """
            INSERT INTO app_organization
                (id, display_name, slug, organization_type, country_code, timezone,
                 default_currency, status, created_by, created_at, updated_at)
            VALUES (?, ?, ?, 'label', 'US', 'UTC', 'USD', 'active', 1, ?, ?)
            """,
            [oid, f"Org {slug}", slug, now, now],
        )

    schema_bootstrap._schema_ready = previous
    yield conn
    conn.close()


def test_cross_tenant_use_case_blocked(db_conn):
    c = CampaignUseCases(db_conn).create(
        actor_user_id=1, organization_id=60, name="Tenant A Campaign",
    )
    with pytest.raises(NotFoundError):
        CampaignUseCases(db_conn).get(c.id, 61)


@pytest.fixture(scope="module")
def viewer_ctx(client: TestClient) -> dict:
    resp = client.post(
        "/api/v1/users/login",
        json={"login": "demo", "password": "demo123", "remember": True},
    )
    assert resp.status_code == 200
    token = resp.json()["token"]
    user_id = resp.json().get("id") or 2
    headers = {"Authorization": f"Bearer {token}"}

    from app.core.database import using_write_conn
    from app.core.time_util import utc_now

    with using_write_conn() as conn:
        now = utc_now()
        conn.execute(
            """
            INSERT INTO app_organization
                (id, display_name, slug, organization_type, country_code, timezone,
                 default_currency, status, created_by, created_at, updated_at)
            VALUES (250, 'Campaigns Viewer Org', 'campaigns-viewer-o5', 'label',
                    'US', 'UTC', 'USD', 'active', ?, ?, ?)
            ON CONFLICT DO NOTHING
            """
        ) if False else None
        existing = conn.execute(
            "SELECT id FROM app_organization WHERE slug = 'campaigns-viewer-o5'"
        ).fetchone()
        if not existing:
            conn.execute(
                """
                INSERT INTO app_organization
                    (id, display_name, slug, organization_type, country_code, timezone,
                     default_currency, status, created_by, created_at, updated_at)
                VALUES (250, 'Campaigns Viewer Org', 'campaigns-viewer-o5', 'label',
                        'US', 'UTC', 'USD', 'active', ?, ?, ?)
                """,
                [int(user_id), now, now],
            )
        m = conn.execute(
            "SELECT id FROM app_organization_member WHERE organization_id = 250 AND user_id = ?",
            [int(user_id)],
        ).fetchone()
        if not m:
            mid = int(conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM app_organization_member").fetchone()[0])
            conn.execute(
                """
                INSERT INTO app_organization_member
                    (id, organization_id, user_id, status, created_by, created_at, updated_at)
                VALUES (?, 250, ?, 'active', ?, ?, ?)
                """,
                [mid, int(user_id), int(user_id), now, now],
            )
            viewer_rid = conn.execute("SELECT id FROM app_business_role WHERE code = 'viewer'").fetchone()[0]
            mrid = int(conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM app_member_role").fetchone()[0])
            conn.execute(
                """
                INSERT INTO app_member_role (id, member_id, role_id, status, assigned_by, assigned_at)
                VALUES (?, ?, ?, 'active', ?, ?)
                """,
                [mrid, mid, int(viewer_rid), int(user_id), now],
            )

    return {"headers": headers, "org_headers": {**headers, "X-Organization-Id": "250"}}


def test_viewer_cannot_create_campaign(client: TestClient, viewer_ctx):
    r = client.post(
        "/api/v1/campaigns",
        json={"name": "Viewer Blocked"},
        headers=viewer_ctx["org_headers"],
    )
    assert r.status_code == 403


def test_viewer_cannot_add_expense(client: TestClient, viewer_ctx):
    r = client.post(
        "/api/v1/campaigns/1/expenses",
        json={"amount": 100, "currency": "USD", "category": "ads", "expense_date": "2026-01-01"},
        headers=viewer_ctx["org_headers"],
    )
    assert r.status_code == 403


def test_audit_log_on_campaign_create(db_conn):
    c = CampaignUseCases(db_conn).create(
        actor_user_id=1, organization_id=60, name="Audit Test",
        request_id="req-campaign-audit-001",
    )
    row = db_conn.execute(
        """
        SELECT action, target_type, target_id, source, request_id
        FROM app_audit_log
        WHERE target_type = 'campaign' AND target_id = ?
        ORDER BY id DESC LIMIT 1
        """,
        [str(c.id)],
    ).fetchone()
    assert row is not None
    assert row[0] == "campaign.created"
    assert row[3] == "campaigns.use_case"
