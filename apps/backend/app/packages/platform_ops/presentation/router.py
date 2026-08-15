"""Platform ops HTTP router — Spec 027."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.packages.platform_ops.application.use_cases import (
    BackupUseCases,
    EmailUseCases,
    FeatureFlagUseCases,
    HealthUseCases,
    JobUseCases,
    NotificationUseCases,
    OperationalIncidentUseCases,
    ProviderConfigUseCases,
    WebhookUseCases,
    redact_secret,
)
from app.packages.platform_ops.application.overview import build_platform_ops_overview
from app.packages.platform_ops.domain.errors import PlatformOpsError
from app.packages.platform_ops.presentation.dependencies import require_ops_permission
from app.packages.platform_ops.presentation.error_mapping import raise_platform_ops_http
from app.shared.schemas.models import (
    AudioSourceManualRequest,
    AudioSourceUnavailableRequest,
    MusicSearchRepairRequest,
    YoutubeSourcesRefreshRequest,
)
from app.packages.platform_ops.presentation.schemas import (
    BackgroundJobOut,
    BackupOut,
    FeatureFlagOut,
    FeatureFlagUpsertRequest,
    HealthOut,
    JobExecutionOut,
    JobRegisterRequest,
    MetricsOut,
    MockEmailOut,
    MockEmailRequest,
    NotificationDeliveryOut,
    NotificationOut,
    NotificationSendRequest,
    OperationalIncidentCreateRequest,
    OperationalIncidentOut,
    PaginatedNotifications,
    PaginatedWebhookEvents,
    PlatformOpsOverviewOut,
    ProviderConfigOut,
    ProviderRegisterRequest,
    RestoreVerificationOut,
    WebhookEventOut,
    WebhookReceiveRequest,
)

platform_ops_router = APIRouter(prefix="/platform-ops", tags=["Platform Ops"])


@platform_ops_router.get("/overview", response_model=PlatformOpsOverviewOut)
def get_platform_ops_overview(
    ctx: dict = Depends(require_ops_permission("ops.view")),
) -> PlatformOpsOverviewOut:
    """Spec 055 — authoritative queue overview (read-only, no DDL)."""
    data = build_platform_ops_overview(ctx["conn"])
    return PlatformOpsOverviewOut.model_validate(data)


def _page(page: int, page_size: int) -> tuple[int, int, int]:
    page = max(1, page)
    ps = min(max(1, page_size), 100)
    return page, ps, (page - 1) * ps


def _provider_out(p) -> ProviderConfigOut:
    return ProviderConfigOut(
        id=p.id,
        provider_code=p.provider_code,
        display_name=p.display_name,
        is_mock=p.is_mock,
        secret_ref_redacted=redact_secret(p.secret_ref),
        status=p.status,
        config_json=p.config_json,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


@platform_ops_router.get("/health", response_model=HealthOut)
def get_health(
    ctx: dict = Depends(require_ops_permission("ops.view")),
) -> HealthOut:
    data = HealthUseCases().get_health()
    return HealthOut(**data)


@platform_ops_router.get("/metrics", response_model=MetricsOut)
def get_metrics(
    ctx: dict = Depends(require_ops_permission("ops.view")),
) -> MetricsOut:
    data = HealthUseCases().get_metrics()
    return MetricsOut(**data)


@platform_ops_router.get("/notifications", response_model=PaginatedNotifications)
def list_notifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    ctx: dict = Depends(require_ops_permission("ops.view")),
) -> PaginatedNotifications:
    p, ps, offset = _page(page, page_size)
    items, total = NotificationUseCases(ctx["conn"]).list(limit=ps, offset=offset)
    return PaginatedNotifications(
        items=[NotificationOut(**n.__dict__) for n in items],
        total=total, page=p, page_size=ps,
    )


@platform_ops_router.post("/notifications", response_model=NotificationOut, status_code=201)
def send_notification(
    body: NotificationSendRequest,
    ctx: dict = Depends(require_ops_permission("ops.manage")),
) -> NotificationOut:
    n, _ = NotificationUseCases(ctx["conn"]).send(
        actor_user_id=ctx["user_id"],
        recipient=body.recipient,
        subject=body.subject,
        body=body.body,
        channel=body.channel,
        request_id=ctx["request_id"],
    )
    return NotificationOut(**n.__dict__)


@platform_ops_router.post("/email/mock", response_model=MockEmailOut)
def send_mock_email(
    body: MockEmailRequest,
    ctx: dict = Depends(require_ops_permission("ops.manage")),
) -> MockEmailOut:
    result = EmailUseCases(ctx["conn"]).send_mock_email(
        actor_user_id=ctx["user_id"],
        to_address=body.to_address,
        subject=body.subject,
        body=body.body,
        request_id=ctx["request_id"],
    )
    return MockEmailOut(**result)


@platform_ops_router.get("/providers", response_model=list[ProviderConfigOut])
def list_providers(
    ctx: dict = Depends(require_ops_permission("ops.view")),
) -> list[ProviderConfigOut]:
    return [_provider_out(p) for p in ProviderConfigUseCases(ctx["conn"]).list()]


@platform_ops_router.post("/providers", response_model=ProviderConfigOut, status_code=201)
def register_provider(
    body: ProviderRegisterRequest,
    ctx: dict = Depends(require_ops_permission("ops.manage")),
) -> ProviderConfigOut:
    try:
        p = ProviderConfigUseCases(ctx["conn"]).register(
            actor_user_id=ctx["user_id"],
            provider_code=body.provider_code,
            display_name=body.display_name,
            is_mock=body.is_mock,
            secret_ref=body.secret_ref,
            config_json=body.config_json,
            request_id=ctx["request_id"],
        )
    except PlatformOpsError as e:
        raise_platform_ops_http(e)
    return _provider_out(p)


@platform_ops_router.post("/providers/seed-billing", response_model=list[ProviderConfigOut])
def seed_billing_providers(
    ctx: dict = Depends(require_ops_permission("ops.manage")),
) -> list[ProviderConfigOut]:
    items = ProviderConfigUseCases(ctx["conn"]).seed_billing_providers(
        actor_user_id=ctx["user_id"],
    )
    return [_provider_out(p) for p in items]


@platform_ops_router.get("/webhooks", response_model=PaginatedWebhookEvents)
def list_webhooks(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    ctx: dict = Depends(require_ops_permission("ops.webhooks")),
) -> PaginatedWebhookEvents:
    p, ps, offset = _page(page, page_size)
    items, total = WebhookUseCases(ctx["conn"]).list_events(limit=ps, offset=offset)
    return PaginatedWebhookEvents(
        items=[WebhookEventOut(**e.__dict__) for e in items],
        total=total, page=p, page_size=ps,
    )


@platform_ops_router.post("/webhooks/receive", response_model=WebhookEventOut, status_code=201)
def receive_webhook(
    body: WebhookReceiveRequest,
    ctx: dict = Depends(require_ops_permission("ops.webhooks")),
) -> WebhookEventOut:
    try:
        event = WebhookUseCases(ctx["conn"]).receive(
            source=body.source,
            event_type=body.event_type,
            idempotency_key=body.idempotency_key,
            payload=body.payload,
            request_id=ctx["request_id"],
        )
    except PlatformOpsError as e:
        raise_platform_ops_http(e)
    return WebhookEventOut(**event.__dict__)


@platform_ops_router.get("/jobs", response_model=list[BackgroundJobOut])
def list_jobs(
    ctx: dict = Depends(require_ops_permission("ops.view")),
) -> list[BackgroundJobOut]:
    return [BackgroundJobOut(**j.__dict__) for j in JobUseCases(ctx["conn"]).list()]


@platform_ops_router.post("/jobs", response_model=BackgroundJobOut, status_code=201)
def register_job(
    body: JobRegisterRequest,
    ctx: dict = Depends(require_ops_permission("ops.manage")),
) -> BackgroundJobOut:
    job = JobUseCases(ctx["conn"]).register(
        actor_user_id=ctx["user_id"],
        job_code=body.job_code,
        display_name=body.display_name,
        max_retries=body.max_retries,
        request_id=ctx["request_id"],
    )
    return BackgroundJobOut(**job.__dict__)


@platform_ops_router.post("/jobs/{job_id}/execute", response_model=JobExecutionOut)
def execute_job(
    job_id: int,
    simulate_failure: bool = Query(default=False),
    ctx: dict = Depends(require_ops_permission("ops.manage")),
) -> JobExecutionOut:
    ex = JobUseCases(ctx["conn"]).execute(
        job_id,
        actor_user_id=ctx["user_id"],
        simulate_failure=simulate_failure,
        request_id=ctx["request_id"],
    )
    return JobExecutionOut(**ex.__dict__)


@platform_ops_router.get("/jobs/{job_id}/executions", response_model=list[JobExecutionOut])
def list_job_executions(
    job_id: int,
    ctx: dict = Depends(require_ops_permission("ops.view")),
) -> list[JobExecutionOut]:
    return [JobExecutionOut(**e.__dict__) for e in JobUseCases(ctx["conn"]).list_executions(job_id)]


@platform_ops_router.get("/flags", response_model=list[FeatureFlagOut])
def list_flags(
    environment: str | None = Query(default=None),
    ctx: dict = Depends(require_ops_permission("ops.flags")),
) -> list[FeatureFlagOut]:
    return [FeatureFlagOut(**f.__dict__) for f in FeatureFlagUseCases(ctx["conn"]).list(environment=environment)]


@platform_ops_router.put("/flags", response_model=FeatureFlagOut)
def upsert_flag(
    body: FeatureFlagUpsertRequest,
    ctx: dict = Depends(require_ops_permission("ops.flags")),
) -> FeatureFlagOut:
    flag = FeatureFlagUseCases(ctx["conn"]).upsert(
        actor_user_id=ctx["user_id"],
        flag_key=body.flag_key,
        description=body.description,
        enabled=body.enabled,
        environment=body.environment,
        request_id=ctx["request_id"],
    )
    return FeatureFlagOut(**flag.__dict__)


@platform_ops_router.get("/backups", response_model=list[BackupOut])
def list_backups(
    ctx: dict = Depends(require_ops_permission("ops.view")),
) -> list[BackupOut]:
    return [BackupOut(**b.__dict__) for b in BackupUseCases(ctx["conn"]).list_backups()]


@platform_ops_router.post("/backups", response_model=BackupOut, status_code=201)
def create_backup(
    ctx: dict = Depends(require_ops_permission("ops.manage")),
) -> BackupOut:
    b = BackupUseCases(ctx["conn"]).create_backup(
        actor_user_id=ctx["user_id"], request_id=ctx["request_id"],
    )
    return BackupOut(**b.__dict__)


@platform_ops_router.post("/backups/{backup_id}/verify", response_model=RestoreVerificationOut)
def verify_backup(
    backup_id: int,
    ctx: dict = Depends(require_ops_permission("ops.manage")),
) -> RestoreVerificationOut:
    try:
        v = BackupUseCases(ctx["conn"]).verify_restore(
            backup_id, actor_user_id=ctx["user_id"], request_id=ctx["request_id"],
        )
    except PlatformOpsError as e:
        raise_platform_ops_http(e)
    return RestoreVerificationOut(**v.__dict__)


@platform_ops_router.get("/incidents", response_model=list[OperationalIncidentOut])
def list_ops_incidents(
    ctx: dict = Depends(require_ops_permission("ops.view")),
) -> list[OperationalIncidentOut]:
    return [OperationalIncidentOut(**i.__dict__) for i in OperationalIncidentUseCases(ctx["conn"]).list()]


@platform_ops_router.post("/incidents", response_model=OperationalIncidentOut, status_code=201)
def create_ops_incident(
    body: OperationalIncidentCreateRequest,
    ctx: dict = Depends(require_ops_permission("ops.manage")),
) -> OperationalIncidentOut:
    inc = OperationalIncidentUseCases(ctx["conn"]).create(
        actor_user_id=ctx["user_id"],
        title=body.title,
        severity=body.severity,
        description=body.description,
        request_id=ctx["request_id"],
    )
    return OperationalIncidentOut(**inc.__dict__)


# ── Unresolved external audio tray ───────────────────────────────────────────


@platform_ops_router.get("/audio-unresolved")
def list_audio_unresolved(
    q: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    ctx: dict = Depends(require_ops_permission("ops.view")),
) -> dict:
    from app.packages.streaming.services.audio_source_service import list_unresolved_audio

    return list_unresolved_audio(ctx["conn"], limit=limit, offset=offset, q=q)


@platform_ops_router.get("/audio-unresolved/{track_id}/candidates")
def audio_unresolved_candidates(
    track_id: int,
    ctx: dict = Depends(require_ops_permission("ops.view")),
) -> dict:
    from app.packages.streaming.services.audio_source_service import search_audio_candidates
    from fastapi import HTTPException

    data = search_audio_candidates(ctx["conn"], track_id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Track {track_id} not found")
    return data


@platform_ops_router.post("/audio-unresolved/{track_id}/manual")
def audio_unresolved_manual(
    track_id: int,
    body: AudioSourceManualRequest,
    ctx: dict = Depends(require_ops_permission("ops.manage")),
) -> dict:
    from app.packages.streaming.services.audio_source_service import (
        YoutubeProviderUnavailableError,
        save_manual_youtube_source,
    )
    from fastapi import HTTPException

    raw = body.video_id or body.url or ""
    try:
        result = save_manual_youtube_source(
            ctx["conn"], track_id, video_id_or_url=str(raw)
        )
    except YoutubeProviderUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "provider_unavailable", "message": str(exc)},
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail=f"Track {track_id} not found")
    return result


@platform_ops_router.post("/audio-unresolved/{track_id}/unavailable")
def audio_unresolved_mark_unavailable(
    track_id: int,
    body: AudioSourceUnavailableRequest | None = None,
    ctx: dict = Depends(require_ops_permission("ops.manage")),
) -> dict:
    from app.packages.streaming.services.audio_source_service import mark_audio_unavailable
    from fastapi import HTTPException

    reason = (body.reason if body and body.reason else None) or ""
    reason = reason.strip()
    if not reason:
        raise HTTPException(
            status_code=400,
            detail={"code": "reason_required", "message": "A non-blank reason is required"},
        )
    result = mark_audio_unavailable(ctx["conn"], track_id, reason=str(reason))
    if result is None:
        raise HTTPException(status_code=404, detail=f"Track {track_id} not found")
    return result


@platform_ops_router.post("/audio-unresolved/{track_id}/reresolve")
def audio_unresolved_reresolve(
    track_id: int,
    ctx: dict = Depends(require_ops_permission("ops.manage")),
) -> dict:
    from app.packages.streaming.services.audio_source_service import resolve_audio_source
    from fastapi import HTTPException

    result = resolve_audio_source(ctx["conn"], track_id, force=True)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Track {track_id} not found")
    return result


@platform_ops_router.post("/youtube-sources/refresh")
def youtube_sources_refresh(
    body: YoutubeSourcesRefreshRequest | None = None,
    ctx: dict = Depends(require_ops_permission("ops.manage")),
) -> dict:
    """Explicit small-batch refresh of stale YouTube metadata (never on Discover)."""
    from app.packages.streaming.services.audio.refresh_youtube_metadata import (
        refresh_youtube_metadata_batch,
    )

    req = body or YoutubeSourcesRefreshRequest()
    return refresh_youtube_metadata_batch(
        ctx["conn"], limit=req.limit, max_age_days=req.max_age_days
    )


@platform_ops_router.post("/youtube-sources/repair")
def youtube_sources_repair(
    body: MusicSearchRepairRequest,
    ctx: dict = Depends(require_ops_permission("ops.manage")),
) -> dict:
    """Reassign a YouTube videoId away from an incompatible Track."""
    from app.packages.catalog.services.music_search_service import (
        repair_youtube_source_association,
    )
    from app.packages.streaming.services.audio_source_service import (
        YoutubeProviderUnavailableError,
    )
    from fastapi import HTTPException

    try:
        return repair_youtube_source_association(ctx["conn"], video_id=body.video_id)
    except YoutubeProviderUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "provider_unavailable", "message": str(exc)},
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
