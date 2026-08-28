"""Smart recommendation API — Phase 4."""

from __future__ import annotations

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.database import get_conn
from app.packages.analytics.services.smart.smart_service import SmartRecommendationService
from app.packages.identity.services.auth_deps import get_optional_user_id

router = APIRouter(prefix="/smart", tags=["Smart Recommendations"])


class SpotifyTasteRequest(BaseModel):
    """Consent-derived Spotify ids; tokens never enter the VOX API."""

    top_track_ids: list[str] = Field(default_factory=list, max_length=50)
    recent_track_ids: list[str] = Field(default_factory=list, max_length=50)
    saved_track_ids: list[str] = Field(default_factory=list, max_length=50)
    limit: int = Field(default=20, ge=1, le=50)


def _svc(conn: duckdb.DuckDBPyConnection = Depends(get_conn)) -> SmartRecommendationService:
    return SmartRecommendationService(conn)


def _require_user(user_id: int | None = Depends(get_optional_user_id)) -> int:
    if user_id is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user_id


@router.get("/home", summary="Personalized home feed sections")
def smart_home(
    user_id: int = Depends(_require_user),
    svc: SmartRecommendationService = Depends(_svc),
):
    return svc.get_home(user_id)


@router.get("/profile", summary="Musical profile and Audio DNA")
def musical_profile(
    user_id: int = Depends(_require_user),
    svc: SmartRecommendationService = Depends(_svc),
):
    return svc.get_profile(user_id)


@router.get("/recommendations", summary="Ranked personalized tracks")
def smart_recommendations(
    limit: int = Query(20, ge=1, le=50),
    user_id: int = Depends(_require_user),
    svc: SmartRecommendationService = Depends(_svc),
):
    return {"user_id": user_id, "tracks": svc.get_recommendations(user_id, limit=limit)}


@router.post(
    "/spotify-taste",
    summary="VOX recommendations seeded by consented Spotify taste signals",
)
def spotify_taste_recommendations(
    body: SpotifyTasteRequest,
    user_id: int = Depends(_require_user),
    svc: SmartRecommendationService = Depends(_svc),
):
    return {
        "user_id": user_id,
        **svc.get_spotify_taste_recommendations(
            user_id,
            top_track_ids=body.top_track_ids,
            recent_track_ids=body.recent_track_ids,
            saved_track_ids=body.saved_track_ids,
            limit=body.limit,
        ),
    }


@router.get("/discover-weekly", summary="Weekly personalized playlist")
def discover_weekly(
    user_id: int = Depends(_require_user),
    svc: SmartRecommendationService = Depends(_svc),
):
    return svc.get_discover_weekly(user_id)


@router.get("/daily-mixes", summary="Daily Mix playlists by cluster")
def daily_mixes(
    user_id: int = Depends(_require_user),
    svc: SmartRecommendationService = Depends(_svc),
):
    return {"mixes": svc.get_daily_mixes(user_id)}


@router.get("/because-you", summary="Because you listened/liked sections")
def because_you(
    user_id: int = Depends(_require_user),
    svc: SmartRecommendationService = Depends(_svc),
):
    return {"sections": svc.get_because_you(user_id)}


@router.get("/similar-tracks/{track_id}", summary="Similar tracks by audio features")
def similar_tracks_route(
    track_id: int,
    limit: int = Query(12, ge=1, le=30),
    svc: SmartRecommendationService = Depends(_svc),
):
    return {"track_id": track_id, "similar": svc.get_similar_tracks(track_id, limit=limit)}


@router.get("/similar-artists/{artist_id}", summary="Related artists")
def similar_artists_route(
    artist_id: int,
    limit: int = Query(8, ge=1, le=20),
    svc: SmartRecommendationService = Depends(_svc),
):
    return {"artist_id": artist_id, "similar": svc.get_similar_artists(artist_id, limit=limit)}


@router.get("/trending", summary="Trending modules bundle")
def smart_trending(svc: SmartRecommendationService = Depends(_svc)):
    return svc.get_trending()
