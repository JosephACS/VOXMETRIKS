"""Historial unificado — auditoría ELT, usuario y búsquedas."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import duckdb

def _warehouse_user_id(app_user_id: int) -> int:
    """Mapea app_user.id → id_usuario del warehouse (datos sintéticos)."""
    return 1 + ((app_user_id - 1) % 5000)


def get_search_history(
    conn: duckdb.DuckDBPyConnection,
    user_id: int,
    limit: int = 25,
) -> List[Dict[str, Any]]:
    """Búsquedas del usuario en fact_searches (warehouse)."""
    wh_user = _warehouse_user_id(user_id)
    try:
        rows = conn.execute(
            """
            SELECT id_search, query_text, results_count, fecha_evento
            FROM fact_searches
            WHERE id_usuario = ?
            ORDER BY fecha_evento DESC
            LIMIT ?
            """,
            [wh_user, limit],
        ).fetchall()
    except Exception:
        return []

    return [
        {
            "id_search": r[0],
            "query": r[1],
            "results_count": int(r[2] or 0),
            "fecha_evento": str(r[3]) if r[3] else None,
        }
        for r in rows
    ]


def get_user_history(
    conn: duckdb.DuckDBPyConnection,
    user_id: int,
    limit: int = 25,
) -> Dict[str, Any]:
    """Actividad del usuario: sesiones, favoritos y eventos del warehouse."""
    wh_user = _warehouse_user_id(user_id)

    sessions: List[Dict[str, Any]] = []
    try:
        rows = conn.execute(
            """
            SELECT created_at, expires_at
            FROM app_session
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            [user_id, min(limit, 15)],
        ).fetchall()
        for r in rows:
            sessions.append({
                "event_type": "login",
                "label": "Inicio de sesión",
                "fecha_evento": str(r[0]) if r[0] else None,
                "detalle": "Sesión activa en VOXMETRIK",
            })
    except Exception:
        pass

    favorites: List[Dict[str, Any]] = []
    try:
        rows = conn.execute(
            """
            SELECT f.added_at, dt.id_track, dt.nombre_track, da.nombre_artista
            FROM app_favorite f
            JOIN dim_track dt ON dt.id_track = f.track_id
            LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
            WHERE f.user_id = ?
            ORDER BY f.added_at DESC
            LIMIT ?
            """,
            [user_id, limit],
        ).fetchall()
        for r in rows:
            artist_raw = r[3] or ""
            primary = artist_raw.split(";")[0].strip() if artist_raw else None
            favorites.append({
                "event_type": "favorite",
                "label": "Añadido a favoritos",
                "fecha_evento": str(r[0]) if r[0] else None,
                "id_track": r[1],
                "nombre_track": r[2],
                "nombre_artista": primary,
            })
    except Exception:
        pass

    activity: List[Dict[str, Any]] = []
    try:
        rows = conn.execute(
            """
            SELECT
                fua.fecha_evento,
                fua.action_type,
                fua.device_type,
                dt.nombre_track,
                da.nombre_artista
            FROM fact_user_activity fua
            LEFT JOIN dim_track dt ON dt.id_track = fua.id_track
            LEFT JOIN dim_artista da ON da.id_artista = dt.id_artista
            WHERE fua.id_usuario = ?
            ORDER BY fua.fecha_evento DESC
            LIMIT ?
            """,
            [wh_user, limit],
        ).fetchall()
        action_labels = {
            "play": "Reproducción",
            "pause": "Pausa",
            "skip": "Saltar",
            "like": "Me gusta",
            "share": "Compartir",
            "add_playlist": "Añadir a playlist",
        }
        for r in rows:
            artist_raw = r[4] or ""
            primary = artist_raw.split(";")[0].strip() if artist_raw else None
            action = r[1] or "event"
            activity.append({
                "event_type": action,
                "label": action_labels.get(action, action),
                "fecha_evento": str(r[0]) if r[0] else None,
                "device_type": r[2],
                "nombre_track": r[3],
                "nombre_artista": primary,
            })
    except Exception:
        pass

    merged = sessions + favorites + activity
    merged.sort(key=lambda x: x.get("fecha_evento") or "", reverse=True)

    return {
        "user_id": user_id,
        "warehouse_user_id": wh_user,
        "sessions": sessions,
        "favorites": favorites,
        "activity": activity,
        "timeline": merged[:limit],
    }


def get_history_hub(
    conn: duckdb.DuckDBPyConnection,
    user_id: Optional[int] = None,
    limit: int = 25,
) -> Dict[str, Any]:
    hub: Dict[str, Any] = {
        "search": [],
        "user": None,
    }
    if user_id:
        hub["user"] = get_user_history(conn, user_id, limit=limit)
        hub["search"] = get_search_history(conn, user_id, limit=limit)
    return hub
