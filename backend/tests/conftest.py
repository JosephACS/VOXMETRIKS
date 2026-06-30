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

_TEST_DB_DIR = BACKEND / "tests" / ".pytest_db"
_TEST_DB_PATH = _TEST_DB_DIR / "voxmetrik_test.duckdb"


def _init_test_database(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    conn = duckdb.connect(str(db_path))
    conn.execute("""
        CREATE TABLE dim_artista (
            id_artista     INTEGER PRIMARY KEY,
            nombre_artista VARCHAR NOT NULL
        )
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
            (1, 'boot_000001', 'Vámonos a Marte', NULL, NULL, 180000, 88),
            (2, 'boot_000002', 'Golden Dreams #00002', NULL, NULL, 200000, 72),
            (3, 'boot_000003', 'Despacito', NULL, NULL, 210000, 95)
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
            id_stream    INTEGER PRIMARY KEY,
            id_usuario   INTEGER,
            id_track     INTEGER,
            played_at    TIMESTAMP,
            duration_ms  INTEGER
        )
    """)
    conn.execute("""
        INSERT INTO fact_streaming (id_stream, id_usuario, id_track, played_at, duration_ms)
        VALUES (1, 1, 1, CURRENT_TIMESTAMP, 180000)
    """)

    from app.packages.streaming.services.app_storage import ensure_app_tables
    from app.packages.users.services.user_storage import ensure_user_tables

    ensure_user_tables(conn)
    ensure_app_tables(conn)
    conn.close()


@pytest.fixture(scope="session", autouse=True)
def _configure_test_database() -> None:
    os.environ["db_path"] = str(_TEST_DB_PATH)
    from app.core.config import get_settings

    get_settings.cache_clear()
    _init_test_database(_TEST_DB_PATH)
    yield
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
