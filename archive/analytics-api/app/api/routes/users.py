from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import UserServiceDep, get_user_service
from app.api.handlers import dispatch_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/segments",
    summary="User engagement segments",
    description="Returns engagement segments from agg_user_engagement.",
)
def users_segments(service: UserServiceDep = Depends(get_user_service)):
    return dispatch_service(service.get_segments)


@router.get(
    "/retention",
    summary="User retention cohort analysis",
    description="Returns retention cohorts with churn-risk and high-value signals.",
)
def users_retention(service: UserServiceDep = Depends(get_user_service)):
    return dispatch_service(service.get_retention)
