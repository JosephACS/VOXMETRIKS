"""T003 — session bootstrap/context contract, isolation, revoked memberships."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.database import using_write_conn
from app.packages.organizations.domain.enums import MembershipStatus, OrganizationStatus
from app.packages.organizations.infrastructure.repositories import (
    MembershipRepository,
    OrganizationRepository,
)


def _login(client: TestClient, login: str, password: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/users/login",
        json={"login": login, "password": password, "remember": True},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_bootstrap_requires_auth(client: TestClient) -> None:
    assert client.get("/api/v1/session/bootstrap").status_code == 401


def test_bootstrap_ordinary_user_has_personal_space(client: TestClient) -> None:
    headers = _login(client, "demo", "demo123")
    resp = client.get("/api/v1/session/bootstrap", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "token" not in body
    assert body["user"]["identity_role"] in {"user", "admin", "engineer"}
    assert "email" not in body["user"]
    keys = [s["key"] for s in body["spaces"]]
    assert "personal" in keys
    assert body["active_space_key"]
    assert body["recommended_path"].startswith("/")
    for space in body["spaces"]:
        for cap in space["capabilities"]:
            if not cap["allowed"]:
                assert cap["reason"]
                assert "hash" not in str(cap["reason"]).lower()


def test_context_rejects_malformed_key(client: TestClient) -> None:
    headers = _login(client, "demo", "demo123")
    bad = client.post("/api/v1/session/context", json={"space_key": "org/1"}, headers=headers)
    assert bad.status_code == 400


def test_context_isolation_and_revoked_membership(client: TestClient) -> None:
    demo_headers = _login(client, "demo", "demo123")
    me = client.get("/api/v1/users/me", headers=demo_headers)
    demo_id = int(me.json()["id"])

    with using_write_conn() as conn:
        orgs = OrganizationRepository(conn)
        members = MembershipRepository(conn)
        org_a = orgs.create(
            display_name="Bootstrap Alpha",
            slug="bootstrap-alpha-050",
            organization_type="label",
            created_by=demo_id,
            status=OrganizationStatus.ACTIVE.value,
        )
        members.create(organization_id=org_a.id, user_id=demo_id, created_by=demo_id)
        org_b = orgs.create(
            display_name="Bootstrap Beta",
            slug="bootstrap-beta-050",
            organization_type="label",
            created_by=demo_id,
            status=OrganizationStatus.ACTIVE.value,
        )

    listed = client.get("/api/v1/session/bootstrap", headers=demo_headers).json()
    keys = [s["key"] for s in listed["spaces"]]
    assert f"organization:{org_a.id}" in keys
    assert f"organization:{org_b.id}" not in keys

    forbidden = client.post(
        "/api/v1/session/context",
        json={"space_key": f"organization:{org_b.id}"},
        headers=demo_headers,
    )
    assert forbidden.status_code == 403

    activated = client.post(
        "/api/v1/session/context",
        json={"space_key": f"organization:{org_a.id}"},
        headers=demo_headers,
    )
    assert activated.status_code == 200, activated.text
    assert activated.json()["active_space_key"] == f"organization:{org_a.id}"

    with using_write_conn() as conn:
        members = MembershipRepository(conn)
        row = conn.execute(
            """
            SELECT id FROM app_organization_member
            WHERE organization_id = ? AND user_id = ? AND status = 'active'
            """,
            [org_a.id, demo_id],
        ).fetchone()
        assert row
        members.update_status(int(row[0]), MembershipStatus.REMOVED.value)

    after = client.get("/api/v1/session/bootstrap", headers=demo_headers).json()
    assert f"organization:{org_a.id}" not in [s["key"] for s in after["spaces"]]
    assert after["active_space_key"] == "personal"


def test_shared_password_policy_rejects_weak_register(client: TestClient) -> None:
    for password in ("1234", "short7!", "demo123", "admin123"):
        resp = client.post(
            "/api/v1/users/register",
            json={
                "username": f"weak_{password[:4]}",
                "email": f"weak_{password[:4]}@voxmetrik.io",
                "password": password,
            },
        )
        assert resp.status_code == 400, password


def test_context_blocked_org_returns_409(client: TestClient) -> None:
    demo_headers = _login(client, "demo", "demo123")
    me = client.get("/api/v1/users/me", headers=demo_headers)
    demo_id = int(me.json()["id"])

    with using_write_conn() as conn:
        orgs = OrganizationRepository(conn)
        members = MembershipRepository(conn)
        org = orgs.create(
            display_name="Bootstrap Suspended",
            slug="bootstrap-suspended-050",
            organization_type="label",
            created_by=demo_id,
            status=OrganizationStatus.SUSPENDED_BY_PLATFORM.value,
        )
        members.create(organization_id=org.id, user_id=demo_id, created_by=demo_id)

    listed = client.get("/api/v1/session/bootstrap", headers=demo_headers).json()
    match = next(s for s in listed["spaces"] if s["key"] == f"organization:{org.id}")
    assert any(not c["allowed"] and c["reason"] == "lifecycle_blocked" for c in match["capabilities"])

    blocked = client.post(
        "/api/v1/session/context",
        json={"space_key": f"organization:{org.id}"},
        headers=demo_headers,
    )
    assert blocked.status_code == 409, blocked.text


def test_context_malformed_keys_return_400(client: TestClient) -> None:
    headers = _login(client, "demo", "demo123")
    # Empty key is rejected by the strict request schema (422); service-level
    # malformation still returns 400.
    empty = client.post("/api/v1/session/context", json={"space_key": ""}, headers=headers)
    assert empty.status_code == 422
    for key in ("spaceship", "organization:abc", "artist:"):
        resp = client.post("/api/v1/session/context", json={"space_key": key}, headers=headers)
        assert resp.status_code == 400, key


def test_active_space_preference_rolls_back_on_failed_activation(client: TestClient) -> None:
    headers = _login(client, "demo", "demo123")
    before = client.get("/api/v1/session/bootstrap", headers=headers).json()["active_space_key"]
    forbidden = client.post(
        "/api/v1/session/context",
        json={"space_key": "organization:999999001"},
        headers=headers,
    )
    assert forbidden.status_code == 403
    after = client.get("/api/v1/session/bootstrap", headers=headers).json()["active_space_key"]
    assert after == before


def test_partial_discovery_surfaces_pending_without_inventing_spaces(
    client: TestClient, monkeypatch
) -> None:
    headers = _login(client, "demo", "demo123")

    def _boom(*_a, **_k):
        raise RuntimeError("forced discovery failure")

    monkeypatch.setattr(
        "app.packages.identity.services.session_bootstrap.OrganizationRepository.list_for_user",
        _boom,
    )
    body = client.get("/api/v1/session/bootstrap", headers=headers).json()
    codes = {p["code"] for p in body["pending_actions"]}
    assert "organization_discovery_unavailable" in codes
    assert all(not s["key"].startswith("organization:") for s in body["spaces"])
    assert "personal" in [s["key"] for s in body["spaces"]]
