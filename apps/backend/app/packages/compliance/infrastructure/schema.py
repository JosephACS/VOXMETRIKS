"""Compliance schema — Spec 026."""

from __future__ import annotations

import logging

import duckdb

from app.core.schema_bootstrap import schema_ready

logger = logging.getLogger("voxmetrik.compliance.schema")

COMPLIANCE_TABLES = (
    "app_terms_version",
    "app_terms_acceptance",
    "app_consent_definition",
    "app_consent_record",
    "app_data_request",
    "app_data_request_action",
    "app_retention_policy",
    "app_retention_execution",
    "app_legal_hold",
    "app_security_incident",
    "app_incident_action",
    "app_sensitive_access_record",
)


def ensure_compliance_tables(conn: duckdb.DuckDBPyConnection) -> None:
    """Create all compliance tables (idempotent)."""
    if schema_ready():
        return

    _create_terms_version(conn)
    _create_terms_acceptance(conn)
    _create_consent_definition(conn)
    _create_consent_record(conn)
    _create_data_request(conn)
    _create_data_request_action(conn)
    _create_retention_policy(conn)
    _create_retention_execution(conn)
    _create_legal_hold(conn)
    _create_security_incident(conn)
    _create_incident_action(conn)
    _create_sensitive_access_record(conn)

    logger.info("Compliance schema ensured (%s tables)", len(COMPLIANCE_TABLES))


def _create_terms_version(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_terms_version (
            id              INTEGER PRIMARY KEY,
            version_code    VARCHAR NOT NULL,
            title           VARCHAR NOT NULL,
            content_summary VARCHAR NOT NULL,
            effective_at    TIMESTAMP NOT NULL,
            status          VARCHAR NOT NULL DEFAULT 'draft',
            created_by      INTEGER,
            created_at      TIMESTAMP NOT NULL,
            updated_at      TIMESTAMP NOT NULL,
            CHECK (status IN ('draft', 'published', 'archived'))
        )
    """)


def _create_terms_acceptance(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_terms_acceptance (
            id               INTEGER PRIMARY KEY,
            terms_version_id INTEGER NOT NULL,
            user_id          INTEGER NOT NULL,
            organization_id  INTEGER,
            accepted_at      TIMESTAMP NOT NULL,
            ip_address       VARCHAR,
            created_at       TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_terms_acceptance_user
        ON app_terms_acceptance(user_id)
    """)


def _create_consent_definition(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_consent_definition (
            id              INTEGER PRIMARY KEY,
            organization_id INTEGER,
            code            VARCHAR NOT NULL,
            title           VARCHAR NOT NULL,
            description     VARCHAR NOT NULL,
            is_required     BOOLEAN NOT NULL DEFAULT FALSE,
            status          VARCHAR NOT NULL DEFAULT 'active',
            created_at      TIMESTAMP NOT NULL,
            updated_at      TIMESTAMP NOT NULL,
            CHECK (status IN ('active', 'archived'))
        )
    """)


def _create_consent_record(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_consent_record (
            id                     INTEGER PRIMARY KEY,
            consent_definition_id  INTEGER NOT NULL,
            user_id                INTEGER NOT NULL,
            organization_id        INTEGER,
            status                 VARCHAR NOT NULL DEFAULT 'granted',
            granted_at             TIMESTAMP,
            withdrawn_at           TIMESTAMP,
            created_at             TIMESTAMP NOT NULL,
            updated_at             TIMESTAMP NOT NULL,
            CHECK (status IN ('granted', 'withdrawn', 'pending'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_consent_record_user
        ON app_consent_record(user_id)
    """)


def _create_data_request(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_data_request (
            id                 INTEGER PRIMARY KEY,
            organization_id    INTEGER NOT NULL,
            requester_user_id  INTEGER NOT NULL,
            request_type       VARCHAR NOT NULL,
            status             VARCHAR NOT NULL DEFAULT 'submitted',
            subject_user_id    INTEGER,
            reason             VARCHAR,
            requested_at       TIMESTAMP NOT NULL,
            completed_at       TIMESTAMP,
            created_at         TIMESTAMP NOT NULL,
            updated_at         TIMESTAMP NOT NULL,
            CHECK (request_type IN ('access', 'export', 'correction', 'deletion')),
            CHECK (status IN ('submitted', 'in_review', 'approved', 'rejected',
                              'completed', 'blocked'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_data_request_org
        ON app_data_request(organization_id)
    """)


def _create_data_request_action(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_data_request_action (
            id              INTEGER PRIMARY KEY,
            data_request_id INTEGER NOT NULL,
            organization_id INTEGER NOT NULL,
            action_type     VARCHAR NOT NULL,
            status          VARCHAR NOT NULL DEFAULT 'pending',
            actor_user_id   INTEGER NOT NULL,
            notes           VARCHAR,
            export_uri      VARCHAR,
            performed_at    TIMESTAMP NOT NULL,
            created_at      TIMESTAMP NOT NULL,
            CHECK (action_type IN ('review', 'export', 'correct', 'delete', 'reject', 'block')),
            CHECK (status IN ('pending', 'completed', 'failed'))
        )
    """)


def _create_retention_policy(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_retention_policy (
            id              INTEGER PRIMARY KEY,
            organization_id INTEGER NOT NULL,
            data_category   VARCHAR NOT NULL,
            retention_days  INTEGER NOT NULL,
            status          VARCHAR NOT NULL DEFAULT 'active',
            description     VARCHAR,
            created_by      INTEGER,
            created_at      TIMESTAMP NOT NULL,
            updated_at      TIMESTAMP NOT NULL,
            CHECK (status IN ('active', 'inactive')),
            CHECK (retention_days > 0)
        )
    """)


def _create_retention_execution(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_retention_execution (
            id                  INTEGER PRIMARY KEY,
            retention_policy_id INTEGER NOT NULL,
            organization_id     INTEGER NOT NULL,
            status              VARCHAR NOT NULL DEFAULT 'completed',
            records_evaluated   INTEGER NOT NULL DEFAULT 0,
            records_blocked     INTEGER NOT NULL DEFAULT 0,
            executed_at         TIMESTAMP NOT NULL,
            created_at          TIMESTAMP NOT NULL,
            CHECK (status IN ('completed', 'partial', 'failed'))
        )
    """)


def _create_legal_hold(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_legal_hold (
            id              INTEGER PRIMARY KEY,
            organization_id INTEGER NOT NULL,
            subject_type    VARCHAR NOT NULL,
            subject_id      VARCHAR NOT NULL,
            status          VARCHAR NOT NULL DEFAULT 'active',
            reason          VARCHAR NOT NULL,
            placed_by       INTEGER NOT NULL,
            placed_at       TIMESTAMP NOT NULL,
            released_at     TIMESTAMP,
            created_at      TIMESTAMP NOT NULL,
            updated_at      TIMESTAMP NOT NULL,
            CHECK (status IN ('active', 'released'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_legal_hold_org_subject
        ON app_legal_hold(organization_id, subject_type, subject_id)
    """)


def _create_security_incident(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_security_incident (
            id              INTEGER PRIMARY KEY,
            organization_id INTEGER,
            title           VARCHAR NOT NULL,
            severity        VARCHAR NOT NULL,
            status          VARCHAR NOT NULL DEFAULT 'open',
            description     VARCHAR NOT NULL,
            reported_by     INTEGER NOT NULL,
            reported_at     TIMESTAMP NOT NULL,
            resolved_at     TIMESTAMP,
            created_at      TIMESTAMP NOT NULL,
            updated_at      TIMESTAMP NOT NULL,
            CHECK (severity IN ('low', 'medium', 'high', 'critical')),
            CHECK (status IN ('open', 'investigating', 'contained', 'resolved', 'closed'))
        )
    """)


def _create_incident_action(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_incident_action (
            id              INTEGER PRIMARY KEY,
            incident_id     INTEGER NOT NULL,
            organization_id INTEGER,
            action_type     VARCHAR NOT NULL,
            description     VARCHAR NOT NULL,
            actor_user_id   INTEGER NOT NULL,
            performed_at    TIMESTAMP NOT NULL,
            created_at      TIMESTAMP NOT NULL
        )
    """)


def _create_sensitive_access_record(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_sensitive_access_record (
            id               INTEGER PRIMARY KEY,
            organization_id  INTEGER,
            accessor_user_id INTEGER NOT NULL,
            resource_type    VARCHAR NOT NULL,
            resource_id      VARCHAR NOT NULL,
            reason           VARCHAR NOT NULL,
            accessed_at      TIMESTAMP NOT NULL,
            created_at       TIMESTAMP NOT NULL
        )
    """)
