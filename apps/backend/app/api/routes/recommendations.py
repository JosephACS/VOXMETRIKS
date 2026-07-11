from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.routes._status import module_status
from app.api.deps import get_recommendation_service
from app.models.schemas import RecommendationsResponse
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
    service: RecommendationService = Depends(get_recommendation_service),
):
    return service.get_recommendations(user_id, limit=limit)
