"""Authorization catalog / member-role persistence."""

from __future__ import annotations

from typing import Any, Optional

import duckdb

from app.core.time_util import utc_now
from app.packages.organizations.domain.entities import MemberRole
from app.packages.organizations.domain.enums import MemberRoleStatus
from app.packages.organizations.domain.errors import NotFoundError, ValidationError
from app.packages.organizations.infrastructure.repositories._helpers import (
    next_id,
    raise_persistence,
)

_SELECT = """
    id, member_id, role_id, status, assigned_by, assigned_at, revoked_by, revoked_at
"""


def _map(row: tuple[Any, ...]) -> MemberRole:
    return MemberRole(
        id=int(row[0]),
        member_id=int(row[1]),
        role_id=int(row[2]),
        status=str(row[3]),
        assigned_by=int(row[4]),
        assigned_at=row[5],
        revoked_by=int(row[6]) if row[6] is not None else None,
        revoked_at=row[7],
    )


class AuthorizationRepository:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def list_member_roles(
        self, member_id: int, *, active_only: bool = True
    ) -> list[MemberRole]:
        if active_only:
            rows = self._conn.execute(
                f"""
                SELECT {_SELECT} FROM app_member_role
                WHERE member_id = ? AND status = ?
                ORDER BY id
                """,
                [member_id, MemberRoleStatus.ACTIVE.value],
            ).fetchall()
        else:
            rows = self._conn.execute(
                f"""
                SELECT {_SELECT} FROM app_member_role
                WHERE member_id = ?
                ORDER BY id
                """,
                [member_id],
            ).fetchall()
        return [_map(r) for r in rows]

    def _assert_member_in_org(
        self, member_id: int, organization_id: Optional[int]
    ) -> None:
        if organization_id is None:
            member = self._conn.execute(
                "SELECT 1 FROM app_organization_member WHERE id = ?", [member_id]
            ).fetchone()
            if not member:
                raise ValidationError(f"member id={member_id} does not exist")
            return
        member = self._conn.execute(
            """
            SELECT 1 FROM app_organization_member
            WHERE id = ? AND organization_id = ?
            """,
            [member_id, organization_id],
        ).fetchone()
        if not member:
            raise NotFoundError(
                f"member id={member_id} not in organization_id={organization_id}"
            )

    def assign_member_role(
        self,
        *,
        member_id: int,
        role_id: int,
        assigned_by: int,
        organization_id: Optional[int] = None,
    ) -> MemberRole:
        self._assert_member_in_org(member_id, organization_id)
        role = self._conn.execute(
            """
            SELECT 1 FROM app_business_role
            WHERE id = ? AND scope = 'organization' AND is_active = TRUE
            """,
            [role_id],
        ).fetchone()
        if not role:
            raise ValidationError(
                f"role id={role_id} is not an active organization business role"
            )

        existing = self._conn.execute(
            f"SELECT {_SELECT} FROM app_member_role WHERE member_id = ? AND role_id = ?",
            [member_id, role_id],
        ).fetchone()
        now = utc_now()
        if existing:
            current = _map(existing)
            if current.status == MemberRoleStatus.ACTIVE.value:
                return current
            try:
                if organization_id is not None:
                    self._conn.execute(
                        """
                        UPDATE app_member_role
                        SET status = ?, assigned_by = ?, assigned_at = ?,
                            revoked_by = NULL, revoked_at = NULL
                        WHERE id = ?
                          AND member_id IN (
                              SELECT id FROM app_organization_member
                              WHERE organization_id = ?
                          )
                        """,
                        [
                            MemberRoleStatus.ACTIVE.value,
                            assigned_by,
                            now,
                            current.id,
                            organization_id,
                        ],
                    )
                else:
                    self._conn.execute(
                        """
                        UPDATE app_member_role
                        SET status = ?, assigned_by = ?, assigned_at = ?,
                            revoked_by = NULL, revoked_at = NULL
                        WHERE id = ?
                        """,
                        [MemberRoleStatus.ACTIVE.value, assigned_by, now, current.id],
                    )
            except Exception as exc:
                raise_persistence(exc, action="reactivate member role")
            return _map(
                self._conn.execute(
                    f"SELECT {_SELECT} FROM app_member_role WHERE id = ?",
                    [current.id],
                ).fetchone()
            )

        role_row_id = next_id(self._conn, "app_member_role")
        try:
            self._conn.execute(
                """
                INSERT INTO app_member_role (
                    id, member_id, role_id, status, assigned_by, assigned_at,
                    revoked_by, revoked_at
                ) VALUES (?, ?, ?, ?, ?, ?, NULL, NULL)
                """,
                [
                    role_row_id,
                    member_id,
                    role_id,
                    MemberRoleStatus.ACTIVE.value,
                    assigned_by,
                    now,
                ],
            )
        except Exception as exc:
            raise_persistence(exc, action="assign member role")
        return _map(
            self._conn.execute(
                f"SELECT {_SELECT} FROM app_member_role WHERE id = ?",
                [role_row_id],
            ).fetchone()
        )

    def revoke_member_role(
        self,
        *,
        member_id: int,
        role_id: int,
        revoked_by: int,
        organization_id: Optional[int] = None,
    ) -> MemberRole:
        self._assert_member_in_org(member_id, organization_id)
        row = self._conn.execute(
            f"SELECT {_SELECT} FROM app_member_role WHERE member_id = ? AND role_id = ?",
            [member_id, role_id],
        ).fetchone()
        if not row:
            raise NotFoundError(
                f"member_role member_id={member_id} role_id={role_id}"
            )
        current = _map(row)
        if current.status == MemberRoleStatus.REVOKED.value:
            return current
        now = utc_now()
        try:
            if organization_id is not None:
                self._conn.execute(
                    """
                    UPDATE app_member_role
                    SET status = ?, revoked_by = ?, revoked_at = ?
                    WHERE id = ?
                      AND member_id IN (
                          SELECT id FROM app_organization_member
                          WHERE organization_id = ?
                      )
                    """,
                    [
                        MemberRoleStatus.REVOKED.value,
                        revoked_by,
                        now,
                        current.id,
                        organization_id,
                    ],
                )
            else:
                self._conn.execute(
                    """
                    UPDATE app_member_role
                    SET status = ?, revoked_by = ?, revoked_at = ?
                    WHERE id = ?
                    """,
                    [MemberRoleStatus.REVOKED.value, revoked_by, now, current.id],
                )
        except Exception as exc:
            raise_persistence(exc, action="revoke member role")
        return _map(
            self._conn.execute(
                f"SELECT {_SELECT} FROM app_member_role WHERE id = ?",
                [current.id],
            ).fetchone()
        )

    def list_role_permissions(self, role_id: int) -> list[str]:
        rows = self._conn.execute(
            """
            SELECT p.code
            FROM app_role_permission rp
            INNER JOIN app_permission p ON p.id = rp.permission_id
            WHERE rp.role_id = ?
              AND p.is_active = TRUE
            ORDER BY p.code
            """,
            [role_id],
        ).fetchall()
        return [str(r[0]) for r in rows]

    def member_has_permission(self, member_id: int, permission_code: str) -> bool:
        row = self._conn.execute(
            """
            SELECT 1
            FROM app_member_role mr
            INNER JOIN app_role_permission rp ON rp.role_id = mr.role_id
            INNER JOIN app_permission p ON p.id = rp.permission_id
            WHERE mr.member_id = ?
              AND mr.status = ?
              AND p.code = ?
              AND p.is_active = TRUE
            LIMIT 1
            """,
            [member_id, MemberRoleStatus.ACTIVE.value, permission_code],
        ).fetchone()
        return row is not None

    def get_role_id_by_code(self, code: str) -> Optional[int]:
        row = self._conn.execute(
            "SELECT id FROM app_business_role WHERE code = ?", [code]
        ).fetchone()
        return int(row[0]) if row else None

    def count_active_owners(self, organization_id: int) -> int:
        """Count members who are active AND hold an active owner role (SQL)."""
        row = self._conn.execute(
            """
            SELECT COUNT(*)
            FROM app_organization_member m
            INNER JOIN app_member_role mr
                ON mr.member_id = m.id AND mr.status = ?
            INNER JOIN app_business_role r
                ON r.id = mr.role_id AND r.code = 'owner' AND r.is_active = TRUE
            WHERE m.organization_id = ?
              AND m.status = ?
            """,
            [
                MemberRoleStatus.ACTIVE.value,
                organization_id,
                "active",
            ],
        ).fetchone()
        return int(row[0] or 0)

    def member_has_active_owner_role(self, member_id: int) -> bool:
        row = self._conn.execute(
            """
            SELECT 1
            FROM app_member_role mr
            INNER JOIN app_business_role r ON r.id = mr.role_id
            WHERE mr.member_id = ?
              AND mr.status = ?
              AND r.code = 'owner'
              AND r.is_active = TRUE
            LIMIT 1
            """,
            [member_id, MemberRoleStatus.ACTIVE.value],
        ).fetchone()
        return row is not None
