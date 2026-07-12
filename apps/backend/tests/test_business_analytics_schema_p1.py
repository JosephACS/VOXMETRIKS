"""Test P1: Business analytics schema — Spec 023."""

from __future__ import annotations

import duckdb
import pytest


@pytest.fixture(scope="module")
def db_conn(tmp_path_factory):
    from app.core import schema_bootstrap
    previous = schema_bootstrap._schema_ready
    schema_bootstrap._schema_ready = False
    db_path = tmp_path_factory.mktemp("biz_analytics_schema") / "test.duckdb"
    conn = duckdb.connect(str(db_path))

    from app.packages.identity.services.user_storage import ensure_user_tables
    from app.packages.organizations.infrastructure.schema import ensure_organization_tables
    from app.packages.platform_rbac.infrastructure.schema import ensure_platform_rbac_tables
    from app.packages.campaigns.infrastructure.schema import ensure_campaign_tables
    from app.packages.business_analytics.infrastructure.schema import ensure_business_analytics_tables

    ensure_user_tables(conn)
    ensure_organization_tables(conn)
    ensure_platform_rbac_tables(conn)
    ensure_campaign_tables(conn)
    ensure_business_analytics_tables(conn)
    schema_bootstrap._schema_ready = previous
    yield conn
    conn.close()


@pytest.mark.parametrize("table", [
    "app_kpi_definition", "app_kpi_snapshot", "app_metric_source",
    "app_data_quality_result", "app_business_alert",
    "app_analytics_view_preference", "app_recommendation_record",
])
def test_table_exists(db_conn, table):
    db_conn.execute(f"SELECT id FROM {table} LIMIT 0")


@pytest.mark.parametrize("code", ["biz_analytics.view", "biz_analytics.manage", "biz_analytics.alert"])
def test_biz_analytics_permissions_seeded(db_conn, code):
    row = db_conn.execute("SELECT id FROM app_permission WHERE code = ?", [code]).fetchone()
    assert row is not None


def test_metric_sources_seeded(db_conn):
    cnt = db_conn.execute("SELECT COUNT(*) FROM app_metric_source").fetchone()[0]
    assert int(cnt) >= 4


def test_default_kpis_seeded(db_conn):
    cnt = db_conn.execute("SELECT COUNT(*) FROM app_kpi_definition").fetchone()[0]
    assert int(cnt) >= 4
