"""Spec 016 I2 — organization use-case tests (isolated DuckDB)."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

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
    UpdateOrganizationProfile,
)
from app.packages.organizations.application.use_cases.preference import (
    PreferenceUseCases,
)
from app.packages.organizations.application.use_cases.roles import RoleUseCases
from app.packages.organizations.domain.errors import (
    InvitationConflict,
    InvitationExpired,
    InvitationAlreadyUsed,
    InvitationNotFound,
    InvalidActiveOrganization,
    LastOwnerViolation,
    MembershipConflict,
    OrganizationNotOperational,
    OrganizationSlugConflict,
    PermissionDenied,
    UserNotFound,
    ValidationError,
)
from app.packages.organizations.domain.invitation_token import hash_invitation_token
from app.packages.organizations.infrastructure.repositories.audit_repository import (
    AuditRepository,
)
from app.packages.organizations.infrastructure.repositories.authorization_repository import (
    AuthorizationRepository,
)
from app.packages.organizations.infrastructure.schema import ensure_organization_tables
from app.core.time_util import utc_now
from datetime import timedelta


@pytest.fixture()
def uc(tmp_path: Path):
    previous = schema_bootstrap.schema_ready()
    schema_bootstrap._schema_ready = False
    conn = duckdb.connect(str(tmp_path / "i2.duckdb"))
    ensure_user_tables(conn)
    ensure_organization_tables(conn)
    users = conn.execute(
        "SELECT id, email FROM app_user ORDER BY id"
    ).fetchall()
    assert len(users) >= 3
    # Ensure second user has distinct email for invite accept tests
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


def _create_org(uc, *, slug="acme", actor=None, make_active=True):
    actor = actor or uc["actor_a"]
    return CreateOrganization(uc["conn"]).execute(
        CreateOrganizationCommand(
            actor=actor,
            display_name="Acme",
            slug=slug,
            organization_type="label",
            make_active=make_active,
        )
    )


def test_create_organization_success(uc):
    result = _create_org(uc, slug="acme-ok")
    assert result.organization.status == "active"
    assert result.membership.status == "active"
    assert result.reused_existing is False
    auth = AuthorizationRepository(uc["conn"])
    assert auth.count_active_owners(result.organization.id) == 1
    assert auth.member_has_permission(result.membership.id, "organization.close")
    audits = AuditRepository(uc["conn"]).list_by_organization(
        result.organization.id, limit=20
    )
    actions = {a.action for a in audits}
    assert "organization.created" in actions
    assert all(
        "token" not in (a.new_values_json or "").lower()
        or "invite_token" not in (a.new_values_json or "")
        for a in audits
    )


def test_create_slug_conflict_and_deterministic_retry(uc):
    first = _create_org(uc, slug="same-slug")
    again = _create_org(uc, slug="same-slug", actor=uc["actor_a"])
    assert again.reused_existing is True
    assert again.organization.id == first.organization.id
    with pytest.raises(OrganizationSlugConflict):
        _create_org(uc, slug="same-slug", actor=uc["actor_b"])


def test_create_unknown_user(uc):
    with pytest.raises(UserNotFound):
        CreateOrganization(uc["conn"]).execute(
            CreateOrganizationCommand(
                actor=ActorContext(user_id=999999),
                display_name="X",
                slug="no-user",
                organization_type="label",
            )
        )


def test_create_rollback_on_role_failure(uc, monkeypatch):
    create = CreateOrganization(uc["conn"])

    def boom(*_a, **_k):
        raise RuntimeError("forced role failure")

    monkeypatch.setattr(create._auth, "assign_member_role", boom)
    with pytest.raises(RuntimeError):
        create.execute(
            CreateOrganizationCommand(
                actor=uc["actor_a"],
                display_name="Rollback",
                slug="rollback-org",
                organization_type="label",
            )
        )
    count = uc["conn"].execute(
        "SELECT COUNT(*) FROM app_organization WHERE slug = 'rollback-org'"
    ).fetchone()[0]
    assert int(count) == 0
    assert (
        uc["conn"].execute("SELECT COUNT(*) FROM app_organization_member").fetchone()[0]
        == 0
    )


def test_update_profile_and_lifecycle(uc):
    org = _create_org(uc, slug="life-org").organization
    updated = UpdateOrganizationProfile(uc["conn"]).execute(
        uc["actor_a"], org.id, display_name="Acme Renamed"
    )
    assert updated.data.display_name == "Acme Renamed"
    suspended = ChangeOrganizationStatus(uc["conn"]).execute(
        uc["platform"],
        org.id,
        "suspended_by_platform",
        reason="review",
    )
    assert suspended.data.status == "suspended_by_platform"
    with pytest.raises(OrganizationNotOperational):
        UpdateOrganizationProfile(uc["conn"]).execute(
            uc["actor_a"], org.id, display_name="Nope"
        )
    reinstated = ChangeOrganizationStatus(uc["conn"]).execute(
        uc["platform"], org.id, "active", reason="cleared"
    )
    assert reinstated.data.status == "active"
    closed = ChangeOrganizationStatus(uc["conn"]).execute(
        uc["actor_a"], org.id, "closed"
    )
    assert closed.data.status == "closed"


def test_last_owner_protection_and_second_owner(uc):
    created = _create_org(uc, slug="owners")
    org_id = created.organization.id
    members = MembershipUseCases(uc["conn"])
    roles = RoleUseCases(uc["conn"])
    invites = InvitationUseCases(uc["conn"])

    with pytest.raises(LastOwnerViolation):
        members.leave_organization(uc["actor_a"], org_id)

    inv = invites.create(
        uc["actor_a"], org_id, uc["email_b"], "owner"
    )
    accepted = invites.accept(uc["actor_b"], inv.invite_token)
    assert accepted.membership.user_id == uc["user_b"]

    # Now owner A can leave
    left = members.leave_organization(uc["actor_a"], org_id)
    assert left.data.status == "left"
    auth = AuthorizationRepository(uc["conn"])
    assert auth.count_active_owners(org_id) >= 1

    # Suspended owner does not count
    b_member = accepted.membership
    # assign only one owner (B). Revoking B owner should fail.
    with pytest.raises(LastOwnerViolation):
        roles.revoke_member_role(uc["actor_b"], org_id, b_member.id, "owner")


def test_membership_suspend_remove_reactivate(uc):
    created = _create_org(uc, slug="mem-ops")
    org_id = created.organization.id
    invites = InvitationUseCases(uc["conn"])
    members = MembershipUseCases(uc["conn"])
    inv = invites.create(uc["actor_a"], org_id, uc["email_b"], "viewer")
    joined = invites.accept(uc["actor_b"], inv.invite_token)
    mid = joined.membership.id
    suspended = members.suspend_member(uc["actor_a"], org_id, mid)
    assert suspended.data.status == "suspended"
    reactivated = members.reactivate_member(uc["actor_a"], org_id, mid)
    assert reactivated.data.status == "active"
    removed = members.remove_member(uc["actor_a"], org_id, mid)
    assert removed.data.status == "removed"


def test_invitations_flow(uc):
    org_id = _create_org(uc, slug="invites").organization.id
    invites = InvitationUseCases(uc["conn"])
    created = invites.create(uc["actor_a"], org_id, uc["email_b"], "viewer")
    assert created.returned_once is True
    assert created.email_delivery_status in {"console", "sent", "failed", "not_sent"}
    assert created.invite_token
    # duplicate pending
    with pytest.raises(InvitationConflict):
        invites.create(uc["actor_a"], org_id, uc["email_b"], "viewer")
    # wrong email — anti-oracle (same as unknown token)
    with pytest.raises(InvitationNotFound):
        invites.accept(uc["actor_c"], created.invite_token)
    # resend invalidates old token
    resent = invites.resend(uc["actor_a"], org_id, created.invitation.id)
    with pytest.raises(Exception):
        invites.accept(uc["actor_b"], created.invite_token)
    accepted = invites.accept(uc["actor_b"], resent.invite_token)
    assert accepted.membership.status == "active"
    with pytest.raises(InvitationAlreadyUsed):
        invites.accept(uc["actor_b"], resent.invite_token)

    # expired
    inv2 = invites.create(uc["actor_a"], org_id, uc["email_c"], "viewer")
    uc["conn"].execute(
        "UPDATE app_organization_invitation SET expires_at = ? WHERE id = ?",
        [utc_now() - timedelta(days=1), inv2.invitation.id],
    )
    with pytest.raises(InvitationExpired):
        invites.accept(uc["actor_c"], inv2.invite_token)

    # revoke
    inv3 = invites.create(
        uc["actor_a"], org_id, "newperson@example.com", "analyst"
    )
    # seed a user with that email for completeness not required for revoke
    revoked = invites.revoke(uc["actor_a"], org_id, inv3.invitation.id)
    assert revoked.data.status == "revoked"

    # audit must not contain plaintext token
    audits = AuditRepository(uc["conn"]).list_by_organization(org_id, limit=50)
    blob = " ".join(
        (a.new_values_json or "") + (a.previous_values_json or "") for a in audits
    )
    assert created.invite_token not in blob
    assert resent.invite_token not in blob


def test_roles_permissions_deny_default(uc):
    org_id = _create_org(uc, slug="roles").organization.id
    roles = RoleUseCases(uc["conn"])
    invites = InvitationUseCases(uc["conn"])
    inv = invites.create(uc["actor_a"], org_id, uc["email_b"], "viewer")
    joined = invites.accept(uc["actor_b"], inv.invite_token)
    assert roles.member_has_permission(org_id, uc["user_b"], "organization.view")
    assert not roles.member_has_permission(org_id, uc["user_b"], "member.invite")
    assert not roles.member_has_permission(org_id, uc["user_c"], "organization.view")
    roles.assign_member_role(
        uc["actor_a"], org_id, joined.membership.id, "analyst"
    )
    assert roles.member_has_permission(org_id, uc["user_b"], "report.view")


def test_preference_rules(uc):
    org = _create_org(uc, slug="prefs", make_active=False).organization
    prefs = PreferenceUseCases(uc["conn"])
    set_r = prefs.set_active(uc["actor_a"], org.id)
    assert set_r.preference.active_organization_id == org.id
    cleared = prefs.clear(uc["actor_a"])
    assert cleared.preference.active_organization_id is None
    with pytest.raises(InvalidActiveOrganization):
        prefs.set_active(uc["actor_b"], org.id)
    # closed blocks
    ChangeOrganizationStatus(uc["conn"]).execute(uc["actor_a"], org.id, "closed")
    with pytest.raises(InvalidActiveOrganization):
        prefs.set_active(uc["actor_a"], org.id)


def test_closed_org_blocks_invite(uc):
    org_id = _create_org(uc, slug="closed-block").organization.id
    ChangeOrganizationStatus(uc["conn"]).execute(uc["actor_a"], org_id, "closed")
    with pytest.raises(Exception):
        InvitationUseCases(uc["conn"]).create(
            uc["actor_a"], org_id, uc["email_b"], "viewer"
        )
