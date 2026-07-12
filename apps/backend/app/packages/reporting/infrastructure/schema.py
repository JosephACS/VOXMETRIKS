"""Reporting schema — Spec 024."""

from __future__ import annotations

import logging

import duckdb

from app.core.schema_bootstrap import schema_ready

logger = logging.getLogger("voxmetrik.reporting.schema")

REPORTING_TABLES = (
    "app_report_definition",
    "app_report_generation",
    "app_report_snapshot",
    "app_report_section",
    "app_report_approval",
    "app_executive_report",
    "app_business_decision",
    "app_decision_action",
    "app_decision_follow_up",
)


def ensure_reporting_tables(conn: duckdb.DuckDBPyConnection) -> None:
    if schema_ready():
        return

    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_report_definition (
            id INTEGER PRIMARY KEY,
            organization_id INTEGER NOT NULL,
            code VARCHAR NOT NULL,
            title VARCHAR NOT NULL,
            description VARCHAR NOT NULL DEFAULT '',
            status VARCHAR NOT NULL DEFAULT 'active',
            default_period VARCHAR NOT NULL DEFAULT 'last_30d',
            created_by INTEGER,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            CHECK (status IN ('active', 'archived'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_report_def_org
        ON app_report_definition(organization_id)
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_report_generation (
            id INTEGER PRIMARY KEY,
            organization_id INTEGER NOT NULL,
            definition_id INTEGER NOT NULL,
            status VARCHAR NOT NULL DEFAULT 'requested',
            period_start VARCHAR,
            period_end VARCHAR,
            filters_json VARCHAR NOT NULL DEFAULT '{}',
            requested_by INTEGER,
            requested_at TIMESTAMP NOT NULL,
            completed_at TIMESTAMP,
            error_message VARCHAR,
            snapshot_id INTEGER,
            CHECK (status IN ('requested', 'generating', 'ready', 'failed', 'canceled'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_report_gen_org
        ON app_report_generation(organization_id)
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_report_snapshot (
            id INTEGER PRIMARY KEY,
            organization_id INTEGER NOT NULL,
            generation_id INTEGER NOT NULL,
            definition_id INTEGER NOT NULL,
            payload_json VARCHAR NOT NULL,
            kpi_versions_json VARCHAR NOT NULL DEFAULT '[]',
            unavailable_sources_json VARCHAR NOT NULL DEFAULT '[]',
            limitations VARCHAR NOT NULL DEFAULT '',
            generated_at TIMESTAMP NOT NULL,
            generated_by INTEGER
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_report_section (
            id INTEGER PRIMARY KEY,
            snapshot_id INTEGER NOT NULL,
            section_code VARCHAR NOT NULL,
            title VARCHAR NOT NULL,
            content_json VARCHAR NOT NULL DEFAULT '{}',
            sort_order INTEGER NOT NULL DEFAULT 0
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_executive_report (
            id INTEGER PRIMARY KEY,
            organization_id INTEGER NOT NULL,
            definition_id INTEGER NOT NULL,
            generation_id INTEGER NOT NULL,
            snapshot_id INTEGER NOT NULL,
            title VARCHAR NOT NULL,
            status VARCHAR NOT NULL DEFAULT 'draft',
            period_start VARCHAR,
            period_end VARCHAR,
            published_at TIMESTAMP,
            archived_at TIMESTAMP,
            created_by INTEGER,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            CHECK (status IN ('draft', 'pending_approval', 'approved', 'published', 'archived'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_exec_report_org
        ON app_executive_report(organization_id)
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_report_approval (
            id INTEGER PRIMARY KEY,
            executive_report_id INTEGER NOT NULL,
            decision VARCHAR NOT NULL,
            approved_by INTEGER,
            approved_at TIMESTAMP NOT NULL,
            comment VARCHAR,
            CHECK (decision IN ('approved', 'rejected'))
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_business_decision (
            id INTEGER PRIMARY KEY,
            organization_id INTEGER NOT NULL,
            executive_report_id INTEGER,
            title VARCHAR NOT NULL,
            proposal VARCHAR NOT NULL,
            status VARCHAR NOT NULL DEFAULT 'proposed',
            evidence_refs_json VARCHAR NOT NULL DEFAULT '[]',
            created_by INTEGER,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            completed_at TIMESTAMP,
            CHECK (status IN ('proposed', 'approved', 'in_progress', 'completed', 'canceled'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_biz_decision_org
        ON app_business_decision(organization_id)
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_decision_action (
            id INTEGER PRIMARY KEY,
            decision_id INTEGER NOT NULL,
            title VARCHAR NOT NULL,
            status VARCHAR NOT NULL DEFAULT 'planned',
            assignee_user_id INTEGER,
            due_at TIMESTAMP,
            completed_at TIMESTAMP,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            CHECK (status IN ('planned', 'in_progress', 'completed', 'canceled'))
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_decision_follow_up (
            id INTEGER PRIMARY KEY,
            decision_id INTEGER NOT NULL,
            note VARCHAR NOT NULL,
            created_by INTEGER,
            created_at TIMESTAMP NOT NULL
        )
    """)

    logger.info("Reporting schema ensured (%s tables)", len(REPORTING_TABLES))
