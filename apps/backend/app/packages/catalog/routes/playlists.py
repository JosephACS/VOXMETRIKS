"""Warehouse catalog playlists API (dim_playlist)."""

from __future__ import annotations

from typing import Optional

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.database import get_conn
from app.packages.catalog.services.playlist_catalog_service import (
    get_catalog_playlist,
    list_catalog_playlists,
)
from app.packages.identity.services.auth_deps import require_user_id
from app.shared.schemas.models import PaginatedResponse, PlaylistDetail

router = APIRouter(prefix="/catalog/playlists", tags=["Catalog Playlists"])


@router.get("", response_model=PaginatedResponse, summary="List warehouse playlists")
def list_playlists(
    page: int = Query(1, ge=1),
    limit: int = Query(24, ge=1, le=100),
    search: Optional[str] = Query(None, max_length=120),
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    _ = user_id
    return list_catalog_playlists(conn, page=page, limit=limit, search=search)


@router.get(
    "/{playlist_id}",
    response_model=PlaylistDetail,
    summary="Get warehouse playlist with tracks",
)
def get_one(
    playlist_id: int,
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    _ = user_id
    row = get_catalog_playlist(conn, playlist_id)
    if not row:
        raise HTTPException(
            status_code=404,
            detail=f"Catalog playlist {playlist_id} not found",
        )
    return row
