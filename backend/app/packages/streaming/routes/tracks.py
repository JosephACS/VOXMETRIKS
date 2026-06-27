"""backend/routes/tracks.py — Full CRUD"""

from __future__ import annotations

from typing import Optional

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.database import get_conn, get_write_conn
from app.packages.users.services.auth_deps import require_engineer_user
from app.shared.schemas.models import (
    AudioFeatures, AudioSource, CoverArt, PaginatedResponse, Track,
    TrackCreate, TrackUpdate, DeleteResponse,
    TrackSearchResult, TrackDetail,
)
from app.packages.streaming.services.track_service import (
    get_tracks, get_track_by_id, get_track_features,
    create_track, update_track, delete_track,
    search_tracks, get_track_detail,
)
from app.packages.streaming.services.audio_source_service import resolve_audio_source
from app.packages.streaming.services.cover_art_service import resolve_cover

router = APIRouter(prefix="/tracks", tags=["Tracks"])


@router.get("", response_model=PaginatedResponse, summary="List tracks")
def list_tracks(
    page:      int            = Query(1,  ge=1),
    limit:     int            = Query(50, ge=1, le=500),
    search:    Optional[str]  = Query(None),
    genre_id:  Optional[int]  = Query(None),
    artist_id: Optional[int]  = Query(None),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    rows, total = get_tracks(
        conn, page=page, limit=limit,
        search=search, genre_id=genre_id, artist_id=artist_id,
    )
    return PaginatedResponse(total=total, page=page, limit=limit, items=rows)


@router.get("/search", response_model=list[TrackSearchResult], summary="Search tracks")
def search_tracks_route(
    q: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=200),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    return search_tracks(conn, q, limit=limit)


@router.post("", response_model=Track, status_code=201, summary="Create track")
def create_track_route(
    body: TrackCreate,
    _engineer: int = Depends(require_engineer_user),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    if not body.nombre_track.strip():
        raise HTTPException(status_code=400, detail="nombre_track cannot be empty")
    row = create_track(
        conn,
        nombre_track=body.nombre_track,
        spotify_track_id=body.spotify_track_id,
        id_artista=body.id_artista,
        id_album=body.id_album,
        id_genero=body.id_genero,
        explicit=body.explicit,
        duration_ms=body.duration_ms,
    )
    if row.get("duplicate"):
        raise HTTPException(
            status_code=409,
            detail=f"Track already exists (id={row.get('id_track')})",
        )
    return row


@router.get("/{track_id}/detail", response_model=TrackDetail, summary="Track detail with features")
def track_detail(
    track_id: int,
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    row = get_track_detail(conn, track_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Track {track_id} not found")
    return row


@router.get("/{track_id}", response_model=Track, summary="Get track by ID")
def get_track(
    track_id: int,
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    row = get_track_by_id(conn, track_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Track {track_id} not found")
    return row


@router.put("/{track_id}", response_model=Track, summary="Update track")
def update_track_route(
    track_id: int,
    body: TrackUpdate,
    _engineer: int = Depends(require_engineer_user),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    row = update_track(
        conn, track_id,
        nombre_track=body.nombre_track,
        spotify_track_id=body.spotify_track_id,
        id_artista=body.id_artista,
        id_album=body.id_album,
        id_genero=body.id_genero,
        explicit=body.explicit,
        duration_ms=body.duration_ms,
    )
    if not row:
        raise HTTPException(status_code=404, detail=f"Track {track_id} not found")
    if row.get("duplicate"):
        raise HTTPException(
            status_code=409,
            detail=f"Another track already uses that name or Spotify ID (id={row.get('id_track')})",
        )
    return row


@router.delete("/{track_id}", response_model=DeleteResponse, summary="Delete track")
def delete_track_route(
    track_id: int,
    _engineer: int = Depends(require_engineer_user),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    ok = delete_track(conn, track_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Track {track_id} not found")
    return DeleteResponse(deleted=True, id=track_id)


@router.get("/{track_id}/features", response_model=AudioFeatures, summary="Track audio features")
def track_features(
    track_id: int,
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    row = get_track_features(conn, track_id)
    if not row:
        raise HTTPException(
            status_code=404, detail=f"Audio features for track {track_id} not found"
        )
    return row


@router.get(
    "/{track_id}/audio-source",
    response_model=AudioSource,
    summary="Resolve real playback source (YouTube) for a track",
)
def track_audio_source(
    track_id: int,
    force: bool = Query(False, description="Bypass cache and re-resolve"),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    row = resolve_audio_source(conn, track_id, force=force)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Track {track_id} not found")
    return row


@router.get(
    "/{track_id}/cover",
    response_model=CoverArt,
    summary="Resolve real cover-art image (iTunes) for a track",
)
def track_cover(
    track_id: int,
    force: bool = Query(False, description="Bypass cache and re-resolve"),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    row = resolve_cover(conn, track_id, force=force)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Track {track_id} not found")
    return row
