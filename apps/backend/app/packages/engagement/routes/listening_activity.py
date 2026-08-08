# -*- coding: utf-8 -*-
"""Personal listening activity API — authenticated user only (spec 035)."""

from __future__ import annotations

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.database import get_conn
from app.packages.engagement.services import listening_activity_service as las
from app.packages.identity.services.auth_deps import require_user_id

router = APIRouter(prefix="/me/listening-activity", tags=["Listening Activity"])


@router.get("", summary="Personal listening activity (authenticated user only)")
def listening_activity(
    period: str = Query("30d", description="7d | 30d | 90d | all"),
    top_limit: int = Query(10, ge=1, le=50),
    recent_limit: int = Query(25, ge=1, le=50),
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    """
    Returns aggregations for the session user only.
    Do not accept client-supplied user_id — isolation is enforced here.
    """
    try:
        return las.get_listening_activity(
            conn,
            user_id,
            period=period,
            top_limit=top_limit,
            recent_limit=recent_limit,
        )
    except ValueError as exc:
        if str(exc) == "invalid_period":
            raise HTTPException(
                status_code=400,
                detail={"code": "invalid_period", "message": "Periodo no válido. Use 7d, 30d, 90d o all."},
            ) from exc
        raise HTTPException(status_code=400, detail="Solicitud inválida") from exc
