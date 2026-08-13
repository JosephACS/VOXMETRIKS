"""Focused P0/P1 hardening: invalid inputs, XSS storage, error envelopes."""

from __future__ import annotations

import asyncio
import json
from datetime import date

import duckdb
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError as PydanticValidationError

from app.core.email_format import is_valid_email_format
from app.core.error_handlers import duckdb_exception_handler, unhandled_exception_handler
from app.packages.artists.presentation.schemas import ArtistProfileCreateRequest
from app.packages.billing.presentation.schemas import InvoiceCreateRequest
from app.shared.schemas.models import UserRegister


def test_email_format_rejects_invalid_values():
    assert is_valid_email_format("person@example.com")
    assert is_valid_email_format("user@example.invalid")
    assert not is_valid_email_format("not-an-email")
    assert not is_valid_email_format("   ")
    assert not is_valid_email_format("foo@bar")
    assert not is_valid_email_format("user@")
    assert not is_valid_email_format("@example.com")


def test_register_schema_rejects_invalid_email():
    with pytest.raises(PydanticValidationError):
        UserRegister(username="hardenuser", email="not-an-email", password="longenough")


def test_register_api_rejects_invalid_email(client: TestClient):
    res = client.post(
        "/api/v1/users/register",
        json={"username": "hardenuser02", "email": "not-an-email", "password": "longenough"},
    )
    assert res.status_code in (400, 422)
    body = res.json()
    assert "status" in body
    assert "Traceback" not in json.dumps(body)
    assert "duckdb" not in json.dumps(body).lower()


def test_invoice_schema_rejects_inverted_period():
    with pytest.raises(PydanticValidationError):
        InvoiceCreateRequest(
            billing_profile_id=1,
            period_start=date(2026, 12, 1),
            period_end=date(2020, 1, 1),
        )


def test_artist_schema_rejects_oversized_and_blank_name():
    with pytest.raises(PydanticValidationError):
        ArtistProfileCreateRequest(display_name="A" * 201)
    with pytest.raises(PydanticValidationError):
        ArtistProfileCreateRequest(display_name="   ")
    stored = ArtistProfileCreateRequest(display_name="<script>alert(1)</script>")
    assert stored.display_name == "<script>alert(1)</script>"


def test_error_handlers_hide_internals():
    duck = asyncio.run(
        duckdb_exception_handler(
            None, duckdb.Error("Binder Error: SELECT * FROM secret_table")  # type: ignore[arg-type]
        )
    )
    duck_body = json.loads(duck.body)
    assert duck.status_code == 503
    assert "Binder" not in duck_body["message"]
    assert "secret_table" not in duck_body["message"]
    assert "SELECT" not in duck_body["message"]

    class DummyRequest:
        method = "GET"
        url = type("U", (), {"path": "/api/v1/probe"})()

    boom = asyncio.run(
        unhandled_exception_handler(
            DummyRequest(), RuntimeError("python exception with SQL SELECT 1")  # type: ignore[arg-type]
        )
    )
    boom_body = json.loads(boom.body)
    assert boom.status_code == 500
    assert boom_body["message"] == "An unexpected error occurred"
    assert "python exception" not in boom_body["message"]
