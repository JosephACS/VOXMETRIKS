from __future__ import annotations

import duckdb
from fastapi import APIRouter, Depends, Path, Query

from app.api.deps_enterprise import get_track_service
from app.core.database import get_conn
from app.core.query_params import (
    ListFilters,
    PaginationParams,
    SortParams,
    apply_list_filters,
    get_list_filters,
    get_pagination_params,
    get_sort_params,
    paginate_items,
    sort_items,
)
from app.packages.identity.services.auth_deps import ensure_self_or_admin, require_user_id
from app.schemas.common import success_response
from app.services.track_service import TrackService

router = APIRouter(prefix="/tracks", tags=["Enterprise Tracks"])


@router.get(
    "/top",
    summary="Top tracks from agg_tracks_populares",
    response_description="Ranked tracks with popularity and stream counts",
)
def top_tracks(
    limit: int = Query(20, ge=1, le=100, description="Max items when page_size is omitted"),
    pagination: PaginationParams | None = Depends(get_pagination_params),
    sort: SortParams = Depends(get_sort_params),
    filters: ListFilters = Depends(get_list_filters),
    _user: int = Depends(require_user_id),
    service: TrackService = Depends(get_track_service),
):
    has_filters = any(
        [
            filters.genre,
            filters.artist,
            filters.platform,
            filters.device,
            filters.min_popularity is not None,
        ]
    )
    fetch_limit = 100 if (pagination or has_filters) else limit
    items = service.get_top_tracks(limit=fetch_limit)
    rows = [i.model_dump() for i in items]
    rows = apply_list_filters(rows, filters)
    rows = sort_items(rows, sort, default_field="total_streams")

    if pagination:
        page_rows, total = paginate_items(rows, pagination)
        return success_response(
            page_rows,
            count=len(page_rows),
            page=pagination.page,
            page_size=pagination.page_size,
            total=total,
            limit=pagination.page_size,
        )

    return success_response(rows[:limit], count=min(len(rows), limit), limit=limit)


@router.get(
    "/recommendations/{user_id}",
    summary="Statistical track recommendations (no ML)",
    response_description="Scored recommendations with explainable reasons",
)
def track_recommendations(
    user_id: int = Path(..., ge=1, description="Target user ID"),
    limit: int = Query(20, ge=1, le=50),
    pagination: PaginationParams | None = Depends(get_pagination_params),
    current_user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
    service: TrackService = Depends(get_track_service),
):
    ensure_self_or_admin(
        target_user_id=user_id,
        current_user_id=current_user_id,
        conn=conn,
    )
    items = service.get_recommendations(user_id, limit=limit)
    rows = [i.model_dump(exclude_none=True) for i in items]

    if pagination:
        page_rows, total = paginate_items(rows, pagination)
        return success_response(
            page_rows,
            count=len(page_rows),
            page=pagination.page,
            page_size=pagination.page_size,
            total=total,
            limit=pagination.page_size,
        )

    return success_response(rows, count=len(rows), limit=limit)
