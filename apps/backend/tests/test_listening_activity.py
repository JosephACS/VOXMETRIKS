"""Tests for personal listening activity (spec 035)."""

from __future__ import annotations

from datetime import datetime, timedelta

import duckdb
import pytest

from app.packages.engagement.services.listening_activity_service import (
    get_listening_activity,
    parse_period,
)
from app.packages.engagement.services.listening_history_service import (
    ensure_listening_history_table,
)


def _seed(conn: duckdb.DuckDBPyConnection) -> None:
    ensure_listening_history_table(conn)
    conn.execute(
        """
        CREATE TABLE dim_artista (id_artista INTEGER, nombre_artista VARCHAR);
        CREATE TABLE dim_genero (id_genero INTEGER, nombre_genero VARCHAR);
        CREATE TABLE dim_track (
          id_track INTEGER,
          nombre_track VARCHAR,
          id_artista INTEGER,
          id_genero INTEGER,
          duration_ms INTEGER
        );
        CREATE TABLE app_track_audio_source (
          track_id INTEGER,
          provider VARCHAR,
          status VARCHAR,
          failure_count INTEGER,
          youtube_video_id VARCHAR,
          source_ref VARCHAR,
          playable_url VARCHAR
        );
        """
    )
    conn.execute("INSERT INTO dim_artista VALUES (1, 'Artist A'), (2, 'Artist B')")
    conn.execute("INSERT INTO dim_genero VALUES (10, 'Pop'), (20, 'Rock')")
    conn.execute(
        """
        INSERT INTO dim_track VALUES
          (100, 'Song One', 1, 10, 200000),
          (101, 'Song Two', 1, 10, 45000),
          (102, 'Song Three', 2, 20, 180000),
          (103, 'Unavailable Hit', 2, 20, 200000)
        """
    )
    conn.execute(
        """
        INSERT INTO app_track_audio_source VALUES
          (100, 'youtube', 'ok', 0, 'aaaaaaaaaaa', 'aaaaaaaaaaa', NULL),
          (101, 'youtube', 'ok', 0, 'bbbbbbbbbbb', 'bbbbbbbbbbb', NULL),
          (102, 'youtube', 'ok', 0, 'ccccccccccc', 'ccccccccccc', NULL),
          (103, 'youtube', 'not_found', 0, NULL, NULL, NULL)
        """
    )
    now = datetime.utcnow()
    rows = [
        # user 1 — valid long plays
        (1, 1, 100, "e1", now - timedelta(days=1), 35000, True),
        (2, 1, 100, "e2", now - timedelta(days=2), 40000, True),
        (3, 1, 101, "e3", now - timedelta(days=3), 25000, True),  # short track 50%
        (4, 1, 102, "e4", now - timedelta(days=10), 60000, True),
        (5, 1, 103, "e5", now - timedelta(days=1), 35000, True),
        # under threshold — excluded
        (6, 1, 100, "e6", now - timedelta(hours=1), 5000, False),
        # user 2 — must never appear for user 1
        (7, 2, 100, "e7", now - timedelta(days=1), 90000, True),
        (8, 2, 102, "e8", now - timedelta(days=1), 90000, True),
    ]
    for r in rows:
        conn.execute(
            """
            INSERT INTO app_listening_history
              (id, user_id, track_id, event_key, played_at, progress_ms, listened_ms, completed, source, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'player', ?, ?)
            """,
            [r[0], r[1], r[2], r[3], r[4], r[5], r[5], r[6], r[4], r[4]],
        )


@pytest.fixture()
def conn() -> duckdb.DuckDBPyConnection:
    c = duckdb.connect(":memory:")
    _seed(c)
    return c


def test_parse_period() -> None:
    assert parse_period("7d") == "7d"
    with pytest.raises(ValueError):
        parse_period("year")


def test_isolation_user_boundary(conn: duckdb.DuckDBPyConnection) -> None:
    a = get_listening_activity(conn, 1, period="all")
    b = get_listening_activity(conn, 2, period="all")
    assert a["summary"]["plays"] == 5  # excludes under-threshold
    assert b["summary"]["plays"] == 2
    ids_a = {t["id_track"] for t in a["top_tracks"]}
    assert 100 in ids_a
    # user 2 plays must not inflate user 1
    assert a["summary"]["plays"] != b["summary"]["plays"]


def test_threshold_excludes_short_preview(conn: duckdb.DuckDBPyConnection) -> None:
    a = get_listening_activity(conn, 1, period="all")
    # e6 (5s) excluded; e3 short track 25s of 45s included
    assert a["summary"]["plays"] == 5


def test_period_7d_filters(conn: duckdb.DuckDBPyConnection) -> None:
    a = get_listening_activity(conn, 1, period="7d")
    # day-10 play of 102 excluded
    track_ids = [t["id_track"] for t in a["top_tracks"]]
    assert 102 not in track_ids
    assert a["summary"]["plays"] == 4


def test_unavailable_preserved_in_stats(conn: duckdb.DuckDBPyConnection) -> None:
    a = get_listening_activity(conn, 1, period="all")
    unavailable = next(t for t in a["top_tracks"] if t["id_track"] == 103)
    assert unavailable["source_unavailable"] is True
    assert unavailable["playback_status"] != "playable"


def test_empty_user(conn: duckdb.DuckDBPyConnection) -> None:
    a = get_listening_activity(conn, 99, period="30d")
    assert a["empty"] is True
    assert a["summary"]["plays"] == 0
    assert a["top_tracks"] == []


def test_genre_primary_only(conn: duckdb.DuckDBPyConnection) -> None:
    a = get_listening_activity(conn, 1, period="all")
    genres = {g["nombre_genero"]: g["plays"] for g in a["top_genres"]}
    assert "Pop" in genres
    assert genres["Pop"] >= 3
