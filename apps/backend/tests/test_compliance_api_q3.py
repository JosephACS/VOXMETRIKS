"""Test Q3: Compliance API — Spec 026."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.database import using_write_conn
from app.core.time_util import utc_now


def _resolve_user_id(client: TestClient, token: str, body: dict) -> int:
    user_id = body.get("id")
    if user_id is None and isinstance(body.get("user"), dict):
        user_id = body["user"].get("id")
    if user_id is None:
        me = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200, me.text
        me_body = me.json()
        user_id = me_body.get("id") or (me_body.get("user") or {}).get("id")
    assert user_id is not None, f"Cannot resolve user id from {body}"
    return int(user_id)


def _ensure_org_with_owner(client: TestClient, org_id: int = 300, slug: str = "compliance-api") -> dict:
    resp = client.post(
        "/api/v1/users/login",
        json={"login": "admin", "password": "admin123", "remember": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    token = body["token"]
    user_id = _resolve_user_id(client, token, body)
    headers = {"Authorization": f"Bearer {token}"}

    with using_write_conn() as conn:
        now = utc_now()
        existing = conn.execute("SELECT id FROM app_organization WHERE slug = ?", [slug]).fetchone()
        if not existing:
            conn.execute(
                """
                INSERT INTO app_organization
                    (id, display_name, slug, organization_type, country_code, timezone,
                     default_currency, status, created_by, created_at, updated_at)
                VALUES (?, 'Compliance API Org', ?, 'label', 'US', 'UTC', 'USD', 'active', ?, ?, ?)
                """,
                [org_id, slug, user_id, now, now],
            )
        if not conn.execute(
            "SELECT 1 FROM app_organization_member WHERE organization_id = ? AND user_id = ?",
            [org_id, user_id],
        ).fetchone():
            mid = int(conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM app_organization_member").fetchone()[0])
            conn.execute(
                """
                INSERT INTO app_organization_member
                    (id, organization_id, user_id, status, created_by, created_at, updated_at)
                VALUES (?, ?, ?, 'active', ?, ?, ?)
                """,
                [mid, org_id, user_id, user_id, now, now],
            )
        member = conn.execute(
            "SELECT id FROM app_organization_member WHERE organization_id = ? AND user_id = ?",
            [org_id, user_id],
        ).fetchone()
        owner_role = conn.execute(
            "SELECT id FROM app_business_role WHERE code = 'owner'",
        ).fetchone()
        if member and owner_role:
            if not conn.execute(
                "SELECT 1 FROM app_member_role WHERE member_id = ? AND role_id = ? AND status = 'active'",
                [int(member[0]), int(owner_role[0])],
            ).fetchone():
                mrid = int(conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM app_member_role").fetchone()[0])
                conn.execute(
                    """
                    INSERT INTO app_member_role (id, member_id, role_id, status, assigned_by, assigned_at)
                    VALUES (?, ?, ?, 'active', ?, ?)
                    """,
                    [mrid, int(member[0]), int(owner_role[0]), user_id, now],
                )

    headers["X-Organization-Id"] = str(org_id)
    return headers


def test_compliance_terms_create_and_list(client: TestClient):
    headers = _ensure_org_with_owner(client)
    from app.core.time_util import utc_now

    resp = client.post(
        "/api/v1/compliance/terms",
        headers=headers,
        json={
            "version_code": "api-v1",
            "title": "API Terms",
            "content_summary": "Test terms",
            "effective_at": utc_now().isoformat(),
        },
    )
    assert resp.status_code == 201, resp.text
    resp2 = client.get("/api/v1/compliance/terms", headers=headers)
    assert resp2.status_code == 200
    assert resp2.json()["total"] >= 1


def test_compliance_dsr_submit(client: TestClient):
    headers = _ensure_org_with_owner(client, org_id=301, slug="compliance-dsr")
    resp = client.post(
        "/api/v1/compliance/dsr",
        headers=headers,
        json={"request_type": "export", "reason": "My data"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["request_type"] == "export"


def test_compliance_missing_org_header(client: TestClient):
    resp = client.post(
        "/api/v1/users/login",
        json={"login": "admin", "password": "admin123", "remember": True},
    )
    headers = {"Authorization": f"Bearer {resp.json()['token']}"}
    resp2 = client.get("/api/v1/compliance/terms", headers=headers)
    assert resp2.status_code == 400
