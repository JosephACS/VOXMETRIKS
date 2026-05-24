"""backend/routes/tracks.py"""

from __future__ import annotations

from typing import Optional

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Query

from ..database import get_conn
from ..schemas  import AudioFeatures, PaginatedResponse, Track
from ..services import get_tracks, get_track_by_id, get_track_features

router = APIRouter(prefix="/tracks", tags=["Tracks"])


@router.get("", response_model=PaginatedResponse, summary="List tracks")
def list_tracks(
    page:      int            = Query(1,  ge=1),
    limit:     int            = Query(50, ge=1, le=500),
    search:    Optional[str]  = Query(None, description="Filter by track name"),
    genre_id:  Optional[int]  = Query(None, description="Filter by genre ID"),
    artist_id: Optional[int]  = Query(None, description="Filter by artist ID"),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    rows, total = get_tracks(
        conn, page=page, limit=limit,
        search=search, genre_id=genre_id, artist_id=artist_id,
    )
    return PaginatedResponse(total=total, page=page, limit=limit, items=rows)


@router.get("/{track_id}", response_model=Track, summary="Get track by ID")
def get_track(
    track_id: int,
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    row = get_track_by_id(conn, track_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Track {track_id} not found")
    return row


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
