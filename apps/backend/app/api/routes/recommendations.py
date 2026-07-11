from __future__ import annotations

import duckdb
from fastapi import APIRouter, Depends, Query

from app.api.routes._status import module_status
from app.api.deps import get_recommendation_service
from app.core.database import get_conn
from app.models.schemas import RecommendationsResponse
from app.packages.identity.services.auth_deps import ensure_self_or_admin, require_user_id
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("/status", summary="Recommendations module status")
def recommendations_status():
    return module_status("recommendations")


@router.get(
    "/{user_id}",
    response_model=RecommendationsResponse,
    summary="Hybrid scored recommendations for a user",
)
def user_recommendations(
    user_id: int,
    limit: int = Query(20, ge=1, le=50),
    current_user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
    service: RecommendationService = Depends(get_recommendation_service),
):
    ensure_self_or_admin(
        target_user_id=user_id,
        current_user_id=current_user_id,
        conn=conn,
    )
    return service.get_recommendations(user_id, limit=limit)
