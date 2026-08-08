"""Public visibility vs admin mutation reads for draft tracks."""

from __future__ import annotations

import duckdb
import pytest

from app.packages.catalog.services.tracks.detail import (
    get_track_by_id,
    get_track_by_id_raw,
)
from app.packages.catalog.services.tracks.list import get_tracks
from app.packages.catalog.services.tracks.mutations import delete_track, update_track
from app.packages.catalog.services.tracks.search import search_tracks


def _seed(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute(
        """
        CREATE TABLE dim_artista (id_artista INTEGER, nombre_artista VARCHAR);
        CREATE TABLE dim_genero (id_genero INTEGER, nombre_genero VARCHAR);
        CREATE TABLE dim_track (
          id_track INTEGER PRIMARY KEY,
          spotify_track_id VARCHAR,
          nombre_track VARCHAR,
          id_artista INTEGER,
          id_album INTEGER,
          id_genero INTEGER,
          explicit BOOLEAN,
          duration_ms INTEGER,
          popularity INTEGER
        );
        CREATE TABLE app_release_submission (
          id INTEGER PRIMARY KEY,
          status VARCHAR,
          planned_release_date DATE
        );
        CREATE TABLE app_release_submission_track (
          submission_id INTEGER,
          warehouse_track_id INTEGER
        );
        """
    )
    conn.execute("INSERT INTO dim_artista VALUES (1, 'Artist')")
    conn.execute("INSERT INTO dim_genero VALUES (1, 'Pop')")
    conn.execute(
        """
        INSERT INTO dim_track VALUES
          (100, 'pub', 'Public Hit', 1, NULL, 1, false, 200000, 90),
          (101, 'drf', 'Draft Song', 1, NULL, 1, false, 180000, 10)
        """
    )
    conn.execute(
        "INSERT INTO app_release_submission VALUES (1, 'draft', NULL)"
    )
    conn.execute(
        "INSERT INTO app_release_submission_track VALUES (1, 101)"
    )


@pytest.fixture()
def conn() -> duckdb.DuckDBPyConnection:
    c = duckdb.connect(":memory:")
    _seed(c)
    return c


def test_public_hides_draft_list_search_detail(conn: duckdb.DuckDBPyConnection) -> None:
    items, total = get_tracks(conn, page=1, limit=50, playable_only=False)
    ids = {i["id_track"] for i in items}
    assert 100 in ids
    assert 101 not in ids
    assert total == 1

    search_items, search_total, _, _ = search_tracks(
        conn, "Draft", limit=20, page=1, playable_only=False
    )
    assert search_total == 0
    assert all(i["id_track"] != 101 for i in search_items)

    assert get_track_by_id(conn, 101) is None
    assert get_track_by_id(conn, 100) is not None


def test_admin_raw_can_mutate_draft_without_false_404(
    conn: duckdb.DuckDBPyConnection,
) -> None:
    raw = get_track_by_id_raw(conn, 101)
    assert raw is not None
    assert raw["nombre_track"] == "Draft Song"

    updated = update_track(conn, 101, nombre_track="Draft Song Renamed")
    assert updated is not None
    assert updated["nombre_track"] == "Draft Song Renamed"
    # Public still hidden
    assert get_track_by_id(conn, 101) is None
    assert get_track_by_id_raw(conn, 101)["nombre_track"] == "Draft Song Renamed"

    assert delete_track(conn, 101) is True
    assert get_track_by_id_raw(conn, 101) is None
