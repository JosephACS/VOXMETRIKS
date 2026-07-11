"""Spec 016 I5 — multi-org isolation, IDOR, invitations, last-owner, audit."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest
from fastapi.testclient import TestClient

from app.core import schema_bootstrap
from app.packages.identity.services.user_storage import ensure_user_tables
from app.packages.organizations.application.dto import (
    ActorContext,
    CreateOrganizationCommand,
)
from app.packages.organizations.application.use_cases.create_organization import (
    CreateOrganization,
)
from app.packages.organizations.application.use_cases.invitations import (
    InvitationUseCases,
)
from app.packages.organizations.application.use_cases.membership import (
    MembershipUseCases,
)
from app.packages.organizations.application.use_cases.organization_ops import (
    ChangeOrganizationStatus,
)
from app.packages.organizations.application.use_cases.preference import (
    PreferenceUseCases,
)
from app.packages.organizations.application.use_cases.roles import RoleUseCases
from app.packages.organizations.domain.errors import (
    InvitationAlreadyUsed,
    InvitationNotFound,
    LastOwnerViolation,
    PermissionDenied,
)
from app.packages.organizations.infrastructure.repositories.audit_repository import (
    AuditRepository,
)
from app.packages.organizations.infrastructure.repositories.membership_repository import (
    MembershipRepository,
)
from app.packages.organizations.infrastructure.repositories.preference_repository import (
    PreferenceRepository,
)
from app.packages.organizations.infrastructure.schema import ensure_organization_tables


@pytest.fixture()
def uc(tmp_path: Path):
    previous = schema_bootstrap.schema_ready()
    schema_bootstrap._schema_ready = False
    conn = duckdb.connect(str(tmp_path / "i5.duckdb"))
    ensure_user_tables(conn)
    ensure_organization_tables(conn)
    users = conn.execute("SELECT id, email FROM app_user ORDER BY id").fetchall()
    assert len(users) >= 3
    yield {
        "conn": conn,
        "user_a": int(users[0][0]),
        "user_b": int(users[1][0]),
        "user_c": int(users[2][0]),
        "email_a": str(users[0][1]).lower(),
        "email_b": str(users[1][1]).lower(),
        "email_c": str(users[2][1]).lower(),
        "actor_a": ActorContext(user_id=int(users[0][0])),
        "actor_b": ActorContext(user_id=int(users[1][0])),
        "actor_c": ActorContext(user_id=int(users[2][0])),
        "platform": ActorContext(
            user_id=int(users[0][0]), platform_role="platform_admin"
        ),
    }
    conn.close()
    schema_bootstrap._schema_ready = previous


def _create(client: TestClient, headers: dict, slug: str) -> dict:
    resp = client.post(
        "/api/v1/organizations",
        headers=headers,
        json={
            "display_name": slug,
            "slug": slug,
            "organization_type": "label",
            "activate": True,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_org_a_cannot_read_org_b(
    client: TestClient, auth_headers: dict, admin_auth_headers: dict
):
    a = _create(client, auth_headers, "i5-a-read")
    b = _create(client, admin_auth_headers, "i5-b-read")
    assert (
        client.get(
            f"/api/v1/organizations/{b['organization']['id']}", headers=auth_headers
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"/api/v1/organizations/{a['organization']['id']}",
            headers=admin_auth_headers,
        ).status_code
        == 404
    )


def test_org_a_cannot_patch_org_b(
    client: TestClient, auth_headers: dict, admin_auth_headers: dict
):
    b = _create(client, admin_auth_headers, "i5-b-patch")
    resp = client.patch(
        f"/api/v1/organizations/{b['organization']['id']}",
        headers=auth_headers,
        json={"display_name": "Hijacked"},
    )
    assert resp.status_code == 404


def test_member_id_cross_org_idor(
    client: TestClient, auth_headers: dict, admin_auth_headers: dict
):
    a = _create(client, auth_headers, "i5-a-mem")
    b = _create(client, admin_auth_headers, "i5-b-mem")
    a_id = a["organization"]["id"]
    b_member = b["membership"]["id"]
    # remove foreign member id under Org A path
    resp = client.post(
        f"/api/v1/organizations/{a_id}/members/{b_member}/remove",
        headers=auth_headers,
    )
    assert resp.status_code == 404
    # suspend foreign
    resp2 = client.patch(
        f"/api/v1/organizations/{a_id}/members/{b_member}",
        headers=auth_headers,
        json={"action": "suspend"},
    )
    assert resp2.status_code == 404
    # role assign foreign
    resp3 = client.put(
        f"/api/v1/organizations/{a_id}/members/{b_member}/roles",
        headers=auth_headers,
        json={"assign": ["viewer"], "revoke": []},
    )
    assert resp3.status_code == 404


def test_invitation_id_cross_org(
    client: TestClient, auth_headers: dict, admin_auth_headers: dict
):
    a = _create(client, auth_headers, "i5-a-inv")
    b = _create(client, admin_auth_headers, "i5-b-inv")
    inv = client.post(
        f"/api/v1/organizations/{b['organization']['id']}/invitations",
        headers=admin_auth_headers,
        json={"email": "x@example.com", "role_codes": ["viewer"]},
    )
    assert inv.status_code == 201
    inv_id = inv.json()["invitation_id"]
    revoke = client.post(
        f"/api/v1/organizations/{a['organization']['id']}/invitations/{inv_id}/revoke",
        headers=auth_headers,
    )
    assert revoke.status_code == 404
    resend = client.post(
        f"/api/v1/organizations/{a['organization']['id']}/invitations/{inv_id}/resend",
        headers=auth_headers,
    )
    assert resend.status_code == 404


def test_audit_cross_org_and_no_mutation_endpoint(
    client: TestClient, auth_headers: dict, admin_auth_headers: dict
):
    a = _create(client, auth_headers, "i5-a-aud")
    b = _create(client, admin_auth_headers, "i5-b-aud")
    assert (
        client.get(
            f"/api/v1/organizations/{b['organization']['id']}/audit-log",
            headers=auth_headers,
        ).status_code
        == 404
    )
    ok = client.get(
        f"/api/v1/organizations/{a['organization']['id']}/audit-log",
        headers=auth_headers,
    )
    assert ok.status_code == 200
    # no update/delete routes
    assert (
        client.put(
            f"/api/v1/organizations/{a['organization']['id']}/audit-log/1",
            headers=auth_headers,
            json={},
        ).status_code
        == 405
        or client.put(
            f"/api/v1/organizations/{a['organization']['id']}/audit-log/1",
            headers=auth_headers,
            json={},
        ).status_code
        == 404
    )


def test_viewer_cannot_list_invitations(
    client: TestClient, auth_headers: dict, admin_auth_headers: dict
):
    org = _create(client, auth_headers, "i5-view-inv")
    org_id = org["organization"]["id"]
    admin_email = client.get("/api/v1/users/me", headers=admin_auth_headers).json()[
        "email"
    ]
    inv = client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        headers=auth_headers,
        json={"email": admin_email, "role_codes": ["viewer"]},
    )
    assert inv.status_code == 201
    token = inv.json()["invite_token"]
    assert (
        client.post(
            f"/api/v1/invitations/{token}/accept", headers=admin_auth_headers
        ).status_code
        == 200
    )
    listed = client.get(
        f"/api/v1/organizations/{org_id}/invitations",
        headers=admin_auth_headers,
    )
    assert listed.status_code == 403


def test_technical_admin_not_platform_operator_for_suspend(uc):
    """Deny-by-default: identity admin ≠ platform elevated access."""
    actor_adminish = ActorContext(user_id=uc["user_a"], platform_role="admin")
    org = CreateOrganization(uc["conn"]).execute(
        CreateOrganizationCommand(
            actor=uc["actor_a"],
            display_name="Plat Deny",
            slug="i5-plat-deny",
            organization_type="label",
        )
    )
    with pytest.raises(PermissionDenied):
        ChangeOrganizationStatus(uc["conn"]).execute(
            actor_adminish,
            org.organization.id,
            "suspended_by_platform",
            reason="should fail",
        )


def test_accept_email_mismatch_anti_oracle(uc):
    org = CreateOrganization(uc["conn"]).execute(
        CreateOrganizationCommand(
            actor=uc["actor_a"],
            display_name="Oracle",
            slug="i5-oracle",
            organization_type="label",
        )
    )
    invites = InvitationUseCases(uc["conn"])
    created = invites.create(uc["actor_a"], org.organization.id, uc["email_b"], "viewer")
    with pytest.raises(InvitationNotFound):
        invites.accept(uc["actor_c"], created.invite_token)
    with pytest.raises(InvitationNotFound):
        invites.accept(uc["actor_b"], "totally-invalid-token-value")


def test_resend_invalidates_old_token_and_duplicate_accept(uc):
    org = CreateOrganization(uc["conn"]).execute(
        CreateOrganizationCommand(
            actor=uc["actor_a"],
            display_name="Resend",
            slug="i5-resend",
            organization_type="label",
        )
    )
    invites = InvitationUseCases(uc["conn"])
    created = invites.create(uc["actor_a"], org.organization.id, uc["email_b"], "viewer")
    old = created.invite_token
    resent = invites.resend(uc["actor_a"], org.organization.id, created.invitation.id)
    with pytest.raises(Exception):
        invites.accept(uc["actor_b"], old)
    accepted = invites.accept(uc["actor_b"], resent.invite_token)
    assert accepted.membership.status == "active"
    with pytest.raises(InvitationAlreadyUsed):
        invites.accept(uc["actor_b"], resent.invite_token)
    members = MembershipRepository(uc["conn"]).list_by_organization(org.organization.id)
    active_b = [
        m
        for m in members
        if m.user_id == uc["user_b"] and m.status == "active"
    ]
    assert len(active_b) == 1


def test_leave_clears_preference(uc):
    org = CreateOrganization(uc["conn"]).execute(
        CreateOrganizationCommand(
            actor=uc["actor_a"],
            display_name="Leave Pref",
            slug="i5-leave-pref",
            organization_type="label",
            make_active=True,
        )
    )
    # invite B as administrator so A can stay owner after leave? Need second owner.
    invites = InvitationUseCases(uc["conn"])
    created = invites.create(
        uc["actor_a"], org.organization.id, uc["email_b"], "owner"
    )
    invites.accept(uc["actor_b"], created.invite_token)
    PreferenceUseCases(uc["conn"]).set_active(uc["actor_b"], org.organization.id)
    pref_before = PreferenceRepository(uc["conn"]).get_for_user(uc["user_b"])
    assert pref_before and pref_before.active_organization_id == org.organization.id
    MembershipUseCases(uc["conn"]).leave_organization(
        uc["actor_b"], org.organization.id
    )
    pref_after = PreferenceRepository(uc["conn"]).get_for_user(uc["user_b"])
    assert pref_after is None or pref_after.active_organization_id is None


def test_last_owner_guards(uc):
    org = CreateOrganization(uc["conn"]).execute(
        CreateOrganizationCommand(
            actor=uc["actor_a"],
            display_name="Last Owner",
            slug="i5-last-owner",
            organization_type="label",
        )
    )
    members = MembershipUseCases(uc["conn"])
    with pytest.raises(LastOwnerViolation):
        members.leave_organization(uc["actor_a"], org.organization.id)
    roles = RoleUseCases(uc["conn"])
    with pytest.raises(LastOwnerViolation):
        roles.revoke_member_role(
            uc["actor_a"],
            org.organization.id,
            org.membership.id,
            "owner",
        )


def test_sql_update_requires_organization_id(uc):
    org_a = CreateOrganization(uc["conn"]).execute(
        CreateOrganizationCommand(
            actor=uc["actor_a"],
            display_name="SQL A",
            slug="i5-sql-a",
            organization_type="label",
        )
    )
    org_b = CreateOrganization(uc["conn"]).execute(
        CreateOrganizationCommand(
            actor=uc["actor_b"],
            display_name="SQL B",
            slug="i5-sql-b",
            organization_type="label",
        )
    )
    repo = MembershipRepository(uc["conn"])
    with pytest.raises(Exception):
        repo.update_status(
            org_b.membership.id,
            "suspended",
            organization_id=org_a.organization.id,
        )


def test_audit_has_no_tokens(uc):
    org = CreateOrganization(uc["conn"]).execute(
        CreateOrganizationCommand(
            actor=uc["actor_a"],
            display_name="Aud Tok",
            slug="i5-aud-tok",
            organization_type="label",
        )
    )
    invites = InvitationUseCases(uc["conn"])
    invites.create(uc["actor_a"], org.organization.id, "secret@example.com", "viewer")
    entries = AuditRepository(uc["conn"]).list_by_organization(
        org.organization.id, limit=50
    )
    blob = " ".join(
        (e.new_values_json or "") + " " + (e.previous_values_json or "")
        for e in entries
    ).lower()
    assert "invite_token" not in blob
    assert "token_hash" not in blob
    assert "authorization" not in blob


def test_user_without_org_keeps_personal_api(
    client: TestClient, auth_headers: dict
):
    me = client.get("/api/v1/users/me", headers=auth_headers)
    assert me.status_code == 200
    current = client.get("/api/v1/organizations/current", headers=auth_headers)
    assert current.status_code == 200
    assert current.json()["context"] in ("none", "active", "invalid", "access_revoked")
    health = client.get("/api/v1/health")
    assert health.status_code == 200


def test_arbitrary_ids_404(
    client: TestClient, auth_headers: dict
):
    org = _create(client, auth_headers, "i5-arb")
    oid = org["organization"]["id"]
    assert (
        client.get(f"/api/v1/organizations/999999", headers=auth_headers).status_code
        == 404
    )
    assert (
        client.get(
            f"/api/v1/organizations/{oid}/members", headers=auth_headers
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/api/v1/organizations/{oid}/members/999999/remove",
            headers=auth_headers,
        ).status_code
        == 404
    )


def test_path_header_conflict_and_preference_not_authz(
    client: TestClient, auth_headers: dict
):
    a = _create(client, auth_headers, "i5-pref-a")
    b = _create(client, auth_headers, "i5-pref-b")
    headers = {
        **auth_headers,
        "X-Organization-Id": str(b["organization"]["id"]),
    }
    conflict = client.get(
        f"/api/v1/organizations/{a['organization']['id']}",
        headers=headers,
    )
    assert conflict.status_code == 400
