"""HTTP contract tests for Platform Ops audio/YouTube request schemas."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.shared.schemas.models import (
    AudioSourceManualRequest,
    AudioSourceUnavailableRequest,
    MusicSearchRepairRequest,
    YoutubeSourcesRefreshRequest,
)


def test_manual_request_exactly_one_of_video_id_or_url() -> None:
    with pytest.raises(ValidationError):
        AudioSourceManualRequest()
    with pytest.raises(ValidationError):
        AudioSourceManualRequest(video_id="dQw4w9WgXcQ", url="https://youtu.be/dQw4w9WgXcQ")
    ok_vid = AudioSourceManualRequest(video_id="dQw4w9WgXcQ")
    assert ok_vid.video_id == "dQw4w9WgXcQ"
    ok_url = AudioSourceManualRequest(url="https://youtu.be/dQw4w9WgXcQ")
    assert ok_url.url is not None


def test_manual_request_forbids_validate_extra() -> None:
    with pytest.raises(ValidationError):
        AudioSourceManualRequest(video_id="dQw4w9WgXcQ", validate=False)  # type: ignore[call-arg]


def test_refresh_request_bounds_and_types() -> None:
    with pytest.raises(ValidationError):
        YoutubeSourcesRefreshRequest(limit=0)
    with pytest.raises(ValidationError):
        YoutubeSourcesRefreshRequest(limit=101)
    with pytest.raises(ValidationError):
        YoutubeSourcesRefreshRequest(max_age_days=0)
    with pytest.raises(ValidationError):
        YoutubeSourcesRefreshRequest(limit="25")  # type: ignore[arg-type]
    ok = YoutubeSourcesRefreshRequest(limit=10, max_age_days=7)
    assert ok.limit == 10


def test_repair_and_unavailable_forbid_extra() -> None:
    with pytest.raises(ValidationError):
        MusicSearchRepairRequest(video_id="short")
    with pytest.raises(ValidationError):
        MusicSearchRepairRequest(video_id="dQw4w9WgXcQ", extra=True)  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        AudioSourceUnavailableRequest(reason="x" * 501)
    with pytest.raises(ValidationError):
        AudioSourceUnavailableRequest(reason="ok", validate=False)  # type: ignore[call-arg]


def test_http_manual_rejects_validate_extra_422(
    client: TestClient, admin_auth_headers: dict[str, str]
) -> None:
    resp = client.post(
        "/api/v1/platform-ops/audio-unresolved/1/manual",
        headers=admin_auth_headers,
        json={"video_id": "dQw4w9WgXcQ", "validate": False},
    )
    assert resp.status_code == 422


def test_http_manual_rejects_both_fields_422(
    client: TestClient, admin_auth_headers: dict[str, str]
) -> None:
    resp = client.post(
        "/api/v1/platform-ops/audio-unresolved/1/manual",
        headers=admin_auth_headers,
        json={
            "video_id": "dQw4w9WgXcQ",
            "url": "https://youtu.be/dQw4w9WgXcQ",
        },
    )
    assert resp.status_code == 422


def test_http_refresh_rejects_bad_types_422(
    client: TestClient, admin_auth_headers: dict[str, str]
) -> None:
    resp = client.post(
        "/api/v1/platform-ops/youtube-sources/refresh",
        headers=admin_auth_headers,
        json={"limit": "many", "max_age_days": 30},
    )
    assert resp.status_code == 422


def test_http_repair_rejects_invalid_video_id_422(
    client: TestClient, admin_auth_headers: dict[str, str]
) -> None:
    resp = client.post(
        "/api/v1/platform-ops/youtube-sources/repair",
        headers=admin_auth_headers,
        json={"video_id": "nope"},
    )
    assert resp.status_code == 422


def test_http_unavailable_rejects_extra_422(
    client: TestClient, admin_auth_headers: dict[str, str]
) -> None:
    resp = client.post(
        "/api/v1/platform-ops/audio-unresolved/1/unavailable",
        headers=admin_auth_headers,
        json={"reason": "ops", "validate": False},
    )
    assert resp.status_code == 422
