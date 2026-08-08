"""Favorites/playlists expose playback_status for unavailable personal collections."""

from __future__ import annotations

import duckdb

from app.packages.engagement.services.favorite_service import list_favorites
from app.packages.engagement.services.playlist_service import _enrich_tracks


def _seed(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute(
        """
        CREATE TABLE dim_artista (id_artista INTEGER, nombre_artista VARCHAR);
        CREATE TABLE dim_genero (id_genero INTEGER, nombre_genero VARCHAR);
        CREATE TABLE dim_track (
          id_track INTEGER, nombre_track VARCHAR, id_artista INTEGER, id_genero INTEGER,
          duration_ms INTEGER, popularity INTEGER
        );
        CREATE TABLE app_favorite (user_id INTEGER, track_id INTEGER, added_at TIMESTAMP);
        CREATE TABLE app_track_audio_source (
          track_id INTEGER, provider VARCHAR, status VARCHAR, failure_count INTEGER,
          youtube_video_id VARCHAR, source_ref VARCHAR, playable_url VARCHAR,
          query VARCHAR, confidence_score DOUBLE, resolved_at TIMESTAMP
        );
        """
    )
    conn.execute("INSERT INTO dim_artista VALUES (1, 'A')")
    conn.execute("INSERT INTO dim_genero VALUES (1, 'Pop')")
    conn.execute("INSERT INTO dim_track VALUES (10, 'Ok Song', 1, 1, 200000, 80)")
    conn.execute("INSERT INTO dim_track VALUES (11, 'Broken Song', 1, 1, 180000, 50)")
    conn.execute(
        "INSERT INTO app_track_audio_source VALUES (10, 'youtube', 'ok', 0, 'aaaaaaaaaaa', 'aaaaaaaaaaa', NULL, NULL, 1.0, CURRENT_TIMESTAMP)"
    )
    conn.execute(
        "INSERT INTO app_track_audio_source VALUES (11, 'youtube', 'not_found', 3, 'bbbbbbbbbbb', 'bbbbbbbbbbb', NULL, 'unavailable:test', 0.0, CURRENT_TIMESTAMP)"
    )
    conn.execute("INSERT INTO app_favorite VALUES (1, 10, CURRENT_TIMESTAMP), (1, 11, CURRENT_TIMESTAMP)")


def test_favorites_include_unavailable_with_status() -> None:
    conn = duckdb.connect(":memory:")
    _seed(conn)
    rows = list_favorites(conn, 1)
    by_id = {r["id_track"]: r for r in rows}
    assert by_id[10]["playback_status"] == "playable"
    assert by_id[10]["source_unavailable"] is False
    assert by_id[11]["playback_status"] in {"unavailable", "failed", "removed"}
    assert by_id[11]["source_unavailable"] is True


def test_playlist_enrich_marks_unavailable() -> None:
    conn = duckdb.connect(":memory:")
    _seed(conn)
    rows = _enrich_tracks(conn, [10, 11])
    assert rows[0]["playback_status"] == "playable"
    assert rows[1]["source_unavailable"] is True
