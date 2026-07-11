from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path

from app.api.deps_enterprise import get_user_service
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
    service: EnterpriseUserService = Depends(get_user_service),
):
    data = service.get_user_insights(user_id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return success_response(data.model_dump())
