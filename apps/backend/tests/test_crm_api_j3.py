"""Test J3: CRM API endpoints — Spec 017.

Uses the session-scoped TestClient from conftest.
Sales users are seeded via platform_rbac assign_role + login.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def sales_agent_headers(client: TestClient) -> dict[str, str]:
    """Login as seeded demo sales_agent@voxmetrik.io."""
    response = client.post(
        "/api/v1/users/login",
        json={"login": "sales_agent@voxmetrik.io", "password": "demo123", "remember": True},
    )
    if response.status_code != 200:
        pytest.skip(f"sales_agent demo user not seeded (status={response.status_code})")
    return {"Authorization": f"Bearer {response.json()['token']}"}


@pytest.fixture(scope="module")
def sales_manager_headers(client: TestClient) -> dict[str, str]:
    """Login as seeded demo sales_manager@voxmetrik.io."""
    response = client.post(
        "/api/v1/users/login",
        json={"login": "sales_manager@voxmetrik.io", "password": "demo123", "remember": True},
    )
    if response.status_code != 200:
        pytest.skip(f"sales_manager demo user not seeded (status={response.status_code})")
    return {"Authorization": f"Bearer {response.json()['token']}"}


# ── Prospect endpoints ────────────────────────────────────────────────────────

def test_create_prospect_as_agent(client: TestClient, sales_agent_headers):
    r = client.post(
        "/api/v1/crm/prospects",
        json={"display_name": "API Test Corp", "company_name": "API Test Ltd", "email": "apitest@test.io"},
        headers=sales_agent_headers,
    )
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["status"] == "new"
    assert data["display_name"] == "API Test Corp"


def test_list_prospects_as_agent(client: TestClient, sales_agent_headers):
    r = client.get("/api/v1/crm/prospects", headers=sales_agent_headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "items" in data
    assert "total" in data


def test_get_prospect_as_agent(client: TestClient, sales_agent_headers):
    # Create first
    r = client.post(
        "/api/v1/crm/prospects",
        json={"display_name": "GetTest Prospect"},
        headers=sales_agent_headers,
    )
    pid = r.json()["id"]
    r2 = client.get(f"/api/v1/crm/prospects/{pid}", headers=sales_agent_headers)
    assert r2.status_code == 200
    assert r2.json()["id"] == pid


def test_update_prospect_as_agent(client: TestClient, sales_agent_headers):
    r = client.post(
        "/api/v1/crm/prospects",
        json={"display_name": "UpdateTest"},
        headers=sales_agent_headers,
    )
    pid = r.json()["id"]
    r2 = client.patch(
        f"/api/v1/crm/prospects/{pid}",
        json={"display_name": "UpdatedName"},
        headers=sales_agent_headers,
    )
    assert r2.status_code == 200
    assert r2.json()["display_name"] == "UpdatedName"


def test_prospect_status_transition(client: TestClient, sales_agent_headers):
    r = client.post("/api/v1/crm/prospects", json={"display_name": "StatusTest"}, headers=sales_agent_headers)
    pid = r.json()["id"]
    r2 = client.post(f"/api/v1/crm/prospects/{pid}/status", json={"status": "contacted"}, headers=sales_agent_headers)
    assert r2.status_code == 200
    assert r2.json()["status"] == "contacted"


# ── Opportunity endpoints ─────────────────────────────────────────────────────

def test_create_opportunity_as_agent(client: TestClient, sales_agent_headers):
    # First create a prospect
    pr = client.post("/api/v1/crm/prospects", json={"display_name": "OppProspect"}, headers=sales_agent_headers)
    pid = pr.json()["id"]

    r = client.post(
        "/api/v1/crm/opportunities",
        json={"prospect_id": pid, "name": "API Opp Deal", "probability": 30, "currency": "USD"},
        headers=sales_agent_headers,
    )
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["stage"] == "qualification"
    assert data["probability"] == 30


def test_advance_opportunity_stage_as_agent(client: TestClient, sales_agent_headers):
    pr = client.post("/api/v1/crm/prospects", json={"display_name": "StageTest Prospect"}, headers=sales_agent_headers)
    pid = pr.json()["id"]
    or_ = client.post("/api/v1/crm/opportunities", json={"prospect_id": pid, "name": "StageTest Opp"}, headers=sales_agent_headers)
    oid = or_.json()["id"]
    r = client.post(f"/api/v1/crm/opportunities/{oid}/stage", json={"stage": "proposal"}, headers=sales_agent_headers)
    assert r.status_code == 200
    assert r.json()["stage"] == "proposal"


# ── Activity endpoints ────────────────────────────────────────────────────────

def test_create_activity_as_agent(client: TestClient, sales_agent_headers):
    pr = client.post("/api/v1/crm/prospects", json={"display_name": "ActProspect"}, headers=sales_agent_headers)
    pid = pr.json()["id"]
    r = client.post(
        "/api/v1/crm/activities",
        json={"activity_type": "call", "subject": "First Call", "prospect_id": pid},
        headers=sales_agent_headers,
    )
    assert r.status_code == 201, r.text
    assert r.json()["activity_type"] == "call"


# ── Quotation endpoints ───────────────────────────────────────────────────────

def test_create_quotation_as_agent(client: TestClient, sales_agent_headers):
    pr = client.post("/api/v1/crm/prospects", json={"display_name": "QuotProspect"}, headers=sales_agent_headers)
    pid = pr.json()["id"]
    or_ = client.post("/api/v1/crm/opportunities", json={"prospect_id": pid, "name": "Quot Opp"}, headers=sales_agent_headers)
    oid = or_.json()["id"]
    r = client.post("/api/v1/crm/quotations", json={"opportunity_id": oid, "currency": "USD"}, headers=sales_agent_headers)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["currency"] == "USD"
    assert data["status"] == "draft"


def test_create_quotation_version(client: TestClient, sales_agent_headers):
    pr = client.post("/api/v1/crm/prospects", json={"display_name": "VerProspect"}, headers=sales_agent_headers)
    pid = pr.json()["id"]
    or_ = client.post("/api/v1/crm/opportunities", json={"prospect_id": pid, "name": "Ver Opp"}, headers=sales_agent_headers)
    oid = or_.json()["id"]
    qr = client.post("/api/v1/crm/quotations", json={"opportunity_id": oid, "currency": "EUR"}, headers=sales_agent_headers)
    qid = qr.json()["id"]
    r = client.post(f"/api/v1/crm/quotations/{qid}/versions", json={}, headers=sales_agent_headers)
    assert r.status_code == 201, r.text
    assert r.json()["version_no"] == 1


# ── Manager approval endpoint ─────────────────────────────────────────────────

def test_manager_can_approve_discount(client: TestClient, sales_agent_headers, sales_manager_headers):
    pr = client.post("/api/v1/crm/prospects", json={"display_name": "ApprovalProspect"}, headers=sales_agent_headers)
    pid = pr.json()["id"]
    or_ = client.post("/api/v1/crm/opportunities", json={"prospect_id": pid, "name": "Approval Opp"}, headers=sales_agent_headers)
    oid = or_.json()["id"]
    qr = client.post("/api/v1/crm/quotations", json={"opportunity_id": oid, "currency": "USD"}, headers=sales_agent_headers)
    qid = qr.json()["id"]
    vr = client.post(f"/api/v1/crm/quotations/{qid}/versions", json={}, headers=sales_agent_headers)
    vid = vr.json()["id"]

    # Agent requests approval
    ar = client.post(
        f"/api/v1/crm/quotation-versions/{vid}/request-approval",
        json={"reason": "10% discount for VIP"},
        headers=sales_agent_headers,
    )
    assert ar.status_code == 201, ar.text
    approval_id = ar.json()["id"]

    # Manager approves
    approved = client.post(
        f"/api/v1/crm/approvals/{approval_id}/approve",
        json={"review_note": "Approved for VIP"},
        headers=sales_manager_headers,
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "approved"


# ── Contact endpoints ─────────────────────────────────────────────────────────

def test_create_and_link_contact(client: TestClient, sales_agent_headers):
    cr = client.post(
        "/api/v1/crm/contacts",
        json={"full_name": "John Doe", "email": "john@acme.io"},
        headers=sales_agent_headers,
    )
    assert cr.status_code == 201, cr.text
    cid = cr.json()["id"]

    pr = client.post("/api/v1/crm/prospects", json={"display_name": "ContactLink Prospect"}, headers=sales_agent_headers)
    pid = pr.json()["id"]

    lr = client.post(
        f"/api/v1/crm/prospects/{pid}/contacts",
        json={"contact_id": cid, "is_primary": True},
        headers=sales_agent_headers,
    )
    assert lr.status_code == 200, lr.text
    assert lr.json()["is_primary"] is True


# ── Audit endpoint ────────────────────────────────────────────────────────────

def test_audit_accessible_to_manager(client: TestClient, sales_manager_headers):
    r = client.get("/api/v1/crm/audit", headers=sales_manager_headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "items" in data


def test_audit_forbidden_to_agent(client: TestClient, sales_agent_headers):
    r = client.get("/api/v1/crm/audit", headers=sales_agent_headers)
    assert r.status_code == 403, r.text
