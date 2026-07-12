"""Canonical DuckDB schema for organizations (Spec 016 I1).

Idempotent CREATE TABLE IF NOT EXISTS + additive ALTER.
Does not mutate identity tables or regenerate the warehouse.
"""

from __future__ import annotations

import logging

import duckdb

from app.core.database import get_table_columns, table_exists
from app.core.schema_bootstrap import schema_ready
from app.core.time_util import utc_now

from .catalogs import (
    BUSINESS_ROLES,
    ORGANIZATION_SCOPE,
    PERMISSIONS,
    ROLE_PERMISSION_MATRIX,
)

logger = logging.getLogger("voxmetrik.organizations.schema")

ORG_TABLES = (
    "app_organization",
    "app_organization_member",
    "app_organization_invitation",
    "app_business_role",
    "app_permission",
    "app_role_permission",
    "app_member_role",
    "app_user_organization_preference",
    "app_audit_log",
)


def ensure_organization_tables(conn: duckdb.DuckDBPyConnection) -> None:
    """Create organization tables and seed role catalogs (idempotent)."""
    if schema_ready():
        # Additive: keep catalogs current only when org tables already exist
        # (isolated temp DBs may share process-level schema_ready without tables).
        if table_exists(conn, "app_business_role") and table_exists(conn, "app_permission"):
            ensure_organization_role_catalogs(conn)
        return

    _create_organization(conn)
    _create_organization_member(conn)
    _create_organization_invitation(conn)
    _create_business_role(conn)
    _create_permission(conn)
    _create_role_permission(conn)
    _create_member_role(conn)
    _create_user_organization_preference(conn)
    _create_audit_log(conn)
    _apply_additive_columns(conn)
    ensure_organization_role_catalogs(conn)
    logger.info("Organization schema ensured (%s tables)", len(ORG_TABLES))


def ensure_organization_role_catalogs(conn: duckdb.DuckDBPyConnection) -> None:
    """Insert missing system roles, permissions, and mappings. No orgs/users."""
    now = utc_now()

    for code, display_name, description in BUSINESS_ROLES:
        exists = conn.execute(
            "SELECT 1 FROM app_business_role WHERE code = ?", [code]
        ).fetchone()
        if exists:
            continue
        next_id = _next_id(conn, "app_business_role")
        conn.execute(
            """
            INSERT INTO app_business_role (
                id, code, display_name, description, scope,
                is_system, is_active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, TRUE, TRUE, ?, ?)
            """,
            [next_id, code, display_name, description, ORGANIZATION_SCOPE, now, now],
        )

    for code, description, domain in PERMISSIONS:
        exists = conn.execute(
            "SELECT 1 FROM app_permission WHERE code = ?", [code]
        ).fetchone()
        if exists:
            continue
        next_id = _next_id(conn, "app_permission")
        conn.execute(
            """
            INSERT INTO app_permission (
                id, code, description, domain, is_active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, TRUE, ?, ?)
            """,
            [next_id, code, description, domain, now, now],
        )

    role_ids = {
        row[0]: int(row[1])
        for row in conn.execute("SELECT code, id FROM app_business_role").fetchall()
    }
    perm_ids = {
        row[0]: int(row[1])
        for row in conn.execute("SELECT code, id FROM app_permission").fetchall()
    }

    for role_code, perm_codes in ROLE_PERMISSION_MATRIX.items():
        role_id = role_ids.get(role_code)
        if role_id is None:
            raise RuntimeError(f"Missing seeded business role: {role_code}")
        for perm_code in sorted(perm_codes):
            perm_id = perm_ids.get(perm_code)
            if perm_id is None:
                raise RuntimeError(f"Missing seeded permission: {perm_code}")
            exists = conn.execute(
                """
                SELECT 1 FROM app_role_permission
                WHERE role_id = ? AND permission_id = ?
                """,
                [role_id, perm_id],
            ).fetchone()
            if exists:
                continue
            next_id = _next_id(conn, "app_role_permission")
            conn.execute(
                """
                INSERT INTO app_role_permission (id, role_id, permission_id, created_at)
                VALUES (?, ?, ?, ?)
                """,
                [next_id, role_id, perm_id, now],
            )


def _next_id(conn: duckdb.DuckDBPyConnection, table: str) -> int:
    row = conn.execute(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table}").fetchone()
    return int(row[0])


def _create_organization(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS app_organization (
            id                 INTEGER PRIMARY KEY,
            display_name       VARCHAR NOT NULL,
            legal_name         VARCHAR,
            slug               VARCHAR NOT NULL UNIQUE,
            organization_type  VARCHAR NOT NULL,
            country_code       VARCHAR,
            timezone           VARCHAR NOT NULL,
            default_currency   VARCHAR NOT NULL,
            status             VARCHAR NOT NULL,
            created_by         INTEGER NOT NULL,
            created_at         TIMESTAMP NOT NULL,
            updated_at         TIMESTAMP NOT NULL,
            closed_at          TIMESTAMP,
            is_demo            BOOLEAN DEFAULT FALSE,
            CHECK (status IN (
                'provisioning', 'active', 'suspended_by_platform', 'closed'
            )),
            CHECK (closed_at IS NULL OR status = 'closed')
        )
        """
    )
    # No secondary index on mutable `status` — DuckDB ART indexes cannot
    # overwrite indexed values on UPDATE (PK/UNIQUE/INDEX limitation).


def _create_organization_member(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS app_organization_member (
            id               INTEGER PRIMARY KEY,
            organization_id  INTEGER NOT NULL,
            user_id          INTEGER NOT NULL,
            status           VARCHAR NOT NULL,
            joined_at        TIMESTAMP,
            suspended_at     TIMESTAMP,
            left_at          TIMESTAMP,
            removed_at       TIMESTAMP,
            created_by       INTEGER NOT NULL,
            created_at       TIMESTAMP NOT NULL,
            updated_at       TIMESTAMP NOT NULL,
            UNIQUE (organization_id, user_id),
            CHECK (status IN ('active', 'suspended', 'left', 'removed'))
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_app_org_member_org
        ON app_organization_member(organization_id)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_app_org_member_user
        ON app_organization_member(user_id)
        """
    )


def _create_organization_invitation(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS app_organization_invitation (
            id                 INTEGER PRIMARY KEY,
            organization_id    INTEGER NOT NULL,
            email_normalized   VARCHAR NOT NULL,
            token_hash         VARCHAR NOT NULL,
            status             VARCHAR NOT NULL,
            expires_at         TIMESTAMP NOT NULL,
            invited_by         INTEGER NOT NULL,
            initial_role_code  VARCHAR NOT NULL,
            accepted_by        INTEGER,
            accepted_at        TIMESTAMP,
            revoked_by         INTEGER,
            revoked_at         TIMESTAMP,
            created_at         TIMESTAMP NOT NULL,
            updated_at         TIMESTAMP NOT NULL,
            CHECK (status IN ('pending', 'accepted', 'expired', 'revoked'))
        )
        """
    )
    # token_hash uniqueness enforced in InvitationRepository (DuckDB ART cannot
    # UPDATE rows that participate in a UNIQUE secondary index).
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_app_org_invitation_org_email
        ON app_organization_invitation(organization_id, email_normalized)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_app_org_invitation_token_hash
        ON app_organization_invitation(token_hash)
        """
    )


def _create_business_role(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS app_business_role (
            id            INTEGER PRIMARY KEY,
            code          VARCHAR NOT NULL UNIQUE,
            display_name  VARCHAR NOT NULL,
            description   VARCHAR NOT NULL,
            scope         VARCHAR NOT NULL,
            is_system     BOOLEAN NOT NULL DEFAULT TRUE,
            is_active     BOOLEAN NOT NULL DEFAULT TRUE,
            created_at    TIMESTAMP NOT NULL,
            updated_at    TIMESTAMP NOT NULL,
            CHECK (scope = 'organization')
        )
        """
    )


def _create_permission(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS app_permission (
            id           INTEGER PRIMARY KEY,
            code         VARCHAR NOT NULL UNIQUE,
            description  VARCHAR NOT NULL,
            domain       VARCHAR NOT NULL,
            is_active    BOOLEAN NOT NULL DEFAULT TRUE,
            created_at   TIMESTAMP NOT NULL,
            updated_at   TIMESTAMP NOT NULL
        )
        """
    )


def _create_role_permission(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS app_role_permission (
            id             INTEGER PRIMARY KEY,
            role_id        INTEGER NOT NULL,
            permission_id  INTEGER NOT NULL,
            created_at     TIMESTAMP NOT NULL,
            UNIQUE (role_id, permission_id)
        )
        """
    )


def _create_member_role(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS app_member_role (
            id           INTEGER PRIMARY KEY,
            member_id    INTEGER NOT NULL,
            role_id      INTEGER NOT NULL,
            status       VARCHAR NOT NULL,
            assigned_by  INTEGER NOT NULL,
            assigned_at  TIMESTAMP NOT NULL,
            revoked_by   INTEGER,
            revoked_at   TIMESTAMP,
            UNIQUE (member_id, role_id),
            CHECK (status IN ('active', 'revoked'))
        )
        """
    )


def _create_user_organization_preference(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS app_user_organization_preference (
            user_id                  INTEGER PRIMARY KEY,
            active_organization_id   INTEGER,
            updated_at               TIMESTAMP NOT NULL,
            updated_by               INTEGER
        )
        """
    )


def _create_audit_log(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS app_audit_log (
            id                     INTEGER PRIMARY KEY,
            organization_id        INTEGER,
            actor_user_id          INTEGER,
            actor_platform_role    VARCHAR,
            action                 VARCHAR NOT NULL,
            target_type            VARCHAR NOT NULL,
            target_id              VARCHAR,
            previous_values_json   VARCHAR,
            new_values_json        VARCHAR,
            reason                 VARCHAR,
            request_id             VARCHAR,
            source                 VARCHAR NOT NULL,
            result                 VARCHAR NOT NULL,
            occurred_at            TIMESTAMP NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_app_audit_log_org_time
        ON app_audit_log(organization_id, occurred_at)
        """
    )


def _apply_additive_columns(conn: duckdb.DuckDBPyConnection) -> None:
    """Additive ALTER only — never DROP tables/columns with data."""
    if table_exists(conn, "app_organization"):
        cols = get_table_columns(conn, "app_organization")
        if "is_demo" not in cols:
            conn.execute(
                "ALTER TABLE app_organization ADD COLUMN is_demo BOOLEAN DEFAULT FALSE"
            )
    # Drop mutable-column ART indexes created by earlier I1 drafts (UPDATE-safe).
    for index_name in (
        "idx_app_organization_status",
    ):
        try:
            conn.execute(f"DROP INDEX IF EXISTS {index_name}")
        except Exception:
            logger.debug("drop index %s skipped", index_name, exc_info=True)

    # Rebuild empty invitation table without UNIQUE(token_hash) for DuckDB UPDATE safety.
    if table_exists(conn, "app_organization_invitation"):
        count = int(
            conn.execute("SELECT COUNT(*) FROM app_organization_invitation").fetchone()[0]
        )
        if count == 0:
            conn.execute("DROP TABLE app_organization_invitation")
            _create_organization_invitation(conn)
