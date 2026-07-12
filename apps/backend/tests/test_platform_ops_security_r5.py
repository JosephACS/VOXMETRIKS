"""Test R5: Platform ops security — Spec 027."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.database import using_write_conn
from app.packages.platform_rbac.infrastructure.repository import assign_role


def _resolve_user_id(client: TestClient, token: str, body: dict) -> int:
    user_id = body.get("id")
    if user_id is None and isinstance(body.get("user"), dict):
        user_id = body["user"].get("id")
    if user_id is None:
        me = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200, me.text
        me_body = me.json()
        user_id = me_body.get("id") or (me_body.get("user") or {}).get("id")
    assert user_id is not None
    return int(user_id)


def test_unauthenticated_ops_denied(client: TestClient):
    resp = client.get("/api/v1/platform-ops/health")
    assert resp.status_code in (401, 403)


def test_demo_user_ops_denied(client: TestClient):
    resp = client.post(
        "/api/v1/users/login",
        json={"login": "demo", "password": "demo123", "remember": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    token = body["token"]
    user_id = _resolve_user_id(client, token, body)
    headers = {"Authorization": f"Bearer {token}"}

    with using_write_conn() as conn:
        conn.execute(
            "UPDATE app_user_platform_role SET status = 'revoked' WHERE user_id = ?",
            [user_id],
        )

    resp2 = client.get("/api/v1/platform-ops/health", headers=headers)
    assert resp2.status_code == 403


def test_provider_secret_redacted_in_api(client: TestClient):
    resp = client.post(
        "/api/v1/users/login",
        json={"login": "admin", "password": "admin123", "remember": True},
    )
    body = resp.json()
    token = body["token"]
    user_id = _resolve_user_id(client, token, body)
    headers = {"Authorization": f"Bearer {token}"}

    with using_write_conn() as conn:
        assign_role(conn, user_id=user_id, role_code="platform_admin", assigned_by=None)

    resp2 = client.post(
        "/api/v1/platform-ops/providers",
        headers=headers,
        json={
            "provider_code": "test_redact",
            "display_name": "Test",
            "secret_ref": "secret://ops/abcdefghijklmnop",
        },
    )
    assert resp2.status_code == 201, resp2.text
    data = resp2.json()
    assert "abcdefghijklmnop" not in (data.get("secret_ref_redacted") or "")
    assert "****" in (data.get("secret_ref_redacted") or "")
