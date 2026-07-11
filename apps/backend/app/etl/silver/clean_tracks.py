from __future__ import annotations

import duckdb

from app.core.logging import get_logger
from app.etl.connection import count_rows, execute_ddl

logger = get_logger(__name__)

SILVER_TRACKS_DDL = """
CREATE TABLE IF NOT EXISTS silver_tracks (
    track_id              VARCHAR PRIMARY KEY,
    track_name            VARCHAR NOT NULL,
    track_name_normalized VARCHAR NOT NULL,
    artists               VARCHAR,
    album_name            VARCHAR,
    popularity            INTEGER,
    duration_ms           INTEGER,
    duration_min          DOUBLE,
    explicit              BOOLEAN,
    danceability          DOUBLE,
    energy                DOUBLE,
    key_col               INTEGER,
    loudness              DOUBLE,
    mode_col              INTEGER,
    speechiness           DOUBLE,
    acousticness          DOUBLE,
    instrumentalness      DOUBLE,
    liveness              DOUBLE,
    valence               DOUBLE,
    tempo                 DOUBLE,
    time_signature        INTEGER,
    track_genre           VARCHAR,
    cleaned_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""


def clean_tracks(conn: duckdb.DuckDBPyConnection) -> dict:
    """Transform bronze_raw_tracks → silver_tracks using SQL-only pipeline."""
    logger.info("[SILVER] Cleaning tracks bronze_raw_tracks → silver_tracks")
    execute_ddl(conn, SILVER_TRACKS_DDL)

    before = count_rows(conn, "bronze_raw_tracks") if _table_exists(conn, "bronze_raw_tracks") else 0

    conn.execute("DELETE FROM silver_tracks")

    conn.execute(
        """
        INSERT INTO silver_tracks (
            track_id, track_name, track_name_normalized, artists, album_name,
            popularity, duration_ms, duration_min, explicit, danceability, energy,
            key_col, loudness, mode_col, speechiness, acousticness, instrumentalness,
            liveness, valence, tempo, time_signature, track_genre, cleaned_at
        )
        SELECT
            track_id,
            track_name,
            lower(trim(track_name)) AS track_name_normalized,
            artists,
            album_name,
            popularity,
            duration_ms,
            ROUND(duration_ms / 60000.0, 4) AS duration_min,
            explicit,
            danceability,
            energy,
            key_col,
            loudness,
            mode_col,
            speechiness,
            acousticness,
            instrumentalness,
            liveness,
            valence,
            tempo,
            time_signature,
            track_genre,
            CURRENT_TIMESTAMP
        FROM (
            SELECT *,
                   ROW_NUMBER() OVER (
                       PARTITION BY track_id ORDER BY ingestion_timestamp DESC
                   ) AS rn
            FROM bronze_raw_tracks
            WHERE track_name IS NOT NULL
              AND energy IS NOT NULL
              AND track_id IS NOT NULL
        ) ranked
        WHERE rn = 1
        """
    )

    after = count_rows(conn, "silver_tracks")
    logger.info("[SILVER] Cleaning tracks → silver_tracks (%s rows)", after)
    return {
        "source": "bronze_raw_tracks",
        "target": "silver_tracks",
        "rows_in": before,
        "rows_out": after,
        "status": "ok",
    }


def _table_exists(conn: duckdb.DuckDBPyConnection, table: str) -> bool:
    return table in {r[0] for r in conn.execute("SHOW TABLES").fetchall()}
