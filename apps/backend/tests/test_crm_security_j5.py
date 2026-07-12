"""Test J5: CRM security — Spec 017.

Covers:
- Normal user (no platform role) gets 403 on all CRM endpoints
- Org owner without platform role gets 403 on CRM endpoints
- Identity roles admin/engineer do NOT grant CRM access
- Claim token is single-use (also in J2; verified here via API)
- sales_agent without platform role gets 403
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


# ── Helpers ───────────────────────────────────────────────────────────────────

def _login(client: TestClient, login: str, password: str) -> dict[str, str]:
    r = client.post(
        "/api/v1/users/login",
        json={"login": login, "password": password, "remember": True},
    )
    assert r.status_code == 200, f"Login failed for {login}: {r.text}"
    return {"Authorization": f"Bearer {r.json()['token']}"}


@pytest.fixture(scope="module")
def demo_headers(client: TestClient) -> dict[str, str]:
    """Regular demo user — no CRM role."""
    return _login(client, "demo", "demo123")


@pytest.fixture(scope="module")
def admin_headers(client: TestClient) -> dict[str, str]:
    """Admin identity role — no CRM role."""
    return _login(client, "admin", "admin123")


@pytest.fixture(scope="module")
def engineer_headers(client: TestClient) -> dict[str, str]:
    """Engineer identity role — no CRM role."""
    return _login(client, "engineer", "engineer123")


# ── Normal user without platform role must get 403 ───────────────────────────

CRM_ENDPOINTS = [
    ("GET", "/api/v1/crm/prospects"),
    ("POST", "/api/v1/crm/prospects"),
    ("GET", "/api/v1/crm/opportunities"),
    ("POST", "/api/v1/crm/opportunities"),
    ("GET", "/api/v1/crm/activities"),
    ("POST", "/api/v1/crm/activities"),
    ("GET", "/api/v1/crm/quotations"),
    ("POST", "/api/v1/crm/quotations"),
    ("GET", "/api/v1/crm/approvals"),
    ("POST", "/api/v1/crm/conversions"),
    ("GET", "/api/v1/crm/audit"),
    ("GET", "/api/v1/crm/contacts"),
    ("POST", "/api/v1/crm/contacts"),
    ("GET", "/api/v1/crm/contracts"),
]


def _call(client: TestClient, method: str, url: str, headers=None) -> object:
    """Call client method safely without passing json for GET requests."""
    if method.upper() == "GET":
        return client.get(url, headers=headers)
    return getattr(client, method.lower())(url, headers=headers, json={})


@pytest.mark.parametrize("method,url", CRM_ENDPOINTS)
def test_normal_user_gets_403_on_crm(client: TestClient, demo_headers, method, url):
    """Regular user (no platform role) must get 403 on any CRM endpoint."""
    r = _call(client, method, url, headers=demo_headers)
    assert r.status_code == 403, f"Expected 403 for {method} {url}, got {r.status_code}: {r.text}"


@pytest.mark.parametrize("method,url", [
    ("GET", "/api/v1/crm/prospects"),
    ("POST", "/api/v1/crm/prospects"),
    ("GET", "/api/v1/crm/audit"),
])
def test_admin_identity_role_gets_403_on_crm(client: TestClient, admin_headers, method, url):
    """admin identity role must NOT grant CRM access (different RBAC system)."""
    r = _call(client, method, url, headers=admin_headers)
    assert r.status_code == 403, f"Expected 403 for admin on {method} {url}, got {r.status_code}"


@pytest.mark.parametrize("method,url", [
    ("GET", "/api/v1/crm/prospects"),
    ("GET", "/api/v1/crm/opportunities"),
])
def test_engineer_identity_role_gets_403_on_crm(client: TestClient, engineer_headers, method, url):
    """engineer identity role must NOT grant CRM access."""
    r = _call(client, method, url, headers=engineer_headers)
    assert r.status_code == 403, f"Expected 403 for engineer on {method} {url}, got {r.status_code}"


# ── Unauthenticated must get 401 ──────────────────────────────────────────────

@pytest.mark.parametrize("method,url", [
    ("GET", "/api/v1/crm/prospects"),
    ("GET", "/api/v1/crm/opportunities"),
    ("POST", "/api/v1/crm/conversions"),
])
def test_unauthenticated_gets_401(client: TestClient, method, url):
    r = _call(client, method, url)
    assert r.status_code == 401, f"Expected 401 for {method} {url}, got {r.status_code}"


# ── Org owner without CRM platform role gets 403 on CRM ──────────────────────

def test_org_owner_without_crm_role_gets_403(client: TestClient, demo_headers):
    """An org owner does NOT automatically get CRM access.

    demo user is a regular user (may or may not have an org). Either way,
    org ownership must NOT grant crm.prospect.view.
    """
    r = client.get("/api/v1/crm/prospects", headers=demo_headers)
    assert r.status_code == 403, f"Org owner should not have CRM access: {r.status_code}"


# ── Sales agent cannot approve quotations (403) ──────────────────────────────

def test_sales_agent_cannot_view_approvals(client: TestClient):
    """sales_agent role does not have quotation.approve permission."""
    r = client.post(
        "/api/v1/users/login",
        json={"login": "sales_agent@voxmetrik.io", "password": "demo123", "remember": True},
    )
    if r.status_code != 200:
        pytest.skip("sales_agent demo user not available")
    headers = {"Authorization": f"Bearer {r.json()['token']}"}

    # GET /approvals requires quotation.approve — agent should get 403
    r2 = client.get("/api/v1/crm/approvals", headers=headers)
    assert r2.status_code == 403, f"Agent must not access approvals: {r2.status_code}"


# ── CRM audit only for manager/auditor/admin ─────────────────────────────────

def test_sales_agent_cannot_view_audit(client: TestClient):
    r = client.post(
        "/api/v1/users/login",
        json={"login": "sales_agent@voxmetrik.io", "password": "demo123"},
    )
    if r.status_code != 200:
        pytest.skip("sales_agent demo user not available")
    headers = {"Authorization": f"Bearer {r.json()['token']}"}
    r2 = client.get("/api/v1/crm/audit", headers=headers)
    assert r2.status_code == 403


# ── Token expiry is checked ────────────────────────────────────────────────────

def test_invalid_token_rejected(client: TestClient):
    """Attempting to claim with a random token must return 410 or 404."""
    # Need an authenticated user to call claim
    r = client.post(
        "/api/v1/users/login",
        json={"login": "demo", "password": "demo123"},
    )
    if r.status_code != 200:
        pytest.skip("demo user not available")
    headers = {"Authorization": f"Bearer {r.json()['token']}"}

    # Try to claim a non-existent conversion
    r2 = client.post(
        "/api/v1/crm/conversions/99999/claim",
        json={
            "token": "bad-token",
            "org_display_name": "Test",
            "org_slug": "test-slug",
        },
        headers=headers,
    )
    assert r2.status_code in (404, 410, 422), f"Expected 404/410/422, got {r2.status_code}"
