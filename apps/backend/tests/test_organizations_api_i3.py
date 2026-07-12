"""Spec 016 I3 — Organizations API + cross-tenant security tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def demo_headers(auth_headers: dict[str, str]) -> dict[str, str]:
    return auth_headers


@pytest.fixture()
def admin_headers(admin_auth_headers: dict[str, str]) -> dict[str, str]:
    return admin_auth_headers


def _create_org(client: TestClient, headers: dict, slug: str = "api-acme") -> dict:
    resp = client.post(
        "/api/v1/organizations",
        headers=headers,
        json={
            "display_name": "API Acme",
            "slug": slug,
            "organization_type": "label",
            "activate": True,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_auth_required(client: TestClient):
    assert client.get("/api/v1/organizations").status_code == 401
    assert client.post("/api/v1/organizations", json={"display_name": "X"}).status_code == 401


def test_create_list_get_update_close(client: TestClient, demo_headers: dict):
    created = _create_org(client, demo_headers, slug="life-api")
    org_id = created["organization"]["id"]
    assert created["organization"]["status"] == "active"
    assert "owner" in created["roles"]

    listed = client.get("/api/v1/organizations", headers=demo_headers)
    assert listed.status_code == 200
    assert any(o["id"] == org_id for o in listed.json())

    got = client.get(f"/api/v1/organizations/{org_id}", headers=demo_headers)
    assert got.status_code == 200

    patched = client.patch(
        f"/api/v1/organizations/{org_id}",
        headers=demo_headers,
        json={"display_name": "Renamed"},
    )
    assert patched.status_code == 200
    assert patched.json()["display_name"] == "Renamed"

    current = client.get("/api/v1/organizations/current", headers=demo_headers)
    assert current.status_code == 200
    assert current.json()["context"] == "active"

    closed = client.post(
        f"/api/v1/organizations/{org_id}/close",
        headers=demo_headers,
        json={},
    )
    assert closed.status_code == 200
    assert closed.json()["status"] == "closed"


def test_slug_conflict(client: TestClient, demo_headers: dict):
    _create_org(client, demo_headers, slug="dup-slug")
    # same user deterministic reuse → 201 with reused_existing
    again = client.post(
        "/api/v1/organizations",
        headers=demo_headers,
        json={"display_name": "Dup", "slug": "dup-slug"},
    )
    assert again.status_code == 201
    assert again.json()["reused_existing"] is True


def test_cross_tenant_org_404(
    client: TestClient, demo_headers: dict, admin_headers: dict
):
    org = _create_org(client, demo_headers, slug="tenant-a")
    org_id = org["organization"]["id"]
    # admin user is different account — should not see demo's org
    resp = client.get(f"/api/v1/organizations/{org_id}", headers=admin_headers)
    assert resp.status_code == 404


def test_header_path_conflict(client: TestClient, demo_headers: dict):
    a = _create_org(client, demo_headers, slug="hdr-a")
    b = _create_org(client, demo_headers, slug="hdr-b")
    headers = {
        **demo_headers,
        "X-Organization-Id": str(b["organization"]["id"]),
    }
    resp = client.get(
        f"/api/v1/organizations/{a['organization']['id']}",
        headers=headers,
    )
    assert resp.status_code == 404 or resp.status_code == 400
    # If membership valid for both, conflict is 400
    # demo owns both — expect 400
    assert resp.status_code == 400


def test_invitations_flow(
    client: TestClient, demo_headers: dict, admin_headers: dict
):
    org = _create_org(client, demo_headers, slug="inv-api")
    org_id = org["organization"]["id"]
    # admin email
    admin_me = client.get("/api/v1/users/me", headers=admin_headers)
    assert admin_me.status_code == 200
    admin_email = admin_me.json()["email"]

    created = client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        headers=demo_headers,
        json={"email": admin_email, "role_codes": ["viewer"]},
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["delivery_status"] in {"not_sent", "console", "sent", "failed"}
    assert body["invite_token"]
    token = body["invite_token"]
    inv_id = body["invitation_id"]

    listed = client.get(
        f"/api/v1/organizations/{org_id}/invitations",
        headers=demo_headers,
    )
    assert listed.status_code == 200
    assert "invite_token" not in listed.text
    assert "token_hash" not in listed.text

    # wrong user email — anti-oracle: indistinguishable from unknown token
    bad = client.post(
        f"/api/v1/invitations/{token}/accept",
        headers=demo_headers,
    )
    assert bad.status_code == 404
    body = bad.json()
    code = (body.get("details") or {}).get("code") or (body.get("detail") or {}).get("code")
    assert code == "not_found"

    accepted = client.post(
        f"/api/v1/invitations/{token}/accept",
        headers=admin_headers,
    )
    assert accepted.status_code == 200, accepted.text

    used = client.post(
        f"/api/v1/invitations/{token}/accept",
        headers=admin_headers,
    )
    assert used.status_code == 410

    # resend on new invite
    created2 = client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        headers=demo_headers,
        json={"email": "someone@example.com", "role_codes": ["analyst"]},
    )
    assert created2.status_code == 201
    inv2 = created2.json()
    resent = client.post(
        f"/api/v1/organizations/{org_id}/invitations/{inv2['invitation_id']}/resend",
        headers=demo_headers,
    )
    assert resent.status_code == 200
    assert resent.json()["invite_token"] != inv2["invite_token"]
    # old token invalid
    old_accept = client.post(
        f"/api/v1/invitations/{inv2['invite_token']}/accept",
        headers=admin_headers,
    )
    assert old_accept.status_code in (403, 404, 410)

    revoked = client.post(
        f"/api/v1/organizations/{org_id}/invitations/{resent.json()['invitation_id']}/revoke",
        headers=demo_headers,
    )
    assert revoked.status_code == 200
    _ = inv_id


def test_roles_and_audit_permissions(
    client: TestClient, demo_headers: dict, admin_headers: dict
):
    org = _create_org(client, demo_headers, slug="roles-api")
    org_id = org["organization"]["id"]
    roles = client.get(f"/api/v1/organizations/{org_id}/roles", headers=demo_headers)
    assert roles.status_code == 200
    assert any(r["code"] == "owner" for r in roles.json())

    perms = client.get(
        f"/api/v1/organizations/{org_id}/permissions", headers=demo_headers
    )
    assert perms.status_code == 200

    # invite admin as viewer then try role.assign as viewer → 403
    admin_email = client.get("/api/v1/users/me", headers=admin_headers).json()["email"]
    inv = client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        headers=demo_headers,
        json={"email": admin_email, "role_codes": ["viewer"]},
    ).json()
    client.post(
        f"/api/v1/invitations/{inv['invite_token']}/accept",
        headers=admin_headers,
    )
    members = client.get(
        f"/api/v1/organizations/{org_id}/members", headers=demo_headers
    ).json()["items"]
    admin_member = next(m for m in members if m["user_id"] != org["membership"]["user_id"])
    denied = client.put(
        f"/api/v1/organizations/{org_id}/members/{admin_member['id']}/roles",
        headers=admin_headers,
        json={"assign": ["analyst"]},
    )
    assert denied.status_code == 403

    audit = client.get(
        f"/api/v1/organizations/{org_id}/audit-log",
        headers=demo_headers,
    )
    assert audit.status_code == 200
    assert "page" in audit.json()
    assert "invite_token" not in audit.text


def test_last_owner_leave_blocked(client: TestClient, demo_headers: dict):
    org = _create_org(client, demo_headers, slug="last-owner-api")
    org_id = org["organization"]["id"]
    mid = org["membership"]["id"]
    resp = client.patch(
        f"/api/v1/organizations/{org_id}/members/{mid}",
        headers=demo_headers,
        json={"action": "leave"},
    )
    assert resp.status_code == 409
    assert resp.json()["details"].get("code") == "last_owner" or "last" in resp.text.lower()


def test_personal_routes_still_work_without_org(
    client: TestClient, demo_headers: dict
):
    # engineer/demo user without forcing org — /me still works
    me = client.get("/api/v1/users/me", headers=demo_headers)
    assert me.status_code == 200
    current = client.get("/api/v1/organizations/current", headers=demo_headers)
    assert current.status_code == 200
    # may be none if no activate yet
    assert current.json()["context"] in {"none", "active", "invalid", "access_revoked"}


def test_cross_org_member_id(
    client: TestClient, demo_headers: dict, admin_headers: dict
):
    org_a = _create_org(client, demo_headers, slug="xorg-a")
    org_b = _create_org(client, admin_headers, slug="xorg-b")
    mid_b = org_b["membership"]["id"]
    resp = client.post(
        f"/api/v1/organizations/{org_a['organization']['id']}/members/{mid_b}/remove",
        headers=demo_headers,
    )
    assert resp.status_code == 404
