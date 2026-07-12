"""Test L3: Billing API endpoints — Spec 019.

Uses the session-scoped TestClient from conftest.
Admin user acts as org owner with all billing permissions.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def billing_admin(client: TestClient) -> dict:
    """Login as admin, ensure org + billing profile exist, return context."""
    resp = client.post(
        "/api/v1/users/login",
        json={"login": "admin", "password": "admin123", "remember": True},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    body = resp.json()
    token = body["token"]
    user_id = body.get("id")
    if user_id is None and isinstance(body.get("user"), dict):
        user_id = body["user"].get("id")
    if user_id is None:
        me = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        me_body = me.json()
        user_id = me_body.get("id") or (me_body.get("user") or {}).get("id")
    assert user_id is not None

    headers = {"Authorization": f"Bearer {token}"}

    # Create org for billing tests
    from app.core.database import using_write_conn
    from app.core.time_util import utc_now

    with using_write_conn() as conn:
        now = utc_now()
        existing = conn.execute(
            "SELECT id FROM app_organization WHERE slug = 'billing-test-org-l3'"
        ).fetchone()
        if not existing:
            conn.execute("""
                INSERT INTO app_organization
                    (id, display_name, legal_name, slug, organization_type, country_code,
                     timezone, default_currency, status, created_by, created_at, updated_at)
                VALUES (200, 'Billing Test Org L3', NULL, 'billing-test-org-l3', 'label', 'US',
                        'UTC', 'USD', 'active', ?, ?, ?)
            """, [int(user_id), now, now])
        # Add user as owner
        m_existing = conn.execute(
            "SELECT id FROM app_organization_member WHERE organization_id = 200 AND user_id = ?",
            [int(user_id)],
        ).fetchone()
        if not m_existing:
            next_mid = int(conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM app_organization_member").fetchone()[0])
            conn.execute("""
                INSERT INTO app_organization_member
                    (id, organization_id, user_id, status, created_by, created_at, updated_at)
                VALUES (?, 200, ?, 'active', ?, ?, ?)
            """, [next_mid, int(user_id), int(user_id), now, now])

            owner_role_id = conn.execute(
                "SELECT id FROM app_business_role WHERE code = 'owner'"
            ).fetchone()[0]
            next_mrid = int(conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM app_member_role").fetchone()[0])
            conn.execute("""
                INSERT INTO app_member_role (id, member_id, role_id, status, assigned_by, assigned_at)
                VALUES (?, ?, ?, 'active', ?, ?)
            """, [next_mrid, next_mid, int(owner_role_id), int(user_id), now])

    return {"headers": headers, "user_id": user_id, "org_id": 200,
            "org_headers": {**headers, "X-Organization-Id": "200"}}


@pytest.fixture(scope="module")
def profile_id(client: TestClient, billing_admin) -> int:
    """Create billing profile, return id."""
    r = client.post(
        "/api/v1/billing/profile",
        json={"default_currency": "USD", "legal_name": "Billing Test Org L3 LLC"},
        headers=billing_admin["org_headers"],
    )
    if r.status_code == 409:
        r2 = client.get("/api/v1/billing/profile", headers=billing_admin["org_headers"])
        return int(r2.json()["id"])
    assert r.status_code == 201, r.text
    return int(r.json()["id"])


@pytest.fixture(scope="module")
def issued_invoice(client: TestClient, billing_admin, profile_id) -> dict:
    """Create + issue an invoice with one item."""
    r = client.post(
        "/api/v1/billing/invoices",
        json={"billing_profile_id": profile_id, "notes": "L3 test invoice"},
        headers=billing_admin["org_headers"],
    )
    assert r.status_code == 201, r.text
    inv = r.json()
    inv_id = inv["id"]

    r2 = client.post(
        f"/api/v1/billing/invoices/{inv_id}/items",
        json={"description": "L3 service", "quantity": "1", "unit_price": "150.00"},
        headers=billing_admin["org_headers"],
    )
    assert r2.status_code == 201, r2.text

    r3 = client.post(
        f"/api/v1/billing/invoices/{inv_id}/issue",
        headers=billing_admin["org_headers"],
    )
    assert r3.status_code == 200, r3.text
    return r3.json()


# ── Profile endpoints ──────────────────────────────────────────────────────────

def test_get_billing_profile(client: TestClient, billing_admin, profile_id):
    r = client.get("/api/v1/billing/profile", headers=billing_admin["org_headers"])
    assert r.status_code == 200, r.text
    assert r.json()["id"] == profile_id


def test_update_billing_profile(client: TestClient, billing_admin):
    r = client.patch(
        "/api/v1/billing/profile",
        json={"email": "updated@testorg.com"},
        headers=billing_admin["org_headers"],
    )
    assert r.status_code == 200, r.text


# ── Invoice endpoints ──────────────────────────────────────────────────────────

def test_list_invoices(client: TestClient, billing_admin):
    r = client.get("/api/v1/billing/invoices", headers=billing_admin["org_headers"])
    assert r.status_code == 200, r.text
    data = r.json()
    assert "items" in data
    assert "total" in data


def test_get_invoice(client: TestClient, billing_admin, issued_invoice):
    r = client.get(
        f"/api/v1/billing/invoices/{issued_invoice['id']}",
        headers=billing_admin["org_headers"],
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "issued"


def test_list_invoice_items(client: TestClient, billing_admin, issued_invoice):
    r = client.get(
        f"/api/v1/billing/invoices/{issued_invoice['id']}/items",
        headers=billing_admin["org_headers"],
    )
    assert r.status_code == 200, r.text
    assert len(r.json()) >= 1


# ── Payment attempt endpoints ──────────────────────────────────────────────────

def test_create_payment_attempt_idempotent(client: TestClient, billing_admin, issued_invoice):
    body = {
        "invoice_id": issued_invoice["id"],
        "provider_code": "academic_mock",
        "idempotency_key": "l3-api-test-idem-001",
        "amount": "150.00",
        "currency": "USD",
    }
    r1 = client.post("/api/v1/billing/payment-attempts", json=body, headers=billing_admin["org_headers"])
    assert r1.status_code == 201, r1.text
    r2 = client.post("/api/v1/billing/payment-attempts", json=body, headers=billing_admin["org_headers"])
    assert r2.status_code == 201, r2.text
    assert r1.json()["id"] == r2.json()["id"]


def test_payment_attempt_is_mock_flagged(client: TestClient, billing_admin, issued_invoice):
    r = client.get("/api/v1/billing/payment-attempts", headers=billing_admin["org_headers"])
    assert r.status_code == 200
    items = r.json().get("items", [])
    mock_items = [a for a in items if a.get("provider_code") == "academic_mock"]
    for a in mock_items:
        assert a["is_mock"] is True, "academic_mock attempt must have is_mock=true"


# ── Manual transfer ────────────────────────────────────────────────────────────

def test_manual_transfer(client: TestClient, billing_admin, profile_id):
    # Create a fresh invoice for manual transfer test
    r = client.post(
        "/api/v1/billing/invoices",
        json={"billing_profile_id": profile_id},
        headers=billing_admin["org_headers"],
    )
    assert r.status_code == 201
    inv_id = r.json()["id"]

    r2 = client.post(
        f"/api/v1/billing/invoices/{inv_id}/items",
        json={"description": "Manual test", "quantity": "1", "unit_price": "300.00"},
        headers=billing_admin["org_headers"],
    )
    assert r2.status_code == 201

    r3 = client.post(
        f"/api/v1/billing/invoices/{inv_id}/issue",
        headers=billing_admin["org_headers"],
    )
    assert r3.status_code == 200

    r4 = client.post(
        "/api/v1/billing/manual-transfer",
        json={"invoice_id": inv_id, "amount": "300.00", "currency": "USD", "notes": "Wire ref #L3"},
        headers=billing_admin["org_headers"],
    )
    assert r4.status_code == 201, r4.text
    assert r4.json()["status"] == "recorded"


# ── Ledger endpoint ────────────────────────────────────────────────────────────

def test_get_ledger(client: TestClient, billing_admin):
    r = client.get("/api/v1/billing/ledger", headers=billing_admin["org_headers"])
    assert r.status_code == 200, r.text
    data = r.json()
    assert "items" in data
    assert "total" in data


# ── Provider event endpoint ────────────────────────────────────────────────────

def test_provider_event_idempotent(client: TestClient):
    body = {
        "provider_code": "academic_mock",
        "provider_event_id": "l3-evt-test-001",
        "event_type": "payment.succeeded",
        "payload": '{"amount": 150}',
    }
    r1 = client.post("/api/v1/billing/provider-events", json=body)
    assert r1.status_code == 201, r1.text
    r2 = client.post("/api/v1/billing/provider-events", json=body)
    assert r2.status_code == 201, r2.text
    assert r1.json()["id"] == r2.json()["id"]


# ── 403 without org header ─────────────────────────────────────────────────────

def test_billing_profile_missing_org_header(client: TestClient, billing_admin):
    r = client.get(
        "/api/v1/billing/profile",
        headers={"Authorization": billing_admin["headers"]["Authorization"]},
    )
    assert r.status_code in (400, 401, 403), r.text
