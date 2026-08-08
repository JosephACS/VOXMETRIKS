# -*- coding: utf-8 -*-
"""Spec 047 — Platform Ops access for Spec 046 platform admins."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.database import using_write_conn
from app.packages.platform_rbac.infrastructure.repository import assign_role


def _login(client: TestClient, login: str, password: str) -> tuple[str, int]:
    resp = client.post(
        "/api/v1/users/login",
        json={"login": login, "password": password, "remember": True},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    token = body["token"]
    user_id = body.get("id")
    if user_id is None and isinstance(body.get("user"), dict):
        user_id = body["user"].get("id")
    if user_id is None:
        me = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200, me.text
        me_body = me.json()
        user_id = me_body.get("id") or (me_body.get("user") or {}).get("id")
    assert user_id is not None
    return token, int(user_id)


def _revoke_platform_roles(user_id: int) -> None:
    with using_write_conn() as conn:
        conn.execute(
            "UPDATE app_user_platform_role SET status = 'revoked' WHERE user_id = ?",
            [user_id],
        )


def test_identity_admin_can_ops_view_and_manage(client: TestClient):
    token, user_id = _login(client, "admin", "admin123")
    _revoke_platform_roles(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    view = client.get("/api/v1/platform-ops/health", headers=headers)
    assert view.status_code == 200, view.text

    manage = client.post(
        "/api/v1/platform-ops/email/mock",
        headers=headers,
        json={
            "to_address": "ops-admin@example.test",
            "subject": "047",
            "body": "identity admin manage",
        },
    )
    assert manage.status_code == 200, manage.text


def test_crm_platform_admin_can_ops_view(client: TestClient):
    token, user_id = _login(client, "demo", "demo123")
    _revoke_platform_roles(user_id)
    with using_write_conn() as conn:
        assign_role(conn, user_id=user_id, role_code="platform_admin", assigned_by=None)
    headers = {"Authorization": f"Bearer {token}"}

    view = client.get("/api/v1/platform-ops/health", headers=headers)
    assert view.status_code == 200, view.text


def test_engineer_without_grant_no_bypass(client: TestClient):
    token, user_id = _login(client, "engineer", "engineer123")
    _revoke_platform_roles(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    denied = client.get("/api/v1/platform-ops/health", headers=headers)
    assert denied.status_code == 403


def test_bypass_does_not_apply_to_webhooks_or_flags(client: TestClient):
    token, user_id = _login(client, "admin", "admin123")
    _revoke_platform_roles(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    # Identity admin still gets ops.view via bypass…
    assert client.get("/api/v1/platform-ops/health", headers=headers).status_code == 200

    # …but not ops.webhooks / ops.flags without RBAC grant.
    webhooks = client.get("/api/v1/platform-ops/webhooks", headers=headers)
    assert webhooks.status_code == 403, webhooks.text

    flags = client.get("/api/v1/platform-ops/flags", headers=headers)
    assert flags.status_code == 403, flags.text
