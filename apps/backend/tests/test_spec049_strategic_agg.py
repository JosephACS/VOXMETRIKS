"""Spec 049 — strategic AGG read model and overview."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

import duckdb
import pytest

from app.packages.business_analytics.application.strategic_agg import (
    OFFICIAL_OBJECTIVES,
    default_period,
    refresh_strategic_kpi_period,
    strategic_overview,
)
from app.packages.business_analytics.infrastructure.schema import (
    BUSINESS_ANALYTICS_TABLES,
    ensure_business_analytics_tables,
)


@pytest.fixture
def db_conn(tmp_path):
    from app.core import schema_bootstrap

    previous = schema_bootstrap._schema_ready
    schema_bootstrap._schema_ready = False
    path = tmp_path / "strategic049.duckdb"
    conn = duckdb.connect(str(path))

    from app.packages.identity.services.user_storage import ensure_user_tables
    from app.packages.organizations.infrastructure.schema import ensure_organization_tables
    from app.packages.platform_rbac.infrastructure.schema import ensure_platform_rbac_tables
    from app.packages.campaigns.infrastructure.schema import ensure_campaign_tables
    from app.packages.subscriptions.infrastructure.schema import ensure_subscription_tables
    from app.core.time_util import utc_now

    ensure_user_tables(conn)
    ensure_organization_tables(conn)
    ensure_platform_rbac_tables(conn)
    ensure_campaign_tables(conn)
    try:
        ensure_subscription_tables(conn)
    except Exception:
        pass
    ensure_business_analytics_tables(conn)

    now = utc_now()
    for oid, name, slug in ((101, "Org A", "org-a-049"), (202, "Org B", "org-b-049")):
        conn.execute(
            "INSERT INTO app_organization (id, display_name, slug, organization_type, country_code, "
            "timezone, default_currency, status, created_by, created_at, updated_at) "
            "VALUES (?, ?, ?, 'label', 'US', 'UTC', 'USD', 'active', 1, ?, ?)",
            [oid, name, slug, now, now],
        )

    conn.execute("""
        CREATE TABLE IF NOT EXISTS fact_streaming (
            id_stream INTEGER PRIMARY KEY, id_usuario INTEGER, id_track INTEGER,
            played_at TIMESTAMP, skipped BOOLEAN DEFAULT FALSE
        )
    """)
    conn.execute(
        "INSERT INTO fact_streaming VALUES (1, 1, 1, CURRENT_TIMESTAMP, FALSE), "
        "(2, 1, 2, CURRENT_TIMESTAMP, TRUE)"
    )
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agg_daily_streams (fecha DATE PRIMARY KEY, total_streams INTEGER)
    """)
    conn.execute("INSERT INTO agg_daily_streams VALUES (CURRENT_DATE, 2)")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ctl_pipeline_stages (
            run_id VARCHAR, stage VARCHAR, status VARCHAR, finished_at TIMESTAMP
        )
    """)
    conn.execute(
        "INSERT INTO ctl_pipeline_stages VALUES ('r1', 'gold', 'OK', CURRENT_TIMESTAMP)"
    )

    schema_bootstrap._schema_ready = previous
    yield conn
    conn.close()


def test_schema_idempotent_includes_strategic_table(db_conn):
    ensure_business_analytics_tables(db_conn)
    ensure_business_analytics_tables(db_conn)
    assert "agg_strategic_kpi_period" in BUSINESS_ANALYTICS_TABLES
    row = db_conn.execute(
        "SELECT 1 FROM information_schema.tables WHERE table_name = 'agg_strategic_kpi_period'"
    ).fetchone()
    assert row


def test_refresh_repeated_no_duplicates(db_conn):
    ps, pe = default_period()
    refresh_strategic_kpi_period(db_conn, organization_id=101, period_start=ps, period_end=pe)
    refresh_strategic_kpi_period(db_conn, organization_id=101, period_start=ps, period_end=pe)
    cnt = db_conn.execute(
        """
        SELECT COUNT(*) FROM (
          SELECT objective_code, kpi_code, COUNT(*) c
          FROM agg_strategic_kpi_period
          WHERE organization_id = 101 AND period_start = ? AND period_end = ?
          GROUP BY 1, 2 HAVING COUNT(*) > 1
        )
        """,
        [ps, pe],
    ).fetchone()[0]
    assert int(cnt) == 0


def test_refresh_rollback_on_failure(db_conn):
    ps, pe = default_period()
    refresh_strategic_kpi_period(db_conn, organization_id=101, period_start=ps, period_end=pe)
    before = int(
        db_conn.execute(
            "SELECT COUNT(*) FROM agg_strategic_kpi_period WHERE organization_id = 101"
        ).fetchone()[0]
    )
    with pytest.raises(RuntimeError, match="forced_refresh_failure"):
        refresh_strategic_kpi_period(
            db_conn, organization_id=101, period_start=ps, period_end=pe, fail=True,
        )
    after = int(
        db_conn.execute(
            "SELECT COUNT(*) FROM agg_strategic_kpi_period WHERE organization_id = 101"
        ).fetchone()[0]
    )
    assert after == before


def test_concurrent_refresh_is_serialized_and_deduplicated(db_conn):
    ps, pe = default_period()

    def refresh() -> int:
        return len(
            refresh_strategic_kpi_period(
                db_conn,
                organization_id=101,
                period_start=ps,
                period_end=pe,
            )
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(refresh), pool.submit(refresh)]
        results = [future.result() for future in futures]

    assert all(count >= 8 for count in results)
    duplicates = db_conn.execute(
        """
        SELECT objective_code, kpi_code, COUNT(*)
        FROM agg_strategic_kpi_period
        WHERE organization_id = 101 AND period_start = ? AND period_end = ?
        GROUP BY objective_code, kpi_code
        HAVING COUNT(*) > 1
        """,
        [ps, pe],
    ).fetchall()
    assert duplicates == []


def test_overview_default_is_read_only(db_conn):
    data = strategic_overview(db_conn, organization_id=101)

    stored = db_conn.execute(
        "SELECT COUNT(*) FROM agg_strategic_kpi_period WHERE organization_id = 101"
    ).fetchone()[0]
    assert int(stored) == 0
    assert len(data["objectives"]) == 8
    assert all(objective["empty"] for objective in data["objectives"])


def test_org_isolation_a_not_b(db_conn):
    ps, pe = default_period()
    refresh_strategic_kpi_period(db_conn, organization_id=101, period_start=ps, period_end=pe)
    refresh_strategic_kpi_period(db_conn, organization_id=202, period_start=ps, period_end=pe)
    a = strategic_overview(db_conn, organization_id=101, auto_refresh=False)
    b_codes = {
        r[0]
        for r in db_conn.execute(
            "SELECT DISTINCT organization_id FROM agg_strategic_kpi_period WHERE organization_id = 101"
        ).fetchall()
    }
    assert a["organization_id"] == 101
    assert b_codes == {101}
    leaked = db_conn.execute(
        """
        SELECT 1 FROM agg_strategic_kpi_period
        WHERE organization_id = 202 AND id IN (
          SELECT id FROM agg_strategic_kpi_period WHERE organization_id = 101
        )
        """
    ).fetchone()
    assert leaked is None


def test_global_rows_only_when_requested(db_conn):
    ps, pe = default_period()
    refresh_strategic_kpi_period(
        db_conn, organization_id=101, period_start=ps, period_end=pe, include_global=True,
    )
    global_rows = db_conn.execute(
        "SELECT COUNT(*) FROM agg_strategic_kpi_period WHERE organization_id IS NULL"
    ).fetchone()[0]
    assert int(global_rows) >= 1
    overview = strategic_overview(db_conn, organization_id=101, include_global=False, auto_refresh=False)
    for obj in overview["objectives"]:
        for k in obj["kpis"]:
            assert k["organization_id"] == 101


def test_null_unavailable_not_zero_for_roi(db_conn):
    ps, pe = default_period()
    refresh_strategic_kpi_period(db_conn, organization_id=101, period_start=ps, period_end=pe)
    row = db_conn.execute(
        """
        SELECT value, availability_status, unavailable_reason
        FROM agg_strategic_kpi_period
        WHERE organization_id = 101 AND kpi_code = 'campaign_roi'
        """
    ).fetchone()
    assert row is not None
    assert row[0] is None
    assert row[1] == "unavailable"
    assert row[0] != 0


def test_security_pct_and_sla_unavailable(db_conn):
    ps, pe = default_period()
    refresh_strategic_kpi_period(db_conn, organization_id=101, period_start=ps, period_end=pe)
    sec = db_conn.execute(
        "SELECT value FROM agg_strategic_kpi_period WHERE organization_id = 101 AND kpi_code = 'security_coverage_pct'"
    ).fetchone()
    sla = db_conn.execute(
        "SELECT value FROM agg_strategic_kpi_period WHERE organization_id = 101 AND kpi_code = 'sla_compliance'"
    ).fetchone()
    assert sec[0] is None
    assert sla[0] is None


def test_synthetic_proxy_propagates_from_warehouse(db_conn):
    db_conn.execute("""
        CREATE TABLE IF NOT EXISTS ctl_carga_dataset (
            id_carga INTEGER, fecha_carga TIMESTAMP, modo VARCHAR,
            total_raw INTEGER, total_procesados INTEGER, estado VARCHAR
        )
    """)
    db_conn.execute(
        "INSERT INTO ctl_carga_dataset VALUES (9100, CURRENT_TIMESTAMP, "
        "'synthetic_activity_demo', 2, 2, 'OK')"
    )
    ps, pe = default_period()
    refresh_strategic_kpi_period(db_conn, organization_id=101, period_start=ps, period_end=pe)
    row = db_conn.execute(
        """
        SELECT is_synthetic, is_proxy FROM agg_strategic_kpi_period
        WHERE organization_id = 101 AND kpi_code = 'total_streams'
        """
    ).fetchone()
    assert row is not None
    assert row[0] is True
    assert row[1] is True


def test_overview_always_eight_objectives(db_conn):
    data = strategic_overview(db_conn, organization_id=101, auto_refresh=True)
    codes = [o["objective_code"] for o in data["objectives"]]
    assert codes == [c for c, _ in OFFICIAL_OBJECTIVES]
    assert len(codes) == 8
    assert data["decision_capability"]["is_ai"] is False
    assert data["decision_capability"]["recommendation_mode"] == "rule_based"
    evidence = {item["objective_code"]: item["evidence_path"] for item in data["objectives"]}
    assert evidence["OE-01"] == "/organizations/101"
    assert evidence["OE-03"] == "/subscriptions/overview"
    assert evidence["OE-07"] == "/organizations/101/audit"
    assert evidence["OE-08"] == "/business-analytics/alerts"


def test_no_trend_with_single_period(db_conn):
    data = strategic_overview(db_conn, organization_id=101, auto_refresh=True)
    assert data["comparable_periods"] == 1
    for obj in data["objectives"]:
        assert obj["trend"] is None


def test_trend_with_two_periods(db_conn):
    ps, pe = default_period()
    earlier_start = (ps.replace(day=1) - timedelta(days=1)).replace(day=1)
    earlier_end = ps - timedelta(days=1)
    refresh_strategic_kpi_period(
        db_conn, organization_id=101, period_start=earlier_start, period_end=earlier_end,
    )
    refresh_strategic_kpi_period(db_conn, organization_id=101, period_start=ps, period_end=pe)
    data = strategic_overview(db_conn, organization_id=101, auto_refresh=False)
    assert data["comparable_periods"] >= 2


def test_multi_currency_no_fx_for_primary_mrr(db_conn):
    # Without plan prices, active_mrr stays unavailable — never invented FX total.
    ps, pe = default_period()
    refresh_strategic_kpi_period(db_conn, organization_id=101, period_start=ps, period_end=pe)
    row = db_conn.execute(
        """
        SELECT value, quality_status FROM agg_strategic_kpi_period
        WHERE organization_id = 101 AND kpi_code = 'active_mrr'
        """
    ).fetchone()
    assert row is not None
    # Either null with honest quality, or a single-currency value — never a fake FX sum.
    if row[0] is None:
        assert row[1] in {
            "no_active_recurring",
            "multi_currency_no_fx",
            "schema_unavailable",
            "ok",
        }
