"""backend/routes/stats.py"""

from __future__ import annotations

import duckdb
from fastapi import APIRouter, Depends, Query

from app.core.database import get_conn
from app.shared.schemas.models import DistribucionEnergia
from app.packages.analytics.services.stats_service import (
    get_summary, get_energia_distribution,
    get_top_tracks_by_popularity, get_last_loads,
)

router = APIRouter(prefix="/stats", tags=["Statistics"])


@router.get("/summary", summary="High-level warehouse counts")
def summary(conn: duckdb.DuckDBPyConnection = Depends(get_conn)):
    return get_summary(conn)


@router.get("/energia", response_model=list[DistribucionEnergia], summary="Energy distribution")
def energia(conn: duckdb.DuckDBPyConnection = Depends(get_conn)):
    return get_energia_distribution(conn)


@router.get("/top-tracks", summary="Top tracks by popularity")
def top_tracks(
    limit: int = Query(10, ge=1, le=100),
    conn:  duckdb.DuckDBPyConnection = Depends(get_conn),
):
    return get_top_tracks_by_popularity(conn, limit=limit)


@router.get("/loads", summary="Recent pipeline load history")
def load_history(
    limit: int = Query(5, ge=1, le=50),
    conn:  duckdb.DuckDBPyConnection = Depends(get_conn),
):
    return get_last_loads(conn, limit=limit)
