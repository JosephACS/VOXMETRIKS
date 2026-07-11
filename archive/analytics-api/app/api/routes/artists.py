from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import ArtistServiceDep, get_artist_service
from app.api.handlers import dispatch_service
from app.schemas.common import LimitQuery

router = APIRouter(prefix="/artists", tags=["Artists"])


@router.get(
    "/growth",
    summary="Top artist growth metrics",
    description="Returns top 20 artists by growth_pct from agg_artist_growth.",
)
def artists_growth(service: ArtistServiceDep = Depends(get_artist_service)):
    return dispatch_service(service.get_growth)


@router.get(
    "/top",
    summary="Top artists by stream volume",
    description="Returns artists ranked by total_streams from agg_top_artistas.",
)
def artists_top(
    query: LimitQuery = Depends(),
    service: ArtistServiceDep = Depends(get_artist_service),
):
    return dispatch_service(lambda: service.get_top(query.limit))
