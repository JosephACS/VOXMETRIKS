"""User musical profile and Audio DNA."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

import duckdb

from app.packages.analytics.services.history_service import _warehouse_user_id
from ._helpers import table_exists_conn

from .feature_extractor import (
    audio_dna_profile,
    centroid,
    fetch_track_features,
    load_user_signal_tracks,
)


def build_musical_profile(
    conn: duckdb.DuckDBPyConnection, app_user_id: int
) -> Dict[str, Any]:
    wh_user = _warehouse_user_id(app_user_id)
    signal_ids = load_user_signal_tracks(conn, app_user_id, wh_user)
    features = fetch_track_features(conn, signal_ids[:60])
    taste_vec = centroid([f.vector for f in features.values()]) if features else []

    top_genres: List[Dict[str, Any]] = []
    top_artists: List[Dict[str, Any]] = []
    top_tracks: List[Dict[str, Any]] = []
    hours_listened = 0
    minutes_listened = 0
    favorite_decade: str | None = None

    events = "silver_streams" if table_exists_conn(conn, "silver_streams") else "fact_streaming"
    if table_exists_conn(conn, events) and table_exists_conn(conn, "dim_track"):
        top_tracks = _top_tracks(conn, events, wh_user)
        top_genres = _top_genres(conn, events, wh_user)
        top_artists = _top_artists(conn, events, wh_user)
        hours_listened, minutes_listened = _listen_time(conn, events, wh_user)

    if signal_ids and table_exists_conn(conn, "dim_track"):
        fav_rows = conn.execute(
            """
            SELECT dt.id_track, dt.nombre_track, da.nombre_artista
            FROM app_favorite f
            INNER JOIN dim_track dt ON dt.id_track = f.track_id
            LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
            WHERE f.user_id = ?
            ORDER BY f.added_at DESC
            LIMIT 5
            """,
            [app_user_id],
        ).fetchall()
        if fav_rows and not top_tracks:
            top_tracks = [
                {"id_track": int(r[0]), "nombre_track": r[1], "nombre_artista": r[2]}
                for r in fav_rows
            ]

    favorite_track = top_tracks[0] if top_tracks else None
    audio_dna = audio_dna_profile(taste_vec)

    return {
        "user_id": app_user_id,
        "warehouse_user_id": wh_user,
        "top_genres": top_genres,
        "top_artists": top_artists,
        "top_tracks": top_tracks,
        "hours_listened": hours_listened,
        "minutes_listened": minutes_listened,
        "favorite_track": favorite_track,
        "favorite_decade": favorite_decade,
        "audio_dna": audio_dna,
        "signal_track_count": len(signal_ids),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _top_tracks(conn: duckdb.DuckDBPyConnection, events: str, wh_user: int) -> List[Dict[str, Any]]:
    rows = conn.execute(
        f"""
        SELECT dt.id_track, dt.nombre_track, da.nombre_artista, COUNT(*) AS plays
        FROM {events} fs
        INNER JOIN dim_track dt ON dt.id_track = fs.id_track
        LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
        WHERE fs.id_usuario = ?
        GROUP BY dt.id_track, dt.nombre_track, da.nombre_artista
        ORDER BY plays DESC
        LIMIT 10
        """,
        [wh_user],
    ).fetchall()
    return [
        {"id_track": int(r[0]), "nombre_track": r[1], "nombre_artista": r[2], "plays": int(r[3])}
        for r in rows
    ]


def _top_genres(conn: duckdb.DuckDBPyConnection, events: str, wh_user: int) -> List[Dict[str, Any]]:
    rows = conn.execute(
        f"""
        SELECT dg.id_genero, dg.nombre_genero, COUNT(*) AS plays
        FROM {events} fs
        INNER JOIN dim_track dt ON dt.id_track = fs.id_track
        LEFT JOIN dim_genero dg ON dg.id_genero = dt.id_genero
        WHERE fs.id_usuario = ? AND dg.id_genero IS NOT NULL
        GROUP BY dg.id_genero, dg.nombre_genero
        ORDER BY plays DESC
        LIMIT 5
        """,
        [wh_user],
    ).fetchall()
    return [
        {"id_genero": int(r[0]), "nombre_genero": r[1], "plays": int(r[2])} for r in rows
    ]


def _top_artists(conn: duckdb.DuckDBPyConnection, events: str, wh_user: int) -> List[Dict[str, Any]]:
    rows = conn.execute(
        f"""
        SELECT da.id_artista, da.nombre_artista, COUNT(*) AS plays
        FROM {events} fs
        INNER JOIN dim_track dt ON dt.id_track = fs.id_track
        LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
        WHERE fs.id_usuario = ? AND da.id_artista IS NOT NULL
        GROUP BY da.id_artista, da.nombre_artista
        ORDER BY plays DESC
        LIMIT 8
        """,
        [wh_user],
    ).fetchall()
    return [
        {"id_artista": int(r[0]), "nombre_artista": r[1], "plays": int(r[2])} for r in rows
    ]


def _listen_time(conn: duckdb.DuckDBPyConnection, events: str, wh_user: int) -> tuple[int, int]:
    row = conn.execute(
        f"""
        SELECT COUNT(*) AS events
        FROM {events}
        WHERE id_usuario = ?
        """,
        [wh_user],
    ).fetchone()
    events_count = int(row[0] or 0) if row else 0
    minutes = events_count * 3
    return minutes // 60, minutes
