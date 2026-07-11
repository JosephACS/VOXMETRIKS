from __future__ import annotations

import duckdb

from app.etl.gold._helpers import rebuild_table, stream_events_all_table, table_exists

AGG_GENERO_POPULARIDAD_DDL = """
CREATE TABLE agg_genero_popularidad (
    id_genero            INTEGER PRIMARY KEY,
    nombre_genero        VARCHAR,
    popularidad_promedio DOUBLE,
    energia_promedio     DOUBLE,
    total_tracks         INTEGER,
    total_artistas       INTEGER
)
"""

AGG_GENRE_TRENDS_DDL = """
CREATE TABLE agg_genre_trends (
    id_genero       INTEGER PRIMARY KEY,
    nombre_genero   VARCHAR,
    streams_7d      INTEGER,
    streams_prev_7d INTEGER,
    trend_pct       DOUBLE,
    avg_popularity  DOUBLE
)
"""


def build_agg_genero_popularidad(conn: duckdb.DuckDBPyConnection) -> int:
    use_silver = table_exists(conn, "silver_tracks")
    track_source = "silver_tracks st INNER JOIN dim_track dt ON dt.spotify_track_id = st.track_id" if use_silver else "dim_track dt"
    pop_expr = "AVG(COALESCE(st.popularity, dt.popularity, 0))" if use_silver else "AVG(COALESCE(dt.popularity, 0))"
    energy_expr = "AVG(COALESCE(st.energy, dt.energy, 0))" if use_silver else "AVG(COALESCE(dt.energy, 0))"

    insert_sql = f"""
        INSERT INTO agg_genero_popularidad (
            id_genero, nombre_genero, popularidad_promedio, energia_promedio,
            total_tracks, total_artistas
        )
        SELECT
            dg.id_genero,
            dg.nombre_genero,
            ROUND({pop_expr}, 2) AS popularidad_promedio,
            ROUND({energy_expr}, 2) AS energia_promedio,
            COUNT(DISTINCT dt.id_track) AS total_tracks,
            COUNT(DISTINCT dt.id_artista) AS total_artistas
        FROM dim_genero dg
        LEFT JOIN {track_source} ON dt.id_genero = dg.id_genero
        GROUP BY dg.id_genero, dg.nombre_genero
        ORDER BY popularidad_promedio DESC
    """
    return rebuild_table(
        conn,
        "agg_genero_popularidad",
        AGG_GENERO_POPULARIDAD_DDL,
        insert_sql,
        label="genre popularity",
    )


def build_agg_genre_trends(conn: duckdb.DuckDBPyConnection) -> int:
    events = stream_events_all_table(conn)
    insert_sql = f"""
        INSERT INTO agg_genre_trends (
            id_genero, nombre_genero, streams_7d, streams_prev_7d, trend_pct, avg_popularity
        )
        WITH ref_date AS (
            SELECT COALESCE(MAX(CAST(fecha_evento AS DATE)), CURRENT_DATE) AS max_d
            FROM {events}
        ),
        genre_streams AS (
            SELECT
                dg.id_genero,
                dg.nombre_genero,
                CAST(fs.fecha_evento AS DATE) AS fecha,
                dt.popularity
            FROM {events} fs
            INNER JOIN dim_track dt ON dt.id_track = fs.id_track
            INNER JOIN dim_genero dg ON dg.id_genero = dt.id_genero
        ),
        s7 AS (
            SELECT id_genero, nombre_genero, COUNT(*) AS cnt, ROUND(AVG(popularity), 1) AS avg_pop
            FROM genre_streams, ref_date
            WHERE fecha > max_d - INTERVAL 7 DAY
            GROUP BY 1, 2
        ),
        sp AS (
            SELECT id_genero, COUNT(*) AS cnt
            FROM genre_streams, ref_date
            WHERE fecha <= max_d - INTERVAL 7 DAY
              AND fecha > max_d - INTERVAL 14 DAY
            GROUP BY 1
        )
        SELECT
            dg.id_genero,
            dg.nombre_genero,
            COALESCE(s7.cnt, 0) AS streams_7d,
            COALESCE(sp.cnt, 0) AS streams_prev_7d,
            CASE
                WHEN COALESCE(sp.cnt, 0) = 0 THEN 0
                ELSE ROUND((COALESCE(s7.cnt, 0) - sp.cnt) * 100.0 / sp.cnt, 1)
            END AS trend_pct,
            COALESCE(s7.avg_pop, 0) AS avg_popularity
        FROM dim_genero dg
        LEFT JOIN s7 ON s7.id_genero = dg.id_genero
        LEFT JOIN sp ON sp.id_genero = dg.id_genero
        ORDER BY trend_pct DESC, streams_7d DESC
    """
    return rebuild_table(
        conn,
        "agg_genre_trends",
        AGG_GENRE_TRENDS_DDL,
        insert_sql,
        label="genre trends",
    )
