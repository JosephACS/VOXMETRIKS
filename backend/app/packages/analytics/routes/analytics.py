"""Enterprise analytics routes."""

from __future__ import annotations

import duckdb
from fastapi import APIRouter, Depends, Query

from app.core.database import get_conn
from app.packages.analytics.services.analytics_service import (
    get_warehouse_status,
    get_trending_analytics,
    get_platform_analytics,
    get_engagement_analytics,
    get_warehouse_tables,
    get_table_preview,
    get_recommendations,
)
from app.packages.analytics.services.history_service import get_history_hub
from app.packages.users.services.auth_deps import get_optional_user_id, require_engineer_user
from app.packages.users.services.user_service import get_me

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/warehouse", summary="Warehouse status — layers, KPIs, pipeline stages")
def warehouse(
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
    _engineer: int = Depends(require_engineer_user),
):
    return get_warehouse_status(conn)


@router.get("/trending", summary="Trending analytics — tracks, genres, daily streams")
def trending(
    limit: int = Query(25, ge=1, le=100),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    return get_trending_analytics(conn, limit=limit)


@router.get("/platform", summary="Platform usage — devices, sessions, active users")
def platform(conn: duckdb.DuckDBPyConnection = Depends(get_conn)):
    return get_platform_analytics(conn)


@router.get("/engagement", summary="Engagement metrics — skip rate, retention, searches")
def engagement(conn: duckdb.DuckDBPyConnection = Depends(get_conn)):
    return get_engagement_analytics(conn)


@router.get("/explorer/tables", summary="List warehouse tables with metadata")
def explorer_tables(
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
    _engineer: int = Depends(require_engineer_user),
):
    return get_warehouse_tables(conn)


@router.get("/explorer/preview/{table_name}", summary="Preview rows from a warehouse table")
def explorer_preview(
    table_name: str,
    page: int = Query(1, ge=1),
    limit: int = Query(8, ge=1, le=50),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
    _engineer: int = Depends(require_engineer_user),
):
    try:
        return get_table_preview(conn, table_name, page=page, limit=limit)
    except ValueError as exc:
        from fastapi import HTTPException
        msg = str(exc)
        if "not accessible" in msg:
            raise HTTPException(status_code=403, detail=msg) from exc
        raise HTTPException(status_code=404, detail=msg) from exc


@router.get("/history", summary="Unified history — user activity and searches")
def history(
    limit: int = Query(25, ge=1, le=50),
    user_id: int | None = Depends(get_optional_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    return get_history_hub(conn, user_id=user_id, limit=limit)


@router.get("/recommendations", summary="Personalized recommendations from warehouse")
def recommendations(
    limit: int = Query(12, ge=1, le=50),
    mood: str | None = Query(None, description="Energy range id e.g. 0_0-0_2"),
    user_id: int | None = Depends(get_optional_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    favorite_genre = None
    if user_id:
        profile = get_me(conn, user_id)
        if profile:
            favorite_genre = profile.get("favorite_genre")
    return get_recommendations(conn, favorite_genre=favorite_genre, limit=limit, mood=mood)
