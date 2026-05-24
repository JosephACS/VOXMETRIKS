"""backend/routes/stats.py"""

from __future__ import annotations

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, model_validator

from app.core.database import get_conn
from app.shared.schemas.models import DistribucionEnergia
from app.packages.analytics.services.stats_service import (
    get_summary, get_energia_distribution,
    get_top_tracks_by_popularity, get_last_loads,
    generate_synthetic_tracks, get_synthetic_limits,
    get_catalog_growth,
    MAX_TARGET_TOTAL, MAX_CREATE_PER_RUN,
)

router = APIRouter(prefix="/stats", tags=["Statistics"])


class SyntheticRequest(BaseModel):
    target_total: int | None = Field(
        None, ge=1, le=MAX_TARGET_TOTAL,
        description=f"Desired total rows in dim_track (max {MAX_TARGET_TOTAL:,})",
    )
    multiplier: int | None = Field(
        None, ge=1, le=1000,
        description="Shortcut: target = current_count × multiplier",
    )

    @model_validator(mode="after")
    def require_mode(self) -> "SyntheticRequest":
        if self.target_total is None and self.multiplier is None:
            raise ValueError("provide target_total or multiplier")
        return self


@router.get("/summary", summary="High-level warehouse counts")
def summary(conn: duckdb.DuckDBPyConnection = Depends(get_conn)):
    return get_summary(conn)


@router.get("/catalog-growth", summary="Catalog growth from load history")
def catalog_growth(
    months: int = Query(12, ge=3, le=24),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    return get_catalog_growth(conn, months=months)


@router.get("/synthetic/limits", summary="Validation limits for synthetic generation")
def synthetic_limits():
    return get_synthetic_limits()


@router.post("/synthetic", summary="Generate synthetic tracks from existing warehouse data")
def synthetic(
    body: SyntheticRequest,
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    try:
        return generate_synthetic_tracks(
            conn,
            target_total=body.target_total,
            multiplier=body.multiplier,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/energia", response_model=list[DistribucionEnergia], summary="Energy distribution")
def energia(conn: duckdb.DuckDBPyConnection = Depends(get_conn)):
    return get_energia_distribution(conn)


@router.get("/energy-distribution", response_model=list[DistribucionEnergia], summary="Energy distribution (alias)")
def energy_distribution(conn: duckdb.DuckDBPyConnection = Depends(get_conn)):
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
