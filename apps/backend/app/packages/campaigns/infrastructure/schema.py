"""Campaigns schema — Spec 022.

Idempotent CREATE TABLE IF NOT EXISTS for all campaign tables.
Call after ensure_catalog_rights_tables and before mark_schema_ready.
"""

from __future__ import annotations

import logging

import duckdb

from app.core.schema_bootstrap import schema_ready

logger = logging.getLogger("voxmetrik.campaigns.schema")

CAMPAIGNS_TABLES = (
    "app_campaign",
    "app_campaign_objective",
    "app_campaign_target",
    "app_campaign_budget",
    "app_campaign_approval",
    "app_campaign_expense",
    "app_campaign_result",
    "app_attribution_definition",
    "app_attributable_revenue_record",
    "app_campaign_roi_snapshot",
    "app_campaign_status_history",
)


def ensure_campaign_tables(conn: duckdb.DuckDBPyConnection) -> None:
    """Create all campaigns tables (idempotent)."""
    if schema_ready():
        return

    _create_campaign(conn)
    _create_campaign_objective(conn)
    _create_campaign_target(conn)
    _create_campaign_budget(conn)
    _create_campaign_approval(conn)
    _create_campaign_expense(conn)
    _create_campaign_result(conn)
    _create_attribution_definition(conn)
    _create_attributable_revenue_record(conn)
    _create_campaign_roi_snapshot(conn)
    _create_campaign_status_history(conn)

    logger.info("Campaigns schema ensured (%s tables)", len(CAMPAIGNS_TABLES))


def _create_campaign(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_campaign (
            id                  INTEGER PRIMARY KEY,
            organization_id     INTEGER NOT NULL,
            name                VARCHAR NOT NULL,
            status              VARCHAR NOT NULL DEFAULT 'draft',
            market              VARCHAR,
            segment             VARCHAR,
            start_date          DATE,
            end_date            DATE,
            artist_profile_id   INTEGER,
            catalog_release_id  INTEGER,
            created_by          INTEGER,
            created_at          TIMESTAMP NOT NULL,
            updated_at          TIMESTAMP NOT NULL,
            CHECK (status IN (
                'draft', 'pending_approval', 'approved', 'active',
                'paused', 'completed', 'canceled'
            ))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_campaign_org
        ON app_campaign(organization_id)
    """)


def _create_campaign_objective(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_campaign_objective (
            id              INTEGER PRIMARY KEY,
            campaign_id     INTEGER NOT NULL,
            organization_id INTEGER NOT NULL,
            objective_type  VARCHAR NOT NULL,
            description     VARCHAR,
            priority        INTEGER NOT NULL DEFAULT 1,
            created_at      TIMESTAMP NOT NULL,
            updated_at      TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_campaign_objective_campaign
        ON app_campaign_objective(campaign_id)
    """)


def _create_campaign_target(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_campaign_target (
            id              INTEGER PRIMARY KEY,
            campaign_id     INTEGER NOT NULL,
            organization_id INTEGER NOT NULL,
            metric_code     VARCHAR NOT NULL,
            target_value    DOUBLE NOT NULL,
            unit            VARCHAR NOT NULL DEFAULT 'count',
            created_at      TIMESTAMP NOT NULL,
            updated_at      TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_campaign_target_campaign
        ON app_campaign_target(campaign_id)
    """)


def _create_campaign_budget(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_campaign_budget (
            id                  INTEGER PRIMARY KEY,
            campaign_id         INTEGER NOT NULL,
            organization_id     INTEGER NOT NULL,
            amount              DOUBLE NOT NULL,
            currency            VARCHAR NOT NULL,
            approval_threshold  DOUBLE,
            override_approved   BOOLEAN NOT NULL DEFAULT FALSE,
            override_reason     VARCHAR,
            override_by         INTEGER,
            override_at         TIMESTAMP,
            created_at          TIMESTAMP NOT NULL,
            updated_at          TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_campaign_budget_campaign
        ON app_campaign_budget(campaign_id)
    """)


def _create_campaign_approval(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_campaign_approval (
            id              INTEGER PRIMARY KEY,
            campaign_id     INTEGER NOT NULL,
            organization_id INTEGER NOT NULL,
            approval_type   VARCHAR NOT NULL DEFAULT 'launch',
            status          VARCHAR NOT NULL DEFAULT 'pending',
            requested_by    INTEGER NOT NULL,
            decided_by      INTEGER,
            decision_reason VARCHAR,
            requested_at    TIMESTAMP NOT NULL,
            decided_at      TIMESTAMP,
            created_at      TIMESTAMP NOT NULL,
            updated_at      TIMESTAMP NOT NULL,
            CHECK (status IN ('pending', 'approved', 'rejected')),
            CHECK (approval_type IN ('launch', 'budget_override', 'expense_override'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_campaign_approval_campaign
        ON app_campaign_approval(campaign_id)
    """)


def _create_campaign_expense(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_campaign_expense (
            id              INTEGER PRIMARY KEY,
            campaign_id     INTEGER NOT NULL,
            organization_id INTEGER NOT NULL,
            amount          DOUBLE NOT NULL,
            currency        VARCHAR NOT NULL,
            category        VARCHAR NOT NULL,
            description     VARCHAR,
            expense_date    DATE NOT NULL,
            recorded_by     INTEGER NOT NULL,
            override_id     INTEGER,
            created_at      TIMESTAMP NOT NULL,
            updated_at      TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_campaign_expense_campaign
        ON app_campaign_expense(campaign_id)
    """)


def _create_campaign_result(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_campaign_result (
            id              INTEGER PRIMARY KEY,
            campaign_id     INTEGER NOT NULL,
            organization_id INTEGER NOT NULL,
            metric_code     VARCHAR NOT NULL,
            value           DOUBLE NOT NULL,
            unit            VARCHAR NOT NULL DEFAULT 'count',
            is_monetary     BOOLEAN NOT NULL DEFAULT FALSE,
            period_start    DATE,
            period_end      DATE,
            source_label    VARCHAR,
            recorded_at     TIMESTAMP NOT NULL,
            created_at      TIMESTAMP NOT NULL,
            updated_at      TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_campaign_result_campaign
        ON app_campaign_result(campaign_id)
    """)


def _create_attribution_definition(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_attribution_definition (
            id              INTEGER PRIMARY KEY,
            campaign_id     INTEGER NOT NULL,
            organization_id INTEGER NOT NULL,
            version         INTEGER NOT NULL DEFAULT 1,
            model_code      VARCHAR NOT NULL,
            description     VARCHAR,
            confidence      DOUBLE NOT NULL,
            responsible     VARCHAR NOT NULL,
            status          VARCHAR NOT NULL DEFAULT 'draft',
            approved_by     INTEGER,
            approved_at     TIMESTAMP,
            created_at      TIMESTAMP NOT NULL,
            updated_at      TIMESTAMP NOT NULL,
            CHECK (status IN ('draft', 'approved', 'superseded')),
            CHECK (confidence >= 0 AND confidence <= 1)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_attribution_def_campaign
        ON app_attribution_definition(campaign_id)
    """)


def _create_attributable_revenue_record(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_attributable_revenue_record (
            id                        INTEGER PRIMARY KEY,
            campaign_id               INTEGER NOT NULL,
            organization_id           INTEGER NOT NULL,
            attribution_definition_id INTEGER NOT NULL,
            amount                    DOUBLE NOT NULL,
            currency                  VARCHAR NOT NULL,
            period_start              DATE NOT NULL,
            period_end                DATE NOT NULL,
            status                    VARCHAR NOT NULL DEFAULT 'pending',
            approved_by               INTEGER,
            approved_at               TIMESTAMP,
            created_at                TIMESTAMP NOT NULL,
            updated_at                TIMESTAMP NOT NULL,
            CHECK (status IN ('pending', 'approved', 'rejected'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_attr_revenue_campaign
        ON app_attributable_revenue_record(campaign_id)
    """)


def _create_campaign_roi_snapshot(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_campaign_roi_snapshot (
            id                        INTEGER PRIMARY KEY,
            campaign_id               INTEGER NOT NULL,
            organization_id           INTEGER NOT NULL,
            attribution_definition_id INTEGER,
            period_start              DATE,
            period_end                DATE,
            currency                  VARCHAR,
            status                    VARCHAR NOT NULL DEFAULT 'unavailable',
            roi_value                 DOUBLE,
            unavailable_reason        VARCHAR,
            cost_per_result           DOUBLE,
            budget_utilization        DOUBLE,
            goal_attainment           DOUBLE,
            engagement_lift           DOUBLE,
            computed_at               TIMESTAMP NOT NULL,
            computed_by               INTEGER,
            created_at                TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_campaign_roi_campaign
        ON app_campaign_roi_snapshot(campaign_id)
    """)


def _create_campaign_status_history(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_campaign_status_history (
            id              INTEGER PRIMARY KEY,
            campaign_id     INTEGER NOT NULL,
            organization_id INTEGER NOT NULL,
            from_status     VARCHAR,
            to_status       VARCHAR NOT NULL,
            reason          VARCHAR,
            actor_user_id   INTEGER,
            at              TIMESTAMP NOT NULL,
            created_at      TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_campaign_status_history_campaign
        ON app_campaign_status_history(campaign_id)
    """)
