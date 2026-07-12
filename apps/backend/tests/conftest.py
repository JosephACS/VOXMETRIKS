"""Pytest fixtures — isolated DuckDB + FastAPI TestClient."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import duckdb
import pytest
from fastapi.testclient import TestClient

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

os.environ.setdefault("AUTH_RATE_LIMIT", "0")
os.environ.setdefault("GLOBAL_RATE_LIMIT", "0")
os.environ.setdefault("LOG_TO_FILES", "false")

_TEST_DB_DIR = BACKEND / "tests" / ".pytest_db"
_TEST_DB_PATH = _TEST_DB_DIR / "voxmetrik_test.duckdb"


def _init_test_database(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    # Spec 028: clear process-level schema_ready so ensure_* always creates tables
    # on a freshly wiped test database (avoids skipping CREATE after prior TestClient).
    from app.core.schema_bootstrap import reset_schema_ready_for_tests

    reset_schema_ready_for_tests()

    conn = duckdb.connect(str(db_path))
    conn.execute("""
        CREATE TABLE dim_artista (
            id_artista     INTEGER PRIMARY KEY,
            nombre_artista VARCHAR NOT NULL
        )
    """)
    conn.execute("""
        INSERT INTO dim_artista (id_artista, nombre_artista)
        VALUES (1, 'Demo Artist')
    """)
    conn.execute("""
        CREATE TABLE dim_genero (
            id_genero     INTEGER PRIMARY KEY,
            nombre_genero VARCHAR NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE dim_track (
            id_track          INTEGER PRIMARY KEY,
            spotify_track_id  VARCHAR,
            nombre_track      VARCHAR NOT NULL,
            id_artista        INTEGER,
            id_album          INTEGER,
            id_genero         INTEGER,
            explicit          BOOLEAN DEFAULT FALSE,
            duration_ms       INTEGER,
            popularity        INTEGER
        )
    """)
    conn.execute(
        """
        INSERT INTO dim_track (id_track, spotify_track_id, nombre_track, id_artista, id_genero, duration_ms, popularity)
        VALUES
            (1, 'boot_000001', 'Vámonos a Marte', 1, NULL, 180000, 88),
            (2, 'boot_000002', 'Golden Dreams #00002', 1, NULL, 200000, 72),
            (3, 'boot_000003', 'Despacito', 1, NULL, 210000, 95)
        """
    )
    conn.execute("""
        CREATE TABLE dim_usuario (
            id_usuario     INTEGER PRIMARY KEY,
            nombre_usuario VARCHAR NOT NULL
        )
    """)
    conn.execute("""
        INSERT INTO dim_usuario (id_usuario, nombre_usuario)
        VALUES (1, 'Demo Listener')
    """)
    conn.execute("""
        CREATE TABLE dim_playlist (
            id_playlist     INTEGER PRIMARY KEY,
            nombre_playlist VARCHAR NOT NULL
        )
    """)
    conn.execute("""
        INSERT INTO dim_playlist (id_playlist, nombre_playlist)
        VALUES (1, 'Smoke Playlist')
    """)
    conn.execute("""
        CREATE TABLE fact_streaming (
            id_stream     INTEGER PRIMARY KEY,
            id_usuario    INTEGER,
            id_track      INTEGER,
            played_at     TIMESTAMP,
            fecha_evento  TIMESTAMP,
            duration_ms   INTEGER,
            duracion_ms   INTEGER,
            skipped       BOOLEAN DEFAULT FALSE
        )
    """)
    conn.execute("""
        INSERT INTO fact_streaming (
            id_stream, id_usuario, id_track, played_at, fecha_evento, duration_ms, duracion_ms, skipped
        )
        VALUES
            (1, 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 180000, 180000, FALSE),
            (2, 1, 2, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 200000, 200000, TRUE),
            (3, 1, 3, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 210000, 210000, FALSE)
    """)
    conn.execute("""
        CREATE TABLE agg_daily_streams (
            fecha DATE PRIMARY KEY,
            total_streams INTEGER,
            unique_users INTEGER,
            unique_tracks INTEGER,
            avg_duration_ms DOUBLE,
            skip_count INTEGER
        )
    """)
    conn.execute("""
        INSERT INTO agg_daily_streams (
            fecha, total_streams, unique_users, unique_tracks, avg_duration_ms, skip_count
        )
        VALUES (CURRENT_DATE, 3, 1, 3, 196666.0, 1)
    """)

    from app.packages.streaming.services.app_storage import ensure_app_tables
    from app.packages.identity.services.user_storage import ensure_user_tables
    from app.packages.organizations.infrastructure.schema import ensure_organization_tables
    from app.packages.platform_rbac.infrastructure.schema import ensure_platform_rbac_tables
    from app.packages.crm.infrastructure.schema import ensure_crm_tables
    from app.packages.contracts.infrastructure.schema import ensure_commercial_contract_tables
    from app.packages.subscriptions.infrastructure.schema import ensure_subscription_tables
    from app.packages.billing.infrastructure.schema import ensure_billing_tables
    from app.packages.artists.infrastructure.schema import ensure_artist_tables
    from app.packages.catalog_rights.infrastructure.schema import ensure_catalog_rights_tables
    from app.packages.campaigns.infrastructure.schema import ensure_campaign_tables
    from app.packages.business_analytics.infrastructure.schema import ensure_business_analytics_tables
    from app.packages.compliance.infrastructure.schema import ensure_compliance_tables
    from app.packages.platform_ops.infrastructure.schema import ensure_platform_ops_tables
    from app.packages.reporting.infrastructure.schema import ensure_reporting_tables
    from app.packages.customer_success.infrastructure.schema import ensure_customer_success_tables

    ensure_user_tables(conn)
    ensure_app_tables(conn)
    ensure_organization_tables(conn)
    ensure_platform_rbac_tables(conn)
    ensure_crm_tables(conn)
    ensure_commercial_contract_tables(conn)
    ensure_subscription_tables(conn)
    ensure_billing_tables(conn)
    ensure_artist_tables(conn)
    ensure_catalog_rights_tables(conn)
    ensure_campaign_tables(conn)
    ensure_business_analytics_tables(conn)
    ensure_compliance_tables(conn)
    ensure_platform_ops_tables(conn)
    ensure_reporting_tables(conn)
    ensure_customer_success_tables(conn)
    conn.close()


@pytest.fixture(scope="session", autouse=True)
def _configure_test_database() -> None:
    os.environ["db_path"] = str(_TEST_DB_PATH)
    os.environ["RUN_ETL_ON_BOOT"] = "never"
    os.environ["SKIP_SYSTEM_BOOT"] = "1"
    from app.core.config import get_settings
    from app.core.database import close_read_pool
    from app.db.duckdb_client import shutdown_duckdb_client

    get_settings.cache_clear()
    shutdown_duckdb_client()
    close_read_pool()
    _init_test_database(_TEST_DB_PATH)
    yield
    shutdown_duckdb_client()
    close_read_pool()
    get_settings.cache_clear()


@pytest.fixture(scope="session")
def client() -> TestClient:
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/users/login",
        json={"login": "admin", "password": "admin123", "remember": True},
    )
    assert response.status_code == 200, response.text
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/users/login",
        json={"login": "demo", "password": "demo123", "remember": True},
    )
    assert response.status_code == 200, response.text
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}
