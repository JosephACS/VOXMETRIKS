"""Transactional email templates (HTML + text). User content is escaped.

Bilingual ES/EN. Preference order: caller locale → Spanish fallback.
No real sends from this module.
"""

from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Literal, Optional

EMAIL_BRAND = "VOXMETRIKS"
EmailLocale = Literal["es", "en"]


def _brand() -> str:
    return EMAIL_BRAND


def _esc(value: object) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def normalize_email_locale(locale: Optional[str]) -> EmailLocale:
    if locale and str(locale).lower().startswith("en"):
        return "en"
    return "es"


@dataclass(frozen=True)
class RenderedEmail:
    subject: str
    body_text: str
    body_html: str
    template_code: str


def _shell(
    title: str,
    paragraphs: list[str],
    cta_label: Optional[str] = None,
    cta_url: Optional[str] = None,
    *,
    locale: EmailLocale = "es",
) -> tuple[str, str]:
    brand = _brand()
    text_parts = [title, ""] + paragraphs
    if cta_label and cta_url:
        text_parts += ["", f"{cta_label}: {cta_url}"]
    text_parts += ["", f"— {brand}"]
    body_text = "\n".join(text_parts)

    paras_html = "".join(f"<p style='color:#444;line-height:1.5'>{_esc(p)}</p>" for p in paragraphs)
    cta_html = ""
    if cta_label and cta_url:
        open_label = "Or open:" if locale == "en" else "O abre:"
        cta_html = (
            f"<p style='margin:24px 0'><a href='{_esc(cta_url)}' "
            f"style='background:#111;color:#fff;padding:12px 18px;border-radius:6px;"
            f"text-decoration:none;display:inline-block'>{_esc(cta_label)}</a></p>"
            f"<p style='color:#888;font-size:12px'>{open_label} {_esc(cta_url)}</p>"
        )
    footer = (
        f"{brand} · academic / enterprise notifications"
        if locale == "en"
        else f"{brand} · notificaciones académicas / empresariales"
    )
    body_html = f"""
    <div style="font-family:system-ui,Segoe UI,Roboto,sans-serif;max-width:480px;margin:auto;padding:24px">
      <h2 style="margin:0 0 8px">{_esc(brand)}</h2>
      <h3 style="margin:0 0 16px;font-weight:600">{_esc(title)}</h3>
      {paras_html}
      {cta_html}
      <p style="color:#aaa;font-size:12px;margin-top:32px">{_esc(footer)}</p>
    </div>
    """
    return body_text, body_html


def verification_code_email(
    *,
    to_name: Optional[str],
    code: str,
    expires_min: int,
    locale: Optional[str] = None,
) -> RenderedEmail:
    brand = _brand()
    loc = normalize_email_locale(locale)
    hello = f"Hello{(' ' + to_name) if to_name else ''}," if loc == "en" else f"Hola{(' ' + to_name) if to_name else ''},"
    if loc == "en":
        title = "Verify your email"
        code_line = f"Your verification code is: {code}"
        paras = [
            hello,
            code_line,
            f"Expires in {expires_min} minutes.",
            "If you did not create this account, ignore this email.",
        ]
        subject = f"{brand} · Verification code"
    else:
        title = "Verifica tu correo"
        code_line = f"Tu código de verificación es: {code}"
        paras = [
            hello,
            code_line,
            f"Expira en {expires_min} minutos.",
            "Si no creaste esta cuenta, ignora este correo.",
        ]
        subject = f"{brand} · Código de verificación"
    text, html_body = _shell(title, paras, locale=loc)
    html_body = html_body.replace(
        _esc(code_line),
        (
            f"Your verification code:<br/><span style='font-size:28px;font-weight:700;letter-spacing:6px'>{_esc(code)}</span>"
            if loc == "en"
            else f"Tu código de verificación:<br/><span style='font-size:28px;font-weight:700;letter-spacing:6px'>{_esc(code)}</span>"
        ),
    )
    return RenderedEmail(
        subject=subject,
        body_text=text,
        body_html=html_body,
        template_code="auth.verification_code",
    )


def password_reset_email(
    *,
    code: str,
    expires_min: int,
    reset_url: Optional[str] = None,
    locale: Optional[str] = None,
) -> RenderedEmail:
    brand = _brand()
    loc = normalize_email_locale(locale)
    if loc == "en":
        title = "Password recovery"
        paras = [
            "We received a request to reset your password.",
            f"One-time code: {code}",
            f"Expires in {expires_min} minutes.",
            "If you did not request this change, ignore this email.",
        ]
        cta = "Reset password"
        subject = f"{brand} · Password recovery"
    else:
        title = "Recuperación de contraseña"
        paras = [
            "Recibimos una solicitud para restablecer tu contraseña.",
            f"Código de un solo uso: {code}",
            f"Expira en {expires_min} minutos.",
            "Si no solicitaste este cambio, ignora este correo.",
        ]
        cta = "Restablecer"
        subject = f"{brand} · Recuperación de contraseña"
    text, html_body = _shell(title, paras, cta, reset_url, locale=loc)
    return RenderedEmail(
        subject=subject,
        body_text=text,
        body_html=html_body,
        template_code="auth.password_reset",
    )


def organization_invitation_email(
    *,
    org_name: str,
    inviter_name: str,
    role_name: str,
    invite_url: Optional[str],
    expires_label: str,
    locale: Optional[str] = None,
) -> RenderedEmail:
    brand = _brand()
    loc = normalize_email_locale(locale)
    if loc == "en":
        title = "Organization invitation"
        paras = [
            f"{inviter_name} invited you to join «{org_name}».",
            f"Initial role: {role_name}",
            f"Invitation expires: {expires_label}",
        ]
        cta = "Accept invitation"
        subject = f"{brand} · Invitation to {org_name}"
    else:
        title = "Invitación a organización"
        paras = [
            f"{inviter_name} te invitó a unirte a «{org_name}».",
            f"Rol inicial: {role_name}",
            f"La invitación expira: {expires_label}",
        ]
        cta = "Aceptar invitación"
        subject = f"{brand} · Invitación a {org_name}"
    text, html_body = _shell(title, paras, cta, invite_url, locale=loc)
    return RenderedEmail(
        subject=subject,
        body_text=text,
        body_html=html_body,
        template_code="org.invitation",
    )


def billing_event_email(
    *,
    template_code: str,
    subject: str,
    title: str,
    paragraphs: list[str],
    action_url: Optional[str] = None,
    locale: Optional[str] = None,
) -> RenderedEmail:
    brand = _brand()
    loc = normalize_email_locale(locale)
    cta = "View billing" if loc == "en" else "Ver facturación"
    text, html_body = _shell(title, paragraphs, cta if action_url else None, action_url, locale=loc)
    return RenderedEmail(
        subject=f"{brand} · {subject}",
        body_text=text,
        body_html=html_body,
        template_code=template_code,
    )


def support_event_email(
    *,
    template_code: str,
    subject: str,
    title: str,
    paragraphs: list[str],
    locale: Optional[str] = None,
) -> RenderedEmail:
    brand = _brand()
    loc = normalize_email_locale(locale)
    text, html_body = _shell(title, paragraphs, locale=loc)
    return RenderedEmail(
        subject=f"{brand} · {subject}",
        body_text=text,
        body_html=html_body,
        template_code=template_code,
    )


def report_ready_email(
    *,
    report_title: str,
    report_url: Optional[str] = None,
    locale: Optional[str] = None,
) -> RenderedEmail:
    brand = _brand()
    loc = normalize_email_locale(locale)
    if loc == "en":
        title = "Executive report ready"
        paras = [f"The report «{report_title}» is ready for review."]
        cta = "Open report"
        subject = f"{brand} · Report ready: {report_title}"
    else:
        title = "Reporte ejecutivo listo"
        paras = [f"El reporte «{report_title}» está listo para revisión."]
        cta = "Abrir reporte"
        subject = f"{brand} · Reporte listo: {report_title}"
    text, html_body = _shell(title, paras, cta, report_url, locale=loc)
    return RenderedEmail(
        subject=subject,
        body_text=text,
        body_html=html_body,
        template_code="reporting.ready",
    )
