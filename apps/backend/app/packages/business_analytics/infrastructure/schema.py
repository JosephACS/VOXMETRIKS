"""Business analytics schema — Spec 023."""

from __future__ import annotations

import logging

import duckdb

from app.core.schema_bootstrap import schema_ready

logger = logging.getLogger("voxmetrik.business_analytics.schema")

BUSINESS_ANALYTICS_TABLES = (
    "app_kpi_definition",
    "app_kpi_snapshot",
    "app_metric_source",
    "app_data_quality_result",
    "app_business_alert",
    "app_analytics_view_preference",
    "app_recommendation_record",
)


def ensure_business_analytics_tables(conn: duckdb.DuckDBPyConnection) -> None:
    if schema_ready():
        return
    _create_kpi_definition(conn)
    _create_kpi_snapshot(conn)
    _create_metric_source(conn)
    _create_data_quality_result(conn)
    _create_business_alert(conn)
    _create_analytics_view_preference(conn)
    _create_recommendation_record(conn)
    _seed_metric_sources(conn)
    _seed_default_kpis(conn)
    logger.info("Business analytics schema ensured (%s tables)", len(BUSINESS_ANALYTICS_TABLES))


def _create_kpi_definition(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_kpi_definition (
            id                  INTEGER PRIMARY KEY,
            code                VARCHAR NOT NULL,
            name                VARCHAR NOT NULL,
            formula_description VARCHAR NOT NULL,
            version             INTEGER NOT NULL DEFAULT 1,
            granularity         VARCHAR NOT NULL DEFAULT 'daily',
            frequency           VARCHAR NOT NULL DEFAULT 'daily',
            owner_role          VARCHAR,
            null_handling       VARCHAR NOT NULL DEFAULT 'exclude',
            source_type         VARCHAR NOT NULL DEFAULT 'warehouse',
            status              VARCHAR NOT NULL DEFAULT 'active',
            created_at          TIMESTAMP NOT NULL,
            updated_at          TIMESTAMP NOT NULL,
            CHECK (status IN ('draft', 'active', 'deprecated')),
            CHECK (null_handling IN ('exclude', 'zero', 'fail'))
        )
    """)


def _create_kpi_snapshot(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_kpi_snapshot (
            id                  INTEGER PRIMARY KEY,
            kpi_definition_id   INTEGER NOT NULL,
            organization_id     INTEGER,
            period              VARCHAR NOT NULL,
            value               DOUBLE,
            quality_status      VARCHAR NOT NULL DEFAULT 'ok',
            source_label        VARCHAR NOT NULL,
            is_synthetic        BOOLEAN NOT NULL DEFAULT FALSE,
            created_at          TIMESTAMP NOT NULL
        )
    """)


def _create_metric_source(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_metric_source (
            id              INTEGER PRIMARY KEY,
            code            VARCHAR NOT NULL,
            label           VARCHAR NOT NULL,
            origin_system   VARCHAR NOT NULL,
            description     VARCHAR,
            created_at      TIMESTAMP NOT NULL
        )
    """)


def _create_data_quality_result(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_data_quality_result (
            id              INTEGER PRIMARY KEY,
            check_code      VARCHAR NOT NULL,
            organization_id INTEGER,
            status          VARCHAR NOT NULL,
            details         VARCHAR,
            measured_at     TIMESTAMP NOT NULL,
            created_at      TIMESTAMP NOT NULL,
            CHECK (status IN ('pass', 'warn', 'fail'))
        )
    """)


def _create_business_alert(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_business_alert (
            id              INTEGER PRIMARY KEY,
            organization_id INTEGER NOT NULL,
            severity        VARCHAR NOT NULL,
            title           VARCHAR NOT NULL,
            body            VARCHAR NOT NULL,
            status          VARCHAR NOT NULL DEFAULT 'open',
            kpi_code        VARCHAR,
            created_at      TIMESTAMP NOT NULL,
            updated_at      TIMESTAMP NOT NULL,
            CHECK (severity IN ('info', 'warning', 'critical')),
            CHECK (status IN ('open', 'acked', 'closed'))
        )
    """)


def _create_analytics_view_preference(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_analytics_view_preference (
            id              INTEGER PRIMARY KEY,
            user_id         INTEGER NOT NULL,
            organization_id INTEGER NOT NULL,
            view_key        VARCHAR NOT NULL,
            payload_json    VARCHAR NOT NULL,
            created_at      TIMESTAMP NOT NULL,
            updated_at      TIMESTAMP NOT NULL
        )
    """)


def _create_recommendation_record(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_recommendation_record (
            id              INTEGER PRIMARY KEY,
            organization_id INTEGER NOT NULL,
            rule_code       VARCHAR NOT NULL,
            title           VARCHAR NOT NULL,
            rationale       VARCHAR NOT NULL,
            evidence_ref    VARCHAR,
            is_ai           BOOLEAN NOT NULL DEFAULT FALSE,
            created_at      TIMESTAMP NOT NULL
        )
    """)


def _seed_metric_sources(conn: duckdb.DuckDBPyConnection) -> None:
    from app.core.time_util import utc_now
    now = utc_now()
    sources = [
        ("warehouse:fact_streaming", "Streaming events", "warehouse", "fact_streaming table"),
        ("warehouse:agg_daily_streams", "Daily stream aggregates", "warehouse", "agg_daily_streams table"),
        ("campaigns:roi_snapshot", "Campaign ROI snapshots", "campaigns", "app_campaign_roi_snapshot"),
        ("subscriptions:usage", "Subscription usage", "subscriptions", "app_subscription_usage if available"),
    ]
    for code, label, origin, desc in sources:
        existing = conn.execute("SELECT id FROM app_metric_source WHERE code = ?", [code]).fetchone()
        if not existing:
            sid = int(conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM app_metric_source").fetchone()[0])
            conn.execute(
                "INSERT INTO app_metric_source (id, code, label, origin_system, description, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                [sid, code, label, origin, desc, now],
            )


def _seed_default_kpis(conn: duckdb.DuckDBPyConnection) -> None:
    from app.core.time_util import utc_now
    now = utc_now()
    kpis = [
        ("total_streams", "Total Streams", "COUNT(*) from fact_streaming", "warehouse:fact_streaming"),
        ("daily_streams", "Daily Streams", "SUM(total_streams) from agg_daily_streams", "warehouse:agg_daily_streams"),
        ("skip_rate", "Skip Rate", "skipped streams / total streams", "warehouse:fact_streaming"),
        ("campaign_roi", "Campaign ROI", "From app_campaign_roi_snapshot when available", "campaigns:roi_snapshot"),
    ]
    for code, name, formula, source_type in kpis:
        existing = conn.execute("SELECT id FROM app_kpi_definition WHERE code = ? AND version = 1", [code]).fetchone()
        if not existing:
            kid = int(conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM app_kpi_definition").fetchone()[0])
            conn.execute(
                """
                INSERT INTO app_kpi_definition
                    (id, code, name, formula_description, version, granularity, frequency,
                     owner_role, null_handling, source_type, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, 1, 'daily', 'daily', 'analyst', 'exclude', ?, 'active', ?, ?)
                """,
                [kid, code, name, formula, source_type, now, now],
            )
