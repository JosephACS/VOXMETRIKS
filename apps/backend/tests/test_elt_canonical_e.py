"""Spec 014 Phase E — canonical ELT adapter and boot modes."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

from app.core.config import get_settings
from app.db.duckdb_client import shutdown_duckdb_client
from app.etl.canonical_adapter import (
    CANONICAL_RELATIVE,
    invoke_canonical_elt,
    project_root,
    resolve_canonical_script,
)
from app.pipeline.orchestrator import get_boot_state, run_system_boot


def test_canonical_script_resolves_under_monorepo() -> None:
    root = project_root()
    script = resolve_canonical_script(root)
    assert script is not None
    assert script.is_file()
    assert script.name == "elt_pipeline.py"
    # Prefer analytics/elt path in monorepo checkout
    assert "elt" in script.parts
    assert (root / CANONICAL_RELATIVE).is_file() or script.exists()


def test_invoke_canonical_missing_script_reports_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    empty = tmp_path / "empty_root"
    empty.mkdir()
    monkeypatch.setenv("DB_PATH", str(tmp_path / "unused.duckdb"))
    from tests.db_isolation import bind_test_db, restore_session_db

    bind_test_db(tmp_path / "unused.duckdb")
    get_settings.cache_clear()
    outcome = invoke_canonical_elt(cwd=empty, db_path=tmp_path / "t.duckdb", timeout_s=5)
    assert outcome["status"] == "error"
    assert "canonical_elt_script_not_found" in outcome["errors"]
    restore_session_db()


@pytest.fixture()
def boot_db_validate(tmp_path, monkeypatch):
    db_path = tmp_path / "boot_validate.duckdb"
    conn = duckdb.connect(str(db_path))
    conn.execute("CREATE TABLE dim_track (id_track INTEGER PRIMARY KEY)")
    conn.execute("INSERT INTO dim_track VALUES (1)")
    conn.execute("CREATE TABLE dim_usuario (id_usuario INTEGER PRIMARY KEY)")
    conn.execute("INSERT INTO dim_usuario VALUES (1)")
    conn.execute(
        "CREATE TABLE fact_streaming (id_streaming INTEGER PRIMARY KEY, id_track INTEGER, id_usuario INTEGER)"
    )
    conn.execute("INSERT INTO fact_streaming VALUES (1, 1, 1)")
    conn.execute(
        """
        CREATE TABLE agg_daily_streams (
            fecha DATE PRIMARY KEY, total_streams INTEGER, unique_users INTEGER,
            unique_tracks INTEGER, avg_duration_ms DOUBLE, skip_rate DOUBLE
        )
        """
    )
    conn.execute("INSERT INTO agg_daily_streams VALUES ('2026-01-01', 5, 2, 1, 100.0, 0.2)")
    conn.execute(
        """
        CREATE TABLE agg_tracks_populares (
            id_track INTEGER PRIMARY KEY, nombre_track VARCHAR, nombre_artista VARCHAR,
            popularity INTEGER, total_streams INTEGER, engagement_score DOUBLE
        )
        """
    )
    conn.execute("INSERT INTO agg_tracks_populares VALUES (1, 'T', 'A', 1, 1, 1.0)")
    conn.execute(
        """
        CREATE TABLE agg_artist_growth (
            id_artista INTEGER PRIMARY KEY, nombre_artista VARCHAR,
            streams_7d INTEGER, streams_30d INTEGER, growth_pct DOUBLE, total_followers INTEGER
        )
        """
    )
    conn.execute("INSERT INTO agg_artist_growth VALUES (1, 'A', 1, 1, 0.0, 1)")
    conn.close()

    monkeypatch.setenv("DB_PATH", str(db_path))
    monkeypatch.setenv("RUN_ETL_ON_BOOT", "validation-only")
    from tests.db_isolation import bind_test_db, restore_session_db

    bind_test_db(db_path)
    get_settings.cache_clear()
    shutdown_duckdb_client()
    yield db_path
    shutdown_duckdb_client()
    restore_session_db()


def test_boot_validation_only_does_not_run_etl(boot_db_validate) -> None:
    state = run_system_boot()
    assert state["completed"] is True
    assert state["etl_status"] == "validation_only"
    assert state["etl_mode"] in {"validation-only", "validate", "validation", "validation_only"}
    assert get_boot_state()["etl_status"] == "validation_only"


def test_boot_never_skips(boot_db_validate, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RUN_ETL_ON_BOOT", "never")
    get_settings.cache_clear()
    shutdown_duckdb_client()
    state = run_system_boot()
    assert state["etl_status"] == "skipped"
