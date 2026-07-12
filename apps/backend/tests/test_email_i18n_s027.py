"""Unit tests for bilingual email templates (no real sends)."""

from app.packages.platform_ops.application.email_templates import (
    normalize_email_locale,
    password_reset_email,
    report_ready_email,
    verification_code_email,
)


def test_normalize_locale_defaults_to_es():
    assert normalize_email_locale(None) == "es"
    assert normalize_email_locale("fr") == "es"
    assert normalize_email_locale("en") == "en"
    assert normalize_email_locale("en-US") == "en"


def test_verification_email_es_and_en():
    es = verification_code_email(to_name="Ada", code="123456", expires_min=15, locale="es")
    en = verification_code_email(to_name="Ada", code="123456", expires_min=15, locale="en")
    assert "Verifica" in es.subject or "verificación" in es.subject.lower()
    assert "Verification" in en.subject
    assert "123456" in es.body_text and "123456" in en.body_text
    assert es.template_code == en.template_code == "auth.verification_code"


def test_password_reset_bilingual():
    es = password_reset_email(code="ABCDEF12", expires_min=30, locale="es")
    en = password_reset_email(code="ABCDEF12", expires_min=30, locale="en")
    assert "contraseña" in es.subject.lower() or "Recuperación" in es.subject
    assert "Password" in en.subject
    assert "ABCDEF12" in es.body_text


def test_report_ready_bilingual():
    es = report_ready_email(report_title="Q1", locale="es")
    en = report_ready_email(report_title="Q1", locale="en")
    assert "Reporte" in es.subject or "listo" in es.subject.lower()
    assert "Report" in en.subject
