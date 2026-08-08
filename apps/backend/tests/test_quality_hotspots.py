"""Unit tests for maintenance hotspots.

Covers three backend hotspots in isolation against minimal in-memory DuckDB
schemas (no FastAPI, no shared session DB). Logic is exercised, never modified.

Hotspots:
  * generate_synthetic_activity  (guards + activity partition)
  * get_tracks_cursor            (keyset pagination)
  * get_recommendations          (aggregate read + fallback)
"""

from __future__ import annotations

import duckdb
import pytest

from app.packages.analytics.services.recommendations.service import get_recommendations
from app.packages.analytics.services.stats.constants import (
    ACTIVITY_FACT_TABLES,
    MAX_TARGET_TOTAL,
)
from app.packages.analytics.services.synthetic.dimensions import split_activity_counts
from app.packages.analytics.services.synthetic.generator import (
    generate_synthetic_activity,
    get_synthetic_limits,
)
from app.packages.streaming.services.tracks.list import get_tracks_cursor


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
def _new_conn() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(":memory:")


def _seed_catalog(conn: duckdb.DuckDBPyConnection) -> None:
    """dim_track + dim_artista + dim_genero with three real tracks."""
    conn.execute(
        """
        CREATE TABLE dim_genero (
            id_genero INTEGER PRIMARY KEY,
            nombre_genero VARCHAR
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE dim_artista (
            id_artista INTEGER PRIMARY KEY,
            nombre_artista VARCHAR
        )
        """
    )
    conn.execute(
        """
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
        )
        """
    )
    conn.execute("INSERT INTO dim_genero VALUES (1, 'Pop'), (2, 'Rock')")
    conn.execute("INSERT INTO dim_artista VALUES (1, 'Aurora'), (2, 'Bowie')")
    conn.execute(
        """
        INSERT INTO dim_track
            (id_track, spotify_track_id, nombre_track, id_artista, id_album,
             id_genero, explicit, duration_ms, popularity)
        VALUES
            (1, 'real_a', 'Alpha',   1, NULL, 1, FALSE, 180000, 95),
            (2, 'real_b', 'Bravo',   2, NULL, 2, FALSE, 200000, 88),
            (3, 'real_c', 'Charlie', 1, NULL, 1, FALSE, 210000, 72)
        """
    )


@pytest.fixture
def catalog_conn() -> duckdb.DuckDBPyConnection:
    conn = _new_conn()
    _seed_catalog(conn)
    yield conn
    conn.close()


# --------------------------------------------------------------------------- #
# Hotspot 1 — generate_synthetic_activity
# --------------------------------------------------------------------------- #
class TestGenerateSyntheticActivity:
    def test_requires_target_or_multiplier(self) -> None:
        conn = _new_conn()
        with pytest.raises(ValueError, match="target_total or multiplier"):
            generate_synthetic_activity(conn)
        conn.close()

    def test_rejects_empty_catalog(self) -> None:
        conn = _new_conn()
        conn.execute(
            "CREATE TABLE dim_track (id_track INTEGER, spotify_track_id VARCHAR)"
        )
        with pytest.raises(ValueError, match="No hay tracks reales"):
            generate_synthetic_activity(conn, target_total=100)
        conn.close()

    def test_rejects_target_over_max(self, catalog_conn: duckdb.DuckDBPyConnection) -> None:
        for table in ACTIVITY_FACT_TABLES:
            catalog_conn.execute(f"CREATE TABLE {table} (id INTEGER)")
        with pytest.raises(ValueError, match="cannot exceed"):
            generate_synthetic_activity(catalog_conn, target_total=MAX_TARGET_TOTAL + 1)

    def test_get_synthetic_limits_shape(self) -> None:
        limits = get_synthetic_limits()
        assert limits["max_target_total"] == MAX_TARGET_TOTAL
        assert set(limits) >= {
            "max_target_total",
            "max_create_per_run",
            "warn_create_above",
            "batch_size",
        }

    def test_split_activity_counts_partitions_exactly(self) -> None:
        target = 1_000_000
        counts = split_activity_counts(target)
        assert set(counts) == {
            "fact_streaming",
            "fact_user_activity",
            "fact_playlist_activity",
            "fact_favorites",
            "fact_searches",
            "fact_stream_sessions",
        }
        assert sum(counts.values()) == target
        assert all(v >= 0 for v in counts.values())
        assert counts["fact_streaming"] == int(target * 0.65)


# --------------------------------------------------------------------------- #
# Hotspot 2 — get_tracks_cursor
# --------------------------------------------------------------------------- #
class TestGetTracksCursor:
    def test_orders_by_popularity_desc(self, catalog_conn: duckdb.DuckDBPyConnection) -> None:
        result = get_tracks_cursor(
            catalog_conn, limit=10, include_total=True, playable_only=False
        )
        names = [t["nombre_track"] for t in result["items"]]
        assert names == ["Alpha", "Bravo", "Charlie"]
        assert result["total"] == 3
        assert result["has_more"] is False
        assert result["next_cursor"] is None

    def test_keyset_pagination_walks_all_rows(
        self, catalog_conn: duckdb.DuckDBPyConnection
    ) -> None:
        page1 = get_tracks_cursor(
            catalog_conn, limit=2, include_total=True, playable_only=False
        )
        assert [t["nombre_track"] for t in page1["items"]] == ["Alpha", "Bravo"]
        assert page1["has_more"] is True
        assert page1["next_cursor"] is not None
        assert page1["total"] == 3

        page2 = get_tracks_cursor(
            catalog_conn, limit=2, cursor=page1["next_cursor"], playable_only=False
        )
        assert [t["nombre_track"] for t in page2["items"]] == ["Charlie"]
        assert page2["has_more"] is False
        assert page2["next_cursor"] is None
        # include_total is suppressed once a cursor is supplied
        assert page2["total"] is None

    def test_limit_is_clamped(self, catalog_conn: duckdb.DuckDBPyConnection) -> None:
        assert get_tracks_cursor(catalog_conn, limit=0, playable_only=False)["limit"] == 1
        assert get_tracks_cursor(catalog_conn, limit=9999, playable_only=False)["limit"] == 500

    def test_invalid_cursor_raises(self, catalog_conn: duckdb.DuckDBPyConnection) -> None:
        with pytest.raises(ValueError, match="Invalid cursor"):
            get_tracks_cursor(catalog_conn, cursor="not-a-cursor", playable_only=False)

    def test_search_filter(self, catalog_conn: duckdb.DuckDBPyConnection) -> None:
        result = get_tracks_cursor(
            catalog_conn, limit=10, search="alpha", playable_only=False
        )
        assert [t["nombre_track"] for t in result["items"]] == ["Alpha"]


# --------------------------------------------------------------------------- #
# Hotspot 3 — get_recommendations
# --------------------------------------------------------------------------- #
class TestGetRecommendations:
    def _seed_agg(self, conn: duckdb.DuckDBPyConnection) -> None:
        conn.execute(
            """
            CREATE TABLE agg_recommendation_scores (
                id_track INTEGER,
                nombre_track VARCHAR,
                nombre_artista VARCHAR,
                nombre_genero VARCHAR,
                recommendation_score DOUBLE,
                engagement_score DOUBLE,
                popularity INTEGER
            )
            """
        )
        conn.execute(
            """
            INSERT INTO agg_recommendation_scores VALUES
                (1, 'Alpha',   'Aurora', 'Pop',  90.0, 80.0, 95),
                (2, 'Bravo',   'Bowie',  'Rock', 70.0, 60.0, 88),
                (3, 'Charlie', 'Aurora', 'Pop',  50.0, 40.0, 72)
            """
        )

    def test_reads_aggregate_scores(self, catalog_conn: duckdb.DuckDBPyConnection) -> None:
        self._seed_agg(catalog_conn)
        rec = get_recommendations(catalog_conn, limit=12)
        assert [t["nombre_track"] for t in rec["for_you"]] == ["Alpha", "Bravo", "Charlie"]
        # aggregates for artists/genres/moods are absent -> empty, no crash
        assert rec["artists"] == []
        assert rec["genres"] == []
        assert rec["moods"] == []
        assert rec["mood_count"] == 0

    def test_favorite_genre_is_prioritized(
        self, catalog_conn: duckdb.DuckDBPyConnection
    ) -> None:
        self._seed_agg(catalog_conn)
        rec = get_recommendations(catalog_conn, limit=12, favorite_genre="Rock")
        # The single Rock track must surface first despite a lower score.
        assert rec["for_you"][0]["nombre_genero"] == "Rock"

    def test_popularity_fallback_when_aggregate_missing(
        self, catalog_conn: duckdb.DuckDBPyConnection
    ) -> None:
        # Consumer recommendations require playable sources under the public contract.
        catalog_conn.execute(
            """
            CREATE TABLE IF NOT EXISTS app_track_audio_source (
                track_id INTEGER PRIMARY KEY,
                provider VARCHAR,
                youtube_video_id VARCHAR,
                source_ref VARCHAR,
                playable_url VARCHAR,
                status VARCHAR,
                failure_count INTEGER DEFAULT 0
            )
            """
        )
        catalog_conn.execute(
            """
            INSERT INTO app_track_audio_source
                (track_id, provider, youtube_video_id, source_ref, playable_url, status, failure_count)
            VALUES
                (1, 'youtube', 'vidA', 'vidA', NULL, 'ok', 0),
                (2, 'youtube', 'vidB', 'vidB', NULL, 'ok', 0),
                (3, 'youtube', 'vidC', 'vidC', NULL, 'ok', 0)
            """
        )
        # No agg_recommendation_scores table -> fallback to popularity ranking.
        rec = get_recommendations(catalog_conn, limit=12)
        names = [t["nombre_track"] for t in rec["for_you"]]
        assert names == ["Alpha", "Bravo", "Charlie"]
        assert rec["for_you"][0]["recommendation_score"] == 95
