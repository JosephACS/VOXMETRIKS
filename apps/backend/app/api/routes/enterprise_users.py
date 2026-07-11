from __future__ import annotations

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Path

from app.api.deps_enterprise import get_user_service
from app.core.database import get_conn
from app.packages.identity.services.auth_deps import ensure_self_or_admin, require_user_id
from app.schemas.common import success_response
from app.services.enterprise_user_service import EnterpriseUserService

router = APIRouter(prefix="/users", tags=["Enterprise Users"])


@router.get(
    "/{user_id}/insights",
    summary="User engagement insights",
    response_description="Listening profile, top genres, and activity metrics",
)
def user_insights(
    user_id: int = Path(..., ge=1, description="User ID"),
    current_user_id: int = Depends(require_user_id),
    conn: duckdb.DuckDBPyConnection = Depends(get_conn),
    service: EnterpriseUserService = Depends(get_user_service),
):
    ensure_self_or_admin(
        target_user_id=user_id,
        current_user_id=current_user_id,
        conn=conn,
    )
    data = service.get_user_insights(user_id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return success_response(data.model_dump())
