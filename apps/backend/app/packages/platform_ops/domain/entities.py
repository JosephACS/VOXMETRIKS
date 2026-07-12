"""Platform ops domain entities — Spec 027."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Notification:
    id: int
    channel: str
    recipient: str
    subject: str
    body: str
    status: str
    created_at: datetime
    updated_at: datetime


@dataclass
class NotificationDelivery:
    id: int
    notification_id: int
    adapter_code: str
    status: str
    labeled_mock: bool
    delivered_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime


@dataclass
class ProviderConfiguration:
    id: int
    provider_code: str
    display_name: str
    is_mock: bool
    secret_ref: Optional[str]
    status: str
    config_json: str
    created_at: datetime
    updated_at: datetime


@dataclass
class WebhookEvent:
    id: int
    source: str
    event_type: str
    idempotency_key: str
    payload_json: str
    status: str
    received_at: datetime
    created_at: datetime


@dataclass
class WebhookDelivery:
    id: int
    webhook_event_id: int
    target_url: str
    status: str
    attempt_count: int
    last_attempt_at: Optional[datetime]
    response_code: Optional[int]
    created_at: datetime
    updated_at: datetime


@dataclass
class BackgroundJob:
    id: int
    job_code: str
    display_name: str
    status: str
    max_retries: int
    created_at: datetime
    updated_at: datetime


@dataclass
class JobExecution:
    id: int
    job_id: int
    status: str
    attempt_number: int
    result_json: Optional[str]
    error_message: Optional[str]
    dead_letter: bool
    started_at: datetime
    finished_at: Optional[datetime]
    created_at: datetime


@dataclass
class FeatureFlag:
    id: int
    flag_key: str
    description: str
    enabled: bool
    environment: str
    created_at: datetime
    updated_at: datetime


@dataclass
class OperationalIncident:
    id: int
    title: str
    severity: str
    status: str
    description: str
    reported_by: int
    reported_at: datetime
    resolved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


@dataclass
class BackupRecord:
    id: int
    backup_type: str
    status: str
    file_path: str
    size_bytes: int
    labeled_academic: bool
    created_by: int
    created_at: datetime
    completed_at: Optional[datetime]


@dataclass
class RestoreVerification:
    id: int
    backup_record_id: int
    status: str
    verification_notes: str
    verified_by: int
    verified_at: datetime
    created_at: datetime
