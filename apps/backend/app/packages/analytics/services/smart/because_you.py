"""Contextual 'Because you...' recommendation sections."""

from __future__ import annotations

from typing import Any, Dict, List

import duckdb

from app.packages.analytics.services.history_service import _warehouse_user_id
from ._helpers import table_exists_conn

from .similarity_engine import similar_tracks


def build_because_sections(
    conn: duckdb.DuckDBPyConnection, app_user_id: int, *, limit: int = 8
) -> List[Dict[str, Any]]:
    wh_user = _warehouse_user_id(app_user_id)
    sections: List[Dict[str, Any]] = []

    if table_exists_conn(conn, "fact_streaming"):
        recent = conn.execute(
            """
            SELECT dt.id_track, dt.nombre_track, da.nombre_artista
            FROM fact_streaming fs
            INNER JOIN dim_track dt ON dt.id_track = fs.id_track
            LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
            WHERE fs.id_usuario = ?
            ORDER BY fs.fecha_evento DESC NULLS LAST
            LIMIT 1
            """,
            [wh_user],
        ).fetchone()
        if recent:
            tid, title, artist = int(recent[0]), recent[1], recent[2]
            sim = similar_tracks(conn, tid, limit=limit)
            if sim:
                sections.append(
                    {
                        "id": f"because-listened-{tid}",
                        "type": "because",
                        "code": "because_listened",
                        "reason_type": "listened",
                        "title_params": {"name": title or ""},
                        "subtitle": artist,
                        "anchor_track_id": tid,
                        "tracks": sim,
                    }
                )

    try:
        fav = conn.execute(
            """
            SELECT dt.id_track, dt.nombre_track, da.nombre_artista
            FROM app_favorite f
            INNER JOIN dim_track dt ON dt.id_track = f.track_id
            LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
            WHERE f.user_id = ?
            ORDER BY f.added_at DESC
            LIMIT 1
            """,
            [app_user_id],
        ).fetchone()
        if fav:
            tid, title, artist = int(fav[0]), fav[1], fav[2]
            sim = similar_tracks(conn, tid, limit=limit)
            if sim:
                sections.append(
                    {
                        "id": f"because-liked-{tid}",
                        "type": "because",
                        "code": "because_liked",
                        "reason_type": "liked",
                        "title_params": {"name": title or ""},
                        "subtitle": artist,
                        "anchor_track_id": tid,
                        "tracks": sim,
                    }
                )
    except Exception:
        pass

    if table_exists_conn(conn, "dim_track") and table_exists_conn(conn, "fact_streaming"):
        top_artist = conn.execute(
            """
            SELECT da.id_artista, da.nombre_artista, COUNT(*) AS c
            FROM fact_streaming fs
            INNER JOIN dim_track dt ON dt.id_track = fs.id_track
            INNER JOIN dim_artista da ON da.id_artista = dt.id_artista
            WHERE fs.id_usuario = ?
            GROUP BY da.id_artista, da.nombre_artista
            ORDER BY c DESC
            LIMIT 1
            """,
            [wh_user],
        ).fetchone()
        if top_artist:
            aid, name, _ = int(top_artist[0]), top_artist[1], top_artist[2]
            rows = conn.execute(
                """
                SELECT dt.id_track, dt.nombre_track, da.nombre_artista, dt.popularity
                FROM dim_track dt
                LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
                WHERE dt.id_artista = ?
                ORDER BY dt.popularity DESC NULLS LAST
                LIMIT ?
                """,
                [aid, limit],
            ).fetchall()
            if rows:
                sections.append(
                    {
                        "id": f"because-artist-{aid}",
                        "type": "because",
                        "code": "because_frequent_artist",
                        "reason_type": "frequent_artist",
                        "title_params": {"name": name or ""},
                        "tracks": [
                            {
                                "id_track": int(r[0]),
                                "nombre_track": r[1],
                                "nombre_artista": r[2],
                                "popularity": r[3],
                            }
                            for r in rows
                        ],
                    }
                )

    return sections
