"""Platform ops schema — Spec 027."""

from __future__ import annotations

import logging

import duckdb

from app.core.schema_bootstrap import schema_ready

logger = logging.getLogger("voxmetrik.platform_ops.schema")

PLATFORM_OPS_TABLES = (
    "app_notification",
    "app_notification_delivery",
    "app_provider_configuration",
    "app_webhook_event",
    "app_webhook_delivery",
    "app_background_job",
    "app_job_execution",
    "app_feature_flag",
    "app_operational_incident",
    "app_backup_record",
    "app_restore_verification",
)


def ensure_platform_ops_tables(conn: duckdb.DuckDBPyConnection) -> None:
    if schema_ready():
        from app.packages.platform_ops.application.email_service import ensure_email_delivery_table
        ensure_email_delivery_table(conn)
        return

    _create_notification(conn)
    _create_notification_delivery(conn)
    _create_provider_configuration(conn)
    _create_webhook_event(conn)
    _create_webhook_delivery(conn)
    _create_background_job(conn)
    _create_job_execution(conn)
    _create_feature_flag(conn)
    _create_operational_incident(conn)
    _create_backup_record(conn)
    _create_restore_verification(conn)
    from app.packages.platform_ops.application.email_service import ensure_email_delivery_table
    ensure_email_delivery_table(conn)

    logger.info("Platform ops schema ensured (%s tables)", len(PLATFORM_OPS_TABLES))


def _create_notification(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_notification (
            id          INTEGER PRIMARY KEY,
            channel     VARCHAR NOT NULL DEFAULT 'console',
            recipient   VARCHAR NOT NULL,
            subject     VARCHAR NOT NULL,
            body        VARCHAR NOT NULL,
            status      VARCHAR NOT NULL DEFAULT 'pending',
            created_at  TIMESTAMP NOT NULL,
            updated_at  TIMESTAMP NOT NULL,
            CHECK (status IN ('pending', 'sent', 'failed'))
        )
    """)


def _create_notification_delivery(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_notification_delivery (
            id               INTEGER PRIMARY KEY,
            notification_id  INTEGER NOT NULL,
            adapter_code     VARCHAR NOT NULL,
            status           VARCHAR NOT NULL DEFAULT 'pending',
            labeled_mock     BOOLEAN NOT NULL DEFAULT TRUE,
            delivered_at     TIMESTAMP,
            error_message    VARCHAR,
            created_at       TIMESTAMP NOT NULL,
            CHECK (status IN ('pending', 'delivered', 'failed'))
        )
    """)


def _create_provider_configuration(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_provider_configuration (
            id            INTEGER PRIMARY KEY,
            provider_code VARCHAR NOT NULL,
            display_name  VARCHAR NOT NULL,
            is_mock       BOOLEAN NOT NULL DEFAULT TRUE,
            secret_ref    VARCHAR,
            status        VARCHAR NOT NULL DEFAULT 'active',
            config_json   VARCHAR NOT NULL DEFAULT '{}',
            created_at    TIMESTAMP NOT NULL,
            updated_at    TIMESTAMP NOT NULL,
            CHECK (status IN ('active', 'inactive'))
        )
    """)


def _create_webhook_event(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_webhook_event (
            id               INTEGER PRIMARY KEY,
            source           VARCHAR NOT NULL,
            event_type       VARCHAR NOT NULL,
            idempotency_key  VARCHAR NOT NULL,
            payload_json     VARCHAR NOT NULL,
            status           VARCHAR NOT NULL DEFAULT 'received',
            received_at      TIMESTAMP NOT NULL,
            created_at       TIMESTAMP NOT NULL,
            CHECK (status IN ('received', 'processed', 'duplicate', 'failed'))
        )
    """)
    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_webhook_idempotency
        ON app_webhook_event(source, idempotency_key)
    """)


def _create_webhook_delivery(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_webhook_delivery (
            id               INTEGER PRIMARY KEY,
            webhook_event_id INTEGER NOT NULL,
            target_url       VARCHAR NOT NULL,
            status           VARCHAR NOT NULL DEFAULT 'pending',
            attempt_count    INTEGER NOT NULL DEFAULT 0,
            last_attempt_at  TIMESTAMP,
            response_code    INTEGER,
            created_at       TIMESTAMP NOT NULL,
            updated_at       TIMESTAMP NOT NULL,
            CHECK (status IN ('pending', 'delivered', 'failed', 'dead_letter'))
        )
    """)


def _create_background_job(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_background_job (
            id           INTEGER PRIMARY KEY,
            job_code     VARCHAR NOT NULL,
            display_name VARCHAR NOT NULL,
            status       VARCHAR NOT NULL DEFAULT 'active',
            max_retries  INTEGER NOT NULL DEFAULT 3,
            created_at   TIMESTAMP NOT NULL,
            updated_at   TIMESTAMP NOT NULL,
            CHECK (status IN ('active', 'paused', 'disabled'))
        )
    """)


def _create_job_execution(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_job_execution (
            id              INTEGER PRIMARY KEY,
            job_id          INTEGER NOT NULL,
            status          VARCHAR NOT NULL DEFAULT 'running',
            attempt_number  INTEGER NOT NULL DEFAULT 1,
            result_json     VARCHAR,
            error_message   VARCHAR,
            dead_letter     BOOLEAN NOT NULL DEFAULT FALSE,
            started_at      TIMESTAMP NOT NULL,
            finished_at     TIMESTAMP,
            created_at      TIMESTAMP NOT NULL,
            CHECK (status IN ('running', 'completed', 'failed', 'dead_letter'))
        )
    """)


def _create_feature_flag(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_feature_flag (
            id          INTEGER PRIMARY KEY,
            flag_key    VARCHAR NOT NULL,
            description VARCHAR NOT NULL,
            enabled     BOOLEAN NOT NULL DEFAULT FALSE,
            environment VARCHAR NOT NULL DEFAULT 'development',
            created_at  TIMESTAMP NOT NULL,
            updated_at  TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_feature_flag_key_env
        ON app_feature_flag(flag_key, environment)
    """)


def _create_operational_incident(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_operational_incident (
            id           INTEGER PRIMARY KEY,
            title        VARCHAR NOT NULL,
            severity     VARCHAR NOT NULL,
            status       VARCHAR NOT NULL DEFAULT 'open',
            description  VARCHAR NOT NULL,
            reported_by  INTEGER NOT NULL,
            reported_at  TIMESTAMP NOT NULL,
            resolved_at  TIMESTAMP,
            created_at   TIMESTAMP NOT NULL,
            updated_at   TIMESTAMP NOT NULL,
            CHECK (severity IN ('low', 'medium', 'high', 'critical')),
            CHECK (status IN ('open', 'investigating', 'resolved', 'closed'))
        )
    """)


def _create_backup_record(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_backup_record (
            id               INTEGER PRIMARY KEY,
            backup_type      VARCHAR NOT NULL,
            status           VARCHAR NOT NULL DEFAULT 'pending',
            file_path        VARCHAR NOT NULL,
            size_bytes       INTEGER NOT NULL DEFAULT 0,
            labeled_academic BOOLEAN NOT NULL DEFAULT TRUE,
            created_by       INTEGER NOT NULL,
            created_at       TIMESTAMP NOT NULL,
            completed_at     TIMESTAMP,
            CHECK (status IN ('pending', 'completed', 'failed')),
            CHECK (backup_type IN ('full', 'incremental', 'conceptual'))
        )
    """)


def _create_restore_verification(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_restore_verification (
            id                 INTEGER PRIMARY KEY,
            backup_record_id   INTEGER NOT NULL,
            status             VARCHAR NOT NULL DEFAULT 'pending',
            verification_notes VARCHAR NOT NULL,
            verified_by        INTEGER NOT NULL,
            verified_at        TIMESTAMP NOT NULL,
            created_at         TIMESTAMP NOT NULL,
            CHECK (status IN ('pending', 'passed', 'failed'))
        )
    """)
