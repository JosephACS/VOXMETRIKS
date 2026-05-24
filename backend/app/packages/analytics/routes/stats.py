"""backend/routes/stats.py"""

from __future__ import annotations

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.database import get_conn
from app.shared.schemas.models import DistribucionEnergia
from app.packages.analytics.services.stats_service import (
    get_summary, get_energia_distribution,
    get_top_tracks_by_popularity, get_last_loads,
    generate_synthetic_tracks,
)

router = APIRouter(prefix="/stats", tags=["Statistics"])


class SyntheticRequest(BaseModel):
    multiplier: int = Field(2, ge=1, le=4, description="Target volume factor (2 = double tracks)")


@router.get("/summary", summary="High-level warehouse counts")
def summary(conn: duckdb.DuckDBPyConnection = Depends(get_conn)):
    return get_summary(conn)


@router.post("/synthetic", summary="Generate synthetic tracks from existing warehouse data")
def synthetic(
    body: SyntheticRequest,
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    try:
        return generate_synthetic_tracks(conn, body.multiplier)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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
