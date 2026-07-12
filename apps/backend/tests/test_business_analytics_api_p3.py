"""Test P3: Business analytics API — Spec 023."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def biz_admin(client: TestClient) -> dict:
    resp = client.post("/api/v1/users/login", json={"login": "admin", "password": "admin123", "remember": True})
    assert resp.status_code == 200
    token = resp.json()["token"]
    user_id = resp.json().get("id")
    if user_id is None:
        me = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
        user_id = me.json().get("id") or (me.json().get("user") or {}).get("id")
    assert user_id is not None
    headers = {"Authorization": f"Bearer {token}"}

    from app.core.database import using_write_conn
    from app.core.time_util import utc_now

    with using_write_conn() as conn:
        now = utc_now()
        if not conn.execute("SELECT id FROM app_organization WHERE slug = 'biz-analytics-o3'").fetchone():
            conn.execute(
                "INSERT INTO app_organization (id, display_name, slug, organization_type, country_code, "
                "timezone, default_currency, status, created_by, created_at, updated_at) "
                "VALUES (260, 'Biz Analytics O3', 'biz-analytics-o3', 'label', 'US', 'UTC', 'USD', "
                "'active', ?, ?, ?)",
                [int(user_id), now, now],
            )
        m_row = conn.execute(
            "SELECT id FROM app_organization_member WHERE organization_id = 260 AND user_id = ?",
            [int(user_id)],
        ).fetchone()
        if not m_row:
            mid = int(conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM app_organization_member").fetchone()[0])
            conn.execute(
                "INSERT INTO app_organization_member (id, organization_id, user_id, status, created_by, created_at, updated_at) "
                "VALUES (?, 260, ?, 'active', ?, ?, ?)",
                [mid, int(user_id), int(user_id), now, now],
            )
            member_id = mid
        else:
            member_id = int(m_row[0])
        rid = conn.execute("SELECT id FROM app_business_role WHERE code = 'owner'").fetchone()[0]
        if not conn.execute(
            "SELECT 1 FROM app_member_role WHERE member_id = ? AND role_id = ? AND status = 'active'",
            [member_id, int(rid)],
        ).fetchone():
            mrid = int(conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM app_member_role").fetchone()[0])
            conn.execute(
                "INSERT INTO app_member_role (id, member_id, role_id, status, assigned_by, assigned_at) VALUES (?, ?, ?, 'active', ?, ?)",
                [mrid, member_id, int(rid), int(user_id), now],
            )

    return {"org_headers": {**headers, "X-Organization-Id": "260"}}


def test_dashboard(client: TestClient, biz_admin):
    r = client.get("/api/v1/business-analytics/dashboard", headers=biz_admin["org_headers"])
    assert r.status_code == 200, r.text
    assert "kpis" in r.json()


def test_list_kpis(client: TestClient, biz_admin):
    r = client.get("/api/v1/business-analytics/kpis", headers=biz_admin["org_headers"])
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_list_sources(client: TestClient, biz_admin):
    r = client.get("/api/v1/business-analytics/sources", headers=biz_admin["org_headers"])
    assert r.status_code == 200
    assert any("warehouse" in s["code"] for s in r.json())


def test_generate_recommendations(client: TestClient, biz_admin):
    r = client.post("/api/v1/business-analytics/recommendations/generate", headers=biz_admin["org_headers"])
    assert r.status_code == 200
    for rec in r.json():
        assert rec["is_ai"] is False


def test_missing_org_header(client: TestClient, biz_admin):
    r = client.get("/api/v1/business-analytics/dashboard", headers={"Authorization": biz_admin["org_headers"]["Authorization"]})
    assert r.status_code == 400
