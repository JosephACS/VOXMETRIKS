"""Presentation + idempotency guards for transactional email (console only)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import duckdb
import pytest

from app.core import schema_bootstrap
from app.core.config import get_settings
from app.core.money_format import format_due_date, format_money
from app.packages.platform_ops.application.email_service import (
    build_email_idempotency_key,
    ensure_email_delivery_table,
    send_rendered_email,
)
from app.packages.platform_ops.application.email_templates import (
    EMAIL_BRAND,
    billing_event_email,
    verification_code_email,
)
from app.packages.platform_ops.infrastructure.email_providers import get_email_adapter


@pytest.fixture(autouse=True)
def _force_console(monkeypatch):
    monkeypatch.setenv("EMAIL_PROVIDER", "console")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture()
def conn(tmp_path: Path):
    previous = schema_bootstrap.schema_ready()
    schema_bootstrap._schema_ready = False
    db = duckdb.connect(str(tmp_path / "email_fmt.duckdb"))
    ensure_email_delivery_table(db)
    yield db
    db.close()
    schema_bootstrap._schema_ready = previous


def test_format_money_two_decimals():
    assert format_money(Decimal("100.0000"), "USD") == "$100.00 USD"
    assert format_money("99.0000", "USD") == "$99.00 USD"
    assert format_money(10.5, "eur") == "$10.50 EUR"
    assert format_money(0, "USD") == "$0.00 USD"


def test_format_due_date_null_and_value():
    assert format_due_date(None) == "Sin fecha de vencimiento definida"
    assert format_due_date(date(2026, 7, 15)) == "2026-07-15"


def test_brand_is_voxmetriks():
    assert EMAIL_BRAND == "VOXMETRIKS"
    rendered = verification_code_email(to_name="Ada", code="123456", expires_min=15)
    assert rendered.subject.startswith("VOXMETRIKS")
    assert "VOXMETRIKS" in rendered.body_text
    assert "VOXMETRIKS" in rendered.body_html
    billing = billing_event_email(
        template_code="billing.invoice_issued",
        subject="Factura emitida",
        title="Factura emitida",
        paragraphs=[
            f"Total: {format_money(Decimal('100.0000'), 'USD')}",
            f"Vence: {format_due_date(None)}",
        ],
    )
    assert "VOXMETRIKS" in billing.subject
    assert "$100.00 USD" in billing.body_text
    assert "Sin fecha de vencimiento definida" in billing.body_text
    assert "N/A" not in billing.body_text


def test_pytest_always_console_adapter():
    adapter = get_email_adapter()
    assert adapter.code == "console"
    # Even if code smtp requested under pytest? Explicit code still allowed for smoke,
    # but default resolution must be console in tests.
    assert get_settings().email_is_console is True
    assert get_settings().is_test_runtime is True


def test_idempotent_email_not_resent(conn):
    rendered = billing_event_email(
        template_code="billing.payment_confirmed",
        subject="Pago",
        title="Pago",
        paragraphs=[f"Monto: {format_money('99.0000', 'USD')}"],
    )
    key = build_email_idempotency_key(
        template_code=rendered.template_code,
        to_address="billing@example.com",
        related_type="payment_attempt",
        related_id="42",
    )
    r1 = send_rendered_email(
        to_address="billing@example.com",
        rendered=rendered,
        conn=conn,
        related_type="payment_attempt",
        related_id="42",
        idempotency_key=key,
    )
    r2 = send_rendered_email(
        to_address="billing@example.com",
        rendered=rendered,
        conn=conn,
        related_type="payment_attempt",
        related_id="42",
        idempotency_key=key,
    )
    assert r1.success is True
    assert r2.success is True
    assert r2.message.startswith("idempotent_skip")
    count = conn.execute(
        "SELECT COUNT(*) FROM app_email_delivery WHERE idempotency_key = ?",
        [key],
    ).fetchone()[0]
    assert int(count) == 1


def test_smoke_script_requires_send_flag():
    import importlib.util

    path = Path(__file__).resolve().parents[1] / "scripts" / "email_smtp_smoke.py"
    spec = importlib.util.spec_from_file_location("email_smtp_smoke_mod", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.main([]) == 2
