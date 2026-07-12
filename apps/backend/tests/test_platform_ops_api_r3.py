"""Test R3: Platform ops API — Spec 027."""

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
    assert user_id is not None, f"Cannot resolve user id from {body}"
    return int(user_id)


def _platform_admin_headers(client: TestClient) -> dict:
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
        assign_role(conn, user_id=user_id, role_code="platform_admin", assigned_by=None)
    return headers


def test_platform_ops_health(client: TestClient):
    headers = _platform_admin_headers(client)
    resp = client.get("/api/v1/platform-ops/health", headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["labeled_academic"] is True
    assert "Conceptual" in data["message"] or "academic" in data["message"].lower()


def test_platform_ops_webhook_receive(client: TestClient):
    headers = _platform_admin_headers(client)
    resp = client.post(
        "/api/v1/platform-ops/webhooks/receive",
        headers=headers,
        json={
            "source": "billing",
            "event_type": "payment.completed",
            "idempotency_key": "api-idem-1",
            "payload": {"amount": 100},
        },
    )
    assert resp.status_code == 201, resp.text
    resp2 = client.post(
        "/api/v1/platform-ops/webhooks/receive",
        headers=headers,
        json={
            "source": "billing",
            "event_type": "payment.completed",
            "idempotency_key": "api-idem-1",
            "payload": {"amount": 200},
        },
    )
    assert resp2.status_code == 409


def test_platform_ops_flags(client: TestClient):
    headers = _platform_admin_headers(client)
    resp = client.put(
        "/api/v1/platform-ops/flags",
        headers=headers,
        json={"flag_key": "api_test", "description": "API test flag", "enabled": True},
    )
    assert resp.status_code == 200, resp.text
    resp2 = client.get("/api/v1/platform-ops/flags", headers=headers)
    assert resp2.status_code == 200
    assert any(f["flag_key"] == "api_test" for f in resp2.json())
