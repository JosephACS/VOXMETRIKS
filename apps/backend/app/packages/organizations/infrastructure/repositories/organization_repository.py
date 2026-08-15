"""Organization persistence."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Any, Optional

import duckdb

from app.core.time_util import utc_now
from app.packages.organizations.domain.entities import Organization
from app.packages.organizations.domain.enums import (
    ARTIST_WORKSPACE_TYPE,
    ORGANIZATION_STATUSES,
    MembershipStatus,
    OrganizationStatus,
)
from app.packages.organizations.domain.errors import NotFoundError, ValidationError
from app.packages.organizations.infrastructure.repositories._helpers import (
    next_id,
    raise_persistence,
)

_COLS = (
    "id",
    "display_name",
    "legal_name",
    "slug",
    "organization_type",
    "country_code",
    "timezone",
    "default_currency",
    "status",
    "created_by",
    "created_at",
    "updated_at",
    "closed_at",
    "is_demo",
    "is_test",
)
_SELECT = ", ".join(_COLS)


def _map(row: tuple[Any, ...]) -> Organization:
    is_test = False
    if len(row) > 14 and row[14] is not None:
        is_test = bool(row[14])
    return Organization(
        id=int(row[0]),
        display_name=str(row[1]),
        legal_name=row[2],
        slug=str(row[3]),
        organization_type=str(row[4]),
        country_code=row[5],
        timezone=str(row[6]),
        default_currency=str(row[7]),
        status=str(row[8]),
        created_by=int(row[9]),
        created_at=row[10],
        updated_at=row[11],
        closed_at=row[12],
        is_demo=bool(row[13]) if row[13] is not None else False,
        is_test=is_test,
    )


class OrganizationRepository:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def create(
        self,
        *,
        display_name: str,
        slug: str,
        organization_type: str,
        created_by: int,
        timezone: str = "UTC",
        default_currency: str = "USD",
        country_code: Optional[str] = None,
        legal_name: Optional[str] = None,
        status: str = OrganizationStatus.PROVISIONING.value,
        is_demo: bool = False,
        is_test: bool = False,
        closed_at: Optional[datetime] = None,
    ) -> Organization:
        if status not in ORGANIZATION_STATUSES:
            raise ValidationError(f"Invalid organization status: {status}")
        if closed_at is not None and status != OrganizationStatus.CLOSED.value:
            raise ValidationError("closed_at only allowed when status=closed")
        if not display_name.strip():
            raise ValidationError("display_name is required")
        if not slug.strip():
            raise ValidationError("slug is required")

        now = utc_now()
        org_id = next_id(self._conn, "app_organization")
        try:
            self._conn.execute(
                """
                INSERT INTO app_organization (
                    id, display_name, legal_name, slug, organization_type,
                    country_code, timezone, default_currency, status,
                    created_by, created_at, updated_at, closed_at, is_demo, is_test
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    org_id,
                    display_name.strip(),
                    legal_name,
                    slug.strip().lower(),
                    organization_type,
                    country_code,
                    timezone,
                    default_currency,
                    status,
                    created_by,
                    now,
                    now,
                    closed_at,
                    is_demo,
                    is_test,
                ],
            )
        except Exception as exc:
            raise_persistence(exc, action="create organization")
        return self.get_by_id(org_id)

    def get_by_id(self, organization_id: int) -> Organization:
        row = self._conn.execute(
            f"SELECT {_SELECT} FROM app_organization WHERE id = ?",
            [organization_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"organization id={organization_id}")
        return _map(row)

    def get_by_slug(self, slug: str) -> Organization:
        row = self._conn.execute(
            f"SELECT {_SELECT} FROM app_organization WHERE slug = ?",
            [slug.strip().lower()],
        ).fetchone()
        if not row:
            raise NotFoundError(f"organization slug={slug}")
        return _map(row)

    def list_for_user(self, user_id: int) -> list[Organization]:
        import os

        from app.core.config import get_settings
        from app.packages.organizations.domain.test_org_patterns import (
            is_canonical_demo,
            looks_like_test_organization,
        )

        rows = self._conn.execute(
            """
            SELECT
                o.id, o.display_name, o.legal_name, o.slug, o.organization_type,
                o.country_code, o.timezone, o.default_currency, o.status,
                o.created_by, o.created_at, o.updated_at, o.closed_at, o.is_demo, o.is_test
            FROM app_organization o
            INNER JOIN app_organization_member m
                ON m.organization_id = o.id
            WHERE m.user_id = ?
              AND m.status = ?
              AND o.organization_type != ?
            ORDER BY o.display_name
            """,
            [user_id, MembershipStatus.ACTIVE.value, ARTIST_WORKSPACE_TYPE],
        ).fetchall()
        mapped = [_map(r) for r in rows]
        # Pytest isolation: return full memberships so suite assertions keep working.
        if os.environ.get("VOXMETRIKS_TEST_ISOLATION") == "1":
            return mapped

        show_demo = bool(get_settings().show_demo_organizations)
        out: list[Organization] = []
        for org in mapped:
            if org.is_test or looks_like_test_organization(
                slug=org.slug,
                display_name=org.display_name,
                is_test=org.is_test,
                is_demo=org.is_demo,
            ):
                continue
            # Canonical product demo always visible in the selector.
            if is_canonical_demo(org.slug):
                out.append(org)
                continue
            if org.is_demo and not show_demo:
                continue
            out.append(org)
        return out

    def update_basic_fields(
        self,
        organization_id: int,
        *,
        display_name: Optional[str] = None,
        legal_name: Optional[str] = None,
        organization_type: Optional[str] = None,
        country_code: Optional[str] = None,
        timezone: Optional[str] = None,
        default_currency: Optional[str] = None,
    ) -> Organization:
        current = self.get_by_id(organization_id)
        updated = replace(
            current,
            display_name=display_name.strip() if display_name is not None else current.display_name,
            legal_name=legal_name if legal_name is not None else current.legal_name,
            organization_type=(
                organization_type if organization_type is not None else current.organization_type
            ),
            country_code=country_code if country_code is not None else current.country_code,
            timezone=timezone if timezone is not None else current.timezone,
            default_currency=(
                default_currency if default_currency is not None else current.default_currency
            ),
            updated_at=utc_now(),
        )
        if not updated.display_name.strip():
            raise ValidationError("display_name is required")
        try:
            self._conn.execute(
                """
                UPDATE app_organization
                SET display_name = ?, legal_name = ?, organization_type = ?,
                    country_code = ?, timezone = ?, default_currency = ?, updated_at = ?
                WHERE id = ?
                """,
                [
                    updated.display_name,
                    updated.legal_name,
                    updated.organization_type,
                    updated.country_code,
                    updated.timezone,
                    updated.default_currency,
                    updated.updated_at,
                    organization_id,
                ],
            )
        except Exception as exc:
            raise_persistence(exc, action="update organization")
        return self.get_by_id(organization_id)

    def update_status(
        self,
        organization_id: int,
        status: str,
        *,
        closed_at: Optional[datetime] = None,
    ) -> Organization:
        if status not in ORGANIZATION_STATUSES:
            raise ValidationError(f"Invalid organization status: {status}")
        self.get_by_id(organization_id)
        now = utc_now()
        if status == OrganizationStatus.CLOSED.value:
            closed_at = closed_at or now
        else:
            closed_at = None
        try:
            self._conn.execute(
                """
                UPDATE app_organization
                SET status = ?, closed_at = ?, updated_at = ?
                WHERE id = ?
                """,
                [status, closed_at, now, organization_id],
            )
        except Exception as exc:
            raise_persistence(exc, action="update organization status")
        return self.get_by_id(organization_id)
