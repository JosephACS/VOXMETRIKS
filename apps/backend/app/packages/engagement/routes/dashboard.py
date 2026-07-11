"""Dashboard BFF routes — batched payloads for hot UI screens."""

from __future__ import annotations

import duckdb
from fastapi import APIRouter, Depends, Query

from app.core.database import get_conn
from app.packages.engagement.services.dashboard_service import get_home_feed
from app.packages.identity.services.auth_deps import require_user_id

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/home", summary="Home feed (summary, rails, discover)")
def home_feed(
    discover_page: int = Query(1, ge=1, le=200),
    user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
):
    return get_home_feed(conn, user_id=user_id, discover_page=discover_page)
