"""Synthetic activity fact-table writers."""

from __future__ import annotations

import duckdb

from app.core.query_helpers import count_rows


def real_track_count(conn: duckdb.DuckDBPyConnection) -> int:
    return int(conn.execute("""
        SELECT COUNT(*) FROM dim_track
        WHERE spotify_track_id IS NULL OR spotify_track_id NOT LIKE 'syn_%'
    """).fetchone()[0])


def replace_fact_streaming(conn: duckdb.DuckDBPyConnection, n: int) -> None:
    conn.execute("DELETE FROM fact_streaming")
    if n <= 0:
        return
    track_count = real_track_count(conn)
    user_count = max(count_rows(conn, "dim_usuario"), 1)
    playlist_count = max(count_rows(conn, "dim_playlist"), 1)
    conn.execute(f"""
        INSERT INTO fact_streaming (
            id_streaming, id_track, id_usuario, id_tiempo, id_playlist,
            streams, duracion_ms, completado, skipped, device_type, platform,
            session_id, hour_of_day, fecha_evento
        )
        WITH tracks AS (
            SELECT id_track, duration_ms, popularity,
                   ROW_NUMBER() OVER (ORDER BY id_track) rn, COUNT(*) OVER () total
            FROM dim_track
            WHERE spotify_track_id IS NULL OR spotify_track_id NOT LIKE 'syn_%'
        ),
        tiempo AS (
            SELECT id_tiempo, fecha, ROW_NUMBER() OVER (ORDER BY fecha DESC) rn
            FROM dim_tiempo WHERE fecha <= CURRENT_DATE
        )
        SELECT g.i, t.id_track,
               1 + ((g.i * 17 + (g.i // 13) * 31) % {user_count}),
               ti.id_tiempo,
               1 + (g.i % {playlist_count}),
               1 + (COALESCE(t.popularity, 0) / 20), COALESCE(t.duration_ms, 180000),
               (g.i % 100) >= 18, (g.i % 100) < 22,
               CASE
                 WHEN (g.i % 100) < 45 THEN 'mobile'
                 WHEN (g.i % 100) < 68 THEN 'desktop'
                 WHEN (g.i % 100) < 85 THEN 'web'
                 WHEN (g.i % 100) < 93 THEN 'tablet'
                 ELSE 'smart_tv'
               END,
               CASE
                 WHEN (g.i % 100) < 45 THEN (ARRAY['ios','android'])[1 + (g.i % 2)]
                 WHEN (g.i % 100) < 68 THEN 'desktop'
                 WHEN (g.i % 100) < 85 THEN 'web'
                 ELSE (ARRAY['ios','android','car'])[1 + (g.i % 3)]
               END,
               1 + (g.i % GREATEST(1, CAST({n} / 20 AS INTEGER))),
               CASE
                 WHEN (g.i % 100) < 8 THEN (g.i % 6)
                 WHEN (g.i % 100) < 25 THEN 6 + (g.i % 6)
                 WHEN (g.i % 100) < 45 THEN 12 + (g.i % 5)
                 WHEN (g.i % 100) < 75 THEN 17 + (g.i % 4)
                 ELSE 20 + (g.i % 4)
               END,
               CAST(ti.fecha AS TIMESTAMP)
                 + (
                   CASE
                     WHEN (g.i % 100) < 8 THEN (g.i % 6)
                     WHEN (g.i % 100) < 25 THEN 6 + (g.i % 6)
                     WHEN (g.i % 100) < 45 THEN 12 + (g.i % 5)
                     WHEN (g.i % 100) < 75 THEN 17 + (g.i % 4)
                     ELSE 20 + (g.i % 4)
                   END
                 ) * 3600 * INTERVAL '1' SECOND
                 + (g.i % 3600) * INTERVAL '1' SECOND
        FROM generate_series(1, {n}) g(i)
        JOIN tracks t ON t.rn = ((g.i - 1) % {track_count}) + 1
        JOIN tiempo ti ON ti.rn = 1 + (
          CASE
            WHEN (g.i % 100) < 50 THEN ((g.i * 17 + (g.i // 11) * 31) % 30)
            WHEN (g.i % 100) < 80 THEN 30 + ((g.i * 13 + (g.i // 19) * 23) % 30)
            ELSE 60 + ((g.i * 19 + (g.i // 7) * 29) % 30)
          END
        )
    """)


def replace_fact_user_activity(conn: duckdb.DuckDBPyConnection, n: int) -> None:
    conn.execute("DELETE FROM fact_user_activity")
    if n <= 0:
        return
    track_count = real_track_count(conn)
    user_count = max(count_rows(conn, "dim_usuario"), 1)
    conn.execute(f"""
        INSERT INTO fact_user_activity (
            id_activity, id_usuario, id_track, id_tiempo, action_type,
            device_type, duration_ms, fecha_evento
        )
        WITH tracks AS (
            SELECT id_track, ROW_NUMBER() OVER (ORDER BY id_track) rn
            FROM dim_track
            WHERE spotify_track_id IS NULL OR spotify_track_id NOT LIKE 'syn_%'
        ),
        tiempo AS (
            SELECT id_tiempo, ROW_NUMBER() OVER (ORDER BY fecha DESC) rn
            FROM dim_tiempo WHERE fecha <= CURRENT_DATE
        )
        SELECT i, 1 + (i % {user_count}), t.id_track, ti.id_tiempo,
               (ARRAY['play','pause','skip','like','share','add_playlist'])[1 + (i % 6)],
               (ARRAY['mobile','desktop','web'])[1 + (i % 3)],
               30000 + (i % 240000),
               CURRENT_TIMESTAMP - (i % 604800) * INTERVAL '1' SECOND
        FROM generate_series(1, {n}) g(i)
        JOIN tracks t ON t.rn = ((i - 1) % {track_count}) + 1
        JOIN tiempo ti ON ti.rn = 1 + (i % 90)
    """)


def replace_fact_playlist_activity(conn: duckdb.DuckDBPyConnection, n: int) -> None:
    conn.execute("DELETE FROM fact_playlist_activity")
    if n <= 0:
        return
    track_count = real_track_count(conn)
    user_count = max(count_rows(conn, "dim_usuario"), 1)
    playlist_count = max(count_rows(conn, "dim_playlist"), 1)
    conn.execute(f"""
        INSERT INTO fact_playlist_activity (
            id_activity, id_playlist, id_usuario, id_track, action_type, fecha_evento
        )
        WITH tracks AS (
            SELECT id_track, ROW_NUMBER() OVER (ORDER BY id_track) rn
            FROM dim_track
            WHERE spotify_track_id IS NULL OR spotify_track_id NOT LIKE 'syn_%'
        )
        SELECT i, 1 + (i % {playlist_count}), 1 + (i % {user_count}), t.id_track,
               (ARRAY['add','remove','play','follow','share'])[1 + (i % 5)],
               CURRENT_TIMESTAMP - (i % 2592000) * INTERVAL '1' SECOND
        FROM generate_series(1, {n}) g(i)
        JOIN tracks t ON t.rn = ((i - 1) % {track_count}) + 1
    """)


def replace_fact_favorites(conn: duckdb.DuckDBPyConnection, n: int) -> None:
    conn.execute("DELETE FROM fact_favorites")
    if n <= 0:
        return
    track_count = real_track_count(conn)
    user_count = max(count_rows(conn, "dim_usuario"), 1)
    conn.execute(f"""
        INSERT INTO fact_favorites (id_favorite, id_usuario, id_track, id_tiempo, fecha_evento)
        WITH tracks AS (
            SELECT id_track, ROW_NUMBER() OVER (ORDER BY id_track) rn
            FROM dim_track
            WHERE spotify_track_id IS NULL OR spotify_track_id NOT LIKE 'syn_%'
        ),
        tiempo AS (
            SELECT id_tiempo, ROW_NUMBER() OVER (ORDER BY fecha DESC) rn
            FROM dim_tiempo WHERE fecha <= CURRENT_DATE
        )
        SELECT i, 1 + (i % {user_count}), t.id_track, ti.id_tiempo,
               CURRENT_TIMESTAMP - (i % 7776000) * INTERVAL '1' SECOND
        FROM generate_series(1, {n}) g(i)
        JOIN tracks t ON t.rn = ((i - 1) % {track_count}) + 1
        JOIN tiempo ti ON ti.rn = 1 + (i % 60)
    """)


def replace_fact_searches(conn: duckdb.DuckDBPyConnection, n: int) -> None:
    conn.execute("DELETE FROM fact_searches")
    if n <= 0:
        return
    user_count = max(count_rows(conn, "dim_usuario"), 1)
    conn.execute(f"""
        INSERT INTO fact_searches (id_search, id_usuario, query_text, results_count, id_tiempo, fecha_evento)
        WITH tiempo AS (
            SELECT id_tiempo, ROW_NUMBER() OVER (ORDER BY fecha DESC) rn
            FROM dim_tiempo WHERE fecha <= CURRENT_DATE
        )
        SELECT i, 1 + (i % {user_count}),
               (ARRAY['bad bunny','taylor swift','drake','reggaeton','rock','pop','chill',
                      'workout','latin hits','indie','focus','party','electronic','jazz',
                      'kpop','metal','hip hop','oldies','discover weekly','sad songs'])[1 + (i % 20)],
               5 + (i % 95), ti.id_tiempo,
               CURRENT_TIMESTAMP - (i % 1209600) * INTERVAL '1' SECOND
        FROM generate_series(1, {n}) g(i)
        JOIN tiempo ti ON ti.rn = 1 + (i % 30)
    """)


def replace_fact_stream_sessions(conn: duckdb.DuckDBPyConnection, n: int) -> None:
    conn.execute("DELETE FROM fact_stream_sessions")
    if n <= 0:
        return
    user_count = max(count_rows(conn, "dim_usuario"), 1)
    conn.execute(f"""
        INSERT INTO fact_stream_sessions (
            id_session, id_usuario, device_type, platform,
            session_start, session_end, tracks_played, total_ms, skips
        )
        SELECT i, 1 + (i % {user_count}),
               (ARRAY['mobile','desktop','tablet','web','smart_tv'])[1 + (i % 5)],
               (ARRAY['ios','android','web','desktop','car'])[1 + (i % 5)],
               CURRENT_TIMESTAMP - (i % 604800) * INTERVAL '1' SECOND,
               CURRENT_TIMESTAMP - (i % 604800) * INTERVAL '1' SECOND + (1800 + i % 5400) * INTERVAL '1' SECOND,
               3 + (i % 25), 180000 + (i % 3600000), i % 8
        FROM generate_series(1, {n}) g(i)
    """)
