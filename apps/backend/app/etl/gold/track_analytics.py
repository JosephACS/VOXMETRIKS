from __future__ import annotations

import duckdb

from app.etl.gold._helpers import rebuild_table, stream_events_table, table_exists

AGG_TRACKS_POPULARES_DDL = """
CREATE TABLE agg_tracks_populares (
    id_track          INTEGER PRIMARY KEY,
    nombre_track      VARCHAR,
    nombre_artista    VARCHAR,
    popularity        INTEGER,
    total_streams     INTEGER,
    engagement_score  DOUBLE
)
"""


def build_agg_tracks_populares(conn: duckdb.DuckDBPyConnection) -> int:
    events = stream_events_table(conn)
    use_silver = table_exists(conn, "silver_tracks")

    track_join = (
        """
        INNER JOIN silver_tracks st ON st.track_id = dt.spotify_track_id
        """
        if use_silver
        else ""
    )
    popularity_expr = "COALESCE(st.popularity, dt.popularity, 0)" if use_silver else "COALESCE(dt.popularity, 0)"
    name_expr = "COALESCE(st.track_name, dt.nombre_track)" if use_silver else "dt.nombre_track"

    insert_sql = f"""
        INSERT INTO agg_tracks_populares (
            id_track, nombre_track, nombre_artista, popularity, total_streams, engagement_score
        )
        WITH stream_agg AS (
            SELECT
                fs.id_track,
                COUNT(*) AS total_streams,
                ROUND(AVG(
                    COALESCE(fs.streams, 1) * COALESCE(fs.duracion_ms, 0) / 1000.0
                ), 2) AS engagement_score
            FROM {events} fs
            GROUP BY 1
        )
        SELECT
            dt.id_track,
            {name_expr} AS nombre_track,
            da.nombre_artista,
            {popularity_expr} AS popularity,
            COALESCE(sa.total_streams, 0) AS total_streams,
            COALESCE(sa.engagement_score, 0) AS engagement_score
        FROM dim_track dt
        LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
        {track_join}
        LEFT JOIN stream_agg sa ON sa.id_track = dt.id_track
        WHERE COALESCE(sa.total_streams, 0) > 0
           OR {popularity_expr} > 0
        ORDER BY total_streams DESC, popularity DESC
    """
    return rebuild_table(
        conn,
        "agg_tracks_populares",
        AGG_TRACKS_POPULARES_DDL,
        insert_sql,
        label="popular tracks",
    )
