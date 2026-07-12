"""Email delivery log + transactional send helper — Spec 027."""

from __future__ import annotations

import logging
from typing import Optional

import duckdb

from app.core.time_util import utc_now
from app.packages.platform_ops.application.email_templates import RenderedEmail
from app.packages.platform_ops.domain.ports import EmailMessage, EmailResult
from app.packages.platform_ops.infrastructure.email_providers import get_configured_email_port

logger = logging.getLogger("voxmetrik.email.service")


def ensure_email_delivery_table(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS app_email_delivery (
            id                   INTEGER PRIMARY KEY,
            template_code        VARCHAR NOT NULL,
            to_address           VARCHAR NOT NULL,
            subject              VARCHAR NOT NULL,
            provider_code        VARCHAR NOT NULL,
            status               VARCHAR NOT NULL,
            provider_message_id  VARCHAR,
            error_sanitized      VARCHAR,
            organization_id      INTEGER,
            related_type         VARCHAR,
            related_id           VARCHAR,
            idempotency_key      VARCHAR,
            labeled_mock         BOOLEAN NOT NULL DEFAULT TRUE,
            created_at           TIMESTAMP NOT NULL
        )
        """
    )
    # Additive column for DBs created before idempotency_key existed
    try:
        cols = {
            str(r[0]).lower()
            for r in conn.execute(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'app_email_delivery'
                """
            ).fetchall()
        }
    except Exception:  # noqa: BLE001
        cols = set()
    if cols and "idempotency_key" not in cols:
        try:
            conn.execute("ALTER TABLE app_email_delivery ADD COLUMN idempotency_key VARCHAR")
        except Exception:  # noqa: BLE001 — race / already added
            pass
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_email_delivery_to ON app_email_delivery(to_address)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_email_delivery_idem ON app_email_delivery(idempotency_key)"
    )


def build_email_idempotency_key(
    *,
    template_code: str,
    to_address: str,
    related_type: Optional[str] = None,
    related_id: Optional[str] = None,
) -> str:
    """Idempotency = email type + recipient + event identity."""
    return "|".join(
        [
            (template_code or "").strip().lower(),
            (to_address or "").strip().lower(),
            (related_type or "").strip().lower(),
            (related_id or "").strip(),
        ]
    )


def _next_id(conn: duckdb.DuckDBPyConnection) -> int:
    return int(conn.execute("SELECT COALESCE(MAX(id),0)+1 FROM app_email_delivery").fetchone()[0])


def _find_delivered(
    conn: duckdb.DuckDBPyConnection, idempotency_key: str
) -> Optional[EmailResult]:
    row = conn.execute(
        """
        SELECT provider_code, provider_message_id, labeled_mock, status
        FROM app_email_delivery
        WHERE idempotency_key = ? AND status IN ('sent', 'console')
        ORDER BY id DESC LIMIT 1
        """,
        [idempotency_key],
    ).fetchone()
    if not row:
        return None
    return EmailResult(
        success=True,
        provider_code=str(row[0]),
        labeled_mock=bool(row[2]),
        message="idempotent_skip: already delivered",
        provider_message_id=row[1],
    )


def _log_delivery(
    conn: Optional[duckdb.DuckDBPyConnection],
    *,
    rendered: RenderedEmail,
    to_address: str,
    result: EmailResult,
    organization_id: Optional[int] = None,
    related_type: Optional[str] = None,
    related_id: Optional[str] = None,
    idempotency_key: Optional[str] = None,
) -> None:
    if conn is None:
        return
    try:
        ensure_email_delivery_table(conn)
        status = "sent" if result.success else "failed"
        if result.labeled_mock and result.success:
            status = "console"
        if result.message.startswith("idempotent_skip"):
            # Do not insert a second successful row for the same key
            return
        conn.execute(
            """
            INSERT INTO app_email_delivery
                (id, template_code, to_address, subject, provider_code, status,
                 provider_message_id, error_sanitized, organization_id, related_type,
                 related_id, idempotency_key, labeled_mock, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                _next_id(conn),
                rendered.template_code,
                to_address.lower(),
                rendered.subject,
                result.provider_code,
                status,
                result.provider_message_id,
                result.error_sanitized,
                organization_id,
                related_type,
                related_id,
                idempotency_key,
                bool(result.labeled_mock),
                utc_now(),
            ],
        )
    except Exception as exc:  # noqa: BLE001 — delivery log must not break business flow
        logger.warning("[email] delivery log skipped: %s", exc.__class__.__name__)


def send_rendered_email(
    *,
    to_address: str,
    rendered: RenderedEmail,
    conn: Optional[duckdb.DuckDBPyConnection] = None,
    organization_id: Optional[int] = None,
    related_type: Optional[str] = None,
    related_id: Optional[str] = None,
    idempotency_key: Optional[str] = None,
    max_retries: int = 1,
) -> EmailResult:
    """Send via configured provider. Never raises on SMTP failure.

    Skips re-send when the same event+recipient+template was already delivered.
    Never logs secrets / codes / API keys.
    """
    to_norm = to_address.strip().lower()
    key = idempotency_key or build_email_idempotency_key(
        template_code=rendered.template_code,
        to_address=to_norm,
        related_type=related_type,
        related_id=related_id,
    )
    if conn is not None:
        try:
            ensure_email_delivery_table(conn)
            prior = _find_delivered(conn, key)
            if prior is not None:
                logger.info(
                    "[email] skip duplicate template=%s to=%s",
                    rendered.template_code,
                    to_norm,
                )
                return prior
        except Exception as exc:  # noqa: BLE001
            logger.warning("[email] idempotency check skipped: %s", exc.__class__.__name__)

    port = get_configured_email_port()
    message = EmailMessage(
        to_address=to_norm,
        subject=rendered.subject,
        body_text=rendered.body_text,
        body_html=rendered.body_html,
        template_code=rendered.template_code,
        organization_id=organization_id,
        related_type=related_type,
        related_id=related_id,
    )
    result: Optional[EmailResult] = None
    attempts = max(1, max_retries + 1)
    for i in range(attempts):
        result = port.send(message)
        if result.success:
            break
        if i < attempts - 1:
            logger.info(
                "[email] retry %s/%s template=%s",
                i + 1,
                attempts - 1,
                rendered.template_code,
            )
    assert result is not None
    _log_delivery(
        conn,
        rendered=rendered,
        to_address=to_norm,
        result=result,
        organization_id=organization_id,
        related_type=related_type,
        related_id=related_id,
        idempotency_key=key,
    )
    return result
