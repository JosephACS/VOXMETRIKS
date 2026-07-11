"""Playlists API routes."""

from __future__ import annotations

import duckdb
from fastapi import APIRouter, Depends, HTTPException

from app.core.database import get_conn, get_write_conn
from app.packages.streaming.services.playlist_service import (
    add_track_to_playlist,
    create_playlist,
    delete_playlist,
    get_playlist,
    list_playlists,
    remove_track_from_playlist,
    update_playlist,
)
from app.packages.users.services.auth_deps import require_user_id
from app.shared.schemas.models import (
    DeleteResponse,
    PlaylistCreate,
    PlaylistDetail,
    PlaylistSummary,
    PlaylistTrackAdd,
    PlaylistUpdate,
)

router = APIRouter(prefix="/playlists", tags=["Playlists"])


@router.get("", response_model=list[PlaylistSummary], summary="List playlists")
def list_all(
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    return list_playlists(conn, user_id)


@router.post("", response_model=PlaylistSummary, status_code=201, summary="Create playlist")
def create(
    body: PlaylistCreate,
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="name cannot be empty")
    return create_playlist(conn, user_id, body.name, body.description)


@router.get("/{playlist_id}", response_model=PlaylistDetail, summary="Get playlist with tracks")
def get_one(
    playlist_id: int,
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    row = get_playlist(conn, playlist_id, user_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Playlist {playlist_id} not found")
    return row


@router.put("/{playlist_id}", response_model=PlaylistSummary, summary="Update playlist")
def update(
    playlist_id: int,
    body: PlaylistUpdate,
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    if body.name is not None and not body.name.strip():
        raise HTTPException(status_code=400, detail="name cannot be empty")
    row = update_playlist(
        conn, playlist_id, user_id,
        name=body.name, description=body.description,
    )
    if not row:
        raise HTTPException(status_code=404, detail=f"Playlist {playlist_id} not found")
    return row


@router.delete("/{playlist_id}", response_model=DeleteResponse, summary="Delete playlist")
def delete(
    playlist_id: int,
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    ok = delete_playlist(conn, playlist_id, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Playlist {playlist_id} not found")
    return DeleteResponse(deleted=True, id=playlist_id)


@router.post("/{playlist_id}/tracks", status_code=201, summary="Add track to playlist")
def add_track(
    playlist_id: int,
    body: PlaylistTrackAdd,
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    ok = add_track_to_playlist(conn, playlist_id, body.track_id, user_id)
    if not ok:
        raise HTTPException(
            status_code=404,
            detail=f"Playlist {playlist_id} or track {body.track_id} not found",
        )
    return {"added": True, "playlist_id": playlist_id, "track_id": body.track_id}


@router.delete("/{playlist_id}/tracks/{track_id}", summary="Remove track from playlist")
def remove_track(
    playlist_id: int,
    track_id: int,
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    ok = remove_track_from_playlist(conn, playlist_id, track_id, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Playlist {playlist_id} not found")
    return {"removed": True, "playlist_id": playlist_id, "track_id": track_id}
