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
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/warehouse", summary="Warehouse status — layers, KPIs, pipeline stages")
def warehouse(conn: duckdb.DuckDBPyConnection = Depends(get_conn)):
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
