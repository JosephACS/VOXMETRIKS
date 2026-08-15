"""Platform ops Pydantic schemas — Spec 027 / Spec 055."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class NotificationSendRequest(BaseModel):
    recipient: str
    subject: str
    body: str
    channel: str = "console"


class NotificationOut(BaseModel):
    id: int
    channel: str
    recipient: str
    subject: str
    body: str
    status: str
    created_at: datetime
    updated_at: datetime


class NotificationDeliveryOut(BaseModel):
    id: int
    notification_id: int
    adapter_code: str
    status: str
    labeled_mock: bool
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime


class PaginatedNotifications(BaseModel):
    items: list[NotificationOut]
    total: int
    page: int
    page_size: int


class ProviderConfigOut(BaseModel):
    id: int
    provider_code: str
    display_name: str
    is_mock: bool
    secret_ref_redacted: Optional[str] = None
    status: str
    config_json: str
    created_at: datetime
    updated_at: datetime


class ProviderRegisterRequest(BaseModel):
    provider_code: str
    display_name: str
    is_mock: bool = True
    secret_ref: Optional[str] = None
    config_json: str = "{}"


class WebhookReceiveRequest(BaseModel):
    source: str
    event_type: str
    idempotency_key: str
    payload: dict[str, Any] = Field(default_factory=dict)


class WebhookEventOut(BaseModel):
    id: int
    source: str
    event_type: str
    idempotency_key: str
    payload_json: str
    status: str
    received_at: datetime
    created_at: datetime


class PaginatedWebhookEvents(BaseModel):
    items: list[WebhookEventOut]
    total: int
    page: int
    page_size: int


class JobRegisterRequest(BaseModel):
    job_code: str
    display_name: str
    max_retries: int = 3


class BackgroundJobOut(BaseModel):
    id: int
    job_code: str
    display_name: str
    status: str
    max_retries: int
    created_at: datetime
    updated_at: datetime


class JobExecutionOut(BaseModel):
    id: int
    job_id: int
    status: str
    attempt_number: int
    result_json: Optional[str] = None
    error_message: Optional[str] = None
    dead_letter: bool
    started_at: datetime
    finished_at: Optional[datetime] = None
    created_at: datetime


class FeatureFlagUpsertRequest(BaseModel):
    flag_key: str
    description: str
    enabled: bool = False
    environment: str = "development"


class FeatureFlagOut(BaseModel):
    id: int
    flag_key: str
    description: str
    enabled: bool
    environment: str
    created_at: datetime
    updated_at: datetime


class HealthOut(BaseModel):
    status: str
    labeled_academic: bool
    message: str
    components: dict[str, str]


class MetricsOut(BaseModel):
    labeled_academic: bool
    message: str
    uptime_seconds: int
    request_count: int


class BackupOut(BaseModel):
    id: int
    backup_type: str
    status: str
    file_path: str
    size_bytes: int
    labeled_academic: bool
    created_by: int
    created_at: datetime
    completed_at: Optional[datetime] = None


class RestoreVerificationOut(BaseModel):
    id: int
    backup_record_id: int
    status: str
    verification_notes: str
    verified_by: int
    verified_at: datetime
    created_at: datetime


class OperationalIncidentCreateRequest(BaseModel):
    title: str
    severity: str = Field(..., pattern="^(low|medium|high|critical)$")
    description: str


class OperationalIncidentOut(BaseModel):
    id: int
    title: str
    severity: str
    status: str
    description: str
    reported_by: int
    reported_at: datetime
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class MockEmailRequest(BaseModel):
    to_address: str
    subject: str
    body: str


class MockEmailOut(BaseModel):
    success: bool
    labeled_mock: bool
    message: str


class OverviewQueueOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: Literal[
        "artist_requests",
        "catalog_reviews",
        "audio_unresolved",
        "incidents",
    ]
    count: Optional[int] = None
    availability: Literal["available", "unavailable"]
    severity: Literal["normal", "attention", "critical"]


class PlatformOpsOverviewOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    health: Literal["healthy", "degraded", "unavailable"]
    generated_at: datetime
    queues: list[OverviewQueueOut]
    next_queue: Optional[
        Literal[
            "artist_requests",
            "catalog_reviews",
            "audio_unresolved",
            "incidents",
        ]
    ] = None
    has_pending_work: bool
