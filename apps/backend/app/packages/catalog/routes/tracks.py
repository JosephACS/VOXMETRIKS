"""backend/routes/tracks.py — Full CRUD"""

from __future__ import annotations

from typing import Optional

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.database import get_conn, get_write_conn, using_write_conn
from app.packages.streaming.services.audio_source_service import (
    get_audio_source_response,
    report_source_failure,
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
from app.packages.identity.services.auth_deps import (
    require_admin_user,
    require_engineer_user,
    require_user_id,
)
from app.shared.schemas.models import (
    AudioFeatures,
    AudioSource,
    CoverArt,
    CursorPaginatedResponse,
    DeleteResponse,
    MusicSearchAdoptRequest,
    MusicSearchRepairRequest,
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
    playable_only:  bool           = Query(True, description="Consumer default: only tracks with usable audio"),
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
                playable_only=playable_only,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return CursorPaginatedResponse(**payload)

    rows, total = get_tracks(
        conn, page=page, limit=limit,
        search=search, genre_id=genre_id, artist_id=artist_id,
        playable_only=playable_only,
    )
    return PaginatedResponse(total=total, page=page, limit=limit, items=rows)


@router.get("/search", summary="Search tracks (paginated or cursor)")
def search_tracks_route(
    q: str = Query(..., min_length=2),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    cursor: Optional[str] = Query(None),
    use_cursor: bool = Query(False),
    playable_only: bool = Query(True, description="Consumer default: only playable tracks"),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    try:
        items, total, next_cursor, has_more = search_tracks(
            conn,
            q,
            limit=limit,
            page=page,
            cursor=cursor if (use_cursor or cursor) else None,
            playable_only=playable_only,
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


@router.get("/music-search", summary="Unified local + YouTube music search")
def music_search_route(
    q: str = Query(..., min_length=2, max_length=120),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    allow_external: bool = Query(True),
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    from app.packages.catalog.services.music_search_service import music_search

    return music_search(
        conn, q, page=page, limit=limit, allow_external=allow_external, user_id=user_id
    )


@router.post("/music-search/adopt", summary="Adopt selected YouTube result into catalog")
def music_search_adopt_route(
    body: MusicSearchAdoptRequest,
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    from app.packages.catalog.services.music_search_service import (
        AdoptRateLimitError,
        TrackSourceMismatchError,
        adopt_youtube_result,
    )
    from app.packages.streaming.services.audio_source_service import (
        YoutubeProviderUnavailableError,
    )

    try:
        return adopt_youtube_result(
            conn,
            video_id=body.video_id,
            preferred_track_id=body.track_id,
            require_preferred=body.require_preferred,
            user_id=user_id,
        )
    except AdoptRateLimitError as exc:
        raise HTTPException(
            status_code=429,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc
    except TrackSourceMismatchError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "code": exc.code,
                "message": str(exc),
                "can_create_new_track": exc.can_create_new_track,
            },
        ) from exc
    except YoutubeProviderUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "provider_unavailable", "message": str(exc)},
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger = __import__("logging").getLogger("voxmetrik.music_search")
        logger.exception("music-search adopt failed")
        raise HTTPException(status_code=502, detail="No fue posible preparar la canción.") from exc


@router.post("/music-search/repair-source", summary="Repair mismatched YouTube→Track association")
def music_search_repair_source_route(
    body: MusicSearchRepairRequest,
    _user: int = Depends(require_engineer_user),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    from app.packages.catalog.services.music_search_service import (
        repair_youtube_source_association,
    )
    from app.packages.streaming.services.audio_source_service import (
        YoutubeProviderUnavailableError,
    )

    try:
        return repair_youtube_source_association(conn, video_id=body.video_id)
    except YoutubeProviderUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "provider_unavailable", "message": str(exc)},
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger = __import__("logging").getLogger("voxmetrik.music_search")
        logger.exception("music-search repair failed")
        raise HTTPException(status_code=502, detail="No fue posible reparar la asociación.") from exc


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
    exclude_source_ref: str | None = Query(
        None,
        description="Comma-separated failed source/video ids to exclude when picking the next candidate",
    ),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    row = get_audio_source_response(
        conn,
        track_id,
        force=force,
        async_resolve=async_resolve,
        skip_provider=skip_provider,
        exclude_source_ref=exclude_source_ref,
    )
    if row is None:
        raise HTTPException(status_code=404, detail=f"Track {track_id} not found")
    return row


@router.post(
    "/{track_id}/audio-source/failure",
    summary="Report playback failure for cached audio source",
)
def track_audio_source_failure(
    track_id: int,
    _user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    report_source_failure(conn, track_id)
    return {"track_id": track_id, "status": "recorded"}


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
