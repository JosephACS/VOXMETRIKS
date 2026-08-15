"""Invitation create / accept / revoke / resend (academic delivery)."""

from __future__ import annotations

from datetime import timedelta
from typing import Optional

import duckdb

from app.packages.organizations.application.dto import (
    AcceptInvitationResult,
    ActorContext,
    InvitationCreateResult,
    MutationResult,
)
from app.packages.organizations.application.services import (
    audit,
    get_organization_or_raise,
    now,
    require_active_membership,
    require_org_active_for_mutations,
    require_permission,
    require_user,
)
from app.packages.organizations.application.transactions import transaction
from app.packages.organizations.domain import events as ev
from app.packages.organizations.domain.enums import (
    InvitationStatus,
    MembershipStatus,
)
from app.packages.organizations.domain.errors import (
    InvitationAlreadyUsed,
    InvitationConflict,
    InvitationExpired,
    InvitationNotFound,
    InvitationRevoked,
    MembershipConflict,
    PermissionDenied,
    RoleNotFound,
    ValidationError,
)
from app.packages.organizations.domain.invitation_token import (
    generate_invitation_token,
    hash_invitation_token,
    verify_invitation_token,
)
from app.packages.organizations.domain.rules import (
    DEFAULT_INVITE_TTL_DAYS,
    MAX_INVITE_TTL_DAYS,
    assert_invite_transition,
    is_platform_role_code,
    normalize_email,
)
from app.packages.organizations.application.journey import assert_invitation_role_assignable
from app.packages.organizations.infrastructure.repositories.audit_repository import (
    AuditRepository,
)
from app.packages.organizations.infrastructure.repositories.authorization_repository import (
    AuthorizationRepository,
)
from app.packages.organizations.infrastructure.repositories.invitation_repository import (
    InvitationRepository,
)
from app.packages.organizations.infrastructure.repositories.membership_repository import (
    MembershipRepository,
)
from app.packages.organizations.infrastructure.repositories.organization_repository import (
    OrganizationRepository,
)


class InvitationUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn
        self._orgs = OrganizationRepository(conn)
        self._members = MembershipRepository(conn)
        self._auth = AuthorizationRepository(conn)
        self._invites = InvitationRepository(conn)
        self._audits = AuditRepository(conn)

    def create(
        self,
        actor: ActorContext,
        organization_id: int,
        email: str,
        initial_role_code: str,
        *,
        ttl_days: int = DEFAULT_INVITE_TTL_DAYS,
    ) -> InvitationCreateResult:
        org = get_organization_or_raise(self._orgs, organization_id)
        require_org_active_for_mutations(org)
        actor_m = require_active_membership(
            self._members, organization_id=organization_id, user_id=actor.user_id
        )
        require_permission(
            self._auth, member_id=actor_m.id, permission_code="member.invite"
        )
        email_n = normalize_email(email)
        role_code = initial_role_code.strip().lower()
        if is_platform_role_code(role_code):
            raise ValidationError("platform roles cannot be invitation roles")
        role_code = assert_invitation_role_assignable(
            self._conn,
            actor_user_id=actor.user_id,
            organization_id=organization_id,
            role_code=role_code,
        )
        if self._auth.get_role_id_by_code(role_code) is None:
            raise RoleNotFound(f"role code={role_code}")
        if ttl_days < 1 or ttl_days > MAX_INVITE_TTL_DAYS:
            raise ValidationError(
                f"ttl_days must be between 1 and {MAX_INVITE_TTL_DAYS}"
            )

        existing_user = self._conn.execute(
            "SELECT id FROM app_user WHERE LOWER(email) = ?", [email_n]
        ).fetchone()
        if existing_user:
            member = self._members.get_by_org_and_user(
                organization_id, int(existing_user[0])
            )
            if member and member.status == MembershipStatus.ACTIVE.value:
                raise MembershipConflict("user is already an active member")

        pending = self._invites.find_active_by_org_and_email(organization_id, email_n)
        if pending is not None:
            raise InvitationConflict(
                "pending invitation already exists; use resend"
            )

        token = generate_invitation_token()
        expires = now() + timedelta(days=ttl_days)
        with transaction(self._conn):
            invitation = self._invites.create(
                organization_id=organization_id,
                email=email_n,
                token_hash=token.token_hash,
                expires_at=expires,
                invited_by=actor.user_id,
                initial_role_code=role_code,
            )
            audit(
                self._audits,
                action="invitation.created",
                target_type="invitation",
                result="success",
                organization_id=organization_id,
                actor_user_id=actor.user_id,
                target_id=str(invitation.id),
                new_values={
                    "email_normalized": email_n,
                    "initial_role_code": role_code,
                    "expires_at": str(expires),
                },
                request_id=actor.request_id,
            )

        delivery = self._deliver_invitation_email(
            invitation_id=invitation.id,
            organization_id=organization_id,
            org_name=org.display_name,
            email=email_n,
            role_code=role_code,
            invite_token=token.plaintext,
            expires_at=expires,
            invited_by=actor.user_id,
        )
        return InvitationCreateResult(
            invitation=invitation,
            invite_token=token.plaintext,
            returned_once=True,
            email_delivery_status=delivery,
            events=[
                ev.evt(
                    ev.INVITATION_CREATED,
                    occurred_at=now(),
                    organization_id=organization_id,
                    actor_user_id=actor.user_id,
                    target_type="invitation",
                    target_id=str(invitation.id),
                )
            ],
        )

    def accept(
        self, actor: ActorContext, plaintext_token: str
    ) -> AcceptInvitationResult:
        user = require_user(self._conn, actor.user_id)
        token_hash = hash_invitation_token(plaintext_token)
        invitation = self._invites.get_by_token_hash(token_hash)
        if invitation is None:
            raise InvitationNotFound("invitation token not found")
        self._assert_accept_preconditions(invitation, user_email=user["email"])
        if not verify_invitation_token(plaintext_token, invitation.token_hash):
            raise InvitationNotFound("invitation token mismatch")

        org = get_organization_or_raise(self._orgs, invitation.organization_id)
        require_org_active_for_mutations(org)
        role_id = self._auth.get_role_id_by_code(invitation.initial_role_code)
        if role_id is None:
            raise RoleNotFound(invitation.initial_role_code)

        with transaction(self._conn):
            # Re-load inside tx for concurrency
            invitation = self._invites.get_by_id(invitation.id)
            self._assert_accept_preconditions(invitation, user_email=user["email"])

            existing = self._members.get_by_org_and_user(
                invitation.organization_id, actor.user_id
            )
            if existing and existing.status == MembershipStatus.ACTIVE.value:
                raise MembershipConflict("already an active member")
            if existing and existing.status == MembershipStatus.SUSPENDED.value:
                raise MembershipConflict("membership suspended; cannot accept invite")
            if existing and existing.status in {
                MembershipStatus.LEFT.value,
                MembershipStatus.REMOVED.value,
            }:
                # Explicit rejoin via invite: reactivate row (UNIQUE org+user).
                membership = self._members.update_status(
                    existing.id,
                    MembershipStatus.ACTIVE.value,
                    organization_id=invitation.organization_id,
                )
            else:
                membership = self._members.create(
                    organization_id=invitation.organization_id,
                    user_id=actor.user_id,
                    created_by=invitation.invited_by,
                )
            self._auth.assign_member_role(
                member_id=membership.id,
                role_id=role_id,
                assigned_by=invitation.invited_by,
                organization_id=invitation.organization_id,
            )
            invitation = self._invites.update_status(
                invitation.id,
                InvitationStatus.ACCEPTED.value,
                organization_id=invitation.organization_id,
                accepted_by=actor.user_id,
            )
            audit(
                self._audits,
                action="invitation.accepted",
                target_type="invitation",
                result="success",
                organization_id=invitation.organization_id,
                actor_user_id=actor.user_id,
                target_id=str(invitation.id),
                new_values={"membership_id": membership.id},
                request_id=actor.request_id,
            )
            audit(
                self._audits,
                action="role.assigned",
                target_type="member_role",
                result="success",
                organization_id=invitation.organization_id,
                actor_user_id=actor.user_id,
                target_id=str(membership.id),
                new_values={"role_code": invitation.initial_role_code},
                request_id=actor.request_id,
            )

        return AcceptInvitationResult(
            organization=org,
            membership=membership,
            events=[
                ev.evt(
                    ev.INVITATION_ACCEPTED,
                    occurred_at=now(),
                    organization_id=org.id,
                    actor_user_id=actor.user_id,
                    target_type="invitation",
                    target_id=str(invitation.id),
                ),
                ev.evt(
                    ev.MEMBER_JOINED,
                    occurred_at=now(),
                    organization_id=org.id,
                    actor_user_id=actor.user_id,
                    target_type="membership",
                    target_id=str(membership.id),
                ),
            ],
        )

    def revoke(
        self, actor: ActorContext, organization_id: int, invitation_id: int
    ) -> MutationResult:
        org = get_organization_or_raise(self._orgs, organization_id)
        require_org_active_for_mutations(org)
        actor_m = require_active_membership(
            self._members, organization_id=organization_id, user_id=actor.user_id
        )
        require_permission(
            self._auth, member_id=actor_m.id, permission_code="invitation.revoke"
        )
        invitation = self._get_invite(invitation_id, organization_id)
        assert_invite_transition(invitation.status, InvitationStatus.REVOKED.value)
        with transaction(self._conn):
            updated = self._invites.update_status(
                invitation_id,
                InvitationStatus.REVOKED.value,
                organization_id=organization_id,
                revoked_by=actor.user_id,
            )
            audit(
                self._audits,
                action="invitation.revoked",
                target_type="invitation",
                result="success",
                organization_id=organization_id,
                actor_user_id=actor.user_id,
                target_id=str(invitation_id),
                previous_values={"status": invitation.status},
                new_values={"status": updated.status},
                request_id=actor.request_id,
            )
        return MutationResult(
            data=updated,
            events=[
                ev.evt(
                    ev.INVITATION_REVOKED,
                    occurred_at=now(),
                    organization_id=organization_id,
                    actor_user_id=actor.user_id,
                    target_type="invitation",
                    target_id=str(invitation_id),
                )
            ],
        )

    def resend(
        self,
        actor: ActorContext,
        organization_id: int,
        invitation_id: int,
        *,
        ttl_days: int = DEFAULT_INVITE_TTL_DAYS,
    ) -> InvitationCreateResult:
        """Academic resend: revoke pending + create replacement (rotate).

        DuckDB cannot UPDATE UNIQUE ``token_hash`` in place (ART limitation),
        so resend follows the approved revoke+create path while keeping a
        single pending invitation per (org, email).
        """
        org = get_organization_or_raise(self._orgs, organization_id)
        require_org_active_for_mutations(org)
        actor_m = require_active_membership(
            self._members, organization_id=organization_id, user_id=actor.user_id
        )
        require_permission(
            self._auth, member_id=actor_m.id, permission_code="member.invite"
        )
        invitation = self._get_invite(invitation_id, organization_id)
        if invitation.status != InvitationStatus.PENDING.value:
            raise ValidationError("only pending invitations can be resent")
        if ttl_days < 1 or ttl_days > MAX_INVITE_TTL_DAYS:
            raise ValidationError(
                f"ttl_days must be between 1 and {MAX_INVITE_TTL_DAYS}"
            )
        token = generate_invitation_token()
        expires = now() + timedelta(days=ttl_days)
        with transaction(self._conn):
            self._invites.update_status(
                invitation_id,
                InvitationStatus.REVOKED.value,
                organization_id=organization_id,
                revoked_by=actor.user_id,
            )
            replacement = self._invites.create(
                organization_id=organization_id,
                email=invitation.email_normalized,
                token_hash=token.token_hash,
                expires_at=expires,
                invited_by=actor.user_id,
                initial_role_code=invitation.initial_role_code,
            )
            audit(
                self._audits,
                action="invitation.resent",
                target_type="invitation",
                result="success",
                organization_id=organization_id,
                actor_user_id=actor.user_id,
                target_id=str(replacement.id),
                previous_values={"replaced_invitation_id": invitation_id},
                new_values={
                    "expires_at": str(expires),
                },
                request_id=actor.request_id,
            )
        delivery = self._deliver_invitation_email(
            invitation_id=replacement.id,
            organization_id=organization_id,
            org_name=org.display_name,
            email=invitation.email_normalized,
            role_code=invitation.initial_role_code,
            invite_token=token.plaintext,
            expires_at=expires,
            invited_by=actor.user_id,
        )
        return InvitationCreateResult(
            invitation=replacement,
            invite_token=token.plaintext,
            returned_once=True,
            email_delivery_status=delivery,
            events=[
                ev.evt(
                    ev.INVITATION_RESENT,
                    occurred_at=now(),
                    organization_id=organization_id,
                    actor_user_id=actor.user_id,
                    target_type="invitation",
                    target_id=str(replacement.id),
                    payload={"replaced_invitation_id": invitation_id},
                )
            ],
        )

    def _deliver_invitation_email(
        self,
        *,
        invitation_id: int,
        organization_id: int,
        org_name: str,
        email: str,
        role_code: str,
        invite_token: str,
        expires_at,
        invited_by: int,
    ) -> str:
        from app.packages.platform_ops.application.notify import notify_organization_invitation

        inviter_row = self._conn.execute(
            "SELECT username, email FROM app_user WHERE id = ?", [invited_by]
        ).fetchone()
        inviter_name = (
            str(inviter_row[0] or inviter_row[1]) if inviter_row else f"user:{invited_by}"
        )
        return notify_organization_invitation(
            self._conn,
            to_email=email,
            org_name=org_name,
            inviter_name=inviter_name,
            role_name=role_code,
            invite_token=invite_token,
            expires_label=str(expires_at),
            organization_id=organization_id,
            invitation_id=invitation_id,
        )

    def _get_invite(self, invitation_id: int, organization_id: int):
        try:
            return self._invites.get_by_id_in_organization(
                invitation_id, organization_id
            )
        except Exception as exc:
            from app.packages.organizations.domain.errors import NotFoundError

            if isinstance(exc, NotFoundError):
                raise InvitationNotFound(str(exc)) from exc
            raise

    def _assert_accept_preconditions(self, invitation, *, user_email: str) -> None:
        if invitation.status == InvitationStatus.REVOKED.value:
            raise InvitationRevoked("invitation revoked")
        if invitation.status == InvitationStatus.ACCEPTED.value:
            raise InvitationAlreadyUsed("invitation already accepted")
        if invitation.status == InvitationStatus.EXPIRED.value:
            raise InvitationExpired("invitation expired")
        if invitation.status != InvitationStatus.PENDING.value:
            raise ValidationError(f"invitation status={invitation.status}")
        if invitation.expires_at is not None and invitation.expires_at < now():
            raise InvitationExpired("invitation expired")
        # Anti-oracle: treat email mismatch like unknown token at the HTTP layer.
        if invitation.email_normalized != normalize_email(user_email):
            raise InvitationNotFound("invitation token not found")
