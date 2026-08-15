"""CreateOrganization — atomic provisioning + owner + activate."""

from __future__ import annotations

import hashlib
import json
import os
from typing import Optional

import duckdb

from app.packages.organizations.application.dto import (
    CreateOrganizationCommand,
    CreateOrganizationResult,
)
from app.packages.organizations.application.journey import ensure_onboarding_row
from app.packages.organizations.application.services import audit, now, require_user
from app.packages.organizations.application.transactions import transaction
from app.packages.organizations.domain import events as ev
from app.packages.organizations.domain.enums import OrganizationStatus
from app.packages.organizations.domain.errors import (
    CreateIntentConflict,
    NotFoundError,
    OrganizationSlugConflict,
    PersistenceError,
    ValidationError,
)
from app.packages.organizations.domain.rules import normalize_slug
from app.packages.organizations.infrastructure.org_profile_catalogs import (
    defaults_for_country,
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
from app.packages.organizations.infrastructure.repositories.preference_repository import (
    PreferenceRepository,
)
from app.packages.organizations.infrastructure.schema import ensure_organization_tables


def _payload_fingerprint(
    *,
    display_name: str,
    organization_type: str,
    country_code: Optional[str],
    timezone: str,
    default_currency: str,
    legal_name: Optional[str],
    slug: Optional[str],
    slug_explicit: bool,
) -> str:
    payload = {
        "country_code": country_code,
        "default_currency": default_currency,
        "display_name": display_name,
        "legal_name": legal_name,
        "organization_type": organization_type,
        "slug": slug if slug_explicit else None,
        "slug_explicit": bool(slug_explicit),
        "timezone": timezone,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class CreateOrganization:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn
        self._orgs = OrganizationRepository(conn)
        self._members = MembershipRepository(conn)
        self._auth = AuthorizationRepository(conn)
        self._prefs = PreferenceRepository(conn)
        self._audits = AuditRepository(conn)

    def execute(self, cmd: CreateOrganizationCommand) -> CreateOrganizationResult:
        ensure_organization_tables(self._conn)
        if not (cmd.display_name or "").strip():
            raise ValidationError("display_name is required")
        require_user(self._conn, cmd.actor.user_id)

        intent = (cmd.client_intent_id or cmd.idempotency_key or "").strip() or None

        try:
            org_type = validate_organization_type(cmd.organization_type)
            country = validate_country_code(cmd.country_code)
        except ValueError as exc:
            raise ValidationError("invalid_catalog_value") from exc

        tz_def, cur_def = defaults_for_country(country)
        tz_in = (cmd.timezone or "").strip()
        cur_in = (cmd.default_currency or "").strip()
        tz = tz_in or tz_def
        currency = cur_in or cur_def
        try:
            tz = validate_timezone(tz)
            currency = validate_currency(currency)
        except ValueError as exc:
            raise ValidationError("invalid_catalog_value") from exc

        display_name = cmd.display_name.strip()
        legal_name = (cmd.legal_name or "").strip() or None
        base_slug = normalize_slug(cmd.slug) if (cmd.slug or "").strip() else normalize_slug(
            display_name
        )
        fingerprint = _payload_fingerprint(
            display_name=display_name,
            organization_type=org_type,
            country_code=country,
            timezone=tz,
            default_currency=currency,
            legal_name=legal_name,
            slug=base_slug,
            slug_explicit=bool(cmd.slug_explicit),
        )

        events = []
        occurred = now()
        with transaction(self._conn):
            if intent:
                reused = self._reuse_by_intent(
                    user_id=cmd.actor.user_id,
                    intent=intent,
                    fingerprint=fingerprint,
                )
                if reused is not None:
                    return reused

            slug = self._allocate_slug(
                base_slug,
                slug_explicit=bool(cmd.slug_explicit),
                intent=intent,
            )

            created_under_pytest = bool(
                os.environ.get("PYTEST_CURRENT_TEST")
                or os.environ.get("VOXMETRIKS_TEST_ISOLATION") == "1"
            )
            org = self._orgs.create(
                display_name=display_name,
                slug=slug,
                organization_type=org_type,
                created_by=cmd.actor.user_id,
                timezone=tz,
                default_currency=currency,
                country_code=country,
                legal_name=legal_name,
                status=OrganizationStatus.PROVISIONING.value,
                is_demo=False,
                is_test=created_under_pytest,
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
            ensure_onboarding_row(self._conn, org.id)
            if intent:
                self._remember_intent(
                    cmd.actor.user_id, intent, org.id, fingerprint
                )
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
            idempotency_mode="client_intent" if intent else "slug_deterministic",
        )

    def _find_by_slug(self, slug: str):
        try:
            return self._orgs.get_by_slug(slug)
        except NotFoundError:
            return None

    def _allocate_slug(
        self,
        base_slug: str,
        *,
        slug_explicit: bool,
        intent: Optional[str],
    ) -> str:
        existing = self._find_by_slug(base_slug)
        if existing is None:
            return base_slug
        if slug_explicit:
            raise OrganizationSlugConflict(f"slug already taken: {base_slug}")
        # Autogenerated: stable suffix from intent when present; else numeric.
        candidates: list[str] = []
        if intent:
            digest = hashlib.sha256(intent.encode("utf-8")).hexdigest()[:8]
            candidates.append(f"{base_slug}-{digest}"[:64])
        for i in range(2, 1000):
            candidates.append(f"{base_slug}-{i}"[:64])
        for candidate in candidates:
            if self._find_by_slug(candidate) is None:
                return candidate
        raise OrganizationSlugConflict(f"slug already taken: {base_slug}")

    def _reuse_by_intent(
        self,
        *,
        user_id: int,
        intent: str,
        fingerprint: str,
    ) -> Optional[CreateOrganizationResult]:
        row = self._conn.execute(
            """
            SELECT organization_id, payload_fingerprint
            FROM app_organization_create_intent
            WHERE user_id = ? AND client_intent_id = ?
            """,
            [user_id, intent],
        ).fetchone()
        if not row:
            return None
        stored_fp = row[1]
        if stored_fp is not None and str(stored_fp) != fingerprint:
            raise CreateIntentConflict("client_intent_id payload mismatch")
        # Legacy rows without fingerprint: bind fingerprint on first re-use only when
        # organization still exists; mismatch path already covered when fingerprint set.
        if stored_fp is None:
            self._conn.execute(
                """
                UPDATE app_organization_create_intent
                SET payload_fingerprint = ?
                WHERE user_id = ? AND client_intent_id = ?
                """,
                [fingerprint, user_id, intent],
            )
        try:
            org = self._orgs.get_by_id(int(row[0]))
        except NotFoundError as exc:
            raise OrganizationSlugConflict("create conflict") from exc
        membership = self._members.get_by_org_and_user(org.id, user_id)
        if membership is None:
            raise OrganizationSlugConflict("create conflict")
        return CreateOrganizationResult(
            organization=org,
            membership=membership,
            events=[],
            reused_existing=True,
            idempotency_mode="client_intent",
        )

    def _remember_intent(
        self,
        user_id: int,
        intent: str,
        organization_id: int,
        fingerprint: str,
    ) -> None:
        exists = self._conn.execute(
            """
            SELECT 1 FROM app_organization_create_intent
            WHERE user_id = ? AND client_intent_id = ?
            """,
            [user_id, intent],
        ).fetchone()
        if exists:
            return
        self._conn.execute(
            """
            INSERT INTO app_organization_create_intent
                (user_id, client_intent_id, organization_id, payload_fingerprint, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            [user_id, intent, organization_id, fingerprint, now()],
        )
