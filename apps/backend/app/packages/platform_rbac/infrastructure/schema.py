"""Platform RBAC schema — Spec 017.

Tables: app_platform_role, app_platform_permission,
        app_platform_role_permission, app_user_platform_role.

Idempotent CREATE IF NOT EXISTS + catalog seed.
Optional DEV CRM bootstrap users only when settings.seed_demo_crm_users_enabled
(SEED_DEMO_CRM_USERS + non-production). Never production.
No CRM roles assigned to existing admin/engineer/demo users.
"""

from __future__ import annotations

import json
import logging

import duckdb

from app.core.config import get_settings
from app.core.schema_bootstrap import schema_ready
from app.core.time_util import utc_now

from .catalogs import (
    PLATFORM_PERMISSIONS,
    PLATFORM_ROLES,
    PLATFORM_ROLE_PERMISSION_MATRIX,
)

logger = logging.getLogger("voxmetrik.platform_rbac.schema")

_PLATFORM_SCOPE = "platform"

PLATFORM_RBAC_TABLES = (
    "app_platform_role",
    "app_platform_permission",
    "app_platform_role_permission",
    "app_user_platform_role",
)


def ensure_platform_rbac_tables(conn: duckdb.DuckDBPyConnection) -> None:
    """Create platform RBAC tables, seed catalogs, optional DEV CRM users."""
    if schema_ready():
        # Additive re-seed when tables exist (isolated DBs may lack them).
        try:
            conn.execute("SELECT 1 FROM app_platform_role LIMIT 1").fetchone()
        except Exception:
            return
        _seed_platform_rbac_catalogs(conn)
        if get_settings().seed_demo_crm_users_enabled:
            _seed_demo_crm_users(conn)
        return

    _create_platform_role(conn)
    _create_platform_permission(conn)
    _create_platform_role_permission(conn)
    _create_user_platform_role(conn)

    _seed_platform_rbac_catalogs(conn)

    if get_settings().seed_demo_crm_users_enabled:
        _seed_demo_crm_users(conn)

    logger.info("Platform RBAC schema ensured (%s tables)", len(PLATFORM_RBAC_TABLES))


def _next_id(conn: duckdb.DuckDBPyConnection, table: str) -> int:
    row = conn.execute(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table}").fetchone()
    return int(row[0])


# ── Table creation ────────────────────────────────────────────────────────────

def _create_platform_role(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_platform_role (
            id            INTEGER PRIMARY KEY,
            code          VARCHAR NOT NULL UNIQUE,
            display_name  VARCHAR NOT NULL,
            description   VARCHAR NOT NULL,
            scope         VARCHAR NOT NULL DEFAULT 'platform',
            is_system     BOOLEAN NOT NULL DEFAULT TRUE,
            is_active     BOOLEAN NOT NULL DEFAULT TRUE,
            created_at    TIMESTAMP NOT NULL,
            updated_at    TIMESTAMP NOT NULL
        )
    """)


def _create_platform_permission(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_platform_permission (
            id           INTEGER PRIMARY KEY,
            code         VARCHAR NOT NULL UNIQUE,
            description  VARCHAR NOT NULL,
            domain       VARCHAR NOT NULL,
            is_active    BOOLEAN NOT NULL DEFAULT TRUE,
            created_at   TIMESTAMP NOT NULL,
            updated_at   TIMESTAMP NOT NULL
        )
    """)


def _create_platform_role_permission(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_platform_role_permission (
            id             INTEGER PRIMARY KEY,
            role_id        INTEGER NOT NULL,
            permission_id  INTEGER NOT NULL,
            created_at     TIMESTAMP NOT NULL,
            UNIQUE (role_id, permission_id)
        )
    """)


def _create_user_platform_role(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_user_platform_role (
            id           INTEGER PRIMARY KEY,
            user_id      INTEGER NOT NULL,
            role_id      INTEGER NOT NULL,
            status       VARCHAR NOT NULL DEFAULT 'active',
            assigned_by  INTEGER,
            assigned_at  TIMESTAMP NOT NULL,
            revoked_at   TIMESTAMP,
            UNIQUE (user_id, role_id),
            CHECK (status IN ('active', 'revoked'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_app_user_platform_role_user
        ON app_user_platform_role(user_id)
    """)


# ── Catalog seed ─────────────────────────────────────────────────────────────

def _seed_platform_rbac_catalogs(conn: duckdb.DuckDBPyConnection) -> None:
    now = utc_now()

    for code, display_name, description in PLATFORM_ROLES:
        exists = conn.execute(
            "SELECT 1 FROM app_platform_role WHERE code = ?", [code]
        ).fetchone()
        if exists:
            continue
        next_id = _next_id(conn, "app_platform_role")
        conn.execute(
            """
            INSERT INTO app_platform_role
                (id, code, display_name, description, scope, is_system, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, TRUE, TRUE, ?, ?)
            """,
            [next_id, code, display_name, description, _PLATFORM_SCOPE, now, now],
        )

    for code, description, domain in PLATFORM_PERMISSIONS:
        exists = conn.execute(
            "SELECT 1 FROM app_platform_permission WHERE code = ?", [code]
        ).fetchone()
        if exists:
            continue
        next_id = _next_id(conn, "app_platform_permission")
        conn.execute(
            """
            INSERT INTO app_platform_permission
                (id, code, description, domain, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, TRUE, ?, ?)
            """,
            [next_id, code, description, domain, now, now],
        )

    role_ids = {
        row[0]: int(row[1])
        for row in conn.execute("SELECT code, id FROM app_platform_role").fetchall()
    }
    perm_ids = {
        row[0]: int(row[1])
        for row in conn.execute("SELECT code, id FROM app_platform_permission").fetchall()
    }

    for role_code, perm_codes in PLATFORM_ROLE_PERMISSION_MATRIX.items():
        role_id = role_ids.get(role_code)
        if role_id is None:
            raise RuntimeError(f"Missing seeded platform role: {role_code}")
        for perm_code in sorted(perm_codes):
            perm_id = perm_ids.get(perm_code)
            if perm_id is None:
                raise RuntimeError(f"Missing seeded platform permission: {perm_code}")
            exists = conn.execute(
                "SELECT 1 FROM app_platform_role_permission WHERE role_id = ? AND permission_id = ?",
                [role_id, perm_id],
            ).fetchone()
            if exists:
                continue
            next_id = _next_id(conn, "app_platform_role_permission")
            conn.execute(
                "INSERT INTO app_platform_role_permission (id, role_id, permission_id, created_at) VALUES (?, ?, ?, ?)",
                [next_id, role_id, perm_id, now],
            )


# ── Demo CRM users ────────────────────────────────────────────────────────────

def _seed_demo_crm_users(conn: duckdb.DuckDBPyConnection) -> None:
    """Optional DEV bootstrap: sales_agent@ / sales_manager@ (not production).

    Only when seed_demo_crm_users_enabled. Prefer DEMO_ACCOUNT_PASSWORD when set;
    local fallbacks never run in production paths.
    Does NOT assign CRM roles to existing admin/engineer/demo users.
    """
    from app.packages.identity.services.password_security import hash_password
    import os

    now = utc_now()
    shared = (
        os.environ.get("DEMO_ACCOUNT_PASSWORD")
        or os.environ.get("DEMO_PASSWORD")
        or os.environ.get("VOXMETRIKS_DEMO_PASSWORD")
        or ""
    ).strip()

    crm_demo_users = [
        ("sales_agent_demo", "sales_agent@voxmetrik.io", shared or "demo123", "sales_agent"),
        ("sales_manager_demo", "sales_manager@voxmetrik.io", shared or "demo123", "sales_manager"),
    ]

    for username, email, pwd, platform_role_code in crm_demo_users:
        row = conn.execute("SELECT id FROM app_user WHERE email = ?", [email]).fetchone()
        if row:
            user_id = int(row[0])
        else:
            next_user_id = int(
                conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM app_user").fetchone()[0]
            )
            prefs = json.dumps({"dark_mode": False})
            conn.execute(
                """
                INSERT INTO app_user
                    (id, username, email, password_hash, role, plan, created_at, preferences_json)
                VALUES (?, ?, ?, ?, 'user', 'Free', ?, ?)
                """,
                [next_user_id, username, email, hash_password(pwd), now, prefs],
            )
            user_id = next_user_id
            logger.info("Seeded demo CRM user: %s (%s)", username, email)

        # Assign platform role (idempotent)
        _assign_platform_role_if_missing(conn, user_id=user_id, role_code=platform_role_code, now=now)


def _assign_platform_role_if_missing(
    conn: duckdb.DuckDBPyConnection,
    *,
    user_id: int,
    role_code: str,
    now,
    assigned_by: int | None = None,
) -> None:
    role_row = conn.execute(
        "SELECT id FROM app_platform_role WHERE code = ?", [role_code]
    ).fetchone()
    if not role_row:
        return
    role_id = int(role_row[0])

    exists = conn.execute(
        "SELECT 1 FROM app_user_platform_role WHERE user_id = ? AND role_id = ? AND status = 'active'",
        [user_id, role_id],
    ).fetchone()
    if exists:
        return

    # Check if there's a revoked record — update it
    revoked = conn.execute(
        "SELECT id FROM app_user_platform_role WHERE user_id = ? AND role_id = ?",
        [user_id, role_id],
    ).fetchone()
    if revoked:
        conn.execute(
            "UPDATE app_user_platform_role SET status = 'active', revoked_at = NULL, assigned_at = ? WHERE id = ?",
            [now, int(revoked[0])],
        )
        return

    next_id = _next_id(conn, "app_user_platform_role")
    conn.execute(
        """
        INSERT INTO app_user_platform_role
            (id, user_id, role_id, status, assigned_by, assigned_at)
        VALUES (?, ?, ?, 'active', ?, ?)
        """,
        [next_id, user_id, role_id, assigned_by, now],
    )
