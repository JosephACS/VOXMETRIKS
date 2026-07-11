from __future__ import annotations

import duckdb

from app.core.logging import get_logger
from app.etl.connection import count_rows, execute_ddl

logger = get_logger(__name__)

BRONZE_RAW_TRACKS_DDL = """
CREATE TABLE IF NOT EXISTS bronze_raw_tracks (
    id               INTEGER,
    track_id         VARCHAR NOT NULL,
    track_name       VARCHAR,
    artists          VARCHAR,
    album_name       VARCHAR,
    popularity       INTEGER,
    duration_ms      INTEGER,
    explicit         BOOLEAN,
    danceability     DOUBLE,
    energy           DOUBLE,
    key_col          INTEGER,
    loudness         DOUBLE,
    mode_col         INTEGER,
    speechiness      DOUBLE,
    acousticness     DOUBLE,
    instrumentalness DOUBLE,
    liveness         DOUBLE,
    valence          DOUBLE,
    tempo            DOUBLE,
    time_signature   INTEGER,
    track_genre      VARCHAR,
    source_fecha_ingesta TIMESTAMP,
    ingestion_timestamp  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (track_id)
)
"""


def ensure_bronze_table(conn: duckdb.DuckDBPyConnection) -> None:
    execute_ddl(conn, BRONZE_RAW_TRACKS_DDL)
    logger.info("[BRONZE] Table bronze_raw_tracks ensured")


def load_bronze_batch(conn: duckdb.DuckDBPyConnection, rows_sql: str) -> int:
    """
    Execute batch insert SQL and return affected row count.
    Caller supplies full INSERT ... SELECT statement.
    """
    before = count_rows(conn, "bronze_raw_tracks")
    conn.execute(rows_sql)
    after = count_rows(conn, "bronze_raw_tracks")
    inserted = max(after - before, 0)
    logger.info("[BRONZE] Batch load complete inserted=%s total=%s", inserted, after)
    return inserted


def upsert_from_source(conn: duckdb.DuckDBPyConnection, source_table: str = "raw_spotify") -> dict:
    """
    Idempotent bronze load: replace rows for track_ids present in source,
    skip duplicates already loaded with same track_id.
    """
    ensure_bronze_table(conn)

    if source_table not in {r[0] for r in conn.execute("SHOW TABLES").fetchall()}:
        raise RuntimeError(f"Source table '{source_table}' not found in warehouse")

    source_count = count_rows(conn, source_table)

    conn.execute(
        f"""
        DELETE FROM bronze_raw_tracks
        WHERE track_id IN (SELECT track_id FROM {source_table} WHERE track_id IS NOT NULL)
        """
    )

    conn.execute(
        f"""
        INSERT INTO bronze_raw_tracks (
            id, track_id, track_name, artists, album_name, popularity, duration_ms,
            explicit, danceability, energy, key_col, loudness, mode_col, speechiness,
            acousticness, instrumentalness, liveness, valence, tempo, time_signature,
            track_genre, source_fecha_ingesta, ingestion_timestamp
        )
        SELECT
            id,
            track_id,
            track_name,
            artists,
            album_name,
            popularity,
            duration_ms,
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
            fecha_ingesta,
            CURRENT_TIMESTAMP
        FROM (
            SELECT *,
                   ROW_NUMBER() OVER (PARTITION BY track_id ORDER BY id) AS rn
            FROM {source_table}
            WHERE track_id IS NOT NULL
        ) deduped
        WHERE rn = 1
        """
    )

    bronze_count = count_rows(conn, "bronze_raw_tracks")
    logger.info(
        "[BRONZE] Upsert from %s source_rows=%s bronze_total=%s",
        source_table,
        source_count,
        bronze_count,
    )
    return {
        "source_table": source_table,
        "source_rows": source_count,
        "bronze_rows": bronze_count,
    }
