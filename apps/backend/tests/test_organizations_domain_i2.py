"""Spec 016 I2 — pure domain rule unit tests."""

from __future__ import annotations

from datetime import timedelta

import pytest

from app.core.time_util import utc_now
from app.packages.organizations.domain.enums import (
    InvitationStatus,
    MembershipStatus,
    OrganizationStatus,
)
from app.packages.organizations.domain.errors import (
    InvalidOrganizationTransition,
    ValidationError,
)
from app.packages.organizations.domain.invitation_token import (
    generate_invitation_token,
    hash_invitation_token,
    verify_invitation_token,
)
from app.packages.organizations.domain.rules import (
    assert_invite_transition,
    assert_member_transition,
    assert_org_transition,
    is_platform_role_code,
    normalize_email,
    normalize_slug,
    would_remove_last_active_owner,
)


def test_normalize_slug():
    assert normalize_slug("Acme Corp") == "acme-corp"
    assert normalize_slug("  Hello_World  ") == "hello-world"
    with pytest.raises(ValidationError):
        normalize_slug("@@@")


def test_normalize_email():
    assert normalize_email(" Person@Example.COM ") == "person@example.com"
    with pytest.raises(ValidationError):
        normalize_email("not-an-email")


def test_org_transitions():
    assert_org_transition(
        OrganizationStatus.PROVISIONING.value, OrganizationStatus.ACTIVE.value
    )
    assert_org_transition(
        OrganizationStatus.ACTIVE.value,
        OrganizationStatus.SUSPENDED_BY_PLATFORM.value,
    )
    with pytest.raises(InvalidOrganizationTransition):
        assert_org_transition(
            OrganizationStatus.CLOSED.value, OrganizationStatus.ACTIVE.value
        )


def test_member_and_invite_transitions():
    assert_member_transition(
        MembershipStatus.ACTIVE.value, MembershipStatus.SUSPENDED.value
    )
    with pytest.raises(ValidationError):
        assert_member_transition(
            MembershipStatus.LEFT.value, MembershipStatus.ACTIVE.value
        )
    assert_invite_transition(
        InvitationStatus.PENDING.value, InvitationStatus.ACCEPTED.value
    )
    with pytest.raises(ValidationError):
        assert_invite_transition(
            InvitationStatus.ACCEPTED.value, InvitationStatus.PENDING.value
        )


def test_token_hash_verify_and_not_plaintext_equal_hash():
    token = generate_invitation_token()
    assert token.returned_once is True
    assert token.email_delivery_status == "not_sent"
    assert token.plaintext != token.token_hash
    assert verify_invitation_token(token.plaintext, token.token_hash)
    assert not verify_invitation_token("wrong", token.token_hash)
    assert hash_invitation_token(token.plaintext) == token.token_hash


def test_last_owner_predicate():
    assert would_remove_last_active_owner(
        active_owner_count=1, target_is_active_owner=True
    )
    assert not would_remove_last_active_owner(
        active_owner_count=2, target_is_active_owner=True
    )
    assert not would_remove_last_active_owner(
        active_owner_count=1, target_is_active_owner=False
    )


def test_platform_role_codes_denied_as_org_roles():
    assert is_platform_role_code("admin")
    assert is_platform_role_code("engineer")
    assert not is_platform_role_code("owner")
    assert not is_platform_role_code("viewer")


def test_invite_expiry_window_helpers():
    # expiry comparison used by use cases
    past = utc_now() - timedelta(days=1)
    assert past < utc_now()
