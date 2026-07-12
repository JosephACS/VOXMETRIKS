"""Test O3: Campaigns API — Spec 022."""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def campaigns_admin(client: TestClient) -> dict:
    resp = client.post(
        "/api/v1/users/login",
        json={"login": "admin", "password": "admin123", "remember": True},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    token = body["token"]
    user_id = body.get("id") or (body.get("user") or {}).get("id")
    if user_id is None:
        me = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
        user_id = me.json().get("id")
    headers = {"Authorization": f"Bearer {token}"}

    from app.core.database import using_write_conn
    from app.core.time_util import utc_now

    with using_write_conn() as conn:
        now = utc_now()
        existing = conn.execute(
            "SELECT id FROM app_organization WHERE slug = 'campaigns-test-org-o3'"
        ).fetchone()
        if not existing:
            conn.execute(
                """
                INSERT INTO app_organization
                    (id, display_name, slug, organization_type, country_code, timezone,
                     default_currency, status, created_by, created_at, updated_at)
                VALUES (245, 'Campaigns Test Org O3', 'campaigns-test-org-o3', 'label',
                        'US', 'UTC', 'USD', 'active', ?, ?, ?)
                """,
                [int(user_id), now, now],
            )
        m_existing = conn.execute(
            "SELECT id FROM app_organization_member WHERE organization_id = 245 AND user_id = ?",
            [int(user_id)],
        ).fetchone()
        if not m_existing:
            next_mid = int(conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM app_organization_member").fetchone()[0])
            conn.execute(
                """
                INSERT INTO app_organization_member
                    (id, organization_id, user_id, status, created_by, created_at, updated_at)
                VALUES (?, 245, ?, 'active', ?, ?, ?)
                """,
                [next_mid, int(user_id), int(user_id), now, now],
            )
            owner_role_id = conn.execute("SELECT id FROM app_business_role WHERE code = 'owner'").fetchone()[0]
            next_mrid = int(conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM app_member_role").fetchone()[0])
            conn.execute(
                """
                INSERT INTO app_member_role (id, member_id, role_id, status, assigned_by, assigned_at)
                VALUES (?, ?, ?, 'active', ?, ?)
                """,
                [next_mrid, next_mid, int(owner_role_id), int(user_id), now],
            )

    return {
        "headers": headers,
        "org_headers": {**headers, "X-Organization-Id": "245"},
        "org_id": 245,
        "user_id": user_id,
    }


@pytest.fixture()
def campaign_id(client: TestClient, campaigns_admin) -> int:
    r = client.post(
        "/api/v1/campaigns",
        json={"name": f"API Campaign {uuid.uuid4().hex[:6]}"},
        headers=campaigns_admin["org_headers"],
    )
    assert r.status_code == 201, r.text
    return int(r.json()["id"])


def test_create_and_list_campaigns(client: TestClient, campaigns_admin):
    r = client.post(
        "/api/v1/campaigns",
        json={"name": f"List Test {uuid.uuid4().hex[:6]}"},
        headers=campaigns_admin["org_headers"],
    )
    assert r.status_code == 201
    r2 = client.get("/api/v1/campaigns", headers=campaigns_admin["org_headers"])
    assert r2.status_code == 200
    assert r2.json()["total"] >= 1


def test_get_campaign(client: TestClient, campaigns_admin, campaign_id):
    r = client.get(f"/api/v1/campaigns/{campaign_id}", headers=campaigns_admin["org_headers"])
    assert r.status_code == 200
    assert r.json()["id"] == campaign_id


def test_missing_org_header(client: TestClient, campaigns_admin):
    r = client.get("/api/v1/campaigns", headers=campaigns_admin["headers"])
    assert r.status_code == 400


def test_set_budget_and_expense(client: TestClient, campaigns_admin, campaign_id):
    r = client.post(
        f"/api/v1/campaigns/{campaign_id}/budget",
        json={"amount": 5000, "currency": "USD"},
        headers=campaigns_admin["org_headers"],
    )
    assert r.status_code == 200, r.text

    r2 = client.post(
        f"/api/v1/campaigns/{campaign_id}/expenses",
        json={
            "amount": 500, "currency": "USD", "category": "ads",
            "expense_date": "2026-01-15",
        },
        headers=campaigns_admin["org_headers"],
    )
    assert r2.status_code == 201, r2.text


def test_budget_exceeded_returns_409(client: TestClient, campaigns_admin, campaign_id):
    client.post(
        f"/api/v1/campaigns/{campaign_id}/budget",
        json={"amount": 100, "currency": "USD"},
        headers=campaigns_admin["org_headers"],
    )
    r = client.post(
        f"/api/v1/campaigns/{campaign_id}/expenses",
        json={
            "amount": 500, "currency": "USD", "category": "ads",
            "expense_date": "2026-01-15",
        },
        headers=campaigns_admin["org_headers"],
    )
    assert r.status_code == 409


def test_compute_roi_unavailable(client: TestClient, campaigns_admin, campaign_id):
    client.patch(
        f"/api/v1/campaigns/{campaign_id}",
        json={"start_date": "2026-01-01", "end_date": "2026-03-31"},
        headers=campaigns_admin["org_headers"],
    )
    r = client.post(
        f"/api/v1/campaigns/{campaign_id}/roi/compute",
        headers=campaigns_admin["org_headers"],
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "unavailable"
    assert body["roi_value"] is None


def test_approval_workflow(client: TestClient, campaigns_admin, campaign_id):
    r = client.post(
        f"/api/v1/campaigns/{campaign_id}/approvals",
        json={"approval_type": "launch"},
        headers=campaigns_admin["org_headers"],
    )
    assert r.status_code == 201, r.text
    approval_id = r.json()["id"]

    r2 = client.post(
        f"/api/v1/campaigns/approvals/{approval_id}/decide",
        json={"approved": True, "reason": "Looks good"},
        headers=campaigns_admin["org_headers"],
    )
    assert r2.status_code == 403


def test_list_approvals_and_expenses(client: TestClient, campaigns_admin, campaign_id):
    r = client.get(
        f"/api/v1/campaigns/{campaign_id}/approvals",
        headers=campaigns_admin["org_headers"],
    )
    assert r.status_code == 200
    r2 = client.get(
        f"/api/v1/campaigns/{campaign_id}/expenses",
        headers=campaigns_admin["org_headers"],
    )
    assert r2.status_code == 200
