"""Customer Success & Support schema — Spec 025."""

from __future__ import annotations

import logging

import duckdb

from app.core.schema_bootstrap import schema_ready
from app.core.time_util import utc_now

logger = logging.getLogger("voxmetrik.customer_success.schema")

CS_TABLES = (
    "app_customer_onboarding",
    "app_customer_onboarding_step",
    "app_customer_health_definition",
    "app_customer_health_snapshot",
    "app_customer_risk",
    "app_customer_intervention",
    "app_renewal_readiness",
    "app_expansion_opportunity",
    "app_support_case",
    "app_support_message",
    "app_support_assignment",
    "app_support_sla_policy",
    "app_support_sla_event",
    "app_support_satisfaction",
)


def ensure_customer_success_tables(conn: duckdb.DuckDBPyConnection) -> None:
    if schema_ready():
        return

    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_customer_onboarding (
            id INTEGER PRIMARY KEY,
            organization_id INTEGER NOT NULL,
            status VARCHAR NOT NULL DEFAULT 'not_started',
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            created_by INTEGER,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            CHECK (status IN ('not_started','in_progress','blocked','completed','canceled'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_customer_onboarding_step (
            id INTEGER PRIMARY KEY,
            onboarding_id INTEGER NOT NULL,
            step_code VARCHAR NOT NULL,
            title VARCHAR NOT NULL,
            status VARCHAR NOT NULL DEFAULT 'pending',
            blocked_reason VARCHAR,
            completed_at TIMESTAMP,
            sort_order INTEGER NOT NULL DEFAULT 0,
            CHECK (status IN ('pending','in_progress','blocked','completed','canceled'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_customer_health_definition (
            id INTEGER PRIMARY KEY,
            organization_id INTEGER,
            code VARCHAR NOT NULL,
            version INTEGER NOT NULL,
            name VARCHAR NOT NULL,
            formula_json VARCHAR NOT NULL,
            weights_json VARCHAR NOT NULL,
            null_handling VARCHAR NOT NULL DEFAULT 'unavailable',
            status VARCHAR NOT NULL DEFAULT 'active',
            limitations VARCHAR NOT NULL DEFAULT '',
            created_at TIMESTAMP NOT NULL,
            CHECK (status IN ('active','archived'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_customer_health_snapshot (
            id INTEGER PRIMARY KEY,
            organization_id INTEGER NOT NULL,
            definition_id INTEGER NOT NULL,
            score DOUBLE,
            score_state VARCHAR NOT NULL,
            confidence DOUBLE,
            components_json VARCHAR NOT NULL DEFAULT '{}',
            limitations VARCHAR NOT NULL DEFAULT '',
            generated_at TIMESTAMP NOT NULL,
            generated_by INTEGER,
            CHECK (score_state IN ('healthy','watch','risk','critical','insufficient_data','No disponible'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_customer_risk (
            id INTEGER PRIMARY KEY,
            organization_id INTEGER NOT NULL,
            title VARCHAR NOT NULL,
            status VARCHAR NOT NULL DEFAULT 'open',
            severity VARCHAR NOT NULL DEFAULT 'medium',
            description VARCHAR NOT NULL DEFAULT '',
            created_by INTEGER,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            CHECK (status IN ('open','monitoring','intervention_required','mitigated','closed'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_customer_intervention (
            id INTEGER PRIMARY KEY,
            organization_id INTEGER NOT NULL,
            risk_id INTEGER,
            title VARCHAR NOT NULL,
            status VARCHAR NOT NULL DEFAULT 'planned',
            assignee_user_id INTEGER,
            completed_at TIMESTAMP,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            CHECK (status IN ('planned','in_progress','completed','canceled'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_renewal_readiness (
            id INTEGER PRIMARY KEY,
            organization_id INTEGER NOT NULL,
            readiness_state VARCHAR NOT NULL,
            score DOUBLE,
            notes VARCHAR NOT NULL DEFAULT '',
            evaluated_at TIMESTAMP NOT NULL,
            evaluated_by INTEGER
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_expansion_opportunity (
            id INTEGER PRIMARY KEY,
            organization_id INTEGER NOT NULL,
            title VARCHAR NOT NULL,
            status VARCHAR NOT NULL DEFAULT 'identified',
            estimated_value DOUBLE,
            notes VARCHAR NOT NULL DEFAULT '',
            created_by INTEGER,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_support_case (
            id INTEGER PRIMARY KEY,
            organization_id INTEGER NOT NULL,
            subject VARCHAR NOT NULL,
            category VARCHAR NOT NULL DEFAULT 'general',
            priority VARCHAR NOT NULL DEFAULT 'normal',
            status VARCHAR NOT NULL DEFAULT 'open',
            requester_user_id INTEGER,
            assignee_user_id INTEGER,
            resolved_at TIMESTAMP,
            closed_at TIMESTAMP,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            CHECK (priority IN ('low','normal','high','urgent')),
            CHECK (status IN ('open','triaged','assigned','in_progress','waiting_customer',
                              'escalated','resolved','closed','reopened'))
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_support_case_org ON app_support_case(organization_id)")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_support_message (
            id INTEGER PRIMARY KEY,
            case_id INTEGER NOT NULL,
            author_user_id INTEGER,
            body VARCHAR NOT NULL,
            is_internal BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_support_assignment (
            id INTEGER PRIMARY KEY,
            case_id INTEGER NOT NULL,
            assignee_user_id INTEGER NOT NULL,
            assigned_by INTEGER,
            assigned_at TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_support_sla_policy (
            id INTEGER PRIMARY KEY,
            organization_id INTEGER NOT NULL,
            name VARCHAR NOT NULL,
            priority VARCHAR NOT NULL,
            response_minutes INTEGER NOT NULL,
            resolve_minutes INTEGER NOT NULL,
            status VARCHAR NOT NULL DEFAULT 'active',
            academic_label VARCHAR NOT NULL DEFAULT 'academic_configuration_not_contractual'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_support_sla_event (
            id INTEGER PRIMARY KEY,
            case_id INTEGER NOT NULL,
            policy_id INTEGER,
            event_type VARCHAR NOT NULL,
            due_at TIMESTAMP,
            occurred_at TIMESTAMP NOT NULL,
            met BOOLEAN
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_support_satisfaction (
            id INTEGER PRIMARY KEY,
            case_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            comment VARCHAR,
            recorded_by INTEGER,
            recorded_at TIMESTAMP NOT NULL,
            CHECK (score BETWEEN 1 AND 5)
        )
    """)

    # Seed default health definition (rule-based, not AI)
    existing = conn.execute(
        "SELECT id FROM app_customer_health_definition WHERE code = 'default_health' AND version = 1"
    ).fetchone()
    if not existing:
        now = utc_now()
        hid = int(conn.execute("SELECT COALESCE(MAX(id),0)+1 FROM app_customer_health_definition").fetchone()[0])
        conn.execute(
            """
            INSERT INTO app_customer_health_definition
                (id, organization_id, code, version, name, formula_json, weights_json,
                 null_handling, status, limitations, created_at)
            VALUES (?, NULL, 'default_health', 1, 'Default weighted health',
                    '{"type":"weighted_sum","inputs":["subscription_active","open_risks","support_open"]}',
                    '{"subscription_active":0.5,"open_risks":0.3,"support_open":0.2}',
                    'unavailable', 'active',
                    'Rule-based academic formula — not AI. Insufficient inputs => No disponible.',
                    ?)
            """,
            [hid, now],
        )

    logger.info("Customer success schema ensured (%s tables)", len(CS_TABLES))
