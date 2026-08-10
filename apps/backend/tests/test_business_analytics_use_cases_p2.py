"""Test P2: Business analytics use cases — Spec 023."""

from __future__ import annotations

import duckdb
import pytest

from app.packages.business_analytics.application.use_cases import (
    AnalyticsDashboardUseCases,
    KpiSnapshotUseCases,
    RecommendationUseCases,
)
from app.packages.business_analytics.domain.errors import NotFoundError


@pytest.fixture(scope="module")
def db_conn(tmp_path_factory):
    from app.core import schema_bootstrap
    previous = schema_bootstrap._schema_ready
    schema_bootstrap._schema_ready = False
    db_path = tmp_path_factory.mktemp("biz_analytics_uc") / "test.duckdb"
    conn = duckdb.connect(str(db_path))

    from app.packages.identity.services.user_storage import ensure_user_tables
    from app.packages.organizations.infrastructure.schema import ensure_organization_tables
    from app.packages.platform_rbac.infrastructure.schema import ensure_platform_rbac_tables
    from app.packages.campaigns.infrastructure.schema import ensure_campaign_tables
    from app.packages.business_analytics.infrastructure.schema import ensure_business_analytics_tables
    from app.core.time_util import utc_now

    ensure_user_tables(conn)
    ensure_organization_tables(conn)
    ensure_platform_rbac_tables(conn)
    ensure_campaign_tables(conn)
    ensure_business_analytics_tables(conn)

    now = utc_now()
    conn.execute(
        "INSERT INTO app_organization (id, display_name, slug, organization_type, country_code, "
        "timezone, default_currency, status, created_by, created_at, updated_at) "
        "VALUES (70, 'Biz Analytics Org', 'biz-analytics-uc', 'label', 'US', 'UTC', 'USD', "
        "'active', 1, ?, ?)",
        [now, now],
    )
    conn.execute("""
        CREATE TABLE fact_streaming (
            id_stream INTEGER PRIMARY KEY, id_usuario INTEGER, id_track INTEGER,
            played_at TIMESTAMP, skipped BOOLEAN DEFAULT FALSE
        )
    """)
    conn.execute("INSERT INTO fact_streaming VALUES (1, 1, 1, CURRENT_TIMESTAMP, FALSE), (2, 1, 2, CURRENT_TIMESTAMP, TRUE)")
    conn.execute("""
        CREATE TABLE agg_daily_streams (fecha DATE PRIMARY KEY, total_streams INTEGER)
    """)
    conn.execute("INSERT INTO agg_daily_streams VALUES (CURRENT_DATE, 2)")

    schema_bootstrap._schema_ready = previous
    yield conn
    conn.close()


ORG = 70


def test_capture_warehouse_kpi_labeled(db_conn):
    snap = KpiSnapshotUseCases(db_conn).capture("total_streams", organization_id=ORG, period="2026-01-01")
    assert snap.source_label == "warehouse:fact_streaming"
    assert snap.value == 2.0
    assert snap.is_synthetic is False


def test_skip_rate_null_handling(db_conn):
    snap = KpiSnapshotUseCases(db_conn).capture("skip_rate", organization_id=ORG, period="2026-01-01")
    assert snap.value == pytest.approx(50.0)
    assert "warehouse" in snap.source_label


def test_synthetic_snapshot_tagged(db_conn):
    snap = KpiSnapshotUseCases(db_conn).capture(
        "total_streams", organization_id=ORG, period="2026-01-01", is_synthetic=True,
    )
    assert snap.is_synthetic is True


def test_warehouse_classification_propagates_to_snapshot(db_conn):
    db_conn.execute("""
        CREATE TABLE IF NOT EXISTS ctl_carga_dataset (
            id_carga INTEGER,
            fecha_carga TIMESTAMP,
            modo VARCHAR,
            total_raw INTEGER,
            total_procesados INTEGER,
            estado VARCHAR
        )
    """)
    db_conn.execute(
        "INSERT INTO ctl_carga_dataset VALUES (9001, CURRENT_TIMESTAMP, "
        "'synthetic_activity_demo', 2, 2, 'OK')"
    )

    snap = KpiSnapshotUseCases(db_conn).capture(
        "total_streams", organization_id=ORG, period="2026-01-02",
    )

    assert snap.is_synthetic is True


def test_campaign_roi_absent_when_missing(db_conn):
    snap = KpiSnapshotUseCases(db_conn).capture("campaign_roi", organization_id=ORG, period="2026-01-01")
    assert snap.value is None
    assert snap.quality_status == "roi_unavailable"


def test_dashboard_overview(db_conn):
    data = AnalyticsDashboardUseCases(db_conn).overview(ORG)
    assert "kpis" in data
    assert data["kpis"]["total_streams"]["source_label"].startswith("warehouse")


def test_recommendations_not_ai(db_conn):
    recs = RecommendationUseCases(db_conn).generate_rule_based(ORG)
    for r in recs:
        assert r.is_ai is False


def test_kpi_not_found(db_conn):
    from app.packages.business_analytics.application.use_cases import KpiCatalogUseCases
    with pytest.raises(NotFoundError):
        KpiCatalogUseCases(db_conn).get_by_code("nonexistent_kpi")
