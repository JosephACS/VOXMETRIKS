from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import GenreServiceDep, get_genre_service
from app.api.handlers import dispatch_service
from app.schemas.common import LimitQuery

router = APIRouter(prefix="/genres", tags=["Genres"])


@router.get(
    "/trends",
    summary="Genre trend momentum",
    description="Returns genre WoW trends from agg_genre_trends.",
)
def genres_trends(
    query: LimitQuery = Depends(),
    service: GenreServiceDep = Depends(get_genre_service),
):
    return dispatch_service(lambda: service.get_trends(query.limit))


@router.get(
    "/popularity",
    summary="Genre popularity and momentum score",
    description="Returns genre popularity with momentum_score from agg_genero_popularidad.",
)
def genres_popularity(
    query: LimitQuery = Depends(),
    service: GenreServiceDep = Depends(get_genre_service),
):
    return dispatch_service(lambda: service.get_popularity(query.limit))
