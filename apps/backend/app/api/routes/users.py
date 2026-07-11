from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.routes._status import module_status
from app.api.deps import get_user_service
from app.models.schemas import UserActivityResponse, UserProfileResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/status", summary="Users module status")
def users_status():
    return module_status("users")


@router.get(
    "/{user_id}",
    response_model=UserProfileResponse,
    summary="User profile with engagement segment",
)
def get_user(user_id: int, service: UserService = Depends(get_user_service)):
    profile = service.get_user(user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return profile


@router.get(
    "/{user_id}/activity",
    response_model=UserActivityResponse,
    summary="User streaming activity summary",
)
def get_user_activity(user_id: int, service: UserService = Depends(get_user_service)):
    activity = service.get_user_activity(user_id)
    if activity is None:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return activity
