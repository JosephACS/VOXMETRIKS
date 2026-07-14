"""Favorites API routes."""

from __future__ import annotations

import duckdb
from fastapi import APIRouter, Depends, HTTPException

from app.core.database import get_conn, get_write_conn
from app.platform.notifications.service import get_notification_service
from app.packages.engagement.services.favorite_service import (
    add_favorite,
    list_favorites,
    remove_favorite,
)
from app.packages.identity.services.auth_deps import require_user_id
from app.shared.schemas.models import FavoriteTrack

router = APIRouter(prefix="/favorites", tags=["Favorites"])


@router.get("", response_model=list[FavoriteTrack], summary="List favorite tracks")
def list_all(
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    return list_favorites(conn, user_id)


@router.post("/{track_id}", status_code=201, summary="Add track to favorites")
def add(
    track_id: int,
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        ok = add_favorite(conn, user_id, track_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=402,
            detail={
                "code": "entitlement_limit",
                "message": str(exc),
                "cta": "/account/plans",
            },
        ) from exc
    if not ok:
        raise HTTPException(status_code=404, detail=f"Track {track_id} not found")
    row = conn.execute(
        "SELECT nombre_track FROM dim_track WHERE id_track = ?", [track_id]
    ).fetchone()
    title = row[0] if row else f"Track {track_id}"
    get_notification_service().favorite_added(user_id, str(title))
    return {"favorited": True, "track_id": track_id}


@router.delete("/{track_id}", summary="Remove track from favorites")
def remove(
    track_id: int,
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    remove_favorite(conn, user_id, track_id)
    return {"removed": True, "track_id": track_id}
