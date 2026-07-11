"""backend/routes/stats.py"""

from __future__ import annotations

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, model_validator

from app.core.database import get_conn, get_write_conn
from app.packages.analytics.services.pipeline_service import run_pocketbase_import
from app.packages.analytics.services.stats_service import (
    MAX_TARGET_TOTAL,
    generate_synthetic_activity,
    get_catalog_growth,
    get_energia_distribution,
    get_last_loads,
    get_summary,
    get_synthetic_limits,
    get_top_tracks_by_popularity,
)
from app.packages.identity.services.auth_deps import require_engineer_user, require_user_id
from app.shared.schemas.models import DistribucionEnergia

router = APIRouter(prefix="/stats", tags=["Statistics"])


class SyntheticRequest(BaseModel):
    target_total: int | None = Field(
        None, ge=1, le=MAX_TARGET_TOTAL,
        description=f"Desired total synthetic activity rows across fact tables (max {MAX_TARGET_TOTAL:,})",
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
def summary(
    _user: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    return get_summary(conn)


@router.get("/catalog-growth", summary="Catalog growth from load history")
def catalog_growth(
    months: int = Query(12, ge=3, le=24),
    _user: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    return get_catalog_growth(conn, months=months)


@router.get("/synthetic/limits", summary="Validation limits for synthetic generation")
def synthetic_limits(_engineer: int = Depends(require_engineer_user)):
    return get_synthetic_limits()


@router.post("/import", summary="Import ~100k Spotify tracks from PocketBase into DuckDB")
def import_from_pocketbase(
    _engineer: int = Depends(require_engineer_user),
):
    """Full ELT: PocketBase CSV → Bronze → Silver → Gold (dim_*, fact_*)."""
    try:
        return run_pocketbase_import()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/synthetic", summary="Generate synthetic activity over the real music catalog")
def synthetic(
    body: SyntheticRequest,
    _engineer: int = Depends(require_engineer_user),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        return generate_synthetic_activity(
            conn,
            target_total=body.target_total,
            multiplier=body.multiplier,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/energia", response_model=list[DistribucionEnergia], summary="Energy distribution")
def energia(
    _user: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    return get_energia_distribution(conn)


@router.get("/energy-distribution", response_model=list[DistribucionEnergia], summary="Energy distribution (alias)")
def energy_distribution(
    _user: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    return get_energia_distribution(conn)


@router.get("/top-tracks", summary="Top tracks by popularity")
def top_tracks(
    limit: int = Query(10, ge=1, le=100),
    _user: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    return get_top_tracks_by_popularity(conn, limit=limit)


@router.get("/loads", summary="Recent pipeline load history")
def load_history(
    limit: int = Query(5, ge=1, le=50),
    _engineer: int = Depends(require_engineer_user),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    return get_last_loads(conn, limit=limit)
