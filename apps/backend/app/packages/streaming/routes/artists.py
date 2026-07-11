"""backend/routes/artists.py — Full CRUD"""

from __future__ import annotations

from typing import Optional

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.database import get_conn, get_write_conn, using_write_conn
from app.packages.streaming.services.artist_service import (
    create_artist,
    delete_artist,
    get_artist_by_id,
    get_artist_stats,
    get_artists,
    get_top_artists,
    update_artist,
)
from app.packages.users.services.auth_deps import require_admin_user
from app.shared.schemas.models import (
    Artista,
    ArtistaCreate,
    ArtistaUpdate,
    ArtistCoverArt,
    DeleteResponse,
    PaginatedResponse,
    TopArtista,
)
from app.packages.streaming.services.cover_art_service import (
    get_cached_artist_cover,
    resolve_artist_cover,
)

router = APIRouter(prefix="/artists", tags=["Artists"])


@router.get("", response_model=PaginatedResponse, summary="List artists")
def list_artists(
    page:   int            = Query(1,  ge=1),
    limit:  int            = Query(50, ge=1, le=500),
    search: Optional[str]  = Query(None),
    conn:   duckdb.DuckDBPyConnection = Depends(get_conn),
):
    rows, total = get_artists(conn, page=page, limit=limit, search=search)
    return PaginatedResponse(total=total, page=page, limit=limit, items=rows)


@router.post("", response_model=Artista, status_code=201, summary="Create artist")
def create_artist_route(
    body: ArtistaCreate,
    _admin: int = Depends(require_admin_user),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    if not body.nombre_artista.strip():
        raise HTTPException(status_code=400, detail="nombre_artista cannot be empty")
    row = create_artist(conn, body.nombre_artista)
    if row.get("duplicate"):
        raise HTTPException(
            status_code=409,
            detail=f"Artist '{body.nombre_artista.strip()}' already exists (id={row['id_artista']})",
        )
    return row


@router.get("/top", response_model=list[TopArtista], summary="Top artists by avg popularity")
def top_artists(
    limit: int = Query(10, ge=1, le=100),
    conn:  duckdb.DuckDBPyConnection = Depends(get_conn),
):
    return get_top_artists(conn, limit=limit)


@router.get("/{artist_id}", response_model=Artista, summary="Get artist by ID")
def get_artist(
    artist_id: int,
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    row = get_artist_by_id(conn, artist_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Artist {artist_id} not found")
    return row


@router.put("/{artist_id}", response_model=Artista, summary="Update artist")
def update_artist_route(
    artist_id: int,
    body: ArtistaUpdate,
    _admin: int = Depends(require_admin_user),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    if not body.nombre_artista.strip():
        raise HTTPException(status_code=400, detail="nombre_artista cannot be empty")
    row = update_artist(conn, artist_id, body.nombre_artista)
    if not row:
        raise HTTPException(status_code=404, detail=f"Artist {artist_id} not found")
    if row.get("duplicate"):
        raise HTTPException(
            status_code=409,
            detail=f"Another artist already uses the name '{body.nombre_artista.strip()}'",
        )
    return row


@router.delete("/{artist_id}", response_model=DeleteResponse, summary="Delete artist")
def delete_artist_route(
    artist_id: int,
    _admin: int = Depends(require_admin_user),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    ok = delete_artist(conn, artist_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Artist {artist_id} not found")
    return DeleteResponse(deleted=True, id=artist_id)


@router.get("/{artist_id}/cover", response_model=ArtistCoverArt, summary="Artist image (iTunes)")
def artist_cover(
    artist_id: int,
    force: bool = Query(False, description="Bypass cache and re-resolve"),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    if not force:
        cached = get_cached_artist_cover(conn, artist_id)
        if cached is not None:
            return cached
    with using_write_conn() as write_conn:
        row = resolve_artist_cover(write_conn, artist_id, force=force)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Artist {artist_id} not found")
    return row


@router.get("/{artist_id}/stats", response_model=TopArtista, summary="Artist statistics")
def artist_stats(
    artist_id: int,
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    row = get_artist_stats(conn, artist_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Stats for artist {artist_id} not found")
    return row
