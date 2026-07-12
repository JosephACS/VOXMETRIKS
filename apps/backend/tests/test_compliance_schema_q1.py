"""Test Q1: Compliance schema — Spec 026."""

from __future__ import annotations

import duckdb
import pytest


@pytest.fixture(scope="module")
def db_conn(tmp_path_factory):
    from app.core import schema_bootstrap

    previous = schema_bootstrap._schema_ready
    schema_bootstrap._schema_ready = False

    db_path = tmp_path_factory.mktemp("compliance_schema") / "test.duckdb"
    conn = duckdb.connect(str(db_path))

    from app.packages.identity.services.user_storage import ensure_user_tables
    from app.packages.organizations.infrastructure.schema import ensure_organization_tables
    from app.packages.compliance.infrastructure.schema import ensure_compliance_tables

    ensure_user_tables(conn)
    ensure_organization_tables(conn)
    ensure_compliance_tables(conn)

    schema_bootstrap._schema_ready = previous
    yield conn
    conn.close()


@pytest.mark.parametrize(
    "table",
    [
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
    ],
)
def test_compliance_table_exists(db_conn, table):
    db_conn.execute(f"SELECT id FROM {table} LIMIT 0")


def test_ensure_compliance_tables_idempotent(db_conn):
    from app.packages.compliance.infrastructure.schema import COMPLIANCE_TABLES, ensure_compliance_tables

    ensure_compliance_tables(db_conn)
    for table in COMPLIANCE_TABLES:
        count = db_conn.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
            [table],
        ).fetchone()[0]
        assert int(count) == 1


def test_data_request_type_check(db_conn):
    from app.core.time_util import utc_now

    now = utc_now()
    with pytest.raises(duckdb.ConstraintException):
        db_conn.execute(
            """
            INSERT INTO app_data_request
                (id, organization_id, requester_user_id, request_type, status,
                 subject_user_id, reason, requested_at, completed_at, created_at, updated_at)
            VALUES (1, 1, 1, 'invalid_type', 'submitted', 1, NULL, ?, NULL, ?, ?)
            """,
            [now, now, now],
        )
