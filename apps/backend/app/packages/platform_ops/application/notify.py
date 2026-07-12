"""Best-effort transactional notifications — never raise into business flows."""

from __future__ import annotations

import logging
from typing import Optional

import duckdb

from app.core.config import get_settings
from app.packages.platform_ops.application.email_service import send_rendered_email
from app.packages.platform_ops.application.email_templates import (
    billing_event_email,
    organization_invitation_email,
    report_ready_email,
    support_event_email,
)
from app.packages.platform_ops.domain.ports import EmailResult

logger = logging.getLogger("voxmetrik.email.notify")


def _delivery_status(result: EmailResult) -> str:
    if result.message.startswith("idempotent_skip"):
        if result.labeled_mock:
            return "console"
        return "sent"
    if result.success and result.labeled_mock:
        return "console"
    if result.success:
        return "sent"
    return "failed"


def _frontend_base() -> str:
    return get_settings().resolved_frontend_base_url


def _org_billing_url() -> Optional[str]:
    base = _frontend_base()
    return f"{base}/billing/invoices" if base else None


def _user_email(conn: duckdb.DuckDBPyConnection, user_id: Optional[int]) -> Optional[str]:
    if not user_id:
        return None
    row = conn.execute(
        "SELECT email FROM app_user WHERE id = ?", [user_id]
    ).fetchone()
    return str(row[0]).strip().lower() if row and row[0] else None


def notify_organization_invitation(
    conn: duckdb.DuckDBPyConnection,
    *,
    to_email: str,
    org_name: str,
    inviter_name: str,
    role_name: str,
    invite_token: str,
    expires_label: str,
    organization_id: int,
    invitation_id: int,
    locale: Optional[str] = None,
) -> str:
    base = _frontend_base()
    invite_url = (
        f"{base}/organizations/accept-invite?token={invite_token}" if base else None
    )
    rendered = organization_invitation_email(
        org_name=org_name,
        inviter_name=inviter_name,
        role_name=role_name,
        invite_url=invite_url,
        expires_label=expires_label,
        locale=locale or "es",
    )
    try:
        result = send_rendered_email(
            to_address=to_email,
            rendered=rendered,
            conn=conn,
            organization_id=organization_id,
            related_type="organization_invitation",
            related_id=str(invitation_id),
        )
        return _delivery_status(result)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[email] invitation notify skipped: %s", exc.__class__.__name__)
        return "failed"


def notify_billing(
    conn: duckdb.DuckDBPyConnection,
    *,
    to_email: Optional[str],
    organization_id: int,
    template_code: str,
    subject: str,
    title: str,
    paragraphs: list[str],
    related_type: str,
    related_id: str,
    locale: Optional[str] = None,
) -> None:
    if not to_email:
        return
    rendered = billing_event_email(
        template_code=template_code,
        subject=subject,
        title=title,
        paragraphs=paragraphs,
        action_url=_org_billing_url(),
        locale=locale or "es",
    )
    try:
        send_rendered_email(
            to_address=to_email,
            rendered=rendered,
            conn=conn,
            organization_id=organization_id,
            related_type=related_type,
            related_id=related_id,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("[email] billing notify skipped: %s", exc.__class__.__name__)


def notify_support(
    conn: duckdb.DuckDBPyConnection,
    *,
    to_email: Optional[str],
    organization_id: int,
    template_code: str,
    subject: str,
    title: str,
    paragraphs: list[str],
    related_id: str,
    locale: Optional[str] = None,
) -> None:
    if not to_email:
        return
    rendered = support_event_email(
        template_code=template_code,
        subject=subject,
        title=title,
        paragraphs=paragraphs,
        locale=locale or "es",
    )
    try:
        send_rendered_email(
            to_address=to_email,
            rendered=rendered,
            conn=conn,
            organization_id=organization_id,
            related_type="support_case",
            related_id=related_id,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("[email] support notify skipped: %s", exc.__class__.__name__)


def notify_report_ready(
    conn: duckdb.DuckDBPyConnection,
    *,
    to_email: Optional[str],
    organization_id: int,
    report_title: str,
    report_id: int,
    locale: Optional[str] = None,
) -> None:
    if not to_email:
        return
    base = _frontend_base()
    url = f"{base}/reporting/reports/{report_id}" if base else None
    rendered = report_ready_email(
        report_title=report_title,
        report_url=url,
        locale=locale or "es",
    )
    try:
        send_rendered_email(
            to_address=to_email,
            rendered=rendered,
            conn=conn,
            organization_id=organization_id,
            related_type="executive_report",
            related_id=str(report_id),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("[email] report notify skipped: %s", exc.__class__.__name__)


def billing_contact_email(
    conn: duckdb.DuckDBPyConnection, organization_id: int
) -> Optional[str]:
    """Prefer billing profile email, else first active org member."""
    try:
        row = conn.execute(
            "SELECT email FROM app_billing_profile WHERE organization_id = ?",
            [organization_id],
        ).fetchone()
        if row and row[0]:
            return str(row[0]).strip().lower()
    except Exception:  # noqa: BLE001 — table may be missing in some fixtures
        pass
    try:
        row = conn.execute(
            """
            SELECT u.email FROM app_organization_member m
            JOIN app_user u ON u.id = m.user_id
            WHERE m.organization_id = ? AND m.status = 'active'
            ORDER BY m.id ASC LIMIT 1
            """,
            [organization_id],
        ).fetchone()
        if row and row[0]:
            return str(row[0]).strip().lower()
    except Exception:  # noqa: BLE001
        pass
    return None


# Re-export helper used by support/report wiring
user_email = _user_email
