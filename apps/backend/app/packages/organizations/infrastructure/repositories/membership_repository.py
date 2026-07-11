"""Membership persistence (no physical delete)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

import duckdb

from app.core.time_util import utc_now
from app.packages.organizations.domain.entities import OrganizationMember
from app.packages.organizations.domain.enums import (
    MEMBERSHIP_STATUSES,
    MembershipStatus,
)
from app.packages.organizations.domain.errors import NotFoundError, ValidationError
from app.packages.organizations.infrastructure.repositories._helpers import (
    next_id,
    raise_persistence,
)

_SELECT = """
    id, organization_id, user_id, status, joined_at, suspended_at,
    left_at, removed_at, created_by, created_at, updated_at
"""


def _map(row: tuple[Any, ...]) -> OrganizationMember:
    return OrganizationMember(
        id=int(row[0]),
        organization_id=int(row[1]),
        user_id=int(row[2]),
        status=str(row[3]),
        joined_at=row[4],
        suspended_at=row[5],
        left_at=row[6],
        removed_at=row[7],
        created_by=int(row[8]),
        created_at=row[9],
        updated_at=row[10],
    )


class MembershipRepository:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def create(
        self,
        *,
        organization_id: int,
        user_id: int,
        created_by: int,
        status: str = MembershipStatus.ACTIVE.value,
        joined_at: Optional[datetime] = None,
    ) -> OrganizationMember:
        if status not in MEMBERSHIP_STATUSES:
            raise ValidationError(f"Invalid membership status: {status}")
        org = self._conn.execute(
            "SELECT 1 FROM app_organization WHERE id = ?", [organization_id]
        ).fetchone()
        if not org:
            raise ValidationError(f"organization id={organization_id} does not exist")
        user = self._conn.execute(
            "SELECT 1 FROM app_user WHERE id = ?", [user_id]
        ).fetchone()
        if not user:
            raise ValidationError(f"user id={user_id} does not exist")

        now = utc_now()
        member_id = next_id(self._conn, "app_organization_member")
        try:
            self._conn.execute(
                """
                INSERT INTO app_organization_member (
                    id, organization_id, user_id, status, joined_at,
                    suspended_at, left_at, removed_at, created_by, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, NULL, NULL, NULL, ?, ?, ?)
                """,
                [
                    member_id,
                    organization_id,
                    user_id,
                    status,
                    joined_at or now,
                    created_by,
                    now,
                    now,
                ],
            )
        except Exception as exc:
            raise_persistence(exc, action="create membership")
        return self.get_by_id(member_id)

    def get_by_id(self, member_id: int) -> OrganizationMember:
        row = self._conn.execute(
            f"SELECT {_SELECT} FROM app_organization_member WHERE id = ?",
            [member_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"membership id={member_id}")
        return _map(row)

    def get_by_org_and_user(
        self, organization_id: int, user_id: int
    ) -> Optional[OrganizationMember]:
        row = self._conn.execute(
            f"""
            SELECT {_SELECT} FROM app_organization_member
            WHERE organization_id = ? AND user_id = ?
            """,
            [organization_id, user_id],
        ).fetchone()
        return _map(row) if row else None

    def get_by_id_in_organization(
        self, member_id: int, organization_id: int
    ) -> OrganizationMember:
        row = self._conn.execute(
            f"""
            SELECT {_SELECT} FROM app_organization_member
            WHERE id = ? AND organization_id = ?
            """,
            [member_id, organization_id],
        ).fetchone()
        if not row:
            raise NotFoundError(
                f"membership id={member_id} organization_id={organization_id}"
            )
        return _map(row)

    def list_by_organization(
        self,
        organization_id: int,
        *,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> list[OrganizationMember]:
        if limit is None:
            rows = self._conn.execute(
                f"""
                SELECT {_SELECT} FROM app_organization_member
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
                SELECT {_SELECT} FROM app_organization_member
                WHERE organization_id = ?
                ORDER BY id
                LIMIT ? OFFSET ?
                """,
                [organization_id, lim, off],
            ).fetchall()
        return [_map(r) for r in rows]

    def count_by_organization(self, organization_id: int) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) FROM app_organization_member WHERE organization_id = ?",
            [organization_id],
        ).fetchone()
        return int(row[0] or 0)

    def list_by_user(self, user_id: int) -> list[OrganizationMember]:
        rows = self._conn.execute(
            f"""
            SELECT {_SELECT} FROM app_organization_member
            WHERE user_id = ?
            ORDER BY id
            """,
            [user_id],
        ).fetchall()
        return [_map(r) for r in rows]

    def update_status(
        self,
        member_id: int,
        status: str,
        *,
        organization_id: Optional[int] = None,
        suspended_at: Optional[datetime] = None,
        left_at: Optional[datetime] = None,
        removed_at: Optional[datetime] = None,
    ) -> OrganizationMember:
        if status not in MEMBERSHIP_STATUSES:
            raise ValidationError(f"Invalid membership status: {status}")
        if organization_id is not None:
            current = self.get_by_id_in_organization(member_id, organization_id)
        else:
            current = self.get_by_id(member_id)
        now = utc_now()
        if status == MembershipStatus.SUSPENDED.value:
            suspended_at = suspended_at or now
        elif status == MembershipStatus.LEFT.value:
            left_at = left_at or now
        elif status == MembershipStatus.REMOVED.value:
            removed_at = removed_at or now
        try:
            if organization_id is not None:
                self._conn.execute(
                    """
                    UPDATE app_organization_member
                    SET status = ?, suspended_at = COALESCE(?, suspended_at),
                        left_at = COALESCE(?, left_at),
                        removed_at = COALESCE(?, removed_at),
                        updated_at = ?
                    WHERE id = ? AND organization_id = ?
                    """,
                    [
                        status,
                        suspended_at,
                        left_at,
                        removed_at,
                        now,
                        member_id,
                        organization_id,
                    ],
                )
            else:
                self._conn.execute(
                    """
                    UPDATE app_organization_member
                    SET status = ?, suspended_at = COALESCE(?, suspended_at),
                        left_at = COALESCE(?, left_at),
                        removed_at = COALESCE(?, removed_at),
                        updated_at = ?
                    WHERE id = ?
                    """,
                    [status, suspended_at, left_at, removed_at, now, member_id],
                )
        except Exception as exc:
            raise_persistence(exc, action="update membership status")
        if organization_id is not None:
            return self.get_by_id_in_organization(member_id, organization_id)
        return self.get_by_id(member_id)
