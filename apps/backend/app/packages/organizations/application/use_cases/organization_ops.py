"""Update organization profile and lifecycle transitions."""

from __future__ import annotations

from typing import Optional

import duckdb

from app.packages.organizations.application.dto import ActorContext, MutationResult
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
from app.packages.organizations.domain.enums import OrganizationStatus
from app.packages.organizations.domain.errors import (
    InvalidOrganizationTransition,
    PermissionDenied,
    ValidationError,
)
from app.packages.organizations.domain.rules import assert_org_transition
from app.packages.organizations.infrastructure.org_profile_catalogs import (
    validate_country_code,
    validate_currency,
    validate_organization_type,
    validate_timezone,
)
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


class UpdateOrganizationProfile:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn
        self._orgs = OrganizationRepository(conn)
        self._members = MembershipRepository(conn)
        self._auth = AuthorizationRepository(conn)
        self._audits = AuditRepository(conn)

    def execute(
        self,
        actor: ActorContext,
        organization_id: int,
        *,
        display_name: Optional[str] = None,
        legal_name: Optional[str] = None,
        organization_type: Optional[str] = None,
        country_code: Optional[str] = None,
        timezone: Optional[str] = None,
        default_currency: Optional[str] = None,
    ) -> MutationResult:
        org = get_organization_or_raise(self._orgs, organization_id)
        require_org_active_for_mutations(org)
        membership = require_active_membership(
            self._members, organization_id=organization_id, user_id=actor.user_id
        )
        require_permission(
            self._auth, member_id=membership.id, permission_code="organization.update"
        )
        try:
            if organization_type is not None:
                organization_type = validate_organization_type(organization_type)
            if country_code is not None:
                country_code = validate_country_code(country_code)
            if timezone is not None:
                timezone = validate_timezone(timezone)
            if default_currency is not None:
                default_currency = validate_currency(default_currency)
        except ValueError as exc:
            raise ValidationError("invalid_catalog_value") from exc
        previous = {
            "display_name": org.display_name,
            "legal_name": org.legal_name,
            "organization_type": org.organization_type,
            "country_code": org.country_code,
            "timezone": org.timezone,
            "default_currency": org.default_currency,
        }
        with transaction(self._conn):
            updated = self._orgs.update_basic_fields(
                organization_id,
                display_name=display_name,
                legal_name=legal_name,
                organization_type=organization_type,
                country_code=country_code,
                timezone=timezone,
                default_currency=default_currency,
            )
            audit(
                self._audits,
                action="organization.updated",
                target_type="organization",
                result="success",
                organization_id=organization_id,
                actor_user_id=actor.user_id,
                target_id=str(organization_id),
                previous_values=previous,
                new_values={
                    "display_name": updated.display_name,
                    "legal_name": updated.legal_name,
                    "organization_type": updated.organization_type,
                    "country_code": updated.country_code,
                    "timezone": updated.timezone,
                    "default_currency": updated.default_currency,
                },
                request_id=actor.request_id,
            )
        return MutationResult(data=updated, events=[])


class ChangeOrganizationStatus:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn
        self._orgs = OrganizationRepository(conn)
        self._members = MembershipRepository(conn)
        self._auth = AuthorizationRepository(conn)
        self._audits = AuditRepository(conn)

    def execute(
        self,
        actor: ActorContext,
        organization_id: int,
        target_status: str,
        *,
        reason: Optional[str] = None,
    ) -> MutationResult:
        org = get_organization_or_raise(self._orgs, organization_id)
        assert_org_transition(org.status, target_status)

        if target_status == OrganizationStatus.SUSPENDED_BY_PLATFORM.value:
            if not actor.is_platform_operator:
                raise PermissionDenied("platform operator required to suspend")
            if not reason:
                raise ValidationError("reason required for platform suspend")
        elif (
            org.status == OrganizationStatus.SUSPENDED_BY_PLATFORM.value
            and target_status == OrganizationStatus.ACTIVE.value
        ):
            if not actor.is_platform_operator:
                raise PermissionDenied("platform operator required to reinstate")
            if not reason:
                raise ValidationError("reason required for reinstate")
        elif target_status == OrganizationStatus.CLOSED.value:
            if org.status == OrganizationStatus.SUSPENDED_BY_PLATFORM.value:
                if not actor.is_platform_operator:
                    raise PermissionDenied(
                        "platform operator required to close suspended org"
                    )
            else:
                membership = require_active_membership(
                    self._members,
                    organization_id=organization_id,
                    user_id=actor.user_id,
                )
                require_permission(
                    self._auth,
                    member_id=membership.id,
                    permission_code="organization.close",
                )
        else:
            raise InvalidOrganizationTransition(
                f"unsupported transition handler for {org.status} → {target_status}"
            )

        event_name = {
            OrganizationStatus.SUSPENDED_BY_PLATFORM.value: ev.ORGANIZATION_SUSPENDED,
            OrganizationStatus.ACTIVE.value: ev.ORGANIZATION_REINSTATED,
            OrganizationStatus.CLOSED.value: ev.ORGANIZATION_CLOSED,
        }.get(target_status, "OrganizationStatusChanged")

        with transaction(self._conn):
            updated = self._orgs.update_status(organization_id, target_status)
            audit(
                self._audits,
                action="organization.status_changed",
                target_type="organization",
                result="success",
                organization_id=organization_id,
                actor_user_id=actor.user_id,
                actor_platform_role=actor.platform_role,
                target_id=str(organization_id),
                previous_values={"status": org.status},
                new_values={"status": updated.status},
                reason=reason,
                request_id=actor.request_id,
            )
        event = ev.evt(
            event_name,
            occurred_at=now(),
            organization_id=organization_id,
            actor_user_id=actor.user_id,
            target_type="organization",
            target_id=str(organization_id),
        )
        return MutationResult(data=updated, events=[event])
