"""CreateOrganization — atomic provisioning + owner + activate."""

from __future__ import annotations

import duckdb

from app.packages.organizations.application.dto import (
    CreateOrganizationCommand,
    CreateOrganizationResult,
)
from app.packages.organizations.application.services import audit, now, require_user
from app.packages.organizations.application.transactions import transaction
from app.packages.organizations.domain import events as ev
from app.packages.organizations.domain.enums import OrganizationStatus
from app.packages.organizations.domain.errors import (
    OrganizationSlugConflict,
    PersistenceError,
    ValidationError,
)
from app.packages.organizations.domain.rules import normalize_slug
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
from app.packages.organizations.domain.errors import NotFoundError


class CreateOrganization:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn
        self._orgs = OrganizationRepository(conn)
        self._members = MembershipRepository(conn)
        self._auth = AuthorizationRepository(conn)
        self._prefs = PreferenceRepository(conn)
        self._audits = AuditRepository(conn)

    def execute(self, cmd: CreateOrganizationCommand) -> CreateOrganizationResult:
        if not (cmd.display_name or "").strip():
            raise ValidationError("display_name is required")
        slug = normalize_slug(cmd.slug)
        require_user(self._conn, cmd.actor.user_id)

        existing = self._find_by_slug(slug)
        if existing is not None:
            if existing.created_by == cmd.actor.user_id:
                membership = self._members.get_by_org_and_user(
                    existing.id, cmd.actor.user_id
                )
                if membership is None:
                    raise OrganizationSlugConflict(f"slug already taken: {slug}")
                return CreateOrganizationResult(
                    organization=existing,
                    membership=membership,
                    events=[],
                    reused_existing=True,
                    idempotency_mode="slug_deterministic",
                )
            raise OrganizationSlugConflict(f"slug already taken: {slug}")

        events = []
        occurred = now()
        with transaction(self._conn):
            org = self._orgs.create(
                display_name=cmd.display_name.strip(),
                slug=slug,
                organization_type=cmd.organization_type,
                created_by=cmd.actor.user_id,
                timezone=cmd.timezone,
                default_currency=cmd.default_currency,
                country_code=cmd.country_code,
                legal_name=cmd.legal_name,
                status=OrganizationStatus.PROVISIONING.value,
                is_demo=False,
                closed_at=None,
            )
            events.append(
                ev.evt(
                    ev.ORGANIZATION_PROVISIONED,
                    occurred_at=occurred,
                    organization_id=org.id,
                    actor_user_id=cmd.actor.user_id,
                    target_type="organization",
                    target_id=str(org.id),
                )
            )
            membership = self._members.create(
                organization_id=org.id,
                user_id=cmd.actor.user_id,
                created_by=cmd.actor.user_id,
            )
            owner_role_id = self._auth.get_role_id_by_code("owner")
            if owner_role_id is None:
                raise PersistenceError("owner role missing from catalog")
            self._auth.assign_member_role(
                member_id=membership.id,
                role_id=owner_role_id,
                assigned_by=cmd.actor.user_id,
            )
            if self._auth.count_active_owners(org.id) < 1:
                raise PersistenceError("organization created without active owner")
            org = self._orgs.update_status(org.id, OrganizationStatus.ACTIVE.value)
            events.append(
                ev.evt(
                    ev.ORGANIZATION_ACTIVATED,
                    occurred_at=now(),
                    organization_id=org.id,
                    actor_user_id=cmd.actor.user_id,
                    target_type="organization",
                    target_id=str(org.id),
                )
            )
            events.append(
                ev.evt(
                    ev.MEMBER_JOINED,
                    occurred_at=now(),
                    organization_id=org.id,
                    actor_user_id=cmd.actor.user_id,
                    target_type="membership",
                    target_id=str(membership.id),
                )
            )
            if cmd.make_active:
                self._prefs.set_active_organization(
                    cmd.actor.user_id, org.id, updated_by=cmd.actor.user_id
                )
                events.append(
                    ev.evt(
                        ev.ACTIVE_ORGANIZATION_CHANGED,
                        occurred_at=now(),
                        organization_id=org.id,
                        actor_user_id=cmd.actor.user_id,
                        target_type="preference",
                        target_id=str(cmd.actor.user_id),
                    )
                )
            audit(
                self._audits,
                action="organization.created",
                target_type="organization",
                result="success",
                organization_id=org.id,
                actor_user_id=cmd.actor.user_id,
                actor_platform_role=cmd.actor.platform_role,
                target_id=str(org.id),
                new_values={
                    "slug": org.slug,
                    "display_name": org.display_name,
                    "status": org.status,
                },
                request_id=cmd.actor.request_id,
            )
            audit(
                self._audits,
                action="organization.status_changed",
                target_type="organization",
                result="success",
                organization_id=org.id,
                actor_user_id=cmd.actor.user_id,
                target_id=str(org.id),
                previous_values={"status": OrganizationStatus.PROVISIONING.value},
                new_values={"status": OrganizationStatus.ACTIVE.value},
                request_id=cmd.actor.request_id,
            )

        return CreateOrganizationResult(
            organization=org,
            membership=membership,
            events=events,
            reused_existing=False,
            idempotency_mode="slug_deterministic",
        )

    def _find_by_slug(self, slug: str):
        try:
            return self._orgs.get_by_slug(slug)
        except NotFoundError:
            return None
