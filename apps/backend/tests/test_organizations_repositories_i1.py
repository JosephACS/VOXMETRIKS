"""Spec 016 I1 — organization repository tests (isolated DuckDB)."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import duckdb
import pytest

from app.core import schema_bootstrap
from app.core.time_util import utc_now
from app.packages.identity.services.user_storage import ensure_user_tables
from app.packages.organizations.domain.errors import OrganizationsError
from app.packages.organizations.infrastructure.repositories import (
    AuditRepository,
    AuthorizationRepository,
    InvitationRepository,
    MembershipRepository,
    OrganizationRepository,
    PreferenceRepository,
)
from app.packages.organizations.infrastructure.schema import ensure_organization_tables


@pytest.fixture()
def repos(tmp_path: Path):
    previous_ready = schema_bootstrap.schema_ready()
    schema_bootstrap._schema_ready = False
    conn = duckdb.connect(str(tmp_path / "org_repos.duckdb"))
    ensure_user_tables(conn)
    ensure_organization_tables(conn)
    users = conn.execute("SELECT id FROM app_user ORDER BY id").fetchall()
    assert len(users) >= 2
    yield {
        "conn": conn,
        "user_a": int(users[0][0]),
        "user_b": int(users[1][0]),
        "orgs": OrganizationRepository(conn),
        "members": MembershipRepository(conn),
        "invites": InvitationRepository(conn),
        "auth": AuthorizationRepository(conn),
        "prefs": PreferenceRepository(conn),
        "audit": AuditRepository(conn),
    }
    conn.close()
    schema_bootstrap._schema_ready = previous_ready


def test_organization_crud_and_list_for_user(repos):
    orgs = repos["orgs"]
    members = repos["members"]
    user_a = repos["user_a"]
    user_b = repos["user_b"]

    org1 = orgs.create(
        display_name="Alpha",
        slug="alpha",
        organization_type="label",
        created_by=user_a,
        status="active",
    )
    org2 = orgs.create(
        display_name="Beta",
        slug="beta",
        organization_type="label",
        created_by=user_a,
        status="active",
    )
    assert orgs.get_by_slug("alpha").id == org1.id
    orgs.update_basic_fields(org1.id, display_name="Alpha Updated")
    assert orgs.get_by_id(org1.id).display_name == "Alpha Updated"
    orgs.update_status(org1.id, "suspended_by_platform")
    assert orgs.get_by_id(org1.id).status == "suspended_by_platform"
    orgs.update_status(org1.id, "active")

    members.create(organization_id=org1.id, user_id=user_a, created_by=user_a)
    members.create(organization_id=org2.id, user_id=user_a, created_by=user_a)
    members.create(organization_id=org2.id, user_id=user_b, created_by=user_a)

    listed = orgs.list_for_user(user_a)
    assert {o.slug for o in listed} == {"alpha", "beta"}
    listed_b = orgs.list_for_user(user_b)
    assert {o.slug for o in listed_b} == {"beta"}


def test_membership_filtered_by_organization(repos):
    orgs = repos["orgs"]
    members = repos["members"]
    user_a = repos["user_a"]
    user_b = repos["user_b"]

    org1 = orgs.create(
        display_name="One", slug="one", organization_type="label", created_by=user_a, status="active"
    )
    org2 = orgs.create(
        display_name="Two", slug="two", organization_type="label", created_by=user_a, status="active"
    )
    members.create(organization_id=org1.id, user_id=user_a, created_by=user_a)
    members.create(organization_id=org2.id, user_id=user_b, created_by=user_a)

    only_org1 = members.list_by_organization(org1.id)
    assert len(only_org1) == 1
    assert only_org1[0].user_id == user_a
    assert all(m.organization_id == org1.id for m in only_org1)


def test_invitation_by_hash_and_active_email(repos):
    orgs = repos["orgs"]
    invites = repos["invites"]
    user_a = repos["user_a"]
    org = orgs.create(
        display_name="InvOrg",
        slug="inv-org",
        organization_type="label",
        created_by=user_a,
        status="active",
    )
    expires = utc_now() + timedelta(days=3)
    created = invites.create(
        organization_id=org.id,
        email="Person@Example.COM",
        token_hash="abc123hash",
        expires_at=expires,
        invited_by=user_a,
        initial_role_code="viewer",
    )
    assert created.email_normalized == "person@example.com"
    found = invites.get_by_token_hash("abc123hash")
    assert found is not None and found.id == created.id
    active = invites.find_active_by_org_and_email(org.id, "person@example.com")
    assert active is not None and active.id == created.id

    other = orgs.create(
        display_name="Other",
        slug="other-org",
        organization_type="label",
        created_by=user_a,
        status="active",
    )
    # organization-scoped: other org must not see this invitation via list
    assert invites.list_by_organization(other.id) == []
    assert all(i.organization_id == org.id for i in invites.list_by_organization(org.id))


def test_assign_revoke_permission_and_preference(repos):
    orgs = repos["orgs"]
    members = repos["members"]
    auth = repos["auth"]
    prefs = repos["prefs"]
    user_a = repos["user_a"]

    org = orgs.create(
        display_name="AuthOrg",
        slug="auth-org",
        organization_type="label",
        created_by=user_a,
        status="active",
    )
    member = members.create(organization_id=org.id, user_id=user_a, created_by=user_a)
    owner_id = auth.get_role_id_by_code("owner")
    viewer_id = auth.get_role_id_by_code("viewer")
    assert owner_id and viewer_id

    auth.assign_member_role(member_id=member.id, role_id=owner_id, assigned_by=user_a)
    assert auth.member_has_permission(member.id, "organization.close") is True
    assert auth.member_has_permission(member.id, "organization.create") is False

    auth.revoke_member_role(member_id=member.id, role_id=owner_id, revoked_by=user_a)
    assert auth.member_has_permission(member.id, "organization.close") is False

    auth.assign_member_role(member_id=member.id, role_id=viewer_id, assigned_by=user_a)
    assert auth.member_has_permission(member.id, "organization.view") is True
    assert auth.member_has_permission(member.id, "member.invite") is False

    pref = prefs.set_active_organization(user_a, org.id)
    assert pref.active_organization_id == org.id
    cleared = prefs.clear_active_organization(user_a)
    assert cleared.active_organization_id is None


def test_audit_append_pagination_and_no_update_delete(repos):
    orgs = repos["orgs"]
    audit = repos["audit"]
    user_a = repos["user_a"]
    org = orgs.create(
        display_name="AuditOrg",
        slug="audit-org",
        organization_type="label",
        created_by=user_a,
        status="active",
    )
    other = orgs.create(
        display_name="AuditOther",
        slug="audit-other",
        organization_type="label",
        created_by=user_a,
        status="active",
    )
    for i in range(5):
        audit.append(
            organization_id=org.id,
            actor_user_id=user_a,
            action=f"test.action.{i}",
            target_type="organization",
            target_id=str(org.id),
            source="test",
            result="success",
            new_values={"password": "secret", "display_name": "x"},
        )
    audit.append(
        organization_id=other.id,
        actor_user_id=user_a,
        action="other.action",
        target_type="organization",
        target_id=str(other.id),
        source="test",
        result="success",
    )
    page = audit.list_by_organization(org.id, limit=2, offset=0)
    assert len(page) == 2
    assert all(e.organization_id == org.id for e in page)
    # secrets stripped from JSON
    assert "password" not in (page[0].new_values_json or "")

    with pytest.raises(OrganizationsError):
        audit.update(1)
    with pytest.raises(OrganizationsError):
        audit.delete(1)
