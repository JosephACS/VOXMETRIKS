"""Unit checks for workpanel metric semantic presentation helpers (pure)."""
from __future__ import annotations

import pytest

# Import path when running from apps/backend
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.packages.workpanel.service import _metric  # noqa: E402


def test_failed_jobs_zero_is_healthy():
    m = _metric(
        id="failed_jobs",
        label="Trabajos o cargas fallidas",
        value=0,
        unit="ejecuciones",
        period="actual",
        explanation="Sin fallos durante el periodo.",
        detail_path="/x",
        available=True,
        scope="platform",
    )
    assert m["status"] == "healthy_zero"
    assert m["display_caption"] == "Sin fallos"
    assert m["value"] == 0


def test_open_alerts_zero_is_healthy():
    m = _metric(
        id="open_alerts",
        label="Alertas de negocio abiertas",
        value=0,
        unit="alertas",
        period="actual",
        explanation="Situaciones que requieren revisión.",
        detail_path="/x",
        available=True,
        scope="organization",
    )
    assert m["status"] == "healthy_zero"
    assert m["display_caption"] == "Sin alertas"


def test_income_zero_stays_numeric_ok():
    m = _metric(
        id="income_collected",
        label="Ingresos cobrados",
        value=0,
        unit="moneda",
        period="2026-06",
        explanation="Pagos confirmados durante el periodo.",
        detail_path="/x",
        available=True,
        scope="organization",
    )
    assert m["status"] == "ok"
    assert m["value"] == 0
    assert m["display_caption"] is None


def test_invoices_pending_zero_is_healthy():
    m = _metric(
        id="invoices_pending",
        label="Facturas pendientes o vencidas",
        value=0,
        unit="facturas",
        period="actual",
        explanation="Facturas de la organización que aún requieren cobro.",
        detail_path="/x",
        available=True,
        scope="organization",
    )
    assert m["status"] == "healthy_zero"
    assert m["display_caption"] == "Sin facturas pendientes"
