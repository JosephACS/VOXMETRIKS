"""Invitation persistence — stores token_hash only, never raw tokens."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

import duckdb

from app.core.time_util import utc_now
from app.packages.organizations.domain.entities import OrganizationInvitation
from app.packages.organizations.domain.enums import (
    INVITATION_STATUSES,
    InvitationStatus,
)
from app.packages.organizations.domain.errors import NotFoundError, ValidationError, DuplicateError
from app.packages.organizations.infrastructure.repositories._helpers import (
    next_id,
    raise_persistence,
)

_SELECT = """
    id, organization_id, email_normalized, token_hash, status, expires_at,
    invited_by, initial_role_code, accepted_by, accepted_at,
    revoked_by, revoked_at, created_at, updated_at
"""


def _map(row: tuple[Any, ...]) -> OrganizationInvitation:
    return OrganizationInvitation(
        id=int(row[0]),
        organization_id=int(row[1]),
        email_normalized=str(row[2]),
        token_hash=str(row[3]),
        status=str(row[4]),
        expires_at=row[5],
        invited_by=int(row[6]),
        initial_role_code=str(row[7]),
        accepted_by=int(row[8]) if row[8] is not None else None,
        accepted_at=row[9],
        revoked_by=int(row[10]) if row[10] is not None else None,
        revoked_at=row[11],
        created_at=row[12],
        updated_at=row[13],
    )


def normalize_email(email: str) -> str:
    return email.strip().lower()


class InvitationRepository:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def create(
        self,
        *,
        organization_id: int,
        email: str,
        token_hash: str,
        expires_at: datetime,
        invited_by: int,
        initial_role_code: str,
        status: str = InvitationStatus.PENDING.value,
    ) -> OrganizationInvitation:
        if status not in INVITATION_STATUSES:
            raise ValidationError(f"Invalid invitation status: {status}")
        if not token_hash.strip():
            raise ValidationError("token_hash is required")
        if expires_at is None:
            raise ValidationError("expires_at is required")

        org = self._conn.execute(
            "SELECT 1 FROM app_organization WHERE id = ?", [organization_id]
        ).fetchone()
        if not org:
            raise ValidationError(f"organization id={organization_id} does not exist")
        inviter = self._conn.execute(
            "SELECT 1 FROM app_user WHERE id = ?", [invited_by]
        ).fetchone()
        if not inviter:
            raise ValidationError(f"invited_by user id={invited_by} does not exist")
        role = self._conn.execute(
            "SELECT 1 FROM app_business_role WHERE code = ? AND is_active = TRUE",
            [initial_role_code],
        ).fetchone()
        if not role:
            raise ValidationError(f"initial_role_code={initial_role_code} not in catalog")

        email_normalized = normalize_email(email)
        if status == InvitationStatus.PENDING.value:
            active = self.find_active_by_org_and_email(organization_id, email_normalized)
            if active is not None:
                raise ValidationError(
                    "pending invitation already exists for organization/email"
                )
        dup_hash = self._conn.execute(
            "SELECT 1 FROM app_organization_invitation WHERE token_hash = ?",
            [token_hash],
        ).fetchone()
        if dup_hash:
            raise DuplicateError("token_hash already exists")

        now = utc_now()
        inv_id = next_id(self._conn, "app_organization_invitation")
        try:
            self._conn.execute(
                """
                INSERT INTO app_organization_invitation (
                    id, organization_id, email_normalized, token_hash, status,
                    expires_at, invited_by, initial_role_code,
                    accepted_by, accepted_at, revoked_by, revoked_at,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL, ?, ?)
                """,
                [
                    inv_id,
                    organization_id,
                    email_normalized,
                    token_hash,
                    status,
                    expires_at,
                    invited_by,
                    initial_role_code,
                    now,
                    now,
                ],
            )
        except Exception as exc:
            raise_persistence(exc, action="create invitation")
        return self.get_by_id(inv_id)

    def get_by_id(self, invitation_id: int) -> OrganizationInvitation:
        row = self._conn.execute(
            f"SELECT {_SELECT} FROM app_organization_invitation WHERE id = ?",
            [invitation_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"invitation id={invitation_id}")
        return _map(row)

    def get_by_token_hash(self, token_hash: str) -> Optional[OrganizationInvitation]:
        row = self._conn.execute(
            f"SELECT {_SELECT} FROM app_organization_invitation WHERE token_hash = ?",
            [token_hash],
        ).fetchone()
        return _map(row) if row else None

    def get_by_id_in_organization(
        self, invitation_id: int, organization_id: int
    ) -> OrganizationInvitation:
        row = self._conn.execute(
            f"""
            SELECT {_SELECT} FROM app_organization_invitation
            WHERE id = ? AND organization_id = ?
            """,
            [invitation_id, organization_id],
        ).fetchone()
        if not row:
            raise NotFoundError(
                f"invitation id={invitation_id} organization_id={organization_id}"
            )
        return _map(row)

    def list_by_organization(
        self,
        organization_id: int,
        *,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> list[OrganizationInvitation]:
        if limit is None:
            rows = self._conn.execute(
                f"""
                SELECT {_SELECT} FROM app_organization_invitation
                WHERE organization_id = ?
                ORDER BY id
                """,
                [organization_id],
            ).fetchall()
        else:
            lim = max(1, min(int(limit), 100))
            off = max(0, int(offset))
            rows = self._conn.execute(
                f"""
                SELECT {_SELECT} FROM app_organization_invitation
                WHERE organization_id = ?
                ORDER BY id
                LIMIT ? OFFSET ?
                """,
                [organization_id, lim, off],
            ).fetchall()
        return [_map(r) for r in rows]

    def count_by_organization(self, organization_id: int) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) FROM app_organization_invitation WHERE organization_id = ?",
            [organization_id],
        ).fetchone()
        return int(row[0] or 0)

    def find_active_by_org_and_email(
        self, organization_id: int, email: str
    ) -> Optional[OrganizationInvitation]:
        row = self._conn.execute(
            f"""
            SELECT {_SELECT} FROM app_organization_invitation
            WHERE organization_id = ?
              AND email_normalized = ?
              AND status = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            [
                organization_id,
                normalize_email(email),
                InvitationStatus.PENDING.value,
            ],
        ).fetchone()
        return _map(row) if row else None

    def update_status(
        self,
        invitation_id: int,
        status: str,
        *,
        organization_id: Optional[int] = None,
        accepted_by: Optional[int] = None,
        accepted_at: Optional[datetime] = None,
        revoked_by: Optional[int] = None,
        revoked_at: Optional[datetime] = None,
    ) -> OrganizationInvitation:
        if status not in INVITATION_STATUSES:
            raise ValidationError(f"Invalid invitation status: {status}")
        if organization_id is not None:
            self.get_by_id_in_organization(invitation_id, organization_id)
        else:
            self.get_by_id(invitation_id)
        now = utc_now()
        if status == InvitationStatus.ACCEPTED.value:
            accepted_at = accepted_at or now
        elif status == InvitationStatus.REVOKED.value:
            revoked_at = revoked_at or now
        try:
            if organization_id is not None:
                self._conn.execute(
                    """
                    UPDATE app_organization_invitation
                    SET status = ?,
                        accepted_by = COALESCE(?, accepted_by),
                        accepted_at = COALESCE(?, accepted_at),
                        revoked_by = COALESCE(?, revoked_by),
                        revoked_at = COALESCE(?, revoked_at),
                        updated_at = ?
                    WHERE id = ? AND organization_id = ?
                    """,
                    [
                        status,
                        accepted_by,
                        accepted_at,
                        revoked_by,
                        revoked_at,
                        now,
                        invitation_id,
                        organization_id,
                    ],
                )
            else:
                self._conn.execute(
                    """
                    UPDATE app_organization_invitation
                    SET status = ?,
                        accepted_by = COALESCE(?, accepted_by),
                        accepted_at = COALESCE(?, accepted_at),
                        revoked_by = COALESCE(?, revoked_by),
                        revoked_at = COALESCE(?, revoked_at),
                        updated_at = ?
                    WHERE id = ?
                    """,
                    [
                        status,
                        accepted_by,
                        accepted_at,
                        revoked_by,
                        revoked_at,
                        now,
                        invitation_id,
                    ],
                )
        except Exception as exc:
            raise_persistence(exc, action="update invitation status")
        if organization_id is not None:
            return self.get_by_id_in_organization(invitation_id, organization_id)
        return self.get_by_id(invitation_id)
