"""backend/routes/genres.py"""

from __future__ import annotations

from typing import Optional

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Query

from ..database import get_conn
from ..schemas  import Genero, GeneroPopularidad, PaginatedResponse
from ..services import get_genres, get_genre_by_id, get_genre_stats

router = APIRouter(prefix="/genres", tags=["Genres"])


@router.get("", response_model=PaginatedResponse, summary="List genres")
def list_genres(
    page:   int           = Query(1,  ge=1),
    limit:  int           = Query(50, ge=1, le=500),
    search: Optional[str] = Query(None, description="Filter by genre name"),
    conn:   duckdb.DuckDBPyConnection = Depends(get_conn),
):
    rows, total = get_genres(conn, page=page, limit=limit, search=search)
    return PaginatedResponse(total=total, page=page, limit=limit, items=rows)


@router.get("/stats", response_model=list[GeneroPopularidad], summary="Genre statistics")
def genre_stats(
    limit: int = Query(20, ge=1, le=200),
    conn:  duckdb.DuckDBPyConnection = Depends(get_conn),
):
    return get_genre_stats(conn, limit=limit)


@router.get("/{genre_id}", response_model=Genero, summary="Get genre by ID")
def get_genre(
    genre_id: int,
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    row = get_genre_by_id(conn, genre_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Genre {genre_id} not found")
    return row
