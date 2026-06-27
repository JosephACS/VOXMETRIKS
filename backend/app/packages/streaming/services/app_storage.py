"""Ensure app-level DuckDB tables for playlists and favorites."""

from __future__ import annotations

import duckdb

from app.core.time_util import utc_now
from app.packages.users.services.user_storage import ensure_user_tables, migrate_user_scoping


def _demo_user_id(conn: duckdb.DuckDBPyConnection) -> int | None:
    row = conn.execute(
        "SELECT id FROM app_user WHERE LOWER(email) = 'demo@voxmetrik.io' LIMIT 1"
    ).fetchone()
    return int(row[0]) if row else None


def _seed_demo_library(conn: duckdb.DuckDBPyConnection) -> None:
    """Seed demo playlists/favorites if demo user has none."""
    ensure_user_tables(conn)
    uid = _demo_user_id(conn)
    if not uid:
        return

    fav_count = conn.execute(
        "SELECT COUNT(*) FROM app_favorite WHERE user_id = ?", [uid]
    ).fetchone()[0]
    if int(fav_count or 0) == 0:
        track_ids = conn.execute(
            "SELECT id_track FROM dim_track ORDER BY popularity DESC NULLS LAST LIMIT 5"
        ).fetchall()
        for (tid,) in track_ids:
            exists = conn.execute(
                "SELECT 1 FROM app_favorite WHERE user_id = ? AND track_id = ?",
                [uid, int(tid)],
            ).fetchone()
            if not exists:
                conn.execute(
                    "INSERT INTO app_favorite (user_id, track_id, added_at) VALUES (?, ?, ?)",
                    [uid, int(tid), utc_now()],
                )

    pl_count = conn.execute(
        "SELECT COUNT(*) FROM app_playlist WHERE user_id = ?", [uid]
    ).fetchone()[0]
    tracks_in_pl = conn.execute(
        """
        SELECT COUNT(*) FROM app_playlist_track pt
        JOIN app_playlist p ON p.id = pt.playlist_id
        WHERE p.user_id = ?
        """,
        [uid],
    ).fetchone()[0]
    if int(pl_count or 0) > 0 and int(tracks_in_pl or 0) > 0:
        return

    if int(pl_count or 0) > 0 and int(tracks_in_pl or 0) == 0:
        empty_pls = conn.execute(
            "SELECT id FROM app_playlist WHERE user_id = ? ORDER BY id LIMIT 2",
            [uid],
        ).fetchall()
        track_rows = conn.execute(
            "SELECT id_track FROM dim_track ORDER BY popularity DESC NULLS LAST LIMIT 8"
        ).fetchall()
        all_ids = [int(r[0]) for r in track_rows]
        for i, (pl_id_row,) in enumerate(empty_pls):
            subset = all_ids[i * 4:(i + 1) * 4] or all_ids[:4]
            for tid in subset:
                dup = conn.execute(
                    "SELECT 1 FROM app_playlist_track WHERE playlist_id = ? AND track_id = ?",
                    [int(pl_id_row), tid],
                ).fetchone()
                if not dup:
                    conn.execute(
                        "INSERT INTO app_playlist_track (playlist_id, track_id, added_at) VALUES (?, ?, ?)",
                        [int(pl_id_row), tid, utc_now()],
                    )
        return

    playlists = [
        ("Mis favoritas", "Top tracks del catálogo"),
        ("Para estudiar", "Baja energía y buen ritmo"),
    ]
    track_rows = conn.execute(
        "SELECT id_track FROM dim_track ORDER BY popularity DESC NULLS LAST LIMIT 12"
    ).fetchall()
    all_ids = [int(r[0]) for r in track_rows]
    if not all_ids:
        return

    next_id = conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM app_playlist").fetchone()[0]
    for i, (name, desc) in enumerate(playlists):
        pl_id = int(next_id) + i
        conn.execute(
            "INSERT INTO app_playlist (id, name, description, created_at, user_id) VALUES (?, ?, ?, ?, ?)",
            [pl_id, name, desc, utc_now(), uid],
        )
        subset = all_ids[i * 4:(i + 1) * 4] or all_ids[:4]
        for tid in subset:
            dup = conn.execute(
                "SELECT 1 FROM app_playlist_track WHERE playlist_id = ? AND track_id = ?",
                [pl_id, tid],
            ).fetchone()
            if not dup:
                conn.execute(
                    "INSERT INTO app_playlist_track (playlist_id, track_id, added_at) VALUES (?, ?, ?)",
                    [pl_id, tid, utc_now()],
                )


def ensure_app_tables(conn: duckdb.DuckDBPyConnection) -> None:
    migrate_user_scoping(conn)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_playlist (
            id          INTEGER PRIMARY KEY,
            name        VARCHAR NOT NULL,
            description VARCHAR,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id     INTEGER DEFAULT 1
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_playlist_track (
            playlist_id INTEGER NOT NULL,
            track_id    INTEGER NOT NULL,
            added_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (playlist_id, track_id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_favorite (
            user_id  INTEGER NOT NULL DEFAULT 1,
            track_id INTEGER NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, track_id)
        )
    """)
    # Resolved YouTube video ids for real playback. Lives in an app_ table so
    # it survives ELT pipeline rebuilds of dim_track.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_track_audio_source (
            track_id         INTEGER PRIMARY KEY,
            provider         VARCHAR NOT NULL DEFAULT 'youtube',
            youtube_video_id VARCHAR,
            query            VARCHAR,
            status           VARCHAR NOT NULL DEFAULT 'ok',
            resolved_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    _seed_demo_library(conn)
