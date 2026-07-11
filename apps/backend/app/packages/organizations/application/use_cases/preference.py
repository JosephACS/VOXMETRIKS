"""Active organization preference (not an authorization source)."""

from __future__ import annotations

import duckdb

from app.packages.organizations.application.dto import (
    ActorContext,
    PreferenceResult,
)
from app.packages.organizations.application.services import (
    audit,
    get_organization_or_raise,
    now,
    require_user,
)
from app.packages.organizations.application.transactions import transaction
from app.packages.organizations.domain import events as ev
from app.packages.organizations.domain.enums import MembershipStatus, OrganizationStatus
from app.packages.organizations.domain.errors import InvalidActiveOrganization
from app.packages.organizations.infrastructure.repositories.audit_repository import (
    AuditRepository,
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


class PreferenceUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn
        self._orgs = OrganizationRepository(conn)
        self._members = MembershipRepository(conn)
        self._prefs = PreferenceRepository(conn)
        self._audits = AuditRepository(conn)

    def get(self, user_id: int):
        require_user(self._conn, user_id)
        return self._prefs.get_for_user(user_id)

    def set_active(
        self, actor: ActorContext, organization_id: int
    ) -> PreferenceResult:
        require_user(self._conn, actor.user_id)
        org = get_organization_or_raise(self._orgs, organization_id)
        if org.status != OrganizationStatus.ACTIVE.value:
            raise InvalidActiveOrganization(
                f"organization status={org.status} cannot be activated"
            )
        membership = self._members.get_by_org_and_user(
            organization_id, actor.user_id
        )
        if membership is None or membership.status != MembershipStatus.ACTIVE.value:
            raise InvalidActiveOrganization(
                "active membership required to set preference"
            )
        previous = self._prefs.get_for_user(actor.user_id)
        with transaction(self._conn):
            pref = self._prefs.set_active_organization(
                actor.user_id, organization_id, updated_by=actor.user_id
            )
            audit(
                self._audits,
                action="organization_preference.changed",
                target_type="preference",
                result="success",
                organization_id=organization_id,
                actor_user_id=actor.user_id,
                target_id=str(actor.user_id),
                previous_values={
                    "active_organization_id": (
                        previous.active_organization_id if previous else None
                    )
                },
                new_values={"active_organization_id": organization_id},
                request_id=actor.request_id,
            )
        return PreferenceResult(
            preference=pref,
            events=[
                ev.evt(
                    ev.ACTIVE_ORGANIZATION_CHANGED,
                    occurred_at=now(),
                    organization_id=organization_id,
                    actor_user_id=actor.user_id,
                    target_type="preference",
                    target_id=str(actor.user_id),
                )
            ],
        )

    def clear(self, actor: ActorContext) -> PreferenceResult:
        require_user(self._conn, actor.user_id)
        previous = self._prefs.get_for_user(actor.user_id)
        with transaction(self._conn):
            pref = self._prefs.clear_active_organization(
                actor.user_id, updated_by=actor.user_id
            )
            audit(
                self._audits,
                action="organization_preference.cleared",
                target_type="preference",
                result="success",
                organization_id=(
                    previous.active_organization_id if previous else None
                ),
                actor_user_id=actor.user_id,
                target_id=str(actor.user_id),
                previous_values={
                    "active_organization_id": (
                        previous.active_organization_id if previous else None
                    )
                },
                new_values={"active_organization_id": None},
                request_id=actor.request_id,
            )
        return PreferenceResult(
            preference=pref,
            events=[
                ev.evt(
                    ev.ACTIVE_ORGANIZATION_CLEARED,
                    occurred_at=now(),
                    actor_user_id=actor.user_id,
                    target_type="preference",
                    target_id=str(actor.user_id),
                )
            ],
        )
