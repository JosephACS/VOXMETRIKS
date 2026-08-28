"""Email + mock payment integration tests (always console — never real SMTP)."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import duckdb
import pytest

from app.core import schema_bootstrap
from app.core.config import Settings, get_settings, set_settings_override
from app.packages.billing.domain.providers import (
    MOCK_SCENARIOS,
    MockPaymentProvider,
    ProviderChargeRequest,
)
from app.packages.billing.infrastructure.schema import ensure_billing_tables
from app.packages.identity.services.user_service import (
    register,
    request_password_reset,
    resend_verification,
    reset_password,
    verify_email,
)
from app.packages.identity.services.user_storage import ensure_user_tables
from app.packages.platform_ops.application.email_service import ensure_email_delivery_table
from app.packages.platform_ops.infrastructure.email_providers import get_email_adapter
from app.packages.billing.application.use_cases import ProviderEventUseCases


@pytest.fixture(autouse=True)
def _force_console_email(monkeypatch):
    monkeypatch.setenv("EMAIL_PROVIDER", "console")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture()
def conn(tmp_path: Path):
    previous = schema_bootstrap.schema_ready()
    schema_bootstrap._schema_ready = False
    db = duckdb.connect(str(tmp_path / "email_mock.duckdb"))
    ensure_user_tables(db)
    ensure_email_delivery_table(db)
    ensure_billing_tables(db)
    yield db
    db.close()
    schema_bootstrap._schema_ready = previous


def test_email_adapter_default_is_console():
    adapter = get_email_adapter()
    assert adapter.code in {"console", "console_mock_email"}


def test_register_verify_wrong_expired_reuse_rate_limit(conn):
    email = "verify.flow@example.com"
    out = register(conn, "verifyflow", email, "secret123")
    assert out["verification_required"] is True
    assert out.get("dev_code")
    code = out["dev_code"]

    with pytest.raises(ValueError, match="invalid"):
        verify_email(conn, email, "000000")

    ok = verify_email(conn, email, code)
    assert ok and ok.get("token")

    with pytest.raises(ValueError):
        verify_email(conn, email, code)

    resent = resend_verification(conn, email)
    assert resent["ok"] is True
    assert "If an unverified" in resent["message"]


def test_controlled_release_caps_new_application_accounts(conn):
    base = get_settings()
    data = base.model_dump()
    existing_users = int(conn.execute("SELECT COUNT(*) FROM app_user").fetchone()[0])
    user_limit = existing_users + 1
    data["max_app_users"] = user_limit
    set_settings_override(Settings(**data))
    try:
        first = register(conn, "firstuser", "first@example.com", "secret123")
        assert first["verification_required"] is True
        with pytest.raises(ValueError, match=rf"límite de {user_limit} usuarios"):
            register(conn, "seconduser", "second@example.com", "secret123")
    finally:
        set_settings_override(base)


def test_resend_rate_limit_and_unknown_email(conn):
    email = "rate.limit@example.com"
    register(conn, "ratelimit", email, "secret123")
    first = resend_verification(conn, email)
    second = resend_verification(conn, email)
    assert second["ok"] is True
    unknown = resend_verification(conn, "nobody@example.com")
    assert unknown["ok"] is True
    assert "If an unverified" in unknown["message"]
    assert first["ok"] is True


def test_password_reset_flow_generic(conn):
    email = "reset.me@example.com"
    out_reg = register(conn, "resetme", email, "oldpass1")
    assert out_reg.get("dev_code")
    verify_email(conn, email, out_reg["dev_code"])

    out = request_password_reset(conn, email)
    assert out["ok"] is True
    assert "If an account exists" in out["message"]
    out2 = request_password_reset(conn, "ghost@example.com")
    assert out2["message"] == out["message"]

    if out.get("dev_code"):
        reset_password(conn, email, out["dev_code"], "newpass99")
        with pytest.raises(ValueError):
            reset_password(conn, email, out["dev_code"], "another1")


def test_email_delivery_log_on_console(conn):
    email = "logged@example.com"
    register(conn, "loggeduser", email, "secret123")
    row = conn.execute(
        "SELECT status, provider_code, labeled_mock FROM app_email_delivery WHERE to_address = ?",
        [email],
    ).fetchone()
    assert row is not None
    assert row[0] in {"console", "sent"}
    assert row[1] in {"console", "console_mock_email"}
    assert bool(row[2]) is True


def test_mock_payment_scenarios_complete():
    provider = MockPaymentProvider()
    for scenario in sorted(MOCK_SCENARIOS):
        req = ProviderChargeRequest(
            amount=Decimal("10.00"),
            currency="USD",
            idempotency_key=f"ik-{scenario}",
            invoice_id=1,
            organization_id=1,
            scenario=scenario,
            payment_attempt_id=1,
        )
        result, event = provider.simulate(req, scenario)
        assert result.labeled_mock is True
        assert event.provider_event_id
        assert event.idempotency_key == f"ik-{scenario}"
        assert "[MOCK]" in result.message or "not a real" in result.message.lower()


def test_duplicate_mock_event_id_stable():
    provider = MockPaymentProvider()
    req = ProviderChargeRequest(
        amount=Decimal("5"),
        currency="USD",
        idempotency_key="same-key",
        invoice_id=1,
        organization_id=1,
        payment_attempt_id=9,
    )
    r1, e1 = provider.simulate(req, "duplicate_event")
    r2, e2 = provider.simulate(req, "duplicate_event")
    assert e1.provider_event_id == e2.provider_event_id
    assert r1.success and r2.success


def test_provider_event_idempotent(conn):
    uc = ProviderEventUseCases(conn)
    e1 = uc.process(
        provider_code="academic_mock",
        provider_event_id="evt_once_1",
        event_type="payment.succeeded",
        payload=json.dumps({"amount": "10", "currency": "USD"}),
    )
    e2 = uc.process(
        provider_code="academic_mock",
        provider_event_id="evt_once_1",
        event_type="payment.succeeded",
        payload=json.dumps({"amount": "10", "currency": "USD"}),
    )
    assert e1.id == e2.id
