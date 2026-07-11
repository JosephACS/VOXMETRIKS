from __future__ import annotations

import duckdb

from app.etl.gold._helpers import rebuild_table, stream_events_all_table

AGG_ARTIST_GROWTH_DDL = """
CREATE TABLE agg_artist_growth (
    id_artista       INTEGER PRIMARY KEY,
    nombre_artista   VARCHAR,
    streams_7d       INTEGER,
    streams_30d      INTEGER,
    growth_pct       DOUBLE,
    total_followers  INTEGER
)
"""


def build_agg_artist_growth(conn: duckdb.DuckDBPyConnection) -> int:
    events = stream_events_all_table(conn)
    insert_sql = f"""
        INSERT INTO agg_artist_growth (
            id_artista, nombre_artista, streams_7d, streams_30d, growth_pct, total_followers
        )
        WITH stream_base AS (
            SELECT
                fs.id_streaming,
                fs.id_usuario,
                fs.fecha_evento,
                dt.id_artista,
                da.nombre_artista
            FROM {events} fs
            INNER JOIN dim_track dt ON dt.id_track = fs.id_track
            INNER JOIN dim_artista da ON da.id_artista = dt.id_artista
        ),
        ref_date AS (
            SELECT COALESCE(MAX(CAST(fecha_evento AS DATE)), CURRENT_DATE) AS max_d
            FROM stream_base
        ),
        w7 AS (
            SELECT id_artista, nombre_artista, COUNT(*) AS cnt
            FROM stream_base, ref_date
            WHERE CAST(fecha_evento AS DATE) > max_d - INTERVAL 7 DAY
            GROUP BY 1, 2
        ),
        prev7 AS (
            SELECT id_artista, COUNT(*) AS cnt
            FROM stream_base, ref_date
            WHERE CAST(fecha_evento AS DATE) <= max_d - INTERVAL 7 DAY
              AND CAST(fecha_evento AS DATE) > max_d - INTERVAL 14 DAY
            GROUP BY 1
        ),
        w30 AS (
            SELECT id_artista, COUNT(*) AS cnt
            FROM stream_base, ref_date
            WHERE CAST(fecha_evento AS DATE) > max_d - INTERVAL 30 DAY
            GROUP BY 1
        ),
        listeners AS (
            SELECT id_artista, COUNT(DISTINCT id_usuario) AS users
            FROM stream_base, ref_date
            WHERE CAST(fecha_evento AS DATE) > max_d - INTERVAL 30 DAY
            GROUP BY 1
        )
        SELECT
            da.id_artista,
            da.nombre_artista,
            COALESCE(w7.cnt, 0) AS streams_7d,
            COALESCE(w30.cnt, 0) AS streams_30d,
            CASE
                WHEN COALESCE(prev7.cnt, 0) = 0 THEN 0
                ELSE ROUND((COALESCE(w7.cnt, 0) - prev7.cnt) * 100.0 / prev7.cnt, 1)
            END AS growth_pct,
            COALESCE(listeners.users, 0) * 3 + (da.id_artista % 1000) AS total_followers
        FROM dim_artista da
        LEFT JOIN w7 ON w7.id_artista = da.id_artista
        LEFT JOIN prev7 ON prev7.id_artista = da.id_artista
        LEFT JOIN w30 ON w30.id_artista = da.id_artista
        LEFT JOIN listeners ON listeners.id_artista = da.id_artista
        WHERE COALESCE(w7.cnt, 0) > 0 OR COALESCE(w30.cnt, 0) > 0
        ORDER BY growth_pct DESC, streams_7d DESC
    """
    return rebuild_table(
        conn,
        "agg_artist_growth",
        AGG_ARTIST_GROWTH_DDL,
        insert_sql,
        label="artist growth",
    )
