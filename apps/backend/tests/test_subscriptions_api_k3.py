"""Test K3: Subscriptions API endpoints — Spec 018.

Uses the session-scoped TestClient from conftest.
Admin user (admin/admin123) acts as platform_admin for plan endpoints.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def plan_admin_headers(client: TestClient) -> dict[str, str]:
    """Login as admin and grant platform_admin (plan.*) for catalog endpoints."""
    response = client.post(
        "/api/v1/users/login",
        json={"login": "admin", "password": "admin123", "remember": True},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    body = response.json()
    token = body["token"]
    user_id = body.get("id")
    if user_id is None and isinstance(body.get("user"), dict):
        user_id = body["user"].get("id")
    if user_id is None:
        me = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me.status_code == 200, me.text
        me_body = me.json()
        user_id = me_body.get("id") or (me_body.get("user") or {}).get("id")
    assert user_id is not None, f"Cannot resolve admin user id from {body}"
    from app.core.database import using_write_conn
    from app.packages.platform_rbac.infrastructure.repository import assign_role

    with using_write_conn() as conn:
        assign_role(conn, user_id=int(user_id), role_code="platform_admin", assigned_by=None)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def plan_id(client: TestClient, plan_admin_headers) -> int:
    """Create and activate a test plan, return its id."""
    r = client.post(
        "/api/v1/plans",
        json={"code": "k3-test-plan", "display_name": "K3 Test Plan", "trial_days_default": 7},
        headers=plan_admin_headers,
    )
    if r.status_code == 409:
        # Already exists from a previous run; get it
        r2 = client.get("/api/v1/plans?limit=100", headers=plan_admin_headers)
        for p in r2.json().get("items", []):
            if p["code"] == "k3-test-plan":
                return p["id"]
        pytest.skip("Cannot find or create k3-test-plan")
    assert r.status_code == 201, r.text
    pid = r.json()["id"]
    # Activate it
    ra = client.post(f"/api/v1/plans/{pid}/activate", headers=plan_admin_headers)
    assert ra.status_code == 200, ra.text
    return pid


# ── Plans list (public-ish) ────────────────────────────────────────────────────

def test_list_plans_authenticated(client: TestClient, plan_admin_headers):
    r = client.get("/api/v1/plans", headers=plan_admin_headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "items" in data
    assert "total" in data


def test_get_plan(client: TestClient, plan_admin_headers, plan_id):
    r = client.get(f"/api/v1/plans/{plan_id}", headers=plan_admin_headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["id"] == plan_id
    assert data["status"] == "active"


def test_create_plan_requires_auth(client: TestClient):
    r = client.post(
        "/api/v1/plans",
        json={"code": "no-auth-plan", "display_name": "NoAuth"},
    )
    assert r.status_code == 401


def test_create_plan_requires_plan_create_permission(client: TestClient):
    """demo user has no platform permissions."""
    r_login = client.post(
        "/api/v1/users/login",
        json={"login": "demo", "password": "demo123", "remember": True},
    )
    if r_login.status_code != 200:
        pytest.skip("demo user not available")
    token = r_login.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    r = client.post(
        "/api/v1/plans",
        json={"code": "demo-plan", "display_name": "Demo Plan"},
        headers=headers,
    )
    assert r.status_code == 403


# ── Plan prices ────────────────────────────────────────────────────────────────

def test_set_plan_price(client: TestClient, plan_admin_headers, plan_id):
    r = client.post(
        f"/api/v1/plans/{plan_id}/prices",
        json={"currency": "USD", "billing_period": "monthly", "amount": "29.99"},
        headers=plan_admin_headers,
    )
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["currency"] == "USD"
    assert data["billing_period"] == "monthly"
    assert data["status"] == "active"


def test_list_plan_prices(client: TestClient, plan_admin_headers, plan_id):
    r = client.get(f"/api/v1/plans/{plan_id}/prices", headers=plan_admin_headers)
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)


# ── Plan features ──────────────────────────────────────────────────────────────

def test_configure_plan_feature(client: TestClient, plan_admin_headers, plan_id):
    r = client.post(
        f"/api/v1/plans/{plan_id}/features",
        json={"feature_code": "api_requests", "limit_value": 500, "enabled": True},
        headers=plan_admin_headers,
    )
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["feature_code"] == "api_requests"


def test_list_plan_features(client: TestClient, plan_admin_headers, plan_id):
    r = client.get(f"/api/v1/plans/{plan_id}/features", headers=plan_admin_headers)
    assert r.status_code == 200, r.text
    features = r.json()
    assert any(f["feature_code"] == "api_requests" for f in features)


# ── Archive plan ───────────────────────────────────────────────────────────────

def test_archive_nonexistent_plan_returns_404(client: TestClient, plan_admin_headers):
    r = client.post("/api/v1/plans/99999/archive", headers=plan_admin_headers)
    assert r.status_code == 404


# ── Addons ─────────────────────────────────────────────────────────────────────

def test_create_addon(client: TestClient, plan_admin_headers):
    r = client.post(
        "/api/v1/addons",
        json={
            "code": "k3-extra-api",
            "display_name": "Extra API Calls",
            "feature_code": "api_requests",
            "amount": "9.99",
            "currency": "USD",
            "billing_period": "monthly",
        },
        headers=plan_admin_headers,
    )
    if r.status_code == 409:
        pytest.skip("Addon already exists")
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["code"] == "k3-extra-api"


def test_list_addons(client: TestClient, plan_admin_headers):
    r = client.get("/api/v1/addons", headers=plan_admin_headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "items" in data


# ── Subscriptions ──────────────────────────────────────────────────────────────

def test_list_subscriptions_requires_org_header(client: TestClient, plan_admin_headers):
    r = client.get("/api/v1/subscriptions", headers=plan_admin_headers)
    assert r.status_code == 400  # missing X-Organization-Id


def test_subscriptions_unauthenticated_returns_401(client: TestClient):
    r = client.get("/api/v1/subscriptions")
    assert r.status_code == 401


def test_plan_catalog_list_no_invoice_endpoint(client: TestClient, plan_admin_headers):
    """Verify there is no /invoices endpoint."""
    r = client.get("/api/v1/invoices", headers=plan_admin_headers)
    assert r.status_code in (404, 405)


def test_plan_catalog_list_no_payment_endpoint(client: TestClient, plan_admin_headers):
    """Verify there is no /payments endpoint."""
    r = client.get("/api/v1/payments", headers=plan_admin_headers)
    assert r.status_code in (404, 405)
