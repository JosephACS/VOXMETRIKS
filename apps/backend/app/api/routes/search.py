from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.routes._status import module_status
from app.api.deps import get_search_service
from app.models.schemas import SearchResponse
from app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/status", summary="Search module status")
def search_status():
    return module_status("search")


@router.get("", response_model=SearchResponse, summary="Search tracks, artists, playlists")
def search_catalog(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=50),
    service: SearchService = Depends(get_search_service),
):
    return service.search(q, limit=limit)
