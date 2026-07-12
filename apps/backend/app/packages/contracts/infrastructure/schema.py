"""Commercial contract schema — Spec 017 (contracts package).

Table: app_commercial_contract
Owner: contracts package. CRM passes quotation_version_id + terms_snapshot into CreateContract.
Contracts must NOT import CRM use cases (only read data via passed parameters).
"""

from __future__ import annotations

import logging

import duckdb

from app.core.schema_bootstrap import schema_ready

logger = logging.getLogger("voxmetrik.contracts.schema")

CONTRACT_TABLES = ("app_commercial_contract",)


def ensure_commercial_contract_tables(conn: duckdb.DuckDBPyConnection) -> None:
    """Create contracts tables (idempotent)."""
    if schema_ready():
        return

    _create_commercial_contract(conn)
    logger.info("Contracts schema ensured (%s tables)", len(CONTRACT_TABLES))


def _create_commercial_contract(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_commercial_contract (
            id                   INTEGER PRIMARY KEY,
            quotation_version_id INTEGER NOT NULL,
            opportunity_id       INTEGER NOT NULL,
            organization_id      INTEGER,
            legal_name           VARCHAR NOT NULL,
            signatory_user_id    INTEGER,
            signatory_contact_id INTEGER,
            terms_snapshot       VARCHAR,
            status               VARCHAR NOT NULL DEFAULT 'draft',
            acceptance_evidence  VARCHAR,
            accepted_at          TIMESTAMP,
            rejected_at          TIMESTAMP,
            expired_at           TIMESTAMP,
            terminated_at        TIMESTAMP,
            termination_reason   VARCHAR,
            approved_by          INTEGER,
            approved_at          TIMESTAMP,
            approval_notes       VARCHAR,
            created_by           INTEGER NOT NULL,
            created_at           TIMESTAMP NOT NULL,
            updated_at           TIMESTAMP NOT NULL,
            CHECK (status IN (
                'draft', 'pending_approval', 'approved', 'sent',
                'accepted', 'rejected', 'expired', 'terminated'
            ))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_contract_opportunity
        ON app_commercial_contract(opportunity_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_contract_quotation_version
        ON app_commercial_contract(quotation_version_id)
    """)
