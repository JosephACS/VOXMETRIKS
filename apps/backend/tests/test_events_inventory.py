"""Tests for analytical events inventory / KPI breakdown."""

from __future__ import annotations

import duckdb

from app.packages.analytics.services.stats.constants import ACTIVITY_FACT_TABLES
from app.packages.analytics.services.stats.events_inventory import (
    classify_activity_facts,
    get_events_breakdown,
)
from app.packages.analytics.services.stats.summary import get_summary


def _seed(conn: duckdb.DuckDBPyConnection) -> None:
    for table in ACTIVITY_FACT_TABLES:
        conn.execute(f"CREATE TABLE {table} (id INTEGER, fecha_evento TIMESTAMP)")
    conn.execute("INSERT INTO fact_streaming VALUES (1, TIMESTAMP '2026-06-01'), (2, TIMESTAMP '2026-06-02')")
    conn.execute("INSERT INTO fact_user_activity VALUES (1, TIMESTAMP '2026-06-01')")
    conn.execute("INSERT INTO fact_favorites VALUES (1, TIMESTAMP '2026-06-01'), (2, TIMESTAMP '2026-06-03')")
    conn.execute(
        """
        CREATE TABLE ctl_carga_dataset (
            id_carga INTEGER,
            fecha_carga TIMESTAMP,
            modo VARCHAR,
            total_raw BIGINT,
            total_procesados BIGINT,
            estado VARCHAR
        )
        """
    )
    conn.execute(
        """
        INSERT INTO ctl_carga_dataset VALUES
        (1, TIMESTAMP '2026-06-28', 'synthetic_activity_target_900000', 600000, 900000, 'OK')
        """
    )
    for dim in ("dim_track", "dim_artista", "dim_genero", "dim_album", "dim_usuario", "dim_playlist"):
        conn.execute(f"CREATE TABLE {dim} (id INTEGER)")
        conn.execute(f"INSERT INTO {dim} VALUES (1)")


def test_events_breakdown_sums_activity_facts_only():
    conn = duckdb.connect(":memory:")
    _seed(conn)
    out = get_events_breakdown(conn)
    assert out["total_events"] == 5
    assert out["formula"].startswith("SUM(COUNT(*))")
    names = [r["table"] for r in out["tables"]]
    assert names == list(ACTIVITY_FACT_TABLES)
    assert out["classification_totals"]["synthetic"] == 5
    assert out["classification_totals"]["unknown"] == 0
    assert round(sum(r["pct_of_total"] for r in out["tables"]), 1) == 100.0


def test_classify_unknown_without_ctl():
    conn = duckdb.connect(":memory:")
    conn.execute("CREATE TABLE fact_streaming (id INTEGER)")
    conn.execute("INSERT INTO fact_streaming VALUES (1)")
    assert classify_activity_facts(conn) == "unknown"


def test_summary_total_events_matches_breakdown():
    conn = duckdb.connect(":memory:")
    _seed(conn)
    # Bypass cache identities by using fresh functions on same conn
    summary = get_summary.__wrapped__(conn) if hasattr(get_summary, "__wrapped__") else get_summary(conn)
    breakdown = (
        get_events_breakdown.__wrapped__(conn)
        if hasattr(get_events_breakdown, "__wrapped__")
        else get_events_breakdown(conn)
    )
    assert summary["total_events"] == breakdown["total_events"] == 5
    assert summary["events_scope"] == "warehouse_activity_facts"
    assert summary["tracks_scope"] == "warehouse_catalog"
