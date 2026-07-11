from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import RecommendationServiceDep, get_recommendation_service
from app.api.handlers import dispatch_service
from app.schemas.common import LimitQuery

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get(
    "/tracks",
    summary="Top recommended tracks",
    description="Returns segmented recommendations from agg_recommendation_scores.",
)
def recommendations_tracks(
    query: LimitQuery = Depends(),
    service: RecommendationServiceDep = Depends(get_recommendation_service),
):
    return dispatch_service(lambda: service.get_tracks(query.limit))
