"""Role assignment and permission checks."""

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
    RoleNotFound,
    ValidationError,
)
from app.packages.organizations.domain.rules import is_platform_role_code
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


class RoleUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn
        self._orgs = OrganizationRepository(conn)
        self._members = MembershipRepository(conn)
        self._auth = AuthorizationRepository(conn)
        self._audits = AuditRepository(conn)

    def list_member_roles(
        self, actor: ActorContext, organization_id: int, member_id: int
    ):
        actor_m = require_active_membership(
            self._members, organization_id=organization_id, user_id=actor.user_id
        )
        require_permission(
            self._auth, member_id=actor_m.id, permission_code="role.view"
        )
        target = self._require_member_in_org(member_id, organization_id)
        return self._auth.list_member_roles(member_id)

    def _require_member_in_org(self, member_id: int, organization_id: int):
        try:
            target = self._members.get_by_id_in_organization(member_id, organization_id)
        except Exception as exc:
            from app.packages.organizations.domain.errors import NotFoundError

            if isinstance(exc, NotFoundError):
                raise MembershipNotFound(str(exc)) from exc
            raise
        return target

    def assign_member_role(
        self,
        actor: ActorContext,
        organization_id: int,
        member_id: int,
        role_code: str,
    ) -> MutationResult:
        org = get_organization_or_raise(self._orgs, organization_id)
        require_org_active_for_mutations(org)
        actor_m = require_active_membership(
            self._members, organization_id=organization_id, user_id=actor.user_id
        )
        require_permission(
            self._auth, member_id=actor_m.id, permission_code="role.assign"
        )
        target = self._require_member_in_org(member_id, organization_id)
        if target.status != MembershipStatus.ACTIVE.value:
            raise ValidationError("target member must be active")
        code = role_code.strip().lower()
        if is_platform_role_code(code):
            raise ValidationError("cannot assign platform roles")
        role_id = self._auth.get_role_id_by_code(code)
        if role_id is None:
            raise RoleNotFound(code)

        with transaction(self._conn):
            assigned = self._auth.assign_member_role(
                member_id=member_id,
                role_id=role_id,
                assigned_by=actor.user_id,
                organization_id=organization_id,
            )
            audit(
                self._audits,
                action="role.assigned",
                target_type="member_role",
                result="success",
                organization_id=organization_id,
                actor_user_id=actor.user_id,
                target_id=str(assigned.id),
                new_values={"member_id": member_id, "role_code": code},
                request_id=actor.request_id,
            )
        return MutationResult(
            data=assigned,
            events=[
                ev.evt(
                    ev.MEMBER_ROLE_ASSIGNED,
                    occurred_at=now(),
                    organization_id=organization_id,
                    actor_user_id=actor.user_id,
                    target_type="member_role",
                    target_id=str(assigned.id),
                    payload={"role_code": code},
                )
            ],
        )

    def revoke_member_role(
        self,
        actor: ActorContext,
        organization_id: int,
        member_id: int,
        role_code: str,
    ) -> MutationResult:
        org = get_organization_or_raise(self._orgs, organization_id)
        require_org_active_for_mutations(org)
        actor_m = require_active_membership(
            self._members, organization_id=organization_id, user_id=actor.user_id
        )
        require_permission(
            self._auth, member_id=actor_m.id, permission_code="role.assign"
        )
        self._require_member_in_org(member_id, organization_id)
        code = role_code.strip().lower()
        role_id = self._auth.get_role_id_by_code(code)
        if role_id is None:
            raise RoleNotFound(code)

        with transaction(self._conn):
            if code == "owner":
                ensure_organization_has_active_owner_after_mutation(
                    self._auth,
                    organization_id=organization_id,
                    target_member_id=member_id,
                    mutation_removes_owner_capacity=True,
                )
            revoked = self._auth.revoke_member_role(
                member_id=member_id,
                role_id=role_id,
                revoked_by=actor.user_id,
                organization_id=organization_id,
            )
            audit(
                self._audits,
                action="role.revoked",
                target_type="member_role",
                result="success",
                organization_id=organization_id,
                actor_user_id=actor.user_id,
                target_id=str(revoked.id),
                new_values={"member_id": member_id, "role_code": code},
                request_id=actor.request_id,
            )
        return MutationResult(
            data=revoked,
            events=[
                ev.evt(
                    ev.MEMBER_ROLE_REVOKED,
                    occurred_at=now(),
                    organization_id=organization_id,
                    actor_user_id=actor.user_id,
                    target_type="member_role",
                    target_id=str(revoked.id),
                    payload={"role_code": code},
                )
            ],
        )

    def member_has_permission(
        self,
        organization_id: int,
        user_id: int,
        permission_code: str,
    ) -> bool:
        """Deny-by-default permission check (active membership + active roles)."""
        membership = self._members.get_by_org_and_user(organization_id, user_id)
        if membership is None or membership.status != MembershipStatus.ACTIVE.value:
            return False
        org = get_organization_or_raise(self._orgs, organization_id)
        if org.status != "active":
            # Suspended/closed orgs: no mutation perms; view may be limited later.
            if permission_code.endswith(".view"):
                return self._auth.member_has_permission(
                    membership.id, permission_code
                )
            return False
        return self._auth.member_has_permission(membership.id, permission_code)
