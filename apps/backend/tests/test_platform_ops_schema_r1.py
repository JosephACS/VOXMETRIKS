"""Test R1: Platform ops schema — Spec 027."""

from __future__ import annotations

import duckdb
import pytest


@pytest.fixture(scope="module")
def db_conn(tmp_path_factory):
    from app.core import schema_bootstrap

    previous = schema_bootstrap._schema_ready
    schema_bootstrap._schema_ready = False

    db_path = tmp_path_factory.mktemp("platform_ops_schema") / "test.duckdb"
    conn = duckdb.connect(str(db_path))

    from app.packages.identity.services.user_storage import ensure_user_tables
    from app.packages.organizations.infrastructure.schema import ensure_organization_tables
    from app.packages.platform_ops.infrastructure.schema import ensure_platform_ops_tables

    ensure_user_tables(conn)
    ensure_organization_tables(conn)
    ensure_platform_ops_tables(conn)

    schema_bootstrap._schema_ready = previous
    yield conn
    conn.close()


@pytest.mark.parametrize(
    "table",
    [
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
    ],
)
def test_platform_ops_table_exists(db_conn, table):
    db_conn.execute(f"SELECT id FROM {table} LIMIT 0")


def test_webhook_idempotency_unique(db_conn):
    from app.core.time_util import utc_now

    now = utc_now()
    db_conn.execute(
        """
        INSERT INTO app_webhook_event
            (id, source, event_type, idempotency_key, payload_json, status, received_at, created_at)
        VALUES (1, 'billing', 'payment', 'key-1', '{}', 'received', ?, ?)
        """,
        [now, now],
    )
    with pytest.raises(duckdb.ConstraintException):
        db_conn.execute(
            """
            INSERT INTO app_webhook_event
                (id, source, event_type, idempotency_key, payload_json, status, received_at, created_at)
            VALUES (2, 'billing', 'payment', 'key-1', '{}', 'received', ?, ?)
            """,
            [now, now],
        )
