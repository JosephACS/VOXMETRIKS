"""Platform RBAC repository — Spec 017.

Query helpers for platform-scoped role/permission checks.
assign_role is provided for tests and admin tooling only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import duckdb

if TYPE_CHECKING:
    pass


def has_permission(
    conn: duckdb.DuckDBPyConnection, user_id: int, permission_code: str
) -> bool:
    """Return True if the user holds an active platform role granting permission_code."""
    row = conn.execute(
        """
        SELECT 1
        FROM app_user_platform_role upr
        JOIN app_platform_role_permission rp ON rp.role_id = upr.role_id
        JOIN app_platform_permission pp ON pp.id = rp.permission_id
        WHERE upr.user_id = ?
          AND upr.status = 'active'
          AND pp.code = ?
          AND pp.is_active = TRUE
        LIMIT 1
        """,
        [user_id, permission_code],
    ).fetchone()
    return row is not None


def list_permissions(
    conn: duckdb.DuckDBPyConnection, user_id: int
) -> list[str]:
    """Return all distinct permission codes the user holds via active platform roles."""
    rows = conn.execute(
        """
        SELECT DISTINCT pp.code
        FROM app_user_platform_role upr
        JOIN app_platform_role_permission rp ON rp.role_id = upr.role_id
        JOIN app_platform_permission pp ON pp.id = rp.permission_id
        WHERE upr.user_id = ?
          AND upr.status = 'active'
          AND pp.is_active = TRUE
        ORDER BY pp.code
        """,
        [user_id],
    ).fetchall()
    return [str(r[0]) for r in rows]


def list_user_platform_roles(
    conn: duckdb.DuckDBPyConnection, user_id: int
) -> list[str]:
    """Return active platform role codes for a user."""
    rows = conn.execute(
        """
        SELECT pr.code
        FROM app_user_platform_role upr
        JOIN app_platform_role pr ON pr.id = upr.role_id
        WHERE upr.user_id = ? AND upr.status = 'active'
        ORDER BY pr.code
        """,
        [user_id],
    ).fetchall()
    return [str(r[0]) for r in rows]


def assign_role(
    conn: duckdb.DuckDBPyConnection,
    *,
    user_id: int,
    role_code: str,
    assigned_by: int | None = None,
) -> None:
    """Assign a platform role to a user (idempotent). For tests/admin tooling only."""
    from app.core.time_util import utc_now

    now = utc_now()

    role_row = conn.execute(
        "SELECT id FROM app_platform_role WHERE code = ?", [role_code]
    ).fetchone()
    if not role_row:
        raise ValueError(f"Unknown platform role: {role_code}")
    role_id = int(role_row[0])

    existing = conn.execute(
        "SELECT id, status FROM app_user_platform_role WHERE user_id = ? AND role_id = ?",
        [user_id, role_id],
    ).fetchone()

    if existing:
        if str(existing[1]) == "active":
            return
        conn.execute(
            "UPDATE app_user_platform_role SET status = 'active', revoked_at = NULL, assigned_at = ? WHERE id = ?",
            [now, int(existing[0])],
        )
        return

    next_id = int(
        conn.execute(
            "SELECT COALESCE(MAX(id), 0) + 1 FROM app_user_platform_role"
        ).fetchone()[0]
    )
    conn.execute(
        """
        INSERT INTO app_user_platform_role
            (id, user_id, role_id, status, assigned_by, assigned_at)
        VALUES (?, ?, ?, 'active', ?, ?)
        """,
        [next_id, user_id, role_id, assigned_by, now],
    )


def revoke_role(
    conn: duckdb.DuckDBPyConnection,
    *,
    user_id: int,
    role_code: str,
) -> None:
    """Revoke a platform role from a user (idempotent)."""
    from app.core.time_util import utc_now

    now = utc_now()
    conn.execute(
        """
        UPDATE app_user_platform_role
        SET status = 'revoked', revoked_at = ?
        WHERE user_id = ?
          AND role_id = (SELECT id FROM app_platform_role WHERE code = ?)
          AND status = 'active'
        """,
        [now, user_id, role_code],
    )
