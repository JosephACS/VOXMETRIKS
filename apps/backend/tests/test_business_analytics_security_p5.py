"""Test P5: Business analytics security — Spec 023."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def viewer_ctx(client: TestClient) -> dict:
    resp = client.post("/api/v1/users/login", json={"login": "demo", "password": "demo123", "remember": True})
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
        if not conn.execute("SELECT id FROM app_organization WHERE slug = 'biz-analytics-viewer-p5'").fetchone():
            conn.execute(
                "INSERT INTO app_organization (id, display_name, slug, organization_type, country_code, "
                "timezone, default_currency, status, created_by, created_at, updated_at) "
                "VALUES (270, 'Biz Viewer P5', 'biz-analytics-viewer-p5', 'label', 'US', 'UTC', 'USD', "
                "'active', ?, ?, ?)",
                [int(user_id), now, now],
            )
        if not conn.execute(
            "SELECT id FROM app_organization_member WHERE organization_id = 270 AND user_id = ?",
            [int(user_id)],
        ).fetchone():
            mid = int(conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM app_organization_member").fetchone()[0])
            conn.execute(
                "INSERT INTO app_organization_member (id, organization_id, user_id, status, created_by, created_at, updated_at) "
                "VALUES (?, 270, ?, 'active', ?, ?, ?)",
                [mid, int(user_id), int(user_id), now, now],
            )
            member_id = mid
        else:
            member_id = int(conn.execute(
                "SELECT id FROM app_organization_member WHERE organization_id = 270 AND user_id = ?",
                [int(user_id)],
            ).fetchone()[0])
        vrid = conn.execute("SELECT id FROM app_business_role WHERE code = 'viewer'").fetchone()[0]
        if not conn.execute(
            "SELECT 1 FROM app_member_role WHERE member_id = ? AND role_id = ? AND status = 'active'",
            [member_id, int(vrid)],
        ).fetchone():
            mrid = int(conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM app_member_role").fetchone()[0])
            conn.execute(
                "INSERT INTO app_member_role (id, member_id, role_id, status, assigned_by, assigned_at) VALUES (?, ?, ?, 'active', ?, ?)",
                [mrid, member_id, int(vrid), int(user_id), now],
            )

    return {"org_headers": {**headers, "X-Organization-Id": "270"}}


def test_viewer_can_view_dashboard(client: TestClient, viewer_ctx):
    r = client.get("/api/v1/business-analytics/dashboard", headers=viewer_ctx["org_headers"])
    assert r.status_code == 200


def test_viewer_cannot_manage_snapshots(client: TestClient, viewer_ctx):
    r = client.post(
        "/api/v1/business-analytics/snapshots",
        json={"kpi_code": "total_streams", "period": "2026-01-01"},
        headers=viewer_ctx["org_headers"],
    )
    assert r.status_code == 403


def test_viewer_cannot_create_alerts(client: TestClient, viewer_ctx):
    r = client.post(
        "/api/v1/business-analytics/alerts",
        json={"severity": "info", "title": "Test", "body": "Body"},
        headers=viewer_ctx["org_headers"],
    )
    assert r.status_code == 403
