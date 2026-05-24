"""User auth, profile and preferences."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, Optional

import duckdb

from app.packages.streaming.services.app_storage import ensure_app_tables
from app.packages.streaming.services.favorite_service import favorite_ids
from app.packages.streaming.services.playlist_service import list_playlists

from .user_storage import (
    create_session,
    ensure_user_tables,
    migrate_user_scoping,
    parse_preferences,
    resolve_session,
)


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _next_user_id(conn: duckdb.DuckDBPyConnection) -> int:
    row = conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM app_user").fetchone()
    return int(row[0])


def _user_row_to_dict(row: tuple) -> Dict[str, Any]:
    prefs = parse_preferences(row[7] if len(row) > 7 else "{}")
    return {
        "id": row[0],
        "username": row[1],
        "email": row[2],
        "plan": row[4],
        "favorite_genre": row[5],
        "created_at": str(row[6]) if row[6] else None,
        "preferences": prefs,
    }


def _fetch_user(conn: duckdb.DuckDBPyConnection, user_id: int) -> Optional[Dict[str, Any]]:
    ensure_user_tables(conn)
    row = conn.execute(
        """
        SELECT id, username, email, password_hash, plan, favorite_genre, created_at, preferences_json
        FROM app_user WHERE id = ?
        """,
        [user_id],
    ).fetchone()
    if not row:
        return None
    return _user_row_to_dict(row)


def login(
    conn: duckdb.DuckDBPyConnection,
    login_id: str,
    password: str,
    remember: bool = True,
) -> Optional[Dict[str, Any]]:
    ensure_user_tables(conn)
    migrate_user_scoping(conn)
    login_id = login_id.strip().lower()
    row = conn.execute(
        """
        SELECT id, username, email, password_hash, plan, favorite_genre, created_at, preferences_json
        FROM app_user
        WHERE LOWER(email) = ? OR LOWER(username) = ?
        """,
        [login_id, login_id],
    ).fetchone()
    if not row or row[3] != _hash_password(password):
        return None
    days = 90 if remember else 1
    token = create_session(conn, int(row[0]), days=days)
    user = _user_row_to_dict(row)
    return {"token": token, "user": user}


def register(
    conn: duckdb.DuckDBPyConnection,
    username: str,
    email: str,
    password: str,
    favorite_genre: Optional[str] = None,
) -> Dict[str, Any]:
    ensure_user_tables(conn)
    migrate_user_scoping(conn)
    username = username.strip()
    email = email.strip().lower()
    if len(username) < 3:
        raise ValueError("username must be at least 3 characters")
    if len(password) < 4:
        raise ValueError("password must be at least 4 characters")

    dup = conn.execute(
        "SELECT 1 FROM app_user WHERE LOWER(email) = ? OR LOWER(username) = ?",
        [email, username.lower()],
    ).fetchone()
    if dup:
        raise ValueError("email or username already exists")

    new_id = _next_user_id(conn)
    prefs = json.dumps({
        "dark_mode": True,
        "audio_quality": "high",
        "recommendations_enabled": True,
        "privacy_public": False,
    })
    conn.execute(
        """
        INSERT INTO app_user
            (id, username, email, password_hash, plan, favorite_genre, created_at, preferences_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            new_id, username, email, _hash_password(password),
            "Free", favorite_genre, datetime.utcnow(), prefs,
        ],
    )
    token = create_session(conn, new_id, days=90)
    user = _fetch_user(conn, new_id)
    return {"token": token, "user": user}


def get_me(conn: duckdb.DuckDBPyConnection, user_id: int) -> Optional[Dict[str, Any]]:
    user = _fetch_user(conn, user_id)
    if not user:
        return None
    ensure_app_tables(conn)
    migrate_user_scoping(conn)
    fav_count = len(favorite_ids(conn, user_id))
    playlists = [p for p in list_playlists(conn, user_id)]
    profile = {
        **user,
        "stats": {
            "favorites_count": fav_count,
            "playlists_count": len(playlists),
        },
        "playlists": playlists[:6],
    }
    return profile


def update_preferences(
    conn: duckdb.DuckDBPyConnection,
    user_id: int,
    updates: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    user = _fetch_user(conn, user_id)
    if not user:
        return None
    pref_keys = {"dark_mode", "audio_quality", "recommendations_enabled", "privacy_public"}
    pref_updates = {k: updates[k] for k in pref_keys if k in updates}
    prefs = {**user.get("preferences", {}), **pref_updates}
    favorite_genre = updates.get("favorite_genre", user.get("favorite_genre"))
    conn.execute(
        """
        UPDATE app_user
        SET preferences_json = ?, favorite_genre = COALESCE(?, favorite_genre)
        WHERE id = ?
        """,
        [json.dumps(prefs), updates.get("favorite_genre"), user_id],
    )
    return _fetch_user(conn, user_id)


def get_user_id_from_token(conn: duckdb.DuckDBPyConnection, token: str) -> Optional[int]:
    return resolve_session(conn, token)
