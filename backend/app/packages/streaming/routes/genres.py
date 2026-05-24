"""backend/routes/genres.py — Full CRUD"""

from __future__ import annotations

from typing import Optional

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.database import get_conn, get_write_conn
from app.shared.schemas.models import (
    Genero, GeneroCreate, GeneroUpdate,
    GeneroPopularidad, PaginatedResponse, DeleteResponse,
)
from app.packages.streaming.services.genre_service import (
    get_genres, get_genre_by_id, get_genre_stats,
    create_genre, update_genre, delete_genre,
)

router = APIRouter(prefix="/genres", tags=["Genres"])


@router.get("", response_model=PaginatedResponse, summary="List genres")
def list_genres(
    page:   int           = Query(1,  ge=1),
    limit:  int           = Query(50, ge=1, le=500),
    search: Optional[str] = Query(None),
    conn:   duckdb.DuckDBPyConnection = Depends(get_conn),
):
    rows, total = get_genres(conn, page=page, limit=limit, search=search)
    return PaginatedResponse(total=total, page=page, limit=limit, items=rows)


@router.post("", response_model=Genero, status_code=201, summary="Create genre")
def create_genre_route(
    body: GeneroCreate,
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    if not body.nombre_genero.strip():
        raise HTTPException(status_code=400, detail="nombre_genero cannot be empty")
    return create_genre(conn, body.nombre_genero)


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


@router.put("/{genre_id}", response_model=Genero, summary="Update genre")
def update_genre_route(
    genre_id: int,
    body: GeneroUpdate,
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    if not body.nombre_genero.strip():
        raise HTTPException(status_code=400, detail="nombre_genero cannot be empty")
    row = update_genre(conn, genre_id, body.nombre_genero)
    if not row:
        raise HTTPException(status_code=404, detail=f"Genre {genre_id} not found")
    return row


@router.delete("/{genre_id}", response_model=DeleteResponse, summary="Delete genre")
def delete_genre_route(
    genre_id: int,
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    ok = delete_genre(conn, genre_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Genre {genre_id} not found")
    return DeleteResponse(deleted=True, id=genre_id)
