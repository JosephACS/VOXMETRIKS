"""Test N3: Catalog rights API endpoints — Spec 021.

Uses the session-scoped TestClient from conftest.
Admin user acts as org owner with all rights.* permissions.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def rights_admin(client: TestClient) -> dict:
    """Login as admin, ensure org + owner membership exist, return context."""
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

    from app.core.database import using_write_conn
    from app.core.time_util import utc_now

    with using_write_conn() as conn:
        now = utc_now()
        existing = conn.execute(
            "SELECT id FROM app_organization WHERE slug = 'catalog-rights-test-org-n3'"
        ).fetchone()
        if not existing:
            conn.execute("""
                INSERT INTO app_organization
                    (id, display_name, legal_name, slug, organization_type, country_code,
                     timezone, default_currency, status, created_by, created_at, updated_at)
                VALUES (230, 'Catalog Rights Test Org N3', NULL, 'catalog-rights-test-org-n3',
                        'label', 'US', 'UTC', 'USD', 'active', ?, ?, ?)
            """, [int(user_id), now, now])
        m_existing = conn.execute(
            "SELECT id FROM app_organization_member WHERE organization_id = 230 AND user_id = ?",
            [int(user_id)],
        ).fetchone()
        if not m_existing:
            next_mid = int(conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM app_organization_member").fetchone()[0])
            conn.execute("""
                INSERT INTO app_organization_member
                    (id, organization_id, user_id, status, created_by, created_at, updated_at)
                VALUES (?, 230, ?, 'active', ?, ?, ?)
            """, [next_mid, int(user_id), int(user_id), now, now])

            owner_role_id = conn.execute(
                "SELECT id FROM app_business_role WHERE code = 'owner'"
            ).fetchone()[0]
            next_mrid = int(conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM app_member_role").fetchone()[0])
            conn.execute("""
                INSERT INTO app_member_role (id, member_id, role_id, status, assigned_by, assigned_at)
                VALUES (?, ?, ?, 'active', ?, ?)
            """, [next_mrid, next_mid, int(owner_role_id), int(user_id), now])

    return {"headers": headers, "user_id": user_id, "org_id": 230,
            "org_headers": {**headers, "X-Organization-Id": "230"}}


@pytest.fixture()
def asset_id(client: TestClient, rights_admin) -> int:
    r = client.post(
        "/api/v1/catalog-rights/assets",
        json={"title": f"N3 API Asset {uuid.uuid4().hex[:8]}"},
        headers=rights_admin["org_headers"],
    )
    assert r.status_code == 201, r.text
    return int(r.json()["id"])


@pytest.fixture()
def contract_id(client: TestClient, rights_admin, asset_id) -> int:
    r = client.post(
        "/api/v1/catalog-rights/contracts",
        json={"asset_id": asset_id, "rights_type": "master", "valid_from": "2024-01-01"},
        headers=rights_admin["org_headers"],
    )
    assert r.status_code == 201, r.text
    return int(r.json()["id"])


# ── Assets ────────────────────────────────────────────────────────────────────

def test_register_asset(client: TestClient, rights_admin):
    r = client.post(
        "/api/v1/catalog-rights/assets",
        json={"title": f"Create Test {uuid.uuid4().hex[:8]}"},
        headers=rights_admin["org_headers"],
    )
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "active"


def test_list_and_get_asset(client: TestClient, rights_admin, asset_id):
    r = client.get("/api/v1/catalog-rights/assets", headers=rights_admin["org_headers"])
    assert r.status_code == 200, r.text
    data = r.json()
    assert "items" in data
    assert any(a["id"] == asset_id for a in data["items"])

    r2 = client.get(f"/api/v1/catalog-rights/assets/{asset_id}", headers=rights_admin["org_headers"])
    assert r2.status_code == 200, r2.text
    assert r2.json()["id"] == asset_id


def test_get_asset_not_found(client: TestClient, rights_admin):
    r = client.get("/api/v1/catalog-rights/assets/999999", headers=rights_admin["org_headers"])
    assert r.status_code == 404, r.text


def test_link_warehouse_track(client: TestClient, rights_admin, asset_id):
    r = client.post(
        f"/api/v1/catalog-rights/assets/{asset_id}/link-warehouse-track",
        json={"warehouse_track_id": 1},
        headers=rights_admin["org_headers"],
    )
    assert r.status_code == 200, r.text
    assert r.json()["warehouse_track_id"] == 1


def test_link_warehouse_track_not_found(client: TestClient, rights_admin, asset_id):
    r = client.post(
        f"/api/v1/catalog-rights/assets/{asset_id}/link-warehouse-track",
        json={"warehouse_track_id": 987654},
        headers=rights_admin["org_headers"],
    )
    assert r.status_code == 404, r.text


def test_register_ownership(client: TestClient, rights_admin, asset_id):
    r = client.post(
        f"/api/v1/catalog-rights/assets/{asset_id}/ownership",
        json={"ownership_type": "label", "owner_organization_id": rights_admin["org_id"]},
        headers=rights_admin["org_headers"],
    )
    assert r.status_code == 201, r.text
    assert r.json()["ownership_type"] == "label"

    r2 = client.get(
        f"/api/v1/catalog-rights/assets/{asset_id}/ownership", headers=rights_admin["org_headers"]
    )
    assert r2.status_code == 200
    assert len(r2.json()) >= 1


# ── Releases ──────────────────────────────────────────────────────────────────

def test_create_and_list_release(client: TestClient, rights_admin):
    r = client.post(
        "/api/v1/catalog-rights/releases",
        json={"title": f"Release {uuid.uuid4().hex[:8]}"},
        headers=rights_admin["org_headers"],
    )
    assert r.status_code == 201, r.text
    release_id = r.json()["id"]

    r2 = client.get("/api/v1/catalog-rights/releases", headers=rights_admin["org_headers"])
    assert r2.status_code == 200
    assert any(rel["id"] == release_id for rel in r2.json()["items"])


# ── Contracts ─────────────────────────────────────────────────────────────────

def test_create_and_get_contract(client: TestClient, rights_admin, asset_id):
    r = client.post(
        "/api/v1/catalog-rights/contracts",
        json={"asset_id": asset_id, "rights_type": "publishing", "valid_from": "2024-01-01"},
        headers=rights_admin["org_headers"],
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "draft"

    r2 = client.get(f"/api/v1/catalog-rights/contracts/{body['id']}", headers=rights_admin["org_headers"])
    assert r2.status_code == 200
    assert r2.json()["rights_type"] == "publishing"


def test_list_contracts_filtered_by_asset(client: TestClient, rights_admin, asset_id, contract_id):
    r = client.get(
        "/api/v1/catalog-rights/contracts", params={"asset_id": asset_id},
        headers=rights_admin["org_headers"],
    )
    assert r.status_code == 200, r.text
    assert any(c["id"] == contract_id for c in r.json()["items"])


def test_archive_contract(client: TestClient, rights_admin, asset_id):
    r = client.post(
        "/api/v1/catalog-rights/contracts",
        json={"asset_id": asset_id, "rights_type": "other", "valid_from": "2024-01-01"},
        headers=rights_admin["org_headers"],
    )
    cid = r.json()["id"]
    r2 = client.post(
        f"/api/v1/catalog-rights/contracts/{cid}/archive", json={"reason": "ended"},
        headers=rights_admin["org_headers"],
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["status"] == "archived"

    r3 = client.get(f"/api/v1/catalog-rights/contracts/{cid}/history", headers=rights_admin["org_headers"])
    assert r3.status_code == 200
    to_statuses = [h["to_status"] for h in r3.json()]
    assert to_statuses == ["draft", "archived"]


# ── Contract parties / percentages ───────────────────────────────────────────

def test_add_contract_party_and_percentage_validation(client: TestClient, rights_admin, contract_id):
    r_bad = client.post(
        f"/api/v1/catalog-rights/contracts/{contract_id}/parties",
        json={"party_name": "Bad", "ownership_percentage": 150},
        headers=rights_admin["org_headers"],
    )
    assert r_bad.status_code == 422, r_bad.text

    r = client.post(
        f"/api/v1/catalog-rights/contracts/{contract_id}/parties",
        json={"party_name": "Good Party", "ownership_percentage": 55, "party_type": "organization"},
        headers=rights_admin["org_headers"],
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["party"]["ownership_percentage"] == 55
    assert body["conflicts_opened"] == []

    r2 = client.get(
        f"/api/v1/catalog-rights/contracts/{contract_id}/parties", headers=rights_admin["org_headers"]
    )
    assert r2.status_code == 200
    assert len(r2.json()) >= 1


def test_overlapping_contracts_open_conflict_via_api(client: TestClient, rights_admin, asset_id):
    r1 = client.post(
        "/api/v1/catalog-rights/contracts",
        json={"asset_id": asset_id, "rights_type": "master", "valid_from": "2030-01-01",
              "valid_to": "2030-12-31"},
        headers=rights_admin["org_headers"],
    )
    r2 = client.post(
        "/api/v1/catalog-rights/contracts",
        json={"asset_id": asset_id, "rights_type": "master", "valid_from": "2030-06-01",
              "valid_to": "2031-06-01"},
        headers=rights_admin["org_headers"],
    )
    c1, c2 = r1.json()["id"], r2.json()["id"]

    for cid in (c1, c2):
        client.post(
            f"/api/v1/catalog-rights/contracts/{cid}/territories",
            json={"territories": [{"territory_code": "IT", "territory_name": "Italy"}]},
            headers=rights_admin["org_headers"],
        )

    client.post(
        f"/api/v1/catalog-rights/contracts/{c1}/parties",
        json={"party_name": "IT Party 1", "ownership_percentage": 70},
        headers=rights_admin["org_headers"],
    )
    r_party2 = client.post(
        f"/api/v1/catalog-rights/contracts/{c2}/parties",
        json={"party_name": "IT Party 2", "ownership_percentage": 70},
        headers=rights_admin["org_headers"],
    )
    assert r_party2.status_code == 201
    conflicts = r_party2.json()["conflicts_opened"]
    assert len(conflicts) == 1
    assert conflicts[0]["territory_code"] == "IT"

    r_conflicts = client.get(
        "/api/v1/catalog-rights/conflicts", params={"asset_id": asset_id},
        headers=rights_admin["org_headers"],
    )
    assert r_conflicts.status_code == 200
    assert any(c["territory_code"] == "IT" and c["status"] == "open" for c in r_conflicts.json())

    conflict_id = conflicts[0]["id"]
    r_resolve = client.post(
        f"/api/v1/catalog-rights/conflicts/{conflict_id}/resolve",
        json={"resolution": "resolved", "notes": "renegotiated"},
        headers=rights_admin["org_headers"],
    )
    assert r_resolve.status_code == 200, r_resolve.text
    assert r_resolve.json()["status"] == "resolved"


def test_open_conflict_manual(client: TestClient, rights_admin, asset_id):
    r = client.post(
        "/api/v1/catalog-rights/conflicts",
        json={"asset_id": asset_id, "rights_type": "other", "territory_code": "SE",
              "details": "manual review needed"},
        headers=rights_admin["org_headers"],
    )
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "open"


def test_detect_overlap_endpoint(client: TestClient, rights_admin, asset_id):
    r = client.post(
        f"/api/v1/catalog-rights/assets/{asset_id}/detect-overlap",
        json={"rights_type": "master"},
        headers=rights_admin["org_headers"],
    )
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)


# ── Territories / authorized uses ────────────────────────────────────────────

def test_set_and_list_territories(client: TestClient, rights_admin, contract_id):
    r = client.post(
        f"/api/v1/catalog-rights/contracts/{contract_id}/territories",
        json={"territories": [{"territory_code": "US", "territory_name": "United States"}]},
        headers=rights_admin["org_headers"],
    )
    assert r.status_code == 200, r.text
    assert len(r.json()["territories"]) == 1

    r2 = client.get(
        f"/api/v1/catalog-rights/contracts/{contract_id}/territories", headers=rights_admin["org_headers"]
    )
    assert r2.status_code == 200
    assert any(t["territory_code"] == "US" for t in r2.json())


def test_set_and_list_authorized_uses(client: TestClient, rights_admin, contract_id):
    r = client.post(
        f"/api/v1/catalog-rights/contracts/{contract_id}/authorized-uses",
        json={"uses": [{"use_code": "streaming", "description": "DSPs"}]},
        headers=rights_admin["org_headers"],
    )
    assert r.status_code == 200, r.text
    assert len(r.json()) == 1

    r2 = client.get(
        f"/api/v1/catalog-rights/contracts/{contract_id}/authorized-uses",
        headers=rights_admin["org_headers"],
    )
    assert r2.status_code == 200
    assert any(u["use_code"] == "streaming" for u in r2.json())


# ── Approvals ─────────────────────────────────────────────────────────────────

def test_submit_and_approve_contract(client: TestClient, rights_admin, contract_id):
    r = client.post(
        f"/api/v1/catalog-rights/contracts/{contract_id}/submit-for-approval",
        headers=rights_admin["org_headers"],
    )
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "pending"

    r2 = client.post(
        f"/api/v1/catalog-rights/contracts/{contract_id}/approve",
        json={"approved": True, "notes": "approved via API test"},
        headers=rights_admin["org_headers"],
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["status"] == "approved"

    r3 = client.get(f"/api/v1/catalog-rights/contracts/{contract_id}", headers=rights_admin["org_headers"])
    assert r3.status_code == 200
    assert r3.json()["status"] == "active"

    r4 = client.get(
        f"/api/v1/catalog-rights/contracts/{contract_id}/approvals", headers=rights_admin["org_headers"]
    )
    assert r4.status_code == 200
    assert len(r4.json()) >= 1


# ── Coverage ──────────────────────────────────────────────────────────────────

def test_query_coverage(client: TestClient, rights_admin, asset_id, contract_id):
    client.post(
        f"/api/v1/catalog-rights/contracts/{contract_id}/parties",
        json={"party_name": "Coverage Party", "ownership_percentage": 30},
        headers=rights_admin["org_headers"],
    )
    r = client.get(
        f"/api/v1/catalog-rights/assets/{asset_id}/coverage", headers=rights_admin["org_headers"]
    )
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)


# ── Missing org header ────────────────────────────────────────────────────────

def test_missing_org_header(client: TestClient, rights_admin):
    r = client.get(
        "/api/v1/catalog-rights/assets",
        headers={"Authorization": rights_admin["headers"]["Authorization"]},
    )
    assert r.status_code in (400, 401, 403), r.text
