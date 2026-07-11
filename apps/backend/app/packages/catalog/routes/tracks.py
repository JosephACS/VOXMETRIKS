"""backend/routes/tracks.py — Full CRUD"""

from __future__ import annotations

from typing import Optional

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.database import get_conn, get_write_conn, using_write_conn
from app.packages.streaming.services.audio_source_service import (
    get_audio_source_response,
)
from app.packages.catalog.services.cover_art_service import get_cached_cover, resolve_cover
from app.packages.catalog.services.track_service import (
    delete_track,
    get_track_by_id,
    get_track_detail,
    get_track_features,
    get_tracks,
    get_tracks_cursor,
    search_tracks,
    update_track,
)
from app.packages.identity.services.auth_deps import require_admin_user, require_user_id
from app.shared.schemas.models import (
    AudioFeatures,
    AudioSource,
    CoverArt,
    CursorPaginatedResponse,
    DeleteResponse,
    PaginatedResponse,
    Track,
    TrackCreate,
    TrackDetail,
    TrackUpdate,
)

router = APIRouter(prefix="/tracks", tags=["Tracks"])


@router.get("", summary="List tracks (offset or cursor pagination)")
def list_tracks(
    page:           int            = Query(1,  ge=1),
    limit:          int            = Query(50, ge=1, le=500),
    search:         Optional[str]  = Query(None),
    genre_id:       Optional[int]  = Query(None),
    artist_id:      Optional[int]  = Query(None),
    cursor:         Optional[str]  = Query(None, description="Keyset cursor from prior response"),
    use_cursor:     bool           = Query(False, description="Use cursor pagination instead of OFFSET"),
    include_total:  bool           = Query(False, description="Include total count on first cursor page"),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    if use_cursor or cursor is not None:
        try:
            payload = get_tracks_cursor(
                conn,
                limit=limit,
                cursor=cursor,
                search=search,
                genre_id=genre_id,
                artist_id=artist_id,
                include_total=include_total or cursor is None,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return CursorPaginatedResponse(**payload)

    rows, total = get_tracks(
        conn, page=page, limit=limit,
        search=search, genre_id=genre_id, artist_id=artist_id,
    )
    return PaginatedResponse(total=total, page=page, limit=limit, items=rows)


@router.get("/search", summary="Search tracks (paginated or cursor)")
def search_tracks_route(
    q: str = Query(..., min_length=2),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    cursor: Optional[str] = Query(None),
    use_cursor: bool = Query(False),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    try:
        items, total, next_cursor, has_more = search_tracks(
            conn, q, limit=limit, page=page, cursor=cursor if (use_cursor or cursor) else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if use_cursor or cursor is not None:
        return CursorPaginatedResponse(
            limit=limit,
            items=items,
            next_cursor=next_cursor,
            has_more=has_more,
        )
    return PaginatedResponse(total=total, page=page, limit=limit, items=items)


@router.post("", response_model=Track, status_code=201, summary="Create track")
def create_track_route(
    body: TrackCreate,
    _user: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    # Las canciones provienen del pipeline ELT (catálogo Spotify), no se crean a
    # mano. Ni siquiera el administrador da de alta tracks manualmente; sí puede
    # gestionar artistas y géneros. Cualquier intento se rechaza.
    raise HTTPException(
        status_code=403,
        detail="Las canciones se gestionan desde el pipeline de datos y no se crean manualmente.",
    )


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
    _admin: int = Depends(require_admin_user),
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
    _admin: int = Depends(require_admin_user),
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
    summary="Resolve playable audio source (multi-provider)",
)
def track_audio_source(
    track_id: int,
    force: bool = Query(False, description="Bypass cache and re-resolve"),
    async_resolve: bool = Query(True, description="Resolve in background on cache miss"),
    skip_provider: str | None = Query(
        None, description="Skip provider on fallback (e.g. youtube after playback failure)"
    ),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    row = get_audio_source_response(
        conn,
        track_id,
        force=force,
        async_resolve=async_resolve,
        skip_provider=skip_provider,
    )
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
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    if not force:
        cached = get_cached_cover(conn, track_id)
        if cached is not None:
            return cached
    with using_write_conn() as write_conn:
        row = resolve_cover(write_conn, track_id, force=force)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Track {track_id} not found")
    return row
