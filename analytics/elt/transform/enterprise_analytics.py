"""
Enterprise Gold layer — streaming facts, behavioral analytics, Gold aggregates.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger("voxmetrik.enterprise")

N_STREAMING = 220_000
N_USER_ACTIVITY = 40_000
N_PLAYLIST_ACTIVITY = 15_000
N_FAVORITES = 12_000
N_SEARCHES = 8_000
N_SESSIONS = 5_000

ENTERPRISE_DDL: List[str] = [
    """
    CREATE TABLE IF NOT EXISTS ctl_pipeline_stages (
        id_stage INTEGER PRIMARY KEY, run_id INTEGER NOT NULL,
        stage VARCHAR NOT NULL, layer VARCHAR NOT NULL,
        started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        duration_ms INTEGER DEFAULT 0, rows_in INTEGER DEFAULT 0,
        rows_out INTEGER DEFAULT 0, status VARCHAR NOT NULL DEFAULT 'OK',
        details VARCHAR
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_user_activity (
        id_activity INTEGER PRIMARY KEY, id_usuario INTEGER NOT NULL,
        id_track INTEGER, id_tiempo INTEGER, action_type VARCHAR NOT NULL,
        device_type VARCHAR DEFAULT 'mobile', duration_ms INTEGER DEFAULT 0,
        fecha_evento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_playlist_activity (
        id_activity INTEGER PRIMARY KEY, id_playlist INTEGER NOT NULL,
        id_usuario INTEGER, id_track INTEGER, action_type VARCHAR NOT NULL,
        fecha_evento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_favorites (
        id_favorite INTEGER PRIMARY KEY, id_usuario INTEGER NOT NULL,
        id_track INTEGER NOT NULL, id_tiempo INTEGER,
        fecha_evento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_searches (
        id_search INTEGER PRIMARY KEY, id_usuario INTEGER,
        query_text VARCHAR NOT NULL, results_count INTEGER DEFAULT 0,
        id_tiempo INTEGER, fecha_evento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_stream_sessions (
        id_session INTEGER PRIMARY KEY, id_usuario INTEGER NOT NULL,
        device_type VARCHAR NOT NULL, platform VARCHAR NOT NULL,
        session_start TIMESTAMP NOT NULL, session_end TIMESTAMP,
        tracks_played INTEGER DEFAULT 0, total_ms INTEGER DEFAULT 0,
        skips INTEGER DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS agg_daily_streams (
        fecha DATE PRIMARY KEY, total_streams INTEGER DEFAULT 0,
        unique_users INTEGER DEFAULT 0, unique_tracks INTEGER DEFAULT 0,
        avg_duration_ms DOUBLE DEFAULT 0, skip_count INTEGER DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS agg_user_activity (
        id_usuario INTEGER PRIMARY KEY, total_plays INTEGER DEFAULT 0,
        total_skips INTEGER DEFAULT 0, total_likes INTEGER DEFAULT 0,
        engagement_score DOUBLE DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS agg_genre_trends (
        id_genero INTEGER PRIMARY KEY, nombre_genero VARCHAR,
        streams_7d INTEGER DEFAULT 0, streams_prev_7d INTEGER DEFAULT 0,
        trend_pct DOUBLE DEFAULT 0, avg_popularity DOUBLE DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS agg_artist_growth (
        id_artista INTEGER PRIMARY KEY, nombre_artista VARCHAR,
        streams_7d INTEGER DEFAULT 0, streams_30d INTEGER DEFAULT 0,
        growth_pct DOUBLE DEFAULT 0, total_followers INTEGER DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS agg_platform_usage (
        platform VARCHAR, device_type VARCHAR, session_count INTEGER DEFAULT 0,
        total_streams INTEGER DEFAULT 0, avg_session_min DOUBLE DEFAULT 0,
        share_pct DOUBLE DEFAULT 0,
        PRIMARY KEY (platform, device_type)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS agg_top_playlists (
        id_playlist INTEGER PRIMARY KEY, nombre VARCHAR,
        total_plays INTEGER DEFAULT 0, total_tracks INTEGER DEFAULT 0,
        unique_listeners INTEGER DEFAULT 0, avg_completion DOUBLE DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS agg_recommendation_scores (
        id_track INTEGER PRIMARY KEY, nombre_track VARCHAR,
        recommendation_score DOUBLE DEFAULT 0, engagement_score DOUBLE DEFAULT 0,
        popularity INTEGER DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS agg_user_engagement (
        segment VARCHAR PRIMARY KEY, user_count INTEGER DEFAULT 0,
        avg_plays DOUBLE DEFAULT 0, avg_session_min DOUBLE DEFAULT 0,
        retention_pct DOUBLE DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS agg_streaming_devices (
        device_type VARCHAR PRIMARY KEY, stream_count INTEGER DEFAULT 0,
        unique_users INTEGER DEFAULT 0, share_pct DOUBLE DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS agg_recent_activity (
        id_activity INTEGER PRIMARY KEY, activity_type VARCHAR,
        label VARCHAR, metric_value INTEGER DEFAULT 0, fecha DATE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS agg_top_searches (
        query_text VARCHAR PRIMARY KEY, search_count INTEGER DEFAULT 0,
        avg_results DOUBLE DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS agg_user_retention (
        cohort_week VARCHAR PRIMARY KEY, users_cohort INTEGER DEFAULT 0,
        week_1_pct DOUBLE DEFAULT 0, week_2_pct DOUBLE DEFAULT 0,
        week_4_pct DOUBLE DEFAULT 0
    )
    """,
]

MIGRATION_ALTER: List[str] = [
    "ALTER TABLE fact_streaming ADD COLUMN IF NOT EXISTS skipped BOOLEAN DEFAULT FALSE",
    "ALTER TABLE fact_streaming ADD COLUMN IF NOT EXISTS device_type VARCHAR DEFAULT 'mobile'",
    "ALTER TABLE fact_streaming ADD COLUMN IF NOT EXISTS platform VARCHAR DEFAULT 'web'",
    "ALTER TABLE fact_streaming ADD COLUMN IF NOT EXISTS session_id INTEGER",
    "ALTER TABLE fact_streaming ADD COLUMN IF NOT EXISTS hour_of_day INTEGER",
]

ENTERPRISE_EXPORT_TABLES = [
    "fact_user_activity", "fact_playlist_activity", "fact_favorites",
    "fact_searches", "fact_stream_sessions",
    "agg_daily_streams", "agg_user_activity", "agg_genre_trends",
    "agg_artist_growth", "agg_platform_usage", "agg_top_playlists",
    "agg_recommendation_scores", "agg_user_engagement", "agg_streaming_devices",
    "agg_recent_activity", "agg_top_searches", "agg_user_retention",
]


def _count(conn, table: str) -> int:
    try:
        return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    except Exception:
        return 0


def apply_enterprise_schema(conn) -> None:
    for ddl in ENTERPRISE_DDL:
        conn.execute(ddl)
    for alt in MIGRATION_ALTER:
        try:
            conn.execute(alt)
        except Exception:
            pass


def _build_dim_usuario_enterprise(conn) -> None:
    conn.execute("DELETE FROM dim_usuario WHERE id_usuario > 1")
    conn.execute("""
        INSERT INTO dim_usuario (id_usuario, nombre, email, pais, plan)
        SELECT 1 + i, 'User_' || LPAD(CAST(i AS VARCHAR), 5, '0'),
               'user' || i || '@voxmetrik.io',
               (ARRAY['EC','US','MX','CO','AR','ES','CL','PE'])[1 + (i % 8)],
               (ARRAY['free','premium','family','student'])[1 + (i % 4)]
        FROM generate_series(1, 4999) AS t(i)
    """)


def _build_dim_playlist_enterprise(conn) -> None:
    conn.execute("DELETE FROM dim_playlist WHERE id_playlist > 1")
    conn.execute("""
        INSERT INTO dim_playlist (id_playlist, nombre, id_usuario, descripcion, publica)
        SELECT 1 + i,
               (ARRAY['Daily Mix','Discover Weekly','Release Radar','Chill Vibes',
                      'Workout Hits','Focus Flow','Top 50','Road Trip'])[1 + (i % 8)] || ' ' || i,
               1 + (i % 4999), 'Enterprise playlist', (i % 3) <> 0
        FROM generate_series(1, 799) AS t(i)
    """)


def _build_fact_streaming_enterprise(conn) -> None:
    conn.execute("DELETE FROM fact_streaming")
    tc = _count(conn, "dim_track")
    uc = max(_count(conn, "dim_usuario"), 1)
    pc = max(_count(conn, "dim_playlist"), 1)
    if tc == 0:
        return
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
        ),
        tiempo AS (
            SELECT id_tiempo, fecha, ROW_NUMBER() OVER (ORDER BY fecha DESC) rn
            FROM dim_tiempo WHERE fecha <= CURRENT_DATE
        )
        SELECT g.i, t.id_track, 1 + (g.i % {uc}), ti.id_tiempo, 1 + (g.i % {pc}),
               1 + (t.popularity / 20), COALESCE(t.duration_ms, 180000),
               (g.i % 100) >= 18, (g.i % 100) < 22,
               (ARRAY['mobile','desktop','tablet','smart_tv','web'])[1 + (g.i % 5)],
               (ARRAY['ios','android','web','desktop','car'])[1 + (g.i % 5)],
               1 + (g.i % 5000), g.i % 24,
               CAST(ti.fecha AS TIMESTAMP) + (g.i % 86400) * INTERVAL '1' SECOND
        FROM generate_series(1, {N_STREAMING}) g(i)
        JOIN tracks t ON t.rn = ((g.i - 1) % t.total) + 1
        JOIN tiempo ti ON ti.rn = 1 + (g.i % 90)
    """)
    conn.execute("""
        UPDATE fact_streaming SET
            skipped = (id_streaming % 100) < 22,
            completado = (id_streaming % 100) >= 18
    """)


def _build_fact_user_activity(conn) -> None:
    conn.execute("DELETE FROM fact_user_activity")
    tc = max(_count(conn, "dim_track"), 1)
    conn.execute(f"""
        INSERT INTO fact_user_activity (
            id_activity, id_usuario, id_track, id_tiempo, action_type,
            device_type, duration_ms, fecha_evento
        )
        WITH tiempo AS (
            SELECT id_tiempo, ROW_NUMBER() OVER (ORDER BY fecha DESC) AS rn
            FROM dim_tiempo WHERE fecha <= CURRENT_DATE
        )
        SELECT i, 1 + (i % 5000), 1 + (i % {tc}), ti.id_tiempo,
               (ARRAY['play','pause','skip','like','share','add_playlist'])[1 + (i % 6)],
               (ARRAY['mobile','desktop','web'])[1 + (i % 3)],
               30000 + (i % 240000),
               CURRENT_TIMESTAMP - (i % 604800) * INTERVAL '1' SECOND
        FROM generate_series(1, {N_USER_ACTIVITY}) t(i)
        JOIN tiempo ti ON ti.rn = 1 + (i % 90)
    """)


def _build_fact_playlist_activity(conn) -> None:
    conn.execute("DELETE FROM fact_playlist_activity")
    tc = max(_count(conn, "dim_track"), 1)
    conn.execute(f"""
        INSERT INTO fact_playlist_activity (
            id_activity, id_playlist, id_usuario, id_track, action_type, fecha_evento
        )
        SELECT i, 1 + (i % 800), 1 + (i % 5000), 1 + (i % {tc}),
               (ARRAY['add','remove','play','follow','share'])[1 + (i % 5)],
               CURRENT_TIMESTAMP - (i % 2592000) * INTERVAL '1' SECOND
        FROM generate_series(1, {N_PLAYLIST_ACTIVITY}) t(i)
    """)


def _build_fact_favorites(conn) -> None:
    conn.execute("DELETE FROM fact_favorites")
    tc = max(_count(conn, "dim_track"), 1)
    conn.execute(f"""
        INSERT INTO fact_favorites (id_favorite, id_usuario, id_track, id_tiempo, fecha_evento)
        WITH tiempo AS (
            SELECT id_tiempo, ROW_NUMBER() OVER (ORDER BY fecha DESC) AS rn
            FROM dim_tiempo WHERE fecha <= CURRENT_DATE
        )
        SELECT i, 1 + (i % 5000), 1 + (i % {tc}), ti.id_tiempo,
               CURRENT_TIMESTAMP - (i % 7776000) * INTERVAL '1' SECOND
        FROM generate_series(1, {N_FAVORITES}) t(i)
        JOIN tiempo ti ON ti.rn = 1 + (i % 60)
    """)


def _build_fact_searches(conn) -> None:
    conn.execute("DELETE FROM fact_searches")
    conn.execute(f"""
        INSERT INTO fact_searches (id_search, id_usuario, query_text, results_count, id_tiempo, fecha_evento)
        WITH tiempo AS (
            SELECT id_tiempo, ROW_NUMBER() OVER (ORDER BY fecha DESC) AS rn
            FROM dim_tiempo WHERE fecha <= CURRENT_DATE
        )
        SELECT i, 1 + (i % 5000),
               (ARRAY['bad bunny','taylor swift','drake','reggaeton','rock','pop','chill',
                      'workout','latin hits','indie','focus','party','electronic','jazz',
                      'kpop','metal','hip hop','oldies','discover weekly','sad songs'])[1 + (i % 20)],
               5 + (i % 95), ti.id_tiempo,
               CURRENT_TIMESTAMP - (i % 1209600) * INTERVAL '1' SECOND
        FROM generate_series(1, {N_SEARCHES}) t(i)
        JOIN tiempo ti ON ti.rn = 1 + (i % 30)
    """)


def _build_fact_stream_sessions(conn) -> None:
    conn.execute("DELETE FROM fact_stream_sessions")
    conn.execute(f"""
        INSERT INTO fact_stream_sessions (
            id_session, id_usuario, device_type, platform,
            session_start, session_end, tracks_played, total_ms, skips
        )
        SELECT i, 1 + (i % 5000),
               (ARRAY['mobile','desktop','tablet','web','smart_tv'])[1 + (i % 5)],
               (ARRAY['ios','android','web','desktop','car'])[1 + (i % 5)],
               CURRENT_TIMESTAMP - (i % 604800) * INTERVAL '1' SECOND,
               CURRENT_TIMESTAMP - (i % 604800) * INTERVAL '1' SECOND + (1800 + i % 5400) * INTERVAL '1' SECOND,
               3 + (i % 25), 180000 + (i % 3600000), i % 8
        FROM generate_series(1, {N_SESSIONS}) t(i)
    """)


def _build_agg_daily_streams(conn) -> None:
    conn.execute("DELETE FROM agg_daily_streams")
    conn.execute("""
        INSERT INTO agg_daily_streams (
            fecha, total_streams, unique_users, unique_tracks, avg_duration_ms, skip_count
        )
        SELECT CAST(fecha_evento AS DATE), COUNT(*), COUNT(DISTINCT id_usuario),
               COUNT(DISTINCT id_track), ROUND(AVG(COALESCE(duracion_ms, 0)), 0),
               SUM(CASE WHEN skipped THEN 1 ELSE 0 END)
        FROM fact_streaming GROUP BY 1 ORDER BY 1 DESC LIMIT 90
    """)


def _build_agg_user_activity(conn) -> None:
    conn.execute("DELETE FROM agg_user_activity")
    conn.execute("""
        INSERT INTO agg_user_activity (id_usuario, total_plays, total_skips, total_likes, engagement_score)
        SELECT u.id_usuario, COALESCE(p.plays, 0), COALESCE(s.skips, 0), COALESCE(l.likes, 0),
               ROUND(LEAST(100, COALESCE(p.plays,0)*0.05 + COALESCE(l.likes,0)*2 - COALESCE(s.skips,0)*0.3), 2)
        FROM dim_usuario u
        LEFT JOIN (SELECT id_usuario, COUNT(*) plays FROM fact_streaming GROUP BY 1) p ON p.id_usuario = u.id_usuario
        LEFT JOIN (SELECT id_usuario, COUNT(*) skips FROM fact_streaming WHERE skipped GROUP BY 1) s ON s.id_usuario = u.id_usuario
        LEFT JOIN (SELECT id_usuario, COUNT(*) likes FROM fact_favorites GROUP BY 1) l ON l.id_usuario = u.id_usuario
        WHERE COALESCE(p.plays, 0) > 0
    """)


def _build_agg_genre_trends(conn) -> None:
    conn.execute("DELETE FROM agg_genre_trends")
    conn.execute("""
        INSERT INTO agg_genre_trends (
            id_genero, nombre_genero, streams_7d, streams_prev_7d, trend_pct, avg_popularity
        )
        SELECT dg.id_genero, dg.nombre_genero, COALESCE(s7.cnt,0), COALESCE(sp.cnt,0),
               CASE WHEN COALESCE(sp.cnt,0)=0 THEN 0 ELSE ROUND((COALESCE(s7.cnt,0)-sp.cnt)*100.0/sp.cnt,1) END,
               ROUND(AVG(COALESCE(dt.popularity,0)),1)
        FROM dim_genero dg
        LEFT JOIN dim_track dt ON dt.id_genero = dg.id_genero
        LEFT JOIN (
            SELECT dt.id_genero, COUNT(*) cnt FROM fact_streaming fs
            JOIN dim_track dt ON dt.id_track = fs.id_track
            WHERE fs.fecha_evento >= CURRENT_DATE - INTERVAL '7' DAY GROUP BY 1
        ) s7 ON s7.id_genero = dg.id_genero
        LEFT JOIN (
            SELECT dt.id_genero, COUNT(*) cnt FROM fact_streaming fs
            JOIN dim_track dt ON dt.id_track = fs.id_track
            WHERE fs.fecha_evento >= CURRENT_DATE - INTERVAL '14' DAY
              AND fs.fecha_evento < CURRENT_DATE - INTERVAL '7' DAY GROUP BY 1
        ) sp ON sp.id_genero = dg.id_genero
        GROUP BY dg.id_genero, dg.nombre_genero, s7.cnt, sp.cnt
    """)


def _build_agg_artist_growth(conn) -> None:
    conn.execute("DELETE FROM agg_artist_growth")
    conn.execute("""
        INSERT INTO agg_artist_growth (
            id_artista, nombre_artista, streams_7d, streams_30d, growth_pct, total_followers
        )
        SELECT da.id_artista, da.nombre_artista, COALESCE(w7.cnt,0), COALESCE(w30.cnt,0),
               CASE WHEN COALESCE(w7.cnt,0)=0 THEN 0 ELSE ROUND((COALESCE(w30.cnt,0)-w7.cnt)*100.0/w7.cnt,1) END,
               COALESCE(w30.cnt,0)*3 + (da.id_artista % 1000)
        FROM dim_artista da
        LEFT JOIN (
            SELECT dt.id_artista, COUNT(*) cnt FROM fact_streaming fs
            JOIN dim_track dt ON dt.id_track = fs.id_track
            WHERE fs.fecha_evento >= CURRENT_DATE - INTERVAL '7' DAY GROUP BY 1
        ) w7 ON w7.id_artista = da.id_artista
        LEFT JOIN (
            SELECT dt.id_artista, COUNT(*) cnt FROM fact_streaming fs
            JOIN dim_track dt ON dt.id_track = fs.id_track
            WHERE fs.fecha_evento >= CURRENT_DATE - INTERVAL '30' DAY GROUP BY 1
        ) w30 ON w30.id_artista = da.id_artista
    """)


def _build_agg_platform_usage(conn) -> None:
    conn.execute("DELETE FROM agg_platform_usage")
    conn.execute("""
        INSERT INTO agg_platform_usage (
            platform, device_type, session_count, total_streams, avg_session_min, share_pct
        )
        WITH base AS (
            SELECT platform, device_type, COUNT(DISTINCT session_id) sessions, COUNT(*) streams
            FROM fact_streaming GROUP BY 1, 2
        ), tot AS (SELECT SUM(streams) t FROM base)
        SELECT b.platform, b.device_type, b.sessions, b.streams,
               ROUND(b.streams*3.5/NULLIF(b.sessions,0),1), ROUND(b.streams*100.0/NULLIF(t.t,0),1)
        FROM base b CROSS JOIN tot t
    """)


def _build_agg_top_playlists(conn) -> None:
    conn.execute("DELETE FROM agg_top_playlists")
    conn.execute("""
        INSERT INTO agg_top_playlists (
            id_playlist, nombre, total_plays, total_tracks, unique_listeners, avg_completion
        )
        SELECT dp.id_playlist, dp.nombre, COALESCE(fs.cnt,0), COALESCE(pa.tracks,1),
               COALESCE(fs.users,0), ROUND(100.0 - COALESCE(fs.skips,0)*100.0/NULLIF(fs.cnt,0),1)
        FROM dim_playlist dp
        LEFT JOIN (
            SELECT id_playlist, COUNT(*) cnt, COUNT(DISTINCT id_usuario) users,
                   SUM(CASE WHEN skipped THEN 1 ELSE 0 END) skips
            FROM fact_streaming GROUP BY 1
        ) fs ON fs.id_playlist = dp.id_playlist
        LEFT JOIN (
            SELECT id_playlist, COUNT(DISTINCT id_track) tracks FROM fact_playlist_activity GROUP BY 1
        ) pa ON pa.id_playlist = dp.id_playlist
        ORDER BY COALESCE(fs.cnt,0) DESC LIMIT 100
    """)


def _build_agg_recommendation_scores(conn) -> None:
    conn.execute("DELETE FROM agg_recommendation_scores")
    conn.execute("""
        INSERT INTO agg_recommendation_scores (
            id_track, nombre_track, recommendation_score, engagement_score, popularity
        )
        SELECT dt.id_track, dt.nombre_track,
               ROUND(COALESCE(dt.popularity,0)*0.4 + COALESCE(dt.danceability,0)*30
                     + COALESCE(dt.energy,0)*20 + COALESCE(fs.plays,0)*0.001, 2),
               ROUND(COALESCE(fs.plays,0)*0.01 + COALESCE(fav.likes,0)*0.5, 2),
               COALESCE(dt.popularity,0)
        FROM dim_track dt
        LEFT JOIN (SELECT id_track, COUNT(*) plays FROM fact_streaming GROUP BY 1) fs ON fs.id_track = dt.id_track
        LEFT JOIN (SELECT id_track, COUNT(*) likes FROM fact_favorites GROUP BY 1) fav ON fav.id_track = dt.id_track
        ORDER BY 3 DESC LIMIT 500
    """)


def _build_agg_user_engagement(conn) -> None:
    conn.execute("DELETE FROM agg_user_engagement")
    conn.execute("""
        INSERT INTO agg_user_engagement (segment, user_count, avg_plays, avg_session_min, retention_pct)
        SELECT 'power_users', COUNT(*), ROUND(AVG(total_plays),1), ROUND(AVG(total_plays)*3.2,1), 78.5
        FROM agg_user_activity WHERE engagement_score >= 50
        UNION ALL SELECT 'regular', COUNT(*), ROUND(AVG(total_plays),1), ROUND(AVG(total_plays)*2.1,1), 52.3
        FROM agg_user_activity WHERE engagement_score BETWEEN 20 AND 49.99
        UNION ALL SELECT 'casual', COUNT(*), ROUND(AVG(total_plays),1), ROUND(AVG(total_plays)*1.4,1), 28.7
        FROM agg_user_activity WHERE engagement_score < 20
    """)


def _build_agg_streaming_devices(conn) -> None:
    conn.execute("DELETE FROM agg_streaming_devices")
    conn.execute("""
        INSERT INTO agg_streaming_devices (device_type, stream_count, unique_users, share_pct)
        WITH base AS (
            SELECT device_type, COUNT(*) cnt, COUNT(DISTINCT id_usuario) users FROM fact_streaming GROUP BY 1
        ), tot AS (SELECT SUM(cnt) t FROM base)
        SELECT b.device_type, b.cnt, b.users, ROUND(b.cnt*100.0/t.t,1) FROM base b CROSS JOIN tot t
    """)


def _build_agg_recent_activity(conn) -> None:
    conn.execute("DELETE FROM agg_recent_activity")
    conn.execute("""
        INSERT INTO agg_recent_activity (id_activity, activity_type, label, metric_value, fecha)
        SELECT ROW_NUMBER() OVER (ORDER BY cnt DESC), 'top_track', dt.nombre_track, cnt, CURRENT_DATE
        FROM (
            SELECT id_track, COUNT(*) cnt FROM fact_streaming
            WHERE fecha_evento >= CURRENT_DATE - INTERVAL '1' DAY
            GROUP BY 1 ORDER BY 2 DESC LIMIT 10
        ) x JOIN dim_track dt ON dt.id_track = x.id_track
    """)


def _build_agg_top_searches(conn) -> None:
    conn.execute("DELETE FROM agg_top_searches")
    conn.execute("""
        INSERT INTO agg_top_searches (query_text, search_count, avg_results)
        SELECT query_text, COUNT(*), ROUND(AVG(results_count),1)
        FROM fact_searches GROUP BY 1 ORDER BY 2 DESC LIMIT 50
    """)


def _build_agg_user_retention(conn) -> None:
    conn.execute("DELETE FROM agg_user_retention")
    conn.execute("""
        INSERT INTO agg_user_retention (cohort_week, users_cohort, week_1_pct, week_2_pct, week_4_pct)
        SELECT 'W' || LPAD(CAST(w AS VARCHAR), 2, '0'), 800 + (w * 47) % 1200,
               ROUND(65 + (w % 10), 1), ROUND(48 + (w % 8), 1), ROUND(32 + (w % 6), 1)
        FROM generate_series(1, 12) t(w)
    """)


def build_enterprise_warehouse(conn) -> Dict[str, Any]:
    logger.info("══ ENTERPRISE GOLD ═════════════════════════════════════════")
    apply_enterprise_schema(conn)
    _build_dim_usuario_enterprise(conn)
    _build_dim_playlist_enterprise(conn)
    _build_fact_streaming_enterprise(conn)
    _build_fact_user_activity(conn)
    _build_fact_playlist_activity(conn)
    _build_fact_favorites(conn)
    _build_fact_searches(conn)
    _build_fact_stream_sessions(conn)
    _build_agg_daily_streams(conn)
    _build_agg_user_activity(conn)
    _build_agg_genre_trends(conn)
    _build_agg_artist_growth(conn)
    _build_agg_platform_usage(conn)
    _build_agg_top_playlists(conn)
    _build_agg_recommendation_scores(conn)
    _build_agg_user_engagement(conn)
    _build_agg_streaming_devices(conn)
    _build_agg_recent_activity(conn)
    _build_agg_top_searches(conn)
    _build_agg_user_retention(conn)
    fact_total = sum(_count(conn, t) for t in [
        "fact_streaming", "fact_user_activity", "fact_playlist_activity",
        "fact_favorites", "fact_searches", "fact_stream_sessions",
    ])
    logger.info(f"[ENTERPRISE] facts={fact_total:,}")
    return {"fact_rows": fact_total}


def register_pipeline_stage(
    conn, run_id: int, stage: str, layer: str,
    duration_ms: int, rows_in: int, rows_out: int,
    status: str = "OK", details: str = "",
) -> None:
    apply_enterprise_schema(conn)
    next_id = conn.execute("SELECT COALESCE(MAX(id_stage), 0) + 1 FROM ctl_pipeline_stages").fetchone()[0]
    conn.execute(
        """INSERT INTO ctl_pipeline_stages
           (id_stage, run_id, stage, layer, duration_ms, rows_in, rows_out, status, details)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [next_id, run_id, stage, layer, duration_ms, rows_in, rows_out, status, details],
    )
