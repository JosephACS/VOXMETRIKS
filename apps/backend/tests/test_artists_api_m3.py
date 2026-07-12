"""Test M3: Artists API endpoints — Spec 020.

Uses the session-scoped TestClient from conftest.
Admin user acts as org owner with all artist permissions.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def artists_admin(client: TestClient) -> dict:
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
            "SELECT id FROM app_organization WHERE slug = 'artists-test-org-m3'"
        ).fetchone()
        if not existing:
            conn.execute("""
                INSERT INTO app_organization
                    (id, display_name, legal_name, slug, organization_type, country_code,
                     timezone, default_currency, status, created_by, created_at, updated_at)
                VALUES (210, 'Artists Test Org M3', NULL, 'artists-test-org-m3', 'label', 'US',
                        'UTC', 'USD', 'active', ?, ?, ?)
            """, [int(user_id), now, now])
        m_existing = conn.execute(
            "SELECT id FROM app_organization_member WHERE organization_id = 210 AND user_id = ?",
            [int(user_id)],
        ).fetchone()
        if not m_existing:
            next_mid = int(conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM app_organization_member").fetchone()[0])
            conn.execute("""
                INSERT INTO app_organization_member
                    (id, organization_id, user_id, status, created_by, created_at, updated_at)
                VALUES (?, 210, ?, 'active', ?, ?, ?)
            """, [next_mid, int(user_id), int(user_id), now, now])

            owner_role_id = conn.execute(
                "SELECT id FROM app_business_role WHERE code = 'owner'"
            ).fetchone()[0]
            next_mrid = int(conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM app_member_role").fetchone()[0])
            conn.execute("""
                INSERT INTO app_member_role (id, member_id, role_id, status, assigned_by, assigned_at)
                VALUES (?, ?, ?, 'active', ?, ?)
            """, [next_mrid, next_mid, int(owner_role_id), int(user_id), now])

    return {"headers": headers, "user_id": user_id, "org_id": 210,
            "org_headers": {**headers, "X-Organization-Id": "210"}}


@pytest.fixture()
def artist_id(client: TestClient, artists_admin) -> int:
    """Create a fresh artist profile per test, return id."""
    r = client.post(
        "/api/v1/artists",
        json={"display_name": f"M3 API Artist {uuid.uuid4().hex[:8]}"},
        headers=artists_admin["org_headers"],
    )
    assert r.status_code == 201, r.text
    return int(r.json()["id"])


# ── Create / list / get ────────────────────────────────────────────────────────

def test_create_artist_profile(client: TestClient, artists_admin):
    r = client.post(
        "/api/v1/artists",
        json={"display_name": f"Create Test {uuid.uuid4().hex[:8]}", "legal_name": "LLC"},
        headers=artists_admin["org_headers"],
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "draft"


def test_list_artists(client: TestClient, artists_admin, artist_id):
    r = client.get("/api/v1/artists", headers=artists_admin["org_headers"])
    assert r.status_code == 200, r.text
    data = r.json()
    assert "items" in data
    assert "total" in data
    assert any(a["id"] == artist_id for a in data["items"])


def test_get_artist(client: TestClient, artists_admin, artist_id):
    r = client.get(f"/api/v1/artists/{artist_id}", headers=artists_admin["org_headers"])
    assert r.status_code == 200, r.text
    assert r.json()["id"] == artist_id


def test_get_artist_not_found(client: TestClient, artists_admin):
    r = client.get("/api/v1/artists/999999", headers=artists_admin["org_headers"])
    assert r.status_code == 404, r.text


def test_duplicate_artist_name_rejected(client: TestClient, artists_admin):
    name = f"Duplicate Check {uuid.uuid4().hex[:8]}"
    r1 = client.post(
        "/api/v1/artists", json={"display_name": name},
        headers=artists_admin["org_headers"],
    )
    assert r1.status_code == 201
    r2 = client.post(
        "/api/v1/artists", json={"display_name": name},
        headers=artists_admin["org_headers"],
    )
    assert r2.status_code == 409, r2.text


# ── Status transitions ─────────────────────────────────────────────────────────

def test_activate_and_deactivate_artist(client: TestClient, artists_admin, artist_id):
    r1 = client.post(
        f"/api/v1/artists/{artist_id}/activate", json={},
        headers=artists_admin["org_headers"],
    )
    assert r1.status_code == 200, r1.text
    assert r1.json()["status"] == "active"

    r2 = client.post(
        f"/api/v1/artists/{artist_id}/deactivate", json={"reason": "hiatus"},
        headers=artists_admin["org_headers"],
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["status"] == "inactive"


def test_archive_artist(client: TestClient, artists_admin, artist_id):
    r = client.post(
        f"/api/v1/artists/{artist_id}/archive", json={"reason": "retired"},
        headers=artists_admin["org_headers"],
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "archived"

    r2 = client.post(
        f"/api/v1/artists/{artist_id}/activate", json={},
        headers=artists_admin["org_headers"],
    )
    assert r2.status_code == 422, r2.text


def test_get_artist_history(client: TestClient, artists_admin, artist_id):
    client.post(f"/api/v1/artists/{artist_id}/activate", json={}, headers=artists_admin["org_headers"])
    r = client.get(f"/api/v1/artists/{artist_id}/history", headers=artists_admin["org_headers"])
    assert r.status_code == 200, r.text
    history = r.json()
    assert len(history) >= 2
    assert history[0]["to_status"] == "draft"


# ── Organization links ──────────────────────────────────────────────────────────

def test_link_organization(client: TestClient, artists_admin, artist_id):
    r = client.post(
        f"/api/v1/artists/{artist_id}/organizations",
        json={"target_organization_id": 999888, "relationship_role": "licensed"},
        headers=artists_admin["org_headers"],
    )
    assert r.status_code == 201, r.text
    assert r.json()["relationship_role"] == "licensed"

    r2 = client.get(
        f"/api/v1/artists/{artist_id}/organizations",
        headers=artists_admin["org_headers"],
    )
    assert r2.status_code == 200, r2.text
    assert any(o["organization_id"] == 999888 for o in r2.json())


# ── Assignments ──────────────────────────────────────────────────────────────────

def test_assign_manager_and_end(client: TestClient, artists_admin, artist_id):
    r = client.post(
        f"/api/v1/artists/{artist_id}/assignments",
        json={"user_id": 777, "role": "manager"},
        headers=artists_admin["org_headers"],
    )
    assert r.status_code == 201, r.text
    assignment_id = r.json()["id"]

    r2 = client.get(
        f"/api/v1/artists/{artist_id}/assignments",
        headers=artists_admin["org_headers"],
    )
    assert r2.status_code == 200
    assert any(a["id"] == assignment_id for a in r2.json())

    r3 = client.post(
        f"/api/v1/artists/{artist_id}/assignments/{assignment_id}/end",
        headers=artists_admin["org_headers"],
    )
    assert r3.status_code == 200, r3.text
    assert r3.json()["status"] == "ended"


# ── Team ─────────────────────────────────────────────────────────────────────────

def test_add_and_remove_team_member(client: TestClient, artists_admin, artist_id):
    r = client.post(
        f"/api/v1/artists/{artist_id}/team",
        json={"user_id": 888, "team_role": "sound_engineer"},
        headers=artists_admin["org_headers"],
    )
    assert r.status_code == 201, r.text
    member_id = r.json()["id"]

    r2 = client.get(f"/api/v1/artists/{artist_id}/team", headers=artists_admin["org_headers"])
    assert r2.status_code == 200
    assert any(m["id"] == member_id for m in r2.json())

    r3 = client.post(
        f"/api/v1/artists/{artist_id}/team/{member_id}/remove",
        headers=artists_admin["org_headers"],
    )
    assert r3.status_code == 200, r3.text
    assert r3.json()["status"] == "removed"


# ── External identifiers ─────────────────────────────────────────────────────────

def test_set_external_identifier(client: TestClient, artists_admin, artist_id):
    r = client.post(
        f"/api/v1/artists/{artist_id}/external-identifiers",
        json={"system_code": "spotify", "external_value": "sp-123"},
        headers=artists_admin["org_headers"],
    )
    assert r.status_code == 201, r.text
    assert r.json()["external_value"] == "sp-123"

    r2 = client.get(
        f"/api/v1/artists/{artist_id}/external-identifiers",
        headers=artists_admin["org_headers"],
    )
    assert r2.status_code == 200
    assert any(i["system_code"] == "spotify" for i in r2.json())


# ── Transfer ─────────────────────────────────────────────────────────────────────

def test_transfer_artist_organization(client: TestClient, artists_admin, artist_id):
    r = client.post(
        f"/api/v1/artists/{artist_id}/transfer",
        json={"target_organization_id": 999777, "reason": "ownership change"},
        headers=artists_admin["org_headers"],
    )
    assert r.status_code == 200, r.text
    assert r.json()["organization_id"] == 999777

    # Old org can no longer see this artist
    r2 = client.get(f"/api/v1/artists/{artist_id}", headers=artists_admin["org_headers"])
    assert r2.status_code == 404, r2.text


# ── Missing org header ──────────────────────────────────────────────────────────

def test_missing_org_header(client: TestClient, artists_admin):
    r = client.get(
        "/api/v1/artists",
        headers={"Authorization": artists_admin["headers"]["Authorization"]},
    )
    assert r.status_code in (400, 401, 403), r.text
