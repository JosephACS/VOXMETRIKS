"""backend/routes/artists.py"""

from __future__ import annotations

from typing import Optional

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Query

from ..database import get_conn
from ..schemas  import Artista, PaginatedResponse, TopArtista
from ..services import (
    get_artists, get_artist_by_id,
    get_artist_stats, get_top_artists,
)

router = APIRouter(prefix="/artists", tags=["Artists"])


@router.get("", response_model=PaginatedResponse, summary="List artists")
def list_artists(
    page:   int            = Query(1,  ge=1,  description="Page number"),
    limit:  int            = Query(50, ge=1, le=500, description="Items per page"),
    search: Optional[str]  = Query(None, description="Filter by name (case-insensitive)"),
    conn:   duckdb.DuckDBPyConnection = Depends(get_conn),
):
    rows, total = get_artists(conn, page=page, limit=limit, search=search)
    return PaginatedResponse(total=total, page=page, limit=limit, items=rows)


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


@router.get("/{artist_id}/stats", response_model=TopArtista, summary="Artist statistics")
def artist_stats(
    artist_id: int,
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    row = get_artist_stats(conn, artist_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Stats for artist {artist_id} not found")
    return row
