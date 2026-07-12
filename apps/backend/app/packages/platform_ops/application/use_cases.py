"""Platform ops use cases — Spec 027."""

from __future__ import annotations

import json
import os
from typing import Any, Optional

import duckdb

from app.core.time_util import utc_now
from app.packages.billing.domain.providers import get_provider
from app.packages.platform_ops.domain.entities import (
    BackgroundJob,
    BackupRecord,
    FeatureFlag,
    JobExecution,
    Notification,
    NotificationDelivery,
    OperationalIncident,
    ProviderConfiguration,
    RestoreVerification,
    WebhookDelivery,
    WebhookEvent,
)
from app.packages.platform_ops.domain.errors import (
    IdempotencyError,
    NotFoundError,
    StateError,
    ValidationError,
)
from app.packages.platform_ops.domain.ports import EmailMessage, NotificationMessage
from app.packages.platform_ops.infrastructure.adapters import (
    get_email_adapter,
    get_notification_adapter,
)


def _next_id(conn: duckdb.DuckDBPyConnection, table: str) -> int:
    return int(conn.execute(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table}").fetchone()[0])


def _now():
    return utc_now()


def _audit(
    conn: duckdb.DuckDBPyConnection,
    *,
    action: str,
    target_type: str,
    target_id: str,
    actor_user_id: Optional[int],
    new_values: Optional[dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> None:
    try:
        from app.packages.organizations.infrastructure.repositories.audit_repository import (
            AuditRepository,
        )
        AuditRepository(conn).append(
            action=action,
            target_type=target_type,
            target_id=target_id,
            source="platform_ops.use_case",
            result="success",
            actor_user_id=actor_user_id,
            organization_id=None,
            new_values=new_values,
            request_id=request_id,
        )
    except Exception:
        pass


def redact_secret(value: Optional[str]) -> Optional[str]:
    """Redact secret values for API responses."""
    if not value:
        return None
    if len(value) <= 4:
        return "****"
    return value[:2] + "****" + value[-2:]


class NotificationUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def send(
        self,
        *,
        actor_user_id: int,
        recipient: str,
        subject: str,
        body: str,
        channel: str = "console",
        request_id: Optional[str] = None,
    ) -> tuple[Notification, NotificationDelivery]:
        now = _now()
        nid = _next_id(self._conn, "app_notification")
        self._conn.execute(
            """
            INSERT INTO app_notification
                (id, channel, recipient, subject, body, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
            """,
            [nid, channel, recipient, subject, body, now, now],
        )
        adapter = get_notification_adapter(channel)
        result = adapter.send(NotificationMessage(
            recipient=recipient, subject=subject, body=body, channel=channel,
        ))
        did = _next_id(self._conn, "app_notification_delivery")
        status = "delivered" if result.success else "failed"
        self._conn.execute(
            """
            INSERT INTO app_notification_delivery
                (id, notification_id, adapter_code, status, labeled_mock,
                 delivered_at, error_message, created_at)
            VALUES (?, ?, ?, ?, ?, ?, NULL, ?)
            """,
            [did, nid, result.adapter_code, status, result.labeled_mock,
             now if result.success else None, now],
        )
        self._conn.execute(
            "UPDATE app_notification SET status = ?, updated_at = ? WHERE id = ?",
            ["sent" if result.success else "failed", now, nid],
        )
        _audit(self._conn, action="notification.sent", target_type="notification",
               target_id=str(nid), actor_user_id=actor_user_id, request_id=request_id)
        n_row = self._conn.execute(
            "SELECT id, channel, recipient, subject, body, status, created_at, updated_at FROM app_notification WHERE id = ?",
            [nid],
        ).fetchone()
        d_row = self._conn.execute(
            """
            SELECT id, notification_id, adapter_code, status, labeled_mock,
                   delivered_at, error_message, created_at
            FROM app_notification_delivery WHERE id = ?
            """,
            [did],
        ).fetchone()
        return Notification(*n_row), NotificationDelivery(*d_row)

    def list(self, *, limit: int = 50, offset: int = 0) -> tuple[list[Notification], int]:
        total = int(self._conn.execute("SELECT COUNT(*) FROM app_notification").fetchone()[0])
        rows = self._conn.execute(
            """
            SELECT id, channel, recipient, subject, body, status, created_at, updated_at
            FROM app_notification ORDER BY created_at DESC LIMIT ? OFFSET ?
            """,
            [limit, offset],
        ).fetchall()
        return [Notification(*r) for r in rows], total


class ProviderConfigUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def list(self) -> list[ProviderConfiguration]:
        rows = self._conn.execute(
            """
            SELECT id, provider_code, display_name, is_mock, secret_ref, status,
                   config_json, created_at, updated_at
            FROM app_provider_configuration ORDER BY provider_code
            """,
        ).fetchall()
        return [ProviderConfiguration(*r) for r in rows]

    def register(
        self,
        *,
        actor_user_id: int,
        provider_code: str,
        display_name: str,
        is_mock: bool = True,
        secret_ref: Optional[str] = None,
        config_json: str = "{}",
        request_id: Optional[str] = None,
    ) -> ProviderConfiguration:
        if secret_ref and not secret_ref.startswith("secret://"):
            raise ValidationError("secret_ref must use secret:// prefix — no raw secrets")
        now = _now()
        pid = _next_id(self._conn, "app_provider_configuration")
        self._conn.execute(
            """
            INSERT INTO app_provider_configuration
                (id, provider_code, display_name, is_mock, secret_ref, status,
                 config_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'active', ?, ?, ?)
            """,
            [pid, provider_code, display_name, is_mock, secret_ref, config_json, now, now],
        )
        _audit(self._conn, action="provider.registered", target_type="provider_configuration",
               target_id=str(pid), actor_user_id=actor_user_id, request_id=request_id)
        return self.get(pid)

    def get(self, config_id: int) -> ProviderConfiguration:
        row = self._conn.execute(
            """
            SELECT id, provider_code, display_name, is_mock, secret_ref, status,
                   config_json, created_at, updated_at
            FROM app_provider_configuration WHERE id = ?
            """,
            [config_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"Provider configuration {config_id} not found")
        return ProviderConfiguration(*row)

    def seed_billing_providers(self, *, actor_user_id: int) -> list[ProviderConfiguration]:
        """Reuse billing PaymentProvider registry — academic mock labeled."""
        results = []
        for code in ("academic_mock", "manual_transfer"):
            try:
                prov = get_provider(code)
                existing = self._conn.execute(
                    "SELECT id FROM app_provider_configuration WHERE provider_code = ?",
                    [code],
                ).fetchone()
                if existing:
                    results.append(self.get(int(existing[0])))
                    continue
                cfg = self.register(
                    actor_user_id=actor_user_id,
                    provider_code=prov.code,
                    display_name=f"Billing provider: {prov.code}",
                    is_mock=prov.is_mock,
                    secret_ref=f"secret://billing/{prov.code}",
                    config_json=json.dumps({"labeled_mock": prov.is_mock}),
                )
                results.append(cfg)
            except ValueError:
                pass
        return results


class WebhookUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def receive(
        self,
        *,
        source: str,
        event_type: str,
        idempotency_key: str,
        payload: dict[str, Any],
        request_id: Optional[str] = None,
    ) -> WebhookEvent:
        existing = self._conn.execute(
            """
            SELECT id, source, event_type, idempotency_key, payload_json, status,
                   received_at, created_at
            FROM app_webhook_event WHERE source = ? AND idempotency_key = ?
            """,
            [source, idempotency_key],
        ).fetchone()
        if existing:
            raise IdempotencyError(f"Duplicate webhook: {source}/{idempotency_key}")

        now = _now()
        eid = _next_id(self._conn, "app_webhook_event")
        self._conn.execute(
            """
            INSERT INTO app_webhook_event
                (id, source, event_type, idempotency_key, payload_json, status,
                 received_at, created_at)
            VALUES (?, ?, ?, ?, ?, 'received', ?, ?)
            """,
            [eid, source, event_type, idempotency_key, json.dumps(payload), now, now],
        )
        _audit(self._conn, action="webhook.received", target_type="webhook_event",
               target_id=str(eid), actor_user_id=None, request_id=request_id)
        row = self._conn.execute(
            """
            SELECT id, source, event_type, idempotency_key, payload_json, status,
                   received_at, created_at
            FROM app_webhook_event WHERE id = ?
            """,
            [eid],
        ).fetchone()
        return WebhookEvent(*row)

    def deliver(
        self,
        event_id: int,
        *,
        target_url: str,
        max_attempts: int = 3,
    ) -> WebhookDelivery:
        event_row = self._conn.execute(
            "SELECT id FROM app_webhook_event WHERE id = ?", [event_id],
        ).fetchone()
        if not event_row:
            raise NotFoundError(f"Webhook event {event_id} not found")

        now = _now()
        did = _next_id(self._conn, "app_webhook_delivery")
        attempt = 1
        status = "delivered"
        response_code = 200
        self._conn.execute(
            """
            INSERT INTO app_webhook_delivery
                (id, webhook_event_id, target_url, status, attempt_count,
                 last_attempt_at, response_code, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [did, event_id, target_url, status, attempt, now, response_code, now, now],
        )
        self._conn.execute(
            "UPDATE app_webhook_event SET status = 'processed' WHERE id = ?",
            [event_id],
        )
        row = self._conn.execute(
            """
            SELECT id, webhook_event_id, target_url, status, attempt_count,
                   last_attempt_at, response_code, created_at, updated_at
            FROM app_webhook_delivery WHERE id = ?
            """,
            [did],
        ).fetchone()
        return WebhookDelivery(*row)

    def list_events(self, *, limit: int = 50, offset: int = 0) -> tuple[list[WebhookEvent], int]:
        total = int(self._conn.execute("SELECT COUNT(*) FROM app_webhook_event").fetchone()[0])
        rows = self._conn.execute(
            """
            SELECT id, source, event_type, idempotency_key, payload_json, status,
                   received_at, created_at
            FROM app_webhook_event ORDER BY received_at DESC LIMIT ? OFFSET ?
            """,
            [limit, offset],
        ).fetchall()
        return [WebhookEvent(*r) for r in rows], total


class JobUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def register(
        self,
        *,
        actor_user_id: int,
        job_code: str,
        display_name: str,
        max_retries: int = 3,
        request_id: Optional[str] = None,
    ) -> BackgroundJob:
        now = _now()
        jid = _next_id(self._conn, "app_background_job")
        self._conn.execute(
            """
            INSERT INTO app_background_job
                (id, job_code, display_name, status, max_retries, created_at, updated_at)
            VALUES (?, ?, ?, 'active', ?, ?, ?)
            """,
            [jid, job_code, display_name, max_retries, now, now],
        )
        _audit(self._conn, action="job.registered", target_type="background_job",
               target_id=str(jid), actor_user_id=actor_user_id, request_id=request_id)
        return self.get(jid)

    def get(self, job_id: int) -> BackgroundJob:
        row = self._conn.execute(
            """
            SELECT id, job_code, display_name, status, max_retries, created_at, updated_at
            FROM app_background_job WHERE id = ?
            """,
            [job_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"Job {job_id} not found")
        return BackgroundJob(*row)

    def execute(
        self,
        job_id: int,
        *,
        actor_user_id: int,
        simulate_failure: bool = False,
        request_id: Optional[str] = None,
    ) -> JobExecution:
        job = self.get(job_id)
        now = _now()
        last_exec = self._conn.execute(
            """
            SELECT attempt_number, status FROM app_job_execution
            WHERE job_id = ? ORDER BY started_at DESC LIMIT 1
            """,
            [job_id],
        ).fetchone()

        attempt = 1
        if last_exec and last_exec[1] == "failed":
            attempt = int(last_exec[0]) + 1

        eid = _next_id(self._conn, "app_job_execution")
        if simulate_failure and attempt < job.max_retries:
            status = "failed"
            dead_letter = False
            error = "Simulated failure for retry testing"
            result_json = None
        elif simulate_failure and attempt >= job.max_retries:
            status = "dead_letter"
            dead_letter = True
            error = "Max retries exceeded — conceptual dead-letter"
            result_json = None
        else:
            status = "completed"
            dead_letter = False
            error = None
            result_json = json.dumps({"status": "ok", "labeled_academic": True})

        self._conn.execute(
            """
            INSERT INTO app_job_execution
                (id, job_id, status, attempt_number, result_json, error_message,
                 dead_letter, started_at, finished_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [eid, job_id, status, attempt, result_json, error,
             dead_letter, now, now, now],
        )
        _audit(self._conn, action="job.executed", target_type="job_execution",
               target_id=str(eid), actor_user_id=actor_user_id, request_id=request_id)
        row = self._conn.execute(
            """
            SELECT id, job_id, status, attempt_number, result_json, error_message,
                   dead_letter, started_at, finished_at, created_at
            FROM app_job_execution WHERE id = ?
            """,
            [eid],
        ).fetchone()
        return JobExecution(*row)

    def list(self) -> list[BackgroundJob]:
        rows = self._conn.execute(
            """
            SELECT id, job_code, display_name, status, max_retries, created_at, updated_at
            FROM app_background_job ORDER BY job_code
            """,
        ).fetchall()
        return [BackgroundJob(*r) for r in rows]

    def list_executions(self, job_id: int) -> list[JobExecution]:
        rows = self._conn.execute(
            """
            SELECT id, job_id, status, attempt_number, result_json, error_message,
                   dead_letter, started_at, finished_at, created_at
            FROM app_job_execution WHERE job_id = ? ORDER BY started_at DESC
            """,
            [job_id],
        ).fetchall()
        return [JobExecution(*r) for r in rows]


class FeatureFlagUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def list(self, *, environment: Optional[str] = None) -> list[FeatureFlag]:
        if environment:
            rows = self._conn.execute(
                """
                SELECT id, flag_key, description, enabled, environment, created_at, updated_at
                FROM app_feature_flag WHERE environment = ? ORDER BY flag_key
                """,
                [environment],
            ).fetchall()
        else:
            rows = self._conn.execute(
                """
                SELECT id, flag_key, description, enabled, environment, created_at, updated_at
                FROM app_feature_flag ORDER BY flag_key
                """,
            ).fetchall()
        return [FeatureFlag(*r) for r in rows]

    def upsert(
        self,
        *,
        actor_user_id: int,
        flag_key: str,
        description: str,
        enabled: bool,
        environment: str = "development",
        request_id: Optional[str] = None,
    ) -> FeatureFlag:
        now = _now()
        existing = self._conn.execute(
            "SELECT id FROM app_feature_flag WHERE flag_key = ? AND environment = ?",
            [flag_key, environment],
        ).fetchone()
        if existing:
            fid = int(existing[0])
            self._conn.execute(
                "UPDATE app_feature_flag SET description = ?, enabled = ?, updated_at = ? WHERE id = ?",
                [description, enabled, now, fid],
            )
        else:
            fid = _next_id(self._conn, "app_feature_flag")
            self._conn.execute(
                """
                INSERT INTO app_feature_flag
                    (id, flag_key, description, enabled, environment, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [fid, flag_key, description, enabled, environment, now, now],
            )
        _audit(self._conn, action="feature_flag.upserted", target_type="feature_flag",
               target_id=str(fid), actor_user_id=actor_user_id, request_id=request_id)
        row = self._conn.execute(
            """
            SELECT id, flag_key, description, enabled, environment, created_at, updated_at
            FROM app_feature_flag WHERE id = ?
            """,
            [fid],
        ).fetchone()
        return FeatureFlag(*row)


class HealthUseCases:
    def get_health(self) -> dict[str, Any]:
        return {
            "status": "healthy",
            "labeled_academic": True,
            "message": "Conceptual health check — not production HA monitoring",
            "components": {
                "database": "ok",
                "jobs_scheduler": "ok",
                "notifications": "console_adapter",
                "email": "mock_labeled",
            },
        }

    def get_metrics(self) -> dict[str, Any]:
        return {
            "labeled_academic": True,
            "message": "Technical metrics snapshot — academic/local only",
            "uptime_seconds": 0,
            "request_count": 0,
        }


class BackupUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def create_backup(
        self,
        *,
        actor_user_id: int,
        backup_type: str = "conceptual",
        request_id: Optional[str] = None,
    ) -> BackupRecord:
        now = _now()
        bid = _next_id(self._conn, "app_backup_record")
        file_path = f"backups/academic/{now.strftime('%Y%m%d_%H%M%S')}.duckdb.bak"
        self._conn.execute(
            """
            INSERT INTO app_backup_record
                (id, backup_type, status, file_path, size_bytes, labeled_academic,
                 created_by, created_at, completed_at)
            VALUES (?, ?, 'completed', ?, 0, TRUE, ?, ?, ?)
            """,
            [bid, backup_type, file_path, actor_user_id, now, now],
        )
        _audit(self._conn, action="backup.created", target_type="backup_record",
               target_id=str(bid), actor_user_id=actor_user_id, request_id=request_id)
        row = self._conn.execute(
            """
            SELECT id, backup_type, status, file_path, size_bytes, labeled_academic,
                   created_by, created_at, completed_at
            FROM app_backup_record WHERE id = ?
            """,
            [bid],
        ).fetchone()
        return BackupRecord(*row)

    def verify_restore(
        self,
        backup_id: int,
        *,
        actor_user_id: int,
        notes: str = "Academic restore verification — not production DR",
        request_id: Optional[str] = None,
    ) -> RestoreVerification:
        backup_row = self._conn.execute(
            "SELECT id FROM app_backup_record WHERE id = ?", [backup_id],
        ).fetchone()
        if not backup_row:
            raise NotFoundError(f"Backup {backup_id} not found")
        now = _now()
        vid = _next_id(self._conn, "app_restore_verification")
        self._conn.execute(
            """
            INSERT INTO app_restore_verification
                (id, backup_record_id, status, verification_notes, verified_by,
                 verified_at, created_at)
            VALUES (?, ?, 'passed', ?, ?, ?, ?)
            """,
            [vid, backup_id, notes, actor_user_id, now, now],
        )
        _audit(self._conn, action="backup.verified", target_type="restore_verification",
               target_id=str(vid), actor_user_id=actor_user_id, request_id=request_id)
        row = self._conn.execute(
            """
            SELECT id, backup_record_id, status, verification_notes, verified_by,
                   verified_at, created_at
            FROM app_restore_verification WHERE id = ?
            """,
            [vid],
        ).fetchone()
        return RestoreVerification(*row)

    def list_backups(self) -> list[BackupRecord]:
        rows = self._conn.execute(
            """
            SELECT id, backup_type, status, file_path, size_bytes, labeled_academic,
                   created_by, created_at, completed_at
            FROM app_backup_record ORDER BY created_at DESC
            """,
        ).fetchall()
        return [BackupRecord(*r) for r in rows]


class OperationalIncidentUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def create(
        self,
        *,
        actor_user_id: int,
        title: str,
        severity: str,
        description: str,
        request_id: Optional[str] = None,
    ) -> OperationalIncident:
        now = _now()
        iid = _next_id(self._conn, "app_operational_incident")
        self._conn.execute(
            """
            INSERT INTO app_operational_incident
                (id, title, severity, status, description, reported_by,
                 reported_at, resolved_at, created_at, updated_at)
            VALUES (?, ?, ?, 'open', ?, ?, ?, NULL, ?, ?)
            """,
            [iid, title, severity, description, actor_user_id, now, now, now],
        )
        _audit(self._conn, action="ops_incident.created", target_type="operational_incident",
               target_id=str(iid), actor_user_id=actor_user_id, request_id=request_id)
        return self.get(iid)

    def get(self, incident_id: int) -> OperationalIncident:
        row = self._conn.execute(
            """
            SELECT id, title, severity, status, description, reported_by,
                   reported_at, resolved_at, created_at, updated_at
            FROM app_operational_incident WHERE id = ?
            """,
            [incident_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"Operational incident {incident_id} not found")
        return OperationalIncident(*row)

    def list(self) -> list[OperationalIncident]:
        rows = self._conn.execute(
            """
            SELECT id, title, severity, status, description, reported_by,
                   reported_at, resolved_at, created_at, updated_at
            FROM app_operational_incident ORDER BY reported_at DESC
            """,
        ).fetchall()
        return [OperationalIncident(*r) for r in rows]


class EmailUseCases:
    def send_mock_email(
        self,
        *,
        actor_user_id: int,
        to_address: str,
        subject: str,
        body: str,
        request_id: Optional[str] = None,
    ) -> dict[str, Any]:
        adapter = get_email_adapter()
        result = adapter.send(EmailMessage(to_address=to_address, subject=subject, body=body))
        _audit(self._conn, action="email.mock_sent", target_type="email",
               target_id=to_address, actor_user_id=actor_user_id, request_id=request_id)
        return {
            "success": result.success,
            "labeled_mock": result.labeled_mock,
            "message": result.message,
        }

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn
