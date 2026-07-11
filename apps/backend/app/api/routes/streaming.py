from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.routes._status import module_status
from app.api.deps import get_streaming_service
from app.models.schemas import (
    LiveSessionStatsResponse,
    StreamActionRequest,
    StreamActionResponse,
    StreamEndRequest,
    StreamEndResponse,
    StreamStartRequest,
    StreamStartResponse,
)
from app.services.streaming_service import StreamingService

router = APIRouter(prefix="/stream", tags=["Streaming"])


@router.get("/status", summary="Streaming module status")
def streaming_status():
    return module_status("streaming")


@router.post(
    "/start",
    response_model=StreamStartResponse,
    status_code=201,
    summary="Start playback (STREAM_START)",
)
def stream_start(
    payload: StreamStartRequest,
    service: StreamingService = Depends(get_streaming_service),
):
    try:
        return service.start_stream(payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post(
    "/end",
    response_model=StreamEndResponse,
    summary="End playback (STREAM_END)",
)
def stream_end(
    payload: StreamEndRequest,
    service: StreamingService = Depends(get_streaming_service),
):
    try:
        return service.end_stream(payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post(
    "/skip",
    response_model=StreamActionResponse,
    summary="Skip track (STREAM_SKIP)",
)
def stream_skip(
    payload: StreamActionRequest,
    service: StreamingService = Depends(get_streaming_service),
):
    try:
        return service.skip_track(payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post(
    "/pause",
    response_model=StreamActionResponse,
    summary="Pause playback (STREAM_PAUSE)",
)
def stream_pause(
    payload: StreamActionRequest,
    service: StreamingService = Depends(get_streaming_service),
):
    try:
        return service.pause_stream(payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post(
    "/resume",
    response_model=StreamActionResponse,
    summary="Resume playback (STREAM_RESUME)",
)
def stream_resume(
    payload: StreamActionRequest,
    service: StreamingService = Depends(get_streaming_service),
):
    try:
        return service.resume_stream(payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get(
    "/session/{user_id}/live",
    response_model=LiveSessionStatsResponse,
    summary="Live session stats for a user",
)
def live_session_stats(
    user_id: int,
    service: StreamingService = Depends(get_streaming_service),
):
    return service.get_live_session_stats(user_id)
