"""Membership use cases."""

from __future__ import annotations

import duckdb

from app.packages.organizations.application.dto import ActorContext, MutationResult
from app.packages.organizations.application.last_owner import (
    ensure_organization_has_active_owner_after_mutation,
)
from app.packages.organizations.application.services import (
    audit,
    get_organization_or_raise,
    now,
    require_active_membership,
    require_org_active_for_mutations,
    require_permission,
)
from app.packages.organizations.application.transactions import transaction
from app.packages.organizations.domain import events as ev
from app.packages.organizations.domain.enums import MembershipStatus
from app.packages.organizations.domain.errors import (
    MembershipNotFound,
    ValidationError,
)
from app.packages.organizations.domain.rules import assert_member_transition
from app.packages.organizations.infrastructure.repositories.audit_repository import (
    AuditRepository,
)
from app.packages.organizations.infrastructure.repositories.authorization_repository import (
    AuthorizationRepository,
)
from app.packages.organizations.infrastructure.repositories.membership_repository import (
    MembershipRepository,
)
from app.packages.organizations.infrastructure.repositories.organization_repository import (
    OrganizationRepository,
)
from app.packages.organizations.infrastructure.repositories.preference_repository import (
    PreferenceRepository,
)


def _clear_pref_if_matches(
    prefs: PreferenceRepository,
    *,
    user_id: int,
    organization_id: int,
    actor_user_id: int,
) -> None:
    pref = prefs.get_for_user(user_id)
    if pref and pref.active_organization_id == organization_id:
        prefs.clear_active_organization(user_id, updated_by=actor_user_id)


class MembershipUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn
        self._orgs = OrganizationRepository(conn)
        self._members = MembershipRepository(conn)
        self._auth = AuthorizationRepository(conn)
        self._audits = AuditRepository(conn)
        self._prefs = PreferenceRepository(conn)

    def get_membership(self, membership_id: int):
        try:
            return self._members.get_by_id(membership_id)
        except Exception as exc:
            from app.packages.organizations.domain.errors import NotFoundError

            if isinstance(exc, NotFoundError):
                raise MembershipNotFound(str(exc)) from exc
            raise

    def get_membership_in_org(self, membership_id: int, organization_id: int):
        try:
            return self._members.get_by_id_in_organization(
                membership_id, organization_id
            )
        except Exception as exc:
            from app.packages.organizations.domain.errors import NotFoundError

            if isinstance(exc, NotFoundError):
                raise MembershipNotFound(str(exc)) from exc
            raise

    def list_by_organization(
        self,
        actor: ActorContext,
        organization_id: int,
        *,
        limit: int | None = None,
        offset: int = 0,
    ):
        org = get_organization_or_raise(self._orgs, organization_id)
        membership = require_active_membership(
            self._members, organization_id=organization_id, user_id=actor.user_id
        )
        require_permission(
            self._auth, member_id=membership.id, permission_code="member.view"
        )
        _ = org
        return self._members.list_by_organization(
            organization_id, limit=limit, offset=offset
        )

    def count_by_organization(self, organization_id: int) -> int:
        return self._members.count_by_organization(organization_id)

    def list_organizations_for_user(self, user_id: int):
        return self._orgs.list_for_user(user_id)

    def suspend_member(
        self, actor: ActorContext, organization_id: int, target_member_id: int
    ) -> MutationResult:
        return self._change_member_status(
            actor,
            organization_id,
            target_member_id,
            MembershipStatus.SUSPENDED.value,
            permission="member.suspend",
            audit_action="member.suspended",
            event_name=ev.MEMBER_SUSPENDED,
            removes_owner_capacity=True,
        )

    def reactivate_member(
        self, actor: ActorContext, organization_id: int, target_member_id: int
    ) -> MutationResult:
        org = get_organization_or_raise(self._orgs, organization_id)
        require_org_active_for_mutations(org)
        actor_m = require_active_membership(
            self._members, organization_id=organization_id, user_id=actor.user_id
        )
        require_permission(
            self._auth, member_id=actor_m.id, permission_code="member.suspend"
        )
        target = self.get_membership_in_org(target_member_id, organization_id)
        assert_member_transition(target.status, MembershipStatus.ACTIVE.value)
        with transaction(self._conn):
            updated = self._members.update_status(
                target_member_id,
                MembershipStatus.ACTIVE.value,
                organization_id=organization_id,
            )
            audit(
                self._audits,
                action="member.reactivated",
                target_type="membership",
                result="success",
                organization_id=organization_id,
                actor_user_id=actor.user_id,
                target_id=str(target_member_id),
                previous_values={"status": target.status},
                new_values={"status": updated.status},
                request_id=actor.request_id,
            )
        return MutationResult(
            data=updated,
            events=[
                ev.evt(
                    ev.MEMBER_UNSUSPENDED,
                    occurred_at=now(),
                    organization_id=organization_id,
                    actor_user_id=actor.user_id,
                    target_type="membership",
                    target_id=str(target_member_id),
                )
            ],
        )

    def leave_organization(
        self, actor: ActorContext, organization_id: int
    ) -> MutationResult:
        org = get_organization_or_raise(self._orgs, organization_id)
        require_org_active_for_mutations(org)
        membership = require_active_membership(
            self._members, organization_id=organization_id, user_id=actor.user_id
        )
        assert_member_transition(membership.status, MembershipStatus.LEFT.value)
        with transaction(self._conn):
            ensure_organization_has_active_owner_after_mutation(
                self._auth,
                organization_id=organization_id,
                target_member_id=membership.id,
                mutation_removes_owner_capacity=True,
            )
            updated = self._members.update_status(
                membership.id,
                MembershipStatus.LEFT.value,
                organization_id=organization_id,
            )
            pref = self._prefs.get_for_user(actor.user_id)
            if pref and pref.active_organization_id == organization_id:
                self._prefs.clear_active_organization(
                    actor.user_id, updated_by=actor.user_id
                )
                audit(
                    self._audits,
                    action="organization_preference.cleared",
                    target_type="preference",
                    result="success",
                    organization_id=organization_id,
                    actor_user_id=actor.user_id,
                    target_id=str(actor.user_id),
                    reason="membership_left",
                    request_id=actor.request_id,
                )
            audit(
                self._audits,
                action="member.left",
                target_type="membership",
                result="success",
                organization_id=organization_id,
                actor_user_id=actor.user_id,
                target_id=str(membership.id),
                previous_values={"status": membership.status},
                new_values={"status": updated.status},
                request_id=actor.request_id,
            )
        return MutationResult(
            data=updated,
            events=[
                ev.evt(
                    ev.MEMBER_LEFT,
                    occurred_at=now(),
                    organization_id=organization_id,
                    actor_user_id=actor.user_id,
                    target_type="membership",
                    target_id=str(membership.id),
                )
            ],
        )

    def remove_member(
        self, actor: ActorContext, organization_id: int, target_member_id: int
    ) -> MutationResult:
        return self._change_member_status(
            actor,
            organization_id,
            target_member_id,
            MembershipStatus.REMOVED.value,
            permission="member.remove",
            audit_action="member.removed",
            event_name=ev.MEMBER_REMOVED,
            removes_owner_capacity=True,
            allow_from_suspended=True,
        )

    def _change_member_status(
        self,
        actor: ActorContext,
        organization_id: int,
        target_member_id: int,
        target_status: str,
        *,
        permission: str,
        audit_action: str,
        event_name: str,
        removes_owner_capacity: bool,
        allow_from_suspended: bool = False,
    ) -> MutationResult:
        org = get_organization_or_raise(self._orgs, organization_id)
        require_org_active_for_mutations(org)
        actor_m = require_active_membership(
            self._members, organization_id=organization_id, user_id=actor.user_id
        )
        require_permission(
            self._auth, member_id=actor_m.id, permission_code=permission
        )
        target = self.get_membership_in_org(target_member_id, organization_id)
        if target.user_id == actor.user_id and target_status == MembershipStatus.REMOVED.value:
            raise ValidationError("use leave for self-removal")
        assert_member_transition(target.status, target_status)
        if (
            not allow_from_suspended
            and target.status != MembershipStatus.ACTIVE.value
            and target_status == MembershipStatus.SUSPENDED.value
        ):
            raise ValidationError("only active members can be suspended")

        with transaction(self._conn):
            ensure_organization_has_active_owner_after_mutation(
                self._auth,
                organization_id=organization_id,
                target_member_id=target_member_id,
                mutation_removes_owner_capacity=removes_owner_capacity,
            )
            updated = self._members.update_status(
                target_member_id,
                target_status,
                organization_id=organization_id,
            )
            _clear_pref_if_matches(
                self._prefs,
                user_id=target.user_id,
                organization_id=organization_id,
                actor_user_id=actor.user_id,
            )
            audit(
                self._audits,
                action=audit_action,
                target_type="membership",
                result="success",
                organization_id=organization_id,
                actor_user_id=actor.user_id,
                target_id=str(target_member_id),
                previous_values={"status": target.status},
                new_values={"status": updated.status},
                request_id=actor.request_id,
            )
        return MutationResult(
            data=updated,
            events=[
                ev.evt(
                    event_name,
                    occurred_at=now(),
                    organization_id=organization_id,
                    actor_user_id=actor.user_id,
                    target_type="membership",
                    target_id=str(target_member_id),
                )
            ],
        )
