"""Ensure app-level DuckDB tables for playlists and favorites."""

from __future__ import annotations

import duckdb

from app.packages.users.services.user_storage import migrate_user_scoping


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
